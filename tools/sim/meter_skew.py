"""The house share against meters that don't report together — the Nov 2026 oscillation.

``peak_sim.run`` ticks every 10 s with an ESS that settles instantly and every meter read
at the same moment. Under those assumptions ``grid − battery`` really is invariant to the
setpoint, and the house share is stable. On the live system neither holds:

* the grid meter and the battery's DC power reach Home Assistant every ~5 s and ~6 s,
  each on its own clock, the battery figure smoothed over a few seconds;
* the ESS needs a couple of seconds to follow a load step or a new setpoint;
* the go-e reports the car every second, and a car told to start takes ~9 s to draw.

So during any step — a car starting, an oven, the setpoint's own moves — one meter has
seen it and the other hasn't, and ``grid − battery − car`` is off by up to the step.
Live (Mon 9 Nov 2026, 07:03) that read a 2.6 kW car start as 2.6 kW of *house* load, and
the setpoint then swung 0 ↔ 3.9 kW every few seconds for seven minutes, charging the
battery from the grid between swings.

This harness runs the real engine at 0.25 s against that timing: an ESS with a lag,
meters on their own cadences, the coordinator's debounce and write throttles, a car
with a start delay. Each scenario runs once per variant:

* ``shipped``    — grid − battery − car, used as read (v5.11.0)
* ``held``       — the same reading, but the share engages / rises only on a load that
                   has held for ``_SHARE_HOLD_S`` (falls at once)
* ``consumption``— the house load read directly (Victron AC consumption − car), used
                   as read

    python tools/sim/meter_skew.py            # the table
    python tools/sim/meter_skew.py 1 shipped  # one run, with its event trace
    python tools/sim/meter_skew.py sweep      # the hold window, swept
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from typing import Callable

import peak_sim
from heavy_load import cooking, sauna
from peak_sim import ChargerInputs, ChargingMode, EngineConfig, EngineState

engine = peak_sim.engine
WINTER = timezone(timedelta(hours=1))
DT = 0.25
CAPACITY_KWH = 30.5


# --- Timing, as measured live (Nov 2026) ----------------------------------------------

@dataclass
class Timing:
    ess_tau_s: float = 2.5  # first-order follow of the ESS toward its target
    ess_dead_s: float = 0.5  # a written setpoint takes effect after this
    grid_period_s: float = 5.0
    grid_phase_s: float = 0.1
    bat_period_s: float = 6.0
    bat_phase_s: float = 2.3
    bat_avg_s: float = 3.0  # the DC battery power is a smoothed figure
    cons_period_s: float = 5.0
    cons_phase_s: float = 0.6
    nrg_period_s: float = 1.0
    car_start_delay_s: float = 9.0  # frc on → first current (seen: 9 s)
    car_ramp_s: float = 2.0
    debounce_s: float = 0.75  # INPUT_SETTLE_S
    cooldown_s: float = 1.5  # the request-refresh debouncer
    poll_s: float = 30.0
    amp_interval_s: float = 2.0  # MIN_UPDATE_INTERVAL_S
    backoff_a: float = 2.0  # FAST_BACKOFF_DELTA_A
    setpoint_deadband_w: float = 25.0
    inverter_eff: float = 0.94
    # How old a reading already is when it reaches Home Assistant. Live, the grid
    # value lagged the battery's by several seconds (07:03:03: grid 2504 W three
    # seconds after the battery had taken the car over at −2923 W).
    grid_lag_s: float = 0.0
    bat_lag_s: float = 0.0
    cons_lag_s: float = 0.0
    nrg_lag_s: float = 0.0


def _due(t: float, period: float, phase: float) -> bool:
    k = round((t - phase) / period)
    return abs(t - phase - k * period) < DT / 2 and t >= phase


# --- Scenario ---------------------------------------------------------------------------

@dataclass
class SkewScenario:
    n: int
    title: str
    cfg: EngineConfig
    house: Callable[[float], float]  # gross house load (W), car excluded
    duration_s: float
    soc0: float
    start: datetime
    car_connected: bool = False
    car_awake_at: float = 0.0  # a car that isn't drawing until it decides to
    seed_month_peak_w: float = 0.0
    pv: Callable[[float], float] = lambda t: 0.0
    # The car's own side: how many phases it can take (Chris's charges on one), and
    # what it draws per amp offered relative to 230 V (charger loss, line voltage).
    car_phases: int = 3
    car_draw: float = 1.0


@dataclass
class SkewResult:
    setpoint_writes: int = 0
    frc_writes: int = 0
    car_starts: int = 0
    amp_writes: int = 0
    grid_to_battery_wh: float = 0.0  # the ESS charging from the grid outside a refill
    battery_out_wh: float = 0.0
    car_kwh: float = 0.0
    grid_max_w: float = 0.0
    worst_qh_w: float = 0.0
    qh: list[float] = field(default_factory=list)
    engaged_s: float = 0.0
    trace: list[str] = field(default_factory=list)


def run(sc: SkewScenario, *, use_consumption: bool, hold_s: float,
        timing: Timing = Timing(), keep_trace: bool | str = False) -> SkewResult:
    engine._SHARE_HOLD_S = hold_s
    tm = timing
    state = EngineState()
    if sc.seed_month_peak_w:
        state.month_peak_w = sc.seed_month_peak_w
        local = sc.start.astimezone(WINTER)
        state.month_key = f"{local.year:04d}-{local.month:02d}"
        state.month_peak_at = sc.start - timedelta(days=3)
    res = SkewResult()
    cap_wh = CAPACITY_KWH * 1000.0

    # Physics
    soc = sc.soc0
    bat_ac = 0.0  # + charging
    car_w = 0.0
    car_target_w = 0.0
    car_start_at: float | None = None
    dc_hist: list[tuple[float, float]] = []
    hist: list[tuple[float, float, float, float, float]] = []  # t, grid, dc, cons, car

    def past(lag: float, idx: int) -> float:
        want = t - lag
        for row in reversed(hist):
            if row[0] <= want + 1e-9:
                return row[idx]
        return hist[0][idx]

    # What the house was told
    setpoint: float | None = 100.0
    setpoint_pending: list[tuple[float, float]] = []
    min_soc: float | None = 50.0
    hold = False
    frc_on: bool | None = None
    amps_written: float | None = None
    phases_written = 1
    last_amp_write = -1e9
    refilling_now = False

    # What the coordinator has read
    rd_grid = 100.0
    rd_bat = 0.0
    rd_cons = sc.house(0.0)
    rd_nrg = 0.0
    next_run: float | None = 0.0
    last_run = -1e9
    last_poll = 0.0
    qh_start = None
    qh_wh = 0.0
    qh_s = 0.0

    def log(t: float, msg: str) -> None:
        if keep_trace:
            res.trace.append(f"{t:7.1f}s  {msg}")

    steps = int(sc.duration_s / DT)
    for i in range(steps + 1):
        t = i * DT
        now = sc.start + timedelta(seconds=t)

        # --- physics --------------------------------------------------------------
        while setpoint_pending and setpoint_pending[0][0] <= t:
            setpoint = setpoint_pending.pop(0)[1]
        house_w = sc.house(t)
        pv_w = sc.pv(t)

        awake = sc.car_connected and t >= sc.car_awake_at
        want = car_target_w if (awake and frc_on) else 0.0
        if want > 0.0 and car_w <= 1.0:
            if car_start_at is None:
                car_start_at = t + tm.car_start_delay_s
            if t >= car_start_at:
                car_w = min(want, car_w + want * DT / tm.car_ramp_s + 2.0)
        elif want > 0.0:
            step = want * DT / tm.car_ramp_s
            car_w = min(want, car_w + step) if car_w < want else max(want, car_w - step)
        else:
            car_start_at = None
            car_w = max(0.0, car_w - 3000.0 * DT)
        if want == 0.0:
            car_start_at = None

        floor = max(10.0, min_soc if min_soc is not None else 10.0)
        load = house_w + car_w - pv_w
        target = -(load - (setpoint if setpoint is not None else 0.0))  # + charging
        if min_soc is not None and soc < min_soc - 0.5:
            target = 10200.0  # the ESS's own full-power recharge
        elif target < 0.0 and (hold or soc <= floor):
            target = 0.0
        if soc >= 100.0 and target > 0.0:
            target = 0.0
        target = max(-10200.0, min(10200.0, target))
        bat_ac += (target - bat_ac) * (1.0 - math.exp(-DT / tm.ess_tau_s))
        grid_w = load + bat_ac
        dc = bat_ac * tm.inverter_eff if bat_ac > 0 else bat_ac / tm.inverter_eff
        soc = max(0.0, min(100.0, soc + dc * DT / 3600.0 / cap_wh * 100.0))
        hist.append((t, grid_w, dc, house_w + car_w, car_w))
        if len(hist) > 200:
            del hist[:100]

        res.car_kwh += car_w * DT / 3600.0 / 1000.0
        res.grid_max_w = max(res.grid_max_w, grid_w)
        if bat_ac > 50.0 and not refilling_now and pv_w < 50.0:
            res.grid_to_battery_wh += bat_ac * DT / 3600.0
        if bat_ac < 0:
            res.battery_out_wh += -bat_ac * DT / 3600.0
        qs = engine._window_start(now)
        if qh_start != qs:
            if qh_start is not None and qh_s >= 600:
                res.worst_qh_w = max(res.worst_qh_w, qh_wh * 3600.0 / qh_s)
                res.qh.append(qh_wh * 3600.0 / qh_s)
            qh_start, qh_wh, qh_s = qs, 0.0, 0.0
        qh_wh += grid_w * DT / 3600.0
        qh_s += DT

        # --- meters ---------------------------------------------------------------
        trigger = False
        if _due(t, tm.nrg_period_s, 0.0):
            rd_nrg = past(tm.nrg_lag_s, 4)
        if _due(t, tm.grid_period_s, tm.grid_phase_s):
            rd_grid = past(tm.grid_lag_s, 1)
            trigger = True
        if _due(t, tm.bat_period_s, tm.bat_phase_s):
            vals = [r[2] for r in hist if t - tm.bat_lag_s - tm.bat_avg_s < r[0] <= t - tm.bat_lag_s + 1e-9]
            rd_bat = sum(vals) / len(vals) if vals else past(tm.bat_lag_s, 2)
            trigger = True
        if _due(t, tm.cons_period_s, tm.cons_phase_s):
            rd_cons = past(tm.cons_lag_s, 3)
            trigger = trigger or use_consumption
        if trigger:
            next_run = t + tm.debounce_s

        run_now = False
        if next_run is not None and t >= next_run and t - last_run >= tm.cooldown_s:
            run_now, next_run = True, None
        if t - last_poll >= tm.poll_s:
            run_now, last_poll = True, t
        if not run_now:
            continue
        last_run = t

        # --- the engine -----------------------------------------------------------
        inp = ChargerInputs(
            car_connected=sc.car_connected,
            car_actual_power_w=rd_nrg,
            phases=phases_written,
            grid_power_w=rd_grid,
            pv_power_w=pv_w,
            battery_soc=round(soc),
            battery_power_w=rd_bat,
            house_consumption_w=rd_cons if use_consumption else None,
            now=now,
        )
        d = engine.decide(inp, sc.cfg, state)
        refilling_now = d.battery_refilling
        if keep_trace == "runs":
            log(t, f"grid {rd_grid:5.0f} bat {rd_bat:6.0f} car {rd_nrg:5.0f} real {house_w:5.0f}+{car_w:5.0f} "
                   f"grid_real {grid_w:5.0f} | eng={int(state.peak_share_engaged)} sp={d.grid_setpoint_w} "
                   f"chg={int(d.should_charge)} {d.target_current_a:.0f}A tier={d.peak_tier} {d.peak_reason_key}/{d.reason_key}")
        if state.peak_share_engaged:
            res.engaged_s += tm.cooldown_s
        if d.house_control:
            sp = d.grid_setpoint_w
            last_sp = setpoint_pending[-1][1] if setpoint_pending else setpoint
            if sp is not None and (last_sp is None or abs(sp - last_sp) >= tm.setpoint_deadband_w):
                setpoint_pending.append((t + tm.ess_dead_s, sp))
                res.setpoint_writes += 1
                log(t, f"setpoint {sp:5.0f}  (grid {rd_grid:5.0f} bat {rd_bat:6.0f} "
                       f"car {rd_nrg:5.0f}) engaged={state.peak_share_engaged}")
            min_soc = d.battery_min_soc
            hold = d.hold_battery
        if d.control and sc.car_connected:
            if d.should_charge != frc_on:
                frc_on = d.should_charge
                res.frc_writes += 1
                if frc_on:
                    res.car_starts += 1
                log(t, f"car {'START' if frc_on else 'STOP '} — {d.reason_key}")
            if d.should_charge:
                amps = round(d.target_current_a)
                phases_written = d.target_phases or phases_written
                if amps != amps_written and (
                    amps_written is None
                    or t - last_amp_write >= tm.amp_interval_s
                    or amps_written - amps >= tm.backoff_a
                ):
                    amps_written = amps
                    last_amp_write = t
                    res.amp_writes += 1
                car_target_w = ((amps_written or 6) * min(phases_written, sc.car_phases)
                                * 230.0 * sc.car_draw)

    if qh_start is not None and qh_s >= 600:
        res.worst_qh_w = max(res.worst_qh_w, qh_wh * 3600.0 / qh_s)
    return res


# --- Chris's setup, Monday 9 Nov 2026 ------------------------------------------------------

def cfg(**kw) -> EngineConfig:
    base = dict(
        mode=ChargingMode.FAST,
        smart_enabled=True,
        min_current_a=6.0,
        max_current_a=16.0,
        battery_hold_mode="free",
        auto_phase=True,
        peak_guard_enabled=True,
        peak_soft_w=3700.0,
        peak_target_w=3900.0,
        peak_hard_w=4000.0,
        peak_follow_month=True,
        peak_month_buffer_w=200.0,
        shaving_reserve_soc=50.0,
        peak_min_soc=35.0,
        peak_ready_soc=80.0,
        battery_capacity_kwh=CAPACITY_KWH,
        grid_setpoint_w=100.0,
        local_tz=WINTER,
    )
    base.update(kw)
    return EngineConfig(**base)


def scenarios() -> list[SkewScenario]:
    morning = datetime(2026, 11, 9, 7, 0, tzinfo=WINTER).astimezone(timezone.utc)
    evening = datetime(2026, 11, 9, 18, 0, tzinfo=WINTER).astimezone(timezone.utc)
    quiet = lambda t: 900.0  # noqa: E731
    return [
        SkewScenario(1, "Mon 07:03 replay: car wakes up into Fast, quiet house", cfg(),
                     quiet, 20 * 60, 82.0, morning, car_connected=True,
                     car_awake_at=170.0, seed_month_peak_w=3656.0),
        SkewScenario(2, "Mon 16:42-like: cooking 40 min, no car, battery 88 %", cfg(),
                     cooking(start_s=60.0), 45 * 60, 88.0, evening,
                     seed_month_peak_w=3656.0),
        SkewScenario(3, "Sauna evening, no car, battery 65 %", cfg(),
                     sauna(start_s=60.0), 3 * 3600, 65.0, evening,
                     seed_month_peak_w=3656.0),
        SkewScenario(4, "Sauna while the car fast-charges, battery 70 %", cfg(),
                     sauna(start_s=600.0), 3 * 3600, 70.0, evening, car_connected=True,
                     seed_month_peak_w=3656.0),
        SkewScenario(5, "Cooking while the car fast-charges, battery 80 %", cfg(),
                     cooking(start_s=300.0), 60 * 60, 80.0, evening, car_connected=True,
                     seed_month_peak_w=3656.0),
        SkewScenario(6, "Quiet night, car fast-charging, battery at its reserve", cfg(),
                     quiet, 60 * 60, 80.0, morning, car_connected=True,
                     seed_month_peak_w=3656.0),
    ]


VARIANTS = {
    "shipped": dict(use_consumption=False, hold_s=0.0),
    "held": dict(use_consumption=False, hold_s=15.0),
    # The engine subtracts the car as it reads at the engine run. Reading it at the
    # consumption's own timestamp instead measured the same within ±10 % on every
    # scenario (Nov 2026), so the coordinator doesn't keep that bookkeeping. A
    # measured load is used as read; the hold only applies to the derived one.
    "consumption": dict(use_consumption=True, hold_s=15.0),
}


def table() -> None:
    print(f"{'scenario':58} {'variant':12} {'worstQH':>7} {'gridmax':>7} {'sp wr':>5} "
          f"{'starts':>6} {'amps':>4} {'grid→bat':>8} {'bat out':>7} {'car':>5} {'shared':>6}")
    for sc in scenarios():
        for name, kw in VARIANTS.items():
            r = run(sc, **kw)
            print(f"{sc.n} {sc.title:56} {name:12} {r.worst_qh_w/1000:7.2f} "
                  f"{r.grid_max_w/1000:7.2f} {r.setpoint_writes:5d} {r.car_starts:6d} "
                  f"{r.amp_writes:4d} {r.grid_to_battery_wh:6.0f}Wh {r.battery_out_wh/1000:5.1f}k "
                  f"{r.car_kwh:5.1f} {r.engaged_s/60:5.1f}m")
        print()


def sweep() -> None:
    holds = (0.0, 5.0, 10.0, 15.0, 20.0, 30.0)
    print("Hold window sweep, grid-only reading — setpoint writes / car starts / grid→battery Wh / worst QH kW")
    for sc in scenarios():
        cells = []
        for h in holds:
            r = run(sc, use_consumption=False, hold_s=h)
            cells.append(f"{r.setpoint_writes:3d}/{r.car_starts:2d}/{r.grid_to_battery_wh:4.0f}/"
                         f"{r.worst_qh_w/1000:4.2f}")
        print(f"{sc.n} {sc.title[:40]:40} " + "  ".join(f"{h:>4.0f}s {c}" for h, c in zip(holds, cells)))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    if args and args[0] == "sweep":
        sweep()
    elif args:
        sc = next(s for s in scenarios() if s.n == int(args[0]))
        r = run(sc, **VARIANTS[args[1] if len(args) > 1 else "shipped"], keep_trace=True)
        print("\n".join(r.trace[:150]))
        print({k: v for k, v in vars(r).items() if k != "trace"})
    else:
        table()
