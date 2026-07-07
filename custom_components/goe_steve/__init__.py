"""The go-e + SteVe Smart Charging integration."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers import restore_state

from .const import (
    CONF_BATTERY_RESERVE_SEED,
    CONF_GOE_BASE_TOPIC,
    CONF_GOE_CHARGING,
    CONF_GOE_CONNECTED,
    CONF_GOE_CURRENT,
    CONF_GOE_ENERGY,
    CONF_GOE_FORCE,
    CONF_GOE_PHASE,
    CONF_GOE_POWER,
    DOMAIN,
)
from .coordinator import GoeSteveCoordinator, SteVeCoordinator
from .services import async_setup_services, async_unload_services

# Legacy (pre-v4) charger-entity keys the v3→v4 migration strips once the direct
# MQTT base topic takes over.
_LEGACY_GOE_KEYS = (
    CONF_GOE_CURRENT,
    CONF_GOE_PHASE,
    CONF_GOE_FORCE,
    CONF_GOE_CONNECTED,
    CONF_GOE_CHARGING,
    CONF_GOE_POWER,
    CONF_GOE_ENERGY,
)

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

    # v4+: the charger link is direct go-e MQTT. A pre-v4 entry migrated to v4 has
    # no base topic yet (an entity map can't become a topic) — guide the user to
    # reconfigure instead of subscribing to nothing.
    if not entry.data.get(CONF_GOE_BASE_TOPIC):
        ir.async_create_issue(
            hass,
            DOMAIN,
            f"reconfigure_topic_{entry.entry_id}",
            is_fixable=False,
            severity=ir.IssueSeverity.ERROR,
            translation_key="reconfigure_topic",
        )
        raise ConfigEntryError(
            "The go-e charger now connects over MQTT — open the integration's "
            "options and set the charger's base topic to finish the upgrade."
        )
    ir.async_delete_issue(hass, DOMAIN, f"reconfigure_topic_{entry.entry_id}")

    coordinator = GoeSteveCoordinator(hass, entry)
    entry.runtime_data = coordinator

    # Subscribe to the charger's MQTT topics before the first engine run so its
    # retained state is primed. Unsubscribe on unload.
    await coordinator.goe.async_start()
    entry.async_on_unload(coordinator.goe.async_stop)

    # Optional SteVe linkage (Phase 3): authorization + metering. A SteVe outage
    # must not block the regulation brain, so we refresh non-blocking — entities
    # simply read as unavailable until SteVe answers.
    coordinator.steve = SteVeCoordinator.from_entry(hass, entry)
    if coordinator.steve is not None:
        await coordinator.steve.async_refresh()
        async_setup_services(hass)

    # Recall whether we own the battery-hold switch (persisted across restarts)
    # before the first engine run, so a hands-off first cycle can release a
    # switch we left on — the mapped entity may gate the whole house's battery.
    await coordinator.async_restore_hold_state()

    # First refresh runs the engine once; control entities restore their state
    # in their platform setup and push values into coordinator.settings.
    await coordinator.async_config_entry_first_refresh()

    # Re-evaluate the moment a power input changes, not just on the 30 s poll,
    # so surplus tracking reacts to clouds/appliances within seconds.
    entry.async_on_unload(coordinator.async_setup_input_triggers())

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # The v1→v2 reserve seed has been applied by the reserve number's restore
    # above — drop it so it can never override a later user choice. Done before
    # the update listener is registered, so this write does not trigger a reload.
    if CONF_BATTERY_RESERVE_SEED in entry.data:
        data = dict(entry.data)
        data.pop(CONF_BATTERY_RESERVE_SEED)
        hass.config_entries.async_update_entry(entry, data=data)

    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    return True


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old config entries to the current schema.

    v1 → v2: the Protect/Share/Assist battery policy and the Assist floor
    collapse into the single home-battery reserve line. The stored policy maps
    onto a one-shot reserve seed (applied by the reserve number instead of its
    own restored state, then removed from the entry):

    * ``protect`` → 100 % — the battery never powers the car.
    * ``share``   → no seed — the line stays at the restored reserve.
    * ``assist``  → the old floor — the battery backs the car down to it.

    v2 → v3: the strategies + arbiter engine. The "Minimum charge power" number
    (``min_grid_floor``) is gone — Solar + minimum now simply guarantees the
    minimum current — so its registry entry is dropped. The old charging modes
    map onto the new presets when the mode select restores its state.

    v3 → v4: the charger link moves to direct go-e MQTT. The six mapped entity
    keys are dropped; there's no way to derive a topic from them, so the entry
    lands without a base topic and setup raises a reconfigure prompt.
    """
    if entry.version > 4:
        return False  # future schema from a newer install — don't guess

    if entry.version == 1:
        registry = er.async_get(hass)
        data = dict(entry.data)
        policy_id = registry.async_get_entity_id(
            "select", DOMAIN, f"{entry.entry_id}_battery_policy"
        )
        floor_id = registry.async_get_entity_id(
            "number", DOMAIN, f"{entry.entry_id}_battery_floor_soc"
        )
        try:
            last_states = restore_state.async_get(hass).last_states
            policy = (
                last_states[policy_id].state.state
                if policy_id and policy_id in last_states
                else None
            )
            if policy == "protect":
                data[CONF_BATTERY_RESERVE_SEED] = 100.0
            elif policy == "assist":
                floor = 20.0
                if floor_id and floor_id in last_states:
                    try:
                        floor = float(last_states[floor_id].state.state)
                    except (TypeError, ValueError):
                        pass
                data[CONF_BATTERY_RESERVE_SEED] = floor
        except Exception:  # noqa: BLE001 - a failed mapping must never block setup
            _LOGGER.warning(
                "Could not map the old battery policy onto the reserve line; "
                "keeping the restored reserve value"
            )
        # The policy select and floor number no longer exist — drop their
        # registry entries so they don't linger as unavailable ghosts.
        for entity_id in (policy_id, floor_id):
            if entity_id:
                registry.async_remove(entity_id)
        hass.config_entries.async_update_entry(entry, data=data, version=2)
        _LOGGER.info("Migrated config entry to v2 (home-battery reserve line)")

    if entry.version == 2:
        registry = er.async_get(hass)
        floor_id = registry.async_get_entity_id(
            "number", DOMAIN, f"{entry.entry_id}_min_grid_floor"
        )
        if floor_id:
            registry.async_remove(floor_id)
        hass.config_entries.async_update_entry(entry, version=3)
        _LOGGER.info("Migrated config entry to v3 (strategies + arbiter engine)")

    if entry.version == 3:
        # Drop the legacy mapped-entity keys; the base topic is set later via the
        # reconfigure prompt raised in async_setup_entry.
        data = {k: v for k, v in entry.data.items() if k not in _LEGACY_GOE_KEYS}
        hass.config_entries.async_update_entry(entry, data=data, version=4)
        _LOGGER.info("Migrated config entry to v4 (direct go-e MQTT charger link)")

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

        # Cache-bust on file mtime so a HACS update reloads the card.
        version = int(card_path.stat().st_mtime)

        # Prefer a real Lovelace resource: the dashboard *awaits* its resources
        # before rendering custom cards, so the element is defined in time. The
        # older `add_extra_js_url` route loads in parallel and Lovelace does not
        # wait for it, which races and yields "Custom element doesn't exist". Fall
        # back to it only for YAML-mode dashboards (no writable resource store).
        if not await _async_register_card_resource(hass, version):
            from homeassistant.components.frontend import add_extra_js_url

            add_extra_js_url(hass, f"{CARD_URL}?v={version}")

        hass.data[_FRONTEND_REGISTERED] = True
        _LOGGER.debug("Registered Lovelace card at %s", CARD_URL)
    except Exception as err:  # noqa: BLE001 - never block setup on a card hiccup
        _LOGGER.warning("Could not auto-register the Lovelace card: %s", err)


async def _async_register_card_resource(hass: HomeAssistant, version: int) -> bool:
    """Register the card as a storage-mode Lovelace resource (deduped/updated).

    Returns True when handled, False when there is no writable resource store
    (e.g. YAML-mode Lovelace), so the caller can fall back to add_extra_js_url.
    """
    lovelace = hass.data.get("lovelace")
    resources = getattr(lovelace, "resources", None)
    # Only the storage-backed collection is writable; YAML mode is read-only.
    if resources is None or type(resources).__name__ != "ResourceStorageCollection":
        return False

    if not resources.loaded:
        await resources.async_load()

    target = f"{CARD_URL}?v={version}"
    for item in resources.async_items():
        if item.get("url", "").split("?")[0] == CARD_URL:
            if item.get("url") != target:  # bump the cache-bust after an update
                await resources.async_update_item(
                    item["id"], {"res_type": "module", "url": target}
                )
            return True

    await resources.async_create_item({"res_type": "module", "url": target})
    return True
