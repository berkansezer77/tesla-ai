"""Select platform for POM Tesla Report.

Dashboard configuration is handled from the POM panel. The generated Dashboard
uses three live bottom-slot helper selects. They are kept in the background
without attaching them to the integration device page, and their entity IDs are
kept stable so generated YAML can always listen to the correct select.
"""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .dashboard.select import PomTeslaDashboardEnergySlotSelect


class PomTeslaDetachedDashboardEnergySlotSelect(PomTeslaDashboardEnergySlotSelect):
    """Dashboard helper select detached from the integration device card."""

    def __init__(self, entry: ConfigEntry, slot: int = 1) -> None:
        super().__init__(entry, slot=slot)
        self._attr_device_info = None


def _desired_select_entity_id(slot: int) -> str:
    if slot == 1:
        return "select.pom_tesla_dashboard_energy_slot_choice"
    return f"select.pom_tesla_dashboard_bottom_slot_{slot}_choice"


def _select_unique_id(slot: int) -> str:
    if slot == 1:
        return f"{DOMAIN}_dashboard_energy_slot_choice"
    return f"{DOMAIN}_dashboard_bottom_slot_{slot}_choice"


def _prepare_dashboard_select_registry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Keep live bottom-slot selects on stable entity IDs.

    If an older alpha leaves stale registry entries behind, HA can create
    select.pom_tesla_dashboard_bottom_slot_2_choice_2. The dashboard YAML then
    listens to the unsuffixed entity while the popup service changes the suffixed
    live entity. This makes slot 2/3 look unchanged after selection. This
    migration removes stale exact IDs and renames the current POM selects back
    to the stable IDs before the platform adds entities.
    """
    try:
        registry = er.async_get(hass)
    except Exception:
        return

    for slot in (1, 2, 3):
        desired_entity_id = _desired_select_entity_id(slot)
        current_unique_id = _select_unique_id(slot)

        try:
            existing = registry.async_get(desired_entity_id)
        except Exception:
            existing = None

        if existing is not None:
            existing_platform = str(getattr(existing, "platform", "") or "")
            existing_unique_id = str(getattr(existing, "unique_id", "") or "")
            existing_config_entry_id = str(getattr(existing, "config_entry_id", "") or "")
            if (
                existing_platform != DOMAIN
                or existing_unique_id != current_unique_id
                or existing_config_entry_id not in {"", entry.entry_id}
            ):
                try:
                    registry.async_remove(desired_entity_id)
                except Exception:
                    pass

        try:
            exact_after_cleanup = registry.async_get(desired_entity_id)
        except Exception:
            exact_after_cleanup = None

        for entity_entry in list(registry.entities.values()):
            entity_id = str(getattr(entity_entry, "entity_id", "") or "")
            unique_id = str(getattr(entity_entry, "unique_id", "") or "")
            platform = str(getattr(entity_entry, "platform", "") or "")
            if platform != DOMAIN or unique_id != current_unique_id:
                continue
            if entity_id == desired_entity_id:
                break
            if exact_after_cleanup is None:
                try:
                    registry.async_update_entity(entity_id, new_entity_id=desired_entity_id)
                except Exception:
                    pass
            break


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up POM Tesla Report select entities."""
    _prepare_dashboard_select_registry(hass, entry)
    async_add_entities([
        PomTeslaDetachedDashboardEnergySlotSelect(entry, slot=1),
        PomTeslaDetachedDashboardEnergySlotSelect(entry, slot=2),
        PomTeslaDetachedDashboardEnergySlotSelect(entry, slot=3),
    ])
