"""Switch platform: master enable for smart control."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

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
            ManualChargeSwitch(coordinator),
            SmartControlSwitch(coordinator),
            AutoPhaseSwitch(coordinator),
            PeakGuardSwitch(coordinator),
            PeakFollowMonthSwitch(coordinator),
            GridChargeSwitch(coordinator),
        ]
    )


class _SettingSwitch(GoeSteveEntity, RestoreEntity, SwitchEntity):
    """A boolean setting that persists and feeds the engine.

    Subclasses declare ``_key`` (the entity key — unique id, translation key and the
    card's lookup all derive from it) and ``_setting`` (the
    :class:`RuntimeSettings` attribute). Same restore → mutate → write state →
    re-evaluate shape as the older hand-written switches above.
    """

    _attr_entity_category = EntityCategory.CONFIG
    _key: str
    _setting: str

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, self._key)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last := await self.async_get_last_state()) is not None and last.state in (
            "on",
            "off",
        ):
            setattr(self.coordinator.settings, self._setting, last.state == "on")

    @property
    def is_on(self) -> bool:
        return bool(getattr(self.coordinator.settings, self._setting))

    async def _set(self, value: bool) -> None:
        setattr(self.coordinator.settings, self._setting, value)
        self.async_write_ha_state()
        self.coordinator.request_apply()

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._set(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._set(False)


class PeakGuardSwitch(_SettingSwitch):
    """Master switch for the capacity-tariff layer.

    Off, the brain behaves exactly as it did before this feature existed — the
    quarter-hour is still *measured* (the sensors stay live, so you can watch your
    peaks for a month before committing) but nothing is ever written.

    On, it answers to this switch alone: unlike everything else here it keeps
    working with *Smart control* off, because the home battery's levers matter
    whether or not a car is plugged in, and a demand charge is money either way.
    """

    _attr_icon = "mdi:transmission-tower-off"
    _key = "peak_guard"
    _setting = "peak_guard_enabled"


class PeakFollowMonthSwitch(_SettingSwitch):
    """Allow this quarter-hour up to the month's existing peak.

    A demand charge is set by the month's single highest quarter-hour, so once one
    window has already gone to 5.2 kW, holding the next one under the target saves
    nothing at all — it only costs a slower charge for the rest of the month. Turn
    this off for a strict ceiling regardless of what the month has already cost.
    """

    _attr_icon = "mdi:calendar-arrow-right"
    _key = "peak_follow_month"
    _setting = "peak_follow_month"


class GridChargeSwitch(_SettingSwitch):
    """Buy energy into the home battery while the price is low.

    Commands the mapped ESS grid setpoint, which *is* total grid import — so the
    peak budget caps it by construction and it imports steadily rather than in the
    spike that would set a monthly peak.
    """

    _attr_icon = "mdi:transmission-tower-import"
    _key = "grid_charge"
    _setting = "grid_charge_enabled"


class ManualChargeSwitch(GoeSteveEntity, RestoreEntity, SwitchEntity):
    """Start/stop the charger in Manual mode (charging-mode 'Manual').

    A primary control (not config): in Manual mode this is the user's start/stop.
    It has no effect in the smart modes, where the brain decides on/off itself.
    """

    _attr_icon = "mdi:ev-station"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "manual_charge")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last := await self.async_get_last_state()) is not None:
            self.coordinator.settings.manual_charge = last.state == "on"

    @property
    def is_on(self) -> bool:
        return self.coordinator.settings.manual_charge

    async def async_turn_on(self, **kwargs: Any) -> None:
        self.coordinator.settings.manual_charge = True
        # Start/stop is the user taking over: leave the passive window.
        self.coordinator.set_manual_passive(False)
        self.async_write_ha_state()
        self.coordinator.request_apply()

    async def async_turn_off(self, **kwargs: Any) -> None:
        self.coordinator.settings.manual_charge = False
        # Start/stop is the user taking over: leave the passive window.
        self.coordinator.set_manual_passive(False)
        self.async_write_ha_state()
        self.coordinator.request_apply()


class SmartControlSwitch(GoeSteveEntity, RestoreEntity, SwitchEntity):
    """When off, the brain never writes the charger — manual control wins."""

    _attr_icon = "mdi:brain"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "smart_control")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last := await self.async_get_last_state()) is not None:
            self.coordinator.settings.smart_enabled = last.state == "on"

    @property
    def is_on(self) -> bool:
        return self.coordinator.settings.smart_enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        self.coordinator.settings.smart_enabled = True
        self.async_write_ha_state()
        self.coordinator.request_apply()

    async def async_turn_off(self, **kwargs: Any) -> None:
        self.coordinator.settings.smart_enabled = False
        self.async_write_ha_state()
        self.coordinator.request_apply()


class AutoPhaseSwitch(GoeSteveEntity, RestoreEntity, SwitchEntity):
    """When on, the brain switches 1↔3 phases to follow the solar surplus."""

    _attr_icon = "mdi:sine-wave"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "auto_phase")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last := await self.async_get_last_state()) is not None:
            self.coordinator.settings.auto_phase = last.state == "on"

    @property
    def is_on(self) -> bool:
        return self.coordinator.settings.auto_phase

    async def async_turn_on(self, **kwargs: Any) -> None:
        self.coordinator.settings.auto_phase = True
        self.async_write_ha_state()
        self.coordinator.request_apply()

    async def async_turn_off(self, **kwargs: Any) -> None:
        self.coordinator.settings.auto_phase = False
        self.async_write_ha_state()
        self.coordinator.request_apply()
