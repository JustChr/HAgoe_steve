"""Number platform: runtime-adjustable tunables."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.const import PERCENTAGE, UnitOfElectricCurrent, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import GoeSteveConfigEntry
from .coordinator import RuntimeSettings
from .entity import GoeSteveEntity


@dataclass(frozen=True, kw_only=True)
class GoeNumberDescription(NumberEntityDescription):
    """Describes a tunable bound to a RuntimeSettings attribute."""

    attr: str
    getter: Callable[[RuntimeSettings], float]
    setter: Callable[[RuntimeSettings, float], None]


NUMBERS: tuple[GoeNumberDescription, ...] = (
    GoeNumberDescription(
        key="min_current",
        attr="min_current_a",
        icon="mdi:current-ac",
        native_min_value=6,
        native_max_value=32,
        native_step=1,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        entity_category=EntityCategory.CONFIG,
        getter=lambda s: s.min_current_a,
        setter=lambda s, v: setattr(s, "min_current_a", v),
    ),
    GoeNumberDescription(
        key="max_current",
        attr="max_current_a",
        icon="mdi:current-ac",
        native_min_value=6,
        native_max_value=32,
        native_step=1,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        entity_category=EntityCategory.CONFIG,
        getter=lambda s: s.max_current_a,
        setter=lambda s, v: setattr(s, "max_current_a", v),
    ),
    GoeNumberDescription(
        key="battery_reserve_soc",
        attr="battery_reserve_soc",
        icon="mdi:home-battery",
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.CONFIG,
        getter=lambda s: s.battery_reserve_soc,
        setter=lambda s, v: setattr(s, "battery_reserve_soc", v),
    ),
    GoeNumberDescription(
        key="min_grid_floor",
        attr="min_grid_floor_w",
        icon="mdi:transmission-tower",
        native_min_value=0,
        native_max_value=11000,
        native_step=100,
        native_unit_of_measurement=UnitOfPower.WATT,
        entity_category=EntityCategory.CONFIG,
        getter=lambda s: s.min_grid_floor_w,
        setter=lambda s, v: setattr(s, "min_grid_floor_w", v),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GoeSteveConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(GoeNumber(coordinator, desc) for desc in NUMBERS)


class GoeNumber(GoeSteveEntity, RestoreEntity, NumberEntity):
    """A tunable that persists and feeds the engine."""

    entity_description: GoeNumberDescription

    def __init__(self, coordinator, description: GoeNumberDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last is not None and last.state not in (None, "unknown", "unavailable"):
            try:
                self.entity_description.setter(
                    self.coordinator.settings, float(last.state)
                )
            except (ValueError, TypeError):
                pass

    @property
    def native_value(self) -> float:
        return self.entity_description.getter(self.coordinator.settings)

    async def async_set_native_value(self, value: float) -> None:
        self.entity_description.setter(self.coordinator.settings, value)
        self.async_write_ha_state()
        self.coordinator.request_apply()
