"""Heavy house loads against the real battery: does the grid help the battery enough?

Each scenario runs twice through the real engine — once with the battery's power
withheld (the tier ladder, i.e. how peak protection behaved up to v5.7) and once
with it (the house share: the grid carries up to the budget, the battery only the
excess). Optionally a third time with the battery's capacity known, which lets the
grid's share rise *before* the pack runs dry.

House: Chris's measured system — 30.5 kWh usable, 10.2 kW inverter, 90 % round trip,
limits 3.2 / 3.7 / 3.9 kW, shaving reserve 50 %, floor 35 %, resting setpoint 100 W.
The sauna is the measured one: 8.7 kW flat out for the 45-minute heat-up, then
thermostat cycling averaging ~4 kW (~13 kWh for the evening).

    python tools/sim/heavy_load.py            # the table
    python tools/sim/heavy_load.py sweep      # the energy-horizon sweep
"""

from __future__ import annotations

import math
import sys
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import peak_sim
from peak_sim import ChargingMode, EngineConfig, Scenario, run

engine = peak_sim.engine  # the very module instance the runs use

WINTER = timezone(timedelta(hours=1))
CAPACITY_KWH = 30.5
FOLLOW_MONTH = "nofollow" not in sys.argv


def cfg(**kw) -> EngineConfig:
    base = dict(
        mode=ChargingMode.SMART,
        smart_enabled=True,
        min_current_a=6.0,
        max_current_a=16.0,
        battery_reserve_soc=85.0,
        peak_guard_enabled=True,
        peak_soft_w=3200.0,
        peak_target_w=3700.0,
        peak_hard_w=3900.0,
        peak_follow_month=FOLLOW_MONTH,  # Chris runs with it on
        shaving_reserve_soc=50.0,
        peak_min_soc=35.0,
        grid_setpoint_w=100.0,
        local_tz=WINTER,
    )
    base.update(kw)
    return EngineConfig(**base)


def sauna(start_s: float = 600.0, base_w: float = 900.0):
    """Base load plus the measured sauna, switched on at ``start_s``."""
    def f(t: float) -> float:
        s = t - start_s
        if s < 0 or s >= 2.5 * 3600:
            return base_w
        if s < 45 * 60:
            return base_w + 8700.0
        # Thermostat cycling, ~46 % duty. The period wanders so it can't alias
        # against the billing quarter-hour (see the README's modelling traps).
        period = 520.0 * (1.0 + 0.30 * math.sin(t / 1100.0))
        return base_w + (8700.0 if (t % period) < period * 0.46 else 0.0)
    return f


def cooking(start_s: float = 600.0, base_w: float = 900.0):
    """Hob and oven together for 40 minutes: short, sharp, ~4 kWh."""
    def f(t: float) -> float:
        s = t - start_s
        if 0 <= s < 40 * 60:
            hob = 3500.0 if (t % 180.0) < 120.0 else 1200.0
            return base_w + 2500.0 + hob
        return base_w
    return f


def scenarios() -> list[Scenario]:
    start = datetime(2027, 1, 15, 18, 0, tzinfo=WINTER).astimezone(timezone.utc)
    common = dict(
        pv=lambda t: 0.0,
        start=start,
        capacity_wh=CAPACITY_KWH * 1000.0,
        max_discharge_w=10200.0,
        max_charge_w=10200.0,
        charge_eff=0.90,
    )
    out = []
    for n, soc in ((1, 85.0), (2, 65.0), (3, 55.0), (4, 45.0)):
        out.append(Scenario(
            n=n, title=f"Sauna evening, no car, battery at {soc:.0f} %",
            story="", duration_s=4 * 3600, cfg=cfg(), house=sauna(), soc0=soc,
            car_connected=lambda t: False, **common,
        ))
    out.append(Scenario(
        n=5, title="Cooking 40 min (hob + oven), battery at 55 %",
        story="", duration_s=2 * 3600, cfg=cfg(), house=cooking(), soc0=55.0,
        car_connected=lambda t: False, **common,
    ))
    out.append(Scenario(
        n=6, title="Sauna while the car fast-charges, battery at 70 %",
        story="", duration_s=4 * 3600, cfg=cfg(mode=ChargingMode.FAST),
        house=sauna(), soc0=70.0, **common,
    ))
    # Today's live test: Fast, car on one phase, a quiet house, the sun going down.
    live = dict(common)
    live["pv"] = lambda t: max(0.0, 1100.0 - t * 1100.0 / 3600.0)
    out.append(Scenario(
        n=7, title="Live test replay: Fast on 1φ, quiet house, battery at 79 %",
        story="", duration_s=2 * 3600,
        cfg=cfg(mode=ChargingMode.FAST, max_phases=1, auto_phase=False),
        house=lambda t: 900.0, soc0=79.0, **live,
    ))
    return out


def summarise(sc: Scenario, res) -> dict:
    worst = max((w[1] for w in res.windows), default=0.0)
    over = sum(1 for w in res.windows if w[1] > sc.cfg.peak_target_w)
    used = (sc.soc0 - res.min_soc_seen) / 100.0 * CAPACITY_KWH
    return dict(worst=worst, over=over, used=used, low=res.min_soc_seen,
                car=res.car_kwh, writes=res.lever_writes, amps=res.amp_writes,
                frc=res.frc_writes)


def variants(sc: Scenario, horizon_s: float | None = None):
    old = replace(sc, hide_battery_power=True)
    new = sc
    paced = replace(sc, cfg=replace(sc.cfg, battery_capacity_kwh=CAPACITY_KWH))
    if horizon_s is not None:
        engine._PEAK_ENERGY_HORIZON_S = horizon_s
    return [("tiers (old)", old), ("share", new), ("share+capacity", paced)]


def table() -> None:
    print(f"{'scenario':58} {'variant':16} {'worst QH':>8} {'>tgt':>4} "
          f"{'batt kWh':>8} {'low SoC':>7} {'car kWh':>7} {'house':>5} "
          f"{'amps':>4} {'frc':>3}")
    for sc in scenarios():
        for name, v in variants(sc):
            s = summarise(v, run(v))
            print(f"{sc.n} {sc.title:56} {name:16} {s['worst']/1000:8.2f} "
                  f"{s['over']:4d} {s['used']:8.1f} {s['low']:6.0f}% "
                  f"{s['car']:7.1f} {s['writes']:5d} {s['amps']:4d} {s['frc']:3d}")
        print()


def sweep() -> None:
    print("Energy horizon sweep (share + capacity): worst quarter-hour, kW")
    horizons = (600, 900, 1800, 2700, 3600, 5400)
    print(f"{'scenario':58} " + " ".join(f"{h//60:>5}m" for h in horizons))
    for sc in scenarios():
        cells = []
        for h in horizons:
            engine._PEAK_ENERGY_HORIZON_S = float(h)
            paced = replace(sc, cfg=replace(sc.cfg, battery_capacity_kwh=CAPACITY_KWH))
            cells.append(summarise(paced, run(paced))["worst"] / 1000.0)
        print(f"{sc.n} {sc.title:56} " + " ".join(f"{c:6.2f}" for c in cells))


if __name__ == "__main__":
    # The reports use φ and arrows; a Windows console defaults to cp1252.
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) > 1 and sys.argv[1] == "sweep":
        sweep()
    else:
        table()
