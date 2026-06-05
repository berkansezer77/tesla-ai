"""Sensor entities for POM Tesla Report Dashboard."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
import math
import unicodedata
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval

from .const import (
    CONF_ENTITY_LOCATION_SENSOR,
    CONF_ENTITY_PERSON_TESLA,
    CONF_LOCATION_DISPLAY_MODE,
    CONF_LOCATION_UPDATE_INTERVAL_MINUTES,
    CONF_PERSON_TRACK_HOURS_TO_SHOW,
    CONF_PERSON_TRACK_1_ENABLED,
    CONF_PERSON_TRACK_1_ENTITY,
    CONF_PERSON_TRACK_1_NAME,
    CONF_PERSON_TRACK_2_ENABLED,
    CONF_PERSON_TRACK_2_ENTITY,
    CONF_PERSON_TRACK_2_NAME,
    CONF_PERSON_TRACK_3_ENABLED,
    CONF_PERSON_TRACK_3_ENTITY,
    CONF_PERSON_TRACK_3_NAME,
    DEFAULT_LOCATION_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
    LOCATION_LABEL_ENTITY_ID,
    PERSON_TRACK_SENSOR_ENTITY_IDS,
)
from .helpers import merged_options_from_report_config

_LOGGER = logging.getLogger(__name__)


DASHBOARD_SELF_OUTPUT_ENTITY_IDS = {
    LOCATION_LABEL_ENTITY_ID,
    "sensor.pom_tesla_dashboard_last_charge",
    *PERSON_TRACK_SENSOR_ENTITY_IDS.values(),
}


def _is_dashboard_self_output_entity(value: Any) -> bool:
    """Return true for dashboard output sensors that must not be used as sources."""
    entity_id = str(value or "").strip().lower()
    return entity_id in {str(item).lower() for item in DASHBOARD_SELF_OUTPUT_ENTITY_IDS} or entity_id.startswith("sensor.pom_tesla_dashboard_person_track_")


TURKEY_PLATE_CODES: dict[str, str] = {
    "adana": "01", "adiyaman": "02", "afyonkarahisar": "03", "agri": "04", "amasya": "05",
    "ankara": "06", "antalya": "07", "artvin": "08", "aydin": "09", "balikesir": "10",
    "bilecik": "11", "bingol": "12", "bitlis": "13", "bolu": "14", "burdur": "15",
    "bursa": "16", "canakkale": "17", "cankiri": "18", "corum": "19", "denizli": "20",
    "diyarbakir": "21", "edirne": "22", "elazig": "23", "erzincan": "24", "erzurum": "25",
    "eskisehir": "26", "gaziantep": "27", "giresun": "28", "gumushane": "29", "hakkari": "30",
    "hatay": "31", "isparta": "32", "mersin": "33", "icel": "33", "istanbul": "34",
    "izmir": "35", "kars": "36", "kastamonu": "37", "kayseri": "38", "kirklareli": "39",
    "kirsehir": "40", "kocaeli": "41", "izmit": "41", "konya": "42", "kutahya": "43",
    "malatya": "44", "manisa": "45", "kahramanmaras": "46", "maras": "46", "mardin": "47",
    "mugla": "48", "mus": "49", "nevsehir": "50", "nigde": "51", "ordu": "52",
    "rize": "53", "sakarya": "54", "adapazari": "54", "samsun": "55", "siirt": "56",
    "sinop": "57", "sivas": "58", "tekirdag": "59", "tokat": "60", "trabzon": "61",
    "tunceli": "62", "sanliurfa": "63", "urfa": "63", "usak": "64", "van": "65",
    "yozgat": "66", "zonguldak": "67", "aksaray": "68", "bayburt": "69", "karaman": "70",
    "kirikkale": "71", "batman": "72", "sirnak": "73", "bartin": "74", "ardahan": "75",
    "igdir": "76", "yalova": "77", "karabuk": "78", "kilis": "79", "osmaniye": "80",
    "duzce": "81",
}

def _norm_key(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = text.replace("ı", "i").replace("İ", "i")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.split())

def _plate_from_address(address: dict[str, Any]) -> str:
    if not isinstance(address, dict):
        return ""
    for key in ("state_abbr", "ISO3166-2-lvl4", "ISO3166-2-lvl6", "ISO3166-2-lvl5"):
        raw = str(address.get(key) or "").strip()
        if raw:
            if raw.upper().startswith("TR-"):
                code = raw.split("-", 1)[1].strip()
                if code.isdigit():
                    return code.zfill(2)
            if raw.isdigit():
                return raw.zfill(2)
    for key in ("province", "state", "city", "town", "municipality", "county"):
        norm = _norm_key(address.get(key))
        if not norm:
            continue
        if norm in TURKEY_PLATE_CODES:
            return TURKEY_PLATE_CODES[norm]
        # Values can sometimes include suffixes like "İstanbul Ili".
        for name, code in TURKEY_PLATE_CODES.items():
            if norm == name or norm.startswith(name + " ") or (" " + name + " ") in (" " + norm + " "):
                return code
    return ""


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up dashboard sensors."""
    sensor = PomTeslaDashboardLocationLabelSensor(hass, entry)
    person_sensors = [PomTeslaDashboardPersonTrackSensor(hass, entry, slot) for slot in (1, 2, 3)]
    domain_data = hass.data.setdefault(DOMAIN, {})
    domain_data[entry.entry_id + "_location_label_sensor"] = sensor
    for person_sensor in person_sensors:
        domain_data[f"{entry.entry_id}_person_track_{person_sensor.slot}_sensor"] = person_sensor
    async_add_entities([sensor, PomTeslaDashboardLastChargeSensor(hass, entry), *person_sensors])


