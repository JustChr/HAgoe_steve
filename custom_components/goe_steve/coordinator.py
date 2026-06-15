"""Coordinator: reads mapped HA entities, runs the engine, writes the charger."""

from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import CALLBACK_TYPE, Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util import dt as dt_util

from .const import (
    CONF_BATTERY_POWER,
    CONF_BATTERY_SOC,
    CONF_GOE_CHARGING,
    CONF_GOE_CONNECTED,
    CONF_GOE_CURRENT,
    CONF_GOE_PHASE,
    CONF_GOE_POWER,
    CONF_GRID_POWER,
    CONF_PRICE,
    CONF_PRICE_FORECAST_ATTR,
    CONF_PV_POWER,
    CONF_PHASES,
    CONF_STEVE_PASSWORD,
    CONF_STEVE_URL,
    CONF_STEVE_USERNAME,
    CONF_VOLTAGE,
    DEFAULT_AUTO_PHASE,
    DEFAULT_BATTERY_FLOOR_SOC,
    DEFAULT_BATTERY_RESERVE_SOC,
    DEFAULT_CHEAP_PRICE,
    DEFAULT_MAX_CURRENT,
    DEFAULT_MIN_CURRENT,
    DEFAULT_MIN_GRID_FLOOR_W,
    DEFAULT_PHASES,
    DEFAULT_PRICE_FORECAST_ATTR,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TARGET_ENERGY_KWH,
    DEFAULT_VOLTAGE,
    DOMAIN,
    MIN_OFF_DWELL_S,
    MIN_ON_DWELL_S,
    MIN_UPDATE_INTERVAL_S,
    MIN_WRITE_DELTA_A,
    PHASE_DWELL_S,
    SMOOTHING_SAMPLES,
    STEVE_SCAN_INTERVAL,
)
from .engine import (
    BatteryPolicy,
    ChargerInputs,
    ChargingMode,
    Decision,
    EngineConfig,
    EngineState,
    PriceSlot,
    decide,
)
from .forecast import dedupe_slots, parse_forecast
from .steve_api import SteVeApiClient, SteVeApiError, SteVeData

_LOGGER = logging.getLogger(__name__)

# Loose truthy/charging tokens, so we tolerate the many ways go-e integrations
# expose "car connected" / "charging" (binary_sensor, sensor, enum, number).
_TRUTHY = {STATE_ON, "true", "1", "connected", "charging", "car", "ready"}


@dataclass(slots=True)
class RuntimeSettings:
    """User-adjustable settings, owned here and mutated by control entities.

    Persisted across restarts by the entities themselves (RestoreEntity), which
    push their restored value back in on startup.
    """

    mode: ChargingMode = ChargingMode.OFF
    battery_policy: BatteryPolicy = BatteryPolicy.PROTECT
    smart_enabled: bool = True
    min_current_a: float = DEFAULT_MIN_CURRENT
    max_current_a: float = DEFAULT_MAX_CURRENT
    battery_reserve_soc: float = DEFAULT_BATTERY_RESERVE_SOC
    min_grid_floor_w: float = DEFAULT_MIN_GRID_FLOOR_W
    cheap_price: float = DEFAULT_CHEAP_PRICE
    battery_floor_soc: float = DEFAULT_BATTERY_FLOOR_SOC
    target_energy_kwh: float = DEFAULT_TARGET_ENERGY_KWH
    departure: datetime | None = None
    auto_phase: bool = DEFAULT_AUTO_PHASE


