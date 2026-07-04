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
            BatteryHoldBinarySensor(coordinator),
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


class BatteryHoldBinarySensor(GoeSteveEntity, BinarySensorEntity):
    """True while the home battery is held from discharging into the car.

    The engine computes this every cycle (``Decision.hold_battery``) but it used
    to live nowhere: the biggest of the "state the brain knows but never shows".
    On the card it becomes the shield chip ("Battery discharge blocked").
    """

    _attr_icon = "mdi:home-battery-outline"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "battery_hold")

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data and self.coordinator.data.hold_battery)

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        data = self.coordinator.data
        if data is None:
            return {}
        # "auto" = the brain's live choice; "hold"/"free" = the user's override.
        return {"source": data.hold_source}
