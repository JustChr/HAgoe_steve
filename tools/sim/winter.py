"""Multi-day winter scenarios: does the home battery's energy last?

The 20 single-event scenarios ask whether the guard *reacts* correctly. These ask
whether it still has anything to react with on day three — the battery is a budget,
and in a December week the only inflows are a weak PV yield and whatever the
cheap-hour grid charge buys.

Same closed loop as peak_sim (the engine drives setpoint / min-SoC / hold, the ESS
obeys them), run at 30 s ticks over several days with a per-day report.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable

from peak_sim import (
    ChargerInputs, ChargingMode, EngineConfig, EngineState, House, decide, engine,
)

TICK_S = 30
WINTER = timezone(timedelta(hours=1))


# --- Weather: December in the eastern Alps -------------------------------------------

def _bell(hour: float, peak_w: float, centre: float = 12.2, width: float = 2.4) -> float:
    x = (hour - centre) / width
    return max(0.0, peak_w * math.exp(-x * x))


#: Day types, as (label, clear-sky fraction). A 9.8 kWp array in December peaks near
#: 4.2 kW on a crisp clear day and manages a few hundred watts under thick stratus.
DAY_TYPES = {
    "clear":     ("crisp and clear", 1.00),
    "bright":    ("bright, some haze", 0.72),
    "hazy":      ("high cloud", 0.42),
    "grey":      ("overcast", 0.16),
    "fog":       ("freezing fog, all day", 0.06),
    "snow":      ("snow on the panels", 0.02),
}


def pv_of(day_types: list[str]) -> Callable[[float], float]:
    """PV power (W) at ``t`` seconds from the scenario start (midnight of day 0)."""
    def f(t: float) -> float:
        day = int(t // 86400)
        hour = (t % 86400) / 3600.0
        kind = day_types[min(day, len(day_types) - 1)]
        return _bell(hour, 4200.0 * DAY_TYPES[kind][1])
    return f


def pv_day_kwh(kind: str) -> float:
    """Roughly what a day of that type yields — what a forecast sensor would report."""
    total = 0.0
    for step in range(0, 86400, 300):
        total += _bell(step / 3600.0, 4200.0 * DAY_TYPES[kind][1]) * 300 / 3600.0
    return total / 1000.0


# --- The house: a heat-pump home in December -----------------------------------------

@dataclass
class Weather:
    """Outside temperature drives the heat pump, which drives everything else."""
    outside_c: list[float]  # per day


def house_of(weather: Weather, *, occupied: Callable[[int], bool] = lambda d: True,
             backup_heater_below_c: float = -8.0) -> Callable[[float], float]:
    """Base load + occupancy peaks + a heat pump whose duty cycle follows the cold."""
    def f(t: float) -> float:
        day = min(int(t // 86400), len(weather.outside_c) - 1)
        hour = (t % 86400) / 3600.0
        temp = weather.outside_c[day]
        home = occupied(day)

        load = 300.0  # standby, fridge, router, ventilation
        if home:
            if 6.0 <= hour < 7.5:
                load += 1400.0          # showers, kettle, toaster
            if 11.5 <= hour < 12.5:
                load += 800.0           # lunch
            if 17.0 <= hour < 20.5:
                load += 1500.0          # cooking, lights, TV
            if 19.0 <= hour < 19.5:
                load += 1800.0          # dishwasher heat cycle

        # Heat pump: a 3.2 kW compressor cycling every half hour, duty rising as it
        # gets colder — ~20 kWh/day of electricity at −5 °C, which is what a decent
        # 150 m² house actually pulls. Below the bivalence point the resistive backup
        # joins in for the morning recovery only.
        duty = min(0.8, max(0.0, (15.0 - temp) / 60.0))
        if (t % 1800.0) < 1800.0 * duty:
            load += 3200.0
            if temp <= backup_heater_below_c and 4.0 <= hour < 10.0:
                load += 3000.0
        return load
    return f


# --- Prices: a day-ahead curve --------------------------------------------------------

def price_of(t: float) -> float:
    """EUR/kWh. Cheap overnight trough, morning and evening ramps."""
    hour = (t % 86400) / 3600.0
    if 0.0 <= hour < 5.0:
        return 0.045
    if 5.0 <= hour < 7.0:
        return 0.11
    if 7.0 <= hour < 10.0:
        return 0.28
    if 10.0 <= hour < 16.0:
        return 0.14
    if 16.0 <= hour < 21.0:
        return 0.32
    return 0.09


# --- Scenario -------------------------------------------------------------------------

@dataclass
class WinterScenario:
    n: str
    title: str
    story: str
    expect: str
    days: list[str]                       # day types
    outside_c: list[float]
    cfg: EngineConfig
    soc0: float = 60.0
    capacity_wh: float = 10000.0
    car_need_kwh: float = 10.0            # per night; 0 = no car
    car_plug_hour: float = 17.5
    car_unplug_hour: float = 7.0
    forecast_error: float = 1.0           # multiply the true next-day yield by this
    occupied: Callable[[int], bool] = lambda d: True
    start_day: int = 6
    # Experiment: in the hard tier, hold the grid at the remaining budget instead of 0.
    setpoint_is_budget: bool = False
    max_discharge_w: float = 4500.0
    max_charge_w: float = 4500.0


@dataclass
class DayReport:
    label: str
    kind: str
    outside_c: float
    pv_kwh: float = 0.0
    house_kwh: float = 0.0
    car_kwh: float = 0.0
    import_kwh: float = 0.0
    export_kwh: float = 0.0
    grid_charge_kwh: float = 0.0
    soc_start: float = 0.0
    soc_min: float = 100.0
    soc_max: float = 0.0
    floor_minutes: float = 0.0            # time spent pinned at the shaving floor
    guard_minutes: float = 0.0
    day_peak_w: float = 0.0
    day_peak_at: str = ""
    cost_eur: float = 0.0


def run_winter(sc: WinterScenario) -> tuple[list[DayReport], EngineState, dict]:
    state = EngineState()
    house = House(soc=sc.soc0, capacity_wh=sc.capacity_wh,
                  max_discharge_w=sc.max_discharge_w, max_charge_w=sc.max_charge_w)
    pv = pv_of(sc.days)
    load = house_of(Weather(sc.outside_c), occupied=sc.occupied)

    start = datetime(2027, 12, sc.start_day, 0, 0, tzinfo=WINTER).astimezone(timezone.utc)
    total_s = len(sc.days) * 86400

    reports = [
        DayReport(label=f"Dec {sc.start_day + d}", kind=sc.days[d],
                  outside_c=sc.outside_c[d])
        for d in range(len(sc.days))
    ]

    setpoint_w: float | None = None
    min_soc: float | None = None
    hold = False
    car_w = 0.0
    car_delivered = 0.0
    day_now = -1
    notes: dict = {"unprotected_evenings": [], "car_short_nights": []}

    for i in range(total_s // TICK_S):
        t = i * TICK_S
        now = start + timedelta(seconds=t)
        day = int(t // 86400)
        hour = (t % 86400) / 3600.0
        rep = reports[day]
        if day != day_now:
            day_now = day
            rep.soc_start = house.soc
            car_delivered = 0.0 if hour < sc.car_plug_hour else car_delivered

        pv_w = pv(t)
        house_w = load(t)

        # The car is plugged in over the night and leaves in the morning; once it has
        # what it needs it stops being a load (charge complete).
        plugged = sc.car_need_kwh > 0.0 and (
            hour >= sc.car_plug_hour or hour < sc.car_unplug_hour
        )
        if plugged and car_delivered >= sc.car_need_kwh:
            plugged = False
        if not plugged:
            car_w = 0.0

        house.step(pv_w, house_w, car_w, setpoint_w=setpoint_w, min_soc=min_soc,
                   hold=hold, dt=TICK_S)

        # Tomorrow's forecast, as a (possibly wrong) sensor would report it.
        tomorrow = sc.days[min(day + 1, len(sc.days) - 1)]
        forecast = pv_day_kwh(tomorrow) * sc.forecast_error

        inp = ChargerInputs(
            car_connected=plugged,
            car_actual_power_w=car_w,
            phases=3,
            voltage_v=230.0,
            grid_power_w=house.grid_w,
            pv_power_w=pv_w,
            battery_soc=house.soc,
            battery_power_w=house.battery_w,
            price_now=price_of(t),
            pv_forecast_kwh=forecast,
            session_delivered_kwh=car_delivered,
            now=now,
        )
        d = decide(inp, sc.cfg, state)

        if d.house_control:
            setpoint_w = d.grid_setpoint_w
            if sc.setpoint_is_budget and d.peak_tier == "hard":
                # The line we are defending is the target, not zero import. Letting the
                # grid supply everything up to the budget is free; making the battery
                # pay for it is what empties the budget before the day's worst window.
                setpoint_w = max(0.0, min(d.peak_allowed_w, d.peak_target_w))
            min_soc = d.battery_min_soc
            hold = d.hold_battery
        if d.control:
            car_w = (d.target_current_a * d.target_phases * 230.0
                     if d.should_charge else 0.0)
        elif plugged:
            car_w = car_w  # nobody is driving it; whatever it was doing continues

        # --- accounting ---------------------------------------------------------------
        h = TICK_S / 3600.0
        rep.pv_kwh += pv_w * h / 1000.0
        rep.house_kwh += house_w * h / 1000.0
        rep.car_kwh += car_w * h / 1000.0
        car_delivered += car_w * h / 1000.0
        if house.grid_w > 0:
            rep.import_kwh += house.grid_w * h / 1000.0
            rep.cost_eur += house.grid_w * h / 1000.0 * price_of(t)
        else:
            rep.export_kwh += -house.grid_w * h / 1000.0
        if d.grid_charging:
            rep.grid_charge_kwh += max(0.0, house.battery_w) * h / 1000.0
        rep.soc_min = min(rep.soc_min, house.soc)
        rep.soc_max = max(rep.soc_max, house.soc)
        if min_soc is not None and house.soc <= min_soc + 0.3:
            rep.floor_minutes += TICK_S / 60.0
        if d.peak_tier != "off":
            rep.guard_minutes += TICK_S / 60.0
        if d.peak_projected_w > rep.day_peak_w:
            rep.day_peak_w = d.peak_projected_w

        # An "unprotected evening": the guard wants to shave in the 17–21 block but the
        # battery is already at its floor, i.e. the budget ran out before the peak did.
        if (17.0 <= hour < 21.0 and d.peak_tier != "off"
                and house.soc <= (min_soc or 0.0) + 0.3):
            if rep.label not in notes["unprotected_evenings"]:
                notes["unprotected_evenings"].append(rep.label)

        if hour >= sc.car_unplug_hour and hour < sc.car_unplug_hour + 0.02:
            if sc.car_need_kwh and car_delivered < sc.car_need_kwh - 0.5:
                short = f"{rep.label} ({car_delivered:.1f}/{sc.car_need_kwh:.0f} kWh)"
                if short not in notes["car_short_nights"]:
                    notes["car_short_nights"].append(short)

    # The real billed number: the highest completed quarter-hour, per day.
    for stamp, avg in state.peak_history:
        pass  # history is capped at 96 windows; day peaks come from day_peak_w above
    return reports, state, notes


def report(sc: WinterScenario) -> None:
    reports, state, notes = run_winter(sc)
    print("=" * 108)
    print(f"WINTER {sc.n}: {sc.title}")
    print(f"  setting  : {sc.story}")
    print(f"  expected : {sc.expect}")
    print(f"  battery  : {sc.capacity_wh/1000:.0f} kWh, rest min-SoC "
          f"{sc.cfg.shaving_reserve_soc:.0f} %, shave floor {sc.cfg.peak_min_soc:.0f} % | "
          f"limits {sc.cfg.peak_soft_w/1000:.1f}/{sc.cfg.peak_target_w/1000:.1f}/"
          f"{sc.cfg.peak_hard_w/1000:.1f} kW | cheap-hour grid charge "
          f"{'ON' if sc.cfg.grid_charge_enabled else 'off'}")
    print(f"  {'day':<7} {'weather':<20} {'°C':>4} {'PV':>5} {'house':>6} {'car':>5} "
          f"{'import':>7} {'gridchg':>7} {'SoC 00h':>8} {'SoC min':>8} {'at floor':>9} "
          f"{'peak kW':>8} {'€':>6}")
    for r in reports:
        print(f"  {r.label:<7} {DAY_TYPES[r.kind][0]:<20} {r.outside_c:>4.0f} "
              f"{r.pv_kwh:>5.1f} {r.house_kwh:>6.1f} {r.car_kwh:>5.1f} "
              f"{r.import_kwh:>7.1f} {r.grid_charge_kwh:>7.1f} "
              f"{r.soc_start:>7.0f}% {r.soc_min:>7.0f}% {r.floor_minutes/60:>8.1f}h "
              f"{r.day_peak_w/1000:>8.2f} {r.cost_eur:>6.2f}")
    print(f"  month peak on the books: {state.month_peak_w/1000:.2f} kW"
          f"   |  total import {sum(r.import_kwh for r in reports):.1f} kWh"
          f"   |  total cost €{sum(r.cost_eur for r in reports):.2f}"
          f"   |  car got {sum(r.car_kwh for r in reports):.1f} kWh")
    if notes["unprotected_evenings"]:
        print("  ⚠ battery flat while the guard was trying to shave: "
              + ", ".join(notes["unprotected_evenings"]))
    if notes["car_short_nights"]:
        print("  ⚠ car left short: " + ", ".join(notes["car_short_nights"]))
