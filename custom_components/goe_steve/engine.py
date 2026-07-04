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

* **Solar surplus** — the smoothed solar power available to the car.
* **Cheap grid** — full power while the spot price is at/below the threshold.
* **Departure plan** — full power during the cheapest forecast slots needed to
  cover the *remaining* energy (target − delivered) by departure, guaranteed.
* **Minimum floor** — the minimum current, always (Solar + minimum mode).
* **Full power** — always (Fast mode).

The arbiter takes the highest proposal (grid strategies win ties, so the
battery-hold below stays engaged), then applies the shared constraints: the
home-battery policy, 1↔3-phase resolution with hysteresis + dwell, and the
start-confirmation / ride-out machine that keeps the charger from flapping.

Home-battery policy (one reserve line, two zones):

* **Below the reserve** the battery comes first: the car gets only genuine
  excess solar and any battery discharge is deducted immediately.
* **At/above the reserve** the battery is a *fluctuation buffer*: the car
  follows the smoothed surplus, the battery bridges short dips and spikes, and
  only sustained discharge into the car is corrected.
* **Whenever a grid strategy wins** (cheap hour, plan, floor, Fast) the battery
  is held (``hold_battery``) so grid power charges the car, never the battery.

Everything time-dependent receives ``now`` explicitly so the logic stays
deterministic and testable.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
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
    # Solar smoothing + battery-buffer behaviour.
    smooth_window_s: float = 120.0  # rolling window for the surplus average
    discharge_tolerance_w: float = 300.0  # sustained battery→car drain above this…
    discharge_grace_s: float = 180.0  # …for this long triggers a decisive ease-off
    # Start/stop shaping ("ride out, then stop").
    start_confirm_s: float = 180.0  # surplus must hold ≥ min this long to start
    stop_ride_out_s: float = 300.0  # keep min current this long through a dip


@dataclass(slots=True)
class EngineState:
    """Mutable memory carried across cycles by the coordinator.

    Holds the smoothing windows and the timers of the start/stop machine; it is
    reset on restart, which simply means the windows and timers start fresh.
    """

    # Phase hysteresis/dwell memory.
    phases: int | None = None
    phase_changed_at: datetime | None = None
    # Start/stop machine.
    charging: bool | None = None
    active_source: str | None = None  # "solar" | "grid" while charging
    surplus_ok_since: datetime | None = None
    ride_out_since: datetime | None = None
    # Battery-buffer memory.
    discharge_high_since: datetime | None = None
    avail_zone: str | None = None  # "protect" | "buffer" the samples belong to
    avail_samples: deque[tuple[datetime, float]] = field(default_factory=deque)
    discharge_samples: deque[tuple[datetime, float]] = field(default_factory=deque)


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


# Ignore tiny home-battery discharge (sensor noise / standby) before the guard
# below starts trimming grid-charge current.
_BATTERY_DRAIN_TOLERANCE_W: float = 100.0

# Manual charging counts as grid-assisted (→ hold the battery) once the
# requested power exceeds the available surplus by more than this margin.
_MANUAL_GRID_MARGIN_W: float = 100.0


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


def _power_to_current(power_w: float, phases: int, voltage_v: float) -> float:
    return power_w / (phases * voltage_v)


def _current_to_power(current_a: float, phases: int, voltage_v: float) -> float:
    return current_a * phases * voltage_v


# --- Solar availability (the surplus strategy's signal) --------------------------

def _smoothed(
    samples: deque[tuple[datetime, float]],
    now: datetime | None,
    value: float,
    window_s: float,
) -> float:
    """Time-based rolling average over ``window_s`` seconds.

    With ``now`` unknown the value passes through raw (stateless tests / one-shot
    reasoning). Samples arrive event-driven, so the window is wall-clock based,
    not count based.
    """
    if now is None:
        return value
    samples.append((now, value))
    cutoff = now - timedelta(seconds=window_s)
    while samples and samples[0][0] < cutoff:
        samples.popleft()
    return sum(v for _, v in samples) / len(samples)


@dataclass(slots=True)
class Availability:
    """Solar power available to the car right now, and how it was derived."""

    power_w: float
    zone: str  # "protect" (below reserve / SoC unknown) or "buffer"
    eased: bool  # sustained battery→car discharge is being corrected


