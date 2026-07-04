"""PriceForecastSensor surfacing logic.

Importing ``sensor`` pulls in Home Assistant, which isn't available in the bare
unit-test env (see test_engine/test_forecast, which stay HA-free). So this is
skipped unless HA is installed, and builds the entity with ``__new__`` to avoid
the CoordinatorEntity machinery — the properties under test only read
``self.coordinator``.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

pytest.importorskip("homeassistant")

from custom_components.goe_steve.engine import (  # noqa: E402
    ChargerInputs,
    Decision,
    PriceSlot,
)
from custom_components.goe_steve.sensor import (  # noqa: E402
    PowerFlowSensor,
    PriceForecastSensor,
    StatusSensor,
)


class _FakeSettings:
    cheap_price = 0.18


class _FakeCoordinator:
    def __init__(self, price_now, forecast, unit):
        self.last_price_now = price_now
        self.last_forecast = forecast
        self.price_unit = unit
        self.settings = _FakeSettings()


def _sensor(coordinator) -> PriceForecastSensor:
    sensor = PriceForecastSensor.__new__(PriceForecastSensor)
    sensor.coordinator = coordinator
    return sensor


def test_serializes_slots_with_threshold_and_unit():
    forecast = [
        PriceSlot(start=datetime(2026, 6, 15, 22, 0, tzinfo=timezone.utc), price=0.123456),
        PriceSlot(start=datetime(2026, 6, 15, 23, 0, tzinfo=timezone.utc), price=0.20),
    ]
    sensor = _sensor(_FakeCoordinator(0.123456, forecast, "€/kWh"))

    assert sensor.native_value == 0.123456
    attrs = sensor.extra_state_attributes
    assert attrs["cheap_price"] == 0.18
    assert attrs["unit"] == "€/kWh"
    assert attrs["slots"] == [
        {"start": "2026-06-15T22:00:00+00:00", "price": 0.12346},  # rounded to 5dp
        {"start": "2026-06-15T23:00:00+00:00", "price": 0.2},
    ]


def test_empty_when_no_forecast():
    sensor = _sensor(_FakeCoordinator(None, None, None))
    assert sensor.native_value is None
    attrs = sensor.extra_state_attributes
    assert attrs["slots"] == []
    assert attrs["unit"] is None


# --- PowerFlowSensor: the car source split -----------------------------------------


class _FlowCoordinator:
    def __init__(self, inputs, session_kwh=None):
        self.last_inputs = inputs
        self.goe_session_energy_kwh = session_kwh


def test_power_flow_exposes_the_car_source_split():
    sensor = PowerFlowSensor.__new__(PowerFlowSensor)
    sensor.coordinator = _FlowCoordinator(
        ChargerInputs(
            car_connected=True,
            car_actual_power_w=5000.0,
            pv_power_w=6200.0,
            grid_power_w=-300.0,
            battery_power_w=0.0,
            battery_soc=78.0,
            phases=3,
        )
    )
    attrs = sensor.extra_state_attributes
    assert attrs["sources"] == {"solar_w": 5000, "battery_w": 0, "grid_w": 0}
    # And still the raw balance the card's balance line reads.
    assert attrs["car_w"] == 5000
    assert attrs["phases"] == 3


# --- StatusSensor: the previously invisible engine state ---------------------------


class _StatusSettings:
    mode = type("M", (), {"value": "smart"})()
    battery_reserve_soc = 60.0
    battery_hold_mode = "auto"


class _StatusCoordinator:
    def __init__(self, decision):
        self.data = decision
        self.settings = _StatusSettings()
        self.last_written_force = False


def test_status_surfaces_hold_plan_and_hold_mode():
    decision = Decision(
        control=True,
        should_charge=True,
        target_current_a=15.3,
        target_phases=3,
        reason="Cheap grid",
        reason_key="cheap_grid",
        hold_battery=True,
        hold_source="auto",
        plan=["2026-07-04T20:00:00+00:00"],
    )
    sensor = StatusSensor.__new__(StatusSensor)
    sensor.coordinator = _StatusCoordinator(decision)
    attrs = sensor.extra_state_attributes
    assert attrs["hold_battery"] is True
    assert attrs["hold_source"] == "auto"
    assert attrs["battery_hold_mode"] == "auto"
    assert attrs["plan"] == ["2026-07-04T20:00:00+00:00"]
    assert attrs["forced"] is False
