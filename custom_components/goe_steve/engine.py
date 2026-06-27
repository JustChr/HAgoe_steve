"""Pure regulation engine for go-e + SteVe Smart Charging.

This module is intentionally free of any Home Assistant imports so that the
decision logic can be reasoned about and unit-tested in isolation (see
``tests/test_engine.py``). The coordinator feeds it a snapshot of the world
(:class:`ChargerInputs`), the current settings (:class:`EngineConfig`) and a
small mutable :class:`EngineState` (dwell/hysteresis memory carried across
cycles) and gets back a single :class:`Decision` describing what the charger
should do and, crucially, *why* — the human-readable ``reason`` is surfaced in
the UI.

Phase 2 scope (this file): price-aware modes (PV+price / Price-optimized /
Combined), the Share and Assist battery policies, automatic 1↔3-phase switching
with hysteresis + a dwell timer, and a minimum on/off dwell to stop the charger
flapping. Everything time-dependent receives ``now`` explicitly so the logic
stays deterministic and testable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum


class ChargingMode(StrEnum):
    """User-selectable charging strategy."""

    OFF = "off"
    PV_ONLY = "pv_only"
    PV_MINIMUM = "pv_minimum"
    PV_PRICE = "pv_price"  # solar, plus full power while grid price is cheap
    PRICE = "price"  # cheapest-hours charging to a target by a deadline
    COMBINED = "combined"  # surplus + cheap-grid + deadline guarantee
    FAST = "fast"


#: Modes offered to the user and implemented by :func:`decide`.
SUPPORTED_MODES: tuple[ChargingMode, ...] = (
    ChargingMode.OFF,
    ChargingMode.PV_ONLY,
    ChargingMode.PV_MINIMUM,
    ChargingMode.PV_PRICE,
    ChargingMode.PRICE,
    ChargingMode.COMBINED,
    ChargingMode.FAST,
)

#: Retained for the original Phase 1 callers/tests.
PHASE1_MODES: tuple[ChargingMode, ...] = (
    ChargingMode.OFF,
    ChargingMode.PV_ONLY,
    ChargingMode.PV_MINIMUM,
    ChargingMode.FAST,
)


class BatteryPolicy(StrEnum):
    """How home-battery energy may participate in car charging."""

    PROTECT = "protect"  # battery first; never reduced/discharged for the car
    SHARE = "share"  # car may take power that would otherwise charge the battery
    ASSIST = "assist"  # battery may discharge into the car, down to a floor SoC


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
    pv_power_w: float | None = None
    # Home battery. ``battery_power_w``: + charging, - discharging.
    battery_soc: float | None = None
    battery_power_w: float | None = None
    # Price environment.
    price_now: float | None = None
    price_forecast: list[PriceSlot] | None = None
    # Wall-clock time for deadline/dwell reasoning (None disables time logic).
    now: datetime | None = None


@dataclass(slots=True)
class EngineConfig:
    """Current settings — mostly runtime-adjustable via number/select entities."""

    mode: ChargingMode = ChargingMode.OFF
    battery_policy: BatteryPolicy = BatteryPolicy.PROTECT
    smart_enabled: bool = True
    min_current_a: float = 6.0
    max_current_a: float = 16.0
    battery_reserve_soc: float = 80.0
    min_grid_floor_w: float = 1400.0
    # Phase 2 tunables.
    cheap_price: float = 0.15  # ≤ this (currency/kWh) counts as "cheap grid"
    battery_floor_soc: float = 20.0  # Assist: stop discharging the battery here
    target_energy_kwh: float = 0.0  # 0 disables deadline planning
    departure: datetime | None = None  # deadline for Price / Combined modes
    # Manual mode (mode == OFF): the user is the brain. Start/stop, current and
    # phase count come straight from these; the battery policy still applies.
    manual_charge: bool = False
    manual_current_a: float = 16.0
    manual_phases: int = 3
    # Phase switching.
    auto_phase: bool = False
    max_phases: int = 3
    phase_dwell_s: float = 300.0  # min time between phase switches
    # Minimum on/off dwell to stop the relay flapping.
    min_on_dwell_s: float = 120.0
    min_off_dwell_s: float = 120.0


@dataclass(slots=True)
class EngineState:
    """Mutable memory carried across cycles by the coordinator.

    Holds only what the dwell/hysteresis logic needs to remember; it is reset on
    restart, which simply means timers start fresh.
    """

    phases: int | None = None
    phase_changed_at: datetime | None = None
    charging: bool | None = None
    charge_changed_at: datetime | None = None


@dataclass(slots=True)
class Decision:
    """The engine's output for one cycle.

    ``control`` is False when the brain should keep its hands off entirely
    (Off mode, smart control disabled, stale data) — the coordinator then writes
    nothing, leaving manual/app control untouched.
    """

    control: bool
    should_charge: bool = False
    target_current_a: float = 0.0
    target_phases: int = 3
    # Force the phase entity to be written this cycle even when auto-phase is off
    # (Manual mode picks phases explicitly). Smart fixed-phase modes leave it False
    # so they never touch a phase switch the user controls.
    write_phases: bool = False
    surplus_w: float = 0.0
    reason: str = ""
    # Structured form of ``reason`` so the Lovelace card can localize it: a stable
    # catalog key plus its pre-formatted string params. ``reason`` itself stays the
    # English rendering (logs, tests, non-card consumers). See ``_reason``.
    reason_key: str = ""
    reason_params: dict[str, str] = field(default_factory=dict)
    # True while we are deliberately grid-charging and want the home battery
    # blocked from discharging into the car (driven onto a user-mapped hold
    # switch by the coordinator). See :func:`_hold_battery`.
    hold_battery: bool = False


# Ignore tiny home-battery discharge (sensor noise / standby) before the guard
# below starts trimming grid-charge current.
_BATTERY_DRAIN_TOLERANCE_W: float = 100.0


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


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _power_to_current(power_w: float, phases: int, voltage_v: float) -> float:
    return power_w / (phases * voltage_v)


def _current_to_power(current_a: float, phases: int, voltage_v: float) -> float:
    return current_a * phases * voltage_v


def compute_surplus(inp: ChargerInputs, cfg: EngineConfig) -> float:
    """Power (W) available to the car under the active battery policy.

    Base headroom is grid export plus the car's own current draw (the car's draw
    suppresses export, so it must be added back).

    * ``PROTECT`` — while the home battery is below its reserve SoC the car gets
      nothing, so the battery fills first. Above the reserve the car may take
      genuine solar surplus, but any battery *discharge* is subtracted so the car
      never runs on the battery (e.g. solar has dropped but the inverter is
      covering the car from the battery).
    * ``SHARE`` — power that is currently charging the home battery is reclaimed
      for the car; the battery yields but is never actively drained, so discharge
      is likewise subtracted.
    * ``ASSIST`` — Share behaviour, and while the battery is above its floor SoC
      it may actively back the car: availability is lifted to the configured
      maximum so charging never stalls on solar alone (the battery and the grid
      floor make up the difference). Set the floor to bound how far it drains.
    """
    export_w = max(0.0, -inp.grid_power_w)
    surplus = export_w + max(0.0, inp.car_actual_power_w)

    policy = cfg.battery_policy

    # PROTECT below reserve: hold the car entirely so the battery fills first.
    if (
        inp.battery_soc is not None
        and policy is BatteryPolicy.PROTECT
        and inp.battery_soc < cfg.battery_reserve_soc
    ):
        return 0.0

    if inp.battery_power_w is not None and policy in (
        BatteryPolicy.SHARE,
        BatteryPolicy.ASSIST,
    ):
        # Reclaim whatever is currently flowing *into* the home battery.
        surplus += max(0.0, inp.battery_power_w)

    if inp.battery_power_w is not None and policy in (
        BatteryPolicy.PROTECT,
        BatteryPolicy.SHARE,
    ):
        # Never let the car run on the battery: discount any discharge so the
        # surplus reflects real PV excess only. Without this, the car's own draw
        # (added back above) masks the fact that the battery — not the sun — is
        # supplying it, and PROTECT/SHARE would silently drain the battery.
        surplus -= max(0.0, -inp.battery_power_w)

    if policy is BatteryPolicy.ASSIST and inp.battery_soc is not None:
        if inp.battery_soc > cfg.battery_floor_soc:
            assist_ceiling = _current_to_power(
                cfg.max_current_a, max(1, inp.phases), inp.voltage_v
            )
            surplus = max(surplus, assist_ceiling)

    return max(0.0, surplus)


def _hold_battery(inp: ChargerInputs, cfg: EngineConfig) -> bool:
    """Whether to protect the home battery from powering the car right now.

    The home battery system regulates the grid to ~0, so during a grid charge it
    will discharge into the car *by default* unless we stop it. When this returns
    True the coordinator turns on a user-mapped hold switch (block discharge / raise
    the grid setpoint) so the grid supplies the car instead; and as a fallback when
    no hold switch is mapped, :func:`_battery_guard_current` trims the car's current.
    When it returns False the battery is *deliberately* allowed to help the car
    (and the guard leaves the current alone) — this is fine, and exactly what the
    Share/Assist policies are for.

    The same battery policy that governs solar-surplus sharing decides it, so users
    learn one concept:

    * ``PROTECT`` — the battery never powers the car: always hold.
    * ``SHARE``   — hold once at/below the reserve SoC; above it there is plenty to
      spare, so let the battery help.
    * ``ASSIST``  — hold once at/below the floor SoC; above it the battery is meant
      to assist the car.

    With SoC unknown, PROTECT/SHARE still hold (the safe default — never silently
    drain); ASSIST can't prove it is above its floor, so it does not hold.
    """
    policy = cfg.battery_policy
    if policy is BatteryPolicy.PROTECT:
        return True
    if inp.battery_soc is None:
        return policy is BatteryPolicy.SHARE
    if policy is BatteryPolicy.SHARE:
        return inp.battery_soc <= cfg.battery_reserve_soc
    return inp.battery_soc <= cfg.battery_floor_soc  # ASSIST


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
    unless something stops it. The real fix is the hold switch (see
    :func:`_hold_battery`), which blocks discharge so the grid supplies the car.
    This is the *fallback* for when no hold switch is mapped (or it has no effect):
    we lower the car's current by whatever the battery is discharging. With the grid
    pinned at 0 this does **not** shift the load onto the grid — it simply throttles
    the car back down to the genuine solar surplus (never below the EV's minimum
    current), which is the best we can do without a hold switch.

    Driven by the *same* policy decision as the hold switch (``hold``): we trim only
    when the policy wants the battery protected. When the policy is deliberately
    letting the battery help the car (Share above reserve, Assist above floor), we
    leave the current alone so it can. Re-evaluated each cycle, so it converges as
    the inverter responds.

    Returns ``(current, guarded)`` where ``guarded`` flags that we trimmed.
    """
    if not hold or inp.battery_power_w is None:
        return full_current_a, False
    discharge_w = max(0.0, -inp.battery_power_w)
    if discharge_w <= _BATTERY_DRAIN_TOLERANCE_W:
        return full_current_a, False
    trim_a = _power_to_current(discharge_w, max(1, phases), inp.voltage_v)
    guarded_a = max(cfg.min_current_a, full_current_a - trim_a)
    return guarded_a, guarded_a < full_current_a


