"""Switch entities for POM Tesla Report Dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN


@dataclass(frozen=True)
class DashboardSwitchDescription:
    """Dashboard switch description."""

    key: str
    name: str
    icon: str
    default_on: bool


SWITCHES: tuple[DashboardSwitchDescription, ...] = (
    DashboardSwitchDescription(
        key="map",
        name="POM Tesla Dashboard Map",
        icon="mdi:map",
        default_on=True,
    ),
    DashboardSwitchDescription(
        key="controls",
        name="POM Tesla Dashboard Controls",
        icon="mdi:tune",
        default_on=True,
    ),
    DashboardSwitchDescription(
        key="interactive_map",
        name="POM Tesla Dashboard Interactive Map",
        icon="mdi:map-marker-path",
        default_on=False,
    ),
    DashboardSwitchDescription(
        key="person_cards_on_map",
        name="POM Tesla Dashboard Person Cards On Map",
        icon="mdi:account-convert",
        default_on=False,
    ),
    DashboardSwitchDescription(
        key="charge_popup",
        name="POM Tesla Dashboard Charge Popup",
        icon="mdi:ev-station",
        default_on=False,
    ),
    DashboardSwitchDescription(
        key="address_popup",
        name="POM Tesla Dashboard Address Popup",
        icon="mdi:map-marker-radius-outline",
        default_on=False,
    ),
    DashboardSwitchDescription(
        key="energy_popup",
        name="POM Tesla Dashboard Energy Popup",
        icon="mdi:form-select",
        default_on=False,
    ),
    DashboardSwitchDescription(
        key="energy_popup_2",
        name="POM Tesla Dashboard Energy Popup 2",
        icon="mdi:form-select",
        default_on=False,
    ),
    DashboardSwitchDescription(
        key="energy_popup_3",
        name="POM Tesla Dashboard Energy Popup 3",
        icon="mdi:form-select",
        default_on=False,
    ),
    DashboardSwitchDescription(
        key="person_track_popup",
        name="POM Tesla Dashboard Person Track Popup",
        icon="mdi:account-map-outline",
        default_on=False,
    ),
    DashboardSwitchDescription(
        key="person_track_1_popup",
        name="POM Tesla Dashboard Person Track 1 Popup",
        icon="mdi:account-map-outline",
        default_on=False,
    ),
    DashboardSwitchDescription(
        key="person_track_2_popup",
        name="POM Tesla Dashboard Person Track 2 Popup",
        icon="mdi:account-map-outline",
        default_on=False,
    ),
    DashboardSwitchDescription(
        key="person_track_3_popup",
        name="POM Tesla Dashboard Person Track 3 Popup",
        icon="mdi:account-map-outline",
        default_on=False,
    ),
    DashboardSwitchDescription(
        key="fullscreen",
        name="POM Tesla Dashboard Fullscreen",
        icon="mdi:fullscreen",
        default_on=True,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up dashboard helper switches."""
    async_add_entities([PomTeslaDashboardSwitch(entry, description) for description in SWITCHES])


class PomTeslaDashboardSwitch(SwitchEntity, RestoreEntity):
    """Auto-created helper switch used by the generated Tesla dashboard."""

    _attr_has_entity_name = False

    def __init__(self, entry: ConfigEntry, description: DashboardSwitchDescription) -> None:
        """Initialize the switch."""
        self._entry = entry
        self._description = description
        self._attr_name = description.name
        self._attr_unique_id = f"{DOMAIN}_{description.key}"
        # The generated dashboard references these exact entity IDs. Setting the
        # suggested/default entity_id avoids users having to create/select helper
        # booleans manually on clean installations.
        self._attr_entity_id = f"switch.pom_tesla_dashboard_{description.key}"
        self._attr_icon = description.icon
        self._attr_is_on = description.default_on
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "POM Tesla Report Dashboard",
            "manufacturer": "POM",
        }

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        return {"dashboard_helper": True, "helper_key": self._description.key}

    async def async_added_to_hass(self) -> None:
        """Restore state after restart.

        For the alpha dashboard merge, controls and fullscreen must come up ON
        even if an earlier broken alpha restored them as off. The user can still
        toggle them from the dashboard after startup.
        """
        await super().async_added_to_hass()
        if self._description.key in {"controls", "fullscreen"}:
            self._attr_is_on = True
            self.async_write_ha_state()
            return
        previous = await self.async_get_last_state()
        if previous is not None:
            self._attr_is_on = previous.state == "on"

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn switch on."""
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn switch off."""
        self._attr_is_on = False
        self.async_write_ha_state()

    async def async_toggle(self, **kwargs: Any) -> None:
        """Toggle switch."""
        self._attr_is_on = not bool(self._attr_is_on)
        self.async_write_ha_state()
