# Backlog

Tracks work beyond the current state. The full design rationale lives in the approved
concept document; this file is the actionable to-do list.

## Status
- **Phase 1 — MVP brain ✅ (done, on `main`)**
  Pure engine + coordinator + config flow + entities (select/switch/number/sensor/binary_sensor),
  EN/DE translations, 12 passing engine tests. Modes: Off / Solar surplus / Solar+minimum / Fast;
  battery **Protect** policy.

## Phase 2 — Smart modes ✅ (done, on `main`)
- [x] `PV + price` mode: solar normally, full/high power when price < configurable threshold.
- [x] `Price-optimized` mode: cheapest-hours charging to a target energy by a departure deadline
      (greedy re-planned each cycle from the forecast).
- [x] `Combined` mode: surplus + opportunistic cheap-grid + deadline, respecting battery policy.
- [x] Departure `datetime` + target-energy `number` entities.
- [x] Provider-agnostic price input wiring (config: price entity + forecast attribute; tolerant
      parsing of Nordpool/EPEX/EnergyZero-style `raw_today`/`raw_tomorrow` lists).
- [x] **Automatic 1↔3 phase switching** with hysteresis + dwell timer (avoid contactor flapping).
      Engine computes `target_phases`; coordinator writes a mapped phase `number`/`select`.
- [x] Battery policies **Share** and **Assist** (Assist = battery may discharge into the car,
      down to a floor SoC). Battery-policy `select`, battery-floor-SoC + cheap-price-threshold
      `number`s, auto-phase `switch`.
- [x] Input smoothing: rolling average on PV/grid, deadband, min update interval, min on/off dwell.

  Follow-ups worth revisiting: Assist sizing is coarse (lifts availability to max current rather
  than tracking real battery discharge headroom); price planning does not yet subtract energy
  already delivered (no car-SoC signal); deadline planning assumes hourly-ish forecast slots.

## Phase 3 — SteVe linkage (via SteVe API) ✅ (done, on `main`)
- [x] Read transactions/kWh → sensors (last session, active transaction, **per-RFID/user energy**).
      Per-RFID surfaced as one energy sensor per discovered id-tag (created lazily as SteVe
      reports tags), with blocked/in-transaction/expiry as attributes.
- [x] Manage authorization: services `authorize_tag` / `block_tag` (read-modify-write on the tag's
      `maxActiveTransactionCount`), plus `remote_start` / `remote_stop`.