def _battery_held(inp: ChargerInputs, cfg: EngineConfig) -> bool:
    """True when PROTECT is parking the car until the home battery fills."""
    return (
        inp.battery_soc is not None
        and cfg.battery_policy is BatteryPolicy.PROTECT
        and inp.battery_soc < cfg.battery_reserve_soc
    )


# --- Price helpers --------------------------------------------------------------

def _slot_minutes(forecast: list[PriceSlot], index: int) -> float:
    """Length of slot ``index`` in minutes (falls back to 60 at the tail)."""
    if index + 1 < len(forecast):
        delta = forecast[index + 1].start - forecast[index].start
        minutes = delta.total_seconds() / 60.0
        if minutes > 0:
            return minutes
    return 60.0


def _is_cheap_window(
    inp: ChargerInputs, cfg: EngineConfig
) -> tuple[bool, dict[str, str]]:
    """Should we grid-charge *now* to hit the target energy by departure?

    Greedy cheapest-hours plan, recomputed every cycle so it self-corrects:
    take the upcoming slots before the deadline, sort by price, and keep the
    cheapest ones until their charging capacity covers ``target_energy_kwh``.
    Charge if the current slot is in that cheapest set.

    On a match returns the ``deadline_plan`` reason params (``price``/``target``);
    otherwise an empty dict.
    """
    if (
        not cfg.target_energy_kwh
        or cfg.departure is None
        or inp.now is None
        or not inp.price_forecast
    ):
        return False, {}

    if inp.now >= cfg.departure:
        return False, {}

    upcoming = [
        (i, s)
        for i, s in enumerate(inp.price_forecast)
        if s.start < cfg.departure
        and s.start + timedelta(minutes=_slot_minutes(inp.price_forecast, i)) > inp.now
    ]
    if not upcoming:
        return False, {}

    max_power_kw = (
        _current_to_power(cfg.max_current_a, cfg.max_phases, inp.voltage_v) / 1000.0
    )
    if max_power_kw <= 0:
        return False, {}

    chosen: set[int] = set()
    energy = 0.0
    for i, slot in sorted(upcoming, key=lambda pair: pair[1].price):
        if energy >= cfg.target_energy_kwh:
            break
        chosen.add(i)
        energy += max_power_kw * (_slot_minutes(inp.price_forecast, i) / 60.0)

    # The slot covering "now" is the upcoming slot with the latest start ≤ now.
    current_index = max(
        (i for i, s in upcoming if s.start <= inp.now),
        default=upcoming[0][0],
    )
    if current_index in chosen:
        price = inp.price_forecast[current_index].price
        return True, {
            "price": f"{price:.3f}",
            "target": f"{cfg.target_energy_kwh:.0f}",
        }
    return False, {}


