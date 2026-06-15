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
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util import dt as dt_util

from .const import (
    CONF_BATTERY_HOLD,
    CONF_BATTERY_POWER,
    CONF_BATTERY_SOC,
    CONF_GOE_CHARGING,
    CONF_GOE_CONNECTED,
    CONF_GOE_CURRENT,
    CONF_GOE_FORCE,
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
    INPUT_SETTLE_S,
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

# go-e controls phases as a *mode* select ("Auto" / "Force single phase" /
# "Force three phases"), not a 1/3 count. Map between the engine's phase count
# and the select option by keyword, so we survive locale/firmware label changes
# (English + German) instead of writing a literal "1"/"3" the select rejects.
_ONE_PHASE_TOKENS = ("single", "1-phase", "1 phase", "1phase", "einphasig", "1")
_THREE_PHASE_TOKENS = ("three", "3-phase", "3 phase", "3phase", "dreiphasig", "3")


def _phases_from_option(option: str) -> int | None:
    """Phase count implied by a phase-switch option, or None for auto/unknown."""
    low = option.lower()
    if "auto" in low:
        return None
    if any(token in low for token in _THREE_PHASE_TOKENS):
        return 3
    if any(token in low for token in _ONE_PHASE_TOKENS):
        return 1
    return None


def _phase_option_for(target_phases: int, options: list[str]) -> str | None:
    """The select option that forces ``target_phases``, matched against live options."""
    for option in options:
        if _phases_from_option(option) == target_phases:
            return option
    return None


# go-e exposes its force-state (``frc``) as a select with three options
# ("Neutral" / "Don't charge" / "Charge", German "Neutral" / "Nicht laden" /
# "Laden") — or, on some integrations, as a number (0/1/2). The amp number floors
# at the 6 A hardware minimum and cannot actually pause charging, so the brain
# starts/stops via this entity instead. Match by keyword to survive locale and
# firmware label changes. The "off" tokens are checked first because the German
# and English "don't charge" labels also contain the "charge"/"laden" keyword.
_FORCE_OFF_TOKENS = ("don", "nicht", "kein", "stop", "off")
_FORCE_ON_TOKENS = ("charge", "laden", "force", "on")
_FORCE_NEUTRAL_TOKENS = ("neutral", "default", "auto")


def _force_option_for(want_charge: bool, options: list[str]) -> str | None:
    """The select option that forces charging on/off, matched against live options."""
    for option in options:
        low = option.lower()
        is_off = any(token in low for token in _FORCE_OFF_TOKENS)
        if want_charge:
            if is_off:
                continue
            if any(token in low for token in _FORCE_ON_TOKENS):
                return option
        elif is_off:
            return option
    return None


def _neutral_force_option(options: list[str]) -> str | None:
    """The select's neutral/default option, to release manual control."""
    for option in options:
        if any(token in option.lower() for token in _FORCE_NEUTRAL_TOKENS):
            return option
    return None


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
        # Latest price snapshot, cached so the price-forecast sensor (and card) can
        # render the curve even on cycles where regulation bails early (no car/grid).
        self._last_price_now: float | None = None
        self._last_forecast: list[PriceSlot] | None = None
        self._voltage = float(self._cfg.get(CONF_VOLTAGE, DEFAULT_VOLTAGE))
        self._phases = int(self._cfg.get(CONF_PHASES, DEFAULT_PHASES))
        # Leave phase memory unseeded: the engine seeds it per mode (surplus
        # charging prefers 1φ, power/grid charging pins the full phase count).
        self._state = EngineState()
        self._last_written_a: float | None = None
        self._last_written_phases: int | None = None
        # Last force-state we wrote: True=charge, False=don't charge, None=released
        # or never touched. Lets us skip redundant writes and release on handoff.
        self._last_written_force: bool | None = None
        # Last battery-hold state we wrote: True=held (no discharge), False=off,
        # None=never touched. Skips redundant writes and releases on handoff so a
        # switch we never set is left alone.
        self._last_written_hold: bool | None = None
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

    def _read_phases(self) -> int:
        """Actual phase count the car is charging on, best-effort.

        Prefer reading the go-e phase-switch select back — a forced single/three
        mode tells us the real count, which keeps the engine's ``P = I·φ·V`` math
        grounded in reality and catches a failed write or a manual/app override.
        An ``Auto`` mode (count unknown) and an unmapped entity fall back to the
        engine's intended phase, then the static configured count.
        """
        entity_id = self._cfg.get(CONF_GOE_PHASE)
        if entity_id:
            state = self.hass.states.get(entity_id)
            if state is not None and state.state not in (
                STATE_UNAVAILABLE,
                STATE_UNKNOWN,
                "",
            ):
                phases = _phases_from_option(state.state)
                if phases is not None:
                    return phases
        return self._state.phases or self._phases

    def _read_price(self) -> tuple[float | None, list[PriceSlot] | None]:
        """Read the current price and (best-effort) the forecast list.

        The result is cached on the coordinator (``last_price_now`` /
        ``last_forecast``) so the price sensor and card keep a usable curve even
        on cycles where regulation bails out before building inputs.
        """
        price_now, forecast = self._read_price_uncached()
        self._last_price_now = price_now
        self._last_forecast = forecast
        return price_now, forecast

    def _read_price_uncached(self) -> tuple[float | None, list[PriceSlot] | None]:
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

    @property
    def last_price_now(self) -> float | None:
        """Most recently read spot price (currency/kWh), or None."""
        return self._last_price_now

    @property
    def last_forecast(self) -> list[PriceSlot] | None:
        """Most recently parsed price forecast, or None."""
        return self._last_forecast

    @property
    def price_unit(self) -> str | None:
        """Unit of the configured price sensor, best-effort (for card labels)."""
        entity_id = self._cfg.get(CONF_PRICE)
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if state is None:
            return None
        unit = state.attributes.get("unit_of_measurement")
        return str(unit) if unit is not None else None

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
            # Still refresh the price cache so the price card renders without a car.
            self._read_price()
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
            phases=self._read_phases(),
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
            await self._release_force()  # hand the charger back to manual/app
            await self._release_hold()  # let the home battery discharge again
            return

        now = dt_util.utcnow()

        # Drive the battery-hold switch every controlling cycle, before the
        # rate-limited current write below so it is never starved by the throttle.
        await self._write_hold(decision.hold_battery)

        # Start/stop via the force-state entity when mapped: the amp number floors
        # at the 6 A hardware minimum, so writing 0 there can't actually pause
        # charging. When pausing, the force-state holds the car off and we leave
        # the amp where it is. Without a force entity we fall back to the legacy
        # current=0 stop (best-effort) below.
        if self._cfg.get(CONF_GOE_FORCE):
            await self._write_force(decision.should_charge)
            if not decision.should_charge:
                return

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
        if domain == "select":
            # go-e exposes a mode select ("Force single/three phase…"), not a
            # 1/3 count — map to the real option, matched against its live list.
            state = self.hass.states.get(phase_entity)
            options = list(state.attributes.get("options", [])) if state else []
            option = _phase_option_for(decision.target_phases, options)
            if option is None:
                _LOGGER.warning(
                    "No option on %s forces %d phase(s); available options: %s",
                    phase_entity,
                    decision.target_phases,
                    options,
                )
                return
            service = "select_option"
            data: dict[str, object] = {"entity_id": phase_entity, "option": option}
        else:
            service = "set_value"
            data = {"entity_id": phase_entity, "value": decision.target_phases}

        try:
            await self.hass.services.async_call(domain, service, data, blocking=False)
            self._last_written_phases = decision.target_phases
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("Failed to set phases via %s: %s", phase_entity, err)

    async def _write_force(self, want_charge: bool) -> None:
        """Force the charger on/off via the go-e force-state entity, when mapped.

        ``want_charge=True`` forces charging on (``frc=2`` / "Charge"); False forces
        it off (``frc=1`` / "Don't charge"). Skips redundant writes by remembering
        the last state we set.
        """
        force_entity = self._cfg.get(CONF_GOE_FORCE)
        if not force_entity:
            return
        if self._last_written_force is want_charge:
            return

        domain = force_entity.split(".", 1)[0]
        if domain == "select":
            state = self.hass.states.get(force_entity)
            options = list(state.attributes.get("options", [])) if state else []
            option = _force_option_for(want_charge, options)
            if option is None:
                _LOGGER.warning(
                    "No option on %s to %s charging; available options: %s",
                    force_entity,
                    "start" if want_charge else "stop",
                    options,
                )
                return
            service = "select_option"
            data: dict[str, object] = {"entity_id": force_entity, "option": option}
        else:
            # Numeric force-state: 2 = force on (charge), 1 = force off.
            service = "set_value"
            data = {"entity_id": force_entity, "value": 2 if want_charge else 1}

        try:
            await self.hass.services.async_call(domain, service, data, blocking=False)
            self._last_written_force = want_charge
        except Exception as err:  # noqa: BLE001 - never let a write break the loop
            _LOGGER.warning("Failed to set force-state via %s: %s", force_entity, err)

    async def _release_force(self) -> None:
        """Return the force-state to neutral so manual/app control resumes.

        Only acts when the brain previously forced the state; an untouched entity
        (``_last_written_force is None``) is left alone so we never override a value
        the user set themselves.
        """
        force_entity = self._cfg.get(CONF_GOE_FORCE)
        if not force_entity or self._last_written_force is None:
            return

        domain = force_entity.split(".", 1)[0]
        if domain == "select":
            state = self.hass.states.get(force_entity)
            options = list(state.attributes.get("options", [])) if state else []
            option = _neutral_force_option(options)
            if option is None:
                self._last_written_force = None
                return
            service = "select_option"
            data: dict[str, object] = {"entity_id": force_entity, "option": option}
        else:
            service = "set_value"
            data = {"entity_id": force_entity, "value": 0}

        try:
            await self.hass.services.async_call(domain, service, data, blocking=False)
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("Failed to release force-state via %s: %s", force_entity, err)
        finally:
            self._last_written_force = None

    async def _write_hold(self, hold: bool) -> None:
        """Drive the battery-hold switch so the car draws grid, not the battery.

        ``hold=True`` turns the mapped switch/input_boolean on (block home-battery
        discharge) while we deliberately grid-charge; False turns it off so the
        battery flows normally again. A no-op when no entity is mapped, and
        redundant writes are skipped via the remembered last state.
        """
        hold_entity = self._cfg.get(CONF_BATTERY_HOLD)
        if not hold_entity:
            return
        if self._last_written_hold is hold:
            return

        domain = hold_entity.split(".", 1)[0]
        service = "turn_on" if hold else "turn_off"
        try:
            await self.hass.services.async_call(
                domain, service, {"entity_id": hold_entity}, blocking=False
            )
            self._last_written_hold = hold
        except Exception as err:  # noqa: BLE001 - never let a write break the loop
            _LOGGER.warning("Failed to set battery-hold via %s: %s", hold_entity, err)

    async def _release_hold(self) -> None:
        """Turn the battery-hold switch back off when we relinquish control.

        Only acts when we previously held it on, so a switch the user manages
        themselves (``_last_written_hold`` None/False) is never touched.
        """
        if self._last_written_hold:
            await self._write_hold(False)

    def request_apply(self) -> None:
        """Ask for an immediate re-evaluation after a settings change."""
        self.hass.async_create_task(self.async_request_refresh())

    @callback
    def async_setup_input_triggers(self) -> CALLBACK_TYPE:
        """Re-run the regulation loop whenever a live power input changes.

        The periodic 30 s poll only catches surplus changes up to 30 s late.
        By also re-evaluating when the grid/PV/battery sensors push a new value,
        we react to a passing cloud or a switched-on appliance within seconds.

        Grid and battery come off the same inverter but report a beat apart, so
        acting on the first event of a burst means evaluating a half-updated world
        (fresh grid, stale battery, or vice versa). A trailing-edge debounce
        (``INPUT_SETTLE_S``) coalesces the burst into one evaluation once both have
        landed — aligned and current. Charger writes stay throttled by
        ``MIN_UPDATE_INTERVAL_S`` on top of that.

        Returns an unsubscribe callback for the caller to register on unload.
        """
        entity_ids = [
            entity_id
            for key in (CONF_GRID_POWER, CONF_PV_POWER, CONF_BATTERY_POWER)
            if (entity_id := self._cfg.get(key))
        ]
        if not entity_ids:
            return lambda: None

        debouncer = Debouncer(
            self.hass,
            _LOGGER,
            cooldown=INPUT_SETTLE_S,
            immediate=False,  # trailing edge: wait for the burst to settle first
            function=self.async_request_refresh,
        )

        @callback
        def _on_input_change(_event: Event[EventStateChangedData]) -> None:
            self.hass.async_create_task(debouncer.async_call())

        unsub = async_track_state_change_event(self.hass, entity_ids, _on_input_change)

        @callback
        def _unsubscribe() -> None:
            unsub()
            debouncer.async_cancel()

        return _unsubscribe


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
