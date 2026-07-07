"""Pure go-e MQTT decoding — the go-e-specific bits, verified against a live box.

HA-free (like test_engine/test_forecast) so it runs in CI without Home Assistant.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys

import pytest

# Load the pure module by file path so the package ``__init__`` (which imports
# Home Assistant) isn't triggered — same trick as test_engine.py.
_PATH = (
    pathlib.Path(__file__).resolve().parents[1]
    / "custom_components"
    / "goe_steve"
    / "goe_parse.py"
)
_spec = importlib.util.spec_from_file_location("goe_parse", _PATH)
goe_parse = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
sys.modules[_spec.name] = goe_parse
_spec.loader.exec_module(goe_parse)

PSM_SINGLE = goe_parse.PSM_SINGLE
PSM_THREE = goe_parse.PSM_THREE
base_topic_from_message_topic = goe_parse.base_topic_from_message_topic
car_connected = goe_parse.car_connected
coerce_float = goe_parse.coerce_float
coerce_int = goe_parse.coerce_int
decode_payload = goe_parse.decode_payload
key_from_message_topic = goe_parse.key_from_message_topic
normalize_base_topic = goe_parse.normalize_base_topic
phase_count_to_psm = goe_parse.phase_count_to_psm
power_from_nrg = goe_parse.power_from_nrg


def test_normalize_base_topic_keeps_leading_slash_drops_trailing():
    assert normalize_base_topic("go-eCharger/222162") == "go-eCharger/222162"
    assert normalize_base_topic("  go-eCharger/222162/ ") == "go-eCharger/222162"
    # The live charger uses a leading slash — it must survive normalization.
    assert normalize_base_topic("/go-eCharger/222162/") == "/go-eCharger/222162"


@pytest.mark.parametrize(
    "topic, expected",
    [
        ("go-eCharger/222162/car", ("go-eCharger/222162", "222162")),
        ("/go-eCharger/222162/car", ("/go-eCharger/222162", "222162")),
        ("/go-eCharger/222162/nrg", ("/go-eCharger/222162", "222162")),
        ("homeassistant/sensor/foo", None),
    ],
)
def test_base_topic_from_message_topic(topic, expected):
    assert base_topic_from_message_topic(topic) == expected


def test_key_from_message_topic_ignores_set_and_result():
    base = "/go-eCharger/222162"
    assert key_from_message_topic(f"{base}/amp", base) == "amp"
    assert key_from_message_topic(f"{base}/amp/set", base) is None
    assert key_from_message_topic(f"{base}/amp/result", base) is None
    assert key_from_message_topic(base, base) is None


def test_decode_payload_json_and_fallback():
    assert decode_payload("16") == 16
    assert decode_payload("true") is True
    assert decode_payload('"mein charger"') == "mein charger"
    assert decode_payload(b"[1, 2, 3]") == [1, 2, 3]
    # Non-JSON stays a raw string rather than raising.
    assert decode_payload("not json") == "not json"


def test_power_from_nrg_uses_index_11():
    # The live idle reading: 16 elements, all powers zero.
    idle = [230.02, 230.02, 230.33, 2.48, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    assert power_from_nrg(idle) == 0.0
    charging = list(range(16))  # index 11 == 11
    assert power_from_nrg(charging) == 11.0
    assert power_from_nrg([1, 2, 3]) is None  # too short
    assert power_from_nrg(None) is None


@pytest.mark.parametrize(
    "car_state, expected",
    [(0, False), (1, False), (2, True), (3, True), (4, True), (5, False), (None, None)],
)
def test_car_connected(car_state, expected):
    assert car_connected(car_state) is expected


def test_phase_count_to_psm():
    # 1 phase -> psm 1 (single); anything else -> psm 2 (three).
    assert phase_count_to_psm(1) == PSM_SINGLE
    assert phase_count_to_psm(3) == PSM_THREE


def test_coerce_rejects_bools():
    assert coerce_int(True) is None
    assert coerce_float(False) is None
    assert coerce_int("6") == 6
    assert coerce_float("2.48") == 2.48
    assert coerce_int("x") is None
