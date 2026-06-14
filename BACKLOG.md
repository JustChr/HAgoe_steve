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

## Phase 3 — SteVe linkage (via SteVe API)
- [ ] Read transactions/kWh → sensors (last session, active transaction, **per-RFID/user energy**).
- [ ] Manage authorization: list RFID idTags + status; service to authorize/block; optional
      remote start/stop.
- [ ] Config: SteVe connection (URL + auth).

## Phase 4 — Lovelace card
- [ ] Modern custom card (TypeScript + Lit, HACS-distributed): live energy-flow visualization
      (PV → house/battery/car/grid), active mode + battery policy with plain-language reason,
      inline controls, per-RFID kWh.

## Phase 5 — Polish & forecasting
- [ ] PV/price forecast-aware planning.
- [ ] Diagnostics: data-source health/staleness, last-decision timestamp, dashboards.

## Open items / decisions to make during build
- [ ] go-e write path: existing integration's `number`/service vs. its API — confirm.
- [ ] Pause behavior: set current 0 vs. a dedicated stop switch/force-state entity.
- [ ] SteVe API surface/version + auth handling (Phase 3).
- [ ] Price-optimization algorithm depth (greedy cheapest-hours vs. forecast-aware scheduling).
- [ ] Model vehicle SoC when the car/charger exposes it.

## Repo / housekeeping
- [ ] Decide on repo name (currently `HAgoe_steve`; alternatives `ha-goe-steve`, `HASteveGoe`).
- [ ] Add `LICENSE`, `info.md` (HACS), and CI for hassfest + HACS validation before HACS submission.