def compute_availability(
    inp: ChargerInputs, cfg: EngineConfig, state: EngineState
) -> Availability:
    """Smoothed solar power available to the car (W), per the battery policy.

    The underlying identity — invariant to the car's own current changes, so it
    can be smoothed without chasing our own moves — is::

        available = PV − house = grid_export + car_draw + battery_signed

    (``battery_signed``: + charging adds reclaimable solar, − discharging
    subtracts power that is *not* solar.)

    Two zones from the single reserve line:

    * **protect** (SoC below the reserve, or unknown): the battery comes first.
      No reclaim of solar the battery is absorbing, and any discharge is
      deducted immediately — zero tolerance.
    * **buffer** (SoC at/above the reserve): solar flowing into the battery is
      reclaimable for the car, and discharge is deducted only via the smoothed
      window — so the battery bridges short dips and spikes. Sustained
      discharge beyond ``discharge_tolerance_w`` for ``discharge_grace_s``
      switches to the raw deduction (a decisive ease-off).
    """
    export_w = max(0.0, -inp.grid_power_w)
    base = export_w + max(0.0, inp.car_actual_power_w)
    batt = inp.battery_power_w
    soc = inp.battery_soc
    protect = soc is None or soc < cfg.battery_reserve_soc
    zone = "protect" if protect else "buffer"

    # The formula changes across the reserve line; stale samples from the other
    # zone would blend two different signals, so start the window fresh.
    if zone != state.avail_zone:
        state.avail_samples.clear()
        state.discharge_samples.clear()
        state.discharge_high_since = None
        state.avail_zone = zone

    discharge_raw = max(0.0, -batt) if batt is not None else 0.0
    if not protect and batt is not None:
        base += max(0.0, batt)  # reclaim solar the battery is absorbing

    base_s = _smoothed(state.avail_samples, inp.now, base, cfg.smooth_window_s)

    if protect:
        return Availability(max(0.0, base_s - discharge_raw), zone, False)

    dis_s = _smoothed(
        state.discharge_samples, inp.now, discharge_raw, cfg.smooth_window_s
    )
    eased = _track_sustained_discharge(inp, cfg, state, discharge_raw)
    penalty = discharge_raw if eased else dis_s
    return Availability(max(0.0, base_s - penalty), zone, eased)


def _track_sustained_discharge(
    inp: ChargerInputs, cfg: EngineConfig, state: EngineState, discharge_raw: float
) -> bool:
    """True once the battery has discharged beyond tolerance for the grace time."""
    if inp.now is None or discharge_raw <= cfg.discharge_tolerance_w:
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
    guarded_a = max(cfg.min_current_a, full_current_a - trim_a)
    return guarded_a, guarded_a < full_current_a


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
    inp: ChargerInputs, cfg: EngineConfig, phases: int
) -> _Plan | None:
    """Greedy cheapest-slots departure plan, or None when not planning.

    Recomputed every cycle so it self-corrects as prices update and energy is
    delivered. ``phases`` is the phase count grid charging would actually use, so
    the per-slot capacity is realistic (a 1φ-locked wallbox books three times the
    hours).

    The target is a **hard guarantee**: the plan keeps booking the
    least-expensive remaining slots until their capacity covers the remaining
    energy, whether or not they are "cheap" — and if the remaining time barely
    covers the remaining energy at full power, it charges regardless of the
    forecast (``urgent``).
    """
    remaining = _plan_remaining_kwh(inp, cfg)
    if remaining is None or remaining <= 0:
        return None
    if inp.now >= cfg.departure:
        return None

    max_power_kw = _current_to_power(cfg.max_current_a, phases, inp.voltage_v) / 1000.0
    if max_power_kw <= 0:
        return None

    # Safety net (also covers a missing/short forecast): when every remaining
    # hour is needed to make the target, price no longer matters.
    hours_left = (cfg.departure - inp.now).total_seconds() / 3600.0
    if hours_left * max_power_kw <= remaining:
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

def _resolve_phases(
    surplus_w: float, inp: ChargerInputs, cfg: EngineConfig, state: EngineState
) -> int:
    """Pick 1 or 3 phases for solar charging, with hysteresis and a dwell timer.

    The thresholds evaluate the surplus against both *candidate* configurations
    (what three phases would minimally need, what one phase could maximally
    deliver) rather than the currently active phase count, so the choice is
    free of the current/target coupling. We switch up to three phases only once
    the surplus can sustain their minimum, and back down only once it drops
    below what a single phase can deliver at full current — the gap between the
    two thresholds is the hysteresis band. A dwell timer caps how often the
    contactor may toggle.

    Surplus charging *prefers* a single phase: with no remembered phase yet we
    start at 1φ so a small surplus is used immediately, climbing to 3φ only
    once it sustains the higher minimum.
    """
    if not cfg.auto_phase or cfg.max_phases < 3:
        return max(1, inp.phases)

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
    "fast": "Fast charging at {amps} A",
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
    "solar_min_topup": (
        "Minimum {amps} A (surplus only {surplus} W, topping up from grid)"
    ),
}


