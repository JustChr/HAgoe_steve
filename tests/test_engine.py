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


def test_manual_mode_paused_controls_but_does_not_charge():
    # Manual mode (OFF) now actively drives the charger: with the manual switch
    # off it holds the car off rather than going hands-off.
    d = decide(_inputs(), _cfg(mode=ChargingMode.OFF, manual_charge=False))
    assert d.control is True
    assert d.should_charge is False
    assert d.write_phases is True


def test_manual_passive_is_hands_off():
    # Right after switching into Manual (before any manual control is touched) the
    # engine goes fully hands-off so the coordinator leaves the charger as-is —
    # even though the manual switch would otherwise ask to charge.
    d = decide(
        _inputs(),
        _cfg(mode=ChargingMode.OFF, manual_passive=True, manual_charge=True),
    )
    assert d.control is False
    assert d.should_charge is False
    assert d.reason_key == "manual_passive"


def test_manual_mode_charges_at_requested_current_and_phases():
    d = decide(
        _inputs(),
        _cfg(
            mode=ChargingMode.OFF,
            manual_charge=True,
            manual_current_a=12.0,
            manual_phases=1,
        ),
    )
    assert d.control is True
    assert d.should_charge is True
    assert d.target_current_a == 12.0
    assert d.target_phases == 1
    assert d.write_phases is True


def test_manual_mode_no_car_holds_off():
    d = decide(
        _inputs(car_connected=False),
        _cfg(mode=ChargingMode.OFF, manual_charge=True),
    )
    assert d.control is True
    assert d.should_charge is False


def test_manual_mode_trims_current_when_battery_discharges_below_line():
    # Below the reserve line the home battery is held: with no hold switch the
    # guard trims the car's current down by the battery discharge (fallback path).
    d = decide(
        _inputs(battery_soc=50.0, battery_power_w=-2300.0, voltage_v=230.0),
        _cfg(
            mode=ChargingMode.OFF,
            manual_charge=True,
            manual_current_a=16.0,
            manual_phases=1,
            battery_reserve_soc=80.0,
        ),
    )
    assert d.should_charge is True
    assert d.target_current_a < 16.0
    assert "protecting" in d.reason.lower()


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


def test_car_waits_below_reserve_line():
    # Big surplus, but home battery at 50% < line 80% → battery first, car waits.
    d = decide(
        _inputs(grid_power_w=-6000.0, battery_soc=50.0),
        _cfg(mode=ChargingMode.PV_ONLY, battery_reserve_soc=80.0),
    )
    assert d.should_charge is False
    assert "battery" in d.reason.lower()


def test_battery_backs_car_above_reserve_line():
    # Above the line the car comes first: availability is lifted to MAX so the
    # battery actively backs the car down to the line.
    d = decide(
        _inputs(grid_power_w=-6000.0, battery_soc=85.0),
        _cfg(mode=ChargingMode.PV_ONLY, battery_reserve_soc=80.0),
    )
    assert d.should_charge is True
    assert d.target_current_a == 16.0


def test_at_the_line_car_does_not_run_on_battery_discharge():
    # Solar has dropped to ~0 but the inverter is discharging the home battery
    # (3400 W) to cover the car (2600 W) while a little still exports (240 W).
    # At the line the discharge is subtracted so the car's own draw can't
    # masquerade as solar — no real surplus, the car holds and the battery stays
    # at its reserve. (Regression for the "charging the car from the house
    # battery on solar-only" report, now anchored at the line.)
    d = decide(
        _inputs(
            grid_power_w=-240.0,
            car_actual_power_w=2600.0,
            battery_power_w=-3400.0,
            battery_soc=80.0,
        ),
        _cfg(mode=ChargingMode.PV_ONLY, battery_reserve_soc=80.0),
    )
    assert d.surplus_w == pytest.approx(0.0, abs=1.0)
    assert d.should_charge is False


def test_unknown_soc_car_does_not_run_on_battery_discharge():
    # Same guard with the SoC unavailable: never silently drain the battery.
    d = decide(
        _inputs(
            grid_power_w=-240.0,
            car_actual_power_w=2600.0,
            battery_power_w=-3400.0,
        ),
        _cfg(mode=ChargingMode.PV_ONLY),
    )
    assert d.surplus_w == pytest.approx(0.0, abs=1.0)
    assert d.should_charge is False


