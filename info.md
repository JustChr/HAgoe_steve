<p align="center">
  <img src="https://raw.githubusercontent.com/JustChr/HAgoe_steve/main/branding/logo-banner.png" alt="go-e + SteVe Smart Charging" width="480">
</p>

# go-e + SteVe Smart Charging

Turn Home Assistant into the **smart-charging brain** for a [go-e](https://go-e.com) wallbox,
with [SteVe](https://github.com/steve-community/steve) as the OCPP backend for authorization
and billable metering.

HA regulates charge power by talking to the go-e charger **directly over its native MQTT**
(no separate go-e integration needed); SteVe owns *"may it charge / how much did it charge"*. They coexist because the go-e applies the **minimum of all active current
limits**.

## Highlights

- **Charging modes:** Smart (solar first + cheap grid + a hard departure guarantee),
  Solar only, Solar + minimum, Fast, and Manual.
- **One home-battery rule:** *"Keep home battery above X %"* — below the line the battery
  comes first; at/above it it buffers surplus fluctuations for the car, and deliberate grid
  charging never drains it (100 % = always protect). An **Auto / Hold / Free** control lets you
  override the brain's discharge decision when you want to.
- **No more pointless export:** once the battery is comfortably charged (halfway between your
  reserve line and full), the whole-amp charging current rounds *up* rather than down — the
  last few hundred watts come from the nearly-full battery instead of going to the grid.
- **Peak protection for the 2027 capacity tariff:** grid operators will bill on the **highest
  15-minute average grid import** in the month, so one unlucky quarter-hour sets a charge that
  stands until the month ends. The brain measures the *billing* quarter-hour, projects where it
  is heading, and holds it under your target — easing the wallbox back and letting the home
  battery cover more of the house. A **household** layer: a sauna sets the peak whether or not
  a car is plugged in. **Off by default** (and off means exactly the old behaviour), while the
  measurement still runs so you can watch your peaks before switching it on. Once a month has
  already peaked higher, the limits float up to just under that peak — you get the headroom you
  have already paid for, without the record creeping up further.
- **Cheap-hour grid charging:** buy energy into the home battery while the price is low, deep
  when tomorrow looks dark and only shallow when it looks bright. Capped by the peak budget, so
  it imports steadily instead of in the spike that would set a monthly peak.
- **Cheapest hours first, then any hour:** a battery on its floor can't shave anything, and in
  a dark winter week the few cheap hours a day don't keep up. Set *Keep ready for peaks above*
  and it's topped up below that level whatever the price — a floor, not a cap, so cheap hours
  still fill deeper. Off by default.
- **Stock up for tonight:** you know tonight is the sauna; the brain doesn't. One switch fills
  the battery at any price *and holds it*, so the afternoon can't spend what the evening needs.
- **Fast on the knob, slow on the switches:** the charging current follows the solar surplus
  within seconds, while starting, stopping and phase switching wait for it to hold — and the
  card's countdown before a solar start is a button, so you can skip that wait.
- **Automatic 1↔3 phase switching** with anti-flap hysteresis, a confirmation window and
  dwell timers.
- **Provider-agnostic price input** (Tibber, EPEX, Nordpool, EnergyZero, …).
- **SteVe metering & control:** per-RFID kWh, session sensors, and services to authorize/block
  tags and remote start/stop charging.
- **Three bundled Lovelace cards** — a *Smart Charging* card (a live **answer strip**: how much
  of the charge is solar/battery/grid right now, the brain's reason, chips for the battery-hold
  shield and price/dwell state, a plan strip with a draggable price target, and inline controls),
  a *Price* card (electricity-price forecast with a draggable "cheap" threshold), and a *Peak
  protection* card (the month's billed peak, the live billing quarter-hour against your limits,
  what set the peak, and the settings inline). All are **auto-registered** on install: just add
  them from the dashboard card picker.

After installing, restart Home Assistant and add the integration via
*Settings → Devices & Services*.

> **Early-stage and actively tested** — it works on the author's setup but hasn't seen every
> wallbox/inverter/price-provider combo. Feedback is very welcome: please
> [open an issue](https://github.com/JustChr/HAgoe_steve/issues) with what worked or broke. 🙏
