"""Pure regulation engine for go-e + SteVe Smart Charging.

This module is intentionally free of any Home Assistant imports so that the
decision logic can be reasoned about and unit-tested in isolation (see
``tests/test_engine.py``). The coordinator feeds it a snapshot of the world
(:class:`ChargerInputs`), the current settings (:class:`EngineConfig`) and a
small mutable :class:`EngineState` (smoothing/dwell memory carried across
cycles) and gets back a single :class:`Decision` describing what the charger
should do and, crucially, *why* — the human-readable ``reason`` is surfaced in
the UI.

Architecture — strategies + arbiter (v3):

Every cycle, each strategy enabled by the charging mode independently proposes
the charging *power* it could justify right now:

* **Solar surplus** — the solar power available to the car, tracked at two
  speeds (see below) so the current follows the surplus closely while the
  decision to charge at all stays deliberate.
* **Cheap grid** — full power while the spot price is at/below the threshold.
* **Departure plan** — full power during the cheapest forecast slots needed to
  cover the *remaining* energy (target − delivered) by departure, guaranteed.
* **Minimum floor** — the minimum current, always (Solar + minimum mode).
* **Full power** — always (Fast mode).

The arbiter takes the highest proposal (grid strategies win ties, so the
battery-hold below stays engaged), then applies the shared constraints: the
home-battery policy, 1↔3-phase resolution with hysteresis + dwell, and the
start-confirmation / ride-out machine that keeps the charger from flapping.

Two speeds, two jobs:

Turning the current knob is cheap and instantly reversible; starting, stopping
and throwing the 1↔3-phase contactor are not. So the same raw surplus is
tracked through two filters and each drives only what it is suited to:

* the **tracking** signal (short time constants, :attr:`Availability.power_w`)
  sets the charging current, so a passing cloud or a switched-on oven reaches
  the amps within seconds;
* the **commitment** signal (long time constants, :attr:`Availability.commit_w`)
  decides whether to charge at all and on how many phases, so those transitions
  stay few and deliberate — on top of the start-confirmation, ride-out and
  phase-dwell timers that were already there.

Home-battery policy (one reserve line, two zones):

* **Below the reserve** the battery comes first: the car gets only genuine
  excess solar and any battery discharge is deducted immediately.
* **At/above the reserve** the battery is a *fluctuation buffer*: the car
  follows the smoothed surplus, the battery bridges short dips and spikes, and
  only sustained discharge into the car is corrected.
* **Comfortably above the reserve** (past the midpoint between the reserve and
  full) the charging current is rounded *up* to the next whole amp instead of
  down — see :func:`_quantize_current`.
* **Whenever a grid strategy wins** (cheap hour, plan, floor, Fast) the battery
  is held (``hold_battery``) so grid power charges the car, never the battery.

Peak protection (the capacity tariff) — a layer, not a strategy:

From 2027 Austrian grid operators bill households on the highest average grid
import over a *fixed clock quarter-hour* in the month, so a single unlucky
15 minutes sets a charge that stands until the month ends. Guarding against that
cannot be a proposal: the arbiter takes the *highest* bid, and a strategy that
wants to charge *less* has no way to say so. Peak protection is therefore a
**ceiling applied after the arbiter** (:func:`apply_peak_guard`), which also
means it covers every branch uniformly — Manual, Fast, ride-out, idle, and the
no-car branch. That last one matters most: a sauna or a heat pump sets the peak
whether or not a car is plugged in, so this layer is a *household* one and its
levers include the home battery, not just the wallbox.

It is off by default, and when off it is a single early return that touches
nothing — the integration behaves exactly as it did before. The *measurement*
(:func:`update_peak_window`) runs regardless, before every gate, so the sensors
stay live and you can watch your peaks before deciding to let anything act.

Everything time-dependent receives ``now`` explicitly so the logic stays
deterministic and testable.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, tzinfo
from enum import StrEnum


class ChargingMode(StrEnum):
    """User-selectable charging mode — a preset over the engine's strategies."""

    SMART = "smart"  # surplus + cheap grid + departure plan
    SOLAR = "solar"  # surplus only
    SOLAR_MIN = "solar_min"  # surplus, but never below the minimum current
    FAST = "fast"  # full power, unconditionally
    MANUAL = "manual"  # the user is the brain (bypasses the arbiter)


#: Modes offered to the user and implemented by :func:`decide`.
SUPPORTED_MODES: tuple[ChargingMode, ...] = (
    ChargingMode.SMART,
    ChargingMode.SOLAR,
    ChargingMode.SOLAR_MIN,
    ChargingMode.FAST,
    ChargingMode.MANUAL,
)

#: v2 → v3 migration: the old mode zoo maps onto the presets. The three
#: price-aware modes were combinations of the same strategies Smart enables.
LEGACY_MODE_MAP: dict[str, ChargingMode] = {
    "off": ChargingMode.MANUAL,
    "pv_only": ChargingMode.SOLAR,
    "pv_minimum": ChargingMode.SOLAR_MIN,
    "pv_price": ChargingMode.SMART,
    "price": ChargingMode.SMART,
    "combined": ChargingMode.SMART,
    "fast": ChargingMode.FAST,
}

#: Modes whose arbiter includes the solar-surplus strategy.
_SOLAR_MODES: frozenset[ChargingMode] = frozenset(
    {ChargingMode.SMART, ChargingMode.SOLAR, ChargingMode.SOLAR_MIN}
)

#: The lowest current any EV accepts (the pilot signal's floor). Every charge
#: bottoms out here; see :func:`_floor_current`.
HARDWARE_MIN_CURRENT_A: float = 6.0


@dataclass(slots=True)
class PriceSlot:
    """One forecast slot: a price valid from ``start`` until the next slot."""

    start: datetime
    price: float


@dataclass(slots=True)
class ChargerInputs:
    """A snapshot of the world, assembled by the coordinator from HA states."""

    car_connected: bool
    # Present charger state.
    car_actual_power_w: float = 0.0
    phases: int = 3
    voltage_v: float = 230.0
    # Energy environment. ``grid_power_w``: + import, - export.
    grid_power_w: float = 0.0
    # The billing meter's cumulative import register, kWh — optional. When present
    # it settles how much the quarter-hour has drawn (see :func:`_apply_meter`);
    # ``grid_power_w`` still drives everything that has to react, including the
    # projection of the rest of the window.
    grid_import_kwh: float | None = None
    pv_power_w: float | None = None
    # Home battery. ``battery_power_w``: + charging, - discharging.
    battery_soc: float | None = None
    battery_power_w: float | None = None
    # Price environment.
    price_now: float | None = None
    price_forecast: list[PriceSlot] | None = None
    # Expected PV production tomorrow (kWh), from an optional mapped solar-forecast
    # sensor. Used by cheap-hour grid charging to decide *how deep* to fill the home
    # battery — not whether to: see ``bright_day_target_soc`` / ``dark_day_target_soc``.
    pv_forecast_kwh: float | None = None
    # Energy delivered in the running session (kWh), anchored at plug-in by the
    # coordinator. Feeds the departure plan (remaining = target − delivered).
    session_delivered_kwh: float | None = None
    # Wall-clock time for deadline/dwell reasoning (None disables time logic).
    now: datetime | None = None


@dataclass(slots=True)
class EngineConfig:
    """Current settings — mostly runtime-adjustable via number/select entities."""

    mode: ChargingMode = ChargingMode.MANUAL
    smart_enabled: bool = True
    # The *Solar + minimum* floor: what that mode tops up to from the grid. It
    # binds in no other mode — read it through :func:`_floor_current`, never
    # directly.
    min_current_a: float = 6.0
    max_current_a: float = 16.0
    # The home-battery reserve line (% SoC): below it the battery comes first
    # (the car gets only genuine excess solar); at/above it the battery buffers
    # surplus fluctuations for the car. 100 = always protect.
    battery_reserve_soc: float = 100.0
    cheap_price: float = 0.15  # ≤ this (currency/kWh) counts as "cheap grid"
    target_energy_kwh: float = 0.0  # 0 disables deadline planning
    departure: datetime | None = None  # deadline for the departure plan
    # Home-battery discharge override, driven by the card's three-way control:
    # "auto" lets the arbiter decide (hold while grid-charging), "hold" always
    # blocks discharge into the car, "free" never does. See the override at the
    # end of ``decide``/``_decide_manual``.
    battery_hold_mode: str = "auto"
    # Manual mode: the user is the brain. Start/stop, current and phase count
    # come straight from these; the battery is held while grid-assisted.
    manual_charge: bool = False
    manual_current_a: float = 16.0
    manual_phases: int = 3
    # True in the brief window right after the user switches *into* Manual mode,
    # before they touch any manual control. While set, the brain leaves the
    # charger exactly as it found it (no writes) so entering Manual never disturbs
    # an in-progress session. Cleared the moment a manual control is used.
    manual_passive: bool = False
    # Phase switching.
    auto_phase: bool = False
    max_phases: int = 3
    phase_dwell_s: float = 300.0  # min time between phase switches
    phase_confirm_s: float = 120.0  # a threshold crossing must hold this long first
    phase_up_margin_w: float = 500.0  # headroom demanded before climbing to 3φ
    # Solar tracking — the *commitment* filter (start/stop + phase choice). An
    # asymmetric EMA: ``smooth_window_s`` is the slow time constant for a *rising*
    # surplus, ``surplus_drop_tau_s`` the faster one for a *falling* surplus.
    smooth_window_s: float = 120.0  # gentle time constant when the surplus rises
    surplus_drop_tau_s: float = 20.0  # fast time constant when the surplus falls
    # …and the *tracking* filter, which sets the charging current. Short in both
    # directions: the amps are meant to follow reality, not to be a commitment.
    # How short is bounded by the sample rate — see the notes in ``const.py``.
    track_rise_tau_s: float = 12.0
    track_drop_tau_s: float = 5.0
    discharge_tolerance_w: float = 300.0  # sustained battery→car drain above this…
    discharge_grace_s: float = 180.0  # …for this long triggers a decisive ease-off
    # How the buffer-zone battery-discharge penalty builds and fades: it ramps in
    # slowly (that lag *is* the battery bridging a short dip) but is released far
    # faster, so a dip that is over stops holding the current down.
    discharge_attack_s: float = 120.0
    discharge_release_s: float = 40.0
    # Start/stop shaping ("ride out, then stop").
    start_confirm_s: float = 180.0  # surplus must hold ≥ min this long to start
    stop_ride_out_s: float = 300.0  # keep min current this long through a dip
    # --- Peak protection (capacity tariff) -------------------------------------
    # Off by default, and when off :func:`apply_peak_guard` returns immediately
    # without touching a thing. The three limits are compared against the
    # *projected* end-of-window average, in watts.
    peak_guard_enabled: bool = False
    peak_soft_w: float = 3300.0  # start easing the wallbox down
    peak_target_w: float = 3700.0  # the ceiling the budget aims at
    peak_hard_w: float = 3900.0  # cut now; pause the car if the budget can't carry 6 A
    # Once this month has already recorded a higher peak, holding below the target
    # saves nothing — the charge is booked. See ``_effective_targets``.
    peak_follow_month: bool = True
    # …but aim a little *under* that record rather than at it, or the allowance
    # ratchets: a window that overshoots by a few watts sets a new record, which
    # raises the ceiling, which invites the next overshoot.
    peak_month_buffer_w: float = 200.0
    # The SoC ladder: the mapped minimum-SoC entity sits at the reserve normally and
    # drops to the floor while shaving. Clamped so the floor is never above it.
    shaving_reserve_soc: float = 50.0
    peak_min_soc: float = 35.0
    peak_confirm_s: float = 120.0  # a soft-tier crossing must hold this long
    peak_release_s: float = 120.0  # …and so must a release, in the other direction
    peak_dwell_s: float = 60.0  # min time between tier changes (releases only)
    # The home battery's usable capacity. Lets a heavy load lean on the grid a little
    # *earlier* when the stored energy won't last (see :func:`_house_share`); 0 means
    # unknown, and the battery then covers the excess until its floor.
    battery_capacity_kwh: float = 0.0
    # --- Cheap-hour grid charging ------------------------------------------------
    # Commands the mapped ESS grid setpoint. On an ESS the setpoint *is* total grid
    # import, so this is capped by the live peak budget by construction.
    grid_charge_enabled: bool = False
    grid_setpoint_w: float = 50.0  # the normal (non-charging) import setpoint
    cheap_charge_power_w: float = 2000.0  # what a cheap hour may import
    bright_day_target_soc: float = 40.0  # stop here when tomorrow looks good
    dark_day_target_soc: float = 80.0  # …and fill to here when it doesn't
    pv_forecast_low_kwh: float = 8.0  # below this, tomorrow counts as "dark"
    # --- Keeping the battery able to shave ------------------------------------------
    # Cheap hours first, then any hour: the two targets above are what a *cheap* hour
    # fills to, and this is the level below which the battery is topped up at **any**
    # price. In a December week the binding constraint is not what the energy costs,
    # it is having any stored energy at all — a pack sitting on its floor defends
    # nothing, and the five cheap midday hours do not keep up with a house that draws
    # 30–58 kWh a day against ~1 kWh of PV. Only consulted while peak protection is
    # on; 0 disables it, which is exactly the old behaviour.
    peak_ready_soc: float = 0.0
    # --- Stocking up before a known event --------------------------------------------
    # The user knows tonight is a sauna; the brain cannot. While this is set the
    # battery fills toward its target at any price *and is held there* — ordinary
    # afternoon load is served from the grid, which sits far below the ceiling anyway,
    # instead of quietly spending the stock before the event it was bought for.
    stock_up: bool = False
    stock_up_target_soc: float = 95.0
    # --- The user's calendar and clock ---------------------------------------------
    # Everything else in here works in UTC, which is right for arithmetic and wrong
    # for two things a *person* reads: the month a demand charge is billed in, and
    # the time a reason string quotes. Both come from the wall clock the user lives
    # on, so the coordinator hands us Home Assistant's configured time zone. ``None``
    # means UTC, which keeps this module's own tests clock-agnostic.
    local_tz: tzinfo | None = None


@dataclass(slots=True)
class EngineState:
    """Mutable memory carried across cycles by the coordinator.

    Holds the smoothing windows and the timers of the start/stop machine; it is
    reset on restart, which simply means the windows and timers start fresh.
    """

    # Phase hysteresis/dwell memory. ``phase_want`` is the switch we are currently
    # confirming (see ``_resolve_phases``), armed at ``phase_want_since``.
    # ``phases`` is what the *solar* strategy last chose; ``phases_targeted`` is what
    # the finalized decision last asked the charger for, whichever strategy won, so
    # the dwell timer sees grid-path switches too (see ``_stamp_phase_change``).
    phases: int | None = None
    phases_targeted: int | None = None
    phase_changed_at: datetime | None = None
    phase_want: int | None = None
    phase_want_since: datetime | None = None
    # Start/stop machine.
    charging: bool | None = None
    active_source: str | None = None  # "solar" | "grid" while charging
    surplus_ok_since: datetime | None = None
    ride_out_since: datetime | None = None
    # One-shot "start now" from the user (the card's countdown chip / the Start
    # now button): skip the remaining start-confirmation wait on the next cycle.
    # Consumed by that cycle whatever it decides — see ``_decide``.
    start_override: bool = False
    # Since when the car has been allowed to charge but drawing nothing (see
    # :func:`_release_hold_for_idle_car`). None while it draws, or isn't allowed to.
    car_idle_since: datetime | None = None
    # Battery-buffer memory.
    discharge_high_since: datetime | None = None
    avail_zone: str | None = None  # "protect" | "buffer" the samples belong to
    # Whether the battery is currently far enough above its reserve for the
    # generous rounding (kept in state so the threshold can have hysteresis).
    generous: bool = False
    # Surplus filters: the last emitted value of the commitment filter
    # (``avail_output``), of the tracking filter (``track_output``) and of the
    # battery-discharge penalty, plus the time they were all sampled, so the next
    # cycle's directional EMAs know the elapsed time.
    avail_output: float | None = None
    track_output: float | None = None
    discharge_output: float | None = None
    avail_sample_t: datetime | None = None
    # --- Peak protection ----------------------------------------------------------
    # The billing quarter-hour accumulator. ``peak_sample_w`` is the last grid
    # reading, *held* until the next sample (zero-order hold), which is what makes
    # the integral correct under the coordinator's irregular event-driven cadence.
    peak_window_start: datetime | None = None
    peak_window_wh: float = 0.0
    peak_window_degraded: bool = False  # part of this window went unmeasured
    peak_seen_good: bool = False  # a trustworthy reading arrived in this window
    peak_sample_t: datetime | None = None
    peak_sample_w: float = 0.0
    # The billing meter's import register, when one is mapped. The window's energy is
    # ``peak_meter_base_wh`` (what the power integral measured before the anchor) plus
    # the register's climb since ``peak_meter_anchor_kwh``. ``_clean`` records whether
    # the window was still fully measured when the anchor was set — only then may an
    # exact register reading vouch for the whole window again. ``_last_kwh/_t`` is the
    # last *accepted change*, kept across windows to tell a real climb from a jump.
    peak_meter_anchor_kwh: float | None = None
    peak_meter_base_wh: float = 0.0
    peak_meter_anchor_clean: bool = False
    peak_meter_last_kwh: float | None = None
    peak_meter_last_t: datetime | None = None
    peak_window_metered: bool = False  # the energy so far is the register's figure
    # Trailing 15-minute samples, for the display-only rolling average. Bounded by
    # the trim in :func:`update_peak_window`, never read by the control path.
    peak_rolling: list[tuple[datetime, float]] = field(default_factory=list)
    # The month record — the number that actually gets billed. Only *completed*,
    # non-degraded windows update it.
    month_key: str = ""  # "2027-01"
    month_peak_w: float = 0.0
    month_peak_at: datetime | None = None
    prev_month_peak_w: float = 0.0
    peak_history: list[tuple[datetime, float]] = field(default_factory=list)
    # Tier hysteresis, mirroring the phase machine: ``peak_tier_want`` is the tier
    # currently being confirmed, armed at ``peak_tier_want_since``.
    peak_tier: str = "off"  # "off" | "soft" | "hard"
    peak_tier_want: str | None = None
    peak_tier_want_since: datetime | None = None
    peak_changed_at: datetime | None = None
    # The cap in force (A). Falls freely, rises only after the dwell.
    peak_cap_a: float | None = None
    peak_cap_at: datetime | None = None
    # The grid request's peak ceiling (A) on ``peak_request_phases`` phases — the
    # same one-sided limiter as the cap, for the *request* the cap never sees.
    peak_request_a: float | None = None
    peak_request_at: datetime | None = None
    peak_request_phases: int | None = None
    # The car's own ramp (see :func:`_settled_inputs`): what the last raise asked the
    # car to draw (W), and when.
    car_expected_w: float | None = None
    car_raised_at: datetime | None = None
    # The house share (see :func:`_house_share`): whether a heavy load is being split
    # between grid and battery, and since when the load has been back under the
    # budget (for the release confirmation).
    peak_share_engaged: bool = False
    peak_share_calm_since: datetime | None = None
    peak_share_setpoint_w: float | None = None  # the setpoint last handed out
    grid_charging: bool = False


