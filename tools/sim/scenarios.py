"""20 peak-protection scenarios, played through the real engine."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone

from peak_sim import (
    ChargingMode, EngineConfig, Scenario, broken_clouds, clear_summer, night,
    overcast_winter, pulses, run, spring_hazy, steady, steps,
)

WINTER = timezone(timedelta(hours=1))
SUMMER = timezone(timedelta(hours=2))


def cfg(**kw) -> EngineConfig:
    """House defaults: the Austrian-ish limits from the docs, guard on."""
    base = dict(
        mode=ChargingMode.SMART,
        smart_enabled=True,
        min_current_a=6.0,
        max_current_a=16.0,
        battery_reserve_soc=60.0,
        cheap_price=0.15,
        peak_guard_enabled=True,
        peak_soft_w=3300.0,
        peak_target_w=3700.0,
        peak_hard_w=3900.0,
        peak_follow_month=True,
        peak_month_buffer_w=200.0,
        shaving_reserve_soc=50.0,
        peak_min_soc=35.0,
        grid_setpoint_w=50.0,
        local_tz=WINTER,
    )
    base.update(kw)
    return EngineConfig(**base)


def at(tz, y, m, d, hh, mm) -> datetime:
    return datetime(y, m, d, hh, mm, tzinfo=tz).astimezone(timezone.utc)


S: list[Scenario] = []


# 1 --------------------------------------------------------------------------------
S.append(Scenario(
    n=1,
    title="Clear summer noon — the car runs on sunlight, the oven imports",
    story="9.8 kWp under a cloudless July sky, car charging on surplus. At +5 min "
          "the oven (3.5 kW) and the dishwasher come on, so the house briefly out-eats "
          "the array and the grid starts importing.",
    expect="The car is NOT trimmed: its power came from PV, and cutting it would only "
           "export the surplus, not reduce the import.",
    duration_s=1800,
    cfg=cfg(mode=ChargingMode.SOLAR, local_tz=SUMMER, battery_reserve_soc=50.0),
    pv=lambda t: clear_summer(t, 12.0),
    house=steps(600.0, (300, 4200.0), (1200, 700.0)),
    start=at(SUMMER, 2027, 7, 12, 12, 0),
    soc0=88.0,
))

# 2 --------------------------------------------------------------------------------
S.append(Scenario(
    n=2,
    title="Dark winter evening, Fast mode — the classic peak maker",
    story="18:00 in January. No sun, house at 900 W, battery at 55 %. The user plugs "
          "in and picks Fast: 16 A × 3φ = 11 kW straight off the grid.",
    expect="Projection blows past the hard line within seconds; the guard cuts to a "
           "current the budget can carry, and pauses when even 6 A doesn't fit.",
    duration_s=1800,
    cfg=cfg(mode=ChargingMode.FAST),
    pv=lambda t: 0.0,
    house=steady(900.0),
    start=at(WINTER, 2027, 1, 14, 18, 0),
    soc0=55.0,
))

# 3 --------------------------------------------------------------------------------
S.append(Scenario(
    n=3,
    title="Sauna, no car in the house at all",
    story="Saturday evening, 6 kW sauna heater plus 800 W of house. No car plugged in. "
          "Battery at 70 %.",
    expect="The wallbox is not a lever here — the home battery is. Min-SoC drops to the "
           "peak floor and the grid setpoint goes to 0 in the hard tier, so the battery "
           "carries the sauna.",
    duration_s=2700,
    cfg=cfg(mode=ChargingMode.SMART),
    pv=lambda t: 0.0,
    house=steps(800.0, (120, 6800.0)),
    start=at(WINTER, 2027, 2, 6, 19, 0),
    soc0=70.0,
    car_connected=lambda t: False,
))

# 4 --------------------------------------------------------------------------------
S.append(Scenario(
    n=4,
    title="Same sauna, but the battery is already flat",
    story="Identical to #3, except the home battery starts at 36 % — one point above "
          "the peak floor.",
    expect="Nothing left to shave with. The guard reports honestly ('battery is at its "
           "floor') instead of pretending, and the quarter-hour sets a new month peak.",
    duration_s=2700,
    cfg=cfg(mode=ChargingMode.SMART),
    pv=lambda t: 0.0,
    house=steps(800.0, (120, 6800.0)),
    start=at(WINTER, 2027, 2, 6, 19, 0),
    soc0=36.0,
    car_connected=lambda t: False,
))

# 5 --------------------------------------------------------------------------------
S.append(Scenario(
    n=5,
    title="Broken cumulus, Solar + minimum — the chatter test",
    story="Summer afternoon, cumulus clouds chopping the array every ~3 minutes. "
          "Solar + minimum keeps a 6 A floor topped up from the grid; house 1.2 kW "
          "with a 2.5 kW heat pump cycling.",
    expect="The rate limiter (cap falls freely, rises only after the dwell) plus the "
           "soft-tier confirm/release should keep the amps from flapping cloud-by-cloud.",
    duration_s=2700,
    cfg=cfg(mode=ChargingMode.SOLAR_MIN, min_current_a=8.0, local_tz=SUMMER,
            battery_reserve_soc=55.0),
    pv=lambda t: broken_clouds(t, 15.0),
    house=pulses(1200.0, 2500.0, 420.0, 900.0),
    start=at(SUMMER, 2027, 6, 20, 15, 0),
    soc0=62.0,
))

# 6 --------------------------------------------------------------------------------
S.append(Scenario(
    n=6,
    title="The month is already spoiled — 6.2 kW peak on the 3rd",
    story="Same dark-evening Fast charge as #2, but a heat-pump defrost during a cold "
          "snap already set a 6.2 kW quarter-hour earlier this month.",
    expect="Holding under 3.7 kW now saves nothing — the charge is booked. The allowance "
           "floats the limits up to just under the record, so the car charges much "
           "harder and the reason says why.",
    duration_s=1800,
    cfg=cfg(mode=ChargingMode.FAST),
    pv=lambda t: 0.0,
    house=steady(900.0),
    start=at(WINTER, 2027, 1, 14, 18, 0),
    soc0=55.0,
    seed_month_peak_w=6200.0,
))

# 7 --------------------------------------------------------------------------------
S.append(Scenario(
    n=7,
    title="Cheap night hour — grid charging the home battery under the ceiling",
    story="02:00, spot price 4 ct, battery at 30 %, tomorrow forecast 3 kWh (dark). "
          "Cheap-hour grid charging is on and wants 2 kW; the boiler cycles at 2.2 kW.",
    expect="On an ESS the setpoint IS total import, so the charge rate is capped by the "
           "live quarter-hour budget — a steady draw that collects cheap energy without "
           "buying a demand charge.",
    duration_s=2700,
    cfg=cfg(mode=ChargingMode.SMART, grid_charge_enabled=True,
            cheap_charge_power_w=2000.0, dark_day_target_soc=80.0),
    pv=lambda t: 0.0,
    house=pulses(400.0, 2200.0, 480.0, 900.0),
    start=at(WINTER, 2027, 1, 20, 2, 0),
    soc0=30.0,
    car_connected=lambda t: False,
    price=lambda t: 0.04,
    pv_forecast_kwh=3.0,
))

# 8 --------------------------------------------------------------------------------
S.append(Scenario(
    n=8,
    title="Late-window spike — 11 kW of cooking at minute 13 of 15",
    story="A quiet quarter-hour (600 W) until 13 minutes in, when 11 kW of cooking lands "
          "with only 2 minutes of window left. No car.",
    expect="Two minutes of 11 kW barely moves a 15-minute average, and the guard should "
           "not panic — but the 60 s floor on 'time remaining' keeps the last minute "
           "deliberately conservative rather than letting the budget diverge.",
    duration_s=1800,
    cfg=cfg(mode=ChargingMode.SMART),
    pv=lambda t: 0.0,
    house=steps(600.0, (780, 11000.0), (900, 600.0)),
    start=at(WINTER, 2027, 1, 22, 19, 0),
    soc0=75.0,
    car_connected=lambda t: False,
))

# 9 --------------------------------------------------------------------------------
S.append(Scenario(
    n=9,
    title="Early-window spike — the same 11 kW at minute 1",
    story="Identical load, 12 minutes earlier in the window.",
    expect="Now it matters: 11 kW held for 14 of 15 minutes would bill ~6 kW of import. Hard tier "
           "must engage on the spot (no confirmation delay) and the battery must carry it.",
    duration_s=1800,
    cfg=cfg(mode=ChargingMode.SMART),
    pv=lambda t: 0.0,
    house=steps(600.0, (60, 11000.0), (900, 600.0)),
    start=at(WINTER, 2027, 1, 22, 19, 0),
    soc0=75.0,
    car_connected=lambda t: False,
))

# 10 -------------------------------------------------------------------------------
S.append(Scenario(
    n=10,
    title="Window boundary — a fresh budget every quarter-hour",
    story="Fast charge starting at 18:07, i.e. 8 minutes into a window that is already "
          "half spent. Runs across the 18:15 boundary.",
    expect="The mid-window budget is tight and the car is throttled hard; at 18:15 the "
           "accumulator resets and the guard relaxes on its own — no clamp carries over.",
    duration_s=1500,
    cfg=cfg(mode=ChargingMode.FAST),
    pv=lambda t: 0.0,
    house=steady(1400.0),
    start=at(WINTER, 2027, 1, 14, 18, 7),
    soc0=48.0,
))

# 11 -------------------------------------------------------------------------------
S.append(Scenario(
    n=11,
    title="Grid meter drops out mid-charge",
    story="Fast charging with a 2 kW house when the grid power sensor goes unavailable "
          "for 4 minutes (Modbus hiccup), then comes back.",
    expect="The window keeps advancing on the held reading, is marked degraded, and the "
           "guard may tighten but never relax while blind. A degraded window must not "
           "set the month record.",
    duration_s=2400,
    cfg=cfg(mode=ChargingMode.FAST),
    pv=lambda t: 0.0,
    house=steady(2000.0),
    start=at(WINTER, 2027, 1, 14, 20, 0),
    soc0=65.0,
    blackout=(300.0, 540.0),
))

# 12 -------------------------------------------------------------------------------
S.append(Scenario(
    n=12,
    title="Smart control OFF — the go-e app is charging at 11 kW",
    story="The user turned Smart control off and started an 11 kW charge from the go-e "
          "app. Peak protection is still on. House 1 kW, no sun.",
    expect="The brain keeps its hands off the wallbox — until the projection crosses the "
           "hard line, which it answers to its own switch for. House levers stay managed "
           "throughout.",
    duration_s=1800,
    cfg=cfg(mode=ChargingMode.SMART, smart_enabled=False),
    pv=lambda t: 0.0,
    house=steady(1000.0),
    start=at(WINTER, 2027, 1, 14, 21, 0),
    soc0=60.0,
    external_car_w=lambda t: 11040.0,
))

# 13 -------------------------------------------------------------------------------
S.append(Scenario(
    n=13,
    title="Manual mode, passive window — just switched over, nothing touched",
    story="The user flips to Manual mid-session (charger doing 7 kW) and hasn't touched "
          "a control yet. A 4 kW workshop load starts at +3 min.",
    expect="The passive window suppresses charger writes only. The house levers still "
           "work, and a hard breach still pauses the car.",
    duration_s=1800,
    cfg=cfg(mode=ChargingMode.MANUAL, manual_passive=True, manual_charge=True,
            manual_current_a=10.0),
    pv=lambda t: 0.0,
    house=steps(700.0, (180, 4700.0)),
    start=at(WINTER, 2027, 1, 14, 17, 0),
    soc0=58.0,
    external_car_w=lambda t: 6900.0,
))

# 14 -------------------------------------------------------------------------------
S.append(Scenario(
    n=14,
    title="Overcast winter noon, Solar + minimum — the floor is the problem",
    story="900 W of weak PV at best, house 700 W, and Solar + minimum topping the car "
           "up to 6 A × 3φ = 4.1 kW from the grid.",
    expect="6 A × 3φ IS the hardware minimum — there is nothing to trim to. Soft can only "
           "watch; hard has to pause outright.",
    duration_s=2700,
    cfg=cfg(mode=ChargingMode.SOLAR_MIN, min_current_a=6.0, battery_reserve_soc=60.0),
    pv=lambda t: overcast_winter(t, 11.5),
    house=steady(700.0),
    start=at(WINTER, 2027, 12, 3, 11, 30),
    soc0=52.0,
))

# 15 -------------------------------------------------------------------------------
S.append(Scenario(
    n=15,
    title="Cheap hour, Smart mode, full home battery",
    story="Spot price 6 ct at 03:00 so Smart wants 11 kW from the grid. Battery is at "
          "92 % and the arbiter holds it (grid strategies hold the battery).",
    expect="The hold and the shave pull in opposite directions. Peak protection outranks "
           "the arbiter's hold — engaged, it releases the battery so it can carry the "
           "difference instead of the grid.",
    duration_s=2700,
    cfg=cfg(mode=ChargingMode.SMART, cheap_price=0.15),
    pv=lambda t: 0.0,
    house=steady(700.0),
    start=at(WINTER, 2027, 1, 27, 3, 0),
    soc0=92.0,
    price=lambda t: 0.06,
))

# 16 -------------------------------------------------------------------------------
S.append(Scenario(
    n=16,
    title="Spring haze, battery walks down to the peak floor",
    story="April, thin high cloud, PV wobbling around 3–5 kW. Fast charge plus a 3 kW "
          "house load. Battery starts at 44 % — below the shaving reserve already.",
    expect="Shaving releases the battery down to 35 %, and once it lands there the guard "
           "has to fall back on the wallbox alone.",
    duration_s=3600,
    cfg=cfg(mode=ChargingMode.FAST, local_tz=SUMMER),
    pv=lambda t: spring_hazy(t, 14.0),
    house=steady(3000.0),
    start=at(SUMMER, 2027, 4, 18, 14, 0),
    soc0=44.0,
    capacity_wh=7000.0,
))

# 17 -------------------------------------------------------------------------------
S.append(Scenario(
    n=17,
    title="Month rollover at local midnight",
    story="23:50 on 31 January with a 6.0 kW record on the books, running a 9 kW load "
          "(sauna + heat pump) across midnight into February.",
    expect="The record must roll on the *user's* calendar, not UTC. At 00:00 local the "
           "allowance vanishes and the configured limits snap back into force.",
    duration_s=1800,
    cfg=cfg(mode=ChargingMode.SMART),
    pv=lambda t: 0.0,
    house=steady(9000.0),
    start=at(WINTER, 2027, 1, 31, 23, 50),
    soc0=80.0,
    car_connected=lambda t: False,
    seed_month_peak_w=6000.0,
))

# 18 -------------------------------------------------------------------------------
S.append(Scenario(
    n=18,
    title="Heat-pump defrost bursts — soft tier in and out",
    story="Cold damp February morning. Defrost plus the resistive backup heater adds 8 kW "
          "for 4 minutes every 12 minutes on top of a 900 W house. No car.",
    expect="Each burst pushes the projection over the soft line; the 120 s confirm keeps "
           "the first moments from acting, and the release hold + dwell keep it from "
           "snapping back the instant the burst ends.",
    duration_s=3600,
    cfg=cfg(mode=ChargingMode.SMART),
    pv=lambda t: 0.0,
    house=pulses(900.0, 8000.0, 240.0, 720.0, first=120.0),
    start=at(WINTER, 2027, 2, 11, 7, 0),
    soc0=68.0,
    car_connected=lambda t: False,
))

# 19 -------------------------------------------------------------------------------
S.append(Scenario(
    n=19,
    title="User forced the battery to 'Hold' during a Fast charge",
    story="The card's three-way battery control is on Hold (never discharge into the "
          "car). Fast charge at 11 kW, house 1.5 kW, battery 75 %.",
    expect="Hold is a preference; a demand charge is money. Once the guard engages it "
           "takes the battery back (hold_source becomes 'peak') so the shave can happen "
           "at all.",
    duration_s=1800,
    cfg=cfg(mode=ChargingMode.FAST, battery_hold_mode="hold"),
    pv=lambda t: 0.0,
    house=steady(1500.0),
    start=at(WINTER, 2027, 1, 14, 19, 30),
    soc0=75.0,
))

# 20 -------------------------------------------------------------------------------
S.append(Scenario(
    n=20,
    title="Home Assistant restarts 7 minutes into a hot window",
    story="A 7 kW load has been running for 7 minutes when HA restarts. The engine comes "
          "up with no accumulator for this quarter-hour.",
    expect="It never shaves blind on a cold start: the window is degraded (7 minutes it "
           "cannot account for), it may tighten but not relax, and it must not let a "
           "guessed number become the month record.",
    duration_s=1800,
    cfg=cfg(mode=ChargingMode.SMART),
    pv=lambda t: 0.0,
    house=steady(7000.0),
    start=at(WINTER, 2027, 1, 9, 17, 7),
    soc0=72.0,
    car_connected=lambda t: False,
))


def main() -> None:
    only = {int(a) for a in sys.argv[1:] if a.isdigit()}
    rows = []
    for sc in S:
        if only and sc.n not in only:
            continue
        res = run(sc)
        print("=" * 100)
        print(f"SCENARIO {sc.n}: {sc.title}")
        print(f"  setting  : {sc.story}")
        print(f"  expected : {sc.expect}")
        print(f"  limits   : soft {sc.cfg.peak_soft_w/1000:.1f} / target "
              f"{sc.cfg.peak_target_w/1000:.1f} / hard {sc.cfg.peak_hard_w/1000:.1f} kW"
              + (f"   month record on the books: {sc.seed_month_peak_w/1000:.2f} kW"
                 if sc.seed_month_peak_w else ""))
        print("  --- what happened ---")
        for line in res.events[:34]:
            print(line)
        if len(res.events) > 34:
            print(f"  … {len(res.events) - 34} more transitions")
        if res.windows:
            print("  completed quarter-hours: " + ", ".join(
                f"{w[0]} → {w[1]/1000:.2f} kW" for w in res.windows))
        print(f"  month peak after  : {res.month_peak_w/1000:.2f} kW")
        print(f"  peak projection hi: {res.max_projected_w/1000:.2f} kW")
        print(f"  battery low-water : {res.min_soc_seen:.0f} %"
              f"   |  car took {res.car_kwh:.2f} kWh"
              f"   |  guard engaged {res.shaved_s/60:.0f} min"
              f"   |  car paused {res.paused_s/60:.0f} min")
        print(f"  write churn       : {res.tier_changes} tier changes, "
              f"{res.frc_writes} start/stop flips, {res.amp_writes} current changes, "
              f"{res.lever_writes} house-lever writes"
              f"   (over {sc.duration_s/60:.0f} min)")
        print(f"  charging reason   : {res.final_reason}")
        print(f"  peak reason       : {res.final_peak_reason}")
        rows.append((sc, res))

    print("=" * 100)
    print(f"{'#':>2}  {'scenario':<46} {'peak kW':>8} {'month kW':>9} "
          f"{'car kWh':>8} {'soc lo':>7} {'guard':>7}  churn (tier/frc/amp/lever)")
    for sc, res in rows:
        print(f"{sc.n:>2}  {sc.title[:46]:<46} {res.max_projected_w/1000:>8.2f} "
              f"{res.month_peak_w/1000:>9.2f} {res.car_kwh:>8.2f} "
              f"{res.min_soc_seen:>6.0f}% {res.shaved_s/60:>5.0f}m  "
              f"{res.tier_changes}/{res.frc_writes}/{res.amp_writes}/{res.lever_writes}")


if __name__ == "__main__":
    main()
