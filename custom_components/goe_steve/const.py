"""Constants for the go-e + SteVe Smart Charging integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "goe_steve"
DEFAULT_NAME: Final = "Smart Wallbox Charging"

# How often the regulation engine re-evaluates and (re)writes the target current.
DEFAULT_SCAN_INTERVAL: Final = timedelta(seconds=30)

# --- Config entry keys: mapped HA entities (the "brain" reads/writes these) -------
CONF_GRID_POWER: Final = "grid_power_entity"
CONF_PV_POWER: Final = "pv_power_entity"
CONF_BATTERY_SOC: Final = "battery_soc_entity"
CONF_BATTERY_POWER: Final = "battery_power_entity"
# Switch/input_boolean that, when on, stops the home battery from discharging
# (e.g. Victron "disable discharge"). The brain turns it on while grid-charging
# whenever the battery is at/below its reserve line (and always during cheap
# hours) so the car draws from the grid, not the battery. Battery-system agnostic.
CONF_BATTERY_HOLD: Final = "battery_hold_entity"
CONF_PRICE: Final = "price_entity"
CONF_PRICE_FORECAST_ATTR: Final = "price_forecast_attr"
# --- Charger link: direct go-e MQTT (v4+) -----------------------------------------
# The brain talks to the go-e charger over its native MQTT instead of mapping
# entities from a separate go-e integration. Only the base topic is needed:
# "<prefix>/<serial>", e.g. "go-eCharger/222162" (a leading slash is preserved for
# chargers that emit "/go-eCharger/…"). See goe_mqtt.py + docs/mqtt-direct-concept.md.
CONF_GOE_BASE_TOPIC: Final = "goe_base_topic"

# --- Legacy charger config keys (pre-v4: mapped HA entities) -----------------------
# Kept only so a pre-v4 config entry keeps parsing during migration; no longer
# offered in the flow. The v3→v4 migration drops them once the base topic is set.
CONF_GOE_CURRENT: Final = "goe_current_number"
CONF_GOE_PHASE: Final = "goe_phase_entity"
CONF_GOE_FORCE: Final = "goe_force_entity"
CONF_GOE_CONNECTED: Final = "goe_connected_entity"
CONF_GOE_CHARGING: Final = "goe_charging_entity"
CONF_GOE_POWER: Final = "goe_power_entity"
CONF_GOE_ENERGY: Final = "goe_energy_entity"

# --- Config entry keys: SteVe linkage (Phase 3, all optional) ----------------------
CONF_STEVE_URL: Final = "steve_url"
CONF_STEVE_USERNAME: Final = "steve_username"
CONF_STEVE_PASSWORD: Final = "steve_api_password"
CONF_STEVE_CHARGEBOX: Final = "steve_charge_box_id"
CONF_STEVE_CONNECTOR: Final = "steve_connector_id"

DEFAULT_STEVE_CONNECTOR: Final = 1
# Metering/authorization data changes slowly; don't hammer SteVe at the 30 s
# regulation cadence.
STEVE_SCAN_INTERVAL: Final = timedelta(seconds=60)

# Default attribute on the price sensor that holds the hourly forecast list.
# Tolerant parsing covers Nordpool/EPEX/EnergyZero ("raw_today"/"raw_tomorrow"
# with start/value items) and similar provider shapes.
DEFAULT_PRICE_FORECAST_ATTR: Final = "raw_today"

# --- Config entry keys: static electrical facts -----------------------------------
CONF_VOLTAGE: Final = "voltage"
CONF_PHASES: Final = "phases"

# Transient key written by the v1→v2 migration: the old battery policy mapped
# onto a reserve-line value. The reserve number applies it once (instead of its
# own restored state) and setup removes it again. Never set by the config flow.
CONF_BATTERY_RESERVE_SEED: Final = "battery_reserve_seed"

# --- Defaults for runtime-adjustable tunables (exposed as number/select entities) --
DEFAULT_MIN_CURRENT: Final = 6.0  # A — EV hardware floor
DEFAULT_MAX_CURRENT: Final = 16.0  # A
DEFAULT_VOLTAGE: Final = 230.0  # V per phase
DEFAULT_PHASES: Final = 3
# % — the home-battery reserve line: below it the battery comes first (car gets
# only genuine excess solar), at/above it the battery buffers surplus
# fluctuations for the car. 100 = always protect (the conservative default).
DEFAULT_BATTERY_RESERVE_SOC: Final = 100.0
DEFAULT_CHEAP_PRICE: Final = 0.15  # currency/kWh — at/below this, grid is "cheap"
DEFAULT_TARGET_ENERGY_KWH: Final = 0.0  # kWh — 0 disables deadline planning

# --- Phase switching (static engine behaviour) -------------------------------------
DEFAULT_AUTO_PHASE: Final = False  # off until the user maps a phase-control entity
PHASE_DWELL_S: Final = 300.0  # min seconds between 1↔3 phase switches
# A threshold crossing must hold this long before the contactor moves at all, so
# a spike or a momentary dip never costs a phase switch.
PHASE_CONFIRM_S: Final = 120.0
# Extra headroom demanded before climbing 1φ → 3φ, widening the hysteresis band.
# One-sided on purpose: widening it downwards would mean holding 3φ (and its
# higher minimum) on a surplus a single phase could carry on its own.
PHASE_UP_MARGIN_W: Final = 500.0

# --- Solar tracking: two speeds, two jobs -------------------------------------------
# Turning the current knob is cheap and instantly reversible; starting, stopping and
# throwing the phase contactor are not. The same surplus is therefore tracked through
# two filters (both asymmetric EMAs, see engine._directional).
#
# The *commitment* filter — start/stop arbitration and the phase choice. Deliberately
# calm on the way up (a bright patch must persist before we commit to it), quicker on
# the way down so a real collapse is recognized promptly.
SURPLUS_SMOOTH_WINDOW_S: Final = 120.0
SURPLUS_DROP_TAU_S: Final = 20.0
# The *tracking* filter — the charging current. Short in both directions: a cloud or
# a switched-on appliance reaches the amps in seconds rather than minutes, and a
# clearing sky is used while it lasts. Still an average, not the raw reading, so a
# single noisy sample can't slam the current around; and because the underlying
# surplus identity is invariant to the car's own draw, a fast loop here converges
# instead of chasing itself.
#
# How short these may be is set by the *sample rate*, not by taste. An EMA's output
# noise scales with dt/τ, so with the loop evaluating every ~1.5 s (see
# INPUT_SETTLE_S + the coordinator's refresh debouncer) a 5 s τ still averages
# ~3 samples — quieter than a 12 s τ would be on a power meter that only reported
# every 5 s. What stops us going lower is no longer noise but *real* short
# transients: at τ=5 s a 2-second compressor inrush still only moves the output a
# third of the way, which is about the right amount of ignoring.
SURPLUS_TRACK_RISE_TAU_S: Final = 12.0
SURPLUS_TRACK_DROP_TAU_S: Final = 5.0
# Above the reserve line the battery may buffer freely — but discharge into the
# car beyond this power, sustained for the grace time, triggers a decisive
# ease-off so the battery never becomes the car's power source.
BATTERY_DISCHARGE_TOLERANCE_W: Final = 300.0
BATTERY_DISCHARGE_GRACE_S: Final = 180.0
# How the buffer-zone discharge penalty builds and fades. The slow attack *is* the
# bridging tolerance (the battery is allowed to cover a short dip); the much faster
# release stops a dip that is already over from holding the current down for another
# two minutes.
BATTERY_DISCHARGE_ATTACK_S: Final = 120.0
BATTERY_DISCHARGE_RELEASE_S: Final = 40.0

# --- Start/stop shaping ("ride out, then stop") -------------------------------------
# Surplus must sustain the minimum current this long before a solar start…
START_CONFIRM_S: Final = 180.0
# …and once charging, a surplus collapse is ridden out at minimum current this
# long before a clean stop. Few, deliberate transitions instead of flapping.
STOP_RIDE_OUT_S: Final = 300.0

# Grid and battery come from the same inverter but report a beat apart, so a raw
# state-change burst would briefly mix a fresh reading with a stale one. We
# coalesce the burst with a trailing-edge debounce this long: just over the
# inter-sensor gap, so evaluation runs once on the settled, aligned pair.
INPUT_SETTLE_S: Final = 0.75

# Minimum seconds between charger writes. This is a post-write settle, not a
# throttle: after we change the amps the car ramps and the inverter/battery
# rebalance, so we give that a moment before commanding again. It is derived from
# the *car*, not from the sensors — a vehicle may take several seconds to follow a
# changed pilot signal, so commanding faster than this just queues up moves it
# hasn't made yet. (It used to be 5 s on the assumption that the power meter only
# reported that often; meters here report sub-second, so the sensor rate stopped
# being the binding constraint.) Stops, phase changes and decisive back-offs
# bypass it (see _apply).
MIN_UPDATE_INTERVAL_S: Final = 2.0

# …and the exception that matters: cutting current is always safe and is the
# direction where hesitating costs money (grid import / a drained home battery),
# so a drop of at least this many amps jumps the settle above. Raising current
# never does — that would command into a plant that hasn't responded yet.
FAST_BACKOFF_DELTA_A: Final = 2.0

# Don't rewrite the charger for sub-amp changes (protects relays, cleaner UX/logs).
# Note this quantizes the loop: at 3φ/230 V one amp is ~690 W, so the deadband, not
# the timing, is what ignores small surplus wobbles.
MIN_WRITE_DELTA_A: Final = 1.0
