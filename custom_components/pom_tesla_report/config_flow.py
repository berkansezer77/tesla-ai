"""Config flow for POM Tesla Report."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers import entity_registry as er


from .const import (
    DOMAIN,
    DEFAULT_NAME,
    CONF_NAME,
    CONF_SHIFT_STATE_ENTITY,
    CONF_SPEED_ENTITY,
    CONF_ODOMETER_ENTITY,
    CONF_BATTERY_LEVEL_ENTITY,
    CONF_ENERGY_REMAINING_ENTITY,
    CONF_ELEVATION_ENTITY,
    CONF_CLIMATE_ENTITY,
    CONF_CHARGING_ENTITY,
    CONF_CHARGE_ENERGY_ADDED_ENTITY,
    CONF_SUPERCHARGER_PRICE,
    CONF_ZES_PRICE,
    CONF_ASTOR_PRICE,
    CONF_CHARGING_REPORT_MODE,
    CHARGING_REPORT_MODE_DIRECT,
    CHARGING_REPORT_MODE_PROMPT,
    DEFAULT_CHARGING_REPORT_MODE,
    CONF_TELEGRAM_TARGET,
    CONF_AUTO_TRIP_TRACKING,
    CONF_AUTO_START_SPEED_THRESHOLD,
    DEFAULT_SUPERCHARGER_PRICE,
    DEFAULT_ZES_PRICE,
    DEFAULT_ASTOR_PRICE,
    DEFAULT_AUTO_TRIP_TRACKING,
    DEFAULT_AUTO_START_SPEED_THRESHOLD,
    CONF_LIVE_TRIP_ENABLED,
    CONF_LIVE_TRIP_UPDATE_INTERVAL_SECONDS,
    CONF_LIVE_TRIP_TRAFFIC_SPEED_THRESHOLD,
    CONF_LIVE_TRIP_FINISH_DELAY_SECONDS,
    CONF_LIVE_TRIP_MIN_DISTANCE_KM,
    DEFAULT_LIVE_TRIP_ENABLED,
    DEFAULT_LIVE_TRIP_UPDATE_INTERVAL_SECONDS,
    DEFAULT_LIVE_TRIP_TRAFFIC_SPEED_THRESHOLD,
    DEFAULT_LIVE_TRIP_FINISH_DELAY_SECONDS,
    DEFAULT_LIVE_TRIP_MIN_DISTANCE_KM,
    CONF_SHOW_DISTANCE,
    CONF_SHOW_DURATION,
    CONF_SHOW_TRAFFIC,
    CONF_SHOW_AVERAGE_SPEED,
    CONF_SHOW_ENERGY,
    CONF_SHOW_CONSUMPTION,
    CONF_SHOW_BATTERY,
    CONF_SHOW_COST,
    CONF_SHOW_CLIMATE,
    CONF_SHOW_ELEVATION,
    DEFAULT_SHOW_DISTANCE,
    DEFAULT_SHOW_DURATION,
    DEFAULT_SHOW_TRAFFIC,
    DEFAULT_SHOW_AVERAGE_SPEED,
    DEFAULT_SHOW_ENERGY,
    DEFAULT_SHOW_CONSUMPTION,
    DEFAULT_SHOW_BATTERY,
    DEFAULT_SHOW_COST,
    DEFAULT_SHOW_CLIMATE,
    DEFAULT_SHOW_ELEVATION,
    CONF_AI_ENABLED,
    CONF_OPENAI_API_KEY,
    CONF_OPENAI_MODEL,
    CONF_AI_TELEGRAM_TARGET,
    CONF_AI_SYSTEM_PROMPT,
    CONF_AI_MAX_OUTPUT_TOKENS,
    CONF_AI_TELEGRAM_LISTENER_ENABLED,
    CONF_AI_TELEGRAM_LISTENER_CHAT_ID,
    CONF_AI_TELEGRAM_ALLOWED_USER_ID,
    CONF_AI_TELEGRAM_INCLUDE_CONTEXT,
    CONF_AI_CONFIRM_OPTIONAL_CONTROLS,
    DEFAULT_AI_ENABLED,
    DEFAULT_OPENAI_MODEL,
    DEFAULT_AI_SYSTEM_PROMPT,
    DEFAULT_AI_MAX_OUTPUT_TOKENS,
    DEFAULT_AI_TELEGRAM_LISTENER_ENABLED,
    DEFAULT_AI_TELEGRAM_ALLOWED_USER_ID,
    DEFAULT_AI_TELEGRAM_INCLUDE_CONTEXT,
    DEFAULT_AI_CONFIRM_OPTIONAL_CONTROLS,
    CONF_TRIP_MAP_ENABLED,
    CONF_TRIP_MAP_TRACKER_ENTITY,
    CONF_TRIP_MAP_SAMPLE_INTERVAL_SECONDS,
    CONF_TRIP_MAP_MIN_MOVEMENT_METERS,
    CONF_TRIP_MAP_SEND_SEPARATE_PNG,
    DEFAULT_TRIP_MAP_ENABLED,
    DEFAULT_TRIP_MAP_TRACKER_ENTITY,
    DEFAULT_TRIP_MAP_SAMPLE_INTERVAL_SECONDS,
    DEFAULT_TRIP_MAP_MIN_MOVEMENT_METERS,
    DEFAULT_TRIP_MAP_SEND_SEPARATE_PNG,
    CONF_AI_PERSONALITY,
    CONF_AI_ANSWER_LENGTH,
    CONF_AI_CONTEXT_MODE,
    CONF_AI_MAIN_TESLA_ENTITY,
    CONF_AI_AUTO_DISCOVER_DEVICE_ENTITIES,
    CONF_AI_INCLUDE_UNAVAILABLE,
    CONF_AI_MAX_CONTEXT_ENTITIES,
    CONF_AI_EXTRA_CONTEXT_ENTITIES,
    CONF_AI_EXCLUDED_CONTEXT_ENTITIES,
    CONF_REVERSE_GEOCODING_ENABLED,
    CONF_REVERSE_GEOCODING_CACHE_MINUTES,
    CONF_REVERSE_GEOCODING_USE_IN_AI,
    DEFAULT_REVERSE_GEOCODING_ENABLED,
    DEFAULT_REVERSE_GEOCODING_CACHE_MINUTES,
    DEFAULT_REVERSE_GEOCODING_USE_IN_AI,
    AI_PERSONALITY_PROFESSIONAL,
    AI_PERSONALITY_FRIENDLY,
    AI_PERSONALITY_FUNNY,
    AI_PERSONALITY_SHORT_DIRECT,
    AI_PERSONALITY_PREMIUM,
    AI_PERSONALITY_TURKISH_BUDDY,
    AI_ANSWER_LENGTH_SHORT,
    AI_ANSWER_LENGTH_NORMAL,
    AI_ANSWER_LENGTH_DETAILED,
    AI_CONTEXT_MODE_BASIC,
    AI_CONTEXT_MODE_SMART_AUTO,
    AI_CONTEXT_MODE_SELECTED_DEVICE,
    AI_CONTEXT_MODE_SMART_MANUAL,
    AI_CONTEXT_MODE_MANUAL_ONLY,
    DEFAULT_AI_PERSONALITY,
    DEFAULT_AI_ANSWER_LENGTH,
    DEFAULT_AI_CONTEXT_MODE,
    DEFAULT_AI_MAIN_TESLA_ENTITY,
    DEFAULT_AI_AUTO_DISCOVER_DEVICE_ENTITIES,
    DEFAULT_AI_INCLUDE_UNAVAILABLE,
    DEFAULT_AI_MAX_CONTEXT_ENTITIES,
    DEFAULT_AI_EXTRA_CONTEXT_ENTITIES,
    DEFAULT_AI_EXCLUDED_CONTEXT_ENTITIES,
    CONF_AI_ALERTS_ENABLED,
    CONF_AI_ALERT_STYLE,
    CONF_AI_ALERT_COOLDOWN_MINUTES,
    CONF_AI_ALERT_LOW_BATTERY_ENABLED,
    CONF_AI_ALERT_LOW_BATTERY_THRESHOLD,
    CONF_AI_ALERT_POST_TRIP_SUMMARY_ENABLED,
    CONF_AI_ALERT_CHARGE_FINISHED_ENABLED,
    CONF_AI_ALERT_CHARGING_STOPPED_ENABLED,
    CONF_AI_ALERT_TIRE_PRESSURE_ENABLED,
    CONF_AI_ALERT_TIRE_PRESSURE_THRESHOLD_BAR,
    CONF_AI_ALERT_HIGH_BATTERY_TEMP_ENABLED,
    CONF_AI_ALERT_HIGH_BATTERY_TEMP_THRESHOLD_C,
    CONF_AI_ALERT_CLIMATE_LEFT_ON_ENABLED,
    CONF_AI_ALERT_CLIMATE_LEFT_ON_DELAY_MINUTES,
    CONF_AI_ALERT_UNLOCKED_ENABLED,
    CONF_AI_ALERT_UNLOCKED_DELAY_MINUTES,
    CONF_AI_ALERT_DOOR_WINDOW_OPEN_ENABLED,
    CONF_AI_ALERT_DOOR_WINDOW_OPEN_DELAY_MINUTES,
    CONF_AI_ALERT_WINDOW_OPEN_INSTANT_ENABLED,
    AI_ALERT_STYLE_RULE,
    AI_ALERT_STYLE_AI,
    DEFAULT_AI_ALERTS_ENABLED,
    DEFAULT_AI_ALERT_STYLE,
    DEFAULT_AI_ALERT_COOLDOWN_MINUTES,
    DEFAULT_AI_ALERT_LOW_BATTERY_ENABLED,
    DEFAULT_AI_ALERT_LOW_BATTERY_THRESHOLD,
    DEFAULT_AI_ALERT_POST_TRIP_SUMMARY_ENABLED,
    DEFAULT_AI_ALERT_CHARGE_FINISHED_ENABLED,
    DEFAULT_AI_ALERT_CHARGING_STOPPED_ENABLED,
    DEFAULT_AI_ALERT_TIRE_PRESSURE_ENABLED,
    DEFAULT_AI_ALERT_TIRE_PRESSURE_THRESHOLD_BAR,
    DEFAULT_AI_ALERT_HIGH_BATTERY_TEMP_ENABLED,
    DEFAULT_AI_ALERT_HIGH_BATTERY_TEMP_THRESHOLD_C,
    DEFAULT_AI_ALERT_CLIMATE_LEFT_ON_ENABLED,
    DEFAULT_AI_ALERT_CLIMATE_LEFT_ON_DELAY_MINUTES,
    DEFAULT_AI_ALERT_UNLOCKED_ENABLED,
    DEFAULT_AI_ALERT_UNLOCKED_DELAY_MINUTES,
    DEFAULT_AI_ALERT_DOOR_WINDOW_OPEN_ENABLED,
    DEFAULT_AI_ALERT_DOOR_WINDOW_OPEN_DELAY_MINUTES,
    DEFAULT_AI_ALERT_WINDOW_OPEN_INSTANT_ENABLED,
    CONF_VEHICLE_ENTITY_MAP,
    DEFAULT_VEHICLE_ENTITY_MAP,
    VEHICLE_ENTITY_ROLES,
    VEHICLE_ROLE_BATTERY_LEVEL,
    VEHICLE_ROLE_BATTERY_RANGE,
    VEHICLE_ROLE_ENERGY_REMAINING,
    VEHICLE_ROLE_CHARGING_STATE,
    VEHICLE_ROLE_CHARGE_ENERGY_ADDED,
    VEHICLE_ROLE_CHARGER_POWER,
    VEHICLE_ROLE_SPEED,
    VEHICLE_ROLE_SHIFT_STATE,
    VEHICLE_ROLE_ODOMETER,
    VEHICLE_ROLE_ELEVATION,
    VEHICLE_ROLE_CLIMATE,
    VEHICLE_ROLE_INSIDE_TEMPERATURE,
    VEHICLE_ROLE_OUTSIDE_TEMPERATURE,
    VEHICLE_ROLE_BATTERY_TEMPERATURE,
    VEHICLE_ROLE_TIRE_PRESSURE_FRONT_LEFT,
    VEHICLE_ROLE_TIRE_PRESSURE_FRONT_RIGHT,
    VEHICLE_ROLE_TIRE_PRESSURE_REAR_LEFT,
    VEHICLE_ROLE_TIRE_PRESSURE_REAR_RIGHT,
    VEHICLE_ROLE_DOOR_WINDOW,
    VEHICLE_ROLE_LOCK_STATE,
    VEHICLE_ROLE_LOCATION_TRACKER,
    VEHICLE_ROLE_VEHICLE_STATE,
    VEHICLE_ROLE_USER_PRESENT,
    VEHICLE_ROLE_OTHER,
)


DEFAULT_SHIFT_STATE_ENTITY = ""
DEFAULT_SPEED_ENTITY = ""
DEFAULT_ODOMETER_ENTITY = ""
DEFAULT_BATTERY_LEVEL_ENTITY = ""
DEFAULT_ENERGY_REMAINING_ENTITY = ""
DEFAULT_ELEVATION_ENTITY = ""
DEFAULT_CLIMATE_ENTITY = ""

DEFAULT_CHARGING_ENTITY = ""
DEFAULT_CHARGE_ENERGY_ADDED_ENTITY = ""

DEFAULT_TELEGRAM_TARGET = ""
DEFAULT_TRIP_MAP_TRACKER = DEFAULT_TRIP_MAP_TRACKER_ENTITY


# UI-only keys. These are deliberately human-readable so the Options screen
# looks cleaner without adding translation files.
UI_SETTINGS_SECTION = "Settings section"
UI_AFTER_SAVING = "After saving"
UI_VEHICLE_MANAGER_ACTION = "Vehicle manager action"

SECTION_CORE_VEHICLE = "core_vehicle"
SECTION_VEHICLE_ENTITY_MANAGER = "vehicle_entity_manager"
SECTION_AUTOMATION_TELEGRAM = "automation_telegram"
SECTION_PRICES_REPORT = "prices_report"
SECTION_LIVE_TRIP = "live_trip_calculation"
SECTION_AI_BASIC = "ai_basic"
SECTION_AI_ALERTS = "ai_alerts"
SECTION_FINISH = "finish"

ENTITY_MANAGER_ACTION = "Entity manager action"
ENTITY_MANAGER_SMART_IMPORT = "smart_import"
ENTITY_MANAGER_ADD_UPDATE = "add_update"
ENTITY_MANAGER_REMOVE = "remove"
ENTITY_MANAGER_SHOW = "show"
ENTITY_MANAGER_RETURN = "return"

UI_VEHICLE_ENTITY = "Vehicle entity"
UI_VEHICLE_ROLE = "Vehicle data role"
UI_VEHICLE_LABEL = "Description / label"
UI_VEHICLE_USE_REPORT = "Use in report"
UI_VEHICLE_USE_AI = "Use in AI"
UI_VEHICLE_USE_ALERTS = "Use in alerts"
UI_VEHICLE_USE_MAP = "Use in map"
UI_REMOVE_VEHICLE_ENTITY = "Entity to remove"
UI_VEHICLE_ENTITY_SUMMARY = "Current vehicle entity map"
UI_VEHICLE_AUTO_SELECT = "Auto select entities from selected Tesla device"
UI_VEHICLE_AUTO_DISCOVERED_SUMMARY = "Auto discovered entities preview"
UI_REPORT_BATTERY_LEVEL_ENTITY = "Vehicle report · Battery level"
UI_REPORT_ENERGY_REMAINING_ENTITY = "Vehicle report · Energy remaining"
UI_REPORT_SPEED_ENTITY = "Vehicle report · Speed"
UI_REPORT_SHIFT_STATE_ENTITY = "Vehicle report · Shift state"
UI_REPORT_ODOMETER_ENTITY = "Vehicle report · Odometer"
UI_REPORT_ELEVATION_ENTITY = "Vehicle report · Elevation"
UI_REPORT_CLIMATE_ENTITY = "Vehicle report · Climate"
UI_REPORT_CHARGING_ENTITY = "Vehicle report · Charging state"
UI_REPORT_CHARGE_ENERGY_ADDED_ENTITY = "Vehicle report · Charge energy added"
UI_REPORT_LOCATION_TRACKER_ENTITY = "Vehicle report · Location tracker / map"
UI_REPORT_VEHICLE_STATE_ENTITY = "Vehicle report · Vehicle state / sleep status"
UI_VEHICLE_AI_ENTITIES = "AI entities / extra vehicle data"
UI_VEHICLE_EXCLUDED_ENTITIES = "Exclude entities from AI / auto discovery"
UI_VEHICLE_REPORT_SECTION_NOTE = "Vehicle report section"
UI_VEHICLE_AI_SECTION_NOTE = "AI / Auto discovery section"

ACTION_RETURN_TO_MENU = "return_to_menu"
ACTION_SAVE_AND_CLOSE = "save_and_close"
ACTION_VEHICLE_AUTO_SELECT_AI = "vehicle_auto_select_ai"
ACTION_VEHICLE_SAVE_REVIEW = "vehicle_save_review"
ACTION_VEHICLE_ADD_UPDATE = "vehicle_add_update"
ACTION_VEHICLE_REMOVE = "vehicle_remove"
ACTION_VEHICLE_SHOW_MAP = "vehicle_show_map"

UI_NAME = "Integration name"

UI_SHIFT_STATE_ENTITY = "Shift state sensor"
UI_SPEED_ENTITY = "Speed sensor"
UI_ODOMETER_ENTITY = "Odometer sensor"
UI_BATTERY_LEVEL_ENTITY = "Battery level sensor"
UI_ENERGY_REMAINING_ENTITY = "Energy remaining sensor"
UI_ELEVATION_ENTITY = "Elevation sensor"
UI_CLIMATE_ENTITY = "Climate entity"
UI_CHARGING_ENTITY = "Charging state sensor"
UI_CHARGE_ENERGY_ADDED_ENTITY = "Charge energy added sensor"

UI_AUTO_TRIP_TRACKING = "Enable automatic trip tracking"
UI_AUTO_START_SPEED_THRESHOLD = "Start speed threshold"
UI_TELEGRAM_TARGET = "Telegram target"
UI_TRIP_MAP_ENABLED = "Enable trip map collection"
UI_TRIP_MAP_TRACKER_ENTITY = "Trip map tracker entity"
UI_TRIP_MAP_SAMPLE_INTERVAL_SECONDS = "Map sample interval seconds"
UI_TRIP_MAP_MIN_MOVEMENT_METERS = "Minimum movement meters"
UI_TRIP_MAP_SEND_SEPARATE_PNG = "Send separate trip map PNG"

UI_SUPERCHARGER_PRICE = "Supercharger price"
UI_ZES_PRICE = "ZES price"
UI_ASTOR_PRICE = "Astor price"
UI_CHARGING_REPORT_MODE = "Charging report send mode"

UI_SHOW_DISTANCE = "Show distance"
UI_SHOW_DURATION = "Show duration"
UI_SHOW_TRAFFIC = "Show traffic duration"
UI_SHOW_AVERAGE_SPEED = "Show average speed"
UI_SHOW_ENERGY = "Show energy"
UI_SHOW_CONSUMPTION = "Show consumption"
UI_SHOW_BATTERY = "Show battery section"
UI_SHOW_COST = "Show cost section"
UI_SHOW_CLIMATE = "Show climate info"
UI_SHOW_ELEVATION = "Show elevation info"

UI_LIVE_TRIP_ENTITY_SUMMARY = "Live trip calculation entities"
UI_LIVE_TRIP_ENABLED = "Enable live trip calculation engine"
UI_LIVE_TRIP_UPDATE_INTERVAL_SECONDS = "Live trip update interval seconds"
UI_LIVE_TRIP_TRAFFIC_SPEED_THRESHOLD = "Traffic speed threshold"
UI_LIVE_TRIP_FINISH_DELAY_SECONDS = "Finish delay after driving stops"
UI_LIVE_TRIP_MIN_DISTANCE_KM = "Minimum trip distance"


UI_AI_ENABLED = "Enable POM AI Basic"
UI_AI_PERSONALITY = "AI personality"
UI_AI_ANSWER_LENGTH = "AI answer length"
UI_AI_CONTEXT_MODE = "AI context mode"
UI_AI_MAIN_TESLA_ENTITY = "Main Tesla entity for smart discovery"
UI_AI_AUTO_DISCOVER_DEVICE_ENTITIES = "Auto discover entities from same Tesla device"
UI_AI_INCLUDE_UNAVAILABLE = "Include unavailable/unknown entities"
UI_AI_MAX_CONTEXT_ENTITIES = "Max context entities"
UI_AI_EXTRA_CONTEXT_ENTITIES = "Extra AI context entities (manual priority)"
UI_AI_EXCLUDED_CONTEXT_ENTITIES = "Excluded AI context entities"
UI_REVERSE_GEOCODING_ENABLED = "Enable reverse geocoding / address lookup"
UI_REVERSE_GEOCODING_CACHE_MINUTES = "Address cache minutes"
UI_REVERSE_GEOCODING_USE_IN_AI = "Use address in AI context"
UI_OPENAI_API_KEY = "OpenAI API key (leave blank to keep saved)"
UI_OPENAI_MODEL = "OpenAI model"
UI_AI_TELEGRAM_TARGET = "AI Telegram target"
UI_AI_SYSTEM_PROMPT = "System prompt"
UI_AI_MAX_OUTPUT_TOKENS = "Max output tokens"
UI_AI_TELEGRAM_LISTENER_ENABLED = "Enable Telegram AI group listener"
UI_AI_TELEGRAM_LISTENER_CHAT_ID = "Telegram group chat ID for listener"
UI_AI_TELEGRAM_ALLOWED_USER_ID = "Allowed Telegram user ID (optional; blank = everyone)"
UI_AI_TELEGRAM_INCLUDE_CONTEXT = "Include Tesla context for group messages"
UI_AI_CONFIRM_OPTIONAL_CONTROLS = "Ask confirmation for optional vehicle controls"
UI_AI_ALERTS_ENABLED = "Enable AI proactive alerts"
UI_AI_ALERT_STYLE = "Alert message style"
UI_AI_ALERT_COOLDOWN_MINUTES = "Minimum minutes between same alert"
UI_AI_ALERT_LOW_BATTERY_ENABLED = "Low battery alert"
UI_AI_ALERT_LOW_BATTERY_THRESHOLD = "Low battery staged levels (%20 / %10 / %5 / %1)"
UI_AI_ALERT_POST_TRIP_SUMMARY_ENABLED = "Post-trip AI summary"
UI_AI_ALERT_CHARGE_FINISHED_ENABLED = "Charging finished alert"
UI_AI_ALERT_CHARGING_STOPPED_ENABLED = "Charging stopped unexpectedly alert"
UI_AI_ALERT_TIRE_PRESSURE_ENABLED = "Tire pressure alert"
UI_AI_ALERT_TIRE_PRESSURE_THRESHOLD_BAR = "Tire pressure threshold (PSI)"
UI_AI_ALERT_HIGH_BATTERY_TEMP_ENABLED = "High battery temperature alert"
UI_AI_ALERT_HIGH_BATTERY_TEMP_THRESHOLD_C = "High battery temperature threshold"
UI_AI_ALERT_CLIMATE_LEFT_ON_ENABLED = "Climate left on alert"
UI_AI_ALERT_CLIMATE_LEFT_ON_DELAY_MINUTES = "Climate left on delay"
UI_AI_ALERT_UNLOCKED_ENABLED = "Vehicle unlocked alert"
UI_AI_ALERT_UNLOCKED_DELAY_MINUTES = "Vehicle unlocked delay when nobody is present"
UI_AI_ALERT_DOOR_WINDOW_OPEN_ENABLED = "Door/window left open alert"
UI_AI_ALERT_DOOR_WINDOW_OPEN_DELAY_MINUTES = "Door/window open delay when locked and empty"
UI_AI_ALERT_WINDOW_OPEN_INSTANT_ENABLED = "Window open instant test alert"

VEHICLE_ROLE_LABELS = {
    VEHICLE_ROLE_BATTERY_LEVEL: "Battery level",
    VEHICLE_ROLE_BATTERY_RANGE: "Battery range",
    VEHICLE_ROLE_ENERGY_REMAINING: "Energy remaining",
    VEHICLE_ROLE_CHARGING_STATE: "Charging state",
    VEHICLE_ROLE_CHARGE_ENERGY_ADDED: "Charge energy added",
    VEHICLE_ROLE_CHARGER_POWER: "Charger power",
    VEHICLE_ROLE_SPEED: "Speed",
    VEHICLE_ROLE_SHIFT_STATE: "Shift state",
    VEHICLE_ROLE_ODOMETER: "Odometer",
    VEHICLE_ROLE_ELEVATION: "Elevation",
    VEHICLE_ROLE_CLIMATE: "Climate",
    VEHICLE_ROLE_INSIDE_TEMPERATURE: "Inside temperature",
    VEHICLE_ROLE_OUTSIDE_TEMPERATURE: "Outside temperature",
    VEHICLE_ROLE_BATTERY_TEMPERATURE: "Battery temperature",
    VEHICLE_ROLE_TIRE_PRESSURE_FRONT_LEFT: "Tire pressure front left",
    VEHICLE_ROLE_TIRE_PRESSURE_FRONT_RIGHT: "Tire pressure front right",
    VEHICLE_ROLE_TIRE_PRESSURE_REAR_LEFT: "Tire pressure rear left",
    VEHICLE_ROLE_TIRE_PRESSURE_REAR_RIGHT: "Tire pressure rear right",
    VEHICLE_ROLE_DOOR_WINDOW: "Door / window",
    VEHICLE_ROLE_LOCK_STATE: "Lock state",
    VEHICLE_ROLE_LOCATION_TRACKER: "Location tracker",
    VEHICLE_ROLE_VEHICLE_STATE: "Vehicle state / sleep status",
    VEHICLE_ROLE_USER_PRESENT: "User present / occupancy",
    VEHICLE_ROLE_OTHER: "Other / custom",
}


def _vehicle_role_selector() -> selector.SelectSelector:
    """Return vehicle data role selector."""
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[{"value": role, "label": VEHICLE_ROLE_LABELS.get(role, role)} for role in VEHICLE_ENTITY_ROLES],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def normalize_vehicle_entity_map(value: Any) -> list[dict[str, Any]]:
    """Normalize stored Vehicle Entity Manager entries."""
    if not isinstance(value, list):
        return []
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, dict):
            continue
        entity_id = str(item.get("entity_id") or "").strip()
        if not entity_id or entity_id in seen:
            continue
        seen.add(entity_id)
        role = str(item.get("role") or VEHICLE_ROLE_OTHER).strip()
        if role not in VEHICLE_ENTITY_ROLES:
            role = VEHICLE_ROLE_OTHER
        result.append({
            "entity_id": entity_id,
            "role": role,
            "label": str(item.get("label") or VEHICLE_ROLE_LABELS.get(role, role)).strip(),
            "use_report": bool(item.get("use_report", role in {VEHICLE_ROLE_BATTERY_LEVEL, VEHICLE_ROLE_ENERGY_REMAINING, VEHICLE_ROLE_CHARGING_STATE, VEHICLE_ROLE_SPEED, VEHICLE_ROLE_SHIFT_STATE, VEHICLE_ROLE_ODOMETER, VEHICLE_ROLE_ELEVATION, VEHICLE_ROLE_CLIMATE, VEHICLE_ROLE_CHARGE_ENERGY_ADDED})),
            "use_ai": bool(item.get("use_ai", True)),
            "use_alerts": bool(item.get("use_alerts", role not in {VEHICLE_ROLE_LOCATION_TRACKER, VEHICLE_ROLE_OTHER})),
            "use_map": bool(item.get("use_map", role == VEHICLE_ROLE_LOCATION_TRACKER)),
            "source": str(item.get("source") or "manual"),
        })
    return result


def infer_vehicle_role(entity_id: str, friendly_name: str = "") -> str:
    """Infer a vehicle role from an entity id and friendly name."""
    text = f"{entity_id} {friendly_name}".lower()
    if any(k in text for k in ["user present", "user_present", "presence", "occupancy", "occupied", "occupant", "inside vehicle", "driver present", "passenger present", "içeride", "iceride"]):
        return VEHICLE_ROLE_USER_PRESENT
    if "device_tracker." in entity_id or any(k in text for k in ["location", "gps", "latitude", "longitude"]):
        return VEHICLE_ROLE_LOCATION_TRACKER
    if any(k in text for k in ["battery module temperature", "battery temp", "battery_temperature", "pack temperature"]):
        return VEHICLE_ROLE_BATTERY_TEMPERATURE
    if any(k in text for k in ["outside temperature", "ambient temperature", "outside_temp", "exterior temperature", "external temperature"]):
        return VEHICLE_ROLE_OUTSIDE_TEMPERATURE
    if any(k in text for k in ["inside temperature", "cabin temperature", "interior temperature", "inside_temp"]):
        return VEHICLE_ROLE_INSIDE_TEMPERATURE
    if any(k in text for k in ["front left", "fl", "ön sol"]) and any(k in text for k in ["tire", "tyre", "pressure", "tpms", "lastik"]):
        return VEHICLE_ROLE_TIRE_PRESSURE_FRONT_LEFT
    if any(k in text for k in ["front right", "fr", "ön sağ", "on sag"]) and any(k in text for k in ["tire", "tyre", "pressure", "tpms", "lastik"]):
        return VEHICLE_ROLE_TIRE_PRESSURE_FRONT_RIGHT
    if any(k in text for k in ["rear left", "rl", "arka sol"]) and any(k in text for k in ["tire", "tyre", "pressure", "tpms", "lastik"]):
        return VEHICLE_ROLE_TIRE_PRESSURE_REAR_LEFT
    if any(k in text for k in ["rear right", "rr", "arka sağ", "arka sag"]) and any(k in text for k in ["tire", "tyre", "pressure", "tpms", "lastik"]):
        return VEHICLE_ROLE_TIRE_PRESSURE_REAR_RIGHT
    if any(k in text for k in ["tire", "tyre", "pressure", "tpms", "lastik"]):
        return VEHICLE_ROLE_OTHER
    if any(k in text for k in ["battery level", "battery_level", "state of charge", "soc"]):
        return VEHICLE_ROLE_BATTERY_LEVEL
    if any(k in text for k in ["battery range", "range", "menzil"]):
        return VEHICLE_ROLE_BATTERY_RANGE
    if any(k in text for k in ["energy remaining", "remaining energy", "kwh remaining", "usable"]):
        return VEHICLE_ROLE_ENERGY_REMAINING
    if any(k in text for k in ["charge energy added", "energy added"]):
        return VEHICLE_ROLE_CHARGE_ENERGY_ADDED
    if any(k in text for k in ["charger power", "charging power"]):
        return VEHICLE_ROLE_CHARGER_POWER
    if any(k in text for k in ["charging", "charge cable", "plugged"]):
        return VEHICLE_ROLE_CHARGING_STATE
    if "speed" in text or "hız" in text or "hiz" in text:
        return VEHICLE_ROLE_SPEED
    if any(k in text for k in ["shift", "gear", "vites"]):
        return VEHICLE_ROLE_SHIFT_STATE
    if "odometer" in text or "kilometre" in text:
        return VEHICLE_ROLE_ODOMETER
    if "elevation" in text or "rakım" in text or "rakim" in text:
        return VEHICLE_ROLE_ELEVATION
    if "climate." in entity_id or any(k in text for k in ["climate", "hvac", "klima"]):
        return VEHICLE_ROLE_CLIMATE
    if any(k in text for k in ["window", "door", "trunk", "frunk", "cam", "kapı", "kapi"]):
        return VEHICLE_ROLE_DOOR_WINDOW
    if "lock." in entity_id or "lock" in text or "kilit" in text:
        return VEHICLE_ROLE_LOCK_STATE
    return VEHICLE_ROLE_OTHER


def build_vehicle_entity_summary(entries: list[dict[str, Any]]) -> str:
    """Return compact summary for Options UI."""
    if not entries:
        return "Henüz merkezi entity kaydı yok. Önce Smart import çalıştır."
    lines = []
    for item in entries[:60]:
        uses = []
        if item.get("use_report"):
            uses.append("Report")
        if item.get("use_ai"):
            uses.append("AI")
        if item.get("use_alerts"):
            uses.append("Alerts")
        if item.get("use_map"):
            uses.append("Map")
        role = VEHICLE_ROLE_LABELS.get(item.get("role"), item.get("role", "other"))
        label = item.get("label") or role
        lines.append(f"- {role}: {item.get('entity_id')} | {label} | {', '.join(uses) or '-'}")
    if len(entries) > 60:
        lines.append(f"... +{len(entries)-60} kayıt daha")
    return "\n".join(lines)


def _any_entity_selector() -> selector.EntitySelector:
    """Return an entity selector without domain restriction."""
    return selector.EntitySelector(selector.EntitySelectorConfig())


def _multi_entity_selector() -> selector.EntitySelector:
    """Return a multi entity selector without domain restriction."""
    try:
        return selector.EntitySelector(selector.EntitySelectorConfig(multiple=True))
    except TypeError:
        return selector.EntitySelector(selector.EntitySelectorConfig())


def _entity_selector(domain: str) -> selector.EntitySelector:
    """Return an entity selector for a domain."""
    return selector.EntitySelector(selector.EntitySelectorConfig(domain=domain))


def _price_selector() -> selector.NumberSelector:
    """Return a TL/kWh price selector."""
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=0,
            max=100,
            step=0.01,
            mode=selector.NumberSelectorMode.BOX,
            unit_of_measurement="TL/kWh",
        )
    )


def _charging_report_mode_selector() -> selector.SelectSelector:
    """Return charging report send mode selector."""
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                {"value": CHARGING_REPORT_MODE_PROMPT, "label": "Ask before sending report"},
                {"value": CHARGING_REPORT_MODE_DIRECT, "label": "Send directly without asking"},
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )

def _speed_threshold_selector() -> selector.NumberSelector:
    """Return a km/h speed threshold selector."""
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=0,
            max=30,
            step=0.5,
            mode=selector.NumberSelectorMode.BOX,
            unit_of_measurement="km/sa",
        )
    )


def _seconds_selector() -> selector.NumberSelector:
    """Return a selector for seconds."""
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=1,
            max=60,
            step=1,
            mode=selector.NumberSelectorMode.BOX,
            unit_of_measurement="sn",
        )
    )


def _meters_selector() -> selector.NumberSelector:
    """Return a selector for meters."""
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=0,
            max=200,
            step=1,
            mode=selector.NumberSelectorMode.BOX,
            unit_of_measurement="m",
        )
    )


def _live_interval_selector() -> selector.NumberSelector:
    """Return live trip update interval selector."""
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=1,
            max=60,
            step=1,
            mode=selector.NumberSelectorMode.BOX,
            unit_of_measurement="sn",
        )
    )


def _finish_delay_selector() -> selector.NumberSelector:
    """Return live trip finish delay selector."""
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=10,
            max=600,
            step=5,
            mode=selector.NumberSelectorMode.BOX,
            unit_of_measurement="sn",
        )
    )


def _distance_km_selector() -> selector.NumberSelector:
    """Return minimum trip distance selector."""
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=0,
            max=10,
            step=0.1,
            mode=selector.NumberSelectorMode.BOX,
            unit_of_measurement="km",
        )
    )


def _ai_personality_selector() -> selector.SelectSelector:
    """Return AI personality selector."""
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                {"value": AI_PERSONALITY_PROFESSIONAL, "label": "Professional"},
                {"value": AI_PERSONALITY_FRIENDLY, "label": "Friendly"},
                {"value": AI_PERSONALITY_FUNNY, "label": "Funny"},
                {"value": AI_PERSONALITY_SHORT_DIRECT, "label": "Short and direct"},
                {"value": AI_PERSONALITY_PREMIUM, "label": "Premium Tesla assistant"},
                {"value": AI_PERSONALITY_TURKISH_BUDDY, "label": "Turkish buddy / samimi"},
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _ai_answer_length_selector() -> selector.SelectSelector:
    """Return AI answer length selector."""
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                {"value": AI_ANSWER_LENGTH_SHORT, "label": "Short"},
                {"value": AI_ANSWER_LENGTH_NORMAL, "label": "Normal"},
                {"value": AI_ANSWER_LENGTH_DETAILED, "label": "Detailed"},
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _ai_context_mode_selector() -> selector.SelectSelector:
    """Return AI context mode selector."""
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                {"value": AI_CONTEXT_MODE_SMART_MANUAL, "label": "Smart auto + manual overrides"},
                {"value": AI_CONTEXT_MODE_SMART_AUTO, "label": "Smart auto only"},
                {"value": AI_CONTEXT_MODE_MANUAL_ONLY, "label": "Manual entities only"},
                {"value": AI_CONTEXT_MODE_BASIC, "label": "Core selected entities only"},
                {"value": AI_CONTEXT_MODE_SELECTED_DEVICE, "label": "Selected Tesla device"},
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _max_context_entities_selector() -> selector.NumberSelector:
    """Return max context entities selector."""
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=10,
            max=150,
            step=5,
            mode=selector.NumberSelectorMode.BOX,
        )
    )


def _alert_style_selector() -> selector.SelectSelector:
    """Return alert message style selector."""
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                {"value": AI_ALERT_STYLE_RULE, "label": "Rule based / fast"},
                {"value": AI_ALERT_STYLE_AI, "label": "AI written / POM style"},
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _minutes_selector(min_value: int = 1, max_value: int = 240) -> selector.NumberSelector:
    """Return minute selector."""
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=min_value,
            max=max_value,
            step=1,
            mode=selector.NumberSelectorMode.BOX,
            unit_of_measurement="dk",
        )
    )


def _percent_selector() -> selector.NumberSelector:
    """Return percentage selector."""
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=1,
            max=100,
            step=1,
            mode=selector.NumberSelectorMode.BOX,
            unit_of_measurement="%",
        )
    )




def _stored_tire_threshold_to_psi(value: Any) -> float:
    """Show old bar thresholds as PSI in the options UI."""
    try:
        threshold = float(value)
    except (TypeError, ValueError):
        return 36.0
    if threshold <= 8:
        return round(threshold * 14.5038, 1)
    return threshold

def _bar_selector() -> selector.NumberSelector:
    """Return tire pressure selector. Stored key is legacy; UI uses PSI now."""
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=20,
            max=60,
            step=1,
            mode=selector.NumberSelectorMode.BOX,
            unit_of_measurement="PSI",
        )
    )


def _temperature_selector() -> selector.NumberSelector:
    """Return temperature selector."""
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=-20,
            max=90,
            step=1,
            mode=selector.NumberSelectorMode.BOX,
            unit_of_measurement="°C",
        )
    )


def _password_text_selector() -> selector.TextSelector:
    """Return a password-style text selector."""
    try:
        return selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
        )
    except Exception:
        return selector.TextSelector(selector.TextSelectorConfig())


def _multiline_text_selector() -> selector.TextSelector:
    """Return a multiline text selector."""
    return selector.TextSelector(selector.TextSelectorConfig(multiline=True))


def _max_output_tokens_selector() -> selector.NumberSelector:
    """Return max output token selector."""
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=100,
            max=4000,
            step=50,
            mode=selector.NumberSelectorMode.BOX,
        )
    )


def _section_selector() -> selector.SelectSelector:
    """Return the section selector used by the main Options menu."""
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                {"value": SECTION_VEHICLE_ENTITY_MANAGER, "label": "01 · Vehicle Entity Manager"},
                {"value": SECTION_AUTOMATION_TELEGRAM, "label": "02 · Automation & Telegram"},
                {"value": SECTION_PRICES_REPORT, "label": "03 · Prices & report layout"},
                {"value": SECTION_LIVE_TRIP, "label": "04 · Live Trip Calculation"},
                {"value": SECTION_AI_BASIC, "label": "05 · POM AI Basic"},
                {"value": SECTION_AI_ALERTS, "label": "06 · AI Alerts & Watchers"},
                {"value": SECTION_FINISH, "label": "Save and close"},
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _after_saving_selector() -> selector.SelectSelector:
    """Return navigation selector for submenu screens."""
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                {"value": ACTION_RETURN_TO_MENU, "label": "Save and return to main menu"},
                {"value": ACTION_SAVE_AND_CLOSE, "label": "Save and close"},
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _vehicle_manager_form_action_selector() -> selector.SelectSelector:
    """Return actions for the single Vehicle Entity Manager form."""
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                {"value": ACTION_VEHICLE_AUTO_SELECT_AI, "label": "Find AI entities from selected Tesla device"},
                {"value": ACTION_VEHICLE_SAVE_REVIEW, "label": "Save and show summary"},
                {"value": ACTION_RETURN_TO_MENU, "label": "Save and return to main menu"},
                {"value": ACTION_SAVE_AND_CLOSE, "label": "Save and close"},
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _map_ui_input(
    user_input: dict[str, Any],
    field_map: dict[str, str],
) -> dict[str, Any]:
    """Map human-readable UI keys back to stored config option keys."""
    return {
        stored_key: user_input[ui_key]
        for ui_key, stored_key in field_map.items()
        if ui_key in user_input
    }


def build_schema(current: dict[str, Any] | None = None) -> vol.Schema:
    """Build the initial setup schema.

    This is intentionally kept as a full schema for first-time setup.
    The Configure / Options flow below is split into cleaner sections.
    """
    current = current or {}

    return vol.Schema(
        {
            vol.Required(
                CONF_NAME,
                default=current.get(CONF_NAME, DEFAULT_NAME),
            ): str,

            vol.Required(
                CONF_SHIFT_STATE_ENTITY,
                default=current.get(CONF_SHIFT_STATE_ENTITY, DEFAULT_SHIFT_STATE_ENTITY),
            ): _entity_selector("sensor"),

            vol.Required(
                CONF_SPEED_ENTITY,
                default=current.get(CONF_SPEED_ENTITY, DEFAULT_SPEED_ENTITY),
            ): _entity_selector("sensor"),

            vol.Required(
                CONF_ODOMETER_ENTITY,
                default=current.get(CONF_ODOMETER_ENTITY, DEFAULT_ODOMETER_ENTITY),
            ): _entity_selector("sensor"),

            vol.Required(
                CONF_BATTERY_LEVEL_ENTITY,
                default=current.get(CONF_BATTERY_LEVEL_ENTITY, DEFAULT_BATTERY_LEVEL_ENTITY),
            ): _entity_selector("sensor"),

            vol.Required(
                CONF_ENERGY_REMAINING_ENTITY,
                default=current.get(CONF_ENERGY_REMAINING_ENTITY, DEFAULT_ENERGY_REMAINING_ENTITY),
            ): _entity_selector("sensor"),

            vol.Required(
                CONF_ELEVATION_ENTITY,
                default=current.get(CONF_ELEVATION_ENTITY, DEFAULT_ELEVATION_ENTITY),
            ): _entity_selector("sensor"),

            vol.Required(
                CONF_CLIMATE_ENTITY,
                default=current.get(CONF_CLIMATE_ENTITY, DEFAULT_CLIMATE_ENTITY),
            ): _entity_selector("climate"),

            vol.Required(
                CONF_CHARGING_ENTITY,
                default=current.get(CONF_CHARGING_ENTITY, DEFAULT_CHARGING_ENTITY),
            ): _entity_selector("binary_sensor"),

            vol.Required(
                CONF_CHARGE_ENERGY_ADDED_ENTITY,
                default=current.get(
                    CONF_CHARGE_ENERGY_ADDED_ENTITY,
                    DEFAULT_CHARGE_ENERGY_ADDED_ENTITY,
                ),
            ): _entity_selector("sensor"),

            vol.Required(
                CONF_SUPERCHARGER_PRICE,
                default=current.get(CONF_SUPERCHARGER_PRICE, DEFAULT_SUPERCHARGER_PRICE),
            ): _price_selector(),

            vol.Required(
                CONF_ZES_PRICE,
                default=current.get(CONF_ZES_PRICE, DEFAULT_ZES_PRICE),
            ): _price_selector(),

            vol.Required(
                CONF_ASTOR_PRICE,
                default=current.get(CONF_ASTOR_PRICE, DEFAULT_ASTOR_PRICE),
            ): _price_selector(),

            vol.Required(
                CONF_TELEGRAM_TARGET,
                default=current.get(CONF_TELEGRAM_TARGET, DEFAULT_TELEGRAM_TARGET),
            ): str,

            vol.Required(
                CONF_AUTO_TRIP_TRACKING,
                default=current.get(CONF_AUTO_TRIP_TRACKING, DEFAULT_AUTO_TRIP_TRACKING),
            ): selector.BooleanSelector(),

            vol.Required(
                CONF_AUTO_START_SPEED_THRESHOLD,
                default=current.get(
                    CONF_AUTO_START_SPEED_THRESHOLD,
                    DEFAULT_AUTO_START_SPEED_THRESHOLD,
                ),
            ): _speed_threshold_selector(),

            vol.Required(
                CONF_SHOW_DISTANCE,
                default=current.get(CONF_SHOW_DISTANCE, DEFAULT_SHOW_DISTANCE),
            ): selector.BooleanSelector(),

            vol.Required(
                CONF_SHOW_DURATION,
                default=current.get(CONF_SHOW_DURATION, DEFAULT_SHOW_DURATION),
            ): selector.BooleanSelector(),

            vol.Required(
                CONF_SHOW_TRAFFIC,
                default=current.get(CONF_SHOW_TRAFFIC, DEFAULT_SHOW_TRAFFIC),
            ): selector.BooleanSelector(),

            vol.Required(
                CONF_SHOW_AVERAGE_SPEED,
                default=current.get(CONF_SHOW_AVERAGE_SPEED, DEFAULT_SHOW_AVERAGE_SPEED),
            ): selector.BooleanSelector(),

            vol.Required(
                CONF_SHOW_ENERGY,
                default=current.get(CONF_SHOW_ENERGY, DEFAULT_SHOW_ENERGY),
            ): selector.BooleanSelector(),

            vol.Required(
                CONF_SHOW_CONSUMPTION,
                default=current.get(CONF_SHOW_CONSUMPTION, DEFAULT_SHOW_CONSUMPTION),
            ): selector.BooleanSelector(),

            vol.Required(
                CONF_SHOW_BATTERY,
                default=current.get(CONF_SHOW_BATTERY, DEFAULT_SHOW_BATTERY),
            ): selector.BooleanSelector(),

            vol.Required(
                CONF_SHOW_COST,
                default=current.get(CONF_SHOW_COST, DEFAULT_SHOW_COST),
            ): selector.BooleanSelector(),

            vol.Required(
                CONF_SHOW_CLIMATE,
                default=current.get(CONF_SHOW_CLIMATE, DEFAULT_SHOW_CLIMATE),
            ): selector.BooleanSelector(),

            vol.Required(
                CONF_SHOW_ELEVATION,
                default=current.get(CONF_SHOW_ELEVATION, DEFAULT_SHOW_ELEVATION),
            ): selector.BooleanSelector(),
        }
    )



def build_options_menu_schema() -> vol.Schema:
    """Build the main Options section picker."""
    return vol.Schema(
        {
            vol.Required(
                UI_SETTINGS_SECTION,
                default=SECTION_VEHICLE_ENTITY_MANAGER,
            ): _section_selector(),
        }
    )


def build_core_vehicle_schema(current: dict[str, Any]) -> vol.Schema:
    """Build combined core and vehicle entity options schema."""
    return vol.Schema(
        {
            vol.Required(
                UI_NAME,
                default=current.get(CONF_NAME, DEFAULT_NAME),
            ): str,

            vol.Required(
                UI_SHIFT_STATE_ENTITY,
                default=current.get(CONF_SHIFT_STATE_ENTITY, DEFAULT_SHIFT_STATE_ENTITY),
            ): _entity_selector("sensor"),

            vol.Required(
                UI_SPEED_ENTITY,
                default=current.get(CONF_SPEED_ENTITY, DEFAULT_SPEED_ENTITY),
            ): _entity_selector("sensor"),

            vol.Required(
                UI_ODOMETER_ENTITY,
                default=current.get(CONF_ODOMETER_ENTITY, DEFAULT_ODOMETER_ENTITY),
            ): _entity_selector("sensor"),

            vol.Required(
                UI_BATTERY_LEVEL_ENTITY,
                default=current.get(CONF_BATTERY_LEVEL_ENTITY, DEFAULT_BATTERY_LEVEL_ENTITY),
            ): _entity_selector("sensor"),

            vol.Required(
                UI_ENERGY_REMAINING_ENTITY,
                default=current.get(CONF_ENERGY_REMAINING_ENTITY, DEFAULT_ENERGY_REMAINING_ENTITY),
            ): _entity_selector("sensor"),

            vol.Required(
                UI_ELEVATION_ENTITY,
                default=current.get(CONF_ELEVATION_ENTITY, DEFAULT_ELEVATION_ENTITY),
            ): _entity_selector("sensor"),

            vol.Required(
                UI_CLIMATE_ENTITY,
                default=current.get(CONF_CLIMATE_ENTITY, DEFAULT_CLIMATE_ENTITY),
            ): _entity_selector("climate"),

            vol.Required(
                UI_CHARGING_ENTITY,
                default=current.get(CONF_CHARGING_ENTITY, DEFAULT_CHARGING_ENTITY),
            ): _entity_selector("binary_sensor"),

            vol.Required(
                UI_CHARGE_ENERGY_ADDED_ENTITY,
                default=current.get(
                    CONF_CHARGE_ENERGY_ADDED_ENTITY,
                    DEFAULT_CHARGE_ENERGY_ADDED_ENTITY,
                ),
            ): _entity_selector("sensor"),

            vol.Required(
                UI_AFTER_SAVING,
                default=ACTION_RETURN_TO_MENU,
            ): _after_saving_selector(),
        }
    )


def build_live_trip_entity_summary(current: dict[str, Any]) -> str:
    """Return read-only-ish summary of report entities used by live trip engine."""
    entries = normalize_vehicle_entity_map(current.get(CONF_VEHICLE_ENTITY_MAP, DEFAULT_VEHICLE_ENTITY_MAP))

    def role_entity(role: str, legacy_key: str | None = None) -> str:
        for item in entries:
            if item.get("role") == role and item.get("use_report"):
                return str(item.get("entity_id") or "").strip() or "—"
        if legacy_key:
            return str(current.get(legacy_key) or "—")
        return "—"

    lines = [
        "Bu bölümde tekrar entity seçilmez. Canlı sürüş hesabı Vehicle Entity Manager / Report alanındaki seçimleri kullanır.",
        "",
        f"Speed: {role_entity(VEHICLE_ROLE_SPEED, CONF_SPEED_ENTITY)}",
        f"Shift state: {role_entity(VEHICLE_ROLE_SHIFT_STATE, CONF_SHIFT_STATE_ENTITY)}",
        f"Odometer: {role_entity(VEHICLE_ROLE_ODOMETER, CONF_ODOMETER_ENTITY)}",
        f"Energy remaining: {role_entity(VEHICLE_ROLE_ENERGY_REMAINING, CONF_ENERGY_REMAINING_ENTITY)}",
        f"Battery level: {role_entity(VEHICLE_ROLE_BATTERY_LEVEL, CONF_BATTERY_LEVEL_ENTITY)}",
        f"Climate: {role_entity(VEHICLE_ROLE_CLIMATE, CONF_CLIMATE_ENTITY)}",
        f"Elevation: {role_entity(VEHICLE_ROLE_ELEVATION, CONF_ELEVATION_ENTITY)}",
        "",
        "Eksik veya yanlış entity varsa Vehicle Entity Manager bölümünden düzelt.",
    ]
    return "\n".join(lines)


def build_live_trip_schema(current: dict[str, Any]) -> vol.Schema:
    """Build live trip calculation options schema."""
    return vol.Schema(
        {
            vol.Optional(
                UI_LIVE_TRIP_ENTITY_SUMMARY,
                default=build_live_trip_entity_summary(current),
            ): _multiline_text_selector(),

            vol.Required(
                UI_LIVE_TRIP_ENABLED,
                default=current.get(CONF_LIVE_TRIP_ENABLED, DEFAULT_LIVE_TRIP_ENABLED),
            ): selector.BooleanSelector(),

            vol.Required(
                UI_LIVE_TRIP_UPDATE_INTERVAL_SECONDS,
                default=current.get(CONF_LIVE_TRIP_UPDATE_INTERVAL_SECONDS, DEFAULT_LIVE_TRIP_UPDATE_INTERVAL_SECONDS),
            ): _live_interval_selector(),

            vol.Required(
                UI_LIVE_TRIP_TRAFFIC_SPEED_THRESHOLD,
                default=current.get(CONF_LIVE_TRIP_TRAFFIC_SPEED_THRESHOLD, DEFAULT_LIVE_TRIP_TRAFFIC_SPEED_THRESHOLD),
            ): _speed_threshold_selector(),

            vol.Required(
                UI_LIVE_TRIP_FINISH_DELAY_SECONDS,
                default=current.get(CONF_LIVE_TRIP_FINISH_DELAY_SECONDS, DEFAULT_LIVE_TRIP_FINISH_DELAY_SECONDS),
            ): _finish_delay_selector(),

            vol.Required(
                UI_LIVE_TRIP_MIN_DISTANCE_KM,
                default=current.get(CONF_LIVE_TRIP_MIN_DISTANCE_KM, DEFAULT_LIVE_TRIP_MIN_DISTANCE_KM),
            ): _distance_km_selector(),

            vol.Required(
                UI_AFTER_SAVING,
                default=ACTION_RETURN_TO_MENU,
            ): _after_saving_selector(),
        }
    )


def build_automation_telegram_schema(current: dict[str, Any]) -> vol.Schema:
    """Build combined automation and Telegram options schema."""
    return vol.Schema(
        {
            vol.Required(
                UI_AUTO_TRIP_TRACKING,
                default=current.get(CONF_AUTO_TRIP_TRACKING, DEFAULT_AUTO_TRIP_TRACKING),
            ): selector.BooleanSelector(),

            vol.Required(
                UI_AUTO_START_SPEED_THRESHOLD,
                default=current.get(
                    CONF_AUTO_START_SPEED_THRESHOLD,
                    DEFAULT_AUTO_START_SPEED_THRESHOLD,
                ),
            ): _speed_threshold_selector(),

            vol.Required(
                UI_TELEGRAM_TARGET,
                default=current.get(CONF_TELEGRAM_TARGET, DEFAULT_TELEGRAM_TARGET),
            ): str,

            vol.Required(
                UI_TRIP_MAP_ENABLED,
                default=current.get(CONF_TRIP_MAP_ENABLED, DEFAULT_TRIP_MAP_ENABLED),
            ): selector.BooleanSelector(),

            vol.Required(
                UI_TRIP_MAP_TRACKER_ENTITY,
                default=current.get(CONF_TRIP_MAP_TRACKER_ENTITY, DEFAULT_TRIP_MAP_TRACKER_ENTITY),
            ): _entity_selector("device_tracker"),

            vol.Required(
                UI_TRIP_MAP_SAMPLE_INTERVAL_SECONDS,
                default=current.get(CONF_TRIP_MAP_SAMPLE_INTERVAL_SECONDS, DEFAULT_TRIP_MAP_SAMPLE_INTERVAL_SECONDS),
            ): _seconds_selector(),

            vol.Required(
                UI_TRIP_MAP_MIN_MOVEMENT_METERS,
                default=current.get(CONF_TRIP_MAP_MIN_MOVEMENT_METERS, DEFAULT_TRIP_MAP_MIN_MOVEMENT_METERS),
            ): _meters_selector(),

            vol.Required(
                UI_TRIP_MAP_SEND_SEPARATE_PNG,
                default=current.get(CONF_TRIP_MAP_SEND_SEPARATE_PNG, DEFAULT_TRIP_MAP_SEND_SEPARATE_PNG),
            ): selector.BooleanSelector(),

            vol.Required(
                UI_AFTER_SAVING,
                default=ACTION_RETURN_TO_MENU,
            ): _after_saving_selector(),
        }
    )


def build_prices_report_schema(current: dict[str, Any]) -> vol.Schema:
    """Build combined charging price and report layout options schema."""
    return vol.Schema(
        {
            vol.Required(
                UI_SUPERCHARGER_PRICE,
                default=current.get(CONF_SUPERCHARGER_PRICE, DEFAULT_SUPERCHARGER_PRICE),
            ): _price_selector(),

            vol.Required(
                UI_ZES_PRICE,
                default=current.get(CONF_ZES_PRICE, DEFAULT_ZES_PRICE),
            ): _price_selector(),

            vol.Required(
                UI_ASTOR_PRICE,
                default=current.get(CONF_ASTOR_PRICE, DEFAULT_ASTOR_PRICE),
            ): _price_selector(),

            vol.Required(
                UI_CHARGING_REPORT_MODE,
                default=current.get(CONF_CHARGING_REPORT_MODE, DEFAULT_CHARGING_REPORT_MODE),
            ): _charging_report_mode_selector(),

            vol.Required(
                UI_SHOW_DISTANCE,
                default=current.get(CONF_SHOW_DISTANCE, DEFAULT_SHOW_DISTANCE),
            ): selector.BooleanSelector(),

            vol.Required(
                UI_SHOW_DURATION,
                default=current.get(CONF_SHOW_DURATION, DEFAULT_SHOW_DURATION),
            ): selector.BooleanSelector(),

            vol.Required(
                UI_SHOW_TRAFFIC,
                default=current.get(CONF_SHOW_TRAFFIC, DEFAULT_SHOW_TRAFFIC),
            ): selector.BooleanSelector(),

            vol.Required(
                UI_SHOW_AVERAGE_SPEED,
                default=current.get(CONF_SHOW_AVERAGE_SPEED, DEFAULT_SHOW_AVERAGE_SPEED),
            ): selector.BooleanSelector(),

            vol.Required(
                UI_SHOW_ENERGY,
                default=current.get(CONF_SHOW_ENERGY, DEFAULT_SHOW_ENERGY),
            ): selector.BooleanSelector(),

            vol.Required(
                UI_SHOW_CONSUMPTION,
                default=current.get(CONF_SHOW_CONSUMPTION, DEFAULT_SHOW_CONSUMPTION),
            ): selector.BooleanSelector(),

            vol.Required(
                UI_SHOW_BATTERY,
                default=current.get(CONF_SHOW_BATTERY, DEFAULT_SHOW_BATTERY),
            ): selector.BooleanSelector(),

            vol.Required(
                UI_SHOW_COST,
                default=current.get(CONF_SHOW_COST, DEFAULT_SHOW_COST),
            ): selector.BooleanSelector(),

            vol.Required(
                UI_SHOW_CLIMATE,
                default=current.get(CONF_SHOW_CLIMATE, DEFAULT_SHOW_CLIMATE),
            ): selector.BooleanSelector(),

            vol.Required(
                UI_SHOW_ELEVATION,
                default=current.get(CONF_SHOW_ELEVATION, DEFAULT_SHOW_ELEVATION),
            ): selector.BooleanSelector(),

            vol.Required(
                UI_AFTER_SAVING,
                default=ACTION_RETURN_TO_MENU,
            ): _after_saving_selector(),
        }
    )



def build_ai_basic_schema(current: dict[str, Any]) -> vol.Schema:
    """Build POM AI Basic options schema."""
    return vol.Schema(
        {
            vol.Required(
                UI_AI_ENABLED,
                default=current.get(CONF_AI_ENABLED, DEFAULT_AI_ENABLED),
            ): selector.BooleanSelector(),

            vol.Required(
                UI_AI_PERSONALITY,
                default=current.get(CONF_AI_PERSONALITY, DEFAULT_AI_PERSONALITY),
            ): _ai_personality_selector(),

            vol.Required(
                UI_AI_ANSWER_LENGTH,
                default=current.get(CONF_AI_ANSWER_LENGTH, DEFAULT_AI_ANSWER_LENGTH),
            ): _ai_answer_length_selector(),

            vol.Required(
                UI_AI_CONTEXT_MODE,
                default=current.get(CONF_AI_CONTEXT_MODE, DEFAULT_AI_CONTEXT_MODE),
            ): _ai_context_mode_selector(),


            vol.Required(
                UI_AI_AUTO_DISCOVER_DEVICE_ENTITIES,
                default=current.get(CONF_AI_AUTO_DISCOVER_DEVICE_ENTITIES, DEFAULT_AI_AUTO_DISCOVER_DEVICE_ENTITIES),
            ): selector.BooleanSelector(),

            vol.Required(
                UI_AI_INCLUDE_UNAVAILABLE,
                default=current.get(CONF_AI_INCLUDE_UNAVAILABLE, DEFAULT_AI_INCLUDE_UNAVAILABLE),
            ): selector.BooleanSelector(),

            vol.Required(
                UI_AI_MAX_CONTEXT_ENTITIES,
                default=current.get(CONF_AI_MAX_CONTEXT_ENTITIES, DEFAULT_AI_MAX_CONTEXT_ENTITIES),
            ): _max_context_entities_selector(),

            vol.Optional(
                UI_OPENAI_API_KEY,
                default=current.get(CONF_OPENAI_API_KEY, ""),
            ): _password_text_selector(),

            vol.Required(
                UI_OPENAI_MODEL,
                default=current.get(CONF_OPENAI_MODEL, DEFAULT_OPENAI_MODEL),
            ): str,

            vol.Optional(
                UI_AI_TELEGRAM_TARGET,
                default=current.get(CONF_AI_TELEGRAM_TARGET, current.get(CONF_TELEGRAM_TARGET, DEFAULT_TELEGRAM_TARGET)),
            ): str,

            vol.Required(
                UI_AI_SYSTEM_PROMPT,
                default=current.get(CONF_AI_SYSTEM_PROMPT, DEFAULT_AI_SYSTEM_PROMPT),
            ): _multiline_text_selector(),

            vol.Required(
                UI_AI_MAX_OUTPUT_TOKENS,
                default=current.get(CONF_AI_MAX_OUTPUT_TOKENS, DEFAULT_AI_MAX_OUTPUT_TOKENS),
            ): _max_output_tokens_selector(),

            vol.Required(
                UI_AI_TELEGRAM_LISTENER_ENABLED,
                default=current.get(CONF_AI_TELEGRAM_LISTENER_ENABLED, DEFAULT_AI_TELEGRAM_LISTENER_ENABLED),
            ): selector.BooleanSelector(),

            vol.Optional(
                UI_AI_TELEGRAM_LISTENER_CHAT_ID,
                default=current.get(
                    CONF_AI_TELEGRAM_LISTENER_CHAT_ID,
                    current.get(CONF_AI_TELEGRAM_TARGET, current.get(CONF_TELEGRAM_TARGET, DEFAULT_TELEGRAM_TARGET)),
                ),
            ): str,

            vol.Optional(
                UI_AI_TELEGRAM_ALLOWED_USER_ID,
                default=current.get(CONF_AI_TELEGRAM_ALLOWED_USER_ID, DEFAULT_AI_TELEGRAM_ALLOWED_USER_ID),
            ): str,

            vol.Required(
                UI_AI_TELEGRAM_INCLUDE_CONTEXT,
                default=current.get(CONF_AI_TELEGRAM_INCLUDE_CONTEXT, DEFAULT_AI_TELEGRAM_INCLUDE_CONTEXT),
            ): selector.BooleanSelector(),

            vol.Required(
                UI_AI_CONFIRM_OPTIONAL_CONTROLS,
                default=current.get(CONF_AI_CONFIRM_OPTIONAL_CONTROLS, DEFAULT_AI_CONFIRM_OPTIONAL_CONTROLS),
            ): selector.BooleanSelector(),

            vol.Required(
                UI_AFTER_SAVING,
                default=ACTION_RETURN_TO_MENU,
            ): _after_saving_selector(),
        }
    )


def build_ai_alerts_schema(current: dict[str, Any]) -> vol.Schema:
    """Build AI proactive alert options schema."""
    return vol.Schema(
        {
            vol.Required(
                UI_AI_ALERTS_ENABLED,
                default=current.get(CONF_AI_ALERTS_ENABLED, DEFAULT_AI_ALERTS_ENABLED),
            ): selector.BooleanSelector(),

            vol.Required(
                UI_AI_ALERT_STYLE,
                default=current.get(CONF_AI_ALERT_STYLE, DEFAULT_AI_ALERT_STYLE),
            ): _alert_style_selector(),

            vol.Required(
                UI_AI_ALERT_COOLDOWN_MINUTES,
                default=current.get(CONF_AI_ALERT_COOLDOWN_MINUTES, DEFAULT_AI_ALERT_COOLDOWN_MINUTES),
            ): _minutes_selector(1, 240),

            vol.Required(
                UI_AI_ALERT_LOW_BATTERY_ENABLED,
                default=current.get(CONF_AI_ALERT_LOW_BATTERY_ENABLED, DEFAULT_AI_ALERT_LOW_BATTERY_ENABLED),
            ): selector.BooleanSelector(),

            vol.Required(
                UI_AI_ALERT_CHARGE_FINISHED_ENABLED,
                default=current.get(CONF_AI_ALERT_CHARGE_FINISHED_ENABLED, DEFAULT_AI_ALERT_CHARGE_FINISHED_ENABLED),
            ): selector.BooleanSelector(),

            vol.Required(
                UI_AI_ALERT_CHARGING_STOPPED_ENABLED,
                default=current.get(CONF_AI_ALERT_CHARGING_STOPPED_ENABLED, DEFAULT_AI_ALERT_CHARGING_STOPPED_ENABLED),
            ): selector.BooleanSelector(),

            vol.Required(
                UI_AI_ALERT_TIRE_PRESSURE_ENABLED,
                default=current.get(CONF_AI_ALERT_TIRE_PRESSURE_ENABLED, DEFAULT_AI_ALERT_TIRE_PRESSURE_ENABLED),
            ): selector.BooleanSelector(),

            vol.Required(
                UI_AI_ALERT_TIRE_PRESSURE_THRESHOLD_BAR,
                default=_stored_tire_threshold_to_psi(current.get(CONF_AI_ALERT_TIRE_PRESSURE_THRESHOLD_BAR, DEFAULT_AI_ALERT_TIRE_PRESSURE_THRESHOLD_BAR)),
            ): _bar_selector(),

            vol.Required(
                UI_AI_ALERT_HIGH_BATTERY_TEMP_ENABLED,
                default=current.get(CONF_AI_ALERT_HIGH_BATTERY_TEMP_ENABLED, DEFAULT_AI_ALERT_HIGH_BATTERY_TEMP_ENABLED),
            ): selector.BooleanSelector(),

            vol.Required(
                UI_AI_ALERT_HIGH_BATTERY_TEMP_THRESHOLD_C,
                default=current.get(CONF_AI_ALERT_HIGH_BATTERY_TEMP_THRESHOLD_C, DEFAULT_AI_ALERT_HIGH_BATTERY_TEMP_THRESHOLD_C),
            ): _temperature_selector(),

            vol.Required(
                UI_AI_ALERT_UNLOCKED_ENABLED,
                default=current.get(CONF_AI_ALERT_UNLOCKED_ENABLED, DEFAULT_AI_ALERT_UNLOCKED_ENABLED),
            ): selector.BooleanSelector(),

            vol.Required(
                UI_AI_ALERT_UNLOCKED_DELAY_MINUTES,
                default=current.get(CONF_AI_ALERT_UNLOCKED_DELAY_MINUTES, DEFAULT_AI_ALERT_UNLOCKED_DELAY_MINUTES),
            ): _minutes_selector(1, 120),

            vol.Required(
                UI_AI_ALERT_DOOR_WINDOW_OPEN_ENABLED,
                default=current.get(CONF_AI_ALERT_DOOR_WINDOW_OPEN_ENABLED, DEFAULT_AI_ALERT_DOOR_WINDOW_OPEN_ENABLED),
            ): selector.BooleanSelector(),

            vol.Required(
                UI_AI_ALERT_DOOR_WINDOW_OPEN_DELAY_MINUTES,
                default=current.get(CONF_AI_ALERT_DOOR_WINDOW_OPEN_DELAY_MINUTES, DEFAULT_AI_ALERT_DOOR_WINDOW_OPEN_DELAY_MINUTES),
            ): _minutes_selector(1, 120),

            vol.Required(
                UI_AFTER_SAVING,
                default=ACTION_RETURN_TO_MENU,
            ): _after_saving_selector(),
        }
    )


def get_entity_for_role(entries: list[dict[str, Any]], role: str, fallback: str = "") -> str:
    """Return the first entity id for a role, preferring report-enabled entries."""
    for item in entries:
        if item.get("role") == role and item.get("use_report"):
            return str(item.get("entity_id") or fallback)
    for item in entries:
        if item.get("role") == role:
            return str(item.get("entity_id") or fallback)
    return fallback


def build_vehicle_entity_manager_schema(
    current: dict[str, Any],
    discovered_summary: str = "",
) -> vol.Schema:
    """Build one-page Vehicle Entity Manager schema.

    This is intentionally a single place for report, AI, auto-discovered and excluded entities.
    """
    entries = normalize_vehicle_entity_map(current.get(CONF_VEHICLE_ENTITY_MAP, DEFAULT_VEHICLE_ENTITY_MAP))

    return vol.Schema(
        {
            vol.Optional(
                UI_VEHICLE_REPORT_SECTION_NOTE,
                default=(
                    "Bu bölüm resmi sürüş raporu, tüketim hesabı ve harita için kullanılan temel araç verileridir. "
                    "Aşağıdaki alanlar raporun ana veri kaynaklarıdır."
                ),
            ): _multiline_text_selector(),

            vol.Required(
                UI_REPORT_BATTERY_LEVEL_ENTITY,
                default=get_entity_for_role(entries, VEHICLE_ROLE_BATTERY_LEVEL, current.get(CONF_BATTERY_LEVEL_ENTITY, DEFAULT_BATTERY_LEVEL_ENTITY)),
            ): _entity_selector("sensor"),

            vol.Required(
                UI_REPORT_ENERGY_REMAINING_ENTITY,
                default=get_entity_for_role(entries, VEHICLE_ROLE_ENERGY_REMAINING, current.get(CONF_ENERGY_REMAINING_ENTITY, DEFAULT_ENERGY_REMAINING_ENTITY)),
            ): _entity_selector("sensor"),

            vol.Required(
                UI_REPORT_SPEED_ENTITY,
                default=get_entity_for_role(entries, VEHICLE_ROLE_SPEED, current.get(CONF_SPEED_ENTITY, DEFAULT_SPEED_ENTITY)),
            ): _entity_selector("sensor"),

            vol.Required(
                UI_REPORT_SHIFT_STATE_ENTITY,
                default=get_entity_for_role(entries, VEHICLE_ROLE_SHIFT_STATE, current.get(CONF_SHIFT_STATE_ENTITY, DEFAULT_SHIFT_STATE_ENTITY)),
            ): _entity_selector("sensor"),

            vol.Required(
                UI_REPORT_ODOMETER_ENTITY,
                default=get_entity_for_role(entries, VEHICLE_ROLE_ODOMETER, current.get(CONF_ODOMETER_ENTITY, DEFAULT_ODOMETER_ENTITY)),
            ): _entity_selector("sensor"),

            vol.Required(
                UI_REPORT_ELEVATION_ENTITY,
                default=get_entity_for_role(entries, VEHICLE_ROLE_ELEVATION, current.get(CONF_ELEVATION_ENTITY, DEFAULT_ELEVATION_ENTITY)),
            ): _entity_selector("sensor"),

            vol.Required(
                UI_REPORT_CLIMATE_ENTITY,
                default=get_entity_for_role(entries, VEHICLE_ROLE_CLIMATE, current.get(CONF_CLIMATE_ENTITY, DEFAULT_CLIMATE_ENTITY)),
            ): _entity_selector("climate"),

            vol.Required(
                UI_REPORT_CHARGING_ENTITY,
                default=get_entity_for_role(entries, VEHICLE_ROLE_CHARGING_STATE, current.get(CONF_CHARGING_ENTITY, DEFAULT_CHARGING_ENTITY)),
            ): _any_entity_selector(),

            vol.Required(
                UI_REPORT_CHARGE_ENERGY_ADDED_ENTITY,
                default=get_entity_for_role(entries, VEHICLE_ROLE_CHARGE_ENERGY_ADDED, current.get(CONF_CHARGE_ENERGY_ADDED_ENTITY, DEFAULT_CHARGE_ENERGY_ADDED_ENTITY)),
            ): _entity_selector("sensor"),

            vol.Required(
                UI_REPORT_LOCATION_TRACKER_ENTITY,
                default=get_entity_for_role(entries, VEHICLE_ROLE_LOCATION_TRACKER, current.get(CONF_TRIP_MAP_TRACKER_ENTITY, DEFAULT_TRIP_MAP_TRACKER_ENTITY)),
            ): _entity_selector("device_tracker"),

            vol.Optional(
                UI_REPORT_VEHICLE_STATE_ENTITY,
                default=get_entity_for_role(entries, VEHICLE_ROLE_VEHICLE_STATE, ""),
            ): _any_entity_selector(),

            vol.Optional(
                UI_VEHICLE_AI_SECTION_NOTE,
                default=(
                    "Vehicle report bölümü burada biter. Aşağıdaki alanlar AI / auto select için kullanılır. "
                    "Auto select, seçtiğin ana Tesla entity'sinin bağlı olduğu cihazdaki entity'leri bulur."
                ),
            ): _multiline_text_selector(),

            vol.Optional(
                UI_AI_MAIN_TESLA_ENTITY,
                default=current.get(
                    CONF_AI_MAIN_TESLA_ENTITY,
                    get_entity_for_role(entries, VEHICLE_ROLE_BATTERY_LEVEL, current.get(CONF_BATTERY_LEVEL_ENTITY, DEFAULT_BATTERY_LEVEL_ENTITY)),
                ),
            ): _any_entity_selector(),

            vol.Required(
                UI_REVERSE_GEOCODING_ENABLED,
                default=current.get(CONF_REVERSE_GEOCODING_ENABLED, DEFAULT_REVERSE_GEOCODING_ENABLED),
            ): selector.BooleanSelector(),

            vol.Required(
                UI_REVERSE_GEOCODING_CACHE_MINUTES,
                default=current.get(CONF_REVERSE_GEOCODING_CACHE_MINUTES, DEFAULT_REVERSE_GEOCODING_CACHE_MINUTES),
            ): _minutes_selector(5, 1440),

            vol.Required(
                UI_REVERSE_GEOCODING_USE_IN_AI,
                default=current.get(CONF_REVERSE_GEOCODING_USE_IN_AI, DEFAULT_REVERSE_GEOCODING_USE_IN_AI),
            ): selector.BooleanSelector(),

            vol.Optional(
                UI_VEHICLE_AI_ENTITIES,
                default=current.get(
                    CONF_AI_EXTRA_CONTEXT_ENTITIES,
                    [
                        item.get("entity_id")
                        for item in entries
                        if item.get("use_ai") and not item.get("use_report") and item.get("entity_id")
                    ],
                ),
            ): _multi_entity_selector(),

            vol.Optional(
                UI_VEHICLE_EXCLUDED_ENTITIES,
                default=current.get(CONF_AI_EXCLUDED_CONTEXT_ENTITIES, DEFAULT_AI_EXCLUDED_CONTEXT_ENTITIES),
            ): _multi_entity_selector(),

            vol.Required(UI_VEHICLE_MANAGER_ACTION, default=ACTION_VEHICLE_SAVE_REVIEW): _vehicle_manager_form_action_selector(),
        }
    )


def build_vehicle_entity_add_schema(current: dict[str, Any], entity_id: str | None = None) -> vol.Schema:
    """Build add/update vehicle entity schema."""
    entries = normalize_vehicle_entity_map(current.get(CONF_VEHICLE_ENTITY_MAP, DEFAULT_VEHICLE_ENTITY_MAP))
    existing = next((item for item in entries if item.get("entity_id") == entity_id), {}) if entity_id else {}
    role_default = existing.get("role", VEHICLE_ROLE_OTHER)
    return vol.Schema(
        {
            vol.Required(UI_VEHICLE_ENTITY, default=entity_id or existing.get("entity_id", "")): _any_entity_selector(),
            vol.Required(UI_VEHICLE_ROLE, default=role_default): _vehicle_role_selector(),
            vol.Optional(UI_VEHICLE_LABEL, default=existing.get("label", VEHICLE_ROLE_LABELS.get(role_default, ""))): str,
            vol.Required(UI_VEHICLE_USE_REPORT, default=existing.get("use_report", False)): selector.BooleanSelector(),
            vol.Required(UI_VEHICLE_USE_AI, default=existing.get("use_ai", True)): selector.BooleanSelector(),
            vol.Required(UI_VEHICLE_USE_ALERTS, default=existing.get("use_alerts", True)): selector.BooleanSelector(),
            vol.Required(UI_VEHICLE_USE_MAP, default=existing.get("use_map", role_default == VEHICLE_ROLE_LOCATION_TRACKER)): selector.BooleanSelector(),
            vol.Required(UI_AFTER_SAVING, default=ACTION_RETURN_TO_MENU): _after_saving_selector(),
        }
    )


def build_vehicle_entity_remove_schema(current: dict[str, Any]) -> vol.Schema:
    """Build remove vehicle entity schema."""
    entries = normalize_vehicle_entity_map(current.get(CONF_VEHICLE_ENTITY_MAP, DEFAULT_VEHICLE_ENTITY_MAP))
    options = [
        {"value": item["entity_id"], "label": f"{VEHICLE_ROLE_LABELS.get(item.get('role'), item.get('role'))}: {item['entity_id']}"}
        for item in entries
    ] or [{"value": "", "label": "No vehicle entity entries"}]
    return vol.Schema(
        {
            vol.Required(UI_REMOVE_VEHICLE_ENTITY, default=options[0]["value"]): selector.SelectSelector(
                selector.SelectSelectorConfig(options=options, mode=selector.SelectSelectorMode.DROPDOWN)
            ),
            vol.Required(UI_AFTER_SAVING, default=ACTION_RETURN_TO_MENU): _after_saving_selector(),
        }
    )


def build_vehicle_entity_show_schema(current: dict[str, Any]) -> vol.Schema:
    """Build vehicle entity map summary schema."""
    entries = normalize_vehicle_entity_map(current.get(CONF_VEHICLE_ENTITY_MAP, DEFAULT_VEHICLE_ENTITY_MAP))
    return vol.Schema(
        {
            vol.Optional(UI_VEHICLE_ENTITY_SUMMARY, default=build_vehicle_entity_summary(entries)): _multiline_text_selector(),
            vol.Required(UI_AFTER_SAVING, default=ACTION_RETURN_TO_MENU): _after_saving_selector(),
        }
    )


def build_vehicle_entity_review_schema(current: dict[str, Any]) -> vol.Schema:
    """Build final Vehicle Entity Manager review schema with clearer grouping."""
    entries = normalize_vehicle_entity_map(current.get(CONF_VEHICLE_ENTITY_MAP, DEFAULT_VEHICLE_ENTITY_MAP))

    report_roles = [
        VEHICLE_ROLE_BATTERY_LEVEL,
        VEHICLE_ROLE_ENERGY_REMAINING,
        VEHICLE_ROLE_SPEED,
        VEHICLE_ROLE_SHIFT_STATE,
        VEHICLE_ROLE_ODOMETER,
        VEHICLE_ROLE_ELEVATION,
        VEHICLE_ROLE_CLIMATE,
        VEHICLE_ROLE_CHARGING_STATE,
        VEHICLE_ROLE_CHARGE_ENERGY_ADDED,
        VEHICLE_ROLE_LOCATION_TRACKER,
    ]

    def _entries_for(role: str, use_key: str | None = None) -> list[dict[str, Any]]:
        result = [item for item in entries if item.get("role") == role]
        if use_key:
            result = [item for item in result if item.get(use_key)]
        return result

    def _line_for_item(item: dict[str, Any]) -> str:
        entity_id = item.get("entity_id", "-")
        role = VEHICLE_ROLE_LABELS.get(item.get("role"), item.get("role", "Other"))
        label = item.get("label") or role
        uses = []
        if item.get("use_report"):
            uses.append("Report")
        if item.get("use_ai"):
            uses.append("AI")
        if item.get("use_alerts"):
            uses.append("Alerts")
        if item.get("use_map"):
            uses.append("Map")
        use_text = ", ".join(uses) if uses else "-"
        return f"✅ {entity_id}\n   {label} · {role} · {use_text}"

    role_categories = {
        "BATARYA / ŞARJ": {
            VEHICLE_ROLE_BATTERY_LEVEL,
            VEHICLE_ROLE_ENERGY_REMAINING,
            VEHICLE_ROLE_BATTERY_RANGE,
            VEHICLE_ROLE_CHARGING_STATE,
            VEHICLE_ROLE_CHARGE_ENERGY_ADDED,
            VEHICLE_ROLE_CHARGER_POWER,
            VEHICLE_ROLE_BATTERY_TEMPERATURE,
        },
        "SÜRÜŞ / HAREKET": {
            VEHICLE_ROLE_SPEED,
            VEHICLE_ROLE_SHIFT_STATE,
            VEHICLE_ROLE_ODOMETER,
            VEHICLE_ROLE_ELEVATION,
        },
        "KONUM / ROTA": {VEHICLE_ROLE_LOCATION_TRACKER},
        "KLİMA / SICAKLIK": {
            VEHICLE_ROLE_CLIMATE,
            VEHICLE_ROLE_INSIDE_TEMPERATURE,
            VEHICLE_ROLE_OUTSIDE_TEMPERATURE,
        },
        "LASTİKLER": {
            VEHICLE_ROLE_TIRE_PRESSURE_FRONT_LEFT,
            VEHICLE_ROLE_TIRE_PRESSURE_FRONT_RIGHT,
            VEHICLE_ROLE_TIRE_PRESSURE_REAR_LEFT,
            VEHICLE_ROLE_TIRE_PRESSURE_REAR_RIGHT,
        },
        "GÜVENLİK / KAPILAR": {
            VEHICLE_ROLE_DOOR_WINDOW,
            VEHICLE_ROLE_LOCK_STATE,
        },
    }

    lines = [
        "POM VEHICLE ENTITY MANAGER ÖZETİ",
        "",
        "VEHICLE REPORT ENTITIES",
        "Rapor, tüketim hesabı ve harita için kullanılan temel roller:",
        "",
    ]

    ready_count = 0
    for role in report_roles:
        role_entries = _entries_for(role, "use_report")
        label = VEHICLE_ROLE_LABELS.get(role, role)
        if role_entries:
            ready_count += 1
            lines.append(f"✅ {label}")
            lines.append(f"   {role_entries[0].get('entity_id')}")
        else:
            lines.append(f"⚠️ {label}")
            lines.append("   seçilmemiş")

    ai_entities = [item for item in entries if item.get("use_ai")]
    alert_entities = [item for item in entries if item.get("use_alerts")]
    map_entities = [item for item in entries if item.get("use_map")]

    lines.extend([
        "",
        f"Report readiness: {ready_count}/{len(report_roles)}",
        "",
        "AI ENTITIES",
        "AI'nın ekstra okuyacağı entity'ler kategori bazlı:",
    ])

    rendered_ids: set[str] = set()
    for category, roles in role_categories.items():
        category_items = [item for item in ai_entities if item.get("role") in roles]
        if not category_items:
            continue
        lines.extend(["", category])
        for item in category_items[:60]:
            rendered_ids.add(str(item.get("entity_id")))
            lines.append(_line_for_item(item))

    other_ai_items = [item for item in ai_entities if str(item.get("entity_id")) not in rendered_ids]
    if other_ai_items:
        lines.extend(["", "DİĞER AI VERİLERİ"])
        for item in other_ai_items[:80]:
            lines.append(_line_for_item(item))

    excluded = current.get(CONF_AI_EXCLUDED_CONTEXT_ENTITIES, DEFAULT_AI_EXCLUDED_CONTEXT_ENTITIES) or []
    if isinstance(excluded, str):
        excluded = [excluded]

    lines.extend([
        "",
        "EXCLUDED ENTITIES",
    ])
    if excluded:
        lines.extend([f"❌ {str(x)}" for x in excluded])
    else:
        lines.append("-")

    lines.extend([
        "",
        "COUNTS",
        f"Report: {sum(1 for item in entries if item.get('use_report'))}",
        f"AI: {len(ai_entities)}",
        f"Alerts: {len(alert_entities)}",
        f"Map: {len(map_entities)}",
        "",
        "Not: Selected AI entities listesinden X ile kaldırdığın entity AI tarafından okunmaz. Exclude listesi ise Auto Find tekrar çalışsa bile o entity'nin geri gelmesini engeller.",
    ])

    return vol.Schema(
        {
            vol.Optional(UI_VEHICLE_ENTITY_SUMMARY, default="\n".join(lines)): _multiline_text_selector(),
            vol.Required(UI_AFTER_SAVING, default=ACTION_RETURN_TO_MENU): _after_saving_selector(),
        }
    )

class PomTeslaReportConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for POM Tesla Report."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return PomTeslaReportOptionsFlow()

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Handle the initial setup step."""
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id("pom_tesla_report_main")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=build_schema(),
            errors=errors,
        )