# --- Phase + dwell helpers ------------------------------------------------------

def _resolve_phases(
    surplus_w: float, inp: ChargerInputs, cfg: EngineConfig, state: EngineState
) -> int:
    """Pick 1 or 3 phases for solar charging, with hysteresis and a dwell timer.

    A single phase lets the car keep charging on a small surplus that three
    phases (with their higher minimum) could not use. We switch up to three
    phases only once the surplus can sustain their minimum, and back down only
    once it drops below what a single phase can deliver at full current — the
    gap between the two thresholds is the hysteresis band. A dwell timer caps
    how often the contactor may toggle.

    Surplus charging *prefers* a single phase: with no remembered phase yet we
    start at 1φ (not the configured default, which is typically 3φ) so a small
    surplus is used immediately, climbing to 3φ only once it sustains the
    higher minimum.
    """
    if not cfg.auto_phase or cfg.max_phases < 3:
        return inp.phases

    current = state.phases if state.phases in (1, 3) else 1
    up_threshold = _current_to_power(cfg.min_current_a, 3, inp.voltage_v)
    down_threshold = _current_to_power(cfg.max_current_a, 1, inp.voltage_v)

    desired = current
    if current == 1 and surplus_w >= up_threshold:
        desired = 3
    elif current == 3 and surplus_w < down_threshold:
        desired = 1

    if desired == current:
        state.phases = current
        return current

    # Honour the dwell timer before toggling the contactor.
    if (
        inp.now is not None
        and state.phase_changed_at is not None
        and (inp.now - state.phase_changed_at).total_seconds() < cfg.phase_dwell_s
    ):
        return current

    state.phases = desired
    state.phase_changed_at = inp.now
    return desired


