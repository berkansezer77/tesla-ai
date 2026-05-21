"""Config flow for POM Tesla Report."""

from __future__ import annotations

import json

from typing import Any

import voluptuous as vol

from aiohttp import ClientError

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession


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
    CONF_BUILTIN_TELEGRAM_ENABLED,
    CONF_BUILTIN_TELEGRAM_BOT_TOKEN,
    CONF_BUILTIN_TELEGRAM_POLL_ENABLED,
    CONF_BUILTIN_TELEGRAM_POLL_INTERVAL_SECONDS,
    CONF_AUTO_TRIP_TRACKING,
    CONF_AUTO_START_SPEED_THRESHOLD,
    DEFAULT_SUPERCHARGER_PRICE,
    DEFAULT_ZES_PRICE,
    DEFAULT_ASTOR_PRICE,
    DEFAULT_AUTO_TRIP_TRACKING,
    DEFAULT_AUTO_START_SPEED_THRESHOLD,
    DEFAULT_BUILTIN_TELEGRAM_ENABLED,
    DEFAULT_BUILTIN_TELEGRAM_POLL_ENABLED,
    DEFAULT_BUILTIN_TELEGRAM_POLL_INTERVAL_SECONDS,
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
    CONF_SHOW_TRIP_MAP,
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
    DEFAULT_SHOW_TRIP_MAP,
    CONF_AI_ENABLED,
    CONF_OPENAI_API_KEY,
    CONF_OPENAI_MODEL,
    CONF_AI_TELEGRAM_TARGET,
    CONF_AI_NAME,
    CONF_AI_SYSTEM_PROMPT,
    CONF_AI_MAX_OUTPUT_TOKENS,
    CONF_AI_TELEGRAM_LISTENER_ENABLED,
    CONF_AI_TELEGRAM_LISTENER_CHAT_ID,
    CONF_AI_TELEGRAM_ALLOWED_USER_ID,
    CONF_AI_TELEGRAM_INCLUDE_CONTEXT,
    CONF_AI_CONFIRM_OPTIONAL_CONTROLS,
    DEFAULT_AI_ENABLED,
    DEFAULT_OPENAI_MODEL,
    DEFAULT_AI_NAME,
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
SECTION_AI_ENTITY_MANAGER = "ai_entity_manager"
SECTION_REPORTS_ENTITY_MANAGER = "reports_entity_manager"
SECTION_AUTOMATION_TELEGRAM = "automation_telegram"
SECTION_PRICES_REPORT = "prices_report"
SECTION_CHARGING_REPORTS = "charging_reports"
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
UI_REPORT_MAIN_TESLA_ENTITY = "Sample Tesla entity for report auto-discovery"
UI_REPORT_BATTERY_LEVEL_ENTITY = "Vehicle report - Battery level"
UI_REPORT_ENERGY_REMAINING_ENTITY = "Vehicle report - Energy remaining"
UI_REPORT_SPEED_ENTITY = "Vehicle report - Speed"
UI_REPORT_SHIFT_STATE_ENTITY = "Vehicle report - Shift state"
UI_REPORT_ODOMETER_ENTITY = "Vehicle report - Odometer"
UI_REPORT_ELEVATION_ENTITY = "Vehicle report - Elevation"
UI_REPORT_CLIMATE_ENTITY = "Vehicle report - Climate"
UI_REPORT_CHARGING_ENTITY = "Vehicle report - Charging state"
UI_REPORT_CHARGE_ENERGY_ADDED_ENTITY = "Vehicle report - Charge energy added"
UI_REPORT_LOCATION_TRACKER_ENTITY = "Vehicle report - Location tracker / map"
UI_REPORT_VEHICLE_STATE_ENTITY = "Vehicle report - Vehicle state / sleep status"
UI_VEHICLE_AI_ENTITIES = "AI entities / extra vehicle data"
UI_AI_BATTERY_LEVEL_ENTITY = "AI context - Battery level"
UI_AI_ENERGY_REMAINING_ENTITY = "AI context - Energy remaining"
UI_AI_BATTERY_RANGE_ENTITY = "AI context - Battery range"
UI_AI_CHARGING_ENTITY = "AI context - Charging state"
UI_AI_CHARGE_ENERGY_ADDED_ENTITY = "AI context - Charge energy added"
UI_AI_CHARGER_POWER_ENTITY = "AI context - Charger power"
UI_AI_SPEED_ENTITY = "AI context - Speed"
UI_AI_SHIFT_STATE_ENTITY = "AI context - Shift state"
UI_AI_ODOMETER_ENTITY = "AI context - Odometer"
UI_AI_ELEVATION_ENTITY = "AI context - Elevation"
UI_AI_LOCATION_TRACKER_ENTITY = "AI context - Location tracker"
UI_AI_CLIMATE_ENTITY = "AI context - Climate"
UI_AI_INSIDE_TEMPERATURE_ENTITY = "AI context - Inside temperature"
UI_AI_OUTSIDE_TEMPERATURE_ENTITY = "AI context - Outside temperature"
UI_AI_BATTERY_TEMPERATURE_ENTITY = "AI context - Battery temperature"
UI_AI_LOCK_STATE_ENTITY = "AI control/context - Lock state"
UI_AI_DOOR_WINDOW_ENTITY = "AI control/context - Door / window state"
UI_AI_VEHICLE_STATE_ENTITY = "AI context - Vehicle state / sleep status"
UI_AI_USER_PRESENT_ENTITY = "AI context - User present / occupancy"
UI_AI_TIRE_PRESSURE_FRONT_LEFT_ENTITY = "AI alerts - Tire pressure front left"
UI_AI_TIRE_PRESSURE_FRONT_RIGHT_ENTITY = "AI alerts - Tire pressure front right"
UI_AI_TIRE_PRESSURE_REAR_LEFT_ENTITY = "AI alerts - Tire pressure rear left"
UI_AI_TIRE_PRESSURE_REAR_RIGHT_ENTITY = "AI alerts - Tire pressure rear right"
UI_AI_CONTROLS_NOTE = "AI control fields help"
UI_AI_HONK_HORN_ENTITY = "AI control - Horn"
UI_AI_FLASH_LIGHTS_ENTITY = "AI control - Flash lights"
UI_AI_WAKE_VEHICLE_ENTITY = "AI control - Wake vehicle"
UI_AI_CLIMATE_CONTROL_ENTITY = "AI control - Climate control"
UI_AI_DEFROST_ENTITY = "AI control - Defrost mode"
UI_AI_SENTRY_ENTITY = "AI control - Sentry mode"
UI_AI_CHARGE_CONTROL_ENTITY = "AI control - Charge start / stop"
UI_AI_CHARGE_PORT_ENTITY = "AI control - Charge port door"
UI_AI_CHARGE_CABLE_LOCK_ENTITY = "AI control - Charge cable lock"
UI_AI_VEHICLE_LOCK_CONTROL_ENTITY = "AI control - Vehicle lock / unlock"
UI_AI_VENT_WINDOWS_ENTITY = "AI control - Vent / close windows"
UI_AI_TRUNK_ENTITY = "AI control - Trunk"
UI_AI_FRUNK_ENTITY = "AI control - Frunk"
UI_AI_HOMELINK_ENTITY = "AI control - HomeLink / garage trigger"
UI_AI_PLAY_FART_ENTITY = "AI control - Play fart"
UI_AI_KEYLESS_DRIVING_ENTITY = "AI control - Keyless driving / remote start"
UI_AI_VALET_ENTITY = "AI control - Valet mode"
UI_AI_STEERING_WHEEL_HEATER_ENTITY = "AI control - Steering wheel heater"
UI_AI_MEDIA_PLAYER_ENTITY = "AI control - Media player"
UI_AI_SEAT_HEATER_FRONT_LEFT_ENTITY = "AI control - Front left seat heater"
UI_AI_SEAT_HEATER_FRONT_RIGHT_ENTITY = "AI control - Front right seat heater"
UI_AI_SEAT_HEATER_REAR_LEFT_ENTITY = "AI control - Rear left seat heater"
UI_AI_SEAT_HEATER_REAR_CENTER_ENTITY = "AI control - Rear center seat heater"
UI_AI_SEAT_HEATER_REAR_RIGHT_ENTITY = "AI control - Rear right seat heater"
UI_AI_OTHER_ENTITIES = "AI context - Other / extra entities"
UI_VEHICLE_AI_ENTITIES_NOTE = "AI entities help"
UI_VEHICLE_EXCLUDED_ENTITIES = "Exclude entities from AI / auto discovery"
UI_VEHICLE_REPORT_SECTION_NOTE = "Vehicle report section"
UI_VEHICLE_AI_SECTION_NOTE = "AI / Auto discovery section"
UI_REPORTS_ENTITY_MANAGER_NOTE = "Reports entity manager help"
UI_AI_ENTITY_MANAGER_NOTE = "AI entity manager help"
UI_AI_CONTROL_FIELDS_NOTE = "AI control and context fields help"
UI_AI_ALERT_FIELDS_NOTE = "AI alert fields help"
UI_TELEGRAM_SETTINGS_NOTE = "Telegram settings help"
UI_AI_SETTINGS_NOTE = "AI settings help"
UI_TRIP_REPORTS_NOTE = "Trip reports help"
UI_CHARGING_REPORTS_NOTE = "Charging reports help"
UI_AUTOMATIONS_NOTE = "Automations and notifications help"

ACTION_RETURN_TO_MENU = "return_to_menu"
ACTION_SAVE_AND_CLOSE = "save_and_close"
ACTION_VEHICLE_AUTO_SELECT_REPORT = "vehicle_auto_select_report"
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
UI_TELEGRAM_REPLIES_ENABLED = "Enable replies"
UI_TELEGRAM_TARGET = "Telegram group ID"
UI_BUILTIN_TELEGRAM_ENABLED = "Use built-in Telegram bot"
UI_BUILTIN_TELEGRAM_BOT_TOKEN = "Telegram bot token"
UI_BUILTIN_TELEGRAM_POLL_ENABLED = "Enable built-in Telegram polling listener"
UI_BUILTIN_TELEGRAM_POLL_INTERVAL_SECONDS = "Built-in Telegram polling interval seconds"
UI_TRIP_MAP_ENABLED = "Enable trip map collection"
UI_TRIP_MAP_TRACKER_ENTITY = "Trip map tracker entity"
UI_TRIP_MAP_SAMPLE_INTERVAL_SECONDS = "Map sample interval seconds"
UI_TRIP_MAP_MIN_MOVEMENT_METERS = "Minimum movement meters"
UI_TRIP_MAP_SEND_SEPARATE_PNG = "Enable map PNG as separate image"

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
UI_SHOW_TRIP_MAP = "Show trip map"

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
UI_AI_NAME = "AI name"
UI_AI_MAIN_TESLA_ENTITY = "Sample Tesla entity for AI auto-discovery"
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
UI_AI_MAX_OUTPUT_TOKENS = "Max output tokens"
UI_AI_TELEGRAM_LISTENER_ENABLED = "Enable Telegram AI group listener"
UI_AI_TELEGRAM_LISTENER_CHAT_ID = "Group ID for listening"
UI_AI_TELEGRAM_ALLOWED_USER_ID = "Allowed Telegram user ID (optional; blank = everyone)"
UI_AI_TELEGRAM_INCLUDE_CONTEXT = "Include Tesla context for group messages"
UI_AI_CONFIRM_OPTIONAL_CONTROLS = "Ask confirmation before sending vehicle controls"
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


