"""Select entities for live POM Tesla dashboard bottom slots."""

from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN

DATA_DASHBOARD_ENERGY_SELECT_ENTITY = "dashboard_energy_select_entity"
DATA_DASHBOARD_BOTTOM_SLOT_SELECT_ENTITY_PREFIX = "dashboard_bottom_slot_{}_select_entity"


ENERGY_SLOT_OPTIONS: dict[str, str] = {
    "energy_remaining": "Energy remaining",
    "battery_level": "Battery level",
    "battery_range": "Battery range",
    "inside_temp": "Inside temperature",
    "outside_temp": "Outside temperature",
    "odometer": "Odometer",
    "battery_temp": "Battery/module temperature",
    "battery_heater": "Battery heater",
    "empty": "Empty / hidden",
}


class PomTeslaDashboardEnergySlotSelect(SelectEntity, RestoreEntity):
    """Live select for one bottom bar field."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:form-select"
    _attr_options = list(ENERGY_SLOT_OPTIONS.values())

    def __init__(self, entry: ConfigEntry, slot: int = 1) -> None:
        self._entry = entry
        self._slot = int(slot or 1)
        if self._slot < 1 or self._slot > 3:
            self._slot = 1
        defaults = {1: "energy_remaining", 2: "inside_temp", 3: "battery_temp"}
        self._selected_key = defaults.get(self._slot, "energy_remaining")
        if self._selected_key not in ENERGY_SLOT_OPTIONS:
            self._selected_key = "energy_remaining"
        self._user_selected = False

        if self._slot == 1:
            self._attr_name = "POM Tesla Dashboard Bottom Slot 1"
            self._attr_unique_id = f"{DOMAIN}_dashboard_energy_slot_choice"
            self._attr_entity_id = "select.pom_tesla_dashboard_energy_slot_choice"
        else:
            self._attr_name = f"POM Tesla Dashboard Bottom Slot {self._slot}"
            self._attr_unique_id = f"{DOMAIN}_dashboard_bottom_slot_{self._slot}_choice"
            self._attr_entity_id = f"select.pom_tesla_dashboard_bottom_slot_{self._slot}_choice"

        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "POM Tesla Report Dashboard",
            "manufacturer": "POM",
        }

    @property
    def current_option(self) -> str | None:
        return ENERGY_SLOT_OPTIONS.get(self._selected_key)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "dashboard_live_select": True,
            "slot": self._slot,
            "slot_key": f"bottom_slot_{self._slot}",
            "selected_key": self._selected_key,
            "user_selected": self._user_selected,
            "option_keys": list(ENERGY_SLOT_OPTIONS.keys()),
            "option_labels": dict(ENERGY_SLOT_OPTIONS),
        }

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        store_key = DATA_DASHBOARD_BOTTOM_SLOT_SELECT_ENTITY_PREFIX.format(self._slot)
        self.hass.data.setdefault(DOMAIN, {})[store_key] = self
        if self._slot == 1:
            # Legacy key kept for older service/dashboard code.
            self.hass.data.setdefault(DOMAIN, {})[DATA_DASHBOARD_ENERGY_SELECT_ENTITY] = self

        previous = await self.async_get_last_state()
        if previous is None:
            self.async_write_ha_state()
            return
        attrs = previous.attributes or {}
        selected_key = str(attrs.get("selected_key") or "").strip()
        self._user_selected = bool(attrs.get("user_selected", False))
        if selected_key in ENERGY_SLOT_OPTIONS:
            self._selected_key = selected_key
        else:
            label_to_key = {label: key for key, label in ENERGY_SLOT_OPTIONS.items()}
            if previous.state in label_to_key:
                self._selected_key = label_to_key[previous.state]
        self.async_write_ha_state()

    async def async_select_option(self, option: str) -> None:
        label_to_key = {label: key for key, label in ENERGY_SLOT_OPTIONS.items()}
        if option not in label_to_key:
            return
        self._selected_key = label_to_key[option]
        self._user_selected = True
        self.async_write_ha_state()