#: Modes that should always charge at full phase count (max power), never on a
#: single phase: Fast, and the grid-charging branches (cheap-grid / deadline) of
#: the price-aware modes. Surplus charging is handled separately by
#: :func:`_resolve_phases`, which prefers a single phase.
_FULL_PHASE_MODES: frozenset[ChargingMode] = frozenset(
    {ChargingMode.FAST, ChargingMode.PRICE}
)


def _phases_for(
    mode: ChargingMode,
    surplus_w: float,
    inp: ChargerInputs,
    cfg: EngineConfig,
    state: EngineState,
    *,
    grid_charging: bool,
) -> int:
    """Per-mode phase count, honouring the ``auto_phase`` master toggle.

    With auto-phase off (or no 3-phase headroom) phases are left untouched —
    today's behaviour. With it on: power/grid charging runs at the full phase
    count for maximum throughput, while solar-surplus charging adapts 1↔3
    phases via :func:`_resolve_phases` (preferring a single phase).
    """
    if not cfg.auto_phase or cfg.max_phases < 3:
        return inp.phases
    if grid_charging or mode in _FULL_PHASE_MODES:
        return cfg.max_phases
    return _resolve_phases(surplus_w, inp, cfg, state)


def _apply_charge_dwell(
    want_charge: bool, inp: ChargerInputs, cfg: EngineConfig, state: EngineState
) -> bool:
    """Hold the previous on/off state until its minimum dwell has elapsed."""
    if state.charging is None:
        state.charging = want_charge
        state.charge_changed_at = inp.now
        return want_charge
    if want_charge == state.charging:
        return want_charge
    if inp.now is not None and state.charge_changed_at is not None:
        dwell = cfg.min_on_dwell_s if state.charging else cfg.min_off_dwell_s
        if (inp.now - state.charge_changed_at).total_seconds() < dwell:
            return state.charging
    state.charging = want_charge
    state.charge_changed_at = inp.now
    return want_charge


