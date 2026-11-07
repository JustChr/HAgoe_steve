"""The field-test log: one record per billing quarter-hour, plus events.

Pure and Home-Assistant-free, like the engine, so it can be tested on its own. The
coordinator feeds it one :class:`Sample` per regulation cycle; whenever a quarter-hour
closes, :meth:`QuarterLog.observe` hands back its record. The coordinator keeps those
in one storage file per day and serves them through *Download diagnostics*.

Why it exists: Home Assistant's recorder keeps states for ten days and the integration's
own decision sensors are often excluded from it, so after a few weeks of live running
nothing would be left to explain a quarter-hour — not the bill, not the reason. This
answers, per quarter-hour: what did it cost, what was the brain doing, where did the
energy go, what did the car pay for it, and how often did we write to the hardware.

Kept deliberately compact (short keys, rounded numbers): 45 days are ~4300 records.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

#: A gap between two samples longer than this is not carried across: the seconds go
#: to ``s_gap`` instead, so a restart can't book half an hour to the last reading.
MAX_HOLD_S: float = 120.0

#: The bug v5.9 fixed: the ESS's minimum SoC above the battery's charge makes it
#: recharge at full power. Counted with a little slack for SoC sensor rounding.
MIN_SOC_ABOVE_SLACK_PCT: float = 0.5

#: Status reasons under which peak protection is holding the car off.
CAR_HELD_KEYS: frozenset[str] = frozenset(
    {"peak_pause", "peak_refill_car", "peak_stock_up_car"}
)

#: Peak reasons that mean the battery is carrying part of a heavy house load.
SHARE_KEYS: frozenset[str] = frozenset({"peak_share", "peak_share_paced"})

#: Write kinds the coordinator reports through :meth:`QuarterLog.note_write`.
WRITE_KINDS: tuple[str, ...] = ("amp", "frc", "psm", "setpoint", "min_soc", "hold")


@dataclass(slots=True)
class Sample:
    """What one regulation cycle saw and decided. Powers in W, SoC in %."""

    now: datetime
    window_start: datetime | None
    control_ok: bool  # False: required input missing, nothing was written
    grid_w: float | None = None
    battery_w: float | None = None  # + charging, − discharging
    battery_soc: float | None = None
    pv_w: float | None = None
    car_w: float = 0.0
    car_connected: bool = False
    tier: str = "off"
    reason_key: str = ""
    peak_reason_key: str = ""
    refilling: bool = False
    grid_charging: bool = False
    setpoint_w: float | None = None  # what the engine asked for
    min_soc: float | None = None  # what the engine asked for
    ess_min_soc: float | None = None  # what the ESS entity actually holds
    peak_degraded: bool = False
    peak_metered: bool = False
    target_w: float = 0.0
    hard_w: float = 0.0
    month_peak_w: float = 0.0


def _round(value: float | None, digits: int = 0) -> float | int | None:
    if value is None:
        return None
    rounded = round(value, digits)
    return int(rounded) if digits == 0 else rounded


@dataclass(slots=True)
class _Quarter:
    """The running accumulator for one quarter-hour."""

    start: datetime
    seconds: dict[str, float] = field(default_factory=dict)
    wh: dict[str, float] = field(default_factory=dict)
    reasons: dict[str, float] = field(default_factory=dict)
    peak_reasons: dict[str, float] = field(default_factory=dict)
    writes: dict[str, int] = field(default_factory=dict)
    soc_first: float | None = None
    soc_last: float | None = None
    soc_min: float | None = None
    grid_max: float | None = None
    setpoint_max: float | None = None
    min_soc_lo: float | None = None
    min_soc_hi: float | None = None
    ess_min_soc_lo: float | None = None
    ess_min_soc_hi: float | None = None
    car_starts: int = 0
    last: Sample | None = None

    def add_s(self, key: str, seconds: float) -> None:
        self.seconds[key] = self.seconds.get(key, 0.0) + seconds

    def add_wh(self, key: str, watts: float, seconds: float) -> None:
        if watts > 0.0:
            self.wh[key] = self.wh.get(key, 0.0) + watts * seconds / 3600.0


def _lo(a: float | None, b: float | None) -> float | None:
    return b if a is None else a if b is None else min(a, b)


def _hi(a: float | None, b: float | None) -> float | None:
    return b if a is None else a if b is None else max(a, b)


class QuarterLog:
    """Accumulates samples into quarter-hour records and transition events."""

    def __init__(self) -> None:
        self._q: _Quarter | None = None
        self._flags: dict[str, bool] = {}
        self._tier: str | None = None
        self._car_charging: bool | None = None

    # --- Input --------------------------------------------------------------------
    def note_write(self, kind: str) -> None:
        """Count one write the coordinator actually sent to the hardware."""
        if self._q is not None:
            self._q.writes[kind] = self._q.writes.get(kind, 0) + 1

    def observe(
        self, sample: Sample, history: list[tuple[datetime, float]] | None = None
    ) -> tuple[dict | None, list[dict]]:
        """Take one cycle's sample. Returns ``(closed_record, events)``.

        ``history`` is the engine's list of completed windows ``(start, average W)``,
        the authoritative billed figure for a quarter-hour that just closed.
        """
        events: list[dict] = []
        closed: dict | None = None
        q = self._q

        # Book the time since the last sample to the window that sample was in, with
        # the last sample's values held (the same zero-order hold the engine uses).
        if q is not None and q.last is not None:
            dt = (sample.now - q.last.now).total_seconds()
            if dt > 0.0:
                if dt > MAX_HOLD_S:
                    q.add_s("gap", dt)
                else:
                    self._book(q, q.last, dt)

        start = sample.window_start
        if start is not None and (q is None or q.start != start):
            if q is not None:
                closed = self._close(q, history or [])
            q = self._q = _Quarter(start=start)
        if q is None:
            return closed, events

        self._take(q, sample)
        events.extend(self._transitions(sample))
        q.last = sample
        return closed, events

    # --- Accumulation ---------------------------------------------------------------
    @staticmethod
    def _book(q: _Quarter, s: Sample, dt: float) -> None:
        q.add_s("seen", dt)
        if not s.control_ok:
            q.add_s("blind", dt)
            return
        if s.tier in ("soft", "hard"):
            q.add_s(s.tier, dt)
        if s.refilling:
            q.add_s("refill", dt)
        if s.grid_charging:
            q.add_s("grid_charge", dt)
        if s.peak_reason_key in SHARE_KEYS:
            q.add_s("share", dt)
        if s.reason_key in CAR_HELD_KEYS:
            q.add_s("car_held", dt)
        if (
            s.ess_min_soc is not None
            and s.battery_soc is not None
            and s.ess_min_soc > s.battery_soc + MIN_SOC_ABOVE_SLACK_PCT
        ):
            q.add_s("min_soc_above_soc", dt)
        if s.reason_key:
            q.reasons[s.reason_key] = q.reasons.get(s.reason_key, 0.0) + dt
        if s.peak_reason_key:
            q.peak_reasons[s.peak_reason_key] = (
                q.peak_reasons.get(s.peak_reason_key, 0.0) + dt
            )
        grid = s.grid_w or 0.0
        battery = s.battery_w or 0.0
        pv = s.pv_w or 0.0
        car = max(0.0, s.car_w)
        q.add_wh("grid_in", grid, dt)
        q.add_wh("grid_out", -grid, dt)
        q.add_wh("bat_in", battery, dt)
        q.add_wh("bat_out", -battery, dt)
        q.add_wh("pv", pv, dt)
        q.add_wh("car", car, dt)
        q.add_wh("house", grid + pv - battery - car, dt)

    @staticmethod
    def _take(q: _Quarter, s: Sample) -> None:
        if s.battery_soc is not None:
            if q.soc_first is None:
                q.soc_first = s.battery_soc
            q.soc_last = s.battery_soc
            q.soc_min = _lo(q.soc_min, s.battery_soc)
        q.grid_max = _hi(q.grid_max, s.grid_w)
        q.setpoint_max = _hi(q.setpoint_max, s.setpoint_w)
        q.min_soc_lo = _lo(q.min_soc_lo, s.min_soc)
        q.min_soc_hi = _hi(q.min_soc_hi, s.min_soc)
        q.ess_min_soc_lo = _lo(q.ess_min_soc_lo, s.ess_min_soc)
        q.ess_min_soc_hi = _hi(q.ess_min_soc_hi, s.ess_min_soc)

    def _transitions(self, s: Sample) -> list[dict]:
        """Events: when a shave, refill, held car or tier starts and ends."""
        if not s.control_ok:
            return []
        stamp = s.now.isoformat(timespec="seconds")
        soc = _round(s.battery_soc, 1)
        events: list[dict] = []
        flags = {
            "share": s.peak_reason_key in SHARE_KEYS,
            "refill": s.refilling,
            "car_held": s.reason_key in CAR_HELD_KEYS,
            "grid_charge": s.grid_charging,
        }
        for name, on in flags.items():
            before = self._flags.get(name)
            if before is not None and before != on:
                events.append({"t": stamp, "ev": name, "on": on, "soc": soc})
            self._flags[name] = on
        if self._tier is not None and s.tier != self._tier:
            events.append({"t": stamp, "ev": "tier", "to": s.tier, "soc": soc})
        self._tier = s.tier
        charging = s.car_connected and s.car_w >= 300.0
        if self._car_charging is False and charging and self._q is not None:
            self._q.car_starts += 1
        self._car_charging = charging
        return events

    @staticmethod
    def _close(q: _Quarter, history: list[tuple[datetime, float]]) -> dict:
        billed = next((avg for start, avg in reversed(history) if start == q.start), None)
        last = q.last
        record: dict = {
            "t": q.start.isoformat(timespec="minutes"),
            "avg_w": _round(billed),
            "metered": bool(last and last.peak_metered),
            "degraded": bool(last and last.peak_degraded),
            "target_w": _round(last.target_w) if last else None,
            "hard_w": _round(last.hard_w) if last else None,
            "month_w": _round(last.month_peak_w) if last else None,
            "grid_max_w": _round(q.grid_max),
            "soc": [_round(q.soc_first, 1), _round(q.soc_min, 1), _round(q.soc_last, 1)],
            "setpoint_max_w": _round(q.setpoint_max),
            "min_soc": [_round(q.min_soc_lo), _round(q.min_soc_hi)],
            "ess_min_soc": [_round(q.ess_min_soc_lo), _round(q.ess_min_soc_hi)],
            "s": {k: _round(v) for k, v in sorted(q.seconds.items())},
            "wh": {k: _round(v) for k, v in sorted(q.wh.items())},
            "writes": dict(sorted(q.writes.items())),
            "car_starts": q.car_starts,
            "reasons": {k: _round(v) for k, v in sorted(q.reasons.items())},
            "peak_reasons": {k: _round(v) for k, v in sorted(q.peak_reasons.items())},
        }
        return record
