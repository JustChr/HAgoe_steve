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
CONF_GOE_CURRENT: Final = "goe_current_number"
CONF_GOE_CONNECTED: Final = "goe_connected_entity"
CONF_GOE_CHARGING: Final = "goe_charging_entity"
CONF_GOE_POWER: Final = "goe_power_entity"

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

# Don't rewrite the charger for sub-amp changes (protects relays, cleaner UX/logs).
MIN_WRITE_DELTA_A: Final = 1.0
