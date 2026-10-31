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
KEY_ACS = "acs"  # accessControl: 0 Open / 1 Wait (a card or the app must authorize)
KEY_TRX = "trx"  # transaction: null none yet / 0 started without a card / n = card slot

# Index of total active power (W) inside the ``nrg`` array:
# U(L1,L2,L3,N)=0-3, I(L1,L2,L3)=4-6, P(L1,L2,L3,N,Total)=7-11, pf=12-15.
NRG_TOTAL_POWER_INDEX = 11
NRG_PHASE_CURRENT_INDEXES = (4, 5, 6)

# A phase counts as carrying the car when it draws more than this. Well below the
# 6 A minimum a car may ever pull, well above the idle noise the meter reports on
# an unused phase.
PHASE_LIVE_CURRENT_A = 1.0

# carState values that mean a car is physically plugged in.
_CONNECTED_CAR_STATES = frozenset({2, 3, 4})

# forceState values.
FRC_NEUTRAL = 0
FRC_OFF = 1
FRC_ON = 2

# accessControl values.
ACS_OPEN = 0
ACS_WAIT = 1

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


def phases_from_nrg(nrg: Any) -> int | None:
    """Phase count the car is actually drawing on, from the ``nrg`` currents.

    The ground truth for ``P = I·φ·V``: indices 4-6 are the per-phase currents, so
    counting the live ones says what the car takes right now, not what the charger
    was told to offer. A car that charges single-phase on a three-phase supply is
    reported as 1 — which is the number the maths needs.

    Returns None when nothing is flowing (idle, or the array is unusable); the
    caller falls back to the configured phase mode then. Two live phases are
    reported as 3, because the charger only switches between single and three and
    the engine has no other vocabulary.
    """
    if not isinstance(nrg, list) or len(nrg) <= max(NRG_PHASE_CURRENT_INDEXES):
        return None
    live = 0
    for index in NRG_PHASE_CURRENT_INDEXES:
        amps = coerce_float(nrg[index])
        if amps is not None and amps > PHASE_LIVE_CURRENT_A:
            live += 1
    if live == 0:
        return None
    return 1 if live == 1 else 3


def car_connected(car_state: int | None) -> bool | None:
    """True when carState says a car is plugged in (2/3/4); None if unknown."""
    if car_state is None:
        return None
    return car_state in _CONNECTED_CAR_STATES


def awaiting_card(acs: Any, trx_reported: bool, trx: Any) -> bool:
    """True when the charger wants a card and none has authorized this plug-in yet.

    With access control on (``acs`` = Wait), a plug-in starts with ``trx`` null;
    a card tap (or the app, or an OCPP remote start) sets it. Forcing the charger
    on before that makes it open a transaction *without a card* (``trx`` 0): no
    OCPP StartTransaction, and card taps are refused until the car is unplugged.

    False when access control is off, or when ``trx`` hasn't been reported yet
    (unknown is not "waiting": the brain then behaves as it always did).
    """
    return coerce_int(acs) == ACS_WAIT and trx_reported and trx is None


def phase_count_to_psm(phases: int) -> int:
    """Map an engine phase *count* (1 or 3) to psm (1 single / 2 three)."""
    return PSM_SINGLE if int(phases) == 1 else PSM_THREE


def psm_to_phase_count(psm: int | None) -> int | None:
    """Map psm (1 single / 2 three) back to an engine phase *count* (1 or 3).

    ``PSM_AUTO`` and anything unknown return None: auto means the charger decides,
    so the mode alone doesn't say how many phases are in use.
    """
    if psm == PSM_SINGLE:
        return 1
    if psm == PSM_THREE:
        return 3
    return None


def should_publish(
    want: int,
    live: int | None,
    last_written: int | None,
    since_write_s: float | None,
    settle_s: float,
) -> bool:
    """Whether a charger key needs (re-)publishing to reach ``want``.

    Writing on "did *I* last write this?" alone is open-loop: anything that moves
    the value at the charger — an RFID swipe, the go-e app, the box's own session
    handling — is invisible, and the brain keeps believing a value it no longer
    holds. Since the charger republishes every key it owns, ``live`` closes the
    loop: we skip the write only when our memory *and* the charger agree.

    The four cases, in order:

    * intent changed → always write, whatever the charger currently says;
    * no reading (``live is None``) → trust the memory, because a firmware that
      never publishes this key would otherwise be rewritten forever;
    * we published within ``settle_s`` → wait, the echo hasn't landed yet and
      ``live`` is still the old value;
    * otherwise the value drifted at the charger → re-assert it.
    """
    if last_written != want:
        return True
    if live is None or live == want:
        return False
    if since_write_s is not None and since_write_s < settle_s:
        return False
    return True


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
