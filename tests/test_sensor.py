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

from custom_components.goe_steve.engine import PriceSlot  # noqa: E402
from custom_components.goe_steve.sensor import PriceForecastSensor  # noqa: E402


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
