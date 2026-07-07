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
from .entity import GoeMqttEntity, GoeSteveEntity, SteVeEntity
from .goe_mqtt import (
    FRC_NEUTRAL,
    FRC_OFF,
    FRC_ON,
    PSM_AUTO,
    PSM_SINGLE,
    PSM_THREE,
)
from .steve_api import SteVeTag

# go-e ``psm`` (phaseSwitchMode) ↔ select option (1 = single, 2 = three phase).
_PSM_TO_OPTION = {PSM_AUTO: "auto", PSM_SINGLE: "1", PSM_THREE: "3"}
_OPTION_TO_PSM = {option: psm for psm, option in _PSM_TO_OPTION.items()}

# go-e ``frc`` (forceState) ↔ select option.
_FRC_TO_OPTION = {FRC_NEUTRAL: "neutral", FRC_OFF: "off", FRC_ON: "on"}
_OPTION_TO_FRC = {option: frc for frc, option in _FRC_TO_OPTION.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GoeSteveConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    entities: list[SelectEntity] = [
        ChargingModeSelect(coordinator),
        BatteryHoldModeSelect(coordinator),
        ManualPhaseSelect(coordinator),
        ChargerPhaseSelect(coordinator),
        ChargerForceSelect(coordinator),
    ]
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


class BatteryHoldModeSelect(GoeSteveEntity, RestoreEntity, SelectEntity):
    """The home-battery three-way: let the brain decide, or override it.

    * **Auto** — the arbiter holds the battery while it deliberately grid-charges
      (cheap hours, the departure plan, Fast) and lets it buffer during solar; the
      battery-hold sensor shows the brain's live choice.
    * **Hold** — always block discharge into the car, whatever the mode.
    * **Free** — never block; the battery may feed the car.

    Maps to ``RuntimeSettings.battery_hold_mode`` (the engine's finalizer applies
    it). Mirrors the Manual-phase select's restore/apply shape.
    """

    _attr_icon = "mdi:home-battery"
    _attr_options = ["auto", "hold", "free"]

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "battery_hold_mode")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last := await self.async_get_last_state()) is not None:
            if last.state in self._attr_options:
                self.coordinator.settings.battery_hold_mode = last.state

    @property
    def current_option(self) -> str:
        return self.coordinator.settings.battery_hold_mode

    async def async_select_option(self, option: str) -> None:
        if option not in self._attr_options:
            return
        self.coordinator.settings.battery_hold_mode = option
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


class ChargerPhaseSelect(GoeMqttEntity, SelectEntity):
    """The charger's phase-switch mode (``psm``), live over MQTT.

    Reflects the go-e's own setting: Auto lets the charger decide, 1/3 force the
    phase count. The brain overrides this while auto-phase or Manual phase control
    is active; by hand it's authoritative when the brain isn't controlling.
    """

    _attr_icon = "mdi:sine-wave"
    _attr_options = ["auto", "1", "3"]

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "charger_phases")

    @property
    def current_option(self) -> str | None:
        return _PSM_TO_OPTION.get(self._client.phase_mode)

    async def async_select_option(self, option: str) -> None:
        psm = _OPTION_TO_PSM.get(option)
        if psm is not None:
            await self._client.set_phase_mode(psm)


class ChargerForceSelect(GoeMqttEntity, SelectEntity):
    """The charger's force-state (``frc``): Neutral / Off / On, live over MQTT.

    Neutral hands control back to the charger's own logic (scheduler, surplus,
    …); Off blocks charging; On forces it. The brain drives this to start/stop;
    setting it by hand is authoritative only when the brain isn't controlling.
    """

    _attr_icon = "mdi:ev-station"
    _attr_options = ["neutral", "off", "on"]

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "charger_force")

    @property
    def current_option(self) -> str | None:
        return _FRC_TO_OPTION.get(self._client.force_state)

    async def async_select_option(self, option: str) -> None:
        frc = _OPTION_TO_FRC.get(option)
        if frc is not None:
            await self._client.set_force(frc)


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
