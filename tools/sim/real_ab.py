"""A/B the ceiling-aware planner against Chris's real winter baseline.

House load  : the p25-per-hour profile derived from his Victron consumption sensors
              (2037 winter hours, i.e. days with no car and no sauna).
PV          : a real dark December day from the same recorder pull.
Prices      : the real EPEX total-price curve, averaged per hour of day over 14 days.
Battery     : 30.5 kWh usable, 10.2 kW — both measured, not assumed.

"old" is the engine with peak_charge_ceiling_w() stubbed to None, which is exactly
the behaviour before the change.
"""

from __future__ import annotations

import pathlib


def _data(name: str) -> pathlib.Path:
    """Snapshots live beside the scripts, not in whatever cwd you launched from."""
    return pathlib.Path(__file__).resolve().with_name(name)


import json
import dataclasses
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from peak_sim import (
    ChargerInputs, ChargingMode, EngineConfig, EngineState, House, decide, engine,
)

TZ = timezone(timedelta(hours=1))
TICK_S = 30

raw = json.load(open(_data("winter_raw.json")))
PRICE = json.load(open(_data("price_curve.json")))

# --- the real baseline (p25 of house consumption per hour of day) --------------------
cons, n = defaultdict(float), defaultdict(int)
for key in ("cons1", "cons2", "cons3"):
    for p in raw[key]:
        if p.get("mean") is not None:
            cons[p["start"]] += p["mean"]
            n[p["start"]] += 1
byhod = defaultdict(list)
for h, v in cons.items():
    if n[h] == 3:
        byhod[datetime.fromtimestamp(h / 1000, TZ).hour].append(v / 1000)
