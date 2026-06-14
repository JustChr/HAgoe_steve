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
CONF_PRICE: Final = "price_entity"
CONF_PRICE_FORECAST_ATTR: Final = "price_forecast_attr"
CONF_GOE_CURRENT: Final = "goe_current_number"
CONF_GOE_PHASE: Final = "goe_phase_entity"
CONF_GOE_CONNECTED: Final = "goe_connected_entity"
CONF_GOE_CHARGING: Final = "goe_charging_entity"
CONF_GOE_POWER: Final = "goe_power_entity"

# Default attribute on the price sensor that holds the hourly forecast list.
# Tolerant parsing covers Nordpool/EPEX/EnergyZero ("raw_today"/"raw_tomorrow"
# with start/value items) and similar provider shapes.
DEFAULT_PRICE_FORECAST_ATTR: Final = "raw_today"

# --- Config entry keys: static electrical facts -----------------------------------
CONF_VOLTAGE: Final = "voltage"
CONF_PHASES: Final = "phases"

# --- Defaults for runtime-adjustable tunables (exposed as number/select entities) --
DEFAULT_MIN_CURRENT: Final = 6.0  # A — EV hardware floor
DEFAULT_MAX_CURRENT: Final = 16.0  # A
DEFAULT_VOLTAGE: Final = 230.0  # V per phase
DEFAULT_PHASES: Final = 3
DEFAULT_BATTERY_RESERVE_SOC: Final = 80.0  # % — Protect: car waits until home battery reaches this
DEFAULT_MIN_GRID_FLOOR_W: Final = 1400.0  # W — PV+minimum: always charge at least this
DEFAULT_CHEAP_PRICE: Final = 0.15  # currency/kWh — at/below this, grid is "cheap"
DEFAULT_BATTERY_FLOOR_SOC: Final = 20.0  # % — Assist: stop draining the home battery here
DEFAULT_TARGET_ENERGY_KWH: Final = 0.0  # kWh — 0 disables deadline planning

# --- Phase switching & anti-flap (static engine behaviour) ------------------------
DEFAULT_AUTO_PHASE: Final = False  # off until the user maps a phase-control entity
PHASE_DWELL_S: Final = 300.0  # min seconds between 1↔3 phase switches
MIN_ON_DWELL_S: Final = 120.0  # keep charging at least this long once started
MIN_OFF_DWELL_S: Final = 120.0  # stay paused at least this long once stopped

# --- Input smoothing --------------------------------------------------------------
SMOOTHING_SAMPLES: Final = 3  # rolling-average window for PV/grid power
MIN_UPDATE_INTERVAL_S: Final = 20.0  # don't rewrite the charger more often than this

# Don't rewrite the charger for sub-amp changes (protects relays, cleaner UX/logs).
MIN_WRITE_DELTA_A: Final = 1.0