AI_CONTROL_FIELD_SPECS = [
    (UI_AI_VEHICLE_LOCK_CONTROL_ENTITY, "Vehicle Lock", VEHICLE_ROLE_LOCK_STATE, ["lock", "unlock", "kilit", "kilidi ac", "kilidi aç", "kapilari kilitle", "kapıları kilitle", "kapilari ac", "kapıları aç"]),
    (UI_AI_HONK_HORN_ENTITY, "Honk Horn", VEHICLE_ROLE_OTHER, ["horn", "honk", "korna"]),
    (UI_AI_FLASH_LIGHTS_ENTITY, "Flash Lights", VEHICLE_ROLE_OTHER, ["flash lights", "flash", "lights", "far", "isik", "ışık"]),
    (UI_AI_WAKE_VEHICLE_ENTITY, "Wake Vehicle", VEHICLE_ROLE_OTHER, ["wake vehicle", "wake", "uyandir", "uyandır", "awake"]),
    (UI_AI_DEFROST_ENTITY, "Defrost Mode", VEHICLE_ROLE_OTHER, ["defrost", "buz", "cam buzu", "defog"]),
    (UI_AI_SENTRY_ENTITY, "Sentry Mode", VEHICLE_ROLE_OTHER, ["sentry"]),
    (UI_AI_CHARGE_CONTROL_ENTITY, "Charge Control", VEHICLE_ROLE_OTHER, ["charge start", "charge stop", "charging start", "charging stop", "sarj baslat", "şarj başlat", "sarj durdur", "şarj durdur"]),
    (UI_AI_CHARGE_PORT_ENTITY, "Charge Port Door", VEHICLE_ROLE_OTHER, ["charge port", "charge door", "sarj port", "şarj port"]),
    (UI_AI_CHARGE_CABLE_LOCK_ENTITY, "Charge Cable Lock", VEHICLE_ROLE_OTHER, ["charge cable", "cable lock", "sarj kablo", "şarj kablo"]),
    (UI_AI_VENT_WINDOWS_ENTITY, "Vent Windows", VEHICLE_ROLE_OTHER, ["vent windows", "window vent", "cam", "window", "pencere"]),
    (UI_AI_TRUNK_ENTITY, "Trunk", VEHICLE_ROLE_OTHER, ["trunk", "bagaj"]),
    (UI_AI_FRUNK_ENTITY, "Frunk", VEHICLE_ROLE_OTHER, ["frunk", "front trunk", "on bagaj", "ön bagaj"]),
    (UI_AI_HOMELINK_ENTITY, "HomeLink", VEHICLE_ROLE_OTHER, ["homelink", "garage", "garaj"]),
    (UI_AI_PLAY_FART_ENTITY, "Play Fart", VEHICLE_ROLE_OTHER, ["fart"]),
    (UI_AI_KEYLESS_DRIVING_ENTITY, "Keyless Driving", VEHICLE_ROLE_OTHER, ["keyless", "remote start", "anahtarsiz", "anahtarsız"]),
    (UI_AI_VALET_ENTITY, "Valet Mode", VEHICLE_ROLE_OTHER, ["valet"]),
    (UI_AI_STEERING_WHEEL_HEATER_ENTITY, "Steering Wheel Heater", VEHICLE_ROLE_OTHER, ["steering wheel heater", "direksiyon isitma", "direksiyon ısıtma"]),
    (UI_AI_MEDIA_PLAYER_ENTITY, "Media Player", VEHICLE_ROLE_OTHER, ["media player", "media", "oynatici", "oynatıcı"]),
    (UI_AI_SEAT_HEATER_FRONT_LEFT_ENTITY, "Front Left Seat Heater", VEHICLE_ROLE_OTHER, ["front left seat heater", "driver seat heater", "on sol koltuk", "ön sol koltuk"]),
    (UI_AI_SEAT_HEATER_FRONT_RIGHT_ENTITY, "Front Right Seat Heater", VEHICLE_ROLE_OTHER, ["front right seat heater", "passenger seat heater", "on sag koltuk", "ön sağ koltuk", "on sağ koltuk"]),
    (UI_AI_SEAT_HEATER_REAR_LEFT_ENTITY, "Rear Left Seat Heater", VEHICLE_ROLE_OTHER, ["rear left seat heater", "arka sol koltuk"]),
    (UI_AI_SEAT_HEATER_REAR_CENTER_ENTITY, "Rear Center Seat Heater", VEHICLE_ROLE_OTHER, ["rear center seat heater", "rear middle seat heater", "arka orta koltuk"]),
    (UI_AI_SEAT_HEATER_REAR_RIGHT_ENTITY, "Rear Right Seat Heater", VEHICLE_ROLE_OTHER, ["rear right seat heater", "arka sag koltuk", "arka sağ koltuk"]),
]

AI_CONTEXT_FIELD_SPECS = [
    (UI_AI_BATTERY_LEVEL_ENTITY, VEHICLE_ROLE_BATTERY_LEVEL),
    (UI_AI_ENERGY_REMAINING_ENTITY, VEHICLE_ROLE_ENERGY_REMAINING),
    (UI_AI_BATTERY_RANGE_ENTITY, VEHICLE_ROLE_BATTERY_RANGE),
    (UI_AI_CHARGING_ENTITY, VEHICLE_ROLE_CHARGING_STATE),
    (UI_AI_CHARGE_ENERGY_ADDED_ENTITY, VEHICLE_ROLE_CHARGE_ENERGY_ADDED),
    (UI_AI_CHARGER_POWER_ENTITY, VEHICLE_ROLE_CHARGER_POWER),
    (UI_AI_SPEED_ENTITY, VEHICLE_ROLE_SPEED),
    (UI_AI_SHIFT_STATE_ENTITY, VEHICLE_ROLE_SHIFT_STATE),
    (UI_AI_ODOMETER_ENTITY, VEHICLE_ROLE_ODOMETER),
    (UI_AI_ELEVATION_ENTITY, VEHICLE_ROLE_ELEVATION),
    (UI_AI_LOCATION_TRACKER_ENTITY, VEHICLE_ROLE_LOCATION_TRACKER),
    (UI_AI_CLIMATE_ENTITY, VEHICLE_ROLE_CLIMATE),
    (UI_AI_INSIDE_TEMPERATURE_ENTITY, VEHICLE_ROLE_INSIDE_TEMPERATURE),
    (UI_AI_OUTSIDE_TEMPERATURE_ENTITY, VEHICLE_ROLE_OUTSIDE_TEMPERATURE),
    (UI_AI_BATTERY_TEMPERATURE_ENTITY, VEHICLE_ROLE_BATTERY_TEMPERATURE),
    (UI_AI_DOOR_WINDOW_ENTITY, VEHICLE_ROLE_DOOR_WINDOW),
    (UI_AI_VEHICLE_STATE_ENTITY, VEHICLE_ROLE_VEHICLE_STATE),
    (UI_AI_USER_PRESENT_ENTITY, VEHICLE_ROLE_USER_PRESENT),
]

AI_ALERT_FIELD_SPECS = [
    (UI_AI_TIRE_PRESSURE_FRONT_LEFT_ENTITY, VEHICLE_ROLE_TIRE_PRESSURE_FRONT_LEFT),
    (UI_AI_TIRE_PRESSURE_FRONT_RIGHT_ENTITY, VEHICLE_ROLE_TIRE_PRESSURE_FRONT_RIGHT),
    (UI_AI_TIRE_PRESSURE_REAR_LEFT_ENTITY, VEHICLE_ROLE_TIRE_PRESSURE_REAR_LEFT),
    (UI_AI_TIRE_PRESSURE_REAR_RIGHT_ENTITY, VEHICLE_ROLE_TIRE_PRESSURE_REAR_RIGHT),
]


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


