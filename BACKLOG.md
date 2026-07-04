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

## Open items / decisions to make during build
- [ ] go-e write path: existing integration's `number`/service vs. its API — confirm.
- [ ] Pause behavior: set current 0 vs. a dedicated stop switch/force-state entity.
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
