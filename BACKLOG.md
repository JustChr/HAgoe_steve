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

## Phase 8 — Rounding direction + "Start now" ✅ (done, on `main`, v5.4.0)
Two small levers the loop was missing.

**Which side of the surplus we land on.** The charger takes whole amps, so a surplus never
divides evenly — and the engine used to hand the coordinator a float that was rounded to
*nearest* on the way out, i.e. the direction was an accident of the remainder. It is now an
explicit decision in the engine (`_quantize_current`): the floor by default (the leftover is
exported, and below the reserve the battery is never asked to lend), the **ceiling** once the
SoC is at/above the midpoint between the reserve line and 100 % — there the last ≤1 amp step
comes out of a nearly-full battery instead of going to the grid. Never with the reserve at
100 %, which the user has declared unconditional. Entering the generous zone takes the
midpoint, leaving it 3 points less (`_GENEROUS_EXIT_MARGIN_PCT`), because rounding up walks
the SoC back across the threshold that enabled it. The deliberate borrow is excluded from the
sustained-discharge ease-off (its tolerance widens by one amp step) and is named in the status
reason. Protective trims (`_battery_guard_current`) now snap *down* for the same reason a
trim shouldn't hand power back.

**"Start now."** The ~3-minute start confirmation is a good default and a bad wait when the
user is looking at the surplus. A one-shot `EngineState.start_override` skips the remaining
window (never the surplus condition itself); it is exposed as a `button` entity that is
available exactly while the wait runs, and the card's countdown chip presses it.

  Follow-ups worth revisiting:
  - The rounding direction *is* the lever the write deadband never was (see Phase 7): at 3φ a
    step is ~690 W, which is a lot of "little bit". If field use shows the borrow is too
    coarse there, cap it by watts rather than by amps.
  - The start gate itself is untouched: a surplus one step short of the minimum still waits
    rather than borrowing its way to 6 A. Deliberate — starting is a commitment, and the
    borrow would then last at least the ride-out window.
  - Nothing skips the *ride-out* from the card yet (the symmetric "stop now"). Not asked for,
    and stopping early is already available via the mode switch.

## Phase 8.1 — "Minimum current" is one mode's setting ✅ (done, on `main`, v5.4.1)

**The bug.** *Minimum current* was global in the engine but mode-scoped in the card, which
only offers it in Solar + minimum. A value raised there followed the user into Solar only
and gated the start: at 10 A the surplus had to reach 2300 W (1φ) before charging began,
with the knob no longer visible to turn back down. It also set the current clamp, the
start-confirmation gate and the 3φ threshold in every mode.

**The rule.** The setting means what the card says it means: it is the minimum-floor
strategy's grid top-up level in Solar + minimum, and binds nowhere else. Every other mode
bottoms out at the EV's own 6 A (`HARDWARE_MIN_CURRENT_A`). One helper, `_floor_current(cfg)`,
answers "what is the floor here"; `min_current_a` is now read directly in exactly that one
place, so the two can't drift apart again.

  Follow-ups worth revisiting:
  - The entity is still called plain *Minimum current* in HA's own settings list, where
    nothing says it is mode-scoped. A rename (`strings.json` + EN/DE + card rebuild) would
    close the last gap between what the knob is called and what it does.
  - Fast and Manual now trim to 6 A rather than the setting when the battery guard bites.
    Correct under this rule, but it is the one place the change reaches beyond solar.

## Phase 9 — Peak protection + cheap-hour grid charging ✅ (done, on `main`, v5.5.0)

**The bill changes shape.** From 2027 Austrian grid operators bill households on the highest
average grid import over a fixed clock quarter-hour (:00/:15/:30/:45) in the month — one
unlucky 15 minutes sets a charge that stands until the month ends. That is a *household*
quantity: a sauna sets the peak whether or not a car is plugged in, so this could not be a
charging strategy.

