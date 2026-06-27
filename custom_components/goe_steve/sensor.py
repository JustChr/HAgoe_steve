"""Sensor platform: what the brain decided, and why."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfElectricCurrent, UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import GoeSteveConfigEntry
from .coordinator import SteVeCoordinator
from .engine import compute_power_flow
from .entity import GoeSteveEntity, SteVeEntity
from .steve_api import recent_completed


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GoeSteveConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        [
            StatusSensor(coordinator),
            SurplusSensor(coordinator),
            TargetCurrentSensor(coordinator),
            PowerFlowSensor(coordinator),
            PriceForecastSensor(coordinator),
        ]
    )

    if coordinator.steve is not None:
        _setup_steve_sensors(coordinator.steve, async_add_entities)


@callback
def _setup_steve_sensors(
    steve: SteVeCoordinator, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    """Add the fixed SteVe sensors, plus one energy sensor per discovered tag.

    Tags are created lazily as SteVe reports them, so cards/users plugged in
    after setup appear automatically without a reconfigure.
    """
    async_add_entities([ActiveTransactionSensor(steve), LastSessionEnergySensor(steve)])

    known: set[str] = set()

    @callback
    def _discover_tags() -> None:
        data = steve.data
        if data is None:
            return
        new = [
            TagEnergySensor(steve, tag.id_tag, tag.name)
            for tag in data.tags
            if tag.id_tag not in known
        ]
        if new:
            known.update(sensor.tag_id for sensor in new)
            async_add_entities(new)

    _discover_tags()
    steve.async_add_listener(_discover_tags)


class StatusSensor(GoeSteveEntity, SensorEntity):
    """Plain-language explanation of the current decision — the key UX element."""

    _attr_icon = "mdi:ev-station"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "status")

    @property
    def native_value(self) -> str | None:
        decision = self.coordinator.data
        return decision.reason if decision else None

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        decision = self.coordinator.data
        settings = self.coordinator.settings
        if decision is None:
            return {}
        return {
            "mode": settings.mode.value,
            "battery_policy": settings.battery_policy.value,
            "controlling": decision.control,
            "charging": decision.should_charge,
            "target_current_a": round(decision.target_current_a, 1),
            "target_phases": decision.target_phases,
            # Structured reason so the card can localize the status line; the
            # sensor state itself stays the English ``reason`` text.
            "reason_key": decision.reason_key,
            "reason_params": decision.reason_params,
        }


class SurplusSensor(GoeSteveEntity, SensorEntity):
    """Power currently available to the car under the active battery policy."""

    _attr_icon = "mdi:solar-power"
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "surplus_for_car")

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.surplus_w if self.coordinator.data else None


class TargetCurrentSensor(GoeSteveEntity, SensorEntity):
    """The current the brain is asking the charger to use (0 when paused)."""

    _attr_icon = "mdi:current-ac"
    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "target_current")

    @property
    def native_value(self) -> float | None:
        decision = self.coordinator.data
        if decision is None:
            return None
        return decision.target_current_a if decision.should_charge else 0.0


class PowerFlowSensor(GoeSteveEntity, SensorEntity):
    """Live home energy balance — the data behind the card's flow diagram.

    State is the car's charging power; the PV/grid/battery/house breakdown rides
    along as attributes so the Lovelace card can render the whole flow from a
    single entity, no extra wiring required.
    """

    _attr_icon = "mdi:transit-connection-variant"
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "power_flow")

    @property
    def native_value(self) -> float | None:
        inputs = self.coordinator.last_inputs
        if inputs is None:
            return None
        return round(compute_power_flow(inputs).car_w)

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        inputs = self.coordinator.last_inputs
        if inputs is None:
            return {}
        flow = compute_power_flow(inputs)
        return {
            "pv_w": round(flow.pv_w),
            "grid_w": round(flow.grid_w),
            "battery_w": round(flow.battery_w) if flow.battery_w is not None else None,
            "battery_soc": flow.battery_soc,
            "car_w": round(flow.car_w),
            "house_w": round(flow.house_w),
            "car_connected": inputs.car_connected,
            "phases": inputs.phases,
        }


class PriceForecastSensor(GoeSteveEntity, SensorEntity):
    """The electricity-price forecast, surfaced for the price card.

    State is the current spot price; the upcoming price slots ride along as
    attributes (with the active cheap threshold) so the card can draw the curve
    and let the user drag the threshold onto it — mirroring how PowerFlowSensor
    feeds the flow diagram from a single entity.
    """

    _attr_icon = "mdi:cash-clock"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 3

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "price_forecast")

    @property
    def native_value(self) -> float | None:
        return self.coordinator.last_price_now

    @property
    def native_unit_of_measurement(self) -> str | None:
        return self.coordinator.price_unit

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        forecast = self.coordinator.last_forecast or []
        return {
            "slots": [
                {"start": slot.start.isoformat(), "price": round(slot.price, 5)}
                for slot in forecast
            ],
            "cheap_price": self.coordinator.settings.cheap_price,
            "unit": self.coordinator.price_unit,
        }


# --- SteVe sensors (Phase 3) -------------------------------------------------------


class ActiveTransactionSensor(SteVeEntity, SensorEntity):
    """The currently running charging session as reported by SteVe."""

    _attr_icon = "mdi:card-account-details"

    def __init__(self, coordinator: SteVeCoordinator) -> None:
        super().__init__(coordinator, "active_transaction")

    @property
    def native_value(self) -> str | None:
        data = self.coordinator.data
        if data is None:
            return None
        if not data.active:
            return "idle"
        return data.active[0].id_tag or "active"

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        data = self.coordinator.data
        if data is None or not data.active:
            return {}
        tx = data.active[0]
        return {
            "transaction_id": tx.id,
            "charge_box_id": tx.charge_box_id,
            "id_tag": tx.id_tag,
            "name": data.name_for_tag(tx.id_tag),
            "started": tx.start.isoformat() if tx.start else None,
            "active_sessions": len(data.active),
        }


class LastSessionEnergySensor(SteVeEntity, SensorEntity):
    """Energy delivered in the most recently finished session."""

    _attr_icon = "mdi:history"
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 2

    def __init__(self, coordinator: SteVeCoordinator) -> None:
        super().__init__(coordinator, "last_session_energy")

    @property
    def native_value(self) -> float | None:
        data = self.coordinator.data
        if data is None or data.last_session is None:
            return None
        return data.last_session.energy_kwh

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        data = self.coordinator.data
        if data is None or data.last_session is None:
            return {}
        tx = data.last_session
        return {
            "id_tag": tx.id_tag,
            "name": data.name_for_tag(tx.id_tag),
            "charge_box_id": tx.charge_box_id,
            "started": tx.start.isoformat() if tx.start else None,
            "stopped": tx.stop.isoformat() if tx.stop else None,
            # Recent finished sessions (newest first) so the card can show a short
            # history without a second sensor. Includes this last session at [0].
            "recent": [
                {
                    "name": data.name_for_tag(s.id_tag),
                    "energy": s.energy_kwh,
                    "started": s.start.isoformat() if s.start else None,
                    "stopped": s.stop.isoformat() if s.stop else None,
                }
                for s in recent_completed(data.transactions)
            ],
        }


class TagEnergySensor(SteVeEntity, SensorEntity):
    """Cumulative energy charged on one RFID id-tag (user)."""

    _attr_icon = "mdi:card-account-details-outline"
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_suggested_display_precision = 2

    def __init__(
        self, coordinator: SteVeCoordinator, tag_id: str, name: str | None = None
    ) -> None:
        super().__init__(coordinator, f"tag_energy_{tag_id}")
        self.tag_id = tag_id
        # Dynamic name: the translation supplies "{tag} energy". Seed it with the
        # tag's SteVe note (its friendly name) so the entity isn't a raw RFID UID;
        # the live `name` attribute below tracks later note edits.
        self._attr_translation_key = "tag_energy"
        self._attr_translation_placeholders = {"tag": name or tag_id}

    @property
    def native_value(self) -> float | None:
        data = self.coordinator.data
        if data is None:
            return None
        return round(data.energy_by_tag.get(self.tag_id, 0.0), 3)

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        data = self.coordinator.data
        if data is None:
            return {"id_tag": self.tag_id}
        tag = next((t for t in data.tags if t.id_tag == self.tag_id), None)
        return {
            "id_tag": self.tag_id,
            "name": tag.name if tag else self.tag_id,
            "blocked": tag.blocked if tag else None,
            "in_transaction": tag.in_transaction if tag else None,
            "expiry": tag.expiry.isoformat() if tag and tag.expiry else None,
        }
