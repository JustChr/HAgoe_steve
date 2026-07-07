"""Direct MQTT link to a go-e charger — no third-party integration in between.

The go-e charger publishes one *retained* topic per API key at ``<base>/<key>``
(JSON-encoded payloads) and accepts writes at ``<base>/<key>/set``. This module
subscribes to ``<base>/#``, caches the latest value per key, exposes typed
accessors for the handful the brain needs, and publishes writes back.

Retained topics mean the cache is primed the instant we subscribe, so entities
render immediately (``local_push``). The base topic is stored *verbatim* — some
chargers emit a leading slash (``/go-eCharger/<serial>/…``), and that slash is
part of every read and write topic.

Pure decoding lives in the HA-free ``goe_parse`` module (unit-tested); this file
is the Home Assistant glue. See ``docs/mqtt-direct-concept.md`` for the mapping.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from homeassistant.components import mqtt
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback

from .goe_parse import (
    FRC_NEUTRAL,
    FRC_OFF,
    FRC_ON,
    GOE_DEFAULT_PREFIX,
    KEY_ACU,
    KEY_ALW,
    KEY_AMP,
    KEY_CAR,
    KEY_CBL,
    KEY_ETO,
    KEY_FNA,
    KEY_FRC,
    KEY_FWV,
    KEY_MCC,
    KEY_MODEL_STATUS,
    KEY_NRG,
    KEY_PNP,
    KEY_PSM,
    KEY_WH,
    PSM_AUTO,
    PSM_SINGLE,
    PSM_THREE,
    base_topic_from_message_topic,
    car_connected as _car_connected,
    coerce_float,
    coerce_int,
    decode_payload,
    key_from_message_topic,
    normalize_base_topic,
    phase_count_to_psm,
    power_from_nrg,
)

_LOGGER = logging.getLogger(__name__)

# Re-exported so callers can import the enums / helpers from here.
__all__ = [
    "FRC_NEUTRAL",
    "FRC_OFF",
    "FRC_ON",
    "PSM_AUTO",
    "PSM_SINGLE",
    "PSM_THREE",
    "GoeMqttClient",
    "async_discover_chargers",
    "normalize_base_topic",
]


class GoeMqttClient:
    """Caches a go-e charger's MQTT state and writes settings back to it."""

    def __init__(self, hass: HomeAssistant, base_topic: str) -> None:
        self.hass = hass
        self.base_topic = normalize_base_topic(base_topic)
        self._values: dict[str, Any] = {}
        self._unsub: CALLBACK_TYPE | None = None
        self._listeners: list[CALLBACK_TYPE] = []
        # Availability latches on the first message; the charger's retained topics
        # make that near-instant after subscribing.
        self._seen = False

    async def async_start(self) -> None:
        """Subscribe to the charger's topic tree. Idempotent."""
        if self._unsub is not None:
            return
        self._unsub = await mqtt.async_subscribe(
            self.hass, f"{self.base_topic}/#", self._on_message, qos=0
        )
        _LOGGER.debug("Subscribed to go-e topics at %s/#", self.base_topic)

    @callback
    def async_stop(self) -> None:
        """Unsubscribe and drop listeners."""
        if self._unsub is not None:
            self._unsub()
            self._unsub = None
        self._listeners.clear()

    @callback
    def _on_message(self, msg: mqtt.ReceiveMessage) -> None:
        """Ingest one published key value; ignore our own ``/set`` and ``/result``."""
        key = key_from_message_topic(msg.topic, self.base_topic)
        if key is None:
            return
        self._values[key] = decode_payload(msg.payload)
        self._seen = True
        for listener in list(self._listeners):
            listener()

    @callback
    def async_add_listener(self, update_callback: CALLBACK_TYPE) -> CALLBACK_TYPE:
        """Register a callback fired on every value update; returns an unsub."""
        self._listeners.append(update_callback)

        @callback
        def _remove() -> None:
            if update_callback in self._listeners:
                self._listeners.remove(update_callback)

        return _remove

    async def _publish(self, key: str, value: Any) -> None:
        """Publish a JSON-encoded write to ``<base>/<key>/set``."""
        try:
            await mqtt.async_publish(
                self.hass, f"{self.base_topic}/{key}/set", json.dumps(value)
            )
        except Exception as err:  # noqa: BLE001 - a write must never break the loop
            _LOGGER.warning("Failed to publish go-e %s=%s: %s", key, value, err)

    # --- Raw access -------------------------------------------------------------
    @property
    def available(self) -> bool:
        """True once we've received any message (charger + MQTT are alive).

        When the charger reports ``mcc`` (MQTT connected) we trust it; otherwise we
        fall back to "have we ever seen a message".
        """
        mcc = self._values.get(KEY_MCC)
        if isinstance(mcc, bool):
            return mcc
        return self._seen

    def get(self, key: str) -> Any:
        """Latest cached value for a key, or None."""
        return self._values.get(key)

    # --- Typed reads the brain uses --------------------------------------------
    @property
    def car_state(self) -> int | None:
        return coerce_int(self.get(KEY_CAR))

    @property
    def car_connected(self) -> bool | None:
        """True when a car is plugged in (carState 2/3/4), None if unknown."""
        return _car_connected(self.car_state)

    @property
    def power_w(self) -> float | None:
        """Total active charging power (W) from ``nrg[11]``, or None."""
        return power_from_nrg(self.get(KEY_NRG))

    @property
    def session_wh(self) -> float | None:
        """Energy since the car connected (Wh); resets at plug-in."""
        return coerce_float(self.get(KEY_WH))

    @property
    def total_energy_wh(self) -> float | None:
        return coerce_float(self.get(KEY_ETO))

    @property
    def phases(self) -> int | None:
        """Phases actually charging (``pnp``), or None."""
        return coerce_int(self.get(KEY_PNP))

    @property
    def allowed_current_a(self) -> int | None:
        return coerce_int(self.get(KEY_ACU))

    @property
    def charging_allowed(self) -> bool | None:
        alw = self.get(KEY_ALW)
        return alw if isinstance(alw, bool) else None

    @property
    def requested_current_a(self) -> int | None:
        return coerce_int(self.get(KEY_AMP))

    @property
    def force_state(self) -> int | None:
        return coerce_int(self.get(KEY_FRC))

    @property
    def phase_mode(self) -> int | None:
        return coerce_int(self.get(KEY_PSM))

    @property
    def model_status(self) -> int | None:
        return coerce_int(self.get(KEY_MODEL_STATUS))

    @property
    def cable_limit_a(self) -> int | None:
        return coerce_int(self.get(KEY_CBL))

    @property
    def firmware(self) -> str | None:
        value = self.get(KEY_FWV)
        return str(value) if value is not None else None

    @property
    def friendly_name(self) -> str | None:
        value = self.get(KEY_FNA)
        return str(value) if value else None

    # --- Writes -----------------------------------------------------------------
    async def set_amp(self, amps: int) -> None:
        """Set the requested charging current (A)."""
        await self._publish(KEY_AMP, int(amps))

    async def set_force(self, force: int) -> None:
        """Set forceState: 0 Neutral / 1 Off / 2 On."""
        await self._publish(KEY_FRC, int(force))

    async def set_phase_count(self, phases: int) -> None:
        """Force a phase *count* (1 or 3) via psm (1 = single, 2 = three)."""
        await self._publish(KEY_PSM, phase_count_to_psm(phases))

    async def set_phase_mode(self, psm: int) -> None:
        """Set the raw phase-switch mode (0 auto / 1 single / 2 three)."""
        await self._publish(KEY_PSM, int(psm))


