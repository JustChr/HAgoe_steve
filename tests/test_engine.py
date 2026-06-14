"""Unit tests for the pure regulation engine.

The engine is HA-free, so we load it directly by file path — these tests run with
nothing more than ``pytest`` installed (no Home Assistant required)::

    pytest tests/test_engine.py
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
from datetime import datetime, timedelta, timezone

import pytest

_ENGINE_PATH = (
    pathlib.Path(__file__).resolve().parents[1]
    / "custom_components"
    / "goe_steve"
    / "engine.py"
)
_spec = importlib.util.spec_from_file_location("goe_engine", _ENGINE_PATH)
engine = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
# Register before exec so @dataclass(slots=True) can resolve the module namespace.
sys.modules[_spec.name] = engine
_spec.loader.exec_module(engine)

ChargerInputs = engine.ChargerInputs
EngineConfig = engine.EngineConfig
EngineState = engine.EngineState
ChargingMode = engine.ChargingMode
BatteryPolicy = engine.BatteryPolicy
PriceSlot = engine.PriceSlot
decide = engine.decide
compute_power_flow = engine.compute_power_flow


def _inputs(**kw) -> "engine.ChargerInputs":
    base = dict(car_connected=True, phases=3, voltage_v=230.0, grid_power_w=0.0)
    base.update(kw)
    return ChargerInputs(**base)


def _cfg(**kw) -> "engine.EngineConfig":
    base = dict(
        mode=ChargingMode.PV_ONLY,
        battery_policy=BatteryPolicy.PROTECT,
        smart_enabled=True,
        min_current_a=6.0,
        max_current_a=16.0,
        battery_reserve_soc=80.0,
        min_grid_floor_w=1400.0,
    )
    base.update(kw)
    return EngineConfig(**base)


def test_smart_disabled_relinquishes_control():
    d = decide(_inputs(), _cfg(smart_enabled=False))
    assert d.control is False


def test_off_mode_is_passthrough():
    d = decide(_inputs(), _cfg(mode=ChargingMode.OFF))
    assert d.control is False


def test_no_car_does_not_charge_but_controls():
    d = decide(_inputs(car_connected=False), _cfg())
    assert d.control is True
    assert d.should_charge is False


def test_fast_uses_max_current():
    d = decide(_inputs(), _cfg(mode=ChargingMode.FAST))
    assert d.should_charge is True
    assert d.target_current_a == 16.0


def test_pv_only_charges_on_surplus():
    # 5000 W export, 3-phase @230 V → ~7.2 A
    d = decide(_inputs(grid_power_w=-5000.0), _cfg(mode=ChargingMode.PV_ONLY))
    assert d.should_charge is True
    assert d.target_current_a == pytest.approx(5000 / (3 * 230), abs=0.1)


def test_pv_only_pauses_below_min_current():
    # 1000 W export → ~1.4 A, below the 6 A floor
    d = decide(_inputs(grid_power_w=-1000.0), _cfg(mode=ChargingMode.PV_ONLY))
    assert d.should_charge is False
    assert "Waiting" in d.reason


def test_pv_only_adds_back_car_draw():
    # Grid balanced but car already pulling 4140 W (6 A @3ph) → true surplus 4140 W
    d = decide(
        _inputs(grid_power_w=0.0, car_actual_power_w=4140.0),
        _cfg(mode=ChargingMode.PV_ONLY),
    )
    assert d.should_charge is True
    assert d.surplus_w == pytest.approx(4140.0, abs=1.0)


def test_pv_only_clamps_to_max_current():
    d = decide(_inputs(grid_power_w=-20000.0), _cfg(mode=ChargingMode.PV_ONLY))
    assert d.target_current_a == 16.0


def test_protect_holds_car_until_battery_reserve():
    # Big surplus, but home battery at 50% < reserve 80% → car waits
    d = decide(
        _inputs(grid_power_w=-6000.0, battery_soc=50.0),
        _cfg(mode=ChargingMode.PV_ONLY, battery_reserve_soc=80.0),
    )
    assert d.should_charge is False
    assert "battery" in d.reason.lower()


def test_protect_releases_above_reserve():
    d = decide(
        _inputs(grid_power_w=-6000.0, battery_soc=85.0),
        _cfg(mode=ChargingMode.PV_ONLY, battery_reserve_soc=80.0),
    )
    assert d.should_charge is True


def test_pv_minimum_tops_up_from_grid():
    # Only 500 W surplus, but PV+minimum guarantees at least the floor current
    d = decide(
        _inputs(grid_power_w=-500.0),
        _cfg(mode=ChargingMode.PV_MINIMUM, min_grid_floor_w=1400.0),
    )
    assert d.should_charge is True
    assert d.target_current_a >= 6.0


# --- Phase 2: battery policies --------------------------------------------------

def test_share_reclaims_battery_charge_power():
    # Grid balanced, but 5000 W is flowing into the home battery → Share lets the
    # car take it (above the 4140 W three-phase floor) instead of holding.
    d = decide(
        _inputs(grid_power_w=0.0, battery_power_w=5000.0, battery_soc=50.0),
        _cfg(mode=ChargingMode.PV_ONLY, battery_policy=BatteryPolicy.SHARE),
    )
    assert d.should_charge is True
    assert d.surplus_w == pytest.approx(5000.0, abs=1.0)


def test_share_does_not_hold_below_reserve():
    d = decide(
        _inputs(grid_power_w=-6000.0, battery_soc=30.0),
        _cfg(mode=ChargingMode.PV_ONLY, battery_policy=BatteryPolicy.SHARE),
    )
    assert d.should_charge is True


def test_assist_charges_from_battery_above_floor():
    # No surplus at all, but battery is well above the floor → Assist still charges.
    d = decide(
        _inputs(grid_power_w=0.0, battery_soc=60.0),
        _cfg(
            mode=ChargingMode.PV_ONLY,
            battery_policy=BatteryPolicy.ASSIST,
            battery_floor_soc=20.0,
        ),
    )
    assert d.should_charge is True


def test_assist_stops_at_floor():
    d = decide(
        _inputs(grid_power_w=0.0, battery_soc=15.0),
        _cfg(
            mode=ChargingMode.PV_ONLY,
            battery_policy=BatteryPolicy.ASSIST,
            battery_floor_soc=20.0,
        ),
    )
    assert d.should_charge is False


# --- Phase 2: price modes -------------------------------------------------------

def test_pv_price_full_power_when_cheap():
    d = decide(
        _inputs(grid_power_w=0.0, price_now=0.08),
        _cfg(mode=ChargingMode.PV_PRICE, cheap_price=0.15),
    )
    assert d.should_charge is True
    assert d.target_current_a == 16.0
    assert "Cheap grid" in d.reason


def test_pv_price_falls_back_to_solar_when_expensive():
    # Expensive grid → behaves like PV-only; tiny surplus means it waits.
    d = decide(
        _inputs(grid_power_w=-500.0, price_now=0.40),
        _cfg(mode=ChargingMode.PV_PRICE, cheap_price=0.15),
    )
    assert d.should_charge is False
    assert "Waiting" in d.reason


def test_cheap_grid_protect_trims_to_avoid_battery_drain():
    # Cheap grid wants full 16 A, but the home battery is discharging 3000 W to
    # cover the car → PROTECT trims that off so the grid carries it instead.
    # 3000 W / (3·230) ≈ 4.35 A trimmed from 16 A → ~11.65 A.
    d = decide(
        _inputs(grid_power_w=0.0, price_now=0.05, battery_power_w=-3000.0),
        _cfg(mode=ChargingMode.PV_PRICE, cheap_price=0.15, battery_policy=BatteryPolicy.PROTECT),
    )
    assert d.should_charge is True
    assert d.target_current_a == pytest.approx(16.0 - 3000 / (3 * 230), abs=0.1)
    assert "battery" in d.reason.lower()


def test_cheap_grid_share_also_protects_battery():
    d = decide(
        _inputs(grid_power_w=0.0, price_now=0.05, battery_power_w=-2000.0),
        _cfg(mode=ChargingMode.PV_PRICE, cheap_price=0.15, battery_policy=BatteryPolicy.SHARE),
    )
    assert d.target_current_a < 16.0


def test_cheap_grid_assist_allows_full_power():
    # ASSIST opts out of the guard — it may back the car from the battery.
    d = decide(
        _inputs(grid_power_w=0.0, price_now=0.05, battery_power_w=-3000.0),
        _cfg(mode=ChargingMode.PV_PRICE, cheap_price=0.15, battery_policy=BatteryPolicy.ASSIST),
    )
    assert d.target_current_a == 16.0


def test_cheap_grid_ignores_small_battery_noise():
    # A trickle of discharge (≤ tolerance) should not trim the current.
    d = decide(
        _inputs(grid_power_w=0.0, price_now=0.05, battery_power_w=-50.0),
        _cfg(mode=ChargingMode.PV_PRICE, cheap_price=0.15, battery_policy=BatteryPolicy.PROTECT),
    )
    assert d.target_current_a == 16.0


def test_cheap_grid_guard_floors_at_min_current():
    # Huge discharge would trim below the EV floor → clamp to min_current_a.
    d = decide(
        _inputs(grid_power_w=0.0, price_now=0.05, battery_power_w=-15000.0),
        _cfg(mode=ChargingMode.PV_PRICE, cheap_price=0.15, battery_policy=BatteryPolicy.PROTECT),
    )
    assert d.target_current_a == 6.0


def _forecast(now, prices):
    return [
        PriceSlot(start=now + timedelta(hours=i), price=p)
        for i, p in enumerate(prices)
    ]


def test_price_mode_charges_in_cheapest_slot():
    now = datetime(2026, 6, 14, 20, 0, tzinfo=timezone.utc)
    # Cheapest hour is right now (0.05); target needs only ~1 slot.
    fc = _forecast(now, [0.05, 0.30, 0.30, 0.30])
    d = decide(
        _inputs(now=now, price_forecast=fc, price_now=0.05),
        _cfg(
            mode=ChargingMode.PRICE,
            target_energy_kwh=5.0,
            departure=now + timedelta(hours=4),
            max_current_a=16.0,
        ),
    )
    assert d.should_charge is True
    assert "Cheap-hours" in d.reason


def test_price_mode_waits_in_expensive_slot():
    now = datetime(2026, 6, 14, 20, 0, tzinfo=timezone.utc)
    # Now is the most expensive hour; a cheaper one comes later.
    fc = _forecast(now, [0.40, 0.05, 0.10, 0.10])
    d = decide(
        _inputs(now=now, price_forecast=fc, price_now=0.40),
        _cfg(
            mode=ChargingMode.PRICE,
            target_energy_kwh=5.0,
            departure=now + timedelta(hours=4),
        ),
    )
    assert d.should_charge is False


def test_combined_uses_cheap_grid():
    now = datetime(2026, 6, 14, 20, 0, tzinfo=timezone.utc)
    d = decide(
        _inputs(grid_power_w=0.0, price_now=0.05, now=now),
        _cfg(mode=ChargingMode.COMBINED, cheap_price=0.15),
    )
    assert d.should_charge is True
    assert d.target_current_a == 16.0


# --- Phase 2: phase switching ---------------------------------------------------

def test_auto_phase_drops_to_single_on_small_surplus():
    state = EngineState(phases=3)
    now = datetime(2026, 6, 14, 12, 0, tzinfo=timezone.utc)
    # ~2500 W: below 1-phase max (16 A·230 = 3680 W) → switch down to 1 phase.
    d = decide(
        _inputs(grid_power_w=-2500.0, now=now),
        _cfg(mode=ChargingMode.PV_ONLY, auto_phase=True, max_phases=3),
        state,
    )
    assert d.target_phases == 1
    assert d.should_charge is True


def test_auto_phase_dwell_blocks_rapid_switch():
    now = datetime(2026, 6, 14, 12, 0, tzinfo=timezone.utc)
    state = EngineState(phases=1, phase_changed_at=now)
    # Big surplus would warrant 3 phases, but the dwell timer hasn't elapsed.
    d = decide(
        _inputs(grid_power_w=-8000.0, now=now + timedelta(seconds=30)),
        _cfg(
            mode=ChargingMode.PV_ONLY,
            auto_phase=True,
            max_phases=3,
            phase_dwell_s=300.0,
        ),
        state,
    )
    assert d.target_phases == 1


def test_auto_phase_switches_up_after_dwell():
    now = datetime(2026, 6, 14, 12, 0, tzinfo=timezone.utc)
    state = EngineState(phases=1, phase_changed_at=now)
    d = decide(
        _inputs(grid_power_w=-8000.0, now=now + timedelta(seconds=600)),
        _cfg(
            mode=ChargingMode.PV_ONLY,
            auto_phase=True,
            max_phases=3,
            phase_dwell_s=300.0,
        ),
        state,
    )
    assert d.target_phases == 3


# --- Phase 2: anti-flap dwell ---------------------------------------------------

def test_min_off_dwell_holds_paused():
    now = datetime(2026, 6, 14, 12, 0, tzinfo=timezone.utc)
    # Was paused 10 s ago; surplus now justifies charging but off-dwell is 120 s.
    state = EngineState(charging=False, charge_changed_at=now)
    d = decide(
        _inputs(grid_power_w=-6000.0, now=now + timedelta(seconds=10)),
        _cfg(mode=ChargingMode.PV_ONLY, min_off_dwell_s=120.0),
        state,
    )
    assert d.should_charge is False
    assert "dwell" in d.reason.lower()


def test_unimplemented_mode_still_safe_by_default():
    # A bare Decision for an unknown enum value should never charge silently;
    # here we confirm Combined with no inputs simply doesn't charge.
    d = decide(_inputs(grid_power_w=0.0), _cfg(mode=ChargingMode.COMBINED))
    assert d.should_charge is False


# --- Phase 4: power-flow derivation for the card --------------------------------

def test_power_flow_solar_charging_no_battery():
    # 5 kW PV, exporting 1 kW, car taking 3 kW, no battery → house = 1 kW.
    flow = compute_power_flow(
        _inputs(pv_power_w=5000.0, grid_power_w=-1000.0, car_actual_power_w=3000.0)
    )
    assert flow.pv_w == 5000.0
    assert flow.battery_w is None
    assert flow.car_w == 3000.0
    assert flow.house_w == pytest.approx(1000.0)


def test_power_flow_battery_discharge_counts_as_input():
    # No PV, importing 200 W, battery discharging 2 kW, car off → house = 2.2 kW.
    flow = compute_power_flow(
        _inputs(
            pv_power_w=0.0,
            grid_power_w=200.0,
            battery_power_w=-2000.0,
            car_actual_power_w=0.0,
        )
    )
    assert flow.house_w == pytest.approx(2200.0)


def test_power_flow_house_never_negative():
    flow = compute_power_flow(
        _inputs(pv_power_w=4000.0, grid_power_w=-3900.0, car_actual_power_w=0.0)
    )
    assert flow.house_w == pytest.approx(100.0)
    # Pathological over-export shouldn't push house below zero.
    flow2 = compute_power_flow(
        _inputs(pv_power_w=1000.0, grid_power_w=-5000.0, car_actual_power_w=0.0)
    )
    assert flow2.house_w == 0.0
