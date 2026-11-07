"""The reserve plan on a real autumn: does stocking for dark days pay, and what does it cost?

Three weeks of Chris's own house (15 Oct – 6 Nov 2026), closed loop, the real engine:

* **measured** hourly house load (grid + PV − battery − car), PV, and the Solcast
  forecasts *as they were issued* at the time (the "today" and "tomorrow" sensors'
  hourly states) — so the forecast's optimism on cloudy days is in the run, not
  idealised away;
* **modelled**: the sauna (8.7 kW, ~13 kWh an evening, the measured one) on four
  evenings — two dark, two bright — and the car on the nights it really charged,
  plugged in 18:00–07:00 in Fast with the energy it really took (capped at 40 kWh).
  Hourly means can't show a short spike; the sauna is what the limit is defended
  against here.

"Remaining today" isn't recorded, so it is reconstructed: the day's forecast spread
over the day in the shape of the PV that actually came.

Variants: the plan off (as shipped), the plan on (dark-day reserve 90 %, 10.5 kWh
self-use — Chris's median), and the plan without a forecast (a flat 90 %, i.e. the
old keep-ready with the hold) — the cost the forecast is there to avoid.

    python tools/sim/reserve_plan.py pull    # needs HA_URL + HA_TOKEN → autumn_raw.json
    python tools/sim/reserve_plan.py         # the table
"""

from __future__ import annotations

import dataclasses
import json
import math
import pathlib
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from peak_sim import ChargerInputs, ChargingMode, EngineConfig, EngineState, House, decide

TZ = ZoneInfo("Europe/Vienna")
START = datetime(2026, 10, 15, 0, 0, tzinfo=TZ)
DAYS = 23
TICK_S = 30
SLOT_S = 900
CAPACITY_KWH = 30.5
SELF_USE_KWH = 10.5
#: Sauna evenings: two after dark days, two after bright ones.
SAUNA_DAYS = {"2026-10-19", "2026-10-29", "2026-11-03", "2026-11-05"}
SAUNA_START_H = 18.5
CAR_CAP_KWH = 40.0
PRICE = 0.244628  # the flat tariff, EUR/kWh


def _data(name: str) -> pathlib.Path:
    return pathlib.Path(__file__).resolve().with_name(name)


# --- Data -------------------------------------------------------------------------------

P = "sensor.victron_mqtt_c0619ab4e653_"
IDS = {
    "grid": P + "grid_0_grid_power",
    "pv": "sensor.pv_leistung_gesamt",
    "batt": P + "system_0_system_dc_battery_power",
    "car": "sensor.smart_wallbox_charging_wallbox_leistung",
    "fc_today": "sensor.solcast_pv_forecast_prognose_heute",
    "fc_tomorrow": "sensor.solcast_pv_forecast_prognose_morgen",
}


def pull() -> None:
    import asyncio

    from ha_ws import connect, stats

    async def go(ha):
        start = (START - timedelta(days=1)).astimezone(timezone.utc).isoformat()
        end = (START + timedelta(days=DAYS + 1)).astimezone(timezone.utc).isoformat()
        r = await stats(ha, IDS.values(), start, end, "hour", ("mean", "state"))
        return {k: r.get(v, []) for k, v in IDS.items()}

    data = asyncio.run(connect(go))
    _data("autumn_raw.json").write_text(json.dumps(data))
    print({k: len(v) for k, v in data.items()})


@dataclasses.dataclass
class Hour:
    pv_w: float
    house_w: float
    car_w: float
    fc_today: float | None
    fc_tomorrow: float | None


def load() -> dict[datetime, Hour]:
    raw = json.loads(_data("autumn_raw.json").read_text())
    by = {k: {p["start"]: p for p in v} for k, v in raw.items()}
    hours: dict[datetime, Hour] = {}
    for ms, g in by["grid"].items():
        if g.get("mean") is None or by["batt"].get(ms, {}).get("mean") is None:
            continue
        pv = by["pv"].get(ms, {}).get("mean") or 0.0  # unreported at night
        car = by["car"].get(ms, {}).get("mean") or 0.0
        house = max(150.0, g["mean"] + pv - by["batt"][ms]["mean"] - car)
        t = datetime.fromtimestamp(ms / 1000, timezone.utc).astimezone(TZ)
        hours[t] = Hour(pv, house, car,
                        by["fc_today"].get(ms, {}).get("state"),
                        by["fc_tomorrow"].get(ms, {}).get("state"))
    return hours


# --- Model ------------------------------------------------------------------------------

def sauna_w(t_local: datetime, abs_s: float) -> float:
    if t_local.date().isoformat() not in SAUNA_DAYS:
        return 0.0
    s = (t_local.hour + t_local.minute / 60.0 - SAUNA_START_H) * 3600.0
    if s < 0 or s >= 2.5 * 3600:
        return 0.0
    if s < 45 * 60:
        return 8700.0
    period = 520.0 * (1.0 + 0.30 * math.sin(abs_s / 1100.0))
    return 8700.0 if (abs_s % period) < period * 0.46 else 0.0


def cfg_for(variant: str) -> EngineConfig:
    plan = variant != "off"
    return EngineConfig(
        mode=ChargingMode.FAST,
        smart_enabled=True,
        min_current_a=6.0,
        max_current_a=16.0,
        battery_reserve_soc=60.0,
        auto_phase=True,
        peak_guard_enabled=True,
        peak_soft_w=3500.0,
        peak_target_w=3700.0,
        peak_hard_w=3900.0,
        peak_follow_month=True,
        peak_month_buffer_w=200.0,
        shaving_reserve_soc=50.0,
        peak_min_soc=35.0,
        battery_capacity_kwh=CAPACITY_KWH,
        grid_setpoint_w=100.0,
        peak_ready_soc=90.0 if plan else 0.0,
        solar_self_use_kwh=SELF_USE_KWH,
        local_tz=TZ,
    )


def run(variant: str, hours: dict[datetime, Hour]) -> dict:
    state = EngineState()
    house = House(soc=50.0, capacity_wh=CAPACITY_KWH * 1000.0, charge_eff=0.90,
                  max_charge_w=10200.0, max_discharge_w=10200.0)
    cfg = cfg_for(variant)
    use_forecast = variant == "plan"

    # Per-day actual PV shape, for the reconstructed "remaining today".
    day_pv: dict[str, list[float]] = defaultdict(lambda: [0.0] * 24)
    for t, h in hours.items():
        day_pv[t.date().isoformat()][t.hour] = h.pv_w
    # The car's real appetite, booked to the night before the day it charged.
    car_day: dict[str, float] = defaultdict(float)
    for t, h in hours.items():
        car_day[t.date().isoformat()] += h.car_w / 1000.0

    setpoint = min_soc = None
    hold = False
    car_w = 0.0
    delivered = want = 0.0
    phases = 3
    slots: list[float] = []
    per_day: dict[str, list[float]] = defaultdict(list)
    acc = n = 0
    imp = exp = car_kwh = paused_h = bought_h = 0.0
    sauna_soc: list[tuple[str, float]] = []

    for i in range(DAYS * 86400 // TICK_S):
        abs_s = i * TICK_S
        now = START + timedelta(seconds=abs_s)
        hour0 = now.replace(minute=0, second=0, microsecond=0)
        h = hours.get(hour0)
        if h is None:
            continue
        nxt = hours.get(hour0 + timedelta(hours=1), h)
        frac = now.minute / 60.0 + now.second / 3600.0
        pv_w = h.pv_w * (1 - frac) + nxt.pv_w * frac
        base_w = h.house_w * (1 - frac) + nxt.house_w * frac
        sauna = sauna_w(now, abs_s)
        if sauna and now.hour == 18 and now.minute == 30 and now.second == 0:
            sauna_soc.append((now.date().isoformat(), house.soc))

        day = now.date().isoformat()
        local_h = now.hour + now.minute / 60.0
        if local_h == 18.0:
            delivered = 0.0
            tomorrow_day = (now + timedelta(days=1)).date().isoformat()
            want = min(CAR_CAP_KWH, car_day.get(tomorrow_day, 0.0))
        plugged = want > 1.0 and (local_h >= 18.0 or local_h < 7.0) and delivered < want
        if not plugged:
            car_w = 0.0

        house.step(pv_w, base_w + sauna, car_w, setpoint_w=setpoint, min_soc=min_soc,
                   hold=hold, dt=TICK_S)

        shape = day_pv[day]
        total = sum(shape) or 1.0
        rest = sum(shape[now.hour + 1:]) + shape[now.hour] * (1 - frac)
        fc_today = h.fc_today
        d = decide(ChargerInputs(
            car_connected=plugged,
            car_actual_power_w=car_w,
            phases=phases,
            grid_power_w=house.grid_w,
            pv_power_w=pv_w,
            battery_soc=house.soc,
            battery_power_w=house.battery_w,
            pv_forecast_kwh=h.fc_tomorrow if use_forecast else None,
            pv_forecast_today_kwh=fc_today if use_forecast else None,
            pv_forecast_remaining_kwh=(
                fc_today * rest / total if use_forecast and fc_today is not None
                else None
            ),
            sun_up=h.pv_w > 20.0,
            session_delivered_kwh=delivered,
            now=now.astimezone(timezone.utc),
        ), cfg, state)

        if d.house_control:
            setpoint, min_soc, hold = d.grid_setpoint_w, d.battery_min_soc, d.hold_battery
        if d.control:
            if d.should_charge:
                phases = d.target_phases
            car_w = d.target_current_a * d.target_phases * 230.0 if d.should_charge else 0.0
        dt_h = TICK_S / 3600.0
        delivered += car_w * dt_h / 1000.0
        car_kwh += car_w * dt_h / 1000.0
        imp += max(0.0, house.grid_w) * dt_h / 1000.0
        exp += max(0.0, -house.grid_w) * dt_h / 1000.0
        if plugged and not d.should_charge:
            paused_h += dt_h
        if d.battery_refilling:
            bought_h += dt_h
        acc += house.grid_w
        n += 1
        if (abs_s + TICK_S) % SLOT_S == 0:
            slots.append(acc / n)
            per_day[now.date().isoformat()].append(acc / n)
            acc = n = 0

    return {
        "worst_kw": max(slots) / 1000.0,
        "over_target": sum(1 for s in slots if s > 3700.0),
        "over_hard": sum(1 for s in slots if s > 3900.0),
        "import_kwh": imp, "export_kwh": exp, "car_kwh": car_kwh,
        "car_paused_h": paused_h, "refill_h": bought_h,
        "cost_eur": imp * PRICE,
        "sauna_soc": sauna_soc, "soc_end": house.soc,
        # The ESS's own full-power recharge (min SoC above the charge): must stay 0.
        "ess_recharge_min": house.recharge_s / 60.0,
        "month_peak_kw": state.month_peak_w / 1000.0,
        "per_day": per_day,
    }


def main() -> None:
    if sys.argv[1:] == ["pull"]:
        pull()
        return
    hours = load()
    results = {v: run(v, hours) for v in ("off", "plan", "flat")}
    names = {"off": "as shipped", "plan": "plan (forecast)", "flat": "flat 90 %"}
    print(f"{'':24}" + "".join(f"{names[v]:>17}" for v in results))
    rows = (
        ("worst quarter-hour kW", "worst_kw", "{:17.2f}"),
        ("quarter-hours > 3.7 kW", "over_target", "{:17d}"),
        ("quarter-hours > 3.9 kW", "over_hard", "{:17d}"),
        ("grid import kWh", "import_kwh", "{:17.0f}"),
        ("PV export kWh", "export_kwh", "{:17.1f}"),
        ("energy cost EUR", "cost_eur", "{:17.2f}"),
        ("car kWh", "car_kwh", "{:17.0f}"),
        ("car waiting h", "car_paused_h", "{:17.1f}"),
        ("battery refill h", "refill_h", "{:17.1f}"),
        ("SoC at the end %", "soc_end", "{:17.0f}"),
        ("ESS full-power recharge min", "ess_recharge_min", "{:17.1f}"),
    )
    for label, key, fmt in rows:
        print(f"  {label:<22}" + "".join(fmt.format(results[v][key]) for v in results))
    print("\n  worst quarter-hour per day, kW (quarter-hours over 3.7 kW):")
    for day in results["off"]["per_day"]:
        tag = "  sauna" if day in SAUNA_DAYS else "       "
        print(f"    {day}{tag}" + "".join(
            f"{max(results[v]['per_day'][day]) / 1000:10.2f} "
            f"({sum(1 for w in results[v]['per_day'][day] if w > 3700):2d})"
            for v in results))
    print("\n  SoC when the sauna starts:")
    for k, (day, _soc) in enumerate(results["off"]["sauna_soc"]):
        print(f"    {day}  " + "".join(
            f"{results[v]['sauna_soc'][k][1]:15.0f} %" for v in results))


if __name__ == "__main__":
    main()