@dataclass(slots=True)
class Decision:
    """The engine's output for one cycle.

    ``control`` is False when the brain should keep its hands off entirely
    (smart control disabled, Manual-passive, stale data) — the coordinator then
    writes nothing, leaving manual/app control untouched.
    """

    control: bool
    should_charge: bool = False
    target_current_a: float = 0.0
    target_phases: int = 3
    # Force the phase entity to be written this cycle even when auto-phase is off
    # (Manual mode picks phases explicitly). Smart fixed-phase modes leave it False
    # so they never touch a phase switch the user controls.
    write_phases: bool = False
    # The surplus this decision acted on (W) — the responsive tracking signal
    # while charging (it is what sets the current), the calm commitment signal
    # while waiting (it is what the start gate is waiting for). So the number on
    # the card always matches the number quoted in ``reason``.
    surplus_w: float = 0.0
    reason: str = ""
    # Structured form of ``reason`` so the Lovelace card can localize it: a stable
    # catalog key plus its pre-formatted string params. ``reason`` itself stays the
    # English rendering (logs, tests, non-card consumers). See ``_reason``.
    reason_key: str = ""
    reason_params: dict[str, str] = field(default_factory=dict)
    # True while we are deliberately grid-charging and want the home battery
    # blocked from discharging into the car (driven onto a user-mapped hold
    # switch by the coordinator).
    hold_battery: bool = False
    # Whether the hold above was chosen by the arbiter ("auto") or forced by the
    # user's three-way control ("hold"/"free"). Surfaced so the card can label the
    # shield chip "held (manual)" vs the brain's live choice.
    hold_source: str = "auto"
    # The booked cheap-charge windows (ISO slot starts) the departure plan would
    # charge in — recomputed every cycle and, until now, discarded. Feeds the
    # card's plan strip. Empty when no deadline plan is active.
    plan: list[str] = field(default_factory=list)
    # Dwell/countdown deadlines the card ticks down, or None when not armed:
    #  * resume_not_before — a solar start is confirming; charging resumes at this time
    #  * pause_not_before  — riding out a surplus dip; a clean stop happens at this time
    #  * phase_locked_until — the 1↔3 contactor is in its dwell window until this time
    resume_not_before: datetime | None = None
    pause_not_before: datetime | None = None
    phase_locked_until: datetime | None = None
    # --- Peak protection -----------------------------------------------------------
    # ``control`` above governs the *charger*. Peak protection also drives *house*
    # outputs (the ESS grid setpoint, the minimum-SoC number, the battery-hold
    # switch), and it does so under its own switch rather than under Smart control —
    # a demand charge is money whether or not the brain is driving the wallbox. So
    # the two permissions are separate. With peak protection off this is simply set
    # to ``control``, which is exactly the old behaviour (the hold switch was written
    # precisely when the brain controlled).
    house_control: bool = False
    peak_tier: str = "off"  # "off" | "soft" | "hard"
    # The billing quarter-hour, surfaced for the sensors and the card.
    peak_window_avg_w: float = 0.0  # running average so far
    peak_projected_w: float = 0.0  # end-of-window average if the present draw holds
    peak_allowed_w: float = 0.0  # total grid import allowed for the rest of it
    peak_rolling_w: float = 0.0  # plain trailing 15-min average (display only)
    peak_window_ends: datetime | None = None
    peak_degraded: bool = False  # part of the window went unmeasured
    peak_metered: bool = False  # this window's energy is the billing meter's count
    month_peak_w: float = 0.0  # the highest completed window this month
    # The three limits *in force* — i.e. after the month-peak allowance, which is why
    # they can sit above the numbers the user typed. The card draws these, so the
    # formula lives here rather than being repeated by the sensor.
    peak_soft_w: float = 0.0
    peak_target_w: float = 0.0
    peak_hard_w: float = 0.0
    # A second reason string, in the same shape as ``reason`` above, for the peak
    # status sensor — kept separate so the charging reason never has to compete with
    # it for the one line the card shows.
    peak_reason: str = ""
    peak_reason_key: str = ""
    peak_reason_params: dict[str, str] = field(default_factory=dict)
    # Values for the optional mapped Victron entities. None = don't write at all,
    # which is what keeps an unmapped or disabled setup completely untouched.
    grid_setpoint_w: float | None = None
    battery_min_soc: float | None = None
    grid_charging: bool = False  # deliberately importing on a cheap price


# Ignore tiny home-battery discharge (sensor noise / standby) before the guard
# below starts trimming grid-charge current.
_BATTERY_DRAIN_TOLERANCE_W: float = 100.0

# Manual charging counts as grid-assisted (→ hold the battery) once the
# requested power exceeds the available surplus by more than this margin.
_MANUAL_GRID_MARGIN_W: float = 100.0

# A car that is allowed to charge but draws less than this is not charging — it
# is full, or waiting on its own timer. Well under the 1.4 kW a single phase at the
# 6 A minimum delivers, well over the standby trickle of a car that has finished.
_CAR_DRAWING_MIN_W: float = 300.0
# How long the car has to sit there not drawing before the battery hold lets go.
# Long enough for a freshly started (or freshly woken) car to ramp up.
_CAR_IDLE_RELEASE_S: float = 180.0

# How far the SoC may fall back below the generous-rounding threshold before the
# rounding turns conservative again (see :func:`_generous_rounding`). Rounding up
# discharges the battery a little, which would otherwise walk the SoC straight
# back across the threshold and make the rounding direction chatter.
_GENEROUS_EXIT_MARGIN_PCT: float = 3.0


@dataclass(slots=True)
class PowerFlow:
    """Live power balance (W) for the energy-flow visualization.

    Sign conventions match :class:`ChargerInputs`: ``grid`` is + import / −
    export, ``battery`` is + charging / − discharging. ``house`` is everything
    the home consumes *other* than the car, derived from the balance
    ``pv + grid_import + battery_discharge = house + car + battery_charge``.
    """

    pv_w: float
    grid_w: float
    battery_w: float | None
    battery_soc: float | None
    car_w: float
    house_w: float


def compute_power_flow(inp: ChargerInputs) -> PowerFlow:
    """Derive the home energy balance from a world snapshot.

    ``house`` consumption is what's left once the car and the home battery's
    charge/discharge are accounted for; clamped at zero so sensor noise can't
    show the house "producing" power.
    """
    pv = inp.pv_power_w or 0.0
    grid = inp.grid_power_w
    battery = inp.battery_power_w
    car = max(0.0, inp.car_actual_power_w)
    # available in = production + net import + battery discharge
    available = pv + grid + max(0.0, -(battery or 0.0))
    # consumed elsewhere = car + battery charge
    other = car + max(0.0, battery or 0.0)
    house = max(0.0, available - other)
    return PowerFlow(
        pv_w=pv,
        grid_w=grid,
        battery_w=battery,
        battery_soc=inp.battery_soc,
        car_w=car,
        house_w=house,
    )


@dataclass(slots=True)
class SourceSplit:
    """How the car's charging power is currently sourced (W), summing to ``car_w``.

    The card renders this as the source bar + the ring around the car: it answers
    the one question the old node diagram couldn't — *how much of the charge is
    free right now?*
    """

    solar_w: float
    battery_w: float
    grid_w: float


def compute_car_sources(flow: PowerFlow) -> SourceSplit:
    """Allocate the car's power across solar, home battery and grid.

    A priority allocation, cheapest source first: the car is fed by leftover PV
    (production beyond the house), then any home-battery discharge, then the grid
    covers whatever remains. The three shares always sum to ``car_w``, so the bar
    and the balance line below it stay consistent.
    """
    car = max(0.0, flow.car_w)
    solar_spare = max(0.0, flow.pv_w - flow.house_w)
    solar = min(car, solar_spare)
    remaining = car - solar
    battery_discharge = max(0.0, -(flow.battery_w or 0.0))
    battery = min(remaining, battery_discharge)
    grid = remaining - battery
    return SourceSplit(solar_w=solar, battery_w=battery, grid_w=grid)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _floor_current(cfg: EngineConfig) -> float:
    """The lowest current a charge may run at in the current mode.

    "Minimum current" belongs to **Solar + minimum**: it is what the minimum-floor
    strategy tops up to from the grid, and the card only offers it in that mode.
    Everywhere else the floor is the EV's own, so a value raised for Solar +
    minimum stops binding the moment you leave it — it used to keep Solar only
    from starting until the sun could carry a current the user could no longer
    see, let alone change.
    """
    if cfg.mode is ChargingMode.SOLAR_MIN:
        return max(HARDWARE_MIN_CURRENT_A, cfg.min_current_a)
    return HARDWARE_MIN_CURRENT_A


def _power_to_current(power_w: float, phases: int, voltage_v: float) -> float:
    return power_w / (phases * voltage_v)


def _current_to_power(current_a: float, phases: int, voltage_v: float) -> float:
    return current_a * phases * voltage_v


# Guards the snap below against floating-point dust (…6.999999 is meant to be 7).
_AMP_EPSILON: float = 1e-6


def _quantize_current(amps: float, cfg: EngineConfig, *, up: bool) -> float:
    """Snap a computed current to a whole amp — the only resolution the charger has.

    The charger takes integer amps, so a surplus never divides evenly and the
    charge lands either just below it (the remainder is exported) or just above
    it (the remainder comes out of the home battery). One amp is ~230 W on a
    single phase and ~690 W on three, so *which side we land on* is a real
    decision, not a rounding detail — and it is made here rather than by
    truncating on the way to the charger.

    ``up`` picks the side: the ceiling while the home battery is comfortably
    charged (see :func:`_generous_rounding`), the floor otherwise. The result is
    re-clamped, so the snap can never push the current outside the configured
    band — in particular a surplus already at the maximum stays there.
    """
    snapped = math.ceil(amps - _AMP_EPSILON) if up else math.floor(amps + _AMP_EPSILON)
    return _clamp(float(snapped), _floor_current(cfg), cfg.max_current_a)


def _generous_rounding(
    cfg: EngineConfig, soc: float | None, protect: bool, state: EngineState
) -> bool:
    """May the charging current round *up* past the surplus right now?

    Rounding up means the last few hundred watts come out of the home battery
    instead of being exported — worth it only when the battery is not just above
    its reserve line but *comfortably* above it, so lending the car a little
    costs nothing that the day's remaining sun won't put back. "Comfortably" is
    the midpoint between the reserve and full: reserve 80 % → from 90 % SoC.

    Never in the protect zone (below the reserve the battery comes first), never
    without an SoC reading, and never with the reserve at 100 %: there the user
    has asked for the battery to be protected unconditionally, so the car gets
    the floor and the remainder goes to the grid.

    Leaving the zone takes a few points more than entering it
    (:data:`_GENEROUS_EXIT_MARGIN_PCT`), because rounding up nudges the SoC back
    down across the very threshold that enabled it.
    """
    if protect or soc is None or cfg.battery_reserve_soc >= 100.0:
        state.generous = False
        return False
    midpoint = (cfg.battery_reserve_soc + 100.0) / 2.0
    threshold = (
        midpoint - _GENEROUS_EXIT_MARGIN_PCT if state.generous else midpoint
    )
    state.generous = soc >= threshold
    return state.generous


# --- Solar availability (the surplus strategy's signal) --------------------------

def _directional(
    prev: float | None,
    last_t: datetime | None,
    now: datetime | None,
    value: float,
    tau_up_s: float,
    tau_down_s: float,
) -> float:
    """Asymmetric exponential filter: track drops fast, rises slow.

    Surplus charging wants opposite speeds in the two directions: ease the current
    *up* gently when the surplus grows (so a passing bright patch doesn't yo-yo the
    wallbox) but follow a *falling* surplus quickly (so a cloud or a switched-on
    appliance stops us drawing from the grid/home battery within tens of seconds,
    not two minutes). This is an EMA whose time constant depends on the direction of
    change: ``tau_down_s`` (short) while ``value`` is below the running output,
    ``tau_up_s`` (long) while at/above it.

    Because it is still an average, a single noisy low sample only nudges the output
    part-way down — the current can't be slammed by one bad reading. With
    ``now``/``prev`` unknown the value passes through raw (stateless one-shot
    reasoning / the first sample after a reset). The blend factor is derived from the
    *actual* elapsed time since the last sample, so irregular event-driven updates
    are weighted correctly.
    """
    if prev is None or now is None or last_t is None:
        return value
    dt = max(0.0, (now - last_t).total_seconds())
    tau = tau_up_s if value >= prev else tau_down_s
    if tau <= 0.0:
        return value
    alpha = 1.0 - math.exp(-dt / tau)
    return prev + alpha * (value - prev)


@dataclass(slots=True)
class Availability:
    """Solar power available to the car right now, and how it was derived.

    Two numbers, same underlying surplus (see the module docstring): ``power_w``
    is the responsive one the charging *current* follows, ``commit_w`` the calm
    one the *decisions* follow — whether to charge at all, and on how many phases.
    """

    power_w: float
    commit_w: float
    zone: str  # "protect" (below reserve / SoC unknown) or "buffer"
    eased: bool  # sustained battery→car discharge is being corrected
    generous: bool = False  # battery comfortably charged → round the amps up


