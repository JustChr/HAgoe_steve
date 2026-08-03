"""Closed-loop scenario harness for the peak-protection layer.

Drives the *real* engine (custom_components/goe_steve/engine.py) against a small
house model: PV, house load, home battery (Victron-ESS-like, obeying the grid
setpoint / minimum-SoC / hold the engine writes) and the car. The grid reading the
engine sees on tick N is produced by the house reacting to the decision it made on
tick N-1 — so the guard is regulating a loop, not a fixture.
"""

from __future__ import annotations

import importlib.util
import math
import pathlib
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable

# Loaded by path, exactly as tests/test_engine.py does it, so the harness needs nothing
# installed beyond the standard library (aiohttp only for the recorder puller).
_ENGINE_PATH = (
    pathlib.Path(__file__).resolve().parents[2]
    / "custom_components" / "goe_steve" / "engine.py"
)
_spec = importlib.util.spec_from_file_location("goe_engine", _ENGINE_PATH)
engine = importlib.util.module_from_spec(_spec)
sys.modules["goe_engine"] = engine
_spec.loader.exec_module(engine)

ChargerInputs = engine.ChargerInputs
EngineConfig = engine.EngineConfig
EngineState = engine.EngineState
ChargingMode = engine.ChargingMode
decide = engine.decide

VIENNA = timezone(timedelta(hours=1))  # winter; summer scenarios use +2 explicitly
TICK_S = 10


# --- Weather / load profiles ---------------------------------------------------------

def clear_summer(t: float, start_h: float) -> float:
    """Bell curve, 9.8 kWp array, clear sky. ``t`` in seconds from scenario start."""
    hour = start_h + t / 3600.0
    x = (hour - 13.0) / 4.2
    return max(0.0, 9800.0 * math.exp(-x * x))


def broken_clouds(t: float, start_h: float) -> float:
    """Same array, cumulus: clear-sky value chopped by ~90 s cloud shadows."""
    base = clear_summer(t, start_h)
    phase = (t % 180.0) / 180.0
    return base * (0.18 if phase < 0.45 else 1.0)


def overcast_winter(t: float, start_h: float) -> float:
    hour = start_h + t / 3600.0
    x = (hour - 12.0) / 2.6
    return max(0.0, 900.0 * math.exp(-x * x))


def spring_hazy(t: float, start_h: float) -> float:
    hour = start_h + t / 3600.0
    x = (hour - 13.0) / 3.6
    wobble = 1.0 + 0.35 * math.sin(t / 220.0) + 0.15 * math.sin(t / 47.0)
    return max(0.0, 5200.0 * math.exp(-x * x) * wobble)


def night(t: float, start_h: float) -> float:
    return 0.0


def steady(w: float) -> Callable[[float], float]:
    return lambda t: w


def pulses(base: float, extra: float, on_s: float, period: float,
           first: float = 0.0) -> Callable[[float], float]:
    """A cycling appliance (heat pump, boiler): ``extra`` W for ``on_s`` every period."""
    def f(t: float) -> float:
        if t < first:
            return base
        return base + (extra if ((t - first) % period) < on_s else 0.0)
    return f


def steps(base: float, *changes: tuple[float, float]) -> Callable[[float], float]:
    """Load that steps to a new absolute value at each ``(t_seconds, watts)``."""
    def f(t: float) -> float:
        value = base
        for when, watts in changes:
            if t >= when:
                value = watts
        return value
    return f


# --- The house ----------------------------------------------------------------------

@dataclass
class House:
    soc: float = 60.0
    capacity_wh: float = 10000.0
    max_charge_w: float = 4500.0
    max_discharge_w: float = 4500.0  # a Multiplus-II 5000, continuous
    hard_floor_soc: float = 10.0  # the inverter's own cut-out
    # Round-trip efficiency, charged against the storing side. 1.0 keeps the older
    # scenarios exactly as they were; a strategy that cycles the battery hard has to
    # pay for it, so peak15 sets this from the measured charge/discharge gap.
    charge_eff: float = 1.0
    battery_w: float = 0.0
    grid_w: float = 0.0

    def step(self, pv_w: float, house_w: float, car_w: float, *,
             setpoint_w: float | None, min_soc: float | None, hold: bool,
             dt: float) -> None:
        """One physical tick: the ESS regulates the battery toward the setpoint."""
        target_grid = setpoint_w if setpoint_w is not None else 0.0
        floor = max(self.hard_floor_soc, min_soc if min_soc is not None else 10.0)
        deficit = house_w + car_w - pv_w  # what the grid+battery must jointly serve
        request = deficit - target_grid   # >0 → battery discharges, <0 → it charges

        if request > 0.0:
            if hold or self.soc <= floor:
                self.battery_w = 0.0
            else:
                self.battery_w = -min(request, self.max_discharge_w)
        else:
            headroom = 0.0 if self.soc >= 100.0 else self.max_charge_w
            self.battery_w = min(-request, headroom)

        self.grid_w = deficit + self.battery_w
        stored = self.battery_w * (self.charge_eff if self.battery_w > 0.0 else 1.0)
        self.soc = max(0.0, min(100.0, self.soc + stored * dt / 3600.0
                                / self.capacity_wh * 100.0))


