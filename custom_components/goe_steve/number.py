"""Number platform: runtime-adjustable tunables."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfEnergy,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import GoeSteveConfigEntry
from .coordinator import RuntimeSettings
from .entity import GoeMqttEntity, GoeSteveEntity


@dataclass(frozen=True, kw_only=True)
class GoeNumberDescription(NumberEntityDescription):
    """Describes a tunable bound to a RuntimeSettings attribute."""

    attr: str
    getter: Callable[[RuntimeSettings], float]
    setter: Callable[[RuntimeSettings, float], None]


NUMBERS: tuple[GoeNumberDescription, ...] = (
    GoeNumberDescription(
        key="manual_current",
        attr="manual_current_a",
        icon="mdi:ev-station",
        native_min_value=6,
        native_max_value=32,
        native_step=1,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        getter=lambda s: s.manual_current_a,
        setter=lambda s, v: setattr(s, "manual_current_a", v),
    ),
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
        key="cheap_price",
        attr="cheap_price",
        icon="mdi:cash",
        native_min_value=0,
        native_max_value=2,
        native_step=0.01,
        native_unit_of_measurement="/kWh",
        entity_category=EntityCategory.CONFIG,
        getter=lambda s: s.cheap_price,
        setter=lambda s, v: setattr(s, "cheap_price", v),
    ),
    GoeNumberDescription(
        key="target_energy",
        attr="target_energy_kwh",
        icon="mdi:battery-charging",
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        entity_category=EntityCategory.CONFIG,
        getter=lambda s: s.target_energy_kwh,
        setter=lambda s, v: setattr(s, "target_energy_kwh", v),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GoeSteveConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    entities: list[NumberEntity] = [GoeNumber(coordinator, desc) for desc in NUMBERS]
    entities.append(ChargerCurrentNumber(coordinator))
    async_add_entities(entities)


class GoeNumber(GoeSteveEntity, RestoreEntity, NumberEntity):
    """A tunable that persists and feeds the engine."""

    entity_description: GoeNumberDescription

    def __init__(self, coordinator, description: GoeNumberDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        # The v1→v2 migration seed (old battery policy mapped onto the reserve
        # line) wins over this entity's own restored state, exactly once.
        if self.entity_description.key == "battery_reserve_soc":
            seed = self.coordinator.consume_reserve_seed()
            if seed is not None:
                self.entity_description.setter(self.coordinator.settings, seed)
                return
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
        # Adjusting the Manual current is the user taking over: leave the passive
        # window so the brain drives the charger from here. Other tunables (config)
        # don't affect the Manual hands-off transition.
        if self.entity_description.key == "manual_current":
            self.coordinator.set_manual_passive(False)
        self.async_write_ha_state()
        self.coordinator.request_apply()


class ChargerCurrentNumber(GoeMqttEntity, NumberEntity):
    """The charger's requested current (``amp``), live over MQTT.

    Reflects the go-e's own value and writes it back. While smart control is
    active the brain also drives this every cycle; setting it by hand is only
    authoritative when the brain isn't controlling (Manual / smart control off).
    """

    _attr_icon = "mdi:ev-station"
    _attr_native_min_value = 6
    _attr_native_max_value = 32
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "charger_current")

    @property
    def native_value(self) -> float | None:
        return self._client.requested_current_a

    async def async_set_native_value(self, value: float) -> None:
        await self._client.set_amp(int(value))
