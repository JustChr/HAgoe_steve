"""The go-e + SteVe Smart Charging integration."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import GoeSteveCoordinator, SteVeCoordinator
from .services import async_setup_services, async_unload_services

_LOGGER = logging.getLogger(__name__)

type GoeSteveConfigEntry = ConfigEntry[GoeSteveCoordinator]

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.DATETIME,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]

# Bundled Lovelace card — served and registered automatically so the user never
# has to add a dashboard resource by hand.
CARD_URL = f"/{DOMAIN}/goe-steve-card.js"
CARD_FILENAME = "goe-steve-card.js"
_FRONTEND_REGISTERED = f"{DOMAIN}_frontend_registered"


async def async_setup_entry(hass: HomeAssistant, entry: GoeSteveConfigEntry) -> bool:
    """Set up go-e + SteVe Smart Charging from a config entry."""
    await _async_register_frontend(hass)

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

    # Re-evaluate the moment a power input changes, not just on the 30 s poll,
    # so surplus tracking reacts to clouds/appliances within seconds.
    entry.async_on_unload(coordinator.async_setup_input_triggers())

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


async def _async_register_frontend(hass: HomeAssistant) -> None:
    """Serve and register the bundled Lovelace card exactly once.

    Failure here is non-fatal: the integration still works, the user just won't
    get the card auto-loaded (they can add it as a manual resource instead).
    """
    if hass.data.get(_FRONTEND_REGISTERED):
        return

    card_dir = Path(__file__).parent / "www"
    card_path = card_dir / CARD_FILENAME
    if not card_path.is_file():
        _LOGGER.debug("Bundled card %s not found; skipping auto-registration", card_path)
        return

    try:
        from homeassistant.components.http import StaticPathConfig

        await hass.http.async_register_static_paths(
            [StaticPathConfig(f"/{DOMAIN}", str(card_dir), cache_headers=False)]
        )

        from homeassistant.components.frontend import add_extra_js_url

        # Cache-bust on file mtime so a HACS update reloads the card.
        version = int(card_path.stat().st_mtime)
        add_extra_js_url(hass, f"{CARD_URL}?v={version}")
        hass.data[_FRONTEND_REGISTERED] = True
        _LOGGER.debug("Registered Lovelace card at %s", CARD_URL)
    except Exception as err:  # noqa: BLE001 - never block setup on a card hiccup
        _LOGGER.warning("Could not auto-register the Lovelace card: %s", err)
