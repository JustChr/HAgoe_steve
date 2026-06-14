"""Sensor platform: what the brain decided, and why."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfElectricCurrent, UnitOfPower
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import GoeSteveConfigEntry
from .entity import GoeSteveEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GoeSteveConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        [
            StatusSensor(coordinator),
            SurplusSensor(coordinator),
            TargetCurrentSensor(coordinator),
        ]
    )


class StatusSensor(GoeSteveEntity, SensorEntity):
    """Plain-language explanation of the current decision — the key UX element."""

    _attr_icon = "mdi:ev-station"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "status")

    @property
    def native_value(self) -> str | None:
        decision = self.coordinator.data
        return decision.reason if decision else None

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        decision = self.coordinator.data
        settings = self.coordinator.settings
        if decision is None:
            return {}
        return {
            "mode": settings.mode.value,
            "battery_policy": settings.battery_policy.value,
            "controlling": decision.control,
            "charging": decision.should_charge,
            "target_current_a": round(decision.target_current_a, 1),
            "target_phases": decision.target_phases,
        }


class SurplusSensor(GoeSteveEntity, SensorEntity):
    """Power currently available to the car under the active battery policy."""

    _attr_icon = "mdi:solar-power"
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "surplus_for_car")

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.surplus_w if self.coordinator.data else None


class TargetCurrentSensor(GoeSteveEntity, SensorEntity):
    """The current the brain is asking the charger to use (0 when paused)."""

    _attr_icon = "mdi:current-ac"
    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "target_current")

    @property
    def native_value(self) -> float | None:
        decision = self.coordinator.data
        if decision is None:
            return None
        return decision.target_current_a if decision.should_charge else 0.0
