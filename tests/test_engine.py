"""Unit tests for the pure regulation engine (strategies + arbiter).

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
PriceSlot = engine.PriceSlot
decide = engine.decide
compute_power_flow = engine.compute_power_flow

T0 = datetime(2026, 7, 4, 12, 0, tzinfo=timezone.utc)


def _inputs(**kw) -> "engine.ChargerInputs":
    base = dict(car_connected=True, phases=3, voltage_v=230.0, grid_power_w=0.0)
    base.update(kw)
    return ChargerInputs(**base)


def _cfg(**kw) -> "engine.EngineConfig":
    base = dict(
        mode=ChargingMode.SOLAR,
        smart_enabled=True,
        min_current_a=6.0,
        max_current_a=16.0,
        battery_reserve_soc=80.0,
    )
    base.update(kw)
    return EngineConfig(**base)


# --- Master gates ------------------------------------------------------------------

def test_smart_disabled_relinquishes_control():
    d = decide(_inputs(), _cfg(smart_enabled=False))
    assert d.control is False
    assert d.reason_key == "smart_disabled"


def test_manual_passive_keeps_hands_off():
    d = decide(
        _inputs(),
        _cfg(mode=ChargingMode.MANUAL, manual_passive=True, manual_charge=True),
    )
    assert d.control is False
    assert d.reason_key == "manual_passive"


def test_no_car_stops_and_resets_the_session():
    state = EngineState(charging=True, active_source="solar", ride_out_since=T0)
    d = decide(_inputs(car_connected=False), _cfg(), state)
    assert d.control is True
    assert d.should_charge is False
    assert d.reason_key == "no_car"
    assert state.charging is False
    assert state.active_source is None
    assert state.ride_out_since is None


# --- Manual mode --------------------------------------------------------------------

def test_manual_paused_controls_but_does_not_charge():
    d = decide(_inputs(), _cfg(mode=ChargingMode.MANUAL, manual_charge=False))
    assert d.control is True
    assert d.should_charge is False
    assert d.write_phases is True
    assert d.reason_key == "manual_paused"


def test_manual_charging_drives_the_requested_current_and_phases():
    d = decide(
        _inputs(grid_power_w=-12000.0, battery_soc=90.0),
        _cfg(
            mode=ChargingMode.MANUAL,
            manual_charge=True,
            manual_current_a=10.0,
            manual_phases=1,
        ),
    )
    assert d.should_charge is True
    assert d.target_current_a == 10.0
    assert d.target_phases == 1
    assert d.write_phases is True
    # 12 kW of export covers 10 A @ 1φ easily → not grid-assisted, no hold.
    assert d.hold_battery is False


def test_manual_grid_assisted_holds_the_battery():
    # 16 A @ 3φ ≈ 11 kW requested with no surplus at all → deliberate grid charge.
    d = decide(
        _inputs(grid_power_w=0.0, battery_soc=90.0),
        _cfg(mode=ChargingMode.MANUAL, manual_charge=True, manual_current_a=16.0),
    )
    assert d.should_charge is True
    assert d.hold_battery is True
    assert d.reason_key == "manual_charging"


def test_manual_guard_trims_when_battery_discharges_anyway():
    # Grid-assisted and the battery is bleeding 2.3 kW into the car (hold switch
    # missing/ineffective) → the guard trims the current by the discharge.
    d = decide(
        _inputs(battery_soc=90.0, battery_power_w=-2300.0),
        _cfg(mode=ChargingMode.MANUAL, manual_charge=True, manual_current_a=16.0),
    )
    assert d.hold_battery is True
    assert d.target_current_a < 16.0
    assert d.reason_key == "manual_charging_guarded"


# --- Solar surplus (availability + battery zones) ------------------------------------

def test_solar_surplus_follows_export():
    d = decide(_inputs(grid_power_w=-5000.0, battery_soc=90.0), _cfg())
    assert d.should_charge is True
    assert d.target_current_a == pytest.approx(5000.0 / (3 * 230.0), abs=0.01)
    assert d.hold_battery is False
    assert d.reason_key == "solar_surplus"


def test_solar_surplus_reclaims_car_draw():
    # The car's own 4.1 kW suppresses the export; it still counts as available.
    d = decide(
        _inputs(grid_power_w=-1000.0, car_actual_power_w=4140.0, battery_soc=90.0),
        _cfg(),
    )
    assert d.should_charge is True
    assert d.surplus_w == pytest.approx(5140.0)


def test_solar_clamped_to_max_current():
    d = decide(_inputs(grid_power_w=-20000.0, battery_soc=90.0), _cfg())
    assert d.target_current_a == 16.0


def test_below_min_surplus_waits():
    d = decide(_inputs(grid_power_w=-1000.0, battery_soc=90.0), _cfg())
    assert d.should_charge is False
    assert d.reason_key == "waiting_surplus"


def test_buffer_zone_reclaims_battery_charging_power():
    # At/above the reserve, solar flowing into the battery is available to the car.
    d = decide(
        _inputs(grid_power_w=-2000.0, battery_soc=85.0, battery_power_w=3000.0),
        _cfg(),
    )
    assert d.should_charge is True
    assert d.surplus_w == pytest.approx(5000.0)


def test_protect_zone_charges_only_genuine_excess():
    # Below the reserve the battery fills first — but export the battery can't
    # absorb (charge-limited) is genuine excess the car may use.
    d = decide(
        _inputs(grid_power_w=-5000.0, battery_soc=50.0, battery_power_w=2000.0),
        _cfg(),
    )
    assert d.should_charge is True
    assert d.surplus_w == pytest.approx(5000.0)  # no reclaim of the 2 kW


def test_protect_zone_deducts_discharge_immediately():
    # Below the reserve, battery power flowing into the car is not surplus.
    d = decide(
        _inputs(car_actual_power_w=4000.0, battery_soc=50.0, battery_power_w=-4000.0),
        _cfg(),
    )
    assert d.should_charge is False
    assert d.surplus_w == 0.0
    assert d.reason_key == "waiting_battery_reserve"


def test_unknown_soc_is_conservative():
    d = decide(
        _inputs(car_actual_power_w=4000.0, battery_power_w=-4000.0),
        _cfg(),
    )
    assert d.should_charge is False
    assert d.surplus_w == 0.0


def test_battery_bridges_a_short_dip():
    # 2 minutes of solid surplus, then a cloud: the battery covers the gap and
    # the car keeps charging near the smoothed level instead of chasing the dip.
    cfg = _cfg()
    state = EngineState()
    for i in range(8):  # 0…210 s: outlasts the 180 s confirmation window
        d = decide(
            _inputs(
                grid_power_w=-4000.0,
                battery_soc=90.0,
                battery_power_w=0.0,
                phases=1,
                now=T0 + timedelta(seconds=30 * i),
            ),
            cfg,
            state,
        )
    assert d.should_charge is True  # confirmed and charging by now
    # The dip: solar gone, the car's 4 kW rides on the battery.
    d = decide(
        _inputs(
            grid_power_w=0.0,
            car_actual_power_w=4000.0,
            battery_soc=90.0,
            battery_power_w=-4000.0,
            phases=1,
            now=T0 + timedelta(seconds=240),
        ),
        cfg,
        state,
    )
    assert d.should_charge is True
    assert d.target_current_a > cfg.min_current_a  # bridged, not slashed to 0


def test_sustained_discharge_eases_off():
    # Discharge beyond the tolerance for longer than the grace period switches
    # to the raw deduction and flags the ease-off.
    cfg = _cfg()
    state = EngineState(
        charging=True,  # mid-session, so no fresh start confirmation applies
        active_source="solar",
        avail_zone="buffer",
        discharge_high_since=T0 - timedelta(seconds=200),
    )
    d = decide(
        _inputs(
            grid_power_w=-2000.0,
            car_actual_power_w=4000.0,
            battery_soc=90.0,
            battery_power_w=-1000.0,
            phases=1,
            now=T0,
        ),
        cfg,
        state,
    )
    assert d.should_charge is True
    assert d.reason_key == "solar_surplus_eased"
    assert d.surplus_w == pytest.approx(5000.0)  # 2000 + 4000 − 1000 raw


# --- Start confirmation + ride-out ---------------------------------------------------

def test_solar_start_waits_for_the_confirmation_window():
    cfg = _cfg()
    state = EngineState()
    d = decide(
        _inputs(grid_power_w=-5000.0, battery_soc=90.0, now=T0), cfg, state
    )
    assert d.should_charge is False
    assert d.reason_key == "surplus_confirm"
    d = decide(
        _inputs(
            grid_power_w=-5000.0, battery_soc=90.0, now=T0 + timedelta(seconds=120)
        ),
        cfg,
        state,
    )
    assert d.should_charge is False  # still confirming
    d = decide(
        _inputs(
            grid_power_w=-5000.0, battery_soc=90.0, now=T0 + timedelta(seconds=185)
        ),
        cfg,
        state,
    )
    assert d.should_charge is True
    assert d.reason_key == "solar_surplus"


def test_surplus_dropout_resets_the_confirmation_window():
    cfg = _cfg()
    state = EngineState()
    decide(_inputs(grid_power_w=-5000.0, battery_soc=90.0, now=T0), cfg, state)
    # Full dropout at t+60 resets the window (raw dip drags the short average
    # below the minimum again).
    decide(
        _inputs(grid_power_w=0.0, battery_soc=90.0, now=T0 + timedelta(seconds=60)),
        cfg,
        state,
    )
    assert state.surplus_ok_since is None


def test_grid_strategies_start_without_confirmation():
    d = decide(
        _inputs(price_now=0.10, now=T0),
        _cfg(mode=ChargingMode.SMART, cheap_price=0.15),
        EngineState(),
    )
    assert d.should_charge is True
    assert d.reason_key == "cheap_grid"


def test_solar_dip_rides_out_then_stops():
    cfg = _cfg()
    state = EngineState(charging=True, active_source="solar")
    d = decide(_inputs(grid_power_w=0.0, battery_soc=90.0, now=T0), cfg, state)
    assert d.should_charge is True
    assert d.target_current_a == cfg.min_current_a
    assert d.reason_key == "surplus_ride_out"
    d = decide(
        _inputs(grid_power_w=0.0, battery_soc=90.0, now=T0 + timedelta(seconds=301)),
        cfg,
        state,
    )
    assert d.should_charge is False
    assert state.charging is False


def test_recovered_surplus_cancels_the_ride_out():
    cfg = _cfg()
    state = EngineState(charging=True, active_source="solar")
    decide(_inputs(grid_power_w=0.0, battery_soc=90.0, now=T0), cfg, state)
    d = decide(
        _inputs(
            grid_power_w=-11040.0, battery_soc=90.0, now=T0 + timedelta(seconds=60)
        ),
        cfg,
        state,
    )
    # Already charging → no fresh confirmation needed, ride-out cleared.
    assert d.should_charge is True
    assert state.ride_out_since is None


def test_grid_session_end_stops_without_ride_out():
    # A cheap hour ending is a deliberate stop: no minutes of expensive grid.
    state = EngineState(charging=True, active_source="grid")
    d = decide(
        _inputs(price_now=0.30, now=T0),
        _cfg(mode=ChargingMode.SMART, cheap_price=0.15),
        state,
    )
    assert d.should_charge is False
    assert state.charging is False


# --- Grid strategies (cheap / plan / fast / floor) -----------------------------------

def test_fast_charges_at_max_and_holds_the_battery():
    d = decide(_inputs(battery_soc=90.0), _cfg(mode=ChargingMode.FAST))
    assert d.should_charge is True
    assert d.target_current_a == 16.0
    assert d.hold_battery is True
    assert d.reason_key == "fast"


def test_cheap_grid_holds_battery_and_guards():
    d = decide(
        _inputs(price_now=0.10, battery_soc=90.0, battery_power_w=-2300.0),
        _cfg(mode=ChargingMode.SMART, cheap_price=0.15),
    )
    assert d.should_charge is True
    assert d.hold_battery is True
    assert d.target_current_a < 16.0
    assert d.reason_key == "cheap_grid_guarded"


def test_grid_beats_an_equal_solar_proposal():
    # Surplus can also deliver full power, but the cheap hour wins the tie so
    # the battery-hold stays engaged (stored energy beats cheap grid).
    d = decide(
        _inputs(grid_power_w=-20000.0, price_now=0.10, battery_soc=90.0),
        _cfg(mode=ChargingMode.SMART, cheap_price=0.15),
    )
    assert d.hold_battery is True
    assert d.reason_key == "cheap_grid"


def test_solar_beats_cheap_grid_when_it_offers_more():
    # 20 kW of export out-bids a cheap hour capped at 16 A? No — both cap at
    # max power. But with a *higher* solar cap unavailable, solar wins only when
    # cheap isn't active: expensive price → solar carries the session.
    d = decide(
        _inputs(grid_power_w=-8000.0, price_now=0.30, battery_soc=90.0),
        _cfg(mode=ChargingMode.SMART, cheap_price=0.15),
    )
    assert d.should_charge is True
    assert d.hold_battery is False
    assert d.reason_key == "solar_surplus"


def test_floor_tops_up_from_grid_and_holds():
    d = decide(
        _inputs(grid_power_w=0.0, battery_soc=50.0),
        _cfg(mode=ChargingMode.SOLAR_MIN),
    )
    assert d.should_charge is True
    assert d.target_current_a == 6.0
    assert d.hold_battery is True
    assert d.reason_key == "solar_min_topup"


def test_floor_yields_to_a_larger_surplus():
    d = decide(
        _inputs(grid_power_w=-8000.0, battery_soc=90.0),
        _cfg(mode=ChargingMode.SOLAR_MIN),
    )
    assert d.target_current_a == pytest.approx(8000.0 / 690.0, abs=0.01)
    assert d.hold_battery is False
    assert d.reason_key == "solar_surplus"


# --- The departure plan ---------------------------------------------------------------

def _forecast(prices: list[float], start: datetime) -> list[PriceSlot]:
    return [
        PriceSlot(start=start + timedelta(hours=i), price=p)
        for i, p in enumerate(prices)
    ]


def test_deadline_plan_charges_in_a_chosen_cheap_slot():
    # 20 kWh remaining at ~11 kW/slot → two slots needed → 0.05 and 0.10 chosen;
    # "now" sits in the 0.10 slot.
    d = decide(
        _inputs(
            price_now=0.10,
            price_forecast=_forecast([0.10, 0.30, 0.05, 0.40], T0),
            now=T0 + timedelta(minutes=30),
        ),
        _cfg(
            mode=ChargingMode.SMART,
            cheap_price=0.0,  # cheap-grid strategy out of the way
            target_energy_kwh=20.0,
            departure=T0 + timedelta(hours=4),
        ),
    )
    assert d.should_charge is True
    assert d.reason_key == "deadline_plan"
    assert d.reason_params["remaining"] == "20"


def test_deadline_plan_subtracts_delivered_energy():
    # Same picture, but 12 kWh already in the car → one slot suffices → only
    # the 0.05 slot is booked and "now" (0.10) waits.
    d = decide(
        _inputs(
            price_now=0.10,
            price_forecast=_forecast([0.10, 0.30, 0.05, 0.40], T0),
            session_delivered_kwh=12.0,
            now=T0 + timedelta(minutes=30),
        ),
        _cfg(
            mode=ChargingMode.SMART,
            cheap_price=0.0,
            target_energy_kwh=20.0,
            departure=T0 + timedelta(hours=4),
        ),
    )
    assert d.should_charge is False
    assert d.reason_key == "plan_waiting"


def test_deadline_capacity_uses_achievable_phases():
    # Locked to 1φ (auto-phase off) a slot only holds ~3.7 kWh, so 7 kWh needs
    # two slots — the plan must book the current 0.20 slot too. A 3φ assumption
    # would book only the 0.10 slot and miss the target.
    d = decide(
        _inputs(
            phases=1,
            price_now=0.20,
            price_forecast=_forecast([0.20, 0.10, 0.30], T0),
            now=T0 + timedelta(minutes=30),
        ),
        _cfg(
            mode=ChargingMode.SMART,
            cheap_price=0.0,
            target_energy_kwh=7.0,
            departure=T0 + timedelta(hours=3),
            auto_phase=False,
        ),
    )
    assert d.should_charge is True
    assert d.reason_key == "deadline_plan"
    assert d.target_phases == 1


def test_deadline_urgent_without_a_forecast():
    # 50 kWh owed, 2 hours left at ~11 kW → impossible to be picky: charge now.
    d = decide(
        _inputs(now=T0),
        _cfg(
            mode=ChargingMode.SMART,
            target_energy_kwh=50.0,
            departure=T0 + timedelta(hours=2),
        ),
    )
    assert d.should_charge is True
    assert d.reason_key == "deadline_urgent"
    assert d.hold_battery is True


def test_target_reached_reports_and_stops_grid_charging():
    d = decide(
        _inputs(
            price_forecast=_forecast([0.10, 0.30], T0),
            session_delivered_kwh=20.0,
            now=T0 + timedelta(minutes=30),
        ),
        _cfg(
            mode=ChargingMode.SMART,
            cheap_price=0.0,
            target_energy_kwh=20.0,
            departure=T0 + timedelta(hours=2),
        ),
    )
    assert d.should_charge is False
    assert d.reason_key == "target_reached"


def test_surplus_still_charges_beyond_the_target():
    # The target is a floor, not a cap: free solar keeps flowing afterwards.
    d = decide(
        _inputs(
            grid_power_w=-8000.0,
            battery_soc=90.0,
            session_delivered_kwh=25.0,
            now=None,  # confirmation bypassed for the stateless check
        ),
        _cfg(
            mode=ChargingMode.SMART,
            target_energy_kwh=20.0,
            departure=None,
        ),
    )
    assert d.should_charge is True
    assert d.reason_key == "solar_surplus"


# --- Phase resolution ------------------------------------------------------------------

def test_small_surplus_prefers_single_phase():
    d = decide(
        _inputs(grid_power_w=-2500.0, battery_soc=90.0),
        _cfg(auto_phase=True, max_phases=3),
        EngineState(),
    )
    assert d.target_phases == 1
    assert d.target_current_a == pytest.approx(2500.0 / 230.0, abs=0.01)


def test_large_surplus_climbs_to_three_phases():
    d = decide(
        _inputs(grid_power_w=-6000.0, battery_soc=90.0),
        _cfg(auto_phase=True, max_phases=3),
        EngineState(),
    )
    assert d.target_phases == 3


def test_phase_dwell_blocks_a_quick_toggle():
    state = EngineState(phases=1, phase_changed_at=T0 - timedelta(seconds=60))
    d = decide(
        _inputs(grid_power_w=-6000.0, battery_soc=90.0, now=T0),
        _cfg(auto_phase=True, max_phases=3, start_confirm_s=0.0),
        state,
    )
    assert d.target_phases == 1  # dwell not yet elapsed


def test_grid_charging_uses_full_phases_with_auto_phase():
    d = decide(
        _inputs(price_now=0.10, phases=1),
        _cfg(mode=ChargingMode.SMART, cheap_price=0.15, auto_phase=True, max_phases=3),
    )
    assert d.target_phases == 3


def test_auto_phase_off_leaves_phases_alone():
    d = decide(
        _inputs(grid_power_w=-8000.0, battery_soc=90.0, phases=3),
        _cfg(auto_phase=False),
    )
    assert d.target_phases == 3
    assert d.write_phases is False


# --- Modes & migration -------------------------------------------------------------------

def test_supported_modes_are_the_five_presets():
    assert set(engine.SUPPORTED_MODES) == {
        ChargingMode.SMART,
        ChargingMode.SOLAR,
        ChargingMode.SOLAR_MIN,
        ChargingMode.FAST,
        ChargingMode.MANUAL,
    }


def test_legacy_modes_map_onto_the_presets():
    legacy = engine.LEGACY_MODE_MAP
    assert legacy["off"] is ChargingMode.MANUAL
    assert legacy["pv_only"] is ChargingMode.SOLAR
    assert legacy["pv_minimum"] is ChargingMode.SOLAR_MIN
    for old in ("pv_price", "price", "combined"):
        assert legacy[old] is ChargingMode.SMART
    assert legacy["fast"] is ChargingMode.FAST
    assert all(new in engine.SUPPORTED_MODES for new in legacy.values())


def test_smart_without_pv_degrades_to_price_only():
    # No surplus signal at all: Smart still waits for its plan/cheap hours
    # rather than erroring or charging blindly.
    d = decide(
        _inputs(price_now=0.30),
        _cfg(mode=ChargingMode.SMART, cheap_price=0.15),
    )
    assert d.control is True
    assert d.should_charge is False


# --- Power flow (unchanged contract) -------------------------------------------------------

def test_power_flow_balances_the_home():
    flow = compute_power_flow(
        _inputs(
            grid_power_w=-2000.0,
            pv_power_w=8000.0,
            battery_power_w=1500.0,
            battery_soc=75.0,
            car_actual_power_w=3000.0,
        )
    )
    assert flow.pv_w == 8000.0
    assert flow.grid_w == -2000.0
    assert flow.car_w == 3000.0
    assert flow.house_w == pytest.approx(1500.0)  # 8000 − 2000 − 1500 − 3000
