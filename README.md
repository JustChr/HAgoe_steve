# go-e + SteVe Smart Charging (Home Assistant)

A HACS custom integration that turns Home Assistant into the **smart-charging brain**
for a [go-e](https://go-e.com) wallbox, while [SteVe](https://github.com/steve-community/steve)
runs alongside as the OCPP backend for authorization and billable metering.

HA regulates charge power **directly via the go-e local API** (reliable), and SteVe owns
*"may it charge / how much did it charge"*. They coexist because the go-e applies the
**minimum of all active current limits**. See [`docs/concept`](#concept) for the full design.

> **Status: Phase 1 (MVP brain).** Solar-surplus and manual charging with a battery-first
> ("Protect") policy. Price-based modes, automatic phase switching, the Share/Assist battery
> policies, SteVe linkage, and a custom Lovelace card follow in later phases.

## What it does today

- Reads your existing HA entities (grid power, optional PV / home-battery SoC & power, go-e state).
- Every ~30 s it computes a target charging current and writes it back to the go-e's
  current-control `number` entity.
- **Modes:** Off (manual), Solar surplus only, Solar + minimum, Fast.
- **Battery policy (Protect):** the car waits until the home battery reaches a configurable
  reserve SoC, so the house battery fills first.
- Safety: if the car isn't connected or required data is stale, the brain keeps its hands off;
  turning **Smart control** off returns full manual control.

## Installation

1. In HACS → *Integrations* → custom repository, add this repo (category: *Integration*).
2. Install **go-e + SteVe Smart Charging**, restart Home Assistant.
3. *Settings → Devices & Services → Add Integration →* search for it.

You need the go-e charger already available in HA (e.g. via
[`ha-goecharger-api2`](https://github.com/marq24/ha-goecharger-api2) or
[`openkfw/smartenergy.goecharger`](https://github.com/openkfw/smartenergy.goecharger)) exposing a
writable current `number` entity.

## Setup

The config flow has two steps:

1. **Energy sources** — grid power (required; + import / − export), optionally PV production,
   home-battery charge level and battery power.
2. **go-e charger** — the current-control `number`, a "car connected" status entity, optionally
   charging status and charging power, plus grid voltage and phase count.

Everything can be re-mapped later via the integration's *Configure* (options) dialog.

## Entities created

| Entity | Purpose |
|--------|---------|
| `select` Charging mode | Off / Solar surplus / Solar+minimum / Fast |
| `switch` Smart control | Master enable — off = manual |
| `number` Min/Max current | Charge current bounds |
| `number` Home battery reserve | Protect threshold (SoC %) |
| `number` Minimum charge power | Floor for *Solar + minimum* |
| `sensor` Status | **Plain-language reason** for the current decision |
| `sensor` Surplus for car | Power available under the battery policy |
| `sensor` Target current | What the brain is asking for |
| `binary_sensor` Brain controlling / Charging requested | Brain state |

## How it works

The decision logic lives in a pure, HA-free module
([`engine.py`](custom_components/goe_steve/engine.py)): given a snapshot of the world and the
current settings, it returns one decision (target current + phases + a human-readable reason).
The coordinator just reads HA states, calls the engine, and writes the result back — so the
strategy is fully unit-testable.

## Development

```bash
pip install pytest
pytest tests/test_engine.py     # no Home Assistant install required
```

## Concept

The full theoretical design (architecture, energy-flow model, battery policies, all charging
modes, SteVe linkage, Lovelace card, roadmap) is documented in the project plan.

## Roadmap

- **Phase 1 ✅** MVP brain — solar-surplus + manual, Protect policy, safety.
- **Phase 2** PV+price, price-optimized, combined modes; departure deadlines; automatic phase
  switching; Share/Assist battery policies.
- **Phase 3** SteVe linkage — per-RFID kWh/transactions + authorization management via the API.
- **Phase 4** Modern Lovelace card (live energy-flow + controls).
- **Phase 5** Forecast-aware planning & polish.
