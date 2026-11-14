"""A full car left plugged in, replayed on the real house: old engine vs. new.

The house load is the *measured* one — grid − battery from the recorder (net of PV,
which is all the engine needs), zero-order held at 5 s — so the heavy loads that
paused the car live (Nov 2026: an oven, four pauses in five minutes) come back at
exactly their real size and timing. The battery and the car are modelled:

* the battery is Chris's (30.5 kWh, 10.2 kW), obeying setpoint / minimum SoC / hold
  through ``peak_sim.House``;
* the car charges single-phase (it does: go-e reports 1 phase, 15 A) and is full —
  it draws nothing unless it *wakes*, at which point it takes whatever it is offered
  at once (no ramp: the worst case for peak protection) until it is paused or the
  wake ends.

Each engine runs twice — never waking, and waking at the worst moments (inside every
heavy load the replay contains, plus a few at random) — and the table compares
charger writes, the billed quarter-hours and what the wakes cost.

    python -I tools/sim/idle_car.py <recorder history json> [start_utc end_utc]

The JSON is ``/api/history/period`` with ``minimal_response`` for the Victron grid
power, DC battery power and SoC. It holds real consumption, so keep it out of git.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import random
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import peak_sim  # noqa: E402  (loads the working-tree engine)

ROOT = pathlib.Path(__file__).resolve().parents[2]
TICK_S = 5
VIENNA = timezone(timedelta(hours=1))
CAR_PHASES = 1


def load_engine(ref: str | None):
    """The working-tree engine (``None``) or the one at a git ref, as its own module."""
    if ref is None:
        return peak_sim.engine
    src = subprocess.run(
        ["git", "show", f"{ref}:custom_components/goe_steve/engine.py"],
        cwd=ROOT, capture_output=True, check=True,
    ).stdout
    path = pathlib.Path(__file__).resolve().parent / f"_engine_{ref}.py"
    path.write_bytes(src)
    spec = importlib.util.spec_from_file_location(f"engine_{ref}", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    path.unlink()
    return mod


def series(raw: list, suffix: str) -> list[tuple[datetime, float]]:
    for s in raw:
        if s[0]["entity_id"].endswith(suffix):
            out = []
            for row in s:
                try:
                    out.append((datetime.fromisoformat(row["last_changed"]),
                                float(row["state"])))
                except ValueError:
                    pass
            return out
    raise SystemExit(f"no {suffix} in the history file")


def sample(points: list[tuple[datetime, float]], start: datetime, n: int) -> list[float]:
    """Zero-order hold onto a 5 s grid."""
    out, j, value = [], 0, points[0][1]
    for i in range(n):
        t = start + timedelta(seconds=i * TICK_S)
        while j < len(points) and points[j][0] <= t:
            value = points[j][1]
            j += 1
        out.append(value)
    return out


def cfg(engine) -> object:
    """Chris's live settings (diagnostics, 2026-11-14)."""
    return engine.EngineConfig(
        mode=engine.ChargingMode.FAST,
        smart_enabled=True,
        min_current_a=6.0,
        max_current_a=16.0,
        battery_reserve_soc=60.0,
        battery_hold_mode="auto",
        auto_phase=True,
        peak_guard_enabled=True,
        peak_soft_w=3700.0,
        peak_target_w=3900.0,
        peak_hard_w=4000.0,
        peak_follow_month=True,
        peak_month_buffer_w=200.0,
        # Live the reserve plan held the battery at 80 % (a dark-day stock); the
        # replay has no forecast, so the plan's hold is given as the reserve.
        shaving_reserve_soc=80.0,
        peak_min_soc=35.0,
        battery_capacity_kwh=30.5,
        grid_setpoint_w=100.0,
        local_tz=VIENNA,
    )


@dataclass
class Out:
    frc: int = 0
    amp: int = 0
    psm: int = 0
    levers: int = 0
    pauses: int = 0
    wake_wh: float = 0.0          # what the car took while awake
    hold_s: float = 0.0           # battery held off the house
    grid_kwh: float = 0.0         # imported
    windows: list[float] = field(default_factory=list)
    over: int = 0


