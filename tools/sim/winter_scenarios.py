"""Eight multi-day December scenarios about the home battery as an energy budget."""

from __future__ import annotations

import sys

from peak_sim import ChargingMode, EngineConfig
from winter import WINTER, WinterScenario, pv_day_kwh, report


def wcfg(**kw) -> EngineConfig:
    """A heat-pump house on the 2027 capacity tariff.

    The limits are set where a heat-pump home can actually hold them (4.5/5.0/5.5),
    not at the 3.3/3.7/3.9 defaults — W1 shows what happens when they aren't.
    """
    base = dict(
        mode=ChargingMode.SMART,
        smart_enabled=True,
        min_current_a=6.0,
        max_current_a=16.0,
        battery_reserve_soc=60.0,
        cheap_price=0.08,
        peak_guard_enabled=True,
        peak_soft_w=4500.0,
        peak_target_w=5000.0,
        peak_hard_w=5500.0,
        peak_follow_month=True,
        peak_month_buffer_w=200.0,
        shaving_reserve_soc=50.0,
        peak_min_soc=35.0,
        grid_setpoint_w=50.0,
        grid_charge_enabled=False,
        cheap_charge_power_w=2500.0,
        bright_day_target_soc=40.0,
        dark_day_target_soc=80.0,
        pv_forecast_low_kwh=8.0,
        local_tz=WINTER,
    )
    base.update(kw)
    return EngineConfig(**base)


GREY_WEEK = ["grey", "fog", "grey", "snow", "grey", "hazy", "grey"]
COLD = [-2.0, -5.0, -6.0, -9.0, -7.0, -3.0, 0.0]

W: list[WinterScenario] = []

# W1 ---------------------------------------------------------------------------------
W.append(WinterScenario(
    n="1",
    title="Grey December week, guard on, nothing refills the battery",
    story="Seven overcast/foggy days at −2 to −9 °C. Heat pump running most of the "
          "day, family at home in the evenings, EV wanting 10 kWh a night. "
          "Cheap-hour grid charging is OFF — the battery's only inflow is the sun.",
    expect="The battery is an energy budget with almost no income. Watch how many days "
           "it takes before the guard is permanently out of ammunition.",
    days=GREY_WEEK, outside_c=COLD, cfg=wcfg(), soc0=75.0,
))

# W2 ---------------------------------------------------------------------------------
W.append(WinterScenario(
    n="2",
    title="Same week, cheap-hour grid charging ON",
    story="Identical week, except the battery may buy energy at ≤8 ct in the overnight "
          "trough, filling to 80 % when tomorrow looks dark.",
    expect="This is the only forward-looking budgeting the integration has. Does one "
           "night's purchase actually carry the next evening's peak?",
    days=GREY_WEEK, outside_c=COLD, cfg=wcfg(grid_charge_enabled=True), soc0=75.0,
))

# W3 ---------------------------------------------------------------------------------
W.append(WinterScenario(
    n="3",
    title="The default limits (3.3/3.7/3.9 kW) in a heat-pump house",
    story="The same grey week with grid charging on, but the user left the peak limits "
          "at the shipped defaults.",
    expect="A 3.2 kW heat pump plus cooking cannot fit under 3.7 kW. The guard should "
           "spend the week engaged and the battery permanently at the floor.",
    days=GREY_WEEK, outside_c=COLD,
    cfg=wcfg(grid_charge_enabled=True, peak_soft_w=3300.0, peak_target_w=3700.0,
             peak_hard_w=3900.0),
    soc0=75.0,
))

# W4 ---------------------------------------------------------------------------------
W.append(WinterScenario(
    n="4",
    title="Cold snap — the backup heater comes on",
    story="Four days at −10 to −14 °C: the resistive backup heater joins the compressor, "
          "so the house alone draws over 9 kW in every heating cycle. Grid charging on.",
    expect="The load exceeds what a 4.5 kW inverter can substitute for. The battery is "
           "not the limiting factor here — the inverter is.",
    days=["fog", "snow", "grey", "grey"], outside_c=[-10.0, -14.0, -13.0, -11.0],
    cfg=wcfg(grid_charge_enabled=True), soc0=80.0,
))

# W5 ---------------------------------------------------------------------------------
W.append(WinterScenario(
    n="5",
    title="Bright cold spell — the sun does the budgeting",
    story="Five crisp, clear, very cold days. Good PV yield (for December) against a "
          "hard-working heat pump. Grid charging on.",
    expect="The bright-day target (40 %) should hand the refill job to the sun instead "
           "of buying it — and the sun should actually manage it.",
    days=["clear", "clear", "bright", "clear", "clear"],
    outside_c=[-6.0, -8.0, -7.0, -9.0, -5.0],
    cfg=wcfg(grid_charge_enabled=True), soc0=55.0,
))

# W6 ---------------------------------------------------------------------------------
W.append(WinterScenario(
    n="6",
    title="The forecast lies — 'bright tomorrow', then fog",
    story="Same clear spell as W5 for two days, then the forecast keeps promising a "
          "bright day that never arrives (forecast reports 3× the real yield).",
    expect="A wrong 'bright' forecast stops the overnight purchase at 40 %, so the "
           "battery goes into a dark evening half full. How badly does one wrong "
           "forecast hurt, and does it compound?",
    days=["clear", "bright", "fog", "snow", "fog", "grey"],
    outside_c=[-6.0, -7.0, -8.0, -9.0, -8.0, -5.0],
    cfg=wcfg(grid_charge_enabled=True), soc0=60.0, forecast_error=3.0,
))

# W7 ---------------------------------------------------------------------------------
W.append(WinterScenario(
    n="7",
    title="The car and the battery want the same cheap hours",
    story="Grey week, grid charging on, and the EV wants 14 kWh a night in Smart mode — "
          "which charges at full power in exactly the same ≤8 ct trough the battery is "
          "trying to buy into.",
    expect="Both loads land in the same three hours. Peak protection outranks grid "
           "charging absolutely, so something has to give — the question is what.",
    days=GREY_WEEK, outside_c=COLD, cfg=wcfg(grid_charge_enabled=True),
    soc0=70.0, car_need_kwh=14.0,
))

# W8 ---------------------------------------------------------------------------------
W.append(WinterScenario(
    n="8",
    title="A bigger battery (20 kWh) on the same grey week",
    story="W2 exactly, with the battery doubled to 20 kWh.",
    expect="Sizing check: how much of the problem is control and how much is simply "
           "not enough stored energy?",
    days=GREY_WEEK, outside_c=COLD, cfg=wcfg(grid_charge_enabled=True),
    soc0=75.0, capacity_wh=20000.0,
))


def main() -> None:
    only = set(sys.argv[1:])
    print("December yields for a 9.8 kWp array in this model:  " + ",  ".join(
        f"{k} {pv_day_kwh(k):.1f} kWh" for k in
        ("clear", "bright", "hazy", "grey", "fog", "snow")))
    for sc in W:
        if only and sc.n not in only:
            continue
        report(sc)


if __name__ == "__main__":
    main()
