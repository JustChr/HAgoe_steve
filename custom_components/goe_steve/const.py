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
# --- Peak protection: optional Victron/ESS steering entities (all best-effort) ------
# Deliberately generic number entities the user maps themselves rather than a tight
# coupling to Victron's own integration. Each is a no-op when unmapped.
#
# The ESS grid setpoint ("hold grid import at X W"). On an ESS this *is* total grid
# import, so writing it commands exactly the quantity a capacity tariff bills.
CONF_VICTRON_SETPOINT: Final = "victron_setpoint_entity"
# The ESS "Minimum SoC (unless grid fails)" number. Peak protection owns it while
# enabled, holding it at the shaving reserve and dropping it to the peak floor while
# actively shaving — that drop is what physically unlocks the discharge headroom.
CONF_VICTRON_MIN_SOC: Final = "victron_min_soc_entity"
# A solar-forecast sensor (Forecast.Solar / Solcast style, kWh expected tomorrow).
# Its job is not "is it winter" but "don't fill the battery from the grid the night
# before a bright day" — see the bright/dark targets below.
CONF_PV_FORECAST: Final = "pv_forecast_entity"
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

# --- Peak protection (capacity tariff / Leistungstarif) ----------------------------
# From 2027 Austrian grid operators bill households on the highest average grid
# import over a *fixed clock quarter-hour* (:00/:15/:30/:45) in the month. The three
# limits below are compared against the *projected* end-of-window average, so the
# brain reacts to where the quarter-hour is heading rather than to a spike.
#
# Off by default: with it off the integration behaves exactly as it did before, and
# the measurement still runs so you can watch your peaks for a month before acting.
DEFAULT_PEAK_GUARD_ENABLED: Final = False
DEFAULT_PEAK_SOFT_W: Final = 3300.0  # start easing the wallbox down
DEFAULT_PEAK_TARGET_W: Final = 3700.0  # the steady-state ceiling we aim to hold
DEFAULT_PEAK_HARD_W: Final = 3900.0  # cut immediately; pause the car if need be
# Once a window has already set 5.2 kW, shaving to 3.7 kW for the rest of the month
# saves nothing — the demand charge is booked. On by default; turn it off for a
# strict ceiling regardless of what the month has already cost.
DEFAULT_PEAK_FOLLOW_MONTH: Final = True
# The allowance aims this far *below* the month's record instead of at it. Without
# the gap it ratchets: a window aimed at the record eventually lands just over it,
# that becomes the new record, and the ceiling creeps up all month. The hard limit
# still sits on the record itself, so the buffer costs nothing but a little margin.
DEFAULT_PEAK_MONTH_BUFFER_W: Final = 200.0
# The SoC ladder. Normally the mapped Victron minimum-SoC sits at the shaving
# reserve, so ordinary house loads can't drain the battery flat; while shaving it
# drops to the peak floor, releasing that banked headroom exactly when it is worth
# money. Clamped so the floor never sits above the reserve.
DEFAULT_SHAVING_RESERVE_SOC: Final = 50.0
DEFAULT_PEAK_MIN_SOC: Final = 35.0
# Tier hysteresis. Escalation to *hard* is immediate (it is a safety stop);
# everything else confirms first, and every release also waits out the dwell.
PEAK_CONFIRM_S: Final = 120.0
PEAK_RELEASE_S: Final = 120.0
PEAK_DWELL_S: Final = 60.0
# How far the projection must fall back below the soft limit before the tier
# releases, so a projection hovering on the threshold doesn't chatter.
PEAK_HYSTERESIS_W: Final = 150.0
# A sample gap longer than this means part of the quarter-hour went unmeasured. The
# last reading is still held across it (never under-count), but the window is marked
# degraded and peak protection may then only tighten, never relax.
PEAK_MAX_GAP_S: Final = 120.0
# The billing window, and the floor on "time remaining" used when sizing the
# remaining import budget — it both avoids a divide-by-zero as the window closes and
# makes the last minute deliberately conservative.
PEAK_WINDOW_S: Final = 900.0
PEAK_MIN_REMAINING_S: Final = 60.0
# How many completed quarter-hours to keep for the card's history strip (24 h).
PEAK_HISTORY_LEN: Final = 96

# --- Cheap-hour grid charging -------------------------------------------------------
# Buy energy into the home battery (and run the house from the grid) while the price
# is at/below the same "cheap price" threshold the car uses. The commanded ESS grid
# setpoint *is* the total import, so this is capped by the live peak budget and
# imports steadily instead of spiking — cheap energy without a demand charge.
DEFAULT_GRID_CHARGE_ENABLED: Final = False
DEFAULT_GRID_SETPOINT_W: Final = 50.0  # the normal ESS import setpoint
DEFAULT_CHEAP_CHARGE_POWER_W: Final = 2000.0  # what we'd import in a cheap hour
# Target SoC depends on tomorrow, not on the calendar: fill deep when the forecast
# is poor, stop early when it is good so there is room for the PV to land in.
DEFAULT_BRIGHT_DAY_TARGET_SOC: Final = 40.0
DEFAULT_DARK_DAY_TARGET_SOC: Final = 80.0
DEFAULT_PV_FORECAST_LOW_KWH: Final = 8.0  # below this, tomorrow counts as "dark"
# Cheapest hours first, then any hour. The two targets above are what a *cheap* hour
# fills to; below this level the battery is topped up whatever the price, because a
# pack sitting on its floor cannot hold a peak limit at all — and in a dark winter
# week the five cheap hours a day do not keep up with the house. 0 disables it.
DEFAULT_PEAK_READY_SOC: Final = 0.0
# "Stock up for tonight": the user knows a sauna/oven/party evening is coming and the
# brain cannot. Fills toward this level at any price **and holds it there**, so the
# ordinary afternoon is served from the grid (far below the ceiling) instead of
# quietly spending the stock before the event it was bought for.
DEFAULT_STOCK_UP: Final = False
DEFAULT_STOCK_UP_TARGET_SOC: Final = 95.0

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

# How long to let one of our own writes echo back before we believe the charger's
# reported value again (see goe_parse.should_publish). We publish `<key>/set`, the
# box applies it and republishes `<key>`; until that lands, its retained value is
# still the *old* one and re-asserting against it would just spam the broker.
# Both directions of being wrong are bounded and mild: too short costs a duplicate
# write, too long lets a force-state someone else changed stand for that much
# longer. Ten seconds is generous for a local broker and still cuts an
# unauthorized charge well inside a minute.
ECHO_SETTLE_S: Final = 10.0