def test_pv_minimum_tops_up_from_grid():
    # Only 500 W surplus, but PV+minimum guarantees at least the floor current
    d = decide(
        _inputs(grid_power_w=-500.0),
        _cfg(mode=ChargingMode.PV_MINIMUM, min_grid_floor_w=1400.0),
    )
    assert d.should_charge is True
    assert d.target_current_a >= 6.0


# --- The home-battery reserve line ------------------------------------------------

def test_at_the_line_car_takes_battery_bound_solar():
    # Grid balanced, battery exactly at its line, 5000 W flowing into it → the
    # reserve is satisfied, so the car takes that solar instead of waiting.
    d = decide(
        _inputs(grid_power_w=0.0, battery_power_w=5000.0, battery_soc=80.0),
        _cfg(mode=ChargingMode.PV_ONLY, battery_reserve_soc=80.0),
    )
    assert d.should_charge is True
    assert d.surplus_w == pytest.approx(5000.0, abs=1.0)


def test_battery_backs_car_with_no_solar_above_line():
    # No surplus at all, but the battery is well above a low line → it carries
    # the car on its own.
    d = decide(
        _inputs(grid_power_w=0.0, battery_soc=60.0),
        _cfg(mode=ChargingMode.PV_ONLY, battery_reserve_soc=20.0),
    )
    assert d.should_charge is True


def test_battery_stops_backing_at_the_line():
    d = decide(
        _inputs(grid_power_w=0.0, battery_soc=15.0),
        _cfg(mode=ChargingMode.PV_ONLY, battery_reserve_soc=20.0),
    )
    assert d.should_charge is False


def test_reserve_100_battery_never_powers_the_car():
    # Line at 100 %: with the battery full the car may still ride real solar
    # surplus, but the battery is always held during grid charging.
    solar = decide(
        _inputs(grid_power_w=-6000.0, battery_soc=100.0),
        _cfg(mode=ChargingMode.PV_ONLY, battery_reserve_soc=100.0),
    )
    assert solar.should_charge is True
    assert solar.hold_battery is False  # pure solar never holds
    fast = decide(
        _inputs(battery_soc=100.0),
        _cfg(mode=ChargingMode.FAST, battery_reserve_soc=100.0),
    )
    assert fast.hold_battery is True


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


def test_cheap_grid_trims_to_avoid_battery_drain():
    # Cheap grid wants full 16 A, but the home battery is discharging 3000 W to
    # cover the car → the guard trims that off so the grid carries it instead.
    # 3000 W / (3·230) ≈ 4.35 A trimmed from 16 A → ~11.65 A.
    d = decide(
        _inputs(grid_power_w=0.0, price_now=0.05, battery_power_w=-3000.0),
        _cfg(mode=ChargingMode.PV_PRICE, cheap_price=0.15),
    )
    assert d.should_charge is True
    assert d.target_current_a == pytest.approx(16.0 - 3000 / (3 * 230), abs=0.1)
    assert "battery" in d.reason.lower()


def test_cheap_grid_always_holds_regardless_of_reserve_line():
    # Cheap grid → grid only, never the battery: hold ON even well above the
    # line. With a discharging battery and no hold switch, the guard also trims.
    for soc in (50.0, 90.0):
        d = decide(
            _inputs(grid_power_w=0.0, price_now=0.05, battery_power_w=-3000.0, battery_soc=soc),
            _cfg(mode=ChargingMode.PV_PRICE, cheap_price=0.15, battery_reserve_soc=80.0),
        )
        assert d.hold_battery is True, soc
        assert d.target_current_a < 16.0, soc  # guard trims the discharge


def test_cheap_grid_holds_even_with_no_battery_discharge():
    # No discharge to trim, but cheap grid still holds so the battery can't kick in.
    d = decide(
        _inputs(grid_power_w=0.0, price_now=0.05, battery_soc=90.0),
        _cfg(mode=ChargingMode.PV_PRICE, cheap_price=0.15, battery_reserve_soc=80.0),
    )
    assert d.hold_battery is True
    assert d.target_current_a == 16.0


def test_cheap_grid_ignores_small_battery_noise():
    # A trickle of discharge (≤ tolerance) should not trim the current.
    d = decide(
        _inputs(grid_power_w=0.0, price_now=0.05, battery_power_w=-50.0),
        _cfg(mode=ChargingMode.PV_PRICE, cheap_price=0.15),
    )
    assert d.target_current_a == 16.0


