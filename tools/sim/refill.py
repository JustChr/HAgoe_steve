"""After the shave: how does the battery get back to its reserve, and at what cost?

A Victron ESS recharges from the grid at full power the moment its minimum SoC sits
above the battery's charge (live, Nov 2026). Up to v5.8 the engine raised the
minimum SoC from the shaving floor straight back to the reserve when a shave ended,
so the ESS bought the very peak the shave had avoided. The same happened when peak
protection took over a battery below the reserve, and while stocking up.

Run this file against two engines to compare: here, and in a worktree of the
release before (``git worktree add $TEMP/old v5.8.2``, copy ``tools/sim/peak_sim.py``
and this file across — the house model with the ESS recharge lives there).

House: Chris's measured system — 30.5 kWh usable, 10.2 kW inverter, 90 % round
trip; his live limits 2.5 / 3.7 / 3.9 kW, reserve 50 %, floor 35 %, resting
setpoint 100 W, month allowance on. The sauna is the measured one.

    python tools/sim/refill.py          # the table
    python tools/sim/refill.py log N    # the event log of scenario N
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone

import peak_sim
from peak_sim import ChargingMode, EngineConfig, Scenario, run
from heavy_load import sauna

WINTER = timezone(timedelta(hours=1))
CAPACITY_KWH = 30.5
RESERVE = 50.0


def cfg(**kw) -> EngineConfig:
    base = dict(
        mode=ChargingMode.SMART,
        smart_enabled=True,
        min_current_a=6.0,
        max_current_a=16.0,
        battery_reserve_soc=85.0,
        peak_guard_enabled=True,
        peak_soft_w=2500.0,
        peak_target_w=3700.0,
        peak_hard_w=3900.0,
        peak_follow_month=True,
        shaving_reserve_soc=RESERVE,
        peak_min_soc=35.0,
        grid_setpoint_w=100.0,
        battery_capacity_kwh=CAPACITY_KWH,
        local_tz=WINTER,
    )
    base.update(kw)
    return EngineConfig(**base)


def quiet(base_w: float = 1000.0):
    """Base load plus a heat pump: 1.5 kW for ~10 minutes, period wandering so it
    can't alias against the quarter-hour (see the harness's modelling traps)."""
    def f(t: float) -> float:
        period = 2230.0 + 400.0 * ((t // 2230.0) % 3)
        return base_w + (1500.0 if (t % period) < 600.0 else 0.0)
    return f


def sauna_evening(base_w: float = 1000.0):
    heat = sauna(start_s=600.0, base_w=0.0)
    pump = quiet(base_w)
    return lambda t: heat(t) + pump(t)


def scenarios() -> list[Scenario]:
    evening = datetime(2027, 1, 15, 18, 0, tzinfo=WINTER).astimezone(timezone.utc)
    noon = datetime(2027, 1, 15, 12, 0, tzinfo=WINTER).astimezone(timezone.utc)
    common = dict(
        pv=lambda t: 0.0,
        capacity_wh=CAPACITY_KWH * 1000.0,
        max_discharge_w=10200.0,
        max_charge_w=10200.0,
        charge_eff=0.90,
    )
    no_car = dict(car_connected=lambda t: False)
    return [
        Scenario(n=1, title="Sauna evening, no car, battery at 55 %", story="",
                 duration_s=6 * 3600, cfg=cfg(), house=sauna_evening(), soc0=55.0,
                 start=evening, **no_car, **common),
        Scenario(n=2, title="Sauna evening, car plugged in (Fast), battery at 55 %",
                 story="", duration_s=6 * 3600, cfg=cfg(mode=ChargingMode.FAST),
                 house=sauna_evening(), soc0=55.0, start=evening, **common),
        Scenario(n=3, title="Peak protection takes over a battery at 25 %, no car",
                 story="", duration_s=4 * 3600, cfg=cfg(), house=quiet(), soc0=25.0,
                 start=evening, **no_car, **common),
        Scenario(n=4, title="Takes over at 25 %, car plugged in (Fast)", story="",
                 duration_s=5 * 3600, cfg=cfg(mode=ChargingMode.FAST),
                 house=quiet(), soc0=25.0, start=evening, **common),
        Scenario(n=5, title="Stocking up for tonight from 60 % (grid charging on)",
                 story="", duration_s=6 * 3600,
                 cfg=cfg(grid_charge_enabled=True, stock_up=True,
                         stock_up_target_soc=95.0, cheap_charge_power_w=2000.0),
                 house=quiet(), soc0=60.0, start=noon, **no_car, **common),
    ]


def back_at_reserve_min(res) -> str:
    """Minutes from the battery's low point until it is back at the reserve."""
    low_t, low = min(res.soc_trace, key=lambda p: p[1])
    if low >= RESERVE:
        return "—"
    for t, soc in res.soc_trace:
        if t > low_t and soc >= RESERVE - 0.05:
            return f"{(t - low_t) / 60:.0f}"
    return "never"


def summarise(sc: Scenario, res) -> dict:
    target = sc.cfg.peak_target_w
    return dict(
        worst=max((w[1] for w in res.windows), default=0.0),
        over=sum(1 for w in res.windows if w[1] > target + 1.0),
        recharge=res.recharge_s / 60.0,
        low=res.min_soc_seen,
        final=res.final_soc,
        back=back_at_reserve_min(res),
        car=res.car_kwh,
        writes=res.lever_writes,
    )


def table() -> None:
    print(f"{'scenario':58} {'worst QH':>8} {'>tgt':>4} {'ESS rech':>8} "
          f"{'low':>5} {'end':>5} {'to 50%':>7} {'car kWh':>7} {'house':>5}")
    for sc in scenarios():
        s = summarise(sc, run(sc))
        print(f"{sc.n} {sc.title:56} {s['worst']/1000:8.2f} {s['over']:4d} "
              f"{s['recharge']:6.0f} m {s['low']:4.0f}% {s['final']:4.0f}% "
              f"{s['back']:>7} {s['car']:7.1f} {s['writes']:5d}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) > 2 and sys.argv[1] == "log":
        n = int(sys.argv[2])
        sc = next(s for s in scenarios() if s.n == n)
        res = run(sc)
        print("\n".join(res.events))
        print("\nquarter-hours:", " ".join(f"{w[0]} {w[1]/1000:.2f}" for w in res.windows))
    else:
        table()
