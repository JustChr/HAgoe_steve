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

from dataclasses import dataclass
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
    surplus_w: float = 0.0
    reason: str = ""


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


def _battery_guard_current(
    full_current_a: float, phases: int, inp: ChargerInputs, cfg: EngineConfig
) -> tuple[float, bool]:
    """Trim grid-charge current so the home battery isn't drained into the car.

    Cheap-grid (and deadline) charging draws from the grid, but on many inverters
    the home battery will happily discharge to cover part of the car's load —
    paying a round-trip loss and a battery cycle for energy the cheap grid could
    supply directly. Under ``PROTECT``/``SHARE`` we therefore subtract whatever the
    battery is currently discharging from the car's target current, so the grid
    carries that load and the battery holds its charge. ``ASSIST`` opts out: it
    exists precisely to back the car from the battery. Re-evaluated every cycle, so
    it converges as the inverter responds.

    Returns ``(current, guarded)`` where ``guarded`` flags that we trimmed.
    """
    if cfg.battery_policy is BatteryPolicy.ASSIST or inp.battery_power_w is None:
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


def _is_cheap_window(inp: ChargerInputs, cfg: EngineConfig) -> tuple[bool, str]:
    """Should we grid-charge *now* to hit the target energy by departure?

    Greedy cheapest-hours plan, recomputed every cycle so it self-corrects:
    take the upcoming slots before the deadline, sort by price, and keep the
    cheapest ones until their charging capacity covers ``target_energy_kwh``.
    Charge if the current slot is in that cheapest set.
    """
    if (
        not cfg.target_energy_kwh
        or cfg.departure is None
        or inp.now is None
        or not inp.price_forecast
    ):
        return False, ""

    if inp.now >= cfg.departure:
        return False, ""

    upcoming = [
        (i, s)
        for i, s in enumerate(inp.price_forecast)
        if s.start < cfg.departure
        and s.start + timedelta(minutes=_slot_minutes(inp.price_forecast, i)) > inp.now
    ]
    if not upcoming:
        return False, ""

    max_power_kw = (
        _current_to_power(cfg.max_current_a, cfg.max_phases, inp.voltage_v) / 1000.0
    )
    if max_power_kw <= 0:
        return False, ""

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
        return True, (
            f"Cheap-hours plan: charging now at {price:.3f}/kWh "
            f"to reach {cfg.target_energy_kwh:.0f} kWh by departure"
        )
    return False, ""


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
        return Decision(control=False, reason="Smart control disabled")
    if cfg.mode is ChargingMode.OFF:
        return Decision(control=False, reason="Mode: Off — manual control")
    if not inp.car_connected:
        return Decision(
            control=True,
            should_charge=False,
            target_phases=inp.phases,
            reason="No car connected",
        )

    # --- Fast: just go ----------------------------------------------------------
    if cfg.mode is ChargingMode.FAST:
        return Decision(
            control=True,
            should_charge=True,
            target_current_a=cfg.max_current_a,
            target_phases=_phases_for(
                cfg.mode, 0.0, inp, cfg, state, grid_charging=True
            ),
            reason=f"Fast charging at {cfg.max_current_a:.0f} A",
        )

    # --- Cheap-grid charging (price-aware modes) --------------------------------
    # Grid charging draws from the grid, not the home battery, so the PROTECT
    # reserve hold does not apply here.
    cheap_now = (
        inp.price_now is not None
        and inp.price_now <= cfg.cheap_price
        and cfg.mode in (ChargingMode.PV_PRICE, ChargingMode.COMBINED)
    )
    deadline_now, deadline_reason = (False, "")
    if cfg.mode in (ChargingMode.PRICE, ChargingMode.COMBINED):
        deadline_now, deadline_reason = _is_cheap_window(inp, cfg)

    if cheap_now or deadline_now:
        phases = _phases_for(cfg.mode, 0.0, inp, cfg, state, grid_charging=True)
        current, guarded = _battery_guard_current(
            cfg.max_current_a, phases, inp, cfg
        )
        if cheap_now:
            reason = (
                f"Cheap grid {inp.price_now:.3f}/kWh ≤ "
                f"{cfg.cheap_price:.3f} → full power"
            )
        else:
            reason = deadline_reason
        if guarded:
            reason += f" (protecting home battery → {current:.1f} A)"
        want = _apply_charge_dwell(True, inp, cfg, state)
        return Decision(
            control=True,
            should_charge=want,
            target_current_a=current if want else 0.0,
            target_phases=phases,
            reason=reason if want else "Holding off (anti-flap dwell)",
        )

    # --- Pure Price mode with nothing to do -------------------------------------
    if cfg.mode is ChargingMode.PRICE:
        want = _apply_charge_dwell(False, inp, cfg, state)
        return Decision(
            control=True,
            should_charge=want,
            target_current_a=cfg.max_current_a if want else 0.0,
            target_phases=inp.phases,
            reason="Waiting for a cheaper price window" if not want else "Charging",
        )

    # --- PV-based modes (PV_ONLY / PV_MINIMUM / PV_PRICE surplus / COMBINED) -----
    surplus = compute_surplus(inp, cfg)
    phases = _phases_for(cfg.mode, surplus, inp, cfg, state, grid_charging=False)
    pv_current = _power_to_current(surplus, phases, inp.voltage_v)
    min_power = _current_to_power(cfg.min_current_a, phases, inp.voltage_v)

    guarantees_floor = cfg.mode is ChargingMode.PV_MINIMUM

    if not guarantees_floor and pv_current < cfg.min_current_a:
        if _battery_held(inp, cfg):
            reason = (
                f"Waiting — home battery {inp.battery_soc:.0f}% "
                f"< reserve {cfg.battery_reserve_soc:.0f}%"
            )
        else:
            reason = (
                f"Waiting for surplus — {surplus:.0f} W < {min_power:.0f} W needed"
            )
        want = _apply_charge_dwell(False, inp, cfg, state)
        return Decision(
            control=True,
            should_charge=want,
            target_current_a=cfg.min_current_a if want else 0.0,
            target_phases=phases,
            surplus_w=surplus,
            reason=reason,
        )

    if guarantees_floor:
        floor_current = max(
            cfg.min_current_a,
            _power_to_current(cfg.min_grid_floor_w, phases, inp.voltage_v),
        )
        current = _clamp(
            max(pv_current, floor_current), cfg.min_current_a, cfg.max_current_a
        )
        if pv_current >= floor_current:
            reason = f"Solar surplus {surplus:.0f} W → {current:.1f} A"
        else:
            reason = (
                f"Minimum {current:.1f} A (surplus only {surplus:.0f} W, "
                "topping up from grid)"
            )
    else:
        current = _clamp(pv_current, cfg.min_current_a, cfg.max_current_a)
        reason = f"Solar surplus {surplus:.0f} W → {current:.1f} A"
        if phases != inp.phases:
            reason += f" ({phases}-phase)"

    want = _apply_charge_dwell(True, inp, cfg, state)
    return Decision(
        control=True,
        should_charge=want,
        target_current_a=current if want else 0.0,
        target_phases=phases,
        surplus_w=surplus,
        reason=reason if want else "Holding charge (anti-flap dwell)",
    )