def test_cheap_grid_guard_floors_at_min_current():
    # Huge discharge would trim below the EV floor → clamp to min_current_a.
    d = decide(
        _inputs(grid_power_w=0.0, price_now=0.05, battery_power_w=-15000.0),
        _cfg(mode=ChargingMode.PV_PRICE, cheap_price=0.15),
    )
    assert d.target_current_a == 6.0


# --- Battery-hold switch (block home-battery discharge during grid charge) -------

def test_hold_off_when_not_grid_charging():
    # PV-only surplus charging never holds — surplus should still fill the battery.
    d = decide(
        _inputs(grid_power_w=-5000.0),
        _cfg(mode=ChargingMode.PV_ONLY),
    )
    assert d.should_charge is True
    assert d.hold_battery is False


def test_hold_on_cheap_grid():
    d = decide(
        _inputs(grid_power_w=0.0, price_now=0.05),
        _cfg(mode=ChargingMode.PV_PRICE, cheap_price=0.15),
    )
    assert d.should_charge is True
    assert d.hold_battery is True


# These probe the reserve-line hold via FAST (a grid charge that is NOT price-gated,
# so the line decides). Cheap grid is a separate, always-hold path tested above.
def test_hold_only_at_or_below_the_line():
    # Above the line the battery may help the car at full power (no hold).
    above = decide(
        _inputs(battery_soc=90.0),
        _cfg(mode=ChargingMode.FAST, battery_reserve_soc=80.0),
    )
    assert above.hold_battery is False
    # At/below the line → hold so the grid carries the car instead.
    below = decide(
        _inputs(battery_soc=70.0),
        _cfg(mode=ChargingMode.FAST, battery_reserve_soc=80.0),
    )
    assert below.hold_battery is True


def test_hold_when_soc_unknown():
    # Can't place the battery against the line → never silently drain it.
    d = decide(
        _inputs(battery_soc=None),
        _cfg(mode=ChargingMode.FAST),
    )
    assert d.hold_battery is True


def test_cheap_price_holds_in_any_grid_charge_mode():
    # "Cheap grid, never the battery" is not tied to the price-aware modes: any
    # grid charge during a cheap price holds, even well above the line — Fast,
    # Manual, and a Price-mode planned hour alike.
    fast = decide(
        _inputs(battery_soc=90.0, price_now=0.05),
        _cfg(mode=ChargingMode.FAST, cheap_price=0.15, battery_reserve_soc=80.0),
    )
    assert fast.hold_battery is True
    manual = decide(
        _inputs(battery_soc=90.0, price_now=0.05),
        _cfg(mode=ChargingMode.OFF, manual_charge=True, cheap_price=0.15,
             battery_reserve_soc=80.0),
    )
    assert manual.hold_battery is True
    now = datetime(2026, 6, 14, 20, 0, tzinfo=timezone.utc)
    fc = _forecast(now, [0.05, 0.30, 0.30, 0.30])
    price = decide(
        _inputs(now=now, price_forecast=fc, price_now=0.05, battery_soc=90.0),
        _cfg(mode=ChargingMode.PRICE, cheap_price=0.15, battery_reserve_soc=80.0,
             target_energy_kwh=5.0, departure=now + timedelta(hours=4)),
    )
    assert price.should_charge is True
    assert price.hold_battery is True


def test_deadline_hour_above_line_lets_battery_help_when_not_cheap():
    # A planned hour that is NOT actually cheap follows the line: above it the
    # battery may back the car toward the departure target.
    now = datetime(2026, 6, 14, 20, 0, tzinfo=timezone.utc)
    fc = _forecast(now, [0.20, 0.30, 0.30, 0.30])
    d = decide(
        _inputs(now=now, price_forecast=fc, price_now=0.20, battery_soc=90.0),
        _cfg(mode=ChargingMode.PRICE, cheap_price=0.15, battery_reserve_soc=80.0,
             target_energy_kwh=5.0, departure=now + timedelta(hours=4)),
    )
    assert d.should_charge is True
    assert d.hold_battery is False


def test_hold_off_when_waiting_not_charging():
    # Not charging (no surplus) → never hold, so the battery system runs normally.
    d = decide(
        _inputs(grid_power_w=200.0),  # importing, no surplus
        _cfg(mode=ChargingMode.PV_ONLY),
    )
    assert d.should_charge is False
    assert d.hold_battery is False


