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
    CONF_PV_FORECAST,
    CONF_PV_POWER,
    CONF_PHASES,
    CONF_STEVE_PASSWORD,
    CONF_STEVE_URL,
    CONF_STEVE_USERNAME,
    CONF_VICTRON_MIN_SOC,
    CONF_VICTRON_SETPOINT,
    CONF_VOLTAGE,
    DEFAULT_AUTO_PHASE,
    DEFAULT_BATTERY_RESERVE_SOC,
    DEFAULT_BRIGHT_DAY_TARGET_SOC,
    DEFAULT_CHEAP_CHARGE_POWER_W,
    DEFAULT_CHEAP_PRICE,
    DEFAULT_DARK_DAY_TARGET_SOC,
    DEFAULT_GRID_CHARGE_ENABLED,
    DEFAULT_GRID_SETPOINT_W,
    DEFAULT_MAX_CURRENT,
    DEFAULT_MIN_CURRENT,
    DEFAULT_PEAK_FOLLOW_MONTH,
    DEFAULT_PEAK_MONTH_BUFFER_W,
    DEFAULT_PEAK_GUARD_ENABLED,
    DEFAULT_PEAK_HARD_W,
    DEFAULT_PEAK_MIN_SOC,
    DEFAULT_PEAK_SOFT_W,
    DEFAULT_PEAK_TARGET_W,
    DEFAULT_PHASES,
    DEFAULT_PRICE_FORECAST_ATTR,
    DEFAULT_PEAK_READY_SOC,
    DEFAULT_PV_FORECAST_LOW_KWH,
    DEFAULT_STOCK_UP,
    DEFAULT_STOCK_UP_TARGET_SOC,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SHAVING_RESERVE_SOC,
    DEFAULT_TARGET_ENERGY_KWH,
    DEFAULT_VOLTAGE,
    DOMAIN,
    ECHO_SETTLE_S,
    FAST_BACKOFF_DELTA_A,
    INPUT_SETTLE_S,
    MIN_UPDATE_INTERVAL_S,
    MIN_WRITE_DELTA_A,
    PEAK_CONFIRM_S,
    PEAK_DWELL_S,
    PEAK_RELEASE_S,
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
    HARDWARE_MIN_CURRENT_A,
    ChargerInputs,
    ChargingMode,
    Decision,
    EngineConfig,
    EngineState,
    PriceSlot,
    attach_peak_status,
    decide,
    resolve_peak_tier,
    update_peak_window,
)
from .forecast import dedupe_slots, parse_forecast
from .goe_mqtt import (
    FRC_NEUTRAL,
    FRC_OFF,
    FRC_ON,
    GoeMqttClient,
    phase_count_to_psm,
    should_publish,
)
from .steve_api import SteVeApiClient, SteVeApiError, SteVeData

_LOGGER = logging.getLogger(__name__)

# Write deadbands for the optional Victron numbers. These sit on a bus we should not
# chatter at, and neither value is worth a service call for a rounding difference.
_SETPOINT_DEADBAND_W: float = 25.0
_MIN_SOC_DEADBAND_PCT: float = 1.0