def compute_availability(
    inp: ChargerInputs, cfg: EngineConfig, state: EngineState
) -> Availability:
    """Solar power available to the car (W), per the battery policy.

    The underlying identity — invariant to the car's own current changes, so it
    can be smoothed without chasing our own moves — is::

        available = PV − house = car_draw + battery_signed − grid_signed

    (``grid_signed``: + import, − export, so exporting adds and importing
    subtracts. ``battery_signed``: + charging adds reclaimable solar,
    − discharging subtracts power that is *not* solar.)

    Two zones from the single reserve line:

    * **protect** (SoC below the reserve, or unknown): the battery comes first.
      No reclaim of solar the battery is absorbing, and any discharge is
      deducted immediately — zero tolerance.
    * **buffer** (SoC at/above the reserve): solar flowing into the battery is
      reclaimable for the car, and discharge is deducted through a filter that
      builds slowly — that lag *is* the battery bridging short dips and spikes —
      but is released quickly once the dip is over, so a battery that has stopped
      discharging stops holding the current down. Sustained discharge beyond
      ``discharge_tolerance_w`` for ``discharge_grace_s`` switches to the raw
      deduction (a decisive ease-off).

    The base surplus runs through :func:`_directional` twice, at the two speeds
    described in the module docstring, giving the tracking and commitment
    signals. The battery penalty is shared: it is a statement about the *world*,
    not about how eagerly we act on it.

    Deep inside the buffer zone the result also carries ``generous``, which lets
    the charging current round up past the surplus (:func:`_generous_rounding`).
    """
    export_w = max(0.0, -inp.grid_power_w)
    car_draw = max(0.0, inp.car_actual_power_w)
    batt = inp.battery_power_w
    soc = inp.battery_soc
    protect = soc is None or soc < cfg.battery_reserve_soc
    zone = "protect" if protect else "buffer"
    generous = _generous_rounding(cfg, soc, protect, state)

    # The formula changes across the reserve line; a value carried over from the
    # other zone would blend two different signals, so start the filter fresh.
    if zone != state.avail_zone:
        state.avail_output = None
        state.track_output = None
        state.discharge_output = None
        state.avail_sample_t = None
        state.discharge_high_since = None
        state.avail_zone = zone

    discharge_raw = max(0.0, -batt) if batt is not None else 0.0
    if protect:
        # Battery comes first: all solar fills it, so the car gets only genuine
        # grid export. The car's own draw is deliberately NOT counted — released,
        # that power flows into the below-reserve battery, not the grid, so
        # treating it as "available" would keep an already-running car alive and
        # starve the battery (raising the reserve above the SoC would never stop
        # the charge). The reclaim below is the buffer-zone counterpart: there
        # the battery is satisfied, so both the car's draw and the solar the
        # battery absorbs are genuine surplus for the car.
        base = export_w
    else:
        # The full identity, with the *signed* grid: export adds to what is
        # available, import subtracts from it. Clamping the grid to its export
        # side here would count the car's draw as surplus even while the grid is
        # importing to supply it — a phantom surplus the car would never back off
        # from (a home battery normally masks this by discharging instead, which
        # the penalty below catches, but not when it is held or power-limited).
        base = -inp.grid_power_w + car_draw
        if batt is not None:
            base += max(0.0, batt)  # reclaim solar the battery is absorbing

    # All three filters advance off the same previous sample time.
    last_t = state.avail_sample_t
    commit_base = _directional(
        state.avail_output,
        last_t,
        inp.now,
        base,
        cfg.smooth_window_s,
        cfg.surplus_drop_tau_s,
    )
    track_base = _directional(
        state.track_output,
        last_t,
        inp.now,
        base,
        cfg.track_rise_tau_s,
        cfg.track_drop_tau_s,
    )
    state.avail_output = commit_base
    state.track_output = track_base

    if protect:
        state.avail_sample_t = inp.now
        return Availability(
            power_w=max(0.0, track_base - discharge_raw),
            commit_w=max(0.0, commit_base - discharge_raw),
            zone=zone,
            eased=False,
            generous=False,
        )

    # Buffer zone: the penalty ramps in over ``discharge_attack_s`` (the bridging
    # tolerance) and is released over the shorter ``discharge_release_s``.
    dis_s = _directional(
        state.discharge_output,
        last_t,
        inp.now,
        discharge_raw,
        cfg.discharge_attack_s,
        cfg.discharge_release_s,
    )
    state.discharge_output = dis_s
    state.avail_sample_t = inp.now

    # The ease-off is meant to catch the battery *becoming the car's power
    # source*. While the current is deliberately rounded up, one amp step of
    # discharge is our own doing, so the guard measures beyond that — otherwise a
    # 3φ charge would sit permanently in "easing off" over a rounding decision.
    tolerance = cfg.discharge_tolerance_w
    if generous:
        tolerance += _current_to_power(1.0, max(1, inp.phases), inp.voltage_v)
    eased = _track_sustained_discharge(inp, cfg, state, discharge_raw, tolerance)
    penalty = discharge_raw if eased else dis_s
    return Availability(
        power_w=max(0.0, track_base - penalty),
        commit_w=max(0.0, commit_base - penalty),
        zone=zone,
        eased=eased,
        generous=generous,
    )


def _track_sustained_discharge(
    inp: ChargerInputs,
    cfg: EngineConfig,
    state: EngineState,
    discharge_raw: float,
    tolerance_w: float,
) -> bool:
    """True once the battery has discharged beyond tolerance for the grace time."""
    if inp.now is None or discharge_raw <= tolerance_w:
        state.discharge_high_since = None
        return False
    if state.discharge_high_since is None:
        state.discharge_high_since = inp.now
    return (
        inp.now - state.discharge_high_since
    ).total_seconds() >= cfg.discharge_grace_s


def _battery_guard_current(
    full_current_a: float,
    phases: int,
    inp: ChargerInputs,
    cfg: EngineConfig,
    *,
    hold: bool,
) -> tuple[float, bool]:
    """Trim grid-charge current so the home battery isn't drained into the car.

    The home battery system regulates the grid to ~0, so it automatically covers
    any load above solar — which means a grid charge will *drain the home battery*
    unless something stops it. The real fix is the hold switch (turned on by the
    coordinator whenever ``Decision.hold_battery`` is set), which blocks discharge
    so the grid supplies the car. This is the *fallback* for when no hold switch is
    mapped (or it has no effect): we lower the car's current by whatever the
    battery is discharging. With the grid pinned at 0 this does **not** shift the
    load onto the grid — it simply throttles the car back down to the genuine
    solar surplus (never below the EV's minimum current), which is the best we can
    do without a hold switch. Re-evaluated each cycle, so it converges as the
    inverter responds.

    Returns ``(current, guarded)`` where ``guarded`` flags that we trimmed.
    """
    if not hold or inp.battery_power_w is None:
        return full_current_a, False
    discharge_w = max(0.0, -inp.battery_power_w)
    if discharge_w <= _BATTERY_DRAIN_TOLERANCE_W:
        return full_current_a, False
    trim_a = _power_to_current(discharge_w, max(1, phases), inp.voltage_v)
    # Snapped down: a protective trim that rounded *up* would hand part of the
    # drain we are trying to stop straight back to the car.
    guarded_a = _quantize_current(
        max(_floor_current(cfg), full_current_a - trim_a), cfg, up=False
    )
    return guarded_a, guarded_a < full_current_a


# Below this a "top-up" is rounding dust, not a source worth naming.
_TOPUP_NAMING_TOLERANCE_W: float = 50.0


def _topup_source_key(inp: ChargerInputs, gap_w: float, *, hold: bool) -> str:
    """Name the *true* source of a minimum-floor top-up.

    The arbiter files the minimum floor under ``source="grid"``, but that label
    means "beyond the surplus", not "out of the meter". Where the extra watts
    really come from is the home battery's decision: held, the battery is blocked
    and the grid supplies them; free, the battery covers them and the grid stays
    at zero. Saying "topping up from grid" while the battery quietly does the
    work contradicts the very source bar drawn underneath the sentence.

    So: the hold is the intent and settles it on its own (and avoids flickering
    while the inverter catches up with a freshly-set hold). With the battery free
    the answer is a measured fact, read through the *same* allocation the card
    draws — the two can then never disagree.
    """
    if gap_w < _TOPUP_NAMING_TOLERANCE_W:
        return "solar_min_covered"
    if hold:
        return "solar_min_topup"
    split = compute_car_sources(compute_power_flow(inp))
    if split.battery_w > split.grid_w:
        return "solar_min_topup_battery"
    return "solar_min_topup"


# --- The departure plan -----------------------------------------------------------

def _slot_minutes(forecast: list[PriceSlot], index: int) -> float:
    """Length of slot ``index`` in minutes (falls back to 60 at the tail)."""
    if index + 1 < len(forecast):
        delta = forecast[index + 1].start - forecast[index].start
        minutes = delta.total_seconds() / 60.0
        if minutes > 0:
            return minutes
    return 60.0


def _plan_remaining_kwh(inp: ChargerInputs, cfg: EngineConfig) -> float | None:
    """Energy still owed to the departure target, or None when not planning.

    Subtracts what the running session has already delivered, so the plan books
    only the cheap hours actually still needed — and stops once the target is in
    the car.
    """
    if not cfg.target_energy_kwh or cfg.departure is None or inp.now is None:
        return None
    return cfg.target_energy_kwh - (inp.session_delivered_kwh or 0.0)


@dataclass(slots=True)
class _Plan:
    """The greedy departure plan for one cycle (see :func:`_compute_plan`)."""

    urgent: bool  # every remaining hour is needed → charge regardless of price
    remaining_kwh: float
    chosen: set[int]  # forecast indices booked to cover ``remaining_kwh``
    current_index: int | None  # the forecast slot covering "now"


def _compute_plan(
    inp: ChargerInputs, cfg: EngineConfig, phases: int, ceiling_w: float | None = None
) -> _Plan | None:
    """Greedy cheapest-slots departure plan, or None when not planning.

    Recomputed every cycle so it self-corrects as prices update and energy is
    delivered. ``phases`` is the phase count grid charging would actually use, so
    the per-slot capacity is realistic (a 1φ-locked wallbox books three times the
    hours).

    ``ceiling_w`` is the peak-protection head-room (see
    :func:`peak_charge_ceiling_w`). Booking slots at full power is what makes a plan
    peak-hostile: it minimises the *number of hours* by maximising the kilowatts,
    which is precisely the quantity a capacity tariff bills. Sizing each slot at what
    fits under the target instead books more, quieter hours for the same energy.

    The target stays a **hard guarantee** and outranks the ceiling: the plan keeps
    booking the least-expensive remaining slots until their capacity covers the
    remaining energy, whether or not they are "cheap" — and if the remaining time
    barely covers it *at full power*, it charges regardless of both the forecast and
    the ceiling (``urgent``). A car that can't make the trip is worse than a demand
    charge; the reason string says which one we bought.
    """
    remaining = _plan_remaining_kwh(inp, cfg)
    if remaining is None or remaining <= 0:
        return None
    if inp.now >= cfg.departure:
        return None

    full_power_kw = _current_to_power(cfg.max_current_a, phases, inp.voltage_v) / 1000.0
    if full_power_kw <= 0:
        return None
    max_power_kw = full_power_kw
    if ceiling_w is not None:
        max_power_kw = min(
            max_power_kw,
            _current_to_power(_ceiling_amps(ceiling_w, phases, inp), phases,
                              inp.voltage_v) / 1000.0,
        )

    # Safety net (also covers a missing/short forecast): when every remaining hour is
    # needed to make the target, price no longer matters. Measured at **full** power,
    # not at the ceiling — this is the test for "can it still be done at all", and
    # answering it with the throttled figure would declare an emergency (and buy the
    # peak) while there was still room to spread the charge.
    hours_left = (cfg.departure - inp.now).total_seconds() / 3600.0
    if hours_left * full_power_kw <= remaining:
        return _Plan(True, remaining, set(), None)

    if not inp.price_forecast:
        return None

    upcoming = [
        (i, s)
        for i, s in enumerate(inp.price_forecast)
        if s.start < cfg.departure
        and s.start + timedelta(minutes=_slot_minutes(inp.price_forecast, i)) > inp.now
    ]
    if not upcoming:
        return None

    chosen: set[int] = set()
    energy = 0.0
    for i, _slot in sorted(upcoming, key=lambda pair: pair[1].price):
        if energy >= remaining:
            break
        chosen.add(i)
        energy += max_power_kw * (_slot_minutes(inp.price_forecast, i) / 60.0)

    # The slot covering "now" is the upcoming slot with the latest start ≤ now.
    current_index = max(
        (i for i, s in upcoming if s.start <= inp.now),
        default=upcoming[0][0],
    )
    return _Plan(False, remaining, chosen, current_index)


def _plan_window_starts(inp: ChargerInputs, plan: _Plan | None) -> list[str]:
    """ISO starts of the booked cheap-charge windows, for the card's plan strip."""
    if plan is None or not inp.price_forecast:
        return []
    return [
        inp.price_forecast[i].start.isoformat()
        for i in sorted(plan.chosen)
        if i < len(inp.price_forecast)
    ]


def _deadline_now(plan: _Plan | None, inp: ChargerInputs) -> tuple[str, dict[str, str]] | None:
    """Should the departure plan grid-charge *right now*? Returns (reason_key, params)."""
    if plan is None:
        return None
    if plan.urgent:
        return "deadline_urgent", {"remaining": f"{max(0.0, plan.remaining_kwh):.0f}"}
    if plan.current_index is not None and plan.current_index in plan.chosen:
        price = inp.price_forecast[plan.current_index].price
        return "deadline_plan", {
            "price": f"{price:.3f}",
            "remaining": f"{plan.remaining_kwh:.0f}",
        }
    return None


# --- Phase resolution --------------------------------------------------------------

# Above this the car is drawing enough for the per-phase currents to say how many
# phases are live; below it ``inp.phases`` is only the configured mode.
_PHASE_MEASURED_MIN_W = 500.0


def _actual_phases(inp: ChargerInputs, cfg: EngineConfig, state: EngineState) -> int:
    """Where the contactor is right now, best-effort.

    While the car is drawing, ``inp.phases`` is measured off the per-phase currents
    (see ``goe_parse.phases_from_nrg``) and is the truth, whoever last moved the
    contactor — a cheap-grid hour, the go-e app, a restart that forgot. Idle it
    degrades to the configured ``psm`` mode, so the phase the solar strategy last
    chose is the better guess, and 1φ the better default: a fresh surplus should be
    usable from ~1.4 kW rather than waiting for a three-phase minimum.

    One exception, and it is load-bearing: while *our own* switch is still settling,
    our intent beats the measurement. The contactor takes a moment to move and the
    car keeps drawing on the old phases meanwhile, so a decision that re-read the
    measurement would see the phases it just left, decide to switch back, and stamp
    a fresh change — flip-flopping the contactor on every cycle instead of moving it
    once. The dwell window is exactly that settling period, so it doubles as the
    guard. Once it expires the measurement is authoritative again, and a
    disagreement then is a real external override worth reacting to.
    """
    if _phase_dwell_active(inp, cfg, state) and state.phases_targeted in (1, 3):
        return state.phases_targeted
    if inp.car_actual_power_w > _PHASE_MEASURED_MIN_W and inp.phases in (1, 3):
        return inp.phases
    return state.phases if state.phases in (1, 3) else 1


def _phase_dwell_active(inp: ChargerInputs, cfg: EngineConfig, state: EngineState) -> bool:
    """Whether the contactor is still inside its minimum time between switches.

    With ``now`` unknown (stateless one-shot reasoning) there is no time to measure,
    so the dwell never blocks — the convention every other timer here follows.
    """
    if inp.now is None or state.phase_changed_at is None:
        return False
    return (inp.now - state.phase_changed_at).total_seconds() < cfg.phase_dwell_s


def _grid_phases(inp: ChargerInputs, cfg: EngineConfig, state: EngineState) -> int:
    """The phase count the grid strategies may charge on.

    Grid charging wants the full count — it is buying power, not tracking a
    surplus, so there is no hysteresis to apply and no crossing to confirm. It does
    answer to the **dwell** timer, though: the contactor is one piece of hardware,
    and a strategy that may throw it the instant a price crosses undoes the rate
    limit the solar path is obeying. Inside the dwell the grid runs on whatever
    phases are already live and picks the third one up when the window expires.

    The cost is bounded and deliberate: at worst a cheap window opens seconds after
    a solar phase switch and spends up to ``phase_dwell_s`` at 1φ — around 0.6 kWh
    of deferred charging, against a contactor that would otherwise have no rate
    limit at all on the cheapest path to move it.

    Never *downshifts*: with the contactor already at 3φ the dwell has nothing to
    protect, and dropping the grid to one phase to honour a timer would be pure loss.
    """
    if not cfg.auto_phase:
        return max(1, inp.phases)
    if _phase_dwell_active(inp, cfg, state):
        return min(max(1, _actual_phases(inp, cfg, state)), cfg.max_phases)
    return cfg.max_phases


def _resolve_phases(
    surplus_w: float, inp: ChargerInputs, cfg: EngineConfig, state: EngineState
) -> int:
    """Pick 1 or 3 phases for solar charging, with hysteresis, confirmation and dwell.

    ``surplus_w`` is the *commitment* signal: throwing the contactor is a
    commitment, so it must not chase the fast tracking value.

    The thresholds evaluate the surplus against both *candidate* configurations
    (what three phases would minimally need, what one phase could maximally
    deliver) rather than the currently active phase count, so the choice is
    free of the current/target coupling. We switch up to three phases only once
    the surplus can sustain their minimum *plus* ``phase_up_margin_w`` of
    headroom, and back down only once it drops below what a single phase can
    deliver at full current — the gap between the two thresholds is the
    hysteresis band. The margin is deliberately one-sided: widening the band
    downwards would mean sitting at 3φ while a single phase could carry the
    surplus, which means importing to hold the 3φ minimum.

    Two timers then guard the switch itself: the crossing must *hold* for
    ``phase_confirm_s`` (so a spike or a momentary dip never moves the
    contactor), and ``phase_dwell_s`` caps how often it may toggle at all.

    Surplus charging *prefers* a single phase: with no remembered phase yet we
    start at 1φ so a small surplus is used immediately, climbing to 3φ only
    once it sustains the higher minimum.

    ``current`` is where the contactor *is*, not where this strategy last wanted
    it to be. While the car is drawing, ``inp.phases`` is measured off the phase
    currents and is the truth — and it may well have been set by someone else:
    a cheap-grid hour that took 3φ, the go-e app, a restart that forgot. Reading
    our own memory instead means the down-switch branch never fires (we believe
    we are already at 1φ), the early return below skips both timers, and the
    contactor drops out of 3φ unconfirmed. Idle there is no current to measure,
    ``inp.phases`` degrades to the configured ``psm`` mode, and the remembered
    phase — with its 1φ preference for a fresh solar start — is the better guess.
    """
    if not cfg.auto_phase or cfg.max_phases < 3:
        return max(1, inp.phases)

    current = _actual_phases(inp, cfg, state)
    up_threshold = (
        _current_to_power(_floor_current(cfg), 3, inp.voltage_v)
        + cfg.phase_up_margin_w
    )
    down_threshold = _current_to_power(cfg.max_current_a, 1, inp.voltage_v)

    desired = current
    if current == 1 and surplus_w >= up_threshold:
        desired = 3
    elif current == 3 and surplus_w < down_threshold:
        desired = 1

    if desired == current:
        state.phase_want = None
        state.phase_want_since = None
        state.phases = current
        return current

    # The crossing has to hold before the contactor moves. With ``now`` unknown
    # (stateless one-shot reasoning) there is no time to measure, so it passes.
    if inp.now is not None:
        if state.phase_want != desired or state.phase_want_since is None:
            state.phase_want = desired
            state.phase_want_since = inp.now
        if (
            inp.now - state.phase_want_since
        ).total_seconds() < cfg.phase_confirm_s:
            return current

    # Honour the dwell timer before toggling the contactor.
    if _phase_dwell_active(inp, cfg, state):
        return current

    state.phases = desired
    state.phase_changed_at = inp.now
    state.phase_want = None
    state.phase_want_since = None
    return desired


