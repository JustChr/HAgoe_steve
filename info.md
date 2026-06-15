# go-e + SteVe Smart Charging

Turn Home Assistant into the **smart-charging brain** for a [go-e](https://go-e.com) wallbox,
with [SteVe](https://github.com/steve-community/steve) as the OCPP backend for authorization
and billable metering.

HA regulates charge power **directly via the go-e local API**; SteVe owns *"may it charge / how
much did it charge"*. They coexist because the go-e applies the **minimum of all active current
limits**.

## Highlights

- **Charging modes:** Off, Solar surplus, Solar + minimum, Solar + cheap grid, Price-optimized
  (cheapest hours to a departure deadline), Combined, and Fast.
- **Battery policies:** Protect (home battery first), Share, Assist (battery may back the car
  down to a floor SoC).
- **Automatic 1↔3 phase switching** with anti-flap hysteresis and dwell timers.
- **Provider-agnostic price input** (Tibber, EPEX, Nordpool, EnergyZero, …).
- **SteVe metering & control:** per-RFID kWh, session sensors, and services to authorize/block
  tags and remote start/stop charging.
- **Two bundled Lovelace cards** — a *Smart Charging* card (live energy-flow, plain-language
  reason, inline mode/policy/smart-control controls, per-RFID energy) and a *Price* card
  (electricity-price forecast with a draggable "cheap" threshold). Both are **auto-registered**
  on install: just add them from the dashboard card picker.

After installing, restart Home Assistant and add the integration via
*Settings → Devices & Services*.

> **Early-stage and actively tested** — it works on the author's setup but hasn't seen every
> wallbox/inverter/price-provider combo. Feedback is very welcome: please
> [open an issue](https://github.com/JustChr/HAgoe_steve/issues) with what worked or broke. 🙏
