"""Fifteen winter days at 15-minute resolution, against a 4 kW grid ceiling.

Same closed loop as the rest of this harness — the real ``engine.py`` decides, the
house model reacts, and the grid reading the engine sees on tick N is the consequence
of its own decision on tick N-1 — but run long enough, and recorded finely enough, to
answer the question a demand charge actually asks: *what was the worst quarter-hour?*

What is real (pulled from the recorder, see ``pull_winter.py``):
  * the household baseline — p25 of consumption per hour of day, 2037 winter hours
  * the PV days — real December days from the same pull, picked to span dark → bright
  * the prices  — the real EPEX total-price curve (0.22–0.42 €/kWh, cheapest ~13:00)
  * the battery — 30.5 kWh usable, 10.2 kW, both measured

What is modelled, because no measurement exists (the Nibe has no long-term statistics
before Aug 2026, and the sauna is not separately metered anywhere):
  * the heat pump — a compressor cycling on a duty curve driven by outside temperature
  * the sauna    — 8.7 kW, the figure Chris gave, on four of the fifteen evenings
  * the car      — a BMW i5 (79 kWh) plugged in overnight with a varying appetite

The decomposition is anchored to the measured total: baseline 20.8 + heat pump ~13 +
sauna ~4.6 kWh/day ≈ 38, against 36.4 kWh/day measured over 106 winter days.

Output: ``peak15_run.json`` — one record per quarter-hour (1440 of them), which is
both the billing unit and the chart's x-axis.
"""

from __future__ import annotations

import dataclasses
import json
import math
import pathlib
import random
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from peak_sim import (
    ChargerInputs, ChargingMode, EngineConfig, EngineState, House, decide, engine,
)

TZ = timezone(timedelta(hours=1))  # Vienna, winter
TICK_S = 30
DAYS = 15
SLOT_S = 900


def _data(name: str) -> pathlib.Path:
    return pathlib.Path(__file__).resolve().with_name(name)


# --- The ceiling ----------------------------------------------------------------------
# Chris's agreed connection capacity is 4 kW, so 4 kW is the line to defend. The soft
# tier starts easing 400 W below it and the hard tier cuts 200 W above — the same
# spacing his live settings use around 3.7 kW.
TARGET_W = 4000.0
SOFT_W = 3600.0
HARD_W = 4200.0


# --- Real data ------------------------------------------------------------------------

raw = json.load(open(_data("winter_raw.json")))
PRICE = json.load(open(_data("price_curve.json")))  # EUR/kWh by hour of day

# Household baseline: p25 of the three consumption phases per hour of day. The low
# quartile is the load that is there whatever else happens — fridge, standby, lights,
# ventilation, controls.
_cons, _n = defaultdict(float), defaultdict(int)
for _key in ("cons1", "cons2", "cons3"):
    for _p in raw[_key]:
        if _p.get("mean") is not None:
            _cons[_p["start"]] += _p["mean"]
            _n[_p["start"]] += 1
_byhod = defaultdict(list)
for _h, _v in _cons.items():
    if _n[_h] == 3:
        _byhod[datetime.fromtimestamp(_h / 1000, TZ).hour].append(_v)