def test_hold_off_when_cheap_window_paused_by_dwell():
    # Cheap grid wants to charge, but the off-dwell keeps it paused this cycle →
    # we are not charging, so the hold switch must be off.
    state = EngineState(charging=False, charge_changed_at=datetime(2025, 1, 1, tzinfo=timezone.utc))
    d = decide(
        _inputs(price_now=0.05, now=datetime(2025, 1, 1, 0, 0, 30, tzinfo=timezone.utc)),
        _cfg(mode=ChargingMode.PV_PRICE, cheap_price=0.15, min_off_dwell_s=120.0),
        state,
    )
    assert d.should_charge is False
    assert d.hold_battery is False


def test_pv_minimum_grid_topup_holds_below_line():
    # PV+minimum tops up from the grid when solar is short. With the grid at 0 the
    # battery would supply the floor, so below the line it must be held.
    d = decide(
        _inputs(grid_power_w=0.0, pv_power_w=0.0, battery_soc=50.0),
        _cfg(mode=ChargingMode.PV_MINIMUM, battery_reserve_soc=80.0,
             min_grid_floor_w=1400.0),
    )
    assert d.should_charge is True
    assert "Minimum" in d.reason  # top-up branch
    assert d.hold_battery is True


def test_pv_minimum_battery_backs_car_above_line():
    # Above the line the battery backs the car outright — the lift covers the
    # floor, so this is solar/battery charging, not a grid top-up, and no hold.
    d = decide(
        _inputs(grid_power_w=0.0, pv_power_w=0.0, battery_soc=50.0),
        _cfg(mode=ChargingMode.PV_MINIMUM, battery_reserve_soc=20.0,
             min_grid_floor_w=1400.0),
    )
    assert d.should_charge is True
    assert d.hold_battery is False


def test_pv_minimum_real_surplus_does_not_hold():
    # Genuine solar surplus above the floor is not grid charging → never hold.
    d = decide(
        _inputs(grid_power_w=-5000.0),
        _cfg(mode=ChargingMode.PV_MINIMUM),
    )
    assert d.should_charge is True
    assert "surplus" in d.reason.lower()  # solar-surplus branch, not the grid top-up
    assert d.hold_battery is False


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


# --- Mode-aware phase selection -------------------------------------------------

def test_fast_uses_full_phases_when_auto_phase():
    # Fast always wants maximum power → full phase count, regardless of surplus.
    d = decide(
        _inputs(phases=1),
        _cfg(mode=ChargingMode.FAST, auto_phase=True, max_phases=3),
    )
    assert d.target_phases == 3


def test_pv_surplus_prefers_single_phase_from_fresh_state():
    # Fresh state (no remembered phase) + a small surplus a single phase can use
    # but three phases can't (3000 W → 1φ ~13 A, 3φ ~4.3 A < 6 A floor).
    d = decide(
        _inputs(grid_power_w=-3000.0, phases=3),
        _cfg(mode=ChargingMode.PV_ONLY, auto_phase=True, max_phases=3),
    )
    assert d.target_phases == 1
    assert d.should_charge is True


def test_cheap_grid_uses_full_phases():
    d = decide(
        _inputs(grid_power_w=0.0, price_now=0.05, phases=1),
        _cfg(mode=ChargingMode.PV_PRICE, cheap_price=0.15, auto_phase=True, max_phases=3),
    )
    assert d.target_phases == 3


def test_deadline_charging_uses_full_phases():
    now = datetime(2026, 6, 14, 20, 0, tzinfo=timezone.utc)
    fc = _forecast(now, [0.05, 0.30, 0.30, 0.30])
    d = decide(
        _inputs(now=now, price_forecast=fc, price_now=0.05, phases=1),
        _cfg(
            mode=ChargingMode.PRICE,
            target_energy_kwh=5.0,
            departure=now + timedelta(hours=4),
            auto_phase=True,
            max_phases=3,
        ),
    )
    assert d.should_charge is True
    assert d.target_phases == 3


def test_auto_phase_off_leaves_phases_untouched():
    # With the toggle off, no mode switches phases — the configured count stands.
    for mode in (ChargingMode.FAST, ChargingMode.PV_ONLY):
        d = decide(
            _inputs(grid_power_w=-3000.0, phases=1),
            _cfg(mode=mode, auto_phase=False),
        )
        assert d.target_phases == 1, mode


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
