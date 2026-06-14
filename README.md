# go-e + SteVe Smart Charging (Home Assistant)

A HACS custom integration that turns Home Assistant into the **smart-charging brain**
for a [go-e](https://go-e.com) wallbox, while [SteVe](https://github.com/steve-community/steve)
runs alongside as the OCPP backend for authorization and billable metering.

HA regulates charge power **directly via the go-e local API** (reliable), and SteVe owns
*"may it charge / how much did it charge"*. They coexist because the go-e applies the
**minimum of all active current limits**. See [`docs/concept`](#concept) for the full design.

> **Status: Phase 3 (SteVe linkage).** All charging modes (solar, price-aware, combined),
> automatic phase switching and the Protect/Share/Assist battery policies are in place, plus
> SteVe metering (per-RFID kWh, sessions) and authorization/remote-control services. A custom
> Lovelace card follows in Phase 4.

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

The config flow has three steps:

1. **Energy sources** — grid power (required; + import / − export), optionally PV production,
   home-battery charge level and battery power, and an electricity-price sensor.
2. **go-e charger** — the current-control `number`, a "car connected" status entity, optionally
   charging status and charging power, plus grid voltage and phase count.
3. **SteVe (optional)** — base URL, an API user + its **API password** (set under *Users* in
   SteVe, not the login password), and an optional default charge box / connector for the
   remote start/stop services. Leave the URL blank to skip — the brain works without it.

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
| `sensor` Active session / Last session energy | SteVe transactions (when configured) |
| `sensor` `{tag} energy` (one per RFID) | Cumulative kWh charged per id-tag |

### SteVe services (when configured)

| Service | What it does |
|---------|--------------|
| `goe_steve.authorize_tag` / `block_tag` | Allow / block an RFID id-tag in SteVe |
| `goe_steve.remote_start` | Start a transaction (`id_tag`, optional `charge_box_id` / `connector_id`) |
| `goe_steve.remote_stop` | Stop a transaction (defaults to the single active session) |

> SteVe's REST API must be enabled and reachable; authentication is HTTP Basic using a web
> user's **API password**. Remote start/stop requires a SteVe build that exposes the
> `remote/start` · `remote/stop` endpoints.

## How it works

The decision logic lives in a pure, HA-free module
([`engine.py`](custom_components/goe_steve/engine.py)): given a snapshot of the world and the
current settings, it returns one decision (target current + phases + a human-readable reason).
The coordinator just reads HA states, calls the engine, and writes the result back — so the
strategy is fully unit-testable.

## Development

```bash
pip install pytest
pytest tests/     # engine + SteVe parsing; no Home Assistant install required
```

## Concept

The full theoretical design (architecture, energy-flow model, battery policies, all charging
modes, SteVe linkage, Lovelace card, roadmap) is documented in the project plan.

## Roadmap

- **Phase 1 ✅** MVP brain — solar-surplus + manual, Protect policy, safety.
- **Phase 2 ✅** PV+price, price-optimized, combined modes; departure deadlines; automatic phase
  switching; Share/Assist battery policies.
- **Phase 3 ✅** SteVe linkage — per-RFID kWh/transactions, authorization + remote start/stop
  services via the SteVe REST API.
- **Phase 4** Modern Lovelace card (live energy-flow + controls).
- **Phase 5** Forecast-aware planning & polish.