def infer_vehicle_role(entity_id: str, friendly_name: str = "", metadata_text: str = "") -> str:
    """Infer a vehicle role from an entity id and friendly name."""
    text = f"{entity_id} {friendly_name} {metadata_text}".lower()
    text = text.replace("-", "_").replace(".", "_").replace(" ", "_")
    if any(k in text for k in ["user_present", "presence", "occupancy", "occupied", "occupant", "inside_vehicle", "driver_present", "passenger_present", "iceride"]):
        return VEHICLE_ROLE_USER_PRESENT
    if "device_tracker." in entity_id or any(k in text for k in ["location", "gps", "latitude", "longitude", "drive_state_latitude", "drive_state_longitude"]):
        return VEHICLE_ROLE_LOCATION_TRACKER
    if any(k in text for k in ["battery_module_temperature", "battery_temp", "battery_temperature", "pack_temperature", "pack_temp", "battery_heater"]):
        return VEHICLE_ROLE_BATTERY_TEMPERATURE
    if any(k in text for k in ["outside_temperature", "ambient_temperature", "outside_temp", "exterior_temperature", "external_temperature", "climate_state_outside_temp", "dis_sicaklik"]):
        return VEHICLE_ROLE_OUTSIDE_TEMPERATURE
    if any(k in text for k in ["inside_temperature", "cabin_temperature", "interior_temperature", "inside_temp", "climate_state_inside_temp", "ic_sicaklik"]):
        return VEHICLE_ROLE_INSIDE_TEMPERATURE
    if any(k in text for k in ["front_left", "fl", "on_sol"]) and any(k in text for k in ["tire", "tyre", "pressure", "tpms", "lastik"]):
        return VEHICLE_ROLE_TIRE_PRESSURE_FRONT_LEFT
    if any(k in text for k in ["front_right", "fr", "on_sag"]) and any(k in text for k in ["tire", "tyre", "pressure", "tpms", "lastik"]):
        return VEHICLE_ROLE_TIRE_PRESSURE_FRONT_RIGHT
    if any(k in text for k in ["rear_left", "rl", "arka_sol"]) and any(k in text for k in ["tire", "tyre", "pressure", "tpms", "lastik"]):
        return VEHICLE_ROLE_TIRE_PRESSURE_REAR_LEFT
    if any(k in text for k in ["rear_right", "rr", "arka_sag"]) and any(k in text for k in ["tire", "tyre", "pressure", "tpms", "lastik"]):
        return VEHICLE_ROLE_TIRE_PRESSURE_REAR_RIGHT
    if any(k in text for k in ["tire", "tyre", "pressure", "tpms", "lastik"]):
        return VEHICLE_ROLE_OTHER
    if any(k in text for k in ["battery_level", "state_of_charge", "soc", "usable_battery_level", "charge_state_battery_level"]):
        return VEHICLE_ROLE_BATTERY_LEVEL
    if any(k in text for k in ["battery_range", "rated_range", "ideal_range", "est_battery_range", "range", "menzil"]):
        return VEHICLE_ROLE_BATTERY_RANGE
    if any(k in text for k in ["energy_remaining", "remaining_energy", "kwh_remaining", "usable_energy", "energy_at_arrival", "varista_sarj"]):
        return VEHICLE_ROLE_ENERGY_REMAINING
    if any(k in text for k in ["charge_energy_added", "energy_added", "charge_state_charge_energy_added"]):
        return VEHICLE_ROLE_CHARGE_ENERGY_ADDED
    if any(k in text for k in ["charger_power", "charging_power", "charge_state_charger_power", "charge_state_charge_rate"]):
        return VEHICLE_ROLE_CHARGER_POWER
    if any(k in text for k in ["charging_state", "charge_state_charging_state", "charge_cable", "plugged", "charge_state_conn_charge_cable", "sarj_kablosu"]):
        return VEHICLE_ROLE_CHARGING_STATE
    if "speed" in text or "drive_state_speed" in text or "hiz" in text or "hiz" in text:
        return VEHICLE_ROLE_SPEED
    if any(k in text for k in ["shift", "shift_state", "drive_state_shift_state", "gear", "vites", "kaydirma_durumu"]):
        return VEHICLE_ROLE_SHIFT_STATE
    if "odometer" in text or "vehicle_state_odometer" in text or "kilometre" in text:
        return VEHICLE_ROLE_ODOMETER
    if "elevation" in text or "drive_state_elevation" in text or "rakim" in text or "rakim" in text:
        return VEHICLE_ROLE_ELEVATION
    if "climate." in entity_id or any(k in text for k in ["climate", "hvac", "klima", "iklimlendirme", "climate_state"]):
        return VEHICLE_ROLE_CLIMATE
    if any(k in text for k in ["window", "door", "trunk", "frunk", "cam", "kapi", "kapi"]):
        return VEHICLE_ROLE_DOOR_WINDOW
    if "lock." in entity_id or "lock" in text or "vehicle_state_locked" in text or "kilit" in text:
        return VEHICLE_ROLE_LOCK_STATE
    if any(k in text for k in ["vehicle_state_state", "drive_state_active_route", "car_state", "online", "asleep", "durum"]):
        return VEHICLE_ROLE_VEHICLE_STATE
    return VEHICLE_ROLE_OTHER


def _extract_openai_response_text(response_data: dict[str, Any]) -> str:
    """Extract assistant text from an OpenAI Responses API payload."""
    output = response_data.get("output")
    if isinstance(output, list):
        parts: list[str] = []
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for part in content:
                if not isinstance(part, dict):
                    continue
                text = part.get("text")
                if isinstance(text, str) and text.strip():
                    parts.append(text.strip())
        if parts:
            return "\n".join(parts).strip()
    return str(response_data.get("output_text") or "").strip()


def _parse_json_object_from_text(text: str) -> dict[str, Any]:
    """Parse a JSON object from model text, tolerating fenced output."""
    raw = str(text or "").strip()
    if not raw:
        return {}
    if raw.startswith("```"):
        raw = raw.strip("`").strip()
        if raw.lower().startswith("json"):
            raw = raw[4:].strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        raw = raw[start : end + 1]
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


async def _async_call_openai_for_config_flow(
    hass,
    *,
    api_key: str,
    model: str,
    system_prompt: str,
    user_message: str,
    max_output_tokens: int = 1200,
) -> str:
    """Call OpenAI from Options flow for setup assistance."""
    session = async_get_clientsession(hass)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "input": [
            {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
            {"role": "user", "content": [{"type": "input_text", "text": user_message}]},
        ],
        "max_output_tokens": max_output_tokens,
    }
    try:
        async with session.post(
            "https://api.openai.com/v1/responses",
            headers=headers,
            json=payload,
            timeout=60,
        ) as response:
            response_data = await response.json(content_type=None)
            if response.status >= 400:
                return ""
    except ClientError:
        return ""
    return _extract_openai_response_text(response_data)


def build_vehicle_entity_summary(entries: list[dict[str, Any]]) -> str:
    """Return compact summary for Options UI."""
    if not entries:
        return "No central entity records yet. Run Smart import first."
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
        lines.append(f"... +{len(entries)-60} more records")
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
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _normalized_supported_ai_personality(value: Any) -> str:
    """Normalize removed legacy personality values to a supported current option."""
    supported = {
        AI_PERSONALITY_PROFESSIONAL,
        AI_PERSONALITY_FRIENDLY,
        AI_PERSONALITY_FUNNY,
        AI_PERSONALITY_SHORT_DIRECT,
    }
    value = str(value or "").strip()
    if value in supported:
        return value
    return DEFAULT_AI_PERSONALITY


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
            unit_of_measurement="C",
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
                {"value": SECTION_AI_ENTITY_MANAGER, "label": "01 - AI Entity Manager"},
                {"value": SECTION_REPORTS_ENTITY_MANAGER, "label": "02 - Reports Entity Manager"},
                {"value": SECTION_AUTOMATION_TELEGRAM, "label": "03 - Telegram Settings"},
                {"value": SECTION_AI_BASIC, "label": "04 - AI Settings"},
                {"value": SECTION_PRICES_REPORT, "label": "05 - Trip Reports"},
                {"value": SECTION_CHARGING_REPORTS, "label": "06 - Charging Reports"},
                {"value": SECTION_LIVE_TRIP, "label": "07 - Live Trip Settings"},
                {"value": SECTION_AI_ALERTS, "label": "08 - Automations and notifications"},
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
                {"value": ACTION_VEHICLE_AUTO_SELECT_REPORT, "label": "Find report entities from selected Tesla device"},
                {"value": ACTION_VEHICLE_AUTO_SELECT_AI, "label": "Find AI entities from selected Tesla device"},
                {"value": ACTION_VEHICLE_SAVE_REVIEW, "label": "Save and show summary"},
                {"value": ACTION_RETURN_TO_MENU, "label": "Save and return to main menu"},
                {"value": ACTION_SAVE_AND_CLOSE, "label": "Save and close"},
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )




def _ai_entity_manager_action_selector() -> selector.SelectSelector:
    """Return actions for the AI Entity Manager form."""
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                {"value": ACTION_VEHICLE_AUTO_SELECT_AI, "label": "Find AI entities automatically"},
                {"value": ACTION_VEHICLE_SAVE_REVIEW, "label": "Save and show summary"},
                {"value": ACTION_RETURN_TO_MENU, "label": "Save and return to main menu"},
                {"value": ACTION_SAVE_AND_CLOSE, "label": "Save and close"},
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _reports_entity_manager_action_selector() -> selector.SelectSelector:
    """Return actions for the Reports Entity Manager form."""
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                {"value": ACTION_VEHICLE_AUTO_SELECT_REPORT, "label": "Find report entities automatically"},
                {"value": ACTION_VEHICLE_SAVE_REVIEW, "label": "Save and show summary"},
                {"value": ACTION_RETURN_TO_MENU, "label": "Save and return to main menu"},
                {"value": ACTION_SAVE_AND_CLOSE, "label": "Save and close"},
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )

def _coerce_decimal(value: Any) -> Any:
    """Accept decimal values with either comma or dot separators."""
    if isinstance(value, str):
        text = value.strip().replace(",", ".")
        if not text:
            return value
        try:
            return float(text)
        except ValueError:
            return value
    return value

def _map_ui_input(
    user_input: dict[str, Any],
    field_map: dict[str, str],
) -> dict[str, Any]:
    """Map human-readable UI keys back to stored config option keys."""
    decimal_fields = {CONF_SUPERCHARGER_PRICE, CONF_ZES_PRICE, CONF_ASTOR_PRICE}
    mapped: dict[str, Any] = {}
    for ui_key, stored_key in field_map.items():
        if ui_key not in user_input:
            continue
        value = user_input[ui_key]
        if stored_key in decimal_fields:
            value = _coerce_decimal(value)
        mapped[stored_key] = value
    return mapped



