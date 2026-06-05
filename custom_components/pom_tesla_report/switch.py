"""Switch platform for POM Tesla Report."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import entity_registry as er

from .const import (
    DOMAIN,
    MANUAL_TRACKING_STATE_KEY,
    DATA_ASYNC_START_MANUAL_TRACKING,
    DATA_ASYNC_FINISH_MANUAL_TRACKING,
)

from .dashboard.switch import PomTeslaDashboardSwitch, SWITCHES as DASHBOARD_SWITCHES


def _dashboard_helper_desired_entity_id(key: str) -> str:
    """Return the stable dashboard helper entity_id used by generated YAML."""
    return f"switch.pom_tesla_dashboard_{key}"


def _dashboard_helper_unique_id(key: str) -> str:
    """Return the current integration unique_id for a dashboard helper."""
    return f"{DOMAIN}_{key}"


def _prepare_dashboard_helper_registry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Keep dashboard helper switches on stable entity IDs.

    Earlier standalone/alpha installs can leave entity registry records behind.
    Home Assistant then creates switch.pom_tesla_dashboard_controls_2 etc.
    The generated dashboard uses these helpers for the sidebar, map opacity,
    person map mode, charge popup, and fullscreen. If the helper entity id is
    suffixed or occupied by an old integration entry, those buttons appear but
    the related conditional cards never change.

    This migration removes stale exact IDs owned by a different integration and
    renames the current POM helper back to the stable ID whenever possible.
    """
    try:
        registry = er.async_get(hass)
    except Exception:  # pragma: no cover - HA defensive path
        return

    for description in DASHBOARD_SWITCHES:
        key = description.key
        desired_entity_id = _dashboard_helper_desired_entity_id(key)
        current_unique_id = _dashboard_helper_unique_id(key)

        # If the clean desired id is occupied by the old standalone installer
        # or by a stale alpha entry, free it so the current helper can claim it.
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

        # If our current helper already exists with _2/_3 suffix, rename it
        # back to the stable entity id now that the old exact id is gone.
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


def _remove_dashboard_helper_switch_registry_entries(hass: HomeAssistant) -> None:
    """Remove legacy dashboard helper switch entities from the device page.

    Dashboard settings are now managed from the POM panel. Keeping these helper
    switches on the integration device page makes the integration look noisy and
    confusing. Manual Tracking stays as the only switch entity.
    """
    try:
        registry = er.async_get(hass)
    except Exception:  # pragma: no cover - HA defensive path
        return

    helper_unique_ids = {f"{DOMAIN}_{description.key}" for description in DASHBOARD_SWITCHES}
    helper_exact_ids = {
        f"switch.pom_tesla_dashboard_{description.key}"
        for description in DASHBOARD_SWITCHES
    }
    for entity_entry in list(registry.entities.values()):
        entity_id = str(getattr(entity_entry, "entity_id", "") or "")
        unique_id = str(getattr(entity_entry, "unique_id", "") or "")
        platform = str(getattr(entity_entry, "platform", "") or "")
        # Remove current POM helper records by unique_id, and old/standalone
        # helper records by their exact stable entity_id.
        if unique_id in helper_unique_ids or entity_id in helper_exact_ids:
            try:
                registry.async_remove(entity_id)
            except Exception:
                pass



class PomTeslaDetachedDashboardSwitch(PomTeslaDashboardSwitch):
    """Dashboard helper switch kept alive but not attached to the device card.

    The generated dashboard and popups still depend on exact helper entity IDs
    such as switch.pom_tesla_dashboard_charge_popup. alpha213 removed these
    helpers to clean the integration device page; that made popups stop working.
    This class restores the helper entities while keeping the device page clean.
    """

    def __init__(self, entry: ConfigEntry, description) -> None:
        super().__init__(entry, description)
        self._attr_device_info = None




async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up POM Tesla Report switches.

    Manual Tracking stays on the integration device page. Dashboard helper
    switches are created in the background without device_info so popups work
    while the device page remains clean.
    """
    _prepare_dashboard_helper_registry(hass, entry)
    async_add_entities(
        [PomTeslaReportManualTrackingSwitch(hass, entry)]
        + [PomTeslaDetachedDashboardSwitch(entry, description) for description in DASHBOARD_SWITCHES]
    )


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
