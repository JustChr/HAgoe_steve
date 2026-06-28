"""Config + options flow for go-e + SteVe Smart Charging.

UX-focused: every field is an entity picker filtered to plausible candidates, the
required signals come first, and optional ones (PV/battery) can be left blank —
the engine simply runs with less information.
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_BATTERY_HOLD,
    CONF_BATTERY_POWER,
    CONF_BATTERY_SOC,
    CONF_GOE_CHARGING,
    CONF_GOE_CONNECTED,
    CONF_GOE_CURRENT,
    CONF_GOE_ENERGY,
    CONF_GOE_FORCE,
    CONF_GOE_PHASE,
    CONF_GOE_POWER,
    CONF_GRID_POWER,
    CONF_PHASES,
    CONF_PRICE,
    CONF_PRICE_FORECAST_ATTR,
    CONF_PV_POWER,
    CONF_STEVE_CHARGEBOX,
    CONF_STEVE_CONNECTOR,
    CONF_STEVE_PASSWORD,
    CONF_STEVE_URL,
    CONF_STEVE_USERNAME,
    CONF_VOLTAGE,
    DEFAULT_NAME,
    DEFAULT_PHASES,
    DEFAULT_PRICE_FORECAST_ATTR,
    DEFAULT_STEVE_CONNECTOR,
    DEFAULT_VOLTAGE,
    DOMAIN,
)

_POWER_SENSOR = selector.EntitySelector(
    selector.EntitySelectorConfig(domain="sensor", device_class="power")
)
_OPTIONAL_POWER_SENSOR = _POWER_SENSOR
_ENERGY_SENSOR = selector.EntitySelector(
    selector.EntitySelectorConfig(domain="sensor", device_class="energy")
)
_BATTERY_SENSOR = selector.EntitySelector(
    selector.EntitySelectorConfig(domain="sensor", device_class="battery")
)
_BATTERY_HOLD_ENTITY = selector.EntitySelector(
    selector.EntitySelectorConfig(domain=["switch", "input_boolean"])
)
_NUMBER_ENTITY = selector.EntitySelector(
    selector.EntitySelectorConfig(domain="number")
)
_PHASE_ENTITY = selector.EntitySelector(
    selector.EntitySelectorConfig(domain=["number", "select"])
)
_FORCE_ENTITY = selector.EntitySelector(
    selector.EntitySelectorConfig(domain=["select", "number"])
)
_PRICE_ENTITY = selector.EntitySelector(
    selector.EntitySelectorConfig(domain=["sensor", "input_number"])
)
_TEXT = selector.TextSelector()
_URL = selector.TextSelector(selector.TextSelectorConfig(type="url"))
_PASSWORD = selector.TextSelector(selector.TextSelectorConfig(type="password"))
_STATUS_ENTITY = selector.EntitySelector(
    selector.EntitySelectorConfig(domain=["binary_sensor", "sensor"])
)


def _charger_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_GOE_CURRENT, default=defaults.get(CONF_GOE_CURRENT)
            ): _NUMBER_ENTITY,
            vol.Optional(
                CONF_GOE_PHASE,
                description={"suggested_value": defaults.get(CONF_GOE_PHASE)},
            ): _PHASE_ENTITY,
            vol.Optional(
                CONF_GOE_FORCE,
                description={"suggested_value": defaults.get(CONF_GOE_FORCE)},
            ): _FORCE_ENTITY,
            vol.Required(
                CONF_GOE_CONNECTED, default=defaults.get(CONF_GOE_CONNECTED)
            ): _STATUS_ENTITY,
            vol.Optional(
                CONF_GOE_CHARGING,
                description={"suggested_value": defaults.get(CONF_GOE_CHARGING)},
            ): _STATUS_ENTITY,
            vol.Optional(
                CONF_GOE_POWER,
                description={"suggested_value": defaults.get(CONF_GOE_POWER)},
            ): _OPTIONAL_POWER_SENSOR,
            vol.Optional(
                CONF_GOE_ENERGY,
                description={"suggested_value": defaults.get(CONF_GOE_ENERGY)},
            ): _ENERGY_SENSOR,
            vol.Required(
                CONF_VOLTAGE, default=defaults.get(CONF_VOLTAGE, DEFAULT_VOLTAGE)
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=100, max=400, step=1, unit_of_measurement="V", mode="box"
                )
            ),
            vol.Required(
                CONF_PHASES, default=defaults.get(CONF_PHASES, DEFAULT_PHASES)
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=["1", "3"], translation_key="phases"
                )
            ),
        }
    )


def _energy_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_GRID_POWER, default=defaults.get(CONF_GRID_POWER)
            ): _POWER_SENSOR,
            vol.Optional(
                CONF_PV_POWER,
                description={"suggested_value": defaults.get(CONF_PV_POWER)},
            ): _OPTIONAL_POWER_SENSOR,
            vol.Optional(
                CONF_BATTERY_SOC,
                description={"suggested_value": defaults.get(CONF_BATTERY_SOC)},
            ): _BATTERY_SENSOR,
            vol.Optional(
                CONF_BATTERY_POWER,
                description={"suggested_value": defaults.get(CONF_BATTERY_POWER)},
            ): _OPTIONAL_POWER_SENSOR,
            vol.Optional(
                CONF_BATTERY_HOLD,
                description={"suggested_value": defaults.get(CONF_BATTERY_HOLD)},
            ): _BATTERY_HOLD_ENTITY,
            vol.Optional(
                CONF_PRICE,
                description={"suggested_value": defaults.get(CONF_PRICE)},
            ): _PRICE_ENTITY,
            vol.Optional(
                CONF_PRICE_FORECAST_ATTR,
                description={
                    "suggested_value": defaults.get(CONF_PRICE_FORECAST_ATTR)
                },
            ): _TEXT,
        }
    )


def _steve_schema(defaults: dict[str, Any]) -> vol.Schema:
    """Optional SteVe linkage: leave the URL blank to skip it entirely."""
    return vol.Schema(
        {
            vol.Optional(
                CONF_STEVE_URL,
                description={"suggested_value": defaults.get(CONF_STEVE_URL)},
            ): _URL,
            vol.Optional(
                CONF_STEVE_USERNAME,
                description={"suggested_value": defaults.get(CONF_STEVE_USERNAME, "admin")},
            ): _TEXT,
            vol.Optional(
                CONF_STEVE_PASSWORD,
                description={"suggested_value": defaults.get(CONF_STEVE_PASSWORD)},
            ): _PASSWORD,
            vol.Optional(
                CONF_STEVE_CHARGEBOX,
                description={"suggested_value": defaults.get(CONF_STEVE_CHARGEBOX)},
            ): _TEXT,
            vol.Optional(
                CONF_STEVE_CONNECTOR,
                default=defaults.get(CONF_STEVE_CONNECTOR, DEFAULT_STEVE_CONNECTOR),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=10, step=1, mode="box")
            ),
        }
    )


# Known provider attribute names that hold an hourly forecast, in priority order.
_FORECAST_ATTR_CANDIDATES = (
    DEFAULT_PRICE_FORECAST_ATTR,  # "raw_today" — Nordpool
    "data",  # EPEX Spot
    "prices_today",  # EnergyZero / Frank Energie
    "forecast",
    "today",
    "prices",
)


def _detect_forecast_attr(hass: Any, entity_id: str) -> str | None:
    """Best-effort: find the attribute on ``entity_id`` holding a price forecast.

    Reuses the tolerant forecast parser so an attribute only qualifies if it
    actually yields usable slots. Known provider names win; otherwise we fall back
    to the first attribute whose value parses into a forecast.
    """
    from .forecast import parse_forecast

    state = hass.states.get(entity_id)
    if state is None:
        return None
    attrs = state.attributes
    for name in _FORECAST_ATTR_CANDIDATES:
        if name in attrs and parse_forecast(attrs[name]):
            return name
    for name, value in attrs.items():
        if parse_forecast(value):
            return name
    return None


def _apply_forecast_autodetect(hass: Any, data: dict[str, Any]) -> None:
    """Fill in the forecast attribute from the selected price entity when blank."""
    price = data.get(CONF_PRICE)
    if not price or data.get(CONF_PRICE_FORECAST_ATTR):
        return
    detected = _detect_forecast_attr(hass, price)
    if detected:
        data[CONF_PRICE_FORECAST_ATTR] = detected


def _normalize(data: dict[str, Any]) -> dict[str, Any]:
    """Coerce numeric strings (phases/voltage/connector) and drop empty optionals."""
    out = {k: v for k, v in data.items() if v not in (None, "")}
    if CONF_PHASES in out:
        out[CONF_PHASES] = int(out[CONF_PHASES])
    if CONF_VOLTAGE in out:
        out[CONF_VOLTAGE] = float(out[CONF_VOLTAGE])
    if CONF_STEVE_CONNECTOR in out:
        out[CONF_STEVE_CONNECTOR] = int(out[CONF_STEVE_CONNECTOR])
    return out


class GoeSteveConfigFlow(ConfigFlow, domain=DOMAIN):
    """Two-step setup: energy sources, then the charger."""

    VERSION = 1

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._data.update(_normalize(user_input))
            _apply_forecast_autodetect(self.hass, self._data)
            return await self.async_step_charger()
        return self.async_show_form(
            step_id="user", data_schema=_energy_schema({})
        )

    async def async_step_charger(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._data.update(_normalize(user_input))
            return await self.async_step_steve()
        return self.async_show_form(
            step_id="charger", data_schema=_charger_schema({})
        )

    async def async_step_steve(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._data.update(_normalize(user_input))
            return self.async_create_entry(
                title=self._data.get(CONF_NAME, DEFAULT_NAME), data=self._data
            )
        return self.async_show_form(
            step_id="steve", data_schema=_steve_schema({})
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return GoeSteveOptionsFlow()


class GoeSteveOptionsFlow(OptionsFlow):
    """Let the user re-map any entity after setup."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        entry = self.config_entry
        if user_input is not None:
            merged = {**entry.data, **_normalize(user_input)}
            _apply_forecast_autodetect(self.hass, merged)
            self.hass.config_entries.async_update_entry(entry, data=merged)
            return self.async_create_entry(title="", data={})

        defaults = dict(entry.data)
        schema = (
            _energy_schema(defaults)
            .extend(_charger_schema(defaults).schema)
            .extend(_steve_schema(defaults).schema)
        )
        return self.async_show_form(step_id="init", data_schema=schema)