# How often the billing window + month record are persisted. Frequent enough that a
# crash loses at most this much of a quarter-hour, rare enough not to churn the disk.
_PEAK_SAVE_INTERVAL_S: float = 30.0
# Completed windows kept in the store (the engine holds 24 h; 4 h is plenty to
# redraw the card's history strip after a restart).
_PEAK_SAVE_HISTORY: int = 16


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
    # --- Peak protection (capacity tariff) --------------------------------------
    # Off by default: with it off the brain behaves exactly as it did before, while
    # the measurement still runs so the peak sensors are usable from day one.
    # Limits are stored in watts; the number entities present them in kW.
    peak_guard_enabled: bool = DEFAULT_PEAK_GUARD_ENABLED
    peak_soft_w: float = DEFAULT_PEAK_SOFT_W
    peak_target_w: float = DEFAULT_PEAK_TARGET_W
    peak_hard_w: float = DEFAULT_PEAK_HARD_W
    peak_follow_month: bool = DEFAULT_PEAK_FOLLOW_MONTH
    peak_month_buffer_w: float = DEFAULT_PEAK_MONTH_BUFFER_W
    shaving_reserve_soc: float = DEFAULT_SHAVING_RESERVE_SOC
    peak_min_soc: float = DEFAULT_PEAK_MIN_SOC
    # --- Cheap-hour grid charging -------------------------------------------------
    grid_charge_enabled: bool = DEFAULT_GRID_CHARGE_ENABLED
    grid_setpoint_w: float = DEFAULT_GRID_SETPOINT_W
    cheap_charge_power_w: float = DEFAULT_CHEAP_CHARGE_POWER_W
    bright_day_target_soc: float = DEFAULT_BRIGHT_DAY_TARGET_SOC
    dark_day_target_soc: float = DEFAULT_DARK_DAY_TARGET_SOC
    pv_forecast_low_kwh: float = DEFAULT_PV_FORECAST_LOW_KWH
    peak_ready_soc: float = DEFAULT_PEAK_READY_SOC
    stock_up: bool = DEFAULT_STOCK_UP
    stock_up_target_soc: float = DEFAULT_STOCK_UP_TARGET_SOC


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
        # It is *memory*, not truth: the charger's own `frc` is checked alongside it
        # (see _write_force), because an RFID swipe or the go-e app can move the real
        # value without us ever hearing about it. The timestamps below are what stop
        # that read-back from re-writing before our own write has echoed back.
        self._last_written_force: bool | None = None
        self._force_written_at: datetime | None = None
        self._phases_written_at: datetime | None = None
        # True once the requested current has been parked at the hardware minimum for
        # the current pause, so parking costs one write per pause and not one a cycle.
        self._amp_parked = False
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
        # Peak protection's two house outputs, same ownership rule as the hold: a
        # value we never wrote is a value we never touch on release. Unlike the
        # charger — which has a neutral state to hand back to — a number entity has
        # no "nobody is driving me" position, so releasing one means putting back
        # what was on it when we took over. That reading is captured on the first
        # write and persisted beside the hold, because the moment it matters most is
        # a restart: without it, turning peak protection off after a reboot would
        # strand the ESS setpoint wherever the last shave left it (0 W at the hard
        # tier) with nothing left that remembers the entity is ours to give back.
        self._last_written_setpoint: float | None = None
        self._last_written_min_soc: float | None = None
        self._setpoint_before: float | None = None
        self._min_soc_before: float | None = None
        # The billing quarter-hour and the month record, persisted so a restart
        # mid-window doesn't blind the guard or lose the number that gets billed.
        # Saved at most every PEAK_SAVE_INTERVAL_S so this never churns the disk.
        self._peak_store: Store = Store(hass, 1, f"{DOMAIN}_{entry.entry_id}_peak")
        self._peak_saved_at: datetime | None = None
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
    def engine_state(self) -> EngineState:
        """The engine's carry-over memory, for sensors that surface it directly.

        Read-only by convention: the month record and the completed-window history
        live here because the engine maintains them, and the peak sensors would
        otherwise have no way to reach them.
        """
        return self._state

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

        Prefer what the charger reports (``GoeMqttClient.phases``: measured phase
        currents, else the ``psm`` mode): it keeps the engine's ``P = I·φ·V`` math
        grounded in reality and catches a failed write or a manual/app override.
        Only when the charger says nothing at all do we fall back to the engine's
        own intended phase, then the configured count — that fallback is a guess,
        and it is the reason a stale solar-strategy phase once had the card
        reporting a three-phase charge as single-phase.
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
        cfg = self._engine_config()

        # Required signals missing/stale → keep hands off rather than guess.
        if connected is None or grid_raw is None:
            # Still refresh the price cache so the price card renders without a car.
            self._read_price()
            # …and still advance the billing quarter-hour. This is exactly the path a
            # dead grid sensor takes, which is precisely when a frozen accumulator
            # would silently under-count the quarter-hour the failure is hiding.
            # ``grid_w=None`` holds the last reading across the gap and marks the
            # window degraded, so the guard may only tighten from here.
            now = dt_util.utcnow()
            window = update_peak_window(now, grid_raw, cfg, self._state)
            tier = resolve_peak_tier(now, window, cfg, self._state)
            await self._save_peak_state(now)
            return attach_peak_status(
                Decision(control=False, reason="Waiting for charger / grid data"),
                cfg,
                self._state,
                window,
                tier,
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
            pv_forecast_kwh=self._get_float(CONF_PV_FORECAST),
            session_delivered_kwh=self._session_delivered_kwh(connected),
            now=dt_util.utcnow(),
        )
        self.last_inputs = inputs

        decision = decide(inputs, cfg, self._state)
        await self._save_peak_state(inputs.now)
        # In the passive window right after switching into Manual, leave the
        # *charger* exactly as it was: no force write, no release, until the user
        # takes over via a manual control.
        #
        # The house is a different question. Peak protection answers to its own
        # switch rather than to the charging mode, and the levers it uses to shave
        # — the ESS setpoint, the minimum SoC, the battery hold — have nothing to
        # do with what the wallbox is doing. Suppressing those here used to make
        # the soft tier a no-op for as long as the passive window lasted: it would
        # measure, report that it was shaving, and write nothing, until the
        # projection escalated to hard. So the passive window now covers only what
        # it is actually about — and even there the hard tier still gets through,
        # because it may have turned this into an active stop (``control`` forced
        # True), which is a safety decision and outranks the passive window.
        await self._apply(
            decision, charger=not self._manual_passive or decision.peak_tier == "hard"
        )
        return decision

    def _engine_config(self) -> EngineConfig:
        """Assemble the engine's settings from the live tunables + static constants."""
        return EngineConfig(
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
            peak_guard_enabled=self.settings.peak_guard_enabled,
            peak_soft_w=self.settings.peak_soft_w,
            peak_target_w=self.settings.peak_target_w,
            peak_hard_w=self.settings.peak_hard_w,
            peak_follow_month=self.settings.peak_follow_month,
            peak_month_buffer_w=self.settings.peak_month_buffer_w,
            shaving_reserve_soc=self.settings.shaving_reserve_soc,
            peak_min_soc=self.settings.peak_min_soc,
            peak_confirm_s=PEAK_CONFIRM_S,
            peak_release_s=PEAK_RELEASE_S,
            peak_dwell_s=PEAK_DWELL_S,
            grid_charge_enabled=self.settings.grid_charge_enabled,
            grid_setpoint_w=self.settings.grid_setpoint_w,
            cheap_charge_power_w=self.settings.cheap_charge_power_w,
            bright_day_target_soc=self.settings.bright_day_target_soc,
            dark_day_target_soc=self.settings.dark_day_target_soc,
            pv_forecast_low_kwh=self.settings.pv_forecast_low_kwh,
            peak_ready_soc=self.settings.peak_ready_soc,
            stock_up=self.settings.stock_up,
            stock_up_target_soc=self.settings.stock_up_target_soc,
            # The engine works in UTC; the billed month and any clock time it puts
            # in front of a user are the wall calendar's, so hand it ours.
            local_tz=dt_util.DEFAULT_TIME_ZONE,
        )

    async def _apply(self, decision: Decision, *, charger: bool = True) -> None:
        """Write the decision out: house outputs first, then the charger.

        Two permissions, deliberately separate. ``house_control`` governs the home
        battery's levers (the ESS grid setpoint, the minimum-SoC number, the hold
        switch); ``control`` governs the charger. Peak protection answers to its own
        switch rather than to Smart control, so it can keep managing the house while
        the wallbox is handed back to the app — and, at its hard tier, stop the
        charger even when the brain is otherwise not driving it.

        With peak protection and cheap-hour charging both off, ``house_control``
        simply equals ``control`` and this behaves exactly as it always did.

        ``charger=False`` is Manual's passive window: write the house, but leave the
        wallbox untouched — not even a release — until the user takes over.
        """
        # House outputs first, and before the rate-limited charger writes below, so
        # they are never starved by the throttle. Both are no-ops when no entity is
        # mapped, and hand the entity back when the engine has nothing to say.
        if decision.house_control:
            await self._write_setpoint(decision.grid_setpoint_w)
            await self._write_min_soc(decision.battery_min_soc)
        else:
            await self._release_setpoint()
            await self._release_min_soc()

        # The hold switch may gate the *whole house's* battery, so the long-standing
        # rule holds: only drive it when we actually have an opinion — the car brain
        # is driving, or peak protection is deliberately releasing the battery to
        # shave. Otherwise release only what we know we turned on ourselves, and in
        # the passive window not even that: releasing is still a write.
        if decision.control or decision.hold_source == "peak":
            await self._write_hold(decision.hold_battery)
        elif charger:
            await self._release_hold()

        if not charger:
            return

        if not decision.control:
            self._last_written_a = None  # we relinquished control
            self._amp_parked = False  # …so the next pause we *do* own parks again
            await self._release_force()  # hand the charger back to manual/app
            return

        now = dt_util.utcnow()

        # Start/stop via the go-e force-state (frc): the amp value floors at the
        # 6 A hardware minimum, so it can't actually pause charging. When pausing,
        # frc=1 holds the car off and the amp value is parked at that floor.
        await self._write_force(decision.should_charge)
        if not decision.should_charge:
            # Park the requested current at the minimum. Holding the car off is
            # frc's job and stays frc's job — this is only about what a car would
            # find if frc were ever cleared behind our back: 6 A rather than
            # whatever the last session happened to leave in the register.
            await self._park_amp()
            # Forget the last written current: while paused the go-e may clamp/alter
            # the amp value, so the first write after resuming must not be
            # deadband-compared against a stale reading.
            self._last_written_a = None
            return
        self._amp_parked = False

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
        want = phase_count_to_psm(decision.target_phases)
        last = (
            None
            if self._last_written_phases is None
            else phase_count_to_psm(self._last_written_phases)
        )
        if not should_publish(
            want, self.goe.phase_mode, last, self._since(self._phases_written_at),
            ECHO_SETTLE_S,
        ):
            return
        await self.goe.set_phase_count(decision.target_phases)
        self._last_written_phases = decision.target_phases
        self._phases_written_at = dt_util.utcnow()

    async def _write_force(self, want_charge: bool) -> None:
        """Force the charger on/off via the go-e ``frc`` key.

        ``want_charge=True`` forces charging on (frc=2 / On); False forces it off
        (frc=1 / Off).

        Closed-loop on purpose. Skipping the write whenever *we* last wrote the same
        value is open-loop, and frc is the one key something else can plausibly move:
        an RFID swipe at the box, the go-e app, the charger's own session handling.
        The brain would go on believing it was holding the car off while the charger
        sat in Neutral — a pause that isn't pausing anything, with nothing in the UI
        disagreeing. So the charger's reported frc has to agree too, and when it
        doesn't we put ours back. That is the contract the Force-state select already
        documents: setting it by hand is authoritative only when the brain isn't
        controlling.
        """
        want = FRC_ON if want_charge else FRC_OFF
        last = (
            None
            if self._last_written_force is None
            else (FRC_ON if self._last_written_force else FRC_OFF)
        )
        if not should_publish(
            want, self.goe.force_state, last, self._since(self._force_written_at),
            ECHO_SETTLE_S,
        ):
            return
        await self.goe.set_force(want)
        self._last_written_force = want_charge
        self._force_written_at = dt_util.utcnow()

    async def _park_amp(self) -> None:
        """Leave the requested current at the hardware minimum while paused.

        Defence in depth, not the pause itself: :meth:`_write_force` is what holds
        the car off, and if it is doing its job this never matters. It matters when
        it *can't* — the charger is in Neutral because we deliberately released it
        (Smart control off, a stale-input cycle), and someone authorizes a session at
        the box. Then the amp register is the only thing deciding how hard that
        charge pulls, and leaving the previous session's 16 A in it is how an
        unplanned charge gets to be a fast one.

        Written once per pause: re-checking every cycle would fight the app for a
        register that is, by then, no longer ours to defend.
        """
        if self._amp_parked:
            return
        self._amp_parked = True
        live = self.goe.requested_current_a
        if live is not None and live <= HARDWARE_MIN_CURRENT_A:
            return
        await self.goe.set_amp(int(HARDWARE_MIN_CURRENT_A))

    def _since(self, stamp: datetime | None) -> float | None:
        """Seconds since ``stamp``, or None if we never wrote that key."""
        return None if stamp is None else (dt_util.utcnow() - stamp).total_seconds()

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
        # Released means we have no opinion left to re-assert, so the read-back in
        # _write_force must not resurrect one: clearing the stamp with the state
        # keeps the two from ever describing different charge sessions.
        self._force_written_at = None

    async def async_restore_hold_state(self) -> None:
        """Restore what we own on the house side, persisted across restarts.

        Call once during setup, before the first engine run. Without it a restart
        forgets whether *we* turned the hold switch on: a hands-off first cycle
        would then leave it on (``_release_hold`` only acts on a remembered
        on-state), cutting the whole house off from the battery until a car
        reconnects. The same applies to peak protection's two number entities —
        forgetting those means never giving them back. We still only ever release
        something we set, so an entity you manage yourself is left alone.
        """
        try:
            data = await self._hold_store.async_load()
        except Exception as err:  # noqa: BLE001 - a bad store must never block setup
            _LOGGER.warning("Could not restore battery-hold state: %s", err)
            return
        if data is None:
            return
        self._last_written_hold = data.get("hold")

        def _float_or_none(value: object) -> float | None:
            try:
                return None if value is None else float(value)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                return None

        self._last_written_setpoint = _float_or_none(data.get("setpoint"))
        self._setpoint_before = _float_or_none(data.get("setpoint_before"))
        self._last_written_min_soc = _float_or_none(data.get("min_soc"))
        self._min_soc_before = _float_or_none(data.get("min_soc_before"))

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
            await self._save_house_ownership()
        except Exception as err:  # noqa: BLE001 - never let a write break the loop
            _LOGGER.warning("Failed to set battery-hold via %s: %s", hold_entity, err)

    async def _release_hold(self) -> None:
        """Turn the battery-hold switch back off when we relinquish control.

        Only acts when we previously held it on, so a switch the user manages
        themselves (``_last_written_hold`` None/False) is never touched.
        """
        if self._last_written_hold:
            await self._write_hold(False)

    # --- Peak protection: the house outputs -------------------------------------
    async def _write_number(
        self, conf_key: str, value: float, last: float | None, deadband: float
    ) -> float | None:
        """Set a mapped ``number``/``input_number``, skipping redundant writes.

        Returns the value now believed to be on the entity, or ``last`` when nothing
        was written. A no-op (returning ``last``) when no entity is mapped, which is
        what keeps an unconfigured setup completely untouched. The deadband matters
        here: these entities sit on a Victron bus that we should not chatter at.
        """
        entity_id = self._cfg.get(conf_key)
        if not entity_id:
            return last
        if last is not None and abs(value - last) < deadband:
            return last
        domain = entity_id.split(".", 1)[0]
        try:
            await self.hass.services.async_call(
                domain,
                "set_value",
                {"entity_id": entity_id, "value": value},
                blocking=False,
            )
        except Exception as err:  # noqa: BLE001 - never let a write break the loop
            _LOGGER.warning("Failed to set %s to %s: %s", entity_id, value, err)
            return last
        return value

    async def _write_setpoint(self, value: float | None) -> None:
        """Command the ESS grid setpoint (the total grid import we want).

        ``None`` means the engine has nothing to say — peak protection and
        cheap-hour charging are both off — so the entity goes back to whatever it
        held before we first touched it, and is then left entirely alone.
        """
        if value is None:
            await self._release_setpoint()
            return
        owned = self._last_written_setpoint is not None
        if not owned:
            self._setpoint_before = self._get_float(CONF_VICTRON_SETPOINT)
        self._last_written_setpoint = await self._write_number(
            CONF_VICTRON_SETPOINT, value, self._last_written_setpoint, _SETPOINT_DEADBAND_W
        )
        # Persist only on the cycle we actually take the entity over — which never
        # happens when none is mapped, so an unconfigured setup writes no disk.
        if not owned and self._last_written_setpoint is not None:
            await self._save_house_ownership()

    async def _write_min_soc(self, value: float | None) -> None:
        """Command the ESS minimum SoC — the shaving reserve, or the peak floor.

        While peak protection is on this entity is *owned*: it rests at the shaving
        reserve so ordinary house loads can't drain the battery flat, and drops to
        the peak floor while shaving. Those two values are the whole contract while
        we hold it — we never try to blend a user's own edits into them — but the
        contract does end, and :meth:`_release_min_soc` is how.
        """
        if value is None:
            await self._release_min_soc()
            return
        owned = self._last_written_min_soc is not None
        if not owned:
            self._min_soc_before = self._get_float(CONF_VICTRON_MIN_SOC)
        self._last_written_min_soc = await self._write_number(
            CONF_VICTRON_MIN_SOC, value, self._last_written_min_soc, _MIN_SOC_DEADBAND_PCT
        )
        if not owned and self._last_written_min_soc is not None:
            await self._save_house_ownership()

    async def _release_setpoint(self) -> None:
        """Hand the ESS grid setpoint back once nothing wants it any more.

        The counterpart to :meth:`_release_force` and :meth:`_release_hold`: acts
        only on an entity we know we took over, so one the user manages themselves
        is never written. Without this, switching peak protection off at the hard
        tier would leave the house permanently commanded to import 0 W.
        """
        if self._last_written_setpoint is None:
            return
        restore, self._setpoint_before = self._setpoint_before, None
        self._last_written_setpoint = None
        if restore is not None:
            # Deadband 0 against a ``last`` of None: this write must not be skipped.
            await self._write_number(CONF_VICTRON_SETPOINT, restore, None, 0.0)
        await self._save_house_ownership()

    async def _release_min_soc(self) -> None:
        """Hand the ESS minimum SoC back — see :meth:`_release_setpoint`."""
        if self._last_written_min_soc is None:
            return
        restore, self._min_soc_before = self._min_soc_before, None
        self._last_written_min_soc = None
        if restore is not None:
            await self._write_number(CONF_VICTRON_MIN_SOC, restore, None, 0.0)
        await self._save_house_ownership()

    async def _save_house_ownership(self) -> None:
        """Persist which house numbers are ours and what they held before.

        Shares the hold store: it is the record of what we have taken over on the
        house side, and all of it has the same failure mode if forgotten — an
        entity left where we put it with nobody left who knows to give it back.
        """
        try:
            await self._hold_store.async_save(self._house_ownership())
        except Exception as err:  # noqa: BLE001 - never let a save break the loop
            _LOGGER.warning("Could not persist house-lever ownership: %s", err)

    def _house_ownership(self) -> dict[str, object]:
        """Everything we have taken over on the house side, as one stored record.

        A ``None`` last-written value means "not ours" — which is why the values go
        in rather than a separate ownership flag: 0 W is a perfectly real setpoint
        for us to be holding, and a boolean beside it could disagree with it.
        """
        return {
            "hold": self._last_written_hold,
            "setpoint": self._last_written_setpoint,
            "setpoint_before": self._setpoint_before,
            "min_soc": self._last_written_min_soc,
            "min_soc_before": self._min_soc_before,
        }

    async def async_restore_peak_state(self) -> None:
        """Restore the billing quarter-hour and the month record across a restart.

        Without this a restart in the middle of a quarter-hour starts the window
        from zero — blind to whatever was already drawn — and, worse, forgets the
        month's peak, which is the number that actually gets billed. The restored
        window is marked degraded, so the guard may only tighten until the next
        clean boundary.
        """
        try:
            data = await self._peak_store.async_load()
        except Exception as err:  # noqa: BLE001 - a bad store must never block setup
            _LOGGER.warning("Could not restore peak state: %s", err)
            return
        if not data:
            return
        try:
            start = data.get("window_start")
            if start:
                self._state.peak_window_start = dt_util.parse_datetime(start)
                self._state.peak_window_wh = float(data.get("window_wh", 0.0))
                self._state.peak_window_degraded = True
                # The sample clock belongs with the window it measured. Restoring
                # the window without it leaves the engine unable to tell a two-second
                # restart from a two-day outage, and the wrong answer there is the
                # expensive one: it back-fills the missed quarter-hours from the
                # first live reading and books the result as this month's peak.
                sample_t = data.get("sample_t")
                self._state.peak_sample_t = (
                    dt_util.parse_datetime(sample_t) if sample_t else None
                )
                self._state.peak_sample_w = float(data.get("sample_w", 0.0))
            self._state.month_key = data.get("month_key", "")
            self._state.month_peak_w = float(data.get("month_peak_w", 0.0))
            self._state.prev_month_peak_w = float(data.get("prev_month_peak_w", 0.0))
            at = data.get("month_peak_at")
            self._state.month_peak_at = dt_util.parse_datetime(at) if at else None
            self._state.peak_history = [
                (dt_util.parse_datetime(stamp), float(value))
                for stamp, value in data.get("history", [])
                if dt_util.parse_datetime(stamp) is not None
            ]
        except (TypeError, ValueError) as err:
            _LOGGER.warning("Ignoring unreadable peak state: %s", err)

    async def _save_peak_state(self, now: datetime | None) -> None:
        """Persist the window + month record, at most every few dozen seconds."""
        if now is None:
            return
        if (
            self._peak_saved_at is not None
            and (now - self._peak_saved_at).total_seconds() < _PEAK_SAVE_INTERVAL_S
        ):
            return
        self._peak_saved_at = now
        state = self._state
        try:
            await self._peak_store.async_save(
                {
                    "window_start": (
                        state.peak_window_start.isoformat()
                        if state.peak_window_start
                        else None
                    ),
                    "window_wh": state.peak_window_wh,
                    "sample_t": (
                        state.peak_sample_t.isoformat() if state.peak_sample_t else None
                    ),
                    "sample_w": state.peak_sample_w,
                    "month_key": state.month_key,
                    "month_peak_w": state.month_peak_w,
                    "month_peak_at": (
                        state.month_peak_at.isoformat() if state.month_peak_at else None
                    ),
                    "prev_month_peak_w": state.prev_month_peak_w,
                    "history": [
                        (stamp.isoformat(), value)
                        for stamp, value in state.peak_history[-_PEAK_SAVE_HISTORY:]
                    ],
                }
            )
        except Exception as err:  # noqa: BLE001 - never let a save break the loop
            _LOGGER.warning("Could not persist peak state: %s", err)

    def reset_month_peak(self) -> None:
        """Forget this month's recorded peak (the *Reset* button).

        For when the operator's own meter reading disagrees with ours, or after a
        one-off that shouldn't shape the rest of the month's throttling.
        """
        self._state.month_peak_w = 0.0
        self._state.month_peak_at = None
        self._peak_saved_at = None

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

    @property
    def waiting_to_start(self) -> bool:
        """True while a solar start is sitting out its confirmation window.

        This is exactly when :meth:`start_now` has something to skip, so the
        button (and the card's countdown chip) can offer itself only then.
        """
        decision = self.data
        return (
            decision is not None
            and decision.control
            and not decision.should_charge
            and decision.resume_not_before is not None
        )

    def start_now(self) -> None:
        """Skip the remaining start-confirmation wait and charge on this cycle.

        The confirmation window is there to keep a bright patch from starting a
        session that has to be undone minutes later — but when the user is
        looking at the surplus and wants it now, waiting it out is just friction.
        Only the *waiting* is skipped: the engine still needs a surplus that
        carries the minimum current, so this can never start a charge the sun
        can't pay for. Ignored when no start is waiting — there is nothing to
        skip then, and an armed request must never lie in wait for a later
        session it wasn't meant for.
        """
        if not self.waiting_to_start:
            _LOGGER.debug("Start now: nothing is waiting to start, ignoring")
            return
        self._state.start_override = True
        self.request_apply()

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
