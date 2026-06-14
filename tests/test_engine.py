"""Unit tests for the pure regulation engine.

The engine is HA-free, so we load it directly by file path — these tests run with
nothing more than ``pytest`` installed (no Home Assistant required)::

    pytest tests/test_engine.py
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys

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
ChargingMode = engine.ChargingMode
BatteryPolicy = engine.BatteryPolicy
decide = engine.decide


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


def test_unimplemented_mode_is_safe():
    d = decide(_inputs(grid_power_w=-6000.0), _cfg(mode=ChargingMode.COMBINED))
    assert d.control is False
    assert "Phase 2" in d.reason
