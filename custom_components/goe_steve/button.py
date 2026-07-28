"""Button platform: one-shot actions on the regulation loop."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
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
    async_add_entities([StartNowButton(coordinator)])


class StartNowButton(GoeSteveEntity, ButtonEntity):
    """Skip the stabilization wait before a solar start.

    Available only while that wait is actually running, so the button is never a
    promise it can't keep: it doesn't force a charge out of thin air, it only
    ends the confirmation window the surplus has already satisfied.
    """

    _attr_icon = "mdi:play-speed"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "start_now")

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.waiting_to_start

    async def async_press(self) -> None:
        self.coordinator.start_now()
