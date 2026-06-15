# go-e + SteVe Smart Charging (Home Assistant)

A HACS custom integration that turns Home Assistant into the **smart-charging brain**
for a [go-e](https://go-e.com) wallbox, while [SteVe](https://github.com/steve-community/steve)
runs alongside as the OCPP backend for authorization and billable metering.

HA regulates charge power **directly via the go-e local API** (reliable), and SteVe owns
*"may it charge / how much did it charge"*. They coexist because the go-e applies the
**minimum of all active current limits**. See [`docs/concept`](#concept) for the full design.

> **Status: v1.0 — first release.** All charging modes (solar, price-aware, combined),
> automatic phase switching and the Protect/Share/Assist battery policies are in place, plus
> SteVe metering (per-RFID kWh, sessions), authorization/remote-control services, and a bundled
> **Lovelace card** with a live energy-flow visualization and inline controls.

## What it does today

- Reads your existing HA entities (grid power, optional PV / home-battery SoC & power, price, go-e state).
- Every ~30 s it computes a target charging current and writes it back to the go-e's
  current-control `number` entity.
- **Modes:** Off (manual), Solar surplus only, Solar + minimum, Solar + cheap grid,
  Price-optimized (cheapest hours to a departure deadline), Combined, and Fast.
- **Battery policies:** Protect (home battery first, to a reserve SoC), Share (car may take what
  would charge the battery), Assist (battery may back the car down to a floor SoC).
- **Mode-aware 1↔3 phase switching** with anti-flap hysteresis and dwell timers: power modes
  (Fast, cheap-grid, deadline charging) use the full phase count, while solar-surplus charging
  prefers a single phase so a small surplus still charges. Enable the **Auto phase** switch
  *and* map a go-e phase-control entity during setup — without a mapped phase entity there is
  nothing to switch.
- **Lovelace card:** live PV → house / battery / car / grid energy flow, the brain's
  plain-language reason, inline controls (charging mode, battery policy, smart control,
  auto-phase, and the relevant battery level for the active mode — home reserve/floor SoC or
  car target energy), and per-RFID energy.
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

## Dashboard card

The integration ships a custom Lovelace card and **registers it automatically** — no manual
dashboard *Resources* entry needed. After setup, edit a dashboard, *Add card*, and pick
**go-e + SteVe Smart Charging** (it also appears in the card picker preview).

It shows a live energy-flow diagram (PV → house / battery / car / grid), the brain's current
reason and mode/policy chips, inline controls (charging mode, battery policy, smart-control
toggle), and per-RFID energy. With one Smart Charging device it auto-discovers all entities; if
you run more than one, pick the device in the card's visual editor.

```yaml
type: custom:goe-steve-card
# device: <optional — auto-detected when there's only one>
# title: My Wallbox
# show_flow: true
# show_controls: true
# show_sessions: true
```

The card source (TypeScript + Lit) lives in [`card/`](card/); the built bundle is committed to
`custom_components/goe_steve/www/` and rebuilt with `cd card && npm install && npm run build`.

## Entities created

| Entity | Purpose |
|--------|---------|
| `select` Charging mode | Off / Solar surplus / Solar+minimum / Solar+cheap-grid / Price-optimized / Combined / Fast |
| `select` Battery policy | Protect / Share / Assist |
| `switch` Smart control | Master enable — off = manual |
| `switch` Auto phase | Enable mode-aware 1↔3 phase switching (needs a mapped go-e phase entity) |
| `number` Min/Max current | Charge current bounds |
| `number` Home battery reserve | Protect threshold (SoC %) |
| `number` Home battery floor | Assist drain limit (SoC %) |
| `number` Car target energy | kWh to deliver by departure (Price / Combined) |
| `number` Minimum charge power | Floor for *Solar + minimum* |
| `number` Cheap price | At/below this price/kWh, grid counts as cheap |
| `sensor` Status | **Plain-language reason** for the current decision |
| `sensor` Surplus for car | Power available under the battery policy |
| `sensor` Target current | What the brain is asking for |
| `sensor` Power flow | Live PV/grid/battery/house/car balance (attributes) — drives the card |
| `binary_sensor` Brain controlling / Charging requested | Brain state |
| `sensor` Active session / Last session energy | SteVe transactions (when configured) |
| `sensor` `{tag} energy` (one per RFID) | Cumulative kWh charged per id-tag |

### SteVe services (when configured)

| Service | What it does |
|---------|--------------|
| `goe_steve.authorize_tag` / `block_tag` | Allow / block an RFID id-tag in SteVe |
| `goe_steve.set_tag_name` | Name an RFID id-tag (`id_tag`, `name`) — stored as its SteVe note and shown everywhere |
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
- **Phase 4 ✅** Modern Lovelace card — live energy-flow, reason, inline controls, per-RFID kWh.
- **Phase 5** Forecast-aware planning & polish.