**A ceiling, not a strategy.** The arbiter takes the highest bid, so a strategy wanting to
charge *less* has no way to win. `apply_peak_guard` therefore runs after the arbiter and the
finalizer, over every branch including Manual, Fast and "no car connected". The engine
integrates import energy over the current quarter-hour and compares the *projection* against
three limits: soft (ease the wallbox back), target (what the budget aims at), hard (setpoint
→ 0 W, pause the car if 6 A won't fit). Escalation is immediate; every release is confirmed
and dwelled. Off by default, and off is one early return — `test_switched_off_the_brain_
behaves_exactly_as_it_did_before` replays 14 scenarios to keep it that way.

**Two permissions, not one.** `Decision.control` governs the charger, `Decision.house_control`
the house (grid setpoint, minimum SoC, hold switch). Peak protection answers to its own switch,
so it keeps managing the house with Smart control off — and with it off the two collapse, which
is exactly the old rule.

**Don't pay twice.** With the month-peak allowance on, all three limits float up to what the
month has already cost — *up to* it, not onto it: the target settles a buffer below the record
so the projection's own error can't ratchet the month upward one overshoot at a time.

**Cheap-hour grid charging.** On an ESS the setpoint *is* total grid import, which is exactly
what a capacity tariff bills — so buying cheap energy into the home battery had to be capped by
the live quarter-hour budget. Depth follows tomorrow's solar forecast; peak protection outranks
it absolutely.

  Fixed before release (found in review of the WIP):
  - The restore path rebuilt the window without its sample clock, so a day of downtime looked
    like a two-second gap and back-filled 96 quarter-hours from one live reading — as
    *non-degraded* windows, i.e. straight into the month record. The outage is now measured
    from the older of the last sample and the still-open window, which is restart-proof rather
    than restore-proof.
  - The soft tier compared against the raw threshold while target/hard were month-adjusted, so
    it engaged — dropping minimum SoC and releasing the hold — to defend a line nobody was
    defending. All three limits now move together (`PeakWindow.soft_w`).
  - Nothing released the ESS setpoint / minimum SoC: switching off at the hard tier stranded
    the house at 0 W import forever. A `number` has no neutral position, so release means
    restore — captured on first write, persisted beside the hold.
  - The billed month rolled on UTC (01:00/02:00 local), and the one wall-clock time in a reason
    string was UTC too. Both now use HA's configured zone via `EngineConfig.local_tz`.
  - A peak pause left the Status sensor saying "Fast charging at 16 A"; a trim left the amp
    figure at the pre-trim value.
  - Manual's passive window suppressed the *house* levers too, so the soft tier silently did
    nothing until it escalated.

  Follow-ups worth revisiting:
  - Windows are floored in UTC. Exact for whole-hour offsets (Austria included); a half-hour
    zone would align to the wrong boundary.
  - Peak protection cannot shed a load. On an ESS the setpoint already sits at ~50 W, so the
    battery is *already* covering the sauna; the peak appears only when it physically can't.
    The `Peak shaving active` binary sensor's `tier` attribute is the hook for the user's own
    load-shedding automations.
  - There is deliberately no way to type this month's peak in by hand — the record is what was
    measured, so a peak drawn while HA was down is not one the guard will spend. *Reset this
    month's peak* is the escape hatch when the operator's meter disagrees.

## Closed-loop charger writes ✅ (v5.5.2)

A pause could stop pausing without anything noticing. `_write_force` skipped the write
whenever *we* had last written the same value — open-loop — so a `frc` moved at the charger
was invisible. Verified on the live instance (2026‑08‑03): unplugging a car makes the go-e
clear `frc` to Neutral ~4 s later; the brain's decision never changes across a car swap
("in control, don't charge" throughout), so it never wrote again, and the next car charged
at whatever `amp` was left in the register while the Status sensor read 0 A. Timestamps and
the full state trace are in `docs/mqtt-direct-concept.md`.

- `goe_parse.should_publish` (pure, unit-tested) decides whether a key needs writing from
  intent + the charger's reported value + our memory + time since our last write.
  `ECHO_SETTLE_S` absorbs the lag before our own write echoes back; a key the charger never
  reports falls back to memory so it can't be rewritten forever.
- Applied to `frc` and `psm`. **Not** to `amp`, which has its own deadband and rate limit.
- Pausing now parks `amp` at the hardware minimum (once per pause), so a charge we didn't
  authorize can't inherit the previous session's 16 A.
- Enforces what the Force-state select's docstring already promised: setting it by hand is
  authoritative only while the brain isn't controlling.

  Follow-ups worth revisiting:
  - A charger that *can't* honour a write is now re-asked every `ECHO_SETTLE_S` instead of
    once. For `frc` that is the wanted behaviour (persistent retry on a safety hold); for
    `psm` on a box without a phase-switching relay it would be pointless chatter. Nothing
    reports such a box today (`has_phase_control` is unconditionally true over MQTT), but if
    one turns up, `psm` wants its own longer settle or an attempt cap.
  - The reset is one-shot per disconnect (verified: `frc` stayed Neutral for hours after),
    so re-asserting costs one write per unplug and cannot become a fight with the charger.

## A full car hands the battery back; OCPP results read ✅ (v5.7.2)

- The grid strategies (and Manual) held the home battery for as long as they *wanted* to
  charge, so a full car left plugged in kept it blocked from the house. `_release_hold_for_idle_car`
  lets the **Auto** hold go once the charger has been allowed for `_CAR_IDLE_RELEASE_S` (180 s)
  with the car under `_CAR_DRAWING_MIN_W` (300 W); reason `car_not_drawing`. Power-based on
  purpose — it also covers a car waiting on its own timer.
- SteVe answers HTTP 200 once it has *tried*; the charger's verdict is in the
  `OcppOperationResponse` body. `operation_failure` now reads it for remote start/stop.
  Without a configured charge box the services fall back to `SteVeData.only_charge_box`
  (learned from the sessions — the v1 API has no charge-box listing). Remote start from the
  card confirmed working on the live instance afterwards (2026-10-24), so the remote
  start/stop payload follow-up under Phase 3 is settled.

  Follow-ups worth revisiting:
  - ~~Not yet seen live~~ Seen live 2026-11-06 (Full power, car stopped drawing): the Status
    reason read *"The car isn't taking power (full, or waiting on its own timer) — home battery
    released"*. The hold switch itself wasn't checked.
  - An explicit **Hold** deliberately still holds for a full car. If that turns out to be
    the case users hit, decide whether Hold should mean "always while the car charges".
  - The card has no way to authorize/block a tag (the picker lists only allowed tags);
    `authorize_tag` / `block_tag` are automation-only. Add a blocked-tags control if wanted.

## Waiting for an RFID card — investigated, not built (2026-11-06)

- 2026-10-21: with `acs` = Wait, a car plugged in while the brain forced the charger on got
  a session **without a card** (`trx` 0): no OCPP StartTransaction, SteVe never saw it,
  taps refused until unplug. PR #2 (branch `feat/wait-for-rfid-card`) held every mode off
  while `trx` was null.
- Live test on firmware 60.6 (details in `docs/mqtt-direct-concept.md`): forcing on **no
  longer** bypasses the card — the box keeps waiting until a tap. A tap works while forced
  off or on, and SteVe records it. PR #2 closed unmerged; its branch stays as a starting point.
- If a card-less session shows up again: detect `trx` not null with no active SteVe
  transaction for the charge box, say so in the Status reason (unplug/replug), and check
  whether `frc` 1→0 recovers it without unplugging (untested). Mind that `trx` 0 is also
  what a valid SteVe tap reports, and that `trx` stays stale ~5 s after an unplug.

## Peak protection, first live test (2026-11-06)

Month record reset, Fast mode, car on 1φ at ~3.4 kW, limits 3.2 / 3.7 / 3.9 kW, peak
protection on. Logged at 5 s for ~1 h. **The bill side works:** every quarter-hour finished
under the soft line (2.87, 2.87 kW …), and minimum SoC / setpoint were handed back every time.

- [x] **Measure on the billing meter's register** (branch `feat/meter-energy-counter`). Optional
      *Grid import energy counter*; the window's energy is the register's climb, grid power
      carries the seconds between ticks and the projection. Netz NÖ's register (5 s, 1 Wh) and
      our Victron-integrated figure agreed within ~0.5 % over the test quarter-hours anyway.
- [x] **The soft tier cycled about once per quarter-hour, and shaved twice.** Fixed by the
      *house share* (same branch): with battery power mapped, the tiers only steer the car; a
      heavy *house* load makes the setpoint follow the load up to the budget, so the battery
      covers only the excess. Optional *Home battery capacity* raises the grid's share when the
      energy won't last 15 min. Spec: matrix § "Heavy loads". Sim: `tools/sim/heavy_load.py`;
      winter fortnight (ceiling-fill) worst quarter-hour 5.20 → 4.25 kW at 95 % of the car energy.
- [ ] A charger the brain isn't driving (Manual passive, Smart control off) is paused only on
      the hard tier, so with a heavy house load it restarts after each 120 s release and is paused
      again 10 s later (scenario 13: every ~2 min, quarter-hour ends at 3.80 kW). Consider holding
      a hard pause on a hands-off charger until the house share releases.
- [x] **The car current hunts** every few seconds — under the soft cap (6–11 A) and from the
      request shaping with the tier off (12–16 A). Suspect: the derived house load jumping as the
      meters update out of step (0 → 3152 → 34 W within seconds). Confirm in `tools/sim` first.
      **Second live run (2026-11-06, 17:16–17:29, v5.8.0, Fast, soft tier):** the charger's `amp`
      really moves, not just the reason text — 12↔13 A every 5 s for ten minutes (~100 writes),
      11↔13 A while the grid swung 3.03↔3.50 kW on a ~10 s cycle with the car's draw flat at
      ~2.37 kW. So it is a real house load pulsing (not only meter skew) and the brain chases it
      at the 2 s / 1 A write limits. **Fixed (v5.8.1):** the source was the grid *request*
      (`peak_charge_ceiling_w`, live house load), which the cap's dwell never covered. It now
      goes through `_rate_limit_request` — down at once, up after `peak_dwell_s`. Replaying the
      live pattern: 119 → 1 current change in ten minutes. The 6–11 A hunting under the soft cap
      from the first test may still have the meter-skew cause; watch for it.
- [x] **v5.8.1's limiter made the car stick at 6 A** (live 2026-11-06 18:16–18:28): every raise
      was undone 5 s later, because the grid meter carries the ramping car 1–2 s before the go-e
      reports it, so the ramp read as +1.7 kW of house load; the dwell then held the low value.
      Sniffed: `amp 13` at :25.6, `amp 6` at :29.7, the go-e's `nrg` rising only at :29.8.
      **Fixed (v5.8.2):** `_settled_inputs` — for 15 s after a raise the peak paths count the car
      at least at what it was asked for. Closed-loop test with a one-cycle-late report.
- [x] **Boiler test (live 18:24:46, ~45 s, house 0.6 → 3.2 kW):** the car went 13 → 6 A in the
      same cycle, the quarter-hour held ~3.48 kW under the 3.7 kW target, the house share did not
      engage (the house alone fit the budget — by design) and the hard tier released at 18:28:41.
- [x] **A reload pauses a charging car for ~10 s.** Seen live 2026-11-06 16:18:36 UTC (options
      flow reload): *Charging requested* off for 3.5 s, `frc` on→off→on, `amp` 12→6→15, charger
      *complete* for 9 s. Cause (code, not yet reproduced in a test): `car_actual_power_w=
      self.goe.power_w or 0.0` in `coordinator.py` — the retained `car` says connected before the
      first `nrg` arrives, so the car's 2.7 kW counts as house load, the peak cap leaves < 6 A and
      the brain pauses. Confirmed: the retained burst is ~320 keys and the first refresh runs in
      it; the engine with car 0 W decides `peak_pause`, with 2.76 kW it keeps 13 A. **Fixed
      (v5.8.1):** a connected car without a power reading is stale input — hands off for that cycle.
- [x] **Meter counter checked live (17:15–17:47):** the 17:30 quarter-hour read 0.029 kWh on the
      register (≈ 116 W) against a projection of ~110 W; the month record stayed 3.34 kW. At each
      quarter-hour start `measured_by` reads `power` for 20–40 s until the register's next tick
      (1 Wh at ~100 W ≈ every 36 s) — expected fallback. Minimum SoC stayed 50 %, setpoint 100 W,
      battery held while the car charged and released at unplug.
- [x] Status wording: *"past the 3.20 kW easing-off point"* while the confirmation runs; a Fast
      charge held below the maximum by the peak budget says so.
- [x] **Hard tier seen live, v5.8.2 verified (2026-11-06 19:29–19:44 local).** Boiler on at 19:32:02,
      two minutes into the window (house 0.65 → 3.3 kW, projection 5.75 kW): `frc 1` + `amp 6` in the
      same cycle, car at 0 W a second later. Boiler off at 19:32:37 → `frc 2` at 6 A in the same cycle
      (no hold), 6 → 12 A 56 s later and it held. 10 writes in 15 min, every fall following a real house
      load, **no raise undone** (the v5.8.1 ramp artefact is gone).
- [x] **The pause reason promised a hold that doesn't exist** (reworded after v5.8.2, unreleased): "the car is paused until this quarter-hour
      is over at 19:45" — it resumed at 19:32:37, as the house share design intends (a displaced car
      resumes as soon as there's room). Reword `peak_pause` (engine + card `localize.ts` EN/DE) to
      "…paused until there's room again". The `until` param then has no job there.
- [ ] Borderline room still steps ±1 A about once a minute when the house wobbles across an amp
      boundary (19:36:53, target − house = 11.99 A). Real, cheap, and in the safe direction; the
      raise-margin idea (≈150 W headroom before going up) would settle it if it ever matters.

## Refill within the peak limit + field-test log ✅ (v5.9.0, v5.10.0 — 2026-11-07)

A Victron ESS recharges at **full power** when its minimum SoC sits above the battery's
charge (Chris, live). Every shave ended by raising it 35 → 50 %, so the ESS bought the peak
the shave had avoided; takeover with a low battery and stocking up (95 %) did the same.
- [x] Minimum SoC is a hold: a raise capped at floor(SoC), a held value kept, rounded down to
      the entity step (Victron 5 %); gradual hand-back on switch-off. (v5.9.0)
- [x] Refill through the setpoint at `min(allowed, target)`, battery first (car paused);
      steps aside for the departure guarantee (Chris: car wins, battery may shave to the floor
      meanwhile), a heavy house load, a degraded window. Stocking up = the same refill with the
      stock-up target. Spec + sim numbers: matrix § *Never above the charge*. (v5.9.0)
- [x] Field-test log: one record per quarter-hour + events, 45 days, Download diagnostics.
      Verified on the Pi: meter vs. Victron integral within 1 %, energy balance closes. (v5.10.0)
- [x] Live 2026-11-07 08:50 (short peak, house 8.45 kW): share, setpoint, min SoC 35 → 50 correct.
- [ ] **Refill + min-SoC cap not yet seen live** — needs a shave that takes the battery below 48 %
      (a sauna evening). Check in the test log: `refill` events, `ess_min_soc` ≤ SoC,
      `min_soc_above_soc` = 0, quarter-hours during the refill ≤ target.
- [ ] A fast-cycling house load (20–60 s) started/stopped the car 4× in 102 s (live 08:50).
      Candidate: resume only after the house stayed calm 30–60 s — simulate first (holding the
      pause to the window end cost 83 kWh/fortnight).
- [ ] Amp writes at the peak limit: 62 in 2 h (1–14 per quarter-hour, test log 2026-11-07) —
      the borderline ±1 A stepping above, now measured. Raise margin if the weeks show it matters.
- [ ] Analyse the field-test weeks before go-live (January 2027 at the latest).

## Stock for a dark day — the reserve follows the forecast (branch `feat/reserve-plan`, 2026-11-07)

Chris asked how energy gets "bought" ahead of a dark day. As built it barely did: the cheap-hour
trigger can't fire on his flat tariff (0.2446 €/kWh vs. a 0.20 threshold), and it read the
"tomorrow" sensor at any hour (at 02:00 that is the day after). On a flat tariff the only
reason to pre-buy is the capacity tariff, so the plan lives in peak protection.
- [x] Decided with Chris: **battery first** on dark nights (car waits, departure guarantee
      exempt); the dark-day level **replaces** *Keep ready for peaks* (same key, value carries
      over); daytime self-use is a **setting** (his median 10.5 kWh, Sep–Nov 2026).
- [x] `reserve_plan`: level = 100 % − room the coming solar day's surplus needs, between the
      shaving reserve and the dark-day reserve; held + refilled by night, by day only bought up
      to tonight's level less the sun still to come. Coming day = sunset to sunset (`sun.sun`).
      Today + rest-of-today forecast sensors added (optional, no migration).
- [x] Cheap-hour target judges the coming solar day too (bug: 02:00 read the day after).
- [x] Sim `tools/sim/reserve_plan.py`, three real autumn weeks: 98 → 0 quarter-hours over 3.7 kW,
      worst 6.12 → 3.70 kW, +€0.93 energy, +15 kWh PV export (flat 90 %: +85 kWh), car −14 kWh.
      Scenarios + refill sims identical to main with the plan off.
- [ ] Chris: map *today* + *rest of today* (Solcast), set *Reserve on a dark day* (90 %?) and
      *Solar the house uses directly* (10.5 kWh) — then watch `plan` in the test log.
- [ ] Self-use moves with the season — revisit whether to learn it once the test log has weeks
      of PV vs. surplus.
- [ ] Solcast's p10 (`estimate10` attribute) would make the plan less trusting of cloudy-day
      forecasts (median +1.4 kWh optimistic, p90 +6 kWh). Not wired: generic sensors don't have it.

## House share vs. meters that don't report together ✅ (v5.12.0 — 2026-11-09)

Live check of v5.11.0 (Sat 14:30 – Mon 22:00, 243 quarter-hours): no quarter-hour over target,
minimum SoC never above the charge, first dark-night refill clean. But Mon 07:03–07:10 the share
swung the setpoint 0 ↔ 3.9 kW (115 writes/QH, 11 car starts, battery charged from the grid), and
again at 16:42 with no car. `grid − battery` from two Victron meters reporting seconds apart
counted every step twice. Decision page: https://claude.ai/artifact/6N3e2BAQC51YWLPEUNqoBj
- [x] Sim `tools/sim/meter_skew.py`: 0.25 s, ESS lag, meter cadences + delays swept; reproduces it.
- [x] Optional *House consumption* mapping (Victron AC consumption L1–L3, summed), used as read.
      No migration (optional key). Chris: recommended options taken (2026-11-09).
- [x] Without it: derived load held 15 s for rises (swept 0–30 s), falls at once.
- [x] Engaging stays immediate on the raw reading (a held battery is only freed by engaging).
- [x] A consumption more than 500 W below the car for 2 min is set aside (one log warning,
      `consumption_rejected` in diagnostics); single readings fall back to the derived figure.
- [x] Battery guard trims at most what the car draws (Sun 8 Nov: 7 ↔ 8 A, 37 writes/QH with a
      full car on Auto).
- [x] Test log: seconds on the measured house load (`s.measured`).
- [ ] Chris: map the three `system_consumption_power_l1..l3` sensors, then check `s.measured`
      ≈ 900 per quarter-hour and the setpoint writes on the next sauna / car start.
- [ ] Live latency check: websocket sniff of grid / battery / consumption / nrg during a car start.
- [x] 5 s `manual_paused` + car restart after the reload on Mon 9 Nov 21:15: the first engine
      run landed before the setting entities restored, so it acted on factory defaults (Manual,
      peak protection off): `frc` off, minimum SoC handed back to 40 %, then all of it re-taken.
      The coordinator now writes nothing until the platforms are set up. (v5.12.1)

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
- [x] Brand images: shipped in `custom_components/goe_steve/brand/` (HA ≥ 2026.3 local brands,
      read by the Marketplace from the latest release) incl. a `dark_logo` for dark themes;
      `ignore: brands` dropped from CI; manifest declares `categories: ["energy.ev_charging"]`.
      No home-assistant/brands PR needed. Sources + re-render: `branding/README.md`.
- [x] Tag/release `v1.0.0`, then `v1.0.1` (event-driven surplus). Released as GitHub tags.
