"""Select platform: charging mode, manual phases, and the SteVe tag picker."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import GoeSteveConfigEntry
from .coordinator import SteVeCoordinator
from .engine import LEGACY_MODE_MAP, SUPPORTED_MODES, ChargingMode
from .entity import GoeSteveEntity, SteVeEntity
from .steve_api import SteVeTag


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GoeSteveConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    entities: list[SelectEntity] = [
        ChargingModeSelect(coordinator),
    ]
    # Manual phase choice only makes sense when a phase-switch entity is mapped.
    if coordinator.has_phase_control:
        entities.append(ManualPhaseSelect(coordinator))
    if coordinator.steve is not None:
        entities.append(SteVeTagSelect(coordinator.steve))
    async_add_entities(entities)


class ChargingModeSelect(GoeSteveEntity, RestoreEntity, SelectEntity):
    """The headline control: pick how the car should charge."""

    _attr_icon = "mdi:ev-station"
    _attr_options = [mode.value for mode in SUPPORTED_MODES]

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "charging_mode")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last := await self.async_get_last_state()) is None:
            return
        # v2 → v3: the old mode zoo maps onto the presets, so a restored legacy
        # value (e.g. "combined") lands on its equivalent instead of resetting.
        restored = last.state
        if restored in LEGACY_MODE_MAP:
            self.coordinator.settings.mode = LEGACY_MODE_MAP[restored]
        elif restored in self._attr_options:
            self.coordinator.settings.mode = ChargingMode(restored)

    @property
    def current_option(self) -> str:
        return self.coordinator.settings.mode.value

    async def async_select_option(self, option: str) -> None:
        mode = ChargingMode(option)
        self.coordinator.settings.mode = mode
        # Switching into Manual should not disturb the charger: stay passive until
        # the user touches a manual control. Picking any other mode drives at once.
        self.coordinator.set_manual_passive(mode is ChargingMode.MANUAL)
        self.async_write_ha_state()
        self.coordinator.request_apply()


class ManualPhaseSelect(GoeSteveEntity, RestoreEntity, SelectEntity):
    """Single- vs three-phase choice for Manual mode.

    A primary control (not config): in Manual mode the user picks the phase
    count directly and the brain writes the go-e phase switch. The smart modes
    use the automatic phase logic instead and ignore this.
    """

    _attr_icon = "mdi:sine-wave"
    _attr_options = ["1", "3"]

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "manual_phases")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last := await self.async_get_last_state()) is not None:
            if last.state in self._attr_options:
                self.coordinator.settings.manual_phases = int(last.state)

    @property
    def current_option(self) -> str:
        return str(self.coordinator.settings.manual_phases)

    async def async_select_option(self, option: str) -> None:
        if option not in self._attr_options:
            return
        self.coordinator.settings.manual_phases = int(option)
        # Using a manual control engages Manual: take over the charger from here.
        self.coordinator.set_manual_passive(False)
        self.async_write_ha_state()
        self.coordinator.request_apply()


class SteVeTagSelect(SteVeEntity, RestoreEntity, SelectEntity):
    """Pick one of SteVe's authorized tags by its friendly name.

    Options are the *notes* (friendly names) of the non-blocked tags SteVe
    knows — so a user selects a name, never a raw RFID UID. The chosen tag's
    id-tag is stored on the SteVe coordinator and used as the default by the
    ``authorize_tag`` / ``block_tag`` / ``remote_start`` services (and the card's
    authorize/start actions). Blocked tags are intentionally excluded: there's
    nothing to authorize/start with a card that's already barred.
    """

    _attr_icon = "mdi:card-account-details-outline"

    def __init__(self, coordinator: SteVeCoordinator) -> None:
        super().__init__(coordinator, "selected_tag")

    @property
    def _tags(self) -> list[SteVeTag]:
        data = self.coordinator.data
        return [tag for tag in data.tags if not tag.blocked] if data else []

    @property
    def options(self) -> list[str]:
        # De-duplicate names (two tags may share a note) while keeping order.
        names: dict[str, None] = {}
        for tag in self._tags:
            names.setdefault(tag.name, None)
        return list(names)

    @property
    def current_option(self) -> str | None:
        selected = self.coordinator.selected_tag
        if selected is None:
            return None
        tag = next((t for t in self._tags if t.id_tag == selected), None)
        return tag.name if tag is not None else None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last := await self.async_get_last_state()) is None:
            return
        if last.state in (None, "", STATE_UNKNOWN, STATE_UNAVAILABLE):
            return
        # Restore by matching the saved friendly name to a current tag.
        tag = next((t for t in self._tags if t.name == last.state), None)
        if tag is not None:
            self.coordinator.selected_tag = tag.id_tag

    async def async_select_option(self, option: str) -> None:
        tag = next((t for t in self._tags if t.name == option), None)
        if tag is None:
            return
        self.coordinator.selected_tag = tag.id_tag
        self.async_write_ha_state()