class GoeSteveCoordinator(DataUpdateCoordinator[Decision]):
    """Drives one regulation loop per config entry."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
            config_entry=entry,
        )
        self._cfg = dict(entry.data)
        self.settings = RuntimeSettings()
        # Optional SteVe metering/authorization coordinator (None when unconfigured).
        self.steve: "SteVeCoordinator | None" = None
        # Latest world snapshot, retained so the power-flow sensor (and card) can
        # surface live PV/grid/battery/car values without re-reading every entity.
        self.last_inputs: ChargerInputs | None = None
        self._voltage = float(self._cfg.get(CONF_VOLTAGE, DEFAULT_VOLTAGE))
        self._phases = int(self._cfg.get(CONF_PHASES, DEFAULT_PHASES))
        # Leave phase memory unseeded: the engine seeds it per mode (surplus
        # charging prefers 1φ, power/grid charging pins the full phase count).
        self._state = EngineState()
        self._last_written_a: float | None = None
        self._last_written_phases: int | None = None
        self._last_write_at: datetime | None = None
        # Rolling-average buffers for input smoothing.
        self._pv_samples: deque[float] = deque(maxlen=SMOOTHING_SAMPLES)
        self._grid_samples: deque[float] = deque(maxlen=SMOOTHING_SAMPLES)

    # --- State reading helpers --------------------------------------------------
    def _get_float(self, conf_key: str) -> float | None:
        entity_id = self._cfg.get(conf_key)
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN, ""):
            return None
        try:
            return float(state.state)
        except (ValueError, TypeError):
            return None

    def _get_bool(self, conf_key: str) -> bool | None:
        entity_id = self._cfg.get(conf_key)
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN, ""):
            return None
        raw = state.state.lower()
        if raw in _TRUTHY:
            return True
        if raw in (STATE_OFF, "false", "0", "idle", "disconnected"):
            return False
        # Numeric truthiness fallback (e.g. go-e "car" status code > 1).
        try:
            return float(raw) > 1
        except (ValueError, TypeError):
            return None

    def _read_price(self) -> tuple[float | None, list[PriceSlot] | None]:
        """Read the current price and (best-effort) the forecast list."""
        entity_id = self._cfg.get(CONF_PRICE)
        if not entity_id:
            return None, None
        state = self.hass.states.get(entity_id)
        if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN, ""):
            return None, None
        try:
            price_now: float | None = float(state.state)
        except (ValueError, TypeError):
            price_now = None

        attr = self._cfg.get(CONF_PRICE_FORECAST_ATTR, DEFAULT_PRICE_FORECAST_ATTR)
        forecast: list[PriceSlot] = []
        # Concatenate today + tomorrow when the provider splits them.
        for candidate in (attr, "raw_tomorrow", "forecast"):
            forecast.extend(
                parse_forecast(
                    state.attributes.get(candidate),
                    default_tz=dt_util.DEFAULT_TIME_ZONE,
                )
            )
        forecast = dedupe_slots(forecast)
        return price_now, (forecast or None)

    @staticmethod
    def _smooth(buffer: deque[float], value: float | None) -> float | None:
        if value is None:
            return None
        buffer.append(value)
        return sum(buffer) / len(buffer)

    # --- The regulation loop ----------------------------------------------------
    async def _async_update_data(self) -> Decision:
        connected = self._get_bool(CONF_GOE_CONNECTED)
        grid_raw = self._get_float(CONF_GRID_POWER)

        # Required signals missing/stale → keep hands off rather than guess.
        if connected is None or grid_raw is None:
            return Decision(
                control=False,
                reason="Waiting for charger / grid data",
            )

        grid = self._smooth(self._grid_samples, grid_raw)
        pv = self._smooth(self._pv_samples, self._get_float(CONF_PV_POWER))
        price_now, forecast = self._read_price()

        inputs = ChargerInputs(
            car_connected=connected,
            car_actual_power_w=self._get_float(CONF_GOE_POWER) or 0.0,
            phases=self._state.phases or self._phases,
            voltage_v=self._voltage,
            grid_power_w=grid if grid is not None else grid_raw,
            pv_power_w=pv,
            battery_soc=self._get_float(CONF_BATTERY_SOC),
            battery_power_w=self._get_float(CONF_BATTERY_POWER),
            price_now=price_now,
            price_forecast=forecast,
            now=dt_util.utcnow(),
        )
        self.last_inputs = inputs
        cfg = EngineConfig(
            mode=self.settings.mode,
            battery_policy=self.settings.battery_policy,
            smart_enabled=self.settings.smart_enabled,
            min_current_a=self.settings.min_current_a,
            max_current_a=self.settings.max_current_a,
            battery_reserve_soc=self.settings.battery_reserve_soc,
            min_grid_floor_w=self.settings.min_grid_floor_w,
            cheap_price=self.settings.cheap_price,
            battery_floor_soc=self.settings.battery_floor_soc,
            target_energy_kwh=self.settings.target_energy_kwh,
            departure=self.settings.departure,
            auto_phase=self.settings.auto_phase,
            max_phases=max(self._phases, 3),
            phase_dwell_s=PHASE_DWELL_S,
            min_on_dwell_s=MIN_ON_DWELL_S,
            min_off_dwell_s=MIN_OFF_DWELL_S,
        )

        decision = decide(inputs, cfg, self._state)
        await self._apply(decision)
        return decision

    async def _apply(self, decision: Decision) -> None:
        """Write target current/phases to the go-e, avoiding redundant writes."""
        if not decision.control:
            self._last_written_a = None  # we relinquished control
            return

        now = dt_util.utcnow()
        target = round(decision.target_current_a) if decision.should_charge else 0

        # Rate-limit writes, but always allow a stop and a phase change through.
        phase_change = (
            self.settings.auto_phase
            and self._last_written_phases is not None
            and decision.target_phases != self._last_written_phases
        )
        if (
            target != 0
            and self._last_write_at is not None
            and (now - self._last_write_at).total_seconds() < MIN_UPDATE_INTERVAL_S
            and not phase_change
        ):
            return

        await self._write_phases(decision)

        current_entity = self._cfg.get(CONF_GOE_CURRENT)
        if not current_entity:
            return
        if (
            self._last_written_a is not None
            and abs(target - self._last_written_a) < MIN_WRITE_DELTA_A
            and not phase_change
        ):
            return

        try:
            await self.hass.services.async_call(
                "number",
                "set_value",
                {"entity_id": current_entity, "value": target},
                blocking=False,
            )
            self._last_written_a = float(target)
            self._last_write_at = now
        except Exception as err:  # noqa: BLE001 - never let a write break the loop
            _LOGGER.warning("Failed to set charger current via %s: %s", current_entity, err)

    async def _write_phases(self, decision: Decision) -> None:
        """Write the phase count when auto-phase is on and an entity is mapped."""
        if not self.settings.auto_phase:
            return
        phase_entity = self._cfg.get(CONF_GOE_PHASE)
        if not phase_entity:
            return
        if self._last_written_phases == decision.target_phases:
            return

        domain = phase_entity.split(".", 1)[0]
        value: object = decision.target_phases
        service = "set_value"
        data: dict[str, object] = {"entity_id": phase_entity, "value": value}
        if domain == "select":
            service = "select_option"
            data = {"entity_id": phase_entity, "option": str(decision.target_phases)}

        try:
            await self.hass.services.async_call(domain, service, data, blocking=False)
            self._last_written_phases = decision.target_phases
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("Failed to set phases via %s: %s", phase_entity, err)

    def request_apply(self) -> None:
        """Ask for an immediate re-evaluation after a settings change."""
        self.hass.async_create_task(self.async_request_refresh())

    @callback
    def async_setup_input_triggers(self) -> CALLBACK_TYPE:
        """Re-run the regulation loop whenever a live power input changes.

        The periodic 30 s poll only catches surplus changes up to 30 s late.
        By also re-evaluating when the grid/PV/battery sensors push a new value,
        we react to a passing cloud or a switched-on appliance within seconds.

        Safe against chatty sensors: ``async_request_refresh`` runs through the
        coordinator's request-refresh debouncer (fires immediately, then coalesces
        a burst), and charger writes stay throttled by ``MIN_UPDATE_INTERVAL_S``.

        Returns an unsubscribe callback for the caller to register on unload.
        """
        entity_ids = [
            entity_id
            for key in (CONF_GRID_POWER, CONF_PV_POWER, CONF_BATTERY_POWER)
            if (entity_id := self._cfg.get(key))
        ]
        if not entity_ids:
            return lambda: None

        @callback
        def _on_input_change(_event: Event[EventStateChangedData]) -> None:
            self.async_request_refresh()

        return async_track_state_change_event(self.hass, entity_ids, _on_input_change)


class SteVeCoordinator(DataUpdateCoordinator[SteVeData]):
    """Polls the SteVe OCPP server for tags + transactions (metering/auth).

    Separate from the regulation loop and far slower: metering and tag state
    change on the order of minutes, and we don't want to hammer SteVe at the
    30 s control cadence.
    """

    config_entry: ConfigEntry

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, client: SteVeApiClient
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_steve",
            update_interval=STEVE_SCAN_INTERVAL,
            config_entry=entry,
        )
        self.client = client
        # The currently picked authorized tag (its raw id-tag). Set by the
        # "Selected tag" select entity / card dropdown; the authorize/block/
        # remote_start services fall back to it when no id_tag is passed.
        self.selected_tag: str | None = None

    async def _async_update_data(self) -> SteVeData:
        try:
            return await self.client.async_fetch_data()
        except SteVeApiError as err:
            raise UpdateFailed(str(err)) from err

    @staticmethod
    def from_entry(
        hass: HomeAssistant, entry: ConfigEntry
    ) -> "SteVeCoordinator | None":
        """Build a coordinator when SteVe is configured, else None."""
        cfg = entry.data
        url = cfg.get(CONF_STEVE_URL)
        if not url:
            return None
        client = SteVeApiClient(
            async_get_clientsession(hass),
            url,
            cfg.get(CONF_STEVE_USERNAME, ""),
            cfg.get(CONF_STEVE_PASSWORD, ""),
        )
        return SteVeCoordinator(hass, entry, client)
