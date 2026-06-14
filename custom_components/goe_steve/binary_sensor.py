"""Binary sensor platform: brain control state."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
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
            ControllingBinarySensor(coordinator),
            ChargingRequestedBinarySensor(coordinator),
        ]
    )


class ControllingBinarySensor(GoeSteveEntity, BinarySensorEntity):
    """True when the brain is actively managing the charger this cycle."""

    _attr_icon = "mdi:robot"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "controlling")

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data and self.coordinator.data.control)


class ChargingRequestedBinarySensor(GoeSteveEntity, BinarySensorEntity):
    """True when the brain wants the car charging right now."""

    _attr_icon = "mdi:flash"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "charging_requested")

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data and self.coordinator.data.should_charge)
