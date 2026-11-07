"""Tests for the field-test log (pure, no Home Assistant needed)."""

from __future__ import annotations

import importlib.util
import pathlib
import sys
from datetime import datetime, timedelta, timezone

_PATH = (
    pathlib.Path(__file__).resolve().parents[1]
    / "custom_components" / "goe_steve" / "testlog.py"
)
_spec = importlib.util.spec_from_file_location("goe_testlog", _PATH)
testlog = importlib.util.module_from_spec(_spec)
sys.modules["goe_testlog"] = testlog
_spec.loader.exec_module(testlog)

Sample = testlog.Sample
QuarterLog = testlog.QuarterLog

W0 = datetime(2026, 11, 7, 8, 45, tzinfo=timezone.utc)
W1 = W0 + timedelta(minutes=15)


def _s(seconds: float, **kw) -> "testlog.Sample":
    now = W0 + timedelta(seconds=seconds)
    start = W0 if now < W1 else W1
    base = dict(now=now, window_start=start, control_ok=True, grid_w=0.0,
                battery_w=0.0, battery_soc=60.0, pv_w=0.0)
    base.update(kw)
    return Sample(**base)


def _run(samples, history=None):
    log = QuarterLog()
    records, events = [], []
    for sample in samples:
        closed, evs = log.observe(sample, history)
        events.extend(evs)
        if closed:
            records.append(closed)
    return log, records, events


def test_a_quarter_hour_closes_with_the_engines_billed_average():
    samples = [_s(t, grid_w=2000.0) for t in range(0, 900, 10)] + [_s(900)]
    _, records, _ = _run(samples, history=[(W0, 1987.6)])
    assert len(records) == 1
    rec = records[0]
    assert rec["t"] == "2026-11-07T08:45+00:00"
    assert rec["avg_w"] == 1988
    assert rec["wh"]["grid_in"] == 500  # 2 kW for the full quarter-hour
    assert rec["s"]["seen"] == 900


def test_energy_is_split_into_where_it_went():
    # 1 kW from the grid, 2 kW of PV, the battery charging 0.5 kW, the car 1 kW.
    samples = [_s(t, grid_w=1000.0, pv_w=2000.0, battery_w=500.0, car_w=1000.0,
                  car_connected=True) for t in range(0, 900, 10)] + [_s(900)]
    _, (rec,), _ = _run(samples)
    assert rec["wh"]["pv"] == 500
    assert rec["wh"]["bat_in"] == 125
    assert rec["wh"]["car"] == 250
    assert rec["wh"]["house"] == 375  # 1 + 2 − 0.5 − 1 = 1.5 kW


def test_the_full_power_recharge_sentinel_counts_seconds():
    samples = [_s(t, battery_soc=41.0, ess_min_soc=50.0) for t in range(0, 60, 10)]
    samples += [_s(t, battery_soc=41.0, ess_min_soc=40.0) for t in range(60, 900, 10)]
    _, (rec,), _ = _run(samples + [_s(900)])
    assert rec["s"]["min_soc_above_soc"] == 60
    assert rec["ess_min_soc"] == [40, 50]


def test_a_long_gap_is_not_carried_across():
    samples = [_s(0, grid_w=3000.0)]
    samples += [_s(t, grid_w=3000.0) for t in range(600, 900, 10)] + [_s(900)]
    _, (rec,), _ = _run(samples)
    assert rec["s"]["gap"] == 600
    assert rec["wh"]["grid_in"] == 250  # only the 300 s after the gap


def test_blind_cycles_are_counted_and_book_no_energy():
    samples = [_s(t, control_ok=False, grid_w=None) for t in range(0, 900, 10)]
    _, (rec,), events = _run(samples + [_s(900)])
    assert rec["s"]["blind"] == 900
    assert rec["wh"] == {}
    assert events == []


def test_shaves_refills_and_held_cars_become_events():
    samples = [
        _s(0),
        _s(10, peak_reason_key="peak_share", tier="soft"),
        _s(20, peak_reason_key="peak_ok", refilling=True, reason_key="peak_refill_car"),
        _s(30),
    ]
    _, _, events = _run(samples)
    kinds = [(e["ev"], e.get("on", e.get("to"))) for e in events]
    assert ("share", True) in kinds and ("share", False) in kinds
    assert ("refill", True) in kinds and ("refill", False) in kinds
    assert ("car_held", True) in kinds and ("car_held", False) in kinds
    assert ("tier", "soft") in kinds and ("tier", "off") in kinds


def test_writes_and_car_starts_are_counted_per_quarter_hour():
    log = QuarterLog()
    log.observe(_s(0, car_connected=True, car_w=0.0))
    log.note_write("frc")
    log.observe(_s(10, car_connected=True, car_w=4000.0))
    log.note_write("amp")
    log.note_write("amp")
    log.observe(_s(20, car_connected=True, car_w=0.0))
    log.observe(_s(30, car_connected=True, car_w=4000.0))
    closed, _ = log.observe(_s(900))
    assert closed["writes"] == {"amp": 2, "frc": 1}
    assert closed["car_starts"] == 2


def test_reasons_are_timed():
    samples = [_s(t, reason_key="fast", peak_reason_key="peak_ok") for t in range(0, 300, 10)]
    samples += [_s(t, reason_key="peak_pause", peak_reason_key="peak_pause")
                for t in range(300, 900, 10)]
    _, (rec,), _ = _run(samples + [_s(900)])
    assert rec["reasons"] == {"fast": 300, "peak_pause": 600}
    assert rec["s"]["car_held"] == 600
