"""The go-e + SteVe Smart Charging integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import GoeSteveCoordinator, SteVeCoordinator
from .services import async_setup_services, async_unload_services

type GoeSteveConfigEntry = ConfigEntry[GoeSteveCoordinator]

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.DATETIME,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: GoeSteveConfigEntry) -> bool:
    """Set up go-e + SteVe Smart Charging from a config entry."""
    coordinator = GoeSteveCoordinator(hass, entry)
    entry.runtime_data = coordinator

    # Optional SteVe linkage (Phase 3): authorization + metering. A SteVe outage
    # must not block the regulation brain, so we refresh non-blocking — entities
    # simply read as unavailable until SteVe answers.
    coordinator.steve = SteVeCoordinator.from_entry(hass, entry)
    if coordinator.steve is not None:
        await coordinator.steve.async_refresh()
        async_setup_services(hass)

    # First refresh runs the engine once; control entities restore their state
    # in their platform setup and push values into coordinator.settings.
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: GoeSteveConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        entry.runtime_data.steve = None
        async_unload_services(hass)
    return unloaded


async def _async_reload_entry(hass: HomeAssistant, entry: GoeSteveConfigEntry) -> None:
    """Reload the entry when its options change."""
    await hass.config_entries.async_reload(entry.entry_id)