def build_initial_setup_schema(current: dict[str, Any] | None = None) -> vol.Schema:
    """Build the minimal first-run setup form."""
    current = current or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_NAME,
                default=current.get(CONF_NAME, DEFAULT_NAME),
            ): str,
        }
    )

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
                default=SECTION_AI_ENTITY_MANAGER,
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
                return str(item.get("entity_id") or "").strip() or "-"
        if legacy_key:
            return str(current.get(legacy_key) or "-")
        return "-"

    lines = [
        "This section does not select entities again. Live trip calculation uses the selections from Reports Entity Manager.",
        "",
        f"Speed: {role_entity(VEHICLE_ROLE_SPEED, CONF_SPEED_ENTITY)}",
        f"Shift state: {role_entity(VEHICLE_ROLE_SHIFT_STATE, CONF_SHIFT_STATE_ENTITY)}",
        f"Odometer: {role_entity(VEHICLE_ROLE_ODOMETER, CONF_ODOMETER_ENTITY)}",
        f"Energy remaining: {role_entity(VEHICLE_ROLE_ENERGY_REMAINING, CONF_ENERGY_REMAINING_ENTITY)}",
        f"Battery level: {role_entity(VEHICLE_ROLE_BATTERY_LEVEL, CONF_BATTERY_LEVEL_ENTITY)}",
        f"Climate: {role_entity(VEHICLE_ROLE_CLIMATE, CONF_CLIMATE_ENTITY)}",
        f"Elevation: {role_entity(VEHICLE_ROLE_ELEVATION, CONF_ELEVATION_ENTITY)}",
        "",
        "If an entity is missing or incorrect, fix it from Reports Entity Manager.",
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
    """Build Telegram settings schema."""
    group_id = current.get(
        CONF_AI_TELEGRAM_LISTENER_CHAT_ID,
        current.get(CONF_AI_TELEGRAM_TARGET, current.get(CONF_TELEGRAM_TARGET, DEFAULT_TELEGRAM_TARGET)),
    )
    return vol.Schema(
        {
            vol.Optional(
                UI_TELEGRAM_SETTINGS_NOTE,
                default=(
                    "Use one shared Telegram group for replies and group listening. "
                    "You can either keep using Home Assistant's Telegram integration or enable the built-in Telegram bot mode below. "
                    "If replies are enabled, AI answers and report messages use the same group ID."
                ),
            ): _multiline_text_selector(),

            vol.Required(
                UI_BUILTIN_TELEGRAM_ENABLED,
                default=current.get(CONF_BUILTIN_TELEGRAM_ENABLED, DEFAULT_BUILTIN_TELEGRAM_ENABLED),
            ): selector.BooleanSelector(),

            vol.Optional(
                UI_BUILTIN_TELEGRAM_BOT_TOKEN,
                default=current.get(CONF_BUILTIN_TELEGRAM_BOT_TOKEN, ""),
            ): str,

            vol.Required(
                UI_BUILTIN_TELEGRAM_POLL_ENABLED,
                default=current.get(CONF_BUILTIN_TELEGRAM_POLL_ENABLED, DEFAULT_BUILTIN_TELEGRAM_POLL_ENABLED),
            ): selector.BooleanSelector(),

            vol.Required(
                UI_BUILTIN_TELEGRAM_POLL_INTERVAL_SECONDS,
                default=current.get(CONF_BUILTIN_TELEGRAM_POLL_INTERVAL_SECONDS, DEFAULT_BUILTIN_TELEGRAM_POLL_INTERVAL_SECONDS),
            ): _seconds_selector(),

            vol.Required(
                UI_TELEGRAM_REPLIES_ENABLED,
                default=(
                    bool(str(current.get(CONF_TELEGRAM_TARGET) or current.get(CONF_AI_TELEGRAM_TARGET) or "").strip())
                    if (CONF_TELEGRAM_TARGET in current or CONF_AI_TELEGRAM_TARGET in current)
                    else True
                ),
            ): selector.BooleanSelector(),

            vol.Optional(
                UI_TELEGRAM_TARGET,
                default=group_id,
            ): str,

            vol.Required(
                UI_AI_TELEGRAM_LISTENER_ENABLED,
                default=current.get(CONF_AI_TELEGRAM_LISTENER_ENABLED, DEFAULT_AI_TELEGRAM_LISTENER_ENABLED),
            ): selector.BooleanSelector(),

            vol.Required(
                UI_AFTER_SAVING,
                default=ACTION_RETURN_TO_MENU,
            ): _after_saving_selector(),
        }
    )


def build_trip_reports_schema(current: dict[str, Any]) -> vol.Schema:
    """Build trip reports and map options schema."""
    return vol.Schema(
        {
            vol.Optional(
                UI_TRIP_REPORTS_NOTE,
                default=(
                    "This section controls automatic trip tracking, trip map collection, report layout, "
                    "and charging prices used inside trip cost cards."
                ),
            ): _multiline_text_selector(),

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
                UI_SHOW_TRIP_MAP,
                default=current.get(CONF_SHOW_TRIP_MAP, DEFAULT_SHOW_TRIP_MAP),
            ): selector.BooleanSelector(),

            vol.Required(
                UI_AFTER_SAVING,
                default=ACTION_RETURN_TO_MENU,
            ): _after_saving_selector(),
        }
    )


def build_charging_reports_schema(current: dict[str, Any]) -> vol.Schema:
    """Build charging report delivery schema."""
    return vol.Schema(
        {
            vol.Optional(
                UI_CHARGING_REPORTS_NOTE,
                default=(
                    "This section controls how charging reports are sent after a charging session finishes."
                ),
            ): _multiline_text_selector(),

            vol.Required(
                UI_CHARGING_REPORT_MODE,
                default=current.get(CONF_CHARGING_REPORT_MODE, DEFAULT_CHARGING_REPORT_MODE),
            ): _charging_report_mode_selector(),

            vol.Required(
                UI_AFTER_SAVING,
                default=ACTION_RETURN_TO_MENU,
            ): _after_saving_selector(),
        }
    )



def build_ai_basic_schema(current: dict[str, Any]) -> vol.Schema:
    """Build AI settings schema."""
    return vol.Schema(
        {
            vol.Optional(
                UI_AI_SETTINGS_NOTE,
                default=(
                    "This section controls AI behavior, OpenAI connection, address understanding, "
                    "and how AI responds in Telegram groups."
                ),
            ): _multiline_text_selector(),

            vol.Required(
                UI_AI_ENABLED,
                default=current.get(CONF_AI_ENABLED, DEFAULT_AI_ENABLED),
            ): selector.BooleanSelector(),

            vol.Required(
                UI_AI_PERSONALITY,
                default=_normalized_supported_ai_personality(current.get(CONF_AI_PERSONALITY, DEFAULT_AI_PERSONALITY)),
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
                UI_AI_NAME,
                default=current.get(CONF_AI_NAME, DEFAULT_AI_NAME),
            ): str,


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

            vol.Required(
                UI_AI_MAX_OUTPUT_TOKENS,
                default=current.get(CONF_AI_MAX_OUTPUT_TOKENS, DEFAULT_AI_MAX_OUTPUT_TOKENS),
            ): _max_output_tokens_selector(),

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
            vol.Optional(
                UI_AUTOMATIONS_NOTE,
                default=(
                    "These switches control proactive AI alerts and vehicle notifications sent by the integration."
                ),
            ): _multiline_text_selector(),

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


def get_entity_for_role(entries: list[dict[str, Any]], role: str, fallback: str = "") -> str | None:
    """Return the first entity id for a role, preferring report-enabled entries."""
    for item in entries:
        if item.get("role") == role and item.get("use_report"):
            entity_id = str(item.get("entity_id") or fallback).strip()
            return entity_id or None
    for item in entries:
        if item.get("role") == role:
            entity_id = str(item.get("entity_id") or fallback).strip()
            return entity_id or None
    fallback = str(fallback or "").strip()
    return fallback or None


def get_entity_for_label(entries: list[dict[str, Any]], label: str, fallback: str = "") -> str | None:
    """Return the first entity id for an exact stored label."""
    target = str(label or "").strip().casefold()
    if not target:
        fallback = str(fallback or "").strip()
        return fallback or None
    for item in entries:
        if str(item.get("label") or "").strip().casefold() == target:
            entity_id = str(item.get("entity_id") or fallback).strip()
            return entity_id or None
    fallback = str(fallback or "").strip()
    return fallback or None

def _optional_entity_key(label: str, value: str) -> vol.Optional:
    """Return an optional selector key without an invalid empty default."""
    value = str(value or "").strip()
    if value:
        return vol.Optional(label, default=value)
    return vol.Optional(label)



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
                    "This section defines the main vehicle data used for trip reports, consumption, and maps. "
                    "The fields below are the primary report data sources."
                ),
            ): _multiline_text_selector(),

            vol.Optional(
                UI_AI_MAIN_TESLA_ENTITY,
                default=current.get(
                    CONF_AI_MAIN_TESLA_ENTITY,
                    get_entity_for_role(entries, VEHICLE_ROLE_BATTERY_LEVEL, current.get(CONF_BATTERY_LEVEL_ENTITY, DEFAULT_BATTERY_LEVEL_ENTITY)),
                ),
            ): _any_entity_selector(),

            _optional_entity_key(UI_REPORT_BATTERY_LEVEL_ENTITY, get_entity_for_role(entries, VEHICLE_ROLE_BATTERY_LEVEL, current.get(CONF_BATTERY_LEVEL_ENTITY, DEFAULT_BATTERY_LEVEL_ENTITY))): _entity_selector("sensor"),

            _optional_entity_key(UI_REPORT_ENERGY_REMAINING_ENTITY, get_entity_for_role(entries, VEHICLE_ROLE_ENERGY_REMAINING, current.get(CONF_ENERGY_REMAINING_ENTITY, DEFAULT_ENERGY_REMAINING_ENTITY))): _entity_selector("sensor"),

            _optional_entity_key(UI_REPORT_SPEED_ENTITY, get_entity_for_role(entries, VEHICLE_ROLE_SPEED, current.get(CONF_SPEED_ENTITY, DEFAULT_SPEED_ENTITY))): _entity_selector("sensor"),

            _optional_entity_key(UI_REPORT_SHIFT_STATE_ENTITY, get_entity_for_role(entries, VEHICLE_ROLE_SHIFT_STATE, current.get(CONF_SHIFT_STATE_ENTITY, DEFAULT_SHIFT_STATE_ENTITY))): _entity_selector("sensor"),

            _optional_entity_key(UI_REPORT_ODOMETER_ENTITY, get_entity_for_role(entries, VEHICLE_ROLE_ODOMETER, current.get(CONF_ODOMETER_ENTITY, DEFAULT_ODOMETER_ENTITY))): _entity_selector("sensor"),

            _optional_entity_key(UI_REPORT_ELEVATION_ENTITY, get_entity_for_role(entries, VEHICLE_ROLE_ELEVATION, current.get(CONF_ELEVATION_ENTITY, DEFAULT_ELEVATION_ENTITY))): _entity_selector("sensor"),

            _optional_entity_key(UI_REPORT_CLIMATE_ENTITY, get_entity_for_role(entries, VEHICLE_ROLE_CLIMATE, current.get(CONF_CLIMATE_ENTITY, DEFAULT_CLIMATE_ENTITY))): _entity_selector("climate"),

            _optional_entity_key(UI_REPORT_CHARGING_ENTITY, get_entity_for_role(entries, VEHICLE_ROLE_CHARGING_STATE, current.get(CONF_CHARGING_ENTITY, DEFAULT_CHARGING_ENTITY))): _any_entity_selector(),

            _optional_entity_key(UI_REPORT_CHARGE_ENERGY_ADDED_ENTITY, get_entity_for_role(entries, VEHICLE_ROLE_CHARGE_ENERGY_ADDED, current.get(CONF_CHARGE_ENERGY_ADDED_ENTITY, DEFAULT_CHARGE_ENERGY_ADDED_ENTITY))): _entity_selector("sensor"),

            _optional_entity_key(UI_REPORT_LOCATION_TRACKER_ENTITY, get_entity_for_role(entries, VEHICLE_ROLE_LOCATION_TRACKER, current.get(CONF_TRIP_MAP_TRACKER_ENTITY, DEFAULT_TRIP_MAP_TRACKER_ENTITY))): _entity_selector("device_tracker"),

            _optional_entity_key(UI_REPORT_VEHICLE_STATE_ENTITY, get_entity_for_role(entries, VEHICLE_ROLE_VEHICLE_STATE, "")): _any_entity_selector(),

            vol.Optional(
                UI_VEHICLE_AI_SECTION_NOTE,
                default=(
                    "Vehicle report selection ends here. The fields below are used for AI and auto select. "
                    "Auto select finds entities from the same device as the selected main Tesla entity."
                ),
            ): _multiline_text_selector(),

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



