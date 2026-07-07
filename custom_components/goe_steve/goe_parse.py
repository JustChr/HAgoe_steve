"""Pure go-e MQTT parsing — no Home Assistant imports, so it's unit-testable.

Holds the go-e API v2 key names / enum values and the small amount of decoding
logic (topic splitting, JSON payloads, the ``nrg`` power index, carState → a
"connected" flag). The HA-facing client in ``goe_mqtt.py`` builds on these.

Verified against a live charger (fw 60.x); see docs/mqtt-direct-concept.md.
"""

from __future__ import annotations

import json
from typing import Any

# The default topic prefix a go-e charger uses before its serial.
GOE_DEFAULT_PREFIX = "go-eCharger"

# --- go-e API v2 keys we read/write ------------------------------------------------
KEY_AMP = "amp"  # requestedCurrent, A (R/W)
KEY_FRC = "frc"  # forceState: 0 Neutral / 1 Off / 2 On (R/W)
KEY_PSM = "psm"  # phaseSwitchMode: 0 auto / 1 single / 2 three (R/W)
KEY_CAR = "car"  # carState: 0 Unknown/1 Idle/2 Charging/3 WaitCar/4 Complete/5 Error
KEY_NRG = "nrg"  # energy array; index 11 = total power in W
KEY_WH = "wh"  # energy since car connected, Wh (session-scoped, resets at plug-in)
KEY_ETO = "eto"  # energy_total, Wh (lifetime)
KEY_ACU = "acu"  # amps the car is actually allowed right now
KEY_ALW = "alw"  # allowed to charge at all now (bool)
KEY_PNP = "pnp"  # number of phases actually charging
KEY_MODEL_STATUS = "modelStatus"  # go-e's own reason code for charging / not
KEY_CBL = "cbl"  # cable current limit, A
KEY_FWV = "fwv"  # firmware version (string)
KEY_FNA = "fna"  # friendly name (string)
KEY_MCC = "mcc"  # MQTT connected (bool)

# Index of total active power (W) inside the ``nrg`` array:
# U(L1,L2,L3,N)=0-3, I(L1,L2,L3)=4-6, P(L1,L2,L3,N,Total)=7-11, pf=12-15.
NRG_TOTAL_POWER_INDEX = 11

# carState values that mean a car is physically plugged in.
_CONNECTED_CAR_STATES = frozenset({2, 3, 4})

# forceState values.
FRC_NEUTRAL = 0
FRC_OFF = 1
FRC_ON = 2

# phaseSwitchMode values (note: 1 = single phase, 2 = three phase).
PSM_AUTO = 0
PSM_SINGLE = 1
PSM_THREE = 2


def normalize_base_topic(base: str) -> str:
    """Trim spaces and any trailing slash; a *leading* slash is kept on purpose."""
    return base.strip().rstrip("/")


def base_topic_from_message_topic(topic: str) -> tuple[str, str] | None:
    """Split a charger message topic into (base_topic, serial), or None.

    Handles both ``go-eCharger/<serial>/<key>`` and the leading-slash variant
    ``/go-eCharger/<serial>/<key>``. The returned base preserves the leading
    slash so it can be reused verbatim for subscribing and writing.
    """
    segs = topic.split("/")
    try:
        i = segs.index(GOE_DEFAULT_PREFIX)
    except ValueError:
        return None
    if i + 1 >= len(segs):
        return None
    serial = segs[i + 1]
    base = "/".join(segs[: i + 2])  # a leading "" segment re-emits the slash
    return base, serial


def key_from_message_topic(topic: str, base_topic: str) -> str | None:
    """The single key a message carries, or None for ``<key>/set`` / ``/result``.

    Returns None when the remainder after the base is empty or has more segments
    (our own write/result echoes), so only the charger's own value topics ingest.
    """
    rest = topic[len(base_topic) :].lstrip("/")
    if not rest or "/" in rest:
        return None
    return rest


def decode_payload(payload: Any) -> Any:
    """JSON-decode a payload; fall back to the raw string when it isn't JSON."""
    if isinstance(payload, (bytes, bytearray)):
        payload = payload.decode(errors="replace")
    try:
        return json.loads(payload)
    except (ValueError, TypeError):
        return payload


def power_from_nrg(nrg: Any) -> float | None:
    """Total active power (W) from the ``nrg`` array, or None if unusable."""
    if isinstance(nrg, list) and len(nrg) > NRG_TOTAL_POWER_INDEX:
        return coerce_float(nrg[NRG_TOTAL_POWER_INDEX])
    return None


def car_connected(car_state: int | None) -> bool | None:
    """True when carState says a car is plugged in (2/3/4); None if unknown."""
    if car_state is None:
        return None
    return car_state in _CONNECTED_CAR_STATES


def phase_count_to_psm(phases: int) -> int:
    """Map an engine phase *count* (1 or 3) to psm (1 single / 2 three)."""
    return PSM_SINGLE if int(phases) == 1 else PSM_THREE


def coerce_int(value: Any) -> int | None:
    """int() a value, rejecting bools and non-numerics."""
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def coerce_float(value: Any) -> float | None:
    """float() a value, rejecting bools and non-numerics."""
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None
