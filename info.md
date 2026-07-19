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
- **Automatic 1↔3 phase switching** with anti-flap hysteresis and dwell timers.
- **Provider-agnostic price input** (Tibber, EPEX, Nordpool, EnergyZero, …).
- **SteVe metering & control:** per-RFID kWh, session sensors, and services to authorize/block
  tags and remote start/stop charging.
- **Two bundled Lovelace cards** — a *Smart Charging* card (a live **answer strip**: how much of
  the charge is solar/battery/grid right now, the brain's reason, chips for the battery-hold
  shield and price/dwell state, a plan strip with a draggable price target, and inline controls)
  and a *Price* card (electricity-price forecast with a draggable "cheap" threshold). Both are
  **auto-registered** on install: just add them from the dashboard card picker.

After installing, restart Home Assistant and add the integration via
*Settings → Devices & Services*.

> **Early-stage and actively tested** — it works on the author's setup but hasn't seen every
> wallbox/inverter/price-provider combo. Feedback is very welcome: please
> [open an issue](https://github.com/JustChr/HAgoe_steve/issues) with what worked or broke. 🙏