def _reason(key: str, **params: str) -> tuple[str, str, dict[str, str]]:
    """Build a decision reason three ways at once.

    Returns ``(english_text, key, params)``: the English rendering for
    ``Decision.reason`` plus the stable key and params the card localizes from.
    """
    return _REASON_TEMPLATES[key].format(**params), key, params


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
        floor_w = _current_to_power(cfg.min_current_a, floor_phases, inp.voltage_v)
        proposals.append(_Proposal("floor", "grid", floor_w))

    if cfg.mode in _SOLAR_MODES:
        proposals.append(
            _Proposal("solar", "solar", min(avail.power_w, max_grid_w))
        )

    return proposals


def _idle_reason(
    inp: ChargerInputs, cfg: EngineConfig, avail: Availability, needed_w: float
) -> tuple[str, str, dict[str, str]]:
    """Why the charger is (staying) off — the most informative answer first."""
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
        surplus=f"{avail.power_w:.0f}",
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
        hold = requested_w > avail.power_w + _MANUAL_GRID_MARGIN_W
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
    """
    if state is None:
        state = EngineState()

    plan: _Plan | None = None
    if cfg.smart_enabled and cfg.mode is ChargingMode.SMART and inp.car_connected:
        grid_phases = cfg.max_phases if cfg.auto_phase else max(1, inp.phases)
        plan = _compute_plan(inp, cfg, grid_phases)

    decision = _decide(inp, cfg, state, plan)
    return _finalize(decision, inp, cfg, state, plan)


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
    if state.phase_changed_at is not None:
        decision.phase_locked_until = state.phase_changed_at + timedelta(
            seconds=cfg.phase_dwell_s
        )
    return decision


def _decide(
    inp: ChargerInputs, cfg: EngineConfig, state: EngineState, plan: _Plan | None
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
    grid_phases = cfg.max_phases if cfg.auto_phase else max(1, inp.phases)
    floor_phases = 1 if cfg.auto_phase else max(1, inp.phases)
    min_solar_w = _current_to_power(cfg.min_current_a, floor_phases, inp.voltage_v)

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
    if avail.power_w >= min_solar_w:
        if state.surplus_ok_since is None:
            state.surplus_ok_since = inp.now
    else:
        state.surplus_ok_since = None
    solar_confirmed = inp.now is None or (
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
                reason, rkey, rparams = _reason(
                    "surplus_ride_out", amps=f"{cfg.min_current_a:.0f}"
                )
                return Decision(
                    control=True,
                    should_charge=True,
                    target_current_a=cfg.min_current_a,
                    target_phases=max(1, inp.phases),
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
            surplus_w=avail.power_w,
            reason=reason,
            reason_key=rkey,
            reason_params=rparams,
        )

    assert winner is not None  # narrowed by `active`
    state.ride_out_since = None

    # --- Solar starts wait for the confirmation window -----------------------------
    if not state.charging and winner.source == "solar" and not solar_confirmed:
        reason, rkey, rparams = _reason(
            "surplus_confirm", surplus=f"{avail.power_w:.0f}"
        )
        return Decision(
            control=True,
            should_charge=False,
            target_phases=max(1, inp.phases),
            surplus_w=avail.power_w,
            reason=reason,
            reason_key=rkey,
            reason_params=rparams,
        )

    state.charging = True
    state.active_source = winner.source

    # --- Build the charging decision ------------------------------------------------
    if winner.source == "grid":
        if winner.kind == "floor":
            phases = _resolve_phases(avail.power_w, inp, cfg, state)
            base_amps = cfg.min_current_a
        else:
            phases = grid_phases
            base_amps = cfg.max_current_a
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
                params["amps"] = f"{amps:.1f}"
        elif winner.kind == "plan":
            key = "deadline_plan_guarded" if guarded else "deadline_plan"
            if guarded:
                params["amps"] = f"{amps:.1f}"
        elif winner.kind == "urgent":
            key = "deadline_urgent"
        elif winner.kind == "fast":
            key = "fast"
            params["amps"] = f"{amps:.0f}"
        else:  # floor
            key = "solar_min_topup"
            params["amps"] = f"{amps:.1f}"
            params["surplus"] = f"{avail.power_w:.0f}"
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

    # Solar winner: follow the smoothed surplus; the battery buffers around it.
    phases = _resolve_phases(avail.power_w, inp, cfg, state)
    amps = _clamp(
        _power_to_current(avail.power_w, phases, inp.voltage_v),
        cfg.min_current_a,
        cfg.max_current_a,
    )
    params = {"surplus": f"{avail.power_w:.0f}", "amps": f"{amps:.1f}"}
    if avail.eased:
        key = "solar_surplus_eased"
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