class PomTeslaDashboardLocationLabelSensor(SensorEntity):
    """Reverse-geocoded short location label for the generated dashboard."""

    _attr_has_entity_name = False
    _attr_name = "POM Tesla Dashboard Location Label"
    _attr_icon = "mdi:map-marker-radius-outline"
    _attr_entity_id = LOCATION_LABEL_ENTITY_ID

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_location_label"
        self._attr_native_value = "-"
        self._attr_extra_state_attributes: dict[str, Any] = {
            "source": "not_initialized",
            "update_interval_minutes": DEFAULT_LOCATION_UPDATE_INTERVAL_MINUTES,
        }
        self._remove_state_listener = None
        self._last_query_monotonic: float | None = None
        self._last_lat_lon: tuple[float, float] | None = None
        self._last_address: dict[str, Any] | None = None
        self._last_display_name: str = ""

    @property
    def _options(self) -> dict[str, Any]:
        """Return current config entry options merged with defaults."""
        return merged_options_from_report_config({**dict(self._entry.data or {}), **dict(self._entry.options or {})})

    async def async_added_to_hass(self) -> None:
        """Register listeners after the entity is added."""
        await super().async_added_to_hass()
        await self._async_reset_source_listener()
        interval_minutes = self._get_interval_minutes()
        self.async_on_remove(
            async_track_time_interval(
                self.hass,
                self._async_scheduled_update,
                timedelta(minutes=interval_minutes),
            )
        )
        self.hass.async_create_task(self.async_refresh_location(force=True, reason="startup"))

    async def async_will_remove_from_hass(self) -> None:
        """Clean up listeners."""
        if self._remove_state_listener is not None:
            self._remove_state_listener()
            self._remove_state_listener = None
        self.hass.data.get(DOMAIN, {}).pop(self._entry.entry_id + "_location_label_sensor", None)
        await super().async_will_remove_from_hass()

    async def async_options_updated(self) -> None:
        """Called by the config entry update listener when options change."""
        await self._async_reset_source_listener()
        await self.async_refresh_location(force=True, reason="options_updated")

    async def _async_reset_source_listener(self) -> None:
        """Listen to the currently selected location source entity."""
        if self._remove_state_listener is not None:
            self._remove_state_listener()
            self._remove_state_listener = None
        source_entity = self._get_source_entity()
        if source_entity:
            self._remove_state_listener = async_track_state_change_event(
                self.hass,
                [source_entity],
                self._handle_source_state_changed,
            )

    @callback
    def _handle_source_state_changed(self, event: Event) -> None:
        """Handle source location state changes."""
        self.hass.async_create_task(self.async_refresh_location(force=False, reason="state_changed"))

    async def _async_scheduled_update(self, now: datetime) -> None:
        """Scheduled reverse-geocode refresh."""
        await self.async_refresh_location(force=True, reason="scheduled")

    def _get_source_entity(self) -> str:
        """Return selected source entity id."""
        entity_id = str(self._options.get(CONF_ENTITY_LOCATION_SENSOR) or "").strip()
        if _is_dashboard_self_output_entity(entity_id):
            _LOGGER.warning(
                "POM Dashboard Location Label ignored self/output source entity: %s",
                entity_id,
            )
            return ""
        return entity_id

    def _get_display_mode(self) -> str:
        """Return selected label display mode."""
        mode = str(self._options.get(CONF_LOCATION_DISPLAY_MODE) or "auto_short").strip()
        return mode or "auto_short"

    def _get_interval_minutes(self) -> int:
        """Return minimum Nominatim update interval."""
        try:
            return max(5, int(self._options.get(CONF_LOCATION_UPDATE_INTERVAL_MINUTES) or DEFAULT_LOCATION_UPDATE_INTERVAL_MINUTES))
        except (TypeError, ValueError):
            return DEFAULT_LOCATION_UPDATE_INTERVAL_MINUTES

    async def async_refresh_location(self, *, force: bool = False, reason: str = "manual") -> None:
        """Refresh the display label from the selected source entity."""
        source_entity = self._get_source_entity()
        if not source_entity:
            self._set_value("-", source="no_source_entity", reason=reason)
            return

        state = self.hass.states.get(source_entity)
        lat_lon = self._extract_lat_lon(state)
        if lat_lon is None:
            self._set_value(
                "-",
                source="waiting_for_latitude_longitude",
                reason=reason,
                source_entity=source_entity,
            )
            return

        lat, lon = lat_lon
        # If the coordinates are effectively unchanged and we already have an address,
        # recompute the selected label locally without calling OpenStreetMap.
        if self._last_address and self._last_lat_lon and self._distance_km(self._last_lat_lon, lat_lon) < 0.25:
            label = self._label_from_address(self._last_address, self._last_display_name)
            self._set_value(
                label,
                source="cached_address",
                reason=reason,
                source_entity=source_entity,
                latitude=lat,
                longitude=lon,
                address=self._last_address,
                display_name=self._last_display_name,
            )
            return

        now_mono = self.hass.loop.time()
        interval_seconds = self._get_interval_minutes() * 60
        if not force and self._last_query_monotonic is not None and now_mono - self._last_query_monotonic < interval_seconds:
            # Keep the current value until the next scheduled refresh. This keeps
            # OpenStreetMap/Nominatim calls to at most once per configured interval.
            attrs = dict(self._attr_extra_state_attributes or {})
            attrs.update({
                "source": "rate_limited_waiting_for_next_5_minute_refresh",
                "reason": reason,
                "source_entity": source_entity,
                "latitude": lat,
                "longitude": lon,
            })
            self._attr_extra_state_attributes = attrs
            self.async_write_ha_state()
            return

        await self._async_reverse_geocode(lat, lon, source_entity=source_entity, reason=reason)

    async def _async_reverse_geocode(self, lat: float, lon: float, *, source_entity: str, reason: str) -> None:
        """Reverse geocode via OpenStreetMap Nominatim."""
        self._last_query_monotonic = self.hass.loop.time()
        session = async_get_clientsession(self.hass)
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "format": "jsonv2",
            "lat": f"{lat:.7f}",
            "lon": f"{lon:.7f}",
            "zoom": "18",
            "addressdetails": "1",
            "accept-language": "tr,en",
        }
        headers = {
            "User-Agent": "POMTeslaDashboardInstaller/0.6 HomeAssistant custom integration",
        }
        try:
            async with session.get(url, params=params, headers=headers, timeout=20) as response:
                if response.status >= 400:
                    text = await response.text()
                    raise RuntimeError(f"Nominatim HTTP {response.status}: {text[:200]}")
                payload = await response.json(content_type=None)
        except Exception as err:  # noqa: BLE001 - readable HA state preferred
            _LOGGER.debug("POM Tesla dashboard reverse geocode failed: %s", err)
            self._set_value(
                self._attr_native_value or "-",
                source="reverse_geocode_failed",
                reason=reason,
                source_entity=source_entity,
                latitude=lat,
                longitude=lon,
                error=str(err),
            )
            return

        address = payload.get("address") if isinstance(payload, dict) else {}
        if not isinstance(address, dict):
            address = {}
        display_name = str(payload.get("display_name") or "") if isinstance(payload, dict) else ""
        self._last_address = address
        self._last_display_name = display_name
        self._last_lat_lon = (lat, lon)
        label = self._label_from_address(address, display_name)
        self._set_value(
            label,
            source="openstreetmap_nominatim",
            reason=reason,
            source_entity=source_entity,
            latitude=lat,
            longitude=lon,
            address=address,
            display_name=display_name,
        )

    @staticmethod
    def _extract_lat_lon(state: Any) -> tuple[float, float] | None:
        """Extract latitude/longitude from common HA entity attributes or state."""
        if state is None:
            return None
        attrs = dict(getattr(state, "attributes", {}) or {})
        lat_candidates = [attrs.get("latitude"), attrs.get("lat")]
        lon_candidates = [attrs.get("longitude"), attrs.get("lon"), attrs.get("lng")]
        location = attrs.get("location") or attrs.get("coordinates")
        if isinstance(location, (list, tuple)) and len(location) >= 2:
            lat_candidates.append(location[0])
            lon_candidates.append(location[1])
        elif isinstance(location, dict):
            lat_candidates.append(location.get("latitude") or location.get("lat"))
            lon_candidates.append(location.get("longitude") or location.get("lon") or location.get("lng"))

        for lat_raw in lat_candidates:
            for lon_raw in lon_candidates:
                try:
                    lat = float(lat_raw)
                    lon = float(lon_raw)
                except (TypeError, ValueError):
                    continue
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return lat, lon

        # Some template sensors store "lat, lon" as the state string.
        raw_state = str(getattr(state, "state", "") or "").strip()
        if "," in raw_state:
            try:
                lat_s, lon_s = raw_state.split(",", 1)
                lat = float(lat_s.strip())
                lon = float(lon_s.strip())
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return lat, lon
            except (TypeError, ValueError):
                return None
        return None

    def _label_from_address(self, address: dict[str, Any], display_name: str) -> str:
        """Return the selected short label from Nominatim address fields."""
        mode = self._get_display_mode()

        def first(*keys: str) -> str:
            for key in keys:
                value = address.get(key)
                if value:
                    return str(value)
            return ""

        if mode == "road":
            label = first("road", "pedestrian", "footway", "path", "residential")
        elif mode == "neighbourhood":
            label = first("neighbourhood", "quarter", "city_district", "suburb")
        elif mode == "suburb":
            label = first("suburb", "quarter", "neighbourhood")
        elif mode == "district":
            label = first("city_district", "district", "county", "municipality")
        elif mode == "city":
            label = first("city", "town", "village", "municipality", "county")
        elif mode == "full_address":
            label = display_name
        else:  # auto_short
            label = first(
                "neighbourhood",
                "quarter",
                "suburb",
                "city_district",
                "town",
                "city",
                "village",
                "road",
                "county",
            )
        return (label or display_name or "-").replace(" Mahallesi", "").strip() or "-"

    def _home_lat_lon(self) -> tuple[float, float] | None:
        """Return zone.home coordinates when available."""
        home = self.hass.states.get("zone.home")
        if home is None:
            return None
        attrs = dict(getattr(home, "attributes", {}) or {})
        try:
            lat = float(attrs.get("latitude"))
            lon = float(attrs.get("longitude"))
        except (TypeError, ValueError):
            return None
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return lat, lon
        return None

    def _set_value(self, value: Any, **attrs: Any) -> None:
        """Write state and attributes."""
        new_state = str(value or "-")[:255]
        previous_state = self._attr_native_value
        merged_attrs = {
            "display_mode": self._get_display_mode(),
            "update_interval_minutes": self._get_interval_minutes(),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
        for key, val in attrs.items():
            if val is not None:
                merged_attrs[key] = val

        address = merged_attrs.get("address")
        if isinstance(address, dict):
            state_abbr = _plate_from_address(address)
            if state_abbr:
                merged_attrs["state_abbr"] = state_abbr

        try:
            lat = float(merged_attrs.get("latitude"))
            lon = float(merged_attrs.get("longitude"))
        except (TypeError, ValueError):
            lat = lon = None
        if lat is not None and lon is not None:
            home_lat_lon = self._home_lat_lon()
            if home_lat_lon is not None:
                merged_attrs["distance_from_home_km"] = round(self._distance_km(home_lat_lon, (lat, lon)), 3)

        previous_attrs = dict(self._attr_extra_state_attributes or {})
        comparable_previous = {k: v for k, v in previous_attrs.items() if k != "last_updated"}
        comparable_new = {k: v for k, v in merged_attrs.items() if k != "last_updated"}
        self._attr_native_value = new_state
        self._attr_extra_state_attributes = merged_attrs
        if previous_state != new_state or comparable_previous != comparable_new:
            self.async_write_ha_state()

    @staticmethod
    def _distance_km(a: tuple[float, float], b: tuple[float, float]) -> float:
        """Approximate haversine distance in kilometers."""
        lat1, lon1 = a
        lat2, lon2 = b
        radius_km = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        rlat1 = math.radians(lat1)
        rlat2 = math.radians(lat2)
        h = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
        return 2 * radius_km * math.asin(min(1, math.sqrt(h)))



class PomTeslaDashboardPersonTrackSensor(SensorEntity):
    """Reverse-geocoded person tracking sensor for dashboard popups."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:account-map-outline"

    SLOT_CONFIG = {
        1: (CONF_PERSON_TRACK_1_ENTITY, CONF_PERSON_TRACK_1_NAME, CONF_PERSON_TRACK_1_ENABLED),
        2: (CONF_PERSON_TRACK_2_ENTITY, CONF_PERSON_TRACK_2_NAME, CONF_PERSON_TRACK_2_ENABLED),
        3: (CONF_PERSON_TRACK_3_ENTITY, CONF_PERSON_TRACK_3_NAME, CONF_PERSON_TRACK_3_ENABLED),
    }

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, slot: int) -> None:
        """Initialize the sensor."""
        self.hass = hass
        self._entry = entry
        self.slot = slot
        self._attr_unique_id = f"{entry.entry_id}_dashboard_person_track_{slot}"
        self._attr_entity_id = PERSON_TRACK_SENSOR_ENTITY_IDS.get(slot, f"sensor.pom_tesla_dashboard_person_track_{slot}")
        self._attr_name = f"POM Tesla Dashboard Person Track {slot}"
        self._attr_native_value = "-"
        self._attr_extra_state_attributes: dict[str, Any] = {"slot": slot, "enabled": False}
        self._remove_state_listener = None
        self._last_query_monotonic: float | None = None
        self._last_lat_lon: tuple[float, float] | None = None
        self._last_address: dict[str, Any] | None = None
        self._last_display_name: str = ""

    @property
    def _options(self) -> dict[str, Any]:
        """Return current config entry options merged with defaults."""
        return merged_options_from_report_config({**dict(self._entry.data or {}), **dict(self._entry.options or {})})

    def _slot_keys(self) -> tuple[str, str, str]:
        """Return option keys for this slot."""
        return self.SLOT_CONFIG[self.slot]

    def _is_enabled(self) -> bool:
        entity_key, _name_key, enabled_key = self._slot_keys()
        entity_id = str(self._options.get(entity_key) or "").strip()
        return bool(self._options.get(enabled_key, False)) and bool(entity_id) and not self._is_invalid_source_entity(entity_id)

    def _person_entity(self) -> str:
        entity_key, _name_key, _enabled_key = self._slot_keys()
        entity_id = str(self._options.get(entity_key) or "").strip()
        if self._is_invalid_source_entity(entity_id):
            _LOGGER.warning(
                "POM Dashboard Person Track %s ignored self/output source entity: %s",
                self.slot,
                entity_id,
            )
            return ""
        return entity_id

    def _configured_person_entity_raw(self) -> str:
        entity_key, _name_key, _enabled_key = self._slot_keys()
        return str(self._options.get(entity_key) or "").strip()

    def _is_invalid_source_entity(self, entity_id: str) -> bool:
        entity_id = str(entity_id or "").strip()
        return bool(entity_id) and _is_dashboard_self_output_entity(entity_id)

    def _person_name(self) -> str:
        _entity_key, name_key, _enabled_key = self._slot_keys()
        configured = str(self._options.get(name_key) or "").strip()
        if configured:
            return configured
        state = self.hass.states.get(self._person_entity())
        if state is not None:
            friendly = str(state.attributes.get("friendly_name") or "").strip()
            if friendly:
                return friendly
        return f"Person {self.slot}"

    def _tesla_entity(self) -> str:
        return str(self._options.get(CONF_ENTITY_LOCATION_SENSOR) or self._options.get(CONF_ENTITY_PERSON_TESLA) or "").strip()

    def _get_interval_minutes(self) -> int:
        try:
            return max(5, int(self._options.get(CONF_LOCATION_UPDATE_INTERVAL_MINUTES) or DEFAULT_LOCATION_UPDATE_INTERVAL_MINUTES))
        except (TypeError, ValueError):
            return DEFAULT_LOCATION_UPDATE_INTERVAL_MINUTES

    async def async_added_to_hass(self) -> None:
        """Register listeners after the entity is added."""
        await super().async_added_to_hass()
        await self._async_reset_source_listener()
        self.async_on_remove(
            async_track_time_interval(
                self.hass,
                self._async_scheduled_update,
                timedelta(minutes=self._get_interval_minutes()),
            )
        )
        self.hass.async_create_task(self.async_refresh_location(force=True, reason="startup"))

    async def async_will_remove_from_hass(self) -> None:
        """Clean up listeners."""
        if self._remove_state_listener is not None:
            self._remove_state_listener()
            self._remove_state_listener = None
        self.hass.data.get(DOMAIN, {}).pop(f"{self._entry.entry_id}_person_track_{self.slot}_sensor", None)
        await super().async_will_remove_from_hass()

    async def async_options_updated(self) -> None:
        """Called when config entry options change."""
        await self._async_reset_source_listener()
        await self.async_refresh_location(force=True, reason="options_updated")

    async def _async_reset_source_listener(self) -> None:
        """Listen to the selected person and Tesla location entities."""
        if self._remove_state_listener is not None:
            self._remove_state_listener()
            self._remove_state_listener = None
        entities = [
            eid
            for eid in [self._person_entity(), self._tesla_entity()]
            if eid and not _is_dashboard_self_output_entity(eid)
        ]
        if entities:
            self._remove_state_listener = async_track_state_change_event(
                self.hass,
                list(dict.fromkeys(entities)),
                self._handle_source_state_changed,
            )

    @callback
    def _handle_source_state_changed(self, event: Event) -> None:
        """Refresh when tracked coordinates change."""
        entity_id = str(event.data.get("entity_id") or "").strip()
        if _is_dashboard_self_output_entity(entity_id):
            _LOGGER.warning(
                "POM Dashboard Person Track %s ignored event from dashboard output entity: %s",
                self.slot,
                entity_id,
            )
            return
        self.hass.async_create_task(self.async_refresh_location(force=False, reason="state_changed"))

    async def _async_scheduled_update(self, now: datetime) -> None:
        """Scheduled reverse geocode refresh."""
        await self.async_refresh_location(force=True, reason="scheduled")

    async def async_refresh_location(self, *, force: bool = False, reason: str = "manual") -> None:
        """Refresh person address and distance attributes."""
        raw_person_entity = self._configured_person_entity_raw()
        person_entity = self._person_entity()
        person_name = self._person_name()
        if self._is_invalid_source_entity(raw_person_entity):
            self._set_value(
                "-",
                enabled=False,
                source="invalid_self_reference_blocked",
                person_entity=raw_person_entity,
                person_name=person_name,
                reason=reason,
                error="Dashboard output sensors cannot be used as person-track source entities.",
            )
            return
        enabled = self._is_enabled()
        if not enabled:
            self._set_value("-", enabled=False, person_entity=person_entity, person_name=person_name, reason=reason)
            return

        person_state = self.hass.states.get(person_entity)
        lat_lon = PomTeslaDashboardLocationLabelSensor._extract_lat_lon(person_state)
        if lat_lon is None:
            self._set_value(
                "-",
                enabled=True,
                source="waiting_for_latitude_longitude",
                person_entity=person_entity,
                person_name=person_name,
                reason=reason,
            )
            return

        lat, lon = lat_lon
        if self._last_address and self._last_lat_lon and PomTeslaDashboardLocationLabelSensor._distance_km(self._last_lat_lon, lat_lon) < 0.25:
            self._set_value_from_address(
                self._last_address,
                self._last_display_name,
                lat=lat,
                lon=lon,
                source="cached_address",
                reason=reason,
            )
            return

        now_mono = self.hass.loop.time()
        interval_seconds = self._get_interval_minutes() * 60
        if not force and self._last_query_monotonic is not None and now_mono - self._last_query_monotonic < interval_seconds:
            attrs = dict(self._attr_extra_state_attributes or {})
            attrs.update({
                "source": "rate_limited_waiting_for_next_refresh",
                "reason": reason,
                "latitude": lat,
                "longitude": lon,
                "google_maps_url": self._google_maps_url(lat, lon),
            })
            self._attr_extra_state_attributes = attrs
            self.async_write_ha_state()
            return

        await self._async_reverse_geocode(lat, lon, reason=reason)

    async def _async_reverse_geocode(self, lat: float, lon: float, *, reason: str) -> None:
        """Reverse geocode via OpenStreetMap Nominatim."""
        self._last_query_monotonic = self.hass.loop.time()
        session = async_get_clientsession(self.hass)
        params = {
            "format": "jsonv2",
            "lat": f"{lat:.7f}",
            "lon": f"{lon:.7f}",
            "zoom": "18",
            "addressdetails": "1",
            "accept-language": "tr,en",
        }
        headers = {"User-Agent": "POMTeslaDashboardPersonTrack/1.0 HomeAssistant custom integration"}
        try:
            async with session.get("https://nominatim.openstreetmap.org/reverse", params=params, headers=headers, timeout=20) as response:
                if response.status >= 400:
                    text = await response.text()
                    raise RuntimeError(f"Nominatim HTTP {response.status}: {text[:200]}")
                payload = await response.json(content_type=None)
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("POM Tesla dashboard person reverse geocode failed: %s", err)
            self._set_value(
                self._attr_native_value or "-",
                enabled=True,
                source="reverse_geocode_failed",
                reason=reason,
                person_entity=self._person_entity(),
                person_name=self._person_name(),
                latitude=lat,
                longitude=lon,
                google_maps_url=self._google_maps_url(lat, lon),
                error=str(err),
            )
            return

        address = payload.get("address") if isinstance(payload, dict) else {}
        if not isinstance(address, dict):
            address = {}
        display_name = str(payload.get("display_name") or "") if isinstance(payload, dict) else ""
        self._last_address = address
        self._last_display_name = display_name
        self._last_lat_lon = (lat, lon)
        self._set_value_from_address(address, display_name, lat=lat, lon=lon, source="openstreetmap_nominatim", reason=reason)

    def _set_value_from_address(self, address: dict[str, Any], display_name: str, *, lat: float, lon: float, source: str, reason: str) -> None:
        """Set sensor value/attributes from an address dict."""
        def first(*keys: str) -> str:
            for key in keys:
                value = address.get(key)
                if value:
                    return str(value)
            return ""

        short = first("neighbourhood", "quarter", "suburb", "city_district", "road", "town", "city") or display_name or "-"
        self._set_value(
            short.replace(" Mahallesi", "").strip() or "-",
            enabled=True,
            source=source,
            reason=reason,
            person_entity=self._person_entity(),
            person_name=self._person_name(),
            latitude=lat,
            longitude=lon,
            address=address,
            display_name=display_name,
            full_address=display_name or short,
            short_address=short,
            neighbourhood=first("neighbourhood", "quarter", "suburb", "city_district"),
            road=first("road", "pedestrian", "footway", "path", "residential"),
            city=first("city", "town", "municipality", "county"),
            google_maps_url=self._google_maps_url(lat, lon),
        )

    def _set_value(self, value: Any, **attrs: Any) -> None:
        """Write state and attributes."""
        lat = attrs.get("latitude")
        lon = attrs.get("longitude")
        try:
            lat_f = float(lat)
            lon_f = float(lon)
        except (TypeError, ValueError):
            lat_f = lon_f = None

        if lat_f is not None and lon_f is not None:
            tesla_lat_lon = self._tesla_lat_lon()
            distance_to_tesla: float | None = None
            if tesla_lat_lon is not None:
                distance_to_tesla = PomTeslaDashboardLocationLabelSensor._distance_km(tesla_lat_lon, (lat_f, lon_f))
                attrs["distance_to_tesla_km"] = round(distance_to_tesla, 3)
            home_lat_lon = self._home_lat_lon()
            if home_lat_lon is not None:
                distance_to_home = PomTeslaDashboardLocationLabelSensor._distance_km(home_lat_lon, (lat_f, lon_f))
                # Defensive fix: if zone.home is clearly stale/wrong but the tracked person
                # is at/near the Tesla, use Tesla as the effective home reference. Some
                # migrated Home Assistant installs have a bogus zone.home coordinate, which
                # showed values like 2223 km even while the car was at home.
                if distance_to_tesla is not None and distance_to_tesla < 1.0 and distance_to_home > 50.0:
                    distance_to_home = distance_to_tesla
                    attrs["distance_to_home_source"] = "tesla_location_fallback_home_distance_suspicious"
                else:
                    attrs["distance_to_home_source"] = "zone_home"
                attrs["distance_to_home_km"] = round(distance_to_home, 3)
            attrs["google_maps_url"] = attrs.get("google_maps_url") or self._google_maps_url(lat_f, lon_f)

        address = attrs.get("address")
        if isinstance(address, dict):
            state_abbr = _plate_from_address(address)
            if state_abbr:
                attrs["state_abbr"] = state_abbr

        attrs.update({
            "slot": self.slot,
            "person_name": attrs.get("person_name") or self._person_name(),
            "person_entity": attrs.get("person_entity") or self._person_entity(),
            "tesla_entity": self._tesla_entity(),
            "map_hours_to_show": self._map_hours_to_show(),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        })
        new_state = str(value or "-")[:255]
        new_attrs = {k: v for k, v in attrs.items() if v is not None}
        previous_state = self._attr_native_value
        previous_attrs = dict(self._attr_extra_state_attributes or {})
        comparable_previous = {k: v for k, v in previous_attrs.items() if k != "last_updated"}
        comparable_new = {k: v for k, v in new_attrs.items() if k != "last_updated"}
        self._attr_native_value = new_state
        self._attr_extra_state_attributes = new_attrs
        if previous_state != new_state or comparable_previous != comparable_new:
            self.async_write_ha_state()

    def _tesla_lat_lon(self) -> tuple[float, float] | None:
        tesla_entity = self._tesla_entity()
        if not tesla_entity:
            return None
        return PomTeslaDashboardLocationLabelSensor._extract_lat_lon(self.hass.states.get(tesla_entity))

    def _home_lat_lon(self) -> tuple[float, float] | None:
        """Return home coordinates for person distance calculations.

        Prefer the Tesla/person location when the configured Tesla location
        entity is currently in the Home zone. This avoids stale or migrated
        zone.home coordinates making a person who is next to the car look
        thousands of kilometers away from home. Otherwise fall back to the
        real zone.home coordinates.
        """
        tesla_entity = self._tesla_entity()
        tesla_state = self.hass.states.get(tesla_entity) if tesla_entity else None
        tesla_lat_lon = PomTeslaDashboardLocationLabelSensor._extract_lat_lon(tesla_state)
        if tesla_state is not None and str(getattr(tesla_state, "state", "") or "").strip().lower() == "home" and tesla_lat_lon is not None:
            return tesla_lat_lon

        home = self.hass.states.get("zone.home")
        home_lat_lon = PomTeslaDashboardLocationLabelSensor._extract_lat_lon(home)
        if home_lat_lon is not None:
            return home_lat_lon

        return tesla_lat_lon if tesla_lat_lon is not None else None

    def _map_hours_to_show(self) -> int:
        try:
            return max(0, min(24, int(float(self._options.get(CONF_PERSON_TRACK_HOURS_TO_SHOW) or 15))))
        except (TypeError, ValueError):
            return 15

    @staticmethod
    def _google_maps_url(lat: float, lon: float) -> str:
        return f"https://www.google.com/maps/search/?api=1&query={lat:.7f},{lon:.7f}"


class PomTeslaDashboardLastChargeSensor(SensorEntity):
    """Expose the latest charging session snapshot to the dashboard popup."""

    _attr_has_entity_name = False
    _attr_name = "POM Tesla Dashboard Last Charge"
    _attr_icon = "mdi:ev-station"
    _attr_entity_id = "sensor.pom_tesla_dashboard_last_charge"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_dashboard_last_charge"

    async def async_added_to_hass(self) -> None:
        """Refresh periodically because the source is integration runtime data."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_track_time_interval(
                self.hass,
                self._async_periodic_refresh,
                timedelta(seconds=10),
            )
        )

    async def _async_periodic_refresh(self, now: datetime) -> None:
        """Write current runtime snapshot to Home Assistant state."""
        self.async_write_ha_state()

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        """Convert to float safely."""
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _state_bucket(self) -> dict[str, Any]:
        """Return mutable charging state created by the report engine."""
        bucket = self.hass.data.setdefault(DOMAIN, {}).setdefault("charging_report_state", {})
        return bucket if isinstance(bucket, dict) else {}

    def _samples(self, state: dict[str, Any]) -> list[dict[str, float]]:
        """Return normalized power samples for the frontend curve."""
        raw = state.get("samples")
        if not isinstance(raw, list):
            return []
        samples: list[dict[str, float]] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            minute = self._safe_float(item.get("minute"), -1.0)
            power = self._safe_float(item.get("power_kw", item.get("power")), 0.0)
            if minute < 0:
                continue
            samples.append({"minute": round(minute, 2), "power_kw": round(max(power, 0.0), 2)})
        return samples

    def _snapshot(self) -> dict[str, Any]:
        """Build attributes consumed by the dashboard charging popup."""
        state = self._state_bucket()
        samples = self._samples(state)
        added_kwh = self._safe_float(state.get("last_added_kwh"), 0.0)
        duration_minutes = self._safe_float(state.get("duration_minutes"), 0.0)
        if duration_minutes <= 0 and samples:
            duration_minutes = max((sample.get("minute", 0.0) for sample in samples), default=0.0)
        peak_power = self._safe_float(state.get("peak_power_kw"), 0.0)
        if peak_power <= 0 and samples:
            peak_power = max((sample.get("power_kw", 0.0) for sample in samples), default=0.0)

        attrs: dict[str, Any] = {
            "active": bool(state.get("active", False)),
            "started_at": state.get("started_at"),
            "finished_at": state.get("finished_at"),
            "added_kwh": round(added_kwh, 3),
            "battery_range_km": round(self._safe_float(state.get("last_battery_range_km"), 0.0), 1),
            "battery_range_estimate_km": round(self._safe_float(state.get("last_battery_range_estimate_km"), 0.0), 1),
            "duration_minutes": round(duration_minutes, 2),
            "peak_power_kw": round(peak_power, 2),
            "power_samples": samples,
            "sample_count": len(samples),
            "last_report_path": state.get("last_report_path"),
            "last_report_sent_ts": state.get("last_report_sent_ts"),
            "last_report_prompt_ts": state.get("last_report_prompt_ts"),
        }
        return attrs

    @property
    def native_value(self) -> str:
        """Return summary state."""
        attrs = self._snapshot()
        if attrs.get("active"):
            return "active"
        if self._safe_float(attrs.get("added_kwh"), 0.0) > 0 or int(attrs.get("sample_count") or 0) > 0:
            return "last_charge"
        return "idle"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return latest charge attributes."""
        return self._snapshot()