# --- Reasons ------------------------------------------------------------------------

# Reason catalog: a stable key → English template. The engine emits the key plus
# pre-formatted string params; the card localizes the same key (see the card's
# ``reason.*`` strings), while ``reason`` keeps the English rendering for logs and
# tests. Keys are explicit per variant (e.g. ``_guarded``/``_phase`` suffixes)
# rather than composed at runtime, so both sides do plain placeholder substitution.
_REASON_TEMPLATES: dict[str, str] = {
    "smart_disabled": "Smart control disabled",
    "manual_passive": "Manual mode — charger left as-is",
    "manual_paused": "Manual mode — paused",
    "manual_charging": "Manual charging at {amps} A",
    "manual_charging_guarded": (
        "Manual charging at {amps} A (protecting home battery)"
    ),
    "no_car": "No car connected",
    "car_not_drawing": (
        "The car isn't taking power (full, or waiting on its own timer) — "
        "home battery released"
    ),
    "fast":"Fast charging at {amps} A",
    "fast_peak": "Fast charging at {amps} A — as much as fits under the peak limit",
    "cheap_grid": "Cheap grid {price}/kWh ≤ {threshold} → full power",
    "cheap_grid_guarded": (
        "Cheap grid {price}/kWh ≤ {threshold} → full power "
        "(protecting home battery → {amps} A)"
    ),
    "deadline_plan": (
        "Planned cheap hour at {price}/kWh — {remaining} kWh to go by departure"
    ),
    "deadline_plan_guarded": (
        "Planned cheap hour at {price}/kWh — {remaining} kWh to go by departure "
        "(protecting home battery → {amps} A)"
    ),
    "deadline_urgent": (
        "Charging now to make the departure target — {remaining} kWh to go"
    ),
    "deadline_urgent_peak": (
        "Charging at full power to make the departure target — {remaining} kWh to go, "
        "so this quarter-hour will go over your peak limit"
    ),
    "target_reached": "Departure target reached — {delivered} kWh charged",
    "plan_waiting": "Waiting for a planned cheap hour",
    "waiting_battery_reserve": (
        "Waiting — home battery {soc}% < reserve {reserve}%"
    ),
    "waiting_surplus": "Waiting for surplus — {surplus} W < {needed} W needed",
    "surplus_confirm": "Surplus {surplus} W — confirming before start",
    "surplus_ride_out": "Surplus dipped — riding it out at {amps} A",
    "solar_surplus": "Solar surplus {surplus} W → {amps} A",
    "solar_surplus_phase": "Solar surplus {surplus} W → {amps} A ({phases}-phase)",
    "solar_surplus_eased": (
        "Solar surplus {surplus} W → {amps} A (easing off home battery)"
    ),
    "solar_surplus_battery_topup": (
        "Solar surplus {surplus} W → {amps} A — the last {gap} W come from the "
        "home battery instead of being exported"
    ),
    "solar_min_covered": "Minimum {amps} A — the {surplus} W surplus covers it",
    "solar_min_topup": (
        "Minimum {amps} A — surplus is only {surplus} W, so the last {gap} W "
        "come from the grid"
    ),
    "solar_min_topup_battery": (
        "Minimum {amps} A — surplus is only {surplus} W, so the last {gap} W "
        "come from the home battery"
    ),
    # --- Peak protection: the second reason line, on its own sensor ----------------
    "peak_off": "Peak protection is off",
    "peak_ok": "This quarter-hour is heading for {projected} kW — comfortable",
    "peak_watch": (
        "This quarter-hour is heading for {projected} kW, close to the {soft} kW "
        "easing-off point"
    ),
    "peak_shaving_car": (
        "Heading for {projected} kW — easing the car back to {amps} A to stay "
        "under {target} kW"
    ),
    "peak_shaving_house": (
        "Heading for {projected} kW — letting the home battery cover more of the "
        "house to stay under {target} kW"
    ),
    "peak_confirming": (
        "This quarter-hour is heading for {projected} kW, past the {soft} kW "
        "easing-off point — easing off if it stays there"
    ),
    "peak_holding": "Holding this quarter-hour under {target} kW — at {projected} kW",
    "peak_share": (
        "Heavy load — the grid carries {grid} kW and the home battery the "
        "{battery} kW above it, to stay under {target} kW"
    ),
    "peak_share_paced": (
        "Heavy load and the home battery is down to {soc}% — the grid now carries "
        "{grid} kW so the battery lasts"
    ),
    "peak_pause": (
        "Heading for {projected} kW — the car is paused until this quarter-hour "
        "is over at {until}"
    ),
    "peak_battery_empty": (
        "Heading for {projected} kW and the home battery is down to its {soc}% "
        "floor — nothing left to shave with"
    ),
    "peak_degraded": (
        "The grid reading was missing for part of this quarter-hour — holding the "
        "current limit until {until} to be safe"
    ),
    "peak_month_headroom": (
        "This month already peaked at {month} kW, so there is nothing to save by "
        "holding below it — aiming at {target} kW, just under the record"
    ),
    # --- Cheap-hour grid charging --------------------------------------------------
    "grid_charge_dark": (
        "Cheap hour at {price}/kWh and little sun expected — importing {power} W "
        "to fill the home battery to {target}%"
    ),
    "grid_charge_bright": (
        "Cheap hour at {price}/kWh, but tomorrow looks bright — filling the home "
        "battery only to {target}% so the sun has somewhere to go"
    ),
    "grid_charge_full": "Home battery at {soc}% — nothing left to buy this cheaply",
    "grid_charge_ready": (
        "Home battery down to {soc}% and too low to hold the peak limit — importing "
        "{power} W to get it back to {target}%, cheap hour or not"
    ),
    "grid_charge_stock_up": (
        "Stocking up for tonight — importing {power} W to fill the home battery to "
        "{target}% and holding it there"
    ),
    "grid_charge_stocked": "Stocked up: home battery at {soc}%, holding it for tonight",
}


def _reason(key: str, **params: str) -> tuple[str, str, dict[str, str]]:
    """Build a decision reason three ways at once.

    Returns ``(english_text, key, params)``: the English rendering for
    ``Decision.reason`` plus the stable key and params the card localizes from.
    """
    return _REASON_TEMPLATES[key].format(**params), key, params


# --- Peak protection: the capacity tariff (Leistungstarif) --------------------------
#
# The billed quantity is the highest *average grid import over a fixed clock
# quarter-hour* in the month — not an instantaneous reading and not a rolling
# window. Everything here follows from that one fact:
#
# * we integrate import energy over the current quarter-hour and compare the
#   *projection* (where the average lands if the present draw holds) against the
#   limits, so the guard reacts to where the window is heading;
# * the throttle needs no ramp logic, because the remaining-budget formula already
#   tightens smoothly as the window fills;
# * a fresh quarter-hour is a fresh budget, so the guard relaxes on its own at every
#   boundary rather than staying clamped;
# * and once the month has already recorded a higher peak, holding below the target
#   saves nothing at all — see :func:`_effective_targets`.

#: The billing window (s).
PEAK_WINDOW_S: float = 900.0

#: Floor on "time remaining" when sizing the rest-of-window budget. Without it the
#: budget diverges as the window closes: a big draw for the last two seconds really
#: does barely move a 15-minute average, but acting on that would just make the amps
#: leap at every boundary. With it, the last minute is deliberately conservative.
_PEAK_MIN_REMAINING_S: float = 60.0

#: A sample gap longer than this means part of the window went unmeasured.
_PEAK_MAX_GAP_S: float = 120.0

#: How far the projection must fall back below a limit before the tier releases, so
#: a projection sitting on the threshold can't chatter.
_PEAK_HYSTERESIS_W: float = 150.0

# How long after a raise the car's reported power may trail the grid meter. Measured
# live (2026-11-06): the go-e reports a raise ~4 s after the write, and the ESS grid
# reading (5 s cadence) can already contain the ramp a second or two before that.
CAR_RAMP_SETTLE_S: float = 15.0

#: Completed quarter-hours kept for the card's history strip (96 = 24 h).
_PEAK_HISTORY_LEN: int = 96

#: Tier ordering, for "is this tightening or relaxing?".
_PEAK_RANK: dict[str, int] = {"off": 0, "soft": 1, "hard": 2}


@dataclass(slots=True)
class PeakWindow:
    """The current billing quarter-hour, as measured so far.

    ``average_w`` is what the window has drawn to date; ``projected_w`` is where it
    lands if the present draw holds, and is what the tiers compare against;
    ``allowed_w`` is the total grid import the *rest* of the window may take and
    still finish at the target. ``soft_w``/``target_w``/``hard_w`` are the limits
    actually in force, i.e. after the month-peak allowance — always read the tiers
    off these, never off :func:`_peak_thresholds`, which returns the raw settings.
    """

    start: datetime | None
    elapsed_s: float
    remaining_s: float
    imported_wh: float
    average_w: float
    projected_w: float
    allowed_w: float
    rolling_w: float  # plain trailing 15-min average — display only, never control
    soft_w: float
    target_w: float
    hard_w: float
    month_peak_w: float
    degraded: bool  # part of this window went unmeasured → tighten only
    metered: bool = False  # energy so far comes from the billing meter's register