def build_ai_entity_manager_schema(current: dict[str, Any]) -> vol.Schema:
    """Build AI-only entity manager schema."""
    entries = normalize_vehicle_entity_map(current.get(CONF_VEHICLE_ENTITY_MAP, DEFAULT_VEHICLE_ENTITY_MAP))
    control_labels = {label for _, label, _, _ in AI_CONTROL_FIELD_SPECS}
    schema: dict[Any, Any] = {
        vol.Optional(
            UI_AI_ENTITY_MANAGER_NOTE,
            default=(
                "Select one sample Tesla entity from Tessie or TeslaMate, then use automatic discovery to find AI entities from the same vehicle. "
                "Auto-fill now separates command entities from context entities. If one field is wrong, replace only that field and save."
            ),
        ): _multiline_text_selector(),

        vol.Optional(
            UI_AI_MAIN_TESLA_ENTITY,
            default=current.get(
                CONF_AI_MAIN_TESLA_ENTITY,
                get_entity_for_role(entries, VEHICLE_ROLE_BATTERY_LEVEL, current.get(CONF_BATTERY_LEVEL_ENTITY, DEFAULT_BATTERY_LEVEL_ENTITY)),
            ),
        ): _any_entity_selector(),

        vol.Optional(
            UI_AI_CONTROLS_NOTE,
            default=(
                "These fields are the command actions Tesla AI can trigger directly, such as horn, lights, trunk, seat heaters, and sentry. "
                "Automatic discovery tries to place them for you. If one action is mapped wrong, correct just that slot."
            ),
        ): _multiline_text_selector(),
    }

    for ui_key, label, role, _keywords in AI_CONTROL_FIELD_SPECS:
        default_entity = get_entity_for_label(entries, label, "")
        if not default_entity and role != VEHICLE_ROLE_OTHER:
            default_entity = get_entity_for_role(entries, role, "")
        schema[_optional_entity_key(ui_key, default_entity)] = _any_entity_selector()

    schema[vol.Optional(
        UI_AI_CONTROL_FIELDS_NOTE,
        default=(
            "These fields are used for AI context and quick reasoning. Tesla AI reads them to understand battery, charging, speed, climate, locks, location, and vehicle state."
        ),
    )] = _multiline_text_selector()

    context_selectors = {
        UI_AI_BATTERY_LEVEL_ENTITY: _any_entity_selector(),
        UI_AI_ENERGY_REMAINING_ENTITY: _any_entity_selector(),
        UI_AI_BATTERY_RANGE_ENTITY: _any_entity_selector(),
        UI_AI_CHARGING_ENTITY: _any_entity_selector(),
        UI_AI_CHARGE_ENERGY_ADDED_ENTITY: _any_entity_selector(),
        UI_AI_CHARGER_POWER_ENTITY: _any_entity_selector(),
        UI_AI_SPEED_ENTITY: _any_entity_selector(),
        UI_AI_SHIFT_STATE_ENTITY: _any_entity_selector(),
        UI_AI_ODOMETER_ENTITY: _any_entity_selector(),
        UI_AI_ELEVATION_ENTITY: _any_entity_selector(),
        UI_AI_LOCATION_TRACKER_ENTITY: _any_entity_selector(),
        UI_AI_CLIMATE_ENTITY: _any_entity_selector(),
        UI_AI_INSIDE_TEMPERATURE_ENTITY: _any_entity_selector(),
        UI_AI_OUTSIDE_TEMPERATURE_ENTITY: _any_entity_selector(),
        UI_AI_BATTERY_TEMPERATURE_ENTITY: _any_entity_selector(),
        UI_AI_DOOR_WINDOW_ENTITY: _any_entity_selector(),
        UI_AI_VEHICLE_STATE_ENTITY: _any_entity_selector(),
        UI_AI_USER_PRESENT_ENTITY: _any_entity_selector(),
    }
    for ui_key, role in AI_CONTEXT_FIELD_SPECS:
        schema[_optional_entity_key(ui_key, get_entity_for_role(entries, role, ""))] = context_selectors[ui_key]

    schema[vol.Optional(
        UI_AI_ALERT_FIELDS_NOTE,
        default=(
            "These optional alert fields help Tesla AI monitor battery, tire, lock, and occupancy conditions. "
            "Leave them empty if your provider does not expose them."
        ),
    )] = _multiline_text_selector()

    for ui_key, role in AI_ALERT_FIELD_SPECS:
        schema[_optional_entity_key(ui_key, get_entity_for_role(entries, role, ""))] = _any_entity_selector()

    schema[vol.Optional(
        UI_AI_OTHER_ENTITIES,
        default=[
            item.get("entity_id")
            for item in entries
            if item.get("use_ai")
            and item.get("role") == VEHICLE_ROLE_OTHER
            and str(item.get("label") or "") not in control_labels
            and item.get("entity_id")
        ],
    )] = _multi_entity_selector()

    schema[vol.Required(UI_VEHICLE_MANAGER_ACTION, default=ACTION_VEHICLE_SAVE_REVIEW)] = _ai_entity_manager_action_selector()
    return vol.Schema(schema)