# --- The decision ---------------------------------------------------------------

# Reason catalog: a stable key → English template. The engine emits the key plus
# pre-formatted string params; the card localizes the same key (see the card's
# ``reason.*`` strings), while ``reason`` keeps the English rendering for logs and
# tests. Keys are explicit per variant (e.g. ``_guarded``/``_phase`` suffixes)
# rather than composed at runtime, so both sides do plain placeholder substitution.
_REASON_TEMPLATES: dict[str, str] = {
    "smart_disabled": "Smart control disabled",
    "manual_paused": "Manual mode — paused",
    "manual_charging": "Manual charging at {amps} A",
    "manual_charging_guarded": (
        "Manual charging at {amps} A (protecting home battery)"
    ),
    "no_car": "No car connected",
    "fast": "Fast charging at {amps} A",
    "cheap_grid": "Cheap grid {price}/kWh ≤ {threshold} → full power",
    "cheap_grid_guarded": (
        "Cheap grid {price}/kWh ≤ {threshold} → full power "
        "(protecting home battery → {amps} A)"
    ),
    "deadline_plan": (
        "Cheap-hours plan: charging now at {price}/kWh "
        "to reach {target} kWh by departure"
    ),
    "deadline_plan_guarded": (
        "Cheap-hours plan: charging now at {price}/kWh "
        "to reach {target} kWh by departure (protecting home battery → {amps} A)"
    ),
    "holding_off_dwell": "Holding off (anti-flap dwell)",
    "price_waiting": "Waiting for a cheaper price window",
    "charging": "Charging",
    "waiting_battery_reserve": (
        "Waiting — home battery {soc}% < reserve {reserve}%"
    ),
    "waiting_surplus": "Waiting for surplus — {surplus} W < {needed} W needed",
    "solar_surplus": "Solar surplus {surplus} W → {amps} A",
    "solar_surplus_phase": "Solar surplus {surplus} W → {amps} A ({phases}-phase)",
    "solar_min_topup": (
        "Minimum {amps} A (surplus only {surplus} W, topping up from grid)"
    ),
    "holding_charge_dwell": "Holding charge (anti-flap dwell)",
}


def _reason(key: str, **params: str) -> tuple[str, str, dict[str, str]]:
    """Build a decision reason three ways at once.

    Returns ``(english_text, key, params)``: the English rendering for
    ``Decision.reason`` plus the stable key and params the card localizes from.
    """
    return _REASON_TEMPLATES[key].format(**params), key, params


