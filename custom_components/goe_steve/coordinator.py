"""Coordinator: reads mapped HA entities, runs the engine, writes the charger."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_BATTERY_POWER,
    CONF_BATTERY_SOC,
    CONF_GOE_CHARGING,
    CONF_GOE_CONNECTED,
    CONF_GOE_CURRENT,
    CONF_GOE_POWER,
    CONF_GRID_POWER,
    CONF_PV_POWER,
    CONF_PHASES,
    CONF_VOLTAGE,
    DEFAULT_BATTERY_RESERVE_SOC,
    DEFAULT_MAX_CURRENT,
    DEFAULT_MIN_CURRENT,
    DEFAULT_MIN_GRID_FLOOR_W,
    DEFAULT_PHASES,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_VOLTAGE,
    DOMAIN,
    MIN_WRITE_DELTA_A,
)
from .engine import (
    BatteryPolicy,
    ChargerInputs,
    ChargingMode,
    Decision,
    EngineConfig,
    decide,
)

_LOGGER = logging.getLogger(__name__)

# Loose truthy/charging tokens, so we tolerate the many ways go-e integrations
# expose "car connected" / "charging" (binary_sensor, sensor, enum, number).
_TRUTHY = {STATE_ON, "true", "1", "connected", "charging", "car", "ready"}


@dataclass(slots=True)
class RuntimeSettings:
    """User-adjustable settings, owned here and mutated by control entities.

    Persisted across restarts by the entities themselves (RestoreEntity), which
    push their restored value back in on startup.
    """

    mode: ChargingMode = ChargingMode.OFF
    battery_policy: BatteryPolicy = BatteryPolicy.PROTECT
    smart_enabled: bool = True
    min_current_a: float = DEFAULT_MIN_CURRENT
    max_current_a: float = DEFAULT_MAX_CURRENT
    battery_reserve_soc: float = DEFAULT_BATTERY_RESERVE_SOC
    min_grid_floor_w: float = DEFAULT_MIN_GRID_FLOOR_W


class GoeSteveCoordinator(DataUpdateCoordinator[Decision]):
    """Drives one regulation loop per config entry."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
            config_entry=entry,
        )
        self._cfg = dict(entry.data)
        self.settings = RuntimeSettings()
        self._voltage = float(self._cfg.get(CONF_VOLTAGE, DEFAULT_VOLTAGE))
        self._phases = int(self._cfg.get(CONF_PHASES, DEFAULT_PHASES))
        self._last_written_a: float | None = None

    # --- State reading helpers --------------------------------------------------
    def _get_float(self, conf_key: str) -> float | None:
        entity_id = self._cfg.get(conf_key)
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN, ""):
            return None
        try:
            return float(state.state)
        except (ValueError, TypeError):
            return None

    def _get_bool(self, conf_key: str) -> bool | None:
        entity_id = self._cfg.get(conf_key)
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN, ""):
            return None
        raw = state.state.lower()
        if raw in _TRUTHY:
            return True
        if raw in (STATE_OFF, "false", "0", "idle", "disconnected"):
            return False
        # Numeric truthiness fallback (e.g. go-e "car" status code > 1).
        try:
            return float(raw) > 1
        except (ValueError, TypeError):
            return None

    # --- The regulation loop ----------------------------------------------------
    async def _async_update_data(self) -> Decision:
        connected = self._get_bool(CONF_GOE_CONNECTED)
        grid = self._get_float(CONF_GRID_POWER)

        # Required signals missing/stale → keep hands off rather than guess.
        if connected is None or grid is None:
            return Decision(
                control=False,
                reason="Waiting for charger / grid data",
            )

        inputs = ChargerInputs(
            car_connected=connected,
            car_actual_power_w=self._get_float(CONF_GOE_POWER) or 0.0,
            phases=self._phases,
            voltage_v=self._voltage,
            grid_power_w=grid,
            pv_power_w=self._get_float(CONF_PV_POWER),
            battery_soc=self._get_float(CONF_BATTERY_SOC),
            battery_power_w=self._get_float(CONF_BATTERY_POWER),
        )
        cfg = EngineConfig(
            mode=self.settings.mode,
            battery_policy=self.settings.battery_policy,
            smart_enabled=self.settings.smart_enabled,
            min_current_a=self.settings.min_current_a,
            max_current_a=self.settings.max_current_a,
            battery_reserve_soc=self.settings.battery_reserve_soc,
            min_grid_floor_w=self.settings.min_grid_floor_w,
        )

        decision = decide(inputs, cfg)
        await self._apply(decision)
        return decision

    async def _apply(self, decision: Decision) -> None:
        """Write the target current to the go-e, avoiding redundant writes."""
        if not decision.control:
            self._last_written_a = None  # we relinquished control
            return

        current_entity = self._cfg.get(CONF_GOE_CURRENT)
        if not current_entity:
            return

        target = round(decision.target_current_a) if decision.should_charge else 0
        if self._last_written_a is not None and abs(target - self._last_written_a) < MIN_WRITE_DELTA_A:
            return

        try:
            await self.hass.services.async_call(
                "number",
                "set_value",
                {"entity_id": current_entity, "value": target},
                blocking=False,
            )
            self._last_written_a = float(target)
        except Exception as err:  # noqa: BLE001 - never let a write break the loop
            _LOGGER.warning("Failed to set charger current via %s: %s", current_entity, err)

    def request_apply(self) -> None:
        """Ask for an immediate re-evaluation after a settings change."""
        self.hass.async_create_task(self.async_request_refresh())
