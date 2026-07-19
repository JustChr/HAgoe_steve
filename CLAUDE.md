# CLAUDE.md — working in this repo

HACS custom integration (`goe_steve`) that makes Home Assistant the smart-charging brain
for a go-e wallbox, talking to the charger **directly over its native MQTT** (no third-party
go-e integration), with SteVe as the optional OCPP backend for authorization and per-RFID
metering. Two bundled Lovelace cards (TypeScript + Lit) live in `card/`.

## Architecture in one paragraph

The decision logic is a **pure, HA-free module**: `engine.py` takes a snapshot of the world
(grid/PV/battery power, prices, charger state) plus settings and returns one decision
(target current + phases + a human-readable reason). Independent *strategies* (solar
surplus, cheap grid, departure plan, minimum floor, full power) each bid a charging power;
an arbiter picks the highest bid (grid strategies win ties). The coordinator
(`coordinator.py`) reads HA states, calls the engine, and writes the result to the charger
over MQTT (`amp` / `frc` / `psm`). Never put decision logic in the coordinator or entity
platforms — it belongs in the engine so it stays unit-testable without HA.

## File map (`custom_components/goe_steve/`)

| File | Role |
|---|---|
| `engine.py` | **The brain.** Pure, HA-free. Strategies + arbiter, battery reserve-line model, start/stop dwell logic, departure planning, `compute_power_flow` / `compute_car_sources`. |
| `coordinator.py` | Glue: reads HA entities + go-e MQTT cache, calls engine, writes `amp`/`frc`/`psm`, throttles writes. Event-driven (debounced ~1.5 s) with a 30 s poll as safety net. Also `SteVeCoordinator` (60 s poll). |
| `goe_parse.py` | Pure, HA-free go-e MQTT decoding: topic split, JSON payloads, `nrg[11]` power, `car`→connected. Unit-tested. |
| `goe_mqtt.py` | HA MQTT client: subscribes `<base>/#`, caches, publishes `<base>/<key>/set`, broker discovery, `local_push` listeners. |
| `steve_api.py` | Pure, HA-free SteVe REST client (HTTP Basic). |
| `forecast.py` | Price-forecast parsing (Nordpool / EPEX / EnergyZero / Tibber-style attributes). |
| `config_flow.py` | 3-step flow: energy sources → go-e base topic (auto-discovered) → SteVe (optional). Options flow re-maps everything. |
| `__init__.py` | Setup, config-entry **migrations** (currently v4), card auto-registration (static path + `add_extra_js_url`). |
| `const.py` | Config keys, defaults, mode/strategy names. |
| `sensor.py`, `number.py`, `select.py`, `switch.py`, `binary_sensor.py`, `datetime.py` | Entity platforms — thin wrappers over coordinator data. Per-RFID energy sensors are created lazily as SteVe reports tags. |
| `services.py` / `services.yaml` | SteVe services: `authorize_tag`, `block_tag`, `set_tag_name`, `remote_start`, `remote_stop`. |
| `www/goe-steve-card.js` | **Committed build output** of `card/` — never edit by hand. |

Docs worth reading before touching behavior:
- `docs/charging-behavior-matrix.md` — situation-by-situation spec of what each mode does. Keep it in sync when changing engine behavior.
- `docs/mqtt-direct-concept.md` — the go-e MQTT key map and verified enum semantics.
- `BACKLOG.md` — phase history, open items, known follow-ups.

## Commands

```bash
# Python tests — pure modules only, no Home Assistant install needed
pip install pytest
pytest tests/

# Cards (TypeScript + Lit, bundled with esbuild)
cd card
npm install
npm run build      # → ../custom_components/goe_steve/www/goe-steve-card.js
npx tsc --noEmit   # type-check only
```

CI (`.github/workflows/validate.yml`): hassfest + HACS validation + pytest + card build
with a **stale-bundle check** — if you change anything under `card/src/`, you MUST run
`npm run build` and commit the regenerated `www/goe-steve-card.js`, or CI fails.

## Gotchas — read before coding

- **go-e base topic may start with a leading slash** (e.g. `/go-eCharger/222162`). It is
  configured verbatim and used verbatim for subscribe and publish. Never hard-code
  `go-eCharger/<serial>` or strip/add slashes.
- **`psm` is not a phase count.** `psm 1` = single phase, `psm 2` = three phases. The
  engine speaks in phase counts (1 or 3); the mapping `1→1, 3→2` (and back) is an explicit
  map, not an identity — keep it that way.
- **`frc`** is the start/stop channel: `0` neutral, `1` force-off, `2` force-on. Pausing
  is done via `frc`, never by writing current 0.
- **`nrg`** is a 16-element array; index 11 is total power in W. `wh` is session energy
  (resets at plug-in).
- **SteVe auth:** HTTP Basic with a web user's **API password** (set under *Users* in
  SteVe), not the login password. Endpoints under `/steve/api/v1`; blocked tag =
  `maxActiveTransactionCount` 0.
- **Config-entry migrations:** the entry is at version 4. Any change to stored config
  keys needs a migration step in `__init__.py` — users upgrade in place.
- **Entity discovery in the cards** goes by registry `translation_key` (entity_id suffix
  as fallback). If you add/rename entities, update `card/src/entities.ts` and both
  `strings.json` and `translations/` (EN + DE are maintained in parallel).
- **Safety invariant:** if the car isn't connected or required input data is stale, the
  brain must not write to the charger; with the *Smart control* switch off it is fully
  hands-off.

## Making a release

The version lives in `custom_components/goe_steve/manifest.json`. A release is complete
only when ALL of these are done:

1. Bump `manifest.json` version.
2. Commit with a message in the house style: `Release vX.Y.Z — <one-line human summary>`.
3. Tag `vX.Y.Z` and push commit + tag.
4. **Create the GitHub Release** with `gh release create vX.Y.Z --title ... --notes ...`
   — HACS users see release notes there; a bare git tag is not a release.

Update `README.md` / `info.md` / `docs/charging-behavior-matrix.md` when the release
changes user-visible behavior. README and info.md must tell the same story (info.md is
the short HACS-facing version).

## Style

- UX first: user-visible text (entity names, reasons, card labels, docs) is written in
  plain language, not jargon; the Status sensor's *reason* string is a feature, not debug
  output.
- Pure modules (`engine.py`, `goe_parse.py`, `steve_api.py`, `forecast.py`) must stay
  importable without Home Assistant — don't add `homeassistant` imports there.
- When requirements are unclear, define and discuss the behavior first (the behavior
  matrix is the place to spec it) rather than guessing.
