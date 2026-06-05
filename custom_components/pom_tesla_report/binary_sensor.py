"""Binary sensor platform for POM Tesla Report aggregate vehicle openings."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_STATE_CHANGED
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_PANEL_DASHBOARD_ENTITY_MAP,
    DEFAULT_NAME,
    DOMAIN,
)

WINDOWS_AGGREGATE_ROLE = "dashboard_vehicle_windows_aggregate"
WINDOW_PART_ROLES = {
    "front_left_window": "dashboard_vehicle_window_front_left",
    "front_right_window": "dashboard_vehicle_window_front_right",
    "rear_left_window": "dashboard_vehicle_window_rear_left",
    "rear_right_window": "dashboard_vehicle_window_rear_right",
}

DOORS_AGGREGATE_ROLE = "dashboard_vehicle_doors_aggregate"
DOOR_PART_ROLES = {
    "front_left_door": "dashboard_vehicle_door_front_left",
    "front_right_door": "dashboard_vehicle_door_front_right",
    "rear_left_door": "dashboard_vehicle_door_rear_left",
    "rear_right_door": "dashboard_vehicle_door_rear_right",
}

OPENING_EXTRA_ROLES = {
    "trunk": "dashboard_vehicle_trunk",
    "frunk": "dashboard_vehicle_frunk",
    "charge_port": "dashboard_vehicle_charge_port",
}

OWN_AGGREGATE_ENTITY_IDS = {
    "binary_sensor.pom_windows_open",
    "binary_sensor.pom_doors_open",
    "binary_sensor.pom_openings_open",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up aggregate open/close binary sensors."""
    async_add_entities(
        [
            PomVehicleAggregateOpeningSensor(hass, entry, "windows"),
            PomVehicleAggregateOpeningSensor(hass, entry, "doors"),
            PomVehicleAggregateOpeningSensor(hass, entry, "openings"),
        ]
    )


def _current_entry_data(hass: HomeAssistant, entry: ConfigEntry) -> dict[str, Any]:
    """Return the freshest config entry data/options available."""
    root = hass.data.setdefault(DOMAIN, {})
    in_memory = root.get(entry.entry_id)
    merged = {**dict(entry.data or {}), **dict(entry.options or {})}
    if isinstance(in_memory, dict):
        merged.update(in_memory)
    return merged


def _dashboard_role_map(data: dict[str, Any]) -> dict[str, str]:
    """Return dashboard role -> entity_id mapping from panel dashboard entity map."""
    rows = data.get(CONF_PANEL_DASHBOARD_ENTITY_MAP)
    if not isinstance(rows, list):
        return {}
    output: dict[str, str] = {}
    for item in rows:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "").strip()
        entity_id = str(item.get("entity_id") or "").strip()
        if not role or not entity_id:
            continue
        output[role] = entity_id
    return output


def _state_to_open(value: Any) -> bool | None:
    """Convert common HA/Tesla states to an open/closed boolean."""
    text = str(value if value is not None else "").strip().lower()
    if not text or text in {"unknown", "unavailable", "none", "null"}:
        return None
    if text in {"on", "open", "opened", "true", "yes", "1", "active", "detected"}:
        return True
    if text in {"off", "closed", "close", "false", "no", "0", "inactive", "clear"}:
        return False
    # Numeric sensors sometimes expose 0/1.
    try:
        return float(text.replace(",", ".")) > 0
    except Exception:
        return None