def build_reports_entity_manager_schema(current: dict[str, Any]) -> vol.Schema:
    """Build Reports-only entity manager schema."""
    entries = normalize_vehicle_entity_map(current.get(CONF_VEHICLE_ENTITY_MAP, DEFAULT_VEHICLE_ENTITY_MAP))
    return vol.Schema(
        {
            vol.Optional(
                UI_REPORTS_ENTITY_MANAGER_NOTE,
                default=(
                    "Select one sample Tesla entity from Tessie or TeslaMate, then use automatic discovery to fill the report fields below. "
                    "Example: choose one Tessie battery level, speed, odometer, climate, or location entity, then select 'Find report entities automatically' at the bottom and submit."
                ),
            ): _multiline_text_selector(),

            vol.Optional(
                UI_REPORT_MAIN_TESLA_ENTITY,
                default=get_entity_for_role(entries, VEHICLE_ROLE_BATTERY_LEVEL, current.get(CONF_BATTERY_LEVEL_ENTITY, DEFAULT_BATTERY_LEVEL_ENTITY)),
            ): _any_entity_selector(),

            _optional_entity_key(UI_REPORT_BATTERY_LEVEL_ENTITY, get_entity_for_role(entries, VEHICLE_ROLE_BATTERY_LEVEL, current.get(CONF_BATTERY_LEVEL_ENTITY, DEFAULT_BATTERY_LEVEL_ENTITY))): _entity_selector("sensor"),
            _optional_entity_key(UI_REPORT_ENERGY_REMAINING_ENTITY, get_entity_for_role(entries, VEHICLE_ROLE_ENERGY_REMAINING, current.get(CONF_ENERGY_REMAINING_ENTITY, DEFAULT_ENERGY_REMAINING_ENTITY))): _entity_selector("sensor"),
            _optional_entity_key(UI_REPORT_SPEED_ENTITY, get_entity_for_role(entries, VEHICLE_ROLE_SPEED, current.get(CONF_SPEED_ENTITY, DEFAULT_SPEED_ENTITY))): _entity_selector("sensor"),
            _optional_entity_key(UI_REPORT_SHIFT_STATE_ENTITY, get_entity_for_role(entries, VEHICLE_ROLE_SHIFT_STATE, current.get(CONF_SHIFT_STATE_ENTITY, DEFAULT_SHIFT_STATE_ENTITY))): _entity_selector("sensor"),
            _optional_entity_key(UI_REPORT_ODOMETER_ENTITY, get_entity_for_role(entries, VEHICLE_ROLE_ODOMETER, current.get(CONF_ODOMETER_ENTITY, DEFAULT_ODOMETER_ENTITY))): _entity_selector("sensor"),
            _optional_entity_key(UI_REPORT_ELEVATION_ENTITY, get_entity_for_role(entries, VEHICLE_ROLE_ELEVATION, current.get(CONF_ELEVATION_ENTITY, DEFAULT_ELEVATION_ENTITY))): _entity_selector("sensor"),
            _optional_entity_key(UI_REPORT_CLIMATE_ENTITY, get_entity_for_role(entries, VEHICLE_ROLE_CLIMATE, current.get(CONF_CLIMATE_ENTITY, DEFAULT_CLIMATE_ENTITY))): _entity_selector("climate"),
            _optional_entity_key(UI_REPORT_CHARGING_ENTITY, get_entity_for_role(entries, VEHICLE_ROLE_CHARGING_STATE, current.get(CONF_CHARGING_ENTITY, DEFAULT_CHARGING_ENTITY))): _any_entity_selector(),
            _optional_entity_key(UI_REPORT_CHARGE_ENERGY_ADDED_ENTITY, get_entity_for_role(entries, VEHICLE_ROLE_CHARGE_ENERGY_ADDED, current.get(CONF_CHARGE_ENERGY_ADDED_ENTITY, DEFAULT_CHARGE_ENERGY_ADDED_ENTITY))): _entity_selector("sensor"),
            _optional_entity_key(UI_REPORT_LOCATION_TRACKER_ENTITY, get_entity_for_role(entries, VEHICLE_ROLE_LOCATION_TRACKER, current.get(CONF_TRIP_MAP_TRACKER_ENTITY, DEFAULT_TRIP_MAP_TRACKER_ENTITY))): _entity_selector("device_tracker"),
            _optional_entity_key(UI_REPORT_VEHICLE_STATE_ENTITY, get_entity_for_role(entries, VEHICLE_ROLE_VEHICLE_STATE, "")): _any_entity_selector(),

            vol.Required(UI_VEHICLE_MANAGER_ACTION, default=ACTION_VEHICLE_SAVE_REVIEW): _reports_entity_manager_action_selector(),
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
        return f"[OK] {entity_id}\n   {label} - {role} - {use_text}"

    role_categories = {
        "BATTERY / CHARGING": {
            VEHICLE_ROLE_BATTERY_LEVEL,
            VEHICLE_ROLE_ENERGY_REMAINING,
            VEHICLE_ROLE_BATTERY_RANGE,
            VEHICLE_ROLE_CHARGING_STATE,
            VEHICLE_ROLE_CHARGE_ENERGY_ADDED,
            VEHICLE_ROLE_CHARGER_POWER,
            VEHICLE_ROLE_BATTERY_TEMPERATURE,
        },
        "DRIVE / MOTION": {
            VEHICLE_ROLE_SPEED,
            VEHICLE_ROLE_SHIFT_STATE,
            VEHICLE_ROLE_ODOMETER,
            VEHICLE_ROLE_ELEVATION,
        },
        "KONUM / ROTA": {VEHICLE_ROLE_LOCATION_TRACKER},
        "CLIMATE / TEMPERATURE": {
            VEHICLE_ROLE_CLIMATE,
            VEHICLE_ROLE_INSIDE_TEMPERATURE,
            VEHICLE_ROLE_OUTSIDE_TEMPERATURE,
        },
        "TIRES": {
            VEHICLE_ROLE_TIRE_PRESSURE_FRONT_LEFT,
            VEHICLE_ROLE_TIRE_PRESSURE_FRONT_RIGHT,
            VEHICLE_ROLE_TIRE_PRESSURE_REAR_LEFT,
            VEHICLE_ROLE_TIRE_PRESSURE_REAR_RIGHT,
        },
        "SECURITY / DOORS": {
            VEHICLE_ROLE_DOOR_WINDOW,
            VEHICLE_ROLE_LOCK_STATE,
        },
    }

    lines = [
        "POM VEHICLE ENTITY MANAGER SUMMARY",
        "",
        "VEHICLE REPORT ENTITIES",
        "Main roles used for reports, consumption, and maps:",
        "",
    ]

    ready_count = 0
    for role in report_roles:
        role_entries = _entries_for(role, "use_report")
        label = VEHICLE_ROLE_LABELS.get(role, role)
        if role_entries:
            ready_count += 1
            lines.append(f"[OK] {label}")
            lines.append(f"   {role_entries[0].get('entity_id')}")
        else:
            lines.append(f"[WARN] {label}")
            lines.append("   not selected")

    ai_entities = [item for item in entries if item.get("use_ai")]
    alert_entities = [item for item in entries if item.get("use_alerts")]
    map_entities = [item for item in entries if item.get("use_map")]

    lines.extend([
        "",
        f"Report readiness: {ready_count}/{len(report_roles)}",
        "",
        "AI ENTITIES",
        "Extra entities that AI can read, grouped by category:",
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
        lines.extend(["", "OTHER AI DATA"])
        for item in other_ai_items[:80]:
            lines.append(_line_for_item(item))

    lines.extend([
        "",
        "COUNTS",
        f"Report: {sum(1 for item in entries if item.get('use_report'))}",
        f"AI: {len(ai_entities)}",
        f"Alerts: {len(alert_entities)}",
        f"Map: {len(map_entities)}",
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
            data_schema=build_initial_setup_schema(),
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

            if section == SECTION_AI_ENTITY_MANAGER:
                return await self.async_step_ai_entity_manager()

            if section == SECTION_REPORTS_ENTITY_MANAGER:
                return await self.async_step_reports_entity_manager()

            if section == SECTION_AUTOMATION_TELEGRAM:
                return await self.async_step_automation_telegram()

            if section == SECTION_PRICES_REPORT:
                return await self.async_step_prices_report()

            if section == SECTION_CHARGING_REPORTS:
                return await self.async_step_charging_reports()

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

    def _registry_metadata_text(self, reg_entry: Any | None, entity_id: str) -> str:
        """Return language-independent registry/state metadata for role detection."""
        parts: list[str] = [entity_id]
        if reg_entry is not None:
            for attr in (
                "unique_id",
                "translation_key",
                "platform",
                "device_class",
                "original_device_class",
                "original_name",
                "name",
            ):
                value = getattr(reg_entry, attr, None)
                if value:
                    parts.append(str(value))

        state = self.hass.states.get(entity_id)
        if state is not None:
            attrs = state.attributes
            for key in (
                "device_class",
                "unit_of_measurement",
                "state_class",
                "attribution",
                "friendly_name",
            ):
                value = attrs.get(key)
                if value:
                    parts.append(str(value))

        return " ".join(parts)

    def _same_device_registry_entries(self, main_entity: str) -> list[Any]:
        """Return registry entries from the same HA device as the selected entity."""
        main_entity = str(main_entity or "").strip()
        if not main_entity:
            return []

        registry = er.async_get(self.hass)
        main_reg_entry = registry.async_get(main_entity)
        device_id = getattr(main_reg_entry, "device_id", None) if main_reg_entry else None
        if not device_id:
            return []

        entries = []
        for reg_entry in registry.entities.values():
            if getattr(reg_entry, "device_id", None) != device_id:
                continue
            if getattr(reg_entry, "disabled_by", None):
                continue
            entity_id = str(getattr(reg_entry, "entity_id", "") or "").strip()
            if entity_id:
                entries.append(reg_entry)
        return entries

    def _candidate_payload_for_ai_discovery(self, reg_entries: list[Any]) -> list[dict[str, Any]]:
        """Build a compact candidate list for AI-assisted entity discovery."""
        candidates: list[dict[str, Any]] = []
        for reg_entry in reg_entries[:160]:
            entity_id = str(getattr(reg_entry, "entity_id", "") or "").strip()
            if not entity_id:
                continue
            state = self.hass.states.get(entity_id)
            attrs = state.attributes if state is not None else {}
            candidates.append(
                {
                    "entity_id": entity_id,
                    "state": str(state.state)[:80] if state is not None else "",
                    "name": str(getattr(reg_entry, "name", "") or ""),
                    "original_name": str(getattr(reg_entry, "original_name", "") or ""),
                    "unique_id": str(getattr(reg_entry, "unique_id", "") or ""),
                    "translation_key": str(getattr(reg_entry, "translation_key", "") or ""),
                    "platform": str(getattr(reg_entry, "platform", "") or ""),
                    "device_class": str(attrs.get("device_class") or getattr(reg_entry, "device_class", "") or ""),
                    "unit": str(attrs.get("unit_of_measurement") or ""),
                }
            )
        return candidates

    async def _ai_assisted_discovered_vehicle_entries(
        self,
        current: dict[str, Any],
        deterministic_entries: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Ask OpenAI to classify same-device entities when localized names hide roles."""
        api_key = str(current.get(CONF_OPENAI_API_KEY) or "").strip()
        if not api_key:
            return []

        main_entity = str(current.get(CONF_AI_MAIN_TESLA_ENTITY) or "").strip()
        reg_entries = self._same_device_registry_entries(main_entity)
        if not reg_entries:
            return []

        candidates = self._candidate_payload_for_ai_discovery(reg_entries)
        if not candidates:
            return []

        already_found = {
            str(item.get("entity_id") or "").strip()
            for item in deterministic_entries
            if str(item.get("entity_id") or "").strip()
        }

        role_values = [role for role in VEHICLE_ENTITY_ROLES if role != VEHICLE_ROLE_OTHER]
        system_prompt = (
            "You classify Home Assistant Tesla vehicle entities for setup. "
            "Entity names may be localized in Turkish, German, Japanese, or any other language, "
            "but unique_id and translation_key often contain canonical Tesla/Tessie/TeslaMate field names. "
            "Prefer unique_id, translation_key, platform, domain, unit, and device_class over display name. "
            "Return strict JSON only. Do not invent entity IDs."
        )
        user_message = (
            "From this same-device entity list, select only entities that are useful for Tesla AI context, "
            "vehicle-control understanding, status answers, alerts, or location. "
            "For each selected entity choose one role from this exact list:\n"
            f"{json.dumps(role_values)}\n\n"
            "Return JSON in this exact shape:\n"
            '{"entities":[{"entity_id":"sensor.example","role":"speed","reason":"short reason"}]}\n\n'
            "Rules:\n"
            "- Use only entity_id values that exist in candidates.\n"
            "- Skip diagnostic noise unless it clearly describes vehicle state, battery, charging, climate, lock, doors, windows, tires, location, user presence, speed, shift, odometer, or temperature.\n"
            "- If unsure, skip it.\n\n"
            f"Already found by deterministic scan: {json.dumps(sorted(already_found))}\n\n"
            f"Candidates:\n{json.dumps(candidates, ensure_ascii=False)}"
        )
        model = str(current.get(CONF_OPENAI_MODEL) or DEFAULT_OPENAI_MODEL)
        response_text = await _async_call_openai_for_config_flow(
            self.hass,
            api_key=api_key,
            model=model,
            system_prompt=system_prompt,
            user_message=user_message,
            max_output_tokens=1600,
        )
        parsed = _parse_json_object_from_text(response_text)
        raw_entities = parsed.get("entities")
        if not isinstance(raw_entities, list):
            return []

        valid_entity_ids = {item["entity_id"] for item in candidates}
        discovered: list[dict[str, Any]] = []
        for item in raw_entities:
            if not isinstance(item, dict):
                continue
            entity_id = str(item.get("entity_id") or "").strip()
            role = str(item.get("role") or "").strip()
            if entity_id not in valid_entity_ids or role not in role_values:
                continue
            entry = self._vehicle_entry_from_entity(entity_id, source="ai_assisted_ai", role=role)
            if entry:
                discovered.append(entry)
        return discovered

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

        reg_entry = None
        if not friendly:
            try:
                registry = er.async_get(self.hass)
                reg_entry = registry.async_get(entity_id)
                if reg_entry:
                    friendly = str(reg_entry.name or reg_entry.original_name or "")
            except Exception:
                friendly = ""
        elif reg_entry is None:
            try:
                registry = er.async_get(self.hass)
                reg_entry = registry.async_get(entity_id)
            except Exception:
                reg_entry = None

        role_value = role or infer_vehicle_role(entity_id, friendly, self._registry_metadata_text(reg_entry, entity_id))
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
        reg_entries = self._same_device_registry_entries(main_entity)

        if reg_entries:
            for reg_entry in reg_entries:
                entity_id = getattr(reg_entry, "entity_id", "")
                friendly = str(reg_entry.name or reg_entry.original_name or "")
                metadata_text = self._registry_metadata_text(reg_entry, entity_id)
                role = infer_vehicle_role(entity_id, friendly, metadata_text)
                if role == VEHICLE_ROLE_OTHER:
                    # Keep useful unknowns visible for AI, but don't flood with every diagnostic entity.
                    text = f"{entity_id} {friendly} {metadata_text}".lower()
                    if not any(k in text for k in ["tesla", "pom", "tessie", "teslamate", "teslafleet", "battery", "charge", "tire", "tyre", "pressure", "temperature", "window", "door", "lock", "range", "speed", "odometer", "climate", "gps", "location", "drive_state", "vehicle_state", "charge_state", "climate_state"]):
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

    def _auto_fill_report_input(
        self,
        user_input: dict[str, Any],
        discovered: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Return user input with report entity fields filled from discovered entries."""
        filled = dict(user_input)
        report_roles = [
            (UI_REPORT_BATTERY_LEVEL_ENTITY, VEHICLE_ROLE_BATTERY_LEVEL),
            (UI_REPORT_ENERGY_REMAINING_ENTITY, VEHICLE_ROLE_ENERGY_REMAINING),
            (UI_REPORT_SPEED_ENTITY, VEHICLE_ROLE_SPEED),
            (UI_REPORT_SHIFT_STATE_ENTITY, VEHICLE_ROLE_SHIFT_STATE),
            (UI_REPORT_ODOMETER_ENTITY, VEHICLE_ROLE_ODOMETER),
            (UI_REPORT_ELEVATION_ENTITY, VEHICLE_ROLE_ELEVATION),
            (UI_REPORT_CLIMATE_ENTITY, VEHICLE_ROLE_CLIMATE),
            (UI_REPORT_CHARGING_ENTITY, VEHICLE_ROLE_CHARGING_STATE),
            (UI_REPORT_CHARGE_ENERGY_ADDED_ENTITY, VEHICLE_ROLE_CHARGE_ENERGY_ADDED),
            (UI_REPORT_LOCATION_TRACKER_ENTITY, VEHICLE_ROLE_LOCATION_TRACKER),
            (UI_REPORT_VEHICLE_STATE_ENTITY, VEHICLE_ROLE_VEHICLE_STATE),
        ]
        for ui_key, role in report_roles:
            if str(filled.get(ui_key) or "").strip():
                continue
            for item in discovered:
                if item.get("role") == role and str(item.get("entity_id") or "").strip():
                    filled[ui_key] = str(item.get("entity_id"))
                    break
        return filled


    def _find_best_ai_control_entity(
        self,
        discovered: list[dict[str, Any]],
        keywords: list[str],
        used_entities: set[str],
    ) -> str:
        """Return the best discovered entity id for an AI control slot."""
        registry = er.async_get(self.hass)
        best_entity = ""
        best_score = 0
        for item in discovered:
            entity_id = str(item.get("entity_id") or "").strip()
            if not entity_id or entity_id in used_entities:
                continue
            reg_entry = registry.async_get(entity_id)
            text = " ".join([
                entity_id,
                str(item.get("label") or ""),
                self._registry_metadata_text(reg_entry, entity_id),
            ]).casefold()
            score = 0
            for keyword in keywords:
                kw = str(keyword or "").strip().casefold()
                if kw and kw in text:
                    score += max(4, len(kw.split()) * 3)
            if score > best_score:
                best_score = score
                best_entity = entity_id
        return best_entity

    def _auto_fill_ai_input(
        self,
        user_input: dict[str, Any],
        discovered: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Return user input with AI context and control slots filled from discovered entries."""
        filled = dict(user_input)
        used_entities: set[str] = set()

        for ui_key, role in AI_CONTEXT_FIELD_SPECS + AI_ALERT_FIELD_SPECS:
            entity_id = str(filled.get(ui_key) or "").strip()
            if entity_id:
                used_entities.add(entity_id)
                continue
            for item in discovered:
                if item.get("role") == role and str(item.get("entity_id") or "").strip():
                    entity_id = str(item.get("entity_id") or "").strip()
                    if entity_id and entity_id not in used_entities:
                        filled[ui_key] = entity_id
                        used_entities.add(entity_id)
                        break

        for ui_key, _label, _role, keywords in AI_CONTROL_FIELD_SPECS:
            entity_id = str(filled.get(ui_key) or "").strip()
            if entity_id:
                used_entities.add(entity_id)
                continue
            match = self._find_best_ai_control_entity(discovered, keywords, used_entities)
            if match:
                filled[ui_key] = match
                used_entities.add(match)

        existing_other = filled.get(UI_AI_OTHER_ENTITIES) or []
        if isinstance(existing_other, str):
            existing_other = [existing_other] if existing_other else []
        other_entities: list[str] = []
        for entity_id in existing_other:
            entity_id = str(entity_id or "").strip()
            if entity_id and entity_id not in other_entities:
                other_entities.append(entity_id)
                used_entities.add(entity_id)
        for item in discovered:
            entity_id = str(item.get("entity_id") or "").strip()
            if not entity_id or entity_id in used_entities:
                continue
            other_entities.append(entity_id)
            used_entities.add(entity_id)
        filled[UI_AI_OTHER_ENTITIES] = other_entities
        return filled

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
        """Build AI-only entries from the explicit AI Entity Manager fields."""
        entries: list[dict[str, Any]] = []
        added: set[str] = set()

        for field_name, role in AI_CONTEXT_FIELD_SPECS + AI_ALERT_FIELD_SPECS:
            entity_id = str(user_input.get(field_name) or "").strip()
            if not entity_id or entity_id in added:
                continue
            entry = self._vehicle_entry_from_entity(entity_id, source="manual_ai", role=role)
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
            added.add(entity_id)

        for field_name, label, role, _keywords in AI_CONTROL_FIELD_SPECS:
            entity_id = str(user_input.get(field_name) or "").strip()
            if not entity_id or entity_id in added:
                continue
            entry = self._vehicle_entry_from_entity(entity_id, source="manual_ai", role=role)
            if not entry:
                continue
            entry["label"] = label
            entry["use_report"] = False
            entry["use_ai"] = True
            entry["use_alerts"] = False
            entry["use_map"] = False
            entries.append(entry)
            added.add(entity_id)

        raw = user_input.get(UI_AI_OTHER_ENTITIES) or []
        if isinstance(raw, str):
            raw = [raw]
        for entity_id in raw:
            entity_id = str(entity_id or "").strip()
            if not entity_id or entity_id in added:
                continue
            entry = self._vehicle_entry_from_entity(entity_id, source="manual_ai", role=VEHICLE_ROLE_OTHER)
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
            added.add(entity_id)
        return entries

    def _build_vehicle_manager_discovered_summary(self, discovered: list[dict[str, Any]], excluded: list[str]) -> str:
        """Return readable preview of auto-discovered entities."""
        if not discovered:
            return "No entities were found with auto select yet. Check the Main Tesla entity setting."
        excluded_set = {str(x).strip() for x in excluded if str(x).strip()}
        lines = ["AUTO DISCOVERED ENTITIES", ""]
        for item in discovered[:120]:
            entity_id = item.get("entity_id", "")
            role = VEHICLE_ROLE_LABELS.get(item.get("role"), item.get("role", "Other"))
            label = item.get("label") or role
            prefix = "EXCLUDED" if entity_id in excluded_set else "OK"
            lines.append(f"{prefix} - {entity_id}")
            lines.append(f"  Role: {role} | {label}")
        if len(discovered) > 120:
            lines.append(f"... +{len(discovered) - 120} entity daha")
        return "\n".join(lines)

    
    async def async_step_ai_entity_manager(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Manage the AI Entity Manager page."""
        errors: dict[str, str] = {}
        current = self._current()

        if user_input is not None:
            action = user_input.get(UI_VEHICLE_MANAGER_ACTION, ACTION_VEHICLE_SAVE_REVIEW)

            temp_current = dict(current)
            temp_current[CONF_AI_MAIN_TESLA_ENTITY] = user_input.get(UI_AI_MAIN_TESLA_ENTITY) or current.get(CONF_AI_MAIN_TESLA_ENTITY, DEFAULT_AI_MAIN_TESLA_ENTITY)

            if action == ACTION_VEHICLE_AUTO_SELECT_AI:
                try:
                    discovered = self._smart_discovered_vehicle_entries(temp_current)
                except Exception:
                    discovered = []
                try:
                    ai_discovered = await self._ai_assisted_discovered_vehicle_entries(temp_current, discovered)
                    discovered = self._merge_vehicle_entries([], discovered + ai_discovered)
                except Exception:
                    pass

                filled_input = self._auto_fill_ai_input(user_input, discovered)
                ai_entries = self._vehicle_manager_ai_entries_from_input(filled_input)
                selected_ai_entities = [item.get("entity_id") for item in ai_entries if item.get("entity_id")]

                existing_entries = normalize_vehicle_entity_map(current.get(CONF_VEHICLE_ENTITY_MAP, DEFAULT_VEHICLE_ENTITY_MAP))
                preserved_entries = [
                    item for item in existing_entries
                    if (
                        item.get("use_report")
                        or item.get("source") not in {"auto_selected_ai", "manual_ai", "ai_assisted_ai"}
                    )
                ]

                merged = self._merge_vehicle_entries([], preserved_entries + ai_entries)
                self._update_pending({
                    CONF_VEHICLE_ENTITY_MAP: normalize_vehicle_entity_map(merged),
                    CONF_AI_EXTRA_CONTEXT_ENTITIES: selected_ai_entities,
                    CONF_AI_MAIN_TESLA_ENTITY: temp_current.get(CONF_AI_MAIN_TESLA_ENTITY),
                    CONF_AI_EXCLUDED_CONTEXT_ENTITIES: [],
                })
                return await self.async_step_ai_entity_manager()

            selected_ai_entries = self._vehicle_manager_ai_entries_from_input(user_input)
            selected_ai_entities = [item.get("entity_id") for item in selected_ai_entries if item.get("entity_id")]

            existing_entries = normalize_vehicle_entity_map(current.get(CONF_VEHICLE_ENTITY_MAP, DEFAULT_VEHICLE_ENTITY_MAP))
            preserved_entries = [
                item for item in existing_entries
                if (
                    item.get("use_report")
                    or item.get("source") not in {"auto_selected_ai", "manual_ai", "ai_assisted_ai"}
                )
            ]

            merged = self._merge_vehicle_entries([], preserved_entries + selected_ai_entries)
            self._update_pending({
                CONF_VEHICLE_ENTITY_MAP: normalize_vehicle_entity_map(merged),
                CONF_AI_EXTRA_CONTEXT_ENTITIES: selected_ai_entities,
                CONF_AI_MAIN_TESLA_ENTITY: temp_current.get(CONF_AI_MAIN_TESLA_ENTITY),
                CONF_AI_EXCLUDED_CONTEXT_ENTITIES: [],
            })

            if action == ACTION_SAVE_AND_CLOSE:
                return self._finish()
            if action == ACTION_RETURN_TO_MENU:
                return await self.async_step_init()
            return await self.async_step_vehicle_entity_review()

        return self.async_show_form(
            step_id="ai_entity_manager",
            data_schema=build_ai_entity_manager_schema(current),
            errors=errors,
        )

    async def async_step_reports_entity_manager(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Manage the Reports Entity Manager page."""
        errors: dict[str, str] = {}
        current = self._current()

        if user_input is not None:
            action = user_input.get(UI_VEHICLE_MANAGER_ACTION, ACTION_VEHICLE_SAVE_REVIEW)

            temp_current = dict(current)
            temp_current[CONF_AI_MAIN_TESLA_ENTITY] = user_input.get(UI_REPORT_MAIN_TESLA_ENTITY) or current.get(CONF_AI_MAIN_TESLA_ENTITY, DEFAULT_AI_MAIN_TESLA_ENTITY)

            if action == ACTION_VEHICLE_AUTO_SELECT_REPORT:
                try:
                    discovered = self._smart_discovered_vehicle_entries(temp_current)
                except Exception:
                    discovered = []

                filled_input = self._auto_fill_report_input(user_input, discovered)
                report_entries = self._vehicle_manager_report_entries_from_input(filled_input)
                existing_entries = normalize_vehicle_entity_map(current.get(CONF_VEHICLE_ENTITY_MAP, DEFAULT_VEHICLE_ENTITY_MAP))
                preserved_entries = [item for item in existing_entries if not item.get("use_report")]
                merged = self._merge_vehicle_entries([], report_entries + preserved_entries)

                self._update_pending({
                    CONF_VEHICLE_ENTITY_MAP: normalize_vehicle_entity_map(merged),
                    CONF_BATTERY_LEVEL_ENTITY: filled_input.get(UI_REPORT_BATTERY_LEVEL_ENTITY),
                    CONF_ENERGY_REMAINING_ENTITY: filled_input.get(UI_REPORT_ENERGY_REMAINING_ENTITY),
                    CONF_SPEED_ENTITY: filled_input.get(UI_REPORT_SPEED_ENTITY),
                    CONF_SHIFT_STATE_ENTITY: filled_input.get(UI_REPORT_SHIFT_STATE_ENTITY),
                    CONF_ODOMETER_ENTITY: filled_input.get(UI_REPORT_ODOMETER_ENTITY),
                    CONF_ELEVATION_ENTITY: filled_input.get(UI_REPORT_ELEVATION_ENTITY),
                    CONF_CLIMATE_ENTITY: filled_input.get(UI_REPORT_CLIMATE_ENTITY),
                    CONF_CHARGING_ENTITY: filled_input.get(UI_REPORT_CHARGING_ENTITY),
                    CONF_CHARGE_ENERGY_ADDED_ENTITY: filled_input.get(UI_REPORT_CHARGE_ENERGY_ADDED_ENTITY),
                    CONF_TRIP_MAP_TRACKER_ENTITY: filled_input.get(UI_REPORT_LOCATION_TRACKER_ENTITY),
                })
                return await self.async_step_reports_entity_manager()

            report_entries = self._vehicle_manager_report_entries_from_input(user_input)
            existing_entries = normalize_vehicle_entity_map(current.get(CONF_VEHICLE_ENTITY_MAP, DEFAULT_VEHICLE_ENTITY_MAP))
            preserved_entries = [item for item in existing_entries if not item.get("use_report")]
            merged = self._merge_vehicle_entries([], report_entries + preserved_entries)

            self._update_pending({
                CONF_VEHICLE_ENTITY_MAP: normalize_vehicle_entity_map(merged),
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
            })

            if action == ACTION_SAVE_AND_CLOSE:
                return self._finish()
            if action == ACTION_RETURN_TO_MENU:
                return await self.async_step_init()
            return await self.async_step_vehicle_entity_review()

        return self.async_show_form(
            step_id="reports_entity_manager",
            data_schema=build_reports_entity_manager_schema(current),
            errors=errors,
        )
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
            temp_current[CONF_AI_MAIN_TESLA_ENTITY] = user_input.get(UI_AI_MAIN_TESLA_ENTITY) or user_input.get(UI_REPORT_MAIN_TESLA_ENTITY) or current.get(CONF_AI_MAIN_TESLA_ENTITY, DEFAULT_AI_MAIN_TESLA_ENTITY)

            if action == ACTION_VEHICLE_AUTO_SELECT_REPORT:
                try:
                    discovered = self._smart_discovered_vehicle_entries(temp_current)
                except Exception:
                    discovered = []

                filled_input = self._auto_fill_report_input(user_input, discovered)
                report_entries = self._vehicle_manager_report_entries_from_input(filled_input)
                existing_entries = normalize_vehicle_entity_map(current.get(CONF_VEHICLE_ENTITY_MAP, DEFAULT_VEHICLE_ENTITY_MAP))
                custom_entries = [
                    item for item in existing_entries
                    if item.get("source") not in {"report_form", "smart_import"}
                    and str(item.get("entity_id") or "").strip() not in excluded_set
                ]
                merged = self._merge_vehicle_entries([], report_entries + custom_entries)
                self._update_pending({
                    CONF_VEHICLE_ENTITY_MAP: normalize_vehicle_entity_map(merged),
                    CONF_AI_MAIN_TESLA_ENTITY: temp_current.get(CONF_AI_MAIN_TESLA_ENTITY),
                    CONF_AI_EXCLUDED_CONTEXT_ENTITIES: excluded_entities,
                    CONF_BATTERY_LEVEL_ENTITY: filled_input.get(UI_REPORT_BATTERY_LEVEL_ENTITY),
                    CONF_ENERGY_REMAINING_ENTITY: filled_input.get(UI_REPORT_ENERGY_REMAINING_ENTITY),
                    CONF_SPEED_ENTITY: filled_input.get(UI_REPORT_SPEED_ENTITY),
                    CONF_SHIFT_STATE_ENTITY: filled_input.get(UI_REPORT_SHIFT_STATE_ENTITY),
                    CONF_ODOMETER_ENTITY: filled_input.get(UI_REPORT_ODOMETER_ENTITY),
                    CONF_ELEVATION_ENTITY: filled_input.get(UI_REPORT_ELEVATION_ENTITY),
                    CONF_CLIMATE_ENTITY: filled_input.get(UI_REPORT_CLIMATE_ENTITY),
                    CONF_CHARGING_ENTITY: filled_input.get(UI_REPORT_CHARGING_ENTITY),
                    CONF_CHARGE_ENERGY_ADDED_ENTITY: filled_input.get(UI_REPORT_CHARGE_ENERGY_ADDED_ENTITY),
                    CONF_TRIP_MAP_TRACKER_ENTITY: filled_input.get(UI_REPORT_LOCATION_TRACKER_ENTITY),
                    CONF_REVERSE_GEOCODING_ENABLED: filled_input.get(UI_REVERSE_GEOCODING_ENABLED),
                    CONF_REVERSE_GEOCODING_CACHE_MINUTES: filled_input.get(UI_REVERSE_GEOCODING_CACHE_MINUTES),
                    CONF_REVERSE_GEOCODING_USE_IN_AI: filled_input.get(UI_REVERSE_GEOCODING_USE_IN_AI),
                })
                return await self.async_step_vehicle_entity_manager()

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
        """Manage Telegram settings."""
        errors: dict[str, str] = {}

        if user_input is not None:
            action = user_input.get(UI_AFTER_SAVING, ACTION_RETURN_TO_MENU)
            group_id = str(user_input.get(UI_TELEGRAM_TARGET) or "").strip()
            replies_enabled = bool(user_input.get(UI_TELEGRAM_REPLIES_ENABLED, False))
            poll_interval_value = _coerce_decimal(
                user_input.get(UI_BUILTIN_TELEGRAM_POLL_INTERVAL_SECONDS)
            )
            poll_interval = max(
                1,
                int(
                    poll_interval_value
                    if isinstance(poll_interval_value, (int, float))
                    else DEFAULT_BUILTIN_TELEGRAM_POLL_INTERVAL_SECONDS
                ),
            )
            updates = {
                CONF_BUILTIN_TELEGRAM_ENABLED: bool(user_input.get(UI_BUILTIN_TELEGRAM_ENABLED, False)),
                CONF_BUILTIN_TELEGRAM_BOT_TOKEN: str(user_input.get(UI_BUILTIN_TELEGRAM_BOT_TOKEN) or "").strip(),
                CONF_BUILTIN_TELEGRAM_POLL_ENABLED: bool(user_input.get(UI_BUILTIN_TELEGRAM_POLL_ENABLED, True)),
                CONF_BUILTIN_TELEGRAM_POLL_INTERVAL_SECONDS: poll_interval,
                CONF_TELEGRAM_TARGET: group_id if replies_enabled else "",
                CONF_AI_TELEGRAM_TARGET: group_id if replies_enabled else "",
                CONF_AI_TELEGRAM_LISTENER_ENABLED: bool(user_input.get(UI_AI_TELEGRAM_LISTENER_ENABLED, False)),
                CONF_AI_TELEGRAM_LISTENER_CHAT_ID: group_id,
            }
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
        """Manage trip report and map options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            action = user_input.get(UI_AFTER_SAVING, ACTION_RETURN_TO_MENU)
            updates = _map_ui_input(
                user_input,
                {
                    UI_AUTO_TRIP_TRACKING: CONF_AUTO_TRIP_TRACKING,
                    UI_AUTO_START_SPEED_THRESHOLD: CONF_AUTO_START_SPEED_THRESHOLD,
                    UI_TRIP_MAP_ENABLED: CONF_TRIP_MAP_ENABLED,
                    UI_TRIP_MAP_TRACKER_ENTITY: CONF_TRIP_MAP_TRACKER_ENTITY,
                    UI_TRIP_MAP_SAMPLE_INTERVAL_SECONDS: CONF_TRIP_MAP_SAMPLE_INTERVAL_SECONDS,
                    UI_TRIP_MAP_MIN_MOVEMENT_METERS: CONF_TRIP_MAP_MIN_MOVEMENT_METERS,
                    UI_TRIP_MAP_SEND_SEPARATE_PNG: CONF_TRIP_MAP_SEND_SEPARATE_PNG,
                    UI_SUPERCHARGER_PRICE: CONF_SUPERCHARGER_PRICE,
                    UI_ZES_PRICE: CONF_ZES_PRICE,
                    UI_ASTOR_PRICE: CONF_ASTOR_PRICE,
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
                    UI_SHOW_TRIP_MAP: CONF_SHOW_TRIP_MAP,
                },
            )
            return await self._save_or_return(updates, action)

        return self.async_show_form(
            step_id="prices_report",
            data_schema=build_trip_reports_schema(self._current()),
            errors=errors,
        )

    async def async_step_charging_reports(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Manage charging report options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            action = user_input.get(UI_AFTER_SAVING, ACTION_RETURN_TO_MENU)
            updates = _map_ui_input(
                user_input,
                {
                    UI_CHARGING_REPORT_MODE: CONF_CHARGING_REPORT_MODE,
                },
            )
            return await self._save_or_return(updates, action)

        return self.async_show_form(
            step_id="charging_reports",
            data_schema=build_charging_reports_schema(self._current()),
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
        """Manage AI settings."""
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
                    UI_AI_NAME: CONF_AI_NAME,
                    UI_AI_AUTO_DISCOVER_DEVICE_ENTITIES: CONF_AI_AUTO_DISCOVER_DEVICE_ENTITIES,
                    UI_AI_INCLUDE_UNAVAILABLE: CONF_AI_INCLUDE_UNAVAILABLE,
                    UI_AI_MAX_CONTEXT_ENTITIES: CONF_AI_MAX_CONTEXT_ENTITIES,
                    UI_REVERSE_GEOCODING_ENABLED: CONF_REVERSE_GEOCODING_ENABLED,
                    UI_REVERSE_GEOCODING_CACHE_MINUTES: CONF_REVERSE_GEOCODING_CACHE_MINUTES,
                    UI_REVERSE_GEOCODING_USE_IN_AI: CONF_REVERSE_GEOCODING_USE_IN_AI,
                    UI_OPENAI_MODEL: CONF_OPENAI_MODEL,
                    UI_AI_MAX_OUTPUT_TOKENS: CONF_AI_MAX_OUTPUT_TOKENS,
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