def _window_start(now: datetime) -> datetime:
    """Floor to the clock quarter-hour the grid operator measures against."""
    return now.replace(minute=(now.minute // 15) * 15, second=0, microsecond=0)


def _peak_thresholds(cfg: EngineConfig) -> tuple[float, float, float]:
    """The three limits, ordered ``soft ≤ target ≤ hard``.

    The user can set three independent numbers in any order; rather than sorting
    them (which would silently swap which knob means what) each is raised to at
    least the one below it, so "start easing off at" always stays authoritative.
    """
    soft = max(0.0, cfg.peak_soft_w)
    target = max(soft, cfg.peak_target_w)
    return soft, target, max(target, cfg.peak_hard_w)


def _peak_soc_floor(cfg: EngineConfig) -> float:
    """The SoC peak protection may discharge down to, never above its own reserve.

    Deliberately reads the *raw* reserve, not :func:`_resting_reserve_soc`: stocking
    up must not raise the floor, or the stock it just bought would be unreachable by
    the very event it was bought for.
    """
    return min(cfg.peak_min_soc, cfg.shaving_reserve_soc)


def _resting_reserve_soc(cfg: EngineConfig) -> float:
    """The minimum SoC to hold while *not* actively shaving.

    Stocking up raises it, and that second half is what makes stocking up work at
    all: filling the battery before a known event and then letting the ordinary
    afternoon serve itself from the pack donates the whole stock to a few hours the
    grid could have carried at a third of the ceiling.
    """
    if cfg.stock_up:
        return max(cfg.shaving_reserve_soc, cfg.stock_up_target_soc)
    return cfg.shaving_reserve_soc


def _effective_targets(
    cfg: EngineConfig,
    state: EngineState,
    soft_w: float,
    target_w: float,
    hard_w: float,
) -> tuple[float, float, float]:
    """The limits in force, after the month-peak allowance.

    A demand charge is set by the month's *highest* quarter-hour, so once one window
    has already gone to 5.2 kW, holding the next one under 3.7 kW saves nothing —
    it only costs a slower charge for the rest of the month. With the allowance on
    (the default) the limits float up to whatever the month has already cost.

    But *up to* it, not *onto* it: aiming exactly at the record is a ratchet. The
    projection is an estimate and the house is not perfectly steerable, so a window
    aimed at 5.2 kW eventually lands at 5.25 — which becomes the new record, which
    raises the ceiling again, and the month creeps upward one overshoot at a time.
    So the target lands a buffer *below* the record and the hard limit sits on it:
    we steer for just under what is already bought, and cut before buying more.

    The soft line travels the same distance as the target rather than staying put.
    It means "start easing off", and easing off two kilowatts below a ceiling we
    have deliberately decided not to defend is not caution — it is discharging the
    home battery for a saving that cannot happen, since the charge is already
    booked. Keeping the gap between the two constant keeps the warning where it
    belongs: just under whatever is actually being enforced.
    """
    if not cfg.peak_follow_month or state.month_peak_w <= 0.0:
        return soft_w, target_w, hard_w
    buffer_w = max(0.0, cfg.peak_month_buffer_w)
    target = max(target_w, state.month_peak_w - buffer_w)
    return (
        soft_w + (target - target_w),
        target,
        max(hard_w, state.month_peak_w),
    )


def _month_key(start: datetime, tz: tzinfo | None) -> str:
    """The billed month of a window, on the *user's* calendar.

    A demand charge is billed per calendar month, and the calendar in question is
    the one on the wall — so this has to be resolved in local time. Doing it in UTC
    rolls the record at 01:00 or 02:00 local, which both files the first hour of a
    new month against the old one and lets the old month's peak keep raising the
    ceiling after it has stopped being billable.
    """
    local = start.astimezone(tz) if tz is not None else start
    return f"{local.year:04d}-{local.month:02d}"


def _local_hhmm(when: datetime, cfg: EngineConfig) -> str:
    """A wall-clock time for a reason string — the only place a user reads one."""
    return f"{when.astimezone(cfg.local_tz) if cfg.local_tz is not None else when:%H:%M}"


def _open_window(
    state: EngineState, start: datetime, *, degraded: bool, tz: tzinfo | None = None
) -> None:
    """Begin a quarter-hour, rolling the month record if this one starts a new one.

    The roll happens on *open*, not on close: the demand charge resets with the
    calendar, so the first quarter-hour of a month must already be measured against
    a clean record — otherwise the month-peak allowance would spend its first
    fifteen minutes still permitting last month's peak.
    """
    key = _month_key(start, tz)
    if key != state.month_key:
        state.prev_month_peak_w = state.month_peak_w if state.month_key else 0.0
        state.month_key = key
        state.month_peak_w = 0.0
        state.month_peak_at = None
    state.peak_window_start = start
    state.peak_window_wh = 0.0
    state.peak_window_degraded = degraded
    # A new window anchors on its own first register reading. ``peak_meter_last_*``
    # deliberately survives: it is what tells a jump from a climb across the boundary.
    state.peak_meter_anchor_kwh = None
    state.peak_meter_base_wh = 0.0
    state.peak_meter_anchor_clean = False
    state.peak_window_metered = False


def _close_window(state: EngineState) -> None:
    """Record the window that just ended: the history strip and the month record."""
    start = state.peak_window_start
    if start is None:
        return
    average = state.peak_window_wh * 3600.0 / PEAK_WINDOW_S
    state.peak_history.append((start, average))
    if len(state.peak_history) > _PEAK_HISTORY_LEN:
        del state.peak_history[:-_PEAK_HISTORY_LEN]

    # Only a window we could actually account for may set the record: a guessed
    # number must never become the one the card calls "your bill".
    if not state.peak_window_degraded and average > state.month_peak_w:
        state.month_peak_w = average
        state.month_peak_at = start


def _time_weighted_mean(
    samples: list[tuple[datetime, float]], now: datetime, cutoff: datetime
) -> float:
    """Zero-order-hold mean of ``(t, value)`` samples over ``[cutoff, now]``.

    A meter reports a *level*, not an event, so each sample counts for the time
    until the next one — which is what makes this correct under the coordinator's
    irregular, event-driven cadence.
    """
    if not samples:
        return 0.0
    total = 0.0
    span = 0.0
    for index, (stamp, value) in enumerate(samples):
        end = samples[index + 1][0] if index + 1 < len(samples) else now
        seconds = (end - max(stamp, cutoff)).total_seconds()
        if seconds <= 0.0:
            continue
        total += value * seconds
        span += seconds
    return total / span if span > 0.0 else samples[-1][1]


#: The fastest a household register can plausibly climb. A 3×63 A connection tops
#: out near 44 kW; anything steeper is a reader glitch or a meter swap, not usage.
_PEAK_METER_MAX_W: float = 100_000.0

#: Slack on that bound, for a reading that lands a few seconds late with the energy
#: of the seconds before it — and for one resolution step of a coarse register.
_PEAK_METER_SLACK_WH: float = 50.0


def _apply_meter(
    state: EngineState, now: datetime, kwh: float | None, *, grid_ok: bool
) -> None:
    """Settle the window's energy on the billing meter's import register.

    The tariff bills *energy*: a quarter-hour's import in kWh, times four. A
    cumulative register measures that directly — the climb since the window opened
    *is* the bill — where integrating a power reading only approximates it, from a
    different meter, with every gap and restart a guess.

    So the integral (:func:`update_peak_window`) keeps running underneath, and each
    time the register *moves* the accumulator is overwritten with the exact figure:
    the power-measured head before the anchor plus the register's climb since. Between
    two moves the integral carries the tail. That makes a stale or vanished register
    fail soft — it is simply the old behaviour again until the register next moves,
    and because the register is cumulative, that next move is exact for the whole
    stretch it missed.

    The anchor is the first reading in the window, so the seconds between the
    boundary and that reading are the integral's. A register that runs backwards or
    jumps faster than any household can draw is not believed *across* the
    discontinuity: it re-anchors there and carries on.
    """
    if kwh is None:
        return

    last_kwh, last_t = state.peak_meter_last_kwh, state.peak_meter_last_t
    if last_kwh is not None and kwh == last_kwh:
        # Unchanged. The integral carries the time until the register next ticks —
        # at low load a 1 Wh register can sit still for half a minute.
        return

    plausible = True
    if last_kwh is not None and last_t is not None:
        climb_wh = (kwh - last_kwh) * 1000.0
        seconds = max(0.0, (now - last_t).total_seconds())
        limit_wh = _PEAK_METER_MAX_W * seconds / 3600.0 + _PEAK_METER_SLACK_WH
        plausible = 0.0 <= climb_wh <= limit_wh
    # Stamped on *change*, not on every look: a reader that froze and comes back with
    # its catch-up climb must be measured against the time it was frozen.
    state.peak_meter_last_kwh = kwh
    state.peak_meter_last_t = now

    if state.peak_meter_anchor_kwh is None or not plausible:
        # First reading in this window, or a discontinuity we refuse to bill across.
        # Everything up to here stays as the integral measured it.
        state.peak_meter_anchor_kwh = kwh
        state.peak_meter_base_wh = state.peak_window_wh
        state.peak_meter_anchor_clean = not state.peak_window_degraded
        return

    state.peak_window_wh = (
        state.peak_meter_base_wh + (kwh - state.peak_meter_anchor_kwh) * 1000.0
    )
    state.peak_window_metered = True
    if state.peak_meter_anchor_clean and grid_ok:
        # The head was measured without a gap and everything since the anchor is the
        # register's own count, so whatever went unmeasured in between — a restart,
        # a dead grid sensor — is accounted for after all. The live reading has to be
        # back too: the projection of the rest of the window still rests on it.
        state.peak_window_degraded = False


def update_peak_window(
    now: datetime | None,
    grid_w: float | None,
    cfg: EngineConfig,
    state: EngineState,
    import_kwh: float | None = None,
) -> PeakWindow:
    """Advance the billing quarter-hour and return it.

    Deliberately takes primitives rather than a :class:`ChargerInputs`: the
    coordinator bails out *before* it can assemble a snapshot when the grid or
    charger reading is missing, and that is precisely the moment the window must
    keep advancing — a frozen accumulator would silently under-count the very
    quarter-hour a failed sensor is hiding.

    Runs whether or not peak protection is enabled: measuring writes nothing, and
    being able to watch your peaks for a month before switching anything on is the
    point.
    """
    soft_w, target_w, hard_w = _peak_thresholds(cfg)
    eff_soft, eff_target, eff_hard = _effective_targets(
        cfg, state, soft_w, target_w, hard_w
    )

    if now is None:
        # Stateless one-shot reasoning: no clock, so no window — the same convention
        # every other timer in this module follows.
        return PeakWindow(
            start=None, elapsed_s=0.0, remaining_s=PEAK_WINDOW_S, imported_wh=0.0,
            average_w=0.0, projected_w=0.0, allowed_w=0.0, rolling_w=0.0,
            soft_w=eff_soft, target_w=eff_target, hard_w=eff_hard,
            month_peak_w=state.month_peak_w, degraded=False,
        )

    start = _window_start(now)
    last_t = state.peak_sample_t
    held_w = max(0.0, state.peak_sample_w)

    if state.peak_window_start is None:
        # First sample ever, or a restart with nothing stored: whatever the elapsed
        # part of this quarter-hour drew, we didn't see it.
        _open_window(state, start, degraded=now > start, tz=cfg.local_tz)
        last_t = None
    elif last_t is None:
        # A window restored from disk, but without the sample clock that belongs to
        # it (a store written by an older build). Its own start is then the last
        # moment we can vouch for, and there is no reading to carry across the gap:
        # the accumulator already holds everything that was measured before the
        # restart, so carrying anything here would double-count it.
        last_t = state.peak_window_start
        held_w = 0.0

    if last_t is not None and now > last_t:
        # How far behind we are is the *older* of two clocks: the last sample and
        # the window still standing open. They come apart across a restart — the
        # sample clock can be seconds old while the open window is a day old — and
        # walking that apart window-by-window would mint a full quarter-hour of
        # history per step out of one live reading, each one looking complete enough
        # to set the month record.
        behind_t = min(last_t, state.peak_window_start or last_t)
        gap = (now - last_t).total_seconds()
        stale = gap > _PEAK_MAX_GAP_S
        if (now - behind_t).total_seconds() > PEAK_WINDOW_S * 2:
            # A long outage. Don't walk hundreds of windows to get here — close the
            # one we were in and start clean, degraded.
            _close_window(state)
            _open_window(state, start, degraded=True, tz=cfg.local_tz)
        else:
            # Carry the last reading across the gap rather than assuming zero:
            # under-counting is the one error that would let a real peak through.
            while state.peak_window_start is not None and state.peak_window_start != start:
                end = state.peak_window_start + timedelta(seconds=PEAK_WINDOW_S)
                covered = (end - max(last_t, state.peak_window_start)).total_seconds()
                state.peak_window_wh += held_w * max(0.0, covered) / 3600.0
                if stale:
                    state.peak_window_degraded = True
                _close_window(state)
                _open_window(state, end, degraded=stale, tz=cfg.local_tz)
                last_t = end
            covered = (now - max(last_t, start)).total_seconds()
            state.peak_window_wh += held_w * max(0.0, covered) / 3600.0
            if stale:
                state.peak_window_degraded = True

    if grid_w is None:
        # No reading this cycle. The held sample above still covers the time, but we
        # are guessing from here on, so the guard may only tighten.
        state.peak_window_degraded = True
    else:
        state.peak_sample_w = max(0.0, grid_w)  # export never lowers an import peak
        state.peak_seen_good = True
    state.peak_sample_t = now

    # After the integral has carried the time up to *now*, so an exact reading
    # replaces it rather than being added to it.
    _apply_meter(state, now, import_kwh, grid_ok=grid_w is not None)

    # The display-only trailing average, kept beside (never inside) the control path.
    state.peak_rolling.append((now, state.peak_sample_w))
    cutoff = now - timedelta(seconds=PEAK_WINDOW_S)
    while len(state.peak_rolling) > 2 and state.peak_rolling[1][0] <= cutoff:
        del state.peak_rolling[0]

    window_start = state.peak_window_start or start
    elapsed = max(0.0, (now - window_start).total_seconds())
    remaining = max(0.0, PEAK_WINDOW_S - elapsed)
    imported_wh = state.peak_window_wh
    live_w = state.peak_sample_w
    return PeakWindow(
        start=window_start,
        elapsed_s=elapsed,
        remaining_s=remaining,
        imported_wh=imported_wh,
        average_w=imported_wh * 3600.0 / elapsed if elapsed >= 1.0 else live_w,
        projected_w=(imported_wh * 3600.0 + live_w * remaining) / PEAK_WINDOW_S,
        allowed_w=max(
            0.0,
            (eff_target * PEAK_WINDOW_S - imported_wh * 3600.0)
            / max(remaining, _PEAK_MIN_REMAINING_S),
        ),
        rolling_w=_time_weighted_mean(state.peak_rolling, now, cutoff),
        soft_w=eff_soft,
        target_w=eff_target,
        hard_w=eff_hard,
        month_peak_w=state.month_peak_w,
        degraded=state.peak_window_degraded,
        metered=state.peak_window_metered,
    )


def resolve_peak_tier(
    now: datetime | None, window: PeakWindow, cfg: EngineConfig, state: EngineState
) -> str:
    """Which tier the projection puts us in — ``"off"``, ``"soft"`` or ``"hard"``.

    Same three-layer shape as the phase machine (hysteresis band, confirmation hold,
    dwell), but deliberately **asymmetric**: escalating to hard is a safety stop and
    happens on the spot, while every relaxation has to be confirmed *and* wait out
    the dwell. Tightening early costs a slower charge; relaxing early costs money.
    """
    if not cfg.peak_guard_enabled or window.start is None or now is None:
        state.peak_tier = "off"
        state.peak_tier_want = None
        state.peak_tier_want_since = None
        state.peak_cap_a = None
        state.peak_cap_at = None
        state.peak_share_engaged = False
        state.peak_share_calm_since = None
        return "off"

    # The limits *in force*, not the raw settings: with the month-peak allowance on,
    # the enforced target can sit well above the configured soft line, and comparing
    # against the raw one would engage the shave — draining the home battery — to
    # defend a level we have deliberately decided not to defend.
    soft = window.soft_w
    current = state.peak_tier if state.peak_tier in _PEAK_RANK else "off"
    projected = window.projected_w

    if projected >= window.hard_w:
        desired = "hard"
    elif current == "hard" and projected >= window.target_w:
        desired = "hard"  # hold hard until the projection is back under the target
    elif projected >= soft:
        desired = "soft"
    elif current != "off" and projected >= soft - _PEAK_HYSTERESIS_W:
        desired = "soft"  # hold soft through the hysteresis band
    else:
        desired = "off"

    if desired == current:
        state.peak_tier_want = None
        state.peak_tier_want_since = None
        return current

    tightening = _PEAK_RANK[desired] > _PEAK_RANK[current]

    if desired == "hard":
        # No confirmation, no dwell: by the time a 120 s window has confirmed, the
        # quarter-hour it was protecting is a third gone.
        state.peak_tier = "hard"
        state.peak_changed_at = now
        state.peak_tier_want = None
        state.peak_tier_want_since = None
        return "hard"

    hold_s = cfg.peak_confirm_s if tightening else cfg.peak_release_s
    if state.peak_tier_want != desired or state.peak_tier_want_since is None:
        state.peak_tier_want = desired
        state.peak_tier_want_since = now
    if (now - state.peak_tier_want_since).total_seconds() < hold_s:
        return current

    if not tightening:
        # A window we can't fully account for may tighten but never relax.
        if window.degraded:
            return current
        if (
            state.peak_changed_at is not None
            and (now - state.peak_changed_at).total_seconds() < cfg.peak_dwell_s
        ):
            return current

    state.peak_tier = desired
    state.peak_changed_at = now
    state.peak_tier_want = None
    state.peak_tier_want_since = None
    return desired


def _peak_current_cap(
    inp: ChargerInputs, cfg: EngineConfig, window: PeakWindow, phases: int
) -> float:
    """The highest whole-amp charging current that still fits the import budget.

    The car may have what the budget leaves *after* the rest of the house has taken
    its share — plus whatever it is already drawing from solar or the home battery,
    which never crossed the grid meter in the first place. That last term is why a
    car running on pure PV is not trimmed at all: stopping it would export the
    surplus, not reduce the import.

    Snapped down (and *not* through :func:`_quantize_current`, whose floor is the
    hardware minimum): a protective cap has to be able to say "less than 6 A", which
    is how the hard tier learns it must pause instead of trim.
    """
    split = compute_car_sources(compute_power_flow(inp))
    non_car_w = max(0.0, inp.grid_power_w - split.grid_w)
    budget_w = (
        max(0.0, window.allowed_w - non_car_w) + split.solar_w + split.battery_w
    )
    amps = _power_to_current(budget_w, max(1, phases), inp.voltage_v)
    return max(0.0, math.floor(min(amps, cfg.max_current_a) + _AMP_EPSILON))


def peak_charge_ceiling_w(
    inp: ChargerInputs, cfg: EngineConfig, window: PeakWindow
) -> float | None:
    """The car's steady share of the peak target — what *planning* should assume.

    Deliberately distinct from :func:`_peak_current_cap`, which sizes the live trim
    against the remaining quarter-hour budget: that number swings through the window
    by design, and a departure plan rebuilt on it would rebook its slots every cycle.
    This is the calm version — the target in force, minus the rest of the house — so
    the plan can work out *how many hours* it needs while the budget still corrects
    the amps inside each one.

    Solar the car is already taking is credited — it never crossed the grid meter, so
    it is genuine head-room. Home-battery discharge is **not**, and that difference is
    the whole reason this is a separate function from the trim. Two reasons: a grid
    strategy deliberately *holds* the battery off the car, so planning to spend it
    plans for something the same cycle forbids; and crediting it is circular — charging
    harder makes the battery cover more, which raises the ceiling, which charges harder
    still. Left in, that loop walks the phase contactor back and forth for hours.

    ``None`` means "no ceiling" — peak protection off, or no clock — and every caller
    then behaves exactly as it did before.
    """
    if not cfg.peak_guard_enabled or window.start is None:
        return None
    split = compute_car_sources(compute_power_flow(inp))
    non_car_w = max(0.0, inp.grid_power_w - split.grid_w)
    return max(0.0, window.target_w - non_car_w) + split.solar_w


def _ceiling_amps(ceiling_w: float, phases: int, inp: ChargerInputs) -> float:
    """Whole amps that fit under ``ceiling_w``, never below the hardware minimum.

    Floored, not rounded: a ceiling is a ceiling. It does not fall below 6 A because
    a request under the pilot signal's floor is not a smaller charge, it is a stopped
    one — deciding *that* is the hard tier's job, not the planner's.
    """
    fits = math.floor(
        _power_to_current(max(0.0, ceiling_w), max(1, phases), inp.voltage_v)
        + _AMP_EPSILON
    )
    return max(HARDWARE_MIN_CURRENT_A, float(fits))


def _plan_phases(
    inp: ChargerInputs, cfg: EngineConfig, state: EngineState, ceiling_w: float | None
) -> int:
    """The phase count a grid charge would pick — **pure**, for sizing plan slots.

    Mirrors :func:`_resolve_phases`' thresholds without touching its timers, because
    the plan is computed before we know which strategy wins and must not spend the
    contactor's confirmation window on a charge that never happens. The winning
    branch makes the real, state-carrying call.
    """
    if not cfg.auto_phase or cfg.max_phases < 3:
        return max(1, inp.phases)
    if ceiling_w is None:
        return cfg.max_phases
    current = state.phases if state.phases in (1, 3) else 1
    up = _current_to_power(_floor_current(cfg), 3, inp.voltage_v) + cfg.phase_up_margin_w
    down = _current_to_power(cfg.max_current_a, 1, inp.voltage_v)
    if current == 1:
        return 3 if ceiling_w >= up else 1
    return 1 if ceiling_w < down else 3


def _rate_limit_cap(
    cap_a: float, now: datetime | None, cfg: EngineConfig, state: EngineState
) -> float:
    """Let the cap fall at once but rise only after the dwell.

    Trimming is safety and is never delayed. Relaxing is comfort, and letting it
    follow every upward wobble of the budget — a kettle switching off, a cloud
    passing — is exactly how the amps would start flapping.
    """
    previous = state.peak_cap_a
    if now is None or previous is None or cap_a <= previous:
        state.peak_cap_a = cap_a
        state.peak_cap_at = now
        return cap_a
    if (
        state.peak_cap_at is not None
        and (now - state.peak_cap_at).total_seconds() < cfg.peak_dwell_s
    ):
        return previous
    state.peak_cap_a = cap_a
    state.peak_cap_at = now
    return cap_a


def _rate_limit_request(
    ceiling_a: float,
    phases: int,
    now: datetime | None,
    cfg: EngineConfig,
    state: EngineState,
) -> float:
    """The request's ceiling, by :func:`_rate_limit_cap`'s rule: down at once, up after the dwell.

    :func:`peak_charge_ceiling_w` subtracts the house load *as it is this second*,
    so a load that cycles — a heat-pump compressor or an oven element pulsing a few
    hundred watts every few seconds — moves the request by an amp or two every
    cycle, and the charger is re-written each time (seen live: 11↔13 A every 5 s for
    ten minutes). The ceiling function itself stays pure because the planner sizes
    slots with it. The limiting happens here, where the request is made.

    Every dip re-arms the dwell, so the request rises only once the load has
    stayed low for a full dwell. A phase change starts afresh, because amps on one
    phase count say nothing about amps on three.
    """
    previous = state.peak_request_a
    if (
        now is None
        or previous is None
        or state.peak_request_phases != phases
        or ceiling_a <= previous
        or state.peak_request_at is None
        or (now - state.peak_request_at).total_seconds() >= cfg.peak_dwell_s
    ):
        state.peak_request_a = ceiling_a
        state.peak_request_at = now
        state.peak_request_phases = phases
        return ceiling_a
    return previous


def _attach_window(decision: Decision, window: PeakWindow) -> None:
    """Surface the measurement on the decision — always, enabled or not."""
    decision.peak_window_avg_w = window.average_w
    decision.peak_projected_w = window.projected_w
    decision.peak_allowed_w = window.allowed_w
    decision.peak_rolling_w = window.rolling_w
    decision.peak_degraded = window.degraded
    decision.peak_metered = window.metered
    decision.month_peak_w = window.month_peak_w
    decision.peak_soft_w = window.soft_w
    decision.peak_target_w = window.target_w
    decision.peak_hard_w = window.hard_w
    if window.start is not None:
        decision.peak_window_ends = window.start + timedelta(seconds=PEAK_WINDOW_S)


def _peak_status_reason(
    inp: ChargerInputs | None,
    cfg: EngineConfig,
    window: PeakWindow,
    tier: str,
    capped_a: float | None,
    *,
    paused: bool,
) -> tuple[str, str, dict[str, str]]:
    """The plain-language answer to "what is peak protection doing right now?"."""
    if not cfg.peak_guard_enabled:
        return _reason("peak_off")

    # Raw settings here, deliberately: this pair is only used to explain that the
    # month-peak allowance has *lifted* the limits off what was configured.
    raw_soft, raw_target, _raw_hard = _peak_thresholds(cfg)
    projected = f"{window.projected_w / 1000.0:.2f}"
    until = (
        _local_hhmm(window.start + timedelta(seconds=PEAK_WINDOW_S), cfg)
        if window.start is not None
        else "the next quarter-hour"
    )

    if window.degraded:
        return _reason("peak_degraded", until=until)
    if paused:
        return _reason("peak_pause", projected=projected, until=until)
    if tier in ("soft", "hard"):
        floor = _peak_soc_floor(cfg)
        if inp is not None and inp.battery_soc is not None and inp.battery_soc <= floor:
            return _reason(
                "peak_battery_empty", projected=projected, soc=f"{floor:.0f}"
            )
        target_kw = f"{window.target_w / 1000.0:.2f}"
        if capped_a is not None:
            return _reason(
                "peak_shaving_car",
                projected=projected,
                amps=f"{capped_a:.0f}",
                target=target_kw,
            )
        if inp is not None and inp.car_connected:
            # A car is plugged in and the budget isn't binding on it — we are
            # watching, not intervening, and the reason should not overclaim.
            return _reason("peak_holding", projected=projected, target=target_kw)
        # No car to ease back: the home battery is the only lever there is.
        return _reason("peak_shaving_house", projected=projected, target=target_kw)
    # Above what you configured, but the month has already bought more than that —
    # so we are *not* shaving, and saying why is the whole point of this line.
    if window.month_peak_w > raw_target and window.projected_w >= raw_soft:
        return _reason(
            "peak_month_headroom",
            month=f"{window.month_peak_w / 1000.0:.2f}",
            target=f"{window.target_w / 1000.0:.2f}",
        )
    if window.projected_w >= window.soft_w:
        # Past the line but the tier hasn't engaged yet: the crossing is still being
        # confirmed. "Close to" would be false — it is already past it.
        return _reason(
            "peak_confirming", projected=projected, soft=f"{window.soft_w / 1000.0:.2f}"
        )
    if window.projected_w >= window.soft_w - _PEAK_HYSTERESIS_W:
        return _reason(
            "peak_watch", projected=projected, soft=f"{window.soft_w / 1000.0:.2f}"
        )
    return _reason("peak_ok", projected=projected)


#: The setpoint is written in steps this size, rounded *down* — the battery then
#: covers the odd few watts more, never the grid. Following a lumpy load watt by
#: watt would be a write every cycle for nothing.
_PEAK_SETPOINT_STEP_W: float = 100.0

#: …and only moved when the new value is at least this far from the last one. The
#: remaining budget drifts every cycle as the quarter-hour fills; chasing that drift
#: in 100 W steps was a write every ten seconds for a few watts of difference.
_PEAK_SETPOINT_MIN_MOVE_W: float = 300.0

#: How long the battery's remaining energy should be able to carry the present
#: excess before the grid starts taking a larger share. See :func:`_house_share`.
#:
#: Swept, not picked (``tools/sim/heavy_load.py sweep``, the measured sauna on a
#: 30.5 kWh pack). Worst quarter-hour starting at 65 / 55 / 45 % SoC:
#: no pacing 3.63 / 6.02 / 8.25 kW, 15 min 3.63 / 5.49 / 7.17, 30 min 4.12 / 5.21 /
#: 7.10, 60 min 4.35 / 5.79 / 7.63. Longer horizons lean on the grid too early on an
#: evening the battery would have carried; 15 min is the longest that never does,
#: and still takes a kilowatt off the evenings that run short.
_PEAK_ENERGY_HORIZON_S: float = 900.0


@dataclass(slots=True)
class _HouseShare:
    """How a heavy load is split between the grid and the home battery this cycle."""

    engaged: bool
    share_w: float  # what the grid may carry for the house + car
    house_net_w: float  # house load net of PV, car excluded (negative = surplus)
    car_room_w: float  # what is left of the share for the car
    setpoint_w: float  # the ESS grid setpoint to write while engaged
    paced: bool  # the share was raised because the battery wouldn't last


def _house_share(
    inp: ChargerInputs, cfg: EngineConfig, state: EngineState, window: PeakWindow
) -> _HouseShare | None:
    """Split a heavy load: the grid carries up to the budget, the battery the rest.

    On an ESS with the setpoint at its resting ~50 W the battery covers *everything*
    above it — so a sauna is carried entirely from storage until the pack reaches its
    reserve, and then lands on the grid all at once. That spends stored energy on the
    part of the load the grid could have carried for free (anything up to the target
    costs nothing extra this month) and then breaches anyway, at full load.

    So once the house alone would take more than the budget, the setpoint *follows the
    load up to the budget*: ``min(share, house + whatever the car may have)``. The
    grid carries the share, the battery only the excess. Following the load rather
    than sitting at the share matters — a setpoint above the load makes the ESS charge
    the battery from the grid, which is exactly what a thermostat switching off would
    otherwise trigger.

    The share is normally the quarter-hour budget. With the battery's capacity known
    it rises when the stored energy can't carry the present excess for
    ``_PEAK_ENERGY_HORIZON_S`` more: rather than shave fully until the pack is empty
    and then hand the grid the whole load, the grid takes progressively more as the
    energy runs down, so the evening ends with a modest peak instead of a cliff.

    Engagement is about the *house*: the car is the steerable load, so a car pushing
    the total over the budget is answered by trimming the car, not by the battery.
    Engaging is immediate; releasing waits for the house to stay under the share for
    ``peak_release_s``, and never happens in a degraded window.

    ``None`` when the battery's power isn't mapped: without it the house load can't be
    told apart from what the battery is already covering, and the tier ladder carries
    on alone.
    """
    if inp.battery_power_w is None or window.start is None or inp.now is None:
        state.peak_share_engaged = False
        state.peak_share_calm_since = None
        return None

    now = inp.now
    # What the grid and battery jointly serve, net of PV. Invariant to the setpoint:
    # whatever we command only moves watts between those two terms.
    net_load_w = inp.grid_power_w - inp.battery_power_w
    car_w = max(0.0, inp.car_actual_power_w) if inp.car_connected else 0.0
    house_net_w = net_load_w - car_w

    share_w = max(0.0, min(window.allowed_w, window.target_w))
    paced = False
    if cfg.battery_capacity_kwh > 0.0 and inp.battery_soc is not None:
        usable_wh = (
            max(0.0, inp.battery_soc - _peak_soc_floor(cfg))
            / 100.0 * cfg.battery_capacity_kwh * 1000.0
        )
        sustainable_w = usable_wh * 3600.0 / _PEAK_ENERGY_HORIZON_S
        if house_net_w - sustainable_w > share_w:
            share_w = house_net_w - sustainable_w
            paced = True

    if house_net_w > share_w:
        state.peak_share_engaged = True
        state.peak_share_calm_since = None
    elif state.peak_share_engaged:
        if house_net_w >= share_w - _PEAK_HYSTERESIS_W or window.degraded:
            state.peak_share_calm_since = None
        elif state.peak_share_calm_since is None:
            state.peak_share_calm_since = now
        elif (now - state.peak_share_calm_since).total_seconds() >= cfg.peak_release_s:
            state.peak_share_engaged = False
            state.peak_share_calm_since = None

    car_room_w = max(0.0, share_w - house_net_w)
    load_w = house_net_w + min(car_w, car_room_w)
    setpoint_w = max(0.0, min(share_w, load_w))
    setpoint_w = math.floor(setpoint_w / _PEAK_SETPOINT_STEP_W) * _PEAK_SETPOINT_STEP_W
    previous = state.peak_share_setpoint_w
    if not state.peak_share_engaged:
        previous = None
    elif previous is not None:
        at_floor = (
            inp.battery_soc is not None and inp.battery_soc <= _peak_soc_floor(cfg)
        )
        # Keeping the previous value is only ever allowed at or below the load: a
        # setpoint above it makes the ESS charge the battery from the grid.
        if previous <= max(0.0, load_w) and (
            # The battery can't discharge, so the setpoint changes nothing…
            at_floor
            # …or the change is small drift.
            or abs(setpoint_w - previous) < _PEAK_SETPOINT_MIN_MOVE_W
        ):
            setpoint_w = previous
    state.peak_share_setpoint_w = setpoint_w if state.peak_share_engaged else None
    return _HouseShare(
        engaged=state.peak_share_engaged,
        share_w=share_w,
        house_net_w=house_net_w,
        car_room_w=car_room_w,
        setpoint_w=setpoint_w,
        paced=paced,
    )


def _apply_tier_levers(
    decision: Decision,
    inp: ChargerInputs,
    cfg: EngineConfig,
    state: EngineState,
    window: PeakWindow,
    tier: str,
) -> tuple[float | None, bool]:
    """The tier ladder's levers — used when the battery's power isn't mapped.

    Without a battery power reading the house load can't be told apart from what
    the battery already covers, so :func:`_house_share` can't run and the levers
    follow the projection's tier instead. Returns ``(capped_a, paused)``.
    """
    engaged = tier in ("soft", "hard")

    # --- House levers ---------------------------------------------------------------
    # The minimum-SoC number is *owned* while this is on: it sits at the shaving
    # reserve normally, so ordinary house loads can't quietly drain the battery flat,
    # and drops to the floor while shaving. That drop is what actually releases the
    # headroom — and it works with no car anywhere near the house.
    decision.battery_min_soc = (
        _peak_soc_floor(cfg) if engaged else _resting_reserve_soc(cfg)
    )
    decision.grid_setpoint_w = 0.0 if tier == "hard" else cfg.grid_setpoint_w
    if engaged:
        # Shaving means the battery has to be allowed to discharge, whatever the car
        # brain — or the user's Auto/Hold/Free control — would otherwise have said.
        decision.hold_battery = False
        decision.hold_source = "peak"

    # --- The wallbox cap ------------------------------------------------------------
    capped_a: float | None = None
    paused = False
    if not engaged or not inp.car_connected:
        state.peak_cap_a = None
        state.peak_cap_at = None
    else:
        phases = max(1, decision.target_phases or inp.phases)
        budget_a = _rate_limit_cap(
            _peak_current_cap(inp, cfg, window, phases), inp.now, cfg, state
        )
        if tier == "hard" and budget_a < HARDWARE_MIN_CURRENT_A:
            # Not even the hardware minimum fits. Stop — and note this reaches a
            # charger the brain is otherwise not driving (Smart control off, Manual
            # passive), because a demand charge, once bought, cannot be un-bought.
            # A car is connected (the branch above guarantees it), so this is a
            # pause we are actively holding, whatever the charger was doing before.
            paused = True
            decision.control = True
            decision.should_charge = False
            decision.target_current_a = 0.0
        elif decision.control and decision.should_charge:
            # Soft never pauses; it eases off, down to the hardware minimum.
            limit_a = max(HARDWARE_MIN_CURRENT_A, min(budget_a, cfg.max_current_a))
            if limit_a < decision.target_current_a:
                decision.target_current_a = limit_a
                capped_a = limit_a
    return capped_a, paused


def _apply_house_share(
    decision: Decision,
    inp: ChargerInputs,
    cfg: EngineConfig,
    state: EngineState,
    window: PeakWindow,
    tier: str,
    share: _HouseShare,
) -> tuple[float | None, bool]:
    """The levers when the house share is known. Returns ``(capped_a, paused)``.

    Engaged, the house levers implement the split and the car gets only what the
    share leaves after the house — the battery is never counted as room for it,
    because the stored energy belongs to the loads that can't be moved. A car that
    doesn't fit at 6 A is paused, and resumes as soon as the room is back.

    Neither "let the battery carry the car's 6 A" nor "hold the pause" survived the
    simulation (``tools/sim/heavy_load.py``, ``peak15.py``). Carrying 6 A — 4.1 kW on
    three phases — spent the sauna's energy on the car and breached at 4.46 kW where
    pausing holds 3.63 kW. Holding the pause to the end of the quarter-hour cost the
    car 83 kWh over a winter fortnight: on heat-pump nights each blip sat out a full
    window. Without either the car kept 95 % of its energy; the price is that it
    starts and stops with a sauna thermostat, which was accepted.

    Not engaged, the house is left to the ESS as usual and the tier only trims the
    car, as before. Notably the tier no longer releases the hold or drops the
    minimum SoC: that is what made it fight itself — the battery took the whole load,
    the projection collapsed, the tier released, and the import came straight back.
    """
    if share.engaged:
        decision.battery_min_soc = _peak_soc_floor(cfg)
        decision.grid_setpoint_w = share.setpoint_w
        decision.hold_battery = False
        decision.hold_source = "peak"
    else:
        decision.battery_min_soc = _resting_reserve_soc(cfg)
        decision.grid_setpoint_w = cfg.grid_setpoint_w

    if not inp.car_connected or inp.now is None or window.start is None:
        state.peak_cap_a = None
        state.peak_cap_at = None
        return None, False

    now = inp.now
    phases = max(1, decision.target_phases or inp.phases)
    driving = decision.control and decision.should_charge

    room_a: float | None = None
    if share.engaged:
        room_a = math.floor(
            _power_to_current(share.car_room_w, phases, inp.voltage_v) + _AMP_EPSILON
        )
    elif tier in ("soft", "hard"):
        room_a = _peak_current_cap(inp, cfg, window, phases)

    too_small = room_a is not None and room_a < HARDWARE_MIN_CURRENT_A
    # Pausing a charger the brain isn't driving is reserved for the hard tier, as
    # before: a demand charge, once bought, cannot be un-bought.
    must_pause = too_small and (driving or tier == "hard")
    if must_pause:
        decision.control = True
        decision.should_charge = False
        decision.target_current_a = 0.0
        state.peak_cap_a = None
        state.peak_cap_at = None
        return None, True

    if not driving or room_a is None:
        state.peak_cap_a = None
        state.peak_cap_at = None
        return None, False

    limit_a = _rate_limit_cap(min(room_a, cfg.max_current_a), now, cfg, state)
    limit_a = max(HARDWARE_MIN_CURRENT_A, limit_a)
    if limit_a < decision.target_current_a:
        decision.target_current_a = limit_a
        return limit_a, False
    return None, False


def _share_status_reason(
    inp: ChargerInputs,
    cfg: EngineConfig,
    window: PeakWindow,
    tier: str,
    share: _HouseShare,
    capped_a: float | None,
    *,
    paused: bool,
) -> tuple[str, str, dict[str, str]]:
    """The status line when the house share is known."""
    if not share.engaged:
        text, key, params = _peak_status_reason(
            inp, cfg, window, tier, capped_a, paused=paused
        )
        if key == "peak_shaving_house":
            # Not engaged means the battery is *not* being asked for anything extra;
            # the tier is only watching. Say so rather than overclaim.
            return _reason(
                "peak_holding",
                projected=f"{window.projected_w / 1000.0:.2f}",
                target=f"{window.target_w / 1000.0:.2f}",
            )
        return text, key, params

    projected = f"{window.projected_w / 1000.0:.2f}"
    until = _local_hhmm(window.start + timedelta(seconds=PEAK_WINDOW_S), cfg)
    if window.degraded:
        return _reason("peak_degraded", until=until)
    floor = _peak_soc_floor(cfg)
    if inp.battery_soc is not None and inp.battery_soc <= floor:
        return _reason("peak_battery_empty", projected=projected, soc=f"{floor:.0f}")
    if paused:
        return _reason("peak_pause", projected=projected, until=until)
    grid_kw = f"{share.setpoint_w / 1000.0:.1f}"
    if share.paced:
        soc = f"{inp.battery_soc:.0f}" if inp.battery_soc is not None else "?"
        return _reason("peak_share_paced", grid=grid_kw, soc=soc)
    target_kw = f"{window.target_w / 1000.0:.2f}"
    if capped_a is not None:
        return _reason(
            "peak_shaving_car", projected=projected, amps=f"{capped_a:.0f}",
            target=target_kw,
        )
    load_w = share.house_net_w + (
        max(0.0, inp.car_actual_power_w) if inp.car_connected else 0.0
    )
    return _reason(
        "peak_share",
        grid=grid_kw,
        battery=f"{max(0.0, load_w - share.setpoint_w) / 1000.0:.1f}",
        target=target_kw,
    )


def apply_peak_guard(
    decision: Decision,
    inp: ChargerInputs,
    cfg: EngineConfig,
    state: EngineState,
    window: PeakWindow,
    tier: str,
) -> Decision:
    """Apply the capacity-tariff ceiling on top of whatever the arbiter decided.

    A ceiling, not a proposal: the arbiter takes the *highest* bid, so a strategy
    wanting to charge less has no way to win. Sitting after it instead means this
    covers every branch uniformly — Manual, Fast, ride-out, idle, and the no-car
    branch, which is the one that matters most. A sauna sets the monthly peak
    whether or not a car is plugged in, and the levers for that are the home
    battery's, not the wallbox's.

    Disabled, this is a single early return that changes nothing: ``house_control``
    mirroring ``control`` is exactly the old rule, under which the hold switch was
    written precisely when the brain was driving the charger.
    """
    _attach_window(decision, window)
    decision.peak_tier = tier

    if not cfg.peak_guard_enabled or window.start is None or not state.peak_seen_good:
        # Off, clockless, or no trustworthy reading has arrived yet. Never shave
        # blind on a cold start — measure, report, write nothing.
        decision.house_control = decision.control
        decision.peak_tier = "off" if not cfg.peak_guard_enabled else tier
        decision.peak_reason, decision.peak_reason_key, decision.peak_reason_params = (
            _peak_status_reason(inp, cfg, window, tier, None, paused=False)
        )
        return decision

    # Peak protection answers to its own switch, not to Smart control: a demand
    # charge is money whether or not the brain is currently driving the wallbox.
    decision.house_control = True
    share = _house_share(inp, cfg, state, window)
    if share is None:
        capped_a, paused = _apply_tier_levers(decision, inp, cfg, state, window, tier)
        decision.peak_reason, decision.peak_reason_key, decision.peak_reason_params = (
            _peak_status_reason(inp, cfg, window, tier, capped_a, paused=paused)
        )
    else:
        capped_a, paused = _apply_house_share(
            decision, inp, cfg, state, window, tier, share
        )
        decision.peak_reason, decision.peak_reason_key, decision.peak_reason_params = (
            _share_status_reason(inp, cfg, window, tier, share, capped_a, paused=paused)
        )

    # The Status sensor's reason has to survive being overruled here, and the two
    # kinds of override need different answers.
    #
    # A pause contradicts it outright: the arbiter's line says "Fast charging at
    # 16 A" while the car stands at 0 A, and no amount of context makes that true.
    # The peak line saying the right thing beside it is a second opinion, not a
    # substitute for the first one being correct — so the pause takes the reason.
    if paused:
        decision.reason = decision.peak_reason
        decision.reason_key = decision.peak_reason_key
        decision.reason_params = decision.peak_reason_params
    elif capped_a is not None and "amps" in decision.reason_params:
        # A trim does not contradict it — the car really is fast-charging, just at
        # fewer amps — so the arbiter keeps the explanation and only the number is
        # corrected. Quoting the current we asked for instead of the one we wrote
        # is the whole falsehood, and the peak line explains the difference.
        decision.reason, decision.reason_key, decision.reason_params = _reason(
            decision.reason_key, **{**decision.reason_params, "amps": f"{capped_a:.0f}"}
        )

    return decision


def _grid_charge_target(cfg: EngineConfig, inp: ChargerInputs) -> float:
    """How deep to fill the home battery from the grid, given tomorrow's forecast.

    The forecast's job is not "is it winter" — it is *don't fill the battery from
    the grid the night before a bright day*, where the sun would have done it for
    free and the paid-for charge only leaves the PV nowhere to go. With no forecast
    mapped we assume the pessimistic case, which is the safe one.
    """
    if inp.pv_forecast_kwh is None or inp.pv_forecast_kwh < cfg.pv_forecast_low_kwh:
        return cfg.dark_day_target_soc
    return cfg.bright_day_target_soc


#: Grid charging stops at its target and does not resume until the SoC has fallen
#: this far below it. Without the band the setpoint flips between "import hard" and
#: "import nothing" every cycle once the target is reached, and the pack pays a
#: round-trip loss on each flip. Five cheap hours a day hides it; a battery kept
#: ready around the clock does not.
#:
#: Two percent, and the size is measured rather than picked. Against a 100 % target —
#: where the pack pins and chatters worst — a 15-day simulation gave: no band 864 kWh
#: imported, 2 % → 776 kWh, 5 % → 771 kWh, 10 % → 769 kWh. So 2 % already captures 88
#: of the 95 kWh available, and it is the widest band that costs *nothing* in peak
#: performance: at 2 % the worst quarter-hour and the breach count are identical to
#: no band at all, while 5 % and 10 % start giving both away. Wider is not safer here
#: — it just means arriving at the evening with a flatter battery.
_GRID_CHARGE_RESUME_BAND_PCT: float = 2.0


def _grid_charge_goal(cfg: EngineConfig, inp: ChargerInputs) -> tuple[float, str]:
    """How full to fill the home battery right now, and why — cheapest hours first.

    Three reasons to buy, in descending order of urgency:

    * **Stocking up** for an evening the user has told us about: fill to the stock-up
      target at any price.
    * **Readiness**, while peak protection is on: below ``peak_ready_soc`` the pack is
      too flat to defend the limit, and an unshaved quarter-hour costs more than the
      difference between a cheap kilowatt-hour and an ordinary one.
    * **A cheap hour**, the original reason: fill to the bright/dark target.

    Returns ``(0.0, "")`` when none of them applies, which is the common case and
    means "don't touch the setpoint".
    """
    ready_soc = cfg.peak_ready_soc if cfg.peak_guard_enabled else 0.0
    if cfg.stock_up:
        return max(cfg.stock_up_target_soc, ready_soc), "stock_up"
    if inp.price_now is not None and inp.price_now <= cfg.cheap_price:
        cheap_target = _grid_charge_target(cfg, inp)
        if cheap_target >= ready_soc:
            key = (
                "grid_charge_bright"
                if cheap_target == cfg.bright_day_target_soc
                and inp.pv_forecast_kwh is not None
                and cfg.bright_day_target_soc != cfg.dark_day_target_soc
                else "grid_charge_dark"
            )
            return cheap_target, key
        return ready_soc, "ready"
    return ready_soc, "ready"


def apply_grid_charge(
    decision: Decision,
    inp: ChargerInputs,
    cfg: EngineConfig,
    state: EngineState,
    window: PeakWindow,
    tier: str,
) -> Decision:
    """Buy energy into the home battery — cheaply when we can, anyway when we must.

    Three reasons to import, resolved by :func:`_grid_charge_goal`: a cheap hour, a
    battery too flat to defend the peak limit, or an evening the user has told us to
    stock up for. Only the first is about price; the other two are about *having*
    stored energy, which in December is the scarcer thing.

    On an ESS the grid setpoint *is* total grid import, so what we command here is
    exactly the quantity a capacity tariff bills — which is the whole trick. Importing
    hard in a cheap hour is precisely how a demand charge gets bought by accident;
    capping the command by the live quarter-hour budget turns it into a steady draw
    that collects the cheap energy without the peak.

    Strictly last in line: peak protection outranks it absolutely.
    """
    if not cfg.grid_charge_enabled:
        state.grid_charging = False
        return decision

    # Whichever feature is on owns the setpoint, so it always has a resting value to
    # return to — otherwise a cheap hour would end with the setpoint left up.
    decision.house_control = True
    if decision.grid_setpoint_w is None:
        decision.grid_setpoint_w = cfg.grid_setpoint_w
    if cfg.stock_up and decision.battery_min_soc is None:
        # Peak protection normally owns the minimum-SoC number, but it is switched
        # off here — and stocking up without the hold is just an expensive way to
        # heat the afternoon. Borrow it (the coordinator hands it back on release).
        decision.battery_min_soc = _resting_reserve_soc(cfg)

    if tier != "off" or state.peak_share_engaged:
        # Peak protection owns the setpoint while it is shaving — by tier, or by
        # splitting a heavy load between grid and battery.
        state.grid_charging = False
        return decision

    target_soc, why = _grid_charge_goal(cfg, inp)
    soc = inp.battery_soc
    if soc is None or target_soc <= 0.0:
        state.grid_charging = False
        return decision

    # Hysteresis: run up to the target, then stay off until the SoC has fallen a band
    # below it. Testing ``soc >= target`` on both edges makes the setpoint chatter
    # once the target is reached — see ``_GRID_CHARGE_RESUME_BAND_PCT``.
    stop_at = (
        target_soc if state.grid_charging
        else target_soc - _GRID_CHARGE_RESUME_BAND_PCT
    )
    if soc >= stop_at:
        state.grid_charging = False
        decision.peak_reason, decision.peak_reason_key, decision.peak_reason_params = (
            _reason(
                "grid_charge_stocked" if why == "stock_up" else "grid_charge_full",
                soc=f"{soc:.0f}",
            )
        )
        return decision

    # What the grid must serve regardless of the battery (house + car − PV): the
    # setpoint is a *total*, so the charge rate we want sits on top of it, and the
    # ceiling then clamps the sum. If the house alone is already at the ceiling the
    # battery simply doesn't charge — which is the correct answer, not a failure.
    soft, _target, _hard = _peak_thresholds(cfg)
    net_load_w = max(0.0, inp.grid_power_w - (inp.battery_power_w or 0.0))
    ceiling_w = min(soft, window.allowed_w) if window.start is not None else soft
    setpoint_w = max(
        0.0, min(net_load_w + cfg.cheap_charge_power_w, ceiling_w)
    )

    decision.grid_setpoint_w = setpoint_w
    decision.grid_charging = True
    state.grid_charging = True
    if why == "stock_up":
        params = dict(power=f"{setpoint_w:.0f}", target=f"{target_soc:.0f}")
        key = "grid_charge_stock_up"
    elif why == "ready":
        params = dict(
            soc=f"{soc:.0f}", power=f"{setpoint_w:.0f}", target=f"{target_soc:.0f}"
        )
        key = "grid_charge_ready"
    else:
        params = dict(
            price=f"{inp.price_now:.3f}",
            power=f"{setpoint_w:.0f}",
            target=f"{target_soc:.0f}",
        )
        key = why
    decision.peak_reason, decision.peak_reason_key, decision.peak_reason_params = (
        _reason(key, **params)
    )
    return decision


def attach_peak_status(
    decision: Decision,
    cfg: EngineConfig,
    state: EngineState,
    window: PeakWindow,
    tier: str,
) -> Decision:
    """Surface the peak measurement on a decision built outside :func:`decide`.

    The coordinator bails out before it can assemble a snapshot when the grid or
    charger reading is missing. The quarter-hour still has to be measured and shown,
    so that path calls :func:`update_peak_window` and then this.
    """
    _attach_window(decision, window)
    decision.peak_tier = tier
    decision.peak_reason, decision.peak_reason_key, decision.peak_reason_params = (
        _peak_status_reason(None, cfg, window, tier, None, paused=False)
    )
    return decision


# --- Strategies + arbiter -----------------------------------------------------------

@dataclass(slots=True)
class _Proposal:
    """One strategy's bid for this cycle, compared by deliverable power."""

    kind: str  # "cheap" | "plan" | "urgent" | "fast" | "floor" | "solar"
    source: str  # "grid" | "solar"
    power_w: float
    params: dict[str, str] = field(default_factory=dict)


def _collect_proposals(
    inp: ChargerInputs,
    cfg: EngineConfig,
    avail: Availability,
    plan: _Plan | None,
    *,
    grid_phases: int,
    floor_phases: int,
) -> list[_Proposal]:
    """All proposals from the mode's enabled strategies, grid strategies first.

    Ordering matters: the arbiter keeps the *first* of equal-power proposals, so
    listing grid strategies ahead of solar keeps the battery-hold engaged when a
    grid strategy ties with the surplus.

    Solar bids its *commitment* power: which strategy runs the session is a
    decision, not a knob. The current it then charges at follows the tracking
    signal (see :func:`_decide`).
    """
    proposals: list[_Proposal] = []
    max_grid_w = _current_to_power(cfg.max_current_a, grid_phases, inp.voltage_v)

    if cfg.mode is ChargingMode.FAST:
        proposals.append(_Proposal("fast", "grid", max_grid_w))

    if cfg.mode is ChargingMode.SMART:
        if inp.price_now is not None and inp.price_now <= cfg.cheap_price:
            proposals.append(
                _Proposal(
                    "cheap",
                    "grid",
                    max_grid_w,
                    {
                        "price": f"{inp.price_now:.3f}",
                        "threshold": f"{cfg.cheap_price:.3f}",
                    },
                )
            )
        now = _deadline_now(plan, inp)
        if now is not None:
            key, params = now
            proposals.append(
                _Proposal("urgent" if key == "deadline_urgent" else "plan",
                          "grid", max_grid_w, params)
            )

    if cfg.mode is ChargingMode.SOLAR_MIN:
        floor_w = _current_to_power(_floor_current(cfg), floor_phases, inp.voltage_v)
        proposals.append(_Proposal("floor", "grid", floor_w))

    if cfg.mode in _SOLAR_MODES:
        proposals.append(
            _Proposal("solar", "solar", min(avail.commit_w, max_grid_w))
        )

    return proposals


def _idle_reason(
    inp: ChargerInputs, cfg: EngineConfig, avail: Availability, needed_w: float
) -> tuple[str, str, dict[str, str]]:
    """Why the charger is (staying) off — the most informative answer first.

    Quotes the commitment signal, because that is the number the start gate is
    actually waiting on.
    """
    remaining = _plan_remaining_kwh(inp, cfg)
    if remaining is not None and remaining <= 0:
        return _reason(
            "target_reached",
            delivered=f"{inp.session_delivered_kwh or 0.0:.1f}",
        )
    if (
        cfg.mode in _SOLAR_MODES
        and inp.battery_soc is not None
        and inp.battery_soc < cfg.battery_reserve_soc
    ):
        return _reason(
            "waiting_battery_reserve",
            soc=f"{inp.battery_soc:.0f}",
            reserve=f"{cfg.battery_reserve_soc:.0f}",
        )
    if remaining is not None and remaining > 0:
        return _reason("plan_waiting")
    return _reason(
        "waiting_surplus",
        surplus=f"{avail.commit_w:.0f}",
        needed=f"{needed_w:.0f}",
    )


def _decide_manual(
    inp: ChargerInputs, cfg: EngineConfig, state: EngineState
) -> Decision:
    """Manual mode: the user is the brain.

    Start/stop, charging current and phase count come straight from the manual
    controls. The battery policy still applies in spirit: once the requested
    power exceeds the available surplus the charge is grid-assisted, so the
    battery is held (and the guard trims as the fallback) — the same single
    concept as everywhere else: deliberate grid power never drains the battery.

    Note this *actively drives* the charger (``control=True``): manual no longer
    means hands-off. To fully release the charger to the go-e app, turn Smart
    control off (handled by the master gate above).
    """
    phases = cfg.manual_phases if cfg.manual_phases in (1, 3) else inp.phases

    # Just switched into Manual and nothing touched yet: hands fully off. The
    # coordinator skips applying this decision entirely (no writes, no releases),
    # so the charger keeps doing whatever it was. ``control=False`` keeps that
    # intent explicit; the user takes over by using a manual control.
    if cfg.manual_passive:
        reason, rkey, rparams = _reason("manual_passive")
        return Decision(
            control=False,
            target_phases=phases,
            reason=reason,
            reason_key=rkey,
            reason_params=rparams,
        )

    if not inp.car_connected:
        reason, rkey, rparams = _reason("no_car")
        return Decision(
            control=True,
            should_charge=False,
            target_phases=phases,
            write_phases=True,
            reason=reason,
            reason_key=rkey,
            reason_params=rparams,
        )

    if not cfg.manual_charge:
        reason, rkey, rparams = _reason("manual_paused")
        return Decision(
            control=True,
            should_charge=False,
            target_phases=phases,
            write_phases=True,
            reason=reason,
            reason_key=rkey,
            reason_params=rparams,
        )

    # Charging: grid-assisted (requested power above the surplus) holds the home
    # battery; the guard trims as the fallback when no hold switch is mapped. The
    # Auto/Hold/Free override wins over the auto grid-assist test (the finalizer
    # sets the same hold on the switch); "free" also disables the guard trim.
    avail = compute_availability(inp, cfg, state)
    requested_w = _current_to_power(cfg.manual_current_a, phases, inp.voltage_v)
    if cfg.battery_hold_mode == "hold":
        hold = True
    elif cfg.battery_hold_mode == "free":
        hold = False
    else:
        # Driving the hold switch is a commitment, so it follows the calm signal.
        hold = requested_w > avail.commit_w + _MANUAL_GRID_MARGIN_W
    current, guarded = _battery_guard_current(
        cfg.manual_current_a, phases, inp, cfg, hold=hold
    )
    if guarded:
        reason, rkey, rparams = _reason("manual_charging_guarded", amps=f"{current:.0f}")
    else:
        reason, rkey, rparams = _reason("manual_charging", amps=f"{current:.0f}")
    return Decision(
        control=True,
        should_charge=True,
        target_current_a=current,
        target_phases=phases,
        write_phases=True,
        surplus_w=avail.power_w,
        hold_battery=hold,
        reason=reason,
        reason_key=rkey,
        reason_params=rparams,
    )


def _reset_session_state(state: EngineState) -> None:
    """Forget the start/stop machine when no car is connected."""
    state.charging = False
    state.active_source = None
    state.ride_out_since = None
    state.surplus_ok_since = None
    state.start_override = False


# --- The decision ---------------------------------------------------------------

def decide(
    inp: ChargerInputs, cfg: EngineConfig, state: EngineState | None = None
) -> Decision:
    """Return the charging decision for the current cycle.

    ``state`` carries smoothing/dwell memory between cycles; a fresh one is used
    when omitted (e.g. one-shot reasoning or tests that don't exercise timers).

    The departure plan is computed once here so its booked windows can be both
    used by the arbiter *and* surfaced on the decision (the card's plan strip),
    and a final pass applies the home-battery override and the countdown
    deadlines that were previously private to :class:`EngineState`.

    Peak protection runs either side of that: the billing quarter-hour is measured
    *before* every gate (it is billed whether or not the brain may act, and the
    sensors stay live either way), and the ceiling is applied *after* the arbiter
    and the finalizer, so it can override the home-battery decision they just made.
    """
    if state is None:
        state = EngineState()

    window = update_peak_window(
        inp.now, inp.grid_power_w, cfg, state, inp.grid_import_kwh
    )
    tier = resolve_peak_tier(inp.now, window, cfg, state)
    # What the peak paths read: the car's own ramp booked to the car, not the house.
    peak_inp = _settled_inputs(inp, cfg, state)

    # The ceiling only means anything where a grid strategy could actually run, and
    # computing it elsewhere would hand Manual and the hands-off gates a number they
    # must not act on.
    ceiling_w: float | None = None
    if (
        cfg.smart_enabled
        and cfg.mode is not ChargingMode.MANUAL
        and inp.car_connected
    ):
        ceiling_w = peak_charge_ceiling_w(peak_inp, cfg, window)

    plan: _Plan | None = None
    if cfg.smart_enabled and cfg.mode is ChargingMode.SMART and inp.car_connected:
        plan = _compute_plan(
            inp, cfg, _plan_phases(inp, cfg, state, ceiling_w), ceiling_w
        )

    decision = _decide(inp, cfg, state, plan, ceiling_w)
    decision = _finalize(decision, inp, cfg, state, plan)
    decision = apply_peak_guard(decision, peak_inp, cfg, state, window, tier)
    decision = apply_grid_charge(decision, inp, cfg, state, window, tier)
    _note_car_raise(decision, inp, state)
    return decision


def _settled_inputs(
    inp: ChargerInputs, cfg: EngineConfig, state: EngineState
) -> ChargerInputs:
    """The inputs the peak paths read, with the car's own ramp booked to the car.

    Everything peak protection sizes — the request ceiling, the cap, the house share —
    takes the house load as *grid − car*, from two meters that don't report together.
    Right after a raise the grid meter already carries the ramping car while the
    charger still reports the old power, so for a sample or two the difference shows
    up as house load: +1.7 kW on a 6 → 13 A raise, seen live. The cap reacts at
    once, as it should to a real load, the raise is undone, and the dwell holds it
    there. Every raise cancelled itself and the car sat at 6 A with room for 13.

    So for :data:`CAR_RAMP_SETTLE_S` after a raise, the car counts as drawing at
    least what it was just asked for. A real load that shows up in that time is
    still seen in full, because the car's share is then right. The one cost: a car
    that doesn't follow (full, or limited by its own charger) leaves the house
    under-counted by the raise for at most the settle time — ~7 Wh at 1.7 kW.

    Peak protection only. Solar tracking already smooths the derived surplus, and
    with the guard off nothing changes at all.
    """
    if (
        not cfg.peak_guard_enabled
        or not inp.car_connected
        or inp.now is None
        or state.car_raised_at is None
        or state.car_expected_w is None
        or (inp.now - state.car_raised_at).total_seconds() >= CAR_RAMP_SETTLE_S
        or inp.car_actual_power_w >= state.car_expected_w
    ):
        return inp
    return replace(inp, car_actual_power_w=state.car_expected_w)


def _note_car_raise(decision: Decision, inp: ChargerInputs, state: EngineState) -> None:
    """Remember what the car was just asked to draw — and when, if that was more."""
    if not (decision.control and decision.should_charge and inp.car_connected):
        state.car_expected_w = None
        state.car_raised_at = None
        return
    phases = max(1, decision.target_phases or inp.phases)
    want_w = _current_to_power(decision.target_current_a, phases, inp.voltage_v)
    if state.car_expected_w is None or want_w > state.car_expected_w + _AMP_EPSILON:
        state.car_raised_at = inp.now
    state.car_expected_w = want_w


def _finalize(
    decision: Decision,
    inp: ChargerInputs,
    cfg: EngineConfig,
    state: EngineState,
    plan: _Plan | None,
) -> Decision:
    """Apply the home-battery override + surface the plan and countdown deadlines.

    The Auto/Hold/Free control only overrides while the brain is actually driving
    the charger (``control=True``); a hands-off decision leaves the battery alone.
    """
    if decision.control:
        if cfg.battery_hold_mode == "hold":
            decision.hold_battery = True
            decision.hold_source = "hold"
        elif cfg.battery_hold_mode == "free":
            decision.hold_battery = False
            decision.hold_source = "free"
        else:
            decision.hold_source = "auto"
    _release_hold_for_idle_car(decision, inp, state)

    decision.plan = _plan_window_starts(inp, plan)

    # Countdown deadlines the card ticks down (all None unless the relevant timer
    # is armed this cycle). Resume only makes sense while we are *not* charging.
    if not decision.should_charge and state.surplus_ok_since is not None:
        decision.resume_not_before = state.surplus_ok_since + timedelta(
            seconds=cfg.start_confirm_s
        )
    if state.ride_out_since is not None:
        decision.pause_not_before = state.ride_out_since + timedelta(
            seconds=cfg.stop_ride_out_s
        )
    _stamp_phase_change(decision, inp, state)
    if state.phase_changed_at is not None:
        decision.phase_locked_until = state.phase_changed_at + timedelta(
            seconds=cfg.phase_dwell_s
        )
    return decision


def _release_hold_for_idle_car(
    decision: Decision, inp: ChargerInputs, state: EngineState
) -> None:
    """Hand the home battery back when the car has stopped taking power.

    The grid strategies hold the battery for as long as they *want* to charge, and
    a full car that stays plugged in never stops them wanting to: Full power keeps
    asking for 16 A into a car that takes nothing, and the hold — there to keep
    the battery out of the car — ends up keeping it out of the house all evening.
    So once the charger has been allowed to charge for a while and the car still
    isn't drawing, the Auto hold lets go. The moment the car draws again (a top-up,
    preconditioning) the timer clears and the hold is back on the next cycle.

    Only the Auto hold: an explicit *Hold* means always, and is the user's to lift.
    """
    if (
        not decision.control
        or not decision.should_charge
        or inp.car_actual_power_w >= _CAR_DRAWING_MIN_W
    ):
        state.car_idle_since = None
        return
    if inp.now is None:
        return
    if state.car_idle_since is None:
        state.car_idle_since = inp.now
    if (inp.now - state.car_idle_since).total_seconds() < _CAR_IDLE_RELEASE_S:
        return
    if decision.hold_source == "auto" and decision.hold_battery:
        decision.hold_battery = False
        decision.reason, decision.reason_key, decision.reason_params = _reason(
            "car_not_drawing"
        )


def _stamp_phase_change(
    decision: Decision, inp: ChargerInputs, state: EngineState
) -> None:
    """Record that the contactor moved, whichever strategy moved it.

    ``_resolve_phases`` stamps its own switches, but it is only consulted on the
    solar path: a cheap-grid hour simply takes ``max_phases``, and a departure plan
    or the minimum floor pick their own count. Those switches reached the charger
    without the dwell timer ever hearing about them, so the next solar decision
    believed the contactor had been sitting still — and the card's phase-lock
    countdown showed nothing while the contactor was in fact throwing.

    Stamped off our own intent rather than the measurement: ``inp.phases`` changes
    source between charging and idle (measured currents vs. the ``psm`` mode), and
    a car that charges single-phase on a three-phase supply would make that flip
    look like a contactor move it never was.
    """
    if not decision.control:
        # Not driving the charger, so nothing of ours moves it; forget the target
        # rather than compare against a stale one when control comes back.
        state.phases_targeted = None
        return
    target = decision.target_phases
    if target not in (1, 3):
        return
    if state.phases_targeted is not None and state.phases_targeted != target:
        state.phase_changed_at = inp.now
    state.phases_targeted = target


def _decide(
    inp: ChargerInputs,
    cfg: EngineConfig,
    state: EngineState,
    plan: _Plan | None,
    ceiling_w: float | None = None,
) -> Decision:
    """The core arbiter — see :func:`decide` for the public wrapper."""
    # --- Master gates ------------------------------------------------------------
    if not cfg.smart_enabled:
        reason, rkey, rparams = _reason("smart_disabled")
        return Decision(
            control=False, reason=reason, reason_key=rkey, reason_params=rparams
        )
    if cfg.mode is ChargingMode.MANUAL:
        return _decide_manual(inp, cfg, state)
    if not inp.car_connected:
        _reset_session_state(state)
        reason, rkey, rparams = _reason("no_car")
        return Decision(
            control=True,
            should_charge=False,
            target_phases=max(1, inp.phases),
            reason=reason,
            reason_key=rkey,
            reason_params=rparams,
        )

    # --- Collect proposals ---------------------------------------------------------
    avail = compute_availability(inp, cfg, state)
    grid_phases = _grid_phases(inp, cfg, state)
    floor_phases = 1 if cfg.auto_phase else max(1, inp.phases)
    min_solar_w = _current_to_power(_floor_current(cfg), floor_phases, inp.voltage_v)

    proposals = _collect_proposals(
        inp, cfg, avail, plan, grid_phases=grid_phases, floor_phases=floor_phases
    )

    winner: _Proposal | None = None
    for proposal in proposals:
        if winner is None or proposal.power_w > winner.power_w:
            winner = proposal

    # A grid strategy always delivers at least the minimum; the surplus counts
    # only once it can sustain the minimum current on its cheapest phase config.
    active = winner is not None and (
        winner.source == "grid" or winner.power_w >= min_solar_w
    )

    # --- Start-confirmation window (solar starts only) -----------------------------
    # On the commitment signal, so a flickering surplus doesn't keep restarting
    # the window — and doesn't start the charge on a bright patch either.
    if avail.commit_w >= min_solar_w:
        if state.surplus_ok_since is None:
            state.surplus_ok_since = inp.now
    else:
        state.surplus_ok_since = None
    # "Start now": the user has seen the surplus and doesn't want to wait out the
    # confirmation. It skips the *waiting* only — the surplus still has to be
    # there, so this can never start a charge the sun can't carry. Consumed on
    # the spot, so it applies to this cycle and no later one.
    start_now, state.start_override = state.start_override, False
    solar_confirmed = start_now or inp.now is None or (
        state.surplus_ok_since is not None
        and (inp.now - state.surplus_ok_since).total_seconds() >= cfg.start_confirm_s
    )

    # --- Nothing demands charging: ride out a solar dip, then stop -----------------
    if not active:
        if (
            state.charging
            and state.active_source == "solar"
            and inp.now is not None
        ):
            if state.ride_out_since is None:
                state.ride_out_since = inp.now
            if (
                inp.now - state.ride_out_since
            ).total_seconds() < cfg.stop_ride_out_s:
                # Ride out at whatever the *live* surplus supports, not blindly at
                # the minimum: if the dip is already recovering the amps recover
                # with it, while the decision to stop keeps waiting on the calm
                # signal. A real collapse still lands on the minimum.
                phases = max(1, inp.phases)
                amps = _quantize_current(
                    _clamp(
                        _power_to_current(avail.power_w, phases, inp.voltage_v),
                        _floor_current(cfg),
                        cfg.max_current_a,
                    ),
                    cfg,
                    up=avail.generous,
                )
                reason, rkey, rparams = _reason(
                    "surplus_ride_out", amps=f"{amps:.0f}"
                )
                return Decision(
                    control=True,
                    should_charge=True,
                    target_current_a=amps,
                    target_phases=phases,
                    surplus_w=avail.power_w,
                    reason=reason,
                    reason_key=rkey,
                    reason_params=rparams,
                )
        state.charging = False
        state.active_source = None
        state.ride_out_since = None
        reason, rkey, rparams = _idle_reason(inp, cfg, avail, min_solar_w)
        return Decision(
            control=True,
            should_charge=False,
            target_phases=max(1, inp.phases),
            surplus_w=avail.commit_w,
            reason=reason,
            reason_key=rkey,
            reason_params=rparams,
        )

    assert winner is not None  # narrowed by `active`
    state.ride_out_since = None

    # --- Solar starts wait for the confirmation window -----------------------------
    if not state.charging and winner.source == "solar" and not solar_confirmed:
        reason, rkey, rparams = _reason(
            "surplus_confirm", surplus=f"{avail.commit_w:.0f}"
        )
        return Decision(
            control=True,
            should_charge=False,
            target_phases=max(1, inp.phases),
            surplus_w=avail.commit_w,
            reason=reason,
            reason_key=rkey,
            reason_params=rparams,
        )

    state.charging = True
    state.active_source = winner.source

    # --- Build the charging decision ------------------------------------------------
    if winner.source == "grid":
        if winner.kind == "floor":
            phases = _resolve_phases(avail.commit_w, inp, cfg, state)
            base_amps = _floor_current(cfg)
        elif ceiling_w is not None:
            # Under a peak ceiling the phase count is part of the answer, not a
            # setting: 6 A × 3φ is 4.14 kW, so a low ceiling cannot fit three phases
            # at all while 6 A × 1φ (1.38 kW) fits easily. Routed through the same
            # resolver as solar so the contactor keeps its hysteresis, confirmation
            # and dwell — this is the one state-carrying phase call this cycle.
            phases = _resolve_phases(ceiling_w, inp, cfg, state)
            base_amps = cfg.max_current_a
        else:
            phases = grid_phases
            base_amps = cfg.max_current_a
        # Peak protection shapes the *request*, not only the correction after it.
        # Asking for 16 A under a 2 kW ceiling just to be trimmed to 6 A wastes a
        # booked slot and quotes the user a current we never meant to write. The
        # departure guarantee is the deliberate exception: it has already decided the
        # peak is worth buying, so it asks for everything and says so.
        ceiling_a = (
            _rate_limit_request(
                _ceiling_amps(ceiling_w, phases, inp), phases, inp.now, cfg, state
            )
            if ceiling_w is not None
            else None
        )
        ceiling_bound = ceiling_a is not None and ceiling_a < base_amps
        if ceiling_bound and winner.kind != "urgent":
            base_amps = ceiling_a
        # "free" lets the home battery feed the car, so the fallback guard must
        # not trim; the finalizer then leaves the hold switch off. Auto/Hold both
        # protect the battery during a deliberate grid charge.
        hold = cfg.battery_hold_mode != "free"
        amps, guarded = _battery_guard_current(
            base_amps, phases, inp, cfg, hold=hold
        )
        params = dict(winner.params)
        if winner.kind == "cheap":
            key = "cheap_grid_guarded" if guarded else "cheap_grid"
            if guarded:
                params["amps"] = f"{amps:.0f}"
        elif winner.kind == "plan":
            key = "deadline_plan_guarded" if guarded else "deadline_plan"
            if guarded:
                params["amps"] = f"{amps:.0f}"
        elif winner.kind == "urgent":
            # Overriding the ceiling is a decision the user has to be told about, not
            # a detail: this is the one path that knowingly buys a demand charge.
            key = "deadline_urgent_peak" if ceiling_bound else "deadline_urgent"
        elif winner.kind == "fast":
            # Say when the peak budget, not the charger's maximum, set the number —
            # "Fast charging at 15 A" with a 16 A maximum otherwise looks like a fault.
            key = "fast_peak" if ceiling_bound and not guarded else "fast"
            params["amps"] = f"{amps:.0f}"
        else:  # floor
            # What the floor asks for beyond the surplus, and who actually pays
            # for it — see :func:`_topup_source_key`.
            gap_w = max(
                0.0, _current_to_power(amps, phases, inp.voltage_v) - avail.power_w
            )
            params["amps"] = f"{amps:.0f}"
            params["surplus"] = f"{avail.power_w:.0f}"
            key = _topup_source_key(inp, gap_w, hold=hold)
            if key != "solar_min_covered":
                params["gap"] = f"{gap_w:.0f}"
        reason, rkey, rparams = _reason(key, **params)
        return Decision(
            control=True,
            should_charge=True,
            target_current_a=amps,
            target_phases=phases,
            surplus_w=avail.power_w,
            hold_battery=hold,
            reason=reason,
            reason_key=rkey,
            reason_params=rparams,
        )

    # Solar winner: the current follows the responsive tracking signal, the phase
    # count the calm one; the battery buffers whatever is left in between.
    phases = _resolve_phases(avail.commit_w, inp, cfg, state)
    amps = _quantize_current(
        _clamp(
            _power_to_current(avail.power_w, phases, inp.voltage_v),
            _floor_current(cfg),
            cfg.max_current_a,
        ),
        cfg,
        up=avail.generous,
    )
    # What the charge asks for beyond the surplus — the home battery covers it.
    gap_w = _current_to_power(amps, phases, inp.voltage_v) - avail.power_w
    params = {"surplus": f"{avail.power_w:.0f}", "amps": f"{amps:.0f}"}
    if avail.eased:
        key = "solar_surplus_eased"
    elif avail.generous and gap_w >= 1.0:
        key = "solar_surplus_battery_topup"
        params["gap"] = f"{gap_w:.0f}"
    elif phases != inp.phases:
        key = "solar_surplus_phase"
        params["phases"] = str(phases)
    else:
        key = "solar_surplus"
    reason, rkey, rparams = _reason(key, **params)
    return Decision(
        control=True,
        should_charge=True,
        target_current_a=amps,
        target_phases=phases,
        surplus_w=avail.power_w,
        reason=reason,
        reason_key=rkey,
        reason_params=rparams,
    )
