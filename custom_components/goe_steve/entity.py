"""Shared base entity for go-e + SteVe Smart Charging."""

from __future__ import annotations

from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_NAME, DOMAIN
from .coordinator import GoeSteveCoordinator, SteVeCoordinator


def _device_info(entry_id: str, title: str | None) -> DeviceInfo:
    """The single device every entity (brain + SteVe) attaches to."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry_id)},
        name=title or DEFAULT_NAME,
        manufacturer="Community",
        model="Smart Charging Brain",
    )


class GoeSteveEntity(CoordinatorEntity[GoeSteveCoordinator]):
    """Base entity: shared device, translation-keyed names, stable unique ids."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: GoeSteveCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._key = key
        entry_id = coordinator.config_entry.entry_id
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = _device_info(
            entry_id, coordinator.config_entry.title
        )


class GoeMqttEntity(Entity):
    """Base for entities backed directly by the go-e MQTT client.

    These mirror the charger's own state (current, phases, power, …) that used to
    come from a separate go-e integration. They push on every MQTT update and share
    the integration's device, like the coordinator-backed entities.
    """

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, coordinator: GoeSteveCoordinator, key: str) -> None:
        self.coordinator = coordinator
        self._client = coordinator.goe
        self._key = key
        entry_id = coordinator.config_entry.entry_id
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = _device_info(
            entry_id, coordinator.config_entry.title
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(self._client.async_add_listener(self.async_write_ha_state))

    @property
    def available(self) -> bool:
        return self._client.available


class SteVeEntity(CoordinatorEntity[SteVeCoordinator]):
    """Base for SteVe-backed entities, sharing the integration's device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SteVeCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._key = key
        entry_id = coordinator.config_entry.entry_id
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = _device_info(
            entry_id, coordinator.config_entry.title
        )