class PomVehicleAggregateOpeningSensor(BinarySensorEntity):
    """Aggregate windows/doors/openings state across Tessie/TeslaMate style sources."""

    _attr_has_entity_name = False
    _attr_device_class = BinarySensorDeviceClass.OPENING

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, kind: str) -> None:
        """Initialize the aggregate sensor."""
        self.hass = hass
        self.entry = entry
        self.kind = kind
        self._last_entities: set[str] = set()

        if kind == "windows":
            self._attr_unique_id = f"{entry.entry_id}_pom_windows_open"
            self._attr_name = "POM Windows Open"
            self._attr_icon = "mdi:car-door"
        elif kind == "doors":
            self._attr_unique_id = f"{entry.entry_id}_pom_doors_open"
            self._attr_name = "POM Doors Open"
            self._attr_icon = "mdi:car-door"
        else:
            self._attr_unique_id = f"{entry.entry_id}_pom_openings_open"
            self._attr_name = "POM Openings Open"
            self._attr_icon = "mdi:car-door-lock-open"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title or DEFAULT_NAME,
            manufacturer="POM",
            model="Tesla Report",
        )

    async def async_added_to_hass(self) -> None:
        """Update the aggregate sensor when any relevant entity changes."""

        @callback
        def _handle_state_changed(event: Event) -> None:
            entity_id = str(event.data.get("entity_id") or "")
            if not entity_id:
                return
            # Recalculate the current source list at event time because panel
            # settings can change without a platform reload.
            if entity_id in self._configured_entities():
                self.async_write_ha_state()

        self.async_on_remove(self.hass.bus.async_listen(EVENT_STATE_CHANGED, _handle_state_changed))

    @property
    def available(self) -> bool:
        """Keep sensor visible even when no source is configured yet."""
        return True

    def _role_map(self) -> dict[str, str]:
        return _dashboard_role_map(_current_entry_data(self.hass, self.entry))

    def _entity_for_role(self, role: str) -> str:
        entity_id = str(self._role_map().get(role) or "").strip()
        # Never use our own aggregate sensors as upstream sources; that would be
        # circular if Auto Find accidentally picked them.
        if entity_id in OWN_AGGREGATE_ENTITY_IDS:
            return ""
        return entity_id

    def _configured_entities(self) -> set[str]:
        entities: set[str] = set()
        for source in self._source_candidates():
            entity_id = str(source.get("entity_id") or "").strip()
            if entity_id:
                entities.add(entity_id)
        return entities

    def _source_candidates(self) -> list[dict[str, str]]:
        """Return configured aggregate/part source candidates."""
        rows: list[dict[str, str]] = []
        if self.kind == "windows":
            aggregate = self._entity_for_role(WINDOWS_AGGREGATE_ROLE)
            if aggregate:
                rows.append({"key": "windows_aggregate", "role": WINDOWS_AGGREGATE_ROLE, "entity_id": aggregate, "mode": "aggregate"})
            for key, role in WINDOW_PART_ROLES.items():
                entity_id = self._entity_for_role(role)
                if entity_id:
                    rows.append({"key": key, "role": role, "entity_id": entity_id, "mode": "parts"})
            return rows

        if self.kind == "doors":
            aggregate = self._entity_for_role(DOORS_AGGREGATE_ROLE)
            if aggregate:
                rows.append({"key": "doors_aggregate", "role": DOORS_AGGREGATE_ROLE, "entity_id": aggregate, "mode": "aggregate"})
            for key, role in DOOR_PART_ROLES.items():
                entity_id = self._entity_for_role(role)
                if entity_id:
                    rows.append({"key": key, "role": role, "entity_id": entity_id, "mode": "parts"})
            return rows

        # Openings: doors + trunk/frunk/charge port. Door aggregate, when set,
        # acts as the door source. Otherwise individual door parts are used.
        aggregate = self._entity_for_role(DOORS_AGGREGATE_ROLE)
        if aggregate:
            rows.append({"key": "doors_aggregate", "role": DOORS_AGGREGATE_ROLE, "entity_id": aggregate, "mode": "aggregate"})
        else:
            for key, role in DOOR_PART_ROLES.items():
                entity_id = self._entity_for_role(role)
                if entity_id:
                    rows.append({"key": key, "role": role, "entity_id": entity_id, "mode": "parts"})
        for key, role in OPENING_EXTRA_ROLES.items():
            entity_id = self._entity_for_role(role)
            if entity_id:
                rows.append({"key": key, "role": role, "entity_id": entity_id, "mode": "parts"})
        return rows

    def _evaluate(self) -> dict[str, Any]:
        """Evaluate configured sources and return state/debug data."""
        sources = self._source_candidates()
        aggregate_sources = [item for item in sources if item.get("mode") == "aggregate"]
        part_sources = [item for item in sources if item.get("mode") != "aggregate"]

        source_mode = "none"
        used_sources: list[dict[str, Any]] = []
        open_items: list[str] = []
        unknown_items: list[str] = []

        # Aggregate has priority for windows/doors. For openings, the door
        # aggregate only represents doors and is combined with trunk/frunk/etc.
        if self.kind in {"windows", "doors"} and aggregate_sources:
            source_mode = "aggregate"
            source = aggregate_sources[0]
            state = self.hass.states.get(source["entity_id"])
            value = _state_to_open(state.state if state is not None else None)
            used_sources.append({**source, "state": state.state if state is not None else "missing", "open": value})
            if value is True:
                open_items.append(source["key"])
            elif value is None:
                unknown_items.append(source["key"])
            return {
                "is_open": value,
                "source_mode": source_mode,
                "used_sources": used_sources,
                "open_items": open_items,
                "unknown_items": unknown_items,
                "configured_entity_count": len(sources),
            }

        source_mode = "parts" if part_sources or aggregate_sources else "none"
        for source in aggregate_sources + part_sources:
            state = self.hass.states.get(source["entity_id"])
            value = _state_to_open(state.state if state is not None else None)
            used_sources.append({**source, "state": state.state if state is not None else "missing", "open": value})
            if value is True:
                open_items.append(source["key"])
            elif value is None:
                unknown_items.append(source["key"])

        if not used_sources:
            is_open: bool | None = None
        elif open_items:
            is_open = True
        elif len(unknown_items) == len(used_sources):
            is_open = None
        else:
            is_open = False

        return {
            "is_open": is_open,
            "source_mode": source_mode,
            "used_sources": used_sources,
            "open_items": open_items,
            "unknown_items": unknown_items,
            "configured_entity_count": len(sources),
        }

    @property
    def is_on(self) -> bool | None:
        """Return true when any configured source is open."""
        return self._evaluate().get("is_open")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return debug attributes explaining why the aggregate is open/closed."""
        result = self._evaluate()
        return {
            "kind": self.kind,
            "source_mode": result.get("source_mode"),
            "open_items": result.get("open_items"),
            "unknown_items": result.get("unknown_items"),
            "configured_entity_count": result.get("configured_entity_count"),
            "sources": result.get("used_sources"),
        }
