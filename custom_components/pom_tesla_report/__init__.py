"""Tesla AI custom integration."""

from __future__ import annotations

import asyncio
import copy
import json
import logging
import re
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import voluptuous as vol
from aiohttp import ClientError, FormData

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import entity_registry as er, device_registry as dr

from .const import (
    DOMAIN,
    TRIP_STATE_KEY,
    MANUAL_TRACKING_STATE_KEY,
    DATA_ASYNC_START_MANUAL_TRACKING,
    DATA_ASYNC_FINISH_MANUAL_TRACKING,
    CONF_TELEGRAM_TARGET,
    CONF_BUILTIN_TELEGRAM_ENABLED,
    CONF_BUILTIN_TELEGRAM_BOT_TOKEN,
    CONF_BUILTIN_TELEGRAM_POLL_ENABLED,
    CONF_BUILTIN_TELEGRAM_POLL_INTERVAL_SECONDS,
    CONF_SHIFT_STATE_ENTITY,
    CONF_SPEED_ENTITY,
    CONF_ODOMETER_ENTITY,
    CONF_BATTERY_LEVEL_ENTITY,
    CONF_ENERGY_REMAINING_ENTITY,
    CONF_ELEVATION_ENTITY,
    CONF_CLIMATE_ENTITY,
    CONF_CHARGE_ENERGY_ADDED_ENTITY,
    CONF_SUPERCHARGER_PRICE,
    CONF_ZES_PRICE,
    CONF_ASTOR_PRICE,
    CONF_CHARGE_PROVIDER_PRESETS,
    DEFAULT_SUPERCHARGER_PRICE,
    DEFAULT_ZES_PRICE,
    DEFAULT_ASTOR_PRICE,
    DEFAULT_CHARGE_PROVIDER_PRESETS,
    CHARGE_COST_LEDGER_FILENAME,
    TRIP_MONTHLY_LEDGER_FILENAME,
    CHARGE_COST_MONTHLY_REPORT_HOUR,
    CHARGE_COST_MONTHLY_REPORT_MINUTE,
    CONF_CHARGING_REPORT_MODE,
    CHARGING_REPORT_MODE_DIRECT,
    CHARGING_REPORT_MODE_PROMPT,
    DEFAULT_CHARGING_REPORT_MODE,
    CONF_APP_LANGUAGE,
    APP_LANGUAGE_TR,
    APP_LANGUAGE_EN,
    DEFAULT_APP_LANGUAGE,
    CONF_REPORT_LANGUAGE,
    DEFAULT_REPORT_LANGUAGE,
    CONF_REPORT_CURRENCY,
    DEFAULT_REPORT_CURRENCY,
    REPORT_CURRENCY_OPTIONS,
    CONF_AI_TELEGRAM_REPORT_LANGUAGE,
    AI_TELEGRAM_REPORT_LANGUAGE_AUTO,
    AI_TELEGRAM_REPORT_LANGUAGE_TR,
    AI_TELEGRAM_REPORT_LANGUAGE_EN,
    DEFAULT_AI_TELEGRAM_REPORT_LANGUAGE,
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
    CONF_AUTO_TRIP_TRACKING,
    CONF_AUTO_START_SPEED_THRESHOLD,
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
    CONF_LIVE_TRIP_IGNORE_SHORT_MANEUVERS,
    CONF_LIVE_TRIP_CANDIDATE_MIN_DISTANCE_KM,
    CONF_LIVE_TRIP_CANDIDATE_MIN_DURATION_SECONDS,
    CONF_LIVE_TRIP_AI_SEGMENT_DISTANCE_KM,
    DEFAULT_LIVE_TRIP_ENABLED,
    DEFAULT_LIVE_TRIP_UPDATE_INTERVAL_SECONDS,
    DEFAULT_LIVE_TRIP_TRAFFIC_SPEED_THRESHOLD,
    DEFAULT_LIVE_TRIP_FINISH_DELAY_SECONDS,
    DEFAULT_LIVE_TRIP_MIN_DISTANCE_KM,
    DEFAULT_LIVE_TRIP_IGNORE_SHORT_MANEUVERS,
    DEFAULT_LIVE_TRIP_CANDIDATE_MIN_DISTANCE_KM,
    DEFAULT_LIVE_TRIP_CANDIDATE_MIN_DURATION_SECONDS,
    DEFAULT_LIVE_TRIP_AI_SEGMENT_DISTANCE_KM,
    LIVE_TRIP_AI_SEGMENT_DISTANCE_OPTIONS,
    CONF_CHARGING_ENTITY,
    CONF_AI_ENABLED,
    CONF_OPENAI_API_KEY,
    CONF_OPENAI_MODEL,
    CONF_AI_TELEGRAM_TARGET,
    CONF_AI_NAME,
    CONF_AI_USER_ADDRESS,
    CONF_AI_SYSTEM_PROMPT,
    CONF_AI_MAX_OUTPUT_TOKENS,
    CONF_AI_TELEGRAM_LISTENER_ENABLED,
    CONF_AI_TELEGRAM_LISTENER_CHAT_ID,
    CONF_AI_TELEGRAM_ALLOWED_USER_ID,
    CONF_AI_TELEGRAM_PREFIX,
    CONF_AI_TELEGRAM_INCLUDE_CONTEXT,
    CONF_AI_CONFIRM_OPTIONAL_CONTROLS,
    DEFAULT_AI_ENABLED,
    DEFAULT_OPENAI_MODEL,
    DEFAULT_AI_NAME,
    DEFAULT_AI_USER_ADDRESS,
    DEFAULT_AI_SYSTEM_PROMPT,
    DEFAULT_AI_MAX_OUTPUT_TOKENS,
    DEFAULT_AI_TELEGRAM_LISTENER_ENABLED,
    DEFAULT_AI_TELEGRAM_ALLOWED_USER_ID,
    DEFAULT_AI_TELEGRAM_PREFIX,
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
    AI_PERSONALITY_LAZ_BLACK_SEA,
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
    CONF_AI_TRIP_STORY_DETAIL_LEVEL,
    AI_TRIP_STORY_DETAIL_BASIC,
    AI_TRIP_STORY_DETAIL_BALANCED,
    AI_TRIP_STORY_DETAIL_DETAILED,
    AI_TRIP_STORY_DETAIL_OPTIONS,
    DEFAULT_AI_TRIP_STORY_DETAIL_LEVEL,
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
    CONF_PANEL_REPORT_ENTITY_MAP,
    DEFAULT_PANEL_REPORT_ENTITY_MAP,
    CONF_PANEL_AI_ENTITY_MAP,
    DEFAULT_PANEL_AI_ENTITY_MAP,
    VEHICLE_ROLE_BATTERY_LEVEL,
    VEHICLE_ROLE_ENERGY_REMAINING,
    VEHICLE_ROLE_CHARGING_STATE,
    VEHICLE_ROLE_CHARGE_ENERGY_ADDED,
    VEHICLE_ROLE_SPEED,
    VEHICLE_ROLE_SHIFT_STATE,
    VEHICLE_ROLE_ODOMETER,
    VEHICLE_ROLE_ELEVATION,
    VEHICLE_ROLE_CLIMATE,
    VEHICLE_ROLE_LOCATION_TRACKER,
    VEHICLE_ROLE_VEHICLE_STATE,
    VEHICLE_ROLE_USER_PRESENT,
    VEHICLE_ROLE_BATTERY_RANGE,
    VEHICLE_ROLE_CHARGER_POWER,
    VEHICLE_ROLE_INSIDE_TEMPERATURE,
    VEHICLE_ROLE_OUTSIDE_TEMPERATURE,
    VEHICLE_ROLE_BATTERY_TEMPERATURE,
    VEHICLE_ROLE_TIRE_PRESSURE_FRONT_LEFT,
    VEHICLE_ROLE_TIRE_PRESSURE_FRONT_RIGHT,
    VEHICLE_ROLE_TIRE_PRESSURE_REAR_LEFT,
    VEHICLE_ROLE_TIRE_PRESSURE_REAR_RIGHT,
    VEHICLE_ROLE_DOOR_WINDOW,
    VEHICLE_ROLE_LOCK_STATE,
    PERIODIC_REPORT_STATE_FILENAME,
    CONF_TELEGRAM_WEEKLY_TRIP_REPORT_ENABLED,
    CONF_TELEGRAM_MONTHLY_TRIP_REPORT_ENABLED,
    CONF_TELEGRAM_WEEKLY_CHARGE_REPORT_ENABLED,
    CONF_TELEGRAM_MONTHLY_CHARGE_REPORT_ENABLED,
    DEFAULT_TELEGRAM_WEEKLY_TRIP_REPORT_ENABLED,
    DEFAULT_TELEGRAM_MONTHLY_TRIP_REPORT_ENABLED,
    DEFAULT_TELEGRAM_WEEKLY_CHARGE_REPORT_ENABLED,
    DEFAULT_TELEGRAM_MONTHLY_CHARGE_REPORT_ENABLED,
    PERIODIC_REPORT_WEEKDAY,
    PERIODIC_REPORT_HOUR,
    PERIODIC_REPORT_MINUTE,
    VEHICLE_ROLE_OTHER,
)
from .image_renderer import render_trip_report_png
from .trip_map_renderer import render_trip_map_png
from .location_map_renderer import render_vehicle_location_map_png
from .charging_report_renderer import render_charging_report_png, render_monthly_charge_cost_report_pngs
from .monthly_trip_report_renderer import render_monthly_trip_report_pngs

DASHBOARD_STATIC_ASSET_URL_PATH = "/pom_tesla_report/dashboard/png"

from .dashboard.helpers import (
    async_show_dependency_notification as async_show_dashboard_dependency_notification,
    async_show_install_notification as async_show_dashboard_install_notification,
    async_write_dashboard as async_write_tesla_dashboard,
    merged_options_from_report_config as merged_dashboard_options_from_report_config,
)

_LOGGER = logging.getLogger(__name__)
DASHBOARD_FRONTEND_VERSION = "2.2.0-dashboard-alpha362-tesla-ai-name-cache-hide"

PLATFORMS: list[Platform] = [Platform.SWITCH, Platform.SENSOR, Platform.SELECT, Platform.BINARY_SENSOR]

TELEGRAM_REPORT_COMMANDS_OPTION_KEY = "telegram_report_commands"
DEFAULT_TELEGRAM_REPORT_COMMANDS = {
    "charge_report": "charge",
    "trip_summary": "trip",
    "trip_all": "tripall",
    "trip_single": "single",
    "trip_last": "triplast",
    "trip_today": "triptoday",
    "trip_week": "tripweek",
}
LEGACY_TELEGRAM_REPORT_COMMAND_ALIASES = {
    "charge_report": ("charge",),
    "trip_summary": ("trip", "trips", "tripsummary"),
    "trip_all": ("tripall",),
    "trip_single": ("single",),
    "trip_last": ("triplast", "lasttrip"),
    "trip_today": ("triptoday", "todaytrip"),
    "trip_week": ("tripweek", "weektrip", "tripsweek"),
}

SERVICE_DEBUG_CONFIG = "debug_config"
SERVICE_SEND_CHARGE_REPORT = "send_charge_report"
SERVICE_START_CHARGE_REPORT_PROMPT = "start_charge_report_prompt"
SERVICE_GENERATE_TEST_TRIP_IMAGE = "generate_test_trip_image"
SERVICE_START_LIVE_TRIP_TEST = "start_live_trip_test"
SERVICE_FINISH_LIVE_TRIP_TEST = "finish_live_trip_test"
SERVICE_RESET_LIVE_TRIP_TEST = "reset_live_trip_test"
SERVICE_GENERATE_TRIP_IMAGE_FROM_JSON = "generate_trip_image_from_json"
SERVICE_START_TRIP = "start_trip"
SERVICE_FINISH_TRIP = "finish_trip"
SERVICE_DEBUG_TRIP_STATE = "debug_trip_state"
SERVICE_RESET_TRIP = "reset_trip"
SERVICE_AI_ASK = "ai_ask"
SERVICE_DEBUG_AI_CONTEXT = "debug_ai_context"
SERVICE_DEBUG_ALERTS = "debug_alerts"
SERVICE_TEST_AI_ALERT = "test_ai_alert"
SERVICE_REBUILD_DASHBOARD = "rebuild_dashboard"
SERVICE_SHOW_DASHBOARD_DEPENDENCIES = "show_dashboard_dependencies"
SERVICE_INSTALL_DASHBOARD_RESOURCES = "install_dashboard_resources"
SERVICE_SET_DASHBOARD_ENERGY_FIELD = "set_dashboard_energy_field"
SERVICE_SEND_DASHBOARD_PERSON_TRACK_TELEGRAM = "send_dashboard_person_track_telegram"

DEFAULT_TRIP_JSON_PATH = "/config/www/tesla_trip_report/tesla_trip_data.json"
DEFAULT_TRIP_IMAGE_OUTPUT_PATH = "/config/www/pom_tesla_report/final_trip_report.png"
DEFAULT_MANUAL_TRIP_IMAGE_OUTPUT_PATH = "/config/www/pom_tesla_report/manual_trip_report.png"
DEFAULT_AUTO_TRIP_IMAGE_OUTPUT_PATH = "/config/www/pom_tesla_report/auto_trip_report.png"
DEFAULT_MANUAL_TRACKING_IMAGE_OUTPUT_PATH = "/config/www/pom_tesla_report/manual_tracking_report.png"
DEFAULT_AUTO_TRIP_MAP_OUTPUT_PATH = "/config/www/pom_tesla_report/auto_trip_map.png"
DEFAULT_FINAL_TRIP_MAP_OUTPUT_PATH = "/config/www/pom_tesla_report/final_trip_map.png"
DEFAULT_MANUAL_TRACKING_MAP_OUTPUT_PATH = "/config/www/pom_tesla_report/manual_tracking_map.png"
DEFAULT_CHARGING_REPORT_IMAGE_OUTPUT_PATH = "/config/www/pom_tesla_report/charging_report.png"
DEFAULT_VEHICLE_LOCATION_MAP_OUTPUT_PATH = "/config/www/pom_tesla_report/vehicle_location_map.png"

TRAFFIC_SPEED_THRESHOLD_KMH = 20.0
MOVING_SPEED_THRESHOLD_KMH = 1.0
SPEED_SAMPLER_INTERVAL_SECONDS = 1
SPEED_SAMPLER_MAX_DELTA_SECONDS = 5.0
SPEED_SAMPLE_HISTORY_LIMIT = 120

# alpha228 traffic model. This follows the TomTom/INRIX-style idea of comparing
# real travel time with a free-flow/reference travel time. The stop-go and slow
# buckets still use speed samples so reports can explain where delay came from.
TRAFFIC_STOP_GO_SPEED_THRESHOLD_KMH = 5.0
TRAFFIC_SLOW_SPEED_THRESHOLD_KMH = 20.0
TRAFFIC_REFERENCE_CITY_KMH = 35.0
TRAFFIC_REFERENCE_MIXED_KMH = 55.0
TRAFFIC_REFERENCE_HIGHWAY_KMH = 90.0
TRAFFIC_REFERENCE_MIN_KMH = 25.0
TRAFFIC_REFERENCE_MAX_KMH = 115.0
TRAFFIC_P85_BLEND_WEIGHT = 0.35

# alpha252 short-trip traffic guard. Very short neighborhood drives can show high
# traffic percentages from a few seconds of start/turn/parking manoeuvres. Keep
# raw values for diagnostics, but do not let them become a "heavy traffic"
# headline unless the absolute delay is meaningful.
SHORT_TRIP_TRAFFIC_DISTANCE_KM = 1.0
SHORT_TRIP_TRAFFIC_DURATION_SECONDS = 300.0
SHORT_TRIP_TINY_TRAFFIC_DELAY_SECONDS = 60.0
SHORT_TRIP_TINY_SPEED_BUCKET_SECONDS = 120.0

# alpha320 cautious traffic interpretation. With our current entity set we can
# reliably measure low-speed/stop-go time, but we cannot always prove that the
# cause is external traffic. Short urban drives, traffic lights, junctions and
# destination/parking search must therefore down-rank the headline traffic claim.
CAUTIOUS_TRAFFIC_DISTANCE_KM = 5.0
CAUTIOUS_TRAFFIC_DELAY_SECONDS = 300.0
CAUTIOUS_TRAFFIC_STRONG_DELAY_SECONDS = 480.0
CAUTIOUS_TRAFFIC_MIN_REAL_DELAY_SECONDS = 120.0

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


SEND_CHARGE_REPORT_SCHEMA = vol.Schema(
    {
        vol.Optional("test_mode", default=False): cv.boolean,
        vol.Optional("send_telegram", default=True): cv.boolean,
        vol.Optional("telegram_target"): cv.string,
        vol.Optional("chat_id"): cv.string,
        vol.Optional("added_kwh"): vol.Coerce(float),
        vol.Optional("battery_level"): vol.Coerce(float),
        vol.Optional("duration_minutes"): vol.Coerce(float),
        vol.Optional("message_prefix", default=""): cv.string,
        vol.Optional("actual_provider"): cv.string,
        vol.Optional("actual_price_per_kwh"): vol.Coerce(float),
        vol.Optional("actual_total_cost"): vol.Coerce(float),
    }
)


START_CHARGE_REPORT_PROMPT_SCHEMA = vol.Schema(
    {
        vol.Optional("test_mode", default=False): cv.boolean,
        vol.Optional("telegram_target"): cv.string,
        vol.Optional("chat_id"): cv.string,
        vol.Optional("added_kwh"): vol.Coerce(float),
        vol.Optional("duration_minutes"): vol.Coerce(float),
        vol.Optional("battery_range_km"): vol.Coerce(float),
        vol.Optional("battery_range_estimate_km"): vol.Coerce(float),
        vol.Optional("peak_power_kw"): vol.Coerce(float),
    }
)


GENERATE_TEST_TRIP_IMAGE_SCHEMA = vol.Schema(
    {
        vol.Optional("send_telegram", default=True): cv.boolean,
        vol.Optional("test_mode", default=True): cv.boolean,
        vol.Optional("trip_km", default=12.4): vol.Coerce(float),
        vol.Optional("duration_text", default="28 dakika"): cv.string,
        vol.Optional("traffic_text", default="9 dakika"): cv.string,
        vol.Optional("average_speed", default=26.6): vol.Coerce(float),
        vol.Optional("average_overall_speed"): vol.Coerce(float),
        vol.Optional("used_kwh", default=2.35): vol.Coerce(float),
        vol.Optional("consumption_kwh_100km", default=18.95): vol.Coerce(float),
        vol.Optional("start_battery", default=82.0): vol.Coerce(float),
        vol.Optional("end_battery", default=78.0): vol.Coerce(float),
        vol.Optional("climate_text", default="Klima yolculuk boyunca 18 dakika açıktı."): cv.string,
        vol.Optional("min_elevation", default=24): vol.Coerce(float),
        vol.Optional("max_elevation", default=74): vol.Coerce(float),
        vol.Optional("elevation_range", default=50): vol.Coerce(float),
        vol.Optional(
            "efficiency_comment",
            default="Bu PNG Chromium olmadan doğrudan entegrasyon içinde oluşturuldu.",
        ): cv.string,
        vol.Optional("telegram_target"): cv.string,
        vol.Optional("chat_id"): cv.string,
    }
)




START_LIVE_TRIP_TEST_SCHEMA = vol.Schema(
    {
        vol.Optional("duration_minutes", default=18): vol.Coerce(float),
        vol.Optional("distance_km", default=3.39): vol.Coerce(float),
        vol.Optional("used_kwh", default=0.62): vol.Coerce(float),
        vol.Optional("start_battery", default=54.0): vol.Coerce(float),
        vol.Optional("end_battery", default=53.0): vol.Coerce(float),
        vol.Optional("min_elevation", default=26.0): vol.Coerce(float),
        vol.Optional("max_elevation", default=49.0): vol.Coerce(float),
        vol.Optional("traffic_minutes", default=18): vol.Coerce(float),
        vol.Optional("climate_minutes", default=18): vol.Coerce(float),
        vol.Optional("speed_multiplier", default=12): vol.Coerce(float),
        vol.Optional("update_interval_seconds", default=1): vol.Coerce(float),
        vol.Optional("telegram_target"): cv.string,
        vol.Optional("chat_id"): cv.string,
    }
)


FINISH_LIVE_TRIP_TEST_SCHEMA = vol.Schema(
    {
        vol.Optional("send_telegram", default=True): cv.boolean,
        vol.Optional("caption", default="🚗 Tesla AI - Live Trip Test Raporu"): cv.string,
        vol.Optional("output_path", default="/config/www/pom_tesla_report/live_trip_test_report.png"): cv.string,
        vol.Optional("telegram_target"): cv.string,
        vol.Optional("chat_id"): cv.string,
    }
)


RESET_LIVE_TRIP_TEST_SCHEMA = vol.Schema({
    vol.Optional("telegram_target"): cv.string,
    vol.Optional("chat_id"): cv.string,
})


GENERATE_TRIP_IMAGE_FROM_JSON_SCHEMA = vol.Schema(
    {
        vol.Optional("json_path", default=DEFAULT_TRIP_JSON_PATH): cv.string,
        vol.Optional("output_path", default=DEFAULT_TRIP_IMAGE_OUTPUT_PATH): cv.string,
        vol.Optional("send_telegram", default=True): cv.boolean,
        vol.Optional("caption", default="🚗 Tesla AI - Sürüş Görseli"): cv.string,
    }
)


START_TRIP_SCHEMA = vol.Schema(
    {
        vol.Optional("force", default=False): cv.boolean,
        vol.Optional("send_notification", default=True): cv.boolean,
    }
)


FINISH_TRIP_SCHEMA = vol.Schema(
    {
        vol.Optional("send_telegram", default=True): cv.boolean,
        vol.Optional("caption", default="🚗 Tesla AI - Manuel Sürüş Raporu"): cv.string,
        vol.Optional("output_path", default=DEFAULT_MANUAL_TRIP_IMAGE_OUTPUT_PATH): cv.string,
        vol.Optional("test_mode", default=False): cv.boolean,
        vol.Optional("override_trip_km"): vol.Coerce(float),
        vol.Optional("override_used_kwh"): vol.Coerce(float),
        vol.Optional("override_end_battery"): vol.Coerce(float),
        vol.Optional("override_duration_minutes"): vol.Coerce(float),
        vol.Optional("override_traffic_minutes"): vol.Coerce(float),
    }
)


AI_ASK_SCHEMA = vol.Schema(
    {
        vol.Required("message"): cv.string,
        vol.Optional("send_telegram", default=True): cv.boolean,
        vol.Optional("telegram_target"): cv.string,
        vol.Optional("chat_id"): cv.string,
        vol.Optional("include_context", default=True): cv.boolean,
    }
)


DEBUG_AI_CONTEXT_SCHEMA = vol.Schema(
    {
        vol.Optional("send_telegram", default=True): cv.boolean,
        vol.Optional("telegram_target"): cv.string,
        vol.Optional("chat_id"): cv.string,
        vol.Optional("max_entities"): vol.Coerce(int),
        vol.Optional("include_unavailable"): cv.boolean,
    }
)


DEBUG_ALERTS_SCHEMA = vol.Schema(
    {
        vol.Optional("send_telegram", default=True): cv.boolean,
        vol.Optional("telegram_target"): cv.string,
        vol.Optional("chat_id"): cv.string,
    }
)


TEST_AI_ALERT_SCHEMA = vol.Schema(
    {
        vol.Required("alert_type"): vol.In([
            "low_battery",
            "tire_pressure",
            "battery_temperature",
            "charging_stopped",
        ]),
        vol.Optional("send_telegram", default=True): cv.boolean,
        vol.Optional("telegram_target"): cv.string,
        vol.Optional("chat_id"): cv.string,
    }
)



SET_DASHBOARD_ENERGY_FIELD_SCHEMA = vol.Schema(
    {
        vol.Required("field"): vol.In([
            "energy_remaining",
            "battery_level",
            "battery_range",
            "inside_temp",
            "outside_temp",
            "odometer",
            "battery_heater",
            "battery_temp",
            "empty",
        ]),
        vol.Optional("slot", default=1): vol.Coerce(int),
    }
)


SEND_DASHBOARD_PERSON_TRACK_TELEGRAM_SCHEMA = vol.Schema(
    {
        vol.Optional("slot", default=1): vol.Coerce(int),
        vol.Optional("telegram_target"): cv.string,
        vol.Optional("chat_id"): cv.string,
    }
)


REPORT_LEGACY_OPTION_BY_ROLE_RUNTIME: dict[str, str] = {
    VEHICLE_ROLE_BATTERY_LEVEL: CONF_BATTERY_LEVEL_ENTITY,
    VEHICLE_ROLE_ENERGY_REMAINING: CONF_ENERGY_REMAINING_ENTITY,
    VEHICLE_ROLE_SPEED: CONF_SPEED_ENTITY,
    VEHICLE_ROLE_SHIFT_STATE: CONF_SHIFT_STATE_ENTITY,
    VEHICLE_ROLE_ODOMETER: CONF_ODOMETER_ENTITY,
    VEHICLE_ROLE_ELEVATION: CONF_ELEVATION_ENTITY,
    VEHICLE_ROLE_CLIMATE: CONF_CLIMATE_ENTITY,
    VEHICLE_ROLE_CHARGING_STATE: CONF_CHARGING_ENTITY,
    VEHICLE_ROLE_CHARGE_ENERGY_ADDED: CONF_CHARGE_ENERGY_ADDED_ENTITY,
    VEHICLE_ROLE_LOCATION_TRACKER: CONF_TRIP_MAP_TRACKER_ENTITY,
}


def get_panel_report_entity_entries(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return Flow-independent panel Reports Entity Manager entries.

    This store is authoritative for reports when present. Options Flow may still
    update legacy keys or vehicle_entity_map, but it should not override panel
    report selections.
    """
    raw = data.get(CONF_PANEL_REPORT_ENTITY_MAP, DEFAULT_PANEL_REPORT_ENTITY_MAP)
    if not isinstance(raw, list):
        return []
    result: list[dict[str, Any]] = []
    seen_roles: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        entity_id = str(item.get("entity_id") or "").strip()
        role = str(item.get("role") or "").strip()
        if not entity_id or not role or role in seen_roles:
            continue
        seen_roles.add(role)
        result.append({
            "entity_id": entity_id,
            "role": role,
            "label": str(item.get("label") or item.get("name") or role or entity_id),
            "use_report": True,
            "use_ai": bool(item.get("use_ai", False)),
            "use_alerts": bool(item.get("use_alerts", False)),
            "use_map": bool(item.get("use_map", role == VEHICLE_ROLE_LOCATION_TRACKER)),
            "source": str(item.get("source") or "panel_report_entity_map"),
        })
    return result


def get_panel_report_role_entity(data: dict[str, Any], role: str) -> str | None:
    """Return the panel-specific report entity for a role, if saved."""
    for item in get_panel_report_entity_entries(data):
        if item.get("role") != role:
            continue
        entity_id = str(item.get("entity_id") or "").strip()
        if entity_id:
            return entity_id
    return None


def bind_report_options_from_vehicle_map(data: dict[str, Any]) -> dict[str, Any]:
    """Make panel Reports Entity Manager selections drive report runtime keys.

    Priority:
    1. Flow-independent panel_report_entity_map.
    2. Existing vehicle_entity_map report rows.
    3. Legacy Options Flow report keys.

    This prevents later Options Flow edits from overriding report entities that
    were already saved from the app panel.
    """
    result = dict(data or {})

    panel_entries = get_panel_report_entity_entries(result)
    if panel_entries:
        result[CONF_PANEL_REPORT_ENTITY_MAP] = panel_entries
        for role, key in REPORT_LEGACY_OPTION_BY_ROLE_RUNTIME.items():
            selected = get_panel_report_role_entity(result, role)
            if selected:
                result[key] = selected
        return result

    entries = result.get(CONF_VEHICLE_ENTITY_MAP, DEFAULT_VEHICLE_ENTITY_MAP)
    if not isinstance(entries, list):
        return result
    for role, key in REPORT_LEGACY_OPTION_BY_ROLE_RUNTIME.items():
        selected = ""
        for item in entries:
            if not isinstance(item, dict):
                continue
            if str(item.get("role") or "") != role:
                continue
            if not bool(item.get("use_report")):
                continue
            entity_id = str(item.get("entity_id") or "").strip()
            if entity_id:
                selected = entity_id
                break
        if selected:
            result[key] = selected
    return result


def get_entry_config(entry: ConfigEntry) -> dict[str, Any]:
    """Return merged config entry data and options.

    Reports Entity Manager panel selections are authoritative and are overlaid
    onto the legacy report option keys so all report-generation code uses the
    panel-selected entities.
    """
    return bind_report_options_from_vehicle_map({
        **dict(entry.data),
        **dict(entry.options),
    })


def get_first_entry_config(hass: HomeAssistant) -> dict[str, Any] | None:
    """Return the first Tesla AI config."""
    entries = hass.config_entries.async_entries(DOMAIN)

    if not entries:
        return None

    return get_entry_config(entries[0])


def get_float_state(hass: HomeAssistant, entity_id: str | None, default: float = 0.0) -> float:
    """Read a Home Assistant entity state as float."""
    if not entity_id:
        return default

    value = hass.states.get(entity_id)

    if value is None:
        return default

    try:
        return float(value.state)
    except (TypeError, ValueError):
        return default


def get_state_text(hass: HomeAssistant, entity_id: str | None, default: str = "") -> str:
    """Read a Home Assistant entity state as text."""
    if not entity_id:
        return default

    value = hass.states.get(entity_id)

    if value is None:
        return default

    return str(value.state)


def safe_float(value: Any, default: float = 0.0) -> float:
    """Convert value to float safely."""
    if isinstance(value, str):
        normalized = (
            value.strip()
            .replace("\u00a0", "")
            .replace("TL/kWh", "")
            .replace("tl/kwh", "")
            .replace("TL", "")
            .replace("tl", "")
            .replace(",", ".")
        )
        try:
            return float(normalized)
        except (TypeError, ValueError):
            pass
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def get_bool_option(data: dict[str, Any], key: str, default: bool) -> bool:
    """Read a boolean option safely."""
    value = data.get(key, default)

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "on", "yes", "1"}:
            return True
        if lowered in {"false", "off", "no", "0"}:
            return False

    return bool(value)








def _score_clamp(value: float, min_value: float = 0.0, max_value: float = 100.0) -> float:
    return max(min_value, min(max_value, safe_float(value, 0.0)))


def _score_lower_is_better(value: float, ideal: float, bad: float, *, floor: float = 20.0) -> float:
    value = safe_float(value, 0.0)
    if value <= ideal:
        return 100.0
    if value >= bad:
        return floor
    return _score_clamp(100.0 - ((value - ideal) / max(0.001, bad - ideal) * (100.0 - floor)))


def _score_inside_band(value: float, low: float, high: float, *, penalty_per_unit: float = 2.0) -> float:
    value = safe_float(value, 0.0)
    if low <= value <= high:
        return 100.0
    if value < low:
        return _score_clamp(100.0 - ((low - value) * penalty_per_unit), 20.0, 100.0)
    return _score_clamp(100.0 - ((value - high) * penalty_per_unit), 20.0, 100.0)


def _trip_score_label(score: float, *, lang: str = "tr") -> str:
    score = safe_float(score, 0.0)
    is_en = str(lang or "").lower().startswith("en")
    if score >= 90:
        return "Excellent" if is_en else "Mükemmel"
    if score >= 80:
        return "Very good" if is_en else "Çok iyi"
    if score >= 70:
        return "Good" if is_en else "İyi"
    if score >= 55:
        return "Average" if is_en else "Orta"
    return "Needs attention" if is_en else "Dikkat"


def build_trip_score_fields(report_data: dict[str, Any] | None, *, lang: str = "tr") -> dict[str, Any]:
    """Return deterministic 0-100 driving score fields for report/AI/records."""
    data = report_data or {}
    consumption = safe_float(data.get("consumption_kwh_100km"), 0.0)
    congestion = safe_float(data.get("traffic_congestion_percent"), 0.0)
    traffic_delay_seconds = safe_float(data.get("traffic_delay_seconds"), 0.0)
    max_speed = safe_float(data.get("max_speed"), 0.0)
    moving_avg = safe_float(data.get("average_moving_speed", data.get("average_speed")), 0.0)
    elevation_range = safe_float(data.get("elevation_range"), 0.0)
    elevation_gain = safe_float(data.get("elevation_gain"), 0.0)
    elevation_loss = safe_float(data.get("elevation_loss"), 0.0)

    # Efficiency: practical EV band. Lower consumption is better.
    efficiency = _score_lower_is_better(consumption, 14.0, 28.0, floor=30.0) if consumption > 0 else 0.0

    # Traffic flow: standard free-flow delay percent is the headline. If it is missing,
    # fall back to older delay seconds so old/test reports still produce a score.
    if congestion > 0:
        traffic_flow = _score_lower_is_better(congestion, 8.0, 80.0, floor=20.0)
    elif traffic_delay_seconds > 0:
        traffic_flow = _score_lower_is_better(traffic_delay_seconds / 60.0, 3.0, 35.0, floor=35.0)
    else:
        traffic_flow = 100.0

    # Speed profile: this is not a speeding detector; it rewards smooth/normal driving.
    speed_score = 82.0
    if max_speed > 0:
        speed_score = _score_lower_is_better(max_speed, 95.0, 150.0, floor=35.0)
    if moving_avg > 0:
        # Extremely low moving average is usually traffic, already scored above; keep only a small penalty.
        if moving_avg < 12:
            speed_score = min(speed_score, 78.0)
        elif 18 <= moving_avg <= 95:
            speed_score = max(speed_score, 82.0)

    # Elevation: neutral when there is no meaningful elevation data, slight penalty for hard routes.
    elevation_intensity = max(elevation_range, (elevation_gain + elevation_loss) * 0.55)
    if elevation_intensity <= 0:
        elevation_score = 100.0
    else:
        elevation_score = _score_lower_is_better(elevation_intensity, 45.0, 420.0, floor=45.0)

    # Weather is only present in post-trip AI context unless caller enriches report_data.
    temp = safe_float(data.get("temperature_c"), 0.0)
    apparent = safe_float(data.get("apparent_temperature_c"), temp)
    wind = safe_float(data.get("wind_speed_kmh"), 0.0)
    precipitation = safe_float(data.get("precipitation_mm"), 0.0)
    weather_score = 100.0
    if temp or apparent or wind or precipitation:
        weather_score = _score_inside_band(apparent or temp, 8.0, 28.0, penalty_per_unit=2.2)
        if wind > 15:
            weather_score -= min(22.0, (wind - 15.0) * 0.8)
        if precipitation > 0:
            weather_score -= min(25.0, precipitation * 8.0)
        weather_score = _score_clamp(weather_score, 35.0, 100.0)

    if efficiency <= 0:
        # Test/partial reports without energy should not look broken.
        overall = (traffic_flow * 0.34) + (speed_score * 0.28) + (elevation_score * 0.18) + (weather_score * 0.20)
    else:
        overall = (efficiency * 0.35) + (traffic_flow * 0.25) + (speed_score * 0.20) + (elevation_score * 0.10) + (weather_score * 0.10)

    score = round(_score_clamp(overall), 0)
    lang_norm = "en" if str(lang or "").lower().startswith("en") else "tr"
    if lang_norm == "en":
        score_text = (
            f"{score:.0f}/100 · efficiency {efficiency:.0f} · traffic {traffic_flow:.0f} · "
            f"speed {speed_score:.0f} · elevation {elevation_score:.0f} · weather {weather_score:.0f}"
        )
    else:
        score_text = (
            f"{score:.0f}/100 · verimlilik {efficiency:.0f} · trafik {traffic_flow:.0f} · "
            f"hız {speed_score:.0f} · rakım {elevation_score:.0f} · hava {weather_score:.0f}"
        )

    return {
        "driving_score": int(score),
        "driving_score_label": _trip_score_label(score, lang=lang_norm),
        "driving_score_text": score_text,
        "score_efficiency": round(efficiency, 0),
        "score_traffic_flow": round(traffic_flow, 0),
        "score_speed_profile": round(speed_score, 0),
        "score_elevation_effect": round(elevation_score, 0),
        "score_weather_effect": round(weather_score, 0),
        "score_model": "pom_v1_weighted_efficiency_traffic_speed_elevation_weather",
    }


def enrich_trip_report_score(report_data: dict[str, Any], *, lang: str = "tr") -> dict[str, Any]:
    """Mutate and return report_data with grade analysis and driving score fields."""
    if isinstance(report_data, dict):
        enrich_trip_report_grade(report_data, lang=lang)
        report_data.update(build_trip_score_fields(report_data, lang=lang))
    return report_data

def is_trip_map_collection_enabled(data: dict[str, Any]) -> bool:
    """Return true when trip map collection is enabled or a map tracker is configured."""
    if get_bool_option(data, CONF_TRIP_MAP_ENABLED, DEFAULT_TRIP_MAP_ENABLED):
        return True
    tracker_entity = (
        get_vehicle_role_entity(data, VEHICLE_ROLE_LOCATION_TRACKER, usage_key="use_map")
        or data.get(CONF_TRIP_MAP_TRACKER_ENTITY, DEFAULT_TRIP_MAP_TRACKER_ENTITY)
    )
    return bool(str(tracker_entity or "").strip())

def get_tracker_lat_lon(hass: HomeAssistant, entity_id: str | None) -> tuple[float, float] | None:
    """Read latitude/longitude from a device_tracker-like entity."""
    if not entity_id:
        return None

    state = hass.states.get(entity_id)
    if state is None:
        return None

    lat = state.attributes.get("latitude")
    lon = state.attributes.get("longitude")

    try:
        return float(lat), float(lon)
    except (TypeError, ValueError):
        return None


def get_nominatim_address_parts(payload: dict[str, Any]) -> dict[str, str]:
    """Extract useful address parts from Nominatim response."""
    if not isinstance(payload, dict):
        return {}

    address = payload.get("address") if isinstance(payload.get("address"), dict) else {}
    if not address:
        return {}

    def _first(*keys: str) -> str:
        for key in keys:
            value = str(address.get(key) or "").strip()
            if value:
                return value
        return ""

    return {
        "house_number": _first("house_number"),
        "road": _first("road", "pedestrian", "footway", "residential", "path"),
        "neighbourhood": _first("neighbourhood", "quarter"),
        "suburb": _first("suburb", "city_district", "district"),
        "town": _first("town", "city", "municipality", "county"),
        "state": _first("state", "province"),
        "postcode": _first("postcode"),
        "country": _first("country"),
    }


def format_address_from_nominatim(payload: dict[str, Any]) -> str:
    """Return a precise compact address from Nominatim reverse-geocode response."""
    if not isinstance(payload, dict):
        return ""

    display_name = str(payload.get("display_name") or "").strip()
    parts_data = get_nominatim_address_parts(payload)

    if parts_data:
        parts: list[str] = []

        road = parts_data.get("road", "")
        house_number = parts_data.get("house_number", "")
        if road and house_number:
            parts.append(f"{road} No: {house_number}")
        elif road:
            parts.append(road)
        elif house_number:
            parts.append(f"No: {house_number}")

        for key in ("neighbourhood", "suburb", "town", "state", "postcode", "country"):
            value = parts_data.get(key, "")
            if value and value not in parts:
                parts.append(value)

        compact = ", ".join(parts)
        if compact:
            return compact

    return display_name


def get_reverse_geocode_cache(hass: HomeAssistant) -> dict[str, Any]:
    """Return integration-wide reverse geocode cache."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    return domain_data.setdefault("reverse_geocode_cache", {})


def get_cached_reverse_geocode_address(hass: HomeAssistant) -> str:
    """Return cached address when available."""
    cache = get_reverse_geocode_cache(hass)
    return str(cache.get("address") or "").strip()


def get_cached_reverse_geocode_parts(hass: HomeAssistant) -> dict[str, str]:
    """Return cached structured address parts when available."""
    cache = get_reverse_geocode_cache(hass)
    parts = cache.get("address_parts")
    return parts if isinstance(parts, dict) else {}


def build_short_location_label_from_parts(parts: dict[str, str] | None) -> str:
    """Return a compact location label suitable for monthly charging visuals."""
    parts = parts if isinstance(parts, dict) else {}
    suburb = str(parts.get("suburb") or "").strip()
    neighbourhood = str(parts.get("neighbourhood") or "").strip()
    town = str(parts.get("town") or "").strip()
    road = str(parts.get("road") or "").strip()

    labels: list[str] = []
    for value in (suburb, neighbourhood, town, road):
        if value and value not in labels:
            labels.append(value)

    if not labels:
        return ""
    if len(labels) == 1:
        return labels[0]
    first, second = labels[0], labels[1]
    combined = f"{first} · {second}"
    return combined if len(combined) <= 32 else first


def get_short_cached_reverse_geocode_label(hass: HomeAssistant) -> str:
    """Return a short cached location label for visuals and monthly ledgers."""
    label = build_short_location_label_from_parts(get_cached_reverse_geocode_parts(hass))
    if label:
        return label
    address = get_cached_reverse_geocode_address(hass)
    if not address:
        return ""
    first = str(address.split(",")[0] or "").strip()
    return first[:32]



def build_live_trip_ai_location_context(hass: HomeAssistant) -> dict[str, Any]:
    """Return cached street/neighbourhood context for Live Trip AI comments.

    Prefer reverse-geocoded street/neighbourhood parts. If the cache does not
    currently contain a street, fall back to the dashboard location-label sensor
    so the in-car Live Trip comment can still mention a meaningful place such as
    a neighbourhood/geofence instead of staying completely generic.
    """
    parts = get_cached_reverse_geocode_parts(hass)
    address = get_cached_reverse_geocode_address(hass)
    road = str(parts.get("road") or "").strip()
    neighbourhood = str(parts.get("neighbourhood") or "").strip()
    suburb = str(parts.get("suburb") or "").strip()
    town = str(parts.get("town") or "").strip()
    location_label = build_short_location_label_from_parts(parts) or get_short_cached_reverse_geocode_label(hass)
    dashboard_location_label = ""
    try:
        # This sensor is derived from the same location/geocode cache used by the
        # dashboard. It is used only as a read-only fallback for wording.
        st = hass.states.get("sensor.pom_tesla_dashboard_location_label")
        raw = str(getattr(st, "state", "") or "").strip() if st is not None else ""
        if raw and raw.lower() not in {"unknown", "unavailable", "none", "—"}:
            dashboard_location_label = raw[:80]
    except Exception:
        dashboard_location_label = ""
    if not location_label and dashboard_location_label:
        location_label = dashboard_location_label
    if not neighbourhood and dashboard_location_label and not road:
        neighbourhood = dashboard_location_label
    return {
        "current_address": address,
        "current_road": road,
        "current_neighbourhood": neighbourhood,
        "current_district": suburb,
        "current_town": town,
        "current_location_label": location_label,
        "current_dashboard_location_label": dashboard_location_label,
    }


async def async_update_reverse_geocode_cache(
    hass: HomeAssistant,
    data: dict[str, Any],
) -> None:
    """Update cached reverse-geocoded address when enabled and cache is stale."""
    if not get_bool_option(data, CONF_REVERSE_GEOCODING_ENABLED, DEFAULT_REVERSE_GEOCODING_ENABLED):
        return
    if not get_bool_option(data, CONF_REVERSE_GEOCODING_USE_IN_AI, DEFAULT_REVERSE_GEOCODING_USE_IN_AI):
        return

    tracker_entity = get_vehicle_role_entity(data, VEHICLE_ROLE_LOCATION_TRACKER) or str(
        data.get(CONF_TRIP_MAP_TRACKER_ENTITY, DEFAULT_TRIP_MAP_TRACKER_ENTITY) or ""
    ).strip()
    point = get_tracker_lat_lon(hass, tracker_entity)
    if point is None:
        return

    lat, lon = point
    cache = get_reverse_geocode_cache(hass)
    now_ts = datetime.now().timestamp()
    cache_minutes = max(5, int(safe_float(data.get(CONF_REVERSE_GEOCODING_CACHE_MINUTES), DEFAULT_REVERSE_GEOCODING_CACHE_MINUTES)))

    last_ts = safe_float(cache.get("updated_ts"), 0.0)
    last_lat = cache.get("lat")
    last_lon = cache.get("lon")
    try:
        moved_m = haversine_distance_meters(float(last_lat), float(last_lon), lat, lon)
    except Exception:
        moved_m = 999999.0

    if cache.get("address") and (now_ts - last_ts) < cache_minutes * 60 and moved_m < 100:
        return

    try:
        session = async_get_clientsession(hass)
        params = {
            "format": "jsonv2",
            "lat": f"{lat:.7f}",
            "lon": f"{lon:.7f}",
            "zoom": "18",
            "addressdetails": "1",
            "accept-language": "tr",
        }
        async with session.get(
            "https://nominatim.openstreetmap.org/reverse",
            params=params,
            headers={"User-Agent": "POMTeslaReport/1.2 HomeAssistant"},
            timeout=10,
        ) as response:
            if response.status != 200:
                _LOGGER.warning("POM reverse geocode failed: HTTP %s", response.status)
                return
            payload = await response.json()

        address = format_address_from_nominatim(payload)
        address_parts = get_nominatim_address_parts(payload)
        if address:
            cache.update({
                "address": address,
                "address_parts": address_parts,
                "raw_display_name": str(payload.get("display_name") or "").strip(),
                "lat": lat,
                "lon": lon,
                "updated_ts": now_ts,
                "tracker_entity": tracker_entity,
            })
    except Exception:
        _LOGGER.exception("POM reverse geocode update failed")


async def async_reverse_geocode_point_address(
    hass: HomeAssistant,
    lat: float,
    lon: float,
) -> str:
    """Reverse geocode an arbitrary latitude/longitude pair."""
    try:
        session = async_get_clientsession(hass)
        params = {
            "format": "jsonv2",
            "lat": f"{lat:.7f}",
            "lon": f"{lon:.7f}",
            "zoom": "18",
            "addressdetails": "1",
            "accept-language": "tr",
        }
        async with session.get(
            "https://nominatim.openstreetmap.org/reverse",
            params=params,
            headers={"User-Agent": "POMTeslaReport/1.2 HomeAssistant"},
            timeout=10,
        ) as response:
            if response.status != 200:
                return ""
            payload = await response.json()
        return format_address_from_nominatim(payload)
    except Exception:
        _LOGGER.debug("Trip reverse geocode lookup failed", exc_info=True)
        return ""


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Approximate distance between two coordinates in meters."""
    from math import asin, cos, radians, sin, sqrt

    radius = 6371000.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * asin(min(1.0, sqrt(a)))
    return radius * c



def _trip_grade_points(report_data: dict[str, Any]) -> list[dict[str, float]]:
    """Return route points with lat/lon/elevation for grade analysis."""
    raw_points = report_data.get("map_points")
    if not isinstance(raw_points, list):
        return []
    points: list[dict[str, float]] = []
    for item in raw_points:
        try:
            if isinstance(item, dict):
                lat = safe_float(item.get("lat", item.get("latitude")), 0.0)
                lon = safe_float(item.get("lon", item.get("longitude", item.get("lng"))), 0.0)
                elevation = item.get("elevation")
            elif isinstance(item, (list, tuple)) and len(item) >= 4:
                lat = safe_float(item[0], 0.0)
                lon = safe_float(item[1], 0.0)
                elevation = item[3]
            else:
                continue
            elev = safe_float(elevation, 999999.0)
            if lat == 0.0 and lon == 0.0:
                continue
            if elev == 999999.0:
                continue
            points.append({"lat": lat, "lon": lon, "elevation": elev})
        except Exception:
            continue
    return points


def build_trip_grade_report_fields(report_data: dict[str, Any] | None, *, lang: str = "tr") -> dict[str, Any]:
    """Build deterministic elevation/grade analysis fields for AI and PNG reports.

    This is intentionally conservative: short/noisy GPS segments are filtered,
    extreme grades are capped, and energy values are explicitly estimates.
    """
    data = report_data or {}
    is_en = str(lang or "").lower().startswith("en")
    points = _trip_grade_points(data)

    uphill_m = downhill_m = flat_m = 0.0
    gain_m = loss_m = 0.0
    weighted_up_grade = weighted_down_grade = 0.0
    max_up_grade = 0.0
    max_down_grade = 0.0
    segment_count = 0

    previous: dict[str, float] | None = None
    for point in points:
        if previous is None:
            previous = point
            continue
        dist_m = haversine_distance_meters(previous["lat"], previous["lon"], point["lat"], point["lon"])
        dz = point["elevation"] - previous["elevation"]
        previous = point

        # Filter GPS/elevation noise and impossible jumps.
        if dist_m < 25.0 or dist_m > 4000.0:
            continue
        if abs(dz) < 0.7:
            flat_m += dist_m
            segment_count += 1
            continue

        grade = max(-18.0, min(18.0, dz / max(1.0, dist_m) * 100.0))
        segment_count += 1

        if grade >= 1.0:
            uphill_m += dist_m
            gain_m += max(0.0, dz)
            weighted_up_grade += abs(grade) * dist_m
            max_up_grade = max(max_up_grade, grade)
        elif grade <= -1.0:
            downhill_m += dist_m
            loss_m += abs(min(0.0, dz))
            weighted_down_grade += abs(grade) * dist_m
            max_down_grade = min(max_down_grade, grade)
        else:
            flat_m += dist_m
            if dz > 0:
                gain_m += dz
            else:
                loss_m += abs(dz)

    total_m = uphill_m + downhill_m + flat_m
    point_count = len(points)

    # Fallback to existing elevation totals when route points are not rich enough.
    fallback_gain = safe_float(data.get("elevation_gain"), 0.0)
    fallback_loss = safe_float(data.get("elevation_loss"), 0.0)
    if total_m <= 0 and (fallback_gain > 0 or fallback_loss > 0):
        gain_m = fallback_gain
        loss_m = fallback_loss

    has_any = total_m > 0 or gain_m > 0 or loss_m > 0
    if not has_any:
        return {
            "elevation_grade_available": False,
            "elevation_grade_model": "pom_grade_v1_no_data",
        }

    uphill_ratio = (uphill_m / total_m * 100.0) if total_m > 0 else 0.0
    downhill_ratio = (downhill_m / total_m * 100.0) if total_m > 0 else 0.0
    flat_ratio = (flat_m / total_m * 100.0) if total_m > 0 else 0.0
    avg_up_grade = (weighted_up_grade / uphill_m) if uphill_m > 0 else 0.0
    avg_down_grade = -(weighted_down_grade / downhill_m) if downhill_m > 0 else 0.0

    intensity = max(gain_m + loss_m * 0.65, abs(gain_m - loss_m), safe_float(data.get("elevation_range"), 0.0))
    if intensity >= 220 or max_up_grade >= 9:
        impact = "high" if is_en else "yüksek"
    elif intensity >= 80 or max_up_grade >= 5:
        impact = "medium" if is_en else "orta"
    else:
        impact = "low" if is_en else "hafif"

    # Rough Model Y-like mass estimate; this is only for narrative context.
    vehicle_mass_kg = 2100.0
    climb_kwh = (vehicle_mass_kg * 9.81 * max(0.0, gain_m) / 3_600_000.0) / 0.86
    regen_kwh = (vehicle_mass_kg * 9.81 * max(0.0, loss_m) / 3_600_000.0) * 0.55

    if total_m > 0:
        if is_en:
            text = (
                f"+{gain_m:.0f}/-{loss_m:.0f} m · uphill {uphill_ratio:.0f}%"
                + (f" · steepest +{max_up_grade:.1f}%" if max_up_grade > 0 else "")
                + (f" / {max_down_grade:.1f}%" if max_down_grade < 0 else "")
                + f" · impact {impact}"
            )
        else:
            text = (
                f"+{gain_m:.0f}/-{loss_m:.0f} m · yokuş %{uphill_ratio:.0f}"
                + (f" · en dik +%{max_up_grade:.1f}" if max_up_grade > 0 else "")
                + (f" / %{max_down_grade:.1f}" if max_down_grade < 0 else "")
                + f" · etki {impact}"
            )
    else:
        text = (
            f"+{gain_m:.0f}/-{loss_m:.0f} m · impact {impact}" if is_en
            else f"+{gain_m:.0f}/-{loss_m:.0f} m · etki {impact}"
        )

    return {
        "elevation_grade_available": True,
        "elevation_grade_model": "pom_grade_v1_segment_filtered",
        "elevation_grade_text": text,
        "elevation_grade_confidence": "high" if segment_count >= 8 else ("medium" if segment_count >= 3 else "low"),
        "grade_segment_count": int(segment_count),
        "grade_point_count": int(point_count),
        "uphill_distance_km": round(uphill_m / 1000.0, 3),
        "downhill_distance_km": round(downhill_m / 1000.0, 3),
        "flat_distance_km": round(flat_m / 1000.0, 3),
        "uphill_ratio_percent": round(uphill_ratio, 1),
        "downhill_ratio_percent": round(downhill_ratio, 1),
        "flat_ratio_percent": round(flat_ratio, 1),
        "avg_uphill_grade_percent": round(avg_up_grade, 2),
        "avg_downhill_grade_percent": round(avg_down_grade, 2),
        "max_uphill_grade_percent": round(max_up_grade, 2),
        "max_downhill_grade_percent": round(max_down_grade, 2),
        "estimated_climb_energy_kwh": round(climb_kwh, 2),
        "estimated_regen_potential_kwh": round(regen_kwh, 2),
        "elevation_energy_impact_label": impact,
    }


def enrich_trip_report_grade(report_data: dict[str, Any], *, lang: str = "tr") -> dict[str, Any]:
    """Mutate and return report_data with grade/elevation analysis fields."""
    if isinstance(report_data, dict):
        report_data.update(build_trip_grade_report_fields(report_data, lang=lang))
    return report_data


def add_trip_map_point(
    trip_state: dict[str, Any],
    point: tuple[float, float] | None,
    *,
    min_movement_meters: float,
    force: bool = False,
    speed: float | None = None,
    elevation: float | None = None,
    ts: str | None = None,
) -> bool:
    """Append a route point to a tracking state if movement threshold allows it.

    alpha235: route points are stored as dicts with optional speed/elevation so
    trip maps can color segments by traffic and elevation. Old list-style points
    remain supported by renderers and readers.
    """
    if point is None:
        return False

    lat, lon = point
    points = trip_state.setdefault("map_points", [])
    if not isinstance(points, list):
        points = []
        trip_state["map_points"] = points

    def _point_lat_lon(value: Any) -> tuple[float, float] | None:
        try:
            if isinstance(value, dict):
                return float(value.get("lat")), float(value.get("lon"))
            if isinstance(value, (list, tuple)) and len(value) >= 2:
                return float(value[0]), float(value[1])
        except Exception:
            return None
        return None

    def _new_point() -> dict[str, Any]:
        item: dict[str, Any] = {"lat": round(float(lat), 7), "lon": round(float(lon), 7)}
        if speed is not None:
            item["speed"] = round(max(0.0, safe_float(speed, 0.0)), 2)
        if elevation is not None:
            item["elevation"] = round(safe_float(elevation, 0.0), 1)
        if ts:
            item["ts"] = str(ts)
        return item

    if not points:
        item = _new_point()
        points.append(item)
        trip_state["last_map_point"] = item
        trip_state["map_point_count"] = len(points)
        return True

    last_pair = _point_lat_lon(points[-1])
    if last_pair is None:
        item = _new_point()
        points.append(item)
        trip_state["last_map_point"] = item
        trip_state["map_point_count"] = len(points)
        return True

    last_lat, last_lon = last_pair
    distance = haversine_distance_meters(last_lat, last_lon, lat, lon)
    if force or distance >= max(0.0, min_movement_meters):
        item = _new_point()
        points.append(item)
        trip_state["last_map_point"] = item
        trip_state["map_point_count"] = len(points)
        return True

    return False


def get_trip_map_output_path_from_report(output_path: str) -> str:
    """Derive a map PNG output path from the trip report PNG output path."""
    if output_path.endswith("_report.png"):
        return output_path.replace("_report.png", "_map.png")
    if output_path.endswith(".png"):
        return output_path[:-4] + "_map.png"
    return f"{output_path}_map.png"


def build_trip_map_render_data(
    trip_state: dict[str, Any],
    report_data: dict[str, Any],
    *,
    title: str,
) -> dict[str, Any]:
    """Build render payload for a separate trip map image."""
    return {
        "title": title,
        "trip_km": report_data.get("trip_km"),
        "duration_text": report_data.get("duration_text"),
        "points": trip_state.get("map_points", []),
        "colored_analysis": True,
        "driving_score": report_data.get("driving_score"),
        "driving_score_label": report_data.get("driving_score_label"),
        "footer": f"Oluşturulma: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
    }


def update_trip_map_samples_for_active_states(
    hass: HomeAssistant,
    integration_data: dict[str, Any],
) -> None:
    """Collect route points for all active tracking modes."""
    if not is_trip_map_collection_enabled(integration_data):
        return

    tracker_entity = get_vehicle_role_entity(integration_data, VEHICLE_ROLE_LOCATION_TRACKER, usage_key="use_map") or integration_data.get(CONF_TRIP_MAP_TRACKER_ENTITY, DEFAULT_TRIP_MAP_TRACKER_ENTITY)
    point = get_tracker_lat_lon(hass, tracker_entity)
    if point is None:
        return

    speed_entity = get_report_configured_entity(integration_data, CONF_SPEED_ENTITY, VEHICLE_ROLE_SPEED)
    elevation_entity = get_report_configured_entity(integration_data, CONF_ELEVATION_ENTITY, VEHICLE_ROLE_ELEVATION)
    current_speed = get_float_state(hass, speed_entity, 0.0)
    current_elevation = get_float_state(hass, elevation_entity, 0.0)
    now_text = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

    min_movement = safe_float(
        integration_data.get(CONF_TRIP_MAP_MIN_MOVEMENT_METERS),
        DEFAULT_TRIP_MAP_MIN_MOVEMENT_METERS,
    )

    for state_key in (TRIP_STATE_KEY, MANUAL_TRACKING_STATE_KEY):
        trip_state = get_named_state(hass, state_key)
        if not trip_state.get("active"):
            continue
        if add_trip_map_point(
            trip_state,
            point,
            min_movement_meters=min_movement,
            force=False,
            speed=current_speed,
            elevation=current_elevation,
            ts=now_text,
        ):
            hass.data[DOMAIN][state_key] = trip_state


def get_report_type_label(state_key: str) -> str:
    """Return a Turkish label for the report/map type."""
    if state_key == MANUAL_TRACKING_STATE_KEY:
        return "Manuel Takip Haritası"
    return "Sürüş Haritası"


def get_report_type_short_caption(state_key: str) -> str:
    """Return Telegram caption for the separate map PNG."""
    if state_key == MANUAL_TRACKING_STATE_KEY:
        return "🗺️ Tesla AI - Manuel Takip Haritası"
    return "🗺️ Tesla AI - Son Sürüş Haritası"


def normalize_text_for_match(value: str) -> str:
    """Normalize Turkish text for simple command matching.

    Do not use ``str.maketrans`` here. Some incoming text or old files may
    contain mojibake variants such as ``Ã§`` or ``ÅŸ``. Those variants are
    multi-character strings, and ``str.maketrans`` only accepts one-character
    string keys. A plain replace loop is safer and prevents the Home Assistant
    error: ``string keys in translate table must be of length 1``.
    """
    text = str(value or "")

    replacements = {
        # Normal Turkish characters
        "Ç": "C",
        "Ğ": "G",
        "İ": "I",
        "Ö": "O",
        "Ş": "S",
        "Ü": "U",
        "Â": "A",
        "Î": "I",
        "Û": "U",
        "ç": "c",
        "ğ": "g",
        "ı": "i",
        "ö": "o",
        "ş": "s",
        "ü": "u",
        "â": "a",
        "î": "i",
        "û": "u",

        # Common mojibake / broken UTF-8 variants
        "Ã‡": "C",
        "Ã§": "c",
        "Äž": "G",
        "ÄŸ": "g",
        "Ä°": "I",
        "Ä±": "i",
        "Ã–": "O",
        "Ã¶": "o",
        "Åž": "S",
        "ÅŸ": "s",
        "Ãœ": "U",
        "Ã¼": "u",
    }

    for source, target in replacements.items():
        text = text.replace(source, target)

    text = text.lower().replace("i̇", "i")

    for ch in ["'", '"', "`", "?", "!", ",", ".", ":", ";", "(", ")", "[", "]"]:
        text = text.replace(ch, " ")

    return " ".join(text.split())


def _has_phrase(normalized_text: str, phrase: str) -> bool:
    """Return True when a normalized phrase appears as a token-bounded phrase.

    This avoids dangerous substring matches such as matching the verb ``ac`` inside
    ``arac``. All control routing should use this helper instead of raw ``in`` for
    short command words.
    """
    phrase_n = normalize_text_for_match(phrase)
    text = str(normalized_text or "")
    if not phrase_n or not text:
        return False
    return re.search(r"(?<![a-z0-9])" + re.escape(phrase_n) + r"(?![a-z0-9])", text) is not None


def _has_any_phrase(normalized_text: str, phrases: list[str] | tuple[str, ...] | set[str]) -> bool:
    """Return True if any token-bounded phrase is present."""
    return any(_has_phrase(normalized_text, phrase) for phrase in phrases if phrase)


def is_vehicle_status_question(message: str) -> bool:
    """Detect read-only vehicle status questions that must never become controls."""
    n = normalize_text_for_match(message)
    if not n:
        return False

    if _has_phrase(n, "sentry") and _has_any_phrase(n, ["acik", "kapali", "durum", "state"]):
        return True

    status_patterns = [
        "uyuyor mu", "uyuyor musun", "uyanik mi", "uyanik misin", "online mi", "cevrimici mi",
        "arac uyanik mi", "araba uyanik mi", "tesla uyanik mi", "arac uyuyor mu", "araba uyuyor mu",
        "sarj oluyor mu", "sarjda mi", "charging mi", "arac sarj oluyor mu", "araba sarj oluyor mu",
        "acik mi", "kapali mi", "kilitli mi", "kilitli misin", "kapilar acik mi", "kapi acik mi",
        "cam acik mi", "camlar acik mi", "pencere acik mi", "pencereler acik mi",
        "sentry acik mi", "sentry kapali mi", "klima acik mi", "klima kapali mi", "defrost acik mi",
        "icinde biri var mi", "aracta biri var mi", "kullanici var mi", "user present mi",
    ]
    if _has_any_phrase(n, status_patterns):
        return True

    # Generic Turkish question marker fallback for common read-only nouns.
    question_tokens = {"mi", "mu", "musun", "misin", "miyim", "miyiz"}
    tokens = set(n.split())
    if tokens.intersection(question_tokens):
        read_only_terms = [
            "uyanik", "uyuyor", "sarj", "charging", "acik", "kapali", "kilitli",
            "cam", "camlar", "pencere", "pencereler", "kapi", "kapilar", "sentry", "klima",
            "hiz", "batarya", "menzil", "sicaklik", "konum", "nerede", "nerdesin", "durum",
        ]
        if _has_any_phrase(n, read_only_terms):
            # Do not block polite commands like "şarjı başlatır mısın".
            explicit_command_terms = [
                "baslat", "calistir", "kilitle", "kilidi ac", "kilidini ac", "kapilari ac",
                "uyandir", "press", "turn on", "turn off", "set", "start", "stop", "enable", "disable",
            ]
            if not _has_any_phrase(n, explicit_command_terms):
                return True
    return False


def _format_binary_status_label(state: str, *, on_text: str, off_text: str, unknown_text: str = "bilinmiyor") -> str:
    value = str(state or "").lower().strip()
    if value in {"on", "true", "open", "opened", "active", "online", "awake", "awake_online", "home", "present"}:
        return on_text
    if value in {"off", "false", "closed", "inactive", "offline", "asleep", "asleep_or_offline", "not_home", "not present"}:
        return off_text
    return unknown_text


def _find_vehicle_entity_by_terms(hass: HomeAssistant, data: dict[str, Any], *, domain: str | None = None, required_terms: list[str] | tuple[str, ...] = (), any_terms: list[str] | tuple[str, ...] = ()) -> str:
    """Find a configured Vehicle Entity Manager entity by normalized entity/friendly text."""
    best: tuple[int, str] = (0, "")
    for entry in get_vehicle_entity_entries(data):
        entity_id = str(entry.get("entity_id") or "").strip()
        if not entity_id or "." not in entity_id:
            continue
        if domain and entity_id.split(".", 1)[0] != domain:
            continue
        st = hass.states.get(entity_id)
        text = _vehicle_entity_search_text(hass, entry)
        if required_terms and not all(_has_phrase(text, term) for term in required_terms):
            continue
        score = 10
        for term in any_terms:
            if _has_phrase(text, term):
                score += 20
        if st is not None and str(st.state).lower() not in {"unknown", "unavailable", "none", ""}:
            score += 5
        if score > best[0]:
            best = (score, entity_id)
    return best[1]


def detect_message_language(message: str) -> str:
    """Very small heuristic for deterministic status replies."""
    n = normalize_text_for_match(message)
    if not n:
        return "tr"

    english_markers = [
        "where", "is", "my", "car", "climate", "on", "off", "locked", "doors",
        "windows", "window", "charging", "awake", "asleep", "online", "status",
        "location", "address", "map", "sentry", "how", "many", "km", "drive", "drove",
        "driven", "trip", "trips", "month", "monthly", "summary", "records", "history",
    ]
    turkish_markers = [
        "arac", "araba", "arabam", "nerede", "nerdesin", "klima", "acik", "kapali",
        "sarj", "uyuyor", "uyanik", "kilitli", "kapi", "cam", "konum", "adres",
        "harita", "nobetci", "sentry", "ay", "bu ay", "km", "kac", "kaç", "surus",
        "sürüş", "gittim", "gitmisim", "gitmişim", "gezdim", "gecmis", "geçmiş", "ozet", "özet",
    ]

    english_score = sum(1 for marker in english_markers if f" {marker} " in f" {n} ")
    turkish_score = sum(1 for marker in turkish_markers if f" {marker} " in f" {n} ")

    if english_score > turkish_score and english_score > 0:
        return "en"
    if turkish_score > 0:
        return "tr"
    return "other"


def build_current_message_language_instruction(message: str) -> str:
    """Return a strong per-message language rule for deterministic and LLM paths."""
    lang = detect_message_language(message)
    if lang == "en":
        return (
            "CURRENT MESSAGE LANGUAGE RULE: The user's current message is in English. "
            "Reply fully in English. Do not default back to Turkish because earlier conversation was Turkish."
        )
    if lang == "other":
        return (
            "CURRENT MESSAGE LANGUAGE RULE: The user's current message is in a non-Turkish, non-English language. "
            "Reply fully in that same language. Do not translate it into Turkish or English unless the user asks."
        )
    return (
        "CURRENT MESSAGE LANGUAGE RULE: The user's current message is in Turkish. "
        "Reply fully in Turkish. Do not switch to English unless the user switches language."
    )


async def async_translate_ready_answer_if_needed(
    hass: HomeAssistant,
    data: dict[str, Any],
    *,
    user_message: str,
    ready_answer: str,
) -> str:
    """Translate a deterministic ready-made answer into the user's language when needed."""
    lang = detect_message_language(user_message)
    if lang in {"tr", "en"}:
        return ready_answer

    api_key = str(data.get(CONF_OPENAI_API_KEY, "")).strip()
    if not api_key:
        return ready_answer

    model = str(data.get(CONF_OPENAI_MODEL, DEFAULT_OPENAI_MODEL)).strip() or DEFAULT_OPENAI_MODEL
    system_prompt = (
        "You are a strict translation assistant. "
        "Translate the provided READY_ANSWER into the same language as USER_MESSAGE. "
        "Preserve meaning exactly. Preserve numbers, temperatures, URLs, coordinates, street names, and formatting. "
        "Do not add explanations. Do not summarize. Return only the translated answer text."
    )
    context_text = (
        f"USER_MESSAGE:\n{user_message}\n\n"
        f"READY_ANSWER:\n{ready_answer}\n\n"
        "Translate READY_ANSWER into the language of USER_MESSAGE."
    )
    try:
        translated = await async_call_openai_responses_api(
            hass,
            api_key=api_key,
            model=model,
            system_prompt=system_prompt,
            user_message="Translate the ready answer into the same language as the user message.",
            context_text=context_text,
            max_output_tokens=min(max(200, len(ready_answer) * 3), 1200),
        )
        return str(translated or ready_answer).strip() or ready_answer
    except Exception:
        return ready_answer


async def async_translate_runtime_message_if_needed(
    hass: HomeAssistant,
    data: dict[str, Any],
    *,
    user_message: str,
    message_text: str,
) -> str:
    """Translate runtime command/result messages into the user's current language."""
    lang = detect_message_language(user_message)
    if lang == "tr":
        return message_text

    api_key = str(data.get(CONF_OPENAI_API_KEY, "")).strip()
    if not api_key:
        return message_text

    model = str(data.get(CONF_OPENAI_MODEL, DEFAULT_OPENAI_MODEL)).strip() or DEFAULT_OPENAI_MODEL
    system_prompt = (
        "You are a strict translation assistant. "
        "Translate the provided MESSAGE_TEXT into the same language as USER_MESSAGE. "
        "Preserve meaning exactly. Preserve command names, temperatures, URLs, coordinates, street names, and formatting. "
        "Do not add explanations. Return only the translated message text."
    )
    context_text = (
        f"USER_MESSAGE:\n{user_message}\n\n"
        f"MESSAGE_TEXT:\n{message_text}\n\n"
        "Translate MESSAGE_TEXT into the language of USER_MESSAGE."
    )
    try:
        translated = await async_call_openai_responses_api(
            hass,
            api_key=api_key,
            model=model,
            system_prompt=system_prompt,
            user_message="Translate the message text into the same language as the user message.",
            context_text=context_text,
            max_output_tokens=min(max(160, len(message_text) * 3), 1200),
        )
        return str(translated or message_text).strip() or message_text
    except Exception:
        return message_text


def _get_vehicle_state_text(hass: HomeAssistant, data: dict[str, Any], *, lang: str = "tr") -> str:
    entity_id = (
        get_vehicle_role_entity(data, VEHICLE_ROLE_VEHICLE_STATE)
        or _find_vehicle_entity_by_terms(hass, data, domain="binary_sensor", any_terms=["status", "online", "awake"])
        or _find_vehicle_entity_by_terms(hass, data, any_terms=["status", "online", "awake"])
    )
    if not entity_id:
        if lang == "en":
            return "I can't read the vehicle sleep/online status right now because no vehicle status entity is configured in Vehicle Entity Manager."
        return "Uyku/online durumunu okuyacak araç durum entity'si seçili değil. Vehicle Entity Manager'da araç status/online entity'sini eklemek gerekiyor."
    st = hass.states.get(entity_id)
    if st is None:
        if lang == "en":
            return f"The selected vehicle status entity cannot be read right now: {entity_id}"
        return f"Araç durum entity'si seçili ama şu an okunamıyor: {entity_id}"
    if lang == "en":
        status = _format_binary_status_label(str(st.state), on_text="awake and online", off_text="asleep or offline", unknown_text="unclear")
        return f"The vehicle currently appears {status}."
    status = _format_binary_status_label(str(st.state), on_text="uyanık ve online", off_text="uykuda veya offline", unknown_text="belirsiz")
    return f"Araç şu an {status} görünüyor."


def _get_simple_binary_answer(
    hass: HomeAssistant,
    entity_id: str,
    *,
    label: str,
    on_text: str,
    off_text: str,
    lang: str = "tr",
    missing_text_en: str | None = None,
) -> str:
    st = hass.states.get(entity_id) if entity_id else None
    if st is None:
        if lang == "en":
            return missing_text_en or f"The entity for {label} cannot be read right now."
        return f"{label} için ilgili entity şu an okunamıyor."
    unknown = "unclear" if lang == "en" else "belirsiz"
    status = _format_binary_status_label(str(st.state), on_text=on_text, off_text=off_text, unknown_text=unknown)
    if lang == "en":
        return f"{label.capitalize()} appears {status}."
    return f"{label} {status} görünüyor."


def build_direct_vehicle_status_answer(hass: HomeAssistant, data: dict[str, Any], message: str) -> str | None:
    """Answer common read-only vehicle questions before the control router or LLM."""
    n = normalize_text_for_match(message)
    if not n or not is_vehicle_status_question(message):
        return None
    lang = detect_message_language(message)
    if lang == "other":
        lang = "tr"

    # Awake / online / sleep status.
    if _has_any_phrase(n, ["uyanik", "uyuyor", "online", "cevrimici", "sleep", "asleep", "awake"]):
        return _get_vehicle_state_text(hass, data, lang=lang)

    # Charging status.
    if _has_any_phrase(n, ["sarj oluyor", "sarjda", "charging"]):
        entity_id = (
            get_vehicle_role_entity(data, VEHICLE_ROLE_CHARGING_STATE)
            or _find_vehicle_entity_by_terms(hass, data, domain="binary_sensor", required_terms=["charging"])
            or _find_vehicle_entity_by_terms(hass, data, domain="binary_sensor", required_terms=["sarj"])
        )
        if lang == "en":
            return _get_simple_binary_answer(
                hass,
                entity_id,
                label="vehicle charging status",
                on_text="charging",
                off_text="not charging",
                lang=lang,
                missing_text_en="The charging status entity cannot be read right now.",
            )
        return _get_simple_binary_answer(hass, entity_id, label="araç şarj durumu", on_text="şarj oluyor", off_text="şarj olmuyor", lang=lang)

    # Climate state.
    if _has_phrase(n, "klima") or _has_phrase(n, "climate"):
        entity_id = get_vehicle_role_entity(data, VEHICLE_ROLE_CLIMATE) or _find_vehicle_entity_by_terms(hass, data, domain="climate", any_terms=["climate", "klima"])
        st = hass.states.get(entity_id) if entity_id else None
        if st is None:
            return "The climate entity cannot be read right now." if lang == "en" else "Klima entity'si şu an okunamıyor."
        state = str(st.state or "").lower()
        if state in {"off", "unavailable", "unknown", "none", ""}:
            return "Climate appears off." if lang == "en" else "Klima kapalı görünüyor."
        return f"Climate appears on. Mode: {st.state}." if lang == "en" else f"Klima açık görünüyor. Mod: {st.state}."

    # Sentry mode state. Keep this deterministic so chat memory cannot override
    # the actual Home Assistant switch state.
    if _has_phrase(n, "sentry") or _has_phrase(n, "nobetci"):
        cap = _capability_by_name("sentry_mode")
        entity_id = find_entity_for_manifest_capability(hass, data, cap) if cap else ""
        if not entity_id:
            entity_id = _find_vehicle_entity_by_terms(hass, data, domain="switch", any_terms=["sentry", "nobetci"])
        st = hass.states.get(entity_id) if entity_id else None
        if st is None:
            return "The Sentry Mode entity cannot be read right now." if lang == "en" else "Sentry Mode entity'si şu an okunamıyor."
        state = str(st.state or "").lower()
        if state in {"on", "true", "active"}:
            return "Sentry Mode appears on." if lang == "en" else "Sentry Mode açık görünüyor."
        if state in {"off", "false", "inactive"}:
            return "Sentry Mode appears off." if lang == "en" else "Sentry Mode kapalı görünüyor."
        return f"Sentry Mode status is unclear: {st.state}." if lang == "en" else f"Sentry Mode durumu belirsiz görünüyor: {st.state}."

    if _has_any_phrase(n, ["kilitli", "kilitsiz", "kilidi", "kilit", "lock", "unlock", "locked", "unlocked"]):
        entity_id = get_vehicle_role_entity(data, VEHICLE_ROLE_LOCK_STATE) or _find_vehicle_entity_by_terms(hass, data, domain="lock", any_terms=["lock", "kilit"])
        st = hass.states.get(entity_id) if entity_id else None
        if st is None:
            return "The lock status entity cannot be read right now." if lang == "en" else "Kilit durumu entity'si şu an okunamıyor."
        state = str(st.state or "").lower()
        if state in {"locked", "lock", "on"}:
            return "The vehicle appears locked." if lang == "en" else "Araç kilitli görünüyor."
        if state in {"unlocked", "unlock", "off"}:
            return "The vehicle appears unlocked." if lang == "en" else "Araç kilidi açık görünüyor."
        return f"Lock status is unclear: {st.state}." if lang == "en" else f"Kilit durumu belirsiz görünüyor: {st.state}."

    # Windows / doors. Specific windows first.
    if _has_any_phrase(n, ["cam", "camlar", "pencere", "pencereler", "window", "windows"]):
        terms = ["window"]
        label = "camlar"
        if _has_any_phrase(n, ["sol arka", "arka sol", "rear left", "left rear"]):
            terms = ["rear", "driver", "window"]
            label = "sol arka cam"
        elif _has_any_phrase(n, ["sag arka", "arka sag", "rear right", "right rear"]):
            terms = ["rear", "passenger", "window"]
            label = "sağ arka cam"
        elif _has_any_phrase(n, ["sol on", "on sol", "front left", "left front", "surucu"]):
            terms = ["front", "driver", "window"]
            label = "sol ön cam"
        elif _has_any_phrase(n, ["sag on", "on sag", "front right", "right front", "yolcu"]):
            terms = ["front", "passenger", "window"]
            label = "sağ ön cam"
        entity_id = _find_vehicle_entity_by_terms(hass, data, domain="binary_sensor", required_terms=terms)
        if not entity_id and label == "camlar":
            entity_id = _find_vehicle_entity_by_terms(hass, data, domain="binary_sensor", any_terms=["windows", "window", "cam"])
        if lang == "en":
            label_en = {
                "camlar": "windows",
                "sol arka cam": "rear left window",
                "sağ arka cam": "rear right window",
                "sol ön cam": "front left window",
                "sağ ön cam": "front right window",
            }.get(label, "windows")
            return _get_simple_binary_answer(hass, entity_id, label=label_en, on_text="open", off_text="closed", lang=lang)
        return _get_simple_binary_answer(hass, entity_id, label=label, on_text="açık", off_text="kapalı", lang=lang)

    if _has_any_phrase(n, ["kapi", "kapilar", "door", "doors"]):
        entity_id = _find_vehicle_entity_by_terms(hass, data, domain="binary_sensor", any_terms=["doors", "door", "kapi"])
        if lang == "en":
            return _get_simple_binary_answer(hass, entity_id, label="doors", on_text="open", off_text="closed", lang=lang)
        return _get_simple_binary_answer(hass, entity_id, label="kapılar", on_text="açık", off_text="kapalı", lang=lang)

    return None


async def async_build_direct_vehicle_status_answer(hass: HomeAssistant, data: dict[str, Any], message: str) -> str | None:
    """Build a deterministic direct status answer and localize it when needed."""
    answer = build_direct_vehicle_status_answer(hass, data, message)
    if not answer:
        return None
    return await async_translate_ready_answer_if_needed(
        hass,
        data,
        user_message=message,
        ready_answer=answer,
    )


def should_send_last_trip_png(user_message: str) -> bool:
    """Return True when the Telegram message asks for the last trip PNG/report."""
    normalized = normalize_text_for_match(user_message)
    trip_terms = [
        "son surus",
        "son surusum",
        "surus png",
        "surus rapor",
        "surus gorsel",
        "surus resmi",
        "trip png",
        "trip report",
        "last trip",
        "last trip report",
        "latest trip",
        "latest trip report",
        "/triplast",
    ]
    image_terms = [
        "png",
        "gorsel",
        "resim",
        "foto",
        "rapor",
        "raporu",
        "gonder",
        "at",
        "atsana",
        "goster",
        "show",
        "send",
        "report",
    ]
    return any(term in normalized for term in trip_terms) and any(term in normalized for term in image_terms)


def should_send_last_trip_map(user_message: str) -> bool:
    """Return True when the Telegram message asks for the last trip map."""
    normalized = normalize_text_for_match(user_message)
    map_terms = ["harita", "rota", "map"]
    trip_terms = ["son surus", "son surusum", "surus", "trip"]
    send_terms = ["gonder", "at", "atsana", "goster", "png", "resim", "gorsel"]
    return (
        any(term in normalized for term in map_terms)
        and any(term in normalized for term in trip_terms)
        and any(term in normalized for term in send_terms)
    )


def get_latest_existing_file(paths: list[str]) -> str | None:
    """Return the newest existing file among candidate paths."""
    existing: list[Path] = []
    for item in paths:
        try:
            path = Path(item)
            if path.exists():
                existing.append(path)
        except Exception:
            continue

    if not existing:
        return None

    existing.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return str(existing[0])


def get_latest_trip_report_info(hass: HomeAssistant) -> dict[str, Any] | None:
    """Return the latest available trip report and map info."""
    candidates: list[dict[str, Any]] = []

    for state_key, caption, fallback_paths, fallback_map_paths in [
        (
            TRIP_STATE_KEY,
            "🚗 Tesla AI - Son Otomatik Sürüş Raporu",
            [DEFAULT_AUTO_TRIP_IMAGE_OUTPUT_PATH, DEFAULT_TRIP_IMAGE_OUTPUT_PATH],
            [DEFAULT_AUTO_TRIP_MAP_OUTPUT_PATH, DEFAULT_FINAL_TRIP_MAP_OUTPUT_PATH],
        ),
        (
            MANUAL_TRACKING_STATE_KEY,
            "🚗 Tesla AI - Son Manuel Takip Raporu",
            [DEFAULT_MANUAL_TRACKING_IMAGE_OUTPUT_PATH, DEFAULT_MANUAL_TRIP_IMAGE_OUTPUT_PATH],
            [DEFAULT_MANUAL_TRACKING_MAP_OUTPUT_PATH],
        ),
    ]:
        state = get_named_state(hass, state_key)
        report_path = str(state.get("last_report_path") or "").strip()
        if not report_path or not Path(report_path).exists():
            report_path = get_latest_existing_file(fallback_paths) or ""

        map_path = str(state.get("last_map_path") or "").strip()
        if not map_path or not Path(map_path).exists():
            map_path = get_latest_existing_file(fallback_map_paths) or ""

        if not report_path and not map_path:
            continue

        timestamp = 0.0
        for candidate in [report_path, map_path]:
            if candidate:
                try:
                    timestamp = max(timestamp, Path(candidate).stat().st_mtime)
                except Exception:
                    pass

        report_data = state.get("last_report_data") if isinstance(state.get("last_report_data"), dict) else {}
        candidates.append({
            "state_key": state_key,
            "caption": caption,
            "path": report_path,
            "map_path": map_path,
            "report_data": report_data,
            "timestamp": timestamp,
        })

    if not candidates:
        return None

    candidates.sort(key=lambda item: item.get("timestamp", 0.0), reverse=True)
    return candidates[0]


def redact_sensitive_config_value(key: str, value: Any) -> Any:
    """Redact sensitive config values before debug output."""
    key_text = str(key).lower()

    if "api_key" in key_text or "token" in key_text or "secret" in key_text:
        text = str(value or "")
        if not text:
            return ""
        if len(text) <= 8:
            return "********"
        return f"{text[:4]}...{text[-4:]}"

    return value


def extract_openai_response_text(response_data: dict[str, Any]) -> str:
    """Extract assistant text from an OpenAI Responses API payload."""
    output_text = response_data.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    parts: list[str] = []

    for item in response_data.get("output", []) or []:
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []) or []:
            if not isinstance(content, dict):
                continue
            text = content.get("text")
            if isinstance(text, str) and text.strip():
                parts.append(text.strip())

    return "\n".join(parts).strip()


def get_device_id_for_entity(hass: HomeAssistant, entity_id: str | None) -> str | None:
    """Return the device_id behind an entity registry entry."""
    if not entity_id:
        return None
    try:
        entity_reg = er.async_get(hass)
        entry = entity_reg.async_get(entity_id)
        if entry is not None:
            return entry.device_id
    except Exception:
        return None
    return None


def get_entities_for_device(hass: HomeAssistant, device_id: str | None) -> list[str]:
    """Return all enabled entities attached to a Home Assistant device."""
    if not device_id:
        return []
    try:
        entity_reg = er.async_get(hass)
        entries = er.async_entries_for_device(entity_reg, device_id, include_disabled_entities=False)
        return sorted({entry.entity_id for entry in entries if entry.entity_id})
    except Exception:
        try:
            entity_reg = er.async_get(hass)
            found = []
            for entry in getattr(entity_reg, "entities", {}).values():
                if getattr(entry, "device_id", None) == device_id and getattr(entry, "entity_id", None):
                    found.append(entry.entity_id)
            return sorted(set(found))
        except Exception:
            return []


def get_device_label(hass: HomeAssistant, device_id: str | None) -> str:
    """Return a readable device label."""
    if not device_id:
        return "seçilmemiş"
    try:
        device_reg = dr.async_get(hass)
        device = device_reg.async_get(device_id)
        if device is None:
            return device_id
        return device.name_by_user or device.name or device.model or device_id
    except Exception:
        return device_id


def clean_entity_state_for_ai(value: Any) -> str:
    """Compact entity state for AI context."""
    text = str(value if value is not None else "").strip()
    if len(text) > 90:
        return text[:87] + "..."
    return text


def normalize_entity_list(value: Any) -> list[str]:
    """Normalize entity list options coming from HA selectors."""
    if value is None:
        return []
    if isinstance(value, str):
        candidates = [part.strip() for part in value.replace("\n", ",").split(",")]
    elif isinstance(value, (list, tuple, set)):
        candidates = [str(part).strip() for part in value]
    else:
        candidates = [str(value).strip()]

    result: list[str] = []
    for entity_id in candidates:
        if entity_id and entity_id not in result:
            result.append(entity_id)
    return result


def get_panel_ai_entity_entries(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return Flow-independent panel AI Entity Manager entries."""
    raw = data.get(CONF_PANEL_AI_ENTITY_MAP, DEFAULT_PANEL_AI_ENTITY_MAP)
    if not isinstance(raw, list):
        return []
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        entity_id = str(item.get("entity_id") or "").strip()
        if not entity_id or entity_id in seen:
            continue
        seen.add(entity_id)
        result.append({
            "entity_id": entity_id,
            "role": str(item.get("role") or VEHICLE_ROLE_OTHER),
            "label": str(item.get("label") or item.get("name") or item.get("role") or entity_id),
            "use_report": bool(item.get("use_report", False)),
            "use_ai": bool(item.get("use_ai", True)),
            "use_alerts": bool(item.get("use_alerts", False)),
            "use_map": bool(item.get("use_map", False)),
            "source": str(item.get("source") or "panel_ai_entity_map"),
        })
    return result


def get_vehicle_entity_entries(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return central Vehicle Entity Manager entries with panel stores overlaid.

    Panel stores are authoritative for their own surfaces. This keeps AI/report
    behavior stable even when Options Flow later changes the older shared map.
    """
    raw = data.get(CONF_VEHICLE_ENTITY_MAP, DEFAULT_VEHICLE_ENTITY_MAP)
    result: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add_item(item: dict[str, Any], *, force_ai: bool | None = None, force_report: bool | None = None) -> None:
        entity_id = str(item.get("entity_id") or "").strip()
        if not entity_id or entity_id in seen:
            return
        seen.add(entity_id)
        result.append({
            "entity_id": entity_id,
            "role": str(item.get("role") or "other"),
            "label": str(item.get("label") or item.get("role") or entity_id),
            "use_report": bool(force_report if force_report is not None else item.get("use_report", False)),
            "use_ai": bool(force_ai if force_ai is not None else item.get("use_ai", True)),
            "use_alerts": bool(item.get("use_alerts", False)),
            "use_map": bool(item.get("use_map", False)),
            "source": str(item.get("source") or "manual"),
        })

    for item in get_panel_ai_entity_entries(data):
        add_item(item, force_ai=True)
    for item in get_panel_report_entity_entries(data):
        add_item(item, force_report=True)
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict):
                add_item(item)
    return result


def get_vehicle_entities_for_usage(data: dict[str, Any], usage_key: str) -> list[str]:
    """Return central entity ids for a usage flag: use_report/use_ai/use_alerts/use_map."""
    result: list[str] = []
    for item in get_vehicle_entity_entries(data):
        if item.get(usage_key):
            entity_id = item.get("entity_id")
            if entity_id and entity_id not in result:
                result.append(entity_id)
    return result


def get_vehicle_role_entity(data: dict[str, Any], role: str, *, usage_key: str | None = None) -> str | None:
    """Return the first central entity matching a semantic role."""
    for item in get_vehicle_entity_entries(data):
        if item.get("role") != role:
            continue
        if usage_key and not item.get(usage_key):
            continue
        entity_id = str(item.get("entity_id") or "").strip()
        if entity_id:
            return entity_id
    return None


def get_configured_entity(data: dict[str, Any], legacy_key: str, role: str, *, usage_key: str | None = None) -> str | None:
    """Return panel-selected central report role first, then legacy config fallback."""
    bound = bind_report_options_from_vehicle_map(data)
    return get_vehicle_role_entity(bound, role, usage_key=usage_key) or bound.get(legacy_key)


def get_report_configured_entity(data: dict[str, Any], legacy_key: str, role: str) -> str | None:
    """Return the report-runtime entity from the panel Reports map.

    alpha225 rule:
    - If the panel Reports Entity Manager has any saved rows, it becomes the
      authoritative source for report/live-trip/manual tracking entities.
    - In that case, missing roles intentionally return None instead of falling
      back to stale Options Flow / old Vehicle Map values.
    - Only installations with no panel Reports map at all fall back to the old
      compatibility path.
    """
    panel_entries = get_panel_report_entity_entries(data)
    if panel_entries:
        selected = get_panel_report_role_entity(data, role)
        return str(selected or "").strip() or None

    bound = bind_report_options_from_vehicle_map(data)
    selected = get_vehicle_role_entity(bound, role, usage_key="use_report")
    if selected:
        return selected
    legacy = str(bound.get(legacy_key) or "").strip()
    return legacy or None


def average_speed_distance_over_moving_time(distance_km: float, moving_seconds: float) -> float:
    """Tessie-style average speed: distance divided by moving time.

    This is different from a raw time-weighted average of speed samples. It
    matches the observed Tessie presentation more closely because parked/idle
    time is excluded from the denominator.
    """
    distance = max(0.0, safe_float(distance_km, 0.0))
    moving = max(0.0, safe_float(moving_seconds, 0.0))
    if distance <= 0 or moving <= 0:
        return 0.0
    return distance / (moving / 3600.0)


def get_vehicle_entity_context_lines(hass: HomeAssistant, data: dict[str, Any]) -> list[str]:
    """Return a readable list of central entity entries for AI/debug context."""
    entries = get_vehicle_entity_entries(data)
    if not entries:
        return ["- Merkezi Vehicle Entity Manager listesi boş."]
    lines = []
    for item in entries[:80]:
        state = hass.states.get(item["entity_id"])
        state_text = clean_entity_state_for_ai(state.state) if state is not None else "not_found"
        unit = ""
        friendly = item.get("label") or item.get("role")
        if state is not None:
            attrs = state.attributes or {}
            unit = str(attrs.get("unit_of_measurement") or "")
            friendly = friendly or str(attrs.get("friendly_name") or "")
        uses = []
        if item.get("use_report"):
            uses.append("report")
        if item.get("use_ai"):
            uses.append("ai")
        if item.get("use_alerts"):
            uses.append("alerts")
        if item.get("use_map"):
            uses.append("map")
        lines.append(f"- {item.get('role')}: {item['entity_id']} = {state_text}{(' ' + unit) if unit else ''} | {friendly} | uses={','.join(uses)}")
    return lines


def get_extra_ai_context_entities(data: dict[str, Any]) -> list[str]:
    """Return manually added AI context entities, preferring panel AI store."""
    panel_entries = get_panel_ai_entity_entries(data)
    if panel_entries:
        return dedupe_entities([str(item.get("entity_id") or "") for item in panel_entries if item.get("use_ai") and item.get("entity_id")])
    return normalize_entity_list(data.get(CONF_AI_EXTRA_CONTEXT_ENTITIES, DEFAULT_AI_EXTRA_CONTEXT_ENTITIES))


def get_excluded_ai_context_entities(data: dict[str, Any]) -> list[str]:
    """Return manually excluded AI context entities."""
    return normalize_entity_list(data.get(CONF_AI_EXCLUDED_CONTEXT_ENTITIES, DEFAULT_AI_EXCLUDED_CONTEXT_ENTITIES))


def dedupe_entities(entity_ids: list[str]) -> list[str]:
    """Dedupe entity IDs while preserving order."""
    result: list[str] = []
    for entity_id in entity_ids:
        entity_id = str(entity_id or "").strip()
        if entity_id and entity_id not in result:
            result.append(entity_id)
    return result


def important_entity_attributes_for_ai(state) -> list[str]:
    """Return compact important attributes for selected Tesla/Home Assistant entities."""
    attrs = state.attributes or {}
    important_keys = [
        "unit_of_measurement",
        "device_class",
        "friendly_name",
        "latitude",
        "longitude",
        "gps_accuracy",
        "battery_level",
        "battery_range",
        "current_temperature",
        "temperature",
        "outside_temperature",
        "ambient_temperature",
        "outside_temp",
        "inside_temp",
        "hvac_action",
        "hvac_modes",
        "available",
        "formatted_address",
        "postal_town",
        "destination",
        "active_route_destination",
        "tire_pressure",
        "warning",
        "user_present",
        "presence",
        "occupancy",
        "icon",
    ]
    parts: list[str] = []
    for key in important_keys:
        if key not in attrs:
            continue
        val = attrs.get(key)
        if isinstance(val, (list, tuple, set)):
            val = ",".join(str(x) for x in list(val)[:6])
        elif isinstance(val, dict):
            continue
        text = clean_entity_state_for_ai(val)
        if text and text.lower() not in {"none", "unknown", "unavailable"}:
            parts.append(f"{key}={text}")
    return parts[:6]


def ai_entity_match_text(entity_id: str, state: Any | None = None) -> str:
    """Return combined searchable text for an entity."""
    parts = [entity_id]
    if state is not None:
        attrs = getattr(state, "attributes", {}) or {}
        friendly = attrs.get("friendly_name")
        device_class = attrs.get("device_class")
        unit = attrs.get("unit_of_measurement")
        if friendly:
            parts.append(str(friendly))
        if device_class:
            parts.append(str(device_class))
        if unit:
            parts.append(str(unit))
    return " ".join(parts).lower()


def ai_entity_priority_score(entity_id: str, state: Any | None = None) -> int:
    """Score entities so important Tesla/Tessie data survives context limits."""
    text = ai_entity_match_text(entity_id, state)
    score = 0
    priority_groups = [
        (120, ["battery module temperature", "module temperature", "battery temp", "battery_temperature", "battery temperature", "pack temperature", "battery_pack_temperature"]),
        (115, ["outside temperature", "outside_temp", "ambient temperature", "ambient_temperature", "exterior temperature", "external temperature"]),
        (110, ["battery", "charge", "charger", "energy", "range"]),
        (100, ["speed", "odometer", "shift", "gear", "drive", "elevation", "heading", "power"]),
        (95, ["location", "gps", "latitude", "longitude", "address", "route", "destination", "tracker"]),
        (90, ["climate", "hvac", "temperature", "temp", "seat heater", "steering heater", "defrost"]),
        (80, ["tire", "pressure", "tpms"]),
        (85, ["user present", "user_present", "presence", "occupancy", "occupied", "occupant"]),
        (75, ["door", "window", "lock", "sentry", "valet", "trunk", "frunk"]),
        (40, ["switch.", "button.", "cover.", "lock."]),
    ]
    for points, keywords in priority_groups:
        if any(keyword in text for keyword in keywords):
            score += points
    if getattr(state, "state", None) not in {None, "unknown", "unavailable", "none", ""}:
        score += 10
    return score


def sort_ai_entities_by_priority(hass: HomeAssistant, entity_ids: list[str]) -> list[str]:
    """Sort entities by Tesla relevance while keeping deterministic order."""
    return sorted(
        entity_ids,
        key=lambda eid: (
            -ai_entity_priority_score(eid, hass.states.get(eid)),
            categorize_entity_for_ai(eid, hass.states.get(eid)),
            eid,
        ),
    )


def categorize_entity_for_ai(entity_id: str, state: Any | None = None) -> str:
    """Categorize entities so the prompt is easier for the model to use."""
    e = ai_entity_match_text(entity_id, state)
    if any(k in e for k in ["battery", "charge", "charger", "energy", "range"]):
        return "Batarya / şarj"
    if any(k in e for k in ["speed", "odometer", "shift", "gear", "drive", "elevation", "heading", "power"]):
        return "Sürüş / hareket"
    if any(k in e for k in ["location", "gps", "latitude", "longitude", "route", "destination", "address", "tracker"]):
        return "Konum / rota"
    if any(k in e for k in ["climate", "temperature", "temp", "ambient", "outside", "exterior", "seat_heater", "seat heater", "steering heater", "hvac", "defrost"]):
        return "Klima / sıcaklık"
    if any(k in e for k in ["user present", "user_present", "presence", "occupancy", "occupied", "occupant"]):
        return "Kullanıcı / varlık"
    if any(k in e for k in ["door", "window", "lock", "trunk", "frunk", "sentry", "valet"]):
        return "Güvenlik / kapılar"
    if any(k in e for k in ["tire", "pressure", "tpms"]):
        return "Lastik / basınç"
    if entity_id.startswith("switch.") or entity_id.startswith("button.") or entity_id.startswith("cover.") or entity_id.startswith("lock."):
        return "Kontrol entity’leri (bilgi amaçlı)"
    return "Diğer Tesla verileri"

def get_core_ai_entities(data: dict[str, Any]) -> list[str]:
    """Return manually configured core entities for AI context."""
    keys = [
        CONF_SHIFT_STATE_ENTITY,
        CONF_SPEED_ENTITY,
        CONF_ODOMETER_ENTITY,
        CONF_BATTERY_LEVEL_ENTITY,
        CONF_ENERGY_REMAINING_ENTITY,
        CONF_ELEVATION_ENTITY,
        CONF_CLIMATE_ENTITY,
        CONF_CHARGING_ENTITY,
        CONF_CHARGE_ENERGY_ADDED_ENTITY,
        CONF_TRIP_MAP_TRACKER_ENTITY,
    ]
    entities: list[str] = []
    for entity_id in get_vehicle_entities_for_usage(data, "use_ai"):
        if entity_id and entity_id not in entities:
            entities.append(entity_id)
    for key in keys:
        entity_id = str(data.get(key) or "").strip()
        if entity_id and entity_id not in entities:
            entities.append(entity_id)
    main_entity = str(data.get(CONF_AI_MAIN_TESLA_ENTITY, DEFAULT_AI_MAIN_TESLA_ENTITY) or "").strip()
    if main_entity and main_entity not in entities:
        entities.append(main_entity)
    return entities


def discover_ai_entities_from_main_device(hass: HomeAssistant, data: dict[str, Any]) -> tuple[list[str], str]:
    """Discover entities by selecting a main Tesla entity and finding its Home Assistant device."""
    main_entity = str(data.get(CONF_AI_MAIN_TESLA_ENTITY, DEFAULT_AI_MAIN_TESLA_ENTITY) or "").strip()
    if not main_entity:
        # fallback to most useful existing entity; this keeps setup easy
        for fallback in [
            data.get(CONF_BATTERY_LEVEL_ENTITY),
            data.get(CONF_SPEED_ENTITY),
            data.get(CONF_TRIP_MAP_TRACKER_ENTITY),
            data.get(CONF_CLIMATE_ENTITY),
        ]:
            fallback = str(fallback or "").strip()
            if fallback:
                main_entity = fallback
                break

    device_id = get_device_id_for_entity(hass, main_entity)
    if not device_id:
        return [], "cihaz bulunamadı"

    device_label = get_device_label(hass, device_id)
    return get_entities_for_device(hass, device_id), device_label


def format_entities_for_ai_context(
    hass: HomeAssistant,
    entity_ids: list[str],
    *,
    include_unavailable: bool,
    max_entities: int,
) -> list[str]:
    """Format entities under categories for AI context."""
    grouped: dict[str, list[str]] = {}
    count = 0

    for entity_id in entity_ids:
        if count >= max_entities:
            break
        state = hass.states.get(entity_id)
        if state is None:
            if include_unavailable:
                grouped.setdefault("Eksik / bulunamadı", []).append(f"- {entity_id}: yok")
                count += 1
            continue

        raw_state = clean_entity_state_for_ai(state.state)
        if not include_unavailable and raw_state.lower() in {"unknown", "unavailable", "none", ""}:
            continue

        category = categorize_entity_for_ai(entity_id, state)
        attrs = important_entity_attributes_for_ai(state)
        attr_text = f" ({'; '.join(attrs)})" if attrs else ""
        grouped.setdefault(category, []).append(f"- {entity_id}: {raw_state}{attr_text}")
        count += 1

    lines: list[str] = []
    preferred_order = [
        "Batarya / şarj",
        "Sürüş / hareket",
        "Konum / rota",
        "Klima / sıcaklık",
        "Güvenlik / kapılar",
        "Lastik / basınç",
        "Kontrol entity’leri (bilgi amaçlı)",
        "Diğer Tesla verileri",
        "Eksik / bulunamadı",
    ]

    for category in preferred_order:
        items = grouped.get(category)
        if not items:
            continue
        lines.append(f"{category}:")
        lines.extend(items)

    return lines


def build_ai_context_entity_selection(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Build the final AI context entity selection without runtime auto discovery.

    Important UX rule:
    - The Vehicle Manager "Find AI entities" action is the only place that runs device discovery.
    - Telegram AI requests must not silently rediscover entities at runtime.
    - AI can see only Vehicle Report/core entities + explicitly selected AI entities - excluded entities.
    """
    context_mode = str(data.get(CONF_AI_CONTEXT_MODE, DEFAULT_AI_CONTEXT_MODE) or DEFAULT_AI_CONTEXT_MODE)

    core_entities = get_core_ai_entities(data)
    selected_ai_entities = get_extra_ai_context_entities(data)
    excluded_entities = get_excluded_ai_context_entities(data)
    excluded_set = set(excluded_entities)

    if context_mode == AI_CONTEXT_MODE_MANUAL_ONLY:
        # In manual-only mode, only the selected AI entity boxes are sent.
        entity_ids = selected_ai_entities
    else:
        # Normal mode: report/core vehicle entities + selected AI entity boxes.
        entity_ids = core_entities + selected_ai_entities

    entity_ids = [entity_id for entity_id in dedupe_entities(entity_ids) if entity_id not in excluded_set]

    main_entity = str(data.get(CONF_AI_MAIN_TESLA_ENTITY, DEFAULT_AI_MAIN_TESLA_ENTITY) or "").strip()
    device_id = get_device_id_for_entity(hass, main_entity) if main_entity else None

    return {
        "context_mode": context_mode,
        "auto_discover": False,
        "runtime_auto_discovery_disabled": True,
        "core_entities": core_entities,
        "extra_entities": selected_ai_entities,
        "excluded_entities": excluded_entities,
        "discovered_entities": [],
        "device_label": get_device_label(hass, device_id) if device_id else "",
        "entity_ids": entity_ids,
    }


def build_ai_context_text(hass: HomeAssistant, data: dict[str, Any]) -> str:
    """Build smart current-state context for POM AI Basic."""
    normal_state = get_trip_state(hass)
    manual_state = get_manual_tracking_state(hass)

    include_unavailable = get_bool_option(data, CONF_AI_INCLUDE_UNAVAILABLE, DEFAULT_AI_INCLUDE_UNAVAILABLE)
    max_entities = int(safe_float(data.get(CONF_AI_MAX_CONTEXT_ENTITIES), DEFAULT_AI_MAX_CONTEXT_ENTITIES))
    max_entities = max(10, min(max_entities, 200))

    selection = build_ai_context_entity_selection(hass, data)
    entity_ids = selection["entity_ids"]

    lines = [
        "POM AI akıllı bağlam verisi:",
        f"- Context mode: {selection['context_mode']}",
        f"- Ana Tesla cihazı: {selection['device_label'] or 'otomatik / seçilmemiş'}",
        f"- Kullanılan entity sınırı: {max_entities}",
        f"- Unavailable dahil: {include_unavailable}",
        f"- Merkezi Vehicle Entity Manager kayıtları: {len(get_vehicle_entity_entries(data))}",
        f"- Seçili AI entity kutuları: {len(selection['extra_entities'])}",
        f"- Hariç tutulan entity: {len(selection['excluded_entities'])}",
        "",
        "Kural: Bir entity unavailable/unknown ise bunu veri yok diye uydurma; kullanıcıya şu anda bu veriyi göremediğini söyle. Araç uyandığında veya hareket halindeyken available olabileceğini belirtebilirsin.",
        "Kural: Vehicle state / sleep status rolünde açık bir entity yoksa veya bu entity sleep/asleep/online/awake gibi net veri vermiyorsa, aracın uyuduğunu kesin söyleme. Parkta, veri sınırlı veya uyuyor olabilir şeklinde temkinli konuş.",
        "Kural: Açık adres içinde kapı/bina no yoksa kapı numarası uydurma. Sadece OpenStreetMap/Nominatim verisinde açıkça gelen house_number değerini kapı no olarak söyle.",
        "",
        "Kural: Sadece son konuşma turunu bağlam olarak kullan; eski konuşmalardan araç durumu veya komut niyeti çıkarma. Güncel entity state her zaman konuşma hafızasından üstündür.",
        "Kural: Sistem tarafından gerçek pending confirmation/suggestion oluşturulmadıysa 'onay bekliyorum', 'onayınız alındı', 'komutu devreye alıyorum' veya benzeri işlem sözü verme.",
        "Merkezi Vehicle Entity Manager rol eşlemesi:",
    ]
    lines.extend(get_vehicle_entity_context_lines(hass, data))

    cached_address = get_cached_reverse_geocode_address(hass)
    if cached_address:
        parts = get_cached_reverse_geocode_parts(hass)
        lines.extend([
            "",
            "Açık adres / reverse geocode:",
            f"- Tam adres: {cached_address}",
        ])
        if parts:
            detail_labels = {
                "house_number": "Kapı/bina no",
                "road": "Sokak/cadde",
                "neighbourhood": "Mahalle/semt",
                "suburb": "İlçe bölgesi",
                "town": "İlçe/şehir",
                "state": "İl",
                "postcode": "Posta kodu",
                "country": "Ülke",
            }
            for key, label in detail_labels.items():
                value = str(parts.get(key) or "").strip()
                if value:
                    lines.append(f"- {label}: {value}")
            if not str(parts.get("house_number") or "").strip():
                lines.append("- Kapı/bina no: OpenStreetMap verisinde yok; kesinlikle uydurma.")

    lines.extend(["", "Güncel Tesla / Home Assistant entity durumları:"])

    entity_lines = format_entities_for_ai_context(
        hass,
        entity_ids,
        include_unavailable=include_unavailable,
        max_entities=max_entities,
    )
    lines.extend(entity_lines or ["- Kullanılabilir entity verisi bulunamadı."])

    lines.extend([
        "",
        "Takip durumları:",
        f"- Otomatik/normal takip aktif: {bool(normal_state.get('active', False))}",
        f"- Manuel switch takip aktif: {bool(manual_state.get('active', False))}",
        f"- Otomatik rota noktası: {normal_state.get('map_point_count', 0)}",
        f"- Manuel rota noktası: {manual_state.get('map_point_count', 0)}",
    ])

    last_normal_report = normal_state.get("last_report_data")
    if isinstance(last_normal_report, dict):
        lines.extend([
            "",
            "Son otomatik/normal rapor özeti:",
            f"- Mesafe: {last_normal_report.get('trip_km')} km",
            f"- Süre: {last_normal_report.get('duration_text')}",
            f"- Trafik: {last_normal_report.get('traffic_text')}",
            f"- Enerji: {last_normal_report.get('used_kwh')} kWh",
            f"- Tüketim: {last_normal_report.get('consumption_kwh_100km')} kWh/100 km",
            f"- Batarya: {last_normal_report.get('start_battery')} -> {last_normal_report.get('end_battery')}",
        ])

    last_manual_report = manual_state.get("last_report_data")
    if isinstance(last_manual_report, dict):
        lines.extend([
            "",
            "Son manuel takip raporu özeti:",
            f"- Mesafe: {last_manual_report.get('trip_km')} km",
            f"- Süre: {last_manual_report.get('duration_text')}",
            f"- Trafik: {last_manual_report.get('traffic_text')}",
            f"- Enerji: {last_manual_report.get('used_kwh')} kWh",
            f"- Tüketim: {last_manual_report.get('consumption_kwh_100km')} kWh/100 km",
            f"- Batarya: {last_manual_report.get('start_battery')} -> {last_manual_report.get('end_battery')}",
        ])

    lines.extend([
        "",
        "Maliyet ayarları:",
        f"- Supercharger: {data.get(CONF_SUPERCHARGER_PRICE)} {get_report_currency(data)}/kWh",
        f"- ZES: {data.get(CONF_ZES_PRICE)} {get_report_currency(data)}/kWh",
        f"- Astor: {data.get(CONF_ASTOR_PRICE)} {get_report_currency(data)}/kWh",
        "",
        "Güvenlik kuralı: Araç kontrol komutları sadece POM onay sistemi üzerinden çalışır; LLM doğrudan servis çağrısı uydurmaz. Kilit/frunk/trunk/klima/korna/far gibi işlemler kullanıcı onayı ister.",
    ])

    return "\n".join(lines)

def build_ai_context_entity_debug(
    hass: HomeAssistant,
    data: dict[str, Any],
    *,
    max_entities_override: int | None = None,
    include_unavailable_override: bool | None = None,
) -> str:
    """Build a readable category-based report showing which data POM AI can read."""
    include_unavailable = (
        include_unavailable_override
        if include_unavailable_override is not None
        else get_bool_option(data, CONF_AI_INCLUDE_UNAVAILABLE, DEFAULT_AI_INCLUDE_UNAVAILABLE)
    )
    max_entities = int(
        max_entities_override
        if max_entities_override is not None
        else safe_float(data.get(CONF_AI_MAX_CONTEXT_ENTITIES), DEFAULT_AI_MAX_CONTEXT_ENTITIES)
    )
    max_entities = max(10, min(max_entities, 200))

    selection = build_ai_context_entity_selection(hass, data)

    visible: list[str] = []
    unavailable_list: list[str] = []
    missing_list: list[str] = []

    for entity_id in selection["entity_ids"]:
        state = hass.states.get(entity_id)
        if state is None:
            missing_list.append(entity_id)
            if include_unavailable:
                visible.append(entity_id)
            continue
        raw_state = clean_entity_state_for_ai(state.state)
        if raw_state.lower() in {"unknown", "unavailable", "none", ""}:
            unavailable_list.append(entity_id)
            if not include_unavailable:
                continue
        visible.append(entity_id)

    included = visible[:max_entities]
    skipped_limit = max(0, len(visible) - len(included))

    vehicle_entries = get_vehicle_entity_entries(data)
    role_by_entity = {
        str(item.get("entity_id")): item.get("role")
        for item in vehicle_entries
        if item.get("entity_id")
    }
    label_by_entity = {
        str(item.get("entity_id")): item.get("label") or VEHICLE_ROLE_LABELS.get(item.get("role"), item.get("role", ""))
        for item in vehicle_entries
        if item.get("entity_id")
    }

    def _status_line(entity_id: str) -> tuple[str, str]:
        state = hass.states.get(entity_id)
        role_label = VEHICLE_ROLE_LABELS.get(role_by_entity.get(entity_id), role_by_entity.get(entity_id, ""))
        custom_label = label_by_entity.get(entity_id) or role_label
        display_name = custom_label or role_label or entity_id

        if state is None:
            return "Eksik / bulunamadı", f"âŒ {display_name}: entity bulunamadı\n   {entity_id}"

        friendly = state.attributes.get("friendly_name") or ""
        unit = state.attributes.get("unit_of_measurement") or ""
        value = clean_entity_state_for_ai(state.state)
        category = categorize_entity_for_ai(entity_id, state)

        if value.lower() in {"unknown", "unavailable", "none", ""}:
            value_text = "şu anda okunamıyor"
            icon = "âš ï¸"
        else:
            value_text = f"{value} {unit}".strip()
            icon = "âœ…"

        detail_parts = []
        if entity_id:
            detail_parts.append(entity_id)
        if friendly and friendly != display_name:
            detail_parts.append(str(friendly))
        if role_label and role_label != display_name:
            detail_parts.append(str(role_label))

        detail = " · ".join(detail_parts)
        return category, f"{icon} {display_name}: {value_text}\n   {detail}"

    grouped: dict[str, list[str]] = {}
    for entity_id in included:
        category, line = _status_line(entity_id)
        grouped.setdefault(category, []).append(line)

    main_entity = str(data.get(CONF_AI_MAIN_TESLA_ENTITY, DEFAULT_AI_MAIN_TESLA_ENTITY) or "").strip()
    if not main_entity:
        main_entity = str(data.get(CONF_BATTERY_LEVEL_ENTITY) or data.get(CONF_SPEED_ENTITY) or data.get(CONF_TRIP_MAP_TRACKER_ENTITY) or "").strip()
    device_id = get_device_id_for_entity(hass, main_entity)

    lines = [
        "📊 POM AI Veri Erişimi",
        "",
        f"Main entity: {main_entity or '-'}",
        f"Device: {selection['device_label'] or get_device_label(hass, device_id) or '-'}",
        "Runtime auto discovery: disabled",
        f"Report/core entities: {len(selection['core_entities'])}",
        f"Selected AI entities: {len(selection['extra_entities'])}",
        f"Excluded entities: {len(selection['excluded_entities'])}",
        f"AI context'e giren entity: {len(included)} / max {max_entities}",
        "",
        "Kural: unavailable / unknown değerlerde POM veri uydurmaz; 'şu anda okuyamıyorum' der.",
    ]

    preferred_order = [
        "Batarya / şarj",
        "Sürüş / hareket",
        "Konum / rota",
        "Klima / sıcaklık",
        "Lastik / basınç",
        "Güvenlik / kapılar",
        "Kontrol entity’leri (bilgi amaçlı)",
        "Diğer Tesla verileri",
        "Eksik / bulunamadı",
    ]

    for category in preferred_order:
        items = grouped.get(category)
        if not items:
            continue
        lines.extend(["", category.upper()])
        lines.extend(items)

    if selection["excluded_entities"]:
        lines.extend(["", "EXCLUDED ENTITIES"])
        lines.extend([f"âŒ {entity_id}" for entity_id in selection["excluded_entities"]])

    if skipped_limit:
        lines.extend([
            "",
            f"Not: {skipped_limit} entity max context sınırı nedeniyle gösterilmedi/gönderilmedi. Gerekirse Max context entities değerini artır.",
        ])

    missing_expected = []
    required_ai_roles = [
        VEHICLE_ROLE_BATTERY_LEVEL,
        VEHICLE_ROLE_ENERGY_REMAINING,
        VEHICLE_ROLE_OUTSIDE_TEMPERATURE,
        VEHICLE_ROLE_BATTERY_TEMPERATURE,
        VEHICLE_ROLE_TIRE_PRESSURE_FRONT_LEFT,
        VEHICLE_ROLE_TIRE_PRESSURE_FRONT_RIGHT,
        VEHICLE_ROLE_TIRE_PRESSURE_REAR_LEFT,
        VEHICLE_ROLE_TIRE_PRESSURE_REAR_RIGHT,
    ]
    roles_present = set(role_by_entity.values())
    for role in required_ai_roles:
        if role not in roles_present:
            missing_expected.append(VEHICLE_ROLE_LABELS.get(role, role))
    if missing_expected:
        lines.extend(["", "SEÇİLMEMİÅ OLABİLECEK ÖNEMLİ VERİLER"])
        lines.extend([f"âš ï¸ {item}" for item in missing_expected[:20]])

    return "\n".join(lines)

def split_telegram_message(message: str, limit: int = 3000) -> list[str]:
    """Split long Telegram messages safely for Telegram.

    This handles both normal multiline text and a single very long line.
    """
    text = str(message or "").strip()
    if not text:
        return ["Boş mesaj."]

    chunks: list[str] = []
    current = ""

    for original_line in text.splitlines():
        line = original_line

        # Hard-break very long single lines.
        while len(line) > limit:
            piece = line[:limit]
            line = line[limit:]
            if current:
                chunks.append(current)
                current = ""
            chunks.append(piece)

        candidate = f"{current}\n{line}" if current else line
        if len(candidate) <= limit:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = line

    if current:
        chunks.append(current)

    return chunks or [text[:limit]]


def is_builtin_telegram_enabled(data: dict[str, Any]) -> bool:
    """Return True when built-in Telegram mode is enabled and has a token."""
    return bool(
        get_bool_option(data, CONF_BUILTIN_TELEGRAM_ENABLED, DEFAULT_BUILTIN_TELEGRAM_ENABLED)
        and str(data.get(CONF_BUILTIN_TELEGRAM_BOT_TOKEN) or "").strip()
    )


def get_builtin_telegram_config_for_target(
    hass: HomeAssistant,
    target: str | None = None,
) -> dict[str, Any] | None:
    """Return the best built-in Telegram config for a given target, or the first enabled one."""
    domain_data = hass.data.get(DOMAIN, {})
    normalized_target = normalize_telegram_id(target)
    fallback: dict[str, Any] | None = None
    for key, value in domain_data.items():
        if not isinstance(key, str) or not isinstance(value, dict):
            continue
        if not is_builtin_telegram_enabled(value):
            continue
        if fallback is None:
            fallback = value
        candidate_target = normalize_telegram_id(
            value.get(CONF_AI_TELEGRAM_LISTENER_CHAT_ID)
            or value.get(CONF_AI_TELEGRAM_TARGET)
            or value.get(CONF_TELEGRAM_TARGET)
        )
        if normalized_target and candidate_target == normalized_target:
            return value
    return fallback


def _telegram_api_url(token: str, method: str) -> str:
    """Build a Telegram Bot API URL."""
    return f"https://api.telegram.org/bot{token}/{method}"


def _telegram_reply_markup_from_inline_keyboard(inline_keyboard: Any) -> dict[str, Any] | None:
    """Convert Home Assistant telegram_bot inline keyboard syntax to Telegram reply_markup."""
    if not inline_keyboard:
        return None
    rows: list[list[dict[str, str]]] = []
    if isinstance(inline_keyboard, list):
        for item in inline_keyboard:
            if not isinstance(item, str):
                continue
            buttons: list[dict[str, str]] = []
            for raw_button in item.split(","):
                button = str(raw_button or "").strip()
                if not button or ":" not in button:
                    continue
                text, callback_data = button.split(":", 1)
                buttons.append({"text": text.strip(), "callback_data": callback_data.strip()})
            if buttons:
                rows.append(buttons)
    if not rows:
        return None
    return {"inline_keyboard": rows}


async def async_builtin_telegram_api_call(
    hass: HomeAssistant,
    data: dict[str, Any],
    method: str,
    *,
    json_payload: dict[str, Any] | None = None,
    form_payload: FormData | None = None,
) -> dict[str, Any]:
    """Call Telegram Bot API directly using built-in bot settings."""
    token = str(data.get(CONF_BUILTIN_TELEGRAM_BOT_TOKEN) or "").strip()
    if not token:
        raise ValueError("Built-in Telegram bot token is empty.")
    session = async_get_clientsession(hass)
    url = _telegram_api_url(token, method)
    try:
        if form_payload is not None:
            async with session.post(url, data=form_payload, timeout=60) as response:
                payload = await response.json(content_type=None)
        else:
            async with session.post(url, json=json_payload or {}, timeout=60) as response:
                payload = await response.json(content_type=None)
    except ClientError as err:
        raise ValueError(f"Telegram API request failed: {err}") from err
    if not isinstance(payload, dict):
        raise ValueError("Telegram API returned an invalid response.")
    if not payload.get("ok", False):
        description = payload.get("description") or "Unknown Telegram API error"
        raise ValueError(str(description))
    return payload


async def async_telegram_send_message(
    hass: HomeAssistant,
    data: dict[str, Any],
    *,
    target: str,
    message: str,
    parse_mode: str | None = None,
    inline_keyboard: Any = None,
) -> None:
    """Send Telegram text using POM built-in bot first; HA telegram_bot is optional fallback only."""
    target = str(target or "").strip()
    if not target:
        raise ValueError("Telegram target is empty.")

    if is_builtin_telegram_enabled(data):
        payload: dict[str, Any] = {
            "chat_id": normalize_telegram_id(target),
            "text": str(message or ""),
        }
        reply_markup = _telegram_reply_markup_from_inline_keyboard(inline_keyboard)
        if reply_markup:
            payload["reply_markup"] = reply_markup
        await async_builtin_telegram_api_call(hass, data, "sendMessage", json_payload=payload)
        return

    if hass.services.has_service("telegram_bot", "send_message"):
        service_data: dict[str, Any] = {
            "target": target,
            "message": str(message or ""),
        }
        if parse_mode:
            service_data["parse_mode"] = parse_mode
        if inline_keyboard:
            service_data["inline_keyboard"] = inline_keyboard
        await hass.services.async_call("telegram_bot", "send_message", service_data, blocking=True)
        return

    raise ValueError("POM built-in Telegram is not configured, and optional HA telegram_bot.send_message fallback is not available.")


async def async_telegram_send_photo(
    hass: HomeAssistant,
    data: dict[str, Any],
    *,
    target: str,
    file_path: str,
    caption: str = "",
    inline_keyboard: Any = None,
) -> None:
    """Send Telegram image/document using POM built-in bot first; HA telegram_bot is optional fallback only."""
    target = str(target or "").strip()
    file_path = str(file_path or "").strip()
    if not target:
        raise ValueError("Telegram target is empty.")
    if not file_path:
        raise ValueError("Telegram file path is empty.")

    if is_builtin_telegram_enabled(data):
        path = Path(file_path)
        if not path.exists():
            raise ValueError(f"Telegram file not found: {file_path}")
        method = "sendPhoto" if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"} else "sendDocument"
        media_field = "photo" if method == "sendPhoto" else "document"
        form = FormData()
        form.add_field("chat_id", normalize_telegram_id(target))
        if caption:
            form.add_field("caption", str(caption))
        reply_markup = _telegram_reply_markup_from_inline_keyboard(inline_keyboard)
        if reply_markup:
            form.add_field("reply_markup", json.dumps(reply_markup, ensure_ascii=False))
        with path.open("rb") as handle:
            form.add_field(media_field, handle.read(), filename=path.name)
        await async_builtin_telegram_api_call(hass, data, method, form_payload=form)
        return

    if hass.services.has_service("telegram_bot", "send_photo"):
        service_data = {"target": target, "file": file_path, "caption": caption}
        if inline_keyboard:
            service_data["inline_keyboard"] = inline_keyboard
        await hass.services.async_call(
            "telegram_bot",
            "send_photo",
            service_data,
            blocking=True,
        )
        return

    raise ValueError("POM built-in Telegram is not configured, and optional HA telegram_bot.send_photo fallback is not available.")


async def async_telegram_delete_message(
    hass: HomeAssistant,
    data: dict[str, Any],
    *,
    chat_id: str,
    message_id: int,
) -> None:
    """Delete a Telegram message using built-in mode or HA telegram_bot fallback."""
    if is_builtin_telegram_enabled(data):
        await async_builtin_telegram_api_call(
            hass,
            data,
            "deleteMessage",
            json_payload={"chat_id": normalize_telegram_id(chat_id), "message_id": int(message_id)},
        )
        return
    if hass.services.has_service("telegram_bot", "delete_message"):
        await hass.services.async_call(
            "telegram_bot",
            "delete_message",
            {"chat_id": str(chat_id), "message_id": int(message_id)},
            blocking=True,
        )
        return
    raise ValueError("Neither built-in Telegram nor Home Assistant telegram_bot.delete_message is available.")


async def async_telegram_edit_message(
    hass: HomeAssistant,
    data: dict[str, Any],
    *,
    chat_id: str,
    message_id: int,
    message: str,
    inline_keyboard: Any = None,
) -> None:
    """Edit a Telegram message using built-in mode or HA telegram_bot fallback."""
    if is_builtin_telegram_enabled(data):
        payload: dict[str, Any] = {
            "chat_id": normalize_telegram_id(chat_id),
            "message_id": int(message_id),
            "text": str(message or ""),
        }
        reply_markup = _telegram_reply_markup_from_inline_keyboard(inline_keyboard)
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup
        await async_builtin_telegram_api_call(hass, data, "editMessageText", json_payload=payload)
        return
    if hass.services.has_service("telegram_bot", "edit_message"):
        await hass.services.async_call(
            "telegram_bot",
            "edit_message",
            {
                "chat_id": str(chat_id),
                "message_id": int(message_id),
                "message": str(message or ""),
                "inline_keyboard": inline_keyboard or [],
            },
            blocking=True,
        )
        return
    raise ValueError("Neither built-in Telegram nor Home Assistant telegram_bot.edit_message is available.")


def _builtin_telegram_state(hass: HomeAssistant, entry_id: str) -> dict[str, Any]:
    """Return per-entry runtime state for built-in Telegram polling."""
    state_key = f"{entry_id}_builtin_telegram_state"
    return hass.data.setdefault(DOMAIN, {}).setdefault(state_key, {"last_update_id": 0, "running": False})


async def async_poll_builtin_telegram_updates(
    hass: HomeAssistant,
    entry_id: str,
    config_data: dict[str, Any],
) -> None:
    """Poll Telegram updates and re-fire them as HA events for existing handlers."""
    if not is_builtin_telegram_enabled(config_data):
        return
    state = _builtin_telegram_state(hass, entry_id)
    if state.get("running"):
        return
    state["running"] = True
    try:
        payload = await async_builtin_telegram_api_call(
            hass,
            config_data,
            "getUpdates",
            json_payload={
                "offset": int(state.get("last_update_id", 0)) + 1,
                "timeout": 0,
                "allowed_updates": ["message", "callback_query"],
            },
        )
        results = payload.get("result")
        if not isinstance(results, list):
            return
        for update in results:
            if not isinstance(update, dict):
                continue
            update_id = int(update.get("update_id", 0) or 0)
            if update_id > int(state.get("last_update_id", 0)):
                state["last_update_id"] = update_id

            if isinstance(update.get("message"), dict):
                msg = update["message"]
                text = msg.get("text") or ""
                event_data = {
                    "chat_id": (msg.get("chat") or {}).get("id"),
                    "user_id": (msg.get("from") or {}).get("id"),
                    "text": text,
                    "message": msg,
                    "update_id": update_id,
                }
                hass.bus.async_fire("telegram_text", event_data)
                if str(text).strip().startswith("/"):
                    token_and_rest = str(text).strip().split(maxsplit=1)
                    command_token = token_and_rest[0]
                    args_text = token_and_rest[1] if len(token_and_rest) > 1 else ""
                    if "@" in command_token:
                        command_token = command_token.split("@", 1)[0]
                    hass.bus.async_fire("telegram_command", {
                        **event_data,
                        "command": command_token.lstrip("/"),
                        "args": args_text,
                    })

            if isinstance(update.get("callback_query"), dict):
                callback = update["callback_query"]
                msg = callback.get("message") or {}
                event_data = {
                    "chat_id": (msg.get("chat") or {}).get("id"),
                    "user_id": (callback.get("from") or {}).get("id"),
                    "from_id": (callback.get("from") or {}).get("id"),
                    "message_id": msg.get("message_id"),
                    "message": msg,
                    "data": callback.get("data") or "",
                    "callback_query": callback,
                    "update_id": update_id,
                }
                hass.bus.async_fire("telegram_callback", event_data)
    finally:
        state["running"] = False


async def async_send_telegram_text_chunks(
    hass: HomeAssistant,
    data: dict[str, Any],
    target: str,
    message: str,
    *,
    title: str | None = None,
    limit: int = 3000,
) -> None:
    """Send long Telegram text as multiple safe chunks."""
    chunks = split_telegram_message(message, limit=limit)
    total = len(chunks)

    for index, chunk in enumerate(chunks, start=1):
        header = ""
        if title and total > 1:
            header = f"{title} ({index}/{total})\n\n"
        elif title and index == 1:
            header = f"{title}\n\n"

        payload = f"{header}{chunk}".strip()
        await async_telegram_send_message(
            hass,
            data,
            target=target,
            parse_mode="plain_text",
            message=payload,
        )


def should_send_ai_context_debug(user_message: str) -> bool:
    """Detect requests asking which data/entities POM AI can see."""
    normalized = normalize_text_for_match(user_message)

    # Direct exact/common phrases first.
    patterns = [
        "hangi verileri goruyorsun",
        "hangi verileri okuyorsun",
        "verileri goruyorsun",
        "verileri okuyorsun",
        "okuyabildigin veriler hangisi",
        "okuyabildigin verileri",
        "okuyabildigin tum verileri",
        "tum okuyabildigin verileri",
        "hangi verileri okuyabiliyorsun",
        "hangi verileri gorebiliyorsun",
        "neleri goruyorsun",
        "neleri okuyorsun",
        "ne gorebiliyorsun",
        "ne okuyabiliyorsun",
        "okudugun veriler",
        "gordugun veriler",
        "veri listesini goster",
        "veri listesi",
        "entityleri listele",
        "entitileri listele",
        "entity listesi",
        "entityleri goster",
        "entitileri goster",
        "sensorleri listele",
        "sensor listesini goster",
        "hangi entity",
        "context debug",
        "ai context",
    ]
    if any(pattern in normalized for pattern in patterns):
        return True

    # Fuzzy fallback: allow natural Turkish phrasing.
    has_data_word = any(word in normalized for word in ["veri", "entity", "entiti", "sensor", "context"])
    has_visibility_word = any(word in normalized for word in ["oku", "gor", "goster", "liste", "hangi", "neler", "neyi"])
    return has_data_word and has_visibility_word


def should_send_vehicle_location_answer(message: str) -> bool:
    """Detect direct vehicle location requests that should include address and Google Maps link."""
    normalized = normalize_text_for_match(message)
    if not normalized:
        return False

    location_phrases = [
        "arac nerede",
        "arac nerde",
        "araba nerede",
        "araba nerde",
        "arabam nerede",
        "arabam nerde",
        "tesla nerede",
        "tesla nerde",
        "pom nerede",
        "pom nerde",
        "neredesin",
        "nerdesin",
        "konum gonder",
        "konumu gonder",
        "arac konumu",
        "arabanin konumu",
        "maps link",
        "google maps",
        "where is my car",
        "where is the car",
        "where are you",
        "car location",
        "location of my car",
        "send location",
        "send the location",
        "exact location",
        "give me exact location",
    ]

    if any(phrase in normalized for phrase in location_phrases):
        return True

    has_vehicle = any(word in normalized for word in ["arac", "araba", "tesla", "pom"])
    has_location = any(word in normalized for word in ["konum", "nerede", "nerde", "maps", "harita", "adres"])
    return has_vehicle and has_location


def get_google_maps_link(lat: float, lon: float) -> str:
    """Build a Google Maps search link for coordinates."""
    return f"https://maps.google.com/?q={lat:.7f},{lon:.7f}"




def get_pending_ai_vehicle_control_state(hass: HomeAssistant) -> dict[str, Any]:
    """Return pending AI vehicle control confirmations."""
    return hass.data.setdefault(DOMAIN, {}).setdefault("pending_ai_vehicle_controls", {})


def get_pending_ai_vehicle_suggestion_state(hass: HomeAssistant) -> dict[str, Any]:
    """Return the single-slot pending AI vehicle suggestion state.

    This is intentionally separate from risk/confirmation prompts. It is used
    for natural follow-ups such as:
    - "çok sıcak oldu" -> POM offers climate
    - "evet / hadi bas / yap" -> execute the newest safe suggestion

    There is only one active suggestion. New suggestions replace old ones.
    """
    return hass.data.setdefault(DOMAIN, {}).setdefault("pending_ai_vehicle_suggestion", {})


def clear_pending_ai_vehicle_suggestion(hass: HomeAssistant) -> None:
    """Clear the single pending AI vehicle suggestion slot."""
    get_pending_ai_vehicle_suggestion_state(hass).clear()


def get_pom_ai_conversation_state(hass: HomeAssistant) -> dict[str, Any]:
    """Return short local POM AI conversation memory keyed by Telegram target.

    This mirrors the useful part of the old Home Assistant conversation_id flow:
    follow-up messages keep recent context, but service execution still depends
    on explicit pending_suggestion / pending_confirmation state.
    """
    return hass.data.setdefault(DOMAIN, {}).setdefault("pom_ai_conversations", {})


def _pom_ai_conversation_key(telegram_target: str | None = None) -> str:
    target = str(telegram_target or "default").strip() or "default"
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", target)


def get_pom_ai_recent_conversation_text(
    hass: HomeAssistant,
    telegram_target: str | None = None,
    *,
    limit_turns: int = 1,
) -> str:
    memory = get_pom_ai_conversation_state(hass)
    key = _pom_ai_conversation_key(telegram_target)
    turns = list(memory.get(key) or [])[-limit_turns:]
    if not turns:
        return ""
    lines = ["LAST POM AI CONVERSATION TURN ONLY:"]
    for turn in turns:
        user = str(turn.get("user") or "").strip()
        assistant = str(turn.get("assistant") or "").strip()
        if user:
            lines.append(f"User: {user}")
        if assistant:
            lines.append(f"POM: {assistant}")
    lines.append(
        "Use only this last turn for conversational wording. Do not use it as factual vehicle state. "
        "Current Home Assistant entity values above always win over this memory. "
        "Never say you are waiting for approval, taking approval, or executing a vehicle command from memory; "
        "vehicle controls require an explicit new command or the single active pending suggestion/confirmation."
    )
    return "\n".join(lines)


def remember_pom_ai_conversation_turn(
    hass: HomeAssistant,
    telegram_target: str | None,
    user_message: str,
    assistant_answer: str,
    *,
    max_turns: int = 2,
) -> None:
    memory = get_pom_ai_conversation_state(hass)
    key = _pom_ai_conversation_key(telegram_target)
    turns = list(memory.get(key) or [])
    turns.append({
        "ts": datetime.now().timestamp(),
        "user": str(user_message or "")[:1200],
        "assistant": str(assistant_answer or "")[:1600],
    })
    memory[key] = turns[-max_turns:]


AI_CONTROL_CAPABILITY_MANIFEST = [{'entity_example': 'switch.pom_charge', 'capability': 'charge_control', 'name': 'Charge Control', 'domain': 'switch', 'purpose': 'Aracın şarj başlat/durdur kontrolüdür. Durum gösterimi için binary_sensor.pom_charging daha uygundur; switch ise kontrol amaçlıdır.', 'service_text': 'switch.turn_on / switch.turn_off', 'services': ['switch.turn_on', 'switch.turn_off'], 'confirmation': 'optional', 'aliases': ['şarjı başlat', 'şarj etmeye başla', 'şarjı durdur', 'şarjı kes', 'şarjı kapat', 'start charging', 'stop charging', 'enable charging', 'disable charging'], 'notes': "Kullanıcı dosyasında 'şarj olma durumunu gösterir' notu var; ancak switch domain olduğu için kontrol amaçlı kullanılabilir. Durum için binary_sensor.pom_charging tercih edilmeli."}, {'entity_example': 'lock.pom_charge_cable_lock', 'capability': 'charge_cable_lock', 'name': 'Charge Cable Lock', 'domain': 'lock', 'purpose': 'Åarj kablosu kilidini kontrol eder veya durumunu gösterir.', 'service_text': 'lock.lock / lock.unlock', 'services': ['lock.lock', 'lock.unlock'], 'confirmation': 'required', 'aliases': ['şarj kablosunu kilitle', 'şarj kablosu kilidini aç', 'kablo kilidini aç', 'lock charge cable', 'unlock charge cable', 'release charge cable lock'], 'notes': 'Kablo kilidini açmak fiziksel güvenlik/şarj güvenliği etkileyebilir; onay önerilir.'}, {'entity_example': 'cover.pom_charge_port_door', 'capability': 'charge_port_door', 'name': 'Charge Port Door', 'domain': 'cover', 'purpose': 'Åarj port kapağını açıp kapatır.', 'service_text': 'cover.open_cover / cover.close_cover', 'services': ['cover.open_cover', 'cover.close_cover'], 'confirmation': 'optional', 'aliases': ['şarj kapağını aç', 'şarj portunu aç', 'şarj kapağını kapat', 'şarj portunu kapat', 'open charge port', 'close charge port', 'open charge port door', 'close charge port door'], 'notes': 'Genelde düşük riskli; yine de kullanıcı isterse tüm araç kontrollerinde onay açılabilir.'}, {'entity_example': 'climate.pom_climate', 'capability': 'climate', 'name': 'Cabin Climate', 'domain': 'climate', 'purpose': 'Tesla kabin klimasını kontrol eder; aç/kapat, hedef sıcaklık ayarı ve desteklenen modlar için kullanılır.', 'service_text': 'climate.turn_on / climate.turn_off / climate.set_temperature / climate.set_hvac_mode', 'services': ['climate.turn_on', 'climate.turn_off', 'climate.set_temperature', 'climate.set_hvac_mode'], 'confirmation': 'none', 'aliases': ['klimayı aç', 'klimayı kapat', 'araç klimasını kapat', 'araba klimasını kapat', 'klimasını kapat', 'klimasını aç', 'soğutmayı aç', 'ısıtmayı aç', 'klimayı 22 derece yap', 'sıcaklığı 25 yap', 'arabayı serinlet', 'arabayı ısıt', 'turn on climate', 'turn off climate', 'set climate to 22', 'set temperature to 25', 'cool the car', 'heat the car'], 'notes': "Çoklu komutta 'klimayı aç ve 28 derece yap' iki aksiyon üretmeli: turn_on + set_temperature."}, {'entity_example': 'switch.pom_defrost_mode', 'capability': 'defrost_mode', 'name': 'Defrost Mode', 'domain': 'switch', 'purpose': 'Cam buğu/buz çözme defrost modunu açıp kapatır.', 'service_text': 'switch.turn_on / switch.turn_off', 'services': ['switch.turn_on', 'switch.turn_off'], 'confirmation': 'optional', 'aliases': ['defrost aç', 'defrost kapat', 'buz çözmeyi aç', 'cam buzunu çöz', 'buğu çözmeyi aç', 'ön camı çöz', 'turn on defrost', 'turn off defrost', 'defrost the car', 'clear windshield', 'windshield defrost'], 'notes': 'Genelde güvenli ama aracı uyandırabilir ve enerji tüketir.'}, {'entity_example': 'button.pom_flash_lights', 'capability': 'flash_lights', 'name': 'Flash Lights', 'domain': 'button', 'purpose': 'Araç farlarını kısa süreli flaşlar/sellektör yapar.', 'service_text': 'button.press', 'services': ['button.press'], 'confirmation': 'none', 'aliases': ['farları yak', 'farları flaşla', 'ışıkları yak', 'selektör yap', 'ışık çak', 'arabayı bulmak için ışık yak', 'flash lights', 'flash the lights', 'blink lights', 'find my car with lights'], 'notes': 'Tek aksiyonlu button.press. Genel olarak düşük riskli.'}, {'entity_example': 'cover.pom_frunk', 'capability': 'frunk', 'name': 'Frunk', 'domain': 'cover', 'purpose': 'Ön bagaj/frunk kapağını açar. Genellikle kapatma desteği yoktur veya araca göre değişebilir.', 'service_text': 'cover.open_cover', 'services': ['cover.open_cover'], 'confirmation': 'required', 'aliases': ['frunku aç', 'ön frunku aç', 'ön bagajı aç', 'ön kaputu aç', 'open frunk', 'open front trunk', 'open front boot'], 'notes': 'Riskli komuttur. Her zaman onay gerekir. Kapatma servisi desteklenmeyebilir.'}, {'entity_example': 'button.pom_homelink', 'capability': 'homelink', 'name': 'HomeLink', 'domain': 'button', 'purpose': 'Araçtaki HomeLink komutunu tetikler; garaj kapısı/bariyer gibi eşleşmiş sistemi çalıştırabilir.', 'service_text': 'button.press', 'services': ['button.press'], 'confirmation': 'required', 'aliases': ['homelink çalıştır', 'garajı aç', 'garaj kapısını aç', 'bariyeri aç', 'trigger homelink', 'open garage', 'open garage door', 'open gate'], 'notes': 'Çevresel kapı/bariyer kontrolü olduğu için onay önerilir.'}, {'entity_example': 'button.pom_honk_horn', 'capability': 'honk_horn', 'name': 'Honk Horn', 'domain': 'button', 'purpose': 'Araç kornasını çalar.', 'service_text': 'button.press', 'services': ['button.press'], 'confirmation': 'optional', 'aliases': ['korna çal', 'kornaya bas', 'kornayı çal', 'ses çıkar', 'honk', 'honk horn', 'sound horn', 'beep the horn'], 'notes': 'Düşük/orta riskli; rahatsızlık verebileceği için kullanıcı ayarına göre onaylı yapılabilir.'}, {'entity_example': 'button.pom_keyless_driving', 'capability': 'keyless_driving', 'name': 'Keyless Driving / Remote Start', 'domain': 'button', 'purpose': 'Aracı keyless driving / remote start moduna alır; sürüşe hazırlama komutudur.', 'service_text': 'button.press', 'services': ['button.press'], 'confirmation': 'required', 'aliases': ['arabayı çalıştır', 'aracı çalıştır', 'teslayı çalıştır', 'sürüşe hazırla', 'anahtarsız sürüşü aç', 'uzaktan çalıştır', 'remote start', 'keyless driving', 'start the car', 'enable keyless driving', 'start Tesla'], 'notes': 'Çok riskli komut. Her zaman onay gerekir.'}, {'entity_example': 'lock.pom_lock', 'capability': 'vehicle_lock', 'name': 'Vehicle Lock', 'domain': 'lock', 'purpose': 'Aracın kilidini kilitler veya açar.', 'service_text': 'lock.lock / lock.unlock', 'services': ['lock.lock', 'lock.unlock'], 'confirmation': 'mixed', 'aliases': ['arabayı kilitle', 'aracı kilitle', 'kapıları kilitle', 'teslayı kilitle', 'kapıları aç', 'kilidi aç', 'araç kilidini aç', 'arabayı aç', 'lock car', 'unlock car', 'lock doors', 'unlock doors', 'unlock Tesla'], 'notes': 'lock.lock genelde onaysız olabilir; lock.unlock mutlaka onay ister.'}, {'entity_example': 'media_player.pom_media_player', 'capability': 'media_player', 'name': 'Tesla Media Player', 'domain': 'media_player', 'purpose': 'Araç içi medya oynatıcısının durumunu ve desteklenen medya kontrollerini temsil eder.', 'service_text': 'media_player.media_play_pause / media_player.volume_set / media_player.media_next_track / media_player.media_previous_track', 'services': ['media_player.media_play_pause', 'media_player.volume_set', 'media_player.media_next_track', 'media_player.media_previous_track'], 'confirmation': 'none', 'aliases': ['müziği durdur', 'müziği başlat', 'sesi aç', 'sesi kıs', 'sonraki şarkı', 'önceki şarkı', 'pause music', 'play music', 'volume up', 'volume down', 'next track', 'previous track'], 'notes': 'Tessie media player her araçta aynı kontrol setini sunmayabilir; sadece desteklenen servisler kullanılmalı.'}, {'entity_example': 'button.pom_play_fart', 'capability': 'play_fart', 'name': 'Play Fart', 'domain': 'button', 'purpose': 'Tesla eğlence/boombox fart sesini çalar.', 'service_text': 'button.press', 'services': ['button.press'], 'confirmation': 'optional', 'aliases': ['arabayı osurt', 'osur', 'osurt', 'gaz çıkar', 'şaka sesi çal', 'fart çal', 'play fart', 'fart the car', 'fart', 'boombox fart'], 'notes': 'Düşük riskli ama kullanıcı tercihiyle onaylı yapılabilir.'}, {'entity_example': 'select.pom_seat_heater_left', 'capability': 'seat_heater_front_left', 'name': 'Front Left Seat Heater', 'domain': 'select', 'purpose': 'Sol ön koltuk ısıtma seviyesini Off/Low/Medium/High benzeri seçeneklerle ayarlar.', 'service_text': 'select.select_option', 'services': ['select.select_option'], 'confirmation': 'optional', 'aliases': ['sol ön koltuk ısıtma aç', 'sol ön koltuk ısıtma kapat', 'sol ön koltuk ısıtma düşük yap', 'sol ön koltuk ısıtma orta yap', 'sol ön koltuk ısıtma yüksek yap', 'turn on front left seat heater', 'turn off front left seat heater', 'set front left seat heater low', 'set front left seat heater medium', 'set front left seat heater high'], 'notes': 'Select seçenekleri araca göre değişebilir; geçerli option listesi entity attributes içinden alınmalı.'}, {'entity_example': 'select.pom_seat_heater_right', 'capability': 'seat_heater_front_right', 'name': 'Front Right Seat Heater', 'domain': 'select', 'purpose': 'Sağ ön koltuk ısıtma seviyesini Off/Low/Medium/High benzeri seçeneklerle ayarlar.', 'service_text': 'select.select_option', 'services': ['select.select_option'], 'confirmation': 'optional', 'aliases': ['sağ ön koltuk ısıtma aç', 'sağ ön koltuk ısıtma kapat', 'sağ ön koltuk ısıtma düşük yap', 'sağ ön koltuk ısıtma orta yap', 'sağ ön koltuk ısıtma yüksek yap', 'turn on front right seat heater', 'turn off front right seat heater', 'set front right seat heater low', 'set front right seat heater medium', 'set front right seat heater high'], 'notes': 'Select seçenekleri araca göre değişebilir; geçerli option listesi entity attributes içinden alınmalı.'}, {'entity_example': 'select.pom_seat_heater_rear_left', 'capability': 'seat_heater_rear_left', 'name': 'Rear Left Seat Heater', 'domain': 'select', 'purpose': 'Sol arka koltuk ısıtma seviyesini Off/Low/Medium/High benzeri seçeneklerle ayarlar.', 'service_text': 'select.select_option', 'services': ['select.select_option'], 'confirmation': 'optional', 'aliases': ['sol arka koltuk ısıtma aç', 'sol arka koltuk ısıtma kapat', 'sol arka koltuk ısıtma düşük yap', 'sol arka koltuk ısıtma orta yap', 'sol arka koltuk ısıtma yüksek yap', 'turn on rear left seat heater', 'turn off rear left seat heater', 'set rear left seat heater low', 'set rear left seat heater medium', 'set rear left seat heater high'], 'notes': 'Select seçenekleri araca göre değişebilir; geçerli option listesi entity attributes içinden alınmalı.'}, {'entity_example': 'select.pom_seat_heater_rear_center', 'capability': 'seat_heater_rear_center', 'name': 'Rear Center Seat Heater', 'domain': 'select', 'purpose': 'Arka orta koltuk ısıtma seviyesini Off/Low/Medium/High benzeri seçeneklerle ayarlar.', 'service_text': 'select.select_option', 'services': ['select.select_option'], 'confirmation': 'optional', 'aliases': ['arka orta koltuk ısıtma aç', 'arka orta koltuk ısıtma kapat', 'arka orta koltuk ısıtma düşük yap', 'arka orta koltuk ısıtma orta yap', 'arka orta koltuk ısıtma yüksek yap', 'turn on rear center seat heater', 'turn off rear center seat heater', 'set rear center seat heater low', 'set rear center seat heater medium', 'set rear center seat heater high'], 'notes': 'Select seçenekleri araca göre değişebilir; geçerli option listesi entity attributes içinden alınmalı.'}, {'entity_example': 'select.pom_seat_heater_rear_right', 'capability': 'seat_heater_rear_right', 'name': 'Rear Right Seat Heater', 'domain': 'select', 'purpose': 'Sağ arka koltuk ısıtma seviyesini Off/Low/Medium/High benzeri seçeneklerle ayarlar.', 'service_text': 'select.select_option', 'services': ['select.select_option'], 'confirmation': 'optional', 'aliases': ['sağ arka koltuk ısıtma aç', 'sağ arka koltuk ısıtma kapat', 'sağ arka koltuk ısıtma düşük yap', 'sağ arka koltuk ısıtma orta yap', 'sağ arka koltuk ısıtma yüksek yap', 'turn on rear right seat heater', 'turn off rear right seat heater', 'set rear right seat heater low', 'set rear right seat heater medium', 'set rear right seat heater high'], 'notes': 'Select seçenekleri araca göre değişebilir; geçerli option listesi entity attributes içinden alınmalı.'}, {'entity_example': 'switch.pom_sentry_mode', 'capability': 'sentry_mode', 'name': 'Sentry Mode', 'domain': 'switch', 'purpose': 'Tesla Sentry/Nöbetçi güvenlik modunu açıp kapatır.', 'service_text': 'switch.turn_on / switch.turn_off', 'services': ['switch.turn_on', 'switch.turn_off'], 'confirmation': 'optional', 'aliases': ['sentry aç', 'sentry kapat', 'nöbetçi modunu aç', 'güvenlik modunu aç', 'nöbetçi modunu kapat', 'turn on sentry mode', 'turn off sentry mode', 'enable sentry', 'disable sentry'], 'notes': 'Güvenlik modu; kapatma komutu kullanıcı ayarına göre onaylı yapılabilir.'}, {'entity_example': 'switch.pom_steering_wheel_heater', 'capability': 'steering_wheel_heater', 'name': 'Steering Wheel Heater', 'domain': 'switch', 'purpose': 'Direksiyon ısıtmasını açıp kapatır.', 'service_text': 'switch.turn_on / switch.turn_off', 'services': ['switch.turn_on', 'switch.turn_off'], 'confirmation': 'optional', 'aliases': ['direksiyon ısıtmasını aç', 'direksiyon ısıtmasını kapat', 'direksiyonu ısıt', 'turn on steering wheel heater', 'turn off steering wheel heater', 'heat steering wheel'], 'notes': 'Düşük riskli konfor kontrolü.'}, {'entity_example': 'cover.pom_trunk', 'capability': 'trunk', 'name': 'Trunk', 'domain': 'cover', 'purpose': 'Arka bagaj/trunk kapağını açıp kapatır; destek araca göre değişir.', 'service_text': 'cover.open_cover / cover.close_cover', 'services': ['cover.open_cover', 'cover.close_cover'], 'confirmation': 'required', 'aliases': ['arka bagajı aç', 'bagajı aç', 'trunk aç', 'arka bagajı kapat', 'bagajı kapat', 'open trunk', 'close trunk', 'open rear trunk', 'close boot'], 'notes': 'Riskli komut. Açma/kapatma için onay gerekir.'}, {'entity_example': 'switch.pom_valet_mode', 'capability': 'valet_mode', 'name': 'Valet Mode', 'domain': 'switch', 'purpose': 'Vale modunu açıp kapatır.', 'service_text': 'switch.turn_on / switch.turn_off', 'services': ['switch.turn_on', 'switch.turn_off'], 'confirmation': 'required', 'aliases': ['vale modunu aç', 'valet mode aç', 'vale modunu kapat', 'valet mode kapat', 'turn on valet mode', 'turn off valet mode', 'enable valet mode', 'disable valet mode'], 'notes': 'Riskli araç erişim/sürüş kısıtlama ayarı. Her zaman onay ister.'}, {'entity_example': 'cover.pom_vent_windows', 'capability': 'vent_windows', 'name': 'Vent Windows', 'domain': 'cover', 'purpose': 'Camları havalandırma pozisyonuna alır veya kapatır.', 'service_text': 'cover.open_cover / cover.close_cover', 'services': ['cover.open_cover', 'cover.close_cover'], 'confirmation': 'required', 'aliases': ['camları havalandır', 'camları arala', 'camları aç', 'camları kapat', 'vent windows', 'close windows', 'open windows slightly', 'close vented windows'], 'notes': 'Cam kontrolü güvenlik/yağmur riski taşır; onay gerekir.'}, {'entity_example': 'button.pom_wake', 'capability': 'wake_vehicle', 'name': 'Wake Vehicle', 'domain': 'button', 'purpose': 'Aracı uyandırır/online hale getirmeyi dener.', 'service_text': 'button.press', 'services': ['button.press'], 'confirmation': 'optional', 'aliases': ['aracı uyandır', 'teslayı uyandır', 'uyan', 'arabayı uyandır', 'wake car', 'wake vehicle', 'wake Tesla'], 'notes': 'Bilgi soruları için otomatik wake yapılmamalı; kullanıcı açıkça isterse çalıştırılmalı.'}]



def get_pending_ai_alias_training_state(hass: HomeAssistant) -> dict[str, Any]:
    """Return pending AI alias training prompts."""
    return hass.data.setdefault(DOMAIN, {}).setdefault("pending_ai_alias_training", {})


AI_ALIAS_STORE_PATH = "/config/pom_tesla_report_ai_aliases.json"


def load_ai_control_aliases(hass: HomeAssistant) -> dict[str, Any]:
    """Load user-trained AI control aliases from disk into memory."""
    root = hass.data.setdefault(DOMAIN, {})
    if "ai_control_aliases" in root:
        return root["ai_control_aliases"]
    try:
        path = Path(AI_ALIAS_STORE_PATH)
        if path.exists():
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                aliases = raw
            else:
                aliases = {}
        else:
            aliases = {}
    except Exception:
        _LOGGER.debug("Could not load POM AI control aliases", exc_info=True)
        aliases = {}
    root["ai_control_aliases"] = aliases
    return aliases


def save_ai_control_aliases(hass: HomeAssistant) -> None:
    """Persist user-trained AI control aliases to disk."""
    aliases = hass.data.setdefault(DOMAIN, {}).setdefault("ai_control_aliases", {})
    try:
        path = Path(AI_ALIAS_STORE_PATH)
        path.write_text(json.dumps(aliases, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    except Exception:
        _LOGGER.exception("Could not save POM AI control aliases")


def get_ai_entity_training_options(hass: HomeAssistant, data: dict[str, Any]) -> list[dict[str, str]]:
    """Return explicit AI-enabled entities that can be used for alias training."""
    options: list[dict[str, str]] = []
    for item in get_vehicle_entity_entries(data):
        if not item.get("use_ai"):
            continue
        entity_id = str(item.get("entity_id") or "").strip()
        if not entity_id or "." not in entity_id:
            continue
        domain = entity_id.split(".", 1)[0]
        if domain not in {"button", "switch", "lock", "climate", "cover"}:
            continue
        state = hass.states.get(entity_id)
        friendly = ""
        if state is not None:
            friendly = str((state.attributes or {}).get("friendly_name") or "")
        label = str(item.get("label") or friendly or entity_id).strip()
        options.append({"entity_id": entity_id, "domain": domain, "label": label})
    return options[:12]


def parse_temperature_from_text(message: str) -> float | None:
    """Extract a plausible climate setpoint from user text."""
    normalized = normalize_text_for_match(message)
    match = re.search(r"(\d{2})(?:[\.,](\d))?\s*(?:derece|c|celsius)?", normalized)
    if not match:
        return None
    value = float(match.group(1))
    if match.group(2):
        value += float("0." + match.group(2))
    if 15 <= value <= 30:
        return value
    return None


def build_action_for_trained_alias(hass: HomeAssistant, entity_id: str, message: str, label: str | None = None) -> dict[str, Any] | None:
    """Build a safe action from a trained alias and explicit AI-enabled entity."""
    entity_id = str(entity_id or "").strip()
    if not entity_id or "." not in entity_id:
        return None
    domain = entity_id.split(".", 1)[0]
    n = normalize_text_for_match(message)
    label = str(label or entity_id).strip()

    def single(action_label: str, service: str, service_data: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = {"entity_id": entity_id}
        if service_data:
            payload.update(service_data)
        return {
            "label": action_label,
            "domain": domain,
            "service": service,
            "service_data": payload,
            "entity_id": entity_id,
            "risky": True,
        }

    if domain == "button":
        return single(label, "press")
    if domain == "switch":
        turn_off = any(term in n for term in ["kapat", "off", "disable", "pasif", "durdur", "stop"])
        return single(f"{label} kapat" if turn_off else f"{label} aç", "turn_off" if turn_off else "turn_on")
    if domain == "lock":
        wants_unlock = any(term in n for term in ["ac", "aç", "unlock", "kilidini ac", "kapilari ac", "kapıları aç", "arabayi ac", "arabayı aç"])
        wants_lock = any(term in n for term in ["kilitle", "lock", "kitle"])
        if wants_lock and not wants_unlock:
            return single("Araç kilitle", "lock")
        return single("Araç kilidini aç", "unlock")
    if domain == "cover":
        close = any(term in n for term in ["kapat", "close"])
        return single(f"{label} kapat" if close else f"{label} aç", "close_cover" if close else "open_cover")
    if domain == "climate":
        actions: list[dict[str, Any]] = []
        turn_off = any(term in n for term in ["kapat", "off", "durdur"])
        turn_on = any(term in n for term in ["ac", "aç", "calistir", "çalıştır", "on", "serinlet", "isit", "ısıt"])
        temp = parse_temperature_from_text(message)
        if turn_off:
            actions.append(single("Klima kapat", "turn_off"))
        else:
            if turn_on:
                actions.append(single("Klima aç", "turn_on"))
            if temp is not None:
                actions.append(single(f"Klimayı {temp:g}°C yap", "set_temperature", {"temperature": temp}))
        if not actions:
            actions.append(single(label, "turn_on"))
        if len(actions) == 1:
            actions[0]["actions"] = [copy.deepcopy(actions[0])]
            return actions[0]
        return {"label": " ve ".join(a.get("label", "Klima") for a in actions), "actions": actions, "risky": True, "multi_action": True}
    return None


def build_action_from_trained_aliases(hass: HomeAssistant, data: dict[str, Any], message: str) -> dict[str, Any] | None:
    """Alias training has been removed; capability manifest routing is used instead."""
    return None


async def async_send_ai_alias_training_prompt(
    hass: HomeAssistant,
    data: dict[str, Any],
    *,
    target: str,
    user_message: str,
) -> bool:
    """Alias training is intentionally disabled. Use the manifest instead."""
    return False


def _state_match_text(state: Any | None) -> str:
    """Return searchable text for an entity state."""
    if state is None:
        return ""
    attrs = getattr(state, "attributes", {}) or {}
    return normalize_text_for_match(
        " ".join(
            [
                str(getattr(state, "entity_id", "") or ""),
                str(attrs.get("friendly_name") or ""),
                str(attrs.get("device_class") or ""),
            ]
        )
    )


def find_ai_control_entity(
    hass: HomeAssistant,
    data: dict[str, Any],
    *,
    domain: str,
    exact_candidates: list[str] | None = None,
    include_terms: list[str] | None = None,
    prefer_terms: list[str] | None = None,
    exclude_terms: list[str] | None = None,
) -> str:
    """Find a vehicle control entity strictly from Vehicle Entity Manager AI entries.

    Security rule: AI vehicle controls may only use entities explicitly listed in
    Vehicle Entity Manager with ``use_ai`` enabled. This function intentionally
    never scans the full Home Assistant state registry and never auto-falls back
    to hardcoded entity ids such as ``button.pom_honk_horn``.
    """
    exact_candidates = exact_candidates or []
    exact_set = {str(entity_id).strip() for entity_id in exact_candidates if str(entity_id).strip()}
    include_terms = [normalize_text_for_match(x) for x in (include_terms or []) if x]
    prefer_terms = [normalize_text_for_match(x) for x in (prefer_terms or []) if x]
    exclude_terms = [normalize_text_for_match(x) for x in (exclude_terms or []) if x]

    allowed_entries: list[tuple[dict[str, Any], Any | None, str]] = []
    for item in get_vehicle_entity_entries(data):
        if not item.get("use_ai"):
            continue
        entity_id = str(item.get("entity_id") or "").strip()
        if not entity_id or not entity_id.startswith(f"{domain}."):
            continue
        state = hass.states.get(entity_id)
        attrs = getattr(state, "attributes", {}) or {}
        searchable = normalize_text_for_match(
            " ".join(
                [
                    entity_id,
                    str(item.get("label") or ""),
                    str(item.get("role") or ""),
                    str(attrs.get("friendly_name") or ""),
                    str(attrs.get("device_class") or ""),
                ]
            )
        )
        allowed_entries.append((item, state, searchable))

    # Exact candidates are allowed only when the user explicitly permitted the
    # entity in Vehicle Entity Manager / Use in AI. Otherwise they are ignored.
    for item, state, _searchable in allowed_entries:
        entity_id = str(item.get("entity_id") or "").strip()
        if entity_id in exact_set and state is not None:
            return entity_id

    scored: list[tuple[int, str]] = []
    for item, state, text in allowed_entries:
        entity_id = str(item.get("entity_id") or "").strip()
        if not entity_id or state is None:
            continue
        if exclude_terms and any(term in text for term in exclude_terms):
            continue
        if include_terms and not all(term in text for term in include_terms):
            continue
        score = 0
        # Prefer explicit user labels and role matches over generic name matches.
        role = normalize_text_for_match(str(item.get("role") or ""))
        label = normalize_text_for_match(str(item.get("label") or ""))
        for term in prefer_terms:
            if term in label:
                score += 40
            if term in role:
                score += 35
            if term in text:
                score += 20
        if "pom" in text:
            score += 5
        if "tesla" in text:
            score += 5
        scored.append((score, entity_id))

    if not scored:
        return ""
    scored.sort(key=lambda item: (-item[0], item[1]))
    return scored[0][1]




def is_ai_vehicle_control_confirmation_text(message: str) -> bool:
    """Return True if text should confirm a pending AI vehicle control."""
    n = normalize_text_for_match(message)
    if not n:
        return False
    return n in {
        "evet", "tamam", "onay", "onayla", "onayliyorum", "onayliyorum", "olur",
        "ok", "okay", "yes", "confirm", "approve", "go", "gonder", "calistir", "yap"
    } or any(term in n for term in ["onayliyorum", "onay veriyorum", "evet onay", "tamam onay", "baslat", "devam et"])


def is_ai_vehicle_control_cancel_text(message: str) -> bool:
    """Return True if text should cancel a pending AI vehicle control."""
    n = normalize_text_for_match(message)
    if not n:
        return False
    return n in {"hayir", "hayır", "iptal", "cancel", "vazgec", "vazgeç", "dur", "stop"} or any(term in n for term in ["iptal et", "vazgectim", "vazgeçtim"])




def is_contextual_ai_vehicle_control_confirmation_text(message: str, pending_item: dict[str, Any] | None = None) -> bool:
    """Return True when a short follow-up confirms the currently pending action.

    This catches natural replies like "kapat" after POM asked to close/off a heater,
    without treating "kapat" as a global confirmation when there is no pending action.
    """
    n = normalize_text_for_match(message)
    if not n or not pending_item:
        return False
    if is_ai_vehicle_control_confirmation_text(message):
        return True

    action = pending_item.get("action") or {}
    raw_actions = action.get("actions") if isinstance(action.get("actions"), list) else [action]
    labels = []
    services = []
    options = []
    for item in raw_actions:
        if not isinstance(item, dict):
            continue
        labels.append(normalize_text_for_match(str(item.get("label") or "")))
        services.append(normalize_text_for_match(str(item.get("service") or "")))
        sd = item.get("service_data") or {}
        if isinstance(sd, dict):
            options.append(normalize_text_for_match(str(sd.get("option") or "")))

    wants_off_pending = any(x in {"off", "turn_off", "close_cover", "lock"} for x in services + options) or any(_has_any_phrase(label, ["kapat", "off", "close"]) for label in labels)
    wants_on_pending = any(x in {"on", "turn_on", "open_cover", "unlock", "press"} for x in services + options) or any(_has_any_phrase(label, ["ac", "aç", "on", "open", "calistir", "press"]) for label in labels)

    if wants_off_pending and n in {"kapat", "kapat onu", "tamam kapat", "evet kapat", "kapatabilirsin", "off", "close"}:
        return True
    if wants_on_pending and n in {"ac", "aç", "tamam ac", "evet ac", "calistir", "baslat", "on", "open", "press"}:
        return True
    return False

def looks_like_vehicle_control_request(message: str) -> bool:
    """Broad guard: prevent control-looking requests from falling through to chat text."""
    n = normalize_text_for_match(message)
    if not n:
        return False
    if is_vehicle_status_question(message):
        return False

    control_nouns = [
        "arac", "araba", "tesla", "pom", "klima", "klimayi", "klimasini", "arac klimasini", "araba klimasini", "climate", "sentry", "valet",
        "korna", "horn", "honk", "fart", "osur", "osurt", "gaz cikar", "boombox",
        "far", "isig", "isik", "selektor", "flash", "defrost", "buz coz", "buz cozu",
        "kilit", "kapi", "frunk", "trunk", "bagaj", "kaput", "cam", "pencere",
        "sarj", "kablo", "port", "koltuk", "isitici", "isiticiyi", "isiticisi", "isiticilar", "isiticilari", "isitma", "isitmayi", "heater", "heaters", "direksiyon", "homelink", "garaj", "bariyer",
        "media", "medya", "muzik", "sarki", "ses"
    ]
    control_verbs = [
        "ac", "kapat", "kilitle", "kilidi ac", "kilidini ac", "calistir", "cal", "bas",
        "yak", "sondur", "ayarla", "yap", "gonder", "uyandir", "press", "open", "close",
        "lock", "unlock", "turn on", "turn off", "set", "start", "stop", "enable", "disable",
        "dusuk", "orta", "yuksek", "low", "medium", "high", "artir", "azalt", "kis", "duraklat", "isit", "isitici", "isiticiyi", "isitma", "isitmayi", "heat"
    ]
    return _has_any_phrase(n, control_nouns) and _has_any_phrase(n, control_verbs)


def is_indirect_vehicle_suggestion_statement(message: str) -> bool:
    """Detect comfort/status complaints that should become a *suggestion*, not an immediate control.

    Examples: "çok sıcak", "içerisi çok sıcak", "üşüdüm". These should let POM
    answer naturally and store a single pending_suggestion. They must not be routed
    through the immediate vehicle-control executor before chat generation.
    Direct commands such as "serinlet", "klimayı aç", "ısıt" still go through
    the control pipeline.
    """
    n = normalize_text_for_match(message)
    if not n or is_vehicle_status_question(message):
        return False

    # Explicit verbs mean the user is commanding, not merely complaining.
    direct_command_phrases = [
        "serinlet", "sogut", "klimayi ac", "klima ac", "klimasini ac", "climate ac",
        "isit", "isitmaya basla", "sicakligi yap", "derece yap", "ayarla",
        "kapat", "ac", "yap", "bas", "calistir", "turn on", "turn off", "set",
    ]
    if _has_any_phrase(n, direct_command_phrases):
        return False

    hot_phrases = [
        "cok sicak", "icerisi cok sicak", "icersi cok sicak", "araba cok sicak",
        "baya sicak", "baya sicak oldu", "sicak oldu", "ic sicaklik yuksek",
        "bunaldim", "terledim", "sicaktan bunaldim", "sıcaktan bunaldim",
    ]
    cold_phrases = [
        "cok soguk", "icerisi cok soguk", "araba cok soguk", "baya soguk",
        "soguk oldu", "usudum", "usuyorum", "donuyorum",
    ]
    return _has_any_phrase(n, hot_phrases) or _has_any_phrase(n, cold_phrases)


def _normalize_manifest_aliases(aliases: list[str]) -> list[str]:
    """Normalize aliases and add a few safe Turkish control variants."""
    result: list[str] = []
    for alias in aliases:
        n = normalize_text_for_match(alias)
        if n and n not in result:
            result.append(n)
        # Turkish users often use aç/yak interchangeably for lights.
        if " yak" in f" {n}" or n.endswith(" yak"):
            v = n.replace(" yak", " ac")
            if v and v not in result:
                result.append(v)
        if " ac" in f" {n}" or n.endswith(" ac"):
            v = n.replace(" ac", " yak")
            if v and v not in result:
                result.append(v)
    return result


def _capability_manifest_controls() -> list[dict[str, Any]]:
    """Return control capabilities from the curated manifest."""
    result: list[dict[str, Any]] = []
    for item in AI_CONTROL_CAPABILITY_MANIFEST:
        if not isinstance(item, dict):
            continue
        capability = str(item.get("capability") or "").strip()
        domain = str(item.get("domain") or "").strip()
        if not capability or not domain:
            continue
        aliases = list(item.get("aliases") or [])
        normalized_aliases = _normalize_manifest_aliases(aliases + [capability.replace("_", " "), str(item.get("name") or "")])
        copied = dict(item)
        copied["normalized_aliases"] = normalized_aliases
        result.append(copied)
    return result


def _vehicle_entity_search_text(hass: HomeAssistant, entry: dict[str, Any]) -> str:
    entity_id = str(entry.get("entity_id") or "").strip()
    state = hass.states.get(entity_id)
    friendly = ""
    if state is not None:
        friendly = str((state.attributes or {}).get("friendly_name") or "")
    return normalize_text_for_match(" ".join([
        entity_id,
        entity_id.split(".", 1)[-1].replace("_", " ") if "." in entity_id else entity_id,
        str(entry.get("label") or ""),
        str(entry.get("role") or ""),
        friendly,
    ]))


def _entity_matches_capability(hass: HomeAssistant, entry: dict[str, Any], cap: dict[str, Any]) -> int:
    """Score a Vehicle Entity Manager entry against a manifest capability."""
    entity_id = str(entry.get("entity_id") or "").strip()
    if not entity_id or "." not in entity_id:
        return 0
    domain = entity_id.split(".", 1)[0]
    expected_domain = str(cap.get("domain") or "").strip()
    if expected_domain and domain != expected_domain:
        return 0

    text = _vehicle_entity_search_text(hass, entry)
    capability = normalize_text_for_match(str(cap.get("capability") or "").replace("_", " "))
    name = normalize_text_for_match(str(cap.get("name") or ""))
    example_suffix = normalize_text_for_match(str(cap.get("entity_example") or "").split(".", 1)[-1].replace("_", " "))
    score = 0

    cap_words = [w for w in capability.split() if len(w) > 1]
    if cap_words and all(w in text for w in cap_words):
        score += 90
    elif cap_words and any(w in text for w in cap_words):
        score += 25

    name_words = [w for w in name.split() if len(w) > 2]
    if name_words and all(w in text for w in name_words):
        score += 55
    elif name_words and any(w in text for w in name_words):
        score += 15

    ex_words = [w for w in example_suffix.split() if len(w) > 2 and w not in {"pom", "tesla"}]
    if ex_words and all(w in text for w in ex_words):
        score += 70
    elif ex_words and any(w in text for w in ex_words):
        score += 20

    # Avoid common false-positive locks.
    cap_name = str(cap.get("capability") or "")
    if cap_name == "vehicle_lock" and any(term in text for term in ["charge cable", "s arj kablo", "sarj kablo", "cable"]):
        score -= 80
    if cap_name == "charge_cable_lock" and "cable" not in text and "kablo" not in text:
        score -= 40

    return max(score, 0)


def find_entity_for_manifest_capability(hass: HomeAssistant, data: dict[str, Any], cap: dict[str, Any]) -> str:
    """Find the best explicit Vehicle Entity Manager entity for a capability.

    This intentionally does not use hardcoded entity IDs. The example entity ID in
    the manifest is only used to infer capability words such as keyless_driving or
    flash_lights; another user's vehicle prefix can be different.
    """
    best: tuple[int, str] = (0, "")
    for entry in get_vehicle_entity_entries(data):
        # The current Vehicle Entity Manager defaults use_ai to True for older entries.
        if not entry.get("use_ai", True):
            continue
        score = _entity_matches_capability(hass, entry, cap)
        entity_id = str(entry.get("entity_id") or "").strip()
        if score > best[0] and entity_id:
            best = (score, entity_id)
    return best[1] if best[0] >= 35 else ""


def _message_mentions_capability(message: str, cap: dict[str, Any]) -> bool:
    if is_vehicle_status_question(message):
        return False

    normalized = normalize_text_for_match(message)
    aliases = list(cap.get("normalized_aliases") or [])
    if _has_any_phrase(normalized, aliases):
        return True

    capability = str(cap.get("capability") or "")

    # Specific capabilities first. Avoid broad substring matching.
    if capability == "climate":
        if _has_any_phrase(normalized, ["koltuk", "seat heater", "koltuk isitici", "koltuk isitma"]):
            return False
        return _has_any_phrase(normalized, [
            "klima", "klimayi", "klimasini", "arac klimasini", "araba klimasini", "climate", "hvac", "sogut", "serinlet", "sicaklik", "derece",
            "kabini isit", "araci isit", "arabayi isit", "heat the car", "cool the car",
        ])

    if capability.startswith("seat_heater_"):
        # Seat heater commands may be written as "sol arka koltuk ısıtıcı"
        # or simply "sol arka ısıtıcı". Do not require the word koltuk.
        if _has_any_phrase(normalized, ["direksiyon", "steering"]):
            return False
        # Seat heater commands may include either a heater verb (ısıt/aç) or
        # a direct level value such as "low/medium/high". Example:
        # "sol arka koltuk low" should still route to rear-left seat heater.
        if not _has_any_phrase(normalized, [
            "isit", "isitici", "isiticiyi", "isitma", "isitmayi", "heater", "heat",
            "ac", "kapat", "off", "low", "medium", "high", "dusuk", "orta", "yuksek", "1", "2", "3"
        ]):
            return False
        # Map Turkish natural orders: "arka sol" and "sol arka".
        if capability == "seat_heater_front_left":
            return _has_any_phrase(normalized, ["sol on", "on sol", "surucu", "driver", "front left", "left front"])
        if capability == "seat_heater_front_right":
            return _has_any_phrase(normalized, ["sag on", "on sag", "yolcu", "passenger", "front right", "right front"])
        if capability == "seat_heater_rear_left":
            return _has_any_phrase(normalized, ["sol arka", "arka sol", "rear left", "left rear"])
        if capability == "seat_heater_rear_right":
            return _has_any_phrase(normalized, ["sag arka", "arka sag", "rear right", "right rear"])
        if capability == "seat_heater_rear_center":
            return _has_any_phrase(normalized, ["arka orta", "orta arka", "rear center", "center rear"])
        return True

    if capability == "flash_lights":
        return _has_any_phrase(normalized, ["isigi ac", "isiklari ac", "isigi yak", "isiklari yak", "far", "selektor", "flash lights", "flash"])
    if capability == "honk_horn":
        return _has_any_phrase(normalized, ["korna", "kornaya", "kornayi", "kornasini", "horn", "honk", "beep"])
    if capability == "play_fart":
        return _has_any_phrase(normalized, ["fart", "osur", "osurt", "gaz cikar", "boombox"])
    if capability == "keyless_driving":
        return _has_any_phrase(normalized, ["arabayi calistir", "araci calistir", "teslayi calistir", "remote start", "keyless", "suruse hazirla", "start the car"])
    if capability == "wake_vehicle":
        return _has_any_phrase(normalized, ["araci uyandir", "arabayi uyandir", "teslayi uyandir", "wake car", "wake vehicle", "wake tesla"])
    if capability == "charge_control":
        return _has_any_phrase(normalized, ["sarji baslat", "sarj etmeye basla", "sarji durdur", "sarji kes", "start charging", "stop charging"])
    if capability == "vehicle_lock":
        has_vehicle = _has_any_phrase(normalized, ["arac", "araba", "tesla", "kapi", "kapilar", "kapilari", "kilit", "door", "doors", "car"])
        has_action = _has_any_phrase(normalized, ["kilitle", "kitle", "kilidi ac", "kilidini ac", "kapilari ac", "arabayi ac", "araci ac", "lock", "unlock", "lock doors", "unlock doors"])
        return has_vehicle and has_action
    if capability == "vent_windows":
        # Only control commands, not "cam açık mı" status questions.
        return _has_any_phrase(normalized, ["camlari havalandir", "camlari arala", "camlari ac", "camlari kapat", "vent windows", "close windows"])

    return False


def _confirmation_required(cap: dict[str, Any], *, service: str, data: dict[str, Any] | None = None) -> bool:
    conf = str(cap.get("confirmation") or "required").strip().lower()
    capability = str(cap.get("capability") or "")
    force_confirmation = bool((data or {}).get(CONF_AI_CONFIRM_OPTIONAL_CONTROLS, DEFAULT_AI_CONFIRM_OPTIONAL_CONTROLS))
    if force_confirmation and conf != "not_applicable":
        return True
    if conf == "none":
        return False
    if conf == "required":
        return True
    if conf == "mixed":
        # Vehicle lock: locking is normally safe, unlocking requires confirmation.
        if capability == "vehicle_lock" and service == "lock":
            return False
        return True
    if conf == "optional":
        # Optional controls only ask when the user enables this checkbox in POM AI Basic.
        return bool((data or {}).get(CONF_AI_CONFIRM_OPTIONAL_CONTROLS, DEFAULT_AI_CONFIRM_OPTIONAL_CONTROLS))
    return True


def _make_manifest_action(label: str, domain: str, service: str, entity_id: str, cap: dict[str, Any], service_data: dict[str, Any] | None = None, data: dict[str, Any] | None = None) -> dict[str, Any] | None:
    if not entity_id:
        return None
    payload = {"entity_id": entity_id}
    if service_data:
        payload.update(service_data)
    return {
        "label": label,
        "domain": domain,
        "service": service,
        "service_data": payload,
        "entity_id": entity_id,
        "capability": cap.get("capability"),
        "risky": _confirmation_required(cap, service=service, data=data),
    }


def _build_actions_for_capability(hass: HomeAssistant, data: dict[str, Any], cap: dict[str, Any], message: str) -> list[dict[str, Any]]:
    capability = str(cap.get("capability") or "")
    domain = str(cap.get("domain") or "")
    normalized = normalize_text_for_match(message)
    entity_id = find_entity_for_manifest_capability(hass, data, cap)
    if not entity_id:
        return []

    actions: list[dict[str, Any]] = []
    wants_off = _has_any_phrase(normalized, ["kapat", "off", "disable", "pasif", "durdur", "stop", "kes"])
    wants_on = _has_any_phrase(normalized, ["ac", "aktif", "on", "enable", "baslat", "start", "calistir", "serinlet", "isit", "yak", "turn on"])
    wants_close = _has_any_phrase(normalized, ["kapat", "close", "close cover"])
    wants_unlock = _has_any_phrase(normalized, ["unlock", "kilidi ac", "kilidini ac", "kapilari ac", "arabayi ac", "araci ac", "unlock doors", "unlock car"])
    wants_lock = _has_any_phrase(normalized, ["lock", "kilitle", "kitle", "kapilari kilitle", "lock doors", "lock car"])

    if capability == "climate":
        temp = parse_temperature_from_text(message)
        if wants_off:
            action = _make_manifest_action("Klima kapat", "climate", "turn_off", entity_id, cap, data=data)
            if action: actions.append(action)
        else:
            if wants_on or temp is not None:
                action = _make_manifest_action("Klima aç", "climate", "turn_on", entity_id, cap, data=data)
                if action and wants_on: actions.append(action)
            if temp is not None:
                action = _make_manifest_action(f"Klimayı {temp:g}°C yap", "climate", "set_temperature", entity_id, cap, {"temperature": temp}, data=data)
                if action: actions.append(action)
            elif wants_on:
                pass
        return actions

    if domain == "button":
        label = str(cap.get("name") or capability).strip()
        special_labels = {
            "flash_lights": "Işıkları yak / flash lights",
            "honk_horn": "Korna çal",
            "play_fart": "Fart mode çalıştır",
            "keyless_driving": "Keyless driving / remote start",
            "wake_vehicle": "Aracı uyandır",
            "homelink": "HomeLink çalıştır",
        }
        action = _make_manifest_action(special_labels.get(capability, label), "button", "press", entity_id, cap, data=data)
        return [action] if action else []

    if domain == "switch":
        service = "turn_off" if wants_off else "turn_on"
        label = str(cap.get("name") or capability).strip()
        suffix = "kapat" if service == "turn_off" else "aç"
        action = _make_manifest_action(f"{label} {suffix}", "switch", service, entity_id, cap, data=data)
        return [action] if action else []

    if domain == "lock":
        service = "unlock" if wants_unlock and not wants_lock else "lock"
        label = "Araç kilidini aç" if capability == "vehicle_lock" and service == "unlock" else "Aracı kilitle" if capability == "vehicle_lock" else f"{cap.get('name') or capability} {'aç' if service == 'unlock' else 'kilitle'}"
        action = _make_manifest_action(label, "lock", service, entity_id, cap, data=data)
        return [action] if action else []

    if domain == "cover":
        service = "close_cover" if wants_close else "open_cover"
        label = str(cap.get("name") or capability).strip()
        suffix = "kapat" if service == "close_cover" else "aç"
        action = _make_manifest_action(f"{label} {suffix}", "cover", service, entity_id, cap, data=data)
        return [action] if action else []

    if domain == "select":
        # Seat heater levels. Tesla/Tessie usually exposes lowercase options:
        # off, low, medium, high. Read the entity's actual option list and keep
        # its exact casing so HA does not reject the service call.
        desired = None
        if _has_any_phrase(normalized, ["kapat", "off", "sifir", "0"]):
            desired = "off"
        elif _has_any_phrase(normalized, ["dusuk", "low", "1"]):
            desired = "low"
        elif _has_any_phrase(normalized, ["orta", "medium", "2"]):
            desired = "medium"
        elif _has_any_phrase(normalized, ["yuksek", "high", "3", "ac", "isit", "isitici", "isiticiyi", "isitma", "isitmayi", "heat", "heater"]):
            desired = "high"
        # Natural commands like "sol arka koltuk ısıt" usually mean turn it on.
        if desired is None and _has_any_phrase(normalized, ["isit", "isitici", "isiticiyi", "isitma", "isitmayi", "heat", "heater"]):
            desired = "high"
        if desired:
            state = hass.states.get(entity_id)
            valid_options = list((getattr(state, "attributes", {}) or {}).get("options") or []) if state is not None else []
            option = desired
            for candidate in valid_options:
                if normalize_text_for_match(str(candidate)) == desired:
                    option = str(candidate)
                    break
            label = f"{cap.get('name') or capability} {option}"
            action = _make_manifest_action(label, "select", "select_option", entity_id, cap, {"option": option}, data=data)
            return [action] if action else []
        return []

    if domain == "media_player":
        service = None
        label = str(cap.get("name") or capability)
        if _has_any_phrase(normalized, ["sonraki", "next"]):
            service = "media_next_track"; label = "Sonraki medya"
        elif _has_any_phrase(normalized, ["onceki", "previous"]):
            service = "media_previous_track"; label = "Önceki medya"
        elif _has_any_phrase(normalized, ["durdur", "baslat", "play", "pause"]):
            service = "media_play_pause"; label = "Medya oynat/duraklat"
        if service:
            action = _make_manifest_action(label, "media_player", service, entity_id, cap, data=data)
            return [action] if action else []
        return []

    return []


def _build_all_seat_heater_actions(hass: HomeAssistant, data: dict[str, Any], message: str) -> list[dict[str, Any]]:
    """Build actions for broad seat heater commands.

    Handles commands such as:
    - "koltuk ısıtıcılarını kapat" -> all seat heaters off
    - "arka ısıtıcıyı kapat" -> all rear seat heaters off
    - "ön koltuk ısıtıcıları low" -> front seat heaters low
    """
    normalized = normalize_text_for_match(message)
    if _has_any_phrase(normalized, ["direksiyon", "steering", "klima", "climate"]):
        return []

    mentions_seat_heater = _has_any_phrase(normalized, [
        "koltuk isiticilar", "koltuk isitmalari", "koltuk isiticilarini",
        "koltuk isitici", "koltuk isiticisi", "koltuk isiticiyi", "koltuk isitma", "isiticilari", "isiticiyi", "isiticisi", "isiticilar",
        "arka isitici", "arka isiticiyi", "arka isiticisi", "arka isiticilari", "on isitici", "on isiticiyi", "on isiticisi", "on isiticilari",
        "seat heaters", "seat heater", "all seat heaters", "rear heater", "rear heaters", "rear seat heater", "rear seat heaters",
        "front heater", "front heaters", "front seat heater", "front seat heaters",
    ])
    if not mentions_seat_heater:
        return []

    desired = None
    if _has_any_phrase(normalized, ["kapat", "off", "sifir", "0"]):
        desired = "off"
    elif _has_any_phrase(normalized, ["dusuk", "low", "1"]):
        desired = "low"
    elif _has_any_phrase(normalized, ["orta", "medium", "2"]):
        desired = "medium"
    elif _has_any_phrase(normalized, ["yuksek", "high", "3", "ac", "isit"]):
        desired = "high"
    if desired is None:
        return []

    rear_only = _has_any_phrase(normalized, ["arka", "rear"])
    front_only = _has_any_phrase(normalized, ["on", "front", "ön"])
    left_only = _has_any_phrase(normalized, ["sol", "left"])
    right_only = _has_any_phrase(normalized, ["sag", "sağ", "right"])
    center_only = _has_any_phrase(normalized, ["orta", "center", "middle"])

    actions: list[dict[str, Any]] = []
    for cap in _capability_manifest_controls():
        capability = str(cap.get("capability") or "")
        if not capability.startswith("seat_heater_"):
            continue
        if rear_only and "_rear_" not in capability:
            continue
        if front_only and "_front_" not in capability:
            continue
        if left_only and not capability.endswith("_left"):
            continue
        if right_only and not capability.endswith("_right"):
            continue
        if center_only and not capability.endswith("_center"):
            continue

        entity_id = find_entity_for_manifest_capability(hass, data, cap)
        if not entity_id:
            continue
        state = hass.states.get(entity_id)
        valid_options = list((getattr(state, "attributes", {}) or {}).get("options") or []) if state is not None else []
        option = desired
        for candidate in valid_options:
            if normalize_text_for_match(str(candidate)) == desired:
                option = str(candidate)
                break
        label = f"{cap.get('name') or capability} {option}"
        action = _make_manifest_action(label, "select", "select_option", entity_id, cap, {"option": option}, data=data)
        if action:
            actions.append(action)
    return actions

def build_ai_vehicle_control_action(hass: HomeAssistant, data: dict[str, Any], message: str) -> dict[str, Any] | None:
    """Build vehicle control actions using the curated capability manifest.

    The router is capability-based, not entity-id based. Entity IDs in the manifest
    are examples only. Runtime execution is allowed only through Vehicle Entity
    Manager entries with AI usage enabled.
    """
    if not looks_like_vehicle_control_request(message):
        return None

    actions: list[dict[str, Any]] = []
    missing_caps: list[str] = []
    matched_any = False

    group_seat_actions = _build_all_seat_heater_actions(hass, data, message)
    if group_seat_actions:
        actions.extend(group_seat_actions)
        matched_any = True

    for cap in _capability_manifest_controls():
        if not _message_mentions_capability(message, cap):
            continue
        matched_any = True
        cap_actions = _build_actions_for_capability(hass, data, cap, message)
        if not cap_actions:
            missing_caps.append(str(cap.get("name") or cap.get("capability") or "Araç kontrolü"))
            continue
        for action in cap_actions:
            if not action:
                continue
            key = (action.get("domain"), action.get("service"), json.dumps(action.get("service_data") or {}, sort_keys=True))
            if not any((a.get("domain"), a.get("service"), json.dumps(a.get("service_data") or {}, sort_keys=True)) == key for a in actions):
                actions.append(action)

    if not actions:
        if matched_any or looks_like_vehicle_control_request(message):
            missing = missing_caps[0] if missing_caps else "Araç kontrolü"
            return {
                "error": True,
                "label": missing,
                "message": (
                    f"{missing} için yetkili Home Assistant entity'si bulunamadı. "
                    "Vehicle Entity Manager içinde ilgili entity'yi ekle ve AI kullanımını açık bırak."
                ),
            }
        return None

    if len(actions) == 1:
        single = actions[0]
        single["actions"] = [copy.deepcopy(single)]
        return single

    label = " ve ".join(str(action.get("label") or "Araç kontrolü") for action in actions)
    return {
        "label": label,
        "actions": actions,
        "risky": any(bool(action.get("risky", True)) for action in actions),
        "multi_action": True,
    }

async def async_send_ai_vehicle_control_confirmation(
    hass: HomeAssistant,
    *,
    target: str,
    action: dict[str, Any],
    user_message: str,
) -> None:
    """Ask Telegram user to confirm one or more detected vehicle control actions."""
    token = str(int(datetime.now().timestamp() * 1000))[-10:]
    pending = get_pending_ai_vehicle_control_state(hass)
    pending[token] = {
        "created_ts": datetime.now().timestamp(),
        "target": target,
        "chat_id": normalize_telegram_id(target),
        "action": copy.deepcopy(action),
        "user_message": user_message,
    }

    actions = action.get("actions") if isinstance(action.get("actions"), list) else [action]
    valid_actions = [item for item in actions if isinstance(item, dict) and not item.get("error")]

    if len(valid_actions) > 1:
        action_lines = ["Çalıştırılacak işlemler:"]
        for index, item in enumerate(valid_actions, start=1):
            entity_id = str(item.get("entity_id") or (item.get("service_data") or {}).get("entity_id") or "-")
            service = f"{item.get('domain')}.{item.get('service')}"
            action_lines.append(f"{index}. {item.get('label') or 'Araç kontrolü'}  ({service} · {entity_id})")
        action_detail = "\n".join(action_lines)
    else:
        item = valid_actions[0] if valid_actions else action
        entity_id = str(item.get("entity_id") or (item.get("service_data") or {}).get("entity_id") or "-")
        action_detail = f"İstenen işlem: {item.get('label') or action.get('label')}\nEntity: {entity_id}"

    message_text = (
        "POM araç kontrol onayı\n\n"
        f"{action_detail}\n\n"
        "Bu işlem araca komut gönderecek. Onaylıyor musun?"
    )
    localized_message = await async_translate_runtime_message_if_needed(
        hass,
        get_first_entry_config(hass) or {},
        user_message=user_message,
        message_text=message_text,
    )
    confirm_label = await async_translate_runtime_message_if_needed(
        hass,
        get_first_entry_config(hass) or {},
        user_message=user_message,
        message_text="Onayla",
    )
    cancel_label = await async_translate_runtime_message_if_needed(
        hass,
        get_first_entry_config(hass) or {},
        user_message=user_message,
        message_text="İptal",
    )

    await hass.services.async_call(
        "telegram_bot",
        "send_message",
        {
            "target": target,
            "parse_mode": "plain_text",
            "message": localized_message,
            "inline_keyboard": [
                f"{confirm_label}:/pom_ai_control_confirm_{token}, {cancel_label}:/pom_ai_control_cancel_{token}",
            ],
        },
        blocking=True,
    )


async def async_execute_ai_vehicle_control_action(hass: HomeAssistant, action: dict[str, Any]) -> str:
    """Execute one or more confirmed vehicle control actions."""
    raw_actions = action.get("actions") if isinstance(action.get("actions"), list) else [action]
    actions = [item for item in raw_actions if isinstance(item, dict) and not item.get("error")]
    if not actions:
        raise ValueError("Çalıştırılacak geçerli araç kontrol işlemi bulunamadı.")

    results: list[str] = []
    for item in actions:
        domain = str(item.get("domain") or "").strip()
        service = str(item.get("service") or "").strip()
        service_data = dict(item.get("service_data") or {})
        label = str(item.get("label") or "Araç kontrolü").strip()

        if not domain or not service or not service_data.get("entity_id"):
            raise ValueError(f"{label} için eksik servis bilgisi nedeniyle araç kontrolü çalıştırılamadı.")

        await hass.services.async_call(domain, service, service_data, blocking=True)
        results.append(f"{label} komutu gonderildi.")

    if len(results) == 1:
        return results[0]
    return "Arac kontrol komutlari gonderildi:\n" + "\n".join(f"{idx}. {line}" for idx, line in enumerate(results, start=1))



def _json_from_ai_router_text(text: str) -> dict[str, Any] | None:
    """Parse the strict LLM intent-router JSON response."""
    raw = str(text or "").strip()
    if not raw:
        return None
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE).strip()
        raw = re.sub(r"\s*```$", "", raw).strip()
    try:
        obj = json.loads(raw)
        return obj if isinstance(obj, dict) else None
    except Exception:
        pass
    match = re.search(r"\{[\s\S]*\}", raw)
    if not match:
        return None
    try:
        obj = json.loads(match.group(0))
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def _configured_control_capabilities_for_llm(hass: HomeAssistant, data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return manifest controls that have a matching Vehicle Entity Manager entity."""
    controls: list[dict[str, Any]] = []
    for cap in _capability_manifest_controls():
        entity_id = find_entity_for_manifest_capability(hass, data, cap)
        if not entity_id:
            continue
        item = {
            "capability": str(cap.get("capability") or ""),
            "name": str(cap.get("name") or ""),
            "domain": str(cap.get("domain") or ""),
            "services": list(cap.get("services") or []),
            "confirmation": str(cap.get("confirmation") or "required"),
            "aliases": list(cap.get("aliases") or [])[:24],
        }
        controls.append(item)
    return controls


def _capability_by_name(capability: str) -> dict[str, Any] | None:
    wanted = str(capability or "").strip().lower()
    if not wanted:
        return None
    for cap in _capability_manifest_controls():
        if str(cap.get("capability") or "").strip().lower() == wanted:
            return cap
    return None


def _select_option_for_action(hass: HomeAssistant, entity_id: str, desired: str) -> str:
    """Return a valid select option preserving HA's exact option casing."""
    desired_n = normalize_text_for_match(desired)
    if desired_n in {"on", "open", "turn_on", "enable", "ac", "heat", "isit"}:
        desired_n = "high"
    if desired_n in {"close", "turn_off", "disable", "kapat"}:
        desired_n = "off"
    state = hass.states.get(entity_id)
    valid_options = list((getattr(state, "attributes", {}) or {}).get("options") or []) if state is not None else []
    for candidate in valid_options:
        if normalize_text_for_match(str(candidate)) == desired_n:
            return str(candidate)
    return desired_n or "high"


def _build_manifest_action_from_llm_action(
    hass: HomeAssistant,
    data: dict[str, Any],
    llm_action: dict[str, Any],
) -> dict[str, Any] | None:
    """Convert a capability/action JSON item into a verified HA service action."""
    capability = str(llm_action.get("capability") or "").strip()
    cap = _capability_by_name(capability)
    if not cap:
        return None
    entity_id = find_entity_for_manifest_capability(hass, data, cap)
    if not entity_id:
        return None
    domain = str(cap.get("domain") or entity_id.split(".", 1)[0]).strip()
    action = normalize_text_for_match(str(llm_action.get("action") or "").strip())
    action = action.replace(" ", "_")
    raw_data = llm_action.get("data") if isinstance(llm_action.get("data"), dict) else {}
    raw_data = raw_data or {}
    name = str(cap.get("name") or capability).strip() or capability

    if domain == "button":
        if action not in {"press", "turn_on", "start", "trigger", "play"}:
            action = "press"
        return _make_manifest_action(name, "button", "press", entity_id, cap, data=data)

    if domain == "switch":
        service = "turn_off" if action in {"turn_off", "off", "stop", "disable", "close"} else "turn_on"
        label = f"{name} {'kapat' if service == 'turn_off' else 'aç'}"
        return _make_manifest_action(label, "switch", service, entity_id, cap, data=data)

    if domain == "lock":
        service = "unlock" if action in {"unlock", "open", "turn_on"} else "lock"
        label = "Araç kilidini aç" if service == "unlock" else "Aracı kilitle"
        return _make_manifest_action(label, "lock", service, entity_id, cap, data=data)

    if domain == "cover":
        service = "close_cover" if action in {"close", "close_cover", "turn_off", "off"} else "open_cover"
        label = f"{name} {'kapat' if service == 'close_cover' else 'aç'}"
        return _make_manifest_action(label, "cover", service, entity_id, cap, data=data)

    if domain == "climate":
        if action in {"turn_off", "off", "stop", "disable"}:
            return _make_manifest_action("Klima kapat", "climate", "turn_off", entity_id, cap, data=data)
        if action in {"set_temperature", "temperature", "set_temp"}:
            temp = safe_float(raw_data.get("temperature"), None)
            if temp is None:
                # Accept values such as {"value": 25} too.
                temp = safe_float(raw_data.get("value"), None)
            if temp is None:
                return None
            return _make_manifest_action(f"Klimayı {temp:g}°C yap", "climate", "set_temperature", entity_id, cap, {"temperature": temp}, data=data)
        if action in {"set_hvac_mode", "hvac_mode"}:
            hvac_mode = str(raw_data.get("hvac_mode") or raw_data.get("mode") or "heat_cool").strip() or "heat_cool"
            return _make_manifest_action(f"Klima modunu {hvac_mode} yap", "climate", "set_hvac_mode", entity_id, cap, {"hvac_mode": hvac_mode}, data=data)
        return _make_manifest_action("Klima aç", "climate", "turn_on", entity_id, cap, data=data)

    if domain == "select":
        option = str(raw_data.get("option") or raw_data.get("level") or raw_data.get("value") or "").strip()
        if not option:
            if action in {"turn_off", "off", "close", "disable"}:
                option = "off"
            elif action in {"set_low", "low"}:
                option = "low"
            elif action in {"set_medium", "medium"}:
                option = "medium"
            else:
                option = "high"
        option = _select_option_for_action(hass, entity_id, option)
        return _make_manifest_action(f"{name} {option}", "select", "select_option", entity_id, cap, {"option": option}, data=data)

    if domain == "media_player":
        service = None
        label = name
        if action in {"next", "media_next_track", "next_track"}:
            service = "media_next_track"; label = "Sonraki medya"
        elif action in {"previous", "media_previous_track", "previous_track"}:
            service = "media_previous_track"; label = "Önceki medya"
        elif action in {"play_pause", "media_play_pause", "play", "pause"}:
            service = "media_play_pause"; label = "Medya oynat/duraklat"
        elif action in {"set_volume", "volume_set"}:
            volume = safe_float(raw_data.get("volume_level"), None)
            if volume is None:
                volume = safe_float(raw_data.get("volume"), None)
            if volume is not None:
                if volume > 1:
                    volume = volume / 100
                volume = max(0.0, min(1.0, volume))
                return _make_manifest_action("Medya sesi ayarla", "media_player", "volume_set", entity_id, cap, {"volume_level": volume}, data=data)
        if service:
            return _make_manifest_action(label, "media_player", service, entity_id, cap, data=data)
    return None


def build_ai_vehicle_control_action_from_llm_intent(
    hass: HomeAssistant,
    data: dict[str, Any],
    intent: dict[str, Any],
) -> dict[str, Any] | None:
    """Build a verified action object from LLM intent-router JSON."""
    if not isinstance(intent, dict):
        return None
    typ = str(intent.get("type") or intent.get("intent") or "").strip().lower()
    if typ in {"not_control", "status", "information", "chat", "none"}:
        return None
    if typ not in {"vehicle_control", "control"}:
        return None
    raw_actions = intent.get("actions")
    if not isinstance(raw_actions, list):
        raw_actions = [intent.get("action")] if isinstance(intent.get("action"), dict) else []

    actions: list[dict[str, Any]] = []
    missing: list[str] = []
    for raw in raw_actions:
        if not isinstance(raw, dict):
            continue
        cap_name = str(raw.get("capability") or "").strip()
        cap = _capability_by_name(cap_name)
        if not cap:
            missing.append(cap_name or "unknown")
            continue
        built = _build_manifest_action_from_llm_action(hass, data, raw)
        if built:
            key = (built.get("domain"), built.get("service"), json.dumps(built.get("service_data") or {}, sort_keys=True))
            if not any((a.get("domain"), a.get("service"), json.dumps(a.get("service_data") or {}, sort_keys=True)) == key for a in actions):
                actions.append(built)
        else:
            missing.append(str(cap.get("name") or cap.get("capability") or cap_name))

    if not actions:
        if missing:
            missing_label = missing[0]
            return {
                "error": True,
                "label": missing_label,
                "message": (
                    f"{missing_label} için yetkili Home Assistant entity'si bulunamadı veya servis uyumsuz. "
                    "Vehicle Entity Manager içinde ilgili entity'yi eklediğinden emin ol."
                ),
            }
        return None
    if len(actions) == 1:
        single = actions[0]
        single["actions"] = [copy.deepcopy(single)]
        if intent.get("summary_tr") or intent.get("summary"):
            single["label"] = str(intent.get("summary_tr") or intent.get("summary") or single.get("label"))
        return single
    risky = any(bool(a.get("risky", True)) for a in actions)
    return {
        "label": str(intent.get("summary_tr") or intent.get("summary") or "Araç kontrol komutları"),
        "domain": "multi",
        "service": "multi",
        "entity_id": "",
        "service_data": {},
        "risky": risky,
        "actions": actions,
    }


async def async_build_ai_vehicle_control_action_with_llm(
    hass: HomeAssistant,
    data: dict[str, Any],
    user_message: str,
) -> dict[str, Any] | None:
    """Use the configured OpenAI model as a natural-language intent router.

    The LLM may only output capability names. It never receives permission to
    choose entity IDs or HA services directly; those are resolved and verified by
    code against the curated manifest and Vehicle Entity Manager.
    """
    api_key = str(data.get(CONF_OPENAI_API_KEY, "")).strip()
    if not api_key:
        return None
    controls = _configured_control_capabilities_for_llm(hass, data)
    if not controls:
        return None
    model = str(data.get(CONF_OPENAI_MODEL, DEFAULT_OPENAI_MODEL)).strip() or DEFAULT_OPENAI_MODEL
    max_output_tokens = 700
    capability_json = json.dumps(controls, ensure_ascii=False)
    system_prompt = (
        "You are Tesla AI's strict vehicle-control intent router. "
        "Return ONLY valid JSON. No prose. No markdown. "
        "Your job is to decide whether the user is asking to CONTROL the car, not to answer as a chat assistant. "
        "Use only the capability values listed in AVAILABLE_CAPABILITIES. Never invent a capability, entity_id, or service. "
        "If the user asks a status/info question such as 'is it on?', 'is the car awake?', 'is it charging?', 'window open?', return {\"type\":\"not_control\"}. "
        "If the user asks a control command, return {\"type\":\"vehicle_control\",\"summary_tr\":\"...\",\"actions\":[...]}. "
        "Each action must have capability and action. Allowed action words: turn_on, turn_off, press, lock, unlock, open, close, set_temperature, set_hvac_mode, set_option, play_pause, next_track, previous_track, set_volume. "
        "For climate commands like 'serinlet', 'cool the car', 'klimayi ac', use capability climate and action turn_on. "
        "For 'klimayi ac ve 25 derece yap', return two actions: climate turn_on and climate set_temperature with data {temperature:25}. "
        "For seat heater commands, use the most specific seat_heater_* capability available; levels are off/low/medium/high in data.option. "
        "For 'arka isiticiyi kapat', return all available rear seat heater capabilities with action set_option and data {option:'off'}. "
        "For buttons such as horn, flash lights, fart, wake, keyless driving, return action press. "
        "For Turkish text, understand spelling without Turkish characters too: klima/klima, klıma, serinlet, isit, osurt, korna, cal, ac, kapat. "
    )
    context_text = "AVAILABLE_CAPABILITIES:\n" + capability_json
    try:
        text = await async_call_openai_responses_api(
            hass,
            api_key=api_key,
            model=model,
            system_prompt=system_prompt,
            user_message=user_message,
            context_text=context_text,
            max_output_tokens=max_output_tokens,
        )
    except Exception as err:
        _LOGGER.debug("POM AI LLM intent router failed, falling back to deterministic router: %s", err)
        return None
    intent = _json_from_ai_router_text(text)
    if not intent:
        _LOGGER.debug("POM AI LLM intent router returned unparsable output: %s", text)
        return None
    return build_ai_vehicle_control_action_from_llm_intent(hass, data, intent)


def _is_pending_suggestion_expired(pending: dict[str, Any], timeout_seconds: int = 120) -> bool:
    created_ts = safe_float(pending.get("created_ts"), 0.0)
    if created_ts <= 0:
        return True
    return (datetime.now().timestamp() - created_ts) > timeout_seconds


def is_ai_vehicle_suggestion_followup_text(message: str, pending: dict[str, Any] | None = None) -> bool:
    """Return True for short contextual replies that accept the single suggestion.

    This is deliberately stricter than a generic parser. It should not catch
    clear new commands such as "kilidi aç" or status questions such as
    "şarjım kaç". Those must be handled as new messages, not as acceptance of
    an old suggestion.
    """
    n = normalize_text_for_match(message)
    if not n or not pending:
        return False
    if is_vehicle_status_question(message) or looks_like_vehicle_control_request(message):
        # A clear new command or info question wins over old context, except very
        # short contextual words below.
        pass

    short_yes = {
        "evet", "tamam", "olur", "ok", "okay", "yes", "yap", "hadi", "hadi bas",
        "bas", "devam", "devam et", "calistir", "çalıştır", "baslat", "başlat",
        "uygula", "aynen", "olur yap", "tamam yap", "tamam bas", "evet yap",
        "evet bas", "evet ac", "tamam ac", "ac", "aç", "ac bakalim", "aç bakalım",
        "hadi ac", "hadi aç", "bas bakalim", "bas bakalım", "kapat", "tamam kapat",
        "evet kapat", "veririm", "onay veririm", "onayliyorum", "onaylıyorum",
        "onay veriyorum", "evet onay veriyorum", "tamam onay veriyorum",
        "izin veriyorum", "tamam izin veriyorum", "veriyorum",
    }
    if n in {normalize_text_for_match(x) for x in short_yes}:
        return True
    return False


async def async_handle_ai_vehicle_suggestion_text(
    hass: HomeAssistant,
    data: dict[str, Any],
    *,
    user_message: str,
    telegram_target: str | None = None,
    send_telegram: bool = True,
) -> bool:
    """Execute/cancel the single pending suggestion on short follow-up replies."""
    pending = get_pending_ai_vehicle_suggestion_state(hass)
    if not pending:
        return False
    if _is_pending_suggestion_expired(pending):
        _LOGGER.info("POM AI pending suggestion expired before reply. message=%s", user_message)
        pending.clear()
        return False

    target = str(telegram_target or pending.get("target") or data.get(CONF_AI_TELEGRAM_TARGET) or data.get(CONF_TELEGRAM_TARGET) or "").strip()

    async def _send(msg: str) -> None:
        if send_telegram and target:
            await hass.services.async_call(
                "telegram_bot",
                "send_message",
                {"target": target, "parse_mode": "plain_text", "message": msg},
                blocking=True,
            )

    if is_ai_vehicle_control_cancel_text(user_message):
        label = str((pending.get("action") or {}).get("label") or "öneri")
        pending.clear()
        user_address = get_ai_user_address(data)
        prefix = f"{user_address}, " if user_address else ""
        await _send(f"Tamam {prefix}{label} için bir şey yapmıyorum.")
        return True

    if not is_ai_vehicle_suggestion_followup_text(user_message, pending):
        # Open new command/info messages must not consume old suggestion.
        return False

    action = copy.deepcopy(pending.get("action") or {})
    if not action:
        pending.clear()
        return False

    pending.clear()
    _LOGGER.info(
        "POM AI pending suggestion accepted by text. message=%s label=%s risky=%s",
        user_message,
        action.get("label"),
        bool(action.get("risky", True)),
    )
    # If the suggested action is risky, convert it to a real confirmation box.
    if bool(action.get("risky", True)):
        if send_telegram and target:
            await async_send_ai_vehicle_control_confirmation(
                hass,
                target=target,
                action=action,
                user_message=str(pending.get("source_message") or user_message),
            )
        else:
            await _send(f"{action.get('label') or 'Bu işlem'} için onay gerekiyor.")
        return True

    try:
        result = await async_execute_ai_vehicle_control_action(hass, action)
    except Exception as err:
        _LOGGER.exception("POM AI pending suggestion execution failed")
        result = f"Önerilen araç kontrolü çalıştırılamadı: {err}"
    await _send(result)
    return True



def build_contextual_vehicle_suggestion_without_llm(
    hass: HomeAssistant,
    data: dict[str, Any],
    *,
    user_message: str,
    assistant_answer: str = "",
) -> dict[str, Any] | None:
    """Deterministically bind obvious comfort statements to one safe pending suggestion.

    This is intentionally small and safe. It is not a general command parser.
    It only prevents POM from saying "istersen yaparım" without storing a real
    follow-up action. The LLM can still handle richer cases, but these common
    Turkish comfort phrases must always create a pending suggestion when the
    matching capability is configured.
    """
    n = normalize_text_for_match(user_message)
    if not n:
        return None
    if is_vehicle_status_question(user_message) or looks_like_vehicle_control_request(user_message):
        return None

    hot_terms = [
        "cok sicak", "sicak oldu", "baya sicak", "cok isindi", "bunaldim",
        "sıcaktan", "sicaktan", "terledim", "serinlemek", "serinletsen", "sogutmak lazim",
        "too hot", "very hot", "so hot", "car is too hot", "the car is too hot",
        "inside is too hot", "its too hot", "it's too hot", "hot in the car",
        "car feels hot", "the cabin is too hot", "cabin is too hot", "i am hot",
    ]
    cold_terms = [
        "cok soguk", "soguk oldu", "baya soguk", "usudum", "üşüdüm",
        "donuyorum", "isitmak lazim", "sicak olsun",
        "too cold", "very cold", "so cold", "car is too cold", "the car is too cold",
        "inside is too cold", "its too cold", "it's too cold", "cold in the car",
        "the cabin is too cold", "cabin is too cold", "i am cold",
    ]

    if _has_any_phrase(n, hot_terms):
        return build_ai_vehicle_control_action_from_llm_intent(hass, data, {
            "type": "vehicle_control",
            "summary_tr": "Klimayı açıp serinlet",
            "actions": [{"capability": "climate", "action": "turn_on"}],
        })

    if _has_any_phrase(n, cold_terms):
        return build_ai_vehicle_control_action_from_llm_intent(hass, data, {
            "type": "vehicle_control",
            "summary_tr": "Klimayı açıp ısıt",
            "actions": [{"capability": "climate", "action": "turn_on"}],
        })

    # If POM's actual answer explicitly offered climate control, bind it too.
    ans = normalize_text_for_match(assistant_answer)
    if ans and (
        _has_any_phrase(ans, [
            "klimayi ac", "klima ac", "serinleteyim", "sogutayim", "isitayim", "sicakligi yukselt",
            "turn on climate", "turn the climate on", "turn it on", "lower the temperature",
            "cool the car", "cool it down", "warm the car", "heat the car",
        ])
        or ("klima" in ans and any(word in ans for word in ["onay", "istersen", "acmak", "acabilirim", "acalim", "haber ver"]))
        or ("climate" in ans and any(word in ans for word in ["turn on", "if you want", "i can", "want me to", "let me know"]))
    ):
        return build_ai_vehicle_control_action_from_llm_intent(hass, data, {
            "type": "vehicle_control",
            "summary_tr": "Klimayı aç",
            "actions": [{"capability": "climate", "action": "turn_on"}],
        })
    return None


async def async_build_contextual_vehicle_suggestion_with_llm(
    hass: HomeAssistant,
    data: dict[str, Any],
    *,
    user_message: str,
    assistant_answer: str,
) -> dict[str, Any] | None:
    """Create a single-slot pending suggestion from an indirect user statement.

    This is not used for direct commands. It only stores a suggestion when the
    user's message plus POM's answer clearly implies a possible vehicle control,
    e.g. "çok sıcak oldu" -> climate turn_on. The output is still capability-only
    and verified against the whitelist before being stored.
    """
    api_key = str(data.get(CONF_OPENAI_API_KEY, "")).strip()
    if not api_key:
        return None
    controls = _configured_control_capabilities_for_llm(hass, data)
    if not controls:
        return None
    model = str(data.get(CONF_OPENAI_MODEL, DEFAULT_OPENAI_MODEL)).strip() or DEFAULT_OPENAI_MODEL
    capability_json = json.dumps(controls, ensure_ascii=False)
    system_prompt = (
        "You are Tesla AI's contextual pending-suggestion detector. "
        "Return ONLY valid JSON. No prose. No markdown. "
        "You decide whether the user's message and POM's answer create ONE clear follow-up vehicle-control suggestion. "
        "Use only AVAILABLE_CAPABILITIES. Never invent capability, entity_id, or service. "
        "If there is no clear suggested control, return {\"type\":\"no_suggestion\"}. "
        "If there is a clear suggestion, return {\"type\":\"vehicle_control\",\"summary_tr\":\"...\",\"actions\":[...]}. "
        "Only create suggestions for natural follow-up offers like cooling/heating the car, turning climate on/off, or similar. "
        "Do not create a suggestion for status/info questions. Do not create a suggestion if the user gave a different explicit command. "
        "For 'çok sıcak oldu', suggest capability climate action turn_on with summary_tr meaning cool/serinlet, never heat. "
        "For 'çok soğuk oldu', suggest capability climate action turn_on with summary_tr meaning warm/ısıt, only if the assistant answer offers warming; otherwise no_suggestion. "
        "For 'istersen klimayı açayım/serinleteyim/ısıtayım', create a climate suggestion. "
    )
    context_text = (
        "AVAILABLE_CAPABILITIES:\n" + capability_json +
        "\n\nUSER_MESSAGE:\n" + str(user_message or "") +
        "\n\nPOM_ANSWER:\n" + str(assistant_answer or "")
    )
    try:
        text = await async_call_openai_responses_api(
            hass,
            api_key=api_key,
            model=model,
            system_prompt=system_prompt,
            user_message="Analyze the USER_MESSAGE and POM_ANSWER and return JSON only.",
            context_text=context_text,
            max_output_tokens=500,
        )
    except Exception as err:
        _LOGGER.debug("POM AI contextual suggestion router failed: %s", err)
        return None
    intent = _json_from_ai_router_text(text)
    if not intent:
        return None
    typ = str(intent.get("type") or intent.get("intent") or "").strip().lower()
    if typ in {"no_suggestion", "not_control", "none", "chat", "status", "information"}:
        return None
    return build_ai_vehicle_control_action_from_llm_intent(hass, data, intent)


async def async_store_contextual_vehicle_suggestion_if_any(
    hass: HomeAssistant,
    data: dict[str, Any],
    *,
    user_message: str,
    assistant_answer: str,
    telegram_target: str | None = None,
) -> None:
    """Replace the single pending suggestion slot if a new suggestion exists."""
    action = build_contextual_vehicle_suggestion_without_llm(
        hass,
        data,
        user_message=user_message,
        assistant_answer=assistant_answer,
    )
    if action is None:
        action = await async_build_contextual_vehicle_suggestion_with_llm(
            hass,
            data,
            user_message=user_message,
            assistant_answer=assistant_answer,
        )
    pending = get_pending_ai_vehicle_suggestion_state(hass)
    if action and not action.get("error"):
        pending.clear()
        pending.update({
            "created_ts": datetime.now().timestamp(),
            "target": str(telegram_target or data.get(CONF_AI_TELEGRAM_TARGET) or data.get(CONF_TELEGRAM_TARGET) or "").strip(),
            "source_message": user_message,
            "assistant_answer": assistant_answer,
            "action": copy.deepcopy(action),
        })
        _LOGGER.info(
            "POM AI pending suggestion saved. message=%s label=%s risky=%s",
            user_message,
            action.get("label"),
            bool(action.get("risky", True)),
        )
    else:
        # A normal chat answer or unrelated question clears older suggestions so
        # a later "evet" cannot accidentally execute stale context.
        pending.clear()


async def async_maybe_start_ai_vehicle_control(
    hass: HomeAssistant,
    data: dict[str, Any],
    *,
    user_message: str,
    telegram_target: str | None = None,
    send_telegram: bool = True,
) -> bool:
    """Detect a vehicle control request and either execute or start confirmation."""
    action = None
    # v2.0: let the LLM do natural-language intent routing first. The LLM only
    # outputs capabilities; entity/service execution is still whitelist-verified
    # by code. If it fails or returns not_control, deterministic fallback remains.
    if not is_vehicle_status_question(user_message):
        action = await async_build_ai_vehicle_control_action_with_llm(hass, data, user_message)
    if action is None:
        action = build_ai_vehicle_control_action(hass, data, user_message)
    if action is None:
        return False

    # A clear new vehicle-control command supersedes any old contextual suggestion.
    clear_pending_ai_vehicle_suggestion(hass)

    target = str(telegram_target or data.get(CONF_AI_TELEGRAM_TARGET) or data.get(CONF_TELEGRAM_TARGET) or "").strip()

    async def _send_or_notify(msg: str, notification_id: str) -> None:
        if send_telegram and target:
            await hass.services.async_call(
                "telegram_bot",
                "send_message",
                {"target": target, "parse_mode": "plain_text", "message": msg},
                blocking=True,
            )
        else:
            await async_create_persistent_notification(
                hass,
                title="POM AI Vehicle Controls",
                message=msg,
                notification_id=notification_id,
            )

    if action.get("error"):
        msg = str(action.get("message") or "Araç kontrol komutu algılandı ama gerekli entity bulunamadı.")
        msg = await async_translate_runtime_message_if_needed(
            hass,
            data,
            user_message=user_message,
            message_text=msg,
        )
        await _send_or_notify(msg, "pom_tesla_report_ai_control_missing_entity")
        return True

    # If no action in the manifest requires confirmation, execute immediately.
    if not bool(action.get("risky", True)):
        try:
            result = await async_execute_ai_vehicle_control_action(hass, action)
        except Exception as err:
            _LOGGER.exception("POM AI vehicle control immediate execution failed")
            result = f"Araç kontrol komutu çalıştırılamadı: {err}"
        result = await async_translate_runtime_message_if_needed(
            hass,
            data,
            user_message=user_message,
            message_text=result,
        )
        await _send_or_notify(result, "pom_tesla_report_ai_control_executed")
        return True

    if send_telegram and target:
        await async_send_ai_vehicle_control_confirmation(
            hass,
            target=target,
            action=action,
            user_message=user_message,
        )
    else:
        await async_create_persistent_notification(
            hass,
            title="POM AI Vehicle Controls",
            message=await async_translate_runtime_message_if_needed(
                hass,
                data,
                user_message=user_message,
                message_text=(
                f"Araç kontrol komutu algılandı: {action.get('label')}\n"
                "Onay için Telegram target gerekli. AI Telegram target ayarını kontrol et."
                ),
            ),
            notification_id="pom_tesla_report_ai_control_needs_telegram",
        )
    return True


async def async_handle_ai_vehicle_control_text_confirmation(
    hass: HomeAssistant,
    data: dict[str, Any],
    *,
    user_message: str,
    telegram_target: str | None = None,
    send_telegram: bool = True,
) -> bool:
    """Handle plain-text confirmation/cancel replies before normal AI chat."""
    pending_controls = get_pending_ai_vehicle_control_state(hass)
    if not pending_controls:
        return False

    target_norm = normalize_telegram_id(telegram_target or data.get(CONF_AI_TELEGRAM_TARGET) or data.get(CONF_TELEGRAM_TARGET) or "")
    # Pick newest pending item, preferably for same chat target.
    candidates = []
    for token, item in pending_controls.items():
        item_target = normalize_telegram_id(item.get("chat_id") or item.get("target") or "")
        if target_norm and item_target and target_norm != item_target:
            continue
        candidates.append((safe_float(item.get("created_ts"), 0.0), token, item))
    if not candidates:
        return False
    candidates.sort(reverse=True)
    _created, token, pending_item = candidates[0]

    target = str(telegram_target or pending_item.get("target") or data.get(CONF_AI_TELEGRAM_TARGET) or data.get(CONF_TELEGRAM_TARGET) or "").strip()
    source_message = str(pending_item.get("user_message") or user_message or "")

    async def _send_result(msg: str) -> None:
        msg = await async_translate_runtime_message_if_needed(
            hass,
            data,
            user_message=source_message,
            message_text=msg,
        )
        if send_telegram and target:
            await hass.services.async_call(
                "telegram_bot",
                "send_message",
                {"target": target, "parse_mode": "plain_text", "message": msg},
                blocking=True,
            )

    if is_ai_vehicle_control_cancel_text(user_message):
        action_label = str((pending_item.get("action") or {}).get("label") or "Araç kontrolü")
        pending_controls.pop(token, None)
        _LOGGER.info("POM AI pending vehicle control canceled by text. message=%s token=%s label=%s", user_message, token, action_label)
        await _send_result(f"{action_label} komutu iptal edildi.")
        return True

    if is_contextual_ai_vehicle_control_confirmation_text(user_message, pending_item):
        try:
            result = await async_execute_ai_vehicle_control_action(hass, pending_item.get("action") or {})
            pending_controls.pop(token, None)
            _LOGGER.info("POM AI pending vehicle control confirmed by text. message=%s token=%s", user_message, token)
            await _send_result(result)
        except Exception as err:
            _LOGGER.exception("POM AI vehicle control text confirmation failed")
            await _send_result(f"Araç kontrol komutu çalıştırılamadı: {err}")
        return True

    return False

async def async_build_vehicle_location_answer(hass: HomeAssistant, data: dict[str, Any], message: str = "") -> str:
    """Build deterministic vehicle location answer with address and Google Maps link."""
    lang = detect_message_language(message)
    base_lang = lang if lang in {"tr", "en"} else "tr"
    tracker_entity = get_vehicle_role_entity(data, VEHICLE_ROLE_LOCATION_TRACKER) or str(
        data.get(CONF_TRIP_MAP_TRACKER_ENTITY, DEFAULT_TRIP_MAP_TRACKER_ENTITY) or ""
    ).strip()

    point = get_tracker_lat_lon(hass, tracker_entity)
    if point is None:
        if base_lang == "en":
            answer = (
                "📍 Vehicle location\n\n"
                "I can't read the vehicle coordinates right now. "
                "Please check whether a Location tracker / map entity is selected in Vehicle Manager."
            )
        else:
            answer = (
            "📍 Araç konumu\n\n"
            "Araç konum koordinatını şu anda okuyamıyorum. "
            "Vehicle Manager içinde Location tracker / map entity seçili mi kontrol et."
        )
        return await async_translate_ready_answer_if_needed(hass, data, user_message=message, ready_answer=answer)

    await async_update_reverse_geocode_cache(hass, data)

    lat, lon = point
    cached_address = get_cached_reverse_geocode_address(hass)
    parts = get_cached_reverse_geocode_parts(hass)
    maps_link = get_google_maps_link(lat, lon)

    lines = ["📍 Vehicle location", ""] if base_lang == "en" else ["📍 Araç konumu", ""]

    if cached_address:
        lines.extend(["Address:", cached_address] if base_lang == "en" else ["Adres:", cached_address])
        house_number = str(parts.get("house_number") or "").strip() if parts else ""
        if not house_number:
            lines.append("House/building number is not available in OpenStreetMap data." if base_lang == "en" else "Kapı/bina no: OpenStreetMap verisinde görünmüyor.")
    else:
        lines.append("Address: A full address is not available right now." if base_lang == "en" else "Adres: Açık adres şu anda alınamadı.")

    lines.extend([
        "",
        "Open in Maps:" if base_lang == "en" else "Haritada aç:",
        maps_link,
    ])

    answer = "\n".join(lines)
    return await async_translate_ready_answer_if_needed(hass, data, user_message=message, ready_answer=answer)


async def async_send_vehicle_location_map_if_available(
    hass: HomeAssistant,
    data: dict[str, Any],
    *,
    target: str,
    message: str = "",
    caption: str = "",
) -> bool:
    """Render and send a light/day-mode vehicle location map if coordinates are available."""
    target = str(target or "").strip()
    if not target:
        return False

    tracker_entity = get_vehicle_role_entity(data, VEHICLE_ROLE_LOCATION_TRACKER) or str(
        data.get(CONF_TRIP_MAP_TRACKER_ENTITY, DEFAULT_TRIP_MAP_TRACKER_ENTITY) or ""
    ).strip()
    point = get_tracker_lat_lon(hass, tracker_entity)
    if point is None:
        return False

    try:
        await async_update_reverse_geocode_cache(hass, data)
        lat, lon = point
        cached_address = get_cached_reverse_geocode_address(hass)
        lang = detect_message_language(message)
        base_lang = lang if lang in {"tr", "en"} else "tr"
        map_data = {
            "lat": lat,
            "lon": lon,
            "address": cached_address,
            "title": "Vehicle Location" if base_lang == "en" else "Araç Konumu",
            "subtitle": f"{lat:.5f}, {lon:.5f}",
        }
        map_path = await hass.async_add_executor_job(
            render_vehicle_location_map_png,
            map_data,
            DEFAULT_VEHICLE_LOCATION_MAP_OUTPUT_PATH,
        )
        await async_telegram_send_photo(
            hass,
            data,
            target=target,
            file_path=map_path,
            caption=str(caption or "").strip(),
        )
        return True
    except Exception:
        _LOGGER.exception("POM vehicle location map could not be sent")
        return False



def get_report_visibility_options(data: dict[str, Any]) -> dict[str, bool]:
    """Return report section visibility options using renderer field names."""
    return {
        "show_distance": get_bool_option(data, CONF_SHOW_DISTANCE, DEFAULT_SHOW_DISTANCE),
        "show_duration": get_bool_option(data, CONF_SHOW_DURATION, DEFAULT_SHOW_DURATION),
        "show_traffic": get_bool_option(data, CONF_SHOW_TRAFFIC, DEFAULT_SHOW_TRAFFIC),
        "show_average_speed": get_bool_option(
            data,
            CONF_SHOW_AVERAGE_SPEED,
            DEFAULT_SHOW_AVERAGE_SPEED,
        ),
        "show_energy": get_bool_option(data, CONF_SHOW_ENERGY, DEFAULT_SHOW_ENERGY),
        "show_consumption": get_bool_option(
            data,
            CONF_SHOW_CONSUMPTION,
            DEFAULT_SHOW_CONSUMPTION,
        ),
        "show_battery": get_bool_option(data, CONF_SHOW_BATTERY, DEFAULT_SHOW_BATTERY),
        "show_cost": get_bool_option(data, CONF_SHOW_COST, DEFAULT_SHOW_COST),
        "show_climate": get_bool_option(data, CONF_SHOW_CLIMATE, DEFAULT_SHOW_CLIMATE),
        "show_elevation": get_bool_option(data, CONF_SHOW_ELEVATION, DEFAULT_SHOW_ELEVATION),
    }


def format_duration_from_minutes(duration_minutes: float) -> str:
    """Format duration in a compact Turkish style for PNG/report output."""
    duration_minutes = max(safe_float(duration_minutes, 0.0), 0.0)

    if duration_minutes < 1:
        return "<1 dk"

    total_minutes = int(round(duration_minutes))

    if total_minutes < 1:
        return "<1 dk"

    hours = total_minutes // 60
    minutes = total_minutes % 60

    if hours > 0:
        if minutes <= 0:
            return f"{hours} sa"
        return f"{hours} sa {minutes} dk"

    return f"{total_minutes} dk"


def parse_duration_text_minutes(value: Any) -> float:
    """Parse compact TR/EN duration text into minutes for test/fallback reports."""
    text = str(value or "").strip().lower().replace(",", ".")
    if not text:
        return 0.0

    # Plain numeric text is treated as minutes.
    plain = re.sub(r"[^0-9.]", "", text)
    if plain and plain == text:
        return safe_float(plain, 0.0)

    total = 0.0
    hour_patterns = [
        r"([0-9]+(?:\.[0-9]+)?)\s*(?:sa|saat|hour|hours|hr|h)\b",
    ]
    minute_patterns = [
        r"([0-9]+(?:\.[0-9]+)?)\s*(?:dk|dakika|minute|minutes|min|m)\b",
    ]
    for pattern in hour_patterns:
        for match in re.finditer(pattern, text):
            total += safe_float(match.group(1), 0.0) * 60.0
    for pattern in minute_patterns:
        for match in re.finditer(pattern, text):
            total += safe_float(match.group(1), 0.0)

    if total > 0:
        return total

    # Fallback: first number in text is minutes.
    nums = re.findall(r"[0-9]+(?:\.[0-9]+)?", text)
    return safe_float(nums[0], 0.0) if nums else 0.0


def overall_speed_from_distance_and_duration_text(distance_km: Any, duration_text: Any) -> float:
    distance = max(0.0, safe_float(distance_km, 0.0))
    minutes = max(0.0, parse_duration_text_minutes(duration_text))
    if distance <= 0 or minutes <= 0:
        return 0.0
    return distance / (minutes / 60.0)


def get_charging_report_state(hass: HomeAssistant) -> dict[str, Any]:
    """Return mutable charging session report state."""
    return hass.data.setdefault(DOMAIN, {}).setdefault("charging_report_state", {})


def _entity_exists(hass: HomeAssistant, entity_id: str) -> bool:
    """Return true when an entity exists in the current HA state machine."""
    return bool(entity_id and hass.states.get(entity_id) is not None)


def get_charging_report_entities(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, str]:
    """Return entity ids used by the charging PNG report.

    The first version intentionally uses a very small data surface, matching Berkan's
    request: charge_energy_added, battery_range, battery_range_estimate and charger_power.
    Vehicle Manager roles are respected first; known POM entity ids are used as fallback.
    """
    added = get_configured_entity(data, CONF_CHARGE_ENERGY_ADDED_ENTITY, VEHICLE_ROLE_CHARGE_ENERGY_ADDED, usage_key="use_report") or "sensor.pom_charge_energy_added"
    battery_range = get_vehicle_role_entity(data, VEHICLE_ROLE_BATTERY_RANGE, usage_key="use_report") or "sensor.pom_battery_range"
    charger_power = get_vehicle_role_entity(data, VEHICLE_ROLE_CHARGER_POWER, usage_key="use_report") or "sensor.pom_charger_power"
    charging_state = get_configured_entity(data, CONF_CHARGING_ENTITY, VEHICLE_ROLE_CHARGING_STATE, usage_key="use_report") or ""

    # There is no dedicated range-estimate role yet, so prefer the well-known POM entity id.
    estimate = "sensor.pom_battery_range_estimate"
    if not _entity_exists(hass, estimate):
        for item in get_vehicle_entity_entries(data):
            entity_id = str(item.get("entity_id") or "").strip()
            haystack = normalize_text_for_match(f"{entity_id} {item.get('label') or ''}")
            if "range estimate" in haystack or "battery range estimate" in haystack or "tahmini menzil" in haystack:
                estimate = entity_id
                break

    return {
        "charge_energy_added": str(added or ""),
        "battery_range": str(battery_range or ""),
        "battery_range_estimate": str(estimate or ""),
        "charger_power": str(charger_power or ""),
        "charging_state": str(charging_state or ""),
    }


def is_charge_report_session_active(hass: HomeAssistant, data: dict[str, Any]) -> bool:
    """Return true when the car is actually receiving charging power."""
    entities = get_charging_report_entities(hass, data)
    power_entity = entities.get("charger_power")
    if power_entity and _entity_exists(hass, power_entity):
        return get_float_state(hass, power_entity, 0.0) > 0.2

    charging_entity = entities.get("charging_state")
    return is_charging_state(get_state_text(hass, charging_entity, ""))


def get_charging_tariff_prices(hass: HomeAssistant, data: dict[str, Any]) -> tuple[float, float, float]:
    """Return configured charging tariff prices with fallback to live entry config."""
    fallback = get_first_entry_config(hass) or {}

    def _pick(key: str, default: float) -> float:
        value = safe_float((data or {}).get(key), 0.0)
        if value > 0:
            return value
        value = safe_float(fallback.get(key), 0.0)
        if value > 0:
            return value
        return float(default)

    return (
        _pick(CONF_SUPERCHARGER_PRICE, DEFAULT_SUPERCHARGER_PRICE),
        _pick(CONF_ZES_PRICE, DEFAULT_ZES_PRICE),
        _pick(CONF_ASTOR_PRICE, DEFAULT_ASTOR_PRICE),
    )


def get_charge_cost_ledger_path(hass: HomeAssistant) -> Path:
    """Return the persistent JSON path for charging cost ledger records."""
    return Path(hass.config.path(CHARGE_COST_LEDGER_FILENAME))


def load_charge_cost_ledger(hass: HomeAssistant) -> dict[str, Any]:
    """Load charging cost ledger payload from disk."""
    path = get_charge_cost_ledger_path(hass)
    default_payload = {"records": [], "last_monthly_report_key": ""}
    try:
        if not path.exists():
            return copy.deepcopy(default_payload)
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return copy.deepcopy(default_payload)
        records = payload.get("records")
        if not isinstance(records, list):
            records = []
        monthly_key = str(payload.get("last_monthly_report_key") or "").strip()
        return {
            "records": records,
            "last_monthly_report_key": monthly_key,
        }
    except Exception:
        _LOGGER.exception("Could not load Tesla AI charging cost ledger")
        return copy.deepcopy(default_payload)


def save_charge_cost_ledger(hass: HomeAssistant, payload: dict[str, Any]) -> None:
    """Persist charging cost ledger payload to disk."""
    path = get_charge_cost_ledger_path(hass)
    normalized = {
        "records": list(payload.get("records") or []),
        "last_monthly_report_key": str(payload.get("last_monthly_report_key") or "").strip(),
    }
    path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")


def get_app_language(data: dict[str, Any] | None) -> str:
    """Return the single global application language.

    CONF_APP_LANGUAGE is the source of truth. CONF_REPORT_LANGUAGE is used only as a
    backward-compatible fallback for older configs created before alpha59.
    """
    raw = str(
        (data or {}).get(CONF_APP_LANGUAGE)
        or (data or {}).get(CONF_REPORT_LANGUAGE)
        or DEFAULT_APP_LANGUAGE
    ).strip().lower()
    return APP_LANGUAGE_EN if raw.startswith("en") else APP_LANGUAGE_TR


def get_report_language(data: dict[str, Any] | None) -> str:
    """Return normalized report language for generated visuals."""
    return get_app_language(data)


def get_report_currency(data: dict[str, Any] | None) -> str:
    """Return selected report currency label, independent from report language."""
    value = str((data or {}).get(CONF_REPORT_CURRENCY, DEFAULT_REPORT_CURRENCY) or DEFAULT_REPORT_CURRENCY).strip().upper()
    allowed = {str(item).upper() for item in REPORT_CURRENCY_OPTIONS}
    return value if value in allowed else DEFAULT_REPORT_CURRENCY


def get_telegram_report_language(data: dict[str, Any] | None, user_message: str = "") -> str:
    """Return language for deterministic Telegram report replies.

    alpha59: slash commands and deterministic report outputs follow the global
    application language, not the language of the command text. This prevents
    /trip and /charge from falling back to Turkish when the app is set to English.
    """
    return get_app_language(data)


def normalize_telegram_report_command_word(value: Any) -> str:
    """Normalize the slash command word stored in settings.

    Users enter only the part after slash. Telegram commands cannot contain
    spaces, so we keep the first token, strip leading slash and bot suffix, and
    normalize Turkish characters through the existing matcher.
    """
    text = str(value or "").strip()
    if not text:
        return ""
    first = text.split()[0].strip()
    if first.startswith("/"):
        first = first[1:]
    if "@" in first:
        first = first.split("@", 1)[0]
    first = first.strip().strip("/")
    return normalize_text_for_match(first).replace(" ", "")


def get_telegram_report_commands(data: dict[str, Any] | None) -> dict[str, str]:
    """Return user-configurable slash commands for existing report actions."""
    raw = (data or {}).get(TELEGRAM_REPORT_COMMANDS_OPTION_KEY)
    if not isinstance(raw, dict):
        raw = {}
    output: dict[str, str] = {}
    for key, default_value in DEFAULT_TELEGRAM_REPORT_COMMANDS.items():
        normalized = normalize_telegram_report_command_word(raw.get(key, default_value))
        if not normalized:
            normalized = normalize_telegram_report_command_word(default_value)
        output[key] = normalized
    return output


def get_live_entry_config_for_telegram(hass: HomeAssistant, entry: ConfigEntry, fallback: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return freshest config for Telegram command matching.

    Panel saves update hass.data immediately and config-entry options as well.
    On some HA versions/custom-panel paths, entry.options may lag for a short
    time. Therefore in-memory hass.data must have priority over the setup-time
    fallback and over entry.options for live command changes such as sarj -> berkan.
    """
    try:
        root = hass.data.setdefault(DOMAIN, {})
        in_memory = root.get(entry.entry_id)
        data = {
            **dict(entry.data or {}),
            **dict(entry.options or {}),
            **dict(fallback or {}),
            **(dict(in_memory) if isinstance(in_memory, dict) else {}),
        }
        root[entry.entry_id] = data
        return data
    except Exception:
        return dict(fallback or {})




def get_live_entry_config_for_entry_id(hass: HomeAssistant, entry_id: str, fallback: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return the freshest config for a running entry by entry_id.

    Live Trip is driven by long-lived interval callbacks. Those callbacks may
    hold a setup-time ``data`` dict. Panel saves, however, update config-entry
    options and ``hass.data`` without reloading the integration. For runtime
    settings such as the 1/5/10 km Live Trip AI interval, the live engine must
    read the newest in-memory/options value on every tick; otherwise the engine
    can overwrite the user-selected interval back to the old 10 km value.
    """
    try:
        root = hass.data.setdefault(DOMAIN, {})
        in_memory = root.get(entry_id)
        entry = None
        for candidate in hass.config_entries.async_entries(DOMAIN):
            if candidate.entry_id == entry_id:
                entry = candidate
                break
        data: dict[str, Any] = {}
        if entry is not None:
            data.update(dict(entry.data or {}))
            data.update(dict(entry.options or {}))
        data.update(dict(fallback or {}))
        if isinstance(in_memory, dict):
            data.update(dict(in_memory))
        if data:
            root[entry_id] = data
        return data
    except Exception:
        return dict(fallback or {})


def ensure_live_trip_ai_runtime_interval(
    hass: HomeAssistant,
    entry_id: str,
    data: dict[str, Any] | None = None,
    *,
    realign_on_change: bool = True,
) -> float:
    """Apply the latest configured Live Trip AI interval to the runtime state.

    Safe to call from the sensor property, the live-trip engine and panel
    endpoints. It keeps the runtime attributes feeding the dashboard card in
    sync with the latest selected 1/5/10 km option.
    """
    latest_data = get_live_entry_config_for_entry_id(hass, entry_id, data)
    size_km = live_trip_ai_segment_size_from_data(latest_data)
    state = get_live_trip_state(hass, entry_id)
    old_size = safe_float(state.get("live_ai_segment_size_km"), size_km)
    current_km = max(0.0, safe_float(state.get("trip_km"), 0.0))
    changed = abs(old_size - size_km) > 0.001
    state["live_ai_segment_size_km"] = size_km
    if changed and realign_on_change:
        # When the user changes from 10 km to 1/5 km during an already running
        # trip, past distance should not be emitted as artificial completed AI
        # comments. The next real target becomes the next selected boundary above
        # the current trip distance, e.g. 3.54 km + 1 km interval => target 4 km.
        completed_index = int(current_km // size_km) if size_km > 0 else 0
        state["live_ai_segment_last_completed_index"] = max(0, completed_index)
        state["live_ai_last_requested_index"] = min(
            int(safe_float(state.get("live_ai_last_requested_index"), 0.0)),
            max(0, completed_index),
        )
        state["live_ai_segment_baseline"] = _live_trip_ai_snapshot_from_state(state)
        if str(state.get("live_ai_comment_source") or "").strip() != "panel_test":
            state["live_ai_comment_status"] = "waiting"
            state["live_ai_comment_error"] = ""
            state["live_comment"] = ""
    state["live_ai_segment_next_target_km"] = _live_trip_ai_reconciled_next_target_km(state, size_km)
    return size_km

def is_known_slash_report_command(data: dict[str, Any] | None, message: str) -> bool:
    """Return True for configured or legacy report slash commands."""
    return match_telegram_report_command(data, message) is not None


def parse_telegram_report_command_token(message: str, default_lang: str = "tr") -> tuple[str, str]:
    """Return normalized slash command token and optional language suffix."""
    text = str(message or "").strip()
    lang = "en" if str(default_lang or "").lower().startswith("en") else "tr"
    if not text.startswith("/"):
        return "", lang
    token = text.split()[0].strip()
    if "@" in token:
        token = token.split("@", 1)[0]
    token = token.lstrip("/")
    lowered = token.lower().replace("ı", "i")
    for suffix in ("_tr", "|tr"):
        if lowered.endswith(suffix):
            lang = "tr"
            lowered = lowered[: -len(suffix)]
            break
    for suffix in ("_en", "|en"):
        if lowered.endswith(suffix):
            lang = "en"
            lowered = lowered[: -len(suffix)]
            break
    return normalize_telegram_report_command_word(lowered), lang


def match_telegram_report_command(data: dict[str, Any] | None, message: str) -> tuple[str, str] | None:
    """Match configured or legacy slash command to a report action."""
    command, lang = parse_telegram_report_command_token(message, get_telegram_report_language(data, message))
    if not command:
        return None

    configured = get_telegram_report_commands(data)
    for action, configured_word in configured.items():
        if command == configured_word:
            return action, lang

    for action, aliases in LEGACY_TELEGRAM_REPORT_COMMAND_ALIASES.items():
        for alias in aliases:
            if command == normalize_telegram_report_command_word(alias):
                return action, lang

    return None


def _log_telegram_command_match(
    data: dict[str, Any] | None,
    message: str,
    matched: tuple[str, str] | None,
) -> None:
    """Debug log command map without exposing secrets."""
    try:
        command, lang = parse_telegram_report_command_token(message, get_telegram_report_language(data, message))
        _LOGGER.info(
            "POM Telegram command received. raw=%s normalized=%s matched=%s commands=%s",
            str(message or "")[:80],
            command,
            matched[0] if matched else "-",
            get_telegram_report_commands(data),
        )
    except Exception:
        _LOGGER.debug("POM Telegram command debug log failed", exc_info=True)


def build_telegram_report_commands_help(data: dict[str, Any] | None, *, lang: str = "tr") -> str:
    """Build compact help text for currently configured report commands."""
    commands = get_telegram_report_commands(data)
    if str(lang or "").lower().startswith("en"):
        labels = {
            "charge_report": "Monthly charge report",
            "trip_summary": "Monthly trip summary",
            "trip_all": "All trip pages",
            "trip_single": "Single-page trip report",
            "trip_last": "Last trip report",
            "trip_today": "Today's trip summary",
            "trip_week": "This week's trip summary",
        }
        title = "Available POM report commands:"
    else:
        labels = {
            "charge_report": "Bu ayın şarj raporu",
            "trip_summary": "Bu ayın sürüş özeti",
            "trip_all": "Bu ayki tüm sürüş sayfaları",
            "trip_single": "Tek sayfa sürüş raporu",
            "trip_last": "Son sürüş raporu",
            "trip_today": "Bugünkü sürüş özeti",
            "trip_week": "Bu haftanın sürüş özeti",
        }
        title = "Kullanılabilir POM rapor komutları:"
    lines = [title]
    for key in ("charge_report", "trip_summary", "trip_all", "trip_single", "trip_last", "trip_today", "trip_week"):
        word = commands.get(key) or DEFAULT_TELEGRAM_REPORT_COMMANDS[key]
        lines.append(f"/{word} — {labels[key]}")
    return "\n".join(lines)


def should_translate_telegram_report_reply(data: dict[str, Any] | None, user_message: str = "") -> bool:
    """Return true when deterministic report text should be translated.

    The app currently supports Turkish and English deterministic report templates,
    so no extra translation pass is required for the global language setting.
    """
    return False


def get_trip_monthly_ledger_path(hass: HomeAssistant) -> Path:
    """Return the persistent JSON path for monthly trip summary records."""
    return Path(hass.config.path(TRIP_MONTHLY_LEDGER_FILENAME))


def load_trip_monthly_ledger(hass: HomeAssistant) -> dict[str, Any]:
    """Load stored trip summary payload from disk."""
    path = get_trip_monthly_ledger_path(hass)
    default_payload = {"records": []}
    try:
        if not path.exists():
            return copy.deepcopy(default_payload)
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return copy.deepcopy(default_payload)
        records = payload.get("records")
        if not isinstance(records, list):
            records = []
        return {"records": records}
    except Exception:
        _LOGGER.exception("Could not load Tesla AI trip monthly ledger")
        return copy.deepcopy(default_payload)


def save_trip_monthly_ledger(hass: HomeAssistant, payload: dict[str, Any]) -> None:
    """Persist trip monthly ledger payload to disk."""
    path = get_trip_monthly_ledger_path(hass)
    normalized = {"records": list(payload.get("records") or [])}
    path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")


def is_manual_tracking_trip_record(record: dict[str, Any] | None) -> bool:
    """Return True for manual tracking records stored in the shared trip ledger.

    Manual tracking entries are intentionally stored in the same historical
    ledger so the Manual Tracking tab can display them. They must not be mixed
    into automatic Trip Records, monthly/weekly trip totals, or Telegram trip
    summaries because automatic tracking already records the real drive.
    """
    if not isinstance(record, dict):
        return False
    source = str(record.get("source") or "").strip().lower().replace("-", "_").replace(" ", "_")
    return "manual_tracking" in source or source in {"manual", "manualtracking"}


def build_trip_record_id(
    *,
    month_key: str,
    report_date: str,
    trip_km: float,
    used_kwh: float,
    start_address: str,
    end_address: str,
) -> str:
    """Build a stable-enough de-duplication key for one trip record."""
    return "|".join(
        [
            month_key,
            str(report_date or "").strip(),
            f"{trip_km:.3f}",
            f"{used_kwh:.3f}",
            normalize_text_for_match(start_address),
            normalize_text_for_match(end_address),
        ]
    )


def build_trip_record_from_report_data(
    report_data: dict[str, Any] | None,
    *,
    source: str,
) -> dict[str, Any] | None:
    """Convert final trip report data into a monthly trip ledger record."""
    report_data = report_data or {}
    trip_km = safe_float(report_data.get("trip_km"), 0.0)
    used_kwh = safe_float(report_data.get("used_kwh"), 0.0)
    if trip_km <= 0 or used_kwh < 0:
        return None

    now = datetime.now()
    month_key = now.strftime("%Y-%m")
    created_at = now.isoformat(timespec="seconds")
    display_at = str(report_data.get("report_date") or now.strftime("%d.%m.%Y %H:%M")).strip()
    start_address = str(report_data.get("start_address") or "").strip()
    end_address = str(report_data.get("end_address") or "").strip()
    duration_text = str(report_data.get("duration_text") or "").strip()
    duration_minutes = safe_float(report_data.get("duration_minutes"), 0.0)
    consumption = safe_float(report_data.get("consumption_kwh_100km"), 0.0)
    total_cost = safe_float(report_data.get("supercharger_trip_cost"), 0.0)

    record_id = build_trip_record_id(
        month_key=month_key,
        report_date=display_at,
        trip_km=trip_km,
        used_kwh=used_kwh,
        start_address=start_address,
        end_address=end_address,
    )

    return {
        "id": record_id,
        "month_key": month_key,
        "created_at": created_at,
        "display_at": display_at,
        "start_address": start_address,
        "end_address": end_address,
        "trip_km": round(trip_km, 3),
        "duration_text": duration_text,
        "duration_minutes": round(duration_minutes, 2),
        "report_duration_seconds": round(safe_float(report_data.get("report_duration_seconds", safe_float(report_data.get("duration_minutes"), 0.0) * 60.0), 0.0), 0),
        "report_duration_text": str(report_data.get("report_duration_text") or duration_text).strip(),
        "total_elapsed_seconds": round(safe_float(report_data.get("total_elapsed_seconds"), 0.0), 0),
        "total_elapsed_text": str(report_data.get("total_elapsed_text") or "").strip(),
        "final_park_wait_seconds": round(safe_float(report_data.get("final_park_wait_seconds"), 0.0), 0),
        "final_park_wait_text": str(report_data.get("final_park_wait_text") or "").strip(),
        "used_kwh": round(used_kwh, 3),
        "consumption_kwh_100km": round(consumption, 3),
        "total_cost": round(total_cost, 2),
        "currency_label": str(report_data.get("currency_label") or "").strip(),
        "source": str(source or "").strip() or "trip",
        "traffic_seconds": round(safe_float(report_data.get("traffic_seconds"), 0.0), 0),
        "stopped_in_drive_seconds": round(safe_float(report_data.get("stopped_in_drive_seconds"), 0.0), 0),
        "stopped_in_drive_text": str(report_data.get("stopped_in_drive_text") or "").strip(),
        "slow_traffic_seconds": round(safe_float(report_data.get("slow_traffic_seconds"), 0.0), 0),
        "slow_traffic_text": str(report_data.get("slow_traffic_text") or "").strip(),
        "normal_drive_seconds": round(safe_float(report_data.get("normal_drive_seconds"), 0.0), 0),
        "normal_drive_text": str(report_data.get("normal_drive_text") or "").strip(),
        "parked_pause_seconds": round(safe_float(report_data.get("parked_pause_seconds"), 0.0), 0),
        "parked_pause_text": str(report_data.get("parked_pause_text") or "").strip(),
        "last_traffic_class": str(report_data.get("last_traffic_class") or "").strip(),
        "traffic_model": str(report_data.get("traffic_model") or "").strip(),
        "traffic_model_label": str(report_data.get("traffic_model_label") or "").strip(),
        "traffic_reference_speed_kmh": round(safe_float(report_data.get("traffic_reference_speed_kmh"), 0.0), 1),
        "traffic_reference_trip_type": str(report_data.get("traffic_reference_trip_type") or "").strip(),
        "traffic_reference_trip_type_label": str(report_data.get("traffic_reference_trip_type_label") or "").strip(),
        "traffic_free_flow_seconds": round(safe_float(report_data.get("traffic_free_flow_seconds"), 0.0), 0),
        "traffic_free_flow_text": str(report_data.get("traffic_free_flow_text") or "").strip(),
        "traffic_delay_seconds": round(safe_float(report_data.get("traffic_delay_seconds"), 0.0), 0),
        "traffic_delay_text": str(report_data.get("traffic_delay_text") or "").strip(),
        "traffic_congestion_percent": round(safe_float(report_data.get("traffic_congestion_percent"), 0.0), 1),
        "traffic_impact_label": str(report_data.get("traffic_impact_label") or "").strip(),
        "effective_traffic_delay_seconds": round(safe_float(report_data.get("effective_traffic_delay_seconds"), safe_float(report_data.get("traffic_delay_seconds"), 0.0)), 0),
        "effective_traffic_delay_text": str(report_data.get("effective_traffic_delay_text") or "").strip(),
        "traffic_effective_impact_label": str(report_data.get("traffic_effective_impact_label") or report_data.get("effective_traffic_impact") or "").strip(),
        "effective_traffic_impact": str(report_data.get("effective_traffic_impact") or report_data.get("traffic_effective_impact_label") or "").strip(),
        "slowdown_reason": str(report_data.get("slowdown_reason") or "").strip(),
        "slowdown_reason_label": str(report_data.get("slowdown_reason_label") or "").strip(),
        "traffic_confidence": str(report_data.get("traffic_confidence") or "").strip(),
        "traffic_analysis_limited": bool(report_data.get("traffic_analysis_limited")),
        "traffic_analysis_reliability": str(report_data.get("traffic_analysis_reliability") or "").strip(),
        "traffic_interpretation_note": str(report_data.get("traffic_interpretation_note") or "").strip(),
        "raw_low_speed_percent": round(safe_float(report_data.get("raw_low_speed_percent"), safe_float(report_data.get("traffic_ratio_moving_percent"), 0.0)), 1),
        "raw_low_speed_seconds": round(safe_float(report_data.get("raw_low_speed_seconds"), safe_float(report_data.get("traffic_seconds"), 0.0)), 0),
        "raw_low_speed_text": str(report_data.get("raw_low_speed_text") or report_data.get("traffic_text") or "").strip(),
        "traffic_ratio_moving_percent": round(safe_float(report_data.get("traffic_ratio_moving_percent"), 0.0), 1),
        "average_speed": round(safe_float(report_data.get("average_speed"), 0.0), 1),
        "average_moving_speed": round(safe_float(report_data.get("average_moving_speed", report_data.get("average_speed")), 0.0), 1),
        "average_overall_speed": round(safe_float(report_data.get("average_overall_speed"), 0.0), 1),
        "moving_seconds": round(safe_float(report_data.get("moving_seconds"), 0.0), 0),
        "moving_minutes": round(safe_float(report_data.get("moving_minutes"), 0.0), 2),
        "moving_duration_text": str(report_data.get("moving_duration_text") or "").strip(),
        "non_moving_seconds": round(safe_float(report_data.get("non_moving_seconds"), 0.0), 0),
        "speed_sample_count": int(safe_float(report_data.get("speed_sample_count"), 0.0)),
        "moving_speed_sample_count": int(safe_float(report_data.get("moving_speed_sample_count"), 0.0)),
        "max_speed": round(safe_float(report_data.get("max_speed"), 0.0), 1),
        "moving_speed_threshold": round(safe_float(report_data.get("moving_speed_threshold"), MOVING_SPEED_THRESHOLD_KMH), 1),
        "speed_sampler_interval_seconds": int(safe_float(report_data.get("speed_sampler_interval_seconds"), SPEED_SAMPLER_INTERVAL_SECONDS)),
        "driving_score": int(safe_float(report_data.get("driving_score"), 0.0)),
        "driving_score_label": str(report_data.get("driving_score_label") or "").strip(),
        "driving_score_text": str(report_data.get("driving_score_text") or "").strip(),
        "score_efficiency": round(safe_float(report_data.get("score_efficiency"), 0.0), 0),
        "score_traffic_flow": round(safe_float(report_data.get("score_traffic_flow"), 0.0), 0),
        "score_speed_profile": round(safe_float(report_data.get("score_speed_profile"), 0.0), 0),
        "score_elevation_effect": round(safe_float(report_data.get("score_elevation_effect"), 0.0), 0),
        "score_weather_effect": round(safe_float(report_data.get("score_weather_effect"), 0.0), 0),
        "score_model": str(report_data.get("score_model") or "").strip(),
        "map_points": report_data.get("map_points") if isinstance(report_data.get("map_points"), list) else [],
        "map_point_count": len(report_data.get("map_points") or []) if isinstance(report_data.get("map_points"), list) else 0,
        "start_latitude": report_data.get("start_latitude"),
        "start_longitude": report_data.get("start_longitude"),
        "end_latitude": report_data.get("end_latitude"),
        "end_longitude": report_data.get("end_longitude"),
        "map_path": str(report_data.get("map_path") or report_data.get("embedded_map_path") or "").strip(),
        "elevation_gain": round(safe_float(report_data.get("elevation_gain"), 0.0), 0),
        "elevation_loss": round(safe_float(report_data.get("elevation_loss"), 0.0), 0),
        "elevation_sample_count": int(safe_float(report_data.get("elevation_sample_count"), 0.0)),
        "elevation_provider": str(report_data.get("elevation_provider") or "").strip(),
        "elevation_source": str(report_data.get("elevation_source") or "").strip(),
    }


async def async_record_trip_summary_entry(
    hass: HomeAssistant,
    report_data: dict[str, Any] | None,
    *,
    source: str,
) -> dict[str, Any] | None:
    """Append a trip record for monthly summary visuals."""
    record = build_trip_record_from_report_data(report_data, source=source)
    if not record:
        return None

    payload = load_trip_monthly_ledger(hass)
    records = [item for item in list(payload.get("records") or []) if isinstance(item, dict)]
    record_id = str(record.get("id") or "").strip()
    records = [item for item in records if str(item.get("id") or "").strip() != record_id]
    records.insert(0, record)
    payload["records"] = records[:500]
    save_trip_monthly_ledger(hass, payload)
    return record



def _format_trip_ai_minutes(seconds: float) -> str:
    """Format seconds for compact AI trip context."""
    seconds = max(0.0, safe_float(seconds, 0.0))
    minutes = int(round(seconds / 60.0))
    if minutes < 1 and seconds > 0:
        return "<1 dk"
    if minutes < 60:
        return f"{minutes} dk"
    hours = minutes // 60
    rest = minutes % 60
    return f"{hours} sa {rest} dk" if rest else f"{hours} sa"


def _trip_ai_efficiency_label(consumption: float) -> str:
    """Return a human efficiency label for kWh/100 km."""
    value = safe_float(consumption, 0.0)
    if value <= 0:
        return "belirsiz"
    if value < 14:
        return "çok verimli"
    if value < 18:
        return "normal"
    if value < 22:
        return "yüksek tüketim"
    return "çok yüksek tüketim"


def _is_short_trip_traffic_limited(
    *,
    distance_km: float,
    duration_seconds: float,
    traffic_delay_seconds: float,
    speed_bucket_traffic_seconds: float,
) -> bool:
    """Return True when traffic interpretation should be muted for tiny trips."""
    distance = max(0.0, safe_float(distance_km, 0.0))
    duration = max(0.0, safe_float(duration_seconds, 0.0))
    delay = max(0.0, safe_float(traffic_delay_seconds, 0.0))
    bucket = max(0.0, safe_float(speed_bucket_traffic_seconds, 0.0))
    if distance <= 0 and duration <= 0:
        return False
    is_short = distance < SHORT_TRIP_TRAFFIC_DISTANCE_KM or duration < SHORT_TRIP_TRAFFIC_DURATION_SECONDS
    is_tiny_traffic = delay < SHORT_TRIP_TINY_TRAFFIC_DELAY_SECONDS or bucket < SHORT_TRIP_TINY_SPEED_BUCKET_SECONDS
    return bool(is_short and is_tiny_traffic)


def _short_trip_traffic_note() -> str:
    return (
        "Kısa mesafeli sürüşte düşük hızlı bölüm oranı yanıltıcı olabilir; "
        "kalkış, sokak içi dönüş, kapı/otopark veya park manevrası trafik gibi yorumlanmamalı."
    )


def slowdown_reason_label(reason: Any, *, lang: str = "tr") -> str:
    """Return user/AI friendly label for the inferred low-speed reason."""
    key = str(reason or "unknown").strip().lower()
    en = str(lang or "").lower().startswith("en")
    labels_en = {
        "traffic": "traffic",
        "signal_stop": "traffic light / junction stop-go",
        "parking_search": "parking search / destination area",
        "short_trip": "short-trip limited analysis",
        "low_speed_city": "urban low-speed flow",
        "unknown": "unknown",
    }
    labels_tr = {
        "traffic": "trafik",
        "signal_stop": "ışık / kavşak dur-kalk",
        "parking_search": "park arama / varış çevresi",
        "short_trip": "kısa mesafe sınırlı analiz",
        "low_speed_city": "şehir içi düşük hız",
        "unknown": "belirsiz",
    }
    return (labels_en if en else labels_tr).get(key, key or ("unknown" if en else "belirsiz"))


def _classify_slowdown_reason(
    *,
    distance_km: float,
    moving_seconds: float,
    delay_seconds: float,
    stopped_seconds: float,
    slow_seconds: float,
    normal_seconds: float,
    moving_avg_speed: float,
    final_park_wait_seconds: float = 0.0,
) -> dict[str, Any]:
    """Classify low-speed time without automatically calling it traffic.

    This is intentionally conservative. With Tesla/HA entities we know speed,
    shift, distance and sometimes navigation delay, but not the official traffic
    state of each road segment. Therefore the headline should only say traffic
    when delay is meaningful and the pattern is not a short destination-area or
    signal/junction case.
    """
    distance = max(0.0, safe_float(distance_km, 0.0))
    moving = max(0.0, safe_float(moving_seconds, 0.0))
    delay = max(0.0, safe_float(delay_seconds, 0.0))
    stopped = max(0.0, safe_float(stopped_seconds, 0.0))
    slow = max(0.0, safe_float(slow_seconds, 0.0))
    normal = max(0.0, safe_float(normal_seconds, 0.0))
    avg = max(0.0, safe_float(moving_avg_speed, 0.0))
    final_wait = max(0.0, safe_float(final_park_wait_seconds, 0.0))
    low_speed = stopped + slow
    low_ratio = (low_speed / moving * 100.0) if moving > 0 else 0.0
    stopped_ratio = (stopped / moving * 100.0) if moving > 0 else 0.0

    short_trip = distance > 0 and distance < CAUTIOUS_TRAFFIC_DISTANCE_KM
    very_short = distance > 0 and distance < 2.0
    tiny_or_short_duration = moving > 0 and moving < SHORT_TRIP_TRAFFIC_DURATION_SECONDS

    reason = "traffic"
    confidence = "normal"
    reliability = "normal"
    note = ""
    effective_delay = delay

    # Destination/parking search usually appears as a short trip with a high
    # low-speed ratio, low average speed, or a final parked wait after P.
    parking_like = bool(
        short_trip
        and low_speed >= 90
        and (low_ratio >= 30 or avg <= 18 or final_wait >= 60)
        and delay < CAUTIOUS_TRAFFIC_STRONG_DELAY_SECONDS
    )
    signal_like = bool(
        short_trip
        and stopped >= 45
        and stopped_ratio >= 8
        and delay < CAUTIOUS_TRAFFIC_DELAY_SECONDS
        and not parking_like
    )
    limited_short = bool(
        (short_trip or tiny_or_short_duration)
        and delay < CAUTIOUS_TRAFFIC_DELAY_SECONDS
        and low_speed >= 45
    )

    if parking_like:
        reason = "parking_search"
        confidence = "normal"
        reliability = "normal"
        effective_delay = min(delay, 60.0)
        note = "Düşük hızın ana nedeni trafik değil; varış çevresinde park arama/sokak içi dolaşma olabilir."
    elif signal_like:
        reason = "signal_stop"
        confidence = "normal"
        reliability = "normal"
        effective_delay = min(delay, 90.0)
        note = "Dur-kalk kısa mesafede ışık veya kavşak davranışına benziyor; tek başına yoğun trafik sayılmadı."
    elif limited_short:
        reason = "short_trip"
        confidence = "low"
        reliability = "düşük"
        effective_delay = min(delay, 60.0)
        note = _short_trip_traffic_note()
    elif delay < CAUTIOUS_TRAFFIC_MIN_REAL_DELAY_SECONDS and low_speed > 0:
        reason = "low_speed_city"
        confidence = "low"
        reliability = "düşük"
        effective_delay = min(delay, 60.0)
        note = "Düşük hız ölçüldü ancak anlamlı trafik gecikmesi yok; bu alan ham düşük hız olarak yorumlandı."
    else:
        reason = "traffic"
        confidence = "high" if delay >= CAUTIOUS_TRAFFIC_STRONG_DELAY_SECONDS else "normal"
        reliability = "yüksek" if delay >= CAUTIOUS_TRAFFIC_STRONG_DELAY_SECONDS else "normal"

    if reason != "traffic":
        impact = "düşük" if effective_delay < 120 else "sınırlı"
    else:
        impact = traffic_impact_label_from_percent((effective_delay / max(60.0, moving - effective_delay) * 100.0) if moving > effective_delay else 0.0)

    return {
        "slowdown_reason": reason,
        "slowdown_reason_label": slowdown_reason_label(reason),
        "traffic_confidence": confidence,
        "traffic_analysis_reliability": reliability,
        "traffic_interpretation_note": note,
        "effective_traffic_delay_seconds": round(effective_delay, 0),
        "effective_traffic_delay_minutes": round(effective_delay / 60.0, 2),
        "effective_traffic_delay_text": format_duration_from_minutes(effective_delay / 60.0),
        "effective_traffic_impact": impact,
        "traffic_effective_impact_label": impact,
        "traffic_analysis_limited": reason != "traffic",
        "raw_low_speed_percent": round(low_ratio, 1),
        "raw_low_speed_seconds": round(low_speed, 0),
        "raw_low_speed_text": format_duration_from_minutes(low_speed / 60.0),
    }


def _trip_ai_type_label(
    distance_km: float,
    moving_avg_speed: float,
    traffic_ratio: float,
    duration_minutes: float,
    *,
    traffic_limited: bool = False,
) -> str:
    """Classify the trip using simple deterministic rules."""
    distance = safe_float(distance_km, 0.0)
    speed = safe_float(moving_avg_speed, 0.0)
    traffic = safe_float(traffic_ratio, 0.0)
    duration = safe_float(duration_minutes, 0.0)
    if traffic_limited:
        return "kısa mesafe / yavaşlama yorumu sınırlı"
    if distance > 30 and speed >= 70:
        return "uzun yol / akıcı sürüş"
    if distance < 5 and duration < 20:
        return "kısa mesafe"
    if traffic >= 35:
        return "şehir içi / trafikli sürüş"
    if speed < 22 and distance >= 5:
        return "şehir içi / yavaş akış"
    if traffic <= 10 and speed >= 50:
        return "akıcı sürüş"
    if 10 < traffic < 35 and distance >= 10:
        return "karma sürüş"
    return "şehir içi / normal sürüş"


def _trip_ai_data_quality(report_data: dict[str, Any]) -> tuple[str, list[str]]:
    """Estimate data quality and missing context for AI story."""
    missing: list[str] = []
    if safe_float(report_data.get("trip_km"), 0.0) <= 0:
        missing.append("mesafe")
    if safe_float(report_data.get("duration_minutes"), 0.0) <= 0 and safe_float(report_data.get("report_duration_seconds"), 0.0) <= 0:
        missing.append("süre")
    if not str(report_data.get("start_address") or "").strip():
        missing.append("başlangıç adresi")
    if not str(report_data.get("end_address") or "").strip():
        missing.append("bitiş adresi")
    if safe_float(report_data.get("consumption_kwh_100km"), 0.0) <= 0:
        missing.append("tüketim")
    if safe_float(report_data.get("speed_sample_count"), 0.0) <= 0:
        missing.append("hız örnekleri")
    if not report_data.get("map_points"):
        missing.append("harita noktaları")
    if len(missing) <= 1:
        return "yüksek", missing
    if len(missing) <= 3:
        return "orta", missing
    return "düşük", missing


def _trip_ai_float_or_none(value: Any) -> float | None:
    """Return rounded float for AI context, or None when not meaningful."""
    number = safe_float(value, 0.0)
    if number == 0.0 and str(value or "").strip() in {"", "0", "0.0", "0.00", "—", "-"}:
        return None
    return round(number, 2)



OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_WEATHER_TIMEOUT_SECONDS = 4.0


def open_meteo_weather_code_label(code: Any) -> str:
    """Map WMO/Open-Meteo weather code to compact Turkish label."""
    try:
        value = int(float(code))
    except Exception:
        return ""
    labels = {
        0: "açık",
        1: "çoğunlukla açık",
        2: "parçalı bulutlu",
        3: "kapalı",
        45: "sisli",
        48: "kırağılı sis",
        51: "hafif çisenti",
        53: "çisenti",
        55: "yoğun çisenti",
        56: "dondurucu çisenti",
        57: "yoğun dondurucu çisenti",
        61: "hafif yağmur",
        63: "yağmur",
        65: "şiddetli yağmur",
        66: "dondurucu yağmur",
        67: "şiddetli dondurucu yağmur",
        71: "hafif kar",
        73: "kar",
        75: "yoğun kar",
        77: "kar taneleri",
        80: "hafif sağanak",
        81: "sağanak",
        82: "şiddetli sağanak",
        85: "hafif kar sağanağı",
        86: "şiddetli kar sağanağı",
        95: "gök gürültülü",
        96: "dolu ihtimalli gök gürültülü",
        99: "şiddetli dolu ihtimalli gök gürültülü",
    }
    return labels.get(value, f"weather_code {value}")


def _weather_float_or_none(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return round(float(value), 2)
    except Exception:
        return None


async def async_fetch_open_meteo_trip_weather(
    hass: HomeAssistant,
    latitude: Any,
    longitude: Any,
) -> dict[str, Any] | None:
    """Fetch current weather directly from Open-Meteo for AI trip context.

    This intentionally does not depend on any Home Assistant weather integration.
    The request is best-effort and short-timeout; if it fails, the trip report
    and AI story continue without weather data.
    """
    lat = safe_float(latitude, 0.0)
    lon = safe_float(longitude, 0.0)
    if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0) or (lat == 0.0 and lon == 0.0):
        return None

    params = {
        "latitude": f"{lat:.6f}",
        "longitude": f"{lon:.6f}",
        "current": ",".join(
            [
                "temperature_2m",
                "relative_humidity_2m",
                "apparent_temperature",
                "precipitation",
                "weather_code",
                "cloud_cover",
                "wind_speed_10m",
                "wind_direction_10m",
            ]
        ),
        "timezone": "auto",
        "wind_speed_unit": "kmh",
    }

    session = async_get_clientsession(hass)
    try:
        async with asyncio.timeout(OPEN_METEO_WEATHER_TIMEOUT_SECONDS):
            async with session.get(OPEN_METEO_FORECAST_URL, params=params) as resp:
                if resp.status >= 400:
                    _LOGGER.debug("Open-Meteo weather fetch failed with HTTP %s", resp.status)
                    return None
                payload = await resp.json(content_type=None)
    except (asyncio.TimeoutError, ClientError, json.JSONDecodeError) as err:
        _LOGGER.debug("Open-Meteo weather fetch skipped: %s", err)
        return None
    except Exception as err:
        _LOGGER.debug("Open-Meteo weather unexpected error: %s", err)
        return None

    current = payload.get("current") if isinstance(payload, dict) else None
    if not isinstance(current, dict):
        return None

    weather_code = current.get("weather_code")
    temperature = _weather_float_or_none(current.get("temperature_2m"))
    apparent = _weather_float_or_none(current.get("apparent_temperature"))
    humidity = _weather_float_or_none(current.get("relative_humidity_2m"))
    precipitation = _weather_float_or_none(current.get("precipitation"))
    cloud_cover = _weather_float_or_none(current.get("cloud_cover"))
    wind_speed = _weather_float_or_none(current.get("wind_speed_10m"))
    wind_direction = _weather_float_or_none(current.get("wind_direction_10m"))
    label = open_meteo_weather_code_label(weather_code)

    summary_parts = []
    if temperature is not None:
        summary_parts.append(f"{temperature:g}°C")
    if label:
        summary_parts.append(label)
    if precipitation is not None and precipitation > 0:
        summary_parts.append(f"yağış {precipitation:g} mm")
    if wind_speed is not None:
        summary_parts.append(f"rüzgar {wind_speed:g} km/sa")
    summary = " · ".join(summary_parts)

    return {
        "weather_provider": "Open-Meteo",
        "weather_source": "direct_open_meteo_api",
        "weather_latitude": round(lat, 6),
        "weather_longitude": round(lon, 6),
        "weather_time": str(current.get("time") or ""),
        "weather_summary": summary,
        "weather_condition": label,
        "weather_code": int(float(weather_code)) if weather_code is not None else None,
        "temperature_c": temperature,
        "apparent_temperature_c": apparent,
        "relative_humidity_percent": humidity,
        "precipitation_mm": precipitation,
        "cloud_cover_percent": cloud_cover,
        "wind_speed_kmh": wind_speed,
        "wind_direction_deg": wind_direction,
    }


async def async_enrich_trip_report_with_weather(
    hass: HomeAssistant,
    report_data: dict[str, Any],
) -> dict[str, Any]:
    """Return report_data copy with direct Open-Meteo weather context if possible."""
    data = dict(report_data or {})

    lat = data.get("end_latitude") or data.get("start_latitude")
    lon = data.get("end_longitude") or data.get("start_longitude")

    # Fallback to last map point when explicit end/start coordinates are absent.
    points = data.get("map_points")
    if (not lat or not lon) and isinstance(points, list) and points:
        last = points[-1]
        if isinstance(last, dict):
            lat = last.get("latitude") or last.get("lat") or lat
            lon = last.get("longitude") or last.get("lon") or last.get("lng") or lon
        elif isinstance(last, (list, tuple)) and len(last) >= 2:
            lat = last[0] or lat
            lon = last[1] or lon

    weather = await async_fetch_open_meteo_trip_weather(hass, lat, lon)
    if weather:
        data["weather"] = weather
        data.update(weather)
    return data


def build_trip_ai_context_payload(report_data: dict[str, Any], *, source: str) -> dict[str, Any]:
    """Build a compact deterministic context for post-trip AI story."""
    report_data = report_data or {}
    distance_km = safe_float(report_data.get("trip_km"), 0.0)
    duration_seconds = safe_float(report_data.get("report_duration_seconds"), 0.0)
    if duration_seconds <= 0:
        duration_seconds = safe_float(report_data.get("duration_minutes"), 0.0) * 60.0
    duration_minutes = duration_seconds / 60.0 if duration_seconds > 0 else safe_float(report_data.get("duration_minutes"), 0.0)
    moving_seconds = safe_float(report_data.get("moving_seconds"), 0.0)
    traffic_seconds = safe_float(report_data.get("traffic_seconds"), 0.0)
    stopped_seconds = safe_float(report_data.get("stopped_in_drive_seconds"), 0.0)
    slow_seconds = safe_float(report_data.get("slow_traffic_seconds"), 0.0)
    normal_seconds = safe_float(report_data.get("normal_drive_seconds"), 0.0)
    climate_seconds = safe_float(report_data.get("climate_seconds"), 0.0)
    final_park_wait_seconds = safe_float(report_data.get("final_park_wait_seconds"), 0.0)
    parked_pause_seconds = safe_float(report_data.get("parked_pause_seconds"), 0.0)

    base_for_ratio = duration_seconds or (traffic_seconds + normal_seconds) or (duration_minutes * 60.0)
    traffic_ratio = (traffic_seconds / base_for_ratio * 100.0) if base_for_ratio > 0 else 0.0
    stop_go_ratio = (stopped_seconds / base_for_ratio * 100.0) if base_for_ratio > 0 else 0.0

    moving_avg_speed = safe_float(report_data.get("average_moving_speed", report_data.get("average_speed")), 0.0)
    overall_avg_speed = safe_float(report_data.get("average_overall_speed"), 0.0)
    if overall_avg_speed <= 0 and duration_seconds > 0 and distance_km > 0:
        overall_avg_speed = distance_km / (duration_seconds / 3600.0)
    max_speed = safe_float(report_data.get("max_speed"), 0.0)
    consumption = safe_float(report_data.get("consumption_kwh_100km"), 0.0)
    used_kwh = safe_float(report_data.get("used_kwh"), 0.0)
    cost = safe_float(report_data.get("supercharger_trip_cost", report_data.get("total_cost")), 0.0)

    traffic_delay_seconds = safe_float(report_data.get("traffic_delay_seconds"), 0.0)
    traffic_congestion_percent = safe_float(report_data.get("traffic_congestion_percent"), 0.0)
    traffic_reference_speed = safe_float(report_data.get("traffic_reference_speed_kmh"), 0.0)
    traffic_p85_speed = safe_float(report_data.get("traffic_p85_speed_kmh"), 0.0)
    traffic_free_flow_seconds = safe_float(report_data.get("traffic_free_flow_seconds"), 0.0)
    traffic_ratio_moving = safe_float(report_data.get("traffic_ratio_moving_percent"), 0.0)
    slowdown_reason = str(report_data.get("slowdown_reason") or "").strip()
    slowdown_reason_label_value = str(report_data.get("slowdown_reason_label") or "").strip()
    effective_traffic_delay_seconds = safe_float(report_data.get("effective_traffic_delay_seconds"), traffic_delay_seconds)
    effective_traffic_impact = str(report_data.get("effective_traffic_impact") or report_data.get("traffic_effective_impact_label") or "").strip()
    raw_low_speed_percent = safe_float(report_data.get("raw_low_speed_percent"), traffic_ratio)
    raw_low_speed_seconds = safe_float(report_data.get("raw_low_speed_seconds"), traffic_seconds)

    elevation_min = safe_float(report_data.get("min_elevation"), 0.0)
    elevation_max = safe_float(report_data.get("max_elevation"), 0.0)
    elevation_range = safe_float(report_data.get("elevation_range"), 0.0)
    elevation_gain = safe_float(report_data.get("elevation_gain"), 0.0)
    elevation_loss = safe_float(report_data.get("elevation_loss"), 0.0)
    elevation_sample_count = int(safe_float(report_data.get("elevation_sample_count"), 0.0))

    start_address = str(report_data.get("start_address") or "").strip()
    end_address = str(report_data.get("end_address") or "").strip()
    route_summary = ""
    if start_address and end_address:
        route_summary = f"{start_address} konumundan {end_address} konumuna"
    elif end_address:
        route_summary = f"Bitiş: {end_address}"
    elif start_address:
        route_summary = f"Başlangıç: {start_address}"

    score_fields = build_trip_score_fields(report_data)
    data_quality, missing = _trip_ai_data_quality(report_data)
    if not slowdown_reason:
        inferred = _classify_slowdown_reason(
            distance_km=distance_km,
            moving_seconds=moving_seconds or duration_seconds,
            delay_seconds=traffic_delay_seconds,
            stopped_seconds=stopped_seconds,
            slow_seconds=slow_seconds,
            normal_seconds=normal_seconds,
            moving_avg_speed=moving_avg_speed,
            final_park_wait_seconds=final_park_wait_seconds,
        )
        slowdown_reason = str(inferred.get("slowdown_reason") or "unknown")
        slowdown_reason_label_value = str(inferred.get("slowdown_reason_label") or slowdown_reason_label(slowdown_reason))
        effective_traffic_delay_seconds = safe_float(inferred.get("effective_traffic_delay_seconds"), traffic_delay_seconds)
        effective_traffic_impact = str(inferred.get("effective_traffic_impact") or "").strip()
    traffic_limited = bool(report_data.get("traffic_analysis_limited")) or slowdown_reason in {"parking_search", "signal_stop", "short_trip", "low_speed_city"} or _is_short_trip_traffic_limited(
        distance_km=distance_km,
        duration_seconds=duration_seconds,
        traffic_delay_seconds=traffic_delay_seconds,
        speed_bucket_traffic_seconds=traffic_seconds,
    )
    traffic_reliability = str(report_data.get("traffic_analysis_reliability") or ("düşük" if traffic_limited else "normal")).strip()
    traffic_note = str(report_data.get("traffic_interpretation_note") or (_short_trip_traffic_note() if traffic_limited else "")).strip()
    traffic_effective_impact_label = str(report_data.get("traffic_effective_impact_label") or effective_traffic_impact or ("düşük" if traffic_limited else report_data.get("traffic_impact_label") or "")).strip()
    traffic_for_trip_type = traffic_congestion_percent if slowdown_reason == "traffic" and effective_traffic_delay_seconds >= CAUTIOUS_TRAFFIC_MIN_REAL_DELAY_SECONDS else 0.0
    trip_type = _trip_ai_type_label(distance_km, moving_avg_speed, traffic_for_trip_type, duration_minutes, traffic_limited=traffic_limited)
    efficiency_label = _trip_ai_efficiency_label(consumption)

    return {
        "source": str(source or report_data.get("source") or "trip").strip(),
        "report_date": str(report_data.get("report_date") or "").strip(),
        "start_address": start_address,
        "end_address": end_address,
        "route_summary": route_summary,
        "distance_km": round(distance_km, 2),
        "duration_minutes": round(duration_minutes, 1),
        "duration_text": str(report_data.get("report_duration_text") or report_data.get("duration_text") or _format_trip_ai_minutes(duration_seconds)).strip(),
        "total_elapsed_minutes": round(safe_float(report_data.get("total_elapsed_seconds"), 0.0) / 60.0, 1),
        "total_elapsed_text": str(report_data.get("total_elapsed_text") or "").strip(),
        "final_park_wait_minutes": round(final_park_wait_seconds / 60.0, 1),
        "final_park_wait_text": str(report_data.get("final_park_wait_text") or _format_trip_ai_minutes(final_park_wait_seconds)).strip(),
        # Raw low-speed buckets. These are NOT traffic percentage by themselves.
        "raw_low_speed_percent": round(raw_low_speed_percent, 1),
        "raw_low_speed_minutes": round(raw_low_speed_seconds / 60.0, 1),
        "raw_low_speed_text": str(report_data.get("raw_low_speed_text") or report_data.get("traffic_text") or _format_trip_ai_minutes(raw_low_speed_seconds)).strip(),
        "stop_go_ratio_percent": round(stop_go_ratio, 1),
        "low_speed_minutes": round(traffic_seconds / 60.0, 1),
        "low_speed_text": str(report_data.get("traffic_text") or _format_trip_ai_minutes(traffic_seconds)).strip(),
        # Legacy aliases kept for compatibility; AI must not treat them as true traffic.
        "traffic_ratio_percent": round(traffic_ratio, 1),
        "traffic_minutes": round(traffic_seconds / 60.0, 1),
        "traffic_text": str(report_data.get("traffic_text") or _format_trip_ai_minutes(traffic_seconds)).strip(),

        # alpha229/alpha320: delay model + cautious interpretation.
        "traffic_model": str(report_data.get("traffic_model") or "").strip(),
        "traffic_model_label": str(report_data.get("traffic_model_label") or "").strip(),
        "traffic_delay_minutes": round(traffic_delay_seconds / 60.0, 1),
        "traffic_delay_text": str(report_data.get("traffic_delay_text") or _format_trip_ai_minutes(traffic_delay_seconds)).strip(),
        "effective_traffic_delay_minutes": round(effective_traffic_delay_seconds / 60.0, 1),
        "effective_traffic_delay_text": str(report_data.get("effective_traffic_delay_text") or _format_trip_ai_minutes(effective_traffic_delay_seconds)).strip(),
        "slowdown_reason": slowdown_reason or "unknown",
        "slowdown_reason_label": slowdown_reason_label_value or slowdown_reason_label(slowdown_reason),
        "traffic_confidence": str(report_data.get("traffic_confidence") or ("low" if traffic_limited else "normal")).strip(),
        "effective_traffic_impact": traffic_effective_impact_label,
        "traffic_congestion_percent": round(traffic_congestion_percent, 1),
        "traffic_impact_label": str(report_data.get("traffic_impact_label") or "").strip(),
        "traffic_reference_speed_kmh": round(traffic_reference_speed, 1),
        "traffic_reference_trip_type": str(report_data.get("traffic_reference_trip_type") or "").strip(),
        "traffic_reference_trip_type_label": str(report_data.get("traffic_reference_trip_type_label") or "").strip(),
        "traffic_reference_source": str(report_data.get("traffic_reference_source") or "").strip(),
        "traffic_p85_speed_kmh": round(traffic_p85_speed, 1),
        "traffic_free_flow_minutes": round(traffic_free_flow_seconds / 60.0, 1),
        "traffic_free_flow_text": str(report_data.get("traffic_free_flow_text") or _format_trip_ai_minutes(traffic_free_flow_seconds)).strip(),
        "traffic_ratio_moving_percent": round(traffic_ratio_moving, 1),
        "traffic_analysis_limited": traffic_limited,
        "traffic_analysis_reliability": traffic_reliability,
        "traffic_effective_impact_label": traffic_effective_impact_label,
        "traffic_interpretation_note": traffic_note,
        "traffic_ai_rule": (
            "raw_low_speed_percent / traffic_ratio_percent ham düşük hız oranıdır, gerçek trafik oranı değildir. "
            "Yoğun trafik demek için effective_traffic_delay, slowdown_reason, traffic_confidence ve traffic_analysis_reliability alanlarına öncelik ver. "
            "slowdown_reason parking_search, signal_stop, short_trip veya low_speed_city ise bunu trafik sıkışıklığı diye anlatma; park arama, ışık/kavşak veya kısa şehir içi akış olarak açıkla."
        ),
        "stopped_in_drive_minutes": round(stopped_seconds / 60.0, 1),
        "stopped_in_drive_text": str(report_data.get("stopped_in_drive_text") or _format_trip_ai_minutes(stopped_seconds)).strip(),
        "slow_traffic_minutes": round(slow_seconds / 60.0, 1),
        "slow_traffic_text": str(report_data.get("slow_traffic_text") or _format_trip_ai_minutes(slow_seconds)).strip(),
        "normal_drive_minutes": round(normal_seconds / 60.0, 1),
        "normal_drive_text": str(report_data.get("normal_drive_text") or _format_trip_ai_minutes(normal_seconds)).strip(),
        "parked_pause_minutes": round(parked_pause_seconds / 60.0, 1),
        "parked_pause_text": str(report_data.get("parked_pause_text") or _format_trip_ai_minutes(parked_pause_seconds)).strip(),
        "moving_minutes": round(moving_seconds / 60.0, 1),
        "moving_duration_text": str(report_data.get("moving_duration_text") or _format_trip_ai_minutes(moving_seconds)).strip(),
        "average_moving_speed_kmh": round(moving_avg_speed, 1),
        "average_overall_speed_kmh": round(overall_avg_speed, 1),
        "max_speed_kmh": round(max_speed, 1),
        "speed_sample_count": int(safe_float(report_data.get("speed_sample_count"), 0.0)),
        "moving_speed_sample_count": int(safe_float(report_data.get("moving_speed_sample_count"), 0.0)),
        "used_kwh": round(used_kwh, 2),
        "consumption_kwh_100km": round(consumption, 2),
        "efficiency_label": efficiency_label,
        "cost": round(cost, 2),
        "currency_label": str(report_data.get("currency_label") or "").strip(),
        "climate_minutes": round(climate_seconds / 60.0, 1),
        "climate_text": str(report_data.get("climate_text") or report_data.get("climate_duration_text") or _format_trip_ai_minutes(climate_seconds)).strip(),
        "elevation_start_m": report_data.get("elevation_start_m"),
        "elevation_end_m": report_data.get("elevation_end_m"),
        "elevation_delta_m": report_data.get("elevation_delta_m"),
        "elevation_min_m": round(elevation_min, 1) if elevation_min else None,
        "elevation_max_m": round(elevation_max, 1) if elevation_max else None,
        "elevation_range_m": round(elevation_range, 1) if elevation_range else None,
        "elevation_gain_m": round(elevation_gain, 1) if elevation_gain else None,
        "elevation_loss_m": round(elevation_loss, 1) if elevation_loss else None,
        "elevation_sample_count": elevation_sample_count,
        "elevation_provider": str(report_data.get("elevation_provider") or "").strip(),
        "elevation_source": str(report_data.get("elevation_source") or "").strip(),
        "elevation_grade_report": {
            "available": bool(report_data.get("elevation_grade_available")),
            "text": str(report_data.get("elevation_grade_text") or "").strip(),
            "confidence": str(report_data.get("elevation_grade_confidence") or "").strip(),
            "uphill_distance_km": _trip_ai_float_or_none(report_data.get("uphill_distance_km")),
            "downhill_distance_km": _trip_ai_float_or_none(report_data.get("downhill_distance_km")),
            "flat_distance_km": _trip_ai_float_or_none(report_data.get("flat_distance_km")),
            "uphill_ratio_percent": _trip_ai_float_or_none(report_data.get("uphill_ratio_percent")),
            "downhill_ratio_percent": _trip_ai_float_or_none(report_data.get("downhill_ratio_percent")),
            "flat_ratio_percent": _trip_ai_float_or_none(report_data.get("flat_ratio_percent")),
            "avg_uphill_grade_percent": _trip_ai_float_or_none(report_data.get("avg_uphill_grade_percent")),
            "avg_downhill_grade_percent": _trip_ai_float_or_none(report_data.get("avg_downhill_grade_percent")),
            "max_uphill_grade_percent": _trip_ai_float_or_none(report_data.get("max_uphill_grade_percent")),
            "max_downhill_grade_percent": _trip_ai_float_or_none(report_data.get("max_downhill_grade_percent")),
            # alpha253: exact climb/regen kWh values are internal estimates, not measured vehicle regen.
            # They are intentionally not exposed to the AI story prompt to avoid definitive claims.
            "energy_estimate_note": "Tırmanış/regen kWh değerleri araçtan ölçülen kesin veri değildir; AI yorumunda sayı olarak yazılmamalı, sadece nitel etki anlatılmalı.",
            "energy_impact_label": str(report_data.get("elevation_energy_impact_label") or "").strip(),
            "segment_count": int(safe_float(report_data.get("grade_segment_count"), 0.0)),
        },
        "start_latitude": _trip_ai_float_or_none(report_data.get("start_latitude")),
        "start_longitude": _trip_ai_float_or_none(report_data.get("start_longitude")),
        "end_latitude": _trip_ai_float_or_none(report_data.get("end_latitude")),
        "end_longitude": _trip_ai_float_or_none(report_data.get("end_longitude")),
        "weather": report_data.get("weather") if isinstance(report_data.get("weather"), dict) else {},
        "weather_provider": str(report_data.get("weather_provider") or "").strip(),
        "weather_summary": str(report_data.get("weather_summary") or "").strip(),
        "weather_condition": str(report_data.get("weather_condition") or "").strip(),
        "weather_temperature_c": _trip_ai_float_or_none(report_data.get("temperature_c")),
        "weather_apparent_temperature_c": _trip_ai_float_or_none(report_data.get("apparent_temperature_c")),
        "weather_humidity_percent": _trip_ai_float_or_none(report_data.get("relative_humidity_percent")),
        "weather_precipitation_mm": _trip_ai_float_or_none(report_data.get("precipitation_mm")),
        "weather_cloud_cover_percent": _trip_ai_float_or_none(report_data.get("cloud_cover_percent")),
        "weather_wind_speed_kmh": _trip_ai_float_or_none(report_data.get("wind_speed_kmh")),
        "weather_wind_direction_deg": _trip_ai_float_or_none(report_data.get("wind_direction_deg")),
        "trip_type": trip_type,
        "data_quality": data_quality,
        "missing_data": missing,
        "map_point_count": len(report_data.get("map_points") or []) if isinstance(report_data.get("map_points"), list) else int(safe_float(report_data.get("map_point_count"), 0.0)),
    }


def normalize_trip_story_detail_level(value: Any) -> str:
    """Normalize the user-selected Live Trip AI story detail level."""
    level = str(value or DEFAULT_AI_TRIP_STORY_DETAIL_LEVEL).strip().lower()
    if level not in AI_TRIP_STORY_DETAIL_OPTIONS:
        return DEFAULT_AI_TRIP_STORY_DETAIL_LEVEL
    return level


def _trip_story_detail_user_instruction(level: str) -> str:
    """Return prompt instructions for the selected story detail level."""
    level = normalize_trip_story_detail_level(level)
    if level == AI_TRIP_STORY_DETAIL_BASIC:
        return (
            "Cevap tek kısa paragraf olsun. Rota özeti, mesafe/süre, genel hız ve tüketim/verimlilikten sade dille bahset. "
            "Trafik, hava, eğim, skor bileşenleri ve teknik detaylara ancak çok belirginse tek cümleyle değin. "
            "Kesin ölçülmeyen tırmanış/regen/hava/trafik enerji etkilerini kWh sayısıyla yazma. Avantaj/dezavantajı kısa ve net söyle."
        )
    if level == AI_TRIP_STORY_DETAIL_BALANCED:
        return (
            "Cevap 2 kısa paragraf olsun. Rota özeti, trafik etkisi, ortalama hız, tüketim/verimlilik ve varsa sürüş skorunu doğal şekilde işle. "
            "Dili sade tut; artıları ve eksileri kullanıcının hemen anlayacağı şekilde anlat. Hava veya eğim verisi varsa sadece sürüşe belirgin etkisi varsa kısa değin. "
            "Kesin ölçülmeyen enerji etkilerini kWh sayısıyla yazma."
        )
    return (
        "Cevap mevcut uzunlukta kalabilir; gereksiz kısaltma yapma. Ancak dili daha sade, net ve kullanıcı dostu kur. "
        "Rota özeti, sürüş skoru, trafik gecikmesi, trafik etkisi, dur-kalk/yavaş trafik, ortalama hareket hızı, genel ortalama, "
        "verimlilik/tüketim, maksimum hız ve sürüş tipini doğal şekilde işle. Anlatımı mümkünse şu akışla düzenle: genel değerlendirme, "
        "artılar, dikkat edilmesi gerekenler, sonuç. traffic_analysis_limited true ise veya trafik gecikmesi 1 dakikanın altındaysa "
        "trafik yüzdesi yüksek görünse bile 'yoğun trafik' deme; kısa sürüş/dönüş/park manevrası olabilir diye belirt. "
        "Rakım/eğim verisi varsa iniş-çıkış, yokuş oranı ve etki seviyesini nitel olarak yorumla; tahmini tırmanış enerjisi veya regen potansiyeli için "
        "kWh sayısı verme ve bunu kesin kazanım/tüketim gibi sunma. 'İnişler tüketimi biraz dengelemiş olabilir' gibi sade, ihtiyatlı cümleler kullan. "
        "Hava durumu verisi varsa sıcaklık, yağış, rüzgar, bulutluluk ve klima/tüketim ilişkisini yorumla; kesin olmayan hava etkisini sayı vererek iddia etme. "
        "Emoji en fazla 1 tane kullan."
    )


def _trip_ai_story_language_rules(lang: str) -> dict[str, str]:
    """Return language-specific rules for post-trip AI stories."""
    en = str(lang or "").lower().startswith("en")
    if en:
        return {
            "unit_speed": "km/h",
            "headline": "Tesla AI Driving Comment",
            "user_intro": (
                "Write a premium post-drive narrative for the user using the Tesla trip data below.\n"
                "Write the entire answer in English. Do not use Turkish words, Turkish headings, or Turkish unit labels.\n"
                "Do not be overly formal; use a clear, natural, slightly premium tone.\n"
            ),
            "system_language": "The configured app/report language is English. Write the entire post-drive report in English only.",
            "measured_estimated": (
                "Separate measured data from estimated interpretation: distance, duration, energy and speed are measured/data fields; "
                "grade effect, regen potential, weather impact and traffic energy impact are estimates. Do not present estimated fields as facts."
            ),
            "energy_estimates": (
                "Do not quote estimated climb/regen/weather/traffic energy effects as exact kWh numbers. Use short, clear advantage/disadvantage language instead."
            ),
            "short_trip": "Raw low-speed/stop-go percentages are not traffic percentages. Use effective_traffic_delay, slowdown_reason, traffic_confidence and traffic_analysis_reliability first. If slowdown_reason is parking_search, signal_stop, short_trip or low_speed_city, do not call it heavy traffic.",
            "speed_unit_rule": "Use km/h for speed in English. Never write km/s.",
            "data_json": "TRIP DATA JSON",
            "detail_label": "Selected detail level",
        }
    return {
        "unit_speed": "km/sa",
        "headline": "Tesla AI Sürüş Yorumu",
        "user_intro": (
            "Aşağıdaki Tesla sürüş verilerini kullanarak kullanıcıya gönderilecek premium bir sürüş sonrası hikâye yorumu yaz.\n"
            "Dil tamamen Türkçe olsun. İngilizce başlık, İngilizce birim veya İngilizce açıklama kullanma.\n"
            "Çok resmi olma; doğal, net, hafif premium his veren bir anlatım kullan.\n"
        ),
        "system_language": "Ayarlardaki uygulama/rapor dili Türkçe. Sürüş sonrası AI raporunu tamamen Türkçe yaz.",
        "measured_estimated": (
            "Ölçülen veri ile tahmini yorumu ayır: mesafe/süre/enerji/hız gibi alanlar veridir; "
            "eğim etkisi, regen potansiyeli, hava etkisi ve trafik enerji etkisi tahmindir. Tahmini alanları kesin sonuç gibi yazma."
        ),
        "energy_estimates": (
            "Tahmini tırmanış/regen/hava/trafik enerji etkilerini kWh sayısıyla yazma. Bunun yerine kısa ve net avantaj/dezavantaj cümleleri kur."
        ),
        "short_trip": "Ham düşük hız/dur-kalk yüzdesi trafik yüzdesi değildir. Önce effective_traffic_delay, slowdown_reason, traffic_confidence ve traffic_analysis_reliability alanlarını kullan. slowdown_reason parking_search, signal_stop, short_trip veya low_speed_city ise yoğun trafik deme.",
        "speed_unit_rule": "Hız birimini km/sa yaz. km/s kesinlikle yazma.",
        "data_json": "SÜRÜŞ VERİLERİ JSON",
        "detail_label": "Seçilen yorum detayı",
    }


def _trip_ai_story_personality_instruction(data: dict[str, Any], lang: str) -> str:
    """Add the selected AI personality to post-trip narratives without weakening safety/data rules."""
    personality = str(data.get(CONF_AI_PERSONALITY, DEFAULT_AI_PERSONALITY) or DEFAULT_AI_PERSONALITY)
    if personality == AI_PERSONALITY_TURKISH_BUDDY:
        personality = AI_PERSONALITY_LAZ_BLACK_SEA
    en = str(lang or "").lower().startswith("en")
    if personality == AI_PERSONALITY_FUNNY:
        if en:
            return (
                "Personality: funny. Make the driving comment noticeably more entertaining: add light automotive/tech humor, "
                "a witty mini punchline or playful metaphor in each major paragraph when appropriate. Keep facts accurate and never joke about safety-critical issues."
            )
        return (
            "Kişilik: komik. Sürüş yorumunu belirgin şekilde daha eğlenceli yap: uygun yerlerde otomobil/teknoloji temalı hafif şaka, "
            "kıvrak benzetme veya kısa takılma kullan. Her ana paragrafta mümkünse küçük bir espri hissi olsun; ama güvenlik ve teknik verilerde ciddiyeti bozma."
        )
    if personality == AI_PERSONALITY_LAZ_BLACK_SEA:
        if en:
            return (
                "Personality: mild Black Sea / Laz flavor, but because the report language is English, do not write dialect words. "
                "Use a warm, energetic tone only."
            )
        return (
            "Kişilik: hafif Karadeniz/Laz şivesi. Çok abartmadan 'uşağum', 'haçan', 'da' gibi ifadeleri ölçülü kullan; "
            "rapor anlaşılır ve teknik olarak net kalsın."
        )
    if personality == AI_PERSONALITY_PROFESSIONAL:
        return "Personality: professional. Keep the report polished, concise and technically clear." if en else "Kişilik: profesyonel. Raporu temiz, net ve teknik açıdan düzgün tut."
    return "Personality: friendly. Keep the tone warm and natural." if en else "Kişilik: samimi. Sıcak ve doğal konuş."


def build_trip_ai_story_user_message(context: dict[str, Any], detail_level: str = DEFAULT_AI_TRIP_STORY_DETAIL_LEVEL, lang: str = APP_LANGUAGE_TR) -> str:
    """Build the user message sent to OpenAI for the post-trip narrative."""
    detail_level = normalize_trip_story_detail_level(detail_level)
    en = str(lang or "").lower().startswith("en")
    rules = _trip_ai_story_language_rules(lang)
    detail_text = _trip_story_detail_user_instruction(detail_level)
    if en:
        # The historical helper is Turkish; keep the actual task language deterministic here.
        detail_text = (
            "Follow the selected detail level. Basic means one short paragraph; Balanced means two short paragraphs; "
            "Detailed may keep the current detailed length and should cover traffic, weather, grade, efficiency and score when those data exist."
        )
    intro = (
        rules["user_intro"]
        + ("Do not invent data. If data is missing, do not write a long apology; simply limit the interpretation.\n" if en else "Verileri uydurma. Eksik veri varsa 'bu veri yok' diye uzun açıklama yapma; sadece yorumu ona göre sınırlı tut.\n")
        + ("Do not judge the driver or lecture about speed; only comment on the driving character.\n" if en else "Sürücüyü yargılama, hız konusunda öğüt verme; sadece sürüş karakterini yorumla.\n")
    )
    return (
        intro
        + f"{rules['short_trip']} {rules['speed_unit_rule']}\n"
        + f"{rules['measured_estimated']}\n"
        + f"{rules['energy_estimates']}\n"
        + f"{rules['detail_label']}: {detail_level}. {detail_text}\n\n"
        + f"{rules['data_json']}:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
    )


def build_trip_ai_story_system_prompt(data: dict[str, Any], lang: str = APP_LANGUAGE_TR) -> str:
    """Build a narrow system prompt for post-trip AI narrative."""
    ai_name = get_ai_display_name(data)
    rules = _trip_ai_story_language_rules(lang)
    en = str(lang or "").lower().startswith("en")
    if en:
        base = [
            f"You are {ai_name}, a premium but clear Tesla drive-report assistant.",
            rules["system_language"],
            "Use only the provided trip data. Do not invent facts or present estimates as measured data.",
            "Keep the report natural and understandable; explain advantages, disadvantages and result clearly.",
            "Follow the selected detail level. If detailed is selected, do not omit traffic/weather/grade/efficiency context when available.",
            "Avoid unnecessary jargon. Keep important measured numbers, but do not state estimated impacts as exact numbers.",
            "If traffic delay and free-flow comparison exist, value them more than raw low-speed percentage.",
            "Never treat raw_low_speed_percent / traffic_ratio_percent as traffic percent. If slowdown_reason is parking_search, signal_stop, short_trip or low_speed_city, describe parking search, lights/junctions or urban low-speed flow instead of heavy traffic.",
            "Use km/h as the speed unit; never write km/s.",
            "If grade/regen/climate/weather impact is not directly measured by the vehicle, do not give exact kWh gain/loss values. Use cautious language like 'may', 'likely', or 'a small amount'.",
            "Comment on weather only if weather context is provided.",
            "Do not preach about driving safety; treat maximum speed as a data point only.",
            build_ai_user_address_instruction(data, lang),
            _trip_ai_story_personality_instruction(data, lang),
        ]
    else:
        base = [
            f"Sen {ai_name} adında, Tesla sürüş raporlarını yorumlayan premium ama sade dilli bir araç asistanısın.",
            rules["system_language"],
            "Sadece verilen sürüş verilerine dayan. Uydurma, tahmin ettiğini veri gibi sunma.",
            "Rapor dili doğal olsun; karmaşık teknik hesapları kullanıcıya kolay anlaşılır artı/eksi/sonuç diliyle aktar.",
            "Seçilen detay seviyesine uy. Kısa istenirse uzatma, detaylı istenirse trafik/hava/eğim/verimlilik bağlamını atlama.",
            "Gereksiz teknik jargon kullanma. Önemli ölçülen sayıları koru, fakat tahmini etkileri kesin sayı gibi verme.",
            "Trafik gecikmesi ve serbest akış karşılaştırması varsa bunu ham düşük hız oranından daha değerli kabul et.",
            "raw_low_speed_percent / traffic_ratio_percent trafik yüzdesi değildir. slowdown_reason parking_search, signal_stop, short_trip veya low_speed_city ise yoğun trafik deme; park arama, ışık/kavşak veya şehir içi düşük hız olarak anlat.",
            "Hız birimi olarak km/sa kullan; km/s kesinlikle yazma.",
            "Eğim/regen/iklim/hava etkisi doğrudan araçtan ölçülmediyse kWh veya kesin kazanç/kayıp rakamı verme. 'olabilir', 'muhtemelen', 'bir miktar' gibi ihtiyatlı dil kullan.",
            "Hava durumu sadece context içinde geldiyse yorumla; yoksa hava hakkında tahmin yürütme.",
            "Sürüş güvenliği konusunda vaaz verme; maksimum hızı sadece veri olarak yorumla.",
            build_ai_user_address_instruction(data, lang),
            _trip_ai_story_personality_instruction(data, lang),
        ]
    return "\n".join(base)


async def async_update_trip_record_ai_summary(
    hass: HomeAssistant,
    record_id: str,
    ai_summary: str,
    *,
    detail_level: str | None = None,
    telegram_status: str | None = None,
) -> None:
    """Persist AI trip narrative into the monthly trip ledger record."""
    record_id = str(record_id or "").strip()
    ai_summary = str(ai_summary or "").strip()
    if not record_id or not ai_summary:
        return
    normalized_detail = normalize_trip_story_detail_level(detail_level) if detail_level else ""
    normalized_status = str(telegram_status or "").strip()

    def _update() -> None:
        payload = load_trip_monthly_ledger(hass)
        records = [item for item in list(payload.get("records") or []) if isinstance(item, dict)]
        changed = False
        for item in records:
            if str(item.get("id") or "").strip() == record_id:
                item["ai_summary"] = ai_summary
                item["ai_summary_at"] = datetime.now().isoformat(timespec="seconds")
                if normalized_detail:
                    item["ai_summary_detail_level"] = normalized_detail
                if normalized_status:
                    item["ai_summary_telegram_status"] = normalized_status
                changed = True
                break
        if changed:
            payload["records"] = records
            save_trip_monthly_ledger(hass, payload)

    await hass.async_add_executor_job(_update)


async def async_generate_and_send_post_trip_ai_story(
    hass: HomeAssistant,
    data: dict[str, Any],
    report_data: dict[str, Any],
    *,
    telegram_target: str,
    source: str,
    record_id: str | None = None,
) -> str | None:
    """Generate and send a post-trip AI story after the normal visual report."""
    if not get_bool_option(data, CONF_AI_ENABLED, DEFAULT_AI_ENABLED):
        _LOGGER.debug("Post-trip AI story skipped because POM AI is disabled")
        return None
    if not get_bool_option(data, CONF_AI_ALERT_POST_TRIP_SUMMARY_ENABLED, DEFAULT_AI_ALERT_POST_TRIP_SUMMARY_ENABLED):
        _LOGGER.debug("Post-trip AI story skipped because post-trip summary setting is disabled")
        return None

    api_key = str(data.get(CONF_OPENAI_API_KEY, "")).strip()
    if not api_key:
        _LOGGER.info("Post-trip AI story skipped because OpenAI API key is empty")
        return None

    telegram_target = str(telegram_target or "").strip()
    if not telegram_target:
        _LOGGER.debug("Post-trip AI story will be saved to Trip Records without Telegram target")

    enriched_report_data = dict(report_data or {})
    try:
        enriched_report_data = await async_enrich_trip_report_with_weather(hass, report_data)
    except Exception as err:
        _LOGGER.exception("Post-trip AI weather enrichment failed safely: %s", err)
    try:
        enrich_trip_report_grade(enriched_report_data, lang=get_report_language(data))
    except Exception as err:
        _LOGGER.exception("Post-trip AI grade enrichment failed safely: %s", err)
    try:
        context = build_trip_ai_context_payload(enriched_report_data, source=source)
    except Exception as err:
        _LOGGER.exception("Post-trip AI context build failed safely: %s", err)
        return None

    story_detail_level = normalize_trip_story_detail_level(data.get(CONF_AI_TRIP_STORY_DETAIL_LEVEL))
    story_lang = get_report_language(data)
    context["story_detail_level"] = story_detail_level
    context["report_language"] = story_lang

    model = str(data.get(CONF_OPENAI_MODEL, DEFAULT_OPENAI_MODEL)).strip() or DEFAULT_OPENAI_MODEL
    configured_max_tokens = int(safe_float(data.get(CONF_AI_MAX_OUTPUT_TOKENS), DEFAULT_AI_MAX_OUTPUT_TOKENS))
    if story_detail_level == AI_TRIP_STORY_DETAIL_BASIC:
        max_tokens = max(220, min(configured_max_tokens, 360))
    elif story_detail_level == AI_TRIP_STORY_DETAIL_BALANCED:
        max_tokens = max(350, min(configured_max_tokens, 650))
    else:
        max_tokens = max(500, min(configured_max_tokens, 1000))

    try:
        story = await async_call_openai_responses_api(
            hass,
            api_key=api_key,
            model=model,
            system_prompt=build_trip_ai_story_system_prompt(data, story_lang),
            user_message=build_trip_ai_story_user_message(context, story_detail_level, story_lang),
            context_text=(
                "This call is only for the post-drive report narrative. Do not use other Home Assistant entity context."
                if story_lang == APP_LANGUAGE_EN else
                "Bu çağrı sadece son sürüş raporunu hikâyeleştirmek içindir. Başka Home Assistant entity bağlamı kullanma."
            ),
            max_output_tokens=max_tokens,
        )
    except Exception as err:
        _LOGGER.exception("Post-trip AI story generation failed: %s", err)
        return None

    story = str(story or "").strip()
    if not story:
        return None

    # Persist the story before Telegram send. If Telegram fails, the user can still
    # read the AI narrative from Trip Records. This is intentionally separate from
    # the normal report pipeline and cannot affect the saved trip ledger.
    if record_id:
        try:
            await async_update_trip_record_ai_summary(
                hass,
                record_id,
                story,
                detail_level=story_detail_level,
                telegram_status="pending" if telegram_target else "saved_no_telegram",
            )
        except Exception:
            _LOGGER.exception("Could not persist post-trip AI story into trip ledger before Telegram send")

    if not telegram_target:
        return story

    try:
        await async_send_telegram_text_chunks(
            hass,
            data,
            telegram_target,
            story,
            title=("🤖 Tesla AI Driving Comment" if story_lang == APP_LANGUAGE_EN else "🤖 Tesla AI Sürüş Yorumu"),
            limit=3000,
        )
    except Exception as err:
        _LOGGER.exception("Post-trip AI story Telegram send failed: %s", err)
        if record_id:
            try:
                await async_update_trip_record_ai_summary(
                    hass,
                    record_id,
                    story,
                    detail_level=story_detail_level,
                    telegram_status="telegram_failed",
                )
            except Exception:
                _LOGGER.exception("Could not persist post-trip AI Telegram failure status")
        return story

    if record_id:
        try:
            await async_update_trip_record_ai_summary(
                hass,
                record_id,
                story,
                detail_level=story_detail_level,
                telegram_status="sent",
            )
        except Exception:
            _LOGGER.exception("Could not persist post-trip AI story sent status")

    return story


async def async_schedule_post_trip_ai_story(
    hass: HomeAssistant,
    data: dict[str, Any],
    report_data: dict[str, Any],
    *,
    telegram_target: str,
    source: str,
    record_id: str | None = None,
    post_report_delay_seconds: float = 0.5,
) -> None:
    """Run the AI story after the normal visual trip report has been sent.

    Important: this function is called only after the normal Live Trip/Trip PNG
    send path succeeds. Therefore the AI story follows the same Live Trip report
    delay window (for example, Park + 5 min) and can never be sent before the
    normal Live Trip report. post_report_delay_seconds is only a tiny spacing
    delay after the normal report message, not a replacement for Live Trip
    finish delay.
    """
    if not telegram_target:
        return
    if not get_bool_option(data, CONF_AI_ALERT_POST_TRIP_SUMMARY_ENABLED, DEFAULT_AI_ALERT_POST_TRIP_SUMMARY_ENABLED):
        return

    spacing = max(0.0, min(float(post_report_delay_seconds or 0.0), 30.0))

    async def _runner() -> None:
        try:
            if spacing:
                await asyncio.sleep(spacing)
            await async_generate_and_send_post_trip_ai_story(
                hass,
                dict(data or {}),
                dict(report_data or {}),
                telegram_target=telegram_target,
                source=source,
                record_id=record_id,
            )
        except Exception as err:
            # AI is a secondary/post-report feature. It must never surface as an
            # unhandled task exception or affect the saved trip record.
            _LOGGER.exception("Post-trip AI story background task failed safely: %s", err)

    hass.async_create_task(_runner())


def build_monthly_trip_summary_payload(hass: HomeAssistant) -> dict[str, Any] | None:
    """Build the active month's trip summary payload."""
    payload = load_trip_monthly_ledger(hass)
    month_key = datetime.now().strftime("%Y-%m")
    records = [
        item
        for item in list(payload.get("records") or [])
        if (
            isinstance(item, dict)
            and str(item.get("month_key") or "").strip() == month_key
            and not is_manual_tracking_trip_record(item)
        )
    ]
    if not records:
        return None

    def _sort_key(item: dict[str, Any]) -> str:
        return str(item.get("created_at") or item.get("display_at") or "")

    records.sort(key=_sort_key, reverse=True)

    total_distance = sum(safe_float(item.get("trip_km"), 0.0) for item in records)
    total_energy = sum(safe_float(item.get("used_kwh"), 0.0) for item in records)
    total_cost = sum(safe_float(item.get("total_cost"), 0.0) for item in records)
    total_duration_minutes = sum(safe_float(item.get("duration_minutes"), 0.0) for item in records)
    avg_consumption = (total_energy / total_distance * 100.0) if total_distance > 0 else 0.0
    score_values = [safe_float(item.get("driving_score"), 0.0) for item in records if safe_float(item.get("driving_score"), 0.0) > 0]
    avg_driving_score = (sum(score_values) / len(score_values)) if score_values else 0.0

    currency_label = get_report_currency(get_first_entry_config(hass) or {})

    return {
        "month_key": month_key,
        "currency_label": currency_label,
        "summary": {
            "count": len(records),
            "total_distance_km": round(total_distance, 3),
            "total_energy_kwh": round(total_energy, 3),
            "total_cost": round(total_cost, 2),
            "total_duration_minutes": round(total_duration_minutes, 2),
            "average_consumption_kwh_100km": round(avg_consumption, 3),
            "average_driving_score": round(avg_driving_score, 1),
        },
        "records": records,
    }


def format_duration_minutes_for_language(minutes: float, lang: str = "tr") -> str:
    """Return a compact duration string in Turkish or English."""
    total = max(0, int(round(safe_float(minutes, 0.0))))
    hours = total // 60
    mins = total % 60
    if str(lang or "tr").lower().startswith("en"):
        if hours and mins:
            return f"{hours} hr {mins} min"
        if hours:
            return f"{hours} hr"
        return f"{mins} min"
    if hours and mins:
        return f"{hours} sa {mins} dk"
    if hours:
        return f"{hours} sa"
    return f"{mins} dk"


def build_monthly_trip_answer_text(payload: dict[str, Any], *, lang: str = "tr") -> str:
    """Build a short answer text for the current month's trip summary."""
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    count = int(safe_float(summary.get("count"), 0.0))
    total_distance = safe_float(summary.get("total_distance_km"), 0.0)
    total_energy = safe_float(summary.get("total_energy_kwh"), 0.0)
    total_cost = safe_float(summary.get("total_cost"), 0.0)
    total_duration = safe_float(summary.get("total_duration_minutes"), 0.0)
    avg_consumption = safe_float(summary.get("average_consumption_kwh_100km"), 0.0)
    avg_driving_score = safe_float(summary.get("average_driving_score"), 0.0)
    score_phrase_en = f", average driving score {avg_driving_score:.0f}/100" if avg_driving_score > 0 else ""
    score_phrase_tr = f", ortalama sürüş skoru {avg_driving_score:.0f}/100" if avg_driving_score > 0 else ""
    month_key = str(payload.get("month_key") or "")
    currency_label = str(payload.get("currency_label") or "TL").strip() or "TL"

    if str(lang or "tr").lower().startswith("en"):
        return (
            f"Current month trip summary ({month_key}): {count} drives, {total_distance:.1f} km total, "
            f"{total_energy:.1f} kWh used, estimated road cost {total_cost:.2f} {currency_label}, "
            f"total drive time {format_duration_minutes_for_language(total_duration, 'en')}, "
            f"average consumption {avg_consumption:.2f} kWh/100 km{score_phrase_en}. I am also sending the visual summary now."
        )

    return (
        f"Bu ayın sürüş özeti ({month_key}): toplam {count} sürüş, {total_distance:.1f} km yol, "
        f"{total_energy:.1f} kWh enerji tüketimi, Supercharger bazlı yaklaşık {total_cost:.2f} {currency_label} yol maliyeti, "
        f"toplam sürüş süresi {format_duration_minutes_for_language(total_duration, 'tr')}, "
        f"ortalama tüketim {avg_consumption:.2f} kWh/100 km{score_phrase_tr}. Görsel özeti de şimdi gönderiyorum."
    )


def build_charge_cost_record_id(
    *,
    month_key: str,
    provider: str,
    added_kwh: float,
    total_cost: float,
    finished_at_iso: str,
) -> str:
    """Build a stable-enough de-duplication key for one charging session."""
    return "|".join(
        [
            month_key,
            finished_at_iso.strip(),
            str(provider or "").strip().lower(),
            f"{added_kwh:.3f}",
            f"{total_cost:.2f}",
        ]
    )


def build_charge_cost_record_from_report_data(
    report_data: dict[str, Any] | None,
    *,
    source: str,
    location_label: str = "",
) -> dict[str, Any] | None:
    """Convert final charging report data into a ledger record."""
    report_data = report_data or {}
    provider = str(report_data.get("actual_provider") or "").strip()
    price_per_kwh = safe_float(report_data.get("actual_price_per_kwh"), 0.0)
    total_cost = safe_float(report_data.get("actual_total_cost"), 0.0)
    added_kwh = safe_float(report_data.get("added_kwh"), 0.0)

    if total_cost <= 0 or added_kwh <= 0:
        return None

    now = datetime.now()
    month_key = now.strftime("%Y-%m")
    finished_at_iso = now.isoformat(timespec="seconds")
    display_at = now.strftime("%d.%m.%Y %H:%M")
    provider = provider or "Diğer"
    record_id = build_charge_cost_record_id(
        month_key=month_key,
        provider=provider,
        added_kwh=added_kwh,
        total_cost=total_cost,
        finished_at_iso=finished_at_iso,
    )
    return {
        "id": record_id,
        "month_key": month_key,
        "created_at": finished_at_iso,
        "display_at": display_at,
        "provider": provider,
        "location_label": str(location_label or "").strip(),
        "added_kwh": round(added_kwh, 3),
        "price_per_kwh": round(price_per_kwh, 4),
        "total_cost": round(total_cost, 2),
        "currency_label": str(report_data.get("currency_label") or "").strip(),
        "source": str(source or "").strip() or "interactive",
    }


async def async_record_charge_cost_entry(
    hass: HomeAssistant,
    report_data: dict[str, Any] | None,
    *,
    source: str,
) -> dict[str, Any] | None:
    """Append a charging cost record if the final report contains a real cost."""
    provider_name = normalize_text_for_match(str((report_data or {}).get("actual_provider") or ""))
    location_label = ""
    if provider_name in {"ev", "home", "house"}:
        location_label = "Ev"
    else:
        location_label = get_short_cached_reverse_geocode_label(hass)

    record = build_charge_cost_record_from_report_data(
        report_data,
        source=source,
        location_label=location_label,
    )
    if not record:
        return None

    ledger = load_charge_cost_ledger(hass)
    records = list(ledger.get("records") or [])
    existing_ids = {str(item.get("id") or "") for item in records if isinstance(item, dict)}
    if record["id"] in existing_ids:
        return None

    records.append(record)
    records.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
    ledger["records"] = records
    save_charge_cost_ledger(hass, ledger)
    return record


def get_monthly_charge_cost_records(hass: HomeAssistant, month_key: str | None = None) -> list[dict[str, Any]]:
    """Return records for one month, newest first."""
    target_month = str(month_key or datetime.now().strftime("%Y-%m"))
    ledger = load_charge_cost_ledger(hass)
    records = [
        item for item in list(ledger.get("records") or [])
        if isinstance(item, dict) and str(item.get("month_key") or "") == target_month
    ]
    records.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
    return records


def summarize_charge_cost_records(records: list[dict[str, Any]]) -> dict[str, float | int]:
    """Build basic totals for a set of charging cost records."""
    total_cost = 0.0
    total_kwh = 0.0
    for item in records:
        if not isinstance(item, dict):
            continue
        total_cost += safe_float(item.get("total_cost"), 0.0)
        total_kwh += safe_float(item.get("added_kwh"), 0.0)
    return {
        "count": len(records),
        "total_cost": round(total_cost, 2),
        "total_kwh": round(total_kwh, 2),
    }


def format_charge_cost_month_label(month_key: str, lang: str = "tr") -> str:
    """Return a friendly month label for monthly charge summaries."""
    return format_month_label_for_language(month_key, lang, fallback=("Monthly Charging Summary" if str(lang or "tr").lower().startswith("en") else "Aylık Şarj Özeti"))


def format_month_label_for_language(month_key: str, lang: str = "tr", *, fallback: str = "") -> str:
    """Return a friendly month label in Turkish or English."""
    lang = "en" if str(lang or "").lower().startswith("en") else "tr"
    months = {
        "tr": {
            "01": "Ocak", "02": "Şubat", "03": "Mart", "04": "Nisan",
            "05": "Mayıs", "06": "Haziran", "07": "Temmuz", "08": "Ağustos",
            "09": "Eylül", "10": "Ekim", "11": "Kasım", "12": "Aralık",
        },
        "en": {
            "01": "January", "02": "February", "03": "March", "04": "April",
            "05": "May", "06": "June", "07": "July", "08": "August",
            "09": "September", "10": "October", "11": "November", "12": "December",
        },
    }[lang]
    raw = str(month_key or "").strip()
    if len(raw) == 7 and raw[4] == "-":
        return f"{months.get(raw[5:], raw[5:])} {raw[:4]}"
    return raw or (fallback or ("Monthly Summary" if lang == "en" else "Aylık Özet"))



def build_monthly_charge_cost_visual_payload(
    hass: HomeAssistant,
    month_key: str | None = None,
    *,
    lang: str = "tr",
) -> dict[str, Any] | None:
    """Build renderer payload for monthly charging cost visuals."""
    month_key = str(month_key or datetime.now().strftime("%Y-%m"))
    records = get_monthly_charge_cost_records(hass, month_key)
    if not records:
        return None
    summary = summarize_charge_cost_records(records)
    currency_label = get_report_currency(get_first_entry_config(hass) or {})
    return {
        "month_key": month_key,
        "month_label": format_month_label_for_language(month_key, lang, fallback=("Monthly Charging Summary" if str(lang or "tr").lower().startswith("en") else "Aylık Şarj Özeti")),
        "report_language": lang,
        "currency_label": currency_label,
        "summary": summary,
        "records": records,
    }


async def async_send_monthly_charge_cost_visual_report(
    hass: HomeAssistant,
    data: dict[str, Any],
    *,
    target: str,
    month_key: str | None = None,
    caption_prefix: str = "",
) -> list[str]:
    """Render and send monthly charge summary pages to Telegram."""
    target = str(target or "").strip()
    if not target:
        return []

    report_lang = get_report_language(data)
    payload = build_monthly_charge_cost_visual_payload(hass, month_key, lang=report_lang)
    if not payload:
        return []

    current_month_key = str(payload.get("month_key") or datetime.now().strftime("%Y-%m"))
    base_path = f"/config/www/pom_tesla_report/monthly_charge_cost_{current_month_key}_{report_lang}.png"
    png_paths = await hass.async_add_executor_job(
        render_monthly_charge_cost_report_pngs,
        payload,
        base_path,
        report_lang,
    )
    total_pages = len(png_paths)
    for page_index, png_path in enumerate(png_paths, start=1):
        if report_lang == "en":
            caption = f"📊 {format_month_label_for_language(current_month_key, report_lang, fallback='Monthly Charging Summary')} monthly charging summary"
        else:
            caption = f"📊 {format_month_label_for_language(current_month_key, report_lang, fallback='Aylık Şarj Özeti')} aylık şarj özeti"
        if total_pages > 1:
            caption = f"{caption} ({page_index}/{total_pages})"
        if caption_prefix:
            caption = f"{caption_prefix}\n{caption}"
        await async_telegram_send_photo(
            hass,
            data,
            target=target,
            file_path=png_path,
            caption=caption,
        )
    return png_paths


def should_answer_charge_cost_question(message: str) -> bool:
    """Return true when the user asks for monthly charge costs or history."""
    n = normalize_text_for_match(message)
    if not n:
        return False
    patterns = (
        "bu ay sarj",
        "bu ay şarj",
        "sarja ne kadar",
        "şarja ne kadar",
        "sarj maliyet",
        "şarj maliyet",
        "sarj gecmis",
        "şarj gecmis",
        "sarj gecmisimi",
        "şarj geçmiş",
        "sarjlarimi goster",
        "şarjlarımı göster",
        "this month charging",
        "charging history",
        "show charging history",
    )
    return any(pattern in n for pattern in patterns)


def build_current_month_charge_cost_answer(hass: HomeAssistant, *, lang: str = "tr") -> str | None:
    """Return the current month's charging cost summary."""
    report_lang = "en" if str(lang or "tr").lower().startswith("en") else "tr"
    month_key = datetime.now().strftime("%Y-%m")
    records = get_monthly_charge_cost_records(hass, month_key)
    if not records:
        return "There is no recorded charging cost for this month yet." if report_lang == "en" else "Bu ay için kayıtlı bir şarj maliyeti yok."

    totals = summarize_charge_cost_records(records)
    currency_label = get_report_currency(get_first_entry_config(hass) or {})
    month_label = format_month_label_for_language(month_key, report_lang, fallback=("Monthly Charging Summary" if report_lang == "en" else "Aylık Şarj Özeti"))
    if report_lang == "en":
        lines = [
            f"{month_label} charging summary:",
            f"Total cost: {totals['total_cost']:.2f} {currency_label}",
            f"Total energy: {totals['total_kwh']:.2f} kWh",
            f"Record count: {totals['count']}",
            "",
            "Records:",
        ]
    else:
        lines = [
            f"{month_label} şarj özeti:",
            f"Toplam maliyet: {totals['total_cost']:.2f} {currency_label}",
            f"Toplam enerji: {totals['total_kwh']:.2f} kWh",
            f"Kayıt sayısı: {totals['count']}",
            "",
            "Kayıtlar:",
        ]
    for idx, item in enumerate(records[:12], start=1):
        display_at = str(item.get("display_at") or item.get("created_at") or "-")
        provider = str(item.get("provider") or ("Other" if report_lang == "en" else "Diğer"))
        added_kwh = safe_float(item.get("added_kwh"), 0.0)
        total_cost = safe_float(item.get("total_cost"), 0.0)
        lines.append(f"{idx}. {display_at} - {provider} - {added_kwh:.1f} kWh - {total_cost:.2f} {currency_label}")
    return "\n".join(lines)


def build_charge_cost_answer(hass: HomeAssistant, message: str, *, lang: str = "tr") -> str | None:
    """Return a deterministic answer for monthly charging cost questions."""
    if not should_answer_charge_cost_question(message):
        return None
    return build_current_month_charge_cost_answer(hass, lang=lang)


def is_direct_charge_summary_command(message: str) -> bool:
    """Return True for explicit slash-style charging summary shortcuts."""
    raw = str(message or "").strip().lower()
    return raw.startswith("/charge")


async def async_detect_charge_cost_intent_with_llm(
    hass: HomeAssistant,
    data: dict[str, Any],
    user_message: str,
) -> bool:
    """Use the configured model to detect monthly charging summary requests."""
    api_key = str(data.get(CONF_OPENAI_API_KEY, "")).strip()
    if not api_key:
        return False

    model = str(data.get(CONF_OPENAI_MODEL, DEFAULT_OPENAI_MODEL)).strip() or DEFAULT_OPENAI_MODEL
    system_prompt = (
        "You are a strict intent classifier for Tesla AI. "
        "Return ONLY JSON. No prose. No markdown. "
        "Classify whether the user's message is asking about the current month's charging totals, "
        "charging costs, charging history, or monthly charging summary in any language. "
        "If yes, return {\"type\":\"charge_monthly_summary\"}. "
        "If not, return {\"type\":\"other\"}. "
        "Messages like '/charge', 'how much did I spend charging this month', "
        "'bu ay ne kadar şarj ettim', 'wie viel habe ich diesen Monat geladen', "
        "or Japanese equivalents should map to charge_monthly_summary. "
        "Vehicle control commands, climate questions, lock requests, and general chat must return other."
    )
    context_text = (
        f"Current month key: {datetime.now().strftime('%Y-%m')}\n"
        "Feature meaning: monthly charging summary includes total cost, total energy, "
        "record count, and list of current-month charging sessions."
    )
    try:
        text = await async_call_openai_responses_api(
            hass,
            api_key=api_key,
            model=model,
            system_prompt=system_prompt,
            user_message=user_message,
            context_text=context_text,
            max_output_tokens=80,
        )
    except Exception:
        return False

    intent = _json_from_ai_router_text(text)
    return isinstance(intent, dict) and str(intent.get("type") or "").strip() == "charge_monthly_summary"


async def async_maybe_build_charge_cost_answer(
    hass: HomeAssistant,
    data: dict[str, Any],
    user_message: str,
) -> str | None:
    """Return the monthly charging summary when the message matches local or AI intent routing."""
    report_lang = get_telegram_report_language(data, user_message)
    if is_direct_charge_summary_command(user_message):
        return build_current_month_charge_cost_answer(hass, lang=report_lang)
    direct = build_charge_cost_answer(hass, user_message, lang=report_lang)
    if direct:
        return direct
    if await async_detect_charge_cost_intent_with_llm(hass, data, user_message):
        return build_current_month_charge_cost_answer(hass, lang=report_lang)
    return None


async def async_handle_configured_telegram_report_command(
    hass: HomeAssistant,
    data: dict[str, Any],
    *,
    user_message: str,
    telegram_target: str | None,
    send_telegram: bool = True,
) -> bool:
    """Handle current report slash commands configured in Telegram settings."""
    matched = match_telegram_report_command(data, user_message)
    if str(user_message or "").strip().startswith("/"):
        _log_telegram_command_match(data, user_message, matched)
    if not matched:
        return False

    action, action_lang = matched
    target = str(telegram_target or "").strip()

    if action == "charge_report":
        if send_telegram and target:
            answer = build_current_month_charge_cost_answer(hass, lang=action_lang)
            if not answer:
                answer = "There is no charging record for this month yet." if action_lang == "en" else "Bu ay için kayıtlı şarj verisi henüz yok."
            await async_telegram_send_message(
                hass,
                data,
                target=target,
                parse_mode="plain_text",
                message=answer,
            )
            await async_send_monthly_charge_cost_visual_report(
                hass,
                data,
                target=target,
            )
        return True

    if action == "trip_last":
        if send_telegram and target:
            await async_send_last_trip_report_visual(
                hass,
                data,
                target=target,
                user_message=user_message,
                report_lang=action_lang,
            )
        return True

    if action == "trip_today":
        if send_telegram and target:
            await async_send_trip_summary_visual_with_options(
                hass,
                data,
                target=target,
                mode="all",
                period="today",
                user_message=user_message,
                include_keyboard=False,
                report_lang=action_lang,
            )
        return True

    if action == "trip_week":
        if send_telegram and target:
            await async_send_trip_summary_visual_with_options(
                hass,
                data,
                target=target,
                mode="all",
                period="weekly",
                user_message=user_message,
                include_keyboard=False,
                report_lang=action_lang,
            )
        return True

    if action == "trip_all":
        if send_telegram and target:
            await async_send_trip_summary_visual_with_options(
                hass,
                data,
                target=target,
                mode="all",
                user_message=user_message,
                include_keyboard=False,
                report_lang=action_lang,
                only_remaining_pages=False,
            )
        return True

    if action == "trip_single":
        if send_telegram and target:
            await async_send_trip_summary_visual_with_options(
                hass,
                data,
                target=target,
                mode="single",
                user_message=user_message,
                include_keyboard=True,
                report_lang=action_lang,
            )
        return True

    if action == "trip_summary":
        if send_telegram and target:
            await async_send_trip_summary_visual_with_options(
                hass,
                data,
                target=target,
                mode="overview",
                user_message=user_message,
                include_keyboard=True,
                report_lang=action_lang,
            )
        return True

    return False


async def async_send_monthly_trip_visual_report(
    hass: HomeAssistant,
    data: dict[str, Any],
    *,
    target: str,
) -> list[str]:
    """Render and send current month's trip summary pages to Telegram."""
    target = str(target or "").strip()
    if not target:
        return []

    payload = build_monthly_trip_summary_payload(hass)
    if not payload:
        return []

    current_month_key = str(payload.get("month_key") or datetime.now().strftime("%Y-%m"))
    base_path = f"/config/www/pom_tesla_report/monthly_trip_summary_{current_month_key}.png"
    report_lang = get_report_language(data)
    png_paths = await hass.async_add_executor_job(
        render_monthly_trip_report_pngs,
        payload,
        base_path,
        report_lang,
    )
    total_pages = len(png_paths)
    month_caption = format_month_label_for_language(current_month_key, report_lang, fallback=("Monthly Trip Summary" if report_lang == "en" else "Aylık Sürüş Özeti"))
    for page_index, png_path in enumerate(png_paths, start=1):
        caption = f"📈 {month_caption} monthly trip summary" if report_lang == "en" else f"📈 {month_caption} aylık sürüş özeti"
        if total_pages > 1:
            caption = f"{caption} ({page_index}/{total_pages})"
        await async_telegram_send_photo(
            hass,
            data,
            target=target,
            file_path=png_path,
            caption=caption,
        )
    return png_paths


def should_answer_trip_summary_question(message: str) -> bool:
    """Return true when the user asks for monthly trip totals or history."""
    n = normalize_text_for_match(message)
    if not n:
        return False
    patterns = (
        "bu ay surus",
        "bu ay sürüş",
        "surus ozet",
        "sürüş özet",
        "surus raporlarim",
        "sürüş raporlarım",
        "suruslerimi goster",
        "sürüşlerimi göster",
        "bu ay kac km",
        "bu ay kaç km",
        "bu ay ne kadar yol",
        "aylik trip",
        "monthly trip",
        "trip summary",
        "trip history",
        "show trip history",
        "this month trips",
        "driving summary",
    )
    return any(pattern in n for pattern in patterns)


def build_trip_summary_answer(hass: HomeAssistant, data: dict[str, Any], message: str) -> str | None:
    """Return a deterministic answer for monthly trip summary questions."""
    if not should_answer_trip_summary_question(message):
        return None
    payload = build_monthly_trip_summary_payload(hass)
    if not payload:
        return "There is no recorded trip data for this month yet." if get_telegram_report_language(data, message) == "en" else "Bu ay için kayıtlı sürüş verisi henüz yok."
    return build_monthly_trip_answer_text(payload, lang=get_telegram_report_language(data, message))


def is_direct_trip_summary_command(message: str) -> bool:
    """Return True for explicit slash-style trip summary shortcuts."""
    raw = str(message or "").strip().lower().replace("ı", "i")
    normalized = normalize_text_for_match(message)
    if is_trip_all_command(message) or is_trip_single_command(message):
        return False
    return raw.startswith("/trip") or raw.startswith("/trips") or raw.startswith("/tripsummary") or normalized.startswith("/trip")


async def async_detect_trip_request_intent_with_llm(
    hass: HomeAssistant,
    data: dict[str, Any],
    user_message: str,
) -> str:
    """Use the configured model to classify trip-related Telegram intents in any language."""
    api_key = str(data.get(CONF_OPENAI_API_KEY, "")).strip()
    if not api_key:
        return "other"

    model = str(data.get(CONF_OPENAI_MODEL, DEFAULT_OPENAI_MODEL)).strip() or DEFAULT_OPENAI_MODEL
    system_prompt = (
        "You are a strict multilingual intent classifier for Tesla AI. "
        "Return ONLY JSON. No prose. No markdown. "
        "Classify the user's message into exactly one of these types: "
        "trip_monthly_summary, trip_monthly_all, last_trip_report, other. "
        "trip_monthly_summary means the user wants this month's driving/trip summary, totals, recent trip list, or a summary page. "
        "trip_monthly_all means the user explicitly wants all current-month trip records/pages/history in full. "
        "last_trip_report means the user wants the visual/details/report for the most recent single trip or asks what happened on the last trip/drive/journey. "
        "The message can be in any language, including Turkish, English, Japanese, German, French, Arabic, etc. "
        "Examples that should map to last_trip_report include: 'show my last trip report', 'son sürüş raporumu göster', 'what happened on the last drive', '前回のドライブを見せて'. "
        "Examples that should map to trip_monthly_summary include: '/trip', 'show my trip summary', 'bu ay kaç km gittim', '今月どれくらい走った？'. "
        "Examples that should map to trip_monthly_all include: '/tripall', 'show all trip records', 'tüm sürüş kayıtlarını göster', 'show every trip this month'. "
        "Vehicle control requests, charge reports, climate/status questions, maps, and general chat must return other. "
        "Return JSON like {\"type\":\"last_trip_report\"}."
    )
    context_text = (
        f"Current month key: {datetime.now().strftime('%Y-%m')}\n"
        "Available trip outputs: current-month trip summary visual, all pages of the monthly trip summary, and the latest single-trip report visual."
    )
    try:
        response_text = await async_call_openai_responses_api(
            hass,
            api_key=api_key,
            model=model,
            system_prompt=system_prompt,
            user_message=user_message,
            context_text=context_text,
            max_output_tokens=80,
        )
    except Exception:
        return "other"

    intent = _json_from_ai_router_text(response_text)
    if not isinstance(intent, dict):
        return "other"
    intent_type = str(intent.get("type") or "").strip()
    return intent_type if intent_type in {"trip_monthly_summary", "trip_monthly_all", "last_trip_report"} else "other"


async def async_maybe_build_trip_summary_answer(
    hass: HomeAssistant,
    data: dict[str, Any],
    user_message: str,
) -> str | None:
    """Return the monthly trip summary when the message matches local or AI intent routing."""
    if is_direct_trip_summary_command(user_message):
        payload = build_monthly_trip_summary_payload(hass)
        if not payload:
            return "There is no recorded trip data for this month yet." if get_telegram_report_language(data, user_message) == "en" else "Bu ay için kayıtlı sürüş verisi henüz yok."
        return build_monthly_trip_answer_text(payload, lang=get_telegram_report_language(data, user_message))
    direct = build_trip_summary_answer(hass, data, user_message)
    if direct:
        return direct
    if await async_detect_trip_request_intent_with_llm(hass, data, user_message) == "trip_monthly_summary":
        payload = build_monthly_trip_summary_payload(hass)
        if not payload:
            return "There is no recorded trip data for this month yet." if get_telegram_report_language(data, user_message) == "en" else "Bu ay için kayıtlı sürüş verisi henüz yok."
        return build_monthly_trip_answer_text(payload, lang=get_telegram_report_language(data, user_message))
    return None


def is_trip_all_command(message: str) -> bool:
    """Return True for direct all-record trip summary commands."""
    raw = str(message or "").strip().lower().replace("ı", "i")
    normalized = normalize_text_for_match(message)
    return raw.startswith("/tripall") or raw.startswith("/tripsall") or normalized.startswith("/tripall")


def is_trip_single_command(message: str) -> bool:
    """Return True for direct single-page trip summary commands."""
    raw = str(message or "").strip().lower().replace("ı", "i")
    normalized = normalize_text_for_match(message)
    return raw.startswith("/single") or raw.startswith("/trip single") or normalized.startswith("/single")


def is_trip_last_command(message: str) -> bool:
    """Return True for direct last-trip visual commands."""
    raw = str(message or "").strip().lower().replace("ı", "i")
    normalized = normalize_text_for_match(message)
    return raw.startswith("/triplast") or raw.startswith("/lasttrip") or normalized.startswith("/triplast")


def is_trip_today_command(message: str) -> bool:
    """Return True for direct current-day trip summary commands."""
    raw = str(message or "").strip().lower().replace("ı", "i")
    normalized = normalize_text_for_match(message)
    return raw.startswith("/triptoday") or raw.startswith("/todaytrip") or normalized.startswith("/triptoday")


def is_trip_week_command(message: str) -> bool:
    """Return True for direct current-week trip summary commands."""
    raw = str(message or "").strip().lower().replace("ı", "i")
    normalized = normalize_text_for_match(message)
    return raw.startswith("/tripweek") or raw.startswith("/weektrip") or normalized.startswith("/tripweek")


def parse_trip_action_and_lang(message: str, default_lang: str = "tr") -> tuple[str, str]:
    """Parse trip action callback/command text and optional language suffix."""
    text = str(message or "").strip().lower().replace("ı", "i")
    lang = "en" if str(default_lang or "tr").lower().startswith("en") else "tr"
    action = text
    for sep in ["|", "_"]:
        if sep in text and text.split(sep)[0] in {"/tripall", "/single", "/triplast", "/triptoday", "/tripweek"}:
            base, suffix = text.split(sep, 1)
            action = base
            suffix = suffix.strip()
            if suffix.startswith("en"):
                lang = "en"
            elif suffix.startswith("tr"):
                lang = "tr"
            break
    return action, lang


def build_trip_summary_inline_keyboard(lang: str = "tr") -> list[str]:
    """Return inline keyboard rows for trip summary follow-up actions."""
    lang = "en" if str(lang or "tr").lower().startswith("en") else "tr"
    suffix = "en" if lang == "en" else "tr"
    if lang == "en":
        return [f"📋 All records:/tripall_{suffix}, 🚗 Last trip report:/triplast_{suffix}"]
    return [f"📋 Tüm kayıtlar:/tripall_{suffix}, 🚗 Son sürüş raporu:/triplast_{suffix}"]


def build_trip_record_compact_line(record: dict[str, Any], index: int, *, lang: str = "tr") -> str:
    """Build one compact Telegram line for a trip record."""
    display_at = str(record.get("display_at") or record.get("report_date") or record.get("created_at") or "-").strip()
    start_address = str(record.get("start_address") or "-").strip()
    end_address = str(record.get("end_address") or "-").strip()
    trip_km = safe_float(record.get("trip_km"), 0.0)
    used_kwh = safe_float(record.get("used_kwh"), 0.0)
    consumption = safe_float(record.get("consumption_kwh_100km"), 0.0)
    total_cost = safe_float(record.get("total_cost"), 0.0)
    currency_label = str(record.get("currency_label") or "TL").strip() or "TL"
    duration_text = str(record.get("duration_text") or "").strip()
    driving_score = safe_float(record.get("driving_score"), 0.0)
    score_part = f" · Skor {driving_score:.0f}/100" if driving_score > 0 else ""
    score_part_en = f" · Score {driving_score:.0f}/100" if driving_score > 0 else ""
    if not duration_text:
        duration_text = format_duration_minutes_for_language(safe_float(record.get("duration_minutes"), 0.0), lang)

    def _short(text: str, max_len: int = 34) -> str:
        text = " ".join(str(text or "-").split())
        if len(text) <= max_len:
            return text
        return text[: max_len - 1].rstrip() + "…"

    arrow = "→"
    if str(lang or "tr").lower().startswith("en"):
        return (
            f"{index}. {display_at}\n"
            f"   {_short(start_address)} {arrow} {_short(end_address)}\n"
            f"   {trip_km:.1f} km · {duration_text} · {used_kwh:.1f} kWh · "
            f"{consumption:.1f} kWh/100 · {total_cost:.0f} {currency_label}{score_part_en}"
        )
    return (
        f"{index}. {display_at}\n"
        f"   {_short(start_address)} {arrow} {_short(end_address)}\n"
        f"   {trip_km:.1f} km · {duration_text} · {used_kwh:.1f} kWh · "
        f"{consumption:.1f} kWh/100 · {total_cost:.0f} {currency_label}{score_part}"
    )


def build_trip_summary_message_from_payload(
    payload: dict[str, Any],
    *,
    lang: str = "tr",
    limit: int = 10,
    all_records: bool = False,
    include_buttons_hint: bool = True,
) -> str:
    """Build compact monthly trip summary text for Telegram."""
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    records = [item for item in list(payload.get("records") or []) if isinstance(item, dict)]
    total_count = int(safe_float(summary.get("count"), float(len(records))))
    total_distance = safe_float(summary.get("total_distance_km"), 0.0)
    total_energy = safe_float(summary.get("total_energy_kwh"), 0.0)
    total_cost = safe_float(summary.get("total_cost"), 0.0)
    total_duration = safe_float(summary.get("total_duration_minutes"), 0.0)
    avg_consumption = safe_float(summary.get("average_consumption_kwh_100km"), 0.0)
    month_key = str(payload.get("month_key") or datetime.now().strftime("%Y-%m"))
    currency_label = str(payload.get("currency_label") or "TL").strip() or "TL"

    for item in records:
        if not str(item.get("currency_label") or "").strip():
            item["currency_label"] = currency_label

    selected_records = records if all_records else records[: max(1, int(limit or 10))]
    shown_count = len(selected_records)
    report_lang = "en" if str(lang or "tr").lower().startswith("en") else "tr"

    if report_lang == "en":
        title = f"🚗 Monthly Trip Summary ({month_key})"
        header = [
            title,
            "",
            f"Total distance: {total_distance:.1f} km",
            f"Total drives: {total_count}",
            f"Total energy: {total_energy:.1f} kWh",
            f"Estimated road cost: {total_cost:.2f} {currency_label}",
            f"Total duration: {format_duration_minutes_for_language(total_duration, 'en')}",
            f"Average consumption: {avg_consumption:.2f} kWh/100 km",
            "",
            f"Records: {'all' if all_records else f'latest {shown_count} of {total_count}'}",
        ]
        if include_buttons_hint and not all_records:
            header.append("Use the buttons below for all records or the single-page view.")
    else:
        title = f"🚗 Aylık Sürüş Özeti ({month_key})"
        header = [
            title,
            "",
            f"Toplam km: {total_distance:.1f} km",
            f"Toplam sürüş: {total_count}",
            f"Toplam enerji: {total_energy:.1f} kWh",
            f"Tahmini yol maliyeti: {total_cost:.2f} {currency_label}",
            f"Toplam süre: {format_duration_minutes_for_language(total_duration, 'tr')}",
            f"Ortalama tüketim: {avg_consumption:.2f} kWh/100 km",
            "",
            f"Kayıtlar: {'tümü' if all_records else f'son {shown_count}/{total_count}'}",
        ]
        if include_buttons_hint and not all_records:
            header.append("Tüm kayıtlar veya tek sayfa görünüm için alttaki butonları kullan.")

    lines = header + [""]
    if not selected_records:
        lines.append("No trip records found." if report_lang == "en" else "Sürüş kaydı bulunamadı.")
    else:
        for idx, item in enumerate(selected_records, start=1):
            lines.append(build_trip_record_compact_line(item, idx, lang=report_lang))
            lines.append("")
    return "\n".join(lines).strip()


async def async_build_monthly_trip_visual_pages(
    hass: HomeAssistant,
    data: dict[str, Any],
    *,
    report_lang: str,
    period: str = "monthly",
) -> tuple[dict[str, Any] | None, list[str]]:
    """Render trip summary pages for monthly, weekly or today periods."""
    normalized_period = str(period or "monthly").strip().lower()
    if normalized_period in {"today", "daily", "day"}:
        payload = build_today_trip_summary_payload(hass, lang=report_lang)
        base_key = datetime.now().strftime("%Y-%m-%d")
        prefix = "today_trip_summary"
    elif normalized_period in {"weekly", "week"}:
        payload = build_weekly_trip_summary_payload(hass, lang=report_lang)
        base_key = _periodic_week_key()
        prefix = "weekly_trip_summary"
    else:
        payload = build_monthly_trip_summary_payload(hass)
        base_key = datetime.now().strftime("%Y-%m")
        prefix = "monthly_trip_summary"
    if not payload:
        return None, []
    safe_key = re.sub(r"[^a-zA-Z0-9_-]", "_", str(base_key or datetime.now().strftime("%Y-%m"))).strip("_") or "period"
    base_path = f"/config/www/pom_tesla_report/{prefix}_{safe_key}_{report_lang}.png"
    png_paths = await hass.async_add_executor_job(
        render_monthly_trip_report_pngs,
        payload,
        base_path,
        report_lang,
    )
    return payload, png_paths


async def async_send_last_trip_report_visual(
    hass: HomeAssistant,
    data: dict[str, Any],
    *,
    target: str,
    user_message: str = "",
    report_lang: str | None = None,
) -> bool:
    """Send the latest single trip report visual in the requested language."""
    target = str(target or "").strip()
    if not target:
        return False
    report_lang = "en" if str(report_lang or "").lower().startswith("en") else get_telegram_report_language(data, user_message)
    report_info = get_latest_trip_report_info(hass)
    if not report_info:
        message = "There is no saved last trip report yet." if report_lang == "en" else "Henüz kayıtlı bir son sürüş raporu yok."
        await async_telegram_send_message(hass, data, target=target, parse_mode="plain_text", message=message)
        return True

    caption = "🚗 Last Trip Report" if report_lang == "en" else "🚗 Son Sürüş Raporu"
    send_path = str(report_info.get("path") or "").strip()
    report_data = report_info.get("report_data") if isinstance(report_info.get("report_data"), dict) else {}
    if report_data:
        temp_name = f"last_trip_report_{report_lang}.png"
        output_path = f"/config/www/pom_tesla_report/{temp_name}"
        try:
            if not report_data.get("driving_score"):
                enrich_trip_report_score(report_data, lang=report_lang)
            send_path = await hass.async_add_executor_job(
                render_trip_report_png,
                report_data,
                output_path,
                report_lang,
            )
        except Exception:
            _LOGGER.exception("Could not render localized last trip report, falling back to existing file")
    if not send_path or not Path(send_path).exists():
        message = "There is no saved last trip report yet." if report_lang == "en" else "Henüz kayıtlı bir son sürüş raporu yok."
        await async_telegram_send_message(hass, data, target=target, parse_mode="plain_text", message=message)
        return True

    await async_telegram_send_photo(
        hass,
        data,
        target=target,
        file_path=send_path,
        caption=caption,
    )
    return True


async def async_send_trip_summary_visual_with_options(
    hass: HomeAssistant,
    data: dict[str, Any],
    *,
    target: str,
    mode: str = "overview",
    period: str = "monthly",
    user_message: str = "",
    include_keyboard: bool = True,
    only_remaining_pages: bool = False,
    report_lang: str | None = None,
) -> bool:
    """Send monthly trip summary visuals to Telegram.

    overview -> first page only, with inline buttons.
    all -> all pages or remaining pages.
    single -> same as overview but no NLP intent text.
    """
    target = str(target or "").strip()
    if not target:
        return False

    report_lang = "en" if str(report_lang or "").lower().startswith("en") else ("tr" if str(report_lang or "").lower().startswith("tr") else get_telegram_report_language(data, user_message))
    normalized_period = str(period or "monthly").strip().lower()
    payload, png_paths = await async_build_monthly_trip_visual_pages(hass, data, report_lang=report_lang, period=normalized_period)
    if not payload or not png_paths:
        if normalized_period in {"today", "daily", "day"}:
            message = "There is no recorded trip data for today yet." if report_lang == "en" else "Bugün için kayıtlı sürüş verisi henüz yok."
        elif normalized_period in {"weekly", "week"}:
            message = "There is no recorded trip data for this week yet." if report_lang == "en" else "Bu hafta için kayıtlı sürüş verisi henüz yok."
        else:
            message = "There is no recorded trip data for this month yet." if report_lang == "en" else "Bu ay için kayıtlı sürüş verisi henüz yok."
        await async_telegram_send_message(hass, data, target=target, parse_mode="plain_text", message=message)
        return True

    month_key = str(payload.get("month_key") or datetime.now().strftime("%Y-%m"))
    if normalized_period in {"today", "daily", "day"}:
        caption_base = f"📈 {month_key} today's trip summary" if report_lang == "en" else f"📈 {month_key} bugünkü sürüş özeti"
    elif normalized_period in {"weekly", "week"}:
        caption_base = f"📈 {month_key} weekly trip summary" if report_lang == "en" else f"📈 {month_key} haftalık sürüş özeti"
    else:
        month_caption = format_month_label_for_language(month_key, report_lang, fallback=("Monthly Trip Summary" if report_lang == "en" else "Aylık Sürüş Özeti"))
        caption_base = f"📈 {month_caption} monthly trip summary" if report_lang == "en" else f"📈 {month_caption} aylık sürüş özeti"

    if mode in {"overview", "single"}:
        caption = caption_base
        if len(png_paths) > 1:
            caption = f"{caption} (1/{len(png_paths)})"
        await async_telegram_send_photo(
            hass,
            data,
            target=target,
            file_path=png_paths[0],
            caption=caption,
            inline_keyboard=build_trip_summary_inline_keyboard(report_lang) if include_keyboard else None,
        )
        return True

    if mode == "all":
        selected_paths = png_paths[1:] if only_remaining_pages and len(png_paths) > 1 else png_paths
        if only_remaining_pages and len(png_paths) <= 1:
            message = "There are no additional monthly trip pages." if report_lang == "en" else "Ek aylık sürüş sayfası yok."
            await async_telegram_send_message(hass, data, target=target, parse_mode="plain_text", message=message)
            return True
        total = len(png_paths)
        for idx, png_path in enumerate(selected_paths, start=(2 if only_remaining_pages and len(png_paths) > 1 else 1)):
            caption = f"{caption_base} ({idx}/{total})" if total > 1 else caption_base
            await async_telegram_send_photo(
                hass,
                data,
                target=target,
                file_path=png_path,
                caption=caption,
            )
        return True

    return False


async def async_handle_trip_summary_request(
    hass: HomeAssistant,
    data: dict[str, Any],
    *,
    user_message: str,
    telegram_target: str | None,
    send_telegram: bool = True,
) -> bool:
    """Handle monthly trip summary commands/intents and send Telegram visuals."""
    target = str(telegram_target or "").strip()
    action, action_lang = parse_trip_action_and_lang(user_message, get_telegram_report_language(data, user_message))

    if action == "/triplast" or is_trip_last_command(user_message):
        if send_telegram and target:
            await async_send_last_trip_report_visual(hass, data, target=target, user_message=user_message, report_lang=action_lang)
        return True

    if action == "/triptoday" or is_trip_today_command(user_message):
        if send_telegram and target:
            await async_send_trip_summary_visual_with_options(
                hass, data, target=target, mode="all", period="today", user_message=user_message, include_keyboard=False, report_lang=action_lang
            )
        return True

    if action == "/tripweek" or is_trip_week_command(user_message):
        if send_telegram and target:
            await async_send_trip_summary_visual_with_options(
                hass, data, target=target, mode="all", period="weekly", user_message=user_message, include_keyboard=False, report_lang=action_lang
            )
        return True

    if action == "/tripall" or is_trip_all_command(user_message):
        if send_telegram and target:
            await async_send_trip_summary_visual_with_options(
                hass, data, target=target, mode="all", user_message=user_message, include_keyboard=False, report_lang=action_lang,
                only_remaining_pages=(action == "/tripall" and ("_" in user_message or "|" in user_message)),
            )
        return True

    if action == "/single" or is_trip_single_command(user_message):
        if send_telegram and target:
            await async_send_trip_summary_visual_with_options(
                hass, data, target=target, mode="single", user_message=user_message, include_keyboard=True, report_lang=action_lang
            )
        return True

    llm_intent = await async_detect_trip_request_intent_with_llm(hass, data, user_message)
    if llm_intent == "last_trip_report":
        if send_telegram and target:
            await async_send_last_trip_report_visual(hass, data, target=target, user_message=user_message)
        return True

    if llm_intent == "trip_monthly_all":
        if send_telegram and target:
            await async_send_trip_summary_visual_with_options(
                hass, data, target=target, mode="all", user_message=user_message, include_keyboard=False
            )
        return True

    is_trip_summary = llm_intent == "trip_monthly_summary" or is_direct_trip_summary_command(user_message) or should_answer_trip_summary_question(user_message)
    if not is_trip_summary:
        return False

    if send_telegram and target:
        await async_send_trip_summary_visual_with_options(
            hass, data, target=target, mode="overview", user_message=user_message, include_keyboard=True
        )
    else:
        payload = build_monthly_trip_summary_payload(hass)
        report_lang = get_telegram_report_language(data, user_message)
        message = (
            build_monthly_trip_answer_text(payload, lang=report_lang)
            if payload
            else ("There is no recorded trip data for this month yet." if report_lang == "en" else "Bu ay için kayıtlı sürüş verisi henüz yok.")
        )
        await async_create_persistent_notification(
            hass,
            title="Tesla AI - Trip Summary",
            message=message,
            notification_id="pom_tesla_report_trip_summary_answer",
        )
    return True




def get_periodic_report_state_path(hass: HomeAssistant) -> Path:
    """Return the persistent JSON path for scheduled Telegram report state."""
    return Path(hass.config.path(PERIODIC_REPORT_STATE_FILENAME))


def load_periodic_report_state(hass: HomeAssistant) -> dict[str, Any]:
    """Load last-sent keys for weekly/monthly scheduled Telegram reports."""
    path = get_periodic_report_state_path(hass)
    default = {
        "last_weekly_trip_report_key": "",
        "last_monthly_trip_report_key": "",
        "last_weekly_charge_report_key": "",
        "last_monthly_charge_report_key": "",
    }
    try:
        if not path.exists():
            return dict(default)
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return dict(default)
        out = dict(default)
        for key in out:
            out[key] = str(payload.get(key) or "").strip()
        return out
    except Exception:
        _LOGGER.exception("Could not load POM scheduled report state")
        return dict(default)


def save_periodic_report_state(hass: HomeAssistant, payload: dict[str, Any]) -> None:
    """Persist last-sent keys for scheduled Telegram reports."""
    path = get_periodic_report_state_path(hass)
    normalized = {
        "last_weekly_trip_report_key": str(payload.get("last_weekly_trip_report_key") or "").strip(),
        "last_monthly_trip_report_key": str(payload.get("last_monthly_trip_report_key") or "").strip(),
        "last_weekly_charge_report_key": str(payload.get("last_weekly_charge_report_key") or "").strip(),
        "last_monthly_charge_report_key": str(payload.get("last_monthly_charge_report_key") or "").strip(),
    }
    path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")


def _periodic_week_key(now: datetime | None = None) -> str:
    now = now or datetime.now()
    iso = now.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def _periodic_week_label(now: datetime | None = None, lang: str = "tr") -> str:
    now = now or datetime.now()
    monday = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    sunday = monday + timedelta(days=6)
    if str(lang or "tr").lower().startswith("en"):
        return f"Weekly · {monday.strftime('%d %b')} - {sunday.strftime('%d %b %Y')}"
    return f"Haftalık · {monday.strftime('%d.%m')} - {sunday.strftime('%d.%m.%Y')}"


def _record_datetime_for_period(raw: dict[str, Any]) -> datetime | None:
    """Parse record timestamps used by trip and charge ledgers."""
    candidates = [raw.get("created_at"), raw.get("finished_at_iso"), raw.get("display_at"), raw.get("report_date"), raw.get("date")]
    for value in candidates:
        text = str(value or "").strip()
        if not text:
            continue
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            pass
        for fmt in ("%d.%m.%Y %H:%M", "%d.%m.%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
            try:
                return datetime.strptime(text, fmt)
            except Exception:
                continue
    return None


def _current_today_trip_records(hass: HomeAssistant) -> list[dict[str, Any]]:
    now = datetime.now()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    ledger = load_trip_monthly_ledger(hass)
    records: list[dict[str, Any]] = []
    for item in list(ledger.get("records") or []):
        if not isinstance(item, dict):
            continue
        if is_manual_tracking_trip_record(item):
            continue
        dt = _record_datetime_for_period(item)
        if dt and start <= dt < end:
            records.append(item)
    records.sort(key=lambda item: str(item.get("created_at") or item.get("display_at") or ""), reverse=True)
    return records


def _today_trip_label(now: datetime | None = None, lang: str = "tr") -> str:
    now = now or datetime.now()
    if str(lang or "tr").lower().startswith("en"):
        return f"Today · {now.strftime('%d %b %Y')}"
    return f"Bugün · {now.strftime('%d.%m.%Y')}"


def build_today_trip_summary_payload(hass: HomeAssistant, *, lang: str = "tr") -> dict[str, Any] | None:
    now = datetime.now()
    return _build_trip_summary_payload_from_records(
        hass,
        _current_today_trip_records(hass),
        period_key=now.strftime("%Y-%m-%d"),
        period_label=_today_trip_label(now, lang),
    )


def _current_week_trip_records(hass: HomeAssistant) -> list[dict[str, Any]]:
    now = datetime.now()
    start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=7)
    ledger = load_trip_monthly_ledger(hass)
    records: list[dict[str, Any]] = []
    for item in list(ledger.get("records") or []):
        if not isinstance(item, dict):
            continue
        if is_manual_tracking_trip_record(item):
            continue
        dt = _record_datetime_for_period(item)
        if dt and start <= dt < end:
            records.append(item)
    records.sort(key=lambda item: str(item.get("created_at") or item.get("display_at") or ""), reverse=True)
    return records


def _build_trip_summary_payload_from_records(hass: HomeAssistant, records: list[dict[str, Any]], *, period_key: str, period_label: str) -> dict[str, Any] | None:
    if not records:
        return None
    total_distance = sum(safe_float(item.get("trip_km"), 0.0) for item in records)
    total_energy = sum(safe_float(item.get("used_kwh"), 0.0) for item in records)
    total_cost = sum(safe_float(item.get("total_cost"), 0.0) for item in records)
    total_duration_minutes = sum(safe_float(item.get("duration_minutes"), 0.0) for item in records)
    avg_consumption = (total_energy / total_distance * 100.0) if total_distance > 0 else 0.0
    score_values = [safe_float(item.get("driving_score"), 0.0) for item in records if safe_float(item.get("driving_score"), 0.0) > 0]
    avg_driving_score = (sum(score_values) / len(score_values)) if score_values else 0.0
    currency_label = get_report_currency(get_first_entry_config(hass) or {})
    return {
        "month_key": period_label or period_key,
        "currency_label": currency_label,
        "summary": {
            "count": len(records),
            "total_distance_km": round(total_distance, 3),
            "total_energy_kwh": round(total_energy, 3),
            "total_cost": round(total_cost, 2),
            "total_duration_minutes": round(total_duration_minutes, 2),
            "average_consumption_kwh_100km": round(avg_consumption, 3),
            "average_driving_score": round(avg_driving_score, 1),
        },
        "records": records,
    }


def build_weekly_trip_summary_payload(hass: HomeAssistant, *, lang: str = "tr") -> dict[str, Any] | None:
    now = datetime.now()
    return _build_trip_summary_payload_from_records(
        hass,
        _current_week_trip_records(hass),
        period_key=_periodic_week_key(now),
        period_label=_periodic_week_label(now, lang),
    )


def _current_week_charge_records(hass: HomeAssistant) -> list[dict[str, Any]]:
    now = datetime.now()
    start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=7)
    ledger = load_charge_cost_ledger(hass)
    records: list[dict[str, Any]] = []
    for item in list(ledger.get("records") or []):
        if not isinstance(item, dict):
            continue
        dt = _record_datetime_for_period(item)
        if dt and start <= dt < end:
            records.append(item)
    records.sort(key=lambda item: str(item.get("created_at") or item.get("finished_at_iso") or item.get("display_at") or ""), reverse=True)
    return records


def build_weekly_charge_cost_visual_payload(hass: HomeAssistant, *, lang: str = "tr") -> dict[str, Any] | None:
    records = _current_week_charge_records(hass)
    if not records:
        return None
    summary = summarize_charge_cost_records(records)
    currency_label = get_report_currency(get_first_entry_config(hass) or {})
    now = datetime.now()
    return {
        "month_key": _periodic_week_label(now, lang),
        "month_label": _periodic_week_label(now, lang),
        "report_language": lang,
        "currency_label": currency_label,
        "summary": summary,
        "records": records,
    }


async def async_send_trip_periodic_visual_report(
    hass: HomeAssistant,
    data: dict[str, Any],
    *,
    target: str,
    period: str,
) -> list[str]:
    """Render and send weekly/monthly trip summary visuals to Telegram."""
    target = str(target or "").strip()
    if not target:
        return []
    report_lang = get_report_language(data)
    if str(period or "monthly") == "weekly":
        payload = build_weekly_trip_summary_payload(hass, lang=report_lang)
        period_caption = "weekly trip summary" if report_lang == "en" else "haftalık sürüş özeti"
        base_name = f"weekly_trip_summary_{_periodic_week_key()}_{report_lang}.png"
    else:
        payload = build_monthly_trip_summary_payload(hass)
        period_caption = "monthly trip summary" if report_lang == "en" else "aylık sürüş özeti"
        base_name = f"monthly_trip_summary_{datetime.now().strftime('%Y-%m')}_{report_lang}.png"
    if not payload:
        return []
    base_path = f"/config/www/pom_tesla_report/{base_name}"
    png_paths = await hass.async_add_executor_job(render_monthly_trip_report_pngs, payload, base_path, report_lang)
    total_pages = len(png_paths)
    for page_index, png_path in enumerate(png_paths, start=1):
        caption = f"📈 {payload.get('month_key') or ''} {period_caption}".strip()
        if total_pages > 1:
            caption = f"{caption} ({page_index}/{total_pages})"
        await async_telegram_send_photo(hass, data, target=target, file_path=png_path, caption=caption)
    return png_paths


async def async_send_charge_periodic_visual_report(
    hass: HomeAssistant,
    data: dict[str, Any],
    *,
    target: str,
    period: str,
) -> list[str]:
    """Render and send weekly/monthly charging summary visuals to Telegram."""
    target = str(target or "").strip()
    if not target:
        return []
    report_lang = get_report_language(data)
    if str(period or "monthly") == "weekly":
        payload = build_weekly_charge_cost_visual_payload(hass, lang=report_lang)
        period_caption = "weekly charging summary" if report_lang == "en" else "haftalık şarj özeti"
        base_name = f"weekly_charge_summary_{_periodic_week_key()}_{report_lang}.png"
    else:
        return await async_send_monthly_charge_cost_visual_report(hass, data, target=target)
    if not payload:
        return []
    base_path = f"/config/www/pom_tesla_report/{base_name}"
    png_paths = await hass.async_add_executor_job(render_monthly_charge_cost_report_pngs, payload, base_path, report_lang)
    total_pages = len(png_paths)
    for page_index, png_path in enumerate(png_paths, start=1):
        caption = f"📊 {payload.get('month_key') or ''} {period_caption}".strip()
        if total_pages > 1:
            caption = f"{caption} ({page_index}/{total_pages})"
        await async_telegram_send_photo(hass, data, target=target, file_path=png_path, caption=caption)
    return png_paths


async def async_send_periodic_reports_if_due(hass: HomeAssistant, data: dict[str, Any]) -> None:
    """Send enabled weekly/monthly Trip and Charge Telegram summaries at 23:55."""
    now = datetime.now()
    if now.hour != PERIODIC_REPORT_HOUR or now.minute != PERIODIC_REPORT_MINUTE:
        return
    target = str(data.get(CONF_AI_TELEGRAM_TARGET) or data.get(CONF_TELEGRAM_TARGET) or data.get(CONF_AI_TELEGRAM_LISTENER_CHAT_ID) or "").strip()
    if not target:
        return
    state = load_periodic_report_state(hass)
    changed = False
    weekly_due = now.weekday() == PERIODIC_REPORT_WEEKDAY
    monthly_due = (now + timedelta(days=1)).month != now.month
    week_key = _periodic_week_key(now)
    month_key = now.strftime("%Y-%m")

    async def _send_guarded(label: str, key_name: str, key_value: str, coro_factory) -> None:
        nonlocal changed
        if str(state.get(key_name) or "") == key_value:
            return
        try:
            sent_paths = await coro_factory()
            # Mark as handled even when there is no data, preventing repeated empty sends within the same due minute.
            state[key_name] = key_value
            changed = True
            _LOGGER.info("POM scheduled Telegram report handled. label=%s key=%s sent=%s", label, key_value, len(sent_paths or []))
        except Exception:
            _LOGGER.exception("POM scheduled Telegram report failed. label=%s key=%s", label, key_value)

    if weekly_due and _to_bool(data.get(CONF_TELEGRAM_WEEKLY_TRIP_REPORT_ENABLED), DEFAULT_TELEGRAM_WEEKLY_TRIP_REPORT_ENABLED):
        await _send_guarded("weekly_trip", "last_weekly_trip_report_key", week_key, lambda: async_send_trip_periodic_visual_report(hass, data, target=target, period="weekly"))
    if monthly_due and _to_bool(data.get(CONF_TELEGRAM_MONTHLY_TRIP_REPORT_ENABLED), DEFAULT_TELEGRAM_MONTHLY_TRIP_REPORT_ENABLED):
        await _send_guarded("monthly_trip", "last_monthly_trip_report_key", month_key, lambda: async_send_trip_periodic_visual_report(hass, data, target=target, period="monthly"))
    if weekly_due and _to_bool(data.get(CONF_TELEGRAM_WEEKLY_CHARGE_REPORT_ENABLED), DEFAULT_TELEGRAM_WEEKLY_CHARGE_REPORT_ENABLED):
        await _send_guarded("weekly_charge", "last_weekly_charge_report_key", week_key, lambda: async_send_charge_periodic_visual_report(hass, data, target=target, period="weekly"))
    if monthly_due and _to_bool(data.get(CONF_TELEGRAM_MONTHLY_CHARGE_REPORT_ENABLED), DEFAULT_TELEGRAM_MONTHLY_CHARGE_REPORT_ENABLED):
        await _send_guarded("monthly_charge", "last_monthly_charge_report_key", month_key, lambda: async_send_charge_periodic_visual_report(hass, data, target=target, period="monthly"))

    if changed:
        save_periodic_report_state(hass, state)

async def async_send_monthly_charge_cost_report_if_due(
    hass: HomeAssistant,
    data: dict[str, Any],
) -> None:
    """Send the current month's charging cost summary at 23:55 on the month's last day."""
    if not _to_bool(data.get(CONF_TELEGRAM_MONTHLY_CHARGE_REPORT_ENABLED), DEFAULT_TELEGRAM_MONTHLY_CHARGE_REPORT_ENABLED):
        return
    now = datetime.now()
    if now.hour != CHARGE_COST_MONTHLY_REPORT_HOUR or now.minute != CHARGE_COST_MONTHLY_REPORT_MINUTE:
        return
    if (now + timedelta(days=1)).month == now.month:
        return

    month_key = now.strftime("%Y-%m")
    ledger = load_charge_cost_ledger(hass)
    if str(ledger.get("last_monthly_report_key") or "") == month_key:
        return

    answer = build_current_month_charge_cost_answer(hass, lang=get_report_language(data))
    if not answer:
        ledger["last_monthly_report_key"] = month_key
        save_charge_cost_ledger(hass, ledger)
        return

    target = str(data.get(CONF_AI_TELEGRAM_TARGET) or data.get(CONF_TELEGRAM_TARGET) or "").strip()
    if not target:
        return

    report_lang = get_report_language(data)
    title = "📊 Monthly charging cost report" if report_lang == "en" else "📊 Aylık şarj maliyeti raporu"
    await async_telegram_send_message(
        hass,
        data,
        target=target,
        parse_mode="plain_text",
        message=f"{title}\n\n{answer}",
    )
    await async_send_monthly_charge_cost_visual_report(
        hass,
        data,
        target=target,
        month_key=month_key,
    )
    ledger["last_monthly_report_key"] = month_key
    save_charge_cost_ledger(hass, ledger)


def build_charging_report_data_from_state(
    hass: HomeAssistant,
    data: dict[str, Any],
    state: dict[str, Any] | None = None,
    *,
    test_mode: bool = False,
    manual_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build renderer data for the charging PNG report."""
    state = state or get_charging_report_state(hass)
    overrides = manual_overrides or {}
    entities = get_charging_report_entities(hass, data)
    supercharger_price, zes_price, astor_price = get_charging_tariff_prices(hass, data)

    now = datetime.now()
    samples = list(state.get("samples") or [])
    if not samples and test_mode:
        # Pleasant test curve so the service can be previewed before a real charge session.
        samples = [
            {"minute": 0, "power_kw": 62}, {"minute": 5, "power_kw": 74},
            {"minute": 10, "power_kw": 72}, {"minute": 20, "power_kw": 64},
            {"minute": 30, "power_kw": 55}, {"minute": 40, "power_kw": 44},
            {"minute": 50, "power_kw": 31}, {"minute": 60, "power_kw": 19},
            {"minute": 70, "power_kw": 9},
        ]

    added_entity = entities.get("charge_energy_added")
    current_added = get_float_state(hass, added_entity, 0.0)
    added_kwh = safe_float(overrides.get("added_kwh"), 0.0) if "added_kwh" in overrides else current_added
    if added_kwh <= 0:
        added_kwh = safe_float(state.get("last_added_kwh"), 0.0)
    if added_kwh <= 0 and test_mode:
        added_kwh = 38.4

    range_km = safe_float(overrides.get("battery_range_km"), 0.0) if "battery_range_km" in overrides else get_float_state(hass, entities.get("battery_range"), 0.0)
    if range_km <= 0:
        range_km = safe_float(state.get("last_battery_range_km"), 0.0)
    if range_km <= 0 and test_mode:
        range_km = 412.0

    estimate_km = safe_float(overrides.get("battery_range_estimate_km"), 0.0) if "battery_range_estimate_km" in overrides else get_float_state(hass, entities.get("battery_range_estimate"), 0.0)
    if estimate_km <= 0:
        estimate_km = safe_float(state.get("last_battery_range_estimate_km"), 0.0)
    if estimate_km <= 0 and test_mode:
        estimate_km = 395.0

    if "duration_minutes" in overrides:
        duration_minutes = safe_float(overrides.get("duration_minutes"), 0.0)
    else:
        duration_minutes = safe_float(state.get("duration_minutes"), 0.0)
        if duration_minutes <= 0 and state.get("start_ts"):
            duration_minutes = max(0.0, (now.timestamp() - safe_float(state.get("start_ts"), now.timestamp())) / 60.0)
    if duration_minutes <= 0 and samples:
        duration_minutes = max(float(item.get("minute", 0)) for item in samples if isinstance(item, dict))
    if duration_minutes <= 0 and test_mode:
        duration_minutes = 84.0

    powers = [safe_float(item.get("power_kw"), 0.0) for item in samples if isinstance(item, dict)]
    peak_power = max(powers, default=get_float_state(hass, entities.get("charger_power"), 0.0))
    if peak_power <= 0 and test_mode:
        peak_power = 74.0
    average_power = (sum(powers) / len(powers)) if powers else ((added_kwh / (duration_minutes / 60.0)) if duration_minutes > 0 else 0.0)

    finished_at = str(state.get("finished_at") or now.strftime("%d %B %Y · %H:%M"))
    location_label = str(overrides.get("location_label") or "").strip() or get_short_cached_reverse_geocode_label(hass)

    report_data = {
        "test_mode": test_mode,
        "currency_label": get_report_currency(data),
        "finished_at": finished_at,
        "meta": finished_at,
        "added_kwh": added_kwh,
        "battery_range_km": range_km,
        "battery_range_estimate_km": estimate_km,
        "duration_minutes": duration_minutes,
        "peak_power_kw": peak_power,
        "average_power_kw": average_power,
        "power_samples": samples,
        "supercharger_price": supercharger_price,
        "zes_price": zes_price,
        "astor_price": astor_price,
        "provider_presets": get_effective_charge_provider_presets(data, max_items=3),
        "location_label": location_label,
        "entities": entities,
    }

    for key in ("actual_provider", "actual_price_per_kwh", "actual_total_cost", "currency_label", "actual_currency"):
        if key in overrides:
            report_data[key] = overrides.get(key)
    if str(report_data.get("actual_currency") or "").strip() and not str(report_data.get("currency_label") or "").strip():
        report_data["currency_label"] = str(report_data.get("actual_currency") or "").strip()

    return report_data


async def render_and_send_charging_report(
    hass: HomeAssistant,
    data: dict[str, Any],
    *,
    state: dict[str, Any] | None = None,
    send_telegram: bool = True,
    telegram_target: str | None = None,
    test_mode: bool = False,
    message_prefix: str = "",
    manual_overrides: dict[str, Any] | None = None,
) -> tuple[str, dict[str, Any]]:
    """Render the charging PNG report and optionally send it to Telegram."""
    report_data = build_charging_report_data_from_state(
        hass,
        data,
        state,
        test_mode=test_mode,
        manual_overrides=manual_overrides,
    )
    output_path = DEFAULT_CHARGING_REPORT_IMAGE_OUTPUT_PATH
    png_path = await hass.async_add_executor_job(render_charging_report_png, report_data, output_path, get_report_language(data))

    target = str(telegram_target or data.get(CONF_AI_TELEGRAM_TARGET) or data.get(CONF_AI_TELEGRAM_LISTENER_CHAT_ID) or data.get(CONF_TELEGRAM_TARGET) or "").strip()
    if send_telegram and target:
        caption = "⚡ POM Charging Report" if get_report_language(data) == "en" else "⚡ POM Şarj Raporu"
        if message_prefix:
            caption = f"{message_prefix}\n{caption}"
        if test_mode:
            caption = f"🧪 TEST · {caption}"
        await async_telegram_send_photo(
            hass,
            data,
            target=target,
            file_path=png_path,
            caption=caption,
        )

    return png_path, report_data


def get_pending_charging_report_state(hass: HomeAssistant) -> dict[str, Any]:
    """Return mutable state for the interactive Telegram charging report flow."""
    return hass.data.setdefault(DOMAIN, {}).setdefault("charging_report_pending", {})


def get_charging_report_telegram_target(data: dict[str, Any]) -> str:
    """Return the best Telegram target for charging report prompts."""
    return str(
        data.get(CONF_AI_TELEGRAM_TARGET)
        or data.get(CONF_AI_TELEGRAM_LISTENER_CHAT_ID)
        or data.get(CONF_TELEGRAM_TARGET)
        or ""
    ).strip()


def clone_charging_state_for_pending(state: dict[str, Any]) -> dict[str, Any]:
    """Create a safe copy of a completed charging state for delayed report rendering."""
    try:
        return copy.deepcopy(state)
    except Exception:
        return dict(state)




def get_manual_charge_provider_presets(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return manually configured extra charging provider presets."""
    raw = data.get(CONF_CHARGE_PROVIDER_PRESETS, DEFAULT_CHARGE_PROVIDER_PRESETS)
    if not isinstance(raw, list):
        return []
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        price = safe_float(item.get("unit_price", item.get("price", 0.0)), 0.0)
        if not name or price <= 0:
            continue
        key = normalize_text_for_match(name)
        if key in seen:
            continue
        seen.add(key)
        result.append({"name": name, "unit_price": round(price, 4), "currency": str(item.get("currency") or item.get("currency_label") or get_report_currency(data)).strip() or get_report_currency(data)})
    return result




def get_effective_charge_provider_presets(data: dict[str, Any], *, max_items: int | None = None) -> list[dict[str, Any]]:
    """Return charging provider presets used by visual report cost cards."""
    presets = get_manual_charge_provider_presets(data)
    if not presets:
        currency = get_report_currency(data)
        presets = [
            {"name": "Supercharger", "unit_price": safe_float(data.get(CONF_SUPERCHARGER_PRICE), DEFAULT_SUPERCHARGER_PRICE), "currency": currency},
            {"name": "ZES", "unit_price": safe_float(data.get(CONF_ZES_PRICE), DEFAULT_ZES_PRICE), "currency": currency},
            {"name": "Astor", "unit_price": safe_float(data.get(CONF_ASTOR_PRICE), DEFAULT_ASTOR_PRICE), "currency": currency},
        ]
    return presets[:max_items] if max_items else presets


def get_trip_cost_presets(data: dict[str, Any], used_kwh: float) -> list[dict[str, Any]]:
    """Return up to three cost-card presets for trip visual reports."""
    return [
        {
            "name": item.get("name"),
            "unit_price": round(safe_float(item.get("unit_price", item.get("price")), 0.0), 2),
            "currency": str(item.get("currency") or item.get("currency_label") or get_report_currency(data)).strip() or get_report_currency(data),
            "cost": round(used_kwh * safe_float(item.get("unit_price", item.get("price")), 0.0), 2),
        }
        for item in get_effective_charge_provider_presets(data, max_items=3)
    ]

def charge_text(data: dict[str, Any] | None, key: str) -> str:
    """Return Telegram charge-flow text in the global app language."""
    lang = get_report_language(data or {})
    en = lang == "en"
    texts = {
        "manual_label": "Manual" if en else "Manuel",
        "abroad_label": "Abroad" if en else "Yurt dışı",
        "provider_prompt": "Charging has finished.\n\nHow should this charging cost be entered?" if en else "Şarj tamamlandı.\n\nBu şarj maliyeti nasıl girilsin?",
        "manual_intro": "Manual entry selected." if en else "Manuel giriş seçtin.",
        "abroad_intro": "Abroad charging selected." if en else "Yurt dışı şarj seçtin.",
        "cancelled": "Charging report creation was cancelled." if en else "Şarj raporu oluşturma iptal edildi.",
        "inactive": "This charging report selection is no longer active." if en else "Bu şarj raporu seçimi artık aktif değil.",
        "not_understood_price": "I could not understand this as a unit price. Please enter only the unit price. Example: 12.49" if en else "Bunu birim fiyat olarak anlayamadım. Lütfen sadece birim fiyat yaz. Örnek: 12.49",
        "not_understood_total": "I could not understand this as the total amount. Please enter the total amount you paid. Example: 480" if en else "Bunu toplam tutar olarak anlayamadım. Lütfen toplam ödediğin tutarı yaz. Örnek: 480",
        "not_understood_currency": "I could not understand the currency. Please enter a currency code such as EUR, BGN, USD or TRY." if en else "Para birimini anlayamadım. Lütfen EUR, BGN, USD veya TRY gibi bir para birimi kodu yaz.",
        "fallback_done": "Charging report was created with the saved/default values." if en else "Şarj raporu kayıtlı/varsayılan değerlerle oluşturuldu.",
        "manual_done": "Charging report was created with the manual cost you confirmed." if en else "Şarj raporu onayladığın manuel maliyetle oluşturuldu.",
        "abroad_done": "Charging report was created with the abroad cost and currency you confirmed." if en else "Şarj raporu onayladığın yurt dışı maliyet ve para birimiyle oluşturuldu.",
        "restart": "Let's start over." if en else "Baştan başlayalım.",
    }
    return texts.get(key, key)


def build_charging_provider_keyboard(data: dict[str, Any], pending: dict[str, Any]) -> list[str]:
    """Build the simplified Telegram charging choice keyboard.

    alpha64: fixed provider choices (ZES/Supercharger/Astor), manual provider presets,
    and skip are intentionally removed from the first prompt. The flow now offers
    only Manual and Abroad, localized by the global application language.
    """
    return (
        f"{charge_text(data, 'manual_label')}:/pom_charge_provider_manual, "
        f"{charge_text(data, 'abroad_label')}:/pom_charge_provider_abroad"
    ).split("\n")

def provider_price_for_charging_report(hass: HomeAssistant, data: dict[str, Any], provider: str) -> tuple[str, float]:
    """Return display label and selected-currency/kWh price for a selected provider."""
    supercharger_price, zes_price, astor_price = get_charging_tariff_prices(hass, data)
    provider_key = normalize_text_for_match(provider)
    if provider_key in {"zes", "ze", "z es"}:
        return "ZES", zes_price
    if provider_key in {"supercharger", "tesla", "tesla supercharger", "super"}:
        return "Supercharger", supercharger_price
    if provider_key in {"astor", "astor sarj", "astor şarj"}:
        return "Astor", astor_price
    return provider.strip() or "Diğer", 0.0


def parse_charging_money_value(message: str) -> float | None:
    """Parse the first money-like numeric value from a Telegram answer.

    The current question decides meaning, so values such as `12.49`, `12,49`,
    `12.49 TL`, `12.49 EUR/kWh` or even `12.49kwh` all become 12.49.
    """
    raw = str(message or "").strip().lower()
    if not raw:
        return None
    cleaned = raw.replace("â‚º", " ").replace(",", ".")
    match = re.search(r"\d+(?:\.\d+)?", cleaned)
    if not match:
        return None
    try:
        value = float(match.group(0))
    except (TypeError, ValueError):
        return None
    if value <= 0:
        return None
    return value


def build_other_charging_overrides_from_pending(pending: dict[str, Any]) -> dict[str, Any] | None:
    """Build manual overrides after the user confirmed custom charging cost."""
    price = safe_float(pending.get("actual_price_per_kwh"), 0.0)
    total = safe_float(pending.get("actual_total_cost"), 0.0)
    if price <= 0 or total <= 0:
        return None
    added_kwh = total / price
    if added_kwh <= 0 or added_kwh > 300:
        return None
    currency_label = str(pending.get("actual_currency") or "").strip()
    return {
        "actual_provider": str(pending.get("provider") or "Diğer"),
        "actual_price_per_kwh": round(price, 4),
        "actual_total_cost": round(total, 2),
        "added_kwh": round(added_kwh, 3),
        **({"currency_label": currency_label, "actual_currency": currency_label} if currency_label else {}),
    }


async def async_send_other_charging_price_prompt(hass: HomeAssistant, target: str, data: dict[str, Any] | None = None, *, flow_kind: str = "manual") -> None:
    """Ask for custom currency/kWh value."""
    data = data or get_first_entry_config(hass) or {}
    lang = get_report_language(data)
    en = lang == "en"
    currency_label = get_report_currency(data)
    intro = charge_text(data, "abroad_intro" if flow_kind == "abroad" else "manual_intro")
    if en:
        question = "What was the unit price per kWh?\nExample: 12.49\n\nIf it is wrong, I will ask again. You can type 'cancel' or 'skip'."
    elif flow_kind == "abroad":
        question = "kWh başına birim fiyat neydi?\nÖrnek: 12.49\n\nYanlış yazarsan tekrar soracağım. İstersen 'iptal' veya 'atla' yazabilirsin."
    else:
        question = f"Kaç {currency_label}/kWh ile şarj ettin?\nÖrnek: 12.49\n\nYanlış yazarsan tekrar soracağım. İstersen 'iptal' veya 'atla' yazabilirsin."
    message = f"{intro}\n\n{question}"
    await hass.services.async_call(
        "telegram_bot",
        "send_message",
        {"target": target, "parse_mode": "plain_text", "message": message},
        blocking=True,
    )


async def async_send_other_charging_total_prompt(hass: HomeAssistant, target: str, price: float, data: dict[str, Any] | None = None, *, flow_kind: str = "manual") -> None:
    """Ask for custom total currency value."""
    data = data or get_first_entry_config(hass) or {}
    en = get_report_language(data) == "en"
    currency_label = get_report_currency(data)
    if en:
        unit_text = f"{price:.2f}/kWh" if flow_kind == "abroad" else f"{price:.2f} {currency_label}/kWh"
        message = (
            f"I understood the unit price as {unit_text}.\n\n"
            f"How much did you pay in total?\n"
            "Example: 480\n\n"
            "If it is wrong, I will ask again. You can type 'cancel' or 'skip'."
        )
    else:
        unit_text = f"{price:.2f}/kWh" if flow_kind == "abroad" else f"{price:.2f} {currency_label}/kWh"
        total_question = "Toplam ödeme tutarı kaçtı?" if flow_kind == "abroad" else f"Toplam kaç {currency_label} tuttu?"
        message = (
            f"Birim fiyatı {unit_text} olarak aldım.\n\n"
            f"{total_question}\n"
            "Örnek: 480\n\n"
            "Yanlış yazarsan tekrar soracağım. İstersen 'iptal' veya 'atla' yazabilirsin."
        )
    await hass.services.async_call(
        "telegram_bot",
        "send_message",
        {"target": target, "parse_mode": "plain_text", "message": message},
        blocking=True,
    )


def parse_charge_currency_code(message: str) -> str | None:
    """Parse a short currency code from a Telegram reply."""
    raw = str(message or "").strip().upper()
    if not raw:
        return None
    raw = raw.replace("₺", " TL ").replace("€", " EUR ").replace("$", " USD ").replace("£", " GBP ")
    aliases = {"TURKISH LIRA": "TRY", "LIRA": "TRY", "TL": "TL", "TRY": "TRY", "LEV": "BGN", "LEVA": "BGN"}
    normalized = re.sub(r"[^A-Z]+", " ", raw).strip()
    if normalized in aliases:
        return aliases[normalized]
    for part in normalized.split():
        if part in aliases:
            return aliases[part]
        if 2 <= len(part) <= 5:
            return part
    return None


async def async_send_other_charging_currency_prompt(hass: HomeAssistant, target: str, data: dict[str, Any] | None = None) -> None:
    """Ask for the currency in Abroad charging flow."""
    data = data or get_first_entry_config(hass) or {}
    if get_report_language(data) == "en":
        message = "Which currency was this payment in?\nExample: EUR, BGN, USD or TRY"
    else:
        message = "Bu ödeme hangi para birimindeydi?\nÖrnek: EUR, BGN, USD veya TRY"
    await hass.services.async_call(
        "telegram_bot",
        "send_message",
        {"target": target, "parse_mode": "plain_text", "message": message},
        blocking=True,
    )


async def async_send_other_charging_summary_prompt(hass: HomeAssistant, pending: dict[str, Any], target: str, data: dict[str, Any] | None = None) -> None:
    """Show custom cost summary and ask for final confirmation before rendering PNG."""
    data = data or get_first_entry_config(hass) or {}
    en = get_report_language(data) == "en"
    overrides = build_other_charging_overrides_from_pending(pending)
    if not overrides:
        await hass.services.async_call(
            "telegram_bot",
            "send_message",
            {"target": target, "parse_mode": "plain_text", "message": "I could not calculate with these values. Let's start over." if en else "Girdiğin değerlerle hesap yapamadım. Baştan başlayalım."},
            blocking=True,
        )
        pending["step"] = "other_price"
        await async_send_other_charging_price_prompt(hass, target, data, flow_kind=str(pending.get("flow_kind") or "manual"))
        return

    currency_label = str(overrides.get("currency_label") or get_report_currency(data))
    if en:
        message = (
            "I understood this:\n\n"
            f"Unit price: {overrides['actual_price_per_kwh']:.2f} {currency_label}/kWh\n"
            f"Total payment: {overrides['actual_total_cost']:.2f} {currency_label}\n"
            f"Calculated energy: {overrides['added_kwh']:.2f} kWh\n\n"
            "Should I create the report with these values?"
        )
        keyboard = [
            "Confirm:/pom_charge_other_confirm, Fix price:/pom_charge_other_fix_price",
            "Fix total:/pom_charge_other_fix_total, Start over:/pom_charge_other_restart",
            "Cancel:/pom_charge_other_cancel",
        ]
    else:
        message = (
            "Şunu anladım:\n\n"
            f"Birim fiyat: {overrides['actual_price_per_kwh']:.2f} {currency_label}/kWh\n"
            f"Toplam ödeme: {overrides['actual_total_cost']:.2f} {currency_label}\n"
            f"Hesaplanan enerji: {overrides['added_kwh']:.2f} kWh\n\n"
            "Raporu bu değerlerle oluşturayım mı?"
        )
        keyboard = [
            "Onayla:/pom_charge_other_confirm, Fiyatı düzelt:/pom_charge_other_fix_price",
            "Toplamı düzelt:/pom_charge_other_fix_total, Baştan başla:/pom_charge_other_restart",
            "İptal:/pom_charge_other_cancel",
        ]
    await hass.services.async_call(
        "telegram_bot",
        "send_message",
        {"target": target, "parse_mode": "plain_text", "message": message, "inline_keyboard": keyboard},
        blocking=True,
    )


def build_manual_charging_prompt_state(
    hass: HomeAssistant,
    data: dict[str, Any],
    service_data: dict[str, Any],
) -> dict[str, Any]:
    """Build a snapshot for manually testing the interactive charging prompt."""
    state = clone_charging_state_for_pending(get_charging_report_state(hass))
    test_mode = bool(service_data.get("test_mode", False))
    now = datetime.now()

    if service_data.get("duration_minutes") is not None:
        state["duration_minutes"] = safe_float(service_data.get("duration_minutes"), 0.0)
    elif safe_float(state.get("duration_minutes"), 0.0) <= 0 and test_mode:
        state["duration_minutes"] = 84.0

    duration = max(10.0, safe_float(state.get("duration_minutes"), 84.0 if test_mode else 10.0))

    if service_data.get("added_kwh") is not None:
        state["last_added_kwh"] = safe_float(service_data.get("added_kwh"), 0.0)
    elif safe_float(state.get("last_added_kwh"), 0.0) <= 0 and test_mode:
        state["last_added_kwh"] = 38.4

    if service_data.get("battery_range_km") is not None:
        state["last_battery_range_km"] = safe_float(service_data.get("battery_range_km"), 0.0)
    elif safe_float(state.get("last_battery_range_km"), 0.0) <= 0 and test_mode:
        state["last_battery_range_km"] = 412.0

    if service_data.get("battery_range_estimate_km") is not None:
        state["last_battery_range_estimate_km"] = safe_float(service_data.get("battery_range_estimate_km"), 0.0)
    elif safe_float(state.get("last_battery_range_estimate_km"), 0.0) <= 0 and test_mode:
        state["last_battery_range_estimate_km"] = 395.0

    if not state.get("samples") and test_mode:
        base_samples = [
            (0.00, 62), (0.06, 74), (0.12, 72), (0.24, 64), (0.36, 55),
            (0.48, 44), (0.60, 31), (0.72, 19), (0.84, 9),
        ]
        state["samples"] = [
            {"minute": round(duration * pos, 2), "power_kw": power}
            for pos, power in base_samples
        ]
    elif not isinstance(state.get("samples"), list):
        state["samples"] = []

    if service_data.get("peak_power_kw") is not None:
        state["peak_power_kw"] = safe_float(service_data.get("peak_power_kw"), 0.0)
    elif safe_float(state.get("peak_power_kw"), 0.0) <= 0 and state.get("samples"):
        state["peak_power_kw"] = max(
            safe_float(item.get("power_kw"), 0.0)
            for item in state.get("samples", [])
            if isinstance(item, dict)
        )

    state["finished_at"] = str(state.get("finished_at") or now.strftime("%d %B %Y · %H:%M"))
    state["active"] = False
    state["inactive_since_ts"] = now.timestamp()
    return state


async def async_send_charging_provider_prompt(
    hass: HomeAssistant,
    data: dict[str, Any],
    state_snapshot: dict[str, Any],
    *,
    target: str | None = None,
) -> bool:
    """Ask the user where the completed charge session happened."""
    target = str(target or get_charging_report_telegram_target(data)).strip()
    if not target:
        return False

    pending = get_pending_charging_report_state(hass)
    pending.clear()
    pending.update({
        "active": True,
        "step": "provider",
        "created_ts": datetime.now().timestamp(),
        "chat_id": normalize_telegram_id(target),
        "target": target,
        "state": clone_charging_state_for_pending(state_snapshot),
    })

    await hass.services.async_call(
        "telegram_bot",
        "send_message",
        {
            "target": target,
            "parse_mode": "plain_text",
            "message": charge_text(data, "provider_prompt"),
            "inline_keyboard": build_charging_provider_keyboard(data, pending),
        },
        blocking=True,
    )
    return True


async def async_finalize_interactive_charging_report(
    hass: HomeAssistant,
    data: dict[str, Any],
    pending: dict[str, Any],
    *,
    manual_overrides: dict[str, Any] | None = None,
    message_prefix: str = "Şarj seansı tamamlandı.",
) -> tuple[str, dict[str, Any]]:
    """Render and send the pending charging report, then clear the interaction state."""
    state_snapshot = pending.get("state") or get_charging_report_state(hass)
    target = str(pending.get("target") or get_charging_report_telegram_target(data)).strip()
    try:
        png_path, report_data = await render_and_send_charging_report(
            hass,
            data,
            state=state_snapshot,
            send_telegram=bool(target),
            telegram_target=target,
            test_mode=False,
            message_prefix=message_prefix,
            manual_overrides=manual_overrides or {},
        )
        record = await async_record_charge_cost_entry(hass, report_data, source="interactive")
        if record and target:
            await async_send_monthly_charge_cost_visual_report(
                hass,
                data,
                target=target,
                month_key=str(record.get("month_key") or ""),
                caption_prefix="Bu ayki şarj toplamın güncellendi.",
            )
        return png_path, report_data
    finally:
        pending.clear()


async def async_timeout_pending_charging_report_if_needed(hass: HomeAssistant, data: dict[str, Any]) -> None:
    """Keep an interactive charging report pending until the user answers.

    alpha254: The old behavior rendered/sent a default charging report after
    five minutes without a Telegram answer. That could record the wrong tariff
    before Berkan replied. Now the completed charge snapshot remains pending
    indefinitely in memory and the report is generated only when the user picks
    a provider, enters a custom price/total, uses skip, or explicitly cancels.
    """
    pending = get_pending_charging_report_state(hass)
    if not pending.get("active"):
        return
    pending["waiting_for_user_reply"] = True
    pending["last_waiting_check_ts"] = datetime.now().timestamp()
    # Intentionally do not auto-finalize and do not clear the pending state.
    return


async def update_charging_report_session(hass: HomeAssistant, data: dict[str, Any]) -> None:
    """Collect charger power samples and auto-send a PNG when charging ends."""
    state = get_charging_report_state(hass)
    entities = get_charging_report_entities(hass, data)
    now = datetime.now()
    now_ts = now.timestamp()

    power_kw = get_float_state(hass, entities.get("charger_power"), 0.0)
    active_now = is_charge_report_session_active(hass, data)

    if active_now:
        if not state.get("active"):
            state.clear()
            state.update({
                "active": True,
                "start_ts": now_ts,
                "started_at": now.strftime("%d %B %Y · %H:%M"),
                "samples": [],
                "last_sample_ts": 0.0,
                "inactive_since_ts": 0.0,
            })
        state["inactive_since_ts"] = 0.0
        start_ts = safe_float(state.get("start_ts"), now_ts)
        elapsed_min = max(0.0, (now_ts - start_ts) / 60.0)
        last_sample_ts = safe_float(state.get("last_sample_ts"), 0.0)
        samples = state.setdefault("samples", [])
        if not isinstance(samples, list):
            samples = []
            state["samples"] = samples
        if not samples or (now_ts - last_sample_ts) >= 2:
            samples.append({"minute": round(elapsed_min, 2), "power_kw": round(max(power_kw, 0.0), 2)})
            # Avoid unbounded state growth. 6 hours at 2-second samples is still more than enough.
            if len(samples) > 10800:
                del samples[:-10800]
            state["last_sample_ts"] = now_ts
        state["duration_minutes"] = elapsed_min
        state["last_added_kwh"] = get_float_state(hass, entities.get("charge_energy_added"), safe_float(state.get("last_added_kwh"), 0.0))
        state["last_battery_range_km"] = get_float_state(hass, entities.get("battery_range"), safe_float(state.get("last_battery_range_km"), 0.0))
        state["last_battery_range_estimate_km"] = get_float_state(hass, entities.get("battery_range_estimate"), safe_float(state.get("last_battery_range_estimate_km"), 0.0))
        state["peak_power_kw"] = max(safe_float(state.get("peak_power_kw"), 0.0), power_kw)
        return

    if not state.get("active"):
        await async_timeout_pending_charging_report_if_needed(hass, data)
        return

    inactive_since = safe_float(state.get("inactive_since_ts"), 0.0)
    if inactive_since <= 0:
        state["inactive_since_ts"] = now_ts
        return

    # Wait a little so short power dips do not split one charging session into multiple reports.
    if (now_ts - inactive_since) < 90:
        return

    start_ts = safe_float(state.get("start_ts"), now_ts)
    duration_minutes = max(0.0, (now_ts - start_ts) / 60.0)
    state["duration_minutes"] = duration_minutes
    state["finished_at"] = now.strftime("%d %B %Y · %H:%M")

    # Add a final zero-power point so the curve visibly ends.
    samples = state.setdefault("samples", [])
    if isinstance(samples, list):
        samples.append({"minute": round(duration_minutes, 2), "power_kw": 0.0})

    added = safe_float(state.get("last_added_kwh"), 0.0)
    if duration_minutes >= 2 and added > 0.05:
        try:
            report_mode = str(data.get(CONF_CHARGING_REPORT_MODE, DEFAULT_CHARGING_REPORT_MODE) or DEFAULT_CHARGING_REPORT_MODE).strip()
            if report_mode == CHARGING_REPORT_MODE_PROMPT:
                prompted = await async_send_charging_provider_prompt(hass, data, state)
                if prompted:
                    state["last_report_prompt_ts"] = now_ts
                else:
                    png_path, _report_data = await render_and_send_charging_report(
                        hass,
                        data,
                        state=state,
                        send_telegram=True,
                        message_prefix="Şarj seansı tamamlandı.",
                    )
                    state["last_report_path"] = png_path
                    state["last_report_sent_ts"] = now_ts
            else:
                png_path, _report_data = await render_and_send_charging_report(
                    hass,
                    data,
                    state=state,
                    send_telegram=True,
                    message_prefix="Şarj seansı tamamlandı.",
                )
                state["last_report_path"] = png_path
                state["last_report_sent_ts"] = now_ts
        except Exception:
            _LOGGER.exception("POM charging report interactive prompt/auto-send failed")

    state["active"] = False



LIVE_TRIP_STATE_STORE = "live_trip_state_by_entry"
LIVE_TRIP_SENSOR_STORE = "live_trip_sensor_by_entry"
LIVE_TRIP_TEST_TASK_STORE = "live_trip_test_task_by_entry"
LIVE_TRIP_AI_TASK_STORE = "live_trip_ai_task_by_entry"
AUTO_TRIP_FINISH_TASK_STORE = "auto_trip_finish_task_by_entry"

TRIP_ELEVATION_STATE_STORE = "trip_elevation_state_by_entry"
TRIP_ELEVATION_SENSOR_STORE = "trip_elevation_sensor_by_entry"
TRIP_ELEVATION_CACHE_STORE = "trip_elevation_cache"
TRIP_ELEVATION_PROVIDER = "Open-Meteo Elevation API"
TRIP_ELEVATION_API_URL = "https://api.open-meteo.com/v1/elevation"
TRIP_ELEVATION_MAX_SAMPLES = 2000
TRIP_ELEVATION_CACHE_MAX_SIZE = 5000
TRIP_ELEVATION_NOISE_THRESHOLD_METERS = 1.5


def get_live_trip_state(hass: HomeAssistant, entry_id: str) -> dict[str, Any]:
    """Return live trip state bucket for an entry."""
    root = hass.data.setdefault(DOMAIN, {})
    store = root.setdefault(LIVE_TRIP_STATE_STORE, {})
    return store.setdefault(entry_id, {})


def get_live_trip_entities(data: dict[str, Any]) -> dict[str, str | None]:
    """Return entities used by the live trip calculation engine.

    This intentionally reuses Vehicle Entity Manager / Report selections and only
    falls back to legacy report options. Users should not select the same entity
    twice for the live card.
    """
    return {
        "speed": get_report_configured_entity(data, CONF_SPEED_ENTITY, VEHICLE_ROLE_SPEED),
        "shift_state": get_report_configured_entity(data, CONF_SHIFT_STATE_ENTITY, VEHICLE_ROLE_SHIFT_STATE),
        "odometer": get_report_configured_entity(data, CONF_ODOMETER_ENTITY, VEHICLE_ROLE_ODOMETER),
        "energy_remaining": get_report_configured_entity(data, CONF_ENERGY_REMAINING_ENTITY, VEHICLE_ROLE_ENERGY_REMAINING),
        "battery_level": get_report_configured_entity(data, CONF_BATTERY_LEVEL_ENTITY, VEHICLE_ROLE_BATTERY_LEVEL),
        "elevation": get_report_configured_entity(data, CONF_ELEVATION_ENTITY, VEHICLE_ROLE_ELEVATION),
        "climate": get_report_configured_entity(data, CONF_CLIMATE_ENTITY, VEHICLE_ROLE_CLIMATE),
    }


def live_trip_short_duration(seconds: float) -> str:
    """Return compact Turkish duration for live trip card."""
    total_min = int(round(max(0.0, seconds) / 60.0))
    if total_min <= 0:
        return "—"
    hours = total_min // 60
    minutes = total_min % 60
    if hours and minutes:
        return f"{hours} sa {minutes} dk."
    if hours:
        return f"{hours} sa."
    return f"{total_min} dk."


def live_trip_active_from_states(hass: HomeAssistant, entities: dict[str, str | None], start_speed_threshold: float) -> bool:
    """Detect whether a trip should be considered active."""
    shift_entity = entities.get("shift_state")
    if shift_entity:
        state = hass.states.get(shift_entity)
        shift = str(state.state if state is not None else "").strip().lower()
        if shift in {"d", "drive", "driving", "r", "reverse", "n", "neutral"}:
            return True
        if shift in {"p", "park", "parking", "parked", "off", "asleep", "sleeping"}:
            return False

    speed = get_float_state(hass, entities.get("speed"), 0.0)
    return speed >= start_speed_threshold


def live_trip_climate_is_active(hass: HomeAssistant, climate_entity: str | None) -> bool:
    """Return whether climate should count as active for live trip."""
    if not climate_entity:
        return False
    state = hass.states.get(climate_entity)
    if state is None:
        return False
    return is_climate_active(str(state.state).strip().lower())


def live_trip_short_maneuver_settings(data: dict[str, Any]) -> dict[str, Any]:
    """Return normalized short-manoeuvre / candidate-trip settings."""
    return {
        "enabled": get_bool_option(
            data,
            CONF_LIVE_TRIP_IGNORE_SHORT_MANEUVERS,
            DEFAULT_LIVE_TRIP_IGNORE_SHORT_MANEUVERS,
        ),
        "min_distance_km": max(
            0.0,
            safe_float(
                data.get(CONF_LIVE_TRIP_CANDIDATE_MIN_DISTANCE_KM),
                DEFAULT_LIVE_TRIP_CANDIDATE_MIN_DISTANCE_KM,
            ),
        ),
        "min_duration_seconds": max(
            0.0,
            safe_float(
                data.get(CONF_LIVE_TRIP_CANDIDATE_MIN_DURATION_SECONDS),
                DEFAULT_LIVE_TRIP_CANDIDATE_MIN_DURATION_SECONDS,
            ),
        ),
    }


def live_trip_candidate_qualified(
    *,
    trip_km: float,
    duration_seconds: float,
    settings: dict[str, Any],
) -> bool:
    """Return whether a candidate movement should become a real Live Trip."""
    min_distance = max(0.0, safe_float(settings.get("min_distance_km"), DEFAULT_LIVE_TRIP_CANDIDATE_MIN_DISTANCE_KM))
    min_duration = max(0.0, safe_float(settings.get("min_duration_seconds"), DEFAULT_LIVE_TRIP_CANDIDATE_MIN_DURATION_SECONDS))
    if min_distance <= 0 and min_duration <= 0:
        return True
    if min_distance > 0 and trip_km >= min_distance:
        return True
    if min_duration > 0 and duration_seconds >= min_duration:
        return True
    return False


def live_trip_candidate_reason(
    *,
    trip_km: float,
    duration_seconds: float,
    settings: dict[str, Any],
) -> str:
    """Return a concise reason explaining candidate-trip qualification."""
    min_distance = max(0.0, safe_float(settings.get("min_distance_km"), DEFAULT_LIVE_TRIP_CANDIDATE_MIN_DISTANCE_KM))
    min_duration = max(0.0, safe_float(settings.get("min_duration_seconds"), DEFAULT_LIVE_TRIP_CANDIDATE_MIN_DURATION_SECONDS))
    reasons: list[str] = []
    if min_distance <= 0 and min_duration <= 0:
        return "thresholds_disabled"
    if min_distance > 0 and trip_km >= min_distance:
        reasons.append(f"distance {trip_km:.2f} km >= {min_distance:.2f} km")
    if min_duration > 0 and duration_seconds >= min_duration:
        reasons.append(f"duration {live_trip_short_duration(duration_seconds)} >= {live_trip_short_duration(min_duration)}")
    return "; ".join(reasons) if reasons else "candidate_thresholds_not_reached"


def live_trip_candidate_finish_decision(
    integration_data: dict[str, Any],
    trip_state: dict[str, Any],
    *,
    end_odometer: float,
    now_ts: float | None = None,
) -> dict[str, Any]:
    """Return and store the final short-manoeuvre/candidate-trip decision.

    The candidate filter must never block a real trip once either configured
    threshold was reached. It also must not rely only on a single end-odometer
    read, because some integrations update odometer slower than shift_state.
    Alpha349 records the decision so support reports and Trip Records can show
    exactly whether the filter ignored a manoeuvre or allowed the report/AI path.
    """
    settings = live_trip_short_maneuver_settings(integration_data)
    enabled = bool(settings.get("enabled"))
    now_value = safe_float(now_ts, datetime.now().timestamp())
    start_odometer = safe_float(trip_state.get("start_odometer"), end_odometer)
    last_odometer = safe_float(trip_state.get("last_odometer"), end_odometer)
    end_value = safe_float(end_odometer, last_odometer)
    odometer_distance = max(0.0, max(last_odometer, end_value) - start_odometer)
    runtime_distance = max(0.0, safe_float(trip_state.get("trip_km"), 0.0))
    distance = max(odometer_distance, runtime_distance)
    start_ts = safe_float(trip_state.get("start_ts"), 0.0)
    elapsed_duration = max(0.0, now_value - start_ts) if start_ts > 0 else 0.0
    runtime_duration = max(
        safe_float(trip_state.get("duration_seconds"), 0.0),
        safe_float(trip_state.get("report_duration_seconds"), 0.0),
        safe_float(trip_state.get("total_elapsed_seconds"), 0.0),
    )
    duration = max(elapsed_duration, runtime_duration)
    qualified = live_trip_candidate_qualified(
        trip_km=distance,
        duration_seconds=duration,
        settings=settings,
    )
    reason = live_trip_candidate_reason(
        trip_km=distance,
        duration_seconds=duration,
        settings=settings,
    )
    if not enabled:
        ignored = False
        reason = "candidate_filter_disabled"
    elif bool(trip_state.get("candidate_confirmed")):
        ignored = False
        reason = str(trip_state.get("candidate_confirm_reason") or "candidate_already_confirmed")
    else:
        ignored = not qualified

    decision = {
        "enabled": enabled,
        "ignored": bool(ignored),
        "qualified": bool(qualified) or bool(trip_state.get("candidate_confirmed")) or not enabled,
        "reason": reason,
        "distance_km": round(distance, 3),
        "duration_seconds": round(duration, 0),
        "min_distance_km": round(max(0.0, safe_float(settings.get("min_distance_km"), DEFAULT_LIVE_TRIP_CANDIDATE_MIN_DISTANCE_KM)), 3),
        "min_duration_seconds": round(max(0.0, safe_float(settings.get("min_duration_seconds"), DEFAULT_LIVE_TRIP_CANDIDATE_MIN_DURATION_SECONDS)), 0),
    }

    trip_state["candidate_distance_km"] = decision["distance_km"]
    trip_state["candidate_duration_seconds"] = decision["duration_seconds"]
    trip_state["candidate_min_distance_km"] = decision["min_distance_km"]
    trip_state["candidate_min_duration_seconds"] = decision["min_duration_seconds"]
    trip_state["candidate_finish_decision"] = decision
    trip_state["short_maneuver_reason"] = reason if ignored else ""
    trip_state["ignored_short_maneuver"] = bool(ignored)
    if enabled and not ignored:
        trip_state["candidate_confirmed"] = True
        trip_state["candidate_trip"] = False
        trip_state["candidate_confirm_reason"] = reason
        trip_state["candidate_confirmed_at"] = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    return decision


def should_ignore_short_maneuver_trip(
    integration_data: dict[str, Any],
    trip_state: dict[str, Any],
    *,
    end_odometer: float,
    now_ts: float | None = None,
) -> bool:
    """Return whether a finished auto trip is only a short parking manoeuvre."""
    return bool(live_trip_candidate_finish_decision(
        integration_data,
        trip_state,
        end_odometer=end_odometer,
        now_ts=now_ts,
    ).get("ignored"))



def get_live_trip_ai_segments_path(hass: HomeAssistant, entry_id: str) -> Path:
    """Return the dedicated JSON path for Live Trip AI comment segments."""
    safe_entry = re.sub(r"[^a-zA-Z0-9_-]", "_", str(entry_id or "default")) or "default"
    return Path(hass.config.path(f"pom_tesla_live_trip_ai_segments_{safe_entry}.json"))


def load_live_trip_ai_segments_payload(hass: HomeAssistant, entry_id: str) -> dict[str, Any]:
    """Load stored Live Trip AI comment segments from disk."""
    path = get_live_trip_ai_segments_path(hass, entry_id)
    default_payload: dict[str, Any] = {
        "entry_id": str(entry_id or ""),
        "segments": [],
        "updated_at": "",
        "started_at": "",
    }
    try:
        if not path.exists():
            return copy.deepcopy(default_payload)
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return copy.deepcopy(default_payload)
        segments = payload.get("segments") if isinstance(payload.get("segments"), list) else []
        return {
            "entry_id": str(payload.get("entry_id") or entry_id or ""),
            "segments": segments,
            "updated_at": str(payload.get("updated_at") or ""),
            "started_at": str(payload.get("started_at") or ""),
        }
    except Exception:
        _LOGGER.exception("Could not load Live Trip AI segments JSON")
        return copy.deepcopy(default_payload)


def save_live_trip_ai_segments_payload(hass: HomeAssistant, entry_id: str, payload: dict[str, Any]) -> None:
    """Persist Live Trip AI comment segments to a dedicated JSON file."""
    path = get_live_trip_ai_segments_path(hass, entry_id)
    normalized = {
        "entry_id": str(payload.get("entry_id") or entry_id or ""),
        "segments": list(payload.get("segments") or []),
        "updated_at": str(payload.get("updated_at") or ""),
        "started_at": str(payload.get("started_at") or ""),
    }
    path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")


def _live_trip_ai_default_runtime() -> dict[str, Any]:
    """Return default in-memory runtime fields for Live Trip AI segments."""
    return {
        "live_ai_segment_size_km": float(DEFAULT_LIVE_TRIP_AI_SEGMENT_DISTANCE_KM),
        "live_ai_segment_last_completed_index": 0,
        "live_ai_segment_next_target_km": 10.0,
        "live_ai_segment_baseline": {},
        "live_ai_segments": [],
        "live_ai_latest_segment": {},
        "live_ai_comment_status": "waiting",
        "live_ai_comment_source": "",
        "live_ai_comment_error": "",
        "live_ai_last_generated_at": "",
        "live_ai_last_prompt_at": "",
        "live_ai_last_prompt_ts": 0.0,
        "live_ai_last_requested_index": 0,
        "live_ai_scheduler_debug": {},
        "live_comment": "",
    }


def live_trip_ai_segment_size_from_data(data: dict[str, Any]) -> float:
    """Return the user-selected Live Trip AI comment interval in km.

    Only the supported presets are allowed so the scheduler stays deterministic:
    1 km for short tests/city use, 5 km for mixed use, or 10 km for long drives.
    """
    raw = safe_float(data.get(CONF_LIVE_TRIP_AI_SEGMENT_DISTANCE_KM), DEFAULT_LIVE_TRIP_AI_SEGMENT_DISTANCE_KM)
    allowed = [float(item) for item in LIVE_TRIP_AI_SEGMENT_DISTANCE_OPTIONS]
    if raw in allowed:
        return raw
    return min(allowed, key=lambda item: abs(item - raw)) if allowed else float(DEFAULT_LIVE_TRIP_AI_SEGMENT_DISTANCE_KM)




def _live_trip_ai_snapshot_from_state(state: dict[str, Any]) -> dict[str, Any]:
    """Capture cumulative live-trip counters used as the next 10 km baseline."""
    return {
        "trip_km": round(safe_float(state.get("trip_km"), 0.0), 3),
        "duration_seconds": round(safe_float(state.get("duration_seconds"), 0.0), 1),
        "moving_seconds": round(safe_float(state.get("moving_seconds"), 0.0), 1),
        "traffic_seconds": round(safe_float(state.get("traffic_seconds"), 0.0), 1),
        "climate_seconds": round(safe_float(state.get("climate_seconds"), 0.0), 1),
        "used_kwh": round(safe_float(state.get("used_kwh"), 0.0), 3),
        "start_battery": round(safe_float(state.get("start_battery"), 0.0), 1),
        "end_battery": round(safe_float(state.get("end_battery"), 0.0), 1),
        "max_speed": round(safe_float(state.get("max_speed"), 0.0), 1),
        "average_moving_speed": round(safe_float(state.get("average_moving_speed"), 0.0), 1),
        "average_overall_speed": round(safe_float(state.get("average_overall_speed"), 0.0), 1),
        "min_elevation": round(safe_float(state.get("min_elevation"), 0.0), 1),
        "max_elevation": round(safe_float(state.get("max_elevation"), 0.0), 1),
        "last_elevation": round(safe_float(state.get("last_elevation"), safe_float(state.get("max_elevation"), 0.0)), 1),
        "traffic_model_label": str(state.get("traffic_model_label") or "").strip(),
        "trip_status": str(state.get("trip_status") or "").strip(),
    }


def _live_trip_ai_segment_label(index: int, size_km: float = 10.0) -> str:
    """Return compact label such as 0–10 km for a segment."""
    start_km = max(0.0, (max(1, int(index)) - 1) * size_km)
    end_km = start_km + size_km
    return f"{int(round(start_km))}–{int(round(end_km))} km"


def _live_trip_ai_next_segment_index(state: dict[str, Any]) -> int:
    """Return the next AI segment index that should be generated."""
    return max(1, int(safe_float(state.get("live_ai_segment_last_completed_index"), 0.0)) + 1)


def _live_trip_ai_next_threshold_km(state: dict[str, Any], size_km: float) -> float:
    """Return the deterministic next threshold based on completed segment count.

    The older implementation trusted `live_ai_segment_next_target_km` too much. If
    that value became stale during candidate-trip transitions or a previous task
    got stuck, the 10 km trigger could be skipped. The threshold is now derived
    from the completed segment index every update.
    """
    index = _live_trip_ai_next_segment_index(state)
    return round(max(size_km, index * size_km), 3)


def _live_trip_ai_set_scheduler_debug(
    state: dict[str, Any],
    *,
    current_km: float,
    next_target: float,
    segment_index: int,
    reason: str,
    should_schedule: bool,
) -> None:
    """Store scheduler diagnostics in sensor attributes for support/debug."""
    state["live_ai_scheduler_debug"] = {
        "current_km": round(current_km, 3),
        "next_target_km": round(next_target, 3),
        "segment_index": int(segment_index),
        "status": str(state.get("status") or ""),
        "comment_status": str(state.get("live_ai_comment_status") or ""),
        "last_completed_index": int(safe_float(state.get("live_ai_segment_last_completed_index"), 0.0)),
        "last_requested_index": int(safe_float(state.get("live_ai_last_requested_index"), 0.0)),
        "should_schedule": bool(should_schedule),
        "reason": str(reason or ""),
        "updated_at": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
    }


def _build_live_trip_ai_segment(state: dict[str, Any], baseline: dict[str, Any], *, segment_index: int, size_km: float = 10.0) -> dict[str, Any]:
    """Build one incremental Live Trip segment payload from cumulative counters."""
    start_km = safe_float(baseline.get("trip_km"), 0.0)
    end_km = safe_float(state.get("trip_km"), 0.0)
    distance_km = max(0.0, end_km - start_km)
    duration_seconds = max(0.0, safe_float(state.get("duration_seconds"), 0.0) - safe_float(baseline.get("duration_seconds"), 0.0))
    moving_seconds = max(0.0, safe_float(state.get("moving_seconds"), 0.0) - safe_float(baseline.get("moving_seconds"), 0.0))
    traffic_seconds = max(0.0, safe_float(state.get("traffic_seconds"), 0.0) - safe_float(baseline.get("traffic_seconds"), 0.0))
    climate_seconds = max(0.0, safe_float(state.get("climate_seconds"), 0.0) - safe_float(baseline.get("climate_seconds"), 0.0))
    used_kwh = max(0.0, safe_float(state.get("used_kwh"), 0.0) - safe_float(baseline.get("used_kwh"), 0.0))
    end_battery = safe_float(state.get("end_battery"), 0.0)
    baseline_end_battery = safe_float(baseline.get("end_battery"), safe_float(state.get("start_battery"), end_battery))
    battery_drop = max(0.0, baseline_end_battery - end_battery)
    consumption = (used_kwh / distance_km * 100.0) if distance_km > 0 else 0.0
    avg_moving = (distance_km / (moving_seconds / 3600.0)) if moving_seconds > 0 else 0.0
    avg_overall = (distance_km / (duration_seconds / 3600.0)) if duration_seconds > 0 else avg_moving
    start_elevation = safe_float(baseline.get("last_elevation"), safe_float(baseline.get("min_elevation"), 0.0))
    end_elevation = safe_float(state.get("last_elevation"), start_elevation)
    elevation_delta = end_elevation - start_elevation
    cumulative_elevation_range = max(
        0.0,
        safe_float(state.get("max_elevation"), end_elevation) - safe_float(state.get("min_elevation"), start_elevation),
    )
    elevation_direction = "flat"
    if elevation_delta >= 3:
        elevation_direction = "uphill"
    elif elevation_delta <= -3:
        elevation_direction = "downhill"
    return {
        "segment_index": int(segment_index),
        "segment_label": _live_trip_ai_segment_label(segment_index, size_km),
        "start_km": round(start_km, 2),
        "end_km": round(end_km, 2),
        "distance_km": round(distance_km, 2),
        "duration_seconds": round(duration_seconds, 0),
        "duration_text": live_trip_short_duration(duration_seconds),
        "moving_seconds": round(moving_seconds, 0),
        "moving_text": live_trip_short_duration(moving_seconds),
        "traffic_seconds": round(traffic_seconds, 0),
        "traffic_text": live_trip_short_duration(traffic_seconds),
        "climate_seconds": round(climate_seconds, 0),
        "climate_text": live_trip_short_duration(climate_seconds),
        "used_kwh": round(used_kwh, 2),
        "consumption_kwh_100km": round(consumption, 2),
        "average_speed": round(avg_moving, 1),
        "overall_speed": round(avg_overall, 1),
        "battery_drop": round(battery_drop, 1),
        "start_battery": round(baseline_end_battery, 1),
        "end_battery": round(end_battery, 1),
        "max_speed": round(max(safe_float(baseline.get("max_speed"), 0.0), safe_float(state.get("max_speed"), 0.0)), 1),
        "start_elevation": round(start_elevation, 1),
        "end_elevation": round(end_elevation, 1),
        "elevation_delta": round(elevation_delta, 1),
        "elevation_range": round(cumulative_elevation_range, 1),
        "elevation_direction": elevation_direction,
        "traffic_model_label": str(state.get("traffic_model_label") or baseline.get("traffic_model_label") or "").strip(),
        "trip_status": str(state.get("trip_status") or "").strip(),
        "generated_at": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
        "comment": "",
        "source": "",
        "status": "queued",
    }


def _live_trip_ai_reconciled_next_target_km(state: dict[str, Any], size_km: float | None = None) -> float:
    """Return the next AI target from completed real segments, not stale/test data."""
    segment_size = max(
        1.0,
        safe_float(
            size_km if size_km is not None else state.get("live_ai_segment_size_km"),
            DEFAULT_LIVE_TRIP_AI_SEGMENT_DISTANCE_KM,
        ),
    )
    completed_index = max(0, int(safe_float(state.get("live_ai_segment_last_completed_index"), 0.0)))
    return round(max(segment_size, (completed_index + 1) * segment_size), 3)


def _build_live_trip_ai_waiting_text(state: dict[str, Any], lang: str | None = None) -> str:
    """Return localized friendly waiting text for the next Live Trip AI interval comment."""
    segment_size = max(1.0, safe_float(state.get("live_ai_segment_size_km"), DEFAULT_LIVE_TRIP_AI_SEGMENT_DISTANCE_KM))
    # Do not trust stale live_ai_segment_next_target_km blindly. In alpha342 a
    # panel-only test comment could leave the target at the next 10 km boundary
    # even after the user changed the interval to 1/5 km. The target displayed
    # to the dashboard must always be derived from completed REAL segments.
    next_target = _live_trip_ai_reconciled_next_target_km(state, segment_size)
    state["live_ai_segment_next_target_km"] = next_target
    current_km = max(0.0, safe_float(state.get("trip_km"), 0.0))
    remaining = max(0.0, next_target - current_km)
    size_label = f"{int(segment_size)}" if abs(segment_size - int(segment_size)) < 0.001 else f"{segment_size:g}"
    target_label = f"{int(round(next_target))}" if next_target >= 1 else f"{next_target:g}"
    report_lang = str(lang or state.get("report_language") or state.get("language") or APP_LANGUAGE_TR).strip().lower()
    if report_lang.startswith("en"):
        if remaining <= 0.05:
            return "Preparing a new Live Trip comment."
        if current_km <= 0.05:
            return f"The first Live Trip comment will be ready around {size_label} km."
        return f"About {remaining:.1f} km left until the next Live Trip comment. Target: {target_label} km."
    if remaining <= 0.05:
        return "Yeni Live Trip yorumu hazırlanıyor."
    if current_km <= 0.05:
        return f"İlk Live Trip yorumu {size_label} km civarında hazır olacak."
    return f"Bir sonraki Live Trip yorumu için yaklaşık {remaining:.1f} km kaldı. Hedef: {target_label} km."


def _build_live_trip_ai_fallback_comment(segment: dict[str, Any], data: dict[str, Any], *, lang: str) -> str:
    """Return a richer deterministic fallback comment when AI is unavailable or when panel-test mode is used."""
    label = str(segment.get("segment_label") or "Son bölüm")
    distance = safe_float(segment.get("distance_km"), 0.0)
    avg_speed = safe_float(segment.get("average_speed"), 0.0)
    overall_speed = safe_float(segment.get("overall_speed"), avg_speed)
    consumption = safe_float(segment.get("consumption_kwh_100km"), 0.0)
    traffic_seconds = safe_float(segment.get("traffic_seconds"), 0.0)
    duration_text = str(segment.get("duration_text") or "").strip()
    moving_text = str(segment.get("moving_text") or "").strip()
    climate_text = str(segment.get("climate_text") or "").strip()
    traffic_note = "trafik baskısı düşük" if traffic_seconds < 120 else ("trafik hissedilir" if traffic_seconds < 480 else "trafik belirgin")
    efficiency_note = "verimli" if consumption <= 16 else ("dengeli" if consumption <= 21 else "biraz yüksek")
    road = str(segment.get("current_road") or "").strip()
    location_label = str(road or segment.get("current_location_label") or segment.get("current_neighbourhood") or segment.get("current_dashboard_location_label") or "").strip()
    neighbourhood = str(segment.get("current_neighbourhood") or segment.get("current_district") or "").strip()
    if location_label and neighbourhood and neighbourhood not in location_label:
        location_note = f" Şu anda {neighbourhood} / {location_label} civarındasın."
    elif road:
        location_note = f" Şu anda {road} civarındasın."
    elif location_label:
        location_note = f" Şu anda {location_label} tarafındasın."
    else:
        location_note = " Konum etiketi gelirse burada mahalle/sokak bilgisini de kullanacağım."
    elevation_delta = safe_float(segment.get("elevation_delta"), 0.0)
    elevation_range = safe_float(segment.get("elevation_range"), 0.0)
    if elevation_delta >= 3:
        elevation_note = f"Bu bölümde yaklaşık {elevation_delta:.0f} m yükseliş var; bu, özellikle düşük hızda tüketimi biraz yukarı çekebilir."
    elif elevation_delta <= -3:
        elevation_note = f"Bu bölümde yaklaşık {abs(elevation_delta):.0f} m iniş var; regen/verimlilik tarafına küçük bir destek beklenir."
    elif elevation_range >= 8:
        elevation_note = f"Rakım aralığı yaklaşık {elevation_range:.0f} m; iniş-çıkış var ama net etki sınırlı görünüyor."
    else:
        elevation_note = "Rakım neredeyse düz kaldığı için tüketimi asıl hız, trafik ve klima belirliyor."
    climate_note = ""
    if climate_text and climate_text != "—":
        climate_note = f" Klima {climate_text} devrede kalmış; kısa segmentlerde bu tüketimi daha görünür etkileyebilir."
    if str(lang or APP_LANGUAGE_TR).lower().startswith("en"):
        loc_en = f" You are around {location_label}." if location_label else " Location context will be used when available."
        elev_en = "Elevation was almost flat, so speed, traffic and climate are the main factors."
        if elevation_delta >= 3:
            elev_en = f"A roughly {elevation_delta:.0f} m climb may add a little consumption."
        elif elevation_delta <= -3:
            elev_en = f"A roughly {abs(elevation_delta):.0f} m descent likely helps efficiency a bit."
        return trim_live_trip_ai_comment(
            f"{label}: about {distance:.1f} km completed in {duration_text or 'this segment'}.{loc_en} Traffic looks {traffic_note.replace('trafik ', '')}; moving average is {avg_speed:.0f} km/h, overall average {overall_speed:.0f} km/h and consumption {consumption:.1f} kWh/100 km. {elev_en}",
            max_chars=900,
        )
    return trim_live_trip_ai_comment(
        f"{label}: yaklaşık {distance:.1f} km tamamlandı; bölüm süresi {duration_text or '—'}, hareket süresi {moving_text or '—'}."
        f"{location_note} {traffic_note.capitalize()}; hareketli ortalama {avg_speed:.0f} km/sa, genel ortalama {overall_speed:.0f} km/sa ve tüketim {consumption:.1f} kWh/100 km ile {efficiency_note}."
        f" {elevation_note}{climate_note}",
        max_chars=900,
    )


def trim_live_trip_ai_comment(comment: str, *, max_chars: int = 520) -> str:
    """Keep Live Trip in-car comments short enough for the dashboard panel."""
    text = re.sub(r"\s+", " ", str(comment or "")).strip()
    if len(text) <= max_chars:
        return text
    cut = text[: max(0, max_chars - 1)].rstrip()
    sentence_end = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "))
    if sentence_end >= 120:
        return cut[: sentence_end + 1].strip()
    word_end = cut.rfind(" ")
    if word_end >= 80:
        return cut[:word_end].rstrip() + "…"
    return cut.rstrip() + "…"


async def async_generate_live_trip_ai_comment(hass: HomeAssistant, data: dict[str, Any], segment: dict[str, Any]) -> tuple[str, str]:
    """Generate one Live Trip distance-segment comment using OpenAI when available."""
    lang = get_app_language(data)
    api_key = str(data.get(CONF_OPENAI_API_KEY, "")).strip()
    model = str(data.get(CONF_OPENAI_MODEL, DEFAULT_OPENAI_MODEL)).strip() or DEFAULT_OPENAI_MODEL
    ai_enabled = get_bool_option(data, CONF_AI_ALERT_POST_TRIP_SUMMARY_ENABLED, DEFAULT_AI_ALERT_POST_TRIP_SUMMARY_ENABLED)
    if not ai_enabled or not api_key:
        return _build_live_trip_ai_fallback_comment(segment, data, lang=lang), "template"

    detail_level = normalize_trip_story_detail_level(data.get(CONF_AI_TRIP_STORY_DETAIL_LEVEL))
    user_address_instruction = build_ai_user_address_instruction(data, lang)
    ai_name = str(data.get(CONF_AI_NAME) or DEFAULT_AI_NAME or "Tesla AI").strip() or "Tesla AI"
    system_prompt = (
        f"Sen {ai_name} adında, canlı Tesla sürüşünü seçilen mesafe bölümleri halinde yorumlayan kısa ve premium bir araç asistanısın.\n"
        f"{user_address_instruction}\n"
        "Görevin: tek bir seçili mesafe sürüş bölümünü yorumlamak.\n"
        "Detaylı ama panel için okunabilir yaz: 4-6 kısa cümle ve yaklaşık 650 karakter.\n"
        "Tek paragraf yaz; madde işareti veya başlık kullanma. Dashboard üzerinde 5-6 satıra sığmalı.\n"
        "Veride current_road/current_location_label/current_neighbourhood varsa mahalle/sokak bilgisini doğal şekilde mutlaka geçir.\n"
        "Rakım/eğim verisi varsa iniş-çıkışın tüketim veya verimlilik üzerindeki nitel etkisini belirt; kesin olmayan enerji miktarı uydurma.\n"
        "Net ve doğal Türkçe kullan. Abartma, veri uydurma, güvenlik dersi verme.\n"
        "Ölçülen veriler ile yorumları karıştırma; olmayan şeyi kesinmiş gibi söyleme.\n"
        "Sadece verilen bölüm için konuş; tüm sürüşün geneli gibi davranma.\n"
    )
    if str(lang).lower().startswith("en"):
        system_prompt = (
            f"You are {ai_name}, a premium in-car assistant that comments on Tesla live-trip progress in short distance segments.\n"
            f"{user_address_instruction}\n"
            "Task: comment only on this single segment. Use 4-6 short sentences and about 650 characters.\n"
            "Write one paragraph only; no bullets or heading, and fit into a compact in-car dashboard panel.\n"
            "If current_road/current_location_label/current_neighbourhood is provided, naturally mention the street/neighbourhood. If elevation data is provided, describe its qualitative effect without inventing exact energy impact.\n"
        )
    context = {"segment": segment, "detail_level": detail_level, "mode": "live_trip_segment"}
    user_message = (
        f"{segment.get('segment_label', 'Segment')} için tek paragraf, 4-6 kısa cümle ve yaklaşık 650 karakterlik detaylı Live Trip yorumu yaz. Konum ve rakım bilgisi varsa mutlaka doğal şekilde kullan."
        if not str(lang).lower().startswith("en")
        else f"Write a one-paragraph detailed live-trip comment for {segment.get('segment_label', 'this segment')}, 4-6 short sentences and about 650 characters. Use location and elevation context when available."
    )
    try:
        answer = await async_call_openai_responses_api(
            hass,
            api_key=api_key,
            model=model,
            system_prompt=system_prompt,
            user_message=user_message,
            context_text=json.dumps(context, ensure_ascii=False, indent=2),
            max_output_tokens=420,
        )
        answer = trim_live_trip_ai_comment(str(answer or "").strip(), max_chars=900)
        if not answer:
            raise ValueError("empty_live_trip_ai_answer")
        return answer, "openai"
    except Exception as err:
        _LOGGER.exception("Live Trip AI segment generation failed; using fallback: %s", err)
        return _build_live_trip_ai_fallback_comment(segment, data, lang=lang), "template"


def _cancel_live_trip_ai_task(hass: HomeAssistant, entry_id: str) -> None:
    """Cancel the currently running Live Trip AI task for the entry if present."""
    task = hass.data.setdefault(DOMAIN, {}).setdefault(LIVE_TRIP_AI_TASK_STORE, {}).get(entry_id)
    if task is not None and not task.done():
        task.cancel()


async def _async_live_trip_ai_segment_task(hass: HomeAssistant, entry_id: str, data: dict[str, Any], *, segment_index: int, baseline: dict[str, Any]) -> None:
    """Background task that generates and persists one Live Trip AI segment."""
    try:
        state = get_live_trip_state(hass, entry_id)
        try:
            await async_update_reverse_geocode_cache(hass, data)
        except Exception as err:
            _LOGGER.debug("Live Trip AI reverse geocode refresh skipped: %s", err)
        segment = _build_live_trip_ai_segment(state, baseline, segment_index=segment_index, size_km=safe_float(state.get("live_ai_segment_size_km"), 10.0))
        segment.update(build_live_trip_ai_location_context(hass))
        state["live_ai_comment_status"] = "generating"
        state["live_ai_comment_error"] = ""
        prompt_now = datetime.now()
        state["live_ai_last_prompt_at"] = prompt_now.strftime("%d.%m.%Y %H:%M:%S")
        state["live_ai_last_prompt_ts"] = prompt_now.timestamp()
        state["live_ai_latest_segment"] = segment
        state["live_comment"] = f"{segment.get('segment_label')}: yorum hazırlanıyor..."
        notify_live_trip_sensor(hass, entry_id)
        comment, source = await async_generate_live_trip_ai_comment(hass, data, segment)
        state = get_live_trip_state(hass, entry_id)
        segment["comment"] = str(comment or "").strip()
        segment["source"] = source
        segment["status"] = "ready"
        segment["generated_at"] = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        segments = state.get("live_ai_segments") if isinstance(state.get("live_ai_segments"), list) else []
        segments = [item for item in segments if int(safe_float((item or {}).get("segment_index"), 0.0)) != int(segment_index)]
        segments.append(segment)
        segments.sort(key=lambda item: int(safe_float((item or {}).get("segment_index"), 0.0)))
        state["live_ai_segments"] = segments[-8:]
        state["live_ai_latest_segment"] = segment
        state["live_ai_segment_last_completed_index"] = int(segment_index)
        next_size = max(1.0, safe_float(state.get("live_ai_segment_size_km"), 10.0))
        state["live_ai_segment_next_target_km"] = round(max(next_size, (int(segment_index) + 1) * next_size), 2)
        state["live_ai_segment_baseline"] = _live_trip_ai_snapshot_from_state(state)
        state["live_ai_comment_status"] = "ready"
        state["live_ai_comment_source"] = source
        state["live_ai_comment_error"] = ""
        state["live_ai_last_generated_at"] = segment["generated_at"]
        state["live_ai_last_requested_index"] = int(segment_index)
        state["live_comment"] = segment["comment"]
        payload = load_live_trip_ai_segments_payload(hass, entry_id)
        payload["entry_id"] = str(entry_id or "")
        payload["started_at"] = str(state.get("started_at") or payload.get("started_at") or "")
        payload["updated_at"] = segment["generated_at"]
        payload["segments"] = state["live_ai_segments"]
        save_live_trip_ai_segments_payload(hass, entry_id, payload)
        notify_live_trip_sensor(hass, entry_id)
    except asyncio.CancelledError:
        raise
    except Exception as err:
        _LOGGER.exception("Live Trip AI segment task failed safely: %s", err)
        state = get_live_trip_state(hass, entry_id)
        state["live_ai_comment_status"] = "error"
        state["live_ai_comment_error"] = str(err)[:240]
        state["live_comment"] = "Live Trip comment could not be prepared right now." if str(state.get("report_language") or "").lower().startswith("en") else "Live Trip yorumu şu anda hazırlanamadı."
        notify_live_trip_sensor(hass, entry_id)
    finally:
        store = hass.data.setdefault(DOMAIN, {}).setdefault(LIVE_TRIP_AI_TASK_STORE, {})
        current_task = asyncio.current_task()
        if store.get(entry_id) is current_task:
            store.pop(entry_id, None)


async def async_maybe_schedule_live_trip_ai_segment(hass: HomeAssistant, entry_id: str, data: dict[str, Any]) -> None:
    """Queue an incremental Live Trip AI comment when the next distance threshold is reached."""
    data = get_live_entry_config_for_entry_id(hass, entry_id, data)
    state = get_live_trip_state(hass, entry_id)
    ensure_live_trip_ai_runtime_interval(hass, entry_id, data, realign_on_change=False)
    status = str((state or {}).get("status") or "").strip().lower()
    if not state or status not in {"active", "finishing", "finished"}:
        if state:
            _live_trip_ai_set_scheduler_debug(
                state,
                current_km=max(0.0, safe_float(state.get("trip_km"), 0.0)),
                next_target=max(1.0, safe_float(state.get("live_ai_segment_next_target_km"), 10.0)),
                segment_index=_live_trip_ai_next_segment_index(state),
                reason=f"status_not_ready:{status or 'empty'}",
                should_schedule=False,
            )
        return

    size_km = max(1.0, safe_float(state.get("live_ai_segment_size_km"), 10.0))
    segment_index = _live_trip_ai_next_segment_index(state)
    next_target = _live_trip_ai_next_threshold_km(state, size_km)
    state["live_ai_segment_next_target_km"] = next_target
    current_km = max(0.0, safe_float(state.get("trip_km"), 0.0))
    trigger_tolerance_km = 0.05  # 50 m guard for odometer/polling rounding.

    if current_km + trigger_tolerance_km < next_target:
        if not str(state.get("live_ai_comment_status") or "").strip():
            state["live_ai_comment_status"] = "waiting"
        _live_trip_ai_set_scheduler_debug(
            state,
            current_km=current_km,
            next_target=next_target,
            segment_index=segment_index,
            reason="waiting_for_distance",
            should_schedule=False,
        )
        return

    task_store = hass.data.setdefault(DOMAIN, {}).setdefault(LIVE_TRIP_AI_TASK_STORE, {})
    existing = task_store.get(entry_id)
    now_ts = datetime.now().timestamp()
    watchdog_seconds = 180.0
    last_prompt_ts = safe_float(state.get("live_ai_last_prompt_ts"), 0.0)
    generating_stale = last_prompt_ts > 0 and (now_ts - last_prompt_ts) > watchdog_seconds

    if existing is not None:
        if existing.done():
            task_store.pop(entry_id, None)
        elif generating_stale:
            _LOGGER.warning(
                "Live Trip AI segment task watchdog cancelled stale task. entry=%s segment=%s age=%.0fs",
                entry_id,
                segment_index,
                now_ts - last_prompt_ts,
            )
            existing.cancel()
            task_store.pop(entry_id, None)
        else:
            _live_trip_ai_set_scheduler_debug(
                state,
                current_km=current_km,
                next_target=next_target,
                segment_index=segment_index,
                reason="task_already_running",
                should_schedule=False,
            )
            return

    requested_index = int(safe_float(state.get("live_ai_last_requested_index"), 0.0))
    comment_status = str(state.get("live_ai_comment_status") or "").strip().lower()
    if requested_index >= segment_index and comment_status not in {"error", ""} and not generating_stale:
        _live_trip_ai_set_scheduler_debug(
            state,
            current_km=current_km,
            next_target=next_target,
            segment_index=segment_index,
            reason="segment_already_requested",
            should_schedule=False,
        )
        return

    baseline = state.get("live_ai_segment_baseline") if isinstance(state.get("live_ai_segment_baseline"), dict) and state.get("live_ai_segment_baseline") else _live_trip_ai_snapshot_from_state(state)
    state["live_ai_comment_status"] = "generating"
    state["live_ai_comment_error"] = ""
    state["live_ai_last_requested_index"] = segment_index
    prompt_now = datetime.now()
    state["live_ai_last_prompt_at"] = prompt_now.strftime("%d.%m.%Y %H:%M:%S")
    state["live_ai_last_prompt_ts"] = prompt_now.timestamp()
    if get_report_language(data) == APP_LANGUAGE_EN:
        state["live_comment"] = f"Preparing a comment for {_live_trip_ai_segment_label(segment_index, size_km)}..."
    else:
        state["live_comment"] = f"{_live_trip_ai_segment_label(segment_index, size_km)} için yorum hazırlanıyor..."
    _live_trip_ai_set_scheduler_debug(
        state,
        current_km=current_km,
        next_target=next_target,
        segment_index=segment_index,
        reason="scheduled",
        should_schedule=True,
    )
    notify_live_trip_sensor(hass, entry_id)
    task_store[entry_id] = hass.async_create_task(
        _async_live_trip_ai_segment_task(hass, entry_id, data, segment_index=segment_index, baseline=copy.deepcopy(baseline))
    )



def build_live_trip_public_attributes(state: dict[str, Any]) -> dict[str, Any]:
    """Return stable attributes for sensor.pom_live_trip."""
    return {
        "status": state.get("status", "idle"),
        "report_type": "live_trip",
        "report_language": str(state.get("report_language") or state.get("language") or APP_LANGUAGE_TR),
        "last_update": state.get("last_update", ""),
        "started_at": state.get("started_at", ""),
        "finished_at": state.get("finished_at", ""),
        "trip_km": round(safe_float(state.get("trip_km"), 0.0), 2),
        "duration_seconds": round(safe_float(state.get("duration_seconds"), 0.0), 0),
        "duration_text": state.get("duration_text", "—"),
        "report_duration_seconds": round(safe_float(state.get("report_duration_seconds", state.get("duration_seconds")), 0.0), 0),
        "report_duration_text": state.get("report_duration_text", state.get("duration_text", "—")),
        "total_elapsed_seconds": round(safe_float(state.get("total_elapsed_seconds"), 0.0), 0),
        "total_elapsed_text": state.get("total_elapsed_text", "—"),
        "final_park_wait_seconds": round(safe_float(state.get("final_park_wait_seconds"), 0.0), 0),
        "final_park_wait_text": state.get("final_park_wait_text", "—"),
        "traffic_seconds": round(safe_float(state.get("traffic_seconds"), 0.0), 0),
        "traffic_text": state.get("traffic_text", "—"),
        "stopped_in_drive_seconds": round(safe_float(state.get("stopped_in_drive_seconds"), 0.0), 0),
        "stopped_in_drive_text": state.get("stopped_in_drive_text", "—"),
        "slow_traffic_seconds": round(safe_float(state.get("slow_traffic_seconds"), 0.0), 0),
        "slow_traffic_text": state.get("slow_traffic_text", "—"),
        "normal_drive_seconds": round(safe_float(state.get("normal_drive_seconds"), 0.0), 0),
        "normal_drive_text": state.get("normal_drive_text", "—"),
        "parked_pause_seconds": round(safe_float(state.get("parked_pause_seconds"), 0.0), 0),
        "parked_pause_text": state.get("parked_pause_text", "—"),
        "last_traffic_class": state.get("last_traffic_class", ""),
        "traffic_model": state.get("traffic_model", ""),
        "traffic_model_label": state.get("traffic_model_label", ""),
        "traffic_delay_seconds": round(safe_float(state.get("traffic_delay_seconds"), 0.0), 0),
        "traffic_delay_text": state.get("traffic_delay_text", "—"),
        "traffic_congestion_percent": round(safe_float(state.get("traffic_congestion_percent"), 0.0), 1),
        "traffic_impact_label": state.get("traffic_impact_label", ""),
        "traffic_reference_speed_kmh": round(safe_float(state.get("traffic_reference_speed_kmh"), 0.0), 1),
        "traffic_free_flow_text": state.get("traffic_free_flow_text", "—"),
        "traffic_reference_trip_type_label": state.get("traffic_reference_trip_type_label", ""),
        "traffic_p85_speed_kmh": round(safe_float(state.get("traffic_p85_speed_kmh"), 0.0), 1),
        "moving_seconds": round(safe_float(state.get("moving_seconds"), 0.0), 0),
        "moving_text": state.get("moving_text", live_trip_short_duration(safe_float(state.get("moving_seconds"), 0.0))),
        "non_moving_seconds": round(safe_float(state.get("non_moving_seconds"), 0.0), 0),
        "average_speed": round(safe_float(state.get("average_moving_speed", state.get("average_speed")), 0.0), 1),
        "average_moving_speed": round(safe_float(state.get("average_moving_speed", state.get("average_speed")), 0.0), 1),
        "average_overall_speed": round(safe_float(state.get("average_overall_speed"), 0.0), 1),
        "speed_sample_count": int(safe_float(state.get("speed_sample_count"), 0.0)),
        "moving_speed_sample_count": int(safe_float(state.get("moving_speed_sample_count"), 0.0)),
        "max_speed": round(safe_float(state.get("max_speed"), 0.0), 1),
        "moving_speed_threshold": round(safe_float(state.get("moving_speed_threshold"), MOVING_SPEED_THRESHOLD_KMH), 1),
        "last_speed_sample": state.get("last_speed_sample", {}),
        "speed_sampler_interval_seconds": int(safe_float(state.get("speed_sampler_interval_seconds"), SPEED_SAMPLER_INTERVAL_SECONDS)),
        "speed_sampler_last_update": state.get("speed_sampler_last_update", ""),
        "used_kwh": round(safe_float(state.get("used_kwh"), 0.0), 2),
        "used_battery": round(safe_float(state.get("used_battery"), 0.0), 1),
        "consumption_kwh_100km": round(safe_float(state.get("consumption_kwh_100km"), 0.0), 2),
        "start_battery": round(safe_float(state.get("start_battery"), 0.0), 1),
        "end_battery": round(safe_float(state.get("end_battery"), 0.0), 1),
        "battery_text": state.get("battery_text", "—"),
        "climate_seconds": round(safe_float(state.get("climate_seconds"), 0.0), 0),
        "climate_text": state.get("climate_text", "—"),
        "min_elevation": round(safe_float(state.get("min_elevation"), 0.0), 0),
        "max_elevation": round(safe_float(state.get("max_elevation"), 0.0), 0),
        "elevation_range": round(safe_float(state.get("elevation_range"), 0.0), 0),
        "elevation_gain": round(safe_float(state.get("elevation_gain"), 0.0), 0),
        "elevation_loss": round(safe_float(state.get("elevation_loss"), 0.0), 0),
        "elevation_sample_count": int(safe_float(state.get("elevation_sample_count"), 0.0)),
        "elevation_provider": state.get("elevation_provider", ""),
        "elevation_source": state.get("elevation_source", ""),
        "zes_kwh_price": round(safe_float(state.get("zes_kwh_price"), 0.0), 2),
        "zes_trip_cost": round(safe_float(state.get("zes_trip_cost"), 0.0), 2),
        "supercharger_kwh_price": round(safe_float(state.get("supercharger_kwh_price"), 0.0), 2),
        "supercharger_trip_cost": round(safe_float(state.get("supercharger_trip_cost"), 0.0), 2),
        "astor_kwh_price": round(safe_float(state.get("astor_kwh_price"), 0.0), 2),
        "astor_trip_cost": round(safe_float(state.get("astor_trip_cost"), 0.0), 2),
        "trip_status": state.get("trip_status", ""),
        "candidate_trip": bool(state.get("candidate_trip", False)),
        "candidate_confirmed": bool(state.get("candidate_confirmed", False)),
        "candidate_min_distance_km": round(safe_float(state.get("candidate_min_distance_km"), 0.0), 3),
        "candidate_min_duration_seconds": round(safe_float(state.get("candidate_min_duration_seconds"), 0.0), 0),
        "ignore_short_maneuvers_enabled": bool(state.get("ignore_short_maneuvers_enabled", False)),
        "ignored_short_maneuver": bool(state.get("ignored_short_maneuver", False)),
        "short_maneuver_reason": state.get("short_maneuver_reason", ""),
        "live_comment": state.get("live_comment", ""),
        "ai_live_comment_status": state.get("live_ai_comment_status", "waiting"),
        "ai_live_comment_source": state.get("live_ai_comment_source", ""),
        "ai_live_comment_error": state.get("live_ai_comment_error", ""),
        "ai_live_last_generated_at": state.get("live_ai_last_generated_at", ""),
        "ai_live_last_prompt_at": state.get("live_ai_last_prompt_at", ""),
        "ai_live_last_prompt_ts": round(safe_float(state.get("live_ai_last_prompt_ts"), 0.0), 3),
        "ai_live_scheduler_debug": state.get("live_ai_scheduler_debug", {}),
        "ai_live_segment_size_km": round(safe_float(state.get("live_ai_segment_size_km"), DEFAULT_LIVE_TRIP_AI_SEGMENT_DISTANCE_KM), 1),
        "ai_live_last_completed_index": int(safe_float(state.get("live_ai_segment_last_completed_index"), 0.0)),
        "live_ai_segment_last_completed_index": int(safe_float(state.get("live_ai_segment_last_completed_index"), 0.0)),
        "ai_live_last_requested_index": int(safe_float(state.get("live_ai_last_requested_index"), 0.0)),
        "ai_live_next_target_km": round(_live_trip_ai_reconciled_next_target_km(state), 1),
        "ai_live_waiting_text": _build_live_trip_ai_waiting_text(state, lang=str(state.get("report_language") or state.get("language") or APP_LANGUAGE_TR)),
        "ai_live_latest_segment": state.get("live_ai_latest_segment", {}),
        "ai_live_segments": state.get("live_ai_segments", []),
        "finish_delay_seconds": round(safe_float(state.get("finish_delay_seconds"), 0.0), 0),
        "finish_delay_minutes": round(safe_float(state.get("finish_delay_minutes"), 0.0), 2),
        "inactive_remaining_seconds": round(safe_float(state.get("inactive_remaining_seconds"), 0.0), 0),
        "inactive_remaining_text": live_trip_short_duration(safe_float(state.get("inactive_remaining_seconds"), 0.0)),
        "test_mode": bool(state.get("test_mode", False)),
        "test_progress": round(safe_float(state.get("test_progress"), 0.0), 3),
        "source": state.get("source", "POM live trip calculation engine"),
    }


def notify_live_trip_sensor(hass: HomeAssistant, entry_id: str) -> None:
    """Ask the sensor platform to write the latest live trip state."""
    sensor = hass.data.get(DOMAIN, {}).get(LIVE_TRIP_SENSOR_STORE, {}).get(entry_id)
    if sensor is not None:
        try:
            sensor.async_write_ha_state()
        except Exception:
            _LOGGER.debug("POM live trip sensor state update skipped", exc_info=True)


def get_trip_elevation_state(hass: HomeAssistant, entry_id: str) -> dict[str, Any]:
    """Return elevation tracking state bucket for an entry."""
    root = hass.data.setdefault(DOMAIN, {})
    store = root.setdefault(TRIP_ELEVATION_STATE_STORE, {})
    return store.setdefault(entry_id, {})


def get_trip_elevation_cache(hass: HomeAssistant) -> dict[str, Any]:
    """Return shared rounded-coordinate elevation cache."""
    root = hass.data.setdefault(DOMAIN, {})
    return root.setdefault(TRIP_ELEVATION_CACHE_STORE, {})


def notify_trip_elevation_sensor(hass: HomeAssistant, entry_id: str) -> None:
    """Ask the elevation sensor platform to write the latest elevation state."""
    sensor = hass.data.get(DOMAIN, {}).get(TRIP_ELEVATION_SENSOR_STORE, {}).get(entry_id)
    if sensor is not None:
        try:
            sensor.async_write_ha_state()
        except Exception:
            _LOGGER.debug("POM trip elevation sensor state update skipped", exc_info=True)


def build_trip_elevation_public_attributes(state: dict[str, Any]) -> dict[str, Any]:
    """Return stable attributes for sensor.pom_trip_elevation."""
    recent_samples = state.get("samples", [])
    if not isinstance(recent_samples, list):
        recent_samples = []
    return {
        "status": state.get("status", "idle"),
        "provider": state.get("provider", TRIP_ELEVATION_PROVIDER),
        "source": state.get("source", ""),
        "session_key": state.get("session_key", ""),
        "started_at": state.get("started_at", ""),
        "last_update": state.get("last_update", ""),
        "last_api_call": state.get("last_api_call", ""),
        "last_error": state.get("last_error", ""),
        "tracker_entity": state.get("tracker_entity", ""),
        "latitude": round(safe_float(state.get("lat"), 0.0), 7) if state.get("lat") is not None else None,
        "longitude": round(safe_float(state.get("lon"), 0.0), 7) if state.get("lon") is not None else None,
        "last_movement_meters": round(safe_float(state.get("last_movement_meters"), 0.0), 1),
        "last_elevation_m": round(safe_float(state.get("elevation"), 0.0), 1) if state.get("elevation") is not None else None,
        "min_elevation_m": round(safe_float(state.get("min_elevation"), 0.0), 1) if state.get("min_elevation") is not None else None,
        "max_elevation_m": round(safe_float(state.get("max_elevation"), 0.0), 1) if state.get("max_elevation") is not None else None,
        "elevation_range_m": round(safe_float(state.get("elevation_range"), 0.0), 1),
        "elevation_gain_m": round(safe_float(state.get("elevation_gain"), 0.0), 1),
        "elevation_loss_m": round(safe_float(state.get("elevation_loss"), 0.0), 1),
        "sample_count": int(safe_float(state.get("sample_count"), 0.0)),
        "api_call_count": int(safe_float(state.get("api_call_count"), 0.0)),
        "cache_hit_count": int(safe_float(state.get("cache_hit_count"), 0.0)),
        "recent_samples": recent_samples[-10:],
    }


def get_internal_trip_elevation_value(hass: HomeAssistant, entry_id: str, default: float = 0.0) -> float:
    """Return current Open-Meteo elevation if available."""
    state = get_trip_elevation_state(hass, entry_id)
    if state.get("elevation") is None:
        return default
    return safe_float(state.get("elevation"), default)


def _trip_elevation_cache_key(lat: float, lon: float) -> str:
    """Return a cache key aligned with the 90m DEM scale."""
    return f"{round(lat, 4):.4f},{round(lon, 4):.4f}"


def _active_elevation_context(hass: HomeAssistant, entry_id: str) -> tuple[str, dict[str, Any], str] | None:
    """Return the currently active trip context for elevation sampling."""
    live_state = get_live_trip_state(hass, entry_id)
    live_status = str(live_state.get("status") or "").strip().lower()
    if live_state.get("active") or live_status in {"active", "finishing"}:
        started = str(live_state.get("started_at") or live_state.get("start_ts") or "").strip()
        return "live_trip", live_state, f"live_trip:{started}"

    for state_key, source in (
        (TRIP_STATE_KEY, "trip"),
        (MANUAL_TRACKING_STATE_KEY, "manual_tracking"),
    ):
        trip_state = get_named_state(hass, state_key)
        if trip_state.get("active"):
            started = str(trip_state.get("started_at") or trip_state.get("start_ts") or "").strip()
            return source, trip_state, f"{source}:{started}"

    return None


async def async_fetch_open_meteo_elevation(hass: HomeAssistant, lat: float, lon: float) -> float | None:
    """Fetch terrain elevation from Open-Meteo."""
    session = async_get_clientsession(hass)
    params = {
        "latitude": f"{lat:.6f}",
        "longitude": f"{lon:.6f}",
    }
    async with session.get(TRIP_ELEVATION_API_URL, params=params, timeout=10) as response:
        if response.status != 200:
            body = await response.text()
            raise RuntimeError(f"Open-Meteo elevation HTTP {response.status}: {body[:160]}")
        payload = await response.json()

    value: Any = None
    if isinstance(payload, dict):
        elevation = payload.get("elevation")
        if isinstance(elevation, list) and elevation:
            value = elevation[0]
        else:
            value = elevation

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _apply_elevation_sample_to_trip_state(
    trip_state: dict[str, Any],
    *,
    ts_text: str,
    lat: float,
    lon: float,
    elevation: float,
    source: str,
) -> None:
    """Apply an elevation sample to active trip/live-trip state."""
    if elevation is None:
        return

    old_last = trip_state.get("last_elevation")
    previous = safe_float(old_last, elevation)
    old_count = int(safe_float(trip_state.get("elevation_sample_count"), 0.0))
    old_min = trip_state.get("min_elevation")
    old_max = trip_state.get("max_elevation")

    if old_count <= 0 or old_min is None or old_max is None or (safe_float(old_min, 0.0) == 0.0 and safe_float(old_max, 0.0) == 0.0):
        trip_state["min_elevation"] = elevation
        trip_state["max_elevation"] = elevation
    else:
        trip_state["min_elevation"] = min(safe_float(old_min, elevation), elevation)
        trip_state["max_elevation"] = max(safe_float(old_max, elevation), elevation)

    delta = elevation - previous
    if old_count > 0 and abs(delta) >= TRIP_ELEVATION_NOISE_THRESHOLD_METERS:
        if delta > 0:
            trip_state["elevation_gain"] = safe_float(trip_state.get("elevation_gain"), 0.0) + delta
        else:
            trip_state["elevation_loss"] = safe_float(trip_state.get("elevation_loss"), 0.0) + abs(delta)

    trip_state["last_elevation"] = elevation
    trip_state["elevation_range"] = max(0.0, safe_float(trip_state.get("max_elevation"), elevation) - safe_float(trip_state.get("min_elevation"), elevation))
    trip_state["elevation_sample_count"] = old_count + 1
    trip_state["elevation_provider"] = TRIP_ELEVATION_PROVIDER
    trip_state["elevation_source"] = source

    samples = trip_state.setdefault("elevation_samples", [])
    if not isinstance(samples, list):
        samples = []
        trip_state["elevation_samples"] = samples
    samples.append({
        "ts": ts_text,
        "lat": round(lat, 7),
        "lon": round(lon, 7),
        "elevation": round(elevation, 1),
    })
    if len(samples) > TRIP_ELEVATION_MAX_SAMPLES:
        del samples[:-TRIP_ELEVATION_MAX_SAMPLES]



async def async_bootstrap_trip_elevation_from_current_location(
    hass: HomeAssistant,
    entry_id: str,
    data: dict[str, Any],
) -> None:
    """Fetch one idle/current-location elevation sample when no trip is active.

    The numeric sensor should not stay unknown forever after install if the
    selected tracker already has coordinates. This does not start a trip and
    does not write trip samples; it only gives the sensor a current elevation
    baseline and keeps attributes clear.
    """
    state = get_trip_elevation_state(hass, entry_id)
    context = _active_elevation_context(hass, entry_id)
    if context is not None:
        return
    if state.get("elevation") is not None:
        return

    now = datetime.now()
    now_text = now.strftime("%d.%m.%Y %H:%M:%S")
    tracker_entity = (
        get_vehicle_role_entity(data, VEHICLE_ROLE_LOCATION_TRACKER, usage_key="use_map")
        or data.get(CONF_TRIP_MAP_TRACKER_ENTITY, DEFAULT_TRIP_MAP_TRACKER_ENTITY)
    )
    tracker_entity = str(tracker_entity or "").strip()
    point = get_tracker_lat_lon(hass, tracker_entity)
    if point is None:
        state.update({
            "status": "idle_no_coordinates",
            "provider": TRIP_ELEVATION_PROVIDER,
            "source": "idle",
            "tracker_entity": tracker_entity,
            "last_update": now_text,
            "last_error": "No latitude/longitude from tracker entity.",
        })
        notify_trip_elevation_sensor(hass, entry_id)
        return

    lat, lon = point
    cache = get_trip_elevation_cache(hass)
    key = _trip_elevation_cache_key(lat, lon)
    cached = cache.get(key)
    from_cache = cached is not None

    try:
        if from_cache:
            elevation = safe_float(cached, 0.0)
            state["cache_hit_count"] = int(safe_float(state.get("cache_hit_count"), 0.0)) + 1
        else:
            fetched = await async_fetch_open_meteo_elevation(hass, lat, lon)
            if fetched is None:
                raise RuntimeError("Open-Meteo elevation response did not include a numeric elevation.")
            elevation = float(fetched)
            cache[key] = elevation
            state["api_call_count"] = int(safe_float(state.get("api_call_count"), 0.0)) + 1
            state["last_api_call"] = now_text
    except (ClientError, asyncio.TimeoutError, RuntimeError) as err:
        state.update({
            "status": "idle_error",
            "provider": TRIP_ELEVATION_PROVIDER,
            "source": "idle",
            "tracker_entity": tracker_entity,
            "lat": lat,
            "lon": lon,
            "last_update": now_text,
            "last_error": str(err),
        })
        notify_trip_elevation_sensor(hass, entry_id)
        return

    sample = {
        "ts": now_text,
        "lat": round(lat, 7),
        "lon": round(lon, 7),
        "elevation": round(elevation, 1),
    }
    state.update({
        "status": "idle_current_location_cached" if from_cache else "idle_current_location",
        "provider": TRIP_ELEVATION_PROVIDER,
        "source": "idle",
        "session_key": "",
        "tracker_entity": tracker_entity,
        "lat": lat,
        "lon": lon,
        "elevation": elevation,
        "min_elevation": elevation,
        "max_elevation": elevation,
        "elevation_range": 0.0,
        "elevation_gain": 0.0,
        "elevation_loss": 0.0,
        "sample_count": max(1, int(safe_float(state.get("sample_count"), 0.0))),
        "last_update": now_text,
        "last_movement_meters": 0.0,
        "last_error": "",
        "samples": [sample],
    })
    notify_trip_elevation_sensor(hass, entry_id)

async def async_update_trip_elevation_sample(
    hass: HomeAssistant,
    entry_id: str,
    data: dict[str, Any],
) -> None:
    """Sample vehicle coordinates and update Open-Meteo elevation during active trips."""
    state = get_trip_elevation_state(hass, entry_id)
    now = datetime.now()
    now_ts = now.timestamp()
    now_text = now.strftime("%d.%m.%Y %H:%M:%S")

    context = _active_elevation_context(hass, entry_id)
    if context is None:
        if state.get("elevation") is None:
            await async_bootstrap_trip_elevation_from_current_location(hass, entry_id, data)
            return
        if state.get("status") not in {"idle_current_location", "idle_current_location_cached", "idle_error", "idle_no_coordinates"}:
            state["status"] = "idle_current_location"
            state["last_update"] = now_text
            notify_trip_elevation_sensor(hass, entry_id)
        return

    source, trip_state, session_key = context
    tracker_entity = (
        get_vehicle_role_entity(data, VEHICLE_ROLE_LOCATION_TRACKER, usage_key="use_map")
        or data.get(CONF_TRIP_MAP_TRACKER_ENTITY, DEFAULT_TRIP_MAP_TRACKER_ENTITY)
    )
    tracker_entity = str(tracker_entity or "").strip()
    point = get_tracker_lat_lon(hass, tracker_entity)
    if point is None:
        state.update({
            "status": "no_coordinates",
            "source": source,
            "session_key": session_key,
            "tracker_entity": tracker_entity,
            "last_update": now_text,
            "last_error": "No latitude/longitude from tracker entity.",
        })
        notify_trip_elevation_sensor(hass, entry_id)
        return

    lat, lon = point

    if state.get("session_key") != session_key:
        state.clear()
        state.update({
            "status": "active",
            "provider": TRIP_ELEVATION_PROVIDER,
            "source": source,
            "session_key": session_key,
            "started_at": now_text,
            "samples": [],
            "sample_count": 0,
            "api_call_count": 0,
            "cache_hit_count": 0,
            "elevation_gain": 0.0,
            "elevation_loss": 0.0,
            "last_error": "",
        })

    last_lat = state.get("lat")
    last_lon = state.get("lon")
    try:
        moved_m = haversine_distance_meters(float(last_lat), float(last_lon), lat, lon)
    except Exception:
        moved_m = 999999.0

    min_movement = max(
        5.0,
        safe_float(data.get(CONF_TRIP_MAP_MIN_MOVEMENT_METERS), DEFAULT_TRIP_MAP_MIN_MOVEMENT_METERS),
    )
    if state.get("elevation") is not None and moved_m < min_movement:
        state.update({
            "status": "active",
            "source": source,
            "tracker_entity": tracker_entity,
            "last_update": now_text,
            "last_movement_meters": round(moved_m, 1),
            "last_error": "",
        })
        notify_trip_elevation_sensor(hass, entry_id)
        return

    cache = get_trip_elevation_cache(hass)
    key = _trip_elevation_cache_key(lat, lon)
    cached = cache.get(key)
    from_cache = cached is not None

    try:
        if from_cache:
            elevation = safe_float(cached, 0.0)
            state["cache_hit_count"] = int(safe_float(state.get("cache_hit_count"), 0.0)) + 1
        else:
            fetched = await async_fetch_open_meteo_elevation(hass, lat, lon)
            if fetched is None:
                raise RuntimeError("Open-Meteo elevation response did not include a numeric elevation.")
            elevation = float(fetched)
            cache[key] = elevation
            state["api_call_count"] = int(safe_float(state.get("api_call_count"), 0.0)) + 1
            state["last_api_call"] = now_text
            if len(cache) > TRIP_ELEVATION_CACHE_MAX_SIZE:
                for old_key in list(cache.keys())[: max(0, len(cache) - TRIP_ELEVATION_CACHE_MAX_SIZE)]:
                    cache.pop(old_key, None)
    except (ClientError, asyncio.TimeoutError, RuntimeError) as err:
        state.update({
            "status": "error",
            "source": source,
            "session_key": session_key,
            "tracker_entity": tracker_entity,
            "lat": lat,
            "lon": lon,
            "last_update": now_text,
            "last_movement_meters": round(moved_m, 1),
            "last_error": str(err),
        })
        notify_trip_elevation_sensor(hass, entry_id)
        return

    previous = state.get("elevation")
    previous_value = safe_float(previous, elevation)
    old_count = int(safe_float(state.get("sample_count"), 0.0))
    if old_count <= 0 or state.get("min_elevation") is None or state.get("max_elevation") is None:
        state["min_elevation"] = elevation
        state["max_elevation"] = elevation
    else:
        state["min_elevation"] = min(safe_float(state.get("min_elevation"), elevation), elevation)
        state["max_elevation"] = max(safe_float(state.get("max_elevation"), elevation), elevation)

    delta = elevation - previous_value
    if old_count > 0 and abs(delta) >= TRIP_ELEVATION_NOISE_THRESHOLD_METERS:
        if delta > 0:
            state["elevation_gain"] = safe_float(state.get("elevation_gain"), 0.0) + delta
        else:
            state["elevation_loss"] = safe_float(state.get("elevation_loss"), 0.0) + abs(delta)

    samples = state.setdefault("samples", [])
    if not isinstance(samples, list):
        samples = []
        state["samples"] = samples
    sample = {
        "ts": now_text,
        "lat": round(lat, 7),
        "lon": round(lon, 7),
        "elevation": round(elevation, 1),
    }
    samples.append(sample)
    if len(samples) > TRIP_ELEVATION_MAX_SAMPLES:
        del samples[:-TRIP_ELEVATION_MAX_SAMPLES]

    state.update({
        "status": "active_cached" if from_cache else "active",
        "provider": TRIP_ELEVATION_PROVIDER,
        "source": source,
        "session_key": session_key,
        "tracker_entity": tracker_entity,
        "lat": lat,
        "lon": lon,
        "elevation": elevation,
        "last_update": now_text,
        "last_movement_meters": round(moved_m, 1),
        "elevation_range": max(0.0, safe_float(state.get("max_elevation"), elevation) - safe_float(state.get("min_elevation"), elevation)),
        "sample_count": old_count + 1,
        "last_error": "",
    })

    _apply_elevation_sample_to_trip_state(
        trip_state,
        ts_text=now_text,
        lat=lat,
        lon=lon,
        elevation=elevation,
        source="open_meteo_cache" if from_cache else "open_meteo_api",
    )

    if source == "live_trip":
        notify_live_trip_sensor(hass, entry_id)
    notify_trip_elevation_sensor(hass, entry_id)



def cancel_live_trip_test_task(hass: HomeAssistant, entry_id: str) -> None:
    """Cancel a running live trip simulator task for an entry."""
    root = hass.data.setdefault(DOMAIN, {})
    tasks = root.setdefault(LIVE_TRIP_TEST_TASK_STORE, {})
    task = tasks.pop(entry_id, None)
    if task is not None and not task.done():
        task.cancel()


async def run_live_trip_test_simulator(
    hass: HomeAssistant,
    entry_id: str,
    data: dict[str, Any],
    params: dict[str, Any],
) -> None:
    """Animate sensor.pom_live_trip with simulated trip data."""
    state = get_live_trip_state(hass, entry_id)

    duration_minutes = max(0.1, safe_float(params.get("duration_minutes"), 18.0))
    distance_km = max(0.0, safe_float(params.get("distance_km"), 3.39))
    used_kwh_total = max(0.0, safe_float(params.get("used_kwh"), 0.62))
    start_battery = max(0.0, min(100.0, safe_float(params.get("start_battery"), 54.0)))
    end_battery = max(0.0, min(100.0, safe_float(params.get("end_battery"), 53.0)))
    min_elevation = safe_float(params.get("min_elevation"), 26.0)
    max_elevation = safe_float(params.get("max_elevation"), 49.0)
    traffic_minutes_total = max(0.0, min(duration_minutes, safe_float(params.get("traffic_minutes"), duration_minutes)))
    climate_minutes_total = max(0.0, min(duration_minutes, safe_float(params.get("climate_minutes"), duration_minutes)))
    speed_multiplier = max(0.1, safe_float(params.get("speed_multiplier"), 12.0))
    update_interval = max(0.5, min(10.0, safe_float(params.get("update_interval_seconds"), 1.0)))

    real_duration_seconds = max(2.0, (duration_minutes * 60.0) / speed_multiplier)
    simulated_total_seconds = duration_minutes * 60.0
    started_dt = datetime.now()
    started_ts = started_dt.timestamp()

    zes_price = safe_float(data.get(CONF_ZES_PRICE), DEFAULT_ZES_PRICE)
    supercharger_price = safe_float(data.get(CONF_SUPERCHARGER_PRICE), DEFAULT_SUPERCHARGER_PRICE)
    astor_price = safe_float(data.get(CONF_ASTOR_PRICE), DEFAULT_ASTOR_PRICE)

    def write_progress(progress: float, status: str) -> None:
        now_dt = datetime.now()
        simulated_seconds = simulated_total_seconds * progress
        trip_km = distance_km * progress
        used_kwh = used_kwh_total * progress
        current_battery = start_battery - ((start_battery - end_battery) * progress)
        used_battery = max(0.0, start_battery - current_battery)
        traffic_seconds = min(simulated_seconds, traffic_minutes_total * 60.0 * progress)
        climate_seconds = min(simulated_seconds, climate_minutes_total * 60.0 * progress)
        current_max_elevation = min_elevation + ((max_elevation - min_elevation) * progress)
        elevation_range = max(0.0, current_max_elevation - min_elevation)
        average_speed = (trip_km / (simulated_seconds / 3600.0)) if simulated_seconds > 0 else 0.0
        consumption = (used_kwh / trip_km * 100.0) if trip_km > 0 else 0.0

        if status == "finished":
            trip_status = "Test sürüşü tamamlandı. Final değerler kart üzerinde gösteriliyor."
        else:
            trip_status = "Test sürüşü devam ediyor. Canlı kart simülasyon verileriyle güncelleniyor."

        state.update({
            "test_mode": True,
            "test_progress": round(progress, 3),
            "source": "POM live trip test simulator",
            "test_params": dict(params),
            "active": status == "active",
            "status": status,
            "started_at": started_dt.strftime("%d.%m.%Y %H:%M:%S"),
            "finished_at": now_dt.strftime("%d.%m.%Y %H:%M:%S") if status == "finished" else "",
            "start_ts": started_ts,
            "last_ts": now_dt.timestamp(),
            "last_update": now_dt.strftime("%d.%m.%Y %H:%M:%S"),
            "trip_km": round(trip_km, 3),
            "duration_seconds": round(simulated_seconds, 0),
            "duration_text": live_trip_short_duration(simulated_seconds),
            "traffic_seconds": round(traffic_seconds, 0),
            "traffic_text": live_trip_short_duration(traffic_seconds),
            "average_speed": round(average_speed, 1),
            "used_kwh": round(used_kwh, 3),
            "used_battery": round(used_battery, 1),
            "consumption_kwh_100km": round(consumption, 2),
            "start_battery": round(start_battery, 1),
            "end_battery": round(current_battery, 1),
            "battery_text": f"%{start_battery:.1f} -> %{current_battery:.1f}",
            "climate_seconds": round(climate_seconds, 0),
            "climate_text": live_trip_short_duration(climate_seconds),
            "min_elevation": round(min_elevation, 0),
            "max_elevation": round(current_max_elevation, 0),
            "elevation_range": round(elevation_range, 0),
            "zes_kwh_price": round(zes_price, 2),
            "zes_trip_cost": round(used_kwh * zes_price, 2),
            "supercharger_kwh_price": round(supercharger_price, 2),
            "supercharger_trip_cost": round(used_kwh * supercharger_price, 2),
            "astor_kwh_price": round(astor_price, 2),
            "astor_trip_cost": round(used_kwh * astor_price, 2),
            "trip_status": trip_status,
            "live_comment": "Live Trip Test Simulator",
        })
        notify_live_trip_sensor(hass, entry_id)

    try:
        write_progress(0.0, "active")
        while True:
            elapsed_real = max(0.0, datetime.now().timestamp() - started_ts)
            progress = min(1.0, elapsed_real / real_duration_seconds)
            if progress >= 1.0:
                write_progress(1.0, "finished")
                state = get_live_trip_state(hass, entry_id)
                data["_live_trip_test_auto_report_sent"] = True
                await async_generate_live_trip_test_report(
                    hass,
                    entry_id,
                    data,
                    state,
                    send_telegram=True,
                    caption="🚗 Tesla AI - Live Trip Test Raporu",
                    output_path="/config/www/pom_tesla_report/live_trip_test_report.png",
                    telegram_target=str(state.get("test_telegram_target") or "").strip() or None,
                )
                break
            write_progress(progress, "active")
            await asyncio.sleep(update_interval)
    except asyncio.CancelledError:
        raise
    except Exception:
        _LOGGER.exception("POM live trip test simulator failed")
    finally:
        tasks = hass.data.setdefault(DOMAIN, {}).setdefault(LIVE_TRIP_TEST_TASK_STORE, {})
        current_task = asyncio.current_task()
        if tasks.get(entry_id) is current_task:
            tasks.pop(entry_id, None)

def _live_trip_params_for_final_state(state: dict[str, Any]) -> dict[str, Any]:
    """Return stored simulator params with safe fallbacks."""
    params = state.get("test_params") if isinstance(state.get("test_params"), dict) else {}
    return dict(params or {})


def finalize_live_trip_test_state_from_params(
    hass: HomeAssistant,
    entry_id: str,
    data: dict[str, Any],
    state: dict[str, Any],
) -> None:
    """Force the simulated live trip state to full final values."""
    params = _live_trip_params_for_final_state(state)
    duration_minutes = max(1.0, safe_float(params.get("duration_minutes"), safe_float(state.get("duration_seconds"), 18 * 60) / 60.0 or 18.0))
    distance_km = max(0.0, safe_float(params.get("distance_km"), safe_float(state.get("trip_km"), 3.39)))
    used_kwh = max(0.0, safe_float(params.get("used_kwh"), safe_float(state.get("used_kwh"), 0.62)))
    start_battery = max(0.0, min(100.0, safe_float(params.get("start_battery"), safe_float(state.get("start_battery"), 54.0))))
    end_battery = max(0.0, min(100.0, safe_float(params.get("end_battery"), safe_float(state.get("end_battery"), 53.0))))
    min_elevation = safe_float(params.get("min_elevation"), safe_float(state.get("min_elevation"), 26.0))
    max_elevation = safe_float(params.get("max_elevation"), safe_float(state.get("max_elevation"), 49.0))
    traffic_minutes = max(0.0, min(duration_minutes, safe_float(params.get("traffic_minutes"), duration_minutes)))
    climate_minutes = max(0.0, min(duration_minutes, safe_float(params.get("climate_minutes"), duration_minutes)))

    duration_seconds = duration_minutes * 60.0
    traffic_seconds = traffic_minutes * 60.0
    climate_seconds = climate_minutes * 60.0
    average_speed = (distance_km / (duration_seconds / 3600.0)) if duration_seconds > 0 else 0.0
    consumption = (used_kwh / distance_km * 100.0) if distance_km > 0 else 0.0
    used_battery = max(0.0, start_battery - end_battery)
    elevation_range = max(0.0, max_elevation - min_elevation)

    zes_price = safe_float(data.get(CONF_ZES_PRICE), DEFAULT_ZES_PRICE)
    supercharger_price = safe_float(data.get(CONF_SUPERCHARGER_PRICE), DEFAULT_SUPERCHARGER_PRICE)
    astor_price = safe_float(data.get(CONF_ASTOR_PRICE), DEFAULT_ASTOR_PRICE)
    now_dt = datetime.now()
    started_at = str(state.get("started_at") or now_dt.strftime("%d.%m.%Y %H:%M:%S"))

    state.update({
        "test_mode": True,
        "test_progress": 1.0,
        "source": "POM live trip test simulator",
        "active": False,
        "status": "finished",
        "started_at": started_at,
        "finished_at": now_dt.strftime("%d.%m.%Y %H:%M:%S"),
        "last_update": now_dt.strftime("%d.%m.%Y %H:%M:%S"),
        "trip_km": round(distance_km, 3),
        "duration_seconds": round(duration_seconds, 0),
        "duration_text": live_trip_short_duration(duration_seconds),
        "traffic_seconds": traffic_debug.get("traffic_seconds", round(traffic_seconds, 0)),
        "traffic_text": traffic_debug.get("traffic_text", live_trip_short_duration(traffic_seconds)),
        "stopped_in_drive_seconds": traffic_debug.get("stopped_in_drive_seconds", 0),
        "stopped_in_drive_text": traffic_debug.get("stopped_in_drive_text", "—"),
        "slow_traffic_seconds": traffic_debug.get("slow_traffic_seconds", 0),
        "slow_traffic_text": traffic_debug.get("slow_traffic_text", "—"),
        "normal_drive_seconds": traffic_debug.get("normal_drive_seconds", 0),
        "normal_drive_text": traffic_debug.get("normal_drive_text", "—"),
        "parked_pause_seconds": traffic_debug.get("parked_pause_seconds", 0),
        "parked_pause_text": traffic_debug.get("parked_pause_text", "—"),
        "last_traffic_class": traffic_debug.get("last_traffic_class", ""),
        "average_speed": round(average_speed, 1),
        "average_moving_speed": round(average_moving_speed, 1),
        "average_overall_speed": round(average_overall_speed, 1),
        "moving_seconds": speed_debug.get("moving_seconds", 0),
        "moving_text": speed_debug.get("moving_duration_text", "—"),
        "non_moving_seconds": speed_debug.get("non_moving_seconds", 0),
        "speed_sample_count": speed_debug.get("speed_sample_count", 0),
        "moving_speed_sample_count": speed_debug.get("moving_speed_sample_count", 0),
        "max_speed": speed_debug.get("max_speed", 0.0),
        "moving_speed_threshold": speed_debug.get("moving_speed_threshold", MOVING_SPEED_THRESHOLD_KMH),
        "last_speed_sample": speed_debug.get("last_speed_sample", {}),
        "speed_sampler_interval_seconds": SPEED_SAMPLER_INTERVAL_SECONDS,
        "speed_sampler_last_update": state.get("speed_sampler_last_update", ""),
        "used_kwh": round(used_kwh, 3),
        "used_battery": round(used_battery, 1),
        "consumption_kwh_100km": round(consumption, 2),
        "start_battery": round(start_battery, 1),
        "end_battery": round(end_battery, 1),
        "battery_text": "—" if display_status == "idle" or start_battery <= 0 else f"%{start_battery:.1f} -> %{end_battery:.1f}",
        "climate_seconds": round(climate_seconds, 0),
        "climate_text": live_trip_short_duration(climate_seconds),
        "min_elevation": round(min_elevation, 0),
        "max_elevation": round(max_elevation, 0),
        "elevation_range": round(elevation_range, 0),
        "zes_kwh_price": round(zes_price, 2),
        "zes_trip_cost": round(used_kwh * zes_price, 2),
        "supercharger_kwh_price": round(supercharger_price, 2),
        "supercharger_trip_cost": round(used_kwh * supercharger_price, 2),
        "astor_kwh_price": round(astor_price, 2),
        "astor_trip_cost": round(used_kwh * astor_price, 2),
        "trip_status": "Test sürüşü tamamlandı. PNG raporu üretildi.",
        "live_comment": "Live Trip Test Simulator",
        "test_params": params,
    })
    notify_live_trip_sensor(hass, entry_id)


def build_live_trip_report_data_from_state(state: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
    """Convert sensor.pom_live_trip state into the normal trip report PNG payload."""
    duration_seconds = safe_float(state.get("duration_seconds"), 0.0)
    traffic_seconds = safe_float(state.get("traffic_seconds"), 0.0)
    climate_seconds = safe_float(state.get("climate_seconds"), 0.0)
    used_kwh_value = safe_float(state.get("used_kwh"), 0.0)
    supercharger_price = safe_float(data.get(CONF_SUPERCHARGER_PRICE), DEFAULT_SUPERCHARGER_PRICE)
    zes_price = safe_float(data.get(CONF_ZES_PRICE), DEFAULT_ZES_PRICE)
    astor_price = safe_float(data.get(CONF_ASTOR_PRICE), DEFAULT_ASTOR_PRICE)
    return {
        "test_mode": True,
        "currency_label": get_report_currency(data),
        "report_date": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "trip_km": f"{safe_float(state.get('trip_km'), 0.0):.2f}",
        "duration_minutes": round(duration_seconds / 60.0, 2),
        "duration_text": live_trip_short_duration(duration_seconds),
        "report_duration_seconds": round(duration_seconds, 0),
        "report_duration_text": live_trip_short_duration(duration_seconds),
        "total_elapsed_seconds": round(safe_float(state.get("total_elapsed_seconds"), 0.0), 0),
        "total_elapsed_text": state.get("total_elapsed_text", "—"),
        "final_park_wait_seconds": round(safe_float(state.get("final_park_wait_seconds"), 0.0), 0),
        "final_park_wait_text": state.get("final_park_wait_text", "—"),
        "traffic_text": str(state.get("traffic_text") or live_trip_short_duration(traffic_seconds)),
        "traffic_seconds": round(traffic_seconds, 0),
        "stopped_in_drive_seconds": round(safe_float(state.get("stopped_in_drive_seconds"), 0.0), 0),
        "stopped_in_drive_text": state.get("stopped_in_drive_text", "—"),
        "slow_traffic_seconds": round(safe_float(state.get("slow_traffic_seconds"), 0.0), 0),
        "slow_traffic_text": state.get("slow_traffic_text", "—"),
        "normal_drive_seconds": round(safe_float(state.get("normal_drive_seconds"), 0.0), 0),
        "normal_drive_text": state.get("normal_drive_text", "—"),
        "parked_pause_seconds": round(safe_float(state.get("parked_pause_seconds"), 0.0), 0),
        "parked_pause_text": state.get("parked_pause_text", "—"),
        "last_traffic_class": state.get("last_traffic_class", ""),
        "traffic_model": state.get("traffic_model", ""),
        "traffic_model_label": state.get("traffic_model_label", ""),
        "traffic_reference_speed_kmh": f"{safe_float(state.get('traffic_reference_speed_kmh'), 0.0):.1f}",
        "traffic_reference_trip_type": state.get("traffic_reference_trip_type", ""),
        "traffic_reference_trip_type_label": state.get("traffic_reference_trip_type_label", ""),
        "traffic_reference_source": state.get("traffic_reference_source", ""),
        "traffic_p85_speed_kmh": f"{safe_float(state.get('traffic_p85_speed_kmh'), 0.0):.1f}",
        "traffic_free_flow_seconds": round(safe_float(state.get("traffic_free_flow_seconds"), 0.0), 0),
        "traffic_free_flow_text": state.get("traffic_free_flow_text", "—"),
        "traffic_delay_seconds": round(safe_float(state.get("traffic_delay_seconds"), 0.0), 0),
        "traffic_delay_text": state.get("traffic_delay_text", "—"),
        "traffic_congestion_percent": f"{safe_float(state.get('traffic_congestion_percent'), 0.0):.1f}",
        "traffic_impact_label": state.get("traffic_impact_label", ""),
        "traffic_ratio_moving_percent": f"{safe_float(state.get('traffic_ratio_moving_percent'), 0.0):.1f}",
        "average_speed": f"{safe_float(state.get('average_moving_speed', state.get('average_speed')), 0.0):.1f}",
        "average_moving_speed": f"{safe_float(state.get('average_moving_speed', state.get('average_speed')), 0.0):.1f}",
        "average_overall_speed": f"{safe_float(state.get('average_overall_speed'), 0.0):.1f}",
        "moving_seconds": round(safe_float(state.get("moving_seconds"), 0.0), 0),
        "moving_minutes": round(safe_float(state.get("moving_seconds"), 0.0) / 60.0, 2),
        "moving_duration_text": live_trip_short_duration(safe_float(state.get("moving_seconds"), 0.0)),
        "non_moving_seconds": round(safe_float(state.get("non_moving_seconds"), 0.0), 0),
        "speed_sample_count": int(safe_float(state.get("speed_sample_count"), 0.0)),
        "moving_speed_sample_count": int(safe_float(state.get("moving_speed_sample_count"), 0.0)),
        "max_speed": f"{safe_float(state.get('max_speed'), 0.0):.1f}",
        "moving_speed_threshold": safe_float(state.get("moving_speed_threshold"), MOVING_SPEED_THRESHOLD_KMH),
        "speed_sampler_interval_seconds": int(safe_float(state.get("speed_sampler_interval_seconds"), SPEED_SAMPLER_INTERVAL_SECONDS)),
        "used_kwh": f"{used_kwh_value:.2f}",
        "consumption_kwh_100km": f"{safe_float(state.get('consumption_kwh_100km'), 0.0):.2f}",
        "start_battery": f"{safe_float(state.get('start_battery'), 0.0):.1f}",
        "end_battery": f"{safe_float(state.get('end_battery'), 0.0):.1f}",
        "climate_text": live_trip_short_duration(climate_seconds),
        "climate_duration_minutes": round(climate_seconds / 60.0, 2),
        "climate_duration_text": live_trip_short_duration(climate_seconds),
        "min_elevation": f"{safe_float(state.get('min_elevation'), 0.0):.0f}",
        "max_elevation": f"{safe_float(state.get('max_elevation'), 0.0):.0f}",
        "elevation_range": f"{safe_float(state.get('elevation_range'), 0.0):.0f}",
        "elevation_gain": f"{safe_float(state.get('elevation_gain'), 0.0):.0f}",
        "elevation_loss": f"{safe_float(state.get('elevation_loss'), 0.0):.0f}",
        "elevation_sample_count": int(safe_float(state.get("elevation_sample_count"), 0.0)),
        "elevation_provider": str(state.get("elevation_provider") or ""),
        "elevation_source": str(state.get("elevation_source") or ""),
        "supercharger_kwh_price": f"{supercharger_price:.2f}",
        "zes_kwh_price": f"{zes_price:.2f}",
        "astor_kwh_price": f"{astor_price:.2f}",
        "supercharger_trip_cost": f"{used_kwh_value * supercharger_price:.2f}",
        "zes_trip_cost": f"{used_kwh_value * zes_price:.2f}",
        "astor_trip_cost": f"{used_kwh_value * astor_price:.2f}",
        "cost_presets": get_trip_cost_presets(data, used_kwh_value),
        "start_address": "Live Trip Test Start",
        "end_address": "Live Trip Test Finish",
        **get_report_visibility_options(data),
    }


async def async_generate_live_trip_test_report(
    hass: HomeAssistant,
    entry_id: str,
    data: dict[str, Any],
    state: dict[str, Any],
    *,
    send_telegram: bool,
    caption: str,
    output_path: str,
    telegram_target: str | None = None,
) -> str:
    """Render/send a normal trip PNG from the simulated live trip state."""
    report_data = build_live_trip_report_data_from_state(state, data)
    enrich_trip_report_score(report_data, lang=get_report_language(data))
    png_path = await hass.async_add_executor_job(
        render_trip_report_png,
        report_data,
        output_path,
        get_report_language(data),
    )

    state["last_report_path"] = png_path
    state["last_report_data"] = report_data
    notify_live_trip_sensor(hass, entry_id)

    latest_trip_state = get_trip_state(hass)
    latest_trip_state.update({
        "active": False,
        "finished_at": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
        "last_report_path": png_path,
        "last_report_data": report_data,
        "finish_source": "live_trip_test",
    })

    await async_record_trip_summary_entry(
        hass,
        report_data,
        source="live_trip_test",
    )

    target = str(
        telegram_target
        or state.get("test_telegram_target")
        or data.get(CONF_AI_TELEGRAM_TARGET)
        or data.get(CONF_AI_TELEGRAM_LISTENER_CHAT_ID)
        or data.get(CONF_TELEGRAM_TARGET)
        or ""
    ).strip()
    if send_telegram and target:
        await async_telegram_send_photo(
            hass,
            data,
            target=target,
            file_path=png_path,
            caption=caption,
        )
    return png_path


def update_live_trip_speed_samples(hass: HomeAssistant, entry_id: str, data: dict[str, Any]) -> None:
    """Sample Live Trip speed every second independently from the main live-trip update interval."""
    data = get_live_entry_config_for_entry_id(hass, entry_id, data)
    if not get_bool_option(data, CONF_LIVE_TRIP_ENABLED, DEFAULT_LIVE_TRIP_ENABLED):
        return

    state = get_live_trip_state(hass, entry_id)
    if state.get("test_mode") or not state.get("active"):
        return

    entities = get_live_trip_entities(data)
    now = datetime.now()
    now_ts = now.timestamp()
    start_speed_threshold = safe_float(data.get(CONF_AUTO_START_SPEED_THRESHOLD), DEFAULT_AUTO_START_SPEED_THRESHOLD)
    traffic_threshold = safe_float(data.get(CONF_LIVE_TRIP_TRAFFIC_SPEED_THRESHOLD), DEFAULT_LIVE_TRIP_TRAFFIC_SPEED_THRESHOLD)

    current_speed = get_float_state(hass, entities.get("speed"), 0.0)
    current_shift_state = get_state_text(hass, entities.get("shift_state"), "")
    active_now = live_trip_active_from_states(hass, entities, start_speed_threshold)

    last_sample_ts = safe_float(state.get("speed_sampler_last_ts"), safe_float(state.get("last_ts"), now_ts))
    delta_seconds = max(0.0, min(SPEED_SAMPLER_MAX_DELTA_SECONDS, now_ts - last_sample_ts))
    previous_speed = safe_float(state.get("speed_sampler_last_speed"), safe_float(state.get("last_speed"), current_speed))
    previous_shift_state = str(state.get("speed_sampler_last_shift_state") or state.get("last_shift_state") or current_shift_state or "")

    if delta_seconds > 0:
        add_speed_runtime_sample(
            state,
            sample_ts=now_ts,
            speed=previous_speed,
            delta_seconds=delta_seconds,
        )
        traffic_class = add_traffic_runtime_sample(
            state,
            speed=previous_speed,
            shift_state=previous_shift_state,
            delta_seconds=delta_seconds,
            traffic_threshold=traffic_threshold,
        )
        state["last_traffic_class"] = traffic_class

    state["speed_sampler_last_ts"] = now_ts
    state["speed_sampler_last_speed"] = current_speed
    state["speed_sampler_last_shift_state"] = current_shift_state
    state["speed_sampler_last_active"] = active_now
    state["speed_sampler_interval_seconds"] = SPEED_SAMPLER_INTERVAL_SECONDS
    state["speed_sampler_last_update"] = now.strftime("%d.%m.%Y %H:%M:%S")
    state["last_speed"] = current_speed
    state["last_shift_state"] = current_shift_state
    state.update(speed_sampling_debug_fields(state))
    state.update(traffic_sampling_debug_fields(state))

    hass.data.setdefault(DOMAIN, {}).setdefault(LIVE_TRIP_STATE_STORE, {})[entry_id] = state
    notify_live_trip_sensor(hass, entry_id)


async def update_live_trip_engine(hass: HomeAssistant, entry_id: str, data: dict[str, Any]) -> None:
    """Update backend live trip calculations from configured report entities."""
    data = get_live_entry_config_for_entry_id(hass, entry_id, data)
    if not get_bool_option(data, CONF_LIVE_TRIP_ENABLED, DEFAULT_LIVE_TRIP_ENABLED):
        return

    state = get_live_trip_state(hass, entry_id)
    if state.get("test_mode"):
        return

    entities = get_live_trip_entities(data)
    now = datetime.now()
    now_ts = now.timestamp()

    start_speed_threshold = safe_float(data.get(CONF_AUTO_START_SPEED_THRESHOLD), DEFAULT_AUTO_START_SPEED_THRESHOLD)
    traffic_threshold = safe_float(data.get(CONF_LIVE_TRIP_TRAFFIC_SPEED_THRESHOLD), DEFAULT_LIVE_TRIP_TRAFFIC_SPEED_THRESHOLD)
    finish_delay = max(10.0, safe_float(data.get(CONF_LIVE_TRIP_FINISH_DELAY_SECONDS), DEFAULT_LIVE_TRIP_FINISH_DELAY_SECONDS))
    min_distance = max(0.0, safe_float(data.get(CONF_LIVE_TRIP_MIN_DISTANCE_KM), DEFAULT_LIVE_TRIP_MIN_DISTANCE_KM))
    ai_segment_size_km = live_trip_ai_segment_size_from_data(data)
    report_lang = get_report_language(data)
    state["report_language"] = report_lang
    short_maneuver_settings = live_trip_short_maneuver_settings(data)
    ignore_short_maneuvers = bool(short_maneuver_settings.get("enabled"))
    candidate_min_distance = max(0.0, safe_float(short_maneuver_settings.get("min_distance_km"), DEFAULT_LIVE_TRIP_CANDIDATE_MIN_DISTANCE_KM))
    candidate_min_duration = max(0.0, safe_float(short_maneuver_settings.get("min_duration_seconds"), DEFAULT_LIVE_TRIP_CANDIDATE_MIN_DURATION_SECONDS))

    active_now = live_trip_active_from_states(hass, entities, start_speed_threshold)
    speed = get_float_state(hass, entities.get("speed"), 0.0)
    shift_state = get_state_text(hass, entities.get("shift_state"), "")
    odometer = get_float_state(hass, entities.get("odometer"), safe_float(state.get("last_odometer"), 0.0))
    energy = get_float_state(hass, entities.get("energy_remaining"), safe_float(state.get("last_energy"), 0.0))
    battery = get_float_state(hass, entities.get("battery_level"), safe_float(state.get("last_battery"), 0.0))
    elevation_entity = entities.get("elevation")
    elevation_state_obj = hass.states.get(elevation_entity) if elevation_entity else None
    elevation_state_text = str(elevation_state_obj.state if elevation_state_obj is not None else "").strip().lower()
    elevation = get_float_state(hass, elevation_entity, safe_float(state.get("last_elevation"), 0.0))
    if not elevation_entity or elevation_state_obj is None or elevation_state_text in {"", "unknown", "unavailable", "none"}:
        elevation = get_internal_trip_elevation_value(hass, entry_id, elevation)

    if active_now and not state.get("active"):
        state.clear()
        _cancel_live_trip_ai_task(hass, entry_id)
        candidate_mode = bool(ignore_short_maneuvers)
        initial_status = "candidate" if candidate_mode else "active"
        state.update({
            "active": True,
            "status": initial_status,
            "report_language": report_lang,
            "candidate_trip": candidate_mode,
            "candidate_confirmed": not candidate_mode,
            "candidate_started_at": now.strftime("%d.%m.%Y %H:%M:%S") if candidate_mode else "",
            "candidate_min_distance_km": round(candidate_min_distance, 3),
            "candidate_min_duration_seconds": round(candidate_min_duration, 0),
            "candidate_distance_km": 0.0,
            "candidate_duration_seconds": 0.0,
            "candidate_confirm_reason": "",
            "candidate_confirmed_at": "",
            "candidate_finish_decision": {},
            "trip_finish_pipeline_started": False,
            "trip_finish_pipeline_source": "",
            "trip_finish_pipeline_started_at": "",
            "ignored_short_maneuver": False,
            "short_maneuver_reason": "",
            "started_at": now.strftime("%d.%m.%Y %H:%M:%S"),
            "finished_at": "",
            "start_ts": now_ts,
            "last_ts": now_ts,
            "inactive_since_ts": 0.0,
            "last_speed": speed,
            "last_shift_state": shift_state,
            "stopped_in_drive_seconds": 0.0,
            "slow_traffic_seconds": 0.0,
            "normal_drive_seconds": 0.0,
            "parked_pause_seconds": 0.0,
            "last_traffic_class": "",
            "speed_sampler_last_ts": now_ts,
            "speed_sampler_last_speed": speed,
            "speed_sampler_last_active": active_now,
            "speed_sampler_interval_seconds": SPEED_SAMPLER_INTERVAL_SECONDS,
            "speed_sampler_last_update": now.strftime("%d.%m.%Y %H:%M:%S"),
            "moving_seconds": 0.0,
            "speed_weighted_sum": 0.0,
            "speed_sample_count": 0,
            "moving_speed_sample_count": 0,
            "speed_total_sample_seconds": 0.0,
            "max_speed": max(0.0, speed if speed > MOVING_SPEED_THRESHOLD_KMH else 0.0),
            "speed_samples": [],
            "last_speed_sample": {},
            "start_odometer": odometer,
            "last_odometer": odometer,
            "start_energy": energy,
            "last_energy": energy,
            "start_battery": battery,
            "last_battery": battery,
            "min_elevation": elevation,
            "max_elevation": elevation,
            "last_elevation": elevation,
            "traffic_seconds": 0.0,
            "climate_seconds": 0.0,
            **_live_trip_ai_default_runtime(),
        })
        state["live_ai_segment_size_km"] = ai_segment_size_km
        state["live_ai_segment_next_target_km"] = ai_segment_size_km
        state["live_ai_segment_baseline"] = _live_trip_ai_snapshot_from_state(state)
        save_live_trip_ai_segments_payload(hass, entry_id, {
            "entry_id": str(entry_id or ""),
            "segments": [],
            "updated_at": now.strftime("%d.%m.%Y %H:%M:%S"),
            "started_at": state.get("started_at", ""),
        })

    if state.get("active"):
        last_ts = safe_float(state.get("last_ts"), now_ts)
        delta_seconds = max(0.0, min(SPEED_SAMPLER_MAX_DELTA_SECONDS, now_ts - last_ts))

        if live_trip_climate_is_active(hass, entities.get("climate")):
            state["climate_seconds"] = safe_float(state.get("climate_seconds"), 0.0) + delta_seconds

        current_min = safe_float(state.get("min_elevation"), elevation)
        current_max = safe_float(state.get("max_elevation"), elevation)
        state["min_elevation"] = min(current_min, elevation)
        state["max_elevation"] = max(current_max, elevation)
        state["last_elevation"] = elevation
        state["last_ts"] = now_ts
        state["last_speed"] = speed
        state["last_shift_state"] = shift_state
        state["last_odometer"] = odometer
        state["last_energy"] = energy
        state["last_battery"] = battery

        if not active_now:
            inactive_since = safe_float(state.get("inactive_since_ts"), 0.0)
            if inactive_since <= 0:
                state["inactive_since_ts"] = now_ts
                state["status"] = "finishing"
            elif (now_ts - inactive_since) >= finish_delay:
                state["active"] = False
                state["status"] = "finished"
                state["finished_at"] = now.strftime("%d.%m.%Y %H:%M:%S")
        else:
            state["inactive_since_ts"] = 0.0
            if state.get("candidate_trip") and not state.get("candidate_confirmed"):
                state["status"] = "candidate"
            else:
                state["status"] = "active"

    start_ts = safe_float(state.get("start_ts"), 0.0)
    end_ts = now_ts if state.get("active") else safe_float(state.get("last_ts"), now_ts)
    total_elapsed_seconds = max(0.0, end_ts - start_ts) if start_ts > 0 else 0.0

    # The visible/report duration is meant to represent the user's vehicle-session time,
    # not the artificial final Park grace used to delay report delivery. Only the last
    # inactive/Park wait that directly precedes report sending is subtracted. Earlier
    # short Park breaks remain part of the session duration.
    inactive_since_for_duration = safe_float(state.get("inactive_since_ts"), 0.0)
    status_for_duration = str(state.get("status") or "").strip().lower()
    final_park_wait_seconds = 0.0
    if inactive_since_for_duration > 0 and status_for_duration in {"finishing", "finished"}:
        final_park_wait_seconds = max(0.0, end_ts - inactive_since_for_duration)

    duration_seconds = max(0.0, total_elapsed_seconds - final_park_wait_seconds)
    trip_km = max(0.0, safe_float(state.get("last_odometer"), odometer) - safe_float(state.get("start_odometer"), odometer))
    # Keep the runtime Live Trip AI interval synchronized with the newest option
    # before the public sensor attributes are rebuilt. This prevents the live
    # engine from rewriting a freshly selected 1/5 km interval back to stale 10 km.
    previous_ai_segment_size_km = safe_float(state.get("live_ai_segment_size_km"), ai_segment_size_km)
    if abs(previous_ai_segment_size_km - ai_segment_size_km) > 0.001:
        state["live_ai_segment_size_km"] = ai_segment_size_km
        completed_index = int(trip_km // ai_segment_size_km) if ai_segment_size_km > 0 else 0
        state["live_ai_segment_last_completed_index"] = max(0, completed_index)
        state["live_ai_last_requested_index"] = min(
            int(safe_float(state.get("live_ai_last_requested_index"), 0.0)),
            max(0, completed_index),
        )
        state["live_ai_segment_baseline"] = _live_trip_ai_snapshot_from_state(state)
        if str(state.get("live_ai_comment_source") or "").strip() != "panel_test":
            state["live_ai_comment_status"] = "waiting"
            state["live_ai_comment_error"] = ""
            state["live_comment"] = ""
    used_kwh = max(0.0, safe_float(state.get("start_energy"), energy) - safe_float(state.get("last_energy"), energy))
    start_battery = safe_float(state.get("start_battery"), battery)
    end_battery = safe_float(state.get("last_battery"), battery)
    used_battery = max(0.0, start_battery - end_battery)
    traffic_seconds = min(safe_float(state.get("traffic_seconds"), 0.0), duration_seconds)
    climate_seconds = safe_float(state.get("climate_seconds"), 0.0)
    average_overall_speed = (trip_km / (duration_seconds / 3600.0)) if duration_seconds > 0 else 0.0
    speed_debug = speed_sampling_debug_fields(state)
    traffic_debug = traffic_sampling_debug_fields(state)
    sample_average_speed = safe_float(speed_debug.get("average_moving_speed"), 0.0)
    average_moving_speed = average_speed_distance_over_moving_time(trip_km, speed_debug.get("moving_seconds", 0.0))
    if average_moving_speed <= 0:
        average_moving_speed = sample_average_speed
    average_speed = average_moving_speed if average_moving_speed > 0 else average_overall_speed
    traffic_model_debug = traffic_delay_model_fields(
        state,
        distance_km=trip_km,
        moving_seconds=speed_debug.get("moving_seconds", 0.0),
        moving_average_speed=average_moving_speed,
    )
    state.update(traffic_model_debug)
    consumption = (used_kwh / trip_km * 100.0) if trip_km > 0 else 0.0
    elevation_range = max(0.0, safe_float(state.get("max_elevation"), 0.0) - safe_float(state.get("min_elevation"), 0.0))

    candidate_pending = bool(state.get("candidate_trip") and not state.get("candidate_confirmed"))
    candidate_ready = live_trip_candidate_qualified(
        trip_km=trip_km,
        duration_seconds=duration_seconds,
        settings=short_maneuver_settings,
    )
    state["candidate_distance_km"] = round(trip_km, 3)
    state["candidate_duration_seconds"] = round(duration_seconds, 0)
    if candidate_pending and candidate_ready:
        state["candidate_confirmed"] = True
        state["candidate_trip"] = False
        state["candidate_confirmed_at"] = now.strftime("%d.%m.%Y %H:%M:%S")
        state["candidate_confirm_reason"] = live_trip_candidate_reason(
            trip_km=trip_km,
            duration_seconds=duration_seconds,
            settings=short_maneuver_settings,
        )
        if str(state.get("status") or "").strip().lower() == "candidate":
            state["status"] = "active"
    elif candidate_pending and not active_now:
        state["active"] = False
        state["status"] = "ignored_short_maneuver"
        state["finished_at"] = now.strftime("%d.%m.%Y %H:%M:%S")
        state["inactive_since_ts"] = 0.0
        state["ignored_short_maneuver"] = True
        state["short_maneuver_reason"] = (
            f"distance {trip_km:.2f} km < {candidate_min_distance:.2f} km and "
            f"duration {live_trip_short_duration(duration_seconds)} < {live_trip_short_duration(candidate_min_duration)}"
        )

    zes_price = safe_float(data.get(CONF_ZES_PRICE), DEFAULT_ZES_PRICE)
    supercharger_price = safe_float(data.get(CONF_SUPERCHARGER_PRICE), DEFAULT_SUPERCHARGER_PRICE)
    astor_price = safe_float(data.get(CONF_ASTOR_PRICE), DEFAULT_ASTOR_PRICE)

    display_status = state.get("status", "idle")
    if display_status == "ignored_short_maneuver":
        trip_status = "Kısa park/garaj manevrası yok sayıldı. Yeni Live Trip raporu başlatılmadı."
    elif display_status == "candidate":
        remaining_distance = max(0.0, candidate_min_distance - trip_km)
        remaining_seconds = max(0.0, candidate_min_duration - duration_seconds)
        trip_status = f"Aday sürüş izleniyor. Gerçek Live Trip için yaklaşık {remaining_distance:.2f} km veya {live_trip_short_duration(remaining_seconds)} kaldı."
    elif display_status == "finished" and trip_km < min_distance:
        trip_status = "Sürüş tamamlandı ama minimum mesafe altında kaldı. Son değerler gösteriliyor."
    elif display_status == "finished":
        trip_status = "Sürüş tamamlandı. Son sürüş raporu kart üzerinde gösteriliyor."
    elif display_status == "finishing":
        inactive_since = safe_float(state.get("inactive_since_ts"), 0.0)
        remaining_seconds = max(0.0, finish_delay - (now_ts - inactive_since)) if inactive_since > 0 else finish_delay
        trip_status = f"Araç Park konumunda. Rapor için {live_trip_short_duration(remaining_seconds)} bekleniyor; bu sürede tekrar hareket ederse Live Trip devam eder."
    elif display_status == "active":
        trip_status = "Sürüş devam ediyor. Canlı veriler güncelleniyor."
    else:
        trip_status = "Canlı sürüş bekleniyor."

    state.update({
        "last_update": now.strftime("%d.%m.%Y %H:%M:%S"),
        "report_language": report_lang,
        "candidate_trip": bool(state.get("candidate_trip", False)),
        "candidate_confirmed": bool(state.get("candidate_confirmed", False)),
        "candidate_min_distance_km": round(candidate_min_distance, 3),
        "candidate_min_duration_seconds": round(candidate_min_duration, 0),
        "candidate_distance_km": round(safe_float(state.get("candidate_distance_km"), trip_km), 3),
        "candidate_duration_seconds": round(safe_float(state.get("candidate_duration_seconds"), duration_seconds), 0),
        "candidate_confirm_reason": str(state.get("candidate_confirm_reason") or ""),
        "candidate_confirmed_at": str(state.get("candidate_confirmed_at") or ""),
        "candidate_finish_decision": state.get("candidate_finish_decision") if isinstance(state.get("candidate_finish_decision"), dict) else {},
        "trip_finish_pipeline_started": bool(state.get("trip_finish_pipeline_started", False)),
        "trip_finish_pipeline_source": str(state.get("trip_finish_pipeline_source") or ""),
        "trip_finish_pipeline_started_at": str(state.get("trip_finish_pipeline_started_at") or ""),
        "ignore_short_maneuvers_enabled": bool(ignore_short_maneuvers),
        "ignored_short_maneuver": bool(state.get("ignored_short_maneuver", False)),
        "short_maneuver_reason": str(state.get("short_maneuver_reason") or ""),
        "trip_km": round(trip_km, 3),
        "duration_seconds": round(duration_seconds, 0),
        "duration_text": live_trip_short_duration(duration_seconds),
        "report_duration_seconds": round(duration_seconds, 0),
        "report_duration_text": live_trip_short_duration(duration_seconds),
        "total_elapsed_seconds": round(total_elapsed_seconds, 0),
        "total_elapsed_text": live_trip_short_duration(total_elapsed_seconds),
        "final_park_wait_seconds": round(final_park_wait_seconds, 0),
        "final_park_wait_text": live_trip_short_duration(final_park_wait_seconds),
        "traffic_seconds": round(traffic_seconds, 0),
        "traffic_text": live_trip_short_duration(traffic_seconds),
        "average_speed": round(average_speed, 1),
        "average_moving_speed": round(average_moving_speed, 1),
        "average_overall_speed": round(average_overall_speed, 1),
        "sample_average_speed": round(sample_average_speed, 1),
        "moving_seconds": speed_debug.get("moving_seconds", 0),
        "moving_minutes": speed_debug.get("moving_minutes", 0),
        "moving_duration_text": speed_debug.get("moving_duration_text", "—"),
        "non_moving_seconds": speed_debug.get("non_moving_seconds", 0),
        "speed_sample_count": speed_debug.get("speed_sample_count", 0),
        "moving_speed_sample_count": speed_debug.get("moving_speed_sample_count", 0),
        "max_speed": speed_debug.get("max_speed", 0),
        "moving_speed_threshold": speed_debug.get("moving_speed_threshold", MOVING_SPEED_THRESHOLD_KMH),
        "used_kwh": round(used_kwh, 3),
        "used_battery": round(used_battery, 1),
        "consumption_kwh_100km": round(consumption, 2),
        "start_battery": round(start_battery, 1),
        "end_battery": round(end_battery, 1),
        "battery_text": "—" if display_status == "idle" or start_battery <= 0 else f"%{start_battery:.1f} -> %{end_battery:.1f}",
        "climate_seconds": round(climate_seconds, 0),
        "climate_text": live_trip_short_duration(climate_seconds),
        "elevation_range": round(elevation_range, 0),
        "zes_kwh_price": round(zes_price, 2),
        "zes_trip_cost": round(used_kwh * zes_price, 2),
        "supercharger_kwh_price": round(supercharger_price, 2),
        "supercharger_trip_cost": round(used_kwh * supercharger_price, 2),
        "astor_kwh_price": round(astor_price, 2),
        "astor_trip_cost": round(used_kwh * astor_price, 2),
        "trip_status": trip_status,
        "live_comment": str(state.get("live_comment") or ""),
        "live_ai_segment_size_km": ai_segment_size_km,
        "live_ai_segment_last_completed_index": int(safe_float(state.get("live_ai_segment_last_completed_index"), 0.0)),
        "live_ai_segment_next_target_km": _live_trip_ai_reconciled_next_target_km({**state, "live_ai_segment_size_km": ai_segment_size_km}, ai_segment_size_km),
        "live_ai_segment_baseline": state.get("live_ai_segment_baseline") if isinstance(state.get("live_ai_segment_baseline"), dict) else _live_trip_ai_snapshot_from_state(state),
        "live_ai_segments": state.get("live_ai_segments") if isinstance(state.get("live_ai_segments"), list) else [],
        "live_ai_latest_segment": state.get("live_ai_latest_segment") if isinstance(state.get("live_ai_latest_segment"), dict) else {},
        "live_ai_comment_status": str(state.get("live_ai_comment_status") or "waiting"),
        "live_ai_comment_source": str(state.get("live_ai_comment_source") or ""),
        "live_ai_comment_error": str(state.get("live_ai_comment_error") or ""),
        "live_ai_last_generated_at": str(state.get("live_ai_last_generated_at") or ""),
        "live_ai_last_prompt_at": str(state.get("live_ai_last_prompt_at") or ""),
        "live_ai_last_prompt_ts": safe_float(state.get("live_ai_last_prompt_ts"), 0.0),
        "live_ai_scheduler_debug": state.get("live_ai_scheduler_debug") if isinstance(state.get("live_ai_scheduler_debug"), dict) else {},
        "live_ai_last_requested_index": int(safe_float(state.get("live_ai_last_requested_index"), 0.0)),
        "finish_delay_seconds": round(finish_delay, 0),
        "finish_delay_minutes": round(finish_delay / 60.0, 2),
        "inactive_remaining_seconds": round(max(0.0, finish_delay - (now_ts - safe_float(state.get("inactive_since_ts"), 0.0))) if safe_float(state.get("inactive_since_ts"), 0.0) > 0 and display_status == "finishing" else 0.0, 0),
    })
    await async_maybe_schedule_live_trip_ai_segment(hass, entry_id, data)
    notify_live_trip_sensor(hass, entry_id)

async def async_sync_live_trip_ai_interval_from_options(hass: HomeAssistant, entry_id: str, data: dict[str, Any]) -> None:
    """Apply the current AI segment interval to the active Live Trip state immediately.

    This is used when the user changes the 1/5/10 km interval from the panel
    during an active drive. The core Live Trip counters are not reset; only the
    AI-comment scheduler target/baseline is realigned so the popup text and the
    next trigger stop showing a stale 10 km threshold.
    """
    try:
        state = get_live_trip_state(hass, entry_id)
        if state is None:
            return
        data = get_live_entry_config_for_entry_id(hass, entry_id, data)
        state["report_language"] = get_report_language(data)
        size_km = live_trip_ai_segment_size_from_data(data)
        old_size = safe_float(state.get("live_ai_segment_size_km"), size_km)
        current_km = max(0.0, safe_float(state.get("trip_km"), 0.0))
        if abs(old_size - size_km) > 0.001:
            state["live_ai_segment_size_km"] = size_km
            # Realign only the REAL segment scheduler. Panel-only test comments
            # must never consume a 1/5/10 km segment or push the next target to
            # the following boundary.
            completed_index = int(current_km // size_km) if size_km > 0 else 0
            state["live_ai_segment_last_completed_index"] = max(0, completed_index)
            state["live_ai_last_requested_index"] = min(
                int(safe_float(state.get("live_ai_last_requested_index"), 0.0)),
                max(0, completed_index),
            )
            state["live_ai_segment_baseline"] = _live_trip_ai_snapshot_from_state(state)
            if str(state.get("live_ai_comment_source") or "").strip() != "panel_test":
                state["live_ai_comment_status"] = "waiting"
                state["live_ai_comment_error"] = ""
                state["live_comment"] = ""
        else:
            state["live_ai_segment_size_km"] = size_km
        next_index = max(1, int(safe_float(state.get("live_ai_segment_last_completed_index"), 0.0)) + 1)
        state["live_ai_segment_next_target_km"] = _live_trip_ai_reconciled_next_target_km(state, size_km)
        _live_trip_ai_set_scheduler_debug(
            state,
            current_km=current_km,
            next_target=safe_float(state.get("live_ai_segment_next_target_km"), size_km),
            segment_index=next_index,
            reason="interval_synced_from_settings",
            should_schedule=False,
        )
        notify_live_trip_sensor(hass, entry_id)
    except Exception:
        _LOGGER.exception("Could not sync Live Trip AI interval from options")


def is_climate_active(state: str) -> bool:
    """Return whether climate state should count as active."""
    return state not in {"", "off", "unknown", "unavailable", "none"}


def normalize_shift_state(value: str) -> str:
    """Normalize Tesla shift state text."""
    return str(value or "").strip().upper()


def should_auto_start_trip(shift_state: str, speed: float, threshold: float) -> bool:
    """Return whether auto trip start conditions are met."""
    return normalize_shift_state(shift_state) == "D" and speed > threshold


def should_auto_finish_trip(shift_state: str) -> bool:
    """Return whether auto trip finish conditions are met."""
    return normalize_shift_state(shift_state) == "P"


def get_named_state(hass: HomeAssistant, state_key: str) -> dict[str, Any]:
    """Return a mutable state bucket for the requested report mode."""
    hass.data.setdefault(DOMAIN, {})
    return hass.data[DOMAIN].setdefault(state_key, {})


def clear_named_state(hass: HomeAssistant, state_key: str) -> None:
    """Clear a named report state bucket."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][state_key] = {}


def get_trip_state(hass: HomeAssistant) -> dict[str, Any]:
    """Return normal auto/service trip state storage."""
    return get_named_state(hass, TRIP_STATE_KEY)


def get_manual_tracking_state(hass: HomeAssistant) -> dict[str, Any]:
    """Return manual switch tracking state storage."""
    return get_named_state(hass, MANUAL_TRACKING_STATE_KEY)


def clear_trip_state(hass: HomeAssistant) -> None:
    """Clear normal auto/service trip state storage."""
    clear_named_state(hass, TRIP_STATE_KEY)


def clear_manual_tracking_state(hass: HomeAssistant) -> None:
    """Clear manual switch tracking state storage."""
    clear_named_state(hass, MANUAL_TRACKING_STATE_KEY)



def is_drive_like_shift_state(value: str) -> bool:
    """Return whether a shift state should count as an active driving context."""
    return normalize_shift_state(value) in {"D", "DRIVE", "DRIVING", "R", "REVERSE", "N", "NEUTRAL"}


def is_park_like_shift_state(value: str) -> bool:
    """Return whether a shift state should count as Park / non-driving context."""
    return normalize_shift_state(value) in {"P", "PARK", "PARKING", "PARKED", "OFF", "ASLEEP", "SLEEPING"}


def add_traffic_runtime_sample(
    trip_state: dict[str, Any],
    *,
    speed: float,
    shift_state: str,
    delta_seconds: float,
    traffic_threshold: float = TRAFFIC_SPEED_THRESHOLD_KMH,
    moving_threshold: float = MOVING_SPEED_THRESHOLD_KMH,
) -> str:
    """Classify one runtime sample into traffic/park/normal-drive buckets.

    Traffic is based on shift + speed:
    - P/off/asleep -> parked pause, never traffic
    - D/R/N + <= moving threshold -> stopped-in-drive traffic
    - D/R/N + moving but <= traffic threshold -> slow traffic
    - D/R/N + above traffic threshold -> normal drive
    """
    delta = max(0.0, safe_float(delta_seconds, 0.0))
    if delta <= 0:
        return "none"

    speed_value = max(0.0, safe_float(speed, 0.0))
    shift_text = str(shift_state or "").strip()
    drive_like = is_drive_like_shift_state(shift_text)
    park_like = is_park_like_shift_state(shift_text)

    if park_like:
        trip_state["parked_pause_seconds"] = safe_float(trip_state.get("parked_pause_seconds"), 0.0) + delta
        return "parked_pause"

    if not drive_like and speed_value <= moving_threshold:
        trip_state["parked_pause_seconds"] = safe_float(trip_state.get("parked_pause_seconds"), 0.0) + delta
        return "parked_pause_unknown_shift"

    if not drive_like and speed_value > moving_threshold:
        drive_like = True

    if drive_like and speed_value <= moving_threshold:
        trip_state["stopped_in_drive_seconds"] = safe_float(trip_state.get("stopped_in_drive_seconds"), 0.0) + delta
        trip_state["traffic_seconds"] = safe_float(trip_state.get("traffic_seconds"), 0.0) + delta
        return "stopped_in_drive"

    if drive_like and speed_value <= traffic_threshold:
        trip_state["slow_traffic_seconds"] = safe_float(trip_state.get("slow_traffic_seconds"), 0.0) + delta
        trip_state["traffic_seconds"] = safe_float(trip_state.get("traffic_seconds"), 0.0) + delta
        return "slow_traffic"

    if drive_like:
        trip_state["normal_drive_seconds"] = safe_float(trip_state.get("normal_drive_seconds"), 0.0) + delta
        return "normal_drive"

    return "none"


def traffic_sampling_debug_fields(trip_state: dict[str, Any]) -> dict[str, Any]:
    """Return reusable traffic classification debug/report fields."""
    stopped = safe_float(trip_state.get("stopped_in_drive_seconds"), 0.0)
    slow = safe_float(trip_state.get("slow_traffic_seconds"), 0.0)
    normal = safe_float(trip_state.get("normal_drive_seconds"), 0.0)
    parked = safe_float(trip_state.get("parked_pause_seconds"), 0.0)
    traffic = safe_float(trip_state.get("traffic_seconds"), stopped + slow)
    return {
        "traffic_seconds": round(traffic, 0),
        "traffic_minutes": round(traffic / 60.0, 2),
        "traffic_text": format_duration_from_minutes(traffic / 60.0),
        "stopped_in_drive_seconds": round(stopped, 0),
        "stopped_in_drive_minutes": round(stopped / 60.0, 2),
        "stopped_in_drive_text": format_duration_from_minutes(stopped / 60.0),
        "slow_traffic_seconds": round(slow, 0),
        "slow_traffic_minutes": round(slow / 60.0, 2),
        "slow_traffic_text": format_duration_from_minutes(slow / 60.0),
        "normal_drive_seconds": round(normal, 0),
        "normal_drive_minutes": round(normal / 60.0, 2),
        "normal_drive_text": format_duration_from_minutes(normal / 60.0),
        "parked_pause_seconds": round(parked, 0),
        "parked_pause_minutes": round(parked / 60.0, 2),
        "parked_pause_text": format_duration_from_minutes(parked / 60.0),
        "last_traffic_class": str(trip_state.get("last_traffic_class") or ""),
    }


def _speed_values_from_state(trip_state: dict[str, Any], *, min_speed: float = MOVING_SPEED_THRESHOLD_KMH) -> list[float]:
    """Return moving speed sample values for percentile/reference calculations."""
    samples = trip_state.get("speed_samples")
    values: list[float] = []
    if isinstance(samples, list):
        for item in samples:
            if not isinstance(item, dict):
                continue
            speed = safe_float(item.get("speed"), 0.0)
            if speed > min_speed:
                values.append(speed)
    return values


def percentile_value(values: list[float], percentile: float, default: float = 0.0) -> float:
    """Small dependency-free percentile helper."""
    if not values:
        return default
    ordered = sorted(float(v) for v in values if v is not None)
    if not ordered:
        return default
    if len(ordered) == 1:
        return ordered[0]
    p = max(0.0, min(100.0, safe_float(percentile, 0.0))) / 100.0
    pos = (len(ordered) - 1) * p
    lower = int(pos)
    upper = min(lower + 1, len(ordered) - 1)
    frac = pos - lower
    return ordered[lower] + ((ordered[upper] - ordered[lower]) * frac)


def classify_trip_type_for_traffic(distance_km: float, moving_average_speed: float, max_speed: float) -> tuple[str, float]:
    """Return trip type and base reference speed."""
    distance = safe_float(distance_km, 0.0)
    moving_speed = safe_float(moving_average_speed, 0.0)
    max_seen = safe_float(max_speed, 0.0)

    if distance >= 30 and (moving_speed >= 55 or max_seen >= 90):
        return "long_road", TRAFFIC_REFERENCE_HIGHWAY_KMH
    if distance >= 12 and (moving_speed >= 38 or max_seen >= 70):
        return "mixed", TRAFFIC_REFERENCE_MIXED_KMH
    return "urban", TRAFFIC_REFERENCE_CITY_KMH


def traffic_impact_label_from_percent(percent: float) -> str:
    """Return a Turkish traffic impact label from congestion percent."""
    value = safe_float(percent, 0.0)
    if value < 10:
        return "düşük"
    if value < 30:
        return "orta"
    if value < 60:
        return "yüksek"
    return "çok yüksek"


def traffic_type_label_for_report(trip_type: str) -> str:
    labels = {
        "urban": "şehir içi",
        "mixed": "karma",
        "long_road": "uzun yol",
    }
    return labels.get(str(trip_type or ""), str(trip_type or "belirsiz"))


def traffic_delay_model_fields(
    trip_state: dict[str, Any],
    *,
    distance_km: float,
    moving_seconds: float | None = None,
    moving_average_speed: float | None = None,
) -> dict[str, Any]:
    """Compute a free-flow delay traffic model.

    Congestion percent is calculated as:
        (moving_time - free_flow_time) / free_flow_time * 100

    This keeps the speed-bucket details, but makes the headline traffic meaning
    closer to traffic-index systems that compare real duration with free-flow
    duration.
    """
    distance = max(0.0, safe_float(distance_km, 0.0))
    moving = safe_float(moving_seconds, safe_float(trip_state.get("moving_seconds"), 0.0))
    if moving <= 0:
        moving = safe_float(trip_state.get("normal_drive_seconds"), 0.0) + safe_float(trip_state.get("slow_traffic_seconds"), 0.0) + safe_float(trip_state.get("stopped_in_drive_seconds"), 0.0)

    moving_avg = safe_float(moving_average_speed, 0.0)
    if moving_avg <= 0:
        moving_avg = average_speed_distance_over_moving_time(distance, moving)
    max_speed = safe_float(trip_state.get("max_speed"), 0.0)

    trip_type, base_reference = classify_trip_type_for_traffic(distance, moving_avg, max_speed)
    speed_values = _speed_values_from_state(trip_state)
    p85 = percentile_value(speed_values, 85, 0.0)

    reference_speed = base_reference
    reference_source = "trip_type_default"
    if TRAFFIC_REFERENCE_MIN_KMH <= p85 <= TRAFFIC_REFERENCE_MAX_KMH:
        reference_speed = (base_reference * (1.0 - TRAFFIC_P85_BLEND_WEIGHT)) + (p85 * TRAFFIC_P85_BLEND_WEIGHT)
        reference_source = "trip_type_plus_p85"

    if distance <= 0 or moving <= 0 or reference_speed <= 0:
        free_flow_seconds = 0.0
        delay_seconds = 0.0
        congestion_percent = 0.0
    else:
        free_flow_seconds = (distance / reference_speed) * 3600.0
        delay_seconds = max(0.0, moving - free_flow_seconds)
        congestion_percent = (delay_seconds / free_flow_seconds * 100.0) if free_flow_seconds > 0 else 0.0

    stopped = safe_float(trip_state.get("stopped_in_drive_seconds"), 0.0)
    slow = safe_float(trip_state.get("slow_traffic_seconds"), 0.0)
    normal = safe_float(trip_state.get("normal_drive_seconds"), 0.0)
    speed_bucket_traffic_seconds = stopped + slow
    traffic_ratio_moving = (speed_bucket_traffic_seconds / moving * 100.0) if moving > 0 else 0.0

    raw_congestion_percent = congestion_percent
    traffic_limited = _is_short_trip_traffic_limited(
        distance_km=distance,
        duration_seconds=moving,
        traffic_delay_seconds=delay_seconds,
        speed_bucket_traffic_seconds=speed_bucket_traffic_seconds,
    )
    cautious = _classify_slowdown_reason(
        distance_km=distance,
        moving_seconds=moving,
        delay_seconds=delay_seconds,
        stopped_seconds=stopped,
        slow_seconds=slow,
        normal_seconds=normal,
        moving_avg_speed=moving_avg,
    )
    traffic_limited = bool(traffic_limited or cautious.get("traffic_analysis_limited"))
    if traffic_limited:
        congestion_percent = min(congestion_percent, 8.0)
        traffic_effective_impact_label = str(cautious.get("traffic_effective_impact_label") or "düşük")
        traffic_analysis_reliability = str(cautious.get("traffic_analysis_reliability") or "düşük")
        traffic_interpretation_note = str(cautious.get("traffic_interpretation_note") or _short_trip_traffic_note())
    else:
        traffic_effective_impact_label = traffic_impact_label_from_percent(congestion_percent)
        traffic_analysis_reliability = str(cautious.get("traffic_analysis_reliability") or "normal")
        traffic_interpretation_note = ""
        cautious["effective_traffic_delay_seconds"] = round(delay_seconds, 0)
        cautious["effective_traffic_delay_minutes"] = round(delay_seconds / 60.0, 2)
        cautious["effective_traffic_delay_text"] = format_duration_from_minutes(delay_seconds / 60.0)
        cautious["effective_traffic_impact"] = traffic_effective_impact_label
        cautious["traffic_effective_impact_label"] = traffic_effective_impact_label

    return {
        "traffic_model": "free_flow_delay",
        "traffic_model_label": "Gecikme bazlı",
        "traffic_reference_speed_kmh": round(reference_speed, 1),
        "traffic_reference_source": reference_source,
        "traffic_reference_trip_type": trip_type,
        "traffic_reference_trip_type_label": traffic_type_label_for_report(trip_type),
        "traffic_p85_speed_kmh": round(p85, 1),
        "traffic_free_flow_seconds": round(free_flow_seconds, 0),
        "traffic_free_flow_minutes": round(free_flow_seconds / 60.0, 2),
        "traffic_free_flow_text": format_duration_from_minutes(free_flow_seconds / 60.0),
        "traffic_delay_seconds": round(delay_seconds, 0),
        "traffic_delay_minutes": round(delay_seconds / 60.0, 2),
        "traffic_delay_text": format_duration_from_minutes(delay_seconds / 60.0),
        "effective_traffic_delay_seconds": round(safe_float(cautious.get("effective_traffic_delay_seconds"), delay_seconds), 0),
        "effective_traffic_delay_minutes": round(safe_float(cautious.get("effective_traffic_delay_seconds"), delay_seconds) / 60.0, 2),
        "effective_traffic_delay_text": str(cautious.get("effective_traffic_delay_text") or format_duration_from_minutes(delay_seconds / 60.0)),
        "slowdown_reason": str(cautious.get("slowdown_reason") or "traffic"),
        "slowdown_reason_label": str(cautious.get("slowdown_reason_label") or slowdown_reason_label(cautious.get("slowdown_reason") or "traffic")),
        "traffic_confidence": str(cautious.get("traffic_confidence") or "normal"),
        "effective_traffic_impact": str(cautious.get("effective_traffic_impact") or traffic_effective_impact_label),
        "raw_low_speed_percent": round(traffic_ratio_moving, 1),
        "raw_low_speed_seconds": round(speed_bucket_traffic_seconds, 0),
        "raw_low_speed_text": format_duration_from_minutes(speed_bucket_traffic_seconds / 60.0),
        "traffic_raw_congestion_percent": round(raw_congestion_percent, 1),
        "traffic_congestion_percent": round(congestion_percent, 1),
        "traffic_impact_label": traffic_effective_impact_label,
        "traffic_effective_impact_label": traffic_effective_impact_label,
        "traffic_analysis_limited": traffic_limited,
        "traffic_analysis_reliability": traffic_analysis_reliability,
        "traffic_interpretation_note": traffic_interpretation_note,
        "traffic_ratio_moving_percent": round(traffic_ratio_moving, 1),
        "stop_go_speed_threshold_kmh": TRAFFIC_STOP_GO_SPEED_THRESHOLD_KMH,
        "slow_traffic_speed_threshold_kmh": TRAFFIC_SLOW_SPEED_THRESHOLD_KMH,
        "traffic_standard_note": "free-flow travel time comparison",
    }


def add_speed_runtime_sample(
    trip_state: dict[str, Any],
    *,
    sample_ts: float,
    speed: float,
    delta_seconds: float,
    moving_threshold: float = MOVING_SPEED_THRESHOLD_KMH,
) -> None:
    """Accumulate time-weighted speed samples for moving average calculations.

    Average speed is intentionally based only on speed values above the moving
    threshold. This prevents Park grace time, shopping breaks, and long idle
    periods from collapsing average speed in Live Trip and Manual Tracking.
    """
    delta = max(0.0, safe_float(delta_seconds, 0.0))
    speed_value = max(0.0, safe_float(speed, 0.0))
    if delta <= 0:
        return

    trip_state["speed_sample_count"] = int(safe_float(trip_state.get("speed_sample_count"), 0.0)) + 1
    trip_state["speed_total_sample_seconds"] = safe_float(trip_state.get("speed_total_sample_seconds"), 0.0) + delta
    trip_state["last_speed_sample"] = {
        "ts": round(sample_ts, 3),
        "speed": round(speed_value, 3),
        "delta_seconds": round(delta, 3),
        "moving": speed_value > moving_threshold,
    }

    samples = trip_state.get("speed_samples")
    if not isinstance(samples, list):
        samples = []
    samples.append(trip_state["last_speed_sample"])
    if len(samples) > SPEED_SAMPLE_HISTORY_LIMIT:
        samples = samples[-SPEED_SAMPLE_HISTORY_LIMIT:]
    trip_state["speed_samples"] = samples

    if speed_value > moving_threshold:
        trip_state["moving_seconds"] = safe_float(trip_state.get("moving_seconds"), 0.0) + delta
        trip_state["speed_weighted_sum"] = safe_float(trip_state.get("speed_weighted_sum"), 0.0) + (speed_value * delta)
        trip_state["moving_speed_sample_count"] = int(safe_float(trip_state.get("moving_speed_sample_count"), 0.0)) + 1
        trip_state["max_speed"] = max(safe_float(trip_state.get("max_speed"), 0.0), speed_value)


def average_moving_speed_from_state(trip_state: dict[str, Any]) -> float:
    """Return the speed-sample moving average for a trip-like state."""
    moving_seconds = safe_float(trip_state.get("moving_seconds"), 0.0)
    if moving_seconds <= 0:
        return 0.0
    return safe_float(trip_state.get("speed_weighted_sum"), 0.0) / moving_seconds


def speed_sampling_debug_fields(trip_state: dict[str, Any]) -> dict[str, Any]:
    """Return reusable debug/report fields for speed sampling."""
    moving_seconds = safe_float(trip_state.get("moving_seconds"), 0.0)
    total_sample_seconds = safe_float(trip_state.get("speed_total_sample_seconds"), 0.0)
    return {
        "moving_seconds": round(moving_seconds, 0),
        "moving_minutes": round(moving_seconds / 60.0, 2),
        "moving_duration_text": format_duration_from_minutes(moving_seconds / 60.0),
        "non_moving_seconds": round(max(0.0, total_sample_seconds - moving_seconds), 0),
        "speed_sample_count": int(safe_float(trip_state.get("speed_sample_count"), 0.0)),
        "moving_speed_sample_count": int(safe_float(trip_state.get("moving_speed_sample_count"), 0.0)),
        "speed_total_sample_seconds": round(total_sample_seconds, 0),
        "max_speed": round(safe_float(trip_state.get("max_speed"), 0.0), 1),
        "average_moving_speed": round(average_moving_speed_from_state(trip_state), 1),
        "moving_speed_threshold": MOVING_SPEED_THRESHOLD_KMH,
        "last_speed_sample": trip_state.get("last_speed_sample") if isinstance(trip_state.get("last_speed_sample"), dict) else {},
    }


def update_runtime_tracking_fields(
    hass: HomeAssistant,
    integration_data: dict[str, Any],
    state_key: str,
) -> None:
    """Accumulate runtime metrics such as traffic, climate, elevation and moving-speed samples."""
    trip_state = get_named_state(hass, state_key)

    if not trip_state.get("active"):
        return

    now_ts = datetime.now().timestamp()
    last_sample_ts = safe_float(trip_state.get("last_sample_ts"), now_ts)
    delta_seconds = max(0.0, min(SPEED_SAMPLER_MAX_DELTA_SECONDS, now_ts - last_sample_ts))

    speed_entity = get_report_configured_entity(integration_data, CONF_SPEED_ENTITY, VEHICLE_ROLE_SPEED)
    shift_entity = get_report_configured_entity(integration_data, CONF_SHIFT_STATE_ENTITY, VEHICLE_ROLE_SHIFT_STATE)
    climate_entity = get_report_configured_entity(integration_data, CONF_CLIMATE_ENTITY, VEHICLE_ROLE_CLIMATE)
    elevation_entity = get_report_configured_entity(integration_data, CONF_ELEVATION_ENTITY, VEHICLE_ROLE_ELEVATION)

    previous_speed = safe_float(
        trip_state.get("last_speed"),
        get_float_state(hass, speed_entity, 0.0),
    )
    previous_shift_state = str(
        trip_state.get("last_shift_state")
        or trip_state.get("start_shift_state")
        or get_state_text(hass, shift_entity, "")
        or ""
    )
    previous_climate_active = bool(
        trip_state.get("last_climate_active", trip_state.get("climate_active_at_start", False))
    )

    add_speed_runtime_sample(
        trip_state,
        sample_ts=now_ts,
        speed=previous_speed,
        delta_seconds=delta_seconds,
    )

    traffic_threshold = safe_float(integration_data.get(CONF_LIVE_TRIP_TRAFFIC_SPEED_THRESHOLD), DEFAULT_LIVE_TRIP_TRAFFIC_SPEED_THRESHOLD)
    traffic_class = add_traffic_runtime_sample(
        trip_state,
        speed=previous_speed,
        shift_state=previous_shift_state,
        delta_seconds=delta_seconds,
        traffic_threshold=traffic_threshold,
    )
    trip_state["last_traffic_class"] = traffic_class

    if previous_climate_active:
        trip_state["climate_active_seconds"] = safe_float(trip_state.get("climate_active_seconds"), 0.0) + delta_seconds

    current_speed = get_float_state(hass, speed_entity, 0.0)
    current_shift_state = get_state_text(hass, shift_entity, "")
    current_climate_state = get_state_text(hass, climate_entity, "")
    current_climate_active = is_climate_active(current_climate_state)
    current_elevation = get_float_state(hass, elevation_entity, 0.0)

    trip_state["last_sample_ts"] = now_ts
    trip_state["last_speed"] = current_speed
    trip_state["last_shift_state"] = current_shift_state
    trip_state["last_climate_active"] = current_climate_active
    trip_state["last_climate_state"] = current_climate_state
    trip_state["last_elevation"] = current_elevation
    trip_state["min_elevation"] = min(safe_float(trip_state.get("min_elevation"), current_elevation), current_elevation)
    trip_state["max_elevation"] = max(safe_float(trip_state.get("max_elevation"), current_elevation), current_elevation)
    trip_state.update(speed_sampling_debug_fields(trip_state))
    trip_state.update(traffic_sampling_debug_fields(trip_state))

    hass.data[DOMAIN][state_key] = trip_state

def update_all_active_tracking_states(
    hass: HomeAssistant,
    integration_data: dict[str, Any],
) -> None:
    """Update runtime tracking metrics for all active report modes."""
    for state_key in (TRIP_STATE_KEY, MANUAL_TRACKING_STATE_KEY):
        update_runtime_tracking_fields(hass, integration_data, state_key)


def build_trip_report_data_from_json(
    json_path: str,
    output_path: str,
    integration_data: dict[str, Any],
) -> str:
    """Read existing trip JSON, enrich it, and render PNG."""
    path = Path(json_path)

    if not path.exists():
        raise FileNotFoundError(f"Trip JSON dosyası bulunamadı: {json_path}")

    with path.open("r", encoding="utf-8") as file:
        source = json.load(file)

    used_kwh = safe_float(source.get("used_kwh"), 0.0)
    trip_km_value = safe_float(source.get("trip_km"), 0.0)
    moving_seconds_value = safe_float(source.get("moving_seconds"), 0.0)
    tessie_average_speed = average_speed_distance_over_moving_time(trip_km_value, moving_seconds_value)
    if tessie_average_speed <= 0:
        tessie_average_speed = safe_float(source.get("average_moving_speed") or source.get("average_speed") or source.get("average_overall_speed"), 0.0)

    supercharger_price = safe_float(integration_data.get(CONF_SUPERCHARGER_PRICE), DEFAULT_SUPERCHARGER_PRICE)
    zes_price = safe_float(integration_data.get(CONF_ZES_PRICE), DEFAULT_ZES_PRICE)
    astor_price = safe_float(integration_data.get(CONF_ASTOR_PRICE), DEFAULT_ASTOR_PRICE)

    report_data = {
        "test_mode": False,
        "currency_label": get_report_currency(integration_data),
        "report_date": source.get("report_date") or datetime.now().strftime("%d.%m.%Y %H:%M"),
        "trip_km": source.get("trip_km"),
        "duration_text": source.get("duration_text"),
        "traffic_text": source.get("traffic_text") or source.get("moving_text"),
        "average_speed": f"{tessie_average_speed:.1f}",
        "used_kwh": source.get("used_kwh"),
        "consumption_kwh_100km": source.get("consumption_kwh_100km"),
        "start_battery": source.get("start_battery"),
        "end_battery": source.get("end_battery"),
        "climate_text": source.get("climate_text"),
        "min_elevation": source.get("min_elevation"),
        "max_elevation": source.get("max_elevation"),
        "elevation_range": source.get("elevation_range"),
        "supercharger_kwh_price": f"{supercharger_price:.2f}",
        "zes_kwh_price": f"{zes_price:.2f}",
        "astor_kwh_price": f"{astor_price:.2f}",
        "supercharger_trip_cost": f"{used_kwh * supercharger_price:.2f}",
        "zes_trip_cost": f"{used_kwh * zes_price:.2f}",
        "astor_trip_cost": f"{used_kwh * astor_price:.2f}",
        "cost_presets": get_trip_cost_presets(integration_data, used_kwh),
        "duration_minutes": source.get("duration_minutes"),
        "climate_duration_minutes": source.get("climate_duration_minutes"),
        "climate_duration_text": source.get("climate_duration_text"),
        "start_address": str(source.get("start_address") or "").strip(),
        "end_address": str(source.get("end_address") or "").strip(),
        **get_report_visibility_options(integration_data),
    }

    enrich_trip_report_score(report_data, lang=get_report_language(integration_data))
    return render_trip_report_png(report_data, output_path, get_report_language(integration_data))


def build_manual_trip_report_data(
    trip_state: dict[str, Any],
    integration_data: dict[str, Any],
    finish_data: dict[str, Any],
) -> dict[str, Any]:
    """Build report data from a start/finish state pair."""
    now_ts = datetime.now().timestamp()

    start_ts = safe_float(trip_state.get("start_ts"), now_ts)
    duration_seconds = max(0.0, now_ts - start_ts)

    if "override_duration_minutes" in finish_data:
        duration_minutes = safe_float(finish_data.get("override_duration_minutes"), 0.0)
        duration_seconds = duration_minutes * 60
    else:
        duration_minutes = duration_seconds / 60

    start_odometer = safe_float(trip_state.get("start_odometer"), 0.0)
    end_odometer = safe_float(finish_data.get("end_odometer"), start_odometer)
    trip_km = max(0.0, end_odometer - start_odometer)

    if "override_trip_km" in finish_data:
        trip_km = max(0.0, safe_float(finish_data.get("override_trip_km"), trip_km))

    start_energy = safe_float(trip_state.get("start_energy_kwh"), 0.0)
    end_energy = safe_float(finish_data.get("end_energy_kwh"), start_energy)
    used_kwh = max(0.0, start_energy - end_energy)

    if "override_used_kwh" in finish_data:
        used_kwh = max(0.0, safe_float(finish_data.get("override_used_kwh"), used_kwh))

    start_battery = safe_float(trip_state.get("start_battery"), 0.0)
    end_battery = safe_float(finish_data.get("end_battery"), start_battery)

    if "override_end_battery" in finish_data:
        end_battery = safe_float(finish_data.get("override_end_battery"), end_battery)

    consumption = 0.0
    if trip_km > 0:
        consumption = used_kwh / trip_km * 100

    average_overall_speed = 0.0
    if duration_seconds > 0:
        average_overall_speed = trip_km / (duration_seconds / 3600)

    speed_debug = speed_sampling_debug_fields(trip_state)
    sample_average_speed = safe_float(speed_debug.get("average_moving_speed"), 0.0)
    average_moving_speed = average_speed_distance_over_moving_time(trip_km, speed_debug.get("moving_seconds", 0.0))
    if average_moving_speed <= 0:
        average_moving_speed = sample_average_speed
    average_speed = average_moving_speed if average_moving_speed > 0 else average_overall_speed

    traffic_debug = traffic_sampling_debug_fields(trip_state)
    traffic_model_debug = traffic_delay_model_fields(
        trip_state,
        distance_km=trip_km,
        moving_seconds=speed_debug.get("moving_seconds", 0.0),
        moving_average_speed=average_moving_speed,
    )
    if "override_traffic_minutes" in finish_data:
        traffic_minutes = safe_float(finish_data.get("override_traffic_minutes"), 0.0)
        traffic_text = format_duration_from_minutes(traffic_minutes)
    else:
        traffic_minutes = safe_float(traffic_debug.get("traffic_minutes"), 0.0)
        traffic_text = str(traffic_debug.get("traffic_text") or format_duration_from_minutes(traffic_minutes))

    start_elevation = safe_float(trip_state.get("start_elevation"), 0.0)
    end_elevation = safe_float(finish_data.get("end_elevation"), start_elevation)

    min_elevation = min(
        safe_float(trip_state.get("min_elevation"), start_elevation),
        start_elevation,
        end_elevation,
    )

    max_elevation = max(
        safe_float(trip_state.get("max_elevation"), start_elevation),
        start_elevation,
        end_elevation,
    )

    elevation_range = max(0.0, max_elevation - min_elevation)

    climate_active_seconds = safe_float(trip_state.get("climate_active_seconds"), 0.0)
    climate_minutes = climate_active_seconds / 60

    if climate_minutes > 0:
        climate_text = f"Klima yolculuk boyunca yaklaşık {format_duration_from_minutes(climate_minutes)} açıktı."
    else:
        climate_text = "Klima yolculuk boyunca kullanılmadı."

    supercharger_price = safe_float(integration_data.get(CONF_SUPERCHARGER_PRICE), DEFAULT_SUPERCHARGER_PRICE)
    zes_price = safe_float(integration_data.get(CONF_ZES_PRICE), DEFAULT_ZES_PRICE)
    astor_price = safe_float(integration_data.get(CONF_ASTOR_PRICE), DEFAULT_ASTOR_PRICE)

    return {
        "test_mode": bool(finish_data.get("test_mode", False)),
        "currency_label": get_report_currency(integration_data),
        "report_date": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "trip_km": f"{trip_km:.2f}",
        "duration_minutes": round(duration_minutes, 2),
        "duration_text": format_duration_from_minutes(duration_minutes),
        "traffic_text": traffic_text,
        "traffic_seconds": traffic_debug.get("traffic_seconds", 0),
        "stopped_in_drive_seconds": traffic_debug.get("stopped_in_drive_seconds", 0),
        "stopped_in_drive_text": traffic_debug.get("stopped_in_drive_text", "—"),
        "slow_traffic_seconds": traffic_debug.get("slow_traffic_seconds", 0),
        "slow_traffic_text": traffic_debug.get("slow_traffic_text", "—"),
        "normal_drive_seconds": traffic_debug.get("normal_drive_seconds", 0),
        "normal_drive_text": traffic_debug.get("normal_drive_text", "—"),
        "parked_pause_seconds": traffic_debug.get("parked_pause_seconds", 0),
        "parked_pause_text": traffic_debug.get("parked_pause_text", "—"),
        "last_traffic_class": traffic_debug.get("last_traffic_class", ""),
        "traffic_model": traffic_model_debug.get("traffic_model", ""),
        "traffic_model_label": traffic_model_debug.get("traffic_model_label", ""),
        "traffic_reference_speed_kmh": f"{safe_float(traffic_model_debug.get('traffic_reference_speed_kmh'), 0.0):.1f}",
        "traffic_reference_trip_type": traffic_model_debug.get("traffic_reference_trip_type", ""),
        "traffic_reference_trip_type_label": traffic_model_debug.get("traffic_reference_trip_type_label", ""),
        "traffic_reference_source": traffic_model_debug.get("traffic_reference_source", ""),
        "traffic_p85_speed_kmh": f"{safe_float(traffic_model_debug.get('traffic_p85_speed_kmh'), 0.0):.1f}",
        "traffic_free_flow_seconds": traffic_model_debug.get("traffic_free_flow_seconds", 0),
        "traffic_free_flow_text": traffic_model_debug.get("traffic_free_flow_text", "—"),
        "traffic_delay_seconds": traffic_model_debug.get("traffic_delay_seconds", 0),
        "traffic_delay_text": traffic_model_debug.get("traffic_delay_text", "—"),
        "traffic_congestion_percent": f"{safe_float(traffic_model_debug.get('traffic_congestion_percent'), 0.0):.1f}",
        "traffic_impact_label": traffic_model_debug.get("traffic_impact_label", ""),
        "traffic_ratio_moving_percent": f"{safe_float(traffic_model_debug.get('traffic_ratio_moving_percent'), 0.0):.1f}",
        "average_speed": f"{average_speed:.1f}",
        "average_moving_speed": f"{average_moving_speed:.1f}",
        "average_overall_speed": f"{average_overall_speed:.1f}",
        "sample_average_speed": f"{sample_average_speed:.1f}",
        "moving_seconds": speed_debug.get("moving_seconds", 0),
        "moving_minutes": speed_debug.get("moving_minutes", 0),
        "moving_duration_text": speed_debug.get("moving_duration_text", "—"),
        "non_moving_seconds": speed_debug.get("non_moving_seconds", 0),
        "speed_sample_count": speed_debug.get("speed_sample_count", 0),
        "moving_speed_sample_count": speed_debug.get("moving_speed_sample_count", 0),
        "max_speed": f"{safe_float(speed_debug.get('max_speed'), 0.0):.1f}",
        "moving_speed_threshold": speed_debug.get("moving_speed_threshold", MOVING_SPEED_THRESHOLD_KMH),
        "used_kwh": f"{used_kwh:.2f}",
        "consumption_kwh_100km": f"{consumption:.2f}",
        "start_battery": f"{start_battery:.1f}",
        "end_battery": f"{end_battery:.1f}",
        "climate_text": climate_text,
        "climate_duration_minutes": round(climate_minutes, 2),
        "climate_duration_text": format_duration_from_minutes(climate_minutes),
        "min_elevation": f"{min_elevation:.0f}",
        "max_elevation": f"{max_elevation:.0f}",
        "elevation_range": f"{elevation_range:.0f}",
        "elevation_gain": f"{safe_float(trip_state.get('elevation_gain'), 0.0):.0f}",
        "elevation_loss": f"{safe_float(trip_state.get('elevation_loss'), 0.0):.0f}",
        "elevation_sample_count": int(safe_float(trip_state.get("elevation_sample_count"), 0.0)),
        "elevation_provider": str(trip_state.get("elevation_provider") or ""),
        "elevation_source": str(trip_state.get("elevation_source") or ""),
        "supercharger_kwh_price": f"{supercharger_price:.2f}",
        "zes_kwh_price": f"{zes_price:.2f}",
        "astor_kwh_price": f"{astor_price:.2f}",
        "supercharger_trip_cost": f"{used_kwh * supercharger_price:.2f}",
        "zes_trip_cost": f"{used_kwh * zes_price:.2f}",
        "astor_trip_cost": f"{used_kwh * astor_price:.2f}",
        "start_address": str(finish_data.get("start_address") or trip_state.get("start_address") or "").strip(),
        "end_address": str(finish_data.get("end_address") or trip_state.get("end_address") or "").strip(),
        "candidate_trip": bool(trip_state.get("candidate_trip", False)),
        "candidate_confirmed": bool(trip_state.get("candidate_confirmed", False)),
        "candidate_confirm_reason": str(trip_state.get("candidate_confirm_reason") or ""),
        "candidate_confirmed_at": str(trip_state.get("candidate_confirmed_at") or ""),
        "candidate_distance_km": round(safe_float(trip_state.get("candidate_distance_km"), trip_km), 3),
        "candidate_duration_seconds": round(safe_float(trip_state.get("candidate_duration_seconds"), duration_seconds), 0),
        "candidate_min_distance_km": round(safe_float(trip_state.get("candidate_min_distance_km"), DEFAULT_LIVE_TRIP_CANDIDATE_MIN_DISTANCE_KM), 3),
        "candidate_min_duration_seconds": round(safe_float(trip_state.get("candidate_min_duration_seconds"), DEFAULT_LIVE_TRIP_CANDIDATE_MIN_DURATION_SECONDS), 0),
        "candidate_finish_decision": trip_state.get("candidate_finish_decision") if isinstance(trip_state.get("candidate_finish_decision"), dict) else {},
        "ignored_short_maneuver": bool(trip_state.get("ignored_short_maneuver", False)),
        "short_maneuver_reason": str(trip_state.get("short_maneuver_reason") or ""),
        "trip_finish_pipeline_started": bool(trip_state.get("trip_finish_pipeline_started", False)),
        "trip_finish_pipeline_source": str(trip_state.get("trip_finish_pipeline_source") or ""),
        "trip_finish_pipeline_started_at": str(trip_state.get("trip_finish_pipeline_started_at") or ""),
        **get_report_visibility_options(integration_data),
    }


def build_start_state(
    hass: HomeAssistant,
    integration_data: dict[str, Any],
    source: str,
) -> dict[str, Any]:
    """Capture the start state used by every trip report mode."""
    now = datetime.now()

    start_odometer = get_float_state(hass, get_report_configured_entity(integration_data, CONF_ODOMETER_ENTITY, VEHICLE_ROLE_ODOMETER), 0.0)
    start_energy = get_float_state(hass, get_report_configured_entity(integration_data, CONF_ENERGY_REMAINING_ENTITY, VEHICLE_ROLE_ENERGY_REMAINING), 0.0)
    start_battery = get_float_state(hass, get_report_configured_entity(integration_data, CONF_BATTERY_LEVEL_ENTITY, VEHICLE_ROLE_BATTERY_LEVEL), 0.0)
    start_elevation = get_float_state(hass, get_report_configured_entity(integration_data, CONF_ELEVATION_ENTITY, VEHICLE_ROLE_ELEVATION), 0.0)
    start_speed = get_float_state(hass, get_report_configured_entity(integration_data, CONF_SPEED_ENTITY, VEHICLE_ROLE_SPEED), 0.0)
    start_shift_state = get_state_text(hass, get_report_configured_entity(integration_data, CONF_SHIFT_STATE_ENTITY, VEHICLE_ROLE_SHIFT_STATE), "")
    climate_state = get_state_text(hass, get_report_configured_entity(integration_data, CONF_CLIMATE_ENTITY, VEHICLE_ROLE_CLIMATE), "")

    return {
        "active": True,
        "started_at": now.strftime("%d.%m.%Y %H:%M:%S"),
        "start_ts": now.timestamp(),
        "start_odometer": start_odometer,
        "start_energy_kwh": start_energy,
        "start_battery": start_battery,
        "start_elevation": start_elevation,
        "min_elevation": start_elevation,
        "max_elevation": start_elevation,
        "start_speed": start_speed,
        "start_shift_state": start_shift_state,
        "start_climate_state": climate_state,
        "climate_active_at_start": is_climate_active(climate_state),
        "traffic_seconds": 0.0,
        "stopped_in_drive_seconds": 0.0,
        "slow_traffic_seconds": 0.0,
        "normal_drive_seconds": 0.0,
        "parked_pause_seconds": 0.0,
        "last_traffic_class": "",
        "climate_active_seconds": 0.0,
        "last_sample_ts": now.timestamp(),
        "last_speed": start_speed,
        "last_shift_state": start_shift_state,
        "last_climate_active": is_climate_active(climate_state),
        "last_climate_state": climate_state,
        "last_elevation": start_elevation,
        "moving_seconds": 0.0,
        "speed_weighted_sum": 0.0,
        "speed_sample_count": 0,
        "moving_speed_sample_count": 0,
        "speed_total_sample_seconds": 0.0,
        "max_speed": max(0.0, start_speed if start_speed > MOVING_SPEED_THRESHOLD_KMH else 0.0),
        "speed_samples": [],
        "last_speed_sample": {},
        "map_points": [],
        "map_point_count": 0,
        "start_tracker_lat": None,
        "start_tracker_lon": None,
        "start_address": "",
        "end_address": "",
        "candidate_trip": bool(live_trip_short_maneuver_settings(integration_data).get("enabled")) if source in {"auto", "auto_delayed"} else False,
        "candidate_confirmed": not bool(live_trip_short_maneuver_settings(integration_data).get("enabled")) if source in {"auto", "auto_delayed"} else True,
        "candidate_started_at": now.strftime("%d.%m.%Y %H:%M:%S") if source in {"auto", "auto_delayed"} and bool(live_trip_short_maneuver_settings(integration_data).get("enabled")) else "",
        "candidate_min_distance_km": round(safe_float(live_trip_short_maneuver_settings(integration_data).get("min_distance_km"), DEFAULT_LIVE_TRIP_CANDIDATE_MIN_DISTANCE_KM), 3),
        "candidate_min_duration_seconds": round(safe_float(live_trip_short_maneuver_settings(integration_data).get("min_duration_seconds"), DEFAULT_LIVE_TRIP_CANDIDATE_MIN_DURATION_SECONDS), 0),
        "candidate_distance_km": 0.0,
        "candidate_duration_seconds": 0.0,
        "candidate_confirm_reason": "",
        "candidate_confirmed_at": "",
        "candidate_finish_decision": {},
        "ignored_short_maneuver": False,
        "short_maneuver_reason": "",
        "trip_finish_pipeline_started": False,
        "trip_finish_pipeline_source": "",
        "trip_finish_pipeline_started_at": "",
        "start_source": source,
    }


async def async_create_persistent_notification(
    hass: HomeAssistant,
    *,
    title: str,
    message: str,
    notification_id: str,
) -> None:
    """Create a persistent notification."""
    await hass.services.async_call(
        "persistent_notification",
        "create",
        {
            "title": title,
            "message": message,
            "notification_id": notification_id,
        },
        blocking=True,
    )




async def async_call_openai_responses_api(
    hass: HomeAssistant,
    *,
    api_key: str,
    model: str,
    system_prompt: str,
    user_message: str,
    context_text: str,
    max_output_tokens: int,
) -> str:
    """Call OpenAI Responses API and return text."""
    session = async_get_clientsession(hass)

    input_messages = [
        {
            "role": "system",
            "content": [
                {
                    "type": "input_text",
                    "text": system_prompt,
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": f"{context_text}\n\nKullanıcı mesajı:\n{user_message}",
                }
            ],
        },
    ]

    payload = {
        "model": model,
        "input": input_messages,
        "max_output_tokens": max_output_tokens,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
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
                error_message = "OpenAI API isteği başarısız oldu."
                if isinstance(response_data, dict):
                    error = response_data.get("error")
                    if isinstance(error, dict):
                        error_message = str(error.get("message") or error_message)
                raise ValueError(f"HTTP {response.status}: {error_message}")

    except ClientError as err:
        raise ValueError(f"OpenAI API bağlantı hatası: {err}") from err

    answer = extract_openai_response_text(response_data)

    if not answer:
        raise ValueError("OpenAI API cevap verdi ama okunabilir metin dönmedi.")

    return answer


def normalize_telegram_id(value: Any) -> str:
    """Normalize Telegram chat/user IDs for string comparison."""
    return str(value or "").strip()


def strip_ai_prefix(message: str, prefix: str) -> str | None:
    """Return message without prefix, or None if prefix does not match."""
    text = str(message or "").strip()
    prefix_text = str(prefix or "").strip()

    if not text or not prefix_text:
        return text or None

    lowered = text.lower()
    lowered_prefix = prefix_text.lower()

    if not lowered.startswith(lowered_prefix):
        return None

    if len(text) > len(prefix_text) and text[len(prefix_text)].isalnum():
        return None

    remaining = text[len(prefix_text):].strip()
    remaining = remaining.lstrip(" ,.:;-_/\\|!?").strip()

    return remaining or text


def build_ai_personality_prompt(data: dict[str, Any]) -> str:
    """Build the user-selected personality and safety prompt."""
    personality = str(data.get(CONF_AI_PERSONALITY, DEFAULT_AI_PERSONALITY) or DEFAULT_AI_PERSONALITY)
    if personality == AI_PERSONALITY_TURKISH_BUDDY:
        personality = AI_PERSONALITY_LAZ_BLACK_SEA
    if personality not in {
        AI_PERSONALITY_PROFESSIONAL,
        AI_PERSONALITY_FRIENDLY,
        AI_PERSONALITY_FUNNY,
        AI_PERSONALITY_LAZ_BLACK_SEA,
    }:
        personality = DEFAULT_AI_PERSONALITY
    answer_length = str(data.get(CONF_AI_ANSWER_LENGTH, DEFAULT_AI_ANSWER_LENGTH) or DEFAULT_AI_ANSWER_LENGTH)
    ai_name = str(data.get(CONF_AI_NAME, DEFAULT_AI_NAME) or DEFAULT_AI_NAME).strip() or DEFAULT_AI_NAME
    user_address_instruction = build_ai_user_address_instruction(data, APP_LANGUAGE_TR)

    personality_map = {
        AI_PERSONALITY_PROFESSIONAL: "Ciddi, teknik, profesyonel ve net konuş. Gereksiz espri yapma.",
        AI_PERSONALITY_FRIENDLY: "Samimi, yardımcı ve doğal konuş. Abartılı samimiyet veya gereksiz övgü kullanma.",
        AI_PERSONALITY_FUNNY: "Komik, sıcak, kıvrak ve biraz daha eğlenceli konuş. Cevaplara doğal bir espri, otomobil/teknoloji temalı minik bir takılma veya zekice kısa benzetme ekle; kullanıcı ciddi konuşuyorsa tonu yumuşat ama tamamen düzleşme. Kısa cevapta bile mümkünse bir esprili ifade kullan; uzun cevapta 1-2 hafif espri yeterlidir. Verileri asla yanlış aktarma, güvenlik/araç kontrolü/sağlık/finans gibi ciddi konularda şakayı geri plana al.",
        AI_PERSONALITY_LAZ_BLACK_SEA: "Hafif Karadeniz/Laz şivesiyle doğal konuş. 'uşağum', 'haçan', 'da' gibi yöresel ifadeleri ölçülü kullan; karikatürize etme, teknik değerleri net ve doğru aktar. Kullanıcı ciddi bir konu sorarsa şiveyi hafiflet ama sıcaklığı koru.",
    }

    length_map = {
        AI_ANSWER_LENGTH_SHORT: "Cevap uzunluğu: kısa. Genelde 1-3 cümle yeterli.",
        AI_ANSWER_LENGTH_NORMAL: "Cevap uzunluğu: normal. Gerekirse birkaç madde kullanabilirsin.",
        AI_ANSWER_LENGTH_DETAILED: "Cevap uzunluğu: detaylı. Kullanıcı analiz isterse gerekçeli açıkla.",
    }

    return "\n".join([
        f"Sen {ai_name} adında, Tesla ve Home Assistant verilerini yorumlayan araç asistanısın.",
        f"Kullanıcı adını sorarsa kendi adının {ai_name} olduğunu söyle.",
        user_address_instruction,
        "Kullanıcı hangi dilde yazıyorsa öncelikle aynı dilde cevap ver. Kullanıcı dili değiştirirse sen de aynı dile uyum sağla.",
        personality_map.get(personality, personality_map[AI_PERSONALITY_FRIENDLY]),
        length_map.get(answer_length, length_map[AI_ANSWER_LENGTH_SHORT]),
        "Sana verilen güncel entity verilerini ve rapor özetlerini esas al.",
        "Veri yoksa veya stale/unavailable görünüyorsa uydurma; eksik veriyi açıkça söyle.",
        "Bir entity unavailable/unknown ise kullanıcıya bu veriyi şu anda göremediğini söyle; araç uyandığında veya hareket halindeyken okunabilir olabileceğini belirt.",
        "Vehicle state / sleep status entity'si yoksa veya net sleep/asleep/awake/online verisi yoksa aracın uyuduğunu kesin söyleme; sadece parkta ve veri sınırlı göründüğünü söyle.",
        "Açık adres bilgisi varsa konum sorularında koordinat yerine mümkün olduğunca bu adresi kullan; adres yoksa uydurma.",
        "Bilgi sorularında sadece veri yorumla; servis çağrısını LLM olarak sen uydurma.",
        "Araç kontrol komutları entegrasyonun onaylı kontrol sistemi tarafından işlenir.",
        "Kullanıcı araç kontrolü isterse komutun onay gerektirdiğini kısa ve net söyle; onay akışını entegrasyon başlatır.",
        "Entity isimlerini kullanıcı istemedikçe uzun uzun listeleme; doğal insan diliyle özetle.",
    ])


def build_final_ai_system_prompt(data: dict[str, Any]) -> str:
    """Build final system prompt from app-managed settings only."""
    return build_ai_personality_prompt(data)


def get_ai_display_name(data: dict[str, Any]) -> str:
    """Return the configured AI display name."""
    return str(data.get(CONF_AI_NAME, DEFAULT_AI_NAME) or DEFAULT_AI_NAME).strip() or DEFAULT_AI_NAME


def get_ai_user_address(data: dict[str, Any]) -> str:
    """Return the configured way the AI should address the user."""
    raw = str(data.get(CONF_AI_USER_ADDRESS, DEFAULT_AI_USER_ADDRESS) or "").strip()
    raw = re.sub(r"[\r\n\t]+", " ", raw)
    raw = re.sub(r"\s{2,}", " ", raw).strip()
    return raw[:80]


def build_ai_user_address_instruction(data: dict[str, Any], lang: str = APP_LANGUAGE_TR) -> str:
    """Return a strict instruction for user addressing."""
    address = get_ai_user_address(data)
    en = str(lang or "").lower().startswith("en")
    if address:
        if en:
            return f"When addressing the user directly, use exactly this address/name: {address}. Do not use Berkan unless this field is Berkan."
        return f"Kullanıcıya doğrudan hitap ederken ayardaki hitap şeklini aynen kullan: {address}. Bu alan Berkan değilse Berkan deme."
    if en:
        return "Do not call the user Berkan or any personal name. If addressing is needed, use a neutral form such as 'you' or avoid a name."
    return "Kullanıcıya Berkan veya başka bir özel isimle hitap etme. Hitap gerekiyorsa nötr konuş veya isim kullanma."


async def async_generate_pom_ai_answer(
    hass: HomeAssistant,
    data: dict[str, Any],
    *,
    user_message: str,
    include_context: bool,
    telegram_target: str | None = None,
) -> str:
    """Generate a POM AI answer using the integration's own OpenAI API settings."""
    if not get_bool_option(data, CONF_AI_ENABLED, DEFAULT_AI_ENABLED):
        raise ValueError("POM AI Basic kapalı. Configure > POM AI Basic bölümünden aktif etmelisin.")

    api_key = str(data.get(CONF_OPENAI_API_KEY, "")).strip()
    if not api_key:
        raise ValueError("OpenAI API key boş. Configure > POM AI Basic bölümüne API key gir.")

    model = str(data.get(CONF_OPENAI_MODEL, DEFAULT_OPENAI_MODEL)).strip() or DEFAULT_OPENAI_MODEL
    system_prompt = build_final_ai_system_prompt(data)
    max_output_tokens = int(safe_float(data.get(CONF_AI_MAX_OUTPUT_TOKENS), DEFAULT_AI_MAX_OUTPUT_TOKENS))
    max_output_tokens = max(100, min(max_output_tokens, 4000))

    if include_context:
        await async_update_reverse_geocode_cache(hass, data)

    context_text = build_ai_context_text(hass, data) if include_context else "Bağlam verisi bu çağrıda kapalı."
    recent_memory = get_pom_ai_recent_conversation_text(hass, telegram_target) if telegram_target else ""
    if recent_memory:
        context_text = f"{context_text}\n\n{recent_memory}"
    context_text = f"{context_text}\n\n{build_current_message_language_instruction(user_message)}"

    pre_suggestion_action = build_contextual_vehicle_suggestion_without_llm(
        hass,
        data,
        user_message=user_message,
        assistant_answer="",
    )
    if pre_suggestion_action and not pre_suggestion_action.get("error"):
        context_text = (
            f"{context_text}\n\n"
            "PENDING_SUGGESTION_HINT:\n"
            f"The user's message can safely map to this follow-up action: {pre_suggestion_action.get('label')}. "
            "If you offer to do it, keep the wording clear because the system will remember this as the next pending suggestion."
        )

    return await async_call_openai_responses_api(
        hass,
        api_key=api_key,
        model=model,
        system_prompt=system_prompt,
        user_message=user_message,
        context_text=context_text,
        max_output_tokens=max_output_tokens,
    )


def get_alert_telegram_target(data: dict[str, Any]) -> str:
    """Return Telegram target for proactive alerts."""
    return str(
        data.get(CONF_AI_TELEGRAM_TARGET)
        or data.get(CONF_AI_TELEGRAM_LISTENER_CHAT_ID)
        or data.get(CONF_TELEGRAM_TARGET)
        or ""
    ).strip()


def is_state_truthy_for_alert(value: Any) -> bool:
    """Return true for open/on/unlocked style states."""
    text = str(value or "").strip().lower()
    return text in {"on", "open", "opened", "unlocked", "true", "yes", "detected", "active"}


def is_charging_state(value: Any) -> bool:
    """Return true for charging-like states."""
    text = str(value or "").strip().lower()
    return text in {"on", "charging", "true", "yes", "connected", "plugged_in", "plugged in"}


def get_ai_alert_state(hass: HomeAssistant) -> dict[str, Any]:
    """Return mutable AI alert runtime state."""
    return hass.data.setdefault(DOMAIN, {}).setdefault("ai_alert_state", {})


def alert_cooldown_allows(hass: HomeAssistant, key: str, cooldown_minutes: float) -> bool:
    """Return whether an alert may be sent considering cooldown."""
    state = get_ai_alert_state(hass)
    last_sent = safe_float(state.get("last_sent", {}).get(key), 0.0)
    now_ts = datetime.now().timestamp()
    return (now_ts - last_sent) >= max(60.0, cooldown_minutes * 60.0)


def mark_alert_sent(hass: HomeAssistant, key: str) -> None:
    """Mark alert as sent."""
    state = get_ai_alert_state(hass)
    state.setdefault("last_sent", {})[key] = datetime.now().timestamp()


async def send_pom_ai_alert(
    hass: HomeAssistant,
    data: dict[str, Any],
    *,
    key: str,
    title: str,
    rule_message: str,
    details: str,
    force: bool = False,
) -> None:
    """Send a proactive alert, optionally using POM AI to write the message."""
    if not get_bool_option(data, CONF_AI_ALERTS_ENABLED, DEFAULT_AI_ALERTS_ENABLED):
        return

    cooldown = safe_float(data.get(CONF_AI_ALERT_COOLDOWN_MINUTES), DEFAULT_AI_ALERT_COOLDOWN_MINUTES)
    if not force and not alert_cooldown_allows(hass, key, cooldown):
        return

    telegram_target = get_alert_telegram_target(data)
    if not telegram_target:
        return

    use_ai = str(data.get(CONF_AI_ALERT_STYLE, DEFAULT_AI_ALERT_STYLE) or DEFAULT_AI_ALERT_STYLE) == AI_ALERT_STYLE_AI
    message = rule_message

    if use_ai and get_bool_option(data, CONF_AI_ENABLED, DEFAULT_AI_ENABLED):
        try:
            message = await async_generate_pom_ai_answer(
                hass,
                data,
                user_message=(
                    "Aşağıdaki olay için Telegram'a gönderilecek kısa bir proaktif Tesla uyarısı yaz. "
                    "Araç kontrolü yapma, servis çağırma, sadece bilgi ver. "
                    "Eğer veri unavailable/unknown ise veri uydurma. "
                    f"Uyarı başlığı: {title}\n"
                    f"Kural mesajı: {rule_message}\n"
                    f"Detaylar: {details}"
                ),
                include_context=True,
            )
        except Exception as err:
            _LOGGER.warning("POM AI alert generation failed for %s: %s", key, err)
            message = rule_message

    await async_telegram_send_message(
        hass,
        data,
        target=telegram_target,
        parse_mode="plain_text",
        message=f"🤖 {get_ai_display_name(data)} Uyarı\n\n{message}",
    )
    mark_alert_sent(hass, key)


def get_numeric_entity_value(hass: HomeAssistant, entity_id: str) -> tuple[float | None, str, str]:
    """Return numeric state, unit and friendly name for an entity."""
    state = hass.states.get(entity_id)
    if state is None:
        return None, "", ""
    try:
        value = float(state.state)
    except (TypeError, ValueError):
        return None, str(state.attributes.get("unit_of_measurement") or ""), str(state.attributes.get("friendly_name") or entity_id)
    return value, str(state.attributes.get("unit_of_measurement") or ""), str(state.attributes.get("friendly_name") or entity_id)


def tire_pressure_to_bar(value: float, unit: str) -> float:
    """Convert tire pressure value to bar when unit is psi/kPa."""
    unit_l = unit.lower()
    if "psi" in unit_l:
        return value / 14.5038
    if "kpa" in unit_l:
        return value / 100.0
    return value


def tire_pressure_to_psi(value: float, unit: str) -> float:
    """Convert tire pressure value to PSI when unit is bar/kPa."""
    unit_l = unit.lower()
    if "bar" in unit_l:
        return value * 14.5038
    if "kpa" in unit_l:
        return value * 0.145038
    return value


def normalize_tire_threshold_to_psi(value: Any) -> float:
    """Return configured tire threshold in PSI. Legacy values <= 8 are treated as bar."""
    threshold = safe_float(value, DEFAULT_AI_ALERT_TIRE_PRESSURE_THRESHOLD_BAR)
    if threshold <= 8:
        return threshold * 14.5038
    return threshold


def get_alert_entities_for_roles(data: dict[str, Any], roles: set[str], *, require_alert_usage: bool = False) -> list[str]:
    """Return Vehicle Entity Manager entities for semantic roles."""
    result: list[str] = []
    for item in get_vehicle_entity_entries(data):
        if item.get("role") not in roles:
            continue
        if require_alert_usage and not item.get("use_alerts"):
            continue
        entity_id = str(item.get("entity_id") or "").strip()
        if entity_id and entity_id not in result:
            result.append(entity_id)
    return result


def get_user_present_entity(hass: HomeAssistant, data: dict[str, Any], candidate_entities: list[str] | None = None) -> str | None:
    """Return the configured or auto-detected user-present/occupancy entity."""
    role_entities = get_alert_entities_for_roles(data, {VEHICLE_ROLE_USER_PRESENT})
    if role_entities:
        return role_entities[0]
    candidates = candidate_entities or get_alert_candidate_entities(hass, data)
    found = find_entities_by_category_or_keywords(
        hass,
        candidates,
        category="Kullanıcı / varlık",
        keywords=["user present", "user_present", "presence", "occupancy", "occupied", "occupant", "driver present", "inside vehicle"],
    )
    return found[0] if found else None


def get_user_absent_for_alert(hass: HomeAssistant, data: dict[str, Any], candidate_entities: list[str] | None = None) -> bool | None:
    """Return True when nobody appears to be in the car, False when present, None when unknown."""
    entity_id = get_user_present_entity(hass, data, candidate_entities)
    if not entity_id:
        return None
    state = hass.states.get(entity_id)
    if state is None:
        return None
    text = str(state.state or "").strip().lower()
    if text in {"on", "true", "yes", "present", "occupied", "detected", "home", "active", "1"}:
        return False
    if text in {"off", "false", "no", "not_present", "not present", "away", "clear", "empty", "unoccupied", "0"}:
        return True
    return None


def get_lock_entities_for_alert(hass: HomeAssistant, data: dict[str, Any], candidate_entities: list[str]) -> list[str]:
    """Return lock-state entities for vehicle lock checks."""
    role_entities = get_alert_entities_for_roles(data, {VEHICLE_ROLE_LOCK_STATE})
    keyword_entities = find_entities_by_category_or_keywords(
        hass,
        candidate_entities,
        keywords=["lock", "locked", "unlocked", "kilit"],
    )
    return dedupe_entities(role_entities + keyword_entities)


def get_vehicle_locked_for_alert(hass: HomeAssistant, data: dict[str, Any], candidate_entities: list[str]) -> bool | None:
    """Return True when lock entities indicate locked, False when any is unlocked, None when unknown."""
    lock_entities = get_lock_entities_for_alert(hass, data, candidate_entities)
    if not lock_entities:
        return None
    saw_locked = False
    for entity_id in lock_entities:
        state = hass.states.get(entity_id)
        if state is None:
            continue
        text = str(state.state or "").strip().lower()
        if text in {"unlocked", "off", "false", "open"}:
            return False
        if text in {"locked", "lock", "on", "true", "closed"}:
            saw_locked = True
    return True if saw_locked else None


def is_door_window_entity_for_alert(hass: HomeAssistant, entity_id: str) -> bool:
    """Return true for door/window/frunk/trunk entities, excluding lock/sentry controls."""
    state = hass.states.get(entity_id)
    friendly = state.attributes.get("friendly_name") if state is not None else ""
    haystack = normalize_text_for_match(f"{entity_id} {friendly or ''} {state.attributes if state is not None else ''}")
    if any(k in haystack for k in ["lock", "locked", "unlocked", "sentry", "valet"]):
        return False
    return any(k in haystack for k in ["door", "window", "trunk", "frunk", "kapı", "kapi", "cam", "bagaj", "pencere"])


def build_low_battery_staged_message(battery_level: float, stage: int) -> str:
    """Return POM-style staged low battery alert text."""
    level_text = f"%{battery_level:.0f}"
    if stage == 1:
        return f"Boku yedik galiba. Batarya {level_text} seviyesine indi. Umarım şu an şarj istasyonu arıyorsundur."
    if stage == 5:
        return f"Batarya {level_text}. POM hafif gerilmeye başladı. Åarj planını artık ertelemesen iyi olur."
    if stage == 10:
        return f"Kaptan, batarya {level_text}. Artık 'sonra bakarım' seviyesi değil; uygun bir şarj noktası bakmak iyi olur."
    return f"Patlamadık değil mi kanka? Batarya {level_text} seviyesine indi. Åarj planı yapmak iyi olabilir."


def get_low_battery_stage_to_send(hass: HomeAssistant, battery_level: float) -> int | None:
    """Return the next one-shot low battery stage, resetting after battery rises above 20%."""
    runtime = get_ai_alert_state(hass)
    sent_stages = set(runtime.setdefault("low_battery_sent_stages", []))
    if battery_level > 20:
        runtime["low_battery_sent_stages"] = []
        return None
    eligible = [stage for stage in (20, 10, 5, 1) if 0 <= battery_level <= stage]
    if not eligible:
        return None
    stage = min(eligible)
    if stage in sent_stages:
        return None
    return stage


def mark_low_battery_stage_sent(hass: HomeAssistant, stage: int) -> None:
    """Mark one low battery threshold as sent."""
    runtime = get_ai_alert_state(hass)
    sent = set(runtime.setdefault("low_battery_sent_stages", []))
    sent.add(stage)
    runtime["low_battery_sent_stages"] = sorted(sent)


def temperature_to_c(value: float, unit: str) -> float:
    """Convert temperature value to Celsius when needed."""
    unit_l = unit.lower()
    if "°f" in unit_l or "fahrenheit" in unit_l:
        return (value - 32) * 5 / 9
    return value


def get_alert_candidate_entities(hass: HomeAssistant, data: dict[str, Any]) -> list[str]:
    """Return entity ids available to alert watchers."""
    selection = build_ai_context_entity_selection(hass, data)
    max_entities = int(safe_float(data.get(CONF_AI_MAX_CONTEXT_ENTITIES), DEFAULT_AI_MAX_CONTEXT_ENTITIES))
    return dedupe_entities(selection.get("entity_ids", []))[: max(10, min(max_entities, 200))]


def find_entities_by_category_or_keywords(
    hass: HomeAssistant,
    entity_ids: list[str],
    *,
    category: str | None = None,
    keywords: list[str] | None = None,
) -> list[str]:
    """Find context entities by AI category and/or keyword."""
    results: list[str] = []
    normalized_keywords = [normalize_text_for_match(k) for k in (keywords or [])]
    for entity_id in entity_ids:
        state = hass.states.get(entity_id)
        entity_category = categorize_entity_for_ai(entity_id, state)
        friendly = state.attributes.get("friendly_name") if state is not None else ""
        haystack = normalize_text_for_match(f"{entity_id} {friendly or ''} {state.attributes if state is not None else ''}")
        if category and entity_category == category:
            results.append(f"{label} komutu gonderildi.")
            continue
        if normalized_keywords and any(k in haystack for k in normalized_keywords):
            results.append(f"{label} komutu gonderildi.")
    return dedupe_entities(results)


def is_window_entity_for_alert(hass: HomeAssistant, entity_id: str) -> bool:
    """Return true when an entity looks like a Tesla window entity."""
    state = hass.states.get(entity_id)
    friendly = state.attributes.get("friendly_name") if state is not None else ""
    haystack = normalize_text_for_match(f"{entity_id} {friendly or ''} {state.attributes if state is not None else ''}")
    window_keywords = [
        "window",
        "windows",
        "cam",
        "pencere",
        "front left window",
        "front right window",
        "rear left window",
        "rear right window",
        "driver window",
        "passenger window",
    ]
    return any(keyword in haystack for keyword in window_keywords)


def get_window_alert_entities(hass: HomeAssistant, data: dict[str, Any]) -> list[str]:
    """Return window-like entities from AI context candidates."""
    candidates = get_alert_candidate_entities(hass, data)
    return dedupe_entities([entity_id for entity_id in candidates if is_window_entity_for_alert(hass, entity_id)])


def build_alert_diagnostics_message(hass: HomeAssistant, data: dict[str, Any]) -> str:
    """Build a readable diagnostics report for proactive alerts."""
    runtime = get_ai_alert_state(hass)
    last_sent = runtime.get("last_sent", {}) if isinstance(runtime.get("last_sent", {}), dict) else {}
    cooldown_minutes = safe_float(data.get(CONF_AI_ALERT_COOLDOWN_MINUTES), DEFAULT_AI_ALERT_COOLDOWN_MINUTES)
    telegram_target = get_alert_telegram_target(data)

    battery_entity = get_report_configured_entity(data, CONF_BATTERY_LEVEL_ENTITY, VEHICLE_ROLE_BATTERY_LEVEL)
    battery_state = hass.states.get(battery_entity) if battery_entity else None
    battery_value = get_float_state(hass, battery_entity, -1) if battery_entity else -1
    battery_threshold = safe_float(data.get(CONF_AI_ALERT_LOW_BATTERY_THRESHOLD), DEFAULT_AI_ALERT_LOW_BATTERY_THRESHOLD)
    battery_would_trigger = get_bool_option(data, CONF_AI_ALERT_LOW_BATTERY_ENABLED, DEFAULT_AI_ALERT_LOW_BATTERY_ENABLED) and 0 <= battery_value <= battery_threshold

    window_entities = get_window_alert_entities(hass, data)
    window_lines = []
    window_would_trigger = False
    for entity_id in window_entities[:30]:
        state = hass.states.get(entity_id)
        state_text = str(state.state) if state else "not_found"
        is_open = state is not None and is_state_truthy_for_alert(state.state)
        if is_open:
            window_would_trigger = True
        friendly = state.attributes.get("friendly_name") if state else entity_id
        window_lines.append(f"- {entity_id}: {state_text} | {friendly} | open={is_open}")
    if len(window_entities) > 30:
        window_lines.append(f"- ... {len(window_entities) - 30} window/cam entity daha var")
    if not window_lines:
        window_lines.append("- Bulunan cam/window entity yok. Selected AI entities içine cam entity'lerini ekle.")

    def cooldown_line(key: str) -> str:
        allows = alert_cooldown_allows(hass, key, cooldown_minutes)
        last = safe_float(last_sent.get(key), 0.0)
        if last <= 0:
            return f"{key}: cooldown açık değil / daha önce gönderilmemiş"
        minutes_ago = (datetime.now().timestamp() - last) / 60
        return f"{key}: {'uygun' if allows else 'cooldown aktif'} · son gönderim {minutes_ago:.1f} dk önce"

    lines = [
        "🧪 POM Alert Diagnostics",
        "",
        f"Proactive alerts: {get_bool_option(data, CONF_AI_ALERTS_ENABLED, DEFAULT_AI_ALERTS_ENABLED)}",
        f"Alert style: {data.get(CONF_AI_ALERT_STYLE, DEFAULT_AI_ALERT_STYLE)}",
        f"Telegram target: {telegram_target or 'boş'}",
        f"Cooldown: {cooldown_minutes:.0f} dk",
        "",
        "LOW BATTERY",
        f"Enabled: {get_bool_option(data, CONF_AI_ALERT_LOW_BATTERY_ENABLED, DEFAULT_AI_ALERT_LOW_BATTERY_ENABLED)}",
        f"Battery entity: {battery_entity or 'seçilmemiş'}",
        f"Current value: {battery_state.state if battery_state else 'not_found'}",
        f"Parsed value: {battery_value if battery_value >= 0 else 'okunamadı'}",
        "Stages: %20 / %10 / %5 / %1",
        f"Sent stages this cycle: {runtime.get('low_battery_sent_stages', [])}",
        f"Would trigger now: {get_low_battery_stage_to_send(hass, battery_value) if battery_value >= 0 else 'okunamadı'}",
    ]
    return "\n".join(lines)


async def evaluate_pom_ai_alerts(hass: HomeAssistant, data: dict[str, Any]) -> None:
    """Evaluate configured proactive AI alerts."""
    if not get_bool_option(data, CONF_AI_ALERTS_ENABLED, DEFAULT_AI_ALERTS_ENABLED):
        return

    candidate_entities = get_alert_candidate_entities(hass, data)
    runtime = get_ai_alert_state(hass)
    active_since = runtime.setdefault("active_since", {})
    now_ts = datetime.now().timestamp()

    # 1) Staged low battery: 20 / 10 / 5 / 1. Each stage is sent once until battery rises above 20%.
    if get_bool_option(data, CONF_AI_ALERT_LOW_BATTERY_ENABLED, DEFAULT_AI_ALERT_LOW_BATTERY_ENABLED):
        battery_entity = get_report_configured_entity(data, CONF_BATTERY_LEVEL_ENTITY, VEHICLE_ROLE_BATTERY_LEVEL)
        battery_level = get_float_state(hass, battery_entity, -1)
        stage = get_low_battery_stage_to_send(hass, battery_level)
        if stage is not None:
            await send_pom_ai_alert(
                hass,
                data,
                key=f"low_battery_{stage}",
                title=f"Düşük batarya %{stage}",
                rule_message=build_low_battery_staged_message(battery_level, stage),
                details=f"battery_entity={battery_entity}, battery_level={battery_level}, stage={stage}",
                force=True,
            )
            mark_low_battery_stage_sent(hass, stage)

    # 3-4) Charging state transitions. Finished stays. Unexpected stop only warns if user_present says nobody is inside.
    charging_entity = get_configured_entity(data, CONF_CHARGING_ENTITY, VEHICLE_ROLE_CHARGING_STATE, usage_key="use_report")
    charging_now = is_charging_state(get_state_text(hass, charging_entity, ""))
    previous_charging = runtime.get("previous_charging")
    if previous_charging is not None and bool(previous_charging) and not charging_now:
        battery_entity = get_report_configured_entity(data, CONF_BATTERY_LEVEL_ENTITY, VEHICLE_ROLE_BATTERY_LEVEL)
        battery_level = get_float_state(hass, battery_entity, -1)
        if battery_level >= 90 and get_bool_option(data, CONF_AI_ALERT_CHARGE_FINISHED_ENABLED, DEFAULT_AI_ALERT_CHARGE_FINISHED_ENABLED):
            await send_pom_ai_alert(
                hass,
                data,
                key="charge_finished",
                title="Åarj bitti",
                rule_message=f"Åarj tamamlanmış görünüyor. Batarya şu anda yaklaşık %{battery_level:.0f}.",
                details=f"charging_entity={charging_entity}, battery_level={battery_level}",
                force=True,
            )
        elif get_bool_option(data, CONF_AI_ALERT_CHARGING_STOPPED_ENABLED, DEFAULT_AI_ALERT_CHARGING_STOPPED_ENABLED):
            user_absent = get_user_absent_for_alert(hass, data, candidate_entities)
            if user_absent is True:
                await send_pom_ai_alert(
                    hass,
                    data,
                    key="charging_stopped_empty_vehicle",
                    title="Åarj beklenmedik şekilde durdu",
                    rule_message=f"Åarj durmuş görünüyor ve araç içinde kullanıcı algılanmıyor. Batarya yaklaşık %{battery_level:.0f}; kabloyu veya istasyonu kontrol etmek iyi olabilir.",
                    details=f"charging_entity={charging_entity}, battery_level={battery_level}, user_absent={user_absent}",
                    force=True,
                )
            else:
                _LOGGER.debug("Charging stopped alert suppressed. user_absent=%s", user_absent)
    runtime["previous_charging"] = charging_now

    # 5) Tire pressure, user-configurable PSI threshold. Legacy stored bar values are supported.
    if get_bool_option(data, CONF_AI_ALERT_TIRE_PRESSURE_ENABLED, DEFAULT_AI_ALERT_TIRE_PRESSURE_ENABLED):
        tire_entities = dedupe_entities(
            get_alert_entities_for_roles(
                data,
                {
                    VEHICLE_ROLE_TIRE_PRESSURE_FRONT_LEFT,
                    VEHICLE_ROLE_TIRE_PRESSURE_FRONT_RIGHT,
                    VEHICLE_ROLE_TIRE_PRESSURE_REAR_LEFT,
                    VEHICLE_ROLE_TIRE_PRESSURE_REAR_RIGHT,
                },
            )
            + find_entities_by_category_or_keywords(
                hass,
                candidate_entities,
                category="Lastik / basınç",
                keywords=["tire pressure", "tyre pressure", "lastik basinc", "lastik basınç", "tpms"],
            )
        )
        threshold_psi = normalize_tire_threshold_to_psi(data.get(CONF_AI_ALERT_TIRE_PRESSURE_THRESHOLD_BAR))
        low_tires: list[str] = []
        for entity_id in tire_entities:
            value, unit, friendly = get_numeric_entity_value(hass, entity_id)
            if value is None:
                continue
            psi_value = tire_pressure_to_psi(value, unit)
            if psi_value <= threshold_psi:
                low_tires.append(f"{friendly} ({entity_id}) {psi_value:.1f} PSI")
        if low_tires:
            await send_pom_ai_alert(
                hass,
                data,
                key="tire_pressure_low",
                title="Lastik basıncı düşük",
                rule_message=(
                    "Lastik basıncı düşük görünüyor: " + ", ".join(low_tires) + "\n\n"
                    f"Uyarı eşiğin: {threshold_psi:.0f} PSI ve altı. Tesla'da doğru soğuk lastik basıncı model, jant ve lastik ölçüsüne göre değişir; "
                    "en güvenilir değer sürücü kapısı içindeki lastik basıncı etiketidir. Ölçümü lastikler soğukken yapmak, sıcak lastikte görülen yüksek değeri referans almamak ve dört lastiği de etiketteki öneriye göre eşitlemek daha doğru olur."
                ),
                details=f"threshold_psi={threshold_psi}; " + "; ".join(low_tires),
            )

    # 6) High battery temperature unchanged.
    if get_bool_option(data, CONF_AI_ALERT_HIGH_BATTERY_TEMP_ENABLED, DEFAULT_AI_ALERT_HIGH_BATTERY_TEMP_ENABLED):
        temp_entities = find_entities_by_category_or_keywords(
            hass,
            candidate_entities,
            keywords=["battery temperature", "battery module temperature", "batarya sicaklik", "battery temp"],
        )
        threshold_c = safe_float(data.get(CONF_AI_ALERT_HIGH_BATTERY_TEMP_THRESHOLD_C), DEFAULT_AI_ALERT_HIGH_BATTERY_TEMP_THRESHOLD_C)
        high_values: list[str] = []
        for entity_id in temp_entities:
            value, unit, friendly = get_numeric_entity_value(hass, entity_id)
            if value is None:
                continue
            c_value = temperature_to_c(value, unit)
            if c_value >= threshold_c:
                high_values.append(f"{friendly} ({entity_id}) {c_value:.1f} °C")
        if high_values:
            await send_pom_ai_alert(
                hass,
                data,
                key="battery_temperature_high",
                title="Batarya sıcaklığı yüksek",
                rule_message="Batarya sıcaklığı yüksek görünüyor: " + ", ".join(high_values),
                details="; ".join(high_values),
            )

    # 7) Climate left-on alert intentionally removed.

    # 8) Vehicle unlocked: only alert if nobody is present for the configured delay. Default is 2 minutes.
    if get_bool_option(data, CONF_AI_ALERT_UNLOCKED_ENABLED, DEFAULT_AI_ALERT_UNLOCKED_ENABLED):
        lock_entities = get_lock_entities_for_alert(hass, data, candidate_entities)
        unlocked = []
        for entity_id in lock_entities:
            state = hass.states.get(entity_id)
            if state and str(state.state).lower() == "unlocked":
                unlocked.append(entity_id)
        user_absent = get_user_absent_for_alert(hass, data, candidate_entities)
        key = "vehicle_unlocked_empty_vehicle"
        if unlocked and user_absent is True:
            active_since.setdefault(key, now_ts)
            delay = safe_float(data.get(CONF_AI_ALERT_UNLOCKED_DELAY_MINUTES), DEFAULT_AI_ALERT_UNLOCKED_DELAY_MINUTES) * 60
            if now_ts - safe_float(active_since.get(key), now_ts) >= delay:
                await send_pom_ai_alert(
                    hass,
                    data,
                    key=key,
                    title="Araç kilitsiz kaldı",
                    rule_message=f"Araç {int(delay/60)} dakikadır kilitsiz görünüyor ve içeride kullanıcı algılanmıyor: " + ", ".join(unlocked),
                    details="; ".join(unlocked) + f"; user_absent={user_absent}",
                )
        else:
            active_since.pop(key, None)

    # 9) Door/window alert: only if nobody is present AND vehicle is locked.
    if get_bool_option(data, CONF_AI_ALERT_DOOR_WINDOW_OPEN_ENABLED, DEFAULT_AI_ALERT_DOOR_WINDOW_OPEN_ENABLED):
        role_open_entities = get_alert_entities_for_roles(data, {VEHICLE_ROLE_DOOR_WINDOW})
        keyword_open_entities = find_entities_by_category_or_keywords(
            hass,
            candidate_entities,
            keywords=["door", "window", "trunk", "frunk", "kapı", "kapi", "cam", "bagaj", "pencere"],
        )
        open_entities = [entity_id for entity_id in dedupe_entities(role_open_entities + keyword_open_entities) if is_door_window_entity_for_alert(hass, entity_id)]
        opened = []
        for entity_id in open_entities:
            state = hass.states.get(entity_id)
            if state and is_state_truthy_for_alert(state.state):
                friendly = str(state.attributes.get("friendly_name") or entity_id)
                opened.append(f"{friendly} ({entity_id})")
        user_absent = get_user_absent_for_alert(hass, data, candidate_entities)
        vehicle_locked = get_vehicle_locked_for_alert(hass, data, candidate_entities)
        key = "door_window_open_locked_empty_vehicle"
        if opened and user_absent is True and vehicle_locked is True:
            active_since.setdefault(key, now_ts)
            delay = safe_float(data.get(CONF_AI_ALERT_DOOR_WINDOW_OPEN_DELAY_MINUTES), DEFAULT_AI_ALERT_DOOR_WINDOW_OPEN_DELAY_MINUTES) * 60
            if now_ts - safe_float(active_since.get(key), now_ts) >= delay:
                await send_pom_ai_alert(
                    hass,
                    data,
                    key=key,
                    title="Kilitliyken kapı/cam açık kaldı",
                    rule_message="Araç kilitli ve içeride kullanıcı algılanmıyor; buna rağmen açık görünen kapı/cam var: " + ", ".join(opened),
                    details="; ".join(opened) + f"; user_absent={user_absent}; vehicle_locked={vehicle_locked}",
                )
        else:
            active_since.pop(key, None)


async def async_register_dashboard_static_assets(hass: HomeAssistant) -> None:
    """Serve bundled Tesla dashboard placeholder/background files."""
    data = hass.data.setdefault(DOMAIN, {})
    if data.get("dashboard_static_assets_registered"):
        return

    asset_dir = Path(__file__).resolve().parent / "dashboard" / "png"
    if not asset_dir.exists():
        _LOGGER.warning("POM Tesla dashboard asset directory not found: %s", asset_dir)
        return

    try:
        from homeassistant.components.http import StaticPathConfig

        await hass.http.async_register_static_paths(
            [StaticPathConfig(DASHBOARD_STATIC_ASSET_URL_PATH, str(asset_dir), False)]
        )
    except Exception as err:  # pragma: no cover - compatibility fallback
        try:
            hass.http.register_static_path(DASHBOARD_STATIC_ASSET_URL_PATH, str(asset_dir), False)
        except Exception as fallback_err:
            _LOGGER.warning(
                "Could not register POM Tesla dashboard asset path: %s / %s",
                err,
                fallback_err,
            )
            return

    data["dashboard_static_assets_registered"] = True
    _LOGGER.info(
        "POM Tesla dashboard assets served at %s from %s",
        DASHBOARD_STATIC_ASSET_URL_PATH,
        asset_dir,
    )




def _dashboard_frontend_version() -> str:
    """Return a cache-busting version for bundled dashboard frontend resources.

    Keep this synchronous and file-read-free. Home Assistant 2026 flags
    pathlib.read_text/open calls inside the event loop, and this function is
    reached during integration setup.
    """
    return DASHBOARD_FRONTEND_VERSION


def _resource_base_url(url: str) -> str:
    """Return Lovelace resource URL without query parameters."""
    return str(url or "").split("?", 1)[0].strip()


def _dashboard_resource_items() -> list[dict[str, str]]:
    """Return bundled POM Lovelace resources that should be present.

    We register both the integration static path and the /local fallback.
    Some HA/browser sessions can keep an old resource registry cache or load
    custom resources before the integration static route is available. The
    /local/pom_tesla_report copies are therefore kept as a reliable fallback.
    The JS files guard customElements.define(), so loading both URLs is safe.
    """
    version = _dashboard_frontend_version()
    return [
        {
            "name": "POM Tesla Dashboard Card",
            "url": f"/{DOMAIN}/pom-tesla-dashboard-card.js?v={version}",
            "type": "module",
        },
        {
            "name": "POM Tesla Dashboard Card /local fallback",
            "url": f"/local/{DOMAIN}/pom-tesla-dashboard-card.js?v={version}",
            "type": "module",
        },
        {
            "name": "POM Tesla Drive Dashboard Card",
            "url": f"/{DOMAIN}/pom-tesla-drive-dashboard-card.js?v={version}",
            "type": "module",
        },
        {
            "name": "POM Tesla Drive Dashboard Card /local fallback",
            "url": f"/local/{DOMAIN}/pom-tesla-drive-dashboard-card.js?v={version}",
            "type": "module",
        },
        {
            "name": "POM Tesla Trip Report Card",
            "url": f"/{DOMAIN}/pom-tesla-trip-report-card.js?v={version}",
            "type": "module",
        },
        {
            "name": "POM Tesla Trip Report Card /local fallback",
            "url": f"/local/{DOMAIN}/pom-tesla-trip-report-card.js?v={version}",
            "type": "module",
        },
        {
            "name": "POM Tesla Trip Report Card alpha346",
            "url": f"/{DOMAIN}/pom-tesla-trip-report-card-alpha346.js?v={version}",
            "type": "module",
        },
        {
            "name": "POM Tesla Trip Report Card alpha346 /local fallback",
            "url": f"/local/{DOMAIN}/pom-tesla-trip-report-card-alpha346.js?v={version}",
            "type": "module",
        },
        {
            "name": "POM Tesla Live Trip Card Alias",
            "url": f"/{DOMAIN}/pom-tesla-live-trip-card.js?v={version}",
            "type": "module",
        },
        {
            "name": "POM Tesla Live Trip Card Alias /local fallback",
            "url": f"/local/{DOMAIN}/pom-tesla-live-trip-card.js?v={version}",
            "type": "module",
        },
    ]


def _install_dashboard_resources_sync(storage_path: Path) -> dict[str, Any]:
    """Install/update bundled POM Lovelace resources in HA storage."""
    storage_path.parent.mkdir(parents=True, exist_ok=True)

    if storage_path.exists():
        try:
            payload = json.loads(storage_path.read_text(encoding="utf-8"))
        except Exception:
            backup_path = storage_path.with_name(
                f"{storage_path.name}.pom_tesla_report_broken_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
            )
            backup_path.write_bytes(storage_path.read_bytes())
            payload = {
                "version": 1,
                "minor_version": 1,
                "key": "lovelace_resources",
                "data": {"items": []},
            }
    else:
        payload = {
            "version": 1,
            "minor_version": 1,
            "key": "lovelace_resources",
            "data": {"items": []},
        }

    if not isinstance(payload, dict):
        payload = {"version": 1, "minor_version": 1, "key": "lovelace_resources", "data": {"items": []}}
    payload.setdefault("version", 1)
    payload.setdefault("minor_version", 1)
    payload.setdefault("key", "lovelace_resources")
    data = payload.setdefault("data", {})
    if not isinstance(data, dict):
        data = {}
        payload["data"] = data
    items = data.setdefault("items", [])
    if not isinstance(items, list):
        items = []
        data["items"] = items

    changed = False
    added: list[str] = []
    updated: list[str] = []
    existing_by_base: dict[str, dict[str, Any]] = {}
    for item in items:
        if isinstance(item, dict):
            base = _resource_base_url(str(item.get("url") or ""))
            if base:
                existing_by_base[base] = item

    for desired in _dashboard_resource_items():
        url = desired["url"]
        base = _resource_base_url(url)
        existing = existing_by_base.get(base)
        if existing is None:
            items.append(
                {
                    "id": uuid.uuid4().hex,
                    "type": desired["type"],
                    "url": url,
                }
            )
            added.append(desired["name"])
            changed = True
            continue

        if existing.get("url") != url or existing.get("type") != desired["type"]:
            existing["url"] = url
            existing["type"] = desired["type"]
            if not existing.get("id"):
                existing["id"] = uuid.uuid4().hex
            updated.append(desired["name"])
            changed = True

    if changed:
        if storage_path.exists():
            backup_path = storage_path.with_name(
                f"{storage_path.name}.pom_tesla_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
            )
            backup_path.write_bytes(storage_path.read_bytes())
        storage_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    return {
        "changed": changed,
        "added": added,
        "updated": updated,
        "storage_path": str(storage_path),
        "resources": _dashboard_resource_items(),
    }


async def async_install_dashboard_lovelace_resources(
    hass: HomeAssistant,
    *,
    notify: bool = False,
) -> dict[str, Any]:
    """Install/update bundled dashboard Lovelace resources."""
    storage_path = Path(hass.config.path(".storage", "lovelace_resources"))
    result = await hass.async_add_executor_job(_install_dashboard_resources_sync, storage_path)

    if notify:
        lines = [
            "POM Tesla dashboard resource kontrolü tamamlandı.",
            "",
            f"Storage: `{result['storage_path']}`",
            "",
        ]
        if result.get("added"):
            lines.append("Eklenenler:")
            lines.extend(f"- {name}" for name in result["added"])
            lines.append("")
        if result.get("updated"):
            lines.append("Güncellenenler:")
            lines.extend(f"- {name}" for name in result["updated"])
            lines.append("")
        if not result.get("changed"):
            lines.append("Değişiklik gerekmedi; POM resources zaten kayıtlı görünüyor.")
            lines.append("")
        lines.append("Kayıtlı POM resource URL'leri:")
        for item in result.get("resources", []):
            lines.append(f"- `{item['url']}` ({item['type']})")
        lines.append("")
        lines.append("Kart hâlâ görünmezse önce /local/pom_tesla_report/pom-tesla-trip-report-card.js adresinin açıldığını kontrol et, sonra tarayıcıyı hard refresh yap veya Home Assistant frontend cache'ini yenile.")
        await async_create_persistent_notification(
            hass,
            title="POM Tesla Dashboard Resources",
            message="\n".join(lines),
            notification_id="pom_tesla_dashboard_resources",
        )

    return result



DRIVE_DASHBOARD_ENTITY_KEY_BY_ROLE_INIT = {
    "dashboard_top_battery_level": "battery_level", "dashboard_charge_popup_battery_level": "battery_level",
    "dashboard_top_rated_range": "battery_range", "dashboard_charge_popup_battery_range": "battery_range",
    "dashboard_top_est_range": "battery_range_estimate", "dashboard_charge_popup_range_estimate": "battery_range_estimate",
    "dashboard_top_energy_remaining": "energy_remaining", "dashboard_top_speed": "speed", "dashboard_top_power": "power", "dashboard_drive_power": "power",
    "dashboard_top_elevation": "elevation", "dashboard_sidebar_inside_temp": "inside_temperature", "dashboard_top_outside_temp": "outside_temperature",
    "dashboard_top_odometer": "odometer", "dashboard_top_location": "location_tracker", "dashboard_drive_location_label": "location_label",
    "dashboard_drive_shift_state": "shift_state", "dashboard_drive_destination": "destination", "dashboard_drive_distance_to_arrival": "distance_to_arrival",
    "dashboard_drive_time_to_arrival": "time_to_arrival", "dashboard_drive_traffic_delay": "traffic_delay", "dashboard_drive_soc_at_arrival": "energy_at_arrival",
    "dashboard_drive_driver_temperature_setting": "driver_temperature_setting", "dashboard_drive_passenger_temperature_setting": "passenger_temperature_setting",
    "dashboard_drive_charging_state": "charging_state", "dashboard_charge_popup_charge_cable": "charge_cable", "dashboard_drive_dashcam": "dashcam",
    "dashboard_drive_lock": "lock", "dashboard_drive_battery_heater": "battery_heater", "dashboard_drive_tire_pressure_front_left": "tire_pressure_front_left",
    "dashboard_drive_tire_pressure_front_right": "tire_pressure_front_right", "dashboard_drive_tire_pressure_rear_left": "tire_pressure_rear_left",
    "dashboard_drive_tire_pressure_rear_right": "tire_pressure_rear_right", "dashboard_drive_phantom_drain": "phantom_drain",
    "dashboard_sidebar_battery_module_temp": "battery_module_temperature_max", "dashboard_drive_battery_pack_temperature": "battery_pack_temperature",
    "dashboard_drive_bluetooth_status": "bluetooth_status", "dashboard_drive_lifetime_energy_used": "lifetime_energy_used",
}


def _drive_dashboard_entities_yaml_init(options: dict | None) -> str:
    entries = (options or {}).get("panel_dashboard_entity_map") or (options or {}).get("dashboard_entity_map") or []
    entities = {}
    if isinstance(entries, list):
        for item in entries:
            if isinstance(item, dict):
                key = DRIVE_DASHBOARD_ENTITY_KEY_BY_ROLE_INIT.get(str(item.get("role") or "").strip())
                ent = str(item.get("entity_id") or "").strip()
                if key and ent and key not in entities:
                    entities[key] = ent
    if not entities:
        return ""
    order = ["battery_level", "battery_range", "battery_range_estimate", "energy_remaining", "speed", "power", "shift_state", "destination", "distance_to_arrival", "time_to_arrival", "traffic_delay", "energy_at_arrival", "inside_temperature", "outside_temperature", "driver_temperature_setting", "passenger_temperature_setting", "elevation", "odometer", "location_tracker", "location_label", "charging_state", "charge_cable", "dashcam", "lock", "battery_heater", "tire_pressure_front_left", "tire_pressure_front_right", "tire_pressure_rear_left", "tire_pressure_rear_right", "phantom_drain", "battery_module_temperature_max", "battery_pack_temperature", "bluetooth_status", "lifetime_energy_used"]
    lines = ["            entities:"]
    for key in order:
        if key in entities:
            lines.append(f"              {key}: {json.dumps(entities[key], ensure_ascii=False)}")
    return "\n".join(lines) + "\n"


def _write_drive_dashboard_file_sync(path: Path, vehicle_image_url: str = "", options: dict | None = None) -> None:
    """Write the standalone Drive Dashboard YAML file."""
    template_path = Path(__file__).resolve().parent / "dashboard" / "drive_dashboard_template.yaml"
    yaml_text = template_path.read_text(encoding="utf-8")
    vehicle_image_url = str(vehicle_image_url or "").strip()
    tire_pressure_image_url = str((options or {}).get("drive_dashboard_tire_pressure_image") or "").strip()
    app_language = str((options or {}).get(CONF_APP_LANGUAGE) or DEFAULT_APP_LANGUAGE).strip().lower()
    app_language = APP_LANGUAGE_EN if app_language.startswith("en") else APP_LANGUAGE_TR
    insert = f"            language: {json.dumps(app_language, ensure_ascii=False)}\n"
    if vehicle_image_url:
        insert += f"            vehicle_image: {json.dumps(vehicle_image_url, ensure_ascii=False)}\n"
    if tire_pressure_image_url:
        insert += f"            tire_pressure_image: {json.dumps(tire_pressure_image_url, ensure_ascii=False)}\n"
    insert += _drive_dashboard_entities_yaml_init(options)
    if insert:
        yaml_text = yaml_text.replace("            title: Drive Dashboard\n", "            title: Drive Dashboard\n" + insert, 1)
    path.write_text(yaml_text, encoding="utf-8")


async def async_write_drive_dashboard(hass: HomeAssistant, options: dict[str, Any] | None = None) -> Path:
    """Write the standalone Drive Dashboard YAML without blocking HA."""
    path = Path(hass.config.path("pom_tesla_drive_dashboard.yaml"))
    if options is None:
        entries = hass.config_entries.async_entries(DOMAIN)
        if entries:
            entry = entries[0]
            options = {**dict(entry.data or {}), **dict(entry.options or {})}
        else:
            options = {}
    vehicle_image_url = str((options or {}).get("drive_dashboard_vehicle_image") or "").strip()
    await hass.async_add_executor_job(_write_drive_dashboard_file_sync, path, vehicle_image_url, dict(options or {}))
    return path


def drive_dashboard_lovelace_yaml_block() -> str:
    """Return Lovelace YAML block for the standalone Drive dashboard."""
    return (
        "lovelace:\n"
        "  dashboards:\n"
        "    pom-drive-dashboard:\n"
        "      mode: yaml\n"
        "      title: Drive\n"
        "      icon: mdi:steering\n"
        "      show_in_sidebar: true\n"
        "      filename: pom_tesla_drive_dashboard.yaml\n"
    )


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up Tesla AI services."""

    hass.data.setdefault(DOMAIN, {})
    await async_register_dashboard_static_assets(hass)
    try:
        await async_install_dashboard_lovelace_resources(hass, notify=False)
    except Exception as err:
        _LOGGER.warning("Could not install POM Tesla dashboard Lovelace resources: %s", err)

    try:
        await async_write_drive_dashboard(hass)
    except Exception as err:
        _LOGGER.warning("Could not write POM Tesla Drive Dashboard YAML: %s", err)

    if not hass.services.has_service(DOMAIN, SERVICE_REBUILD_DASHBOARD):
        async def _handle_rebuild_dashboard(call: ServiceCall) -> None:
            entries = hass.config_entries.async_entries(DOMAIN)
            if not entries:
                await async_create_persistent_notification(
                    hass,
                    title="Tesla AI Dashboard",
                    message="Dashboard oluşturulamadı: Tesla AI config entry bulunamadı.",
                    notification_id="pom_tesla_report_dashboard_error",
                )
                return
            entry = entries[0]
            current_config = {**dict(entry.data or {}), **dict(entry.options or {})}
            dashboard_options = merged_dashboard_options_from_report_config(current_config)
            await async_install_dashboard_lovelace_resources(hass, notify=False)
            path = await async_write_tesla_dashboard(hass, dashboard_options)
            drive_path = await async_write_drive_dashboard(hass, current_config)
            await async_show_dashboard_install_notification(hass, dashboard_options)
            await async_show_dashboard_dependency_notification(hass)
            _LOGGER.info("POM Tesla dashboard YAML regenerated at %s", path)
            _LOGGER.info("POM Tesla Drive dashboard YAML regenerated at %s", drive_path)

        hass.services.async_register(DOMAIN, SERVICE_REBUILD_DASHBOARD, _handle_rebuild_dashboard)

    if not hass.services.has_service(DOMAIN, SERVICE_SHOW_DASHBOARD_DEPENDENCIES):
        async def _handle_show_dashboard_dependencies(call: ServiceCall) -> None:
            await async_show_dashboard_dependency_notification(hass)

        hass.services.async_register(
            DOMAIN,
            SERVICE_SHOW_DASHBOARD_DEPENDENCIES,
            _handle_show_dashboard_dependencies,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_INSTALL_DASHBOARD_RESOURCES):
        async def _handle_install_dashboard_resources(call: ServiceCall) -> None:
            await async_install_dashboard_lovelace_resources(hass, notify=True)

        hass.services.async_register(
            DOMAIN,
            SERVICE_INSTALL_DASHBOARD_RESOURCES,
            _handle_install_dashboard_resources,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_SET_DASHBOARD_ENERGY_FIELD):
        async def _handle_set_dashboard_energy_field(call: ServiceCall) -> None:
            field = str(call.data.get("field") or "energy_remaining").strip()
            slot = int(call.data.get("slot") or 1)
            if slot < 1 or slot > 3:
                slot = 1
            labels = {
                "energy_remaining": "Energy remaining",
                "battery_level": "Battery level",
                "battery_range": "Battery range",
                "inside_temp": "Inside temperature",
                "outside_temp": "Outside temperature",
                "odometer": "Odometer",
                "battery_heater": "Battery heater",
                "battery_temp": "Battery/module temperature",
                "empty": "Empty / hidden",
            }
            option = labels.get(field, "Energy remaining")

            select_entity_id = "select.pom_tesla_dashboard_energy_slot_choice" if slot == 1 else f"select.pom_tesla_dashboard_bottom_slot_{slot}_choice"
            target_slot_key = f"bottom_slot_{slot}"
            try:
                for state in hass.states.async_all("select"):
                    if state.attributes.get("dashboard_live_select") is True and state.attributes.get("slot_key") == target_slot_key:
                        select_entity_id = state.entity_id
                        break
            except Exception:
                pass

            select_store_key = f"dashboard_bottom_slot_{slot}_select_entity"
            select_entity_obj = hass.data.get(DOMAIN, {}).get(select_store_key)
            if select_entity_obj is None and slot == 1:
                select_entity_obj = hass.data.get(DOMAIN, {}).get("dashboard_energy_select_entity")
            if select_entity_obj is not None and hasattr(select_entity_obj, "async_select_option"):
                await select_entity_obj.async_select_option(option)
            else:
                await hass.services.async_call(
                    "select",
                    "select_option",
                    {"entity_id": select_entity_id, "option": option},
                    blocking=True,
                )

            popup_key = "energy_popup" if slot == 1 else f"energy_popup_{slot}"
            popup_entity_id = "switch.pom_tesla_dashboard_energy_popup" if slot == 1 else f"switch.pom_tesla_dashboard_energy_popup_{slot}"
            try:
                for state in hass.states.async_all("switch"):
                    if state.attributes.get("dashboard_helper") is True and state.attributes.get("helper_key") == popup_key:
                        popup_entity_id = state.entity_id
                        break
            except Exception:
                pass
            if hass.states.get(popup_entity_id) is not None:
                await hass.services.async_call(
                    "switch",
                    "turn_off",
                    {"entity_id": popup_entity_id},
                    blocking=False,
                )

        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_DASHBOARD_ENERGY_FIELD,
            _handle_set_dashboard_energy_field,
            schema=SET_DASHBOARD_ENERGY_FIELD_SCHEMA,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_SEND_DASHBOARD_PERSON_TRACK_TELEGRAM):
        async def _handle_send_dashboard_person_track_telegram(call: ServiceCall) -> None:
            slot = int(call.data.get("slot") or 1)
            if slot < 1 or slot > 3:
                slot = 1
            entries = hass.config_entries.async_entries(DOMAIN)
            data = get_entry_config(entries[0]) if entries else {}
            target = str(
                call.data.get("telegram_target")
                or call.data.get("chat_id")
                or data.get(CONF_AI_TELEGRAM_TARGET)
                or data.get(CONF_AI_TELEGRAM_LISTENER_CHAT_ID)
                or data.get(CONF_TELEGRAM_TARGET)
                or ""
            ).strip()
            if not target:
                raise ValueError("Telegram target is not configured.")

            sensor_entity = f"sensor.pom_tesla_dashboard_person_track_{slot}"
            state = hass.states.get(sensor_entity)
            if state is None:
                raise ValueError(f"Person Track sensor not found: {sensor_entity}")
            attrs = dict(state.attributes or {})
            name = str(attrs.get("person_name") or f"Person {slot}").strip()
            full_address = str(attrs.get("full_address") or attrs.get("display_name") or state.state or "-").strip()
            google_url = str(attrs.get("google_maps_url") or "").strip()
            distance_to_tesla = attrs.get("distance_to_tesla_km")
            distance_to_home = attrs.get("distance_to_home_km")
            try:
                _d_tesla = float(distance_to_tesla)
                _d_home = float(distance_to_home)
                if _d_tesla < 1.0 and _d_home > 500.0:
                    distance_to_home = _d_tesla
            except (TypeError, ValueError):
                pass

            def _fmt_distance(value: Any) -> str:
                try:
                    return f"{float(value):.1f} km"
                except (TypeError, ValueError):
                    return "-"

            message = (
                f"📍 {name} konumu\n\n"
                f"Adres: {full_address}\n"
                f"Tesla'ya uzaklık: {_fmt_distance(distance_to_tesla)}\n"
                f"Eve uzaklık: {_fmt_distance(distance_to_home)}"
            )
            if google_url:
                message += f"\n\nGoogle Maps: {google_url}"
            await async_telegram_send_message(hass, data, target=target, message=message)

        hass.services.async_register(
            DOMAIN,
            SERVICE_SEND_DASHBOARD_PERSON_TRACK_TELEGRAM,
            _handle_send_dashboard_person_track_telegram,
            schema=SEND_DASHBOARD_PERSON_TRACK_TELEGRAM_SCHEMA,
        )


    # Serve bundled frontend files, including the optional dashboard card.
    # Resource URL: /pom_tesla_report/pom-tesla-dashboard-card.js
    static_dir = Path(__file__).resolve().parent / "www"
    if static_dir.exists():
        try:
            from homeassistant.components.http import StaticPathConfig

            await hass.http.async_register_static_paths(
                [StaticPathConfig(f"/{DOMAIN}", str(static_dir), False)]
            )
            _LOGGER.debug("Tesla AI static frontend path registered: /%s", DOMAIN)
        except Exception as err:  # pragma: no cover - fallback for older HA cores
            try:
                hass.http.register_static_path(f"/{DOMAIN}", str(static_dir), False)
                _LOGGER.debug("Tesla AI legacy static frontend path registered: /%s", DOMAIN)
            except Exception as fallback_err:
                _LOGGER.warning(
                    "Could not register Tesla AI frontend path: %s / %s",
                    err,
                    fallback_err,
                )

        # Also copy frontend cards to /config/www so users can add them as normal
        # Lovelace resources with /local/pom_tesla_report/<card-file>.js.
        # File scanning/copying is done in the executor to avoid blocking HA's event loop.
        def _copy_frontend_cards_to_www() -> None:
            target_dir = Path(hass.config.path("www", "pom_tesla_report"))
            target_dir.mkdir(parents=True, exist_ok=True)
            for src in static_dir.glob("*.js"):
                target = target_dir / src.name
                target.write_bytes(src.read_bytes())

        try:
            await hass.async_add_executor_job(_copy_frontend_cards_to_www)
            _LOGGER.debug("POM Tesla frontend cards copied to /config/www/pom_tesla_report")
        except Exception as err:
            _LOGGER.warning("Could not copy POM Tesla frontend cards to /config/www: %s", err)

        # Re-run the installer after the /local fallback files are physically in
        # /config/www. This makes the resource repair operation deterministic even
        # on fresh installations.
        try:
            await async_install_dashboard_lovelace_resources(hass, notify=False)
        except Exception as err:
            _LOGGER.warning("Could not refresh POM Tesla Lovelace resources after copying frontend cards: %s", err)

    try:
        from .panel import async_setup_panel

        await async_setup_panel(hass, version=_dashboard_frontend_version())
    except Exception as err:
        _LOGGER.warning("Could not set up Tesla AI app panel: %s", err)

    async def async_start_state_core(
        state_key: str,
        integration_data: dict[str, Any],
        *,
        force: bool,
        send_notification: bool,
        source: str,
        title: str,
        notification_id: str,
    ) -> bool:
        """Start a trip-like state bucket."""
        trip_state = get_named_state(hass, state_key)

        if trip_state.get("active") and not force:
            message = (
                "Zaten aktif bir Tesla AI sürüş kaydı var.\n\n"
                "Yeni kayıt başlatmak için önce mevcut kaydı bitirmelisin."
            )

            await async_create_persistent_notification(
                hass,
                title=title,
                message=message,
                notification_id=f"{notification_id}_active",
            )
            return False

        start_state = build_start_state(hass, integration_data, source)
        if is_trip_map_collection_enabled(integration_data):
            tracker_entity = get_vehicle_role_entity(integration_data, VEHICLE_ROLE_LOCATION_TRACKER, usage_key="use_map") or integration_data.get(CONF_TRIP_MAP_TRACKER_ENTITY, DEFAULT_TRIP_MAP_TRACKER_ENTITY)
            start_state["map_tracker_entity"] = tracker_entity
            start_point = get_tracker_lat_lon(hass, tracker_entity)
            if start_point is not None:
                start_state["start_tracker_lat"], start_state["start_tracker_lon"] = start_point
            add_trip_map_point(
                start_state,
                start_point,
                min_movement_meters=safe_float(
                    integration_data.get(CONF_TRIP_MAP_MIN_MOVEMENT_METERS),
                    DEFAULT_TRIP_MAP_MIN_MOVEMENT_METERS,
                ),
                force=True,
                speed=start_state.get("start_speed"),
                elevation=start_state.get("start_elevation"),
                ts=start_state.get("started_at"),
            )
        hass.data[DOMAIN][state_key] = start_state

        if send_notification:
            message = (
                "Tesla AI sürüş takibi başlatıldı.\n\n"
                f"- Kaynak: `{source}`\n"
                f"- Başlangıç zamanı: `{start_state['started_at']}`\n"
                f"- Odometer: `{start_state['start_odometer']}`\n"
                f"- Kalan enerji: `{start_state['start_energy_kwh']}` kWh\n"
                f"- Batarya: `%{start_state['start_battery']}`\n"
                f"- Rakım: `{start_state['start_elevation']}` m\n"
                f"- Shift state: `{start_state['start_shift_state']}`\n"
                f"- Hız: `{start_state['start_speed']}` km/sa\n"
                f"- Klima state: `{start_state['start_climate_state']}`"
            )

            await async_create_persistent_notification(
                hass,
                title=title,
                message=message,
                notification_id=notification_id,
            )

        return True

    async def async_finish_state_core(
        state_key: str,
        integration_data: dict[str, Any],
        *,
        send_telegram: bool,
        caption: str,
        output_path: str,
        test_mode: bool,
        overrides: dict[str, Any],
        source: str,
        title: str,
        notification_id: str,
    ) -> bool:
        """Finish a trip-like state bucket and generate the same report type."""
        trip_state = get_named_state(hass, state_key)

        if not trip_state.get("active"):
            message = "Aktif Tesla AI sürüş kaydı yok."

            await async_create_persistent_notification(
                hass,
                title=title,
                message=message,
                notification_id=f"{notification_id}_no_active",
            )
            return False

        update_runtime_tracking_fields(hass, integration_data, state_key)
        trip_state = get_named_state(hass, state_key)
        trip_state["trip_finish_pipeline_started"] = True
        trip_state["trip_finish_pipeline_source"] = source
        trip_state["trip_finish_pipeline_started_at"] = datetime.now().isoformat(timespec="seconds")
        hass.data[DOMAIN][state_key] = trip_state

        end_odometer = get_float_state(hass, get_report_configured_entity(integration_data, CONF_ODOMETER_ENTITY, VEHICLE_ROLE_ODOMETER), 0.0)
        end_energy = get_float_state(hass, get_report_configured_entity(integration_data, CONF_ENERGY_REMAINING_ENTITY, VEHICLE_ROLE_ENERGY_REMAINING), 0.0)
        end_battery = get_float_state(hass, get_report_configured_entity(integration_data, CONF_BATTERY_LEVEL_ENTITY, VEHICLE_ROLE_BATTERY_LEVEL), 0.0)
        end_elevation = get_float_state(hass, get_report_configured_entity(integration_data, CONF_ELEVATION_ENTITY, VEHICLE_ROLE_ELEVATION), 0.0)
        climate_state = get_state_text(hass, get_report_configured_entity(integration_data, CONF_CLIMATE_ENTITY, VEHICLE_ROLE_CLIMATE), "")

        finish_data = {
            "end_odometer": end_odometer,
            "end_energy_kwh": end_energy,
            "end_battery": end_battery,
            "end_elevation": end_elevation,
            "climate_active_at_finish": is_climate_active(climate_state),
            "test_mode": test_mode,
        }

        finish_data.update(overrides)

        end_point: tuple[float, float] | None = None
        start_point: tuple[float, float] | None = None
        start_lat = trip_state.get("start_tracker_lat")
        start_lon = trip_state.get("start_tracker_lon")
        try:
            if start_lat is not None and start_lon is not None:
                start_point = (float(start_lat), float(start_lon))
        except (TypeError, ValueError):
            start_point = None

        if is_trip_map_collection_enabled(integration_data):
            tracker_entity = get_vehicle_role_entity(integration_data, VEHICLE_ROLE_LOCATION_TRACKER, usage_key="use_map") or integration_data.get(CONF_TRIP_MAP_TRACKER_ENTITY, DEFAULT_TRIP_MAP_TRACKER_ENTITY)
            end_point = get_tracker_lat_lon(hass, tracker_entity)
            add_trip_map_point(
                trip_state,
                end_point,
                min_movement_meters=safe_float(
                    integration_data.get(CONF_TRIP_MAP_MIN_MOVEMENT_METERS),
                    DEFAULT_TRIP_MAP_MIN_MOVEMENT_METERS,
                ),
                force=True,
                speed=get_float_state(hass, get_report_configured_entity(integration_data, CONF_SPEED_ENTITY, VEHICLE_ROLE_SPEED), 0.0),
                elevation=end_elevation,
                ts=datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
            )

        map_points = trip_state.get("map_points") if isinstance(trip_state.get("map_points"), list) else []
        if start_point is None and map_points:
            first_point = map_points[0] if isinstance(map_points[0], dict) else {}
            try:
                start_point = (float(first_point.get("lat")), float(first_point.get("lon")))
            except Exception:
                start_point = None
        if end_point is None and map_points:
            last_point = map_points[-1] if isinstance(map_points[-1], dict) else {}
            try:
                end_point = (float(last_point.get("lat")), float(last_point.get("lon")))
            except Exception:
                end_point = None

        start_address = str(trip_state.get("start_address") or "").strip()
        if start_point is not None:
            try:
                looked_up_start = await async_reverse_geocode_point_address(hass, start_point[0], start_point[1])
                if looked_up_start:
                    start_address = looked_up_start
            except Exception as err:
                _LOGGER.exception("Tesla AI start reverse geocode failed safely: %s", err)

        end_address = ""
        if end_point is not None:
            try:
                end_address = await async_reverse_geocode_point_address(hass, end_point[0], end_point[1])
            except Exception as err:
                _LOGGER.exception("Tesla AI end reverse geocode failed safely: %s", err)
        if not end_address:
            try:
                await async_update_reverse_geocode_cache(hass, integration_data)
                end_address = get_cached_reverse_geocode_address(hass)
            except Exception as err:
                _LOGGER.exception("Tesla AI cached reverse geocode fallback failed safely: %s", err)

        finish_data["start_address"] = start_address
        finish_data["end_address"] = end_address
        trip_state["start_address"] = start_address
        trip_state["end_address"] = end_address

        report_lang = get_report_language(integration_data)
        report_data = build_manual_trip_report_data(trip_state, integration_data, finish_data)
        if isinstance(trip_state.get("map_points"), list):
            report_data["map_points"] = trip_state.get("map_points")
            report_data["map_point_count"] = len(trip_state.get("map_points") or [])
        if start_point is not None:
            report_data["start_latitude"] = start_point[0]
            report_data["start_longitude"] = start_point[1]
        if end_point is not None:
            report_data["end_latitude"] = end_point[0]
            report_data["end_longitude"] = end_point[1]

        def _append_pipeline_error(stage: str, err: Exception) -> None:
            try:
                errors = report_data.setdefault("report_pipeline_errors", [])
                if isinstance(errors, list):
                    errors.append({
                        "stage": str(stage or "unknown"),
                        "error": str(err),
                        "at": datetime.now().isoformat(timespec="seconds"),
                    })
            except Exception:
                pass

        try:
            enrich_trip_report_score(report_data, lang=report_lang)
        except Exception as err:
            _LOGGER.exception("Tesla AI trip enrichment failed safely before ledger: %s", err)
            _append_pipeline_error("enrich_before_ledger", err)

        # Core rule: save the trip ledger before optional visuals/AI/Telegram work.
        # If map rendering, PNG rendering, weather/grade enrichment, or AI fails later,
        # the user's actual drive must still appear in Trip Records.
        trip_record: dict[str, Any] | None = None
        try:
            trip_record = await async_record_trip_summary_entry(
                hass,
                report_data,
                source=source,
            )
            if isinstance(trip_record, dict):
                report_data["trip_record_id"] = str(trip_record.get("id") or "")
                report_data["trip_record_stage"] = "base_saved_before_outputs"
        except Exception as err:
            _LOGGER.exception("Tesla AI trip ledger base save failed: %s", err)
            _append_pipeline_error("ledger_base_save", err)

        map_png_path = ""
        if is_trip_map_collection_enabled(integration_data):
            try:
                map_output_path = get_trip_map_output_path_from_report(output_path)
                map_data = build_trip_map_render_data(
                    trip_state,
                    report_data,
                    title=f"Tesla AI - {get_report_type_label(state_key)}",
                )
                map_png_path = await hass.async_add_executor_job(
                    render_trip_map_png,
                    map_data,
                    map_output_path,
                )
                if map_png_path:
                    report_data["map_path"] = map_png_path
                if map_png_path and get_bool_option(
                    integration_data,
                    CONF_SHOW_TRIP_MAP,
                    DEFAULT_SHOW_TRIP_MAP,
                ):
                    report_data["embedded_map_path"] = map_png_path
            except Exception as err:
                _LOGGER.exception("Tesla AI trip map render failed safely: %s", err)
                _append_pipeline_error("map_render", err)
                map_png_path = ""

        try:
            enrich_trip_report_score(report_data, lang=report_lang)
        except Exception as err:
            _LOGGER.exception("Tesla AI trip enrichment failed safely after map: %s", err)
            _append_pipeline_error("enrich_after_map", err)

        png_path = ""
        try:
            png_path = await hass.async_add_executor_job(
                render_trip_report_png,
                report_data,
                output_path,
                report_lang,
            )
        except Exception as err:
            _LOGGER.exception("Tesla AI trip PNG render failed safely; ledger was already saved: %s", err)
            _append_pipeline_error("png_render", err)

        trip_state["active"] = False
        trip_state["finished_at"] = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        trip_state["last_report_path"] = png_path
        trip_state["last_report_data"] = report_data
        if map_png_path:
            trip_state["last_map_path"] = map_png_path
        trip_state["finish_source"] = source
        trip_state["finish_pipeline_status"] = {
            "ledger_saved": isinstance(trip_record, dict),
            "png_rendered": bool(png_path),
            "map_rendered": bool(map_png_path),
            "errors": report_data.get("report_pipeline_errors", []),
            "finished_at": datetime.now().isoformat(timespec="seconds"),
        }
        hass.data[DOMAIN][state_key] = trip_state

        # Re-save after optional map/score fields so the ledger can contain the final
        # richer record. This uses the same deterministic id, so it replaces the base
        # entry instead of creating a duplicate. If it fails, the base entry remains.
        try:
            final_trip_record = await async_record_trip_summary_entry(
                hass,
                report_data,
                source=source,
            )
            if isinstance(final_trip_record, dict):
                trip_record = final_trip_record
                report_data["trip_record_id"] = str(final_trip_record.get("id") or "")
                report_data["trip_record_stage"] = "final_saved_after_outputs"
        except Exception as err:
            _LOGGER.exception("Tesla AI trip ledger final save failed; base entry remains: %s", err)
            _append_pipeline_error("ledger_final_save", err)

        message = (
            "Tesla AI sürüş raporu işlendi.\n\n"
            f"- Kaynak: `{source}`\n"
            f"- PNG: `{png_path or 'oluşturulamadı'}`\n"
            f"- Harita: `{map_png_path or 'oluşturulamadı / kapalı'}`\n"
            f"- Kayıt: `{'yazıldı' if isinstance(trip_record, dict) else 'yazılamadı'}`\n\n"
            f"Mesafe: `{report_data.get('trip_km')}` km\n"
            f"Enerji: `{report_data.get('used_kwh')}` kWh\n"
            f"Tüketim: `{report_data.get('consumption_kwh_100km')}` kWh/100 km"
        )

        await async_create_persistent_notification(
            hass,
            title=title,
            message=message,
            notification_id=notification_id,
        )

        telegram_target = (
            integration_data.get(CONF_AI_TELEGRAM_TARGET)
            or integration_data.get(CONF_AI_TELEGRAM_LISTENER_CHAT_ID)
            or integration_data.get(CONF_TELEGRAM_TARGET)
        )

        normal_report_sent = False
        telegram_status = "skipped"
        telegram_error = ""
        telegram_fallback_text_status = "skipped"
        if not send_telegram:
            telegram_status = "disabled"
        elif not telegram_target:
            telegram_status = "no_target"
        elif not png_path:
            telegram_status = "no_png"
        elif send_telegram and telegram_target and png_path:
            try:
                # POM built-in Telegram path is preferred inside this helper. HA telegram_bot
                # is only an optional fallback; the user does not need the HA Telegram integration.
                await async_telegram_send_photo(
                    hass,
                    integration_data,
                    target=str(telegram_target),
                    file_path=png_path,
                    caption=caption,
                )
                normal_report_sent = True
                telegram_status = "sent"
            except Exception as err:
                telegram_status = "failed"
                telegram_error = str(err)
                _LOGGER.exception("Tesla AI trip Telegram photo send failed safely: %s", err)
                _append_pipeline_error("telegram_report_photo", err)

        # If PNG upload failed or PNG could not be rendered, still notify via text when possible.
        # This prevents a completely silent trip finish and keeps the AI story path independent
        # from visual-report delivery.
        if send_telegram and telegram_target and (telegram_status in {"failed", "no_png"}):
            try:
                fallback_lines = [
                    "🚗 Tesla AI",
                    "Sürüş kaydı Trip Records içine yazıldı; ancak görsel Trip Report Telegram'a gönderilemedi.",
                    f"Mesafe: {report_data.get('trip_km', 0)} km",
                    f"Enerji: {report_data.get('used_kwh', 0)} kWh",
                    f"Tüketim: {report_data.get('consumption_kwh_100km', 0)} kWh/100 km",
                ]
                if telegram_error:
                    fallback_lines.append(f"Hata: {telegram_error}")
                await async_send_telegram_text_chunks(
                    hass,
                    integration_data,
                    str(telegram_target),
                    "\n".join(str(line) for line in fallback_lines),
                    limit=3000,
                )
                telegram_fallback_text_status = "sent"
            except Exception as err:
                telegram_fallback_text_status = "failed"
                _LOGGER.exception("Tesla AI fallback Telegram trip text failed safely: %s", err)
                _append_pipeline_error("telegram_report_fallback_text", err)

        report_data["telegram_report_status"] = telegram_status
        report_data["telegram_report_fallback_text_status"] = telegram_fallback_text_status
        if telegram_error:
            report_data["telegram_report_error"] = telegram_error
        try:
            trip_state["finish_pipeline_status"]["telegram_report_status"] = telegram_status
            trip_state["finish_pipeline_status"]["telegram_report_fallback_text_status"] = telegram_fallback_text_status
            if telegram_error:
                trip_state["finish_pipeline_status"]["telegram_report_error"] = telegram_error
            hass.data[DOMAIN][state_key] = trip_state
        except Exception:
            pass

        map_telegram_status = "skipped"
        if map_png_path and is_trip_map_collection_enabled(integration_data) and get_bool_option(
            integration_data,
            CONF_TRIP_MAP_SEND_SEPARATE_PNG,
            DEFAULT_TRIP_MAP_SEND_SEPARATE_PNG,
        ):
            if send_telegram and telegram_target:
                try:
                    await async_telegram_send_photo(
                        hass,
                        integration_data,
                        target=str(telegram_target),
                        file_path=map_png_path,
                        caption=get_report_type_short_caption(state_key),
                    )
                    map_telegram_status = "sent"
                except Exception as err:
                    map_telegram_status = "failed"
                    _LOGGER.exception("Tesla AI trip Telegram map send failed safely: %s", err)
                    _append_pipeline_error("telegram_map_photo", err)
            else:
                map_telegram_status = "disabled_or_no_target"
        report_data["telegram_map_status"] = map_telegram_status
        try:
            trip_state["finish_pipeline_status"]["telegram_map_status"] = map_telegram_status
            hass.data[DOMAIN][state_key] = trip_state
        except Exception:
            pass

        # Save the final Telegram send status back into the ledger record after the
        # visual Telegram step. The earlier base/final saves intentionally happen
        # before optional output stages; this extra save preserves diagnostics
        # without blocking the report pipeline.
        if isinstance(trip_record, dict):
            try:
                final_status_record = await async_record_trip_summary_entry(
                    hass,
                    report_data,
                    source=source,
                )
                if isinstance(final_status_record, dict):
                    trip_record = final_status_record
                    report_data["trip_record_id"] = str(final_status_record.get("id") or report_data.get("trip_record_id") or "")
                    report_data["trip_record_stage"] = "final_saved_after_telegram_status"
            except Exception as err:
                _LOGGER.exception("Tesla AI trip ledger telegram-status save failed; previous entry remains: %s", err)
                _append_pipeline_error("ledger_telegram_status_save", err)

        if isinstance(trip_record, dict):
            # The AI story must not depend on the visual PNG send succeeding. If the
            # trip was saved and Telegram target exists, send the AI text through the
            # POM built-in Telegram helper even when the normal PNG path failed.
            ai_telegram_target = str(telegram_target) if send_telegram and telegram_target else ""
            try:
                report_data["ai_story_schedule_target_status"] = "target_available" if ai_telegram_target else "saved_only_no_target"
                await async_schedule_post_trip_ai_story(
                    hass,
                    integration_data,
                    report_data,
                    telegram_target=ai_telegram_target,
                    source=source,
                    record_id=str(trip_record.get("id") or ""),
                    post_report_delay_seconds=0.5,
                )
                report_data["ai_story_schedule_status"] = "scheduled" if get_bool_option(integration_data, CONF_AI_ALERT_POST_TRIP_SUMMARY_ENABLED, DEFAULT_AI_ALERT_POST_TRIP_SUMMARY_ENABLED) else "disabled"
            except Exception as err:
                report_data["ai_story_schedule_status"] = "failed"
                report_data["ai_story_schedule_error"] = str(err)
                _LOGGER.exception("Tesla AI post-trip AI scheduling failed safely: %s", err)
                _append_pipeline_error("ai_schedule", err)

        return True

    async def async_start_trip_core(
        integration_data: dict[str, Any],
        *,
        force: bool,
        send_notification: bool,
        source: str,
    ) -> bool:
        """Start the normal auto/service trip state."""
        return await async_start_state_core(
            TRIP_STATE_KEY,
            integration_data,
            force=force,
            send_notification=send_notification,
            source=source,
            title="Tesla AI - Start Trip",
            notification_id="pom_tesla_report_start_trip",
        )

    async def async_finish_trip_core(
        integration_data: dict[str, Any],
        *,
        send_telegram: bool,
        caption: str,
        output_path: str,
        test_mode: bool,
        overrides: dict[str, Any],
        source: str,
    ) -> bool:
        """Finish the normal auto/service trip state."""
        return await async_finish_state_core(
            TRIP_STATE_KEY,
            integration_data,
            send_telegram=send_telegram,
            caption=caption,
            output_path=output_path,
            test_mode=test_mode,
            overrides=overrides,
            source=source,
            title="Tesla AI - Finish Trip",
            notification_id="pom_tesla_report_finish_trip",
        )

    async def async_start_manual_tracking(entry_id: str) -> bool:
        """Start switch-based manual tracking for a config entry."""
        integration_data = hass.data.get(DOMAIN, {}).get(entry_id)

        if not integration_data:
            return False

        return await async_start_state_core(
            MANUAL_TRACKING_STATE_KEY,
            integration_data,
            force=False,
            send_notification=True,
            source="manual_tracking_switch",
            title="Tesla AI - Manual Tracking",
            notification_id="pom_tesla_report_manual_tracking_start",
        )

    async def async_finish_manual_tracking(entry_id: str) -> bool:
        """Finish switch-based manual tracking for a config entry."""
        integration_data = hass.data.get(DOMAIN, {}).get(entry_id)

        if not integration_data:
            return False

        return await async_finish_state_core(
            MANUAL_TRACKING_STATE_KEY,
            integration_data,
            send_telegram=True,
            caption="🚗 Tesla AI - Manuel Takip Raporu",
            output_path=DEFAULT_MANUAL_TRACKING_IMAGE_OUTPUT_PATH,
            test_mode=False,
            overrides={},
            source="manual_tracking_switch",
            title="Tesla AI - Manual Tracking",
            notification_id="pom_tesla_report_manual_tracking_finish",
        )

    async def async_process_auto_trip_signal(entry_id: str, source_entity: str) -> None:
        """Process automatic start/finish signals from shift and speed changes."""
        domain_data = hass.data.get(DOMAIN, {})
        integration_data = domain_data.get(entry_id)

        if not integration_data:
            return

        auto_tracking_enabled = get_bool_option(
            integration_data,
            CONF_AUTO_TRIP_TRACKING,
            DEFAULT_AUTO_TRIP_TRACKING,
        )
        auto_start_speed_threshold = safe_float(
            integration_data.get(CONF_AUTO_START_SPEED_THRESHOLD),
            DEFAULT_AUTO_START_SPEED_THRESHOLD,
        )

        if not auto_tracking_enabled:
            _LOGGER.debug(
                "Auto trip signal ignored because automatic trip tracking is disabled. "
                "entity=%s threshold=%s",
                source_entity,
                auto_start_speed_threshold,
            )
            return

        trip_state = get_trip_state(hass)

        shift_state = get_state_text(hass, get_report_configured_entity(integration_data, CONF_SHIFT_STATE_ENTITY, VEHICLE_ROLE_SHIFT_STATE), "")
        speed = get_float_state(hass, get_report_configured_entity(integration_data, CONF_SPEED_ENTITY, VEHICLE_ROLE_SPEED), 0.0)

        _LOGGER.debug(
            "Auto trip signal: entity=%s shift=%s speed=%s active=%s threshold=%s",
            source_entity,
            shift_state,
            speed,
            trip_state.get("active"),
            auto_start_speed_threshold,
        )

        update_all_active_tracking_states(hass, integration_data)
        trip_state = get_trip_state(hass)

        if not trip_state.get("active"):
            if should_auto_start_trip(shift_state, speed, auto_start_speed_threshold):
                _LOGGER.info(
                    "Auto trip start triggered. shift=%s speed=%s threshold=%s entity=%s",
                    shift_state,
                    speed,
                    auto_start_speed_threshold,
                    source_entity,
                )
                await async_start_trip_core(
                    integration_data,
                    force=False,
                    send_notification=True,
                    source="auto",
                )
            return

        finish_tasks = hass.data.setdefault(DOMAIN, {}).setdefault(AUTO_TRIP_FINISH_TASK_STORE, {})

        # If the car moved again while a delayed Park finish was pending, cancel it.
        pending_task = finish_tasks.get(entry_id)
        if pending_task is not None and not pending_task.done() and not should_auto_finish_trip(shift_state):
            pending_task.cancel()
            finish_tasks.pop(entry_id, None)
            trip_state.pop("auto_finish_pending_since_ts", None)
            trip_state.pop("auto_finish_pending_delay_seconds", None)
            hass.data[DOMAIN][TRIP_STATE_KEY] = trip_state

        if should_auto_finish_trip(shift_state):
            finish_delay_seconds = max(
                0.0,
                safe_float(
                    integration_data.get(CONF_LIVE_TRIP_FINISH_DELAY_SECONDS),
                    DEFAULT_LIVE_TRIP_FINISH_DELAY_SECONDS,
                ),
            )

            if finish_delay_seconds <= 0:
                _LOGGER.info(
                    "Auto trip finish triggered immediately. shift=%s speed=%s entity=%s",
                    shift_state,
                    speed,
                    source_entity,
                )
                end_odometer = get_float_state(
                    hass,
                    get_report_configured_entity(integration_data, CONF_ODOMETER_ENTITY, VEHICLE_ROLE_ODOMETER),
                    safe_float(trip_state.get("start_odometer"), 0.0),
                )
                decision = live_trip_candidate_finish_decision(integration_data, trip_state, end_odometer=end_odometer)
                hass.data[DOMAIN][TRIP_STATE_KEY] = trip_state
                if decision.get("ignored"):
                    _LOGGER.info("Auto trip ignored as a short parking manoeuvre. decision=%s", decision)
                    clear_trip_state(hass)
                    return
                trip_state["trip_finish_pipeline_started"] = True
                trip_state["trip_finish_pipeline_source"] = "auto"
                trip_state["trip_finish_pipeline_started_at"] = datetime.now().isoformat(timespec="seconds")
                hass.data[DOMAIN][TRIP_STATE_KEY] = trip_state
                await async_finish_trip_core(
                    integration_data,
                    send_telegram=True,
                    caption="🚗 Tesla AI - Otomatik Sürüş Raporu",
                    output_path=DEFAULT_AUTO_TRIP_IMAGE_OUTPUT_PATH,
                    test_mode=False,
                    overrides={},
                    source="auto",
                )
                return

            existing_task = finish_tasks.get(entry_id)
            if existing_task is not None and not existing_task.done():
                _LOGGER.debug("Auto trip finish delay already pending. entry=%s delay=%ss", entry_id, finish_delay_seconds)
                return

            trip_state["auto_finish_pending_since_ts"] = datetime.now().timestamp()
            trip_state["auto_finish_pending_delay_seconds"] = finish_delay_seconds
            hass.data[DOMAIN][TRIP_STATE_KEY] = trip_state

            async def _delayed_auto_finish() -> None:
                try:
                    await asyncio.sleep(finish_delay_seconds)
                    current_data = hass.data.get(DOMAIN, {}).get(entry_id, integration_data)
                    current_state = get_trip_state(hass)
                    if not current_state.get("active"):
                        return
                    current_shift = get_state_text(
                        hass,
                        get_report_configured_entity(current_data, CONF_SHIFT_STATE_ENTITY, VEHICLE_ROLE_SHIFT_STATE),
                        "",
                    )
                    current_speed = get_float_state(
                        hass,
                        get_report_configured_entity(current_data, CONF_SPEED_ENTITY, VEHICLE_ROLE_SPEED),
                        0.0,
                    )
                    if not should_auto_finish_trip(current_shift):
                        _LOGGER.info(
                            "Delayed auto trip finish cancelled because vehicle moved again. shift=%s speed=%s",
                            current_shift,
                            current_speed,
                        )
                        return
                    _LOGGER.info(
                        "Delayed auto trip finish triggered after %.0fs. shift=%s speed=%s",
                        finish_delay_seconds,
                        current_shift,
                        current_speed,
                    )
                    end_odometer = get_float_state(
                        hass,
                        get_report_configured_entity(current_data, CONF_ODOMETER_ENTITY, VEHICLE_ROLE_ODOMETER),
                        safe_float(current_state.get("start_odometer"), 0.0),
                    )
                    decision = live_trip_candidate_finish_decision(current_data, current_state, end_odometer=end_odometer)
                    hass.data[DOMAIN][TRIP_STATE_KEY] = current_state
                    if decision.get("ignored"):
                        _LOGGER.info("Delayed auto trip ignored as a short parking manoeuvre. decision=%s", decision)
                        clear_trip_state(hass)
                        return
                    current_state["trip_finish_pipeline_started"] = True
                    current_state["trip_finish_pipeline_source"] = "auto_delayed"
                    current_state["trip_finish_pipeline_started_at"] = datetime.now().isoformat(timespec="seconds")
                    hass.data[DOMAIN][TRIP_STATE_KEY] = current_state
                    await async_finish_trip_core(
                        current_data,
                        send_telegram=True,
                        caption="🚗 Tesla AI - Otomatik Sürüş Raporu",
                        output_path=DEFAULT_AUTO_TRIP_IMAGE_OUTPUT_PATH,
                        test_mode=False,
                        overrides={},
                        source="auto_delayed",
                    )
                finally:
                    finish_tasks.pop(entry_id, None)

            finish_tasks[entry_id] = hass.async_create_task(_delayed_auto_finish())
            _LOGGER.info(
                "Auto trip finish scheduled after %.0fs. shift=%s speed=%s entity=%s",
                finish_delay_seconds,
                shift_state,
                speed,
                source_entity,
            )

    hass.data[DOMAIN]["async_process_auto_trip_signal"] = async_process_auto_trip_signal
    hass.data[DOMAIN][DATA_ASYNC_START_MANUAL_TRACKING] = async_start_manual_tracking
    hass.data[DOMAIN][DATA_ASYNC_FINISH_MANUAL_TRACKING] = async_finish_manual_tracking

    async def handle_debug_config(call: ServiceCall) -> None:
        """Show selected Tesla AI config data."""
        entries = hass.config_entries.async_entries(DOMAIN)

        if not entries:
            message = (
                "Tesla AI için kayıtlı config entry bulunamadı.\n\n"
                "Önce Ayarlar > Cihazlar ve Servisler üzerinden "
                "Tesla AI entegrasyonunu eklemelisin."
            )

            await async_create_persistent_notification(
                hass,
                title="Tesla AI",
                message=message,
                notification_id="pom_tesla_report_debug_config",
            )

            _LOGGER.warning(message)
            return

        lines = [
            "Tesla AI kayıtlı ayarları:",
            "",
            f"Toplam kayıt sayısı: {len(entries)}",
            "",
        ]

        telegram_target: str | None = None

        for index, entry in enumerate(entries, start=1):
            data = get_entry_config(entry)

            if telegram_target is None:
                telegram_target = str(
            call.data.get("chat_id") or call.data.get("telegram_target")
            or data.get(CONF_AI_TELEGRAM_TARGET)
            or data.get(CONF_AI_TELEGRAM_LISTENER_CHAT_ID)
            or data.get(CONF_TELEGRAM_TARGET)
            or ""
        ).strip()

            lines.append(f"## Kayıt {index}")
            lines.append(f"- title: `{entry.title}`")
            lines.append(f"- entry_id: `{entry.entry_id}`")
            lines.append("")

            lines.append("### Aktif ayarlar")
            for key, value in data.items():
                lines.append(f"- `{key}`: `{redact_sensitive_config_value(key, value)}`")

            lines.append("")

        message = "\n".join(lines)

        _LOGGER.warning("Tesla AI debug config çalıştı:\n%s", message)

        await async_create_persistent_notification(
            hass,
            title="Tesla AI Debug Config",
            message=message,
            notification_id="pom_tesla_report_debug_config",
        )

        if telegram_target:
            await hass.services.async_call(
                "telegram_bot",
                "send_message",
                {
                    "target": telegram_target,
                    "parse_mode": "plain_text",
                    "message": message,
                },
                blocking=True,
            )



    async def handle_debug_ai_context(call: ServiceCall) -> None:
        """Show exactly which entities POM AI can see."""
        data = get_first_entry_config(hass)

        if data is None:
            await async_create_persistent_notification(
                hass,
                title="POM AI Context Debug",
                message="Tesla AI için kayıtlı config entry bulunamadı.",
                notification_id="pom_tesla_report_ai_context_debug",
            )
            return

        max_entities = call.data.get("max_entities")
        include_unavailable = call.data.get("include_unavailable")
        message = build_ai_context_entity_debug(
            hass,
            data,
            max_entities_override=max_entities,
            include_unavailable_override=include_unavailable,
        )

        await async_create_persistent_notification(
            hass,
            title="POM AI Context Debug",
            message=message,
            notification_id="pom_tesla_report_ai_context_debug",
        )

        send_telegram = bool(call.data.get("send_telegram", True))
        telegram_target = str(
            call.data.get("chat_id") or call.data.get("telegram_target")
            or data.get(CONF_AI_TELEGRAM_TARGET)
            or data.get(CONF_AI_TELEGRAM_LISTENER_CHAT_ID)
            or data.get(CONF_TELEGRAM_TARGET)
            or ""
        ).strip()

        if send_telegram and telegram_target:
            for chunk in split_telegram_message(message):
                await hass.services.async_call(
                    "telegram_bot",
                    "send_message",
                    {
                        "target": telegram_target,
                        "parse_mode": "plain_text",
                        "message": chunk,
                    },
                    blocking=True,
                )


    async def handle_debug_alerts(call: ServiceCall) -> None:
        """Show proactive alert diagnostics."""
        data = get_first_entry_config(hass)
        if data is None:
            await async_create_persistent_notification(
                hass,
                title="POM Alert Diagnostics",
                message="Tesla AI için kayıtlı config entry bulunamadı.",
                notification_id="pom_tesla_report_alert_diagnostics",
            )
            return

        message = build_alert_diagnostics_message(hass, data)
        await async_create_persistent_notification(
            hass,
            title="POM Alert Diagnostics",
            message=message,
            notification_id="pom_tesla_report_alert_diagnostics",
        )

        send_telegram = bool(call.data.get("send_telegram", True))
        telegram_target = str(
            call.data.get("chat_id") or call.data.get("telegram_target")
            or get_alert_telegram_target(data)
            or ""
        ).strip()

        if send_telegram and telegram_target:
            for chunk in split_telegram_message(message):
                await async_telegram_send_message(
                    hass,
                    data,
                    target=telegram_target,
                    parse_mode="plain_text",
                    message=chunk,
                )


    async def handle_test_ai_alert(call: ServiceCall) -> None:
        """Send a forced proactive alert test message."""
        data = get_first_entry_config(hass)
        if data is None:
            await async_create_persistent_notification(
                hass,
                title="POM AI Alert Test",
                message="Tesla AI için kayıtlı config entry bulunamadı.",
                notification_id="pom_tesla_report_alert_test",
            )
            return

        alert_type = str(call.data["alert_type"])
        mapping = {
            "low_battery": ("low_battery_test", "Düşük batarya test", "Bu bir testtir. Batarya düşük uyarı hattı çalışıyor."),
            "tire_pressure": ("tire_pressure_test", "Lastik basıncı test", "Bu bir testtir. Lastik basıncı uyarı hattı çalışıyor."),
            "battery_temperature": ("battery_temperature_test", "Batarya sıcaklığı test", "Bu bir testtir. Batarya sıcaklığı uyarı hattı çalışıyor."),
            "charging_stopped": ("charging_stopped_test", "Åarj durdu test", "Bu bir testtir. Åarj durdu uyarı hattı çalışıyor."),
        }
        key, title, rule_message = mapping[alert_type]

        send_telegram = bool(call.data.get("send_telegram", True))
        if send_telegram:
            # Optional override for one-off target without changing config.
            override_target = str(call.data.get("chat_id") or call.data.get("telegram_target") or "").strip()
            test_data = dict(data)
            if override_target:
                test_data[CONF_AI_TELEGRAM_TARGET] = override_target

            await send_pom_ai_alert(
                hass,
                test_data,
                key=key,
                title=title,
                rule_message=rule_message,
                details=f"manual_test_alert_type={alert_type}",
                force=True,
            )

        await async_create_persistent_notification(
            hass,
            title="POM AI Alert Test",
            message=f"Test alert gönderildi: {alert_type}",
            notification_id="pom_tesla_report_alert_test",
        )


    async def handle_ai_ask(call: ServiceCall) -> None:
        """Ask POM AI Basic and optionally send the answer to Telegram."""
        data = get_first_entry_config(hass)

        if data is None:
            message = "Tesla AI için kayıtlı config entry bulunamadı. Önce entegrasyonu kurmalısın."
            await async_create_persistent_notification(
                hass,
                title="POM AI Basic",
                message=message,
                notification_id="pom_tesla_report_ai_error",
            )
            return

        if not get_bool_option(data, CONF_AI_ENABLED, DEFAULT_AI_ENABLED):
            message = "POM AI Basic kapalı. Configure > POM AI Basic bölümünden aktif etmelisin."
            await async_create_persistent_notification(
                hass,
                title="POM AI Basic",
                message=message,
                notification_id="pom_tesla_report_ai_disabled",
            )
            return

        user_message = str(call.data["message"]).strip()
        include_context = bool(call.data.get("include_context", True))
        send_telegram = bool(call.data.get("send_telegram", True))
        telegram_target = str(call.data.get("chat_id") or call.data.get("telegram_target") or data.get(CONF_AI_TELEGRAM_TARGET) or data.get(CONF_TELEGRAM_TARGET) or "").strip()

        charge_cost_answer = await async_maybe_build_charge_cost_answer(hass, data, user_message)
        if charge_cost_answer:
            await async_create_persistent_notification(
                hass,
                title="Tesla AI - Şarj Maliyeti",
                message=charge_cost_answer,
                notification_id="pom_tesla_report_charge_cost_answer",
            )
            if send_telegram and telegram_target:
                await async_telegram_send_message(
                    hass,
                    data,
                    target=telegram_target,
                    parse_mode="plain_text",
                    message=charge_cost_answer,
                )
                await async_send_monthly_charge_cost_visual_report(
                    hass,
                    data,
                    target=telegram_target,
                )
            return

        if await async_handle_trip_summary_request(
            hass,
            data,
            user_message=user_message,
            telegram_target=telegram_target,
            send_telegram=send_telegram,
        ):
            return

        try:
            if await async_handle_ai_vehicle_control_text_confirmation(
                hass,
                data,
                user_message=user_message,
                telegram_target=telegram_target,
                send_telegram=send_telegram,
            ):
                return

            if await async_handle_ai_vehicle_suggestion_text(
                hass,
                data,
                user_message=user_message,
                telegram_target=telegram_target,
                send_telegram=send_telegram,
            ):
                return

            # Direct vehicle controls are handled before normal chat.
            # Indirect comfort complaints must not execute immediately;
            # they go to chat and store a single pending_suggestion for follow-up replies.
            if not is_indirect_vehicle_suggestion_statement(user_message):
                if await async_maybe_start_ai_vehicle_control(
                    hass,
                    data,
                    user_message=user_message,
                    telegram_target=telegram_target,
                    send_telegram=send_telegram,
                ):
                    return
        except Exception as err:
            _LOGGER.exception("POM AI vehicle-control precheck failed; continuing as normal chat")
            await async_create_persistent_notification(
                hass,
                title="POM AI Vehicle Controls - Error",
                message=f"Vehicle-control precheck failed, so this message was routed to normal AI chat: {err}",
                notification_id="pom_tesla_report_ai_control_precheck_error",
            )

        api_key = str(data.get(CONF_OPENAI_API_KEY, "")).strip()
        if not api_key:
            message = "OpenAI API key boş. Configure > POM AI Basic bölümüne API key gir."
            await async_create_persistent_notification(
                hass,
                title="POM AI Basic",
                message=message,
                notification_id="pom_tesla_report_ai_no_api_key",
            )
            return

        model = str(data.get(CONF_OPENAI_MODEL, DEFAULT_OPENAI_MODEL)).strip() or DEFAULT_OPENAI_MODEL
        system_prompt = build_final_ai_system_prompt(data)
        max_output_tokens = int(safe_float(data.get(CONF_AI_MAX_OUTPUT_TOKENS), DEFAULT_AI_MAX_OUTPUT_TOKENS))
        max_output_tokens = max(100, min(max_output_tokens, 4000))

        context_text = build_ai_context_text(hass, data) if include_context else "Bağlam verisi bu çağrıda kapalı."
        recent_memory = get_pom_ai_recent_conversation_text(hass, telegram_target)
        if recent_memory:
            context_text = f"{context_text}\n\n{recent_memory}"
        context_text = f"{context_text}\n\n{build_current_message_language_instruction(user_message)}"

        # Build an explicit pending suggestion candidate before chat generation.
        # This prevents POM from making a natural offer like "klimayı açayım mı"
        # without a real follow-up action behind it. The answer may still be
        # generated naturally, but the single-slot action is already known.
        pre_suggestion_action = build_contextual_vehicle_suggestion_without_llm(
            hass,
            data,
            user_message=user_message,
            assistant_answer="",
        )
        if pre_suggestion_action and not pre_suggestion_action.get("error"):
            context_text = (
                f"{context_text}\n\n"
                "PENDING_SUGGESTION_HINT:\n"
                f"The user's message can safely map to this follow-up action: {pre_suggestion_action.get('label')}. "
                "If you offer to do it, keep the wording clear because the system will remember this as the next pending suggestion."
            )

        try:
            answer = await async_call_openai_responses_api(
                hass,
                api_key=api_key,
                model=model,
                system_prompt=system_prompt,
                user_message=user_message,
                context_text=context_text,
                max_output_tokens=max_output_tokens,
            )
        except Exception as err:
            message = f"POM AI Basic cevap üretemedi: {err}"
            _LOGGER.exception(message)
            await async_create_persistent_notification(
                hass,
                title="POM AI Basic - Hata",
                message=message,
                notification_id="pom_tesla_report_ai_error",
            )
            return

        hass.data.setdefault(DOMAIN, {})["ai_state"] = {
            "last_question": user_message,
            "last_answer": answer,
            "last_model": model,
            "last_at": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
        }

        if pre_suggestion_action and not pre_suggestion_action.get("error"):
            pending = get_pending_ai_vehicle_suggestion_state(hass)
            pending.clear()
            pending.update({
                "created_ts": datetime.now().timestamp(),
                "target": telegram_target,
                "source_message": user_message,
                "assistant_answer": answer,
                "action": copy.deepcopy(pre_suggestion_action),
            })
        else:
            await async_store_contextual_vehicle_suggestion_if_any(
                hass,
                data,
                user_message=user_message,
                assistant_answer=answer,
                telegram_target=telegram_target,
            )

        remember_pom_ai_conversation_turn(hass, telegram_target, user_message, answer)

        notification_message = (
            "POM AI Basic cevap üretti.\n\n"
            f"Soru: `{user_message}`\n\n"
            f"Cevap:\n{answer}"
        )

        await async_create_persistent_notification(
            hass,
            title="POM AI Basic",
            message=notification_message,
            notification_id="pom_tesla_report_ai_last_answer",
        )

        if send_telegram and telegram_target:
            await async_telegram_send_message(
                hass,
                data,
                target=telegram_target,
                parse_mode="plain_text",
                message=f"🤖 {get_ai_display_name(data)}\n\n{answer}",
            )

    async def handle_send_charge_report(call: ServiceCall) -> None:
        """Generate and optionally send the Tesla charging session PNG report."""
        data = get_first_entry_config(hass)

        if data is None:
            message = (
                "Tesla AI için kayıtlı config entry bulunamadı. "
                "Önce entegrasyonu kurmalısın."
            )
            await async_create_persistent_notification(
                hass,
                title="Tesla AI",
                message=message,
                notification_id="pom_tesla_report_charge_report_error",
            )
            return

        test_mode = bool(call.data.get("test_mode", False))
        message_prefix = str(call.data.get("message_prefix", "")).strip()
        send_telegram = bool(call.data.get("send_telegram", True))
        telegram_target = str(
            call.data.get("chat_id") or call.data.get("telegram_target")
            or data.get(CONF_AI_TELEGRAM_TARGET)
            or data.get(CONF_AI_TELEGRAM_LISTENER_CHAT_ID)
            or data.get(CONF_TELEGRAM_TARGET)
            or ""
        ).strip()

        manual_overrides: dict[str, Any] = {}
        if call.data.get("added_kwh") is not None:
            manual_overrides["added_kwh"] = float(call.data.get("added_kwh"))
        if call.data.get("duration_minutes") is not None:
            manual_overrides["duration_minutes"] = float(call.data.get("duration_minutes"))
        if call.data.get("actual_provider") is not None:
            manual_overrides["actual_provider"] = str(call.data.get("actual_provider") or "").strip()
        if call.data.get("actual_price_per_kwh") is not None:
            manual_overrides["actual_price_per_kwh"] = float(call.data.get("actual_price_per_kwh"))
        if call.data.get("actual_total_cost") is not None:
            manual_overrides["actual_total_cost"] = float(call.data.get("actual_total_cost"))
            if "actual_price_per_kwh" in manual_overrides and "added_kwh" not in manual_overrides and manual_overrides["actual_price_per_kwh"] > 0:
                manual_overrides["added_kwh"] = manual_overrides["actual_total_cost"] / manual_overrides["actual_price_per_kwh"]

        try:
            png_path, report_data = await render_and_send_charging_report(
                hass,
                data,
                state=get_charging_report_state(hass),
                send_telegram=send_telegram and bool(telegram_target),
                telegram_target=telegram_target,
                test_mode=test_mode,
                message_prefix=message_prefix,
                manual_overrides=manual_overrides,
            )
            if not test_mode:
                record = await async_record_charge_cost_entry(hass, report_data, source="service")
                if record and send_telegram and telegram_target:
                    await async_send_monthly_charge_cost_visual_report(
                        hass,
                        data,
                        target=telegram_target,
                        month_key=str(record.get("month_key") or ""),
                        caption_prefix="Bu ayki şarj toplamın güncellendi.",
                    )
        except Exception as err:
            _LOGGER.exception("POM charging report generation failed: %s", err)
            await async_create_persistent_notification(
                hass,
                title="Tesla AI - Åarj Raporu Hatası",
                message=f"Åarj raporu PNG üretilemedi: {err}",
                notification_id="pom_tesla_report_charge_report_error",
            )
            return

        added_kwh = safe_float(report_data.get("added_kwh"), 0.0)
        duration_text = format_duration_from_minutes(safe_float(report_data.get("duration_minutes"), 0.0))
        message = (
            "Tesla AI şarj PNG raporu üretildi.\n\n"
            f"PNG: `{png_path}`\n"
            f"Eklenen enerji: `{added_kwh:.2f} kWh`\n"
            f"Süre: `{duration_text}`\n"
            f"Örnek sayısı: `{len(report_data.get('power_samples') or [])}`"
        )
        if send_telegram and not telegram_target:
            message += "\n\nTelegram target boş olduğu için görsel sadece dosyaya üretildi."

        await async_create_persistent_notification(
            hass,
            title="Tesla AI - Åarj Raporu",
            message=message,
            notification_id="pom_tesla_report_charge_report",
        )

    async def handle_start_charge_report_prompt(call: ServiceCall) -> None:
        """Manually start the interactive Telegram charging report prompt."""
        data = get_first_entry_config(hass)

        if data is None:
            await async_create_persistent_notification(
                hass,
                title="Tesla AI",
                message="Tesla AI için kayıtlı config entry bulunamadı. Önce entegrasyonu kurmalısın.",
                notification_id="pom_tesla_report_charge_prompt_error",
            )
            return

        telegram_target = str(
            call.data.get("chat_id") or call.data.get("telegram_target")
            or data.get(CONF_AI_TELEGRAM_TARGET)
            or data.get(CONF_AI_TELEGRAM_LISTENER_CHAT_ID)
            or data.get(CONF_TELEGRAM_TARGET)
            or ""
        ).strip()

        state_snapshot = build_manual_charging_prompt_state(hass, data, dict(call.data))

        try:
            prompted = await async_send_charging_provider_prompt(
                hass,
                data,
                state_snapshot,
                target=telegram_target,
            )
        except Exception as err:
            _LOGGER.exception("POM interactive charge report prompt failed: %s", err)
            await async_create_persistent_notification(
                hass,
                title="Tesla AI - Åarj Sorusu Hatası",
                message=f"Åarj raporu soru akışı başlatılamadı: {err}",
                notification_id="pom_tesla_report_charge_prompt_error",
            )
            return

        if not prompted:
            await async_create_persistent_notification(
                hass,
                title="Tesla AI - Åarj Sorusu",
                message="Telegram target boş olduğu için şarj raporu soru akışı başlatılamadı.",
                notification_id="pom_tesla_report_charge_prompt_error",
            )
            return

        await async_create_persistent_notification(
            hass,
            title="Tesla AI - Åarj Sorusu",
            message="Telegram'a 'Nerede şarj ettin?' sorusu gönderildi.",
            notification_id="pom_tesla_report_charge_prompt",
        )

    async def handle_start_live_trip_test(call: ServiceCall) -> None:
        """Start a simulated live trip for testing the live trip card."""
        entries = hass.config_entries.async_entries(DOMAIN)
        if not entries:
            await async_create_persistent_notification(
                hass,
                title="POM Live Trip Test",
                message="Tesla AI için kayıtlı config entry bulunamadı.",
                notification_id="pom_tesla_report_live_trip_test",
            )
            return

        entry_obj = entries[0]
        data = get_entry_config(entry_obj)
        cancel_live_trip_test_task(hass, entry_obj.entry_id)

        state = get_live_trip_state(hass, entry_obj.entry_id)
        state.clear()
        test_target = str(call.data.get("chat_id") or call.data.get("telegram_target") or "").strip()
        state.update({
            "test_mode": True,
            "status": "active",
            "active": True,
            "trip_status": "Test sürüşü başlatılıyor.",
            "source": "POM live trip test simulator",
            "test_params": dict(call.data),
            "test_telegram_target": test_target,
        })
        notify_live_trip_sensor(hass, entry_obj.entry_id)

        task = hass.async_create_task(
            run_live_trip_test_simulator(hass, entry_obj.entry_id, data, dict(call.data))
        )
        hass.data.setdefault(DOMAIN, {}).setdefault(LIVE_TRIP_TEST_TASK_STORE, {})[entry_obj.entry_id] = task

        await async_create_persistent_notification(
            hass,
            title="POM Live Trip Test",
            message=(
                "Test sürüşü başlatıldı. `sensor.pom_live_trip` canlı simülasyon verileriyle güncellenecek.\n\n"
                f"Süre: `{safe_float(call.data.get('duration_minutes'), 18.0):.1f} dk`\n"
                f"Mesafe: `{safe_float(call.data.get('distance_km'), 3.39):.2f} km`\n"
                f"Enerji: `{safe_float(call.data.get('used_kwh'), 0.62):.2f} kWh`"
            ),
            notification_id="pom_tesla_report_live_trip_test",
        )

    async def handle_finish_live_trip_test(call: ServiceCall) -> None:
        """Finish the current simulated live trip immediately."""
        entries = hass.config_entries.async_entries(DOMAIN)
        if not entries:
            return
        entry_obj = entries[0]
        data = get_entry_config(entry_obj)
        cancel_live_trip_test_task(hass, entry_obj.entry_id)
        state = get_live_trip_state(hass, entry_obj.entry_id)
        if state:
            finalize_live_trip_test_state_from_params(hass, entry_obj.entry_id, data, state)
            png_path = await async_generate_live_trip_test_report(
                hass,
                entry_obj.entry_id,
                data,
                state,
                send_telegram=bool(call.data.get("send_telegram", True)),
                caption=str(call.data.get("caption") or "🚗 Tesla AI - Live Trip Test Raporu"),
                output_path=str(call.data.get("output_path") or "/config/www/pom_tesla_report/live_trip_test_report.png"),
                telegram_target=str(call.data.get("chat_id") or call.data.get("telegram_target") or state.get("test_telegram_target") or "").strip() or None,
            )
        else:
            png_path = ""

        await async_create_persistent_notification(
            hass,
            title="POM Live Trip Test",
            message=(
                "Test sürüşü final moda alındı ve PNG raporu üretildi."
                + (f"\n\nPNG: `{png_path}`" if png_path else "")
            ),
            notification_id="pom_tesla_report_live_trip_test",
        )

    async def handle_reset_live_trip_test(call: ServiceCall) -> None:
        """Reset simulated live trip state back to idle."""
        entries = hass.config_entries.async_entries(DOMAIN)
        if not entries:
            return
        entry_obj = entries[0]
        cancel_live_trip_test_task(hass, entry_obj.entry_id)
        state = get_live_trip_state(hass, entry_obj.entry_id)
        state.clear()
        state.update({
            "status": "idle",
            "active": False,
            "test_mode": False,
            "test_progress": 0.0,
            "last_update": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
            "trip_status": "Canlı sürüş bekleniyor.",
            "source": "POM live trip calculation engine",
        })
        notify_live_trip_sensor(hass, entry_obj.entry_id)

        await async_create_persistent_notification(
            hass,
            title="POM Live Trip Test",
            message="Test sürüşü sıfırlandı.",
            notification_id="pom_tesla_report_live_trip_test",
        )

    async def handle_generate_test_trip_image(call: ServiceCall) -> None:
        """Generate a test trip report PNG and optionally send it to Telegram."""
        data = get_first_entry_config(hass)

        if data is None:
            message = (
                "Tesla AI için kayıtlı config entry bulunamadı. "
                "Önce entegrasyonu kurmalısın."
            )

            await async_create_persistent_notification(
                hass,
                title="Tesla AI",
                message=message,
                notification_id="pom_tesla_report_trip_image_error",
            )
            return

        telegram_target = data.get(CONF_TELEGRAM_TARGET)

        supercharger_price, zes_price, astor_price = get_charging_tariff_prices(hass, data)

        used_kwh = float(call.data["used_kwh"])
        trip_km_value = float(call.data["trip_km"])
        duration_text_value = str(call.data["duration_text"])
        average_overall_speed = safe_float(
            call.data.get("average_overall_speed"),
            overall_speed_from_distance_and_duration_text(trip_km_value, duration_text_value),
        )

        report_data = {
            "test_mode": bool(call.data["test_mode"]),
            "currency_label": get_report_currency(data),
            "report_date": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "trip_km": f"{trip_km_value:.2f}",
            "duration_text": duration_text_value,
            "traffic_text": str(call.data["traffic_text"]),
            "average_speed": f"{float(call.data['average_speed']):.1f}",
            "average_moving_speed": f"{float(call.data['average_speed']):.1f}",
            "average_overall_speed": f"{average_overall_speed:.1f}",
            "used_kwh": f"{used_kwh:.2f}",
            "consumption_kwh_100km": f"{float(call.data['consumption_kwh_100km']):.2f}",
            "start_battery": f"{float(call.data['start_battery']):.1f}",
            "end_battery": f"{float(call.data['end_battery']):.1f}",
            "climate_text": str(call.data["climate_text"]),
            "min_elevation": f"{float(call.data['min_elevation']):.0f}",
            "max_elevation": f"{float(call.data['max_elevation']):.0f}",
            "elevation_range": f"{float(call.data['elevation_range']):.0f}",
            "supercharger_kwh_price": f"{supercharger_price:.2f}",
            "zes_kwh_price": f"{zes_price:.2f}",
            "astor_kwh_price": f"{astor_price:.2f}",
            "supercharger_trip_cost": f"{used_kwh * supercharger_price:.2f}",
            "zes_trip_cost": f"{used_kwh * zes_price:.2f}",
            "astor_trip_cost": f"{used_kwh * astor_price:.2f}",
            "cost_presets": get_trip_cost_presets(data, used_kwh),
            **get_report_visibility_options(data),
        }

        png_path = await hass.async_add_executor_job(
            render_trip_report_png,
            report_data,
            "/config/www/pom_tesla_report/test_trip_report.png",
            get_report_language(data),
        )

        message = (
            "Test sürüş raporu PNG üretildi.\n\n"
            f"Dosya yolu: `{png_path}`\n\n"
            "Tarayıcıdan kontrol:\n"
            "/local/pom_tesla_report/test_trip_report.png"
        )

        await async_create_persistent_notification(
            hass,
            title="Tesla AI - Test PNG",
            message=message,
            notification_id="pom_tesla_report_test_trip_png",
        )

        if bool(call.data["send_telegram"]) and telegram_target:
            await hass.services.async_call(
                "telegram_bot",
                "send_photo",
                {
                    "target": telegram_target,
                    "file": png_path,
                    "caption": "🧪 Tesla AI - Test Sürüş Görseli",
                },
                blocking=True,
            )

    async def handle_generate_trip_image_from_json(call: ServiceCall) -> None:
        """Generate a trip report image from an existing JSON file."""
        data = get_first_entry_config(hass)

        if data is None:
            message = (
                "Tesla AI için kayıtlı config entry bulunamadı. "
                "Önce entegrasyonu kurmalısın."
            )

            await async_create_persistent_notification(
                hass,
                title="Tesla AI",
                message=message,
                notification_id="pom_tesla_report_json_trip_image_error",
            )
            return

        json_path = str(call.data["json_path"])
        output_path = str(call.data["output_path"])
        send_telegram = bool(call.data["send_telegram"])
        caption = str(call.data["caption"])

        try:
            png_path = await hass.async_add_executor_job(
                build_trip_report_data_from_json,
                json_path,
                output_path,
                data,
            )
        except Exception as err:
            message = f"JSON'dan PNG üretilemedi: {err}"

            _LOGGER.exception(message)

            await async_create_persistent_notification(
                hass,
                title="Tesla AI - JSON PNG Hatası",
                message=message,
                notification_id="pom_tesla_report_json_trip_image_error",
            )
            return

        message = (
            "JSON'dan sürüş raporu PNG üretildi.\n\n"
            f"JSON: `{json_path}`\n"
            f"PNG: `{png_path}`\n\n"
            "Tarayıcıdan kontrol:\n"
            "/local/pom_tesla_report/final_trip_report.png"
        )

        await async_create_persistent_notification(
            hass,
            title="Tesla AI - JSON PNG",
            message=message,
            notification_id="pom_tesla_report_json_trip_image",
        )

        telegram_target = data.get(CONF_TELEGRAM_TARGET)

        if send_telegram and telegram_target:
            await hass.services.async_call(
                "telegram_bot",
                "send_photo",
                {
                    "target": telegram_target,
                    "file": png_path,
                    "caption": caption,
                },
                blocking=True,
            )

    async def handle_start_trip(call: ServiceCall) -> None:
        """Start normal trip tracking inside the integration."""
        data = get_first_entry_config(hass)

        if data is None:
            message = "Tesla AI için kayıtlı config entry bulunamadı. Önce entegrasyonu kurmalısın."
            await async_create_persistent_notification(
                hass,
                title="Tesla AI - Start Trip",
                message=message,
                notification_id="pom_tesla_report_start_trip_error",
            )
            return

        await async_start_trip_core(
            data,
            force=bool(call.data.get("force", False)),
            send_notification=bool(call.data.get("send_notification", True)),
            source="manual_service",
        )

    async def handle_finish_trip(call: ServiceCall) -> None:
        """Finish normal trip tracking and generate PNG report."""
        data = get_first_entry_config(hass)

        if data is None:
            message = "Tesla AI için kayıtlı config entry bulunamadı. Önce entegrasyonu kurmalısın."
            await async_create_persistent_notification(
                hass,
                title="Tesla AI - Finish Trip",
                message=message,
                notification_id="pom_tesla_report_finish_trip_error",
            )
            return

        overrides: dict[str, Any] = {}
        for key in [
            "override_trip_km",
            "override_used_kwh",
            "override_end_battery",
            "override_duration_minutes",
            "override_traffic_minutes",
        ]:
            if key in call.data:
                overrides[key] = call.data[key]

        await async_finish_trip_core(
            data,
            send_telegram=bool(call.data["send_telegram"]),
            caption=str(call.data["caption"]),
            output_path=str(call.data["output_path"]),
            test_mode=bool(call.data.get("test_mode", False)),
            overrides=overrides,
            source="manual_service",
        )

    async def handle_debug_trip_state(call: ServiceCall) -> None:
        """Show current normal and manual switch trip states."""
        normal_state = get_trip_state(hass)
        manual_state = get_manual_tracking_state(hass)

        lines = ["Tesla AI trip state:", ""]

        if not normal_state:
            lines.append("## Normal / otomatik sürüş state")
            lines.append("Kayıt yok.")
        else:
            lines.append("## Normal / otomatik sürüş state")
            for key, value in normal_state.items():
                lines.append(f"- `{key}`: `{value}`")

        lines.append("")

        if not manual_state:
            lines.append("## Boolean / manuel takip state")
            lines.append("Kayıt yok.")
        else:
            lines.append("## Boolean / manuel takip state")
            for key, value in manual_state.items():
                lines.append(f"- `{key}`: `{value}`")

        message = "\n".join(lines)

        await async_create_persistent_notification(
            hass,
            title="Tesla AI - Trip State",
            message=message,
            notification_id="pom_tesla_report_trip_state",
        )

    async def handle_reset_trip(call: ServiceCall) -> None:
        """Reset normal and manual switch trip states."""
        clear_trip_state(hass)
        clear_manual_tracking_state(hass)

        await async_create_persistent_notification(
            hass,
            title="Tesla AI - Reset Trip",
            message="Tesla AI normal ve manuel takip state'i sıfırlandı.",
            notification_id="pom_tesla_report_reset_trip",
        )

    if not hass.services.has_service(DOMAIN, SERVICE_DEBUG_CONFIG):
        hass.services.async_register(
            DOMAIN,
            SERVICE_DEBUG_CONFIG,
            handle_debug_config,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_SEND_CHARGE_REPORT):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SEND_CHARGE_REPORT,
            handle_send_charge_report,
            schema=SEND_CHARGE_REPORT_SCHEMA,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_START_CHARGE_REPORT_PROMPT):
        hass.services.async_register(
            DOMAIN,
            SERVICE_START_CHARGE_REPORT_PROMPT,
            handle_start_charge_report_prompt,
            schema=START_CHARGE_REPORT_PROMPT_SCHEMA,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_START_LIVE_TRIP_TEST):
        hass.services.async_register(
            DOMAIN,
            SERVICE_START_LIVE_TRIP_TEST,
            handle_start_live_trip_test,
            schema=START_LIVE_TRIP_TEST_SCHEMA,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_FINISH_LIVE_TRIP_TEST):
        hass.services.async_register(
            DOMAIN,
            SERVICE_FINISH_LIVE_TRIP_TEST,
            handle_finish_live_trip_test,
            schema=FINISH_LIVE_TRIP_TEST_SCHEMA,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_RESET_LIVE_TRIP_TEST):
        hass.services.async_register(
            DOMAIN,
            SERVICE_RESET_LIVE_TRIP_TEST,
            handle_reset_live_trip_test,
            schema=RESET_LIVE_TRIP_TEST_SCHEMA,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_GENERATE_TEST_TRIP_IMAGE):
        hass.services.async_register(
            DOMAIN,
            SERVICE_GENERATE_TEST_TRIP_IMAGE,
            handle_generate_test_trip_image,
            schema=GENERATE_TEST_TRIP_IMAGE_SCHEMA,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_GENERATE_TRIP_IMAGE_FROM_JSON):
        hass.services.async_register(
            DOMAIN,
            SERVICE_GENERATE_TRIP_IMAGE_FROM_JSON,
            handle_generate_trip_image_from_json,
            schema=GENERATE_TRIP_IMAGE_FROM_JSON_SCHEMA,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_START_TRIP):
        hass.services.async_register(
            DOMAIN,
            SERVICE_START_TRIP,
            handle_start_trip,
            schema=START_TRIP_SCHEMA,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_FINISH_TRIP):
        hass.services.async_register(
            DOMAIN,
            SERVICE_FINISH_TRIP,
            handle_finish_trip,
            schema=FINISH_TRIP_SCHEMA,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_DEBUG_TRIP_STATE):
        hass.services.async_register(
            DOMAIN,
            SERVICE_DEBUG_TRIP_STATE,
            handle_debug_trip_state,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_RESET_TRIP):
        hass.services.async_register(
            DOMAIN,
            SERVICE_RESET_TRIP,
            handle_reset_trip,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_AI_ASK):
        hass.services.async_register(
            DOMAIN,
            SERVICE_AI_ASK,
            handle_ai_ask,
            schema=AI_ASK_SCHEMA,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_DEBUG_AI_CONTEXT):
        hass.services.async_register(
            DOMAIN,
            SERVICE_DEBUG_AI_CONTEXT,
            handle_debug_ai_context,
            schema=DEBUG_AI_CONTEXT_SCHEMA,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_DEBUG_ALERTS):
        hass.services.async_register(
            DOMAIN,
            SERVICE_DEBUG_ALERTS,
            handle_debug_alerts,
            schema=DEBUG_ALERTS_SCHEMA,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_TEST_AI_ALERT):
        hass.services.async_register(
            DOMAIN,
            SERVICE_TEST_AI_ALERT,
            handle_test_ai_alert,
            schema=TEST_AI_ALERT_SCHEMA,
        )

    if not hass.services.has_service("telegram_bot", "send_message"):
        async def _compat_send_message(call: ServiceCall) -> None:
            target = str(call.data.get("target") or call.data.get("chat_id") or "").strip()
            data = get_builtin_telegram_config_for_target(hass, target)
            if data is None:
                raise ValueError("Built-in Telegram bot is not configured.")
            await async_telegram_send_message(
                hass,
                data,
                target=target,
                message=str(call.data.get("message") or ""),
                parse_mode=str(call.data.get("parse_mode") or "").strip() or None,
                inline_keyboard=call.data.get("inline_keyboard"),
            )

        hass.services.async_register("telegram_bot", "send_message", _compat_send_message)

    if not hass.services.has_service("telegram_bot", "send_photo"):
        async def _compat_send_photo(call: ServiceCall) -> None:
            target = str(call.data.get("target") or call.data.get("chat_id") or "").strip()
            data = get_builtin_telegram_config_for_target(hass, target)
            if data is None:
                raise ValueError("Built-in Telegram bot is not configured.")
            await async_telegram_send_photo(
                hass,
                data,
                target=target,
                file_path=str(call.data.get("file") or ""),
                caption=str(call.data.get("caption") or ""),
            )

        hass.services.async_register("telegram_bot", "send_photo", _compat_send_photo)

    if not hass.services.has_service("telegram_bot", "delete_message"):
        async def _compat_delete_message(call: ServiceCall) -> None:
            target = str(call.data.get("target") or call.data.get("chat_id") or "").strip()
            data = get_builtin_telegram_config_for_target(hass, target)
            if data is None:
                raise ValueError("Built-in Telegram bot is not configured.")
            await async_telegram_delete_message(
                hass,
                data,
                chat_id=target,
                message_id=int(call.data.get("message_id")),
            )

        hass.services.async_register("telegram_bot", "delete_message", _compat_delete_message)

    if not hass.services.has_service("telegram_bot", "edit_message"):
        async def _compat_edit_message(call: ServiceCall) -> None:
            target = str(call.data.get("target") or call.data.get("chat_id") or "").strip()
            data = get_builtin_telegram_config_for_target(hass, target)
            if data is None:
                raise ValueError("Built-in Telegram bot is not configured.")
            await async_telegram_edit_message(
                hass,
                data,
                chat_id=target,
                message_id=int(call.data.get("message_id")),
                message=str(call.data.get("message") or ""),
                inline_keyboard=call.data.get("inline_keyboard"),
            )

        hass.services.async_register("telegram_bot", "edit_message", _compat_edit_message)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Tesla AI from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    hass.data[DOMAIN][entry.entry_id] = get_entry_config(entry)

    _LOGGER.warning("Tesla AI alpha283 Drive Dashboard entity bindings build loaded. version=2.2.0-dashboard-alpha362-tesla-ai-name-cache-hide entry=%s", entry.entry_id)

    entry.async_on_unload(entry.add_update_listener(async_update_options))

    process_func = hass.data[DOMAIN].get("async_process_auto_trip_signal")
    config_data = hass.data[DOMAIN][entry.entry_id]

    shift_entity = config_data.get(CONF_SHIFT_STATE_ENTITY)
    speed_entity = config_data.get(CONF_SPEED_ENTITY)
    climate_entity = config_data.get(CONF_CLIMATE_ENTITY)
    elevation_entity = config_data.get(CONF_ELEVATION_ENTITY)

    watched_entities = [
        entity
        for entity in [shift_entity, speed_entity, climate_entity, elevation_entity]
        if entity
    ]

    if process_func and watched_entities:

        async def _handle_state_change(event) -> None:
            entity_id = event.data.get("entity_id", "")
            await process_func(entry.entry_id, entity_id)

        unsub = async_track_state_change_event(
            hass,
            watched_entities,
            _handle_state_change,
        )
        entry.async_on_unload(unsub)

        _LOGGER.info(
            "Tesla AI auto trip listeners registered for entry %s: %s",
            entry.entry_id,
            watched_entities,
        )

    map_enabled = is_trip_map_collection_enabled(config_data)

    if map_enabled:
        sample_interval_seconds = max(
            1,
            int(
                safe_float(
                    config_data.get(CONF_TRIP_MAP_SAMPLE_INTERVAL_SECONDS),
                    DEFAULT_TRIP_MAP_SAMPLE_INTERVAL_SECONDS,
                )
            ),
        )

        async def _handle_map_interval(_now) -> None:
            current_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, config_data)
            update_trip_map_samples_for_active_states(hass, current_data)

        unsub_map = async_track_time_interval(
            hass,
            _handle_map_interval,
            timedelta(seconds=sample_interval_seconds),
        )
        entry.async_on_unload(unsub_map)

        _LOGGER.info(
            "Tesla AI trip map sampler registered. entry=%s tracker=%s interval=%ss",
            entry.entry_id,
            config_data.get(CONF_TRIP_MAP_TRACKER_ENTITY, DEFAULT_TRIP_MAP_TRACKER_ENTITY),
            sample_interval_seconds,
        )

    # Open-Meteo elevation sampler.
    # It follows the same location tracker used by Trip Map and writes a live
    # sensor during Live Trip / manual tracking / classic trip sessions. The
    # external API is rate-limited by movement and interval, with rounded-coordinate
    # cache, so we do not call the free open API every second.
    elevation_interval_seconds = max(
        5,
        int(
            safe_float(
                config_data.get(CONF_TRIP_MAP_SAMPLE_INTERVAL_SECONDS),
                DEFAULT_TRIP_MAP_SAMPLE_INTERVAL_SECONDS,
            )
        ),
    )

    async def _handle_trip_elevation_interval(_now) -> None:
        current_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, config_data)
        try:
            await async_update_trip_elevation_sample(hass, entry.entry_id, current_data)
        except Exception as err:
            _LOGGER.exception("POM Open-Meteo elevation sampler failed: %s", err)

    unsub_trip_elevation = async_track_time_interval(
        hass,
        _handle_trip_elevation_interval,
        timedelta(seconds=elevation_interval_seconds),
    )
    entry.async_on_unload(unsub_trip_elevation)

    _LOGGER.info(
        "Tesla AI Open-Meteo elevation sampler registered. entry=%s interval=%ss",
        entry.entry_id,
        elevation_interval_seconds,
    )

    async def _bootstrap_trip_elevation_once() -> None:
        await asyncio.sleep(2)
        current_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, config_data)
        try:
            await async_bootstrap_trip_elevation_from_current_location(hass, entry.entry_id, current_data)
        except Exception as err:
            _LOGGER.debug("POM Open-Meteo idle elevation bootstrap skipped: %s", err, exc_info=True)

    hass.async_create_task(_bootstrap_trip_elevation_once())

    # Runtime speed sampler for manual tracking and classic auto trip states.
    # It keeps moving-average speed independent from total elapsed time, so Park
    # grace periods and manual switch breaks do not distort report speed.
    async def _handle_runtime_tracking_interval(_now) -> None:
        current_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, config_data)
        try:
            update_all_active_tracking_states(hass, current_data)
        except Exception as err:
            _LOGGER.exception("POM runtime speed sampler failed: %s", err)

    unsub_runtime_tracking = async_track_time_interval(
        hass,
        _handle_runtime_tracking_interval,
        timedelta(seconds=1),
    )
    entry.async_on_unload(unsub_runtime_tracking)

    # Charging Session Graph sampler.
    # It intentionally uses only a small set of entities: charge_energy_added,
    # battery_range, battery_range_estimate and charger_power. No extra UI setting is required.
    async def _handle_charging_report_interval(_now) -> None:
        current_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, config_data)
        try:
            await update_charging_report_session(hass, current_data)
        except Exception as err:
            _LOGGER.exception("POM charging report sampler failed: %s", err)

    unsub_charging_report = async_track_time_interval(
        hass,
        _handle_charging_report_interval,
        timedelta(seconds=2),
    )
    entry.async_on_unload(unsub_charging_report)

    _LOGGER.info(
        "Tesla AI charging report sampler registered for entry %s",
        entry.entry_id,
    )

    async def _handle_periodic_report_interval(_now) -> None:
        current_data = get_live_entry_config_for_telegram(hass, entry, config_data)
        try:
            await async_send_periodic_reports_if_due(hass, current_data)
        except Exception as err:
            _LOGGER.exception("POM scheduled Telegram reports failed: %s", err)

    unsub_periodic_reports = async_track_time_interval(
        hass,
        _handle_periodic_report_interval,
        timedelta(minutes=1),
    )
    entry.async_on_unload(unsub_periodic_reports)

    # Backend live trip calculation engine.
    if get_bool_option(config_data, CONF_LIVE_TRIP_ENABLED, DEFAULT_LIVE_TRIP_ENABLED):
        live_interval_seconds = max(
            1,
            int(
                safe_float(
                    config_data.get(CONF_LIVE_TRIP_UPDATE_INTERVAL_SECONDS),
                    DEFAULT_LIVE_TRIP_UPDATE_INTERVAL_SECONDS,
                )
            ),
        )

        async def _handle_live_trip_interval(_now) -> None:
            current_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, config_data)
            try:
                await update_live_trip_engine(hass, entry.entry_id, current_data)
            except Exception as err:
                _LOGGER.exception("POM live trip calculation failed: %s", err)

        unsub_live_trip = async_track_time_interval(
            hass,
            _handle_live_trip_interval,
            timedelta(seconds=live_interval_seconds),
        )
        entry.async_on_unload(unsub_live_trip)

        async def _handle_live_trip_speed_sampler_interval(_now) -> None:
            current_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, config_data)
            try:
                update_live_trip_speed_samples(hass, entry.entry_id, current_data)
            except Exception as err:
                _LOGGER.exception("POM live trip speed sampler failed: %s", err)

        unsub_live_trip_speed_sampler = async_track_time_interval(
            hass,
            _handle_live_trip_speed_sampler_interval,
            timedelta(seconds=SPEED_SAMPLER_INTERVAL_SECONDS),
        )
        entry.async_on_unload(unsub_live_trip_speed_sampler)

        # Prime the sensor shortly after startup so the card has attributes even before driving.
        try:
            await update_live_trip_engine(hass, entry.entry_id, config_data)
        except Exception:
            _LOGGER.debug("POM live trip initial update skipped", exc_info=True)

        _LOGGER.info(
            "Tesla AI live trip engine registered for entry %s interval=%ss speed_sampler=%ss",
            entry.entry_id,
            live_interval_seconds,
            SPEED_SAMPLER_INTERVAL_SECONDS,
        )

    # Register proactive alert watchers unconditionally. Panel option saves are applied
    # in memory without reloading the config entry, so gating listener registration by
    # the startup value of ai_alerts_enabled could leave Automations inactive until a
    # full HA restart. The evaluators below read current options on every run.

    async def _handle_ai_alert_interval(_now) -> None:
        current_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, config_data)
        try:
            await evaluate_pom_ai_alerts(hass, current_data)
        except Exception as err:
            _LOGGER.exception("POM AI proactive alert evaluation failed: %s", err)

    unsub_alerts = async_track_time_interval(
        hass,
        _handle_ai_alert_interval,
        timedelta(seconds=60),
    )
    entry.async_on_unload(unsub_alerts)

    async def _handle_low_battery_event(event) -> None:
        current_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, config_data)
        if not get_bool_option(current_data, CONF_AI_ALERTS_ENABLED, DEFAULT_AI_ALERTS_ENABLED):
            return
        if not get_bool_option(current_data, CONF_AI_ALERT_LOW_BATTERY_ENABLED, DEFAULT_AI_ALERT_LOW_BATTERY_ENABLED):
            return
        battery_alert_entity = get_report_configured_entity(
            current_data,
            CONF_BATTERY_LEVEL_ENTITY,
            VEHICLE_ROLE_BATTERY_LEVEL,
        ) or get_configured_entity(
            current_data,
            CONF_BATTERY_LEVEL_ENTITY,
            VEHICLE_ROLE_BATTERY_LEVEL,
            usage_key="use_report",
        )
        changed_entity = str(event.data.get("entity_id") or "").strip()
        if not battery_alert_entity or changed_entity != battery_alert_entity:
            return
        new_state = event.data.get("new_state")
        if new_state is None:
            return
        try:
            value = float(new_state.state)
        except (TypeError, ValueError):
            return
        stage = get_low_battery_stage_to_send(hass, value)
        if stage is not None:
            await send_pom_ai_alert(
                hass,
                current_data,
                key=f"low_battery_{stage}",
                title=f"Düşük batarya %{stage}",
                rule_message=build_low_battery_staged_message(value, stage),
                details=f"battery_entity={battery_alert_entity}, battery_level={value}, stage={stage}, trigger=state_changed",
                force=True,
            )
            mark_low_battery_stage_sent(hass, stage)

    unsub_low_battery = hass.bus.async_listen("state_changed", _handle_low_battery_event)
    entry.async_on_unload(unsub_low_battery)

    _LOGGER.info(
        "Tesla AI AI Alerts & Watchers registered for entry %s (dynamic options + built-in Telegram path)",
        entry.entry_id,
    )

    # Window open instant test alert removed.

    listener_enabled = get_bool_option(
        config_data,
        CONF_AI_TELEGRAM_LISTENER_ENABLED,
        DEFAULT_AI_TELEGRAM_LISTENER_ENABLED,
    )
    # Slash-style deterministic report commands must work even when the AI
    # conversation listener is disabled. They only need Telegram events and the
    # configured Telegram target/chat. AI fallback remains disabled unless
    # listener_enabled is true.
    command_listener_enabled = bool(
        normalize_telegram_id(
            config_data.get(CONF_TELEGRAM_TARGET)
            or config_data.get(CONF_AI_TELEGRAM_TARGET)
            or config_data.get(CONF_AI_TELEGRAM_LISTENER_CHAT_ID)
        )
    ) or is_builtin_telegram_enabled(config_data)

    if listener_enabled or command_listener_enabled:
        listener_chat_id = normalize_telegram_id(
            config_data.get(CONF_AI_TELEGRAM_LISTENER_CHAT_ID)
            or config_data.get(CONF_TELEGRAM_TARGET)
            or config_data.get(CONF_AI_TELEGRAM_TARGET)
        )
        allowed_user_id = normalize_telegram_id(
            config_data.get(CONF_AI_TELEGRAM_ALLOWED_USER_ID, DEFAULT_AI_TELEGRAM_ALLOWED_USER_ID)
        )
        prefix_text = str(
            config_data.get(CONF_AI_TELEGRAM_PREFIX, DEFAULT_AI_TELEGRAM_PREFIX)
            or DEFAULT_AI_TELEGRAM_PREFIX
        ).strip()
        include_context = get_bool_option(
            config_data,
            CONF_AI_TELEGRAM_INCLUDE_CONTEXT,
            DEFAULT_AI_TELEGRAM_INCLUDE_CONTEXT,
        )
        listener_state_key = f"{entry.entry_id}_telegram_listener_state"
        listener_runtime = hass.data.setdefault(DOMAIN, {}).setdefault(
            listener_state_key,
            {"text_events": {}, "callback_events": {}},
        )

        def _event_chat_id(event_data: dict[str, Any]) -> str:
            chat_id_value = event_data.get("chat_id")
            if chat_id_value is None and isinstance(event_data.get("message"), dict):
                chat = event_data.get("message", {}).get("chat")
                if isinstance(chat, dict):
                    chat_id_value = chat.get("id")
            return normalize_telegram_id(chat_id_value)

        def _event_user_id(event_data: dict[str, Any]) -> str:
            user_id_value = event_data.get("user_id") or event_data.get("from_id")
            if user_id_value is None and isinstance(event_data.get("message"), dict):
                from_block = event_data.get("message", {}).get("from")
                if isinstance(from_block, dict):
                    user_id_value = from_block.get("id")
            return normalize_telegram_id(user_id_value)

        def _event_text(event_data: dict[str, Any]) -> str:
            text_value = event_data.get("text")
            if text_value is None and isinstance(event_data.get("message"), dict):
                text_value = event_data.get("message", {}).get("text")
            return str(text_value or "").strip()

        def _event_message_id(event_data: dict[str, Any]) -> str:
            raw_value = event_data.get("message_id") or event_data.get("msg_id")
            if raw_value is None and isinstance(event_data.get("message"), dict):
                raw_value = event_data.get("message", {}).get("message_id") or event_data.get("message", {}).get("id")
            return str(raw_value or "").strip()

        def _event_update_id(event_data: dict[str, Any]) -> str:
            return str(event_data.get("update_id") or "").strip()

        def _build_telegram_event_dedupe_key(event_data: dict[str, Any], kind: str) -> tuple[str, float]:
            chat_id_value = _event_chat_id(event_data)
            user_id_value = _event_user_id(event_data)
            message_id_value = _event_message_id(event_data)
            if message_id_value:
                return (f"{kind}:msg:{chat_id_value}:{message_id_value}", 180.0)

            update_id_value = _event_update_id(event_data)
            if update_id_value:
                return (f"{kind}:upd:{update_id_value}", 180.0)

            text_value = normalize_text_for_match(_event_text(event_data))[:200]
            callback_value = str(event_data.get("data") or "").strip()[:200]
            fingerprint = callback_value if kind == "callback" else text_value
            return (f"{kind}:txt:{chat_id_value}:{user_id_value}:{fingerprint}", 6.0)

        def _telegram_event_dedupe_alias_keys(event_data: dict[str, Any], kind: str) -> tuple[list[str], float]:
            primary_key, ttl_seconds = _build_telegram_event_dedupe_key(event_data, kind)
            keys = [primary_key]
            chat_id_value = _event_chat_id(event_data)
            user_id_value = _event_user_id(event_data)
            if kind == "text":
                text_value = normalize_text_for_match(_event_text(event_data))[:200]
                if text_value:
                    keys.append(f"text:txt:{chat_id_value}:{user_id_value}:{text_value}")
                    keys.append(f"text:chat-txt:{chat_id_value}:{text_value}")
                    if text_value.startswith("/"):
                        command_word = text_value.split(maxsplit=1)[0]
                        keys.append(f"text:chat-cmd:{chat_id_value}:{command_word}")
            elif kind == "callback":
                callback_value = str(event_data.get("data") or "").strip()[:200]
                if callback_value:
                    keys.append(f"callback:data:{chat_id_value}:{user_id_value}:{callback_value}")
                    keys.append(f"callback:chat-data:{chat_id_value}:{callback_value}")
            # preserve order while removing duplicates
            return list(dict.fromkeys(keys)), ttl_seconds

        def _should_skip_duplicate_telegram_event(event_data: dict[str, Any], kind: str) -> bool:
            cache_name = "callback_events" if kind == "callback" else "text_events"
            cache = listener_runtime.setdefault(cache_name, {})
            now_ts = datetime.now().timestamp()

            # Keep the small dedupe caches tidy.
            stale_keys = [
                cache_key
                for cache_key, item in list(cache.items())
                if now_ts - float(item.get("ts", 0.0)) > float(item.get("ttl", 180.0))
            ]
            for stale_key in stale_keys:
                cache.pop(stale_key, None)

            dedupe_keys, ttl_seconds = _telegram_event_dedupe_alias_keys(event_data, kind)
            for dedupe_key in dedupe_keys:
                previous = cache.get(dedupe_key)
                if previous and (now_ts - float(previous.get("ts", 0.0))) <= float(previous.get("ttl", ttl_seconds)):
                    return True

            for dedupe_key in dedupe_keys:
                cache[dedupe_key] = {"ts": now_ts, "ttl": ttl_seconds}
            if len(cache) > 800:
                for overflow_key, _item in sorted(
                    cache.items(),
                    key=lambda pair: float(pair[1].get("ts", 0.0)),
                )[: len(cache) - 650]:
                    cache.pop(overflow_key, None)
            return False

        async def _handle_telegram_callback_event(event) -> None:
            event_data = event.data or {}
            callback_data = str(event_data.get("data") or "").strip()
            chat_id = _event_chat_id(event_data)
            user_id = _event_user_id(event_data)

            if listener_chat_id and chat_id and chat_id != listener_chat_id:
                return
            if allowed_user_id and user_id and user_id != allowed_user_id:
                return
            if _should_skip_duplicate_telegram_event(event_data, "callback"):
                _LOGGER.debug("Skipping duplicate telegram callback event for chat %s", chat_id or "-")
                return

            current_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, config_data)

            if callback_data.startswith("/pom_ai_alias_"):
                # Alias training was removed in favor of the curated capability manifest.
                target = chat_id or str(current_data.get(CONF_AI_TELEGRAM_TARGET) or current_data.get(CONF_TELEGRAM_TARGET) or "").strip()
                if target:
                    await hass.services.async_call(
                        "telegram_bot",
                        "send_message",
                        {"target": target, "parse_mode": "plain_text", "message": "Alias öğrenme kaldırıldı. Kontroller capability manifest üzerinden çalışıyor."},
                        blocking=True,
                    )
                return

            if callback_data.startswith("/tripall") or callback_data.startswith("/single") or callback_data.startswith("/triplast") or callback_data.startswith("/triptoday") or callback_data.startswith("/tripweek"):
                target = chat_id or str(current_data.get(CONF_AI_TELEGRAM_TARGET) or current_data.get(CONF_TELEGRAM_TARGET) or "").strip()
                await async_handle_trip_summary_request(
                    hass,
                    current_data,
                    user_message=callback_data,
                    telegram_target=target,
                    send_telegram=True,
                )
                return

            if callback_data.startswith("/pom_ai_control_"):
                action_part = callback_data.replace("/pom_ai_control_", "", 1)
                if "_" not in action_part:
                    return
                decision, token = action_part.split("_", 1)
                pending_controls = get_pending_ai_vehicle_control_state(hass)
                pending_item = pending_controls.get(token)
                target = chat_id or str((pending_item or {}).get("target") or current_data.get(CONF_AI_TELEGRAM_TARGET) or current_data.get(CONF_TELEGRAM_TARGET) or "").strip()
                source_message = str((pending_item or {}).get("user_message") or "")

                def _callback_message_id() -> int | None:
                    msg = event_data.get("message") or {}
                    raw = event_data.get("message_id") or event_data.get("msg_id")
                    if not raw and isinstance(msg, dict):
                        raw = msg.get("message_id") or msg.get("id")
                    try:
                        return int(raw) if raw is not None and str(raw).strip() else None
                    except (TypeError, ValueError):
                        return None

                async def _edit_or_send_result(result_message: str) -> None:
                    localized_result = await async_translate_runtime_message_if_needed(
                        hass,
                        current_data,
                        user_message=source_message or result_message,
                        message_text=result_message,
                    )
                    message_id = _callback_message_id()
                    # Prefer deleting the inline-keyboard confirmation so the old approval box disappears.
                    if target and message_id:
                        try:
                            await hass.services.async_call(
                                "telegram_bot",
                                "delete_message",
                                {
                                    "chat_id": target,
                                    "message_id": message_id,
                                },
                                blocking=True,
                            )
                        except Exception:
                            _LOGGER.debug("Could not delete POM AI vehicle control confirmation message", exc_info=True)
                            try:
                                await hass.services.async_call(
                                    "telegram_bot",
                                    "edit_message",
                                    {
                                    "chat_id": target,
                                    "message_id": message_id,
                                        "message": localized_result,
                                        "inline_keyboard": [],
                                    },
                                    blocking=True,
                                )
                                return
                            except Exception:
                                _LOGGER.debug("Could not edit POM AI vehicle control confirmation message", exc_info=True)
                    if target:
                        await hass.services.async_call(
                            "telegram_bot",
                            "send_message",
                            {"target": target, "parse_mode": "plain_text", "message": localized_result},
                            blocking=True,
                        )

                if not pending_item:
                    await _edit_or_send_result("Bu araç kontrol onayı artık aktif değil.")
                    return
                if decision == "cancel":
                    action_label = str((pending_item.get("action") or {}).get("label") or "Araç kontrolü")
                    pending_controls.pop(token, None)
                    await _edit_or_send_result(f"{action_label} komutu iptal edildi.")
                    return
                if decision == "confirm":
                    try:
                        result = await async_execute_ai_vehicle_control_action(hass, pending_item.get("action") or {})
                        pending_controls.pop(token, None)
                        await _edit_or_send_result(result)
                    except Exception as err:
                        _LOGGER.exception("POM AI vehicle control failed")
                        await _edit_or_send_result(f"Araç kontrol komutu çalıştırılamadı: {err}")
                    return
                return

            if not (callback_data.startswith("/pom_charge_provider_") or callback_data.startswith("/pom_charge_other_")):
                return

            pending = get_pending_charging_report_state(hass)
            if not pending.get("active"):
                await hass.services.async_call(
                    "telegram_bot",
                    "send_message",
                    {
                        "target": chat_id or get_charging_report_telegram_target(current_data),
                        "parse_mode": "plain_text",
                        "message": charge_text(current_data, "inactive"),
                    },
                    blocking=True,
                )
                return

            target = str(pending.get("target") or chat_id or get_charging_report_telegram_target(current_data)).strip()

            if callback_data.startswith("/pom_charge_other_"):
                action = callback_data.replace("/pom_charge_other_", "", 1).strip().lower()
                if action == "confirm":
                    manual_overrides = build_other_charging_overrides_from_pending(pending)
                    if not manual_overrides:
                        pending["step"] = "other_price"
                        await async_send_other_charging_price_prompt(hass, target, current_data, flow_kind=str(pending.get("flow_kind") or "manual"))
                        return
                    try:
                        await async_finalize_interactive_charging_report(
                            hass,
                            current_data,
                            pending,
                            manual_overrides=manual_overrides,
                            message_prefix=charge_text(current_data, "abroad_done" if str(pending.get("flow_kind") or "") == "abroad" else "manual_done"),
                        )
                    except Exception as err:
                        _LOGGER.exception("POM charge report other confirm failed")
                        await hass.services.async_call(
                            "telegram_bot",
                            "send_message",
                            {"target": target, "parse_mode": "plain_text", "message": f"Şarj raporu oluşturulamadı: {err}"},
                            blocking=True,
                        )
                    return

                if action == "fix_price":
                    pending["step"] = "other_price"
                    await async_send_other_charging_price_prompt(hass, target, current_data, flow_kind=str(pending.get("flow_kind") or "manual"))
                    return

                if action == "fix_total":
                    if safe_float(pending.get("actual_price_per_kwh"), 0.0) <= 0:
                        pending["step"] = "other_price"
                        await async_send_other_charging_price_prompt(hass, target, current_data, flow_kind=str(pending.get("flow_kind") or "manual"))
                    else:
                        pending["step"] = "other_total"
                        await async_send_other_charging_total_prompt(hass, target, safe_float(pending.get("actual_price_per_kwh"), 0.0), current_data, flow_kind=str(pending.get("flow_kind") or "manual"))
                    return

                if action == "restart":
                    await async_send_charging_provider_prompt(hass, current_data, pending.get("state") or get_charging_report_state(hass), target=target)
                    return

                if action == "cancel":
                    pending.clear()
                    await hass.services.async_call(
                        "telegram_bot",
                        "send_message",
                        {"target": target, "parse_mode": "plain_text", "message": charge_text(current_data, "cancelled")},
                        blocking=True,
                    )
                    return

            selected = callback_data.replace("/pom_charge_provider_", "", 1).strip().lower()

            if selected == "manual":
                pending["step"] = "other_price"
                pending["flow_kind"] = "manual"
                pending["provider"] = charge_text(current_data, "manual_label")
                pending["actual_currency"] = get_report_currency(current_data)
                pending.pop("actual_price_per_kwh", None)
                pending.pop("actual_total_cost", None)
                await async_send_other_charging_price_prompt(hass, target, current_data, flow_kind="manual")
                return

            if selected == "abroad":
                pending["step"] = "other_price"
                pending["flow_kind"] = "abroad"
                pending["provider"] = charge_text(current_data, "abroad_label")
                pending.pop("actual_price_per_kwh", None)
                pending.pop("actual_total_cost", None)
                pending.pop("actual_currency", None)
                await async_send_other_charging_price_prompt(hass, target, current_data, flow_kind="abroad")
                return

            await async_send_charging_provider_prompt(hass, current_data, pending.get("state") or get_charging_report_state(hass), target=target)
            return

        async def _handle_telegram_text_event(event) -> None:
            event_data = event.data or {}
            chat_id = _event_chat_id(event_data)
            user_id = _event_user_id(event_data)
            raw_message = _event_text(event_data)

            if not raw_message:
                return

            if listener_chat_id and chat_id != listener_chat_id:
                return

            if allowed_user_id and user_id != allowed_user_id:
                return
            if _should_skip_duplicate_telegram_event(event_data, "text"):
                _LOGGER.debug("Skipping duplicate telegram text event for chat %s text=%s", chat_id or "-", raw_message[:80])
                return

            current_data = get_live_entry_config_for_telegram(
                hass,
                entry,
                hass.data.get(DOMAIN, {}).get(entry.entry_id, config_data),
            )

            pending_charge = get_pending_charging_report_state(hass)
            if pending_charge.get("active") and pending_charge.get("step") in {"other_price", "other_total", "other_currency"}:
                pending_chat_id = normalize_telegram_id(pending_charge.get("chat_id") or pending_charge.get("target"))
                if (not pending_chat_id) or chat_id == pending_chat_id:
                    lowered = normalize_text_for_match(raw_message)
                    target = str(pending_charge.get("target") or chat_id or get_charging_report_telegram_target(current_data)).strip()
                    if lowered in {"iptal", "cancel", "vazgec", "vazgeç"}:
                        pending_charge.clear()
                        await hass.services.async_call(
                            "telegram_bot",
                            "send_message",
                            {"target": target, "parse_mode": "plain_text", "message": charge_text(current_data, "cancelled")},
                            blocking=True,
                        )
                        return

                    if lowered in {"atla", "skip", "gec", "geç"}:
                        try:
                            await async_finalize_interactive_charging_report(
                                hass,
                                current_data,
                                pending_charge,
                                message_prefix=charge_text(current_data, "fallback_done"),
                            )
                        except Exception as err:
                            _LOGGER.exception("POM charge report custom flow skip failed")
                            await hass.services.async_call(
                                "telegram_bot",
                                "send_message",
                                {"target": target, "parse_mode": "plain_text", "message": f"Şarj raporu oluşturulamadı: {err}"},
                                blocking=True,
                            )
                        return

                    value = parse_charging_money_value(raw_message)
                    if pending_charge.get("step") == "other_price":
                        if value is None or value <= 0 or value > 100:
                            await hass.services.async_call(
                                "telegram_bot",
                                "send_message",
                                {
                                    "target": target,
                                    "parse_mode": "plain_text",
                                    "message": charge_text(current_data, "not_understood_price"),
                                },
                                blocking=True,
                            )
                            return
                        pending_charge["actual_price_per_kwh"] = round(value, 4)
                        pending_charge["step"] = "other_total"
                        await async_send_other_charging_total_prompt(hass, target, value, current_data, flow_kind=str(pending_charge.get("flow_kind") or "manual"))
                        return

                    if pending_charge.get("step") == "other_total":
                        if value is None or value <= 0 or value > 50000:
                            await hass.services.async_call(
                                "telegram_bot",
                                "send_message",
                                {
                                    "target": target,
                                    "parse_mode": "plain_text",
                                    "message": charge_text(current_data, "not_understood_total"),
                                },
                                blocking=True,
                            )
                            return
                        price = safe_float(pending_charge.get("actual_price_per_kwh"), 0.0)
                        if price <= 0:
                            pending_charge["step"] = "other_price"
                            await async_send_other_charging_price_prompt(hass, target, current_data, flow_kind=str(pending_charge.get("flow_kind") or "manual"))
                            return
                        calculated_kwh = value / price
                        if calculated_kwh <= 0 or calculated_kwh > 300:
                            await hass.services.async_call(
                                "telegram_bot",
                                "send_message",
                                {
                                    "target": target,
                                    "parse_mode": "plain_text",
                                    "message": (
                                        f"Bu değerlerle hesaplanan enerji {calculated_kwh:.1f} kWh çıkıyor. "
                                        "Bu mantıklı görünmedi. Toplam tutarı tekrar yaz. Örnek: 480"
                                    ),
                                },
                                blocking=True,
                            )
                            return
                        pending_charge["actual_total_cost"] = round(value, 2)
                        if str(pending_charge.get("flow_kind") or "") == "abroad" and not str(pending_charge.get("actual_currency") or "").strip():
                            pending_charge["step"] = "other_currency"
                            await async_send_other_charging_currency_prompt(hass, target, current_data)
                            return
                        pending_charge["step"] = "other_confirm"
                        await async_send_other_charging_summary_prompt(hass, pending_charge, target, current_data)
                        return

                    if pending_charge.get("step") == "other_currency":
                        currency = parse_charge_currency_code(raw_message)
                        if not currency:
                            await hass.services.async_call(
                                "telegram_bot",
                                "send_message",
                                {"target": target, "parse_mode": "plain_text", "message": charge_text(current_data, "not_understood_currency")},
                                blocking=True,
                            )
                            return
                        pending_charge["actual_currency"] = currency
                        pending_charge["step"] = "other_confirm"
                        await async_send_other_charging_summary_prompt(hass, pending_charge, target, current_data)
                        return

            # Prefix is optional legacy sugar only. Telegram AI never requires it.
            stripped_for_command = strip_ai_prefix(raw_message, prefix_text) if prefix_text else None
            command_candidates = [raw_message]
            if stripped_for_command and stripped_for_command not in command_candidates:
                command_candidates.append(stripped_for_command)

            if any(should_send_ai_context_debug(candidate) for candidate in command_candidates):
                try:
                    debug_message = build_ai_context_entity_debug(hass, current_data)
                    await async_send_telegram_text_chunks(
                        hass,
                        current_data,
                        chat_id,
                        debug_message,
                        title="📊 POM AI Veri Erişimi",
                        limit=3000,
                    )
                except Exception as err:  # pragma: no cover - defensive runtime guard
                    _LOGGER.exception("POM AI context visibility command failed")
                    try:
                        await hass.services.async_call(
                            "telegram_bot",
                            "send_message",
                            {
                                "target": chat_id,
                                "parse_mode": "plain_text",
                                "message": f"POM AI veri listesi hazırlanırken hata oluştu: {err}",
                            },
                            blocking=True,
                        )
                    except Exception:
                        _LOGGER.exception("Could not send POM AI context visibility error to Telegram")
                return

            user_message = stripped_for_command or raw_message

            if await async_handle_configured_telegram_report_command(
                hass,
                current_data,
                user_message=user_message,
                telegram_target=chat_id,
                send_telegram=True,
            ):
                return

            if str(user_message or "").strip().startswith("/"):
                # Slash commands are deterministic. If the custom/legacy command
                # did not match, answer with the live command help instead of
                # silently falling through to AI or older natural-language paths.
                await async_telegram_send_message(
                    hass,
                    current_data,
                    target=chat_id,
                    parse_mode="plain_text",
                    message=build_telegram_report_commands_help(
                        current_data,
                        lang=get_telegram_report_language(current_data, user_message),
                    ),
                )
                return

            charge_cost_answer = await async_maybe_build_charge_cost_answer(hass, current_data, user_message)
            if charge_cost_answer:
                await async_telegram_send_message(
                    hass,
                    current_data,
                    target=chat_id,
                    parse_mode="plain_text",
                    message=charge_cost_answer,
                )
                await async_send_monthly_charge_cost_visual_report(
                    hass,
                    current_data,
                    target=chat_id,
                )
                return

            if should_send_last_trip_png(user_message) or is_trip_last_command(user_message):
                await async_send_last_trip_report_visual(
                    hass,
                    current_data,
                    target=chat_id,
                    user_message=user_message,
                )
                return

            if await async_handle_trip_summary_request(
                hass,
                current_data,
                user_message=user_message,
                telegram_target=chat_id,
                send_telegram=True,
            ):
                return

            if any(candidate and should_send_vehicle_location_answer(candidate) for candidate in command_candidates):
                try:
                    # alpha234: send a single Telegram answer. Previously this path
                    # sent the map image and then a second text-only location reply.
                    # With built-in Telegram / some clients that looked like duplicate
                    # responses. Now the deterministic text is used as the photo caption;
                    # if the image cannot be rendered, we fall back to text only.
                    location_message = await async_build_vehicle_location_answer(hass, current_data, user_message)
                    sent_map = await async_send_vehicle_location_map_if_available(
                        hass,
                        current_data,
                        target=chat_id,
                        message=user_message,
                        caption=location_message,
                    )
                    if not sent_map:
                        await async_telegram_send_message(
                            hass,
                            current_data,
                            target=chat_id,
                            parse_mode="plain_text",
                            message=location_message,
                        )
                except Exception as err:  # pragma: no cover - defensive runtime guard
                    _LOGGER.exception("POM vehicle location command failed")
                    try:
                        await async_telegram_send_message(
                            hass,
                            current_data,
                            target=chat_id,
                            parse_mode="plain_text",
                            message=f"Araç konumu hazırlanırken hata oluştu: {err}",
                        )
                    except Exception:
                        _LOGGER.exception("Could not send POM vehicle location error to Telegram")
                return

            if not listener_enabled:
                # Deterministic slash commands are handled above. When AI listener
                # is disabled, do not route unknown text into AI/control flows.
                if str(user_message or "").strip().startswith("/"):
                    await async_telegram_send_message(
                        hass,
                        current_data,
                        target=chat_id,
                        parse_mode="plain_text",
                        message=build_telegram_report_commands_help(
                            current_data,
                            lang=get_telegram_report_language(current_data, user_message),
                        ),
                    )
                return

            if await async_handle_ai_vehicle_control_text_confirmation(
                hass,
                current_data,
                user_message=user_message,
                telegram_target=chat_id,
                send_telegram=True,
            ):
                return

            if await async_handle_ai_vehicle_suggestion_text(
                hass,
                current_data,
                user_message=user_message,
                telegram_target=chat_id,
                send_telegram=True,
            ):
                return

            if is_ai_vehicle_control_confirmation_text(user_message) or is_ai_vehicle_control_cancel_text(user_message):
                await hass.services.async_call(
                    "telegram_bot",
                    "send_message",
                    {
                        "target": chat_id,
                        "parse_mode": "plain_text",
                        "message": "Bekleyen bir araç kontrol onayı yok. Önce hangi işlemi yapmamı istediğini yazmalısın.",
                    },
                    blocking=True,
                )
                return

            direct_status_answer = await async_build_direct_vehicle_status_answer(hass, current_data, user_message)
            if direct_status_answer:
                await hass.services.async_call(
                    "telegram_bot",
                    "send_message",
                    {"target": chat_id, "parse_mode": "plain_text", "message": f"🤖 {get_ai_display_name(current_data)}\n\n{direct_status_answer}"},
                    blocking=True,
                )
                return

            if not is_indirect_vehicle_suggestion_statement(user_message):
                if await async_maybe_start_ai_vehicle_control(
                    hass,
                    current_data,
                    user_message=user_message,
                    telegram_target=chat_id,
                    send_telegram=True,
                ):
                    return

            if should_send_last_trip_map(user_message):
                report_info = get_latest_trip_report_info(hass)
                map_path = report_info.get("map_path") if report_info else ""
                if (not map_path) or (not Path(map_path).exists()):
                    fallback_paths = [DEFAULT_AUTO_TRIP_MAP_OUTPUT_PATH, DEFAULT_FINAL_TRIP_MAP_OUTPUT_PATH, DEFAULT_MANUAL_TRACKING_MAP_OUTPUT_PATH]
                    map_path = get_latest_existing_file(fallback_paths) or ""
                if not map_path:
                    await hass.services.async_call(
                        "telegram_bot",
                        "send_message",
                        {"target": chat_id, "parse_mode": "plain_text", "message": "Henüz gönderilebilecek kayıtlı bir son sürüş haritası yok."},
                        blocking=True,
                    )
                    return
                await hass.services.async_call(
                    "telegram_bot",
                    "send_photo",
                    {"target": chat_id, "file": map_path, "caption": "🗺️ Tesla AI - Son Sürüş Haritası"},
                    blocking=True,
                )
                return

            try:
                pre_suggestion_action = build_contextual_vehicle_suggestion_without_llm(
                    hass,
                    current_data,
                    user_message=user_message,
                    assistant_answer="",
                )
                answer = await async_generate_pom_ai_answer(
                    hass,
                    current_data,
                    user_message=user_message,
                    include_context=include_context,
                    telegram_target=chat_id,
                )
            except Exception as err:
                error_message = f"POM AI cevap üretemedi: {err}"
                _LOGGER.exception(error_message)
                await async_create_persistent_notification(
                    hass,
                    title="POM AI Telegram Listener - Hata",
                    message=error_message,
                    notification_id="pom_tesla_report_ai_telegram_listener_error",
                )
                if chat_id:
                    await hass.services.async_call(
                        "telegram_bot",
                        "send_message",
                        {
                            "target": chat_id,
                            "parse_mode": "plain_text",
                            "message": error_message,
                        },
                        blocking=True,
                )
                return

            hass.data.setdefault(DOMAIN, {})["ai_state"] = {
                "last_question": user_message,
                "last_answer": answer,
                "last_model": str(current_data.get(CONF_OPENAI_MODEL, DEFAULT_OPENAI_MODEL)),
                "last_at": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
                "last_source": "telegram_listener",
                "last_chat_id": chat_id,
                "last_user_id": user_id,
            }

            if pre_suggestion_action and not pre_suggestion_action.get("error"):
                pending = get_pending_ai_vehicle_suggestion_state(hass)
                pending.clear()
                pending.update({
                    "created_ts": datetime.now().timestamp(),
                    "target": chat_id,
                    "source_message": user_message,
                    "assistant_answer": answer,
                    "action": copy.deepcopy(pre_suggestion_action),
                })
            else:
                await async_store_contextual_vehicle_suggestion_if_any(
                    hass,
                    current_data,
                    user_message=user_message,
                    assistant_answer=answer,
                    telegram_target=chat_id,
                )
            remember_pom_ai_conversation_turn(hass, chat_id, user_message, answer)

            await hass.services.async_call(
                "telegram_bot",
                "send_message",
                {
                    "target": chat_id,
                    "parse_mode": "plain_text",
                    "message": f"🤖 {get_ai_display_name(current_data)}\n\n{answer}",
                },
                blocking=True,
            )

        async def _handle_telegram_command_event(event) -> None:
            """Convert Home Assistant telegram_command events into text events.

            HA's telegram_bot integration emits slash commands as telegram_command,
            not always as telegram_text. POM report commands are slash commands, so
            listening only to telegram_text makes /charge, /trip, or custom /berkan
            look like they are ignored when HA telegram_bot consumes getUpdates.
            """
            command_data = dict(getattr(event, "data", {}) or {})
            command = str(command_data.get("command") or "").strip()
            args = command_data.get("args")
            if isinstance(args, (list, tuple)):
                args_text = " ".join(str(item) for item in args if str(item).strip())
            else:
                args_text = str(args or "").strip()

            if command and not command.startswith("/"):
                command = f"/{command}"
            text = f"{command} {args_text}".strip() if args_text else command
            if not text:
                return

            command_data["text"] = text
            command_data.setdefault("raw_command", command)
            command_data.setdefault("raw_args", args_text)
            _LOGGER.info(
                "POM Telegram command event received. command=%s text=%s chat_id=%s",
                command,
                text,
                command_data.get("chat_id"),
            )
            await _handle_telegram_text_event(SimpleNamespace(data=command_data))

        unsub_telegram = hass.bus.async_listen("telegram_text", _handle_telegram_text_event)
        unsub_telegram_command = hass.bus.async_listen("telegram_command", _handle_telegram_command_event)
        unsub_telegram_callback = hass.bus.async_listen("telegram_callback", _handle_telegram_callback_event)
        entry.async_on_unload(unsub_telegram)
        entry.async_on_unload(unsub_telegram_command)
        entry.async_on_unload(unsub_telegram_callback)

        _LOGGER.info(
            "Tesla AI Telegram listener registered. entry=%s chat_id=%s allowed_user=%s ai_listener=%s command_listener=%s prefix_required=false",
            entry.entry_id,
            listener_chat_id,
            allowed_user_id or "everyone",
            listener_enabled,
            command_listener_enabled,
        )

        if is_builtin_telegram_enabled(config_data) and get_bool_option(
            config_data,
            CONF_BUILTIN_TELEGRAM_POLL_ENABLED,
            DEFAULT_BUILTIN_TELEGRAM_POLL_ENABLED,
        ):
            # Opt-in single-poller mode. Keep this disabled when Home Assistant's
            # telegram_bot integration is already polling the same bot token.
            poll_interval_seconds = max(
                3,
                int(
                    safe_float(
                        config_data.get(CONF_BUILTIN_TELEGRAM_POLL_INTERVAL_SECONDS),
                        DEFAULT_BUILTIN_TELEGRAM_POLL_INTERVAL_SECONDS,
                    )
                ),
            )

            async def _handle_builtin_telegram_poll_interval(_now) -> None:
                current_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, config_data)
                try:
                    await async_poll_builtin_telegram_updates(hass, entry.entry_id, current_data)
                except Exception as err:
                    _LOGGER.exception("POM built-in Telegram polling failed: %s", err)

            unsub_builtin_telegram_poll = async_track_time_interval(
                hass,
                _handle_builtin_telegram_poll_interval,
                timedelta(seconds=poll_interval_seconds),
            )
            entry.async_on_unload(unsub_builtin_telegram_poll)
            hass.async_create_task(
                async_poll_builtin_telegram_updates(
                    hass,
                    entry.entry_id,
                    get_live_entry_config_for_telegram(hass, entry, config_data),
                )
            )

            _LOGGER.info(
                "POM Tesla built-in Telegram polling enabled. entry=%s chat_id=%s interval=%ss",
                entry.entry_id,
                listener_chat_id or "-",
                poll_interval_seconds,
            )
        else:
            _LOGGER.info(
                "POM Tesla deterministic Telegram command listener uses Home Assistant telegram_text events. "
                "Built-in polling is disabled. entry=%s chat_id=%s ai_listener=%s",
                entry.entry_id,
                listener_chat_id or "-",
                listener_enabled,
            )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    try:
        dashboard_options = merged_dashboard_options_from_report_config(config_data)
        path = await async_write_tesla_dashboard(hass, dashboard_options)
        await async_show_dashboard_install_notification(hass, dashboard_options)
        _LOGGER.info("POM Tesla dashboard YAML generated at %s", path)
    except Exception as err:
        _LOGGER.warning("POM Tesla dashboard auto-generation skipped: %s", err)

    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Apply option changes in memory without forcing a Core/component reload.

    Panel saves such as Telegram group ID, currency, station presets and UI
    preferences must be lightweight. Reloading the config entry on every
    option update can look like a Home Assistant restart to users and can
    restart background listeners unnecessarily.
    """
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = get_entry_config(entry)
    _LOGGER.info(
        "Tesla AI options updated in memory without automatic reload. entry=%s",
        entry.entry_id,
    )


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Tesla AI config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok and DOMAIN in hass.data:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok






