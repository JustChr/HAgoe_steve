"""Pull the real winter from Chris's Home Assistant and describe it in numbers."""

from __future__ import annotations

import pathlib


def _data(name: str) -> pathlib.Path:
    """Snapshots live beside the scripts, not in whatever cwd you launched from."""
    return pathlib.Path(__file__).resolve().with_name(name)


import asyncio
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from ha_ws import connect, stats

TZ = timezone(timedelta(hours=1))
P = "sensor.victron_mqtt_c0619ab4e653_"
IDS = {
    "grid": P + "grid_0_grid_power",
    "pv": "sensor.pv_leistung_gesamt",
    "soc": P + "system_0_system_dc_battery_soc",
    "batt": P + "system_0_system_dc_battery_power",
    "cons1": P + "system_0_system_consumption_power_l1",
    "cons2": P + "system_0_system_consumption_power_l2",
    "cons3": P + "system_0_system_consumption_power_l3",
    "nibe": "sensor.nibe_heat_pump_leistungsaufnahme",
    "price": "sensor.epex_spot_data_total_price",
    "car": "sensor.smart_wallbox_charging_wallbox_leistung",
    "gridfwd": P + "grid_0_grid_energy_forward",
    "gridrev": P + "grid_0_grid_energy_reverse",
}
START = "2025-11-15T00:00:00+00:00"
END = "2026-03-01T00:00:00+00:00"


async def go(ha):
    r = await stats(ha, IDS.values(), START, END, "hour",
                    ("mean", "min", "max", "sum"))
    out = {k: r.get(v, []) for k, v in IDS.items()}
    json.dump(out, open(_data("winter_raw.json"), "w"))
    return out


def day_of(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, TZ).strftime("%Y-%m-%d")


def main() -> None:
    data = asyncio.run(connect(go))
    print("hourly points pulled: " + ", ".join(
        f"{k}={len(v)}" for k, v in data.items()))

    by = {k: {p["start"]: p for p in v} for k, v in data.items()}
    hours = sorted(by["grid"])

    days: dict[str, dict] = defaultdict(lambda: {
        "imp": 0.0, "exp": 0.0, "pv": 0.0, "cons": 0.0, "nibe": 0.0, "car": 0.0,
        "soc_lo": 100.0, "soc_hi": 0.0, "gridmax": 0.0, "battmin": 0.0,
        "n": 0, "price_sum": 0.0, "price_n": 0,
    })
    for h in hours:
        d = days[day_of(h)]
        g = by["grid"].get(h, {})
        gm = g.get("mean")
        if gm is not None:
            d["imp"] += max(0.0, gm) / 1000.0
            d["exp"] += max(0.0, -gm) / 1000.0
        if g.get("max") is not None:
            d["gridmax"] = max(d["gridmax"], g["max"])
        pv = by["pv"].get(h, {}).get("mean")
        if pv is not None:
            d["pv"] += pv / 1000.0
        cons = sum((by[f"cons{i}"].get(h, {}).get("mean") or 0.0) for i in (1, 2, 3))
        d["cons"] += cons / 1000.0
        nb = by["nibe"].get(h, {}).get("mean")
        if nb is not None:
            d["nibe"] += nb / 1000.0
        cw = by["car"].get(h, {}).get("mean")
        if cw is not None:
            d["car"] += cw / 1000.0
        s = by["soc"].get(h, {})
        if s.get("min") is not None:
            d["soc_lo"] = min(d["soc_lo"], s["min"])
            d["soc_hi"] = max(d["soc_hi"], s["max"])
        b = by["batt"].get(h, {})
        if b.get("min") is not None:
            d["battmin"] = min(d["battmin"], b["min"])
        pr = by["price"].get(h, {}).get("mean")
        if pr is not None:
            d["price_sum"] += pr
            d["price_n"] += 1
        d["n"] += 1

    full = {k: v for k, v in days.items() if v["n"] >= 23}
    print(f"\ncomplete days: {len(full)}  ({min(full)} … {max(full)})\n")

    worst = sorted(full.items(), key=lambda kv: -kv[1]["gridmax"])[:12]
    print("--- the 12 days with the highest instantaneous grid import ---")
    print(f"{'day':<12}{'import':>7}{'export':>7}{'PV':>6}{'house':>7}{'heatpump':>9}"
          f"{'car':>6}{'SoC lo-hi':>11}{'peak kW':>9}{'max disch':>10}{'ct/kWh':>8}")
    for name, d in worst:
        pr = d["price_sum"] / d["price_n"] * 100 if d["price_n"] else 0
        print(f"{name:<12}{d['imp']:>7.1f}{d['exp']:>7.1f}{d['pv']:>6.1f}{d['cons']:>7.1f}"
              f"{d['nibe']:>9.1f}{d['car']:>6.1f}"
              f"{d['soc_lo']:>5.0f}-{d['soc_hi']:<5.0f}{d['gridmax']/1000:>9.2f}"
              f"{-d['battmin']/1000:>10.2f}{pr:>8.1f}")

    tot = lambda k: sum(v[k] for v in full.values())
    n = len(full)
    print(f"\n--- the whole period, {n} complete days ---")
    print(f"  grid import   {tot('imp'):8.0f} kWh   ({tot('imp')/n:5.1f} kWh/day)")
    print(f"  grid export   {tot('exp'):8.0f} kWh   ({tot('exp')/n:5.1f} kWh/day)")
    print(f"  PV            {tot('pv'):8.0f} kWh   ({tot('pv')/n:5.1f} kWh/day)")
    print(f"  house load    {tot('cons'):8.0f} kWh   ({tot('cons')/n:5.1f} kWh/day)")
    print(f"  heat pump     {tot('nibe'):8.0f} kWh   ({tot('nibe')/n:5.1f} kWh/day)")
    print(f"  car           {tot('car'):8.0f} kWh   ({tot('car')/n:5.1f} kWh/day)")
    print(f"  highest instantaneous grid import seen: "
          f"{max(v['gridmax'] for v in full.values())/1000:.2f} kW")
    print(f"  deepest battery discharge seen:        "
          f"{-min(v['battmin'] for v in full.values())/1000:.2f} kW")

    # Days sorted by PV — the dark stretch is what the budget has to survive.
    dark = sorted(full.items(), key=lambda kv: kv[1]["pv"])[:10]
    print("\n--- the 10 darkest days ---")
    for name, d in dark:
        print(f"  {name}  PV {d['pv']:5.1f} kWh   import {d['imp']:5.1f}   "
              f"house {d['cons']:5.1f}   SoC {d['soc_lo']:.0f}-{d['soc_hi']:.0f} %   "
              f"peak {d['gridmax']/1000:.2f} kW")

    json.dump({k: dict(v) for k, v in full.items()}, open(_data("winter_days.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
