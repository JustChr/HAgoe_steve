"""SteVe authorization + remote-control services.

Registered once for the integration. Each service resolves the SteVe-enabled
config entry (the lone one by default, or an explicit ``entry_id``) and calls
the API client. Mutating SteVe is an outward-facing action, so failures surface
as :class:`HomeAssistantError` rather than being swallowed.
"""

from __future__ import annotations

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_STEVE_CHARGEBOX,
    CONF_STEVE_CONNECTOR,
    DEFAULT_STEVE_CONNECTOR,
    DOMAIN,
)
from .coordinator import SteVeCoordinator
from .steve_api import SteVeApiError

ATTR_ID_TAG = "id_tag"
ATTR_NAME = "name"
ATTR_TRANSACTION_ID = "transaction_id"
ATTR_CHARGE_BOX_ID = "charge_box_id"
ATTR_CONNECTOR_ID = "connector_id"
ATTR_ENTRY_ID = "entry_id"

SERVICE_AUTHORIZE_TAG = "authorize_tag"
SERVICE_BLOCK_TAG = "block_tag"
SERVICE_SET_TAG_NAME = "set_tag_name"
SERVICE_REMOTE_START = "remote_start"
SERVICE_REMOTE_STOP = "remote_stop"

_TAG_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_ID_TAG): cv.string,
        vol.Optional(ATTR_ENTRY_ID): cv.string,
    }
)
_SET_TAG_NAME_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ID_TAG): cv.string,
        vol.Required(ATTR_NAME): cv.string,
        vol.Optional(ATTR_ENTRY_ID): cv.string,
    }
)
_REMOTE_START_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_ID_TAG): cv.string,
        vol.Optional(ATTR_CHARGE_BOX_ID): cv.string,
        vol.Optional(ATTR_CONNECTOR_ID): cv.positive_int,
        vol.Optional(ATTR_ENTRY_ID): cv.string,
    }
)
_REMOTE_STOP_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_TRANSACTION_ID): cv.positive_int,
        vol.Optional(ATTR_CHARGE_BOX_ID): cv.string,
        vol.Optional(ATTR_ENTRY_ID): cv.string,
    }
)


def _steve_coordinator(hass: HomeAssistant, call: ServiceCall) -> SteVeCoordinator:
    """Find the SteVe coordinator, optionally narrowed by ``entry_id``."""
    wanted = call.data.get(ATTR_ENTRY_ID)
    matches: list[SteVeCoordinator] = []
    for entry in hass.config_entries.async_entries(DOMAIN):
        if wanted and entry.entry_id != wanted:
            continue
        coordinator = getattr(entry.runtime_data, "steve", None)
        if isinstance(coordinator, SteVeCoordinator):
            matches.append(coordinator)
    if not matches:
        raise ServiceValidationError(
            "No SteVe connection is configured. Add the SteVe server in the "
            "integration options first."
        )
    if len(matches) > 1:
        raise ServiceValidationError(
            "Multiple SteVe connections found — pass 'entry_id' to choose one."
        )
    return matches[0]


def _resolve_id_tag(coordinator: SteVeCoordinator, call: ServiceCall) -> str:
    """The explicit ``id_tag``, else the tag picked in the 'Selected tag' select."""
    id_tag = call.data.get(ATTR_ID_TAG) or coordinator.selected_tag
    if not id_tag:
        raise ServiceValidationError(
            "No 'id_tag' given and no tag is selected. Pick a tag in the "
            "'Selected tag' dropdown (or on the card) or pass 'id_tag'."
        )
    return id_tag


async def _async_authorize(hass: HomeAssistant, call: ServiceCall) -> None:
    coordinator = _steve_coordinator(hass, call)
    id_tag = _resolve_id_tag(coordinator, call)
    try:
        await coordinator.client.async_set_tag_blocked(id_tag, blocked=False)
    except SteVeApiError as err:
        raise HomeAssistantError(str(err)) from err
    await coordinator.async_request_refresh()


async def _async_block(hass: HomeAssistant, call: ServiceCall) -> None:
    coordinator = _steve_coordinator(hass, call)
    id_tag = _resolve_id_tag(coordinator, call)
    try:
        await coordinator.client.async_set_tag_blocked(id_tag, blocked=True)
    except SteVeApiError as err:
        raise HomeAssistantError(str(err)) from err
    await coordinator.async_request_refresh()


