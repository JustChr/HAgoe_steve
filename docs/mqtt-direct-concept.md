# Concept: talk to the go-e charger over MQTT directly

Removes the dependency on a separate go-e HA integration. The brain subscribes and
publishes to the charger's **native MQTT topics** itself and **owns** the wallbox
entities. Charger setup collapses from six entity pickers to one thing: the go-e
**base topic** (auto-discovered from the broker).

Status: **implemented** (v5.0.0). Key mapping + decisions verified against a live
charger, serial `222162`, 2026-07-07. Pure decoding lives in `goe_parse.py`
(HA-free, unit-tested in `tests/test_goe_parse.py`); the HA client is `goe_mqtt.py`.

---

## Why

Today the wallbox six-pack (`amp` number, phase/force selects, connected/power/energy
sensors) comes from a *third-party* go-e integration; the brain reads them with
`hass.states.get(...)` and writes them with `number.set_value` / `select.select_option`
service calls ([`coordinator.py`](../custom_components/goe_steve/coordinator.py) `_apply`,
`_write_*`). That means a second HACS install to keep working, a translation layer that
guesses at option labels (`_force_option_for`, `_phase_option_for`), and no access to the
richer go-e state (`modelStatus`, `acu`, `alw`, …).

Going direct: one dependency fewer, exact enum values instead of label-matching, live
`local_push`, and the full go-e status surface.

---

## Transport (go-e API v2, verified)

- **Read:** the charger publishes a **retained** topic per API key at
  `<base>/<key>`, payload is **JSON** (numbers raw, strings quoted, bools `true`/`false`,
  arrays as JSON). Retained ⇒ current values arrive the moment we subscribe.
- **Write:** publish JSON to `<base>/<key>/set`; the charger echoes `<base>/<key>/result`
  (`success` or an error string).
- **Base topic is not fixed.** Default is `go-eCharger/<serial>`, but the `mtp` prefix
  can change it. **This charger emits `/go-eCharger/222162/…` — with a leading slash.**
  So the base topic must be captured verbatim (leading slash included) and used for both
  subscribe and `/set`. Never hard-code `go-eCharger/<serial>`.
- **Charger prerequisites:** MQTT enabled (`mce=true`) and **writes allowed**
  (`mcr=false` — off by default since firmware 051.5). Surface this in setup; it is the
  most likely reason writes silently do nothing.

---

## The key mapping — reviewed & confirmed

| Purpose (old config key) | go-e key | R/W | Payload / enum | Status |
|---|---|---|---|---|
| Requested current (`CONF_GOE_CURRENT`) | `amp` | W | uint8 Amps | ✅ |
| Start / stop (`CONF_GOE_FORCE`) | `frc` | W | `0` Neutral · `1` Off · `2` On | ✅ maps 1:1 to the brain's start/stop |
| Phase select (`CONF_GOE_PHASE`) | `psm` | W | **`1` = 1-phase · `2` = 3-phase** (`0` auto, unused) | ✅ verified live (`psm 1`) |
| Car connected (`CONF_GOE_CONNECTED`) | `car` | R | `0` Unknown · `1` Idle (no car) · `2` Charging · `3` WaitCar · `4` Complete · `5` Error | ✅ connected = `car ∈ {2,3,4}` |
| Car power (`CONF_GOE_POWER`) | `nrg[11]` | R | 16-elem array, index 11 = **total power in W** | ✅ verified live (array `[U×4, I×3, P L1/L2/L3/N/Total, pf×4]`) |
| Session energy (`CONF_GOE_ENERGY`) | `wh` | R | double Wh, resets at plug-in | ✅ already session-scoped |

> **`psm` note:** value semantics are `1 → single phase`, `2 → three phase`. This is the
> opposite reading from "count of phases" — the engine speaks in phase *counts* (1 or 3),
> so the adapter maps `count → psm` as `1→1`, `3→2`, and back `psm 1→1`, `psm 2→3`.
> Coincidentally 1↔1, but write it as an explicit map, not an identity.

> **`nrg` layout** (index): `U` L1,L2,L3,N = 0‑3 · `I` L1,L2,L3 = 4‑6 ·
> `P` L1,L2,L3,N,**Total** = 7‑11 · `pf` L1,L2,L3,N = 12‑15. Total power = **`nrg[11]`**.

### Extras we gain (surfaced as full entities, per decision)

- `acu` — amps the car is *actually allowed* right now
- `alw` — allowed to charge at all (bool)
- `pnp` — phases actually charging → replaces the read-back guessing in `_read_phases`
- `modelStatus` — go-e's own reason code (`ChargingBecausePvSurplus`,
  `NotChargingBecauseForceStateOff`, …) → feeds the card's reason line
- `eto` lifetime energy, `cbl` cable current limit, `fwv`/`fna`/`mcc` diagnostics

---

## Architecture

A thin adapter `goe_mqtt.py`:

- On setup, **subscribe `<base>/#`** via HA's built-in MQTT client
  (`homeassistant.components.mqtt.async_subscribe`), parse each JSON payload, cache
  `key → value`. Retained topics prime the cache immediately.
- Expose typed accessors (`car_connected`, `power_w`, `session_wh`, `phases`, `allowed`,
  `model_status`, …) and setters (`set_amp`, `set_frc`, `set_psm`) that publish JSON to
  `<base>/<key>/set` via `mqtt.async_publish`.
- The **coordinator** swaps its `hass.states.get` / `services.async_call` calls for this
  adapter. **The engine and all regulation logic stay untouched** — this is purely the
  read/write edge. `_read_phases` reads `pnp`; the `_force_option_for` /
  `_phase_option_for` / label-matching helpers are deleted (we write exact enums now).
- The wallbox entities become **ours**, under our own device, backed by the cached values
  (`local_push`). Full parity set + the extras above.
- `manifest.json`: add `"mqtt"` to `dependencies` (so setup waits for the MQTT
  integration), flip `iot_class` to `"local_push"`.

### Config flow

The charger step becomes **auto-discovery**:

1. Subscribe briefly to **both** `go-eCharger/#` **and** `/go-eCharger/#` (leading-slash
   variant — required for this charger).
2. Collect distinct base topics seen (`<prefix>/<serial>`), enrich with `fna`
   (friendly name) and `fwv` if present, present as a picker.
3. Fall back to a manual base-topic text field when nothing is discovered.
4. Store the chosen base topic **verbatim**. Voltage / phases stay as they are.

`const.py`: replace the six `CONF_GOE_*` entity keys with a single `CONF_GOE_BASE_TOPIC`
(keep the old keys defined only for the migration below).

### Migration (v3 → v4): repair flow

An entity-id map can't be turned into a topic, so existing entries can't be auto-migrated.
On load of a pre-MQTT entry, raise a **repair issue / reconfigure step** that runs the same
auto-discovery and writes `CONF_GOE_BASE_TOPIC`, then drops the old `CONF_GOE_*` keys. One
re-config, clean break to MQTT. Call it out in the release notes.

---

## Open / to confirm during build

- **Write confirmation:** optionally subscribe `<base>/<key>/result` and log non-`success`
  responses (helps diagnose the `mcr=true` foot-gun without extra config).
- **Availability:** treat the charger as unavailable when `mcc` (MQTT connected) is false or
  no message seen within N intervals, so entities go unavailable rather than serve stale
  retained values.
- **Multiple chargers:** discovery may surface several serials; the flow already picks one —
  keep single-charger scope for now (matches the rest of the integration).