# --- Scenario -----------------------------------------------------------------------

@dataclass
class Scenario:
    n: int
    title: str
    story: str
    duration_s: int
    cfg: EngineConfig
    pv: Callable[[float], float]
    house: Callable[[float], float]
    start: datetime
    soc0: float = 60.0
    car_connected: Callable[[float], bool] = lambda t: True
    external_car_w: Callable[[float], float] = lambda t: 0.0  # when control=False
    price: Callable[[float], float | None] = lambda t: None
    pv_forecast_kwh: float | None = None
    seed_month_peak_w: float = 0.0
    blackout: tuple[float, float] | None = None  # grid sensor unavailable window
    capacity_wh: float = 10000.0
    notes: str = ""
    expect: str = ""


@dataclass
class Result:
    scenario: Scenario
    events: list[str] = field(default_factory=list)
    windows: list[tuple[str, float, bool]] = field(default_factory=list)
    month_peak_w: float = 0.0
    max_projected_w: float = 0.0
    paused_s: float = 0.0
    shaved_s: float = 0.0
    min_soc_seen: float = 100.0
    car_kwh: float = 0.0
    tier_changes: int = 0
    frc_writes: int = 0     # start/stop flips sent to the charger
    amp_writes: int = 0     # current changes sent to the charger
    lever_writes: int = 0   # setpoint / min-SoC / hold changes sent to the house
    final_reason: str = ""
    final_peak_reason: str = ""