def run(engine, load: list[float], soc0: float, start: datetime,
        wakes: list[tuple[int, int]]) -> Out:
    c = cfg(engine)
    state = engine.EngineState()
    state.month_peak_w = 3656.0
    state.month_key = f"{start.astimezone(VIENNA):%Y-%m}"
    state.month_peak_at = start - timedelta(days=5)
    house = peak_sim.House(soc=soc0, capacity_wh=30500.0, max_charge_w=10200.0,
                           max_discharge_w=10200.0, charge_eff=0.9)
    out = Out()
    setpoint = min_soc = None
    hold = False
    car_w = 0.0
    allowed, amps, phases = True, 16.0, CAR_PHASES
    last_amp_written: float | None = None
    last_charge: bool | None = None
    last_phases: int | None = None
    last_levers = None
    awake_until = -1
    wake_iter = iter(sorted(wakes))
    next_wake = next(wake_iter, None)
    prev_window = None

    for i, net in enumerate(load):
        t = i * TICK_S
        now = start + timedelta(seconds=t)
        if next_wake is not None and i >= next_wake[0]:
            awake_until = next_wake[0] + next_wake[1]
            next_wake = next(wake_iter, None)
        awake = i < awake_until
        car_w = (amps * min(phases, CAR_PHASES) * 230.0) if (awake and allowed) else 0.0
        pv = max(0.0, -net)
        house_w = max(0.0, net)
        house.step(pv, house_w, car_w, setpoint_w=setpoint, min_soc=min_soc,
                   hold=hold, dt=TICK_S)
        if car_w > 0:
            out.wake_wh += car_w * TICK_S / 3600.0
        out.grid_kwh += max(0.0, house.grid_w) * TICK_S / 3.6e6
        if hold:
            out.hold_s += TICK_S

        d = engine.decide(engine.ChargerInputs(
            car_connected=True, car_actual_power_w=car_w, phases=phases,
            voltage_v=230.0, grid_power_w=house.grid_w, pv_power_w=pv,
            battery_soc=house.soc, battery_power_w=house.battery_w, now=now,
        ), c, state)

        if d.house_control:
            levers = (d.grid_setpoint_w, d.battery_min_soc, d.hold_battery)
            if last_levers is not None and levers != last_levers:
                out.levers += 1
            last_levers = levers
            setpoint, min_soc, hold = levers
        if d.control:
            if d.should_charge != last_charge:
                out.frc += 1
                if last_charge and not d.should_charge:
                    out.pauses += 1
                last_charge = d.should_charge
            allowed = d.should_charge
            if d.should_charge:
                want = round(d.target_current_a)
                if last_amp_written is None or abs(want - last_amp_written) >= 1:
                    out.amp += 1
                    last_amp_written = want
                amps = float(want)
                if d.target_phases != last_phases:
                    if last_phases is not None:
                        out.psm += 1
                    last_phases = d.target_phases
                phases = d.target_phases
            else:
                last_amp_written = None
        if prev_window is not None and state.peak_window_start != prev_window:
            if state.peak_history:
                w = state.peak_history[-1][1]
                out.windows.append(w)
                if w > 3900.0:
                    out.over += 1
        prev_window = state.peak_window_start

    return out


def heavy_moments(load: list[float], threshold: float = 2500.0) -> list[int]:
    """Indices where the house load first crosses ``threshold`` (≥10 min apart)."""
    hits, last = [], -10**9
    for i in range(1, len(load)):
        if load[i] >= threshold > load[i - 1] and i - last > 120:
            hits.append(i)
            last = i
    return hits


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # -I ignores PYTHONIOENCODING
    raw = json.load(open(sys.argv[1], encoding="utf-8"))
    start = datetime.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else \
        datetime(2026, 11, 12, 3, 30, tzinfo=timezone.utc)
    end = datetime.fromisoformat(sys.argv[3]) if len(sys.argv) > 3 else \
        datetime(2026, 11, 13, 18, 0, tzinfo=timezone.utc)
    n = int((end - start).total_seconds() // TICK_S)
    grid = sample(series(raw, "grid_0_grid_power"), start, n)
    bat = sample(series(raw, "system_0_system_dc_battery_power"), start, n)
    soc = series(raw, "system_0_system_dc_battery_soc")
    soc0 = [v for t, v in soc if t <= start][-1] if soc[0][0] <= start else soc[0][1]
    load = [g - b for g, b in zip(grid, bat)]  # net of PV; positive = house draws

    heavy = heavy_moments(load)
    rnd = random.Random(7)
    # Wake 20 s into every heavy load (the worst moment) and at 10 random times;
    # each wake lasts 2 minutes — a pre-conditioning burst or a top-up.
    wakes = [(i + 4, 24) for i in heavy] + [(rnd.randrange(n), 24) for _ in range(10)]

    print(f"Replay {start:%Y-%m-%d %H:%M} → {end:%Y-%m-%d %H:%M} UTC, "
          f"{n * TICK_S / 3600:.1f} h, {len(heavy)} heavy loads ≥ 2.5 kW, "
          f"start SoC {soc0:.0f} %")
    old, new = load_engine("HEAD"), peak_sim.engine
    rows = []
    for name, eng in (("old (HEAD)", old), ("new", new)):
        for label, w in (("never wakes", []), ("wakes", wakes)):
            r = run(eng, load, soc0, start, w)
            rows.append((name, label, r))
    print(f"{'engine':11} {'car':12} {'frc':>5} {'amp':>5} {'psm':>4} {'pauses':>6} "
          f"{'levers':>6} {'max QH':>7} {'>3.9':>5} {'wake Wh':>8} {'hold h':>6} {'grid kWh':>8}")
    for name, label, r in rows:
        print(f"{name:11} {label:12} {r.frc:5d} {r.amp:5d} {r.psm:4d} {r.pauses:6d} "
              f"{r.levers:6d} {max(r.windows):7.0f} {r.over:5d} {r.wake_wh:8.0f} "
              f"{r.hold_s / 3600:6.1f} {r.grid_kwh:8.1f}")
    # Per-window difference the wakes made under the new rule.
    by = {(n_, l_): r for n_, l_, r in rows}
    for name in ("old (HEAD)", "new"):
        base, woke = by[(name, "never wakes")], by[(name, "wakes")]
        deltas = [b - a for a, b in zip(base.windows, woke.windows)]
        print(f"{name}: wakes moved a quarter-hour by at most {max(deltas):+.0f} W "
              f"(worst QH with wakes {max(woke.windows):.0f} W)")


if __name__ == "__main__":
    main()
