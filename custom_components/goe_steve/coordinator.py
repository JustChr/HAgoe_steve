"""Coordinator: reads mapped HA entities, runs the engine, writes the charger."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import CALLBACK_TYPE, Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util import dt as dt_util

from .const import (
    BATTERY_DISCHARGE_ATTACK_S,
    BATTERY_DISCHARGE_GRACE_S,
    BATTERY_DISCHARGE_RELEASE_S,
    BATTERY_DISCHARGE_TOLERANCE_W,
    CONF_BATTERY_HOLD,
    CONF_BATTERY_POWER,
    CONF_BATTERY_RESERVE_SEED,
    CONF_BATTERY_SOC,
    CONF_GOE_BASE_TOPIC,
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
    DEFAULT_BATTERY_RESERVE_SOC,
    DEFAULT_CHEAP_PRICE,
    DEFAULT_MAX_CURRENT,
    DEFAULT_MIN_CURRENT,
    DEFAULT_PHASES,
    DEFAULT_PRICE_FORECAST_ATTR,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TARGET_ENERGY_KWH,
    DEFAULT_VOLTAGE,
    DOMAIN,
    FAST_BACKOFF_DELTA_A,
    INPUT_SETTLE_S,
    MIN_UPDATE_INTERVAL_S,
    MIN_WRITE_DELTA_A,
    PHASE_CONFIRM_S,
    PHASE_DWELL_S,
    PHASE_UP_MARGIN_W,
    START_CONFIRM_S,
    STEVE_SCAN_INTERVAL,
    STOP_RIDE_OUT_S,
    SURPLUS_DROP_TAU_S,
    SURPLUS_SMOOTH_WINDOW_S,
    SURPLUS_TRACK_DROP_TAU_S,
    SURPLUS_TRACK_RISE_TAU_S,
)
from .engine import (
    ChargerInputs,
    ChargingMode,
    Decision,
    EngineConfig,
    EngineState,
    PriceSlot,
    decide,
)
from .forecast import dedupe_slots, parse_forecast
from .goe_mqtt import FRC_NEUTRAL, FRC_OFF, FRC_ON, GoeMqttClient
from .steve_api import SteVeApiClient, SteVeApiError, SteVeData

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class RuntimeSettings:
    """User-adjustable settings, owned here and mutated by control entities.

    Persisted across restarts by the entities themselves (RestoreEntity), which
    push their restored value back in on startup.
    """

    mode: ChargingMode = ChargingMode.MANUAL
    smart_enabled: bool = True
    min_current_a: float = DEFAULT_MIN_CURRENT
    max_current_a: float = DEFAULT_MAX_CURRENT
    battery_reserve_soc: float = DEFAULT_BATTERY_RESERVE_SOC
    cheap_price: float = DEFAULT_CHEAP_PRICE
    target_energy_kwh: float = DEFAULT_TARGET_ENERGY_KWH
    departure: datetime | None = None
    # Home-battery discharge override (the card's Auto/Hold/Free three-way): "auto"
    # lets the brain decide, "hold" always blocks discharge into the car, "free"
    # never does. See the engine's finalizer.
    battery_hold_mode: str = "auto"
    auto_phase: bool = DEFAULT_AUTO_PHASE
    # Manual mode (mode == OFF) cockpit: start/stop, current and phase count.
    manual_charge: bool = False
    manual_current_a: float = DEFAULT_MAX_CURRENT
    manual_phases: int = DEFAULT_PHASES


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
            # Replace the coordinator's default 10 s request-refresh cooldown with a
            # short one: an input-triggered engine run (a passing cloud, a switched
            # appliance) then reaches the loop in ~1.5 s instead of up to 10 s, so
            # the card's live numbers track reality. Charger *writes* stay throttled
            # by MIN_UPDATE_INTERVAL_S in _apply, so hardware churn is unaffected.
            request_refresh_debouncer=Debouncer(
                hass, _LOGGER, cooldown=1.5, immediate=True
            ),
        )
        self._cfg = dict(entry.data)
        # Direct link to the go-e charger over MQTT (replaces the old third-party
        # integration + entity mapping). Subscription is started in setup.
        self.goe = GoeMqttClient(hass, self._cfg.get(CONF_GOE_BASE_TOPIC, ""))
        self.settings = RuntimeSettings()
        # One-shot v1→v2 migration seed: the old battery policy mapped onto the
        # reserve line. Applied immediately (so the first engine cycles use it)
        # and consumed by the reserve number instead of its own restored state.
        seed = self._cfg.get(CONF_BATTERY_RESERVE_SEED)
        self._reserve_seed: float | None = float(seed) if seed is not None else None
        if self._reserve_seed is not None:
            self.settings.battery_reserve_soc = self._reserve_seed
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
        # switch we never set is left alone. Persisted across restarts (the store
        # below): the mapped entity may gate the *whole house's* battery, so if we
        # restart while holding it on we must still remember we own it and turn it
        # back off — otherwise a hands-off first cycle would leave the house cut
        # off from the battery until a car reconnects. Restored before the first
        # refresh via async_restore_hold_state().
        self._last_written_hold: bool | None = None
        self._hold_store: Store = Store(hass, 1, f"{DOMAIN}_{entry.entry_id}_hold")
        # True for the window after the user switches *into* Manual mode but before
        # they touch a manual control: we leave the charger exactly as it was — no
        # writes, no releases — so entering Manual never disturbs a running session.
        # Cleared the instant any manual control is used, or another mode is picked.
        # Runtime-only by design: a Manual mode restored on restart drives normally.
        self._manual_passive = False
        self._last_write_at: datetime | None = None
        # Session-energy anchor: the meter reading captured when the car plugged
        # in, so "delivered this session" works whether the mapped entity is
        # session-scoped (go-e "energy since car connected") or a total counter.
        self._session_baseline_kwh: float | None = None
        self._was_connected: bool | None = None

    def consume_reserve_seed(self) -> float | None:
        """Hand the v1→v2 reserve seed to the reserve number, at most once."""
        seed, self._reserve_seed = self._reserve_seed, None
        return seed

    @property
    def has_phase_control(self) -> bool:
        """Always true over MQTT: the charger's ``psm`` is always writable."""
        return True

    @property
    def last_written_force(self) -> bool | None:
        """The force-state the brain last wrote: True=charge, False=don't, None=released.

        Surfaced on the status sensor so the card can explain "why is the box off
        although the app says ready" — a forced-off state the user didn't set.
        """
        return self._last_written_force

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

    @property
    def goe_session_energy_kwh(self) -> float | None:
        """Energy charged in the running session (kWh), from the go-e ``wh`` key.

        go-e reports ``wh`` in Wh ("energy since car connected"); we normalize to
        kWh. Returns None when the charger hasn't reported it yet.
        """
        wh = self.goe.session_wh
        return wh / 1000.0 if wh is not None else None

    def _read_phases(self) -> int:
        """Actual phase count the car is charging on, best-effort.

        Prefer the charger's reported ``pnp`` (phases actually charging): it keeps
        the engine's ``P = I·φ·V`` math grounded in reality and catches a failed
        write or a manual/app override. When the charger hasn't reported it (e.g.
        idle), fall back to the engine's intended phase, then the configured count.
        """
        phases = self.goe.phases
        if phases in (1, 3):
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

    def _session_delivered_kwh(self, connected: bool) -> float | None:
        """Energy delivered in the running session (kWh), anchored at plug-in.

        On the connected rising edge the current meter reading becomes the
        baseline; a reading below the baseline means the meter reset itself
        (go-e's session counter does at plug-in), so the raw value already *is*
        the session figure. With no rising edge observed yet (restart mid-
        session) the entity is assumed session-scoped, matching go-e's
        "energy since car connected".
        """
        raw = self.goe_session_energy_kwh
        if connected and self._was_connected is False:
            self._session_baseline_kwh = raw or 0.0
        self._was_connected = connected
        if raw is None:
            return None
        base = self._session_baseline_kwh
        if base is None or raw < base:
            return raw
        return raw - base

    # --- The regulation loop ----------------------------------------------------
    async def _async_update_data(self) -> Decision:
        connected = self.goe.car_connected
        grid_raw = self._get_float(CONF_GRID_POWER)

        # Required signals missing/stale → keep hands off rather than guess.
        if connected is None or grid_raw is None:
            # Still refresh the price cache so the price card renders without a car.
            self._read_price()
            return Decision(
                control=False,
                reason="Waiting for charger / grid data",
            )

        price_now, forecast = self._read_price()

        # Raw power readings go straight in: the engine smooths the *derived*
        # surplus over a time window itself, which — unlike smoothing grid and
        # car power separately — is invariant to the car's own current changes.
        inputs = ChargerInputs(
            car_connected=connected,
            car_actual_power_w=self.goe.power_w or 0.0,
            phases=self._read_phases(),
            voltage_v=self._voltage,
            grid_power_w=grid_raw,
            pv_power_w=self._get_float(CONF_PV_POWER),
            battery_soc=self._get_float(CONF_BATTERY_SOC),
            battery_power_w=self._get_float(CONF_BATTERY_POWER),
            price_now=price_now,
            price_forecast=forecast,
            session_delivered_kwh=self._session_delivered_kwh(connected),
            now=dt_util.utcnow(),
        )
        self.last_inputs = inputs
        cfg = EngineConfig(
            mode=self.settings.mode,
            smart_enabled=self.settings.smart_enabled,
            min_current_a=self.settings.min_current_a,
            max_current_a=self.settings.max_current_a,
            battery_reserve_soc=self.settings.battery_reserve_soc,
            cheap_price=self.settings.cheap_price,
            target_energy_kwh=self.settings.target_energy_kwh,
            departure=self.settings.departure,
            battery_hold_mode=self.settings.battery_hold_mode,
            auto_phase=self.settings.auto_phase,
            manual_charge=self.settings.manual_charge,
            manual_current_a=self.settings.manual_current_a,
            manual_phases=self.settings.manual_phases,
            manual_passive=self._manual_passive,
            max_phases=max(self._phases, 3),
            phase_dwell_s=PHASE_DWELL_S,
            phase_confirm_s=PHASE_CONFIRM_S,
            phase_up_margin_w=PHASE_UP_MARGIN_W,
            smooth_window_s=SURPLUS_SMOOTH_WINDOW_S,
            surplus_drop_tau_s=SURPLUS_DROP_TAU_S,
            track_rise_tau_s=SURPLUS_TRACK_RISE_TAU_S,
            track_drop_tau_s=SURPLUS_TRACK_DROP_TAU_S,
            discharge_tolerance_w=BATTERY_DISCHARGE_TOLERANCE_W,
            discharge_grace_s=BATTERY_DISCHARGE_GRACE_S,
            discharge_attack_s=BATTERY_DISCHARGE_ATTACK_S,
            discharge_release_s=BATTERY_DISCHARGE_RELEASE_S,
            start_confirm_s=START_CONFIRM_S,
            stop_ride_out_s=STOP_RIDE_OUT_S,
        )

        decision = decide(inputs, cfg, self._state)
        # In the passive window right after switching into Manual, leave the
        # charger exactly as it was: skip applying entirely (no writes, no
        # releases) until the user takes over via a manual control.
        if not self._manual_passive:
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

        # Start/stop via the go-e force-state (frc): the amp value floors at the
        # 6 A hardware minimum, so it can't actually pause charging. When pausing,
        # frc=1 holds the car off and we leave the amp where it is.
        await self._write_force(decision.should_charge)
        if not decision.should_charge:
            # Forget the last written current: while paused the go-e may clamp/alter
            # the amp value, so the first write after resuming must not be
            # deadband-compared against a stale reading.
            self._last_written_a = None
            return

        target = round(decision.target_current_a) if decision.should_charge else 0

        # Rate-limit writes, but always allow a stop, a phase change and a decisive
        # back-off through. The back-off exception is what keeps the post-write
        # settle from costing anything: the settle exists so we don't command into a
        # car that is still ramping, and that reasoning only applies to asking for
        # *more*. Asking for less is always safe to do at once, and it is the
        # direction where waiting means importing or draining the home battery.
        phase_change = (
            (self.settings.auto_phase or decision.write_phases)
            and self._last_written_phases is not None
            and decision.target_phases != self._last_written_phases
        )
        backing_off = (
            self._last_written_a is not None
            and self._last_written_a - target >= FAST_BACKOFF_DELTA_A
        )
        if (
            target != 0
            and self._last_write_at is not None
            and (now - self._last_write_at).total_seconds() < MIN_UPDATE_INTERVAL_S
            and not phase_change
            and not backing_off
        ):
            return

        await self._write_phases(decision)

        if (
            self._last_written_a is not None
            and abs(target - self._last_written_a) < MIN_WRITE_DELTA_A
            and not phase_change
        ):
            return

        await self.goe.set_amp(target)
        self._last_written_a = float(target)
        self._last_write_at = now

    async def _write_phases(self, decision: Decision) -> None:
        """Force the charger's phase count (psm) over MQTT.

        Driven by auto-phase (smart modes that adapt 1↔3) or an explicit
        ``write_phases`` request from the decision (Manual mode, where the user
        picks the phase count directly).
        """
        if not self.settings.auto_phase and not decision.write_phases:
            return
        if self._last_written_phases == decision.target_phases:
            return
        await self.goe.set_phase_count(decision.target_phases)
        self._last_written_phases = decision.target_phases

    async def _write_force(self, want_charge: bool) -> None:
        """Force the charger on/off via the go-e ``frc`` key.

        ``want_charge=True`` forces charging on (frc=2 / On); False forces it off
        (frc=1 / Off). Skips redundant writes by remembering the last state we set.
        """
        if self._last_written_force is want_charge:
            return
        await self.goe.set_force(FRC_ON if want_charge else FRC_OFF)
        self._last_written_force = want_charge

    async def _release_force(self) -> None:
        """Return ``frc`` to neutral so manual/app control resumes.

        Only acts when the brain previously forced the state; an untouched charger
        (``_last_written_force is None``) is left alone so we never override a value
        the user set themselves.
        """
        if self._last_written_force is None:
            return
        await self.goe.set_force(FRC_NEUTRAL)
        self._last_written_force = None

    async def async_restore_hold_state(self) -> None:
        """Restore the last battery-hold state we wrote, persisted across restarts.

        Call once during setup, before the first engine run. Without it a restart
        forgets whether *we* turned the switch on: a hands-off first cycle would
        then leave it on (``_release_hold`` only acts on a remembered on-state),
        cutting the whole house off from the battery until a car reconnects. We
        still only ever release a switch we set, so one you manage yourself is
        left alone.
        """
        try:
            data = await self._hold_store.async_load()
        except Exception as err:  # noqa: BLE001 - a bad store must never block setup
            _LOGGER.warning("Could not restore battery-hold state: %s", err)
            return
        if data is not None:
            self._last_written_hold = data.get("hold")

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
            # Persist immediately so a restart can't forget we own an on-switch.
            await self._hold_store.async_save({"hold": hold})
        except Exception as err:  # noqa: BLE001 - never let a write break the loop
            _LOGGER.warning("Failed to set battery-hold via %s: %s", hold_entity, err)

    async def _release_hold(self) -> None:
        """Turn the battery-hold switch back off when we relinquish control.

        Only acts when we previously held it on, so a switch the user manages
        themselves (``_last_written_hold`` None/False) is never touched.
        """
        if self._last_written_hold:
            await self._write_hold(False)

    def set_manual_passive(self, passive: bool) -> None:
        """Arm or clear the Manual-mode passive window.

        Set ``True`` when the user switches into Manual (leave the charger
        untouched); cleared (``False``) by any other mode pick or the first use of
        a manual control. Callers follow with :meth:`request_apply` themselves.
        """
        self._manual_passive = passive

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