def run(sc: Scenario) -> Result:
    state = EngineState()
    if sc.seed_month_peak_w:
        state.month_peak_w = sc.seed_month_peak_w
        local = sc.start.astimezone(sc.cfg.local_tz or timezone.utc)
        state.month_key = f"{local.year:04d}-{local.month:02d}"
        state.month_peak_at = sc.start - timedelta(days=3)

    house = House(soc=sc.soc0, capacity_wh=sc.capacity_wh)
    res = Result(scenario=sc)

    car_w = 0.0
    setpoint_w: float | None = None
    min_soc: float | None = None
    hold = False
    prev_tier = "off"
    prev_amps = -1.0
    prev_charge: bool | None = None
    prev_window_start: datetime | None = None
    prev_limits: tuple[float, float, float] | None = None
    prev_levers: tuple | None = None
    decision = None

    for i in range(int(sc.duration_s / TICK_S) + 1):
        t = i * TICK_S
        now = sc.start + timedelta(seconds=t)
        pv_w = sc.pv(t)
        house_w = sc.house(t)
        connected = sc.car_connected(t)
        if not connected:
            car_w = 0.0

        house.step(pv_w, house_w, car_w, setpoint_w=setpoint_w, min_soc=min_soc,
                   hold=hold, dt=TICK_S)
        res.min_soc_seen = min(res.min_soc_seen, house.soc)
        res.car_kwh += car_w * TICK_S / 3600.0 / 1000.0

        blacked = (sc.blackout is not None
                   and sc.blackout[0] <= t < sc.blackout[1])
        grid_reading = None if blacked else house.grid_w

        if grid_reading is None:
            # Faithful to the coordinator: with no grid reading it never assembles a
            # snapshot at all. The window still advances (blind → degraded), the peak
            # status is attached to a hands-off decision, and nothing is written.
            window = engine.update_peak_window(now, None, sc.cfg, state)
            tier = engine.resolve_peak_tier(now, window, sc.cfg, state)
            decision = engine.attach_peak_status(
                engine.Decision(control=False, reason="Grid reading unavailable"),
                sc.cfg, state, window, tier,
            )
        else:
            inp = ChargerInputs(
                car_connected=connected,
                car_actual_power_w=car_w,
                phases=3,
                voltage_v=230.0,
                grid_power_w=grid_reading,
                pv_power_w=pv_w,
                battery_soc=house.soc,
                battery_power_w=house.battery_w,
                price_now=sc.price(t),
                pv_forecast_kwh=sc.pv_forecast_kwh,
                now=now,
            )
            decision = decide(inp, sc.cfg, state)

        # --- what the house does with the decision -----------------------------------
        if decision.house_control:
            setpoint_w = decision.grid_setpoint_w
            min_soc = decision.battery_min_soc
            hold = decision.hold_battery
        if decision.control:
            car_w = (decision.target_current_a * decision.target_phases * 230.0
                     if decision.should_charge else 0.0)
        else:
            car_w = sc.external_car_w(t) if connected else 0.0

        # --- event log ---------------------------------------------------------------
        stamp = f"{now.astimezone(sc.cfg.local_tz or timezone.utc):%H:%M:%S}"
        limits = (decision.peak_soft_w, decision.peak_target_w, decision.peak_hard_w)
        if prev_limits is not None and limits != prev_limits:
            res.events.append(
                f"  {stamp}  LIMITS IN FORCE {prev_limits[0]/1000:.2f}/"
                f"{prev_limits[1]/1000:.2f}/{prev_limits[2]/1000:.2f}"
                f" → {limits[0]/1000:.2f}/{limits[1]/1000:.2f}/{limits[2]/1000:.2f} kW"
                f"   (month record {decision.month_peak_w/1000:.2f} kW)"
            )
        prev_limits = limits
        levers = (decision.house_control, decision.grid_setpoint_w,
                  decision.battery_min_soc, decision.hold_battery, decision.hold_source)
        if prev_levers is not None and levers != prev_levers:
            res.events.append(
                f"  {stamp}  house levers: setpoint "
                f"{'—' if decision.grid_setpoint_w is None else f'{decision.grid_setpoint_w:.0f} W'}"
                f", min-SoC "
                f"{'—' if decision.battery_min_soc is None else f'{decision.battery_min_soc:.0f} %'}"
                f", hold {'on' if decision.hold_battery else 'off'}"
                f" ({decision.hold_source})"
                f"{'' if decision.house_control else '   [NOT WRITTEN — no house control]'}"
            )
        if prev_levers is not None and levers != prev_levers and decision.house_control:
            res.lever_writes += 1
        prev_levers = levers
        if decision.peak_tier != prev_tier:
            res.tier_changes += 1
            res.events.append(
                f"  {stamp}  tier {prev_tier} → {decision.peak_tier.upper()}"
                f"   (projected {decision.peak_projected_w/1000:.2f} kW,"
                f" limits {decision.peak_soft_w/1000:.1f}/"
                f"{decision.peak_target_w/1000:.1f}/"
                f"{decision.peak_hard_w/1000:.1f} kW)"
            )
            prev_tier = decision.peak_tier
        if decision.should_charge != prev_charge:
            res.events.append(
                f"  {stamp}  car {'START' if decision.should_charge else 'STOP '}"
                f"  {decision.target_current_a:.0f} A × {decision.target_phases}φ"
                f"   — {decision.reason}"
            )
            prev_charge = decision.should_charge
            prev_amps = decision.target_current_a
            res.frc_writes += 1
        elif decision.should_charge and abs(decision.target_current_a - prev_amps) >= 1.0:
            res.events.append(
                f"  {stamp}  car {decision.target_current_a:.0f} A"
                f" ({'trim' if decision.target_current_a < prev_amps else 'up'})"
                f"   soc {house.soc:.0f}%  grid {house.grid_w/1000:+.2f} kW"
            )
            prev_amps = decision.target_current_a
            res.amp_writes += 1
        if prev_window_start is not None and state.peak_window_start != prev_window_start:
            done = state.peak_history[-1] if state.peak_history else None
            if done:
                res.windows.append(
                    (f"{done[0].astimezone(sc.cfg.local_tz or timezone.utc):%H:%M}",
                     done[1], False)
                )
        prev_window_start = state.peak_window_start

        res.max_projected_w = max(res.max_projected_w, decision.peak_projected_w)
        if decision.peak_tier != "off":
            res.shaved_s += TICK_S
        if (decision.peak_reason_key == "peak_pause"):
            res.paused_s += TICK_S

    res.month_peak_w = state.month_peak_w
    res.final_reason = decision.reason if decision else ""
    res.final_peak_reason = decision.peak_reason if decision else ""
    return res
