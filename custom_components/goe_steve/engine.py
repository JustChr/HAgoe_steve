"""Pure regulation engine for go-e + SteVe Smart Charging.

This module is intentionally free of any Home Assistant imports so that the
decision logic can be reasoned about and unit-tested in isolation (see
``tests/test_engine.py``). The coordinator feeds it a snapshot of the world
(:class:`ChargerInputs`) plus the current settings (:class:`EngineConfig`) and
gets back a single :class:`Decision` describing what the charger should do and,
crucially, *why* — the human-readable ``reason`` is surfaced in the UI.

Phase 1 scope: Off / PV-surplus / PV+minimum / Fast modes, with the "Protect"
battery policy (home battery has priority over the car). Price-based modes,
phase switching, and the Share/Assist battery policies arrive in Phase 2.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class ChargingMode(StrEnum):
    """User-selectable charging strategy.

    The full set from the concept is defined here for forward compatibility, but
    only ``PHASE1_MODES`` are offered in the UI and implemented by :func:`decide`.
    """

    OFF = "off"
    PV_ONLY = "pv_only"
    PV_MINIMUM = "pv_minimum"
    PV_PRICE = "pv_price"  # Phase 2
    PRICE = "price"  # Phase 2
    COMBINED = "combined"  # Phase 2
    FAST = "fast"


#: Modes implemented and offered to the user in Phase 1.
PHASE1_MODES: tuple[ChargingMode, ...] = (
    ChargingMode.OFF,
    ChargingMode.PV_ONLY,
    ChargingMode.PV_MINIMUM,
    ChargingMode.FAST,
)


class BatteryPolicy(StrEnum):
    """How home-battery energy may participate in car charging."""

    PROTECT = "protect"  # battery first; never reduced/discharged for the car
    SHARE = "share"  # Phase 2: car may take power that would charge the battery
    ASSIST = "assist"  # Phase 2: battery may discharge into the car


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


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def compute_surplus(inp: ChargerInputs, cfg: EngineConfig) -> float:
    """Power (W) available to the car under the active battery policy.

    Base headroom is grid export plus the car's own current draw (the car's draw
    suppresses export, so it must be added back). Phase 1 implements the
    ``PROTECT`` policy: while the home battery is below its reserve SoC the car
    gets nothing, so the battery fills first.
    """
    export_w = max(0.0, -inp.grid_power_w)
    surplus = export_w + max(0.0, inp.car_actual_power_w)

    if inp.battery_soc is not None and cfg.battery_policy is BatteryPolicy.PROTECT:
        if inp.battery_soc < cfg.battery_reserve_soc:
            return 0.0
    return surplus


def _power_to_current(power_w: float, phases: int, voltage_v: float) -> float:
    return power_w / (phases * voltage_v)


def _current_to_power(current_a: float, phases: int, voltage_v: float) -> float:
    return current_a * phases * voltage_v


def decide(inp: ChargerInputs, cfg: EngineConfig) -> Decision:
    """Return the charging decision for the current cycle."""
    phases = inp.phases  # phase switching is Phase 2 — keep the configured count

    # --- Master gates ------------------------------------------------------------
    if not cfg.smart_enabled:
        return Decision(control=False, reason="Smart control disabled")
    if cfg.mode is ChargingMode.OFF:
        return Decision(control=False, reason="Mode: Off — manual control")
    if not inp.car_connected:
        return Decision(
            control=True,
            should_charge=False,
            target_phases=phases,
            reason="No car connected",
        )

    # --- Fast: just go ----------------------------------------------------------
    if cfg.mode is ChargingMode.FAST:
        current = cfg.max_current_a
        return Decision(
            control=True,
            should_charge=True,
            target_current_a=current,
            target_phases=phases,
            reason=f"Fast charging at {current:.0f} A",
        )

    # --- PV-based modes ---------------------------------------------------------
    surplus = compute_surplus(inp, cfg)
    pv_current = _power_to_current(surplus, phases, inp.voltage_v)
    min_power = _current_to_power(cfg.min_current_a, phases, inp.voltage_v)

    if cfg.mode is ChargingMode.PV_ONLY:
        if pv_current < cfg.min_current_a:
            held = (
                inp.battery_soc is not None
                and cfg.battery_policy is BatteryPolicy.PROTECT
                and inp.battery_soc < cfg.battery_reserve_soc
            )
            if held:
                reason = (
                    f"Waiting — home battery {inp.battery_soc:.0f}% "
                    f"< reserve {cfg.battery_reserve_soc:.0f}%"
                )
            else:
                reason = (
                    f"Waiting for surplus — {surplus:.0f} W "
                    f"< {min_power:.0f} W needed"
                )
            return Decision(
                control=True,
                should_charge=False,
                target_phases=phases,
                surplus_w=surplus,
                reason=reason,
            )
        current = _clamp(pv_current, cfg.min_current_a, cfg.max_current_a)
        return Decision(
            control=True,
            should_charge=True,
            target_current_a=current,
            target_phases=phases,
            surplus_w=surplus,
            reason=f"Solar surplus {surplus:.0f} W → {current:.1f} A",
        )

    if cfg.mode is ChargingMode.PV_MINIMUM:
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
        return Decision(
            control=True,
            should_charge=True,
            target_current_a=current,
            target_phases=phases,
            surplus_w=surplus,
            reason=reason,
        )

    # Defensive: a not-yet-implemented mode must never charge silently.
    return Decision(
        control=False,
        target_phases=phases,
        reason=f"Mode '{cfg.mode.value}' not available yet (Phase 2)",
    )
