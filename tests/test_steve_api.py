"""Unit tests for the pure SteVe parsing/aggregation helpers.

Like the engine tests, these load the module directly by file path and need
nothing more than ``pytest`` (aiohttp is optional and only used by the HTTP
client, which these tests don't touch)::

    pytest tests/test_steve_api.py
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
from datetime import datetime, timezone

_PATH = (
    pathlib.Path(__file__).resolve().parents[1]
    / "custom_components"
    / "goe_steve"
    / "steve_api.py"
)
_spec = importlib.util.spec_from_file_location("goe_steve_api", _PATH)
steve = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
sys.modules[_spec.name] = steve
_spec.loader.exec_module(steve)


def _tx(start_val, stop_val, *, id_tag="A", stop="2026-06-14T11:00:00Z"):
    return {
        "id": 1,
        "chargeBoxId": "GOE1",
        "ocppIdTag": id_tag,
        "startTimestamp": "2026-06-14T10:00:00Z",
        "stopTimestamp": stop,
        "startValue": start_val,
        "stopValue": stop_val,
    }


# --- timestamp + number parsing ----------------------------------------------------

def test_parse_dt_handles_zulu_and_offset():
    assert steve._parse_dt("2026-06-14T10:00:00Z") == datetime(
        2026, 6, 14, 10, 0, tzinfo=timezone.utc
    )
    assert steve._parse_dt("2026-06-14T10:00:00+02:00").utcoffset() is not None
    assert steve._parse_dt("") is None
    assert steve._parse_dt("not-a-date") is None


def test_parse_float_tolerant():
    assert steve._parse_float("1234") == 1234.0
    assert steve._parse_float(None) is None
    assert steve._parse_float("") is None
    assert steve._parse_float("oops") is None


# --- tags --------------------------------------------------------------------------

def test_parse_tag_blocked_via_max_active_zero():
    tag = steve.parse_tag({"ocppTagPk": 5, "idTag": "CARD1", "maxActiveTransactionCount": 0})
    assert tag.id_tag == "CARD1"
    assert tag.pk == 5
    assert tag.blocked is True


def test_parse_tag_authorized_and_explicit_blocked_flag():
    assert steve.parse_tag(
        {"idTag": "CARD2", "maxActiveTransactionCount": -1}
    ).blocked is False
    assert steve.parse_tag({"idTag": "CARD3", "blocked": True}).blocked is True


def test_parse_tag_requires_id():
    assert steve.parse_tag({"ocppTagPk": 1}) is None
    assert steve.parse_tag("nope") is None


def test_tag_name_prefers_note_then_falls_back_to_id():
    named = steve.parse_tag({"idTag": "CARD1", "note": "Chris's Model 3"})
    assert named.name == "Chris's Model 3"
    # Blank/whitespace notes fall back to the raw id-tag.
    assert steve.parse_tag({"idTag": "CARD2"}).name == "CARD2"
    assert steve.parse_tag({"idTag": "CARD3", "note": "   "}).name == "CARD3"


def test_name_for_tag_resolves_via_tags_list():
    data = steve.SteVeData(
        tags=[steve.SteVeTag(pk=1, id_tag="CARD1", note="Garage key")]
    )
    assert data.name_for_tag("CARD1") == "Garage key"
    # Unknown tag → raw id-tag; None id → None.
    assert data.name_for_tag("CARD9") == "CARD9"
    assert data.name_for_tag(None) is None


# --- transactions + energy ---------------------------------------------------------

def test_transaction_energy_kwh_from_meter_values():
    tx = steve.parse_transaction(_tx(1000, 6500))
    assert tx.energy_kwh == 5.5
    assert tx.is_active is False


def test_active_transaction_has_no_stop():
    tx = steve.parse_transaction(_tx(1000, None, stop=None))
    assert tx.is_active is True
    assert tx.energy_kwh is None


def test_energy_never_negative():
    tx = steve.parse_transaction(_tx(6500, 1000))
    assert tx.energy_kwh == 0.0


# --- aggregation -------------------------------------------------------------------

def test_aggregate_energy_by_tag_sums_per_tag():
    txs = steve.parse_transactions(
        [
            _tx(0, 1000, id_tag="A"),
            _tx(0, 3000, id_tag="A"),
            _tx(0, 2000, id_tag="B"),
            _tx(0, None, id_tag="B", stop=None),  # open session ignored
        ]
    )
    totals = steve.aggregate_energy_by_tag(txs)
    assert totals == {"A": 4.0, "B": 2.0}


def test_latest_completed_picks_most_recent_stop():
    early = _tx(0, 1000, id_tag="A", stop="2026-06-14T08:00:00Z")
    late = _tx(0, 1000, id_tag="B", stop="2026-06-14T20:00:00Z")
    txs = steve.parse_transactions([early, late])
    assert steve.latest_completed(txs).id_tag == "B"


def test_build_steve_data_assembles_snapshot():
    tags = [{"idTag": "A", "ocppTagPk": 1}]
    txs = [_tx(0, 1000, id_tag="A"), _tx(0, None, id_tag="A", stop=None)]
    data = steve.build_steve_data(tags, txs)
    assert [t.id_tag for t in data.tags] == ["A"]
    assert len(data.active) == 1
    assert data.energy_by_tag == {"A": 1.0}
    assert data.last_session is not None


# --- URL normalization -------------------------------------------------------------

def test_normalize_base_url_variants():
    assert steve.normalize_base_url("http://h:8080") == "http://h:8080/steve/api/v1"
    assert steve.normalize_base_url("http://h:8080/") == "http://h:8080/steve/api/v1"
    assert (
        steve.normalize_base_url("http://h:8080/steve") == "http://h:8080/steve/api/v1"
    )
    assert (
        steve.normalize_base_url("http://h:8080/steve/api/v1")
        == "http://h:8080/steve/api/v1"
    )