- [x] Config: SteVe connection (optional 3rd config step; URL + Basic-auth API user/password +
      default charge box/connector). HA-free `steve_api.py` client; slow (60 s) `SteVeCoordinator`.

  Follow-ups worth revisiting: the tag PUT sends a minimal body (idTag/parent/note/maxActive) —
  if a SteVe build requires `expiryDate`, extend it. Per-tag energy recomputes from all returned
  transactions each poll (fine for home use; revisit if SteVe history is large/pruned). Remote
  start/stop endpoint/payload assumes a recent SteVe (PR #1291/#1949); verify against the
  instance's OpenAPI (`/manager/v3/api-docs`).

## Phase 4 — Lovelace card ✅ (done, on `main`)
- [x] Modern custom card (TypeScript + Lit): live energy-flow visualization
      (PV → house/battery/car/grid), active mode + battery policy with plain-language reason,
      inline controls, per-RFID kWh.
- [x] Source in `card/` (esbuild bundle), built output committed to `custom_components/goe_steve/www/`.
- [x] **Auto-registered** by the integration (static path + `add_extra_js_url`) — no manual
      dashboard resource. Self-contained data source: a `power_flow` sensor exposes the live
      PV/grid/battery/house/car balance as attributes (derived by pure `compute_power_flow`).
- [x] Visual config editor with a device selector; auto-discovers entities for a single device.

  Follow-ups worth revisiting: the flow diagram assumes the standard 5-node layout; very large
  installs (multiple cars) aren't modelled. Entity discovery prefers the registry
  `translation_key` with an entity_id-suffix fallback. Card i18n is currently EN-only (it does
  localize select-option labels via the integration's translations).

## Phase 5 — Polish & forecasting
- [x] Event-driven regulation: re-evaluate surplus the moment grid/PV/battery power changes,
      not just on the 30 s poll (debounced refresh; writes still throttled; poll kept as a
      safety net for time-based triggers). (v1.0.1)
- [x] **v2.0 — the home-battery reserve line.** Protect/Share/Assist and the reserve+floor pair
      collapsed into one number ("Keep home battery above X %"): below it the battery comes
      first (car gets no solar surplus), above it the battery actively backs the car down to
      the line; cheap grid always holds regardless. Config entry v1→v2 migration maps the old
      policy (protect→100, share→old reserve, assist→old floor) and removes the orphaned
      entities. Intentionally dropped: Share's middle ground (intercept battery-bound solar
      without ever discharging) — raise the line instead.
- [x] **v3.0 — strategies + arbiter engine (green-field redesign).** The 7-mode if/else
      ladder replaced by independent strategies (surplus / cheap grid / departure plan /
      minimum floor / full power) that each bid a charging power; the highest bid wins, grid
      strategies take ties. Modes collapse to five presets (Smart / Solar only / Solar+minimum
      / Fast / Manual) with automatic migration of restored legacy values. Battery model:
      below the reserve the battery comes first (genuine excess only, zero discharge
      tolerance); at/above it it *buffers* — the car follows a 2-min time-smoothed surplus,
      dips are bridged, sustained discharge (>300 W >3 min) eases the car off; every
      deliberate grid charge engages the hold switch. Start/stop: 3-min surplus confirmation,
      5-min ride-out at min current, no ride-out for grid slots. Deadline plan now subtracts
      delivered session energy (anchored at plug-in), uses achievable phases for slot
      capacity, and hard-guarantees the target (urgency fallback without a forecast).
      Time-based smoothing replaces `SMOOTHING_SAMPLES` (the follow-up below). `min_grid_floor`
      removed (floor = min current); dead `goe_charging` config input dropped from the flow.
- [x] **v4.0 — card redesign + exposing the brain's hidden state.** The five-node flow diagram
      is replaced outright by an *answer strip*: a hero (live kW + a ring/source bar splitting the
      car's power into solar/battery/grid, from a new `compute_car_sources` + `sources` attribute),
      a one-line balance, the reason, and chips for state the engine computed but never showed —
      the **battery-hold shield** (new `binary_sensor.battery_hold` + `hold_battery`/`hold_source`
      on status), the price verdict, live dwell countdowns (new `resume/pause_not_before`,
      `phase_locked_until`) and the phase count. A **plan strip** surfaces the booked cheap windows
      (new `plan` attribute; `_deadline_now` refactored into a reusable `_compute_plan`) with a
      draggable price target writing `number.cheap_price`. New **Auto / Hold / Free** home-battery
      three-way (`select.battery_hold_mode` → engine finalizer). Freshness: a ~1.5 s
      `request_refresh_debouncer` replaces HA's 10 s default, plus a 1 s card-side ticker and
      optimistic controls. Card is now EN/DE and theme-aware.
- [ ] PV/price forecast-aware planning (solar forecast feeding the departure plan).
- [ ] Diagnostics: data-source health/staleness, last-decision timestamp, dashboards.

## Phase 6 — Direct go-e MQTT ✅ (done, on `main`)
- [x] **v5.0.0 (breaking) — drop the third-party go-e integration; talk go-e MQTT directly.**
      New HA-free `goe_parse.py` (keys/enums + pure decoding: topic split incl. the leading-slash
      variant, JSON payloads, `nrg[11]` power, carState→connected) + HA client `goe_mqtt.py`
      (subscribe `<base>/#`, cache, publish `<base>/<key>/set`, typed accessors + `local_push`
      listeners, broker discovery on both `go-eCharger/#` and `/go-eCharger/#`). Coordinator now
      reads `car`/`nrg`/`wh`/`pnp` and writes `amp`/`frc`/`psm` over MQTT — the label-matching
      helpers are gone. Config charger step is a single **base topic** (auto-discovered). The
      integration now **owns** the wallbox entities: current `number`, phase/force `select`s,
      car-connected + charging-allowed `binary_sensor`s, charger status/power/session/total/
      allowed-current `sensor`s. `manifest` gains the `mqtt` dependency + `local_push`. Config
      entry v3→v4 drops the six mapped-entity keys; setup raises a repair issue prompting the user
      to set the base topic (an entity map can't become a topic). Tests: `tests/test_goe_parse.py`.
      Full design: `docs/mqtt-direct-concept.md`.

## Phase 7 — Two-speed surplus tracking ✅ (done, on `main`, v5.3.0)
The surplus is now tracked through **two** filters instead of one: a *tracking* signal
(12 s up / 5 s down) that sets the charging current, and the existing calm *commitment*
signal (120 s / 20 s) that decides whether to charge at all and on how many phases. One
number could not do both jobs — it had to stay slow enough for the contactor, which made
the amps crawl (a step took minutes). Phase switching gained a confirmation window
(`PHASE_CONFIRM_S`) and one-sided headroom (`PHASE_UP_MARGIN_W`); the buffer-zone
discharge penalty became a directional EMA (slow attack = the bridging tolerance, fast
release) instead of a box-mean; the ride-out now follows the live surplus instead of
pinning the minimum; and the write path dropped to a 2 s settle with a fast lane for
decisive back-offs. Also fixed: the buffer-zone identity clamped the grid to its export
side, so while the grid was *importing* to feed the car, the car's own draw counted as
surplus — a phantom surplus it would never back off from (normally masked by the home
battery discharging instead). Spec: `docs/charging-behavior-matrix.md` § "Two speeds".

  Follow-ups worth revisiting:
  - ~~Watch the amp write rate in the field.~~ **Closed:** the go-e handles >1 write/s
    sustained (verified in practice), so the ~4 writes/min this release produces is a
    non-issue. Recorded in `docs/mqtt-direct-concept.md`. The charger is not the limiting
    factor when tuning the loop — the car's response time is.
  - **Not a lever: the write deadband.** `amp` is uint8 *integer* amps and the coordinator
    already rounds, so `MIN_WRITE_DELTA_A = 1.0` is a no-op that merely documents the
    charger's own resolution (1 A ≈ 690 W at 3φ). Finer tracking is only available at 1φ,
    where a step is 230 W — another reason surplus charging prefers a single phase.
  - `START_CONFIRM_S` still hard-resets on any dip below the minimum, so a fluctuating
    morning restarts the full 3 minutes repeatedly. A short grace before resetting would
    start solar sessions sooner; deliberately left alone as it trades against start caution.
  - Tracking time constants are bounded by the *sample rate* (noise ∝ dt/τ). If the loop
    ever evaluates faster than ~1.5 s, they could shorten further — but real short
    transients, not noise, are what bites below ~5 s.

## Open items / decisions to make during build
- [x] go-e write path: **direct go-e MQTT** — `amp`/`frc`/`psm` topics (Phase 6, v5.0.0).
- [x] Pause behavior: **`frc` force-state** (0 neutral / 1 off / 2 on), not current=0 (Phase 6).
- [x] SteVe API surface/version + auth handling — `/steve/api/v1`, HTTP Basic with the web user's
      API password; tags `maxActiveTransactionCount`=0 → blocked. (Phase 3)
- [ ] Price-optimization algorithm depth (greedy cheapest-hours vs. forecast-aware scheduling).
- [ ] Model vehicle SoC when the car/charger exposes it.

## Repo / housekeeping
- [ ] Decide on repo name (currently `HAgoe_steve`; alternatives `ha-goe-steve`, `HASteveGoe`).
- [x] Add `LICENSE` (MIT), `info.md` (HACS), and CI (`.github/workflows/validate.yml`:
      hassfest + HACS validation + engine tests + card build/stale-bundle check). (v1.0)
- [ ] Submit to home-assistant/brands for the integration logo, then drop `ignore: brands` in CI.
      Assets ready (Option 3) in `branding/hacs/custom_integrations/goe_steve/` — copy that folder
      into a fork of home-assistant/brands and open the PR. Sources: `branding/icon-brands.svg`,
      `branding/logo-lockup.svg`; re-render via `branding/render.mjs`.
- [x] Tag/release `v1.0.0`, then `v1.0.1` (event-driven surplus). Released as GitHub tags.
