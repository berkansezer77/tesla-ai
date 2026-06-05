"""Sensor platform for POM Tesla Report."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfLength
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN, DEFAULT_NAME
from . import (
    LIVE_TRIP_SENSOR_STORE,
    TRIP_ELEVATION_SENSOR_STORE,
    get_live_trip_state,
    build_live_trip_public_attributes,
    get_live_entry_config_for_entry_id,
    ensure_live_trip_ai_runtime_interval,
    get_trip_elevation_state,
    build_trip_elevation_public_attributes,
)
from .dashboard.sensor import PomTeslaDashboardLocationLabelSensor, PomTeslaDashboardLastChargeSensor, PomTeslaDashboardPersonTrackSensor


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up POM Tesla Report sensors."""
    sensor = PomLiveTripSensor(hass, entry)
    elevation_sensor = PomTripElevationSensor(hass, entry)
    # Keep the elevation sensor available even before the first driving sample.
    # It should show an unknown numeric value with status=idle, not unavailable.
    elevation_state = get_trip_elevation_state(hass, entry.entry_id)
    elevation_state.setdefault("status", "idle")
    elevation_state.setdefault("provider", "Open-Meteo Elevation API")
    elevation_state.setdefault("source", "")
    elevation_state.setdefault("last_error", "")
    domain_data = hass.data.setdefault(DOMAIN, {})
    domain_data.setdefault(LIVE_TRIP_SENSOR_STORE, {})[entry.entry_id] = sensor
    domain_data.setdefault(TRIP_ELEVATION_SENSOR_STORE, {})[entry.entry_id] = elevation_sensor
    dashboard_location_sensor = PomTeslaDashboardLocationLabelSensor(hass, entry)
    person_sensors = [PomTeslaDashboardPersonTrackSensor(hass, entry, slot) for slot in (1, 2, 3)]
    domain_data[entry.entry_id + "_location_label_sensor"] = dashboard_location_sensor
    for person_sensor in person_sensors:
        domain_data[f"{entry.entry_id}_person_track_{person_sensor.slot}_sensor"] = person_sensor
    async_add_entities([sensor, elevation_sensor, dashboard_location_sensor, PomTeslaDashboardLastChargeSensor(hass, entry), *person_sensors])


class PomLiveTripSensor(SensorEntity):
    """Backend live trip calculation sensor."""

    _attr_icon = "mdi:car-clock"
    _attr_has_entity_name = False

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self.hass = hass
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_live_trip"
        self._attr_name = "POM Live Trip"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title or DEFAULT_NAME,
            manufacturer="POM",
            model="Tesla Report",
        )

    @property
    def native_value(self) -> str:
        """Return the live trip status."""
        state = get_live_trip_state(self.hass, self.entry.entry_id)
        return str(state.get("status") or "idle")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return live trip attributes."""
        data = get_live_entry_config_for_entry_id(self.hass, self.entry.entry_id, {**dict(self.entry.data or {}), **dict(self.entry.options or {})})
        ensure_live_trip_ai_runtime_interval(self.hass, self.entry.entry_id, data, realign_on_change=True)
        state = get_live_trip_state(self.hass, self.entry.entry_id)
        return build_live_trip_public_attributes(state)

class PomTripElevationSensor(SensorEntity):
    """Open-Meteo based live trip elevation sensor."""

    _attr_icon = "mdi:elevation-rise"
    _attr_has_entity_name = False
    _attr_native_unit_of_measurement = UnitOfLength.METERS
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self.hass = hass
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_trip_elevation"
        self._attr_name = "POM Trip Elevation"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title or DEFAULT_NAME,
            manufacturer="POM",
            model="Tesla Report",
        )

    @property
    def available(self) -> bool:
        """Keep the entity available while waiting for the first active-trip sample."""
        return True

    @property
    def native_value(self) -> float | None:
        """Return current terrain elevation in meters.

        Before the first Live Trip / Manual Tracking sample there is no
        trustworthy elevation value yet. In that idle state we deliberately
        return None so Home Assistant shows unknown, while available remains
        True and attributes explain the status.
        """
        state = get_trip_elevation_state(self.hass, self.entry.entry_id)
        value = state.get("elevation")
        try:
            return round(float(value), 1)
        except (TypeError, ValueError):
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return elevation tracking attributes."""
        state = get_trip_elevation_state(self.hass, self.entry.entry_id)
        return build_trip_elevation_public_attributes(state)