async def async_discover_chargers(
    hass: HomeAssistant, timeout: float = 4.0
) -> dict[str, dict[str, str]]:
    """Listen briefly for go-e chargers on the broker; return {base_topic: info}.

    Scans both ``go-eCharger/#`` and the leading-slash ``/go-eCharger/#`` so a
    charger with an empty MQTT prefix is found too. ``info`` may carry ``serial``,
    ``name`` (fna) and ``firmware`` (fwv) for a friendlier picker. Returns an empty
    dict when MQTT is unavailable or nothing answers in time.
    """
    import asyncio

    found: dict[str, dict[str, str]] = {}

    @callback
    def _on_message(msg: mqtt.ReceiveMessage) -> None:
        parsed = base_topic_from_message_topic(msg.topic)
        if parsed is None:
            return
        base, serial = parsed
        info = found.setdefault(base, {"serial": serial})
        key = msg.topic.rsplit("/", 1)[-1]
        if key == KEY_FNA:
            name = decode_payload(msg.payload)
            if name:
                info["name"] = str(name)
        elif key == KEY_FWV:
            fw = decode_payload(msg.payload)
            if fw:
                info["firmware"] = str(fw)

    unsubs: list[CALLBACK_TYPE] = []
    try:
        for topic_filter in (f"{GOE_DEFAULT_PREFIX}/#", f"/{GOE_DEFAULT_PREFIX}/#"):
            unsubs.append(await mqtt.async_subscribe(hass, topic_filter, _on_message))
    except Exception as err:  # noqa: BLE001 - MQTT may be unconfigured
        _LOGGER.debug("go-e discovery could not subscribe: %s", err)
        for unsub in unsubs:
            unsub()
        return {}

    try:
        await asyncio.sleep(timeout)
    finally:
        for unsub in unsubs:
            unsub()
    return found
