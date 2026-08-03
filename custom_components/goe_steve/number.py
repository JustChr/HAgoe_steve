"""Number platform: runtime-adjustable tunables."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfEnergy,
    UnitOfPower,
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
    # --- Peak protection ------------------------------------------------------
    # The three limits are stored in watts (the engine's unit) but presented in kW,
    # because that is the unit the tariff and the meter reading are quoted in.
    GoeNumberDescription(
        key="peak_soft_limit",
        attr="peak_soft_w",
        icon="mdi:speedometer-slow",
        native_min_value=0.5,
        native_max_value=20,
        native_step=0.1,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        entity_category=EntityCategory.CONFIG,
        getter=lambda s: s.peak_soft_w / 1000.0,
        setter=lambda s, v: setattr(s, "peak_soft_w", v * 1000.0),
    ),
    GoeNumberDescription(
        key="peak_target_limit",
        attr="peak_target_w",
        icon="mdi:speedometer-medium",
        native_min_value=0.5,
        native_max_value=20,
        native_step=0.1,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        entity_category=EntityCategory.CONFIG,
        getter=lambda s: s.peak_target_w / 1000.0,
        setter=lambda s, v: setattr(s, "peak_target_w", v * 1000.0),
    ),
    GoeNumberDescription(
        key="peak_hard_limit",
        attr="peak_hard_w",
        icon="mdi:speedometer",
        native_min_value=0.5,
        native_max_value=20,
        native_step=0.1,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        entity_category=EntityCategory.CONFIG,
        getter=lambda s: s.peak_hard_w / 1000.0,
        setter=lambda s, v: setattr(s, "peak_hard_w", v * 1000.0),
    ),
    # How far under the month's record the allowance aims. Small on purpose: it only
    # has to swallow the projection's error, and every watt of it is headroom you
    # have already paid for. 0 means "aim exactly at the record" — the old behaviour.
    GoeNumberDescription(
        key="peak_month_buffer",
        attr="peak_month_buffer_w",
        icon="mdi:arrow-collapse-down",
        native_min_value=0,
        native_max_value=1,
        native_step=0.05,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        entity_category=EntityCategory.CONFIG,
        getter=lambda s: s.peak_month_buffer_w / 1000.0,
        setter=lambda s, v: setattr(s, "peak_month_buffer_w", v * 1000.0),
    ),
    GoeNumberDescription(
        key="shaving_reserve_soc",
        attr="shaving_reserve_soc",
        icon="mdi:home-battery",
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.CONFIG,
        getter=lambda s: s.shaving_reserve_soc,
        setter=lambda s, v: setattr(s, "shaving_reserve_soc", v),
    ),
    GoeNumberDescription(
        key="peak_min_soc",
        attr="peak_min_soc",
        icon="mdi:battery-alert-variant-outline",
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.CONFIG,
        getter=lambda s: s.peak_min_soc,
        setter=lambda s, v: setattr(s, "peak_min_soc", v),
    ),
    # --- Cheap-hour grid charging ---------------------------------------------
    GoeNumberDescription(
        key="grid_setpoint",
        attr="grid_setpoint_w",
        icon="mdi:transmission-tower",
        native_min_value=0,
        native_max_value=500,
        native_step=10,
        native_unit_of_measurement=UnitOfPower.WATT,
        entity_category=EntityCategory.CONFIG,
        getter=lambda s: s.grid_setpoint_w,
        setter=lambda s, v: setattr(s, "grid_setpoint_w", v),
    ),
    GoeNumberDescription(
        key="cheap_charge_power",
        attr="cheap_charge_power_w",
        icon="mdi:transmission-tower-import",
        native_min_value=0,
        native_max_value=10000,
        native_step=100,
        native_unit_of_measurement=UnitOfPower.WATT,
        entity_category=EntityCategory.CONFIG,
        getter=lambda s: s.cheap_charge_power_w,
        setter=lambda s, v: setattr(s, "cheap_charge_power_w", v),
    ),
    GoeNumberDescription(
        key="bright_day_target_soc",
        attr="bright_day_target_soc",
        icon="mdi:weather-sunny",
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.CONFIG,
        getter=lambda s: s.bright_day_target_soc,
        setter=lambda s, v: setattr(s, "bright_day_target_soc", v),
    ),
    GoeNumberDescription(
        key="dark_day_target_soc",
        attr="dark_day_target_soc",
        icon="mdi:weather-cloudy",
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.CONFIG,
        getter=lambda s: s.dark_day_target_soc,
        setter=lambda s, v: setattr(s, "dark_day_target_soc", v),
    ),
    GoeNumberDescription(
        key="peak_ready_soc",
        attr="peak_ready_soc",
        icon="mdi:battery-heart-outline",
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.CONFIG,
        getter=lambda s: s.peak_ready_soc,
        setter=lambda s, v: setattr(s, "peak_ready_soc", v),
    ),
    GoeNumberDescription(
        key="stock_up_target_soc",
        attr="stock_up_target_soc",
        icon="mdi:battery-plus-outline",
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.CONFIG,
        getter=lambda s: s.stock_up_target_soc,
        setter=lambda s, v: setattr(s, "stock_up_target_soc", v),
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
