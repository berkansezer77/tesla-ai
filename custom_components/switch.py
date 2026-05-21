"""Switch platform for POM Tesla Report."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    MANUAL_TRACKING_STATE_KEY,
    DATA_ASYNC_START_MANUAL_TRACKING,
    DATA_ASYNC_FINISH_MANUAL_TRACKING,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up POM Tesla Report switches."""
    async_add_entities([PomTeslaReportManualTrackingSwitch(hass, entry)])


class PomTeslaReportManualTrackingSwitch(SwitchEntity):
    """Switch that controls switch-based manual trip tracking."""

    _attr_name = "POM Tesla Report Manual Tracking"
    _attr_icon = "mdi:map-clock"
    _attr_has_entity_name = False

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the manual tracking switch."""
        self._hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_manual_tracking"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "POM Tesla Report",
            "manufacturer": "POM",
        }

    @property
    def available(self) -> bool:
        """Return whether the switch can call the backing functions."""
        domain_data = self._hass.data.get(DOMAIN, {})
        return (
            self._entry.entry_id in domain_data
            and callable(domain_data.get(DATA_ASYNC_START_MANUAL_TRACKING))
            and callable(domain_data.get(DATA_ASYNC_FINISH_MANUAL_TRACKING))
        )

    @property
    def is_on(self) -> bool:
        """Return whether manual tracking is active."""
        state = self._hass.data.get(DOMAIN, {}).get(MANUAL_TRACKING_STATE_KEY, {})
        return bool(state.get("active", False))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return useful state attributes."""
        state = self._hass.data.get(DOMAIN, {}).get(MANUAL_TRACKING_STATE_KEY, {})

        return {
            "active": bool(state.get("active", False)),
            "started_at": state.get("started_at"),
            "finished_at": state.get("finished_at"),
            "start_odometer": state.get("start_odometer"),
            "start_energy_kwh": state.get("start_energy_kwh"),
            "start_battery": state.get("start_battery"),
            "last_report_path": state.get("last_report_path"),
            "start_source": state.get("start_source"),
            "finish_source": state.get("finish_source"),
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Start manual tracking."""
        start_func = self._hass.data.get(DOMAIN, {}).get(DATA_ASYNC_START_MANUAL_TRACKING)

        if callable(start_func):
            await start_func(self._entry.entry_id)

        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Finish manual tracking and generate the report."""
        finish_func = self._hass.data.get(DOMAIN, {}).get(DATA_ASYNC_FINISH_MANUAL_TRACKING)

        if callable(finish_func):
            await finish_func(self._entry.entry_id)

        self.async_write_ha_state()