BASELINE = [sorted(byhod[h])[len(byhod[h]) // 4] * 1000 for h in range(24)]  # W

# --- a real dark December day's PV ---------------------------------------------------
pv_by_day = defaultdict(dict)
for p in raw["pv"]:
    if p.get("mean") is not None:
        d = datetime.fromtimestamp(p["start"] / 1000, TZ)
        pv_by_day[d.strftime("%Y-%m-%d")][d.hour] = p["mean"]
# The sensor only reports while it is producing, so a December day has ~8 usable
# hours; the rest really are zero.
dark = min(
    (d for d, v in pv_by_day.items() if len(v) >= 6 and d.startswith("2025-12")),
    key=lambda d: sum(pv_by_day[d].values()),
)
PV = [pv_by_day[dark].get(h, 0.0) for h in range(24)]


def cfg_for(target_kw: float, **kw) -> EngineConfig:
    base = dict(
        mode=ChargingMode.SMART,
        smart_enabled=True,
        min_current_a=6.0,
        max_current_a=16.0,
        battery_reserve_soc=70.0,
        cheap_price=0.25,
        auto_phase=True,
        max_phases=3,
        peak_guard_enabled=True,
        peak_soft_w=target_kw * 1000 - 400,
        peak_target_w=target_kw * 1000,
        peak_hard_w=target_kw * 1000 + 200,
        peak_follow_month=True,
        peak_month_buffer_w=200.0,
        shaving_reserve_soc=50.0,
        peak_min_soc=35.0,
        grid_setpoint_w=50.0,
        target_energy_kwh=11.0,
        local_tz=TZ,
    )
    base.update(kw)
    return EngineConfig(**base)


def run(cfg: EngineConfig, days: int = 4, soc0: float = 70.0) -> dict:
    state = EngineState()
    house = House(soc=soc0, capacity_wh=30500.0,
                  max_discharge_w=10200.0, max_charge_w=10200.0)
    start = datetime(2027, 12, 6, 0, 0, tzinfo=TZ).astimezone(timezone.utc)
    setpoint = min_soc = None
    hold = False
    car_w = 0.0
    delivered = 0.0
    cost = car_kwh = imported = 0.0
    phase_flips = 0
    last_phases = None
    peak_hi = 0.0

    for i in range(days * 86400 // TICK_S):
        t = i * TICK_S
        now = start + timedelta(seconds=t)
        local = now.astimezone(TZ)
        hod = local.hour
        pv_w = PV[hod]
        house_w = BASELINE[hod]

        plugged = hod >= 18 or hod < 7
        if not plugged:
            car_w, delivered = 0.0, 0.0
        house.step(pv_w, house_w, car_w, setpoint_w=setpoint, min_soc=min_soc,
                   hold=hold, dt=TICK_S)

        # Departure at 07:00, 11 kWh wanted, real price curve as the forecast.
        dep = local.replace(hour=7, minute=0, second=0, microsecond=0)
        if local.hour >= 7:
            dep += timedelta(days=1)
        hour0 = local.replace(minute=0, second=0, microsecond=0)
        forecast = [
            engine.PriceSlot(start=(hour0 + timedelta(hours=k)).astimezone(timezone.utc),
                             price=PRICE[(hod + k) % 24])
            for k in range(26)
        ]
        c = dataclasses.replace(cfg, departure=dep.astimezone(timezone.utc))

        d = decide(ChargerInputs(
            car_connected=plugged, car_actual_power_w=car_w, phases=house_phases(last_phases),
            voltage_v=230.0, grid_power_w=house.grid_w, pv_power_w=pv_w,
            battery_soc=house.soc, battery_power_w=house.battery_w,
            price_now=PRICE[hod], price_forecast=forecast,
            session_delivered_kwh=delivered, now=now,
        ), c, state)

        if d.house_control:
            setpoint, min_soc, hold = d.grid_setpoint_w, d.battery_min_soc, d.hold_battery
        if d.control:
            new = (d.target_current_a * d.target_phases * 230.0) if d.should_charge else 0.0
            if d.should_charge and last_phases not in (None, d.target_phases):
                phase_flips += 1
            if d.should_charge:
                last_phases = d.target_phases
            car_w = new

        h = TICK_S / 3600.0
        delivered += car_w * h / 1000.0
        car_kwh += car_w * h / 1000.0
        if house.grid_w > 0:
            imported += house.grid_w * h / 1000.0
            cost += house.grid_w * h / 1000.0 * PRICE[hod]
        peak_hi = max(peak_hi, d.peak_projected_w)

    return dict(month_peak=state.month_peak_w / 1000, car_kwh=car_kwh,
                imported=imported, cost=cost, flips=phase_flips,
                soc=house.soc, worst_projection=peak_hi / 1000,
                windows=sorted((a for _, a in state.peak_history), reverse=True)[:3])


def house_phases(last):
    return last if last in (1, 3) else 3


def main() -> None:
    print(f"baseline (p25, W by hour): " + " ".join(f"{b:.0f}" for b in BASELINE))
    print(f"PV from the real dark day {dark}: {sum(PV)/1000:.1f} kWh")
    print(f"prices {min(PRICE):.3f}-{max(PRICE):.3f} EUR/kWh, cheapest at "
          f"{PRICE.index(min(PRICE))}:00\n")

    original = engine.peak_charge_ceiling_w
    for target in (3.7, 2.0):
        for label, stub in (("before (plan at full power)", True),
                            ("after  (plan under ceiling)", False)):
            engine.peak_charge_ceiling_w = (
                (lambda *a, **k: None) if stub else original
            )
            r = run(cfg_for(target))
            w = ", ".join(f"{x/1000:.2f}" for x in r["windows"])
            print(f"  target {target:.1f} kW  {label}:  month peak {r['month_peak']:5.2f} kW"
                  f"   car {r['car_kwh']:5.1f} kWh   import {r['imported']:5.1f} kWh"
                  f"   EUR {r['cost']:5.2f}   phase flips {r['flips']:>2}"
                  f"   worst windows {w}")
        print()
    engine.peak_charge_ceiling_w = original


if __name__ == "__main__":
    main()
