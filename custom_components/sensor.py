"""Sensor platform for POM Tesla Report."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN, DEFAULT_NAME
from . import LIVE_TRIP_SENSOR_STORE, get_live_trip_state, build_live_trip_public_attributes


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up POM Tesla Report sensors."""
    sensor = PomLiveTripSensor(hass, entry)
    hass.data.setdefault(DOMAIN, {}).setdefault(LIVE_TRIP_SENSOR_STORE, {})[entry.entry_id] = sensor
    async_add_entities([sensor])


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
        state = get_live_trip_state(self.hass, self.entry.entry_id)
        return build_live_trip_public_attributes(state)
