"""Download diagnostics: the settings, the mapping, and the field-test log.

Home Assistant offers this under the integration's ⋮ menu → *Download diagnostics*.
The test log (see ``testlog.py``) is the part that matters: one record per billing
quarter-hour and the shave / refill / held-car events, for the last 45 days.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import GoeSteveConfigEntry
from .const import CONF_STEVE_PASSWORD, CONF_STEVE_URL, CONF_STEVE_USERNAME

TO_REDACT = {CONF_STEVE_PASSWORD, CONF_STEVE_USERNAME, CONF_STEVE_URL}


def _plain(value: Any) -> Any:
    """A JSON-safe form of one setting (a departure time, a mode enum)."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: GoeSteveConfigEntry
) -> dict[str, Any]:
    """Return the diagnostics for one config entry."""
    coordinator = entry.runtime_data
    settings = coordinator.settings
    return {
        "version": entry.version,
        "data": async_redact_data(dict(entry.data), TO_REDACT),
        "options": async_redact_data(dict(entry.options), TO_REDACT),
        "settings": {
            key: _plain(value)
            for key, value in (asdict(settings) if is_dataclass(settings) else {}).items()
        },
        # True once a mapped house consumption read below the wallbox alone for two
        # minutes and was set aside until the next restart.
        "consumption_rejected": coordinator.consumption_rejected,
        "test_log": await coordinator.async_testlog_dump(),
    }
