<p align="center">
  <img src="branding/logo-banner.png" alt="go-e + SteVe Smart Charging" width="480">
</p>

# go-e + SteVe Smart Charging (Home Assistant)

A HACS custom integration that turns Home Assistant into the **smart-charging brain**
for a [go-e](https://go-e.com) wallbox, while [SteVe](https://github.com/steve-community/steve)
runs alongside as the OCPP backend for authorization and billable metering.

HA regulates charge power **directly via the go-e local API** (reliable), and SteVe owns
*"may it charge / how much did it charge"*. They coexist because the go-e applies the
**minimum of all active current limits**. See [`docs/concept`](#concept) for the full design.

> **Status: early days, actively tested.** All charging modes (solar, price-aware,
> combined), automatic phase switching and the single home-battery reserve line are in
> place, plus SteVe metering (per-RFID kWh, sessions), authorization/remote-control services, and
> **two bundled Lovelace cards** (energy-flow + price-forecast). It works on the author's own
> setup, but it's still young and not every wallbox/inverter/price-provider combination has been
> exercised yet. **Try it, and please [open an issue](https://github.com/JustChr/HAgoe_steve/issues)**
> with what worked, what broke, or what you'd like — feedback shapes where this goes next. 🙏

## What it does today

- Reads your existing HA entities (grid power, optional PV / home-battery SoC & power, price, go-e state).
- It reacts to grid/PV/battery power changes **within seconds** (event-driven, debounced), with a
  30 s poll as a safety net, computing a target charging current and writing it back to the go-e's
  current-control `number` entity (writes are throttled so it doesn't chase noise).
- **Modes:** Off (manual), Solar surplus only, Solar + minimum, Solar + cheap grid,
  Price-optimized (cheapest hours to a departure deadline), Combined, and Fast.
- **One home-battery rule — the reserve line:** a single *"Keep home battery above X %"*
  number. Below the line the battery comes first (all solar fills it); above the line the car
  comes first and the battery actively backs it down to the line. 100 % = the battery never
  powers the car.
- **Battery-hold for grid charging:** map an optional "stop discharge" switch (e.g. a Victron
  helper) and the brain flips it on while grid-charging with the battery at/below its reserve
  line — and always during cheap hours, when grid power is worth less than stored energy — so
  the car draws from the grid instead of draining your home battery. Solar surplus still
  charges the battery.
- **Mode-aware 1↔3 phase switching** with anti-flap hysteresis and dwell timers: power modes
  (Fast, cheap-grid, deadline charging) use the full phase count, while solar-surplus charging
  prefers a single phase so a small surplus still charges. Enable the **Auto phase** switch
  *and* map a go-e phase-control entity during setup — without a mapped phase entity there is
  nothing to switch.
- **Two Lovelace cards:** a main card with the live PV → house / battery / car / grid energy
  flow, the brain's plain-language reason, inline controls (charging mode, the home-battery
  reserve line, smart control, auto-phase, and the mode's own tunables like car target energy)
  and per-RFID energy; plus a price-forecast card that plots upcoming electricity prices with a
  **draggable "cheap" threshold** you set right on the chart.
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
   home-battery charge level and battery power, an electricity-price sensor, and an optional
   home-battery **hold switch** (turned on to stop the battery discharging while charging the car
   from the grid). The price forecast is auto-detected from the sensor (Nordpool, EPEX Spot,
   EnergyZero, Tibber, …) — leave the override blank unless detection fails.
2. **go-e charger** — the current-control `number`, a "car connected" status entity, optionally
   charging status and charging power, plus grid voltage and phase count.
3. **SteVe (optional)** — base URL, an API user + its **API password** (set under *Users* in
   SteVe, not the login password), and an optional default charge box / connector for the
   remote start/stop services. Leave the URL blank to skip — the brain works without it.

Everything can be re-mapped later via the integration's *Configure* (options) dialog.

## Dashboard cards

The integration ships **two** custom Lovelace cards and **registers them automatically** — no
manual dashboard *Resources* entry needed. After setup, edit a dashboard, *Add card*, and pick
them from the card picker (both show a preview). With one Smart Charging device they auto-discover
all entities; if you run more than one, pick the device in the card's visual editor.

**1. Smart Charging card** (`custom:goe-steve-card`) — the main card. A live energy-flow diagram
(PV → house / battery / car / grid), the brain's current reason and mode/reserve chips, inline
controls (charging mode, the home-battery reserve line, smart-control toggle, the active mode's
tunables) and per-RFID energy.

```yaml
type: custom:goe-steve-card
# device: <optional — auto-detected when there's only one>
# title: My Wallbox
# show_flow: true
# show_controls: true
# show_sessions: true
```

**2. Price card** (`custom:goe-steve-price-card`) — an electricity-price forecast chart with a
**draggable "cheap" threshold**: grab the handle and drop it to set the price at/below which grid
power counts as cheap (it writes straight to the *Cheap price* number, no YAML needed).

```yaml
type: custom:goe-steve-price-card
# device: <optional — auto-detected when there's only one>
# title: Electricity price
# hours: 48   # how many hours of forecast to show
```

Both cards are built from one TypeScript + Lit source tree in [`card/`](card/); the bundle is
committed to `custom_components/goe_steve/www/` and rebuilt with
`cd card && npm install && npm run build`.

## Entities created

| Entity | Purpose |
|--------|---------|
| `select` Charging mode | Off / Solar surplus / Solar+minimum / Solar+cheap-grid / Price-optimized / Combined / Fast |
| `switch` Smart control | Master enable — off = manual |
| `switch` Auto phase | Enable mode-aware 1↔3 phase switching (needs a mapped go-e phase entity) |
| `number` Min/Max current | Charge current bounds |
| `number` Keep home battery above | The reserve line (SoC %) — below it the battery comes first, above it it backs the car; 100 = never |
| `number` Car target energy | kWh to deliver by departure (Price / Combined) |
| `number` Minimum charge power | Floor for *Solar + minimum* |
| `number` Cheap price | At/below this price/kWh, grid counts as cheap |
| `sensor` Status | **Plain-language reason** for the current decision |
| `sensor` Surplus for car | Power available under the reserve line |
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

For a complete, situation-by-situation breakdown of **exactly what the brain does in each mode**
given the price, the home-battery state and the solar surplus, see the
[**Charging behavior matrix**](docs/charging-behavior-matrix.md).

## Development

```bash
pip install pytest
pytest tests/     # engine + SteVe parsing; no Home Assistant install required
```

## Concept

The full theoretical design (architecture, energy-flow model, the home-battery reserve line,
all charging modes, SteVe linkage, Lovelace card, roadmap) is documented in the project plan.

## Feedback

This is an early-stage project and feedback is hugely welcome — whether it works great or not.
Please [open an issue](https://github.com/JustChr/HAgoe_steve/issues) with your setup (wallbox,
inverter/battery, price provider), what you tried, and anything that surprised you. Bug reports,
"this mode did X when I expected Y", and feature ideas all help steer the roadmap.

## Roadmap

- **Phase 1 ✅** MVP brain — solar-surplus + manual, Protect policy, safety.
- **Phase 2 ✅** PV+price, price-optimized, combined modes; departure deadlines; automatic phase
  switching; Share/Assist battery policies.
- **Phase 3 ✅** SteVe linkage — per-RFID kWh/transactions, authorization + remote start/stop
  services via the SteVe REST API.
- **Phase 4 ✅** Modern Lovelace card — live energy-flow, reason, inline controls, per-RFID kWh.
- **Phase 5 🚧** Forecast-aware planning & polish — price-forecast card with a draggable cheap
  threshold and a battery-hold switch for grid charging are in; smarter forecast-based planning
  is next.
- **v2.0** The Protect/Share/Assist battery policies and their two thresholds collapsed into a
  single **home-battery reserve line** ("Keep home battery above X %"); existing settings are
  migrated automatically (see the
  [behavior matrix](docs/charging-behavior-matrix.md#migrating-from-v1-protect--share--assist)).
