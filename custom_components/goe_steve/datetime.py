"""Datetime platform: charging departure deadline."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.datetime import DateTimeEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util

from . import GoeSteveConfigEntry
from .entity import GoeSteveEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GoeSteveConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([DepartureDateTime(entry.runtime_data)])


class DepartureDateTime(GoeSteveEntity, RestoreEntity, DateTimeEntity):
    """The deadline by which the target energy should be delivered."""

    _attr_icon = "mdi:calendar-clock"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "departure")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last := await self.async_get_last_state()) is not None:
            parsed = dt_util.parse_datetime(last.state)
            if parsed is not None:
                self.coordinator.settings.departure = dt_util.as_utc(parsed)

    @property
    def native_value(self) -> datetime | None:
        return self.coordinator.settings.departure

    async def async_set_value(self, value: datetime) -> None:
        self.coordinator.settings.departure = dt_util.as_utc(value)
        self.async_write_ha_state()
        self.coordinator.request_apply()