class PomTeslaReportOptionsFlow(config_entries.OptionsFlow):
    """Handle POM Tesla Report options."""

    def __init__(self) -> None:
        """Initialize pending options storage for multi-step editing."""
        self._pending_options: dict[str, Any] | None = None

    def _current(self) -> dict[str, Any]:
        """Return current pending options, or merged entry data and options."""
        if self._pending_options is not None:
            return dict(self._pending_options)

        return {
            **dict(self.config_entry.data),
            **dict(self.config_entry.options),
        }

    def _update_pending(self, updates: dict[str, Any]) -> None:
        """Update pending OptionsFlow data while preserving existing values."""
        current = self._current()
        current.update(updates)
        self._pending_options = current

    def _finish(self):
        """Save pending options and close the Options flow."""
        return self.async_create_entry(
            title="",
            data=self._current(),
        )

    async def _save_or_return(
        self,
        updates: dict[str, Any],
        action: str,
    ):
        """Save pending changes and either return to menu or close."""
        self._update_pending(updates)

        if action == ACTION_SAVE_AND_CLOSE:
            return self._finish()

        return await self.async_step_init()

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Show a compact Options section picker."""
        errors: dict[str, str] = {}

        if user_input is not None:
            section = user_input.get(UI_SETTINGS_SECTION)

            if section == SECTION_CORE_VEHICLE:
                return await self.async_step_core_vehicle()

            if section == SECTION_VEHICLE_ENTITY_MANAGER:
                return await self.async_step_vehicle_entity_manager()

            if section == SECTION_AUTOMATION_TELEGRAM:
                return await self.async_step_automation_telegram()

            if section == SECTION_PRICES_REPORT:
                return await self.async_step_prices_report()

            if section == SECTION_LIVE_TRIP:
                return await self.async_step_live_trip()

            if section == SECTION_AI_BASIC:
                return await self.async_step_ai_basic()

            if section == SECTION_AI_ALERTS:
                return await self.async_step_ai_alerts()

            if section == SECTION_FINISH:
                return self._finish()

            errors[UI_SETTINGS_SECTION] = "invalid_section"

        return self.async_show_form(
            step_id="init",
            data_schema=build_options_menu_schema(),
            errors=errors,
        )

    def _vehicle_entry_from_entity(
        self,
        entity_id: str,
        *,
        source: str,
        role: str | None = None,
    ) -> dict[str, Any] | None:
        """Build a Vehicle Entity Manager entry from an entity id."""
        entity_id = str(entity_id or "").strip()
        if not entity_id:
            return None

        state = self.hass.states.get(entity_id)
        friendly = ""
        if state is not None:
            friendly = str(state.attributes.get("friendly_name") or "")

        if not friendly:
            try:
                registry = er.async_get(self.hass)
                reg_entry = registry.async_get(entity_id)
                if reg_entry:
                    friendly = str(reg_entry.name or reg_entry.original_name or "")
            except Exception:
                friendly = ""

        role_value = role or infer_vehicle_role(entity_id, friendly)
        if role_value not in VEHICLE_ENTITY_ROLES:
            role_value = VEHICLE_ROLE_OTHER

        use_report_roles = {
            VEHICLE_ROLE_BATTERY_LEVEL,
            VEHICLE_ROLE_ENERGY_REMAINING,
            VEHICLE_ROLE_CHARGING_STATE,
            VEHICLE_ROLE_CHARGE_ENERGY_ADDED,
            VEHICLE_ROLE_SPEED,
            VEHICLE_ROLE_SHIFT_STATE,
            VEHICLE_ROLE_ODOMETER,
            VEHICLE_ROLE_ELEVATION,
            VEHICLE_ROLE_CLIMATE,
        }
        use_map_roles = {VEHICLE_ROLE_LOCATION_TRACKER}
        alert_roles = {
            VEHICLE_ROLE_BATTERY_LEVEL,
            VEHICLE_ROLE_CHARGING_STATE,
            VEHICLE_ROLE_BATTERY_TEMPERATURE,
            VEHICLE_ROLE_TIRE_PRESSURE_FRONT_LEFT,
            VEHICLE_ROLE_TIRE_PRESSURE_FRONT_RIGHT,
            VEHICLE_ROLE_TIRE_PRESSURE_REAR_LEFT,
            VEHICLE_ROLE_TIRE_PRESSURE_REAR_RIGHT,
            VEHICLE_ROLE_DOOR_WINDOW,
            VEHICLE_ROLE_LOCK_STATE,
            VEHICLE_ROLE_USER_PRESENT,
        }

        return {
            "entity_id": entity_id,
            "role": role_value,
            "label": friendly or VEHICLE_ROLE_LABELS.get(role_value, role_value),
            "use_report": role_value in use_report_roles,
            "use_ai": True,
            "use_alerts": role_value in alert_roles,
            "use_map": role_value in use_map_roles,
            "source": source,
        }

    def _merge_vehicle_entries(
        self,
        base_entries: list[dict[str, Any]],
        new_entries: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Merge vehicle entity entries by entity_id, preserving manual entries when possible."""
        merged: dict[str, dict[str, Any]] = {}

        for item in normalize_vehicle_entity_map(base_entries):
            entity_id = item.get("entity_id")
            if entity_id:
                merged[entity_id] = item

        for item in normalize_vehicle_entity_map(new_entries):
            entity_id = item.get("entity_id")
            if not entity_id:
                continue
            if entity_id in merged and merged[entity_id].get("source") == "manual":
                continue
            if entity_id in merged:
                current = merged[entity_id]
                current.update({k: v for k, v in item.items() if v not in [None, ""]})
                merged[entity_id] = current
            else:
                merged[entity_id] = item

        return list(merged.values())

    def _legacy_vehicle_seed_entries(self, current: dict[str, Any]) -> list[dict[str, Any]]:
        """Seed central vehicle manager from legacy report/entity options."""
        seeds: list[dict[str, Any]] = []
        legacy_pairs = [
            (current.get(CONF_BATTERY_LEVEL_ENTITY), VEHICLE_ROLE_BATTERY_LEVEL),
            (current.get(CONF_ENERGY_REMAINING_ENTITY), VEHICLE_ROLE_ENERGY_REMAINING),
            (current.get(CONF_CHARGING_ENTITY), VEHICLE_ROLE_CHARGING_STATE),
            (current.get(CONF_CHARGE_ENERGY_ADDED_ENTITY), VEHICLE_ROLE_CHARGE_ENERGY_ADDED),
            (current.get(CONF_SPEED_ENTITY), VEHICLE_ROLE_SPEED),
            (current.get(CONF_SHIFT_STATE_ENTITY), VEHICLE_ROLE_SHIFT_STATE),
            (current.get(CONF_ODOMETER_ENTITY), VEHICLE_ROLE_ODOMETER),
            (current.get(CONF_ELEVATION_ENTITY), VEHICLE_ROLE_ELEVATION),
            (current.get(CONF_CLIMATE_ENTITY), VEHICLE_ROLE_CLIMATE),
            (current.get(CONF_TRIP_MAP_TRACKER_ENTITY), VEHICLE_ROLE_LOCATION_TRACKER),
        ]
        for entity_id, role in legacy_pairs:
            entry = self._vehicle_entry_from_entity(entity_id, source="legacy_seed", role=role)
            if entry:
                seeds.append(entry)
        return seeds

    def _smart_discovered_vehicle_entries(self, current: dict[str, Any]) -> list[dict[str, Any]]:
        """Discover entities from the same HA device as the selected main Tesla entity."""
        main_entity = str(current.get(CONF_AI_MAIN_TESLA_ENTITY) or "").strip()
        if not main_entity:
            main_entity = str(current.get(CONF_BATTERY_LEVEL_ENTITY) or DEFAULT_BATTERY_LEVEL_ENTITY).strip()

        discovered: list[dict[str, Any]] = []
        registry = er.async_get(self.hass)
        main_reg_entry = registry.async_get(main_entity)
        device_id = getattr(main_reg_entry, "device_id", None) if main_reg_entry else None

        if device_id:
            for reg_entry in registry.entities.values():
                if getattr(reg_entry, "device_id", None) != device_id:
                    continue
                entity_id = getattr(reg_entry, "entity_id", "")
                friendly = str(reg_entry.name or reg_entry.original_name or "")
                role = infer_vehicle_role(entity_id, friendly)
                if role == VEHICLE_ROLE_OTHER:
                    # Keep useful unknowns visible for AI, but don't flood with every diagnostic entity.
                    text = f"{entity_id} {friendly}".lower()
                    if not any(k in text for k in ["tesla", "pom", "tessie", "battery", "charge", "tire", "tyre", "pressure", "temperature", "window", "door", "lock", "range", "speed", "odometer", "climate", "gps", "location"]):
                        continue
                entry = self._vehicle_entry_from_entity(entity_id, source="smart_import", role=role)
                if entry:
                    discovered.append(entry)
        else:
            # Fallback: use legacy configured entities if device registry cannot resolve the main entity.
            discovered.extend(self._legacy_vehicle_seed_entries(current))

        # Put important roles first for readable summaries and max limits downstream.
        priority = {
            VEHICLE_ROLE_BATTERY_LEVEL: 10,
            VEHICLE_ROLE_ENERGY_REMAINING: 20,
            VEHICLE_ROLE_BATTERY_RANGE: 30,
            VEHICLE_ROLE_CHARGING_STATE: 40,
            VEHICLE_ROLE_CHARGE_ENERGY_ADDED: 50,
            VEHICLE_ROLE_CHARGER_POWER: 60,
            VEHICLE_ROLE_SHIFT_STATE: 70,
            VEHICLE_ROLE_SPEED: 80,
            VEHICLE_ROLE_ODOMETER: 90,
            VEHICLE_ROLE_LOCATION_TRACKER: 100,
            VEHICLE_ROLE_CLIMATE: 110,
            VEHICLE_ROLE_INSIDE_TEMPERATURE: 120,
            VEHICLE_ROLE_OUTSIDE_TEMPERATURE: 130,
            VEHICLE_ROLE_BATTERY_TEMPERATURE: 140,
            VEHICLE_ROLE_TIRE_PRESSURE_FRONT_LEFT: 150,
            VEHICLE_ROLE_TIRE_PRESSURE_FRONT_RIGHT: 151,
            VEHICLE_ROLE_TIRE_PRESSURE_REAR_LEFT: 152,
            VEHICLE_ROLE_TIRE_PRESSURE_REAR_RIGHT: 153,
            VEHICLE_ROLE_DOOR_WINDOW: 160,
            VEHICLE_ROLE_LOCK_STATE: 170,
            VEHICLE_ROLE_USER_PRESENT: 180,
            VEHICLE_ROLE_OTHER: 999,
        }
        discovered.sort(key=lambda item: (priority.get(item.get("role"), 999), item.get("entity_id", "")))
        return discovered

    def _vehicle_manager_report_entries_from_input(self, user_input: dict[str, Any]) -> list[dict[str, Any]]:
        """Build report role entries from the one-page Vehicle Entity Manager form."""
        report_map = [
            (UI_REPORT_BATTERY_LEVEL_ENTITY, VEHICLE_ROLE_BATTERY_LEVEL, "Battery level"),
            (UI_REPORT_ENERGY_REMAINING_ENTITY, VEHICLE_ROLE_ENERGY_REMAINING, "Energy remaining"),
            (UI_REPORT_SPEED_ENTITY, VEHICLE_ROLE_SPEED, "Speed"),
            (UI_REPORT_SHIFT_STATE_ENTITY, VEHICLE_ROLE_SHIFT_STATE, "Shift state"),
            (UI_REPORT_ODOMETER_ENTITY, VEHICLE_ROLE_ODOMETER, "Odometer"),
            (UI_REPORT_ELEVATION_ENTITY, VEHICLE_ROLE_ELEVATION, "Elevation"),
            (UI_REPORT_CLIMATE_ENTITY, VEHICLE_ROLE_CLIMATE, "Climate"),
            (UI_REPORT_CHARGING_ENTITY, VEHICLE_ROLE_CHARGING_STATE, "Charging state"),
            (UI_REPORT_CHARGE_ENERGY_ADDED_ENTITY, VEHICLE_ROLE_CHARGE_ENERGY_ADDED, "Charge energy added"),
            (UI_REPORT_LOCATION_TRACKER_ENTITY, VEHICLE_ROLE_LOCATION_TRACKER, "Location tracker"),
            (UI_REPORT_VEHICLE_STATE_ENTITY, VEHICLE_ROLE_VEHICLE_STATE, "Vehicle state / sleep status"),
        ]
        entries: list[dict[str, Any]] = []
        for ui_key, role, label in report_map:
            entity_id = str(user_input.get(ui_key) or "").strip()
            if not entity_id:
                continue
            entries.append({
                "entity_id": entity_id,
                "role": role,
                "label": label,
                "use_report": role != VEHICLE_ROLE_LOCATION_TRACKER or True,
                "use_ai": True,
                "use_alerts": role in {
                    VEHICLE_ROLE_BATTERY_LEVEL,
                    VEHICLE_ROLE_CHARGING_STATE,
                },
                "use_map": role == VEHICLE_ROLE_LOCATION_TRACKER,
                "source": "report_form",
            })
        return entries

    def _vehicle_manager_ai_entries_from_input(self, user_input: dict[str, Any]) -> list[dict[str, Any]]:
        """Build AI-only entries from the one-page Vehicle Entity Manager form."""
        raw = user_input.get(UI_VEHICLE_AI_ENTITIES) or []
        if isinstance(raw, str):
            raw = [raw]
        entries: list[dict[str, Any]] = []
        for entity_id in raw:
            entity_id = str(entity_id or "").strip()
            if not entity_id:
                continue
            entry = self._vehicle_entry_from_entity(entity_id, source="manual_ai")
            if not entry:
                continue
            entry["use_report"] = False
            entry["use_ai"] = True
            entry["use_alerts"] = entry.get("role") in {
                VEHICLE_ROLE_BATTERY_LEVEL,
                VEHICLE_ROLE_CHARGING_STATE,
                VEHICLE_ROLE_BATTERY_TEMPERATURE,
                VEHICLE_ROLE_TIRE_PRESSURE_FRONT_LEFT,
                VEHICLE_ROLE_TIRE_PRESSURE_FRONT_RIGHT,
                VEHICLE_ROLE_TIRE_PRESSURE_REAR_LEFT,
                VEHICLE_ROLE_TIRE_PRESSURE_REAR_RIGHT,
                VEHICLE_ROLE_DOOR_WINDOW,
                VEHICLE_ROLE_LOCK_STATE,
                VEHICLE_ROLE_USER_PRESENT,
            }
            entries.append(entry)
        return entries

    def _build_vehicle_manager_discovered_summary(self, discovered: list[dict[str, Any]], excluded: list[str]) -> str:
        """Return readable preview of auto-discovered entities."""
        if not discovered:
            return "Auto select ile henüz entity bulunamadı. Main Tesla entity ayarını kontrol et."
        excluded_set = {str(x).strip() for x in excluded if str(x).strip()}
        lines = ["AUTO DISCOVERED ENTITIES", ""]
        for item in discovered[:120]:
            entity_id = item.get("entity_id", "")
            role = VEHICLE_ROLE_LABELS.get(item.get("role"), item.get("role", "Other"))
            label = item.get("label") or role
            prefix = "EXCLUDED" if entity_id in excluded_set else "OK"
            lines.append(f"{prefix} · {entity_id}")
            lines.append(f"  Role: {role} | {label}")
        if len(discovered) > 120:
            lines.append(f"... +{len(discovered) - 120} entity daha")
        return "\n".join(lines)

    async def async_step_vehicle_entity_manager(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Manage the single Vehicle Entity Manager page."""
        errors: dict[str, str] = {}
        current = self._current()

        try:
            discovered = self._smart_discovered_vehicle_entries(current)
        except Exception:
            discovered = []

        if user_input is not None:
            action = user_input.get(UI_VEHICLE_MANAGER_ACTION, ACTION_VEHICLE_SAVE_REVIEW)

            excluded_raw = user_input.get(UI_VEHICLE_EXCLUDED_ENTITIES) or []
            if isinstance(excluded_raw, str):
                excluded_entities = [excluded_raw] if excluded_raw else []
            else:
                excluded_entities = [str(x).strip() for x in excluded_raw if str(x).strip()]
            excluded_set = set(excluded_entities)

            # AI entities are shown as selected entity boxes. Auto select fills this field;
            # the user can remove unwanted entities with the X button or blacklist them via Exclude.
            temp_current = dict(current)
            temp_current[CONF_AI_MAIN_TESLA_ENTITY] = user_input.get(UI_AI_MAIN_TESLA_ENTITY) or current.get(CONF_AI_MAIN_TESLA_ENTITY, DEFAULT_AI_MAIN_TESLA_ENTITY)

            if action == ACTION_VEHICLE_AUTO_SELECT_AI:
                try:
                    discovered = self._smart_discovered_vehicle_entries(temp_current)
                except Exception:
                    discovered = []

                discovered_ids = [
                    str(item.get("entity_id") or "").strip()
                    for item in discovered
                    if str(item.get("entity_id") or "").strip()
                    and str(item.get("entity_id") or "").strip() not in excluded_set
                ]
                selected_raw = user_input.get(UI_VEHICLE_AI_ENTITIES) or []
                if isinstance(selected_raw, str):
                    selected_raw = [selected_raw]

                combined_ai_entities = []
                for entity_id in list(selected_raw) + discovered_ids:
                    entity_id = str(entity_id or "").strip()
                    if entity_id and entity_id not in excluded_set and entity_id not in combined_ai_entities:
                        combined_ai_entities.append(entity_id)

                report_entries = self._vehicle_manager_report_entries_from_input(user_input)
                ai_entries = []
                for entity_id in combined_ai_entities:
                    entry = self._vehicle_entry_from_entity(entity_id, source="auto_selected_ai")
                    if entry:
                        entry["use_report"] = False
                        entry["use_ai"] = True
                        entry["use_alerts"] = entry.get("role") in {
                            VEHICLE_ROLE_BATTERY_LEVEL,
                            VEHICLE_ROLE_CHARGING_STATE,
                            VEHICLE_ROLE_BATTERY_TEMPERATURE,
                            VEHICLE_ROLE_TIRE_PRESSURE_FRONT_LEFT,
                            VEHICLE_ROLE_TIRE_PRESSURE_FRONT_RIGHT,
                            VEHICLE_ROLE_TIRE_PRESSURE_REAR_LEFT,
                            VEHICLE_ROLE_TIRE_PRESSURE_REAR_RIGHT,
                            VEHICLE_ROLE_DOOR_WINDOW,
                            VEHICLE_ROLE_LOCK_STATE,
                            VEHICLE_ROLE_USER_PRESENT,
                        }
                        entry["use_map"] = entry.get("role") == VEHICLE_ROLE_LOCATION_TRACKER
                        ai_entries.append(entry)

                # Preserve custom manually-added entries that are not report roles and not excluded.
                existing_entries = normalize_vehicle_entity_map(current.get(CONF_VEHICLE_ENTITY_MAP, DEFAULT_VEHICLE_ENTITY_MAP))
                custom_entries = [
                    item for item in existing_entries
                    if item.get("source") not in {"auto_selected_ai", "report"}
                    and str(item.get("entity_id") or "").strip() not in excluded_set
                ]

                merged = self._merge_vehicle_entries([], report_entries + ai_entries + custom_entries)
                self._update_pending({
                    CONF_VEHICLE_ENTITY_MAP: normalize_vehicle_entity_map(merged),
                    CONF_AI_EXTRA_CONTEXT_ENTITIES: combined_ai_entities,
                    CONF_AI_MAIN_TESLA_ENTITY: temp_current.get(CONF_AI_MAIN_TESLA_ENTITY),
                    CONF_AI_EXCLUDED_CONTEXT_ENTITIES: excluded_entities,
                    CONF_BATTERY_LEVEL_ENTITY: user_input.get(UI_REPORT_BATTERY_LEVEL_ENTITY),
                    CONF_ENERGY_REMAINING_ENTITY: user_input.get(UI_REPORT_ENERGY_REMAINING_ENTITY),
                    CONF_SPEED_ENTITY: user_input.get(UI_REPORT_SPEED_ENTITY),
                    CONF_SHIFT_STATE_ENTITY: user_input.get(UI_REPORT_SHIFT_STATE_ENTITY),
                    CONF_ODOMETER_ENTITY: user_input.get(UI_REPORT_ODOMETER_ENTITY),
                    CONF_ELEVATION_ENTITY: user_input.get(UI_REPORT_ELEVATION_ENTITY),
                    CONF_CLIMATE_ENTITY: user_input.get(UI_REPORT_CLIMATE_ENTITY),
                    CONF_CHARGING_ENTITY: user_input.get(UI_REPORT_CHARGING_ENTITY),
                    CONF_CHARGE_ENERGY_ADDED_ENTITY: user_input.get(UI_REPORT_CHARGE_ENERGY_ADDED_ENTITY),
                    CONF_TRIP_MAP_TRACKER_ENTITY: user_input.get(UI_REPORT_LOCATION_TRACKER_ENTITY),
                    CONF_REVERSE_GEOCODING_ENABLED: user_input.get(UI_REVERSE_GEOCODING_ENABLED),
                    CONF_REVERSE_GEOCODING_CACHE_MINUTES: user_input.get(UI_REVERSE_GEOCODING_CACHE_MINUTES),
                    CONF_REVERSE_GEOCODING_USE_IN_AI: user_input.get(UI_REVERSE_GEOCODING_USE_IN_AI),
                })
                return await self.async_step_vehicle_entity_manager()

            report_entries = self._vehicle_manager_report_entries_from_input(user_input)
            selected_ai_entries = [
                item for item in self._vehicle_manager_ai_entries_from_input(user_input)
                if str(item.get("entity_id") or "").strip() not in excluded_set
            ]
            merged = self._merge_vehicle_entries([], report_entries + selected_ai_entries)
            selected_ai_entities = [item.get("entity_id") for item in selected_ai_entries if item.get("entity_id")]

            updates = {
                CONF_VEHICLE_ENTITY_MAP: normalize_vehicle_entity_map(merged),
                CONF_AI_EXTRA_CONTEXT_ENTITIES: selected_ai_entities,
                CONF_AI_MAIN_TESLA_ENTITY: temp_current.get(CONF_AI_MAIN_TESLA_ENTITY),
                CONF_AI_EXCLUDED_CONTEXT_ENTITIES: excluded_entities,
                CONF_BATTERY_LEVEL_ENTITY: user_input.get(UI_REPORT_BATTERY_LEVEL_ENTITY),
                CONF_ENERGY_REMAINING_ENTITY: user_input.get(UI_REPORT_ENERGY_REMAINING_ENTITY),
                CONF_SPEED_ENTITY: user_input.get(UI_REPORT_SPEED_ENTITY),
                CONF_SHIFT_STATE_ENTITY: user_input.get(UI_REPORT_SHIFT_STATE_ENTITY),
                CONF_ODOMETER_ENTITY: user_input.get(UI_REPORT_ODOMETER_ENTITY),
                CONF_ELEVATION_ENTITY: user_input.get(UI_REPORT_ELEVATION_ENTITY),
                CONF_CLIMATE_ENTITY: user_input.get(UI_REPORT_CLIMATE_ENTITY),
                CONF_CHARGING_ENTITY: user_input.get(UI_REPORT_CHARGING_ENTITY),
                CONF_CHARGE_ENERGY_ADDED_ENTITY: user_input.get(UI_REPORT_CHARGE_ENERGY_ADDED_ENTITY),
                CONF_TRIP_MAP_TRACKER_ENTITY: user_input.get(UI_REPORT_LOCATION_TRACKER_ENTITY),
                    CONF_REVERSE_GEOCODING_ENABLED: user_input.get(UI_REVERSE_GEOCODING_ENABLED),
                    CONF_REVERSE_GEOCODING_CACHE_MINUTES: user_input.get(UI_REVERSE_GEOCODING_CACHE_MINUTES),
                    CONF_REVERSE_GEOCODING_USE_IN_AI: user_input.get(UI_REVERSE_GEOCODING_USE_IN_AI),
            }

            self._update_pending(updates)

            if action == ACTION_SAVE_AND_CLOSE:
                return self._finish()
            if action == ACTION_RETURN_TO_MENU:
                return await self.async_step_init()
            return await self.async_step_vehicle_entity_review()

        return self.async_show_form(
            step_id="vehicle_entity_manager",
            data_schema=build_vehicle_entity_manager_schema(current, ""),
            errors=errors,
        )

    async def async_step_vehicle_entity_review(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Show Vehicle Entity Manager summary after saving selections."""
        errors: dict[str, str] = {}

        if user_input is not None:
            action = user_input.get(UI_AFTER_SAVING, ACTION_RETURN_TO_MENU)
            if action == ACTION_SAVE_AND_CLOSE:
                return self._finish()
            return await self.async_step_init()

        return self.async_show_form(
            step_id="vehicle_entity_review",
            data_schema=build_vehicle_entity_review_schema(self._current()),
            errors=errors,
        )

    async def async_step_vehicle_entity_add(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Add or update a central vehicle entity entry."""
        errors: dict[str, str] = {}

        if user_input is not None:
            action = user_input.get(UI_AFTER_SAVING, ACTION_RETURN_TO_MENU)
            entity_id = str(user_input.get(UI_VEHICLE_ENTITY) or "").strip()
            role = str(user_input.get(UI_VEHICLE_ROLE) or VEHICLE_ROLE_OTHER).strip()
            if not entity_id:
                errors[UI_VEHICLE_ENTITY] = "required"
            else:
                current = self._current()
                entries = normalize_vehicle_entity_map(current.get(CONF_VEHICLE_ENTITY_MAP, DEFAULT_VEHICLE_ENTITY_MAP))
                entries = [item for item in entries if item.get("entity_id") != entity_id]
                entries.append({
                    "entity_id": entity_id,
                    "role": role if role in VEHICLE_ENTITY_ROLES else VEHICLE_ROLE_OTHER,
                    "label": str(user_input.get(UI_VEHICLE_LABEL) or VEHICLE_ROLE_LABELS.get(role, role)).strip(),
                    "use_report": bool(user_input.get(UI_VEHICLE_USE_REPORT, False)),
                    "use_ai": bool(user_input.get(UI_VEHICLE_USE_AI, True)),
                    "use_alerts": bool(user_input.get(UI_VEHICLE_USE_ALERTS, True)),
                    "use_map": bool(user_input.get(UI_VEHICLE_USE_MAP, False)),
                    "source": "manual",
                })
                self._update_pending({CONF_VEHICLE_ENTITY_MAP: normalize_vehicle_entity_map(entries)})
                if action == ACTION_SAVE_AND_CLOSE:
                    return self._finish()
                return await self.async_step_vehicle_entity_manager()

        return self.async_show_form(
            step_id="vehicle_entity_add",
            data_schema=build_vehicle_entity_add_schema(self._current()),
            errors=errors,
        )

    async def async_step_vehicle_entity_remove(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Remove a central vehicle entity entry."""
        errors: dict[str, str] = {}

        if user_input is not None:
            action = user_input.get(UI_AFTER_SAVING, ACTION_RETURN_TO_MENU)
            remove_entity = str(user_input.get(UI_REMOVE_VEHICLE_ENTITY) or "").strip()
            current = self._current()
            entries = normalize_vehicle_entity_map(current.get(CONF_VEHICLE_ENTITY_MAP, DEFAULT_VEHICLE_ENTITY_MAP))
            if remove_entity:
                entries = [item for item in entries if item.get("entity_id") != remove_entity]
            self._update_pending({CONF_VEHICLE_ENTITY_MAP: entries})
            if action == ACTION_SAVE_AND_CLOSE:
                return self._finish()
            return await self.async_step_vehicle_entity_manager()

        return self.async_show_form(
            step_id="vehicle_entity_remove",
            data_schema=build_vehicle_entity_remove_schema(self._current()),
            errors=errors,
        )

    async def async_step_vehicle_entity_show(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Show current central vehicle entity map."""
        errors: dict[str, str] = {}

        if user_input is not None:
            action = user_input.get(UI_AFTER_SAVING, ACTION_RETURN_TO_MENU)
            if action == ACTION_SAVE_AND_CLOSE:
                return self._finish()
            return await self.async_step_vehicle_entity_manager()

        return self.async_show_form(
            step_id="vehicle_entity_show",
            data_schema=build_vehicle_entity_show_schema(self._current()),
            errors=errors,
        )

    async def async_step_core_vehicle(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Manage core and vehicle entity options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            action = user_input.get(UI_AFTER_SAVING, ACTION_RETURN_TO_MENU)
            updates = _map_ui_input(
                user_input,
                {
                    UI_NAME: CONF_NAME,
                    UI_SHIFT_STATE_ENTITY: CONF_SHIFT_STATE_ENTITY,
                    UI_SPEED_ENTITY: CONF_SPEED_ENTITY,
                    UI_ODOMETER_ENTITY: CONF_ODOMETER_ENTITY,
                    UI_BATTERY_LEVEL_ENTITY: CONF_BATTERY_LEVEL_ENTITY,
                    UI_ENERGY_REMAINING_ENTITY: CONF_ENERGY_REMAINING_ENTITY,
                    UI_ELEVATION_ENTITY: CONF_ELEVATION_ENTITY,
                    UI_CLIMATE_ENTITY: CONF_CLIMATE_ENTITY,
                    UI_CHARGING_ENTITY: CONF_CHARGING_ENTITY,
                    UI_CHARGE_ENERGY_ADDED_ENTITY: CONF_CHARGE_ENERGY_ADDED_ENTITY,
                },
            )
            return await self._save_or_return(updates, action)

        return self.async_show_form(
            step_id="core_vehicle",
            data_schema=build_core_vehicle_schema(self._current()),
            errors=errors,
        )

    async def async_step_automation_telegram(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Manage automation and Telegram options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            action = user_input.get(UI_AFTER_SAVING, ACTION_RETURN_TO_MENU)
            updates = _map_ui_input(
                user_input,
                {
                    UI_AUTO_TRIP_TRACKING: CONF_AUTO_TRIP_TRACKING,
                    UI_AUTO_START_SPEED_THRESHOLD: CONF_AUTO_START_SPEED_THRESHOLD,
                    UI_TELEGRAM_TARGET: CONF_TELEGRAM_TARGET,
                    UI_TRIP_MAP_ENABLED: CONF_TRIP_MAP_ENABLED,
                    UI_TRIP_MAP_TRACKER_ENTITY: CONF_TRIP_MAP_TRACKER_ENTITY,
                    UI_TRIP_MAP_SAMPLE_INTERVAL_SECONDS: CONF_TRIP_MAP_SAMPLE_INTERVAL_SECONDS,
                    UI_TRIP_MAP_MIN_MOVEMENT_METERS: CONF_TRIP_MAP_MIN_MOVEMENT_METERS,
                    UI_TRIP_MAP_SEND_SEPARATE_PNG: CONF_TRIP_MAP_SEND_SEPARATE_PNG,
                },
            )
            return await self._save_or_return(updates, action)

        return self.async_show_form(
            step_id="automation_telegram",
            data_schema=build_automation_telegram_schema(self._current()),
            errors=errors,
        )

    async def async_step_prices_report(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Manage charging prices and report layout options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            action = user_input.get(UI_AFTER_SAVING, ACTION_RETURN_TO_MENU)
            updates = _map_ui_input(
                user_input,
                {
                    UI_SUPERCHARGER_PRICE: CONF_SUPERCHARGER_PRICE,
                    UI_ZES_PRICE: CONF_ZES_PRICE,
                    UI_ASTOR_PRICE: CONF_ASTOR_PRICE,
                    UI_CHARGING_REPORT_MODE: CONF_CHARGING_REPORT_MODE,
                    UI_SHOW_DISTANCE: CONF_SHOW_DISTANCE,
                    UI_SHOW_DURATION: CONF_SHOW_DURATION,
                    UI_SHOW_TRAFFIC: CONF_SHOW_TRAFFIC,
                    UI_SHOW_AVERAGE_SPEED: CONF_SHOW_AVERAGE_SPEED,
                    UI_SHOW_ENERGY: CONF_SHOW_ENERGY,
                    UI_SHOW_CONSUMPTION: CONF_SHOW_CONSUMPTION,
                    UI_SHOW_BATTERY: CONF_SHOW_BATTERY,
                    UI_SHOW_COST: CONF_SHOW_COST,
                    UI_SHOW_CLIMATE: CONF_SHOW_CLIMATE,
                    UI_SHOW_ELEVATION: CONF_SHOW_ELEVATION,
                },
            )
            return await self._save_or_return(updates, action)

        return self.async_show_form(
            step_id="prices_report",
            data_schema=build_prices_report_schema(self._current()),
            errors=errors,
        )

    async def async_step_live_trip(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Manage live trip calculation options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            action = user_input.get(UI_AFTER_SAVING, ACTION_RETURN_TO_MENU)
            updates = _map_ui_input(
                user_input,
                {
                    UI_LIVE_TRIP_ENABLED: CONF_LIVE_TRIP_ENABLED,
                    UI_LIVE_TRIP_UPDATE_INTERVAL_SECONDS: CONF_LIVE_TRIP_UPDATE_INTERVAL_SECONDS,
                    UI_LIVE_TRIP_TRAFFIC_SPEED_THRESHOLD: CONF_LIVE_TRIP_TRAFFIC_SPEED_THRESHOLD,
                    UI_LIVE_TRIP_FINISH_DELAY_SECONDS: CONF_LIVE_TRIP_FINISH_DELAY_SECONDS,
                    UI_LIVE_TRIP_MIN_DISTANCE_KM: CONF_LIVE_TRIP_MIN_DISTANCE_KM,
                },
            )
            return await self._save_or_return(updates, action)

        return self.async_show_form(
            step_id="live_trip",
            data_schema=build_live_trip_schema(self._current()),
            errors=errors,
        )

    async def async_step_ai_basic(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Manage POM AI Basic options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            action = user_input.get(UI_AFTER_SAVING, ACTION_RETURN_TO_MENU)
            updates = _map_ui_input(
                user_input,
                {
                    UI_AI_ENABLED: CONF_AI_ENABLED,
                    UI_AI_PERSONALITY: CONF_AI_PERSONALITY,
                    UI_AI_ANSWER_LENGTH: CONF_AI_ANSWER_LENGTH,
                    UI_AI_CONTEXT_MODE: CONF_AI_CONTEXT_MODE,
                    UI_AI_AUTO_DISCOVER_DEVICE_ENTITIES: CONF_AI_AUTO_DISCOVER_DEVICE_ENTITIES,
                    UI_AI_INCLUDE_UNAVAILABLE: CONF_AI_INCLUDE_UNAVAILABLE,
                    UI_AI_MAX_CONTEXT_ENTITIES: CONF_AI_MAX_CONTEXT_ENTITIES,
                    UI_AI_EXTRA_CONTEXT_ENTITIES: CONF_AI_EXTRA_CONTEXT_ENTITIES,
                    UI_AI_EXCLUDED_CONTEXT_ENTITIES: CONF_AI_EXCLUDED_CONTEXT_ENTITIES,
                    UI_OPENAI_MODEL: CONF_OPENAI_MODEL,
                    UI_AI_TELEGRAM_TARGET: CONF_AI_TELEGRAM_TARGET,
                    UI_AI_SYSTEM_PROMPT: CONF_AI_SYSTEM_PROMPT,
                    UI_AI_MAX_OUTPUT_TOKENS: CONF_AI_MAX_OUTPUT_TOKENS,
                    UI_AI_TELEGRAM_LISTENER_ENABLED: CONF_AI_TELEGRAM_LISTENER_ENABLED,
                    UI_AI_TELEGRAM_LISTENER_CHAT_ID: CONF_AI_TELEGRAM_LISTENER_CHAT_ID,
                    UI_AI_TELEGRAM_ALLOWED_USER_ID: CONF_AI_TELEGRAM_ALLOWED_USER_ID,
                    UI_AI_TELEGRAM_INCLUDE_CONTEXT: CONF_AI_TELEGRAM_INCLUDE_CONTEXT,
                    UI_AI_CONFIRM_OPTIONAL_CONTROLS: CONF_AI_CONFIRM_OPTIONAL_CONTROLS,
                },
            )

            # Password fields are intentionally not pre-filled by Home Assistant.
            # If the user leaves the API key field blank, keep the previously saved key.
            new_api_key = str(user_input.get(UI_OPENAI_API_KEY, "")).strip()
            if new_api_key:
                updates[CONF_OPENAI_API_KEY] = new_api_key

            return await self._save_or_return(updates, action)

        return self.async_show_form(
            step_id="ai_basic",
            data_schema=build_ai_basic_schema(self._current()),
            errors=errors,
        )



    async def async_step_ai_alerts(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Manage AI Alerts & Watchers options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            action = user_input.get(UI_AFTER_SAVING, ACTION_RETURN_TO_MENU)
            updates = _map_ui_input(
                user_input,
                {
                    UI_AI_ALERTS_ENABLED: CONF_AI_ALERTS_ENABLED,
                    UI_AI_ALERT_STYLE: CONF_AI_ALERT_STYLE,
                    UI_AI_ALERT_COOLDOWN_MINUTES: CONF_AI_ALERT_COOLDOWN_MINUTES,
                    UI_AI_ALERT_LOW_BATTERY_ENABLED: CONF_AI_ALERT_LOW_BATTERY_ENABLED,
                    UI_AI_ALERT_CHARGE_FINISHED_ENABLED: CONF_AI_ALERT_CHARGE_FINISHED_ENABLED,
                    UI_AI_ALERT_CHARGING_STOPPED_ENABLED: CONF_AI_ALERT_CHARGING_STOPPED_ENABLED,
                    UI_AI_ALERT_TIRE_PRESSURE_ENABLED: CONF_AI_ALERT_TIRE_PRESSURE_ENABLED,
                    UI_AI_ALERT_TIRE_PRESSURE_THRESHOLD_BAR: CONF_AI_ALERT_TIRE_PRESSURE_THRESHOLD_BAR,
                    UI_AI_ALERT_HIGH_BATTERY_TEMP_ENABLED: CONF_AI_ALERT_HIGH_BATTERY_TEMP_ENABLED,
                    UI_AI_ALERT_HIGH_BATTERY_TEMP_THRESHOLD_C: CONF_AI_ALERT_HIGH_BATTERY_TEMP_THRESHOLD_C,
                    UI_AI_ALERT_UNLOCKED_ENABLED: CONF_AI_ALERT_UNLOCKED_ENABLED,
                    UI_AI_ALERT_UNLOCKED_DELAY_MINUTES: CONF_AI_ALERT_UNLOCKED_DELAY_MINUTES,
                    UI_AI_ALERT_DOOR_WINDOW_OPEN_ENABLED: CONF_AI_ALERT_DOOR_WINDOW_OPEN_ENABLED,
                    UI_AI_ALERT_DOOR_WINDOW_OPEN_DELAY_MINUTES: CONF_AI_ALERT_DOOR_WINDOW_OPEN_DELAY_MINUTES,
                },
            )
            return await self._save_or_return(updates, action)

        return self.async_show_form(
            step_id="ai_alerts",
            data_schema=build_ai_alerts_schema(self._current()),
            errors=errors,
        )