async def _async_set_tag_name(hass: HomeAssistant, call: ServiceCall) -> None:
    coordinator = _steve_coordinator(hass, call)
    try:
        await coordinator.client.async_set_tag_note(
            call.data[ATTR_ID_TAG], call.data[ATTR_NAME]
        )
    except SteVeApiError as err:
        raise HomeAssistantError(str(err)) from err
    await coordinator.async_request_refresh()


async def _async_remote_start(hass: HomeAssistant, call: ServiceCall) -> None:
    coordinator = _steve_coordinator(hass, call)
    cfg = coordinator.config_entry.data
    charge_box = call.data.get(ATTR_CHARGE_BOX_ID) or cfg.get(CONF_STEVE_CHARGEBOX)
    if not charge_box:
        raise ServiceValidationError(
            "No charge box configured — set one in options or pass 'charge_box_id'."
        )
    connector = call.data.get(
        ATTR_CONNECTOR_ID,
        cfg.get(CONF_STEVE_CONNECTOR, DEFAULT_STEVE_CONNECTOR),
    )
    id_tag = _resolve_id_tag(coordinator, call)
    try:
        await coordinator.client.async_remote_start(
            charge_box, int(connector), id_tag
        )
    except SteVeApiError as err:
        raise HomeAssistantError(str(err)) from err
    await coordinator.async_request_refresh()


async def _async_remote_stop(hass: HomeAssistant, call: ServiceCall) -> None:
    coordinator = _steve_coordinator(hass, call)
    cfg = coordinator.config_entry.data
    transaction_id = call.data.get(ATTR_TRANSACTION_ID)
    charge_box = call.data.get(ATTR_CHARGE_BOX_ID) or cfg.get(CONF_STEVE_CHARGEBOX)

    # Default to the single active session when not told which one to stop.
    if transaction_id is None:
        active = coordinator.data.active if coordinator.data else []
        if len(active) != 1:
            raise ServiceValidationError(
                "Specify 'transaction_id' — there is not exactly one active session."
            )
        transaction_id = active[0].id
        charge_box = charge_box or active[0].charge_box_id
    if transaction_id is None or not charge_box:
        raise ServiceValidationError(
            "Could not determine the transaction or charge box to stop."
        )
    try:
        await coordinator.client.async_remote_stop(charge_box, int(transaction_id))
    except SteVeApiError as err:
        raise HomeAssistantError(str(err)) from err
    await coordinator.async_request_refresh()


def async_setup_services(hass: HomeAssistant) -> None:
    """Register the SteVe services once for the integration."""
    if hass.services.has_service(DOMAIN, SERVICE_AUTHORIZE_TAG):
        return

    async def authorize(call: ServiceCall) -> None:
        await _async_authorize(hass, call)

    async def block(call: ServiceCall) -> None:
        await _async_block(hass, call)

    async def set_tag_name(call: ServiceCall) -> None:
        await _async_set_tag_name(hass, call)

    async def remote_start(call: ServiceCall) -> None:
        await _async_remote_start(hass, call)

    async def remote_stop(call: ServiceCall) -> None:
        await _async_remote_stop(hass, call)

    hass.services.async_register(DOMAIN, SERVICE_AUTHORIZE_TAG, authorize, _TAG_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_BLOCK_TAG, block, _TAG_SCHEMA)
    hass.services.async_register(
        DOMAIN, SERVICE_SET_TAG_NAME, set_tag_name, _SET_TAG_NAME_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_REMOTE_START, remote_start, _REMOTE_START_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_REMOTE_STOP, remote_stop, _REMOTE_STOP_SCHEMA
    )


def async_unload_services(hass: HomeAssistant) -> None:
    """Remove services when the last entry is unloaded."""
    if any(
        getattr(entry.runtime_data, "steve", None) is not None
        for entry in hass.config_entries.async_entries(DOMAIN)
    ):
        return
    for service in (
        SERVICE_AUTHORIZE_TAG,
        SERVICE_BLOCK_TAG,
        SERVICE_SET_TAG_NAME,
        SERVICE_REMOTE_START,
        SERVICE_REMOTE_STOP,
    ):
        hass.services.async_remove(DOMAIN, service)
