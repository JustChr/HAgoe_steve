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
            TagEnergySensor(steve, tag.id_tag)
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
            "charge_box_id": tx.charge_box_id,
            "started": tx.start.isoformat() if tx.start else None,
            "stopped": tx.stop.isoformat() if tx.stop else None,
        }


class TagEnergySensor(SteVeEntity, SensorEntity):
    """Cumulative energy charged on one RFID id-tag (user)."""

    _attr_icon = "mdi:card-account-details-outline"
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_suggested_display_precision = 2

    def __init__(self, coordinator: SteVeCoordinator, tag_id: str) -> None:
        super().__init__(coordinator, f"tag_energy_{tag_id}")
        self.tag_id = tag_id
        # Dynamic name: the translation supplies "{tag} energy".
        self._attr_translation_key = "tag_energy"
        self._attr_translation_placeholders = {"tag": tag_id}

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
            "blocked": tag.blocked if tag else None,
            "in_transaction": tag.in_transaction if tag else None,
            "expiry": tag.expiry.isoformat() if tag and tag.expiry else None,
        }