def _decide_manual(
    inp: ChargerInputs, cfg: EngineConfig, state: EngineState
) -> Decision:
    """Manual mode (``ChargingMode.OFF``): the user is the brain.

    Start/stop, charging current and phase count come straight from the manual
    controls; the battery policy still governs whether the home battery is held
    back from the car (and trims the current as a fallback when no hold switch is
    mapped), exactly as in the smart modes — so users learn one battery concept.

    Note this *actively drives* the charger (``control=True``): manual no longer
    means hands-off. To fully release the charger to the go-e app, turn Smart
    control off (handled by the master gate above).
    """
    phases = cfg.manual_phases if cfg.manual_phases in (1, 3) else inp.phases

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

    # Charging: hold the home battery per policy and trim as the fallback, then
    # drive the user's requested current.
    hold = _hold_battery(inp, cfg)
    current, guarded = _battery_guard_current(
        cfg.manual_current_a, phases, inp, cfg, hold=hold
    )
    if guarded:
        reason, rkey, rparams = _reason("manual_charging_guarded", amps=f"{current:.1f}")
    else:
        reason, rkey, rparams = _reason("manual_charging", amps=f"{current:.0f}")
    return Decision(
        control=True,
        should_charge=True,
        target_current_a=current,
        target_phases=phases,
        write_phases=True,
        hold_battery=hold,
        reason=reason,
        reason_key=rkey,
        reason_params=rparams,
    )


