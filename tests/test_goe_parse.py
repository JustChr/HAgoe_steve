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
psm_to_phase_count = goe_parse.psm_to_phase_count
phases_from_nrg = goe_parse.phases_from_nrg
power_from_nrg = goe_parse.power_from_nrg
should_publish = goe_parse.should_publish
FRC_OFF = goe_parse.FRC_OFF
FRC_ON = goe_parse.FRC_ON
FRC_NEUTRAL = goe_parse.FRC_NEUTRAL


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


def test_phases_from_nrg_counts_the_phases_the_car_actually_draws():
    # A live three-phase charge, straight off the wire (fw 60.5, 16 A requested).
    three = [
        230.02, 227.85, 230.64, 2.48,
        15.048, 15.124, 15.086,
        3447.9, 3431.8, 3457.1, 0, 10336.8,
        99.6, 99.6, 99.4, 100,
    ]
    assert phases_from_nrg(three) == 3
    # The same charge on one phase: L1 only.
    single = list(three)
    single[5] = single[6] = 0.0
    assert phases_from_nrg(single) == 1
    # Two live phases have no name of their own — the charger only switches 1↔3.
    two = list(three)
    two[6] = 0.0
    assert phases_from_nrg(two) == 3


def test_phases_from_nrg_says_nothing_when_no_current_flows():
    # Idle: there is no phase count to measure, so the caller must fall back to
    # psm rather than be told "1".
    idle = [230.02, 230.02, 230.33, 2.48, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    assert phases_from_nrg(idle) is None
    # Meter noise on an unused phase must not read as a live one.
    assert phases_from_nrg([230, 230, 230, 0, 0.06, 0.04, 0.05] + [0] * 9) is None
    assert phases_from_nrg([1, 2, 3]) is None  # too short
    assert phases_from_nrg(None) is None


def test_phase_count_to_psm():
    # 1 phase -> psm 1 (single); anything else -> psm 2 (three).
    assert phase_count_to_psm(1) == PSM_SINGLE
    assert phase_count_to_psm(3) == PSM_THREE


def test_psm_to_phase_count_is_the_inverse_and_refuses_to_guess_at_auto():
    assert psm_to_phase_count(PSM_SINGLE) == 1
    assert psm_to_phase_count(PSM_THREE) == 3
    # psm 0 means the charger decides; the mode alone doesn't say how many.
    assert psm_to_phase_count(goe_parse.PSM_AUTO) is None
    assert psm_to_phase_count(None) is None


def test_should_publish_writes_whenever_the_intent_changed():
    # A changed intent is written regardless of what the charger reports, and
    # regardless of how recently we wrote something else.
    assert should_publish(FRC_OFF, FRC_ON, FRC_ON, 0.0, 10.0) is True
    assert should_publish(FRC_ON, FRC_ON, FRC_OFF, 0.0, 10.0) is True
    # Nothing written yet this session.
    assert should_publish(FRC_OFF, FRC_OFF, None, None, 10.0) is True


def test_should_publish_stays_quiet_when_memory_and_charger_agree():
    assert should_publish(FRC_OFF, FRC_OFF, FRC_OFF, 999.0, 10.0) is False


def test_should_publish_reasserts_a_value_that_drifted_at_the_charger():
    # The scenario this exists for: we hold the car off, something at the box
    # (an RFID swipe, the app) clears frc, and nothing in our own memory changed.
    assert should_publish(FRC_OFF, FRC_NEUTRAL, FRC_OFF, 999.0, 10.0) is True
    assert should_publish(FRC_OFF, FRC_ON, FRC_OFF, 999.0, 10.0) is True


def test_should_publish_waits_for_our_own_write_to_echo_back():
    # Inside the settle window the charger's retained value is still the old one,
    # so re-asserting against it would just spam the broker.
    assert should_publish(FRC_OFF, FRC_NEUTRAL, FRC_OFF, 2.0, 10.0) is False
    # Once the echo is overdue, the disagreement is real.
    assert should_publish(FRC_OFF, FRC_NEUTRAL, FRC_OFF, 10.0, 10.0) is True


def test_should_publish_trusts_memory_when_the_charger_never_reports_the_key():
    # A firmware that doesn't publish this key would otherwise be rewritten every
    # single cycle, forever.
    assert should_publish(FRC_OFF, None, FRC_OFF, 999.0, 10.0) is False
    assert should_publish(PSM_THREE, None, PSM_THREE, None, 10.0) is False


def test_should_publish_treats_psm_auto_as_a_value_to_correct():
    # psm 0 is the charger's own auto mode: not the phase count we asked for, so
    # a box that fell back to it gets our value put back.
    assert should_publish(PSM_SINGLE, goe_parse.PSM_AUTO, PSM_SINGLE, 999.0, 10.0) is True
    assert should_publish(PSM_THREE, PSM_THREE, PSM_THREE, 999.0, 10.0) is False


def test_coerce_rejects_bools():
    assert coerce_int(True) is None
    assert coerce_float(False) is None
    assert coerce_int("6") == 6
    assert coerce_float("2.48") == 2.48
    assert coerce_int("x") is None
