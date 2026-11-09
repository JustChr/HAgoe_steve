"""Unit tests for the pure regulation engine (strategies + arbiter).

The engine is HA-free, so we load it directly by file path — these tests run with
nothing more than ``pytest`` installed (no Home Assistant required)::

    pytest tests/test_engine.py
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
from dataclasses import replace
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
        _inputs(battery_soc=90.0, battery_power_w=-2300.0, car_actual_power_w=11000.0),
        _cfg(mode=ChargingMode.MANUAL, manual_charge=True, manual_current_a=16.0),
    )
    assert d.hold_battery is True
    assert d.target_current_a < 16.0
    assert d.reason_key == "manual_charging_guarded"


def test_guard_ignores_the_house_discharge_while_the_car_takes_nothing():
    # A full car stays plugged in: the battery discharging for the house is not the
    # car's, and trimming by it moved the current with every house load (live, Nov
    # 2026: 7↔8 A every few seconds, 37 amp writes a quarter-hour).
    for discharge in (-1497.0, -1761.0, -1570.0, -1655.0):
        d = decide(
            _inputs(battery_soc=89.0, battery_power_w=discharge, car_actual_power_w=0.0),
            _cfg(mode=ChargingMode.MANUAL, manual_charge=True, manual_current_a=16.0),
        )
        assert d.target_current_a == 16.0


def test_guard_trims_no_more_than_the_car_draws():
    # 3 kW out of the battery, 1.4 kW of it into the car: only the car's share is
    # the car's to give back.
    d = decide(
        _inputs(battery_soc=90.0, battery_power_w=-3000.0, car_actual_power_w=1380.0,
                phases=1),
        _cfg(mode=ChargingMode.MANUAL, manual_charge=True, manual_current_a=16.0,
             manual_phases=1),
    )
    assert d.target_current_a == 10.0  # 16 A − 1380 W / 230 V = 10 A


# --- Solar surplus (availability + battery zones) ------------------------------------

def test_solar_surplus_follows_export():
    # 5 kW over three phases is 7.2 A; the charger takes whole amps, and inside
    # the buffer zone but below the midpoint the snap is downwards.
    d = decide(_inputs(grid_power_w=-5000.0, battery_soc=85.0), _cfg())
    assert d.should_charge is True
    assert d.target_current_a == 7.0
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


def test_protect_zone_ignores_the_cars_own_draw():
    # A car already pulling 4 kW of solar, no grid export (the car eats it all),
    # battery flat and below the reserve: that draw would fill the battery if the
    # car let go, so it is NOT available surplus. Raising the reserve above the
    # SoC must therefore stop the charge, not keep it running on its own draw.
    d = decide(
        _inputs(car_actual_power_w=4000.0, battery_soc=50.0, battery_power_w=0.0),
        _cfg(),
    )
    assert d.should_charge is False
    assert d.surplus_w == 0.0
    assert d.reason_key == "waiting_battery_reserve"


def test_raising_reserve_above_soc_stops_an_active_solar_charge():
    # Mirrors the reported bug: mid-session, charging on 4 kW of solar the car is
    # fully consuming (grid ~0), then the reserve is lifted above the SoC. After
    # the ride-out window the charge stops so the battery can fill.
    cfg = _cfg()
    state = EngineState(charging=True, active_source="solar", avail_zone="buffer")
    stop_at = T0 + timedelta(seconds=cfg.stop_ride_out_s + 1)
    for now in (T0, stop_at):
        d = decide(
            _inputs(
                car_actual_power_w=4000.0,
                grid_power_w=0.0,
                battery_soc=50.0,
                battery_power_w=0.0,
                phases=1,
                now=now,
            ),
            cfg,
            state,
        )
    assert d.should_charge is False
    assert d.reason_key == "waiting_battery_reserve"


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


def test_current_tracks_a_drop_quickly():
    # A fading surplus reaches the amps within tens of seconds, not minutes.
    cfg = _cfg()
    state = EngineState(charging=True, active_source="solar", avail_zone="buffer")
    decide(
        _inputs(grid_power_w=-6000.0, battery_soc=90.0, phases=1, now=T0), cfg, state
    )
    d = decide(
        _inputs(
            grid_power_w=-1000.0,
            battery_soc=90.0,
            phases=1,
            now=T0 + timedelta(seconds=30),
        ),
        cfg,
        state,
    )
    # 5 s tracking tau, 30 s step: 6000 + (1-e^-6)(1000-6000) ≈ 1012 W — essentially
    # all the way down, where a plain 2-sample average would still read 3500 W.
    assert d.surplus_w == pytest.approx(1012.0, abs=5.0)
    assert d.target_current_a == cfg.min_current_a  # 1 kW at 1φ is below the floor


def test_current_climbs_quickly_on_a_rise():
    # …and a returning surplus is used while it lasts instead of being eased in
    # over several minutes.
    cfg = _cfg()
    state = EngineState(charging=True, active_source="solar", avail_zone="buffer")
    decide(
        _inputs(grid_power_w=-2000.0, battery_soc=90.0, phases=1, now=T0), cfg, state
    )
    d = decide(
        _inputs(
            grid_power_w=-8000.0,
            battery_soc=90.0,
            phases=1,
            now=T0 + timedelta(seconds=30),
        ),
        cfg,
        state,
    )
    # 12 s tracking tau, 30 s step: 2000 + (1-e^-2.5)(8000-2000) ≈ 7507 W, versus
    # the 3327 W the calm commitment filter is still sitting at.
    assert d.surplus_w == pytest.approx(7507.0, abs=5.0)


def test_a_short_dip_moves_the_amps_but_not_the_charging_state():
    # The point of the two speeds: the current follows the dip immediately while
    # the decision to keep charging stays with the calm signal.
    cfg = _cfg()
    state = EngineState(charging=True, active_source="solar", avail_zone="buffer")
    decide(
        _inputs(
            grid_power_w=-6000.0,
            battery_soc=85.0,
            battery_power_w=0.0,
            phases=1,
            now=T0,
        ),
        cfg,
        state,
    )
    d = decide(
        _inputs(
            grid_power_w=0.0,
            battery_soc=85.0,
            battery_power_w=0.0,
            phases=1,
            now=T0 + timedelta(seconds=5),
        ),
        cfg,
        state,
    )
    assert d.should_charge is True
    assert d.reason_key == "solar_surplus"
    assert state.ride_out_since is None  # no stop is being contemplated
    # Five seconds into the dip the amps are already well down from the 16 A cap
    # (6000·e^-1 ≈ 2207 W → 9.6 A → 9 A), while the commitment signal is still at
    # ≈ 4673 W.
    assert d.target_current_a == 9.0


def test_ride_out_follows_a_recovering_surplus():
    # Mid ride-out the commitment signal still says "stop soon", but the surplus
    # is back — the amps go with it instead of sitting at the minimum.
    cfg = _cfg()
    state = EngineState(
        charging=True,
        active_source="solar",
        avail_zone="buffer",
        ride_out_since=T0,
        avail_output=200.0,
        track_output=200.0,
        avail_sample_t=T0,
    )
    d = decide(
        _inputs(
            grid_power_w=-8000.0,
            battery_soc=85.0,
            phases=3,
            now=T0 + timedelta(seconds=30),
        ),
        cfg,
        state,
    )
    assert d.reason_key == "surplus_ride_out"  # commitment signal not convinced yet
    assert d.target_current_a > cfg.min_current_a
    assert d.target_current_a == 10.0  # 7360 W over three phases is 10.7 A


def test_battery_penalty_releases_once_the_dip_is_over():
    # A battery that has stopped discharging must stop holding the current down.
    cfg = _cfg()
    state = EngineState(charging=True, active_source="solar", avail_zone="buffer")
    decide(
        _inputs(
            grid_power_w=-4000.0, battery_soc=90.0, battery_power_w=0.0,
            phases=1, now=T0,
        ),
        cfg,
        state,
    )
    decide(  # the dip: the car's 4 kW rides on the battery
        _inputs(
            grid_power_w=0.0, car_actual_power_w=4000.0, battery_soc=90.0,
            battery_power_w=-4000.0, phases=1, now=T0 + timedelta(seconds=30),
        ),
        cfg,
        state,
    )
    d = decide(  # …and it's over: sun back, battery idle
        _inputs(
            grid_power_w=-4000.0, car_actual_power_w=4000.0, battery_soc=90.0,
            battery_power_w=0.0, phases=1, now=T0 + timedelta(seconds=60),
        ),
        cfg,
        state,
    )
    # Penalty after one 30 s release step: 884 W · e^(-30/40) ≈ 418 W, off a
    # tracked base of ≈ 7672 W. A symmetric 120 s average would still deduct
    # ≈ 1333 W here.
    assert d.surplus_w == pytest.approx(7254.0, abs=10.0)


# --- Rounding direction: which side of the surplus we land on --------------------------

def test_generous_rounding_takes_the_last_amp_from_the_battery():
    # Comfortably above the reserve (80 % → generous from 90 %), the 7.2 A of
    # surplus become 8 A: the last 520 W come out of the home battery instead of
    # being exported.
    d = decide(_inputs(grid_power_w=-5000.0, battery_soc=95.0), _cfg())
    assert d.target_current_a == 8.0
    assert d.reason_key == "solar_surplus_battery_topup"
    assert d.reason_params["gap"] == "520"  # 8 A · 3φ · 230 V − 5000 W


def test_conservative_rounding_stays_below_the_surplus():
    # Same surplus, battery only just inside the buffer zone: the remainder is
    # exported rather than borrowed.
    d = decide(_inputs(grid_power_w=-5000.0, battery_soc=85.0), _cfg())
    assert d.target_current_a == 7.0
    assert d.reason_key == "solar_surplus"


def test_generous_rounding_never_exceeds_the_max_current():
    d = decide(_inputs(grid_power_w=-20000.0, battery_soc=95.0), _cfg())
    assert d.target_current_a == 16.0


def test_reserve_at_100_never_rounds_up():
    # "Keep the battery at 100 %" means it even when the battery is full: the
    # leftover is exported, never taken back out of the battery.
    d = decide(
        _inputs(grid_power_w=-5000.0, battery_soc=100.0),
        _cfg(battery_reserve_soc=100.0),
    )
    assert d.should_charge is True
    assert d.target_current_a == 7.0
    assert d.reason_key == "solar_surplus"


def test_generous_rounding_holds_through_a_small_soc_dip():
    # Rounding up nudges the SoC back down across the very threshold that enabled
    # it, so leaving the zone takes a few points more than entering it.
    cfg = _cfg()
    state = EngineState()
    decide(_inputs(grid_power_w=-5000.0, battery_soc=90.0), cfg, state)
    assert state.generous is True
    decide(_inputs(grid_power_w=-5000.0, battery_soc=88.0), cfg, state)
    assert state.generous is True  # still inside the exit margin
    decide(_inputs(grid_power_w=-5000.0, battery_soc=86.0), cfg, state)
    assert state.generous is False


def test_the_borrowed_amp_is_not_treated_as_a_sustained_drain():
    # One amp step of discharge is our own doing while rounding up (~690 W at 3φ),
    # so the ease-off correction must not fire on it — otherwise every generous
    # charge would permanently report "easing off home battery".
    cfg = _cfg()
    common = dict(
        grid_power_w=0.0,
        car_actual_power_w=5520.0,
        battery_power_w=-600.0,
        phases=3,
        now=T0,
    )
    generous = EngineState(
        charging=True,
        active_source="solar",
        avail_zone="buffer",
        generous=True,
        discharge_high_since=T0 - timedelta(seconds=200),
    )
    d = decide(_inputs(battery_soc=95.0, **common), cfg, generous)
    assert d.reason_key == "solar_surplus_battery_topup"

    # Below the midpoint the same 600 W is nobody's plan, and is corrected.
    plain = EngineState(
        charging=True,
        active_source="solar",
        avail_zone="buffer",
        discharge_high_since=T0 - timedelta(seconds=200),
    )
    d = decide(_inputs(battery_soc=85.0, **common), cfg, plain)
    assert d.reason_key == "solar_surplus_eased"


# --- Start confirmation + ride-out ---------------------------------------------------

def test_solar_start_waits_for_the_confirmation_window():
    cfg = _cfg()
    state = EngineState()
    d = decide(
        _inputs(grid_power_w=-5000.0, battery_soc=85.0, now=T0), cfg, state
    )
    assert d.should_charge is False
    assert d.reason_key == "surplus_confirm"
    d = decide(
        _inputs(
            grid_power_w=-5000.0, battery_soc=85.0, now=T0 + timedelta(seconds=120)
        ),
        cfg,
        state,
    )
    assert d.should_charge is False  # still confirming
    d = decide(
        _inputs(
            grid_power_w=-5000.0, battery_soc=85.0, now=T0 + timedelta(seconds=185)
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


def test_start_now_skips_the_confirmation_window():
    cfg = _cfg()
    state = EngineState()
    d = decide(_inputs(grid_power_w=-5000.0, battery_soc=85.0, now=T0), cfg, state)
    assert d.should_charge is False
    assert d.reason_key == "surplus_confirm"

    state.start_override = True  # the user taps the countdown / presses the button
    d = decide(
        _inputs(grid_power_w=-5000.0, battery_soc=85.0, now=T0 + timedelta(seconds=5)),
        cfg,
        state,
    )
    assert d.should_charge is True
    assert d.reason_key == "solar_surplus"
    assert state.start_override is False  # one-shot, not a standing permission


def test_start_now_cannot_conjure_a_surplus():
    # It skips the waiting, not the condition: with no surplus there is nothing
    # to start, and the request is consumed rather than left lying around.
    state = EngineState(start_override=True)
    d = decide(_inputs(grid_power_w=-500.0, battery_soc=85.0, now=T0), _cfg(), state)
    assert d.should_charge is False
    assert d.reason_key == "waiting_surplus"
    assert state.start_override is False


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


def _run_idle_car(cfg, seconds, power_w=0.0, state=None):
    """Replay ``seconds`` of a plugged-in car drawing ``power_w``, 20 s per cycle."""
    state = state if state is not None else EngineState()
    d = None
    for t in range(0, seconds + 1, 20):
        d = decide(
            _inputs(battery_soc=90.0, car_actual_power_w=power_w,
                    now=T0 + timedelta(seconds=t)),
            cfg,
            state,
        )
    return d, state


def test_a_full_car_hands_the_battery_back():
    # Full power into a car that takes nothing: the hold has nothing left to protect.
    d, _ = _run_idle_car(_cfg(mode=ChargingMode.FAST), 200)
    assert d.should_charge is True  # the car may still start a top-up
    assert d.hold_battery is False
    assert d.reason_key == "car_not_drawing"


def test_a_car_that_is_still_ramping_keeps_the_hold():
    d, _ = _run_idle_car(_cfg(mode=ChargingMode.FAST), 120)
    assert d.hold_battery is True
    assert d.reason_key == "fast"


def test_the_hold_returns_the_moment_the_car_draws_again():
    cfg = _cfg(mode=ChargingMode.FAST)
    _, state = _run_idle_car(cfg, 200)
    d = decide(
        _inputs(battery_soc=90.0, car_actual_power_w=11000.0,
                now=T0 + timedelta(seconds=220)),
        cfg,
        state,
    )
    assert d.hold_battery is True
    assert state.car_idle_since is None


def test_a_full_car_in_manual_hands_the_battery_back_too():
    d, _ = _run_idle_car(
        _cfg(mode=ChargingMode.MANUAL, manual_charge=True, manual_current_a=16.0), 200
    )
    assert d.hold_battery is False
    assert d.reason_key == "car_not_drawing"


def test_an_explicit_hold_stays_on_for_a_full_car():
    d, _ = _run_idle_car(_cfg(mode=ChargingMode.FAST, battery_hold_mode="hold"), 200)
    assert d.hold_battery is True
    assert d.hold_source == "hold"


def test_cheap_grid_holds_battery_and_guards():
    d = decide(
        _inputs(
            price_now=0.10, battery_soc=90.0, battery_power_w=-2300.0,
            car_actual_power_w=11000.0,
        ),
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
        _inputs(grid_power_w=-8000.0, price_now=0.30, battery_soc=85.0),
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


def test_floor_names_the_home_battery_when_it_is_the_one_topping_up():
    # A real snapshot: Solar + minimum at a 16 A floor, home battery "free", sun
    # a few hundred watts short. Nothing is being imported — the grid is even
    # exporting a little — and the battery covers the shortfall. The status line
    # used to say "topping up from grid" flat out, contradicting the source bar
    # drawn right underneath it, which correctly showed no grid share at all.
    inp = _inputs(
        phases=1,
        pv_power_w=4531.0,
        grid_power_w=-44.0,
        battery_power_w=-325.0,
        battery_soc=86.0,
        car_actual_power_w=3429.0,
    )
    cfg = _cfg(
        mode=ChargingMode.SOLAR_MIN,
        min_current_a=16.0,
        max_current_a=16.0,
        battery_hold_mode="free",
        auto_phase=False,
    )
    d = decide(inp, cfg, EngineState(charging=True, active_source="grid"))
    assert d.should_charge is True
    assert d.target_current_a == 16.0
    assert d.hold_battery is False
    assert d.reason_key == "solar_min_topup_battery"
    assert "home battery" in d.reason
    # …and the sentence agrees with the bar the card draws below it.
    split = engine.compute_car_sources(compute_power_flow(inp))
    assert split.grid_w == 0.0
    assert split.battery_w > 0.0


def test_floor_still_names_the_grid_when_the_battery_is_held():
    # Same shortfall, but the battery is held (the default): now the grid really
    # does pay for the top-up, and the reason has to say so.
    inp = _inputs(
        phases=1,
        pv_power_w=4531.0,
        grid_power_w=-44.0,
        battery_power_w=-325.0,
        battery_soc=86.0,
        car_actual_power_w=3429.0,
    )
    cfg = _cfg(
        mode=ChargingMode.SOLAR_MIN,
        min_current_a=16.0,
        max_current_a=16.0,
        battery_reserve_soc=80.0,
        auto_phase=False,
    )
    d = decide(inp, cfg, EngineState(charging=True, active_source="grid"))
    assert d.hold_battery is True
    assert d.reason_key == "solar_min_topup"
    assert "grid" in d.reason


def test_floor_claims_no_top_up_when_the_surplus_covers_it():
    # The surplus lands on the floor almost exactly: there is no top-up to
    # attribute, so the reason must not invent one.
    inp = _inputs(
        phases=1,
        pv_power_w=5100.0,
        grid_power_w=-3680.0,
        battery_power_w=0.0,
        battery_soc=86.0,
        car_actual_power_w=0.0,
    )
    cfg = _cfg(
        mode=ChargingMode.SOLAR_MIN,
        min_current_a=16.0,
        max_current_a=16.0,
        battery_hold_mode="free",
        auto_phase=False,
    )
    d = decide(inp, cfg, EngineState(charging=True, active_source="grid"))
    assert d.target_current_a == 16.0
    assert d.reason_key == "solar_min_covered"
    assert "grid" not in d.reason


def test_raised_minimum_only_binds_in_solar_min():
    # A minimum raised for Solar + minimum used to follow the user into Solar
    # only — where the card doesn't even show the knob — and hold the start
    # hostage to a surplus the sun couldn't reach. 1φ at 6 A is 1380 W.
    inp = _inputs(phases=1, grid_power_w=-1500.0, battery_soc=85.0)

    d = decide(inp, _cfg(mode=ChargingMode.SOLAR, min_current_a=10.0))
    assert d.should_charge is True
    assert d.target_current_a == 6.0
    assert d.reason_key == "solar_surplus"

    # …while Solar + minimum still tops up to the raised minimum from the grid.
    d = decide(inp, _cfg(mode=ChargingMode.SOLAR_MIN, min_current_a=10.0))
    assert d.should_charge is True
    assert d.target_current_a == 10.0
    assert d.reason_key == "solar_min_topup"


def test_floor_yields_to_a_larger_surplus():
    d = decide(
        _inputs(grid_power_w=-8000.0, battery_soc=85.0),
        _cfg(mode=ChargingMode.SOLAR_MIN),
    )
    assert d.target_current_a == 11.0  # 8000 W over three phases is 11.6 A
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
            battery_soc=85.0,
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
        _inputs(grid_power_w=-2500.0, battery_soc=85.0),
        _cfg(auto_phase=True, max_phases=3),
        EngineState(),
    )
    assert d.target_phases == 1
    assert d.target_current_a == 10.0  # 2500 W on one phase is 10.9 A


def test_large_surplus_climbs_to_three_phases():
    d = decide(
        _inputs(grid_power_w=-6000.0, battery_soc=90.0),
        _cfg(auto_phase=True, max_phases=3),
        EngineState(),
    )
    assert d.target_phases == 3


def test_phase_up_needs_headroom_above_the_three_phase_minimum():
    # Just over the bare 3φ minimum (4140 W) is not enough — the margin keeps us
    # on one phase rather than switching into a configuration we can barely hold.
    d = decide(
        _inputs(grid_power_w=-4300.0, battery_soc=90.0),
        _cfg(auto_phase=True, max_phases=3),
        EngineState(),
    )
    assert d.target_phases == 1


def test_phase_switch_waits_for_the_confirmation_window():
    # A crossing has to hold before the contactor moves at all.
    cfg = _cfg(auto_phase=True, max_phases=3, start_confirm_s=0.0)
    state = EngineState()
    inputs = lambda now: _inputs(  # noqa: E731 - terse fixture, one expression
        grid_power_w=-6000.0, battery_soc=90.0, phases=1, now=now
    )
    assert decide(inputs(T0), cfg, state).target_phases == 1
    assert decide(inputs(T0 + timedelta(seconds=60)), cfg, state).target_phases == 1
    assert decide(inputs(T0 + timedelta(seconds=130)), cfg, state).target_phases == 3


def test_a_momentary_spike_does_not_switch_phases():
    # The crossing has to hold *continuously*: a spike re-arms the window.
    cfg = _cfg(auto_phase=True, max_phases=3, start_confirm_s=0.0)
    state = EngineState()
    decide(
        _inputs(grid_power_w=-6000.0, battery_soc=90.0, phases=1, now=T0), cfg, state
    )
    decide(  # spike over well inside the confirmation window
        _inputs(
            grid_power_w=-1500.0,
            battery_soc=90.0,
            phases=1,
            now=T0 + timedelta(seconds=60),
        ),
        cfg,
        state,
    )
    assert state.phase_want is None  # window disarmed, not merely paused
    d = decide(
        _inputs(
            grid_power_w=-6000.0,
            battery_soc=90.0,
            phases=1,
            now=T0 + timedelta(seconds=130),
        ),
        cfg,
        state,
    )
    assert d.target_phases == 1


def test_phase_dwell_blocks_a_quick_toggle():
    # The contactor moved a minute ago, so even a crossing that has held past the
    # confirmation window has to wait out the dwell.
    cfg = _cfg(auto_phase=True, max_phases=3, start_confirm_s=0.0)
    state = EngineState(phases=1, phase_changed_at=T0 - timedelta(seconds=60))
    inputs = lambda now: _inputs(  # noqa: E731 - terse fixture, one expression
        grid_power_w=-6000.0, battery_soc=90.0, phases=1, now=now
    )
    decide(inputs(T0), cfg, state)
    # Confirmed (120 s) but still inside the 300 s dwell, which started 60 s ago.
    assert decide(inputs(T0 + timedelta(seconds=130)), cfg, state).target_phases == 1
    assert decide(inputs(T0 + timedelta(seconds=250)), cfg, state).target_phases == 3


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


def test_solar_does_not_drop_a_grid_hours_third_phase_without_confirming():
    # The handover a stale phase memory used to get wrong: a cheap hour put the car
    # on three phases, the price jumps, and the surplus alone cannot hold them. The
    # switch down is real and must serve the confirmation window — reading our own
    # remembered phase instead made the engine believe it was on 1φ already and drop
    # the contactor the same second.
    cfg = _cfg(mode=ChargingMode.SMART, cheap_price=0.19, auto_phase=True,
               max_phases=3, start_confirm_s=0.0)
    state = EngineState(charging=True, active_source="grid", avail_zone="buffer")
    grid_hour = _inputs(now=T0, price_now=0.10, grid_power_w=7200.0,
                        pv_power_w=5400.0, battery_soc=90.0,
                        car_actual_power_w=10300.0, phases=3)
    assert decide(grid_hour, cfg, state).target_phases == 3

    def after(seconds):
        return _inputs(now=T0 + timedelta(seconds=seconds), price_now=0.30,
                       grid_power_w=7200.0, pv_power_w=5400.0, battery_soc=90.0,
                       car_actual_power_w=10300.0, phases=3)

    # Solar has taken over and wants one phase, but the contactor holds meanwhile.
    assert decide(after(30), cfg, state).target_phases == 3
    assert state.phase_want == 1  # the switch is armed, not executed
    assert decide(after(90), cfg, state).target_phases == 3
    assert decide(after(180), cfg, state).target_phases == 1


def test_a_grid_hour_that_moved_the_contactor_arms_the_dwell_timer():
    # Cheap grid takes three phases without consulting _resolve_phases, so the move
    # used to be invisible: the dwell timer stayed unarmed and the card's phase-lock
    # countdown showed nothing while the contactor was throwing.
    cfg = _cfg(mode=ChargingMode.SMART, cheap_price=0.19, auto_phase=True,
               max_phases=3, start_confirm_s=0.0)
    state = EngineState(charging=True, active_source="solar", avail_zone="buffer",
                        phases=1)
    solar = _inputs(now=T0, price_now=0.30, grid_power_w=1000.0, pv_power_w=5400.0,
                    battery_soc=90.0, car_actual_power_w=3400.0, phases=1)
    assert decide(solar, cfg, state).target_phases == 1
    assert state.phase_changed_at is None

    cheap = _inputs(now=T0 + timedelta(seconds=30), price_now=0.10,
                    grid_power_w=1000.0, pv_power_w=5400.0, battery_soc=90.0,
                    car_actual_power_w=3400.0, phases=1)
    d = decide(cheap, cfg, state)
    assert d.target_phases == 3
    assert state.phase_changed_at == T0 + timedelta(seconds=30)
    assert d.phase_locked_until == T0 + timedelta(seconds=330)  # +300 s dwell


def test_a_hands_off_decision_never_stamps_a_contactor_move():
    # With the brain switched off nothing of ours reaches psm, so no phase change
    # may be recorded — and the stale target must not survive to be compared against.
    cfg = _cfg(smart_enabled=False, auto_phase=True, max_phases=3)
    state = EngineState(phases_targeted=1)
    d = decide(_inputs(now=T0, phases=3), cfg, state)
    assert d.control is False
    assert state.phase_changed_at is None
    assert state.phases_targeted is None


def _cheap_hour_state():
    """Solar has just switched the contactor to one phase at T0."""
    return EngineState(charging=True, active_source="solar", avail_zone="buffer",
                       phases=1, phases_targeted=1, phase_changed_at=T0)


def _cheap_hour_inputs(seconds, phases=1):
    return _inputs(now=T0 + timedelta(seconds=seconds), price_now=0.10,
                   grid_power_w=1000.0, pv_power_w=5400.0, battery_soc=90.0,
                   car_actual_power_w=3400.0, phases=phases)


def test_a_cheap_hour_waits_out_the_phase_dwell_before_taking_the_third_phase():
    # The contactor is one piece of hardware: a price crossing may not throw it any
    # faster than the surplus may. The cheap hour still charges throughout — at 16 A
    # on the phase it already has — and picks the other two up when the dwell ends.
    cfg = _cfg(mode=ChargingMode.SMART, cheap_price=0.19, auto_phase=True,
               max_phases=3, start_confirm_s=0.0)
    state = _cheap_hour_state()
    for seconds in (30, 120, 299):
        d = decide(_cheap_hour_inputs(seconds), cfg, state)
        assert d.reason_key == "cheap_grid"
        assert d.target_phases == 1, seconds
        assert d.target_current_a == 16.0  # blocked from 3φ, not from charging
    d = decide(_cheap_hour_inputs(301), cfg, state)
    assert d.target_phases == 3


def test_a_grid_upshift_does_not_flip_back_while_the_contactor_is_still_settling():
    # The trap the dwell block opens: the upshift stamps a fresh dwell, and for a
    # few cycles the car is still drawing on the old phase, so a decision that
    # re-read the measurement would see 1φ, "block" itself back down to it and stamp
    # again — throwing the contactor twice in 1.5 s and never reaching three phases.
    cfg = _cfg(mode=ChargingMode.SMART, cheap_price=0.19, auto_phase=True,
               max_phases=3, start_confirm_s=0.0)
    state = _cheap_hour_state()
    assert decide(_cheap_hour_inputs(301), cfg, state).target_phases == 3
    locked_until = state.phase_changed_at
    # The charger still reports one phase while the contactor moves.
    for tick in range(1, 5):
        d = decide(_cheap_hour_inputs(301 + 1.5 * tick, phases=1), cfg, state)
        assert d.target_phases == 3, tick
    assert state.phase_changed_at == locked_until  # not re-stamped each cycle


def test_the_grid_never_drops_a_phase_it_already_has_to_honour_the_dwell():
    # The block is one-directional. Sitting at 3φ there is nothing for the dwell to
    # protect, and giving up two thirds of a cheap window to a timer is pure loss.
    cfg = _cfg(mode=ChargingMode.SMART, cheap_price=0.19, auto_phase=True,
               max_phases=3, start_confirm_s=0.0)
    state = EngineState(charging=True, active_source="solar", avail_zone="buffer",
                        phases=3, phases_targeted=3, phase_changed_at=T0)
    d = decide(
        _inputs(now=T0 + timedelta(seconds=30), price_now=0.10, grid_power_w=1000.0,
                pv_power_w=5400.0, battery_soc=90.0, car_actual_power_w=10300.0,
                phases=3),
        cfg, state,
    )
    assert d.target_phases == 3


def test_an_idle_three_phase_charger_still_starts_solar_on_one_phase():
    # The seed only trusts inp.phases while current is actually flowing. Idle it is
    # merely the psm mode the last session left behind — usually 3 — and letting that
    # seed the hysteresis would cost the 1φ preference a fresh small surplus needs.
    d = decide(
        _inputs(grid_power_w=-2500.0, battery_soc=85.0, phases=3,
                car_actual_power_w=0.0),
        _cfg(auto_phase=True, max_phases=3),
        EngineState(),
    )
    assert d.target_phases == 1


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


# --- Car source split (the card's source bar + ring) ---------------------------------

compute_car_sources = engine.compute_car_sources


def _sources(**kw):
    return compute_car_sources(compute_power_flow(_inputs(**kw)))


def test_sources_all_solar_when_pv_covers_car_and_house():
    # 6.2 kW PV, ~0.9 kW house, 5 kW car → the car is entirely solar-fed.
    s = _sources(pv_power_w=6200.0, grid_power_w=-300.0, car_actual_power_w=5000.0)
    assert s.solar_w == pytest.approx(5000.0)
    assert s.battery_w == 0.0
    assert s.grid_w == 0.0


def test_sources_priority_solar_then_battery_then_grid():
    # pv 3 kW, grid +3 kW, battery −1 kW, car 5 kW → house eats 2 kW of PV, so the
    # car is fed 1 kW solar spare, then 1 kW battery, then 3 kW grid (cheapest first).
    s = _sources(
        pv_power_w=3000.0,
        grid_power_w=3000.0,
        battery_power_w=-1000.0,
        car_actual_power_w=5000.0,
    )
    assert s.solar_w == pytest.approx(1000.0)
    assert s.battery_w == pytest.approx(1000.0)
    assert s.grid_w == pytest.approx(3000.0)


def test_sources_always_sum_to_car_power():
    s = _sources(
        pv_power_w=1000.0, grid_power_w=9000.0, battery_power_w=0.0,
        car_actual_power_w=10000.0,
    )
    assert s.solar_w + s.battery_w + s.grid_w == pytest.approx(10000.0)


# --- Home-battery three-way override (Auto / Hold / Free) -----------------------------

def _cheap_grid(**cfg_kw):
    return decide(
        _inputs(
            price_now=0.10,
            grid_power_w=8000.0,
            battery_power_w=-500.0,  # would drain into the car without a hold
            battery_soc=64.0,
            now=T0,
        ),
        _cfg(mode=ChargingMode.SMART, cheap_price=0.15, **cfg_kw),
    )


def test_hold_mode_auto_holds_during_cheap_grid():
    d = _cheap_grid(battery_hold_mode="auto")
    assert d.hold_battery is True
    assert d.hold_source == "auto"


def test_hold_mode_free_releases_the_battery_and_skips_the_guard():
    # Free lets the battery feed the car: no hold, and the fallback guard must not
    # trim the current down to the surplus.
    d = _cheap_grid(battery_hold_mode="free")
    assert d.hold_battery is False
    assert d.hold_source == "free"
    assert d.target_current_a == pytest.approx(16.0)


def test_hold_mode_hold_blocks_discharge_even_in_solar():
    # Plain solar charging never holds on its own; "hold" forces it on.
    d = decide(
        _inputs(grid_power_w=-6000.0, battery_soc=90.0, now=T0),
        _cfg(battery_hold_mode="hold"),
    )
    assert d.hold_battery is True
    assert d.hold_source == "hold"


# --- Plan windows + countdown deadlines exposed on the decision -----------------------

def test_decision_exposes_booked_plan_windows():
    fc = _forecast([0.30, 0.30, 0.10, 0.10, 0.30], T0)
    d = decide(
        _inputs(price_now=0.30, price_forecast=fc, now=T0 + timedelta(minutes=5)),
        _cfg(
            mode=ChargingMode.SMART,
            cheap_price=0.0,
            target_energy_kwh=8.0,
            departure=T0 + timedelta(hours=5),
        ),
    )
    # 8 kWh ≈ one 3φ slot → the single cheapest hour (index 2) is booked.
    assert d.plan == [fc[2].start.isoformat()]


def test_decision_exposes_resume_countdown_while_confirming():
    # Surplus just crossed the minimum, so a solar start is confirming: the
    # resume deadline is start_confirm_s ahead, and we are not charging yet.
    state = EngineState()
    d = decide(
        _inputs(grid_power_w=-4200.0, battery_soc=90.0, now=T0),
        _cfg(),
        state,
    )
    assert d.should_charge is False
    assert d.resume_not_before == T0 + timedelta(seconds=engine.EngineConfig().start_confirm_s)


def test_plan_is_empty_outside_smart_mode():
    d = decide(_inputs(grid_power_w=-6000.0, battery_soc=90.0, now=T0), _cfg())
    assert d.plan == []


# --- Peak protection (the capacity tariff) ------------------------------------------

update_peak_window = engine.update_peak_window
resolve_peak_tier = engine.resolve_peak_tier
PEAK_WINDOW_S = engine.PEAK_WINDOW_S

# 12:00 is a quarter-hour boundary, so windows start clean unless a test says otherwise.
W0 = datetime(2026, 7, 4, 12, 0, tzinfo=timezone.utc)

# For the two things the engine has to resolve on the user's clock rather than in
# UTC: the billed month, and any wall-clock time it puts in a reason string. A
# fixed offset rather than a named zone, so these tests still need nothing beyond
# pytest — both dates below are in summer, when Vienna is UTC+2.
VIENNA = timezone(timedelta(hours=2))


def _peak_cfg(**kw) -> "engine.EngineConfig":
    """A config with peak protection on and the Austrian-ish limits from the docs."""
    base = dict(
        mode=ChargingMode.FAST,
        smart_enabled=True,
        max_current_a=16.0,
        battery_reserve_soc=80.0,
        peak_guard_enabled=True,
        peak_soft_w=3300.0,
        peak_target_w=3700.0,
        peak_hard_w=3900.0,
        peak_follow_month=False,  # opt in per test; it changes the limits in force
        shaving_reserve_soc=50.0,
        peak_min_soc=35.0,
    )
    base.update(kw)
    return EngineConfig(**base)


def _run(cfg, state, seconds, step=20, **kw):
    """Drive the engine across a span of time, returning the last decision."""
    decision = None
    for offset in range(0, seconds + 1, step):
        decision = decide(_inputs(now=W0 + timedelta(seconds=offset), **kw), cfg, state)
    return decision


# --- The measurement (runs whether or not the guard is enabled) ---------------------

def test_window_integrates_by_zero_order_hold():
    # A meter reports a level, not an event: 4 kW held for 60 s is 66.7 Wh, and the
    # *previous* sample is what covers the interval — the new one covers what follows.
    cfg, state = _peak_cfg(), EngineState()
    update_peak_window(W0, 4000.0, cfg, state)
    window = update_peak_window(W0 + timedelta(seconds=60), 4000.0, cfg, state)
    assert window.imported_wh == pytest.approx(4000.0 * 60 / 3600.0, abs=0.1)
    assert window.average_w == pytest.approx(4000.0, abs=1.0)


def test_export_never_lowers_an_import_peak():
    # The tariff bills import; exporting 5 kW does not buy back a kilowatt of it.
    cfg, state = _peak_cfg(), EngineState()
    update_peak_window(W0, -5000.0, cfg, state)
    window = update_peak_window(W0 + timedelta(seconds=60), -5000.0, cfg, state)
    assert window.imported_wh == 0.0
    assert window.projected_w == 0.0


def test_window_resets_exactly_on_the_quarter_hour():
    cfg, state = _peak_cfg(), EngineState()
    for offset in range(0, 900, 30):
        update_peak_window(W0 + timedelta(seconds=offset), 4000.0, cfg, state)
    before = update_peak_window(W0 + timedelta(seconds=890), 4000.0, cfg, state)
    after = update_peak_window(W0 + timedelta(seconds=910), 4000.0, cfg, state)
    assert before.start == W0
    assert after.start == W0 + timedelta(seconds=900)
    assert after.imported_wh < before.imported_wh  # a fresh budget, not a running total


def test_projection_and_budget_are_the_documented_formulas():
    # 6 minutes at 4 kW = 400 Wh. Projected = (400*3600 + 4000*540)/900 = 4000 W.
    # Allowed  = (3700*900 - 400*3600)/540 = 3500 W.
    cfg, state = _peak_cfg(), EngineState()
    update_peak_window(W0, 4000.0, cfg, state)
    window = update_peak_window(W0 + timedelta(seconds=360), 4000.0, cfg, state)
    assert window.imported_wh == pytest.approx(400.0, abs=1.0)
    assert window.projected_w == pytest.approx(4000.0, abs=5.0)
    assert window.allowed_w == pytest.approx(3500.0, abs=10.0)


def test_budget_floors_the_remaining_time_at_a_minute():
    # 5 s from the end the budget would otherwise diverge; the floor keeps the last
    # minute deliberately conservative instead of inviting a boundary spike.
    cfg, state = _peak_cfg(), EngineState()
    update_peak_window(W0, 1000.0, cfg, state)
    window = update_peak_window(W0 + timedelta(seconds=895), 1000.0, cfg, state)
    assert window.remaining_s == pytest.approx(5.0, abs=0.1)
    # Computed against 60 s, not the 5 s actually left.
    assert window.allowed_w == pytest.approx(
        (3700.0 * 900.0 - window.imported_wh * 3600.0) / 60.0, rel=1e-6
    )


def test_month_peak_records_completed_windows_only():
    cfg, state = _peak_cfg(), EngineState()
    for offset in range(0, 1000, 20):
        update_peak_window(W0 + timedelta(seconds=offset), 4000.0, cfg, state)
    # The first window completed at 4 kW; the second is still running.
    assert state.month_peak_w == pytest.approx(4000.0, abs=20.0)
    assert state.month_peak_at == W0
    assert len(state.peak_history) == 1


def test_a_degraded_window_never_becomes_the_billed_number():
    # A five-minute gap: the reading is held across it (never under-count) but the
    # window is no longer trustworthy, so it must not set the month's record.
    cfg, state = _peak_cfg(), EngineState()
    update_peak_window(W0, 9000.0, cfg, state)
    window = update_peak_window(W0 + timedelta(seconds=300), 9000.0, cfg, state)
    assert window.degraded is True
    assert window.imported_wh == pytest.approx(9000.0 * 300 / 3600.0, abs=1.0)
    update_peak_window(W0 + timedelta(seconds=910), 9000.0, cfg, state)
    assert state.month_peak_w == 0.0
    assert state.peak_history  # it still happened, and the card still shows it


def test_a_missing_reading_degrades_the_window():
    cfg, state = _peak_cfg(), EngineState()
    update_peak_window(W0, 1000.0, cfg, state)
    window = update_peak_window(W0 + timedelta(seconds=30), None, cfg, state)
    assert window.degraded is True
    # …and the held reading still covered the interval.
    assert window.imported_wh == pytest.approx(1000.0 * 30 / 3600.0, abs=0.1)


def test_a_long_outage_does_not_walk_every_window():
    # Two days down. We must land in the right window without iterating hundreds.
    cfg, state = _peak_cfg(), EngineState()
    update_peak_window(W0, 1000.0, cfg, state)
    window = update_peak_window(W0 + timedelta(days=2), 1000.0, cfg, state)
    assert window.start == W0 + timedelta(days=2)
    assert window.degraded is True


# --- The billing meter's register ---------------------------------------------------
#
# The tariff bills a quarter-hour's import *energy*. With the operator's register
# mapped, the window's energy is the register's climb; grid power only carries the
# seconds between two register ticks (and the projection of the rest of the window).

_REG0 = 38_000.0  # kWh on the register at W0


def _reg(seconds: float, watts: float, base: float = _REG0) -> float:
    """The register after ``seconds`` at ``watts``, rounded to its 1 Wh resolution."""
    return round(base + watts * seconds / 3_600_000.0, 3)


def _metered_run(cfg, state, seconds, *, power_w, meter_w, step=5, start=0, base=_REG0):
    window = None
    for offset in range(start, start + seconds + 1, step):
        window = update_peak_window(
            W0 + timedelta(seconds=offset), power_w, cfg, state,
            _reg(offset, meter_w, base),
        )
    return window


def test_the_register_settles_the_window_not_the_power_reading():
    # The battery system's meter reads 4 % high against the operator's. The bill is
    # the operator's, so after five minutes the window holds *its* count.
    cfg, state = _peak_cfg(), EngineState()
    window = _metered_run(cfg, state, 300, power_w=4000.0, meter_w=3840.0)
    assert window.metered is True
    assert window.imported_wh == pytest.approx(3840.0 * 300 / 3600.0, abs=1.5)
    # The projection of what is *left* still rests on the live reading.
    assert window.projected_w == pytest.approx(
        (window.imported_wh * 3600.0 + 4000.0 * 600.0) / 900.0, rel=1e-6
    )


def test_without_a_register_nothing_changes():
    cfg = _peak_cfg()
    plain, metered = EngineState(), EngineState()
    for offset in range(0, 1000, 20):
        a = update_peak_window(W0 + timedelta(seconds=offset), 4000.0, cfg, plain)
        b = update_peak_window(W0 + timedelta(seconds=offset), 4000.0, cfg, metered, None)
        assert a == b
    assert a.metered is False


def test_the_month_record_is_the_registers_quarter_hour():
    cfg, state = _peak_cfg(), EngineState()
    _metered_run(cfg, state, 905, power_w=4000.0, meter_w=3600.0)
    # Anchored at the first reading (W0), so the whole window is the register's.
    assert state.month_peak_w == pytest.approx(3600.0, abs=10.0)


def test_power_carries_the_time_between_two_register_ticks():
    # At low load a 1 Wh register sits still for many seconds. Between ticks the
    # integral must keep counting, or the projection would read low until it moves.
    cfg, state = _peak_cfg(), EngineState()
    update_peak_window(W0, 3600.0, cfg, state, _REG0)
    update_peak_window(W0 + timedelta(seconds=10), 3600.0, cfg, state, _reg(10, 3600.0))
    settled = state.peak_window_wh
    window = update_peak_window(
        W0 + timedelta(seconds=20), 3600.0, cfg, state, _reg(10, 3600.0)  # unchanged
    )
    assert window.imported_wh == pytest.approx(settled + 3600.0 * 10 / 3600.0, abs=0.1)


def test_a_frozen_register_falls_back_and_its_catch_up_is_exact():
    # The reader stalls for three minutes, then reports the real register again.
    # Meanwhile the (high-reading) power integral carries the window; the first
    # fresh value puts it back on the operator's count for the whole stretch.
    cfg, state = _peak_cfg(), EngineState()
    _metered_run(cfg, state, 60, power_w=4000.0, meter_w=3840.0)
    frozen = _reg(60, 3840.0)
    for offset in range(65, 241, 5):
        window = update_peak_window(
            W0 + timedelta(seconds=offset), 4000.0, cfg, state, frozen
        )
    assert window.imported_wh > 3840.0 * 240 / 3600.0  # the integral, reading high
    window = update_peak_window(
        W0 + timedelta(seconds=245), 4000.0, cfg, state, _reg(245, 3840.0)
    )
    assert window.imported_wh == pytest.approx(3840.0 * 245 / 3600.0, abs=1.5)


def test_a_register_that_runs_backwards_is_not_billed_across():
    # A reader restart reporting 0, or a swapped meter: re-anchor, never subtract.
    cfg, state = _peak_cfg(), EngineState()
    _metered_run(cfg, state, 120, power_w=3000.0, meter_w=3000.0)
    before = state.peak_window_wh
    update_peak_window(W0 + timedelta(seconds=125), 3000.0, cfg, state, 0.0)
    assert state.peak_window_wh >= before
    window = _metered_run(
        cfg, state, 60, power_w=3000.0, meter_w=3000.0, start=130, base=0.0 - 130 * 3000.0 / 3_600_000.0
    )
    # Everything still adds up to ~3 kW for the whole stretch.
    assert window.imported_wh == pytest.approx(3000.0 * 190 / 3600.0, abs=6.0)


def test_an_impossible_jump_never_becomes_a_peak():
    # +500 kWh in five seconds is a glitch, not a sauna.
    cfg, state = _peak_cfg(), EngineState()
    _metered_run(cfg, state, 60, power_w=2000.0, meter_w=2000.0)
    update_peak_window(W0 + timedelta(seconds=65), 2000.0, cfg, state, _REG0 + 500.0)
    for offset in range(70, 905, 5):
        update_peak_window(
            W0 + timedelta(seconds=offset), 2000.0, cfg, state,
            _REG0 + 500.0 + 2000.0 * (offset - 65) / 3_600_000.0,
        )
    assert state.month_peak_w == pytest.approx(2000.0, abs=20.0)


def test_a_new_window_anchors_on_its_first_reading():
    # The boundary passes between two readings: the seconds before the new window's
    # first reading are the integral's, everything after is the register's.
    cfg, state = _peak_cfg(), EngineState()
    _metered_run(cfg, state, 895, power_w=3000.0, meter_w=3000.0)
    window = _metered_run(cfg, state, 60, power_w=3000.0, meter_w=3000.0, start=903)
    assert window.start == W0 + timedelta(seconds=900)
    assert window.imported_wh == pytest.approx(3000.0 * 63 / 3600.0, abs=1.5)


def test_after_a_restart_the_register_vouches_for_the_gap():
    # HA was down for five minutes mid-window. The integral can only guess across the
    # gap — that is what degraded means — but the register counted every watt-hour,
    # so with the anchor restored the window is exact again and may set the record.
    cfg, state = _peak_cfg(), EngineState()
    _metered_run(cfg, state, 120, power_w=3000.0, meter_w=3000.0)
    restored = EngineState(
        peak_window_start=state.peak_window_start,
        peak_window_wh=state.peak_window_wh,
        peak_window_degraded=True,  # what the coordinator's restore always sets
        peak_sample_t=state.peak_sample_t,
        peak_sample_w=state.peak_sample_w,
        peak_meter_anchor_kwh=state.peak_meter_anchor_kwh,
        peak_meter_base_wh=state.peak_meter_base_wh,
        peak_meter_anchor_clean=state.peak_meter_anchor_clean,
        peak_meter_last_kwh=state.peak_meter_last_kwh,
        peak_meter_last_t=state.peak_meter_last_t,
    )
    # Down 120 s → 420 s, drawing 6 kW while nobody was looking.
    climb = _reg(120, 3000.0) + 6000.0 * 300 / 3_600_000.0
    window = update_peak_window(W0 + timedelta(seconds=420), 3000.0, cfg, restored, round(climb, 3))
    assert window.degraded is False
    assert window.imported_wh == pytest.approx((3000.0 * 120 + 6000.0 * 300) / 3600.0, abs=1.5)


def test_an_anchor_set_after_a_gap_cannot_clear_it():
    # Anchored only *after* the window went unmeasured: the register can't speak for
    # the part before its anchor, so the window stays degraded.
    cfg, state = _peak_cfg(), EngineState()
    update_peak_window(W0, 3000.0, cfg, state)
    update_peak_window(W0 + timedelta(seconds=200), 3000.0, cfg, state)  # a gap
    window = _metered_run(cfg, state, 60, power_w=3000.0, meter_w=3000.0, start=205)
    assert window.metered is True
    assert window.degraded is True


def test_a_missing_live_reading_keeps_the_window_degraded():
    cfg, state = _peak_cfg(), EngineState()
    _metered_run(cfg, state, 60, power_w=3000.0, meter_w=3000.0)
    window = update_peak_window(W0 + timedelta(seconds=70), None, cfg, state, _reg(70, 3000.0))
    assert window.degraded is True


# --- Tiers, confirmation and release ------------------------------------------------

def test_soft_tier_waits_out_the_confirmation_window():
    cfg, state = _peak_cfg(), EngineState()
    d = _run(cfg, state, 60, car_connected=True, grid_power_w=3600.0, battery_soc=60.0)
    assert d.peak_tier == "off"  # projected 3.6 kW is over soft, but not for long
    d = _run(cfg, state, 200, car_connected=True, grid_power_w=3600.0, battery_soc=60.0)
    assert d.peak_tier == "soft"


def test_hard_tier_engages_on_the_very_next_cycle():
    # No confirmation: by the time 120 s had confirmed, a third of the quarter-hour
    # it was protecting would be gone.
    cfg, state = _peak_cfg(), EngineState()
    decide(_inputs(now=W0, car_connected=True, grid_power_w=500.0), cfg, state)
    d = decide(
        _inputs(now=W0 + timedelta(seconds=20), car_connected=True, grid_power_w=9000.0),
        cfg,
        state,
    )
    assert d.peak_tier == "hard"


def test_release_needs_both_the_confirmation_and_the_dwell():
    cfg = _peak_cfg(peak_release_s=120.0, peak_dwell_s=300.0)
    state = EngineState()
    _run(cfg, state, 40, step=20, car_connected=True, grid_power_w=9000.0)
    assert state.peak_tier == "hard"
    # The grid collapses to nothing, but the window has already banked the energy,
    # so the projection stays high for a while — then it falls and the timers start.
    d = _run(cfg, state, 200, step=20, car_connected=True, grid_power_w=0.0)
    assert d.peak_tier == "hard"  # the dwell (300 s) has not elapsed
    d = _run(cfg, state, 600, step=20, car_connected=True, grid_power_w=0.0)
    assert d.peak_tier in ("soft", "off")  # both timers satisfied


def test_a_degraded_window_may_tighten_but_never_relax():
    cfg, state = _peak_cfg(peak_dwell_s=0.0, peak_release_s=0.0), EngineState()
    _run(cfg, state, 40, step=20, car_connected=True, grid_power_w=9000.0)
    assert state.peak_tier == "hard"
    # A five-minute blackout in the reading, then a calm grid: the tier is stuck
    # until the next clean window, because we cannot account for the gap.
    decide(
        _inputs(now=W0 + timedelta(seconds=400), car_connected=True, grid_power_w=0.0),
        cfg,
        state,
    )
    d = decide(
        _inputs(now=W0 + timedelta(seconds=500), car_connected=True, grid_power_w=0.0),
        cfg,
        state,
    )
    assert d.peak_degraded is True
    assert d.peak_tier == "hard"


# --- The wallbox cap ----------------------------------------------------------------

def test_soft_tier_eases_the_car_back_without_pausing():
    # House 800 W + car 3600 W, 200 s into the window: 244 Wh banked, so the rest
    # of it may take (3700·900 − 244·3600)/700 = 3500 W. The house keeps 800 of
    # that, leaving 2700 W for the car — 11 A at 1φ.
    cfg, state = _peak_cfg(peak_hard_w=99000.0), EngineState()
    d = _run(
        cfg, state, 200, car_connected=True, phases=1,
        car_actual_power_w=3600.0, grid_power_w=4400.0, battery_soc=60.0,
    )
    assert d.peak_tier == "soft"
    assert d.should_charge is True
    assert d.target_current_a == 11.0
    # The arbiter's decision is trimmed, not replaced — and it says the peak limit,
    # not the charger, is why it isn't 16 A.
    assert d.reason_key == "fast_peak"
    assert d.peak_reason_key == "peak_shaving_car"
    # …but the number in it is the one we actually wrote. A status line reading
    # "Fast charging at 16 A" while 11 A goes to the car is the sensor lying about
    # the single fact a user checks it for.
    assert d.reason_params["amps"] == "11"
    assert d.reason == "Fast charging at 11 A — as much as fits under the peak limit"


def test_a_peak_pause_takes_over_the_status_reason():
    # A trim leaves the arbiter's explanation true, so it keeps it. A pause does
    # not: the car is at 0 A and "Fast charging" is simply wrong, however well the
    # peak line beside it explains why.
    cfg, state = _peak_cfg(), EngineState()
    d = _run(
        cfg, state, 300, car_connected=True, phases=3,
        car_actual_power_w=1000.0, grid_power_w=9000.0, battery_soc=36.0,
    )
    assert d.should_charge is False
    assert d.reason_key == "peak_pause"
    assert d.reason == d.peak_reason


def test_soft_tier_clamps_at_the_hardware_minimum_rather_than_stopping():
    cfg = _peak_cfg(peak_hard_w=99000.0)
    state = EngineState()
    d = _run(
        cfg, state, 300, car_connected=True, phases=1,
        car_actual_power_w=1000.0, grid_power_w=8000.0, battery_soc=60.0,
    )
    assert d.peak_tier == "soft"
    assert d.should_charge is True
    assert d.target_current_a == engine.HARDWARE_MIN_CURRENT_A


def test_hard_tier_pauses_when_six_amps_will_not_fit():
    cfg, state = _peak_cfg(), EngineState()
    d = _run(
        cfg, state, 300, car_connected=True, phases=3,
        car_actual_power_w=1000.0, grid_power_w=9000.0, battery_soc=36.0,
    )
    assert d.peak_tier == "hard"
    assert d.should_charge is False
    assert d.target_current_a == 0.0
    assert d.peak_reason_key == "peak_pause"


def test_the_hard_stop_outranks_the_solar_ride_out():
    # Mid-ride-out, a peak appears. The ride-out exists to smooth *solar* dips; it
    # has no business holding the charger on through a demand-charge breach.
    cfg = _peak_cfg(mode=ChargingMode.SOLAR)
    state = EngineState(charging=True, active_source="solar", avail_zone="buffer")
    d = _run(
        cfg, state, 100, step=20, car_connected=True, phases=3,
        car_actual_power_w=1000.0, grid_power_w=9000.0, battery_soc=36.0,
    )
    assert d.peak_tier == "hard"
    assert d.should_charge is False


def test_a_car_on_pure_solar_is_not_trimmed():
    # PV 5 kW, house 1 kW, car 3 kW off the sun, battery charging 4 kW from grid:
    # a 3 kW import peak the car has no part in. Stopping it would export, not
    # reduce the import, so the cap must leave it alone.
    cfg, state = _peak_cfg(peak_soft_w=1000.0, peak_target_w=1200.0), EngineState()
    d = _run(
        cfg, state, 200, car_connected=True, phases=1, car_actual_power_w=3000.0,
        pv_power_w=5000.0, battery_power_w=4000.0, grid_power_w=3000.0,
        battery_soc=60.0,
    )
    assert d.peak_tier in ("soft", "hard")
    assert d.should_charge is True
    # The cap lands on the car's own solar share (3000 W ≈ 13 A at 1φ) rather than
    # below it: the guard stops it climbing into the grid, it does not cut it back.
    assert d.target_current_a >= 13.0


def test_the_cap_falls_at_once_but_rises_only_after_the_dwell():
    cfg = _peak_cfg(peak_hard_w=99000.0, peak_dwell_s=300.0)
    state = EngineState()
    _run(
        cfg, state, 200, car_connected=True, phases=1,
        car_actual_power_w=3600.0, grid_power_w=4400.0, battery_soc=60.0,
    )
    assert state.peak_cap_a == 11.0
    # The house load vanishes, so the budget jumps — but relaxing is comfort, not
    # safety, and following every upward wobble is how the amps start flapping.
    d = decide(
        _inputs(
            now=W0 + timedelta(seconds=220), car_connected=True, phases=1,
            car_actual_power_w=3600.0, grid_power_w=3600.0, battery_soc=60.0,
        ),
        cfg,
        state,
    )
    assert d.target_current_a == 11.0
    d = decide(
        _inputs(
            now=W0 + timedelta(seconds=700), car_connected=True, phases=1,
            car_actual_power_w=3600.0, grid_power_w=3600.0, battery_soc=60.0,
        ),
        cfg,
        state,
    )
    assert d.target_current_a > 11.0


def test_the_cap_binds_in_manual_mode_too():
    cfg = _peak_cfg(
        mode=ChargingMode.MANUAL, manual_charge=True, manual_current_a=16.0,
        manual_phases=1, peak_hard_w=99000.0,
    )
    state = EngineState()
    d = _run(
        cfg, state, 200, car_connected=True, phases=1,
        car_actual_power_w=3600.0, grid_power_w=4400.0, battery_soc=60.0,
    )
    assert d.peak_tier == "soft"
    assert d.target_current_a == 11.0


# --- The house levers ---------------------------------------------------------------

def test_shaving_releases_the_battery_over_the_users_hold():
    cfg = _peak_cfg(battery_hold_mode="hold")
    state = EngineState()
    d = _run(
        cfg, state, 300, car_connected=True, phases=3,
        car_actual_power_w=1000.0, grid_power_w=9000.0, battery_soc=60.0,
    )
    assert d.peak_tier == "hard"
    assert d.hold_battery is False
    assert d.hold_source == "peak"
    assert d.battery_min_soc == 35.0
    assert d.grid_setpoint_w == 0.0


def test_the_min_soc_rests_at_the_shaving_reserve():
    cfg, state = _peak_cfg(), EngineState()
    d = _run(cfg, state, 60, car_connected=True, grid_power_w=200.0, battery_soc=60.0)
    assert d.peak_tier == "off"
    assert d.battery_min_soc == 50.0  # banked headroom, held year-round
    assert d.grid_setpoint_w == 50.0


def test_a_house_peak_with_no_car_still_drives_the_battery():
    # The case the whole layer exists for: a sauna sets the monthly peak whether or
    # not a car is plugged in, and the levers for it are the battery's.
    cfg, state = _peak_cfg(), EngineState()
    d = _run(cfg, state, 300, car_connected=False, grid_power_w=9000.0, battery_soc=41.0)
    assert d.peak_tier == "hard"
    assert d.house_control is True
    assert d.battery_min_soc == 35.0
    assert d.grid_setpoint_w == 0.0
    assert d.peak_reason_key == "peak_shaving_house"


def test_an_empty_battery_says_so_rather_than_pretending():
    cfg, state = _peak_cfg(), EngineState()
    d = _run(cfg, state, 300, car_connected=False, grid_power_w=9000.0, battery_soc=35.0)
    assert d.peak_reason_key == "peak_battery_empty"


def test_the_soc_ladder_is_clamped_when_the_numbers_are_inverted():
    # A floor above the reserve is meaningless; the floor gives way.
    cfg = _peak_cfg(shaving_reserve_soc=40.0, peak_min_soc=70.0)
    state = EngineState()
    d = _run(cfg, state, 300, car_connected=False, grid_power_w=9000.0, battery_soc=60.0)
    assert d.battery_min_soc == 40.0


def test_the_limits_are_clamped_when_the_numbers_are_inverted():
    # "Start easing off at" stays authoritative; the others are raised to fit.
    cfg = _peak_cfg(peak_soft_w=5000.0, peak_target_w=3700.0, peak_hard_w=1000.0)
    assert engine._peak_thresholds(cfg) == (5000.0, 5000.0, 5000.0)


def test_smart_control_off_still_guards_the_house_and_stops_the_car():
    # Peak protection answers to its own switch: a demand charge is money whether or
    # not the brain is currently driving the wallbox.
    cfg = _peak_cfg(smart_enabled=False)
    state = EngineState()
    d = _run(
        cfg, state, 300, car_connected=True, phases=3,
        car_actual_power_w=1000.0, grid_power_w=9000.0, battery_soc=60.0,
    )
    assert d.house_control is True
    assert d.battery_min_soc == 35.0
    assert d.control is True  # the hard stop reaches even a released charger
    assert d.should_charge is False
    assert d.peak_reason_key == "peak_pause"
    # …and the hold is flagged as ours to drive, so the coordinator writes it rather
    # than leaving a switch the user may own untouched.
    assert d.hold_source == "peak"


def test_nothing_is_written_before_a_trustworthy_reading_arrives():
    # A cold start must not shave blind.
    cfg, state = _peak_cfg(), EngineState()
    window = update_peak_window(W0 + timedelta(seconds=60), None, cfg, state)
    tier = resolve_peak_tier(W0 + timedelta(seconds=60), window, cfg, state)
    d = engine.apply_peak_guard(
        engine.Decision(control=True),
        _inputs(car_connected=False),
        cfg,
        state,
        window,
        tier,
    )
    assert d.grid_setpoint_w is None
    assert d.battery_min_soc is None


# --- The month-peak allowance --------------------------------------------------------

def test_the_limits_follow_a_peak_the_month_has_already_paid_for():
    # Up to the record, not onto it: the target lands a buffer below so the guard
    # steers for just under what is already bought, while the hard limit sits on the
    # record itself — nothing is thrown away, but nothing new is bought either.
    cfg = _peak_cfg(peak_follow_month=True)
    state = EngineState(month_key="2026-07", month_peak_w=5200.0)
    window = update_peak_window(W0, 1000.0, cfg, state)
    assert window.target_w == 5000.0
    assert window.hard_w == 5200.0


def test_the_soft_line_travels_with_the_allowance():
    # The month has already bought 5.2 kW, so the enforced target is 5.0 kW. A
    # 3.6 kW projection is over the *configured* soft line but well under anything
    # we are actually defending — engaging the shave there would drop the minimum
    # SoC and drain the home battery for a saving that cannot happen.
    cfg = _peak_cfg(peak_follow_month=True)
    state = EngineState(month_key="2026-07", month_peak_w=5200.0)
    d = _run(cfg, state, 400, car_connected=True, grid_power_w=3600.0, battery_soc=60.0)
    assert d.peak_tier == "off"
    assert d.battery_min_soc == 50.0  # the resting reserve, not the shaving floor
    assert d.hold_source != "peak"
    # …and the status line explains exactly that, instead of claiming to shave.
    assert d.peak_reason_key == "peak_month_headroom"


def test_the_soft_line_still_engages_once_the_allowance_is_reached():
    # The other direction: the allowance raises the line, it does not remove it.
    # 5.1 kW against an enforced 5.0 kW target is over the soft line that moved
    # with it, and the shave has to engage.
    cfg = _peak_cfg(peak_follow_month=True)
    state = EngineState(month_key="2026-07", month_peak_w=5200.0)
    d = _run(cfg, state, 400, car_connected=True, grid_power_w=5100.0, battery_soc=60.0)
    assert d.peak_tier == "soft"
    assert d.battery_min_soc == 35.0
    assert d.hold_source == "peak"


def test_the_quarter_hour_in_a_reason_is_the_users_wall_clock():
    # The one time a user reads off this module. 12:15 UTC is 14:15 in Vienna, and
    # a status line telling someone their car resumes two hours from when it does
    # is worse than no time at all.
    cfg = _peak_cfg(local_tz=VIENNA)
    state = EngineState()
    d = _run(
        cfg, state, 300, car_connected=True, phases=3,
        car_actual_power_w=1000.0, grid_power_w=9000.0, battery_soc=36.0,
    )
    assert d.peak_reason_key == "peak_pause"
    assert d.peak_reason_params["until"] == "14:15"


def test_the_allowance_does_not_ratchet_the_month_upward():
    # The failure the buffer exists to prevent: aim exactly at the record, land a
    # little over it because the projection is an estimate, and that overshoot is
    # the new record — repeat all month. Holding a steady draw at the target must
    # therefore finish the window *under* what the month has already cost.
    cfg = _peak_cfg(peak_follow_month=True)
    state = EngineState(month_key="2026-07", month_peak_w=5200.0)
    window = update_peak_window(W0, 5000.0, cfg, state)
    for offset in range(30, int(PEAK_WINDOW_S) + 1, 30):
        window = update_peak_window(W0 + timedelta(seconds=offset), 5000.0, cfg, state)
    assert state.month_peak_w == 5200.0  # the record stands; nothing new was bought
    assert window.target_w == 5000.0


def test_a_zero_buffer_aims_at_the_record_itself():
    # The knob turned all the way down is the old behaviour, exactly.
    cfg = _peak_cfg(peak_follow_month=True, peak_month_buffer_w=0.0)
    state = EngineState(month_key="2026-07", month_peak_w=5200.0)
    window = update_peak_window(W0, 1000.0, cfg, state)
    assert window.target_w == 5200.0
    assert window.hard_w == 5200.0


def test_the_buffer_never_pulls_a_limit_below_what_you_asked_for():
    # A record barely above the target must not make the guard *stricter* than the
    # setting it is supposed to be relaxing.
    cfg = _peak_cfg(peak_follow_month=True, peak_month_buffer_w=200.0)
    state = EngineState(month_key="2026-07", month_peak_w=3750.0)
    window = update_peak_window(W0, 1000.0, cfg, state)
    assert window.target_w == 3700.0  # the configured target, not 3.55 kW
    assert window.hard_w == 3900.0


def test_the_allowance_can_be_switched_off_for_a_strict_ceiling():
    cfg = _peak_cfg(peak_follow_month=False)
    state = EngineState(month_key="2026-07", month_peak_w=5200.0)
    window = update_peak_window(W0, 1000.0, cfg, state)
    assert window.target_w == 3700.0
    assert window.hard_w == 3900.0


def test_a_new_month_starts_a_new_record():
    # The demand charge resets with the calendar, so the record has to roll the
    # moment the month does — not one window later, or the allowance would spend
    # the first quarter-hour of the month still permitting the old peak.
    cfg, state = _peak_cfg(), EngineState()
    end_of_month = datetime(2026, 7, 31, 23, 45, tzinfo=timezone.utc)
    for offset in range(0, 1000, 30):  # 30 s steps: no gap, so nothing is degraded
        update_peak_window(end_of_month + timedelta(seconds=offset), 6000.0, cfg, state)
    assert state.month_key == "2026-08"
    assert state.month_peak_w == 0.0  # August's own record starts empty
    assert state.prev_month_peak_w == pytest.approx(6000.0, abs=100.0)


def test_the_month_rolls_on_the_users_calendar_not_on_utc():
    # A demand charge is billed per calendar month, and the calendar is the one on
    # the wall. In UTC the record would roll at 02:00 local, so a peak drawn in the
    # first two hours of a new month would be filed against the old one — and the
    # old month's peak would keep raising the ceiling after it stopped being
    # billable.
    cfg = _peak_cfg(local_tz=VIENNA)
    state = EngineState(month_key="2026-06", month_peak_w=5000.0)
    # 22:30 UTC on 30 June is 00:30 on 1 July in Vienna: July, as far as the bill
    # is concerned.
    update_peak_window(datetime(2026, 6, 30, 22, 30, tzinfo=timezone.utc), 1000.0, cfg, state)
    assert state.month_key == "2026-07"
    assert state.month_peak_w == 0.0
    assert state.prev_month_peak_w == 5000.0


# --- Surviving a restart -------------------------------------------------------------

def _restored(window_start, *, sample_t=None, sample_w=0.0) -> "engine.EngineState":
    """An EngineState as the coordinator rebuilds it from the peak store."""
    state = EngineState(month_key="2026-07")
    state.peak_window_start = window_start
    state.peak_window_wh = 100.0
    state.peak_window_degraded = True
    state.peak_sample_t = sample_t
    state.peak_sample_w = sample_w
    return state


def test_a_restart_after_a_long_outage_does_not_invent_a_month_peak():
    # The expensive failure: come back after a day down, with the house drawing
    # 8 kW right now, and back-fill the missed quarter-hours from that one live
    # reading. Each fabricated window looks complete enough to set the record, and
    # the record is the number the bill is made of — one restart would then hand
    # the month a ceiling it never actually bought.
    cfg = _peak_cfg(peak_follow_month=True)
    state = _restored(W0, sample_t=W0 + timedelta(seconds=200), sample_w=1500.0)

    down_for_a_day = W0 + timedelta(hours=24)
    update_peak_window(down_for_a_day, 8000.0, cfg, state)
    window = update_peak_window(down_for_a_day + timedelta(seconds=2), 8000.0, cfg, state)

    assert state.month_peak_w == 0.0  # nothing was measured, so nothing is recorded
    assert len(state.peak_history) == 1  # only the window we were actually in
    assert window.degraded is True  # …and we say so until the next clean boundary
    assert window.hard_w == 3900.0  # the configured limit, not a fabricated one


def test_a_restored_window_without_a_sample_clock_is_still_a_long_outage():
    # A peak store written by a build that didn't persist the sample clock. The
    # window's own start is then the oldest thing we can vouch for, and that is
    # what the outage has to be measured from — not from the first sample after
    # the restart, which is seconds old and says nothing about the day we missed.
    cfg = _peak_cfg(peak_follow_month=True)
    state = _restored(W0)  # no sample_t at all

    down_for_a_day = W0 + timedelta(hours=24)
    update_peak_window(down_for_a_day, 8000.0, cfg, state)
    window = update_peak_window(down_for_a_day + timedelta(seconds=2), 8000.0, cfg, state)

    assert state.month_peak_w == 0.0
    assert window.degraded is True


def test_a_brief_restart_still_carries_the_reading_across_the_gap():
    # The other side of the same coin: a restart of a few minutes must *not* take
    # the long-outage shortcut, or we would throw away a quarter-hour we can
    # legitimately account for. Under-counting is the error that lets a real peak
    # through.
    cfg = _peak_cfg()
    state = _restored(W0, sample_t=W0 + timedelta(seconds=60), sample_w=4000.0)
    window = update_peak_window(W0 + timedelta(seconds=300), 4000.0, cfg, state)
    assert window.start == W0  # same window we were in
    # 100 Wh restored + 4 kW held across the 240 s we were away.
    assert window.imported_wh == pytest.approx(100.0 + 4000.0 * 240 / 3600.0, abs=1.0)


# --- Cheap-hour grid charging --------------------------------------------------------

def _grid_charge_cfg(**kw) -> "engine.EngineConfig":
    base = dict(
        mode=ChargingMode.SMART,
        grid_charge_enabled=True,
        cheap_price=0.15,
        cheap_charge_power_w=2000.0,
        bright_day_target_soc=40.0,
        dark_day_target_soc=80.0,
        pv_forecast_low_kwh=8.0,
        grid_setpoint_w=50.0,
        peak_guard_enabled=True,
        peak_soft_w=3300.0,
        peak_target_w=3700.0,
        peak_hard_w=3900.0,
        peak_follow_month=False,
    )
    base.update(kw)
    return EngineConfig(**base)


def test_a_cheap_hour_commands_the_import_it_wants():
    # House 400 W, battery idle → the setpoint is the house plus the charge rate,
    # because on an ESS the setpoint *is* total grid import. (Above the shaving
    # reserve: below it the refill after a shave takes the setpoint.)
    d = decide(
        _inputs(
            car_connected=False, grid_power_w=400.0, battery_power_w=0.0,
            battery_soc=55.0, price_now=0.08, pv_forecast_kwh=2.0, now=W0,
        ),
        _grid_charge_cfg(),
        EngineState(),
    )
    assert d.grid_charging is True
    assert d.grid_setpoint_w == pytest.approx(2400.0)
    assert d.peak_reason_key == "grid_charge_dark"


def test_a_bright_tomorrow_stops_the_buying_early():
    # 55 % is already past the bright-day target: no point paying for a charge the
    # sun would have given us, and the PV needs somewhere to land.
    d = decide(
        _inputs(
            car_connected=False, grid_power_w=400.0, battery_power_w=0.0,
            battery_soc=55.0, price_now=0.08, pv_forecast_kwh=30.0, now=W0,
        ),
        _grid_charge_cfg(),
        EngineState(),
    )
    assert d.grid_charging is False
    assert d.grid_setpoint_w == 50.0
    assert d.peak_reason_key == "grid_charge_full"


def test_with_no_forecast_mapped_it_assumes_the_pessimistic_case():
    d = decide(
        _inputs(
            car_connected=False, grid_power_w=400.0, battery_power_w=0.0,
            battery_soc=55.0, price_now=0.08, now=W0,
        ),
        _grid_charge_cfg(),
        EngineState(),
    )
    assert d.grid_charging is True
    assert d.peak_reason_key == "grid_charge_dark"


def test_cheap_hour_importing_never_breaches_the_soft_limit():
    # The whole point: buying cheap energy must not buy a demand charge with it.
    d = decide(
        _inputs(
            car_connected=False, grid_power_w=2800.0, battery_power_w=0.0,
            battery_soc=55.0, price_now=0.08, now=W0,
        ),
        _grid_charge_cfg(cheap_charge_power_w=9000.0),
        EngineState(),
    )
    assert d.grid_setpoint_w == 3300.0  # the soft limit, not 2800 + 9000


def test_grid_charging_is_abandoned_the_moment_the_guard_engages():
    cfg = _grid_charge_cfg()
    state = EngineState()
    d = _run(
        cfg, state, 300, car_connected=False, grid_power_w=9000.0,
        battery_power_w=0.0, battery_soc=20.0, price_now=0.08,
    )
    assert d.peak_tier == "hard"
    assert d.grid_charging is False
    # The setpoint is the house share now: never above the target, and never the
    # cheap-hour charge rate it would otherwise have taken.
    assert d.grid_setpoint_w <= 3700.0


def test_without_battery_power_the_hard_tier_still_zeroes_the_setpoint():
    # No battery power mapped: the house share can't be measured, and the tier
    # ladder keeps its old levers.
    cfg = _grid_charge_cfg()
    state = EngineState()
    d = _run(
        cfg, state, 300, car_connected=False, grid_power_w=9000.0,
        battery_soc=20.0, price_now=0.08,
    )
    assert d.peak_tier == "hard"
    assert d.grid_charging is False
    assert d.grid_setpoint_w == 0.0


def test_an_expensive_hour_leaves_the_setpoint_at_rest():
    d = decide(
        _inputs(
            car_connected=False, grid_power_w=400.0, battery_power_w=0.0,
            battery_soc=55.0, price_now=0.40, now=W0,
        ),
        _grid_charge_cfg(),
        EngineState(),
    )
    assert d.grid_charging is False
    assert d.grid_setpoint_w == 50.0


def test_below_the_shaving_reserve_the_refill_outranks_cheap_hour_buying():
    """The refill imports the whole budget; cheap-hour charging has nothing to add
    and steps aside rather than fight it for the setpoint."""
    d = decide(
        _inputs(
            car_connected=False, grid_power_w=400.0, battery_power_w=0.0,
            battery_soc=20.0, price_now=0.08, now=W0,
        ),
        _grid_charge_cfg(),
        EngineState(),
    )
    assert d.grid_charging is False
    assert d.battery_refilling is True
    assert d.grid_setpoint_w == pytest.approx(3700.0)
    assert d.battery_min_soc == pytest.approx(20.0)  # held where it is, never above


# --- The compatibility guarantee -----------------------------------------------------

_BEHAVIOUR_FIELDS = (
    "control",
    "should_charge",
    "target_current_a",
    "target_phases",
    "write_phases",
    "surplus_w",
    "reason_key",
    "reason_params",
    "hold_battery",
    "hold_source",
    "plan",
)

# Scenarios spanning every branch of the arbiter, replayed with the peak layer both
# absent (as the engine was before this feature) and present-but-disabled.
_GOLDEN_SCENARIOS = (
    ("no car", dict(car_connected=False, grid_power_w=0.0), dict()),
    ("solar confirming", dict(grid_power_w=-5000.0, battery_soc=85.0), dict()),
    ("solar charging", dict(grid_power_w=-5000.0, battery_soc=85.0),
     dict(start_confirm_s=0.0)),
    ("below the reserve", dict(grid_power_w=-5000.0, battery_soc=50.0), dict()),
    ("no surplus", dict(grid_power_w=500.0, battery_soc=85.0), dict()),
    ("battery topping up", dict(grid_power_w=-4000.0, battery_soc=95.0),
     dict(start_confirm_s=0.0)),
    ("cheap grid", dict(grid_power_w=8000.0, battery_soc=64.0, price_now=0.10),
     dict(mode=ChargingMode.SMART, cheap_price=0.15)),
    ("cheap grid, battery draining",
     dict(grid_power_w=8000.0, battery_power_w=-500.0, battery_soc=64.0,
          price_now=0.10),
     dict(mode=ChargingMode.SMART, cheap_price=0.15)),
    ("expensive grid", dict(grid_power_w=8000.0, battery_soc=64.0, price_now=0.40),
     dict(mode=ChargingMode.SMART, cheap_price=0.15)),
    ("fast", dict(grid_power_w=0.0, battery_soc=64.0), dict(mode=ChargingMode.FAST)),
    ("solar + minimum", dict(grid_power_w=0.0, battery_soc=85.0),
     dict(mode=ChargingMode.SOLAR_MIN, min_current_a=8.0)),
    ("manual charging", dict(grid_power_w=0.0, battery_soc=85.0),
     dict(mode=ChargingMode.MANUAL, manual_charge=True, manual_current_a=10.0)),
    ("manual passive", dict(grid_power_w=0.0, battery_soc=85.0),
     dict(mode=ChargingMode.MANUAL, manual_passive=True)),
    ("smart control off", dict(grid_power_w=-5000.0, battery_soc=85.0),
     dict(smart_enabled=False)),
)


@pytest.mark.parametrize("name,inputs,cfg_kw", _GOLDEN_SCENARIOS)
def test_switched_off_the_brain_behaves_exactly_as_it_did_before(name, inputs, cfg_kw):
    """The compatibility guarantee, enforced rather than asserted in prose.

    With peak protection and cheap-hour charging off, every charging-relevant field
    must match what the engine produced before either existed — and nothing may be
    offered to the coordinator to write.
    """
    plain = decide(_inputs(now=T0, **inputs), _cfg(**cfg_kw), EngineState())
    guarded = decide(
        _inputs(now=T0, **inputs),
        _cfg(peak_guard_enabled=False, grid_charge_enabled=False, **cfg_kw),
        EngineState(),
    )
    for field in _BEHAVIOUR_FIELDS:
        assert getattr(guarded, field) == getattr(plain, field), field
    # Nothing to write: an unmapped or disabled setup is left completely alone.
    assert guarded.grid_setpoint_w is None
    assert guarded.battery_min_soc is None
    assert guarded.grid_charging is False
    assert guarded.peak_tier == "off"
    # …and the house permission collapses back onto the old single one, under which
    # the hold switch was written precisely when the brain was driving the charger.
    assert guarded.house_control == guarded.control


def test_the_measurement_runs_even_with_the_guard_switched_off():
    # Deliberate, and the one read-only exception: you can watch your peaks for a
    # month before deciding to let anything act on them.
    cfg = _cfg(peak_guard_enabled=False)
    state = EngineState()
    decide(_inputs(grid_power_w=4000.0, now=W0), cfg, state)
    d = decide(_inputs(grid_power_w=4000.0, now=W0 + timedelta(seconds=300)), cfg, state)
    assert d.peak_window_avg_w == pytest.approx(4000.0, abs=20.0)
    assert d.peak_window_ends == W0 + timedelta(seconds=900)
    assert d.peak_reason_key == "peak_off"


def test_without_a_clock_there_is_no_window_and_no_cap():
    # The stateless one-shot convention every other timer in the engine follows.
    d = decide(
        _inputs(car_connected=True, grid_power_w=9000.0, now=None),
        _peak_cfg(),
        EngineState(),
    )
    assert d.peak_tier == "off"
    assert d.peak_window_ends is None
    assert d.grid_setpoint_w is None


# --- Charging under the ceiling, not against it -------------------------------------
#
# A departure plan used to book the *cheapest* slots at *full* power: it minimised the
# number of hours by maximising the kilowatts, which is exactly the quantity a capacity
# tariff bills. These cover the plan, the request and the phase count now being sized
# from the peak target instead — and the guarantee that still outranks it.

def _slots(start, prices, minutes=60):
    return [
        PriceSlot(start=start + timedelta(minutes=minutes * i), price=p)
        for i, p in enumerate(prices)
    ]


def test_a_cheap_hour_asks_for_what_fits_under_the_ceiling():
    # 16 A x 3φ is 11 kW against a 3.7 kW target: asking for it only to be trimmed
    # wastes the slot and quotes a current we never meant to write.
    cfg = _peak_cfg(mode=ChargingMode.SMART, cheap_price=0.15, peak_follow_month=False)
    state = EngineState()
    inp = lambda t: _inputs(
        grid_power_w=500.0, price_now=0.05, battery_soc=90.0, now=W0 + timedelta(seconds=t)
    )
    d = None
    for t in range(0, 121, 20):
        d = decide(inp(t), cfg, state)
    assert d.should_charge
    # 3.7 kW target − 0.5 kW of house = 3.2 kW → 4 A on three phases, floored at the
    # 6 A the pilot signal cannot go below.
    assert d.target_current_a == pytest.approx(engine.HARDWARE_MIN_CURRENT_A)


def test_with_the_guard_off_a_cheap_hour_still_asks_for_full_power():
    cfg = _peak_cfg(
        mode=ChargingMode.SMART, cheap_price=0.15, peak_guard_enabled=False
    )
    d = decide(
        _inputs(grid_power_w=500.0, price_now=0.05, battery_soc=90.0, now=W0),
        cfg,
        EngineState(),
    )
    assert d.target_current_a == pytest.approx(16.0)


def test_the_plan_books_more_hours_rather_than_more_kilowatts():
    # The same 8 kWh, planned with and without a ceiling. Under one it has to spread.
    forecast = _slots(W0, [0.30, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.11])
    base = dict(
        mode=ChargingMode.SMART,
        target_energy_kwh=8.0,
        departure=W0 + timedelta(hours=8),
        peak_follow_month=False,
    )
    common = dict(
        grid_power_w=500.0,
        price_now=0.30,
        price_forecast=forecast,
        session_delivered_kwh=0.0,
        battery_soc=90.0,
        now=W0,
    )
    loose = decide(_inputs(**common), _peak_cfg(peak_guard_enabled=False, **base),
                   EngineState())
    tight = decide(_inputs(**common), _peak_cfg(**base), EngineState())
    assert len(loose.plan) == 1  # one hour at 11 kW covers 8 kWh
    assert len(tight.plan) > len(loose.plan)  # …but not under a 3.7 kW target


def test_the_departure_guarantee_still_outranks_the_ceiling():
    # Two hours left, 25 kWh owed: 16 A x 3φ delivers only 22 kWh in that time, so
    # not even full power makes it. The ceiling loses and the reason has to admit the
    # quarter-hour is going over.
    cfg = _peak_cfg(
        mode=ChargingMode.SMART,
        target_energy_kwh=25.0,
        departure=W0 + timedelta(hours=2),
        peak_follow_month=False,
    )
    d = decide(
        _inputs(
            grid_power_w=500.0,
            price_now=0.30,
            session_delivered_kwh=0.0,
            battery_soc=90.0,
            now=W0,
        ),
        cfg,
        EngineState(),
    )
    assert d.should_charge
    assert d.target_current_a == pytest.approx(16.0)
    assert d.reason_key == "deadline_urgent_peak"
    assert "peak limit" in d.reason


def test_a_low_ceiling_picks_one_phase_because_three_cannot_fit():
    # 6 A x 3φ is 4.14 kW and simply does not go under a 3.7 kW target; 6 A x 1φ is
    # 1.38 kW and does. Without the phase lever the guard's only options are 4.14 kW
    # or nothing.
    cfg = _peak_cfg(
        mode=ChargingMode.FAST, auto_phase=True, max_phases=3, peak_follow_month=False,
        phase_confirm_s=0.0, phase_dwell_s=0.0,
    )
    state = EngineState()
    d = None
    for t in range(0, 121, 20):
        d = decide(
            _inputs(grid_power_w=500.0, battery_soc=90.0, phases=3,
                    now=W0 + timedelta(seconds=t)),
            cfg,
            state,
        )
    assert d.target_phases == 1
    assert d.should_charge


def test_a_generous_ceiling_still_uses_three_phases():
    cfg = _peak_cfg(
        mode=ChargingMode.FAST, auto_phase=True, max_phases=3,
        peak_soft_w=20000.0, peak_target_w=22000.0, peak_hard_w=24000.0,
        peak_follow_month=False, phase_confirm_s=0.0, phase_dwell_s=0.0,
    )
    state = EngineState()
    d = None
    for t in range(0, 121, 20):
        d = decide(
            _inputs(grid_power_w=500.0, battery_soc=90.0, phases=3,
                    now=W0 + timedelta(seconds=t)),
            cfg,
            state,
        )
    assert d.target_phases == 3
    assert d.target_current_a == pytest.approx(16.0)


def test_a_car_on_pure_solar_is_not_squeezed_by_the_ceiling():
    # The ceiling credits solar and battery power the car already has: it never
    # crossed the grid meter, so withholding it would export the surplus, not
    # reduce the import.
    cfg = _peak_cfg(mode=ChargingMode.FAST, peak_follow_month=False)
    state = EngineState()
    d = None
    for t in range(0, 121, 20):
        d = decide(
            _inputs(
                grid_power_w=-2000.0,
                pv_power_w=13000.0,
                car_actual_power_w=11040.0,
                battery_soc=95.0,
                battery_power_w=0.0,
                now=W0 + timedelta(seconds=t),
            ),
            cfg,
            state,
        )
    assert d.target_current_a == pytest.approx(16.0)


def test_the_ceiling_does_not_credit_home_battery_discharge():
    # Crediting it is circular — charging harder makes the battery cover more, which
    # raises the ceiling, which charges harder — and it plans to spend a battery the
    # same cycle holds off the car. Left in, it walked the phase contactor for hours.
    cfg = _peak_cfg(mode=ChargingMode.FAST, peak_follow_month=False)
    window = engine.update_peak_window(W0, 500.0, cfg, EngineState())
    idle = engine.peak_charge_ceiling_w(
        _inputs(grid_power_w=500.0, car_actual_power_w=0.0, battery_power_w=0.0), cfg,
        window,
    )
    # Same house, but the battery is now dumping 5 kW into a running car.
    draining = engine.peak_charge_ceiling_w(
        _inputs(grid_power_w=500.0, car_actual_power_w=5000.0, battery_power_w=-5000.0),
        cfg,
        window,
    )
    assert draining == pytest.approx(idle, abs=1.0)


def test_the_ceiling_does_credit_solar_the_car_already_has():
    # Solar never crossed the grid meter, so it is real head-room — this is what keeps
    # a car on pure PV from being squeezed.
    cfg = _peak_cfg(mode=ChargingMode.FAST, peak_follow_month=False)
    window = engine.update_peak_window(W0, -2000.0, cfg, EngineState())
    ceiling = engine.peak_charge_ceiling_w(
        _inputs(
            grid_power_w=-2000.0, pv_power_w=13000.0, car_actual_power_w=11040.0,
            battery_power_w=0.0,
        ),
        cfg,
        window,
    )
    assert ceiling >= 11040.0


def _pulsing_fast(cfg, state, start_s, seconds, house_w, car_w=2400.0, step=5):
    """Fast on 1φ while the house draws ``house_w(t)``; returns the target amps seen.

    The car's draw is held flat, as it was live: a car doesn't follow a 5 s wobble.
    The tiers are pushed out of reach so only the *request* is under test.
    """
    seen = []
    for t in range(start_s, start_s + seconds + 1, step):
        house = house_w(t)
        d = decide(
            _inputs(
                now=W0 + timedelta(seconds=t), phases=1, car_actual_power_w=car_w,
                grid_power_w=house + car_w, battery_soc=78.0,
            ),
            cfg,
            state,
        )
        assert d.should_charge
        seen.append(d.target_current_a)
    return seen


def _quiet_tiers_cfg(**kw):
    return _peak_cfg(
        # The soft line sits just under the target (the three move together, so it
        # can't simply be pushed away); the loads below stay under it.
        mode=ChargingMode.FAST, peak_soft_w=3650.0, peak_hard_w=99000.0,
        max_phases=1, auto_phase=False, **kw,
    )


def test_a_pulsing_house_load_does_not_make_the_request_hunt():
    # Seen live: a ~450 W load cycling every ~10 s moved Fast's request 11↔13 A on
    # every evaluation for ten minutes, and each flip was a charger write. 3.7 kW
    # target − 0.6 kW = 13 A; − 1.05 kW = 11 A. The request takes the low one at
    # once and stays there while the pulses keep coming.
    cfg, state = _quiet_tiers_cfg(), EngineState()
    pulse = lambda t: 1050.0 if (t // 5) % 2 else 600.0
    seen = _pulsing_fast(cfg, state, 0, 600, pulse)
    assert seen[0] == 13.0
    # The start is a raise too, so the first CAR_RAMP_SETTLE_S book the 13 A asked
    # for to the car (this car is held flat below it); after that, steady at 11.
    settled = int(engine.CAR_RAMP_SETTLE_S // 5) + 1
    assert set(seen[settled:]) == {11.0}


def test_the_request_rises_once_the_load_has_stayed_low_for_the_dwell():
    cfg, state = _quiet_tiers_cfg(), EngineState()
    _pulsing_fast(cfg, state, 0, 60, lambda t: 1050.0)
    # The load is gone, but the request waits out the dwell before asking for more…
    early = _pulsing_fast(cfg, state, 65, 30, lambda t: 600.0)
    assert set(early) == {11.0}
    # …and then follows it.
    late = _pulsing_fast(cfg, state, 100, 120, lambda t: 600.0)
    assert late[-1] == 13.0


def _lagging_charger(cfg, state, start_s, seconds, house_w, first_a, step=5):
    """Closed loop with the charger's report one cycle behind the grid meter.

    The car draws what it was told within a cycle, the grid meter sees that at once,
    and the charger's own power reading arrives a cycle later — the order measured
    live on 2026-11-06 (go-e ~1–2 s behind the ESS grid reading).
    """
    told_a, reported_w, seen = first_a, first_a * 230.0, []
    for t in range(start_s, start_s + seconds + 1, step):
        drawn_w = told_a * 230.0
        d = decide(
            _inputs(
                now=W0 + timedelta(seconds=t), phases=1,
                car_actual_power_w=reported_w, grid_power_w=house_w(t) + drawn_w,
                battery_soc=78.0,
            ),
            cfg,
            state,
        )
        reported_w = drawn_w
        told_a = d.target_current_a if d.should_charge else 0.0
        seen.append(told_a)
    return seen


@pytest.mark.parametrize("soft_w", [3650.0, 3200.0])  # tiers quiet / the live limits
def test_a_raise_is_not_undone_by_the_cars_own_ramp(soft_w):
    # Seen live after v5.8.1: 6 → 13 A, and five seconds later back to 6, every
    # minute. The grid meter already held the ramping car while the charger still
    # reported 6 A, so the ramp read as +1.7 kW of house load and the raise was
    # undone, then held there by the dwell. The car sat at 6 A with room for 13.
    cfg = _peak_cfg(
        mode=ChargingMode.FAST, peak_soft_w=soft_w, peak_hard_w=99000.0,
        max_phases=1, auto_phase=False,
    )
    state = EngineState()
    _lagging_charger(cfg, state, 0, 60, lambda t: 3200.0, first_a=6.0)  # a boiler
    seen = _lagging_charger(cfg, state, 65, 300, lambda t: 580.0, first_a=6.0)
    raised = seen.index(13.0)
    assert set(seen[raised:]) == {13.0}


def test_a_real_load_during_the_settle_is_still_seen():
    # The settle books the *car's* ramp to the car; a boiler switching on in the very
    # next cycle after a raise must still cut the request at once.
    cfg, state = _quiet_tiers_cfg(), EngineState()
    _lagging_charger(cfg, state, 0, 60, lambda t: 3200.0, first_a=6.0)
    told_a, reported_w, boiler, t = 6.0, 6 * 230.0, False, 65
    while True:
        drawn_w = told_a * 230.0
        house = 3200.0 if boiler else 580.0
        d = decide(
            _inputs(
                now=W0 + timedelta(seconds=t), phases=1, car_actual_power_w=reported_w,
                grid_power_w=house + drawn_w, battery_soc=78.0,
            ),
            cfg,
            state,
        )
        if boiler:
            break
        if d.target_current_a == 13.0:
            boiler = True  # on in the cycle right after the raise was written
        reported_w, told_a, t = drawn_w, d.target_current_a, t + 5
        assert t < 400, "never raised"
    # 3.7 kW − 3.2 kW of house leaves ~2 A: the 6 A floor, not 13.
    assert d.target_current_a == 6.0


def test_the_request_still_falls_at_once():
    # Asking for less is never delayed: that is the direction a slow answer costs.
    cfg, state = _quiet_tiers_cfg(), EngineState()
    _pulsing_fast(cfg, state, 0, 120, lambda t: 600.0)
    assert _pulsing_fast(cfg, state, 125, 0, lambda t: 1500.0) == [9.0]


# --- Hysteresis, readiness and stocking up -------------------------------------------
#
# All three come out of a 15-day closed-loop simulation against a 4 kW ceiling
# (tools/sim/peak15.py). See the notes on each test for what it actually cost.

def test_grid_charging_does_not_chatter_once_it_reaches_its_target():
    """Reaching the target must not hand the setpoint straight back.

    Without a resume band the setpoint flips between "import hard" and "import
    nothing" every cycle at the target, and the pack pays a round-trip loss on each
    flip — 115 kWh over a simulated fortnight.
    """
    cfg = _grid_charge_cfg(dark_day_target_soc=80.0)
    state = EngineState()

    def at(soc: float):
        return decide(
            _inputs(
                car_connected=False, grid_power_w=400.0, battery_power_w=0.0,
                battery_soc=soc, price_now=0.08, pv_forecast_kwh=2.0, now=W0,
            ),
            cfg, state,
        )

    band = engine._GRID_CHARGE_RESUME_BAND_PCT
    assert band > 0.0
    assert at(60.0).grid_charging is True     # well below → buy
    assert at(80.0).grid_charging is False    # target reached → stop
    # Just under the target is exactly where the old code restarted. It must not.
    assert at(80.0 - band / 2).grid_charging is False
    assert at(80.0 - band - 1.0).grid_charging is True   # a real dip → buy again
    # …and once buying again it runs all the way back up, rather than stopping the
    # moment it re-crosses the resume point.
    assert at(80.0 - band + 0.5).grid_charging is True


def test_without_a_forecast_the_dark_day_reserve_is_a_flat_level_the_refill_keeps():
    """The old "keep ready for peaks", now done by the refill — and held.

    A pack sitting on its floor defends nothing, and in a dark winter week the few
    cheap hours a day do not keep up with the house, so the price is not the
    question. Unlike the old readiness path it buys at the *budget* (the refill),
    and holds what it has rather than letting ordinary loads cycle it.
    """
    cfg = _grid_charge_cfg(peak_ready_soc=60.0)
    d = decide(
        _inputs(
            car_connected=False, grid_power_w=400.0, battery_power_w=0.0,
            battery_soc=52.0, price_now=0.42, now=W0,
        ),
        cfg, EngineState(),
    )
    assert d.reserve_day == "flat"
    assert d.reserve_fill_soc == pytest.approx(60.0)
    assert d.battery_refilling is True
    assert d.grid_charging is False  # the refill owns the setpoint, not grid charging
    assert d.grid_setpoint_w == pytest.approx(3700.0)
    assert d.peak_reason_key == "peak_ready"
    assert d.battery_min_soc == pytest.approx(52.0)  # held where it is, not spent


def test_the_dark_day_reserve_does_nothing_at_or_below_the_shaving_reserve():
    cfg = _grid_charge_cfg(peak_ready_soc=50.0, shaving_reserve_soc=50.0)
    d = decide(
        _inputs(
            car_connected=False, grid_power_w=400.0, battery_power_w=0.0,
            battery_soc=52.0, price_now=0.42, now=W0,
        ),
        cfg, EngineState(),
    )
    assert d.reserve_day == ""
    assert d.battery_refilling is False
    assert d.grid_setpoint_w == pytest.approx(50.0)


def test_the_dark_day_reserve_is_ignored_when_peak_protection_is_off():
    """It exists to keep the guard supplied; with nothing to defend it must not buy."""
    cfg = _grid_charge_cfg(peak_ready_soc=60.0, peak_guard_enabled=False)
    d = decide(
        _inputs(
            car_connected=False, grid_power_w=400.0, battery_power_w=0.0,
            battery_soc=30.0, price_now=0.42, pv_forecast_kwh=2.0, now=W0,
        ),
        cfg, EngineState(),
    )
    assert d.grid_charging is False
    assert d.battery_refilling is False


# --- The reserve plan: stock for a dark day, room for a bright one -------------------
#
# Chris's numbers: a 30.5 kWh pack, 10.5 kWh of PV the house uses as it comes (his
# median, Sep–Nov 2026), shaving reserve 50 %, dark-day reserve 90 %.

def _plan_cfg(**kw) -> "engine.EngineConfig":
    base = dict(
        peak_guard_enabled=True, shaving_reserve_soc=50.0, peak_ready_soc=90.0,
        battery_capacity_kwh=30.5, solar_self_use_kwh=10.5, local_tz=VIENNA,
    )
    base.update(kw)
    return EngineConfig(**base)


def _at_local(hour: int, day: int = 7) -> datetime:
    return datetime(2026, 11, day, hour, 0, tzinfo=VIENNA).astimezone(timezone.utc)


def _plan(cfg, state=None, **kw):
    state = state if state is not None else EngineState()
    return engine.reserve_plan(cfg, _inputs(**kw), state)


def test_the_night_before_a_dark_day_stocks_the_battery_to_the_top():
    p = _plan(_plan_cfg(), now=_at_local(22), sun_up=False, pv_forecast_kwh=4.0)
    assert p.day == "tomorrow"
    assert p.forecast_kwh == pytest.approx(4.0)
    assert p.hold_soc == pytest.approx(90.0)
    assert p.fill_soc == pytest.approx(90.0)


def test_the_night_before_a_bright_day_leaves_the_sun_its_room():
    # 22 kWh − 10.5 used as it comes = 11.5 kWh of surplus = 37.7 % of the pack.
    p = _plan(_plan_cfg(), now=_at_local(22), sun_up=False, pv_forecast_kwh=22.0)
    assert p.hold_soc == pytest.approx(100.0 - 100.0 * 11.5 / 30.5)
    assert p.fill_soc == pytest.approx(p.hold_soc)
    # A summer-bright day wants more room than there is: the shaving reserve, i.e.
    # exactly what the battery did before there was a plan.
    p = _plan(_plan_cfg(), now=_at_local(22), sun_up=False, pv_forecast_kwh=40.0)
    assert p.hold_soc == pytest.approx(50.0)


def test_after_midnight_the_coming_day_is_today():
    """"Tomorrow" at 02:00 is the day *after* the one about to start."""
    p = _plan(_plan_cfg(), now=_at_local(2), sun_up=False,
              pv_forecast_today_kwh=4.0, pv_forecast_kwh=30.0)
    assert p.day == "today"
    assert p.hold_soc == pytest.approx(90.0)


def test_with_only_tomorrow_mapped_the_evening_reading_carries_past_midnight():
    cfg = _plan_cfg()
    state = EngineState()
    evening = _inputs(now=_at_local(22, day=6), sun_up=False, pv_forecast_kwh=4.0)
    engine._note_solar_forecast(evening, cfg, state)
    # 02:00 on the 7th: the sensor now reads the 8th (bright) — the plan must still
    # be preparing for the dark 7th.
    p = _plan(cfg, state, now=_at_local(2), sun_up=False, pv_forecast_kwh=30.0)
    assert p.forecast_kwh == pytest.approx(4.0)
    assert p.hold_soc == pytest.approx(90.0)
    # A reading for some other night is no evidence about this one: fall back to
    # the flat level, the pessimistic case.
    p = _plan(cfg, EngineState(), now=_at_local(2), sun_up=False, pv_forecast_kwh=30.0)
    assert p.day == "flat"
    assert p.hold_soc == pytest.approx(90.0)


def test_by_day_it_buys_only_what_the_sun_will_not_deliver():
    """A bright today before a dark tomorrow, at 13:00.

    Tonight wants 90 %. The rest of today brings 6 kWh, of which the house uses its
    share (10.5 × 6/22 kWh) — the other 3.1 kWh, 10.3 % of the pack, is the sun's.
    So the refill buys to 79.7 % and the afternoon does the rest.
    """
    p = _plan(_plan_cfg(), now=_at_local(13), sun_up=True, pv_forecast_today_kwh=22.0,
              pv_forecast_remaining_kwh=6.0, pv_forecast_kwh=4.0)
    still_room = 100.0 * (6.0 - 10.5 * 6.0 / 22.0) / 30.5
    assert p.fill_soc == pytest.approx(90.0 - still_room)
    # …and holds what it has meanwhile: the stock is for tonight, not the afternoon.
    assert p.hold_soc == pytest.approx(p.fill_soc)


def test_a_dark_day_keeps_its_stock_even_before_a_bright_tomorrow():
    """Bought last night for today's peaks: the afternoon doesn't get to spend it.
    The release comes at sunset, when the coming day becomes tomorrow."""
    cfg = _plan_cfg()
    day = _plan(cfg, now=_at_local(13), sun_up=True, pv_forecast_today_kwh=3.0,
                pv_forecast_remaining_kwh=1.0, pv_forecast_kwh=25.0)
    assert day.hold_soc == pytest.approx(90.0)
    assert day.fill_soc == pytest.approx(100.0 - 100.0 * 14.5 / 30.5)  # tomorrow's
    night = _plan(cfg, now=_at_local(18), sun_up=False, pv_forecast_today_kwh=3.0,
                  pv_forecast_remaining_kwh=0.0, pv_forecast_kwh=25.0)
    assert night.hold_soc == pytest.approx(100.0 - 100.0 * 14.5 / 30.5)


def test_by_day_without_a_remaining_forecast_it_waits_for_the_night():
    p = _plan(_plan_cfg(), now=_at_local(13), sun_up=True, pv_forecast_today_kwh=3.0,
              pv_forecast_kwh=4.0)
    assert p.fill_soc == pytest.approx(50.0)
    assert p.hold_soc == pytest.approx(90.0)


def test_without_sun_sun_the_clock_stands_in():
    cfg = _plan_cfg()
    assert engine._solar_clock(_inputs(now=_at_local(12)), cfg)[0] is True
    assert engine._solar_clock(_inputs(now=_at_local(17)), cfg)[0] is False
    # 05:00 is still before the coming day; 17:00 is after it.
    assert engine._solar_clock(_inputs(now=_at_local(5)), cfg)[1] is True
    assert engine._solar_clock(_inputs(now=_at_local(17)), cfg)[1] is False


def test_without_a_battery_capacity_the_plan_cannot_size_room_and_stays_flat():
    p = _plan(_plan_cfg(battery_capacity_kwh=0.0), now=_at_local(22), sun_up=False,
              pv_forecast_kwh=30.0)
    assert p.day == "flat"
    assert p.hold_soc == pytest.approx(90.0)


def test_a_dark_night_refills_at_the_budget_and_the_car_waits():
    """Battery first, as for any refill (Chris, Nov 2026): a dark night can't fill
    both within the limit, and the stock is what the peaks are defended with."""
    cfg = _plan_cfg(
        mode=ChargingMode.FAST, smart_enabled=True, max_current_a=16.0,
        peak_soft_w=3300.0, peak_target_w=3700.0, peak_hard_w=3900.0,
        peak_follow_month=False, grid_setpoint_w=50.0,
    )
    state = EngineState()
    now = _at_local(22)
    d = None
    for k in range(3):  # a trustworthy reading must arrive before the guard acts
        d = decide(
            _inputs(
                car_connected=True, car_actual_power_w=0.0, grid_power_w=500.0,
                battery_power_w=0.0, battery_soc=60.0, sun_up=False,
                pv_forecast_kwh=4.0, now=now + timedelta(seconds=10 * k),
            ),
            cfg, state,
        )
    assert d.battery_refilling is True
    assert d.grid_setpoint_w == pytest.approx(3700.0)
    assert d.should_charge is False
    assert d.peak_reason_key == "peak_dark_day_car"
    assert d.peak_reason_params["forecast"] == "4"
    assert d.peak_reason_params["reserve"] == "90"
    assert d.battery_min_soc == pytest.approx(60.0)  # never above the charge


def test_a_cheap_hour_after_midnight_judges_today_not_the_day_after():
    """The old bug: at 02:00 the "tomorrow" sensor already describes the day after."""
    cfg = _grid_charge_cfg(local_tz=VIENNA)
    d = decide(
        _inputs(
            car_connected=False, grid_power_w=400.0, battery_power_w=0.0,
            battery_soc=55.0, price_now=0.08, sun_up=False, now=_at_local(2),
            pv_forecast_today_kwh=30.0, pv_forecast_kwh=2.0,
        ),
        cfg, EngineState(),
    )
    # Today is bright: 55 % is already past the bright-day target.
    assert d.grid_charging is False
    assert d.peak_reason_key == "grid_charge_full"


def test_stocking_up_buys_at_any_price_and_holds_what_it_bought():
    """The hold is the half that matters.

    Filling before a known evening and then letting the ordinary afternoon serve
    itself from the pack donates the whole stock to hours the grid could have
    carried at a third of the ceiling. So the resting reserve rises with it — but
    only as far as the battery has got: a minimum SoC above the charge makes the
    ESS recharge at full power, which is the peak the stock is meant to prevent.
    """
    cfg = _grid_charge_cfg(stock_up=True, stock_up_target_soc=95.0,
                           shaving_reserve_soc=50.0)
    d = decide(
        _inputs(
            car_connected=False, grid_power_w=400.0, battery_power_w=0.0,
            battery_soc=60.0, price_now=0.42, pv_forecast_kwh=30.0, now=W0,
        ),
        cfg, EngineState(),
    )
    # With peak protection on, stocking up is the refill with a higher goal: the
    # whole budget, not the cheap-hour rate under the soft line.
    assert d.battery_refilling is True
    assert d.grid_setpoint_w == pytest.approx(3700.0)
    assert d.peak_reason_key == "peak_stock_up"
    assert d.peak_reason_params["reserve"] == "95"
    assert d.battery_min_soc == pytest.approx(60.0)  # held where it is, not spent


def test_stocking_up_never_raises_the_floor_the_event_will_need():
    """Holding at 95 % while resting must not stop the guard reaching the stock at
    18:30 — the shaving floor still comes off the raw reserve."""
    cfg = _peak_cfg(stock_up=True, stock_up_target_soc=95.0,
                    shaving_reserve_soc=50.0, peak_min_soc=35.0)
    assert engine._resting_reserve_soc(cfg) == pytest.approx(95.0)
    assert engine._peak_soc_floor(cfg) == pytest.approx(35.0)


def test_stocking_up_holds_the_battery_with_peak_protection_switched_off():
    """The switch is a user action, not part of the guard: it has to work on its own
    or the fill happens and the hold silently does not."""
    cfg = _grid_charge_cfg(stock_up=True, stock_up_target_soc=95.0,
                           peak_guard_enabled=False, shaving_reserve_soc=50.0)
    d = decide(
        _inputs(
            car_connected=False, grid_power_w=400.0, battery_power_w=0.0,
            battery_soc=60.0, price_now=0.42, pv_forecast_kwh=2.0, now=W0,
        ),
        cfg, EngineState(),
    )
    assert d.grid_charging is True
    assert d.battery_min_soc == pytest.approx(60.0)  # the hold, at the charge reached


def test_the_new_levers_are_all_off_by_default():
    """Defaults must leave a existing install byte-for-byte where it was."""
    cfg = EngineConfig()
    assert cfg.peak_ready_soc == 0.0
    assert cfg.stock_up is False
    assert engine._resting_reserve_soc(cfg) == cfg.shaving_reserve_soc


# --- The house share: grid up to the budget, the battery only the excess -------------
#
# Readings below are what an ESS at its resting 100 W setpoint reports while the
# battery carries a load: grid ≈ 100 W, battery = −(load − 100). The engine only ever
# uses their difference (the net load), which the setpoint can't move.

def _ess(load_w: float, *, setpoint_w: float = 100.0, **kw) -> dict:
    return dict(grid_power_w=setpoint_w, battery_power_w=-(load_w - setpoint_w), **kw)


def _share_cfg(**kw) -> "engine.EngineConfig":
    return _peak_cfg(**{"mode": ChargingMode.SMART, "grid_setpoint_w": 100.0, **kw})


def _step(cfg, state, seconds, **kw):
    return decide(_inputs(now=W0 + timedelta(seconds=seconds), **kw), cfg, state)


def test_a_heavy_load_hands_the_grid_its_share_and_the_battery_the_rest():
    # A 9.6 kW sauna evening: the grid carries the target, the battery the excess,
    # instead of the battery carrying all of it until its reserve.
    cfg, state = _share_cfg(), EngineState()
    d = _step(cfg, state, 0, car_connected=False, battery_soc=70.0, **_ess(9600.0))
    assert d.grid_setpoint_w == 3700.0
    assert d.battery_min_soc == 35.0  # the floor: the battery may go deep for this
    assert d.hold_battery is False and d.hold_source == "peak"
    assert d.peak_reason_key == "peak_share"
    assert d.peak_reason_params["battery"] == "5.9"


def test_the_setpoint_follows_the_load_down_so_the_battery_never_charges_from_grid():
    # The thermostat switches the heater off: a setpoint left at 3.7 kW would make
    # the ESS charge the battery from the grid at 2.8 kW. It follows the load instead.
    cfg, state = _share_cfg(), EngineState()
    _step(cfg, state, 0, car_connected=False, battery_soc=70.0, **_ess(9600.0))
    d = _step(
        cfg, state, 40, car_connected=False, battery_soc=70.0,
        **_ess(900.0, setpoint_w=3700.0),
    )
    assert d.grid_setpoint_w == 900.0
    assert state.peak_share_engaged is True  # still the sauna's evening


def test_the_share_releases_only_after_the_house_stays_calm():
    cfg, state = _share_cfg(peak_release_s=120.0), EngineState()
    _step(cfg, state, 0, car_connected=False, battery_soc=70.0, **_ess(9600.0))
    for t in range(40, 160, 10):
        _step(cfg, state, t, car_connected=False, battery_soc=70.0, **_ess(900.0))
    assert state.peak_share_engaged is True  # 120 s not yet over
    d = _step(cfg, state, 200, car_connected=False, battery_soc=70.0, **_ess(900.0))
    assert state.peak_share_engaged is False
    assert d.grid_setpoint_w == 100.0
    assert d.battery_min_soc == 50.0  # back at the resting reserve


def test_a_car_pushing_the_total_over_is_trimmed_not_shaved_by_the_battery():
    # Today's live test: Fast on one phase, a quiet house. The car is the steerable
    # load, so the battery is not drawn into it — no hold release, no min-SoC drop,
    # nothing to fight itself over.
    cfg, state = _share_cfg(mode=ChargingMode.FAST), EngineState()
    d = None
    for t in range(0, 300, 10):
        d = _step(
            cfg, state, t, car_connected=True, phases=1, car_actual_power_w=3400.0,
            battery_soc=79.0, grid_power_w=4300.0, battery_power_w=0.0,
        )
    assert state.peak_share_engaged is False
    assert d.battery_min_soc == 50.0
    assert d.hold_source != "peak"


def test_a_car_displaced_by_the_house_pauses_and_comes_back_with_the_room():
    # The sauna takes the whole share: the car pauses rather than lean on the
    # battery. When the thermostat switches the heater off there is room again, and
    # the car resumes — no held pause, which on heat-pump nights starved the car.
    cfg, state = _share_cfg(mode=ChargingMode.FAST), EngineState()

    def at(t, load):
        return _step(
            cfg, state, t, car_connected=True, phases=1, battery_soc=70.0,
            car_actual_power_w=0.0, **_ess(load),
        )

    d = at(0, 9600.0)
    assert d.should_charge is False
    assert d.peak_reason_key == "peak_pause"
    for t in range(10, 300, 10):
        d = at(t, 9600.0)
        assert d.should_charge is False
    d = at(300, 900.0)
    assert d.should_charge is True  # 2.8 kW of room: the car fits at 1φ


def test_the_battery_never_carries_the_cars_minimum_in_a_heavy_load():
    # Even well above the reserve: on a sauna evening that energy is the sauna's.
    cfg, state = _share_cfg(mode=ChargingMode.FAST), EngineState()
    d = _step(
        cfg, state, 0, car_connected=True, phases=3, battery_soc=95.0,
        car_actual_power_w=0.0, **_ess(9600.0),
    )
    assert d.should_charge is False


def test_a_battery_running_short_hands_the_grid_more_before_it_is_empty():
    # 38 % on a 30.5 kWh pack with a 35 % floor is ~0.9 kWh: at 5.9 kW of excess
    # that's nine minutes. Rather than run it dry and then drop the whole load on
    # the grid, the grid's share rises now.
    cfg, state = _share_cfg(battery_capacity_kwh=30.5), EngineState()
    d = _step(cfg, state, 0, car_connected=False, battery_soc=38.0, **_ess(9600.0))
    assert d.grid_setpoint_w > 3700.0
    assert d.peak_reason_key == "peak_share_paced"
    # Without the capacity it shaves fully until the floor.
    cfg2, state2 = _share_cfg(), EngineState()
    d2 = _step(cfg2, state2, 0, car_connected=False, battery_soc=38.0, **_ess(9600.0))
    assert d2.grid_setpoint_w == 3700.0


def test_a_full_battery_is_not_paced():
    cfg, state = _share_cfg(battery_capacity_kwh=30.5), EngineState()
    d = _step(cfg, state, 0, car_connected=False, battery_soc=90.0, **_ess(9600.0))
    assert d.grid_setpoint_w == 3700.0
    assert d.peak_reason_key == "peak_share"


def test_grid_charging_waits_while_the_share_is_engaged():
    cfg = _grid_charge_cfg(grid_setpoint_w=100.0)
    state = EngineState()
    d = _step(
        cfg, state, 30, car_connected=False, battery_soc=30.0, price_now=0.05,
        **_ess(9600.0),
    )
    assert state.peak_share_engaged is True
    assert d.grid_charging is False
    assert d.grid_setpoint_w <= 3700.0


def test_small_budget_drift_does_not_rewrite_the_setpoint():
    cfg, state = _share_cfg(), EngineState()
    first = _step(cfg, state, 0, car_connected=False, battery_soc=70.0, **_ess(9600.0))
    # A slightly smaller load: well within the move threshold, so no new write.
    second = _step(
        cfg, state, 40, car_connected=False, battery_soc=70.0,
        **_ess(9500.0, setpoint_w=first.grid_setpoint_w),
    )
    assert second.grid_setpoint_w == first.grid_setpoint_w


# --- After a shave: the minimum SoC never above the charge, the refill by setpoint ---
#
# A Victron ESS treats a minimum SoC above the battery's charge as an order to
# recharge at full power (live, Nov 2026). Raising it from the shaving floor back to
# the reserve at the end of a shave bought exactly the peak the shave had avoided.


def test_a_shave_ending_below_the_reserve_holds_the_battery_where_it_is():
    cfg, state = _share_cfg(peak_release_s=120.0), EngineState()
    _step(cfg, state, 0, car_connected=False, battery_soc=41.6, **_ess(9600.0))
    d = None
    for t in range(40, 400, 10):
        d = _step(cfg, state, t, car_connected=False, battery_soc=41.6, **_ess(900.0))
    assert state.peak_share_engaged is False
    assert d.battery_min_soc == 41.0  # never above the charge, never the 50 % reserve


def test_the_refill_imports_the_budget_and_the_minimum_soc_trails_the_charge():
    cfg, state = _share_cfg(), EngineState()
    d = _step(cfg, state, 0, car_connected=False, battery_soc=40.3, **_ess(900.0))
    assert d.battery_refilling is True
    assert d.grid_setpoint_w == 3700.0  # the target: free on the demand charge
    assert d.battery_min_soc == 40.0
    assert d.peak_reason_key == "peak_refill"
    assert d.peak_reason_params == {
        "soc": "40", "reserve": "50", "grid": "3.7", "target": "3.70",
    }
    d = _step(cfg, state, 60, car_connected=False, battery_soc=46.2, **_ess(900.0))
    assert d.battery_min_soc == 46.0  # follows the fill up, one step behind it


def test_the_refill_waits_for_a_real_dip_and_runs_to_the_reserve():
    cfg, state = _share_cfg(), EngineState()
    assert _step(cfg, state, 0, car_connected=False, battery_soc=48.5,
                 **_ess(900.0)).battery_refilling is False  # inside the band
    assert _step(cfg, state, 10, car_connected=False, battery_soc=47.5,
                 **_ess(900.0)).battery_refilling is True
    assert _step(cfg, state, 20, car_connected=False, battery_soc=49.6,
                 **_ess(900.0)).battery_refilling is True  # runs on to the reserve
    d = _step(cfg, state, 30, car_connected=False, battery_soc=50.0, **_ess(900.0))
    assert d.battery_refilling is False
    assert d.grid_setpoint_w == 100.0
    assert d.battery_min_soc == 50.0


def test_the_refill_never_sizes_past_what_is_left_of_the_quarter_hour():
    # A heavy start leaves the rest of the window less than the target.
    cfg, state = _share_cfg(), EngineState()
    inp = _inputs(now=W0, battery_soc=40.0, grid_power_w=900.0, battery_power_w=0.0)
    window = engine.update_peak_window(W0, 900.0, cfg, state)
    share = engine._house_share(inp, cfg, state, window)
    tight = replace(window, allowed_w=2450.0)
    plain = engine.Decision(control=True)
    assert engine._refill_setpoint(plain, inp, cfg, state, tight, share) == 2400.0
    # …and a budget that grows a little later doesn't chase every watt.
    roomier = replace(window, allowed_w=2650.0)
    assert engine._refill_setpoint(plain, inp, cfg, state, roomier, share) == 2400.0
    # A budget that shrinks is followed at once.
    tighter = replace(window, allowed_w=1950.0)
    assert engine._refill_setpoint(plain, inp, cfg, state, tighter, share) == 1900.0


def test_the_battery_comes_first_the_car_waits_for_the_refill():
    cfg, state = _share_cfg(mode=ChargingMode.FAST), EngineState()
    d = _step(cfg, state, 0, car_connected=True, phases=3, car_actual_power_w=0.0,
              battery_soc=40.0, grid_power_w=900.0, battery_power_w=0.0)
    assert d.battery_refilling is True
    assert d.should_charge is False
    assert d.reason_key == "peak_refill_car"
    assert d.grid_setpoint_w == 3700.0
    # Back at the reserve, the car gets its room again.
    d = _step(cfg, state, 30, car_connected=True, phases=3, car_actual_power_w=0.0,
              battery_soc=50.0, grid_power_w=900.0, battery_power_w=0.0)
    assert d.battery_refilling is False
    assert d.should_charge is True


def test_the_refill_steps_aside_for_the_departure_guarantee():
    cfg, state = _share_cfg(), EngineState()
    inp = _inputs(now=W0, battery_soc=40.0, grid_power_w=900.0, battery_power_w=0.0)
    window = engine.update_peak_window(W0, 900.0, cfg, state)
    share = engine._house_share(inp, cfg, state, window)
    urgent = engine.Decision(
        control=True, should_charge=True, reason_key="deadline_urgent"
    )
    assert engine._refill_setpoint(urgent, inp, cfg, state, window, share) is None
    assert state.peak_refilling is True  # suspended, not forgotten
    plain = engine.Decision(control=True, should_charge=True, reason_key="fast")
    assert engine._refill_setpoint(plain, inp, cfg, state, window, share) == 3700.0


def test_the_refill_pauses_while_the_house_share_needs_the_battery():
    cfg, state = _share_cfg(), EngineState()
    d = _step(cfg, state, 0, car_connected=False, battery_soc=40.0, **_ess(9600.0))
    assert state.peak_share_engaged is True
    assert d.battery_refilling is False
    assert d.battery_min_soc == 35.0  # shaving: the floor
    assert d.grid_setpoint_w == 3700.0  # the share, not the refill


def test_a_refill_in_a_partly_unmeasured_window_waits():
    cfg, state = _share_cfg(), EngineState()
    inp = _inputs(now=W0, battery_soc=40.0, grid_power_w=900.0, battery_power_w=0.0)
    window = engine.update_peak_window(W0, 900.0, cfg, state)
    share = engine._house_share(inp, cfg, state, window)
    blind = replace(window, degraded=True)
    plain = engine.Decision(control=True)
    assert engine._refill_setpoint(plain, inp, cfg, state, blind, share) is None


def test_a_charger_the_brain_is_not_driving_is_not_paused_by_the_refill():
    # Smart control off: only the hard tier may stop a charger we aren't driving.
    cfg, state = _share_cfg(smart_enabled=False), EngineState()
    d = _step(cfg, state, 0, car_connected=True, phases=3, car_actual_power_w=0.0,
              battery_soc=40.0, grid_power_w=900.0, battery_power_w=0.0)
    assert d.battery_refilling is True
    assert d.control is False


def test_switching_peak_protection_off_forgets_the_refill():
    cfg, state = _grid_charge_cfg(), EngineState()
    _step(cfg, state, 0, car_connected=False, battery_soc=40.0,
          grid_power_w=400.0, battery_power_w=0.0)
    assert state.peak_refill_setpoint_w is not None
    off = _grid_charge_cfg(peak_guard_enabled=False)
    d = _step(off, state, 10, car_connected=False, battery_soc=40.0,
              grid_power_w=400.0, battery_power_w=0.0, price_now=0.08)
    assert state.peak_refill_setpoint_w is None
    assert d.grid_charging is True  # cheap-hour charging is no longer stood aside


def test_without_battery_power_the_tier_ladder_still_caps_the_minimum_soc():
    cfg, state = _peak_cfg(), EngineState()
    d = _step(cfg, state, 0, car_connected=False, battery_soc=38.2,
              grid_power_w=900.0)
    assert d.battery_refilling is False  # no refill without the battery's power
    assert d.battery_min_soc == 38.0


def test_with_the_soc_unknown_the_minimum_soc_may_fall_but_never_rise():
    state = EngineState()
    d = engine.Decision(control=True, battery_min_soc=50.0)
    engine._limit_min_soc(d, _inputs(battery_soc=42.4), state)
    assert d.battery_min_soc == 42.0
    d = engine.Decision(control=True, battery_min_soc=50.0)
    engine._limit_min_soc(d, _inputs(battery_soc=None), state)
    assert d.battery_min_soc == 42.0  # not back up to 50 blind
    d = engine.Decision(control=True, battery_min_soc=35.0)
    engine._limit_min_soc(d, _inputs(battery_soc=None), state)
    assert d.battery_min_soc == 35.0  # a drop is always safe


def test_with_the_soc_never_seen_the_minimum_soc_is_left_alone():
    d = engine.Decision(control=True, battery_min_soc=50.0)
    engine._limit_min_soc(d, _inputs(battery_soc=None), EngineState())
    assert d.battery_min_soc is None
    assert d.min_soc_skip is True  # not a hand-back: write nothing at all


def test_a_minimum_soc_rounds_down_onto_the_entity_grid():
    assert engine.floor_to_step(43.0, 5.0) == 40.0
    assert engine.floor_to_step(45.0, 5.0) == 45.0
    assert engine.floor_to_step(44.999999999, 5.0) == 45.0  # float noise, not a step
    assert engine.floor_to_step(43.0, None) == 43.0
    assert engine.floor_to_step(12.0, 5.0, minimum=10.0) == 10.0


def test_a_hand_back_upward_follows_the_battery():
    release = engine.min_soc_release_value
    assert release(30.0, 50.0, 41.0) == (30.0, True)   # downward: at once
    assert release(50.0, 35.0, 60.0) == (50.0, True)   # battery above it: at once
    assert release(50.0, 35.0, 41.7) == (41.0, False)  # follow the charge up
    assert release(50.0, 41.0, 41.9) == (None, False)  # nothing new to write
    assert release(50.0, 35.0, None) == (None, False)  # blind: keep what is there


def test_a_held_minimum_soc_does_not_walk_down_with_the_charge():
    # The ESS holds 50 %, the battery reads 49.9: that is the hold working, and
    # capping down to it would let the battery discharge one step further each lap.
    state = EngineState()
    d = engine.Decision(control=True, battery_min_soc=50.0)
    engine._limit_min_soc(d, _inputs(battery_soc=50.2), state)
    assert d.battery_min_soc == 50.0
    d = engine.Decision(control=True, battery_min_soc=50.0)
    engine._limit_min_soc(d, _inputs(battery_soc=49.9), state)
    assert d.battery_min_soc == 50.0
    # A shave still takes it down at once, and the raise after it is capped again.
    d = engine.Decision(control=True, battery_min_soc=35.0)
    engine._limit_min_soc(d, _inputs(battery_soc=49.0), state)
    assert d.battery_min_soc == 35.0
    d = engine.Decision(control=True, battery_min_soc=50.0)
    engine._limit_min_soc(d, _inputs(battery_soc=41.5), state)
    assert d.battery_min_soc == 41.0



def test_stocking_up_fills_at_the_target_without_cheap_hour_charging():
    # The switch is the user's: with peak protection on it needs nothing else.
    cfg, state = _share_cfg(stock_up=True, stock_up_target_soc=95.0), EngineState()
    d = _step(cfg, state, 0, car_connected=False, battery_soc=70.0, **_ess(900.0))
    assert d.battery_refilling is True
    assert d.grid_setpoint_w == 3700.0
    assert d.battery_min_soc == 70.0


def test_while_stocking_up_the_car_waits_and_is_told_why():
    cfg = _share_cfg(mode=ChargingMode.FAST, stock_up=True, stock_up_target_soc=95.0)
    d = _step(cfg, EngineState(), 0, car_connected=True, phases=3,
              car_actual_power_w=0.0, battery_soc=70.0,
              grid_power_w=900.0, battery_power_w=0.0)
    assert d.should_charge is False
    assert d.reason_key == "peak_stock_up_car"


# --- The house share against meters that don't report together (Nov 2026) ----------
#
# Live, a 2.6 kW car start read as 2.6 kW of *house* load: the grid meter had seen the
# step, the battery reading came after the ESS had taken it over, and the difference
# counted it twice. The share engaged, the setpoint sat above the load and the ESS
# charged the battery from the grid. tools/sim/meter_skew.py reproduces it.

def _quiet_then(cfg, state, *, until=30, **kw):
    """A quiet house (900 W, battery covering it) for ``until`` seconds."""
    for t in range(0, until, 5):
        _step(cfg, state, t, car_connected=False, battery_soc=70.0, **_ess(900.0), **kw)


def test_a_meter_glitch_engages_the_share_but_the_setpoint_stays_at_the_real_load():
    cfg, state = _share_cfg(), EngineState()
    _quiet_then(cfg, state)
    # Grid caught the step, battery reading already after the ESS answered it.
    d = _step(cfg, state, 30, car_connected=False, battery_soc=70.0,
              grid_power_w=2300.0, battery_power_w=-2900.0)
    assert state.peak_share_engaged is True  # engaging frees a held battery: at once
    assert d.battery_min_soc == 35.0
    assert d.grid_setpoint_w == 900.0  # the held load, not the 5.2 kW glitch
    assert d.house_load_source == "derived"


def test_a_real_heavy_load_reaches_the_setpoint_once_it_has_held():
    cfg, state = _share_cfg(), EngineState()
    _quiet_then(cfg, state)
    d = _step(cfg, state, 30, car_connected=False, battery_soc=70.0, **_ess(9600.0))
    assert state.peak_share_engaged is True
    assert d.grid_setpoint_w == 900.0  # the battery carries it while it proves itself
    d = _step(cfg, state, 40, car_connected=False, battery_soc=70.0, **_ess(9600.0))
    assert d.grid_setpoint_w == 900.0
    d = _step(cfg, state, 50, car_connected=False, battery_soc=70.0, **_ess(9600.0))
    assert d.grid_setpoint_w == 3700.0  # held for 15 s: the grid takes its share


def test_a_measured_house_load_is_used_as_read():
    cfg, state = _share_cfg(), EngineState()
    _quiet_then(cfg, state, house_consumption_w=900.0)
    # The same glitch in the meters: the consumption reading isn't fooled by it.
    d = _step(cfg, state, 30, car_connected=False, battery_soc=70.0,
              grid_power_w=2300.0, battery_power_w=-2900.0, house_consumption_w=900.0)
    assert state.peak_share_engaged is False
    assert d.house_load_source == "measured"
    # A real step reaches the setpoint at once — there is nothing to wait out.
    d = _step(cfg, state, 35, car_connected=False, battery_soc=70.0,
              house_consumption_w=9600.0, **_ess(9600.0))
    assert state.peak_share_engaged is True
    assert d.grid_setpoint_w == 3700.0


def _charging(cfg, state, t, consumption):
    return _step(cfg, state, t, car_connected=True, phases=1, car_actual_power_w=3000.0,
                 battery_soc=70.0, grid_power_w=3100.0, battery_power_w=-800.0,
                 house_consumption_w=consumption)


def test_a_consumption_that_leaves_out_the_wallbox_is_set_aside():
    # 900 W "consumption" while the car alone draws 3 kW: it can't include the
    # wallbox. Each such reading falls back to the meters; two minutes of it and the
    # mapping is set aside until the next restart.
    cfg, state = _share_cfg(mode=ChargingMode.FAST), EngineState()
    d = None
    for t in range(0, 120, 10):
        d = _charging(cfg, state, t, 900.0)
        assert d.house_load_source == "derived"
    assert state.consumption_rejected is False
    _charging(cfg, state, 120, 900.0)
    assert state.consumption_rejected is True
    d = _charging(cfg, state, 130, 4000.0)  # even a plausible reading now
    assert d.house_load_source == "derived"


def test_a_brief_dip_below_the_car_keeps_the_consumption():
    # After a car start the go-e reports the car before the consumption includes it.
    cfg, state = _share_cfg(mode=ChargingMode.FAST), EngineState()
    for t in range(0, 20, 5):
        _charging(cfg, state, t, 900.0)
    d = _charging(cfg, state, 20, 3900.0)
    assert d.house_load_source == "measured"
    assert state.consumption_low_since is None
    assert state.consumption_rejected is False