def decide(
    inp: ChargerInputs, cfg: EngineConfig, state: EngineState | None = None
) -> Decision:
    """Return the charging decision for the current cycle.

    ``state`` carries dwell/hysteresis memory between cycles; a fresh one is used
    when omitted (e.g. one-shot reasoning or tests that don't exercise timers).
    """
    if state is None:
        state = EngineState()

    # --- Master gates ------------------------------------------------------------
    if not cfg.smart_enabled:
        reason, rkey, rparams = _reason("smart_disabled")
        return Decision(
            control=False, reason=reason, reason_key=rkey, reason_params=rparams
        )
    if cfg.mode is ChargingMode.OFF:
        return _decide_manual(inp, cfg, state)
    if not inp.car_connected:
        reason, rkey, rparams = _reason("no_car")
        return Decision(
            control=True,
            should_charge=False,
            target_phases=inp.phases,
            reason=reason,
            reason_key=rkey,
            reason_params=rparams,
        )

    # --- Fast: just go ----------------------------------------------------------
    if cfg.mode is ChargingMode.FAST:
        reason, rkey, rparams = _reason("fast", amps=f"{cfg.max_current_a:.0f}")
        return Decision(
            control=True,
            should_charge=True,
            target_current_a=cfg.max_current_a,
            target_phases=_phases_for(
                cfg.mode, 0.0, inp, cfg, state, grid_charging=True
            ),
            hold_battery=_hold_battery(inp, cfg),
            reason=reason,
            reason_key=rkey,
            reason_params=rparams,
        )

    # --- Cheap-grid charging (price-aware modes) --------------------------------
    # Grid charging draws from the grid, not the home battery, so the PROTECT
    # reserve hold does not apply here.
    cheap_now = (
        inp.price_now is not None
        and inp.price_now <= cfg.cheap_price
        and cfg.mode in (ChargingMode.PV_PRICE, ChargingMode.COMBINED)
    )
    deadline_now, deadline_params = (False, {})
    if cfg.mode in (ChargingMode.PRICE, ChargingMode.COMBINED):
        deadline_now, deadline_params = _is_cheap_window(inp, cfg)

    if cheap_now or deadline_now:
        phases = _phases_for(cfg.mode, 0.0, inp, cfg, state, grid_charging=True)
        # Cheap grid → use the grid, never the home battery: the stored energy is
        # worth more than the cheap grid we'd otherwise pass up, so always hold,
        # regardless of battery policy. The deadline plan can charge at
        # not-actually-cheap hours to hit departure, so it stays policy-based (the
        # battery may help there). One decision drives both the hold switch and the
        # current-trim fallback, so they stay consistent.
        hold = True if cheap_now else _hold_battery(inp, cfg)
        current, guarded = _battery_guard_current(
            cfg.max_current_a, phases, inp, cfg, hold=hold
        )
        if cheap_now:
            base, params = "cheap_grid", {
                "price": f"{inp.price_now:.3f}",
                "threshold": f"{cfg.cheap_price:.3f}",
            }
        else:
            base, params = "deadline_plan", dict(deadline_params)
        if guarded:
            base += "_guarded"
            params["amps"] = f"{current:.1f}"
        want = _apply_charge_dwell(True, inp, cfg, state)
        reason, rkey, rparams = (
            _reason(base, **params) if want else _reason("holding_off_dwell")
        )
        return Decision(
            control=True,
            should_charge=want,
            target_current_a=current if want else 0.0,
            target_phases=phases,
            hold_battery=want and hold,
            reason=reason,
            reason_key=rkey,
            reason_params=rparams,
        )

    # --- Pure Price mode with nothing to do -------------------------------------
    if cfg.mode is ChargingMode.PRICE:
        want = _apply_charge_dwell(False, inp, cfg, state)
        reason, rkey, rparams = _reason("charging" if want else "price_waiting")
        return Decision(
            control=True,
            should_charge=want,
            target_current_a=cfg.max_current_a if want else 0.0,
            target_phases=inp.phases,
            hold_battery=want and _hold_battery(inp, cfg),
            reason=reason,
            reason_key=rkey,
            reason_params=rparams,
        )

    # --- PV-based modes (PV_ONLY / PV_MINIMUM / PV_PRICE surplus / COMBINED) -----
    surplus = compute_surplus(inp, cfg)
    phases = _phases_for(cfg.mode, surplus, inp, cfg, state, grid_charging=False)
    pv_current = _power_to_current(surplus, phases, inp.voltage_v)
    min_power = _current_to_power(cfg.min_current_a, phases, inp.voltage_v)

    guarantees_floor = cfg.mode is ChargingMode.PV_MINIMUM

    if not guarantees_floor and pv_current < cfg.min_current_a:
        if _battery_held(inp, cfg):
            reason, rkey, rparams = _reason(
                "waiting_battery_reserve",
                soc=f"{inp.battery_soc:.0f}",
                reserve=f"{cfg.battery_reserve_soc:.0f}",
            )
        else:
            reason, rkey, rparams = _reason(
                "waiting_surplus",
                surplus=f"{surplus:.0f}",
                needed=f"{min_power:.0f}",
            )
        want = _apply_charge_dwell(False, inp, cfg, state)
        return Decision(
            control=True,
            should_charge=want,
            target_current_a=cfg.min_current_a if want else 0.0,
            target_phases=phases,
            surplus_w=surplus,
            reason=reason,
            reason_key=rkey,
            reason_params=rparams,
        )

    # Pure solar charging rides on real surplus, so it never holds the battery
    # (and Assist may back the car here). The exception is the PV+minimum grid
    # top-up below: that draws above solar, so — with the grid pinned at 0 — the
    # battery would supply the floor unless we hold it per policy.
    hold = False
    if guarantees_floor:
        floor_current = max(
            cfg.min_current_a,
            _power_to_current(cfg.min_grid_floor_w, phases, inp.voltage_v),
        )
        current = _clamp(
            max(pv_current, floor_current), cfg.min_current_a, cfg.max_current_a
        )
        if pv_current >= floor_current:
            base, params = "solar_surplus", {
                "surplus": f"{surplus:.0f}",
                "amps": f"{current:.1f}",
            }
        else:
            base, params = "solar_min_topup", {
                "amps": f"{current:.1f}",
                "surplus": f"{surplus:.0f}",
            }
            hold = _hold_battery(inp, cfg)
    else:
        current = _clamp(pv_current, cfg.min_current_a, cfg.max_current_a)
        params = {"surplus": f"{surplus:.0f}", "amps": f"{current:.1f}"}
        if phases != inp.phases:
            base = "solar_surplus_phase"
            params["phases"] = str(phases)
        else:
            base = "solar_surplus"

    want = _apply_charge_dwell(True, inp, cfg, state)
    reason, rkey, rparams = (
        _reason(base, **params) if want else _reason("holding_charge_dwell")
    )
    return Decision(
        control=True,
        should_charge=want,
        target_current_a=current if want else 0.0,
        target_phases=phases,
        surplus_w=surplus,
        hold_battery=want and hold,
        reason=reason,
        reason_key=rkey,
        reason_params=rparams,
    )
