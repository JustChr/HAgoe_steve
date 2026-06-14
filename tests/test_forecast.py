"""Unit tests for the provider-agnostic forecast parser.

Like ``test_engine.py`` these run HA-free. ``forecast.py`` does a relative import
(``from .engine import PriceSlot``), so we register a lightweight parent package and
load both modules by path under it — no Home Assistant required::

    pytest tests/test_forecast.py
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import types
from datetime import datetime, timezone

import pytest

_PKG = "goe_steve_pkg"
_BASE = (
    pathlib.Path(__file__).resolve().parents[1]
    / "custom_components"
    / "goe_steve"
)

# A stand-in package so `from .engine import ...` resolves to our path-loaded module.
_pkg = types.ModuleType(_PKG)
_pkg.__path__ = [str(_BASE)]
sys.modules[_PKG] = _pkg


def _load(name: str):
    spec = importlib.util.spec_from_file_location(f"{_PKG}.{name}", _BASE / f"{name}.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


engine = _load("engine")
forecast = _load("forecast")

parse_forecast = forecast.parse_forecast
dedupe_slots = forecast.dedupe_slots
PriceSlot = engine.PriceSlot

# A fixed aware timestamp reused across provider shapes.
_ISO = "2026-06-14T10:00:00+02:00"
_EXPECTED_START = datetime(2026, 6, 14, 8, 0, tzinfo=timezone.utc)  # 10:00 +02:00 → UTC


@pytest.mark.parametrize(
    ("item", "expected_price"),
    [
        # Nordpool: raw_today entries use start/value in currency/kWh.
        ({"start": _ISO, "value": 0.2534}, 0.2534),
        # Tibber priceInfo: start_time/total in currency/kWh.
        ({"start_time": _ISO, "total": 0.30}, 0.30),
        # EnergyZero / Frank Energie style: from/price in currency/kWh.
        ({"from": _ISO, "price": 0.12}, 0.12),
        # EPEX Spot: ct/kWh is normalized to currency/kWh.
        ({"start_time": _ISO, "price_ct_per_kwh": 25.34}, 0.2534),
        # EPEX Spot: €/MWh is normalized to currency/kWh.
        ({"start_time": _ISO, "price_eur_per_mwh": 253.4}, 0.2534),
    ],
)
def test_parses_each_provider_shape(item, expected_price):
    slots = parse_forecast([item])
    assert len(slots) == 1
    assert slots[0].start == _EXPECTED_START
    assert slots[0].price == pytest.approx(expected_price)


def test_price_key_priority_prefers_native_currency():
    # When a per-kWh value is present it wins over the scaled EPEX keys.
    slots = parse_forecast(
        [{"start": _ISO, "value": 0.20, "price_ct_per_kwh": 99.0}]
    )
    assert slots[0].price == pytest.approx(0.20)


def test_accepts_datetime_objects_and_naive_timestamps():
    aware = datetime(2026, 6, 14, 8, 0, tzinfo=timezone.utc)
    slots = parse_forecast([{"start": aware, "value": 0.1}])
    assert slots[0].start == aware

    # Naive timestamps are interpreted in the supplied default_tz, then UTC-ized.
    tz = timezone.utc
    naive = parse_forecast([{"start": "2026-06-14T08:00:00", "value": 0.1}], default_tz=tz)
    assert naive[0].start == datetime(2026, 6, 14, 8, 0, tzinfo=timezone.utc)


def test_skips_unusable_entries():
    items = [
        {"start": _ISO},  # no price
        {"value": 0.2},  # no start
        {"start": "not-a-date", "value": 0.2},  # unparseable timestamp
        "garbage",  # not a dict
        {"start": _ISO, "value": "nan-ish"},  # price not floatable
        {"start": _ISO, "value": 0.25},  # the one good entry
    ]
    slots = parse_forecast(items)
    assert len(slots) == 1
    assert slots[0].price == pytest.approx(0.25)


@pytest.mark.parametrize("raw", [None, {}, "raw_today", 42, [1, 2, 3]])
def test_non_forecast_inputs_yield_empty(raw):
    assert parse_forecast(raw) == []


def test_dedupe_sorts_and_drops_duplicate_timestamps():
    t0 = datetime(2026, 6, 14, 8, 0, tzinfo=timezone.utc)
    t1 = datetime(2026, 6, 14, 9, 0, tzinfo=timezone.utc)
    slots = [
        PriceSlot(start=t1, price=0.3),
        PriceSlot(start=t0, price=0.1),
        PriceSlot(start=t0, price=0.99),  # duplicate start → dropped (first kept)
    ]
    out = dedupe_slots(slots)
    assert [s.start for s in out] == [t0, t1]
    assert out[0].price == pytest.approx(0.1)