_P25 = [sorted(_byhod[h])[len(_byhod[h]) // 4] for h in range(24)]  # W, 20.8 kWh/day

# The p25 curve is the measured *shape* of when this household draws power, but it is
# a whole-house figure — the heat pump's own base contribution is inside it. Charting
# the heat pump as its own series means taking it back out, so the curve is scaled to a
# plausible non-heat-pump household base and the pump is added back explicitly below.
# The sum is what gets calibrated, against the 36.4 kWh/day measured over 106 winter days.
NON_HP_BASE_KWH = 11.0
_scale = NON_HP_BASE_KWH / (sum(_P25) / 1000.0)
BASELINE = [w * _scale for w in _P25]  # W

# PV: real December days, ordered darkest → brightest.
_pv_by_day = defaultdict(dict)
for _p in raw["pv"]:
    if _p.get("mean") is not None:
        _d = datetime.fromtimestamp(_p["start"] / 1000, TZ)
        _pv_by_day[_d.strftime("%Y-%m-%d")][_d.hour] = _p["mean"]
_dec = {d: v for d, v in _pv_by_day.items() if d.startswith("2025-12") and len(v) >= 5}
PV_DAYS = sorted(_dec, key=lambda d: sum(_dec[d].values()))


def pv_profile(name: str) -> list[float]:
    """24 hourly means (W) for a real December day; hours it never reported are 0."""
    return [_dec[name].get(h, 0.0) for h in range(24)]


def _interp(curve: list[float], hour: float) -> float:
    """Hourly means read as a smooth curve — an hourly staircase would put artificial
    steps exactly on the boundaries the billing quarter-hour cares about."""
    x = (hour - 0.5) % 24.0
    lo = int(math.floor(x)) % 24
    frac = x - math.floor(x)
    return curve[lo] * (1.0 - frac) + curve[(lo + 1) % 24] * frac


# --- The fifteen days -------------------------------------------------------------------
# Deliberately a mixed fortnight rather than fifteen average days: a cold snap in the
# middle, a couple of bright days, sauna evenings, and the wallbox mode changing under
# the guard's feet. "Realistic, but arbitrary" — nothing here is a forecast of a
# particular December.

@dataclasses.dataclass
class Day:
    label: str
    pv_day: str          # which real December day supplies the PV
    outside_c: float     # drives the heat pump's duty cycle
    mode: ChargingMode
    car_kwh: float       # what the car wants overnight; 0 = not plugged in
    sauna: bool
    note: str
    # Sauna evenings are known in advance, so the battery is stocked up during the
    # day's cheap hours rather than met from the grid at 18:30. This is not a new
    # engine feature — it is the existing cheap-hour grid charge with its target
    # raised, which is what a person would actually do the morning of a sauna.
    prefill: bool = False


_pv = {  # darkest → brightest, by index into PV_DAYS
    "dark": PV_DAYS[0], "grey": PV_DAYS[len(PV_DAYS) // 4],
    "hazy": PV_DAYS[len(PV_DAYS) // 2], "bright": PV_DAYS[-2], "clear": PV_DAYS[-1],
}

SCHEDULE = [
    Day("Dec 1", _pv["grey"], 2.0, ChargingMode.SMART, 18.0, False, "ordinary damp day"),
    Day("Dec 2", _pv["dark"], -1.0, ChargingMode.SMART, 12.0, False, "dark and damp"),
    Day("Dec 3", _pv["hazy"], 1.0, ChargingMode.SOLAR_MIN, 22.0, False, "big charge wanted"),
    Day("Dec 4", _pv["bright"], 3.0, ChargingMode.SOLAR_MIN, 9.0, False, "sun at last"),
    Day("Dec 5", _pv["grey"], -3.0, ChargingMode.SMART, 0.0, False, "car away"),
    Day("Dec 6", _pv["dark"], -7.0, ChargingMode.SMART, 25.0, True,
        "cold snap begins — sauna, battery stocked up since midday", prefill=True),
    Day("Dec 7", _pv["dark"], -9.0, ChargingMode.SMART, 20.0, False, "coldest day"),
    Day("Dec 8", _pv["grey"], -8.0, ChargingMode.FAST, 24.0, False, "user forces Fast"),
    Day("Dec 9", _pv["hazy"], -4.0, ChargingMode.SMART, 14.0, False, "thaw"),
    Day("Dec 10", _pv["clear"], -2.0, ChargingMode.SOLAR, 10.0, False, "clear and cold"),
    Day("Dec 11", _pv["bright"], 1.0, ChargingMode.SOLAR, 8.0, False, "solar-only day"),
    Day("Dec 12", _pv["grey"], 4.0, ChargingMode.SMART, 16.0, False, "mild and grey"),
    Day("Dec 13", _pv["dark"], 2.0, ChargingMode.MANUAL, 20.0, True,
        "manual 16 A — second sauna of the fortnight, stocked up again", prefill=True),
    Day("Dec 14", _pv["hazy"], 0.0, ChargingMode.SMART, 15.0, False, "back to Smart"),
    Day("Dec 15", _pv["bright"], -2.0, ChargingMode.SMART, 12.0, False, "clearing up"),
]


# --- The loads that are modelled --------------------------------------------------------

def heat_pump_w(t: float, outside_c: float, rng: random.Random) -> float:
    """A Nibe cycling on demand: duty follows the cold, with a morning recovery boost.

    Calibrated on daily energy, not on gut feel: ~12 kWh at +4 °C, ~18 kWh around
    freezing, ~27 kWh at −9 °C. Together with the household base and the appliances that
    puts an ordinary day at ~36 kWh, which is the measured winter average. Below −8 °C
    the resistive backup joins the morning recovery.
    """
    hour = (t % 86400) / 3600.0
    duty = min(0.75, max(0.06, (16.0 - outside_c) / 75.0))
    if 5.0 <= hour < 9.0:
        duty = min(0.90, duty * 1.35)      # night setback recovery
    elif 0.0 <= hour < 5.0:
        duty *= 0.75                        # setback
    # A real compressor does not cycle in lockstep with the billing quarter-hour. Left
    # at a clean 1800 s the cycle aliases against the 15-minute window and every other
    # slot reads high — an artefact of the model, not a property of the house. Letting
    # the period wander removes it.
    period = 1800.0 * (1.0 + 0.22 * math.sin(t / 7300.0) + 0.08 * math.sin(t / 1900.0))
    if (t % period) >= period * duty:
        return 0.0
    power = 3100.0 + 350.0 * max(0.0, (5.0 - outside_c) / 10.0)  # colder → worse COP
    if outside_c <= -8.0 and 5.0 <= hour < 9.0:
        power += 3000.0                     # resistive backup
    return power


def sauna_w(t: float) -> float:
    """~13 kWh for an evening, which is how this sauna is actually used.

    8.7 kW is the element's real rating: flat out for the 45-minute heat-up, then
    thermostatic cycling averaging ~4 kW for the rest of the session. 6.5 + 7.0 kWh.
    The cycle period wanders for the same reason the heat pump's does — a clean
    divisor of 900 s would alias against the billing quarter-hour.
    """
    hour = (t % 86400) / 3600.0
    if not (18.5 <= hour < 21.0):
        return 0.0
    if hour < 19.25:
        return 8700.0                       # heat-up, flat out
    period = 520.0 * (1.0 + 0.30 * math.sin(t / 1100.0))
    return 8700.0 if ((t % period) < period * 0.46) else 0.0


def appliances_w(t: float, rng: random.Random) -> float:
    """Cooking, dishwasher, washing — the ordinary lumpy stuff on top of the baseline."""
    hour = (t % 86400) / 3600.0
    load = 0.0
    if 6.5 <= hour < 7.2:
        load += 1800.0                      # kettle, toaster, shower pump
    if 11.8 <= hour < 12.4:
        load += 900.0
    if 17.5 <= hour < 19.0:
        load += 1600.0                      # cooking
    if 19.5 <= hour < 20.2:
        load += 2000.0                      # dishwasher heat cycle
    if 9.0 <= hour < 10.5:
        load += 1200.0                      # washing machine
    return load


# --- Config -----------------------------------------------------------------------------

#: When the *Stock up for tonight* switch goes on and off on a sauna day. The engine
#: owns what stocking up means — fill at any price and hold what it bought; all the
#: scenario decides is when a person would flip the switch.
PREFILL_FROM_H, PREFILL_HOLD_TO_H = 9.0, 18.4
STOCK_UP_TARGET_SOC = 95.0

#: Ceiling-fill tuning: the readiness level the pack is kept at, and how hard to push.
#: ``peak_ready_soc`` is the engine's own field — deliberately *not* ``cheap_price``,
#: so the wallbox's price gate is untouched and the comparison isolates the battery.
FLAT_READY_SOC = 95.0
FLAT_POWER_W = 2500.0
#: How deep the guard may take the pack while shaving. 35 % is Chris's live setting;
#: ceiling-fill runs deeper, which costs nothing in energy and buys back the mornings.
PEAK_MIN_SOC = 35.0
FLAT_MIN_SOC = 20.0


def make_cfg(day: Day, session_want: float, hour: float = 0.0, *, guard: bool = True,
             follow_month: bool = True, flat: bool = False) -> EngineConfig:
    stocking = day.prefill and PREFILL_FROM_H <= hour < PREFILL_HOLD_TO_H
    return EngineConfig(
        mode=day.mode,
        smart_enabled=True,
        min_current_a=6.0,
        max_current_a=16.0,
        battery_reserve_soc=70.0,
        # The real curve's cheap third — the same in every variant. Readiness and
        # stocking up now have their own gates in the engine, so this stays where the
        # *wallbox* wants it and the comparison isolates the home battery.
        cheap_price=0.26,
        auto_phase=True,
        max_phases=3,
        manual_charge=True,                 # Manual day: the user asked for 16 A / 3φ
        manual_current_a=16.0,
        manual_phases=3,
        target_energy_kwh=session_want,
        peak_guard_enabled=guard,
        peak_soft_w=SOFT_W,
        peak_target_w=TARGET_W,
        peak_hard_w=HARD_W,
        peak_follow_month=follow_month,
        peak_month_buffer_w=200.0,
        shaving_reserve_soc=50.0,
        peak_min_soc=FLAT_MIN_SOC if flat else PEAK_MIN_SOC,
        grid_charge_enabled=True,
        grid_setpoint_w=50.0,
        # "6000" means "use all the headroom": the engine clamps the setpoint to
        # min(soft tier, remaining budget), so this is a cap, never a demand.
        cheap_charge_power_w=(FLAT_POWER_W if flat
                              else 6000.0 if stocking else 2500.0),
        bright_day_target_soc=40.0,
        dark_day_target_soc=80.0,
        pv_forecast_low_kwh=8.0,
        # The two new levers, doing the work the scenario used to fake by hand.
        peak_ready_soc=FLAT_READY_SOC if flat else 0.0,
        stock_up=stocking,
        stock_up_target_soc=STOCK_UP_TARGET_SOC,
        local_tz=TZ,
    )


# --- The run ------------------------------------------------------------------------------

def run(*, guard: bool = True, follow_month: bool = True, flat: bool = False) -> dict:
    rng = random.Random(20271201)
    state = EngineState()
    # 90 % round trip — the measured charge/discharge gap. It matters here because the
    # ceiling-fill strategy cycles the pack far harder than the others.
    house = House(soc=65.0, capacity_wh=30500.0, charge_eff=0.90,
                  max_discharge_w=10200.0, max_charge_w=10200.0)
    start = datetime(2027, 12, 1, 0, 0, tzinfo=TZ).astimezone(timezone.utc)

    setpoint: float | None = None
    min_soc: float | None = None
    hold = False
    car_w = 0.0
    delivered = 0.0
    session_want = SCHEDULE[0].car_kwh   # the run opens mid-session, at midnight
    last_phases = 3

    slots: list[dict] = []
    acc = _fresh_slot()
    slot_index = 0
    phase_flips = 0

    total_ticks = DAYS * 86400 // TICK_S
    for i in range(total_ticks):
        t = i * TICK_S
        now = start + timedelta(seconds=t)
        local = now.astimezone(TZ)
        day_i = int(t // 86400)
        day = SCHEDULE[day_i]
        hour = (t % 86400) / 3600.0

        # --- the world, before the engine sees it ------------------------------------
        pv_w = _interp(pv_profile(day.pv_day), hour)
        base_w = _interp(BASELINE, hour)
        hp_w = heat_pump_w(t, day.outside_c, rng)
        sauna = sauna_w(t) if day.sauna else 0.0
        appl_w = appliances_w(t, rng)
        house_w = base_w + hp_w + sauna + appl_w

        # The car is plugged in from 17:30 until it leaves at 07:00, and stops being a
        # load once it has what it wanted. The session straddles midnight, so its target
        # is anchored at plug-in — reading it off the calendar day would swap the goal
        # out from under a charge that is already half done.
        if hour >= 17.5 and hour < 17.5 + TICK_S / 3600.0:
            delivered = 0.0                  # fresh plug-in
            session_want = day.car_kwh
        want = session_want
        plugged = want > 0.0 and (hour >= 17.5 or hour < 7.0)
        if plugged and delivered >= want:
            plugged = False
        if not plugged:
            car_w = 0.0

        house.step(pv_w, house_w, car_w, setpoint_w=setpoint, min_soc=min_soc,
                   hold=hold, dt=TICK_S)

        # --- the engine ---------------------------------------------------------------
        dep = local.replace(hour=7, minute=0, second=0, microsecond=0)
        if local.hour >= 7:
            dep += timedelta(days=1)
        hour0 = local.replace(minute=0, second=0, microsecond=0)
        forecast = [
            engine.PriceSlot(
                start=(hour0 + timedelta(hours=k)).astimezone(timezone.utc),
                price=PRICE[(local.hour + k) % 24],
            )
            for k in range(26)
        ]
        # Tomorrow's yield, as a solar-forecast sensor would report it.
        nxt = SCHEDULE[min(day_i + 1, DAYS - 1)]
        pv_forecast = sum(pv_profile(nxt.pv_day)) / 1000.0

        c = dataclasses.replace(
            make_cfg(day, session_want, hour, guard=guard, follow_month=follow_month,
                     flat=flat),
            departure=dep.astimezone(timezone.utc))
        d = decide(ChargerInputs(
            car_connected=plugged,
            car_actual_power_w=car_w,
            phases=last_phases,
            voltage_v=230.0,
            grid_power_w=house.grid_w,
            pv_power_w=pv_w,
            battery_soc=house.soc,
            battery_power_w=house.battery_w,
            price_now=PRICE[local.hour],
            price_forecast=forecast,
            pv_forecast_kwh=pv_forecast,
            session_delivered_kwh=delivered,
            now=now,
        ), c, state)

        if d.house_control:
            setpoint, min_soc, hold = d.grid_setpoint_w, d.battery_min_soc, d.hold_battery
        if d.control:
            if d.should_charge and d.target_phases != last_phases:
                phase_flips += 1
                last_phases = d.target_phases
            car_w = (d.target_current_a * d.target_phases * 230.0) if d.should_charge else 0.0

        h = TICK_S / 3600.0
        delivered += car_w * h / 1000.0

        # --- accumulate the quarter-hour ----------------------------------------------
        acc["n"] += 1
        acc["grid"] += house.grid_w
        acc["pv"] += pv_w
        acc["base"] += base_w + appl_w
        acc["hp"] += hp_w
        acc["sauna"] += sauna
        acc["car"] += car_w
        acc["batt"] += house.battery_w
        acc["house"] += house_w
        acc["grid_max"] = max(acc["grid_max"], house.grid_w)
        acc["proj"] = max(acc["proj"], d.peak_projected_w)
        if d.peak_tier == "hard":
            acc["tier"] = "hard"
        elif d.peak_tier == "soft" and acc["tier"] != "hard":
            acc["tier"] = "soft"
        if d.grid_charging:
            acc["grid_charge_s"] += TICK_S
        if plugged and not d.should_charge:
            acc["paused_s"] += TICK_S

        if (t + TICK_S) % SLOT_S == 0:
            n = acc["n"]
            slot_end = now + timedelta(seconds=TICK_S)
            slots.append({
                "i": slot_index,
                "t": slot_end.astimezone(TZ).isoformat(),
                "day": day.label,
                "day_i": day_i,
                "mode": str(day.mode),
                "hour": round((slot_index % 96) * 0.25, 2),
                "grid_w": round(acc["grid"] / n, 1),
                "grid_max_w": round(acc["grid_max"], 1),
                "pv_w": round(acc["pv"] / n, 1),
                "base_w": round(acc["base"] / n, 1),
                "hp_w": round(acc["hp"] / n, 1),
                "sauna_w": round(acc["sauna"] / n, 1),
                "car_w": round(acc["car"] / n, 1),
                "house_w": round(acc["house"] / n, 1),
                "batt_w": round(acc["batt"] / n, 1),
                "soc": round(house.soc, 2),
                "price": round(PRICE[local.hour], 4),
                "tier": acc["tier"],
                "proj_w": round(acc["proj"], 1),
                "limit_w": round(d.peak_target_w, 1),
                "hard_w": round(d.peak_hard_w, 1),
                "month_peak_w": round(d.month_peak_w, 1),
                "grid_charging": acc["grid_charge_s"] > 0,
                "paused_s": acc["paused_s"],
                "reason": d.reason,
                "peak_reason": d.peak_reason,
            })
            slot_index += 1
            acc = _fresh_slot()

    return _summarise(slots, state, phase_flips, house)


def _fresh_slot() -> dict:
    return {"n": 0, "grid": 0.0, "pv": 0.0, "base": 0.0, "hp": 0.0, "sauna": 0.0,
            "car": 0.0, "batt": 0.0, "house": 0.0, "grid_max": 0.0, "proj": 0.0,
            "tier": "off", "grid_charge_s": 0, "paused_s": 0}


def _summarise(slots: list[dict], state: EngineState, flips: int, house: House) -> dict:
    days = []
    for d_i, day in enumerate(SCHEDULE):
        mine = [s for s in slots if s["day_i"] == d_i]
        imp = sum(max(0.0, s["grid_w"]) for s in mine) * 0.25 / 1000.0
        exp = sum(max(0.0, -s["grid_w"]) for s in mine) * 0.25 / 1000.0
        worst = max(mine, key=lambda s: s["grid_w"])
        days.append({
            "label": day.label, "mode": str(day.mode), "outside_c": day.outside_c,
            "note": day.note, "sauna": day.sauna, "car_want_kwh": day.car_kwh,
            "pv_kwh": round(sum(s["pv_w"] for s in mine) * 0.25 / 1000.0, 2),
            "house_kwh": round(sum(s["house_w"] for s in mine) * 0.25 / 1000.0, 2),
            "hp_kwh": round(sum(s["hp_w"] for s in mine) * 0.25 / 1000.0, 2),
            "car_kwh": round(sum(s["car_w"] for s in mine) * 0.25 / 1000.0, 2),
            "import_kwh": round(imp, 2), "export_kwh": round(exp, 2),
            "cost_eur": round(sum(max(0.0, s["grid_w"]) * 0.25 / 1000.0 * s["price"]
                                  for s in mine), 2),
            "peak_w": round(worst["grid_w"], 1), "peak_at": worst["t"][11:16],
            "peak_uncapped_w": round(max(s["house_w"] for s in mine), 1),
            "soc_min": round(min(s["soc"] for s in mine), 1),
            "soc_max": round(max(s["soc"] for s in mine), 1),
            "shaved_slots": sum(1 for s in mine if s["tier"] != "off"),
            "paused_min": round(sum(s["paused_s"] for s in mine) / 60.0, 1),
        })

    billed = max(s["grid_w"] for s in slots)
    return {
        "meta": {
            "days": DAYS, "slots": len(slots),
            "target_w": TARGET_W, "soft_w": SOFT_W, "hard_w": HARD_W,
            "battery_kwh": 30.5, "battery_kw": 10.2,
            "billed_peak_w": round(billed, 1),
            "billed_peak_at": max(slots, key=lambda s: s["grid_w"])["t"],
            "month_peak_w": round(state.month_peak_w, 1),
            "breaches": sum(1 for s in slots if s["grid_w"] > TARGET_W),
            "hard_breaches": sum(1 for s in slots if s["grid_w"] > HARD_W),
            "import_kwh": round(sum(max(0.0, s["grid_w"]) for s in slots) * 0.25 / 1000, 1),
            "export_kwh": round(sum(max(0.0, -s["grid_w"]) for s in slots) * 0.25 / 1000, 1),
            "car_kwh": round(sum(s["car_w"] for s in slots) * 0.25 / 1000, 1),
            "cost_eur": round(sum(max(0.0, s["grid_w"]) * 0.25 / 1000 * s["price"]
                                  for s in slots), 2),
            "phase_flips": flips,
            "shaved_slots": sum(1 for s in slots if s["tier"] != "off"),
            "soc_end": round(house.soc, 1),
        },
        "days": days,
        "slots": slots,
    }


def main() -> None:
    out = run(guard=True)                          # the integration as it ships
    base = run(guard=False)                        # peak protection switched off
    hold = run(guard=True, follow_month=False)     # defend 4 kW all month, come what may
    # …and the one that actually works: defend all month *and* keep the battery stocked
    # by importing on every hour that has headroom, price be damned.
    flat = run(guard=True, follow_month=False, flat=True)
    # Carry the other two traces along slot-for-slot so the chart can draw all three
    # without re-running anything.
    for s, b, h, f in zip(out["slots"], base["slots"], hold["slots"], flat["slots"]):
        s["grid_off_w"] = b["grid_w"]
        s["car_off_w"] = b["car_w"]
        s["soc_off"] = b["soc"]
        s["grid_hold_w"] = h["grid_w"]
        s["car_hold_w"] = h["car_w"]
        s["soc_hold"] = h["soc"]
        s["tier_hold"] = h["tier"]
        s["grid_flat_w"] = f["grid_w"]
        s["car_flat_w"] = f["car_w"]
        s["soc_flat"] = f["soc"]
    for d, bd, hd, fd in zip(out["days"], base["days"], hold["days"], flat["days"]):
        d["peak_off_w"] = bd["peak_w"]
        d["cost_off_eur"] = bd["cost_eur"]
        d["car_off_kwh"] = bd["car_kwh"]
        d["peak_hold_w"] = hd["peak_w"]
        d["cost_hold_eur"] = hd["cost_eur"]
        d["car_hold_kwh"] = hd["car_kwh"]
        d["shaved_hold"] = hd["shaved_slots"]
        d["peak_flat_w"] = fd["peak_w"]
        d["cost_flat_eur"] = fd["cost_eur"]
        d["car_flat_kwh"] = fd["car_kwh"]
        d["soc_flat_min"] = fd["soc_min"]
    out["baseline"] = base["meta"]
    out["hold"] = hold["meta"]
    out["flat"] = flat["meta"]

    path = _data("peak15_run.json")
    path.write_text(json.dumps(out), encoding="utf-8")
    m = out["meta"]
    print(f"baseline p25: {sum(BASELINE)/1000:.1f} kWh/day, peak {max(BASELINE):.0f} W")
    print(f"PV days available: {len(PV_DAYS)}  ({PV_DAYS[0]} … {PV_DAYS[-1]})")
    print(f"prices {min(PRICE):.3f}–{max(PRICE):.3f} EUR/kWh, cheapest {PRICE.index(min(PRICE))}:00\n")
    print(f"{'day':<7} {'mode':<10} {'°C':>4} {'PV':>5} {'house':>6} {'HP':>5} {'car':>5} "
          f"{'imp':>6} {'off':>6} {'ship':>6} {'hold':>6} {'FILL':>6} {'SoC':>9} {'shv':>4}")
    for d in out["days"]:
        print(f"{d['label']:<7} {d['mode']:<10} {d['outside_c']:>4.0f} {d['pv_kwh']:>5.1f} "
              f"{d['house_kwh']:>6.1f} {d['hp_kwh']:>5.1f} {d['car_kwh']:>5.1f} "
              f"{d['import_kwh']:>6.1f} {d['peak_off_w']/1000:>6.2f} "
              f"{d['peak_w']/1000:>6.2f} {d['peak_hold_w']/1000:>6.2f} "
              f"{d['peak_flat_w']/1000:>6.2f} "
              f"{d['soc_min']:>4.0f}-{d['soc_max']:<4.0f} {d['shaved_slots']:>4}")
    b, hl, fl = out["baseline"], out["hold"], out["flat"]
    print(f"\n{'':22}{'guard off':>12}{'as shipped':>12}{'hold 4 kW':>12}{'ceiling-fill':>14}")
    for name, key, scale, fmt in (
        ("worst quarter-hour kW", "billed_peak_w", 1000.0, "8.2f"),
        ("slots over 4.0 kW", "breaches", 1.0, "8.0f"),
        ("slots over 4.2 kW", "hard_breaches", 1.0, "8.0f"),
        ("import kWh", "import_kwh", 1.0, "8.1f"),
        ("car kWh", "car_kwh", 1.0, "8.1f"),
        ("energy cost EUR", "cost_eur", 1.0, "8.2f"),
        ("slots shaved", "shaved_slots", 1.0, "8.0f"),
    ):
        print(f"  {name:<22}"
              + "".join(f"{v[key]/scale:>{fmt}}    " for v in (b, m, hl))
              + f"{fl[key]/scale:>10.2f}")
    print(f"\nceiling {TARGET_W/1000:.1f} kW (soft {SOFT_W/1000:.1f}, hard {HARD_W/1000:.1f}) "
          f"| battery 30.5 kWh / 10.2 kW | worst slot as shipped at {m['billed_peak_at'][:16]}")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
