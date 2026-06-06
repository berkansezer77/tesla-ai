"""Tesla AI management panel and API views.

alpha101 expands the app-like management surface with modular Settings, Charging Settings,
and Trip Report Settings. The panel is
kept separate from config_flow.py because Options Flow is not suitable for live
record editing, table selection, and dynamic add/update/delete workflows.
"""

from __future__ import annotations

import time
import os
import gc

import asyncio
import hashlib
import hmac
import secrets
import base64
import html
import json
import logging
import re
import shutil
import sys
import unicodedata
import zipfile
from io import BytesIO
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from PIL import Image, ImageDraw

from aiohttp import ClientError, FormData, web

from homeassistant.components import frontend
from homeassistant.components.http import HomeAssistantView
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import entity_registry as er
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .image_renderer import render_trip_report_png
from .trip_map_renderer import render_trip_map_png
from .location_map_renderer import render_vehicle_location_map_png
from .charging_report_renderer import render_charging_report_png, render_monthly_charge_cost_report_pngs
from .dashboard.helpers import (
    async_write_dashboard as async_write_tesla_dashboard,
    merged_options_from_report_config as merged_dashboard_options_from_report_config,
    apply_fullscreen_options_to_drive_dashboard,
)

from .const import (
    APP_LANGUAGE_EN,
    APP_LANGUAGE_TR,
    CHARGE_COST_LEDGER_FILENAME,
    CONF_APP_LANGUAGE,
    CONF_ASTOR_PRICE,
    CONF_AUTO_START_SPEED_THRESHOLD,
    CONF_AUTO_TRIP_TRACKING,
    CONF_BATTERY_LEVEL_ENTITY,
    CONF_ENERGY_REMAINING_ENTITY,
    CONF_SPEED_ENTITY,
    CONF_SHIFT_STATE_ENTITY,
    CONF_ODOMETER_ENTITY,
    CONF_ELEVATION_ENTITY,
    CONF_CLIMATE_ENTITY,
    CONF_CHARGING_ENTITY,
    CONF_CHARGE_ENERGY_ADDED_ENTITY,
    CONF_CHARGING_REPORT_MODE,
    CONF_CHARGE_PROVIDER_PRESETS,
    CONF_TELEGRAM_TARGET,
    CONF_BUILTIN_TELEGRAM_ENABLED,
    CONF_BUILTIN_TELEGRAM_BOT_TOKEN,
    CONF_BUILTIN_TELEGRAM_POLL_ENABLED,
    CONF_BUILTIN_TELEGRAM_POLL_INTERVAL_SECONDS,
    CONF_AI_TELEGRAM_TARGET,
    CONF_AI_TELEGRAM_LISTENER_ENABLED,
    CONF_AI_TELEGRAM_LISTENER_CHAT_ID,
    CONF_REPORT_CURRENCY,
    CONF_SHOW_AVERAGE_SPEED,
    CONF_SHOW_BATTERY,
    CONF_SHOW_CLIMATE,
    CONF_SHOW_CONSUMPTION,
    CONF_SHOW_COST,
    CONF_SHOW_DISTANCE,
    CONF_SHOW_DURATION,
    CONF_SHOW_ELEVATION,
    CONF_SHOW_ENERGY,
    CONF_SHOW_TRAFFIC,
    CONF_SHOW_TRIP_MAP,
    CONF_SUPERCHARGER_PRICE,
    CONF_TRIP_MAP_ENABLED,
    CONF_TRIP_MAP_MIN_MOVEMENT_METERS,
    CONF_TRIP_MAP_SAMPLE_INTERVAL_SECONDS,
    CONF_TRIP_MAP_SEND_SEPARATE_PNG,
    CONF_TRIP_MAP_TRACKER_ENTITY,
    CONF_LIVE_TRIP_ENABLED,
    CONF_LIVE_TRIP_UPDATE_INTERVAL_SECONDS,
    CONF_LIVE_TRIP_TRAFFIC_SPEED_THRESHOLD,
    CONF_LIVE_TRIP_FINISH_DELAY_SECONDS,
    CONF_LIVE_TRIP_MIN_DISTANCE_KM,
    CONF_LIVE_TRIP_IGNORE_SHORT_MANEUVERS,
    CONF_LIVE_TRIP_CANDIDATE_MIN_DISTANCE_KM,
    CONF_LIVE_TRIP_CANDIDATE_MIN_DURATION_SECONDS,
    CONF_LIVE_TRIP_AI_SEGMENT_DISTANCE_KM,
    CONF_ZES_PRICE,
    DEFAULT_APP_LANGUAGE,
    DEFAULT_ASTOR_PRICE,
    DEFAULT_AUTO_START_SPEED_THRESHOLD,
    DEFAULT_AUTO_TRIP_TRACKING,
    DEFAULT_CHARGING_REPORT_MODE,
    DEFAULT_CHARGE_PROVIDER_PRESETS,
    DEFAULT_BUILTIN_TELEGRAM_ENABLED,
    DEFAULT_BUILTIN_TELEGRAM_POLL_ENABLED,
    DEFAULT_BUILTIN_TELEGRAM_POLL_INTERVAL_SECONDS,
    DEFAULT_AI_TELEGRAM_LISTENER_ENABLED,
    DEFAULT_REPORT_CURRENCY,
    DEFAULT_SHOW_AVERAGE_SPEED,
    DEFAULT_SHOW_BATTERY,
    DEFAULT_SHOW_CLIMATE,
    DEFAULT_SHOW_CONSUMPTION,
    DEFAULT_SHOW_COST,
    DEFAULT_SHOW_DISTANCE,
    DEFAULT_SHOW_DURATION,
    DEFAULT_SHOW_ELEVATION,
    DEFAULT_SHOW_ENERGY,
    DEFAULT_SHOW_TRAFFIC,
    DEFAULT_SHOW_TRIP_MAP,
    DEFAULT_SUPERCHARGER_PRICE,
    DEFAULT_TRIP_MAP_ENABLED,
    DEFAULT_TRIP_MAP_MIN_MOVEMENT_METERS,
    DEFAULT_TRIP_MAP_SAMPLE_INTERVAL_SECONDS,
    DEFAULT_TRIP_MAP_SEND_SEPARATE_PNG,
    DEFAULT_TRIP_MAP_TRACKER_ENTITY,
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
    DEFAULT_ZES_PRICE,
    CONF_AI_ENABLED,
    CONF_OPENAI_API_KEY,
    CONF_OPENAI_MODEL,
    CONF_AI_NAME,
    CONF_AI_USER_ADDRESS,
    CONF_AI_SYSTEM_PROMPT,
    CONF_AI_MAX_OUTPUT_TOKENS,
    CONF_AI_TELEGRAM_INCLUDE_CONTEXT,
    CONF_AI_CONFIRM_OPTIONAL_CONTROLS,
    DEFAULT_AI_ENABLED,
    DEFAULT_OPENAI_MODEL,
    DEFAULT_AI_NAME,
    DEFAULT_AI_USER_ADDRESS,
    DEFAULT_AI_SYSTEM_PROMPT,
    DEFAULT_AI_MAX_OUTPUT_TOKENS,
    DEFAULT_AI_TELEGRAM_INCLUDE_CONTEXT,
    DEFAULT_AI_CONFIRM_OPTIONAL_CONTROLS,
    CONF_AI_PERSONALITY,
    CONF_AI_ANSWER_LENGTH,
    CONF_AI_CONTEXT_MODE,
    CONF_REVERSE_GEOCODING_ENABLED,
    CONF_REVERSE_GEOCODING_CACHE_MINUTES,
    CONF_REVERSE_GEOCODING_USE_IN_AI,
    DEFAULT_AI_PERSONALITY,
    DEFAULT_AI_ANSWER_LENGTH,
    DEFAULT_AI_CONTEXT_MODE,
    AI_PERSONALITY_PROFESSIONAL,
    AI_PERSONALITY_FRIENDLY,
    AI_PERSONALITY_FUNNY,
    AI_PERSONALITY_TURKISH_BUDDY,
    AI_PERSONALITY_LAZ_BLACK_SEA,
    DEFAULT_REVERSE_GEOCODING_ENABLED,
    DEFAULT_REVERSE_GEOCODING_CACHE_MINUTES,
    DEFAULT_REVERSE_GEOCODING_USE_IN_AI,
    CONF_AI_ALERTS_ENABLED,
    CONF_AI_ALERT_STYLE,
    CONF_AI_ALERT_COOLDOWN_MINUTES,
    CONF_AI_ALERT_LOW_BATTERY_ENABLED,
    CONF_AI_ALERT_LOW_BATTERY_THRESHOLD,
    CONF_AI_ALERT_POST_TRIP_SUMMARY_ENABLED,
    CONF_AI_TRIP_STORY_DETAIL_LEVEL,
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
    CONF_AI_MAIN_TESLA_ENTITY,
    CONF_AI_AUTO_DISCOVER_DEVICE_ENTITIES,
    CONF_AI_EXTRA_CONTEXT_ENTITIES,
    CONF_AI_EXCLUDED_CONTEXT_ENTITIES,
    DEFAULT_AI_MAIN_TESLA_ENTITY,
    DEFAULT_AI_AUTO_DISCOVER_DEVICE_ENTITIES,
    DEFAULT_AI_EXTRA_CONTEXT_ENTITIES,
    DEFAULT_AI_EXCLUDED_CONTEXT_ENTITIES,
    CONF_VEHICLE_ENTITY_MAP,
    DEFAULT_VEHICLE_ENTITY_MAP,
    CONF_PANEL_REPORT_ENTITY_MAP,
    DEFAULT_PANEL_REPORT_ENTITY_MAP,
    CONF_PANEL_AI_ENTITY_MAP,
    DEFAULT_PANEL_AI_ENTITY_MAP,
    CONF_PANEL_DASHBOARD_ENTITY_MAP,
    DEFAULT_PANEL_DASHBOARD_ENTITY_MAP,
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
    DOMAIN,
    REPORT_CURRENCY_OPTIONS,
    CONF_TELEGRAM_WEEKLY_TRIP_REPORT_ENABLED,
    CONF_TELEGRAM_MONTHLY_TRIP_REPORT_ENABLED,
    CONF_TELEGRAM_WEEKLY_CHARGE_REPORT_ENABLED,
    CONF_TELEGRAM_MONTHLY_CHARGE_REPORT_ENABLED,
    DEFAULT_TELEGRAM_WEEKLY_TRIP_REPORT_ENABLED,
    DEFAULT_TELEGRAM_MONTHLY_TRIP_REPORT_ENABLED,
    DEFAULT_TELEGRAM_WEEKLY_CHARGE_REPORT_ENABLED,
    DEFAULT_TELEGRAM_MONTHLY_CHARGE_REPORT_ENABLED,
    TRIP_MONTHLY_LEDGER_FILENAME,
)

_LOGGER = logging.getLogger(__name__)

PANEL_URL_PATH = "pom-tesla-report"
PANEL_ELEMENT_NAME = "pom-tesla-report-panel-alpha373"
PANEL_JS_FILE = "pom-tesla-report-panel-alpha373.js"
DASHBOARD_PANEL_VERSION = "2.2.0-alpha.373"

TELEGRAM_REPORT_COMMANDS_OPTION_KEY = "telegram_report_commands"
DEFAULT_TELEGRAM_REPORT_COMMANDS = {
    "charge_report": "charge",
    "trip_summary": "trip",
    "trip_all": "tripall",
    "trip_single": "single",
    "trip_last": "triplast",
}
API_CHARGE_RECORDS_URL = f"/api/{DOMAIN}/charge_records"
API_TRIP_RECORDS_URL = f"/api/{DOMAIN}/trip_records"
API_SETTINGS_URL = f"/api/{DOMAIN}/settings"
API_HEALTH_URL = f"/api/{DOMAIN}/health"
API_RECORD_MAP_URL = f"/api/{DOMAIN}/record_map"
API_TELEGRAM_TEST_URL = f"/api/{DOMAIN}/telegram_test"
API_AI_TEST_URL = f"/api/{DOMAIN}/ai_test"
API_DASHBOARD_MEDIA_URL = f"/api/{DOMAIN}/dashboard_media"
API_DASHBOARD_RESOURCES_URL = f"/api/{DOMAIN}/dashboard_resources"
API_BACKUP_EXPORT_URL = f"/api/{DOMAIN}/backup_export"
API_YOUTUBE_JSMPEG_PLAYER_URL = f"/{DOMAIN}/youtube_jsmpeg_player"
API_YOUTUBE_JSMPEG_STREAM_URL = f"/{DOMAIN}/youtube_jsmpeg_stream"
API_YOUTUBE_JSMPEG_HEALTH_URL = f"/{DOMAIN}/youtube_jsmpeg_health"
API_YOUTUBE_JSMPEG_WS_URL = f"/{DOMAIN}/youtube_jsmpeg_ws"

YOUTUBE_JSMPEG_TOKEN_SECRET_OPTION = "youtube_jsmpeg_signed_token_secret"

# Dashboard visual option keys are local here so panel registration does not
# import the dashboard helper package.
DASHBOARD_IMAGE_PARKED_KEY = "image_parked"
DASHBOARD_IMAGE_CHARGING_KEY = "image_charging"
DASHBOARD_IMAGE_DRIVING_KEY = "image_driving"
DASHBOARD_BUNDLED_IMAGE_PARKED = "/pom_tesla_report/dashboard/png/tesla.png"
DASHBOARD_BUNDLED_IMAGE_CHARGING = "/pom_tesla_report/dashboard/png/teslacharging.gif"
DASHBOARD_BUNDLED_IMAGE_DRIVING = "/pom_tesla_report/dashboard/png/tesladriving.gif"
DASHBOARD_BACKGROUND_UPLOAD_MAX_BYTES = 25 * 1024 * 1024
DASHBOARD_DRIVE_VEHICLE_IMAGE_KEY = "drive_dashboard_vehicle_image"
DASHBOARD_DRIVE_TIRE_PRESSURE_IMAGE_KEY = "drive_dashboard_tire_pressure_image"
DASHBOARD_YOUTUBE_DRIVING_BG_KEYS = {
    "youtube_driving_bg_enabled": False,
    "youtube_driving_bg_video": "",
    "youtube_driving_bg_start_seconds": 0,
    "youtube_driving_bg_mute": True,
    "youtube_driving_bg_loop": True,
    "youtube_driving_bg_quality": "480",
}

DASHBOARD_FULLSCREEN_KEYS = {
    "fullscreen_enabled": True,
    "fullscreen_hide_header": True,
    "fullscreen_hide_sidebar": True,
    "fullscreen_disable_scroll": True,
    "fullscreen_show_button": True,
    "rebuild_on_save": True,
}
DASHBOARD_TOP_SLOT_KEYS = {
    "top_left_slot_1": "elevation",
    "top_left_slot_2": "power",
    "top_center_slot": "speed",
    "top_right_slot_1": "battery_level",
    "top_right_slot_2": "est_range",
}
DASHBOARD_TOP_SLOT_TYPES = {
    "elevation": "Elevation",
    "power": "Power",
    "speed": "Speed",
    "battery_level": "Battery level",
    "est_range": "Estimated range",
    "rated_range": "Rated range",
    "energy_remaining": "Energy remaining",
    "inside_temp": "Inside temperature",
    "outside_temp": "Outside temperature",
    "battery_temp": "Battery/module temperature",
    "odometer": "Odometer",
    "battery_heater": "Battery heater",
    "empty": "Empty / hidden",
}
DASHBOARD_TOP_FONT_SCALE_KEYS = {
    "top_font_scale": 1.0,
    "top_left_font_scale": 1.0,
    "top_center_font_scale": 1.0,
    "top_right_font_scale": 1.0,
}
DASHBOARD_CENTER_SLOT_TYPES = {
    "speed": "Speed",
    "battery_level": "Battery level",
    "power": "Power",
    "energy_remaining": "Energy remaining",
    "empty": "Empty / hidden",
}
DASHBOARD_SIDEBAR_SLOT_KEYS = [f"sidebar_slot_{idx}" for idx in range(1, 9)]
DASHBOARD_SIDEBAR_DEFAULTS = [
    "flash_lights", "sentry", "honk", "fart", "windows", "empty", "empty", "empty"
]
DASHBOARD_SIDEBAR_ACTION_TYPES = {
    "empty": "Empty / hidden",
    "honk": "Honk horn",
    "flash_lights": "Flash lights",
    "sentry": "Sentry mode",
    "horn": "Horn",
    "fart": "Fart",
    "windows": "Windows",
    "rear_middle_seat_heater": "Rear middle seat heater",
    "rear_right_seat_heater": "Rear right seat heater",
    "rear_left_seat_heater": "Rear left seat heater",
    "right_seat_heater": "Right seat heater",
    "left_seat_heater": "Left seat heater",
    "charge_cable_lock": "Charge cable lock",
    "charge_port": "Charge port",
    "valet_mode": "Valet mode",
    "wake": "Wake vehicle",
    "home_entity_1": "Home entity 1",
    "home_entity_2": "Home entity 2",
}

DASHBOARD_LOCATION_DISPLAY_MODES = {
    "auto_short": "Auto short address",
    "neighbourhood": "Neighborhood / quarter",
    "suburb": "Suburb",
    "district": "District",
    "city": "City / town",
    "road": "Road / street",
}
DASHBOARD_BOTTOM_SLOT_KEYS = {
    "bottom_slot_1": "energy_remaining",
    "bottom_slot_2": "inside_temp",
    "bottom_slot_3": "battery_temp",
}
DASHBOARD_BOTTOM_SLOT_TYPES = {
    "energy_remaining": "Energy remaining",
    "inside_temp": "Inside temperature",
    "battery_temp": "Battery/module temperature",
    "outside_temp": "Outside temperature",
    "odometer": "Odometer",
    "battery_heater": "Battery heater",
    "empty": "Empty / hidden",
}
DASHBOARD_BOTTOM_TOGGLE_KEYS = {
    "show_bottom_map_toggle": True,
    "show_bottom_controls": True,
    "show_bottom_person_toggle": True,
    "show_bottom_charging": True,
    "show_bottom_person_track_1": True,
    "show_bottom_person_track_2": True,
    "show_bottom_person_track_3": True,
}
DASHBOARD_MAP_KEYS = {
    "tesla_map_hours_to_show": 1,
    "person_map_hours_to_show": 0,
}
DASHBOARD_MAP_THEME_KEY = "map_theme_mode"
DASHBOARD_MAP_THEME_DEFAULT = "dark"
DASHBOARD_MAP_THEME_MODES = {
    "dark": "Dark / eski okunabilir dashboard haritası",
    "light": "Light / gündüz haritası",
}
DASHBOARD_PERSON_TRACK_KEYS = {
    "person_track_enabled": True,
    "person_track_show_button": True,
    "person_track_hours_to_show": 15,
    "person_track_1_entity": "person.cavidan",
    "person_track_1_name": "Cavidan",
    "person_track_1_enabled": True,
    "person_track_2_entity": "person.ali",
    "person_track_2_name": "Ali",
    "person_track_2_enabled": True,
    "person_track_3_entity": "",
    "person_track_3_name": "Person 3",
    "person_track_3_enabled": False,
}


DASHBOARD_PERSON_TRACK_ROLES = {
    "dashboard_person_track_1",
    "dashboard_person_track_2",
    "dashboard_person_track_3",
}

DASHBOARD_SELF_OUTPUT_ENTITY_IDS = {
    "sensor.pom_tesla_dashboard_location_label",
    "sensor.pom_tesla_dashboard_last_charge",
    "sensor.pom_tesla_dashboard_person_track_1",
    "sensor.pom_tesla_dashboard_person_track_2",
    "sensor.pom_tesla_dashboard_person_track_3",
}


def _is_dashboard_self_output_entity_panel(entity_id: Any) -> bool:
    """Return true for POM dashboard output sensors that must not be selected as sources."""
    text = str(entity_id or "").strip().lower()
    return text in DASHBOARD_SELF_OUTPUT_ENTITY_IDS or text.startswith("sensor.pom_tesla_dashboard_person_track_")


def _is_invalid_dashboard_role_source_panel(role: Any, entity_id: Any) -> bool:
    """Block self-referential Dashboard Entity Manager assignments."""
    role_text = str(role or "").strip()
    if _is_dashboard_self_output_entity_panel(entity_id):
        return True
    return False


def _read_proc_status_kb(field: str) -> int:
    """Read a numeric kB field from /proc/self/status."""
    try:
        for line in Path("/proc/self/status").read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.startswith(field + ":"):
                parts = line.split()
                if len(parts) >= 2:
                    return int(float(parts[1]))
    except Exception:
        pass
    return 0


def _read_meminfo_kb() -> dict[str, int]:
    """Return selected /proc/meminfo values in kB."""
    result: dict[str, int] = {}
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8", errors="ignore").splitlines():
            if ":" not in line:
                continue
            key, rest = line.split(":", 1)
            parts = rest.split()
            if parts:
                try:
                    result[key] = int(float(parts[0]))
                except Exception:
                    pass
    except Exception:
        pass
    return result


def _ha_state_count(hass: HomeAssistant) -> int:
    try:
        return len(hass.states.async_all())
    except Exception:
        try:
            return len(hass.states.async_entity_ids())
        except Exception:
            return 0


def _pom_state_count(hass: HomeAssistant) -> int:
    try:
        return len([st.entity_id for st in hass.states.async_all() if str(st.entity_id).startswith(("sensor.pom_", "binary_sensor.pom_", "switch.pom_", "button.pom_", "select.pom_"))])
    except Exception:
        return 0


def _invalid_dashboard_self_reference_rows(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Find stored dashboard person-track self references in current options/config."""
    issues: list[dict[str, Any]] = []
    for key in ("person_track_1_entity", "person_track_2_entity", "person_track_3_entity"):
        entity_id = str(data.get(key) or "").strip()
        if entity_id and _is_dashboard_self_output_entity_panel(entity_id):
            issues.append({"where": key, "entity_id": entity_id, "kind": "legacy_option"})
    raw = data.get(CONF_PANEL_DASHBOARD_ENTITY_MAP)
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            role = str(item.get("role") or "").strip()
            entity_id = str(item.get("entity_id") or "").strip()
            if role in DASHBOARD_PERSON_TRACK_ROLES and entity_id and _is_dashboard_self_output_entity_panel(entity_id):
                issues.append({"where": "panel_dashboard_entity_map", "role": role, "entity_id": entity_id, "kind": "panel_store"})
    return issues


def _system_health_payload(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Return lightweight runtime diagnostics for the General screen.

    Memory is process-wide HA Core memory, not per-integration memory, because
    custom integrations run inside the Home Assistant Core Python process.
    """
    meminfo = _read_meminfo_kb()
    rss_kb = _read_proc_status_kb("VmRSS")
    hwm_kb = _read_proc_status_kb("VmHWM")
    total_kb = int(meminfo.get("MemTotal") or 0)
    available_kb = int(meminfo.get("MemAvailable") or 0)
    if not rss_kb:
        try:
            import resource
            rss_raw = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss or 0)
            # Linux returns kB; macOS may return bytes. HA OS/Linux is the target.
            rss_kb = int(rss_raw if rss_raw < 10_000_000 else rss_raw / 1024.0)
            hwm_kb = max(hwm_kb, rss_kb)
        except Exception:
            pass

    rss_mb = round(rss_kb / 1024.0, 1) if rss_kb else 0.0
    hwm_mb = round(hwm_kb / 1024.0, 1) if hwm_kb else 0.0
    total_mb = round(total_kb / 1024.0, 1) if total_kb else 0.0
    available_mb = round(available_kb / 1024.0, 1) if available_kb else 0.0
    rss_percent = round((rss_kb / total_kb * 100.0), 1) if total_kb else 0.0
    available_percent = round((available_kb / total_kb * 100.0), 1) if total_kb else 0.0

    # Lightweight in-memory trend. This is not persisted and resets on HA restart,
    # but it is enough to show sudden RAM growth before an OOM on low-RAM testers.
    now_ts = time.time()
    domain_data = hass.data.setdefault(DOMAIN, {})
    samples = domain_data.setdefault("panel_health_samples", [])
    if isinstance(samples, list):
        samples.append({"ts": now_ts, "rss_mb": rss_mb})
        samples[:] = [item for item in samples if isinstance(item, dict) and now_ts - float(item.get("ts") or 0) <= 600]
    else:
        samples = []
        domain_data["panel_health_samples"] = samples
    baseline = None
    for item in samples:
        try:
            if now_ts - float(item.get("ts") or 0) >= 240:
                baseline = item
                break
        except Exception:
            continue
    if baseline is None and samples:
        baseline = samples[0]
    trend_5m_mb = round(rss_mb - float((baseline or {}).get("rss_mb") or rss_mb), 1)
    trend_per_min_mb = round(trend_5m_mb / max(1.0, (now_ts - float((baseline or {}).get("ts") or now_ts)) / 60.0), 1) if baseline else 0.0

    self_refs = _invalid_dashboard_self_reference_rows(data)
    jobs = _panel_autofind_jobs(hass)
    job_snapshots = {
        key: _panel_autofind_job_snapshot(value)
        for key, value in jobs.items()
        if key in {"ai", "report", "dashboard"}
    }
    running_jobs = [
        key
        for key, value in job_snapshots.items()
        if str(value.get("status") or "") == "running"
    ]

    gc_counts = gc.get_count()
    warnings: list[str] = []
    status = "ok"
    severity = "normal"

    if self_refs:
        warnings.append(f"Self-reference guard blocked {len(self_refs)} dashboard source assignment(s).")
        status = "critical"
        severity = "critical"

    if total_kb:
        if rss_percent >= 88 or (available_percent <= 8 and available_mb <= 250):
            warnings.append("HA Core memory is in the critical range.")
            status = "critical"
            severity = "critical"
        elif rss_percent >= 72 or (available_percent <= 12 and available_mb <= 350):
            warnings.append("HA Core memory is high; watch for growth.")
            if status != "critical":
                status = "warning"
                severity = "warning"
    else:
        if rss_mb >= 3200:
            warnings.append("HA Core process RSS is above 3.2 GB.")
            status = "critical"
            severity = "critical"
        elif rss_mb >= 2200:
            warnings.append("HA Core process RSS is above 2.2 GB.")
            status = "warning"
            severity = "warning"

    if running_jobs:
        warnings.append("Auto Find is currently running: " + ", ".join(running_jobs))
        if status == "ok":
            status = "watch"
            severity = "watch"

    # Treat short-lived RAM jumps as a watch/warning signal instead of a red
    # critical alarm. Support-report and log-tail actions can briefly increase
    # RSS even when the system has plenty of free memory. A trend becomes
    # critical only when it is sustained and the absolute memory situation is
    # also unhealthy.
    trend_age_sec = max(0.0, now_ts - float((baseline or {}).get("ts") or now_ts)) if baseline else 0.0
    sustained_trend = trend_age_sec >= 180.0
    absolute_memory_pressure = bool(
        (total_kb and (rss_percent >= 55 or available_percent <= 22 or available_mb <= 900))
        or (not total_kb and rss_mb >= 2200)
    )
    if sustained_trend and absolute_memory_pressure and (trend_5m_mb >= 650 or trend_per_min_mb >= 160):
        warnings.append(f"Sustained RAM growth detected: +{trend_5m_mb} MB recent trend.")
        status = "critical"
        severity = "critical"
    elif sustained_trend and (trend_5m_mb >= 280 or trend_per_min_mb >= 80):
        warnings.append(f"RAM growth detected: +{trend_5m_mb} MB recent trend.")
        if status != "critical":
            status = "warning"
            severity = "warning"
    elif trend_5m_mb >= 120 or trend_per_min_mb >= 80:
        warnings.append(f"Temporary RAM growth observed: +{trend_5m_mb} MB recent trend.")
        if status == "ok":
            status = "watch"
            severity = "watch"

    return {
        "status": status,
        "severity": severity,
        "status_label": {
            "ok": "Normal",
            "watch": "Watch",
            "warning": "Warning",
            "critical": "Critical",
        }.get(status, status),
        "red_alert": severity == "critical",
        "warning_alert": severity in {"warning", "watch"},
        "safe_mode_recommended": severity == "critical",
        "memory": {
            "rss_mb": rss_mb,
            "high_watermark_mb": hwm_mb,
            "total_mb": total_mb,
            "available_mb": available_mb,
            "rss_percent": rss_percent,
            "available_percent": available_percent,
            "note": "Process memory is Home Assistant Core memory, not per-integration memory.",
            "trend_5m_mb": trend_5m_mb,
            "trend_per_min_mb": trend_per_min_mb,
            "sample_count": len(samples) if isinstance(samples, list) else 0,
        },
        "counts": {
            "ha_entities": _ha_state_count(hass),
            "pom_entities": _pom_state_count(hass),
            "gc_generation_0": int(gc_counts[0]),
            "gc_generation_1": int(gc_counts[1]),
            "gc_generation_2": int(gc_counts[2]),
        },
        "self_reference": {
            "issue_count": len(self_refs),
            "issues": self_refs[:20],
            "blocked_output_entities": sorted(DASHBOARD_SELF_OUTPUT_ENTITY_IDS),
        },
        "autofind": {
            "running": running_jobs,
            "jobs": job_snapshots,
        },
        "warnings": warnings[:12],
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }


DASHBOARD_PANEL_RESOURCE_ITEMS = [
    {
        "name": "POM Tesla Live Trip Card",
        "url_path": "/pom_tesla_report/pom-tesla-live-trip-card.js",
        "type": "module",
        "github": "Bundled with Tesla AI integration",
        "description": "Only POM-bundled Lovelace resource required by the current dashboard setup.",
    },
    {
        "name": "POM Tesla Trip Report Card",
        "url_path": "/pom_tesla_report/pom-tesla-trip-report-card.js",
        "type": "module",
        "github": "Bundled with Tesla AI integration",
        "description": "Stable Live Trip report card with AI popup panel. The stable resource also defines the alpha346 alias to reduce Lovelace custom-element/cache races.",
    },
    {
        "name": "POM Tesla Trip Report Card alpha346",
        "url_path": "/pom_tesla_report/pom-tesla-trip-report-card-alpha346.js",
        "type": "module",
        "github": "Bundled with Tesla AI integration",
        "description": "Versioned alpha346 bridge is bundled only as a fallback; dashboard YAML uses the stable custom:pom-tesla-trip-report-card type to avoid versioned-card load failures.",
    },
]

DASHBOARD_PANEL_CUSTOM_DEPENDENCIES = [
    {
        "name": "Button Card",
        "type": "custom:button-card",
        "github": "https://github.com/custom-cards/button-card",
        "description": "Required external Lovelace card for dashboard action/status buttons.",
        "local_checks": [
            "www/community/button-card/button-card.js",
            "www/community/button-card/button-card.js.gz",
        ],
    },
    {
        "name": "Card Mod",
        "type": "card_mod / custom:mod-card",
        "github": "https://github.com/thomasloven/lovelace-card-mod",
        "description": "Required external Lovelace dependency for dashboard styling and mod-card containers.",
        "local_checks": [
            "www/community/lovelace-card-mod/card-mod.js",
            "www/community/lovelace-card-mod/card-mod.js.gz",
            "www/community/card-mod/card-mod.js",
            "www/community/card-mod/card-mod.js.gz",
        ],
    },
]
API_TRIP_TEST_URL = f"/api/{DOMAIN}/trip_test"
API_LIVE_TRIP_TEST_URL = f"/api/{DOMAIN}/live_trip_test"
API_LIVE_TRIP_AI_TEST_URL = f"/api/{DOMAIN}/live_trip_ai_test"
API_LIVE_TRIP_AI_INTERVAL_URL = f"/api/{DOMAIN}/live_trip_ai_interval"
API_LIVE_TRIP_DEBUG_URL = f"/api/{DOMAIN}/live_trip_debug"
API_SYSTEM_LOGS_URL = f"/api/{DOMAIN}/system_logs"
API_CHARGE_TEST_URL = f"/api/{DOMAIN}/charge_test"
CONF_DASHBOARD_ENTITY_MAP = "dashboard_entity_map"
CONF_DASHBOARD_MAIN_ENTITY = "dashboard_main_entity"


def _charge_ledger_path(hass: HomeAssistant) -> Path:
    return Path(hass.config.path(CHARGE_COST_LEDGER_FILENAME))


def _trip_ledger_path(hass: HomeAssistant) -> Path:
    return Path(hass.config.path(TRIP_MONTHLY_LEDGER_FILENAME))


def _load_charge_ledger(hass: HomeAssistant) -> dict[str, Any]:
    default_payload = {"records": [], "last_monthly_report_key": ""}
    path = _charge_ledger_path(hass)
    try:
        if not path.exists():
            return dict(default_payload)
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return dict(default_payload)
        records = payload.get("records")
        if not isinstance(records, list):
            records = []
        return {
            "records": [item for item in records if isinstance(item, dict)],
            "last_monthly_report_key": str(payload.get("last_monthly_report_key") or "").strip(),
        }
    except Exception:
        _LOGGER.exception("Could not load POM Tesla charge ledger for panel")
        return dict(default_payload)


def _save_charge_ledger(hass: HomeAssistant, payload: dict[str, Any]) -> None:
    normalized = {
        "records": [item for item in list(payload.get("records") or []) if isinstance(item, dict)],
        "last_monthly_report_key": str(payload.get("last_monthly_report_key") or "").strip(),
    }
    _charge_ledger_path(hass).write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")


def _extract_records_from_payload(payload: Any) -> list[dict[str, Any]]:
    """Return records from known POM ledger shapes.

    The historical report code normally stores {"records": [...]}, but early
    test/dev files and manual backups may be list-rooted, month-keyed, or may
    use alternative keys. The app panel must be tolerant so the UI never shows
    a raw [object Object] error when one of those shapes is encountered.
    """
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []

    for key in ("records", "trips", "trip_records", "entries", "items"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]

    flattened: list[dict[str, Any]] = []
    for value in payload.values():
        if isinstance(value, list):
            flattened.extend(item for item in value if isinstance(item, dict))
        elif isinstance(value, dict):
            nested = value.get("records") or value.get("trips") or value.get("entries")
            if isinstance(nested, list):
                flattened.extend(item for item in nested if isinstance(item, dict))
    return flattened


def _load_trip_ledger(hass: HomeAssistant) -> dict[str, Any]:
    default_payload = {"records": []}
    path = _trip_ledger_path(hass)
    try:
        if not path.exists():
            return dict(default_payload)
        payload = json.loads(path.read_text(encoding="utf-8"))
        return {"records": _extract_records_from_payload(payload)}
    except Exception:
        _LOGGER.exception("Could not load POM Tesla trip ledger for panel")
        return dict(default_payload)


def _save_trip_ledger(hass: HomeAssistant, payload: dict[str, Any]) -> None:
    normalized = {"records": _extract_records_from_payload(payload)}
    _trip_ledger_path(hass).write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")


def _entry_config(hass: HomeAssistant) -> dict[str, Any]:
    entries = hass.config_entries.async_entries(DOMAIN)
    if not entries:
        return {}
    entry = entries[0]
    in_memory = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    merged = {
        **dict(entry.data or {}),
        **dict(entry.options or {}),
        **(dict(in_memory) if isinstance(in_memory, dict) else {}),
    }
    return _bind_report_options_from_vehicle_map_panel(merged)


def _app_language(hass: HomeAssistant) -> str:
    data = _entry_config(hass)
    raw = str(data.get(CONF_APP_LANGUAGE) or DEFAULT_APP_LANGUAGE).strip().lower()
    return APP_LANGUAGE_EN if raw.startswith("en") else APP_LANGUAGE_TR


def _live_trip_ai_segment_distance_for_panel(value: Any) -> float:
    """Normalize panel Live Trip AI comment interval to supported presets."""
    raw = _to_float(value, DEFAULT_LIVE_TRIP_AI_SEGMENT_DISTANCE_KM)
    allowed = [float(item) for item in LIVE_TRIP_AI_SEGMENT_DISTANCE_OPTIONS]
    if raw in allowed:
        return raw
    return min(allowed, key=lambda item: abs(item - raw)) if allowed else float(DEFAULT_LIVE_TRIP_AI_SEGMENT_DISTANCE_KM)


def _report_currency(hass: HomeAssistant) -> str:
    data = _entry_config(hass)
    return str(data.get(CONF_REPORT_CURRENCY) or DEFAULT_REPORT_CURRENCY).strip() or DEFAULT_REPORT_CURRENCY





def _supported_ai_personality_panel(value: Any) -> str:
    text = str(value or "").strip()
    if text == AI_PERSONALITY_TURKISH_BUDDY:
        return AI_PERSONALITY_LAZ_BLACK_SEA
    if text in {AI_PERSONALITY_PROFESSIONAL, AI_PERSONALITY_FRIENDLY, AI_PERSONALITY_FUNNY, AI_PERSONALITY_LAZ_BLACK_SEA}:
        return text
    return DEFAULT_AI_PERSONALITY


def _normalize_telegram_id_panel(value: Any) -> str:
    text = str(value or "").strip()
    if text.endswith(".0") and text.replace("-", "", 1).replace(".", "", 1).isdigit():
        text = text[:-2]
    return text


def _normalize_telegram_report_command_panel(value: Any, default: str = "") -> str:
    """Normalize user-editable slash command word, without leading slash."""
    text = str(value if value is not None else default or "").strip()
    if not text:
        text = str(default or "").strip()
    first = text.split()[0].strip() if text else ""
    if first.startswith("/"):
        first = first[1:]
    if "@" in first:
        first = first.split("@", 1)[0]
    first = first.strip().strip("/")
    allowed = []
    for char in first:
        if char.isalnum() or char in {"_", "-"}:
            allowed.append(char)
    cleaned = "".join(allowed).lower()
    fallback = str(default or "").strip().lstrip("/").split()[0].lower() if default else ""
    return cleaned or fallback


def _telegram_report_commands_payload(data: dict[str, Any]) -> dict[str, str]:
    raw = data.get(TELEGRAM_REPORT_COMMANDS_OPTION_KEY)
    if not isinstance(raw, dict):
        raw = {}
    return {
        key: _normalize_telegram_report_command_panel(raw.get(key), default)
        for key, default in DEFAULT_TELEGRAM_REPORT_COMMANDS.items()
    }


def _secret_last4(value: Any) -> str:
    text = str(value or "").strip()
    return text[-4:] if len(text) >= 4 else text


def _mask_secret_for_panel(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    return "••••••••" + _secret_last4(text)


def _is_masked_secret_from_panel(value: Any) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    return text.startswith("•") or text.startswith("*") or text.lower().startswith("configured")


def _backup_safe_settings_payload(settings: dict[str, Any]) -> dict[str, Any]:
    """Return settings suitable for export without live API keys/tokens."""
    try:
        safe = json.loads(json.dumps(settings or {}, ensure_ascii=False))
    except Exception:
        safe = dict(settings or {})
    ai = safe.get("ai_settings")
    if isinstance(ai, dict):
        ai.pop("openai_api_key", None)
    telegram = safe.get("telegram")
    if isinstance(telegram, dict):
        telegram.pop("builtin_telegram_bot_token", None)
    dashboard_settings = safe.get("dashboard_settings")
    if isinstance(dashboard_settings, dict):
        dashboard_settings.pop(YOUTUBE_JSMPEG_TOKEN_SECRET_OPTION, None)
    safe.pop(YOUTUBE_JSMPEG_TOKEN_SECRET_OPTION, None)
    return safe


def _youtube_jsmpeg_signed_token(secret: Any, youtube_url: Any, quality: Any) -> str:
    secret_text = str(secret or "").strip()
    if not secret_text:
        return ""
    url_text = str(youtube_url or "").strip()
    quality_text = str(quality or "480").strip()
    message = f"{quality_text}\n{url_text}".encode("utf-8")
    return hmac.new(secret_text.encode("utf-8"), message, hashlib.sha256).hexdigest()


def _youtube_jsmpeg_token_secret(hass: HomeAssistant) -> str:
    return str(_entry_config(hass).get(YOUTUBE_JSMPEG_TOKEN_SECRET_OPTION) or "").strip()


def _ensure_youtube_jsmpeg_token_secret_in_options(hass: HomeAssistant, merged_options: dict[str, Any]) -> dict[str, Any]:
    """Ensure a per-install internal token secret exists for iframe/WebSocket URLs."""
    current = dict(merged_options or {})
    if str(current.get(YOUTUBE_JSMPEG_TOKEN_SECRET_OPTION) or "").strip():
        return current

    entries = hass.config_entries.async_entries(DOMAIN)
    if not entries:
        return current

    entry = entries[0]
    existing = {
        **dict(entry.data or {}),
        **dict(entry.options or {}),
        **current,
    }
    secret_value = str(existing.get(YOUTUBE_JSMPEG_TOKEN_SECRET_OPTION) or "").strip()
    if not secret_value:
        secret_value = secrets.token_urlsafe(32)
        updated_options = dict(entry.options or {})
        updated_options[YOUTUBE_JSMPEG_TOKEN_SECRET_OPTION] = secret_value
        try:
            hass.config_entries.async_update_entry(entry, options=updated_options)
            hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
                **dict(entry.data or {}),
                **updated_options,
            }
        except Exception:
            _LOGGER.exception("Could not persist YouTube/JSMpeg signed token secret")

    current[YOUTUBE_JSMPEG_TOKEN_SECRET_OPTION] = secret_value
    return current


def _youtube_jsmpeg_validate_signed_token(hass: HomeAssistant, youtube_url: Any, quality: Any, token: Any) -> None:
    """Validate the signed token used by browser-driven no-auth video endpoints."""
    secret_value = _youtube_jsmpeg_token_secret(hass)
    if not secret_value:
        raise ValueError("YouTube background token is not initialized. Rebuild the Tesla AI dashboard.")
    expected = _youtube_jsmpeg_signed_token(secret_value, youtube_url, quality)
    provided = str(token or "").strip()
    if not expected or not provided or not hmac.compare_digest(provided, expected):
        raise ValueError("Invalid YouTube background token. Rebuild the Tesla AI dashboard.")


def _request_user_is_admin(request: web.Request) -> bool:
    """Return True only for Home Assistant admin users."""
    user = None
    try:
        user = request.get("hass_user")
    except Exception:
        user = None
    if user is None:
        try:
            user = request["hass_user"]
        except Exception:
            user = None
    return bool(getattr(user, "is_admin", False))


def _admin_required_response(request: web.Request) -> web.Response | None:
    if _request_user_is_admin(request):
        return None
    return web.json_response(
        {
            "success": False,
            "error": "admin_required",
            "message": "This Tesla AI management endpoint requires a Home Assistant admin user.",
        },
        status=403,
    )


def _redact_youtube_signed_tokens_from_text(text: str) -> str:
    """Redact dashboard iframe signed tokens before export/debug sharing."""
    return re.sub(r"([?&]token=)[^&\s\"'<>]+", r"\1REDACTED", str(text or ""))


def _telegram_diag_log(hass: HomeAssistant) -> list[dict[str, Any]]:
    return hass.data.setdefault(DOMAIN, {}).setdefault("telegram_diagnostics", [])


def _add_telegram_diag(hass: HomeAssistant, level: str, message: str, detail: Any = None) -> None:
    item = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "level": str(level or "info").lower(),
        "message": str(message or "").strip(),
    }
    if detail is not None:
        if isinstance(detail, (dict, list)):
            try:
                item["detail"] = json.dumps(detail, ensure_ascii=False)[:2000]
            except Exception:
                item["detail"] = str(detail)[:2000]
        else:
            item["detail"] = str(detail)[:2000]
    log = _telegram_diag_log(hass)
    log.insert(0, item)
    del log[80:]




def _ai_diag_log(hass: HomeAssistant) -> list[dict[str, Any]]:
    return hass.data.setdefault(DOMAIN, {}).setdefault("ai_diagnostics", [])


def _add_ai_diag(hass: HomeAssistant, level: str, message: str, detail: Any = None) -> None:
    item = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "level": str(level or "info").lower(),
        "message": str(message or "").strip(),
    }
    if detail is not None:
        if isinstance(detail, (dict, list)):
            try:
                item["detail"] = json.dumps(detail, ensure_ascii=False)[:3000]
            except Exception:
                item["detail"] = str(detail)[:3000]
        else:
            item["detail"] = str(detail)[:3000]
    log = _ai_diag_log(hass)
    log.insert(0, item)
    del log[80:]


def _ai_test_config_from_request(hass: HomeAssistant, ai_settings: Any = None) -> dict[str, Any]:
    data = dict(_entry_config(hass))
    if not isinstance(ai_settings, dict):
        return data
    mapping = {
        "ai_enabled": CONF_AI_ENABLED,
        "ai_personality": CONF_AI_PERSONALITY,
        "ai_answer_length": CONF_AI_ANSWER_LENGTH,
        "ai_context_mode": CONF_AI_CONTEXT_MODE,
        "ai_name": CONF_AI_NAME,
        "ai_user_address": CONF_AI_USER_ADDRESS,
        "openai_api_key": CONF_OPENAI_API_KEY,
        "openai_model": CONF_OPENAI_MODEL,
        "reverse_geocoding_enabled": CONF_REVERSE_GEOCODING_ENABLED,
        "reverse_geocoding_cache_minutes": CONF_REVERSE_GEOCODING_CACHE_MINUTES,
        "reverse_geocoding_use_in_ai": CONF_REVERSE_GEOCODING_USE_IN_AI,
        "ai_max_output_tokens": CONF_AI_MAX_OUTPUT_TOKENS,
        "ai_telegram_include_context": CONF_AI_TELEGRAM_INCLUDE_CONTEXT,
        "ai_confirm_optional_controls": CONF_AI_CONFIRM_OPTIONAL_CONTROLS,
    }
    for ui_key, conf_key in mapping.items():
        if ui_key in ai_settings:
            data[conf_key] = ai_settings.get(ui_key)
    if "openai_api_key" in ai_settings:
        raw_key = str(ai_settings.get("openai_api_key") or "").strip()
        if raw_key and not _is_masked_secret_from_panel(raw_key):
            data[CONF_OPENAI_API_KEY] = raw_key
        else:
            data[CONF_OPENAI_API_KEY] = str(_entry_config(hass).get(CONF_OPENAI_API_KEY) or "").strip()
    return data


def _ai_service_state(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    key = str(data.get(CONF_OPENAI_API_KEY) or "").strip()
    return {
        "ai_enabled": _to_bool(data.get(CONF_AI_ENABLED), DEFAULT_AI_ENABLED),
        "has_openai_key": bool(key),
        "model": str(data.get(CONF_OPENAI_MODEL) or DEFAULT_OPENAI_MODEL or "").strip(),
        "ai_name": str(data.get(CONF_AI_NAME) or DEFAULT_AI_NAME or "").strip(),
        "ai_user_address": str(data.get(CONF_AI_USER_ADDRESS) or DEFAULT_AI_USER_ADDRESS or "").strip(),
        "max_output_tokens": _positive_int(data.get(CONF_AI_MAX_OUTPUT_TOKENS), DEFAULT_AI_MAX_OUTPUT_TOKENS, minimum=128, maximum=4096),
    }


def _extract_panel_openai_text(response_data: dict[str, Any]) -> str:
    if not isinstance(response_data, dict):
        return ""
    output_text = response_data.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()
    pieces: list[str] = []
    output = response_data.get("output")
    if isinstance(output, list):
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if isinstance(content, list):
                for part in content:
                    if not isinstance(part, dict):
                        continue
                    text = part.get("text") or part.get("content")
                    if isinstance(text, str) and text.strip():
                        pieces.append(text.strip())
    if pieces:
        return "\n".join(pieces).strip()
    choices = response_data.get("choices")
    if isinstance(choices, list):
        for choice in choices:
            if not isinstance(choice, dict):
                continue
            message = choice.get("message")
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, str) and content.strip():
                    return content.strip()
    return ""


async def _panel_openai_test_call(hass: HomeAssistant, data: dict[str, Any], prompt: str) -> str:
    api_key = str(data.get(CONF_OPENAI_API_KEY) or "").strip()
    if not api_key:
        raise ValueError("OpenAI API key is empty.")
    model = str(data.get(CONF_OPENAI_MODEL) or DEFAULT_OPENAI_MODEL or "").strip() or DEFAULT_OPENAI_MODEL
    max_tokens = _positive_int(data.get(CONF_AI_MAX_OUTPUT_TOKENS), DEFAULT_AI_MAX_OUTPUT_TOKENS, minimum=128, maximum=4096)
    ai_name = str(data.get(CONF_AI_NAME) or DEFAULT_AI_NAME or "Tesla AI").strip() or "Tesla AI"
    system = (
        f"You are {ai_name}, the Tesla AI AI diagnostic assistant. "
        "Reply briefly. This is a panel connectivity test; do not operate vehicle controls."
    )
    payload = {
        "model": model,
        "input": [
            {"role": "system", "content": system},
            {"role": "user", "content": str(prompt or "Say OK.").strip()},
        ],
        "max_output_tokens": max_tokens,
    }
    session = async_get_clientsession(hass)
    try:
        async with session.post(
            "https://api.openai.com/v1/responses",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=60,
        ) as response:
            try:
                result = await response.json(content_type=None)
            except Exception:
                result = {"raw": await response.text()}
            if response.status >= 400:
                message = "OpenAI API request failed."
                if isinstance(result, dict):
                    err = result.get("error")
                    if isinstance(err, dict):
                        message = str(err.get("message") or message)
                raise ValueError(f"{message} HTTP {response.status}")
    except ClientError as err:
        raise ValueError(f"OpenAI API connection failed: {err}") from err
    text = _extract_panel_openai_text(result if isinstance(result, dict) else {})
    if not text:
        raise ValueError("OpenAI API returned no readable text.")
    return text

def _telegram_test_config_from_request(hass: HomeAssistant, telegram: Any = None) -> dict[str, Any]:
    data = dict(_entry_config(hass))
    if not isinstance(telegram, dict):
        return data
    existing_group_id = _normalize_telegram_id_panel(
        data.get(CONF_AI_TELEGRAM_LISTENER_CHAT_ID)
        or data.get(CONF_AI_TELEGRAM_TARGET)
        or data.get(CONF_TELEGRAM_TARGET)
    )
    raw_group_value = (
        telegram.get("telegram_group_id")
        if "telegram_group_id" in telegram
        else telegram.get("group_id", existing_group_id)
    )
    group_id = _normalize_telegram_id_panel(raw_group_value)
    replies_enabled = _to_bool(telegram.get("replies_enabled", bool(group_id or existing_group_id)), bool(group_id or existing_group_id))
    data[CONF_BUILTIN_TELEGRAM_ENABLED] = _to_bool(
        telegram.get("builtin_telegram_enabled", data.get(CONF_BUILTIN_TELEGRAM_ENABLED)),
        DEFAULT_BUILTIN_TELEGRAM_ENABLED,
    )
    raw_bot_token = str(telegram.get("builtin_telegram_bot_token", "") or "").strip()
    if raw_bot_token and not _is_masked_secret_from_panel(raw_bot_token):
        data[CONF_BUILTIN_TELEGRAM_BOT_TOKEN] = raw_bot_token
    else:
        data[CONF_BUILTIN_TELEGRAM_BOT_TOKEN] = str(_entry_config(hass).get(CONF_BUILTIN_TELEGRAM_BOT_TOKEN) or data.get(CONF_BUILTIN_TELEGRAM_BOT_TOKEN, "") or "").strip()
    data[CONF_BUILTIN_TELEGRAM_POLL_ENABLED] = _to_bool(
        telegram.get("builtin_telegram_poll_enabled", data.get(CONF_BUILTIN_TELEGRAM_POLL_ENABLED)),
        DEFAULT_BUILTIN_TELEGRAM_POLL_ENABLED,
    )
    data[CONF_BUILTIN_TELEGRAM_POLL_INTERVAL_SECONDS] = _positive_int(
        telegram.get("builtin_telegram_poll_interval_seconds", data.get(CONF_BUILTIN_TELEGRAM_POLL_INTERVAL_SECONDS)),
        DEFAULT_BUILTIN_TELEGRAM_POLL_INTERVAL_SECONDS,
        minimum=1,
        maximum=3600,
    )
    data[CONF_TELEGRAM_TARGET] = group_id if replies_enabled else ""
    data[CONF_AI_TELEGRAM_TARGET] = group_id if replies_enabled else ""
    data[CONF_AI_TELEGRAM_LISTENER_CHAT_ID] = group_id
    data[CONF_AI_TELEGRAM_LISTENER_ENABLED] = _to_bool(
        telegram.get("ai_group_listener_enabled", data.get(CONF_AI_TELEGRAM_LISTENER_ENABLED)),
        DEFAULT_AI_TELEGRAM_LISTENER_ENABLED,
    )
    return data


def _telegram_service_state(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    token = str(data.get(CONF_BUILTIN_TELEGRAM_BOT_TOKEN) or "").strip()
    group_id = _normalize_telegram_id_panel(
        data.get(CONF_AI_TELEGRAM_LISTENER_CHAT_ID)
        or data.get(CONF_AI_TELEGRAM_TARGET)
        or data.get(CONF_TELEGRAM_TARGET)
    )
    return {
        "builtin_enabled": _to_bool(data.get(CONF_BUILTIN_TELEGRAM_ENABLED), DEFAULT_BUILTIN_TELEGRAM_ENABLED),
        "builtin_has_token": bool(token),
        "builtin_poll_enabled": _to_bool(data.get(CONF_BUILTIN_TELEGRAM_POLL_ENABLED), DEFAULT_BUILTIN_TELEGRAM_POLL_ENABLED),
        "ha_send_message_service": hass.services.has_service("telegram_bot", "send_message"),
        "group_id": group_id,
        "mode": "built_in" if _to_bool(data.get(CONF_BUILTIN_TELEGRAM_ENABLED), DEFAULT_BUILTIN_TELEGRAM_ENABLED) and token else "ha_telegram_service",
    }


async def _panel_telegram_api_call(
    hass: HomeAssistant,
    data: dict[str, Any],
    method: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    token = str(data.get(CONF_BUILTIN_TELEGRAM_BOT_TOKEN) or "").strip()
    if not token:
        raise ValueError("Built-in Telegram bot token is empty.")
    session = async_get_clientsession(hass)
    url = f"https://api.telegram.org/bot{token}/{method}"
    try:
        async with session.post(url, json=payload, timeout=30) as response:
            result = await response.json(content_type=None)
    except ClientError as err:
        raise ValueError(f"Telegram API request failed: {err}") from err
    except Exception as err:
        raise ValueError(f"Telegram API request failed: {err}") from err
    if not isinstance(result, dict):
        raise ValueError("Telegram API returned a non-object response.")
    if not result.get("ok"):
        raise ValueError(str(result.get("description") or result))
    return result

def _first_config_entry(hass: HomeAssistant):
    entries = hass.config_entries.async_entries(DOMAIN)
    return entries[0] if entries else None


def _normalize_currency(value: Any, *, default: str = DEFAULT_REPORT_CURRENCY) -> str:
    raw = str(value or default or DEFAULT_REPORT_CURRENCY).strip().upper()
    if raw == "TRY":
        return "TL"
    allowed = {str(item).upper() for item in REPORT_CURRENCY_OPTIONS}
    return raw if raw in allowed else default


def _normalize_provider_presets(value: Any, *, default_currency: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        value = []
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        unit_price = _to_float(item.get("unit_price", item.get("price")), 0.0)
        if unit_price <= 0:
            continue
        key = name.casefold()
        if key in seen:
            continue
        seen.add(key)
        currency = _normalize_currency(item.get("currency") or item.get("currency_label"), default=default_currency)
        result.append({
            "id": key,
            "name": name,
            "unit_price": round(unit_price, 4),
            "currency": currency,
        })
    return result[:50]




def _default_provider_presets_from_legacy(data: dict[str, Any], *, default_currency: str) -> list[dict[str, Any]]:
    """Build the three default price presets from legacy price keys.

    The app panel now treats station presets as the source for visual report
    cost cards. Legacy Supercharger/ZES/Astor price keys are still kept for
    backward compatibility, but the UI no longer exposes them separately.
    """
    defaults = [
        ("Supercharger", CONF_SUPERCHARGER_PRICE, DEFAULT_SUPERCHARGER_PRICE),
        ("ZES", CONF_ZES_PRICE, DEFAULT_ZES_PRICE),
        ("Astor", CONF_ASTOR_PRICE, DEFAULT_ASTOR_PRICE),
    ]
    return [
        {"name": name, "unit_price": round(_positive_float(data.get(key), default), 4), "currency": default_currency}
        for name, key, default in defaults
    ]


def _effective_provider_presets(data: dict[str, Any], *, default_currency: str) -> list[dict[str, Any]]:
    """Return station presets used by the panel and report renderers.

    Existing saved presets win. If the user has not saved any preset yet, we
    seed the list from the legacy Supercharger/ZES/Astor price references.
    """
    presets = _normalize_provider_presets(
        data.get(CONF_CHARGE_PROVIDER_PRESETS, DEFAULT_CHARGE_PROVIDER_PRESETS),
        default_currency=default_currency,
    )
    if presets:
        return presets
    return _normalize_provider_presets(_default_provider_presets_from_legacy(data, default_currency=default_currency), default_currency=default_currency)


def _trip_cost_presets(data: dict[str, Any], *, used_kwh: float) -> list[dict[str, Any]]:
    """Build up to three visual report cost presets from charging settings."""
    default_currency = _normalize_currency(data.get(CONF_REPORT_CURRENCY), default=DEFAULT_REPORT_CURRENCY)
    presets = _effective_provider_presets(data, default_currency=default_currency)[:3]
    return [
        {
            "name": str(item.get("name") or "").strip(),
            "unit_price": round(_to_float(item.get("unit_price", item.get("price")), 0.0), 2),
            "currency": _normalize_currency(item.get("currency") or item.get("currency_label"), default=default_currency),
            "cost": round(used_kwh * _to_float(item.get("unit_price", item.get("price")), 0.0), 2),
        }
        for item in presets
        if str(item.get("name") or "").strip()
    ]

def _to_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on", "enable", "enabled"}:
        return True
    if text in {"0", "false", "no", "off", "disable", "disabled"}:
        return False
    return default


def _positive_int(value: Any, default: int, *, minimum: int = 0, maximum: int = 86400) -> int:
    try:
        number = int(round(_to_float(value, float(default))))
    except Exception:
        number = default
    return max(minimum, min(maximum, number))


def _positive_float(value: Any, default: float, *, minimum: float = 0.0, maximum: float = 100000.0) -> float:
    number = _to_float(value, default)
    if not isinstance(number, (int, float)):
        number = default
    return max(minimum, min(maximum, float(number)))



VEHICLE_ROLE_LABELS_PANEL: dict[str, dict[str, str]] = {
    VEHICLE_ROLE_BATTERY_LEVEL: {"tr": "Batarya seviyesi", "en": "Battery level"},
    VEHICLE_ROLE_BATTERY_RANGE: {"tr": "Menzil", "en": "Battery range"},
    VEHICLE_ROLE_ENERGY_REMAINING: {"tr": "Kalan enerji", "en": "Energy remaining"},
    VEHICLE_ROLE_CHARGING_STATE: {"tr": "Şarj durumu", "en": "Charging state"},
    VEHICLE_ROLE_CHARGE_ENERGY_ADDED: {"tr": "Eklenen enerji", "en": "Charge energy added"},
    VEHICLE_ROLE_CHARGER_POWER: {"tr": "Şarj gücü", "en": "Charger power"},
    VEHICLE_ROLE_SPEED: {"tr": "Hız", "en": "Speed"},
    VEHICLE_ROLE_SHIFT_STATE: {"tr": "Vites / sürüş durumu", "en": "Shift state"},
    VEHICLE_ROLE_ODOMETER: {"tr": "Kilometre", "en": "Odometer"},
    VEHICLE_ROLE_ELEVATION: {"tr": "Rakım", "en": "Elevation"},
    VEHICLE_ROLE_CLIMATE: {"tr": "Klima", "en": "Climate"},
    VEHICLE_ROLE_INSIDE_TEMPERATURE: {"tr": "İç sıcaklık", "en": "Inside temperature"},
    VEHICLE_ROLE_OUTSIDE_TEMPERATURE: {"tr": "Dış sıcaklık", "en": "Outside temperature"},
    VEHICLE_ROLE_BATTERY_TEMPERATURE: {"tr": "Batarya sıcaklığı", "en": "Battery temperature"},
    VEHICLE_ROLE_TIRE_PRESSURE_FRONT_LEFT: {"tr": "Ön sol lastik basıncı", "en": "Front-left tire pressure"},
    VEHICLE_ROLE_TIRE_PRESSURE_FRONT_RIGHT: {"tr": "Ön sağ lastik basıncı", "en": "Front-right tire pressure"},
    VEHICLE_ROLE_TIRE_PRESSURE_REAR_LEFT: {"tr": "Arka sol lastik basıncı", "en": "Rear-left tire pressure"},
    VEHICLE_ROLE_TIRE_PRESSURE_REAR_RIGHT: {"tr": "Arka sağ lastik basıncı", "en": "Rear-right tire pressure"},
    VEHICLE_ROLE_DOOR_WINDOW: {"tr": "Kapı / cam durumu", "en": "Door / window state"},
    VEHICLE_ROLE_LOCK_STATE: {"tr": "Kilit durumu", "en": "Lock state"},
    VEHICLE_ROLE_LOCATION_TRACKER: {"tr": "Konum takip entity", "en": "Location tracker"},
    VEHICLE_ROLE_VEHICLE_STATE: {"tr": "Araç durumu", "en": "Vehicle state"},
    VEHICLE_ROLE_USER_PRESENT: {"tr": "Kullanıcı araçta mı", "en": "User present"},
    VEHICLE_ROLE_OTHER: {"tr": "Diğer", "en": "Other"},
}

VEHICLE_ROLE_DESCRIPTIONS_PANEL: dict[str, dict[str, str]] = {
    VEHICLE_ROLE_BATTERY_LEVEL: {"tr": "AI cevaplarında batarya yüzdesini ve düşük batarya uyarılarını besler.", "en": "Used for AI battery answers and low-battery alerts."},
    VEHICLE_ROLE_BATTERY_RANGE: {"tr": "Menzil soruları ve rapor bağlamı için kullanılır.", "en": "Used for range questions and report context."},
    VEHICLE_ROLE_ENERGY_REMAINING: {"tr": "kWh bazlı kalan enerji hesabı için kullanılır.", "en": "Used for remaining energy in kWh calculations."},
    VEHICLE_ROLE_CHARGING_STATE: {"tr": "Araç şarjda mı, kablo takılı mı gibi sorular için kullanılır.", "en": "Used to answer whether the car is charging or plugged in."},
    VEHICLE_ROLE_CHARGE_ENERGY_ADDED: {"tr": "Şarj raporunda eklenen kWh değerinin ana kaynağıdır.", "en": "Primary source for added kWh in charge reports."},
    VEHICLE_ROLE_CHARGER_POWER: {"tr": "Şarj eğrisi, anlık güç ve tepe güç hesabı için kullanılır.", "en": "Used for charge curve, live power, and peak power."},
    VEHICLE_ROLE_SPEED: {"tr": "Sürüş takibi ve hız soruları için kullanılır.", "en": "Used for trip tracking and speed questions."},
    VEHICLE_ROLE_SHIFT_STATE: {"tr": "Park/Drive/Reverse durumunu anlamak için kullanılır.", "en": "Used to understand Park/Drive/Reverse state."},
    VEHICLE_ROLE_ODOMETER: {"tr": "Sürüş mesafesi ve kilometre bilgisi için kullanılır.", "en": "Used for odometer and trip distance context."},
    VEHICLE_ROLE_ELEVATION: {"tr": "Raporlarda rakım ve rota farkı bilgisi için kullanılır.", "en": "Used for elevation and route elevation difference."},
    VEHICLE_ROLE_CLIMATE: {"tr": "Klima durumu, sıcaklık set değeri ve HVAC bilgileri için kullanılır.", "en": "Used for HVAC state, setpoint, and climate context."},
    VEHICLE_ROLE_INSIDE_TEMPERATURE: {"tr": "Kabin sıcaklığı soruları ve klima yorumları için kullanılır.", "en": "Used for cabin temperature and climate comments."},
    VEHICLE_ROLE_OUTSIDE_TEMPERATURE: {"tr": "Dış hava sıcaklığı ve klima yorumları için kullanılır.", "en": "Used for outside temperature and climate comments."},
    VEHICLE_ROLE_BATTERY_TEMPERATURE: {"tr": "Batarya sıcaklığı, hızlı şarj ve güvenlik yorumları için kullanılır.", "en": "Used for battery temperature, fast charging, and safety context."},
    VEHICLE_ROLE_TIRE_PRESSURE_FRONT_LEFT: {"tr": "Ön sol lastik basıncı uyarıları için kullanılır.", "en": "Used for front-left tire pressure alerts."},
    VEHICLE_ROLE_TIRE_PRESSURE_FRONT_RIGHT: {"tr": "Ön sağ lastik basıncı uyarıları için kullanılır.", "en": "Used for front-right tire pressure alerts."},
    VEHICLE_ROLE_TIRE_PRESSURE_REAR_LEFT: {"tr": "Arka sol lastik basıncı uyarıları için kullanılır.", "en": "Used for rear-left tire pressure alerts."},
    VEHICLE_ROLE_TIRE_PRESSURE_REAR_RIGHT: {"tr": "Arka sağ lastik basıncı uyarıları için kullanılır.", "en": "Used for rear-right tire pressure alerts."},
    VEHICLE_ROLE_DOOR_WINDOW: {"tr": "Kapı/cam açık mı soruları ve güvenlik uyarıları için kullanılır.", "en": "Used for door/window questions and security alerts."},
    VEHICLE_ROLE_LOCK_STATE: {"tr": "Araç kilit durumu ve güvenlik yorumları için kullanılır.", "en": "Used for lock state and security comments."},
    VEHICLE_ROLE_LOCATION_TRACKER: {"tr": "Araç nerede, harita, adres ve rota bağlamı için kullanılır.", "en": "Used for location, map, address, and route context."},
    VEHICLE_ROLE_VEHICLE_STATE: {"tr": "Araç online/asleep gibi genel durum bilgisi için kullanılır.", "en": "Used for general vehicle state such as online/asleep."},
    VEHICLE_ROLE_USER_PRESENT: {"tr": "Araçta biri var mı / kullanıcı araçta mı yorumları için kullanılır.", "en": "Used for occupancy or user-present context."},
    VEHICLE_ROLE_OTHER: {"tr": "AI bağlamına eklemek istediğin özel veya destekleyici entity.", "en": "Custom/supporting entity you want to include in AI context."},
}

ENTITY_CATEGORY_LABELS_PANEL: dict[str, dict[str, str]] = {
    "vehicle_controls": {"tr": "Araç Kontrolleri", "en": "Vehicle Controls"},
    "sensors": {"tr": "Sensörler", "en": "Sensors"},
    "diagnostics": {"tr": "Diagnostics", "en": "Diagnostics"},
    "teslamate": {"tr": "Teslamate", "en": "Teslamate"},
    "dashboard_top": {"tr": "Üst Alan", "en": "Top Area"},
    "dashboard_sidebar": {"tr": "Sidebar", "en": "Sidebar"},
    "dashboard_bottom": {"tr": "Bottom Bar", "en": "Bottom Bar"},
    "dashboard_map": {"tr": "Harita", "en": "Map"},
    "dashboard_charge_popup": {"tr": "Şarj Popup", "en": "Charge Popup"},
    "other": {"tr": "Diğer", "en": "Other"},
}

PANEL_ENTITY_SLOT_DEFINITIONS: list[dict[str, Any]] = [
    {
        "role": 'tessie_charge_switch',
        "category": 'vehicle_controls',
        "expected_entity": 'switch.pom_charge',
        "labels": {'tr': 'Şarj başlat/durdur', 'en': 'Charge switch'},
        "descriptions": {'tr': 'Şarjı başlatma/durdurma kontrolü ve şarj aktifliği için kullanılır.', 'en': 'Used to start/stop charging and identify the charging control switch.'},
        "aliases": ['charge start', 'charge stop', 'şarj başlat', 'şarj durdur'],
    },
    {
        "role": 'tessie_charge_cable_lock',
        "category": 'vehicle_controls',
        "expected_entity": 'lock.pom_charge_cable_lock',
        "labels": {'tr': 'Şarj kablo kilidi', 'en': 'Charge cable lock'},
        "descriptions": {'tr': 'Şarj kablosu kilit durumunu ve kablo kilitleme kontrolünü temsil eder.', 'en': 'Represents the charge cable lock state and cable lock control.'},
        "aliases": ['charge cable lock', 'kablo kilidi'],
    },
    {
        "role": 'tessie_charge_port_door',
        "category": 'vehicle_controls',
        "expected_entity": 'cover.pom_charge_port_door',
        "labels": {'tr': 'Şarj port kapağı', 'en': 'Charge port door'},
        "descriptions": {'tr': 'Şarj port kapağını açma/kapama kontrolü için kullanılır.', 'en': 'Used for opening and closing the charge port door.'},
        "aliases": ['charge port', 'şarj port'],
    },
    {
        "role": VEHICLE_ROLE_CLIMATE,
        "category": 'vehicle_controls',
        "expected_entity": 'climate.pom_climate',
        "labels": {'tr': 'Klima', 'en': 'Climate'},
        "descriptions": {'tr': 'Klima durumu, HVAC ve sıcaklık set değerleri için kullanılır.', 'en': 'Used for climate state, HVAC, and temperature setpoints.'},
        "aliases": ['hvac', 'klima'],
    },
    {
        "role": 'tessie_defrost_mode',
        "category": 'vehicle_controls',
        "expected_entity": 'switch.pom_defrost_mode',
        "labels": {'tr': 'Defrost modu', 'en': 'Defrost mode'},
        "descriptions": {'tr': 'Cam buğu/buz çözme modunu kontrol eder.', 'en': 'Controls windshield defrost/defog mode.'},
        "aliases": ['defrost', 'defog', 'buz çözme'],
    },
    {
        "role": 'tessie_flash_lights',
        "category": 'vehicle_controls',
        "expected_entity": 'button.pom_flash_lights',
        "labels": {'tr': 'Farları yak/söndür', 'en': 'Flash lights'},
        "descriptions": {'tr': 'Aracın farlarını kısa süreli yakıp söndürme komutudur.', 'en': 'Command used to flash the vehicle lights.'},
        "aliases": ['flash lights', 'far', 'ışık'],
    },
    {
        "role": 'tessie_frunk',
        "category": 'vehicle_controls',
        "expected_entity": 'cover.pom_frunk',
        "labels": {'tr': 'Ön bagaj', 'en': 'Frunk'},
        "descriptions": {'tr': 'Ön bagaj kapağı kontrolü için kullanılır.', 'en': 'Used for front trunk/frunk control.'},
        "aliases": ['front trunk', 'ön bagaj'],
    },
    {
        "role": 'tessie_homelink',
        "category": 'vehicle_controls',
        "expected_entity": 'button.pom_homelink',
        "labels": {'tr': 'HomeLink', 'en': 'HomeLink'},
        "descriptions": {'tr': 'HomeLink/garaj komutu için kullanılır.', 'en': 'Used for HomeLink/garage command.'},
        "aliases": ['garage', 'garaj'],
    },
    {
        "role": 'tessie_honk_horn',
        "category": 'vehicle_controls',
        "expected_entity": 'button.pom_honk_horn',
        "labels": {'tr': 'Korna çal', 'en': 'Honk horn'},
        "descriptions": {'tr': 'Aracın kornasını çalma komutudur.', 'en': 'Command used to honk the vehicle horn.'},
        "aliases": ['honk', 'horn', 'korna'],
    },
    {
        "role": 'tessie_keyless_driving',
        "category": 'vehicle_controls',
        "expected_entity": 'button.pom_keyless_driving',
        "labels": {'tr': 'Anahtarsız sürüş', 'en': 'Keyless driving'},
        "descriptions": {'tr': 'Uzaktan anahtarsız sürüş/çalıştırma komutu için kullanılır.', 'en': 'Used for remote keyless driving/start command.'},
        "aliases": ['keyless', 'remote start', 'anahtarsız'],
    },
    {
        "role": VEHICLE_ROLE_LOCK_STATE,
        "category": 'vehicle_controls',
        "expected_entity": 'lock.pom_lock',
        "labels": {'tr': 'Araç kilidi', 'en': 'Vehicle lock'},
        "descriptions": {'tr': 'Araç kilit durumu ve kilitle/aç komutları için kullanılır.', 'en': 'Used for vehicle lock state and lock/unlock commands.'},
        "aliases": ['lock', 'kilit'],
    },
    {
        "role": 'tessie_media_player',
        "category": 'vehicle_controls',
        "expected_entity": 'media_player.pom_media_player',
        "labels": {'tr': 'Medya oynatıcı', 'en': 'Media player'},
        "descriptions": {'tr': 'Araç medya oynatıcı durumunu ve medya kontrolünü temsil eder.', 'en': 'Represents vehicle media player state and media control.'},
        "aliases": ['media', 'oynatıcı'],
    },
    {
        "role": 'tessie_play_fart',
        "category": 'vehicle_controls',
        "expected_entity": 'button.pom_play_fart',
        "labels": {'tr': 'Fart modu', 'en': 'Play fart'},
        "descriptions": {'tr': 'Tesla eğlence/fart ses komutu için kullanılır.', 'en': 'Used for Tesla entertainment/fart sound command.'},
        "aliases": ['fart'],
    },
    {
        "role": 'tessie_seat_heater_left',
        "category": 'vehicle_controls',
        "expected_entity": 'select.pom_seat_heater_left',
        "labels": {'tr': 'Sol ön koltuk ısıtma', 'en': 'Left front seat heater'},
        "descriptions": {'tr': 'Sürücü/sol ön koltuk ısıtma seviyesini seçer.', 'en': 'Selects the driver/left-front seat heater level.'},
        "aliases": ['seat heater left', 'driver seat heater'],
    },
    {
        "role": 'tessie_seat_heater_right',
        "category": 'vehicle_controls',
        "expected_entity": 'select.pom_seat_heater_right',
        "labels": {'tr': 'Sağ ön koltuk ısıtma', 'en': 'Right front seat heater'},
        "descriptions": {'tr': 'Yolcu/sağ ön koltuk ısıtma seviyesini seçer.', 'en': 'Selects the passenger/right-front seat heater level.'},
        "aliases": ['seat heater right', 'passenger seat heater'],
    },
    {
        "role": 'tessie_seat_heater_rear_left',
        "category": 'vehicle_controls',
        "expected_entity": 'select.pom_seat_heater_rear_left',
        "labels": {'tr': 'Arka sol koltuk ısıtma', 'en': 'Rear-left seat heater'},
        "descriptions": {'tr': 'Arka sol koltuk ısıtma seviyesini seçer.', 'en': 'Selects the rear-left seat heater level.'},
        "aliases": ['rear left seat heater'],
    },
    {
        "role": 'tessie_seat_heater_rear_center',
        "category": 'vehicle_controls',
        "expected_entity": 'select.pom_seat_heater_rear_center',
        "labels": {'tr': 'Arka orta koltuk ısıtma', 'en': 'Rear-center seat heater'},
        "descriptions": {'tr': 'Arka orta koltuk ısıtma seviyesini seçer.', 'en': 'Selects the rear-center seat heater level.'},
        "aliases": ['rear center seat heater'],
    },
    {
        "role": 'tessie_seat_heater_rear_right',
        "category": 'vehicle_controls',
        "expected_entity": 'select.pom_seat_heater_rear_right',
        "labels": {'tr': 'Arka sağ koltuk ısıtma', 'en': 'Rear-right seat heater'},
        "descriptions": {'tr': 'Arka sağ koltuk ısıtma seviyesini seçer.', 'en': 'Selects the rear-right seat heater level.'},
        "aliases": ['rear right seat heater'],
    },
    {
        "role": 'tessie_sentry_mode',
        "category": 'vehicle_controls',
        "expected_entity": 'switch.pom_sentry_mode',
        "labels": {'tr': 'Sentry modu', 'en': 'Sentry mode'},
        "descriptions": {'tr': 'Sentry güvenlik modunu açma/kapama kontrolüdür.', 'en': 'Control used to enable/disable Sentry Mode.'},
        "aliases": ['sentry'],
    },
    {
        "role": 'tessie_steering_wheel_heater',
        "category": 'vehicle_controls',
        "expected_entity": 'switch.pom_steering_wheel_heater',
        "labels": {'tr': 'Direksiyon ısıtma', 'en': 'Steering wheel heater'},
        "descriptions": {'tr': 'Direksiyon ısıtmasını açma/kapama kontrolüdür.', 'en': 'Control used to enable/disable steering wheel heat.'},
        "aliases": ['steering wheel heater', 'direksiyon'],
    },
    {
        "role": 'tessie_trunk',
        "category": 'vehicle_controls',
        "expected_entity": 'cover.pom_trunk',
        "labels": {'tr': 'Bagaj', 'en': 'Trunk'},
        "descriptions": {'tr': 'Arka bagaj kapağı kontrolü için kullanılır.', 'en': 'Used for rear trunk control.'},
        "aliases": ['trunk', 'bagaj'],
    },
    {
        "role": 'tessie_valet_mode',
        "category": 'vehicle_controls',
        "expected_entity": 'switch.pom_valet_mode',
        "labels": {'tr': 'Valet modu', 'en': 'Valet mode'},
        "descriptions": {'tr': 'Valet modunu açma/kapama kontrolüdür.', 'en': 'Control used to enable/disable valet mode.'},
        "aliases": ['valet'],
    },
    {
        "role": 'tessie_vent_windows',
        "category": 'vehicle_controls',
        "expected_entity": 'cover.pom_vent_windows',
        "labels": {'tr': 'Cam havalandırma', 'en': 'Vent windows'},
        "descriptions": {'tr': 'Camları havalandırma/kapatma kontrolü için kullanılır.', 'en': 'Used for venting/closing windows.'},
        "aliases": ['vent windows', 'window vent', 'cam'],
    },
    {
        "role": 'tessie_wake',
        "category": 'vehicle_controls',
        "expected_entity": 'button.pom_wake',
        "labels": {'tr': 'Aracı uyandır', 'en': 'Wake vehicle'},
        "descriptions": {'tr': 'Uyuyan aracı uyandırma komutudur.', 'en': 'Command used to wake the sleeping vehicle.'},
        "aliases": ['wake', 'uyandır'],
    },
    {
        "role": VEHICLE_ROLE_BATTERY_LEVEL,
        "category": 'sensors',
        "expected_entity": 'sensor.pom_battery_level',
        "labels": {'tr': 'Batarya seviyesi', 'en': 'Battery level'},
        "descriptions": {'tr': 'Batarya yüzdesi ve düşük batarya yorumları için ana sensördür.', 'en': 'Primary sensor for battery percentage and low-battery comments.'},
        "aliases": ['soc', 'battery level'],
    },
    {
        "role": VEHICLE_ROLE_BATTERY_RANGE,
        "category": 'sensors',
        "expected_entity": 'sensor.pom_battery_range',
        "labels": {'tr': 'Menzil', 'en': 'Battery range'},
        "descriptions": {'tr': 'Güncel tahmini menzil soruları ve rapor bağlamı için kullanılır.', 'en': 'Used for current estimated range questions and report context.'},
        "aliases": ['range', 'menzil'],
    },
    {
        "role": 'tessie_battery_range_estimate',
        "category": 'sensors',
        "expected_entity": 'sensor.pom_battery_range_estimate',
        "labels": {'tr': 'Tahmini menzil', 'en': 'Estimated battery range'},
        "descriptions": {'tr': 'Tessie tahmini menzil değerini gösterir.', 'en': 'Shows Tessie estimated battery range.'},
        "aliases": ['estimated range', 'range estimate'],
    },
    {
        "role": 'tessie_battery_range_ideal',
        "category": 'sensors',
        "expected_entity": 'sensor.pom_battery_range_ideal',
        "labels": {'tr': 'İdeal menzil', 'en': 'Ideal battery range'},
        "descriptions": {'tr': 'İdeal/nominal menzil değerini gösterir.', 'en': 'Shows ideal/nominal battery range.'},
        "aliases": ['ideal range'],
    },
    {
        "role": VEHICLE_ROLE_CHARGE_ENERGY_ADDED,
        "category": 'sensors',
        "expected_entity": 'sensor.pom_charge_energy_added',
        "labels": {'tr': 'Eklenen enerji', 'en': 'Charge energy added'},
        "descriptions": {'tr': 'Şarj oturumunda eklenen kWh değerinin ana kaynağıdır.', 'en': 'Primary source for kWh added during a charge session.'},
        "aliases": ['energy added'],
    },
    {
        "role": VEHICLE_ROLE_CHARGER_POWER,
        "category": 'sensors',
        "expected_entity": 'sensor.pom_charger_power',
        "labels": {'tr': 'Şarj gücü', 'en': 'Charger power'},
        "descriptions": {'tr': 'Anlık şarj gücü ve şarj eğrisi için kullanılır.', 'en': 'Used for live charger power and charge curve.'},
        "aliases": ['charging power'],
    },
    {
        "role": VEHICLE_ROLE_CHARGING_STATE,
        "category": 'sensors',
        "expected_entity": 'binary_sensor.pom_charging',
        "labels": {'tr': 'Şarj oluyor mu', 'en': 'Charging state'},
        "descriptions": {'tr': 'Aracın şu anda şarj olup olmadığını gösterir.', 'en': 'Shows whether the car is currently charging.'},
        "aliases": ['charging', 'şarj oluyor'],
    },
    {
        "role": 'tessie_distance_to_arrival',
        "category": 'sensors',
        "expected_entity": 'sensor.pom_distance_to_arrival',
        "labels": {'tr': 'Varışa kalan mesafe', 'en': 'Distance to arrival'},
        "descriptions": {'tr': 'Navigasyon aktifken varış noktasına kalan mesafeyi gösterir.', 'en': 'Shows remaining distance to destination when navigation is active.'},
        "aliases": ['distance to arrival'],
    },
    {
        "role": VEHICLE_ROLE_INSIDE_TEMPERATURE,
        "category": 'sensors',
        "expected_entity": 'sensor.pom_inside_temperature',
        "labels": {'tr': 'İç sıcaklık', 'en': 'Inside temperature'},
        "descriptions": {'tr': 'Kabin sıcaklığı ve klima yorumları için kullanılır.', 'en': 'Used for cabin temperature and climate comments.'},
        "aliases": ['cabin temperature'],
    },
    {
        "role": VEHICLE_ROLE_OUTSIDE_TEMPERATURE,
        "category": 'sensors',
        "expected_entity": 'sensor.pom_outside_temperature',
        "labels": {'tr': 'Dış sıcaklık', 'en': 'Outside temperature'},
        "descriptions": {'tr': 'Dış hava sıcaklığı ve iklim yorumları için kullanılır.', 'en': 'Used for outside temperature and climate comments.'},
        "aliases": ['outside temp'],
    },
    {
        "role": VEHICLE_ROLE_SHIFT_STATE,
        "category": 'sensors',
        "expected_entity": 'sensor.pom_shift_state',
        "labels": {'tr': 'Vites / sürüş durumu', 'en': 'Shift state'},
        "descriptions": {'tr': 'Park/Drive/Reverse durumunu anlamak için kullanılır.', 'en': 'Used to understand Park/Drive/Reverse state.'},
        "aliases": ['gear', 'vites'],
    },
    {
        "role": VEHICLE_ROLE_SPEED,
        "category": 'sensors',
        "expected_entity": 'sensor.pom_speed',
        "labels": {'tr': 'Hız', 'en': 'Speed'},
        "descriptions": {'tr': 'Anlık hız, sürüş takibi ve hız soruları için kullanılır.', 'en': 'Used for current speed, trip tracking, and speed questions.'},
        "aliases": ['speed', 'hız'],
    },
    {
        "role": VEHICLE_ROLE_VEHICLE_STATE,
        "category": 'sensors',
        "expected_entity": 'binary_sensor.pom_status',
        "labels": {'tr': 'Araç durumu', 'en': 'Vehicle status'},
        "descriptions": {'tr': 'Aracın online/asleep gibi genel erişilebilirlik durumunu gösterir.', 'en': 'Shows general vehicle availability such as online/asleep.'},
        "aliases": ['status', 'online', 'asleep'],
    },
    {
        "role": 'tessie_time_to_arrival',
        "category": 'sensors',
        "expected_entity": 'sensor.pom_time_to_arrival',
        "labels": {'tr': 'Varışa kalan süre', 'en': 'Time to arrival'},
        "descriptions": {'tr': 'Navigasyon aktifken varışa kalan süreyi gösterir.', 'en': 'Shows time remaining to destination when navigation is active.'},
        "aliases": ['time to arrival', 'eta'],
    },
    {
        "role": 'tessie_traffic_delay',
        "category": 'sensors',
        "expected_entity": 'sensor.pom_traffic_delay',
        "labels": {'tr': 'Trafik gecikmesi', 'en': 'Traffic delay'},
        "descriptions": {'tr': 'Rota üzerindeki trafik gecikmesini gösterir.', 'en': 'Shows traffic delay on the active route.'},
        "aliases": ['traffic delay'],
    },
    {
        "role": VEHICLE_ROLE_USER_PRESENT,
        "category": 'sensors',
        "expected_entity": 'binary_sensor.pom_user_present',
        "labels": {'tr': 'Kullanıcı araçta mı', 'en': 'User present'},
        "descriptions": {'tr': 'Araçta kullanıcı/occupancy var mı bilgisini verir.', 'en': 'Shows whether user/occupancy is present in the vehicle.'},
        "aliases": ['user present', 'occupancy'],
    },
    {
        "role": 'tessie_auto_seat_climate_left',
        "category": 'diagnostics',
        "expected_entity": 'binary_sensor.pom_auto_seat_climate_left',
        "labels": {'tr': 'Sol otomatik koltuk iklimi', 'en': 'Left auto seat climate'},
        "descriptions": {'tr': 'Sol koltuk otomatik iklim/ısıtma durumunu gösterir.', 'en': 'Shows left seat automatic climate/heater state.'},
        "aliases": ['auto seat climate left'],
    },
    {
        "role": 'tessie_auto_seat_climate_right',
        "category": 'diagnostics',
        "expected_entity": 'binary_sensor.pom_auto_seat_climate_right',
        "labels": {'tr': 'Sağ otomatik koltuk iklimi', 'en': 'Right auto seat climate'},
        "descriptions": {'tr': 'Sağ koltuk otomatik iklim/ısıtma durumunu gösterir.', 'en': 'Shows right seat automatic climate/heater state.'},
        "aliases": ['auto seat climate right'],
    },
    {
        "role": 'tessie_auto_steering_wheel_heater',
        "category": 'diagnostics',
        "expected_entity": 'binary_sensor.pom_auto_steering_wheel_heater',
        "labels": {'tr': 'Otomatik direksiyon ısıtma', 'en': 'Auto steering wheel heater'},
        "descriptions": {'tr': 'Direksiyon ısıtmasının otomatik mod durumunu gösterir.', 'en': 'Shows automatic steering wheel heater state.'},
        "aliases": ['auto steering wheel heater'],
    },
    {
        "role": 'tessie_battery_heater',
        "category": 'diagnostics',
        "expected_entity": 'binary_sensor.pom_battery_heater',
        "labels": {'tr': 'Batarya ısıtıcısı', 'en': 'Battery heater'},
        "descriptions": {'tr': 'Batarya ısıtıcısının aktif olup olmadığını gösterir.', 'en': 'Shows whether the battery heater is active.'},
        "aliases": ['battery heater'],
    },
    {
        "role": VEHICLE_ROLE_BATTERY_TEMPERATURE,
        "category": 'diagnostics',
        "expected_entity": 'sensor.pom_battery_module_temperature_max',
        "labels": {'tr': 'Batarya modül sıcaklığı', 'en': 'Battery module temperature'},
        "descriptions": {'tr': 'En yüksek batarya modül sıcaklığı, hızlı şarj ve güvenlik yorumları için kullanılır.', 'en': 'Used for max battery module temperature, fast charging, and safety comments.'},
        "aliases": ['battery module temperature'],
    },
    {
        "role": 'tessie_battery_pack_current',
        "category": 'diagnostics',
        "expected_entity": 'sensor.pom_battery_pack_current',
        "labels": {'tr': 'Batarya paket akımı', 'en': 'Battery pack current'},
        "descriptions": {'tr': 'Batarya paketinden geçen anlık akımı gösterir.', 'en': 'Shows instantaneous battery pack current.'},
        "aliases": ['pack current'],
    },
    {
        "role": 'tessie_battery_pack_voltage',
        "category": 'diagnostics',
        "expected_entity": 'sensor.pom_battery_pack_voltage',
        "labels": {'tr': 'Batarya paket voltajı', 'en': 'Battery pack voltage'},
        "descriptions": {'tr': 'Batarya paket voltajını gösterir.', 'en': 'Shows battery pack voltage.'},
        "aliases": ['pack voltage'],
    },
    {
        "role": 'tessie_cabin_overheat_protection',
        "category": 'diagnostics',
        "expected_entity": 'binary_sensor.pom_cabin_overheat_protection',
        "labels": {'tr': 'Kabin aşırı ısınma koruması', 'en': 'Cabin overheat protection'},
        "descriptions": {'tr': 'Kabin aşırı ısınma korumasının etkin olup olmadığını gösterir.', 'en': 'Shows whether Cabin Overheat Protection is enabled.'},
        "aliases": ['cabin overheat protection'],
    },
    {
        "role": 'tessie_cabin_overheat_cooling',
        "category": 'diagnostics',
        "expected_entity": 'binary_sensor.pom_cabin_overheat_protection_actively_cooling',
        "labels": {'tr': 'Kabin aktif soğutma', 'en': 'Cabin actively cooling'},
        "descriptions": {'tr': 'Kabin aşırı ısınma korumasının aktif soğutma yapıp yapmadığını gösterir.', 'en': 'Shows whether Cabin Overheat Protection is actively cooling.'},
        "aliases": ['actively cooling'],
    },
    {
        "role": 'tessie_charge_cable',
        "category": 'diagnostics',
        "expected_entity": 'binary_sensor.pom_charge_cable',
        "labels": {'tr': 'Şarj kablosu', 'en': 'Charge cable'},
        "descriptions": {'tr': 'Şarj kablosunun takılı/algılanmış durumunu gösterir.', 'en': 'Shows whether the charge cable is connected/detected.'},
        "aliases": ['charge cable'],
    },
    {
        "role": 'tessie_charge_rate',
        "category": 'diagnostics',
        "expected_entity": 'sensor.pom_charge_rate',
        "labels": {'tr': 'Şarj hızı', 'en': 'Charge rate'},
        "descriptions": {'tr': 'Şarj sırasında menzil/mesafe bazlı şarj hızını gösterir.', 'en': 'Shows range/distance charge rate during charging.'},
        "aliases": ['charge rate'],
    },
    {
        "role": 'tessie_charger_current',
        "category": 'diagnostics',
        "expected_entity": 'sensor.pom_charger_current',
        "labels": {'tr': 'Şarj akımı', 'en': 'Charger current'},
        "descriptions": {'tr': 'Şarj cihazından çekilen akımı gösterir.', 'en': 'Shows current drawn from the charger.'},
        "aliases": ['charger current'],
    },
    {
        "role": 'tessie_charger_voltage',
        "category": 'diagnostics',
        "expected_entity": 'sensor.pom_charger_voltage',
        "labels": {'tr': 'Şarj voltajı', 'en': 'Charger voltage'},
        "descriptions": {'tr': 'Şarj voltajını gösterir.', 'en': 'Shows charger voltage.'},
        "aliases": ['charger voltage'],
    },
    {
        "role": 'tessie_dashcam',
        "category": 'diagnostics',
        "expected_entity": 'binary_sensor.pom_dashcam',
        "labels": {'tr': 'Dashcam', 'en': 'Dashcam'},
        "descriptions": {'tr': 'Dashcam kayıt/aktif durumunu gösterir.', 'en': 'Shows dashcam active/recording state.'},
        "aliases": ['dashcam'],
    },
    {
        "role": 'tessie_destination',
        "category": 'diagnostics',
        "expected_entity": 'sensor.pom_destination',
        "labels": {'tr': 'Hedef', 'en': 'Destination'},
        "descriptions": {'tr': 'Aktif navigasyon hedefini gösterir.', 'en': 'Shows active navigation destination.'},
        "aliases": ['destination'],
    },
    {
        "role": 'tessie_driver_temperature_setting',
        "category": 'diagnostics',
        "expected_entity": 'sensor.pom_driver_temperature_setting',
        "labels": {'tr': 'Sürücü sıcaklık ayarı', 'en': 'Driver temperature setting'},
        "descriptions": {'tr': 'Sürücü tarafı klima sıcaklık set değerini gösterir.', 'en': 'Shows driver-side climate temperature setpoint.'},
        "aliases": ['driver temperature'],
    },
    {
        "role": VEHICLE_ROLE_ENERGY_REMAINING,
        "category": 'diagnostics',
        "expected_entity": 'sensor.pom_energy_remaining',
        "labels": {'tr': 'Kalan enerji', 'en': 'Energy remaining'},
        "descriptions": {'tr': 'kWh bazlı kalan enerji hesabı için kullanılır.', 'en': 'Used for remaining energy in kWh calculations.'},
        "aliases": ['energy remaining'],
    },
    {
        "role": 'tessie_front_driver_door',
        "category": 'diagnostics',
        "expected_entity": 'binary_sensor.pom_front_driver_door',
        "labels": {'tr': 'Ön sürücü kapısı', 'en': 'Front driver door'},
        "descriptions": {'tr': 'Ön sürücü kapısının açık/kapalı durumunu gösterir.', 'en': 'Shows front driver door open/closed state.'},
        "aliases": ['front driver door'],
    },
    {
        "role": 'tessie_front_driver_window',
        "category": 'diagnostics',
        "expected_entity": 'binary_sensor.pom_front_driver_window',
        "labels": {'tr': 'Ön sürücü camı', 'en': 'Front driver window'},
        "descriptions": {'tr': 'Ön sürücü camının açık/kapalı durumunu gösterir.', 'en': 'Shows front driver window open/closed state.'},
        "aliases": ['front driver window'],
    },
    {
        "role": 'tessie_front_passenger_door',
        "category": 'diagnostics',
        "expected_entity": 'binary_sensor.pom_front_passenger_door',
        "labels": {'tr': 'Ön yolcu kapısı', 'en': 'Front passenger door'},
        "descriptions": {'tr': 'Ön yolcu kapısının açık/kapalı durumunu gösterir.', 'en': 'Shows front passenger door open/closed state.'},
        "aliases": ['front passenger door'],
    },
    {
        "role": 'tessie_front_passenger_window',
        "category": 'diagnostics',
        "expected_entity": 'binary_sensor.pom_front_passenger_window',
        "labels": {'tr': 'Ön yolcu camı', 'en': 'Front passenger window'},
        "descriptions": {'tr': 'Ön yolcu camının açık/kapalı durumunu gösterir.', 'en': 'Shows front passenger window open/closed state.'},
        "aliases": ['front passenger window'],
    },
    {
        "role": 'tessie_lifetime_energy_used',
        "category": 'diagnostics',
        "expected_entity": 'sensor.pom_lifetime_energy_used',
        "labels": {'tr': 'Toplam enerji kullanımı', 'en': 'Lifetime energy used'},
        "descriptions": {'tr': 'Aracın ömür boyu kullandığı toplam enerji değerini gösterir.', 'en': 'Shows lifetime total energy used by the vehicle.'},
        "aliases": ['lifetime energy'],
    },
    {
        "role": VEHICLE_ROLE_LOCATION_TRACKER,
        "category": 'diagnostics',
        "expected_entity": 'device_tracker.pom_location',
        "labels": {'tr': 'Konum', 'en': 'Location tracker'},
        "descriptions": {'tr': 'Araç konumu, harita, adres ve rota bağlamı için kullanılır.', 'en': 'Used for vehicle location, map, address, and route context.'},
        "aliases": ['location', 'konum'],
    },
    {
        "role": VEHICLE_ROLE_ODOMETER,
        "category": 'diagnostics',
        "expected_entity": 'sensor.pom_odometer',
        "labels": {'tr': 'Kilometre', 'en': 'Odometer'},
        "descriptions": {'tr': 'Toplam kilometre ve sürüş mesafesi bağlamı için kullanılır.', 'en': 'Used for total odometer and trip distance context.'},
        "aliases": ['odometer', 'kilometre'],
    },
    {
        "role": 'tessie_passenger_temperature_setting',
        "category": 'diagnostics',
        "expected_entity": 'sensor.pom_passenger_temperature_setting',
        "labels": {'tr': 'Yolcu sıcaklık ayarı', 'en': 'Passenger temperature setting'},
        "descriptions": {'tr': 'Yolcu tarafı klima sıcaklık set değerini gösterir.', 'en': 'Shows passenger-side climate temperature setpoint.'},
        "aliases": ['passenger temperature'],
    },
    {
        "role": 'tessie_phantom_drain',
        "category": 'diagnostics',
        "expected_entity": 'sensor.pom_phantom_drain',
        "labels": {'tr': 'Phantom drain', 'en': 'Phantom drain'},
        "descriptions": {'tr': 'Park halindeki enerji kaybını/phantom drain değerini gösterir.', 'en': 'Shows parked energy loss / phantom drain.'},
        "aliases": ['phantom drain'],
    },
    {
        "role": 'tessie_power',
        "category": 'diagnostics',
        "expected_entity": 'sensor.pom_power',
        "labels": {'tr': 'Güç', 'en': 'Power'},
        "descriptions": {'tr': 'Aracın anlık güç tüketim/üretim değerini gösterir.', 'en': 'Shows current vehicle power consumption/regeneration value.'},
        "aliases": ['power'],
    },
    {
        "role": 'tessie_preconditioning_enabled',
        "category": 'diagnostics',
        "expected_entity": 'binary_sensor.pom_preconditioning_enabled',
        "labels": {'tr': 'Ön koşullandırma', 'en': 'Preconditioning enabled'},
        "descriptions": {'tr': 'Batarya/klima ön koşullandırmasının aktif olup olmadığını gösterir.', 'en': 'Shows whether preconditioning is enabled.'},
        "aliases": ['preconditioning'],
    },
    {
        "role": 'tessie_rear_driver_door',
        "category": 'diagnostics',
        "expected_entity": 'binary_sensor.pom_rear_driver_door',
        "labels": {'tr': 'Arka sürücü kapısı', 'en': 'Rear driver door'},
        "descriptions": {'tr': 'Arka sürücü tarafı kapının açık/kapalı durumunu gösterir.', 'en': 'Shows rear driver-side door open/closed state.'},
        "aliases": ['rear driver door'],
    },
    {
        "role": 'tessie_rear_driver_window',
        "category": 'diagnostics',
        "expected_entity": 'binary_sensor.pom_rear_driver_window',
        "labels": {'tr': 'Arka sürücü camı', 'en': 'Rear driver window'},
        "descriptions": {'tr': 'Arka sürücü tarafı camın açık/kapalı durumunu gösterir.', 'en': 'Shows rear driver-side window open/closed state.'},
        "aliases": ['rear driver window'],
    },
    {
        "role": 'tessie_rear_passenger_door',
        "category": 'diagnostics',
        "expected_entity": 'binary_sensor.pom_rear_passenger_door',
        "labels": {'tr': 'Arka yolcu kapısı', 'en': 'Rear passenger door'},
        "descriptions": {'tr': 'Arka yolcu tarafı kapının açık/kapalı durumunu gösterir.', 'en': 'Shows rear passenger-side door open/closed state.'},
        "aliases": ['rear passenger door'],
    },
    {
        "role": 'tessie_rear_passenger_window',
        "category": 'diagnostics',
        "expected_entity": 'binary_sensor.pom_rear_passenger_window',
        "labels": {'tr': 'Arka yolcu camı', 'en': 'Rear passenger window'},
        "descriptions": {'tr': 'Arka yolcu tarafı camın açık/kapalı durumunu gösterir.', 'en': 'Shows rear passenger-side window open/closed state.'},
        "aliases": ['rear passenger window'],
    },
    {
        "role": 'tessie_route_tracker',
        "category": 'diagnostics',
        "expected_entity": 'device_tracker.pom_route',
        "labels": {'tr': 'Rota takip', 'en': 'Route tracker'},
        "descriptions": {'tr': 'Aktif rota/izleme bilgisini takip etmek için kullanılır.', 'en': 'Used to track active route information.'},
        "aliases": ['route'],
    },
    {
        "role": 'tessie_scheduled_charging_pending',
        "category": 'diagnostics',
        "expected_entity": 'binary_sensor.pom_scheduled_charging_pending',
        "labels": {'tr': 'Zamanlı şarj bekliyor', 'en': 'Scheduled charging pending'},
        "descriptions": {'tr': 'Zamanlı şarjın beklemede olup olmadığını gösterir.', 'en': 'Shows whether scheduled charging is pending.'},
        "aliases": ['scheduled charging'],
    },
    {
        "role": 'tessie_soc_at_arrival',
        "category": 'diagnostics',
        "expected_entity": 'sensor.pom_state_of_charge_at_arrival',
        "labels": {'tr': 'Varış batarya yüzdesi', 'en': 'State of charge at arrival'},
        "descriptions": {'tr': 'Navigasyon varış noktasındaki tahmini batarya yüzdesini gösterir.', 'en': 'Shows estimated state of charge at arrival.'},
        "aliases": ['soc at arrival'],
    },
    {
        "role": 'tessie_time_to_full_charge',
        "category": 'diagnostics',
        "expected_entity": 'sensor.pom_time_to_full_charge',
        "labels": {'tr': 'Tam şarja kalan süre', 'en': 'Time to full charge'},
        "descriptions": {'tr': 'Şarj sırasında tam doluma kalan süreyi gösterir.', 'en': 'Shows time remaining until full charge.'},
        "aliases": ['time to full charge'],
    },
    {
        "role": VEHICLE_ROLE_TIRE_PRESSURE_FRONT_LEFT,
        "category": 'diagnostics',
        "expected_entity": 'sensor.pom_tire_pressure_front_left',
        "labels": {'tr': 'Ön sol lastik basıncı', 'en': 'Front-left tire pressure'},
        "descriptions": {'tr': 'Ön sol lastik basıncı uyarıları için kullanılır.', 'en': 'Used for front-left tire pressure alerts.'},
        "aliases": ['front left tire'],
    },
    {
        "role": VEHICLE_ROLE_TIRE_PRESSURE_FRONT_RIGHT,
        "category": 'diagnostics',
        "expected_entity": 'sensor.pom_tire_pressure_front_right',
        "labels": {'tr': 'Ön sağ lastik basıncı', 'en': 'Front-right tire pressure'},
        "descriptions": {'tr': 'Ön sağ lastik basıncı uyarıları için kullanılır.', 'en': 'Used for front-right tire pressure alerts.'},
        "aliases": ['front right tire'],
    },
    {
        "role": VEHICLE_ROLE_TIRE_PRESSURE_REAR_LEFT,
        "category": 'diagnostics',
        "expected_entity": 'sensor.pom_tire_pressure_rear_left',
        "labels": {'tr': 'Arka sol lastik basıncı', 'en': 'Rear-left tire pressure'},
        "descriptions": {'tr': 'Arka sol lastik basıncı uyarıları için kullanılır.', 'en': 'Used for rear-left tire pressure alerts.'},
        "aliases": ['rear left tire'],
    },
    {
        "role": VEHICLE_ROLE_TIRE_PRESSURE_REAR_RIGHT,
        "category": 'diagnostics',
        "expected_entity": 'sensor.pom_tire_pressure_rear_right',
        "labels": {'tr': 'Arka sağ lastik basıncı', 'en': 'Rear-right tire pressure'},
        "descriptions": {'tr': 'Arka sağ lastik basıncı uyarıları için kullanılır.', 'en': 'Used for rear-right tire pressure alerts.'},
        "aliases": ['rear right tire'],
    },
    {
        "role": 'tessie_tire_pressure_warning_front_left',
        "category": 'diagnostics',
        "expected_entity": 'binary_sensor.pom_tire_pressure_warning_front_left',
        "labels": {'tr': 'Ön sol lastik uyarısı', 'en': 'Front-left tire warning'},
        "descriptions": {'tr': 'Ön sol lastik basınç uyarısını gösterir.', 'en': 'Shows front-left tire pressure warning.'},
        "aliases": ['front left tire warning'],
    },
    {
        "role": 'tessie_tire_pressure_warning_front_right',
        "category": 'diagnostics',
        "expected_entity": 'binary_sensor.pom_tire_pressure_warning_front_right',
        "labels": {'tr': 'Ön sağ lastik uyarısı', 'en': 'Front-right tire warning'},
        "descriptions": {'tr': 'Ön sağ lastik basınç uyarısını gösterir.', 'en': 'Shows front-right tire pressure warning.'},
        "aliases": ['front right tire warning'],
    },
    {
        "role": 'tessie_tire_pressure_warning_rear_left',
        "category": 'diagnostics',
        "expected_entity": 'binary_sensor.pom_tire_pressure_warning_rear_left',
        "labels": {'tr': 'Arka sol lastik uyarısı', 'en': 'Rear-left tire warning'},
        "descriptions": {'tr': 'Arka sol lastik basınç uyarısını gösterir.', 'en': 'Shows rear-left tire pressure warning.'},
        "aliases": ['rear left tire warning'],
    },
    {
        "role": 'tessie_tire_pressure_warning_rear_right',
        "category": 'diagnostics',
        "expected_entity": 'binary_sensor.pom_tire_pressure_warning_rear_right',
        "labels": {'tr': 'Arka sağ lastik uyarısı', 'en': 'Rear-right tire warning'},
        "descriptions": {'tr': 'Arka sağ lastik basınç uyarısını gösterir.', 'en': 'Shows rear-right tire pressure warning.'},
        "aliases": ['rear right tire warning'],
    },
    {
        "role": 'tessie_trip_charging',
        "category": 'diagnostics',
        "expected_entity": 'binary_sensor.pom_trip_charging',
        "labels": {'tr': 'Sürüşte şarj', 'en': 'Trip charging'},
        "descriptions": {'tr': 'Sürüş/rota sırasında şarj ilişkili durumu gösterir.', 'en': 'Shows trip/route-related charging state.'},
        "aliases": ['trip charging'],
    },
    {
        "role": VEHICLE_ROLE_DOOR_WINDOW,
        "category": 'diagnostics',
        "expected_entity": '',
        "labels": {'tr': 'Genel kapı/cam durumu', 'en': 'General door/window state'},
        "descriptions": {'tr': 'Eski yapıdan gelen genel kapı/cam rolüdür; özel kapı/cam slotları yukarıdadır.', 'en': 'Legacy general door/window role; specific door/window slots are listed above.'},
        "aliases": ['door window'],
    },
    {
        "role": 'teslamate_model',
        "category": 'teslamate',
        "expected_entity": 'sensor.tesla_model',
        "labels": {'tr': 'Tesla modeli', 'en': 'Tesla model'},
        "descriptions": {'tr': 'Teslamate üzerinden araç model bilgisini gösterir.', 'en': 'Shows vehicle model from Teslamate.'},
        "aliases": ['tesla model'],
    },
    {
        "role": VEHICLE_ROLE_ELEVATION,
        "category": 'teslamate',
        "expected_entity": 'sensor.tesla_elevation',
        "labels": {'tr': 'Rakım', 'en': 'Elevation'},
        "descriptions": {'tr': 'Teslamate rakım/elevation verisini gösterir.', 'en': 'Shows Teslamate elevation data.'},
        "aliases": ['tesla elevation'],
    },
    {
        "role": 'teslamate_version',
        "category": 'teslamate',
        "expected_entity": 'sensor.tesla_version',
        "labels": {'tr': 'Yazılım sürümü', 'en': 'Software version'},
        "descriptions": {'tr': 'Tesla yazılım sürümünü gösterir.', 'en': 'Shows Tesla software version.'},
        "aliases": ['software version', 'tesla version'],
    },
    {
        "role": 'teslamate_exterior_color',
        "category": 'teslamate',
        "expected_entity": 'sensor.tesla_exterior_color',
        "labels": {'tr': 'Dış renk', 'en': 'Exterior color'},
        "descriptions": {'tr': 'Araç dış renk bilgisini gösterir.', 'en': 'Shows vehicle exterior color.'},
        "aliases": ['exterior color'],
    },
]

PANEL_SLOT_BY_ROLE = {str(item["role"]): item for item in PANEL_ENTITY_SLOT_DEFINITIONS}
PANEL_EXPECTED_ROLE_BY_ENTITY = {str(item.get("expected_entity") or "").lower(): str(item["role"]) for item in PANEL_ENTITY_SLOT_DEFINITIONS if item.get("expected_entity")}
PANEL_ACCEPTED_ENTITY_ROLES = set(VEHICLE_ENTITY_ROLES) | set(PANEL_SLOT_BY_ROLE)
AI_ENTITY_MANAGER_ROLES: list[str] = []
_seen_ai_panel_roles: set[str] = set()
for _slot in PANEL_ENTITY_SLOT_DEFINITIONS:
    _role = str(_slot.get("role") or "")
    if _role and _role != VEHICLE_ROLE_OTHER and _role not in _seen_ai_panel_roles:
        AI_ENTITY_MANAGER_ROLES.append(_role)
        _seen_ai_panel_roles.add(_role)
for _role in VEHICLE_ENTITY_ROLES:
    if _role != VEHICLE_ROLE_OTHER and _role not in _seen_ai_panel_roles:
        AI_ENTITY_MANAGER_ROLES.append(_role)
        _seen_ai_panel_roles.add(_role)
del _seen_ai_panel_roles

REPORT_ENTITY_MANAGER_ROLES: list[str] = [
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
    VEHICLE_ROLE_VEHICLE_STATE,
]

REPORT_LEGACY_OPTION_BY_ROLE: dict[str, str] = {
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

REPORT_SOURCE_LABEL_BY_ROLE: dict[str, str] = {
    VEHICLE_ROLE_BATTERY_LEVEL: "Battery level",
    VEHICLE_ROLE_ENERGY_REMAINING: "Energy remaining",
    VEHICLE_ROLE_SPEED: "Speed",
    VEHICLE_ROLE_SHIFT_STATE: "Shift state",
    VEHICLE_ROLE_ODOMETER: "Odometer",
    VEHICLE_ROLE_ELEVATION: "Elevation",
    VEHICLE_ROLE_CLIMATE: "Climate",
    VEHICLE_ROLE_CHARGING_STATE: "Charging state",
    VEHICLE_ROLE_CHARGE_ENERGY_ADDED: "Charge energy added",
    VEHICLE_ROLE_LOCATION_TRACKER: "Location tracker",
    VEHICLE_ROLE_VEHICLE_STATE: "Vehicle state / sleep status",
}



def _normalize_panel_report_entity_map_panel(raw: Any) -> list[dict[str, Any]]:
    """Normalize Flow-independent panel Reports Entity Manager store."""
    rows: list[dict[str, Any]] = []
    if not isinstance(raw, list):
        return rows
    seen_roles: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "").strip()
        entity_id = str(item.get("entity_id") or "").strip()
        if not role or role not in REPORT_ENTITY_MANAGER_ROLES or not entity_id or role in seen_roles:
            continue
        rows.append({
            "role": role,
            "entity_id": entity_id,
            "label": str(item.get("label") or item.get("name") or "").strip(),
            "source": str(item.get("source") or "panel_report_entity_map").strip(),
            **_match_meta_from_item(item),
            "use_report": True,
            "use_ai": _to_bool(item.get("use_ai"), False),
            "use_alerts": _to_bool(item.get("use_alerts"), False),
            "use_map": _to_bool(item.get("use_map"), role == VEHICLE_ROLE_LOCATION_TRACKER),
        })
        seen_roles.add(role)
    return rows


def _panel_report_role_entity(data: dict[str, Any], role: str) -> str:
    """Return panel report store entity for role."""
    for item in _normalize_panel_report_entity_map_panel(data.get(CONF_PANEL_REPORT_ENTITY_MAP, DEFAULT_PANEL_REPORT_ENTITY_MAP)):
        if item.get("role") == role:
            return str(item.get("entity_id") or "").strip()
    return ""


def _panel_report_store_exists(data: dict[str, Any]) -> bool:
    return bool(_normalize_panel_report_entity_map_panel(data.get(CONF_PANEL_REPORT_ENTITY_MAP, DEFAULT_PANEL_REPORT_ENTITY_MAP)))


def _bind_report_options_from_vehicle_map_panel(data: dict[str, Any]) -> dict[str, Any]:
    """Overlay legacy report keys from panel report store first, then vehicle map.

    Priority:
    1. panel_report_entity_map (Flow-independent app-panel store)
    2. vehicle_entity_map report rows
    3. legacy report option keys
    """
    result = dict(data or {})

    panel_entries = _normalize_panel_report_entity_map_panel(result.get(CONF_PANEL_REPORT_ENTITY_MAP, DEFAULT_PANEL_REPORT_ENTITY_MAP))
    if panel_entries:
        result[CONF_PANEL_REPORT_ENTITY_MAP] = panel_entries
        for role, key in REPORT_LEGACY_OPTION_BY_ROLE.items():
            selected = ""
            for item in panel_entries:
                if item.get("role") == role:
                    selected = str(item.get("entity_id") or "").strip()
                    break
            if selected:
                result[key] = selected
        return result

    entries = result.get(CONF_VEHICLE_ENTITY_MAP, DEFAULT_VEHICLE_ENTITY_MAP)
    if not isinstance(entries, list):
        return result
    for role, key in REPORT_LEGACY_OPTION_BY_ROLE.items():
        selected = ""
        for item in entries:
            if not isinstance(item, dict) or str(item.get("role") or "") != role:
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


def _report_binding_audit_panel(data: dict[str, Any]) -> dict[str, Any]:
    """Return a compact audit of report panel selections and legacy bindings."""
    bound = _bind_report_options_from_vehicle_map_panel(data)
    panel_entries = _normalize_panel_report_entity_map_panel(bound.get(CONF_PANEL_REPORT_ENTITY_MAP, DEFAULT_PANEL_REPORT_ENTITY_MAP))
    entries = panel_entries or bound.get(CONF_VEHICLE_ENTITY_MAP, DEFAULT_VEHICLE_ENTITY_MAP)
    source = "panel_report_entity_map" if panel_entries else "legacy_flow_fallback"
    by_role: dict[str, str] = {}
    if isinstance(entries, list):
        for item in entries:
            if not isinstance(item, dict):
                continue
            if not panel_entries and not bool(item.get("use_report")):
                continue
            role = str(item.get("role") or "").strip()
            entity_id = str(item.get("entity_id") or "").strip()
            if role and entity_id and role not in by_role:
                by_role[role] = entity_id
    legacy: dict[str, str] = {}
    for role, key in REPORT_LEGACY_OPTION_BY_ROLE.items():
        legacy[key] = str(bound.get(key) or "").strip()
    missing_roles = [role for role in REPORT_ENTITY_MANAGER_ROLES if role in REPORT_LEGACY_OPTION_BY_ROLE and not (by_role.get(role) or legacy.get(REPORT_LEGACY_OPTION_BY_ROLE[role], ""))]
    return {
        "source": "panel_test",
        "effective_by_role": {role: by_role.get(role) or legacy.get(REPORT_LEGACY_OPTION_BY_ROLE.get(role, ""), "") for role in REPORT_ENTITY_MANAGER_ROLES},
        "legacy_keys": legacy,
        "missing_required_legacy_roles": missing_roles,
        "panel_drives_reports": True,
        "flow_independent": bool(panel_entries),
    }


ENTITY_CATEGORY_LABELS_PANEL.update({
    "dashboard_person": {"tr": "Person Takip", "en": "Person Tracking"},
    "dashboard_custom_home": {"tr": "Custom Home Assistant Entities", "en": "Custom Home Assistant Entities"},
    "dashboard_vehicle_open_close": {"tr": "Araç Açık/Kapalı Durumları", "en": "Vehicle Open/Close Status"},
    "dashboard_drive": {"tr": "Drive Dashboard", "en": "Drive Dashboard"},
})

DASHBOARD_ENTITY_SLOT_DEFINITIONS: list[dict[str, Any]] = [
    # Üst alan + bottom card ortak veri kaynakları
    {"role": "dashboard_top_power", "category": "dashboard_top", "expected_entity": "sensor.tesla_power", "labels": {"tr": "Güç", "en": "Power"}, "descriptions": {"tr": "Üst alan ve bottom card anlık güç/regen değeri.", "en": "Instant power/regen value used by the top area and bottom card."}, "aliases": ["power", "regen", "guc", "güç"]},
    {"role": "dashboard_top_speed", "category": "dashboard_top", "expected_entity": "sensor.tesla_speed", "labels": {"tr": "Hız", "en": "Speed"}, "descriptions": {"tr": "Üst orta hız göstergesinde kullanılan hız entity'si. TeslaMate kullanmak istersen burada sensor.tesla_speed seçebilirsin.", "en": "Speed entity used by the top center speed gauge. Select sensor.tesla_speed here if you want TeslaMate speed."}, "aliases": ["speed", "vehicle speed", "hiz", "hız"]},
    {"role": "dashboard_top_elevation", "category": "dashboard_top", "expected_entity": "sensor.tesla_elevation", "labels": {"tr": "Eğim", "en": "Elevation / slope"}, "descriptions": {"tr": "Üst alan ve bottom card eğim/rakım verisi.", "en": "Elevation/slope data used by the top area and bottom card."}, "aliases": ["elevation", "altitude", "slope", "egim", "eğim"]},
    {"role": "dashboard_top_battery_level", "category": "dashboard_top", "expected_entity": "sensor.tesla_battery_level", "labels": {"tr": "Batarya yüzde", "en": "Battery percentage"}, "descriptions": {"tr": "Üst alan ve bottom card batarya yüzdesi.", "en": "Battery percentage shown in the top area and bottom card."}, "aliases": ["battery level", "battery percentage", "soc", "pil seviyesi"]},
    {"role": "dashboard_top_est_range", "category": "dashboard_top", "expected_entity": "sensor.tesla_est_range", "labels": {"tr": "Kalan tahmini menzil", "en": "Estimated remaining range"}, "descriptions": {"tr": "Üst alan ve bottom card kalan tahmini menzil.", "en": "Estimated remaining range used by the top area and bottom card."}, "aliases": ["estimated range", "est range", "remaining range", "tahmini menzil"]},
    {"role": "dashboard_top_outside_temp", "category": "dashboard_top", "expected_entity": "sensor.tesla_outside_temp", "labels": {"tr": "Dış ısı", "en": "Outside temperature"}, "descriptions": {"tr": "Üst alan ve bottom card dış sıcaklık değeri.", "en": "Outside temperature used by the top area and bottom card."}, "aliases": ["outside temp", "outside temperature", "dis isi", "dış ısı"]},
    {"role": "dashboard_top_location", "category": "dashboard_top", "expected_entity": "device_tracker.tesla", "labels": {"tr": "Konum", "en": "Location"}, "descriptions": {"tr": "Adres ve konum bilgisini çekmek için kullanılan tracker/entity.", "en": "Tracker/entity used to resolve address and location."}, "aliases": ["location", "tracker", "address", "konum", "adres"]},
    {"role": "dashboard_top_rated_range", "category": "dashboard_top", "expected_entity": "sensor.tesla_rated_range", "labels": {"tr": "Arabanın gösterdiği menzil", "en": "Displayed range"}, "descriptions": {"tr": "Arabanın gösterdiği rated/ekran menzil değeri.", "en": "Rated/displayed range reported by the vehicle."}, "aliases": ["rated range", "displayed range", "battery range", "menzil"]},
    {"role": "dashboard_top_energy_remaining", "category": "dashboard_top", "expected_entity": "sensor.pom_energy_remaining", "labels": {"tr": "Energy Remaining", "en": "Energy remaining"}, "descriptions": {"tr": "Bataryada kalan kullanılabilir enerji/kWh bilgisi.", "en": "Remaining usable battery energy/kWh value."}, "aliases": ["energy remaining", "kalan enerji"]},
    {"role": "dashboard_sidebar_inside_temp", "category": "dashboard_top", "expected_entity": "sensor.tesla_inside_temp", "labels": {"tr": "İç ısı", "en": "Inside temperature"}, "descriptions": {"tr": "Üst alan ve bottom card kabin iç sıcaklık değeri.", "en": "Cabin temperature used by the top area and bottom card."}, "aliases": ["inside temp", "cabin temperature", "ic isi", "iç ısı"]},
    {"role": "dashboard_sidebar_battery_module_temp", "category": "dashboard_top", "expected_entity": "sensor.pom_battery_module_temperature_max", "labels": {"tr": "Battery heater", "en": "Battery heater"}, "descriptions": {"tr": "Batarya ısıtıcı / batarya sıcaklık durumu için kullanılan entity.", "en": "Entity used for battery heater / battery temperature state."}, "aliases": ["battery heater", "battery temp", "pil isitici"]},
    {"role": "dashboard_top_odometer", "category": "dashboard_top", "expected_entity": "sensor.tesla_odometer", "labels": {"tr": "Odometer", "en": "Odometer"}, "descriptions": {"tr": "Araç kilometre sayacı.", "en": "Vehicle odometer."}, "aliases": ["odometer", "kilometre"]},

    # Drive Dashboard data sources. These stay inside Entities > Dashboard, so the standalone Drive Dashboard does not need a separate entity manager.
    {"role": "dashboard_drive_shift_state", "category": "dashboard_drive", "expected_entity": "sensor.pom_shift_state", "labels": {"tr": "Vites / sürüş durumu", "en": "Shift state"}, "descriptions": {"tr": "Drive Dashboard orta kartında Park/Drive/Reverse bilgisini gösterir.", "en": "Shows Park/Drive/Reverse state on the Drive Dashboard center card."}, "aliases": ["shift state", "gear", "vites"]},
    {"role": "dashboard_drive_destination", "category": "dashboard_drive", "expected_entity": "sensor.pom_destination", "labels": {"tr": "Navigasyon hedefi", "en": "Navigation destination"}, "descriptions": {"tr": "Drive Dashboard Route kartında aktif navigasyon hedefini gösterir.", "en": "Shows the active navigation destination in the Drive Dashboard Route card."}, "aliases": ["destination", "active route destination", "hedef"]},
    {"role": "dashboard_drive_distance_to_arrival", "category": "dashboard_drive", "expected_entity": "sensor.pom_distance_to_arrival", "labels": {"tr": "Varışa kalan mesafe", "en": "Distance to arrival"}, "descriptions": {"tr": "Drive Dashboard Route kartında hedefe kalan mesafeyi gösterir.", "en": "Shows remaining distance to destination on the Drive Dashboard Route card."}, "aliases": ["distance to arrival", "miles to arrival", "remaining distance"]},
    {"role": "dashboard_drive_time_to_arrival", "category": "dashboard_drive", "expected_entity": "sensor.pom_time_to_arrival", "labels": {"tr": "Varışa kalan süre", "en": "Time to arrival"}, "descriptions": {"tr": "Drive Dashboard Route kartında varışa kalan süreyi gösterir.", "en": "Shows remaining time to destination on the Drive Dashboard Route card."}, "aliases": ["time to arrival", "eta", "minutes to arrival"]},
    {"role": "dashboard_drive_traffic_delay", "category": "dashboard_drive", "expected_entity": "sensor.pom_traffic_delay", "labels": {"tr": "Trafik gecikmesi", "en": "Traffic delay"}, "descriptions": {"tr": "Drive Dashboard Route kartında aktif rotadaki trafik gecikmesini gösterir.", "en": "Shows active-route traffic delay on the Drive Dashboard Route card."}, "aliases": ["traffic delay", "traffic minutes delay"]},
    {"role": "dashboard_drive_soc_at_arrival", "category": "dashboard_drive", "expected_entity": "sensor.pom_state_of_charge_at_arrival", "labels": {"tr": "Varış batarya yüzdesi", "en": "SoC at arrival"}, "descriptions": {"tr": "Drive Dashboard Route kartında Tesla/Tessie varış batarya tahminini gösterir.", "en": "Shows Tesla/Tessie estimated state of charge at arrival on the Route card."}, "aliases": ["soc at arrival", "energy at arrival", "state of charge at arrival"]},
    {"role": "dashboard_drive_driver_temperature_setting", "category": "dashboard_drive", "expected_entity": "sensor.pom_driver_temperature_setting", "labels": {"tr": "Sürücü sıcaklık ayarı", "en": "Driver temperature setting"}, "descriptions": {"tr": "Drive Dashboard Climate kartında sürücü tarafı klima set değerini gösterir.", "en": "Shows driver-side climate setpoint in the Drive Dashboard Climate card."}, "aliases": ["driver temperature", "driver temp setting"]},
    {"role": "dashboard_drive_passenger_temperature_setting", "category": "dashboard_drive", "expected_entity": "sensor.pom_passenger_temperature_setting", "labels": {"tr": "Yolcu sıcaklık ayarı", "en": "Passenger temperature setting"}, "descriptions": {"tr": "Drive Dashboard Climate kartında yolcu tarafı klima set değerini gösterir.", "en": "Shows passenger-side climate setpoint in the Drive Dashboard Climate card."}, "aliases": ["passenger temperature", "passenger temp setting"]},
    {"role": "dashboard_drive_charging_state", "category": "dashboard_drive", "expected_entity": "binary_sensor.pom_charging", "labels": {"tr": "Şarj oluyor mu", "en": "Charging state"}, "descriptions": {"tr": "Drive Dashboard Energy & Charging kartında şarj durumunu gösterir.", "en": "Shows charging state in the Drive Dashboard Energy & Charging card."}, "aliases": ["charging state", "charging", "şarj oluyor"]},
    {"role": "dashboard_drive_dashcam", "category": "dashboard_drive", "expected_entity": "binary_sensor.pom_dashcam", "labels": {"tr": "Dashcam", "en": "Dashcam"}, "descriptions": {"tr": "Drive Dashboard Vehicle Health kartında dashcam durumunu gösterir.", "en": "Shows dashcam state in the Drive Dashboard Vehicle Health card."}, "aliases": ["dashcam", "dashcam state"]},
    {"role": "dashboard_drive_lock", "category": "dashboard_drive", "expected_entity": "lock.pom_lock", "labels": {"tr": "Kilit durumu", "en": "Lock state"}, "descriptions": {"tr": "Drive Dashboard Vehicle Health kartında kapı/kilit özetini gösterir.", "en": "Shows lock/door summary in the Drive Dashboard Vehicle Health card."}, "aliases": ["lock", "locked", "kilit"]},
    {"role": "dashboard_drive_battery_heater", "category": "dashboard_drive", "expected_entity": "binary_sensor.pom_battery_heater", "labels": {"tr": "Batarya ısıtıcısı", "en": "Battery heater"}, "descriptions": {"tr": "Drive Dashboard Vehicle Health kartında batarya ısıtıcısı durumunu gösterir.", "en": "Shows battery-heater state in the Drive Dashboard Vehicle Health card."}, "aliases": ["battery heater"]},
    {"role": "dashboard_drive_tire_pressure_front_left", "category": "dashboard_drive", "expected_entity": "sensor.pom_tire_pressure_front_left", "labels": {"tr": "Ön sol lastik basıncı", "en": "Front-left tire pressure"}, "descriptions": {"tr": "Drive Dashboard Tire Pressure kartında ön sol lastik basıncını gösterir.", "en": "Shows front-left tire pressure in the Drive Dashboard Tire Pressure card."}, "aliases": ["front left tire", "tpms fl"]},
    {"role": "dashboard_drive_tire_pressure_front_right", "category": "dashboard_drive", "expected_entity": "sensor.pom_tire_pressure_front_right", "labels": {"tr": "Ön sağ lastik basıncı", "en": "Front-right tire pressure"}, "descriptions": {"tr": "Drive Dashboard Tire Pressure kartında ön sağ lastik basıncını gösterir.", "en": "Shows front-right tire pressure in the Drive Dashboard Tire Pressure card."}, "aliases": ["front right tire", "tpms fr"]},
    {"role": "dashboard_drive_tire_pressure_rear_left", "category": "dashboard_drive", "expected_entity": "sensor.pom_tire_pressure_rear_left", "labels": {"tr": "Arka sol lastik basıncı", "en": "Rear-left tire pressure"}, "descriptions": {"tr": "Drive Dashboard Tire Pressure kartında arka sol lastik basıncını gösterir.", "en": "Shows rear-left tire pressure in the Drive Dashboard Tire Pressure card."}, "aliases": ["rear left tire", "tpms rl"]},
    {"role": "dashboard_drive_tire_pressure_rear_right", "category": "dashboard_drive", "expected_entity": "sensor.pom_tire_pressure_rear_right", "labels": {"tr": "Arka sağ lastik basıncı", "en": "Rear-right tire pressure"}, "descriptions": {"tr": "Drive Dashboard Tire Pressure kartında arka sağ lastik basıncını gösterir.", "en": "Shows rear-right tire pressure in the Drive Dashboard Tire Pressure card."}, "aliases": ["rear right tire", "tpms rr"]},
    {"role": "dashboard_drive_phantom_drain", "category": "dashboard_drive", "expected_entity": "sensor.pom_phantom_drain", "labels": {"tr": "Phantom drain", "en": "Phantom drain"}, "descriptions": {"tr": "Drive Dashboard Diagnostics kartında park halindeki enerji kaybını gösterir.", "en": "Shows parked energy loss in the Drive Dashboard Diagnostics card."}, "aliases": ["phantom drain"]},
    {"role": "dashboard_drive_battery_pack_temperature", "category": "dashboard_drive", "expected_entity": "sensor.pom_battery_pack_temperature", "labels": {"tr": "Batarya paket sıcaklığı", "en": "Battery pack temperature"}, "descriptions": {"tr": "Drive Dashboard Diagnostics kartında batarya paket sıcaklığını gösterir.", "en": "Shows battery pack temperature in the Drive Dashboard Diagnostics card."}, "aliases": ["battery pack temperature", "pack temp"]},
    {"role": "dashboard_drive_bluetooth_status", "category": "dashboard_drive", "expected_entity": "binary_sensor.pom_bluetooth", "labels": {"tr": "Bluetooth bağlantısı", "en": "Bluetooth status"}, "descriptions": {"tr": "Drive Dashboard üst başlıkta bağlantı durumunu gösterir.", "en": "Shows connection status in the Drive Dashboard header."}, "aliases": ["bluetooth", "connection"]},
    {"role": "dashboard_drive_location_label", "category": "dashboard_drive", "expected_entity": "sensor.pom_tesla_dashboard_location_label", "labels": {"tr": "Konum etiketi", "en": "Location label"}, "descriptions": {"tr": "Drive Dashboard üst başlık ve alt barda okunabilir konum adını gösterir.", "en": "Shows a readable location label in the Drive Dashboard header/footer."}, "aliases": ["location label", "address label"]},
    {"role": "dashboard_drive_power", "category": "dashboard_drive", "expected_entity": "sensor.pom_power", "labels": {"tr": "Anlık güç", "en": "Power"}, "descriptions": {"tr": "Drive Dashboard orta kartında anlık güç/regen değerini göstermek için kullanılır.", "en": "Used to show live power/regen on the Drive Dashboard center card."}, "aliases": ["power", "regen", "güç"]},
    {"role": "dashboard_drive_lifetime_energy_used", "category": "dashboard_drive", "expected_entity": "sensor.pom_lifetime_energy_used", "labels": {"tr": "Toplam enerji kullanımı", "en": "Lifetime energy used"}, "descriptions": {"tr": "Drive Dashboard Diagnostics kartı için aracın ömür boyu kullandığı toplam enerji değeridir.", "en": "Vehicle lifetime total energy used for the Drive Dashboard Diagnostics card."}, "aliases": ["lifetime energy", "lifetime energy used"]},

    # Vehicle open / close aggregate sources
    {"role": "dashboard_vehicle_windows_aggregate", "category": "dashboard_vehicle_open_close", "expected_entity": "", "labels": {"tr": "Camlar açık mı? Tek entity", "en": "Windows open? Aggregate entity"}, "descriptions": {"tr": "TeslaMate gibi tüm camları tek entity ile veren entegrasyonlar için. Bu alan doluysa POM Windows Open bunu ana kaynak kullanır.", "en": "For integrations such as TeslaMate that expose all windows as one entity. If set, POM Windows Open uses this as the primary source."}, "aliases": ["windows open", "window open", "all windows", "camlar acik", "camlar açık"]},
    {"role": "dashboard_vehicle_window_front_left", "category": "dashboard_vehicle_open_close", "expected_entity": "", "labels": {"tr": "Sol ön cam", "en": "Front left window"}, "descriptions": {"tr": "Tessie gibi camları ayrı veren entegrasyonlar için sol ön cam entity'si.", "en": "Front left window entity for integrations that expose each window separately."}, "aliases": ["front left window", "front driver window", "driver window", "window front left", "sol on cam", "sol ön cam"]},
    {"role": "dashboard_vehicle_window_front_right", "category": "dashboard_vehicle_open_close", "expected_entity": "", "labels": {"tr": "Sağ ön cam", "en": "Front right window"}, "descriptions": {"tr": "Tessie gibi camları ayrı veren entegrasyonlar için sağ ön cam entity'si.", "en": "Front right window entity for integrations that expose each window separately."}, "aliases": ["front right window", "front passenger window", "passenger window", "window front right", "sag on cam", "sağ ön cam"]},
    {"role": "dashboard_vehicle_window_rear_left", "category": "dashboard_vehicle_open_close", "expected_entity": "", "labels": {"tr": "Sol arka cam", "en": "Rear left window"}, "descriptions": {"tr": "Tessie gibi camları ayrı veren entegrasyonlar için sol arka cam entity'si.", "en": "Rear left window entity for integrations that expose each window separately."}, "aliases": ["rear left window", "rear driver window", "window rear left", "sol arka cam"]},
    {"role": "dashboard_vehicle_window_rear_right", "category": "dashboard_vehicle_open_close", "expected_entity": "", "labels": {"tr": "Sağ arka cam", "en": "Rear right window"}, "descriptions": {"tr": "Tessie gibi camları ayrı veren entegrasyonlar için sağ arka cam entity'si.", "en": "Rear right window entity for integrations that expose each window separately."}, "aliases": ["rear right window", "rear passenger window", "window rear right", "sag arka cam", "sağ arka cam"]},

    {"role": "dashboard_vehicle_doors_aggregate", "category": "dashboard_vehicle_open_close", "expected_entity": "", "labels": {"tr": "Kapılar açık mı? Tek entity", "en": "Doors open? Aggregate entity"}, "descriptions": {"tr": "TeslaMate gibi tüm kapıları tek entity ile veren entegrasyonlar için. Bu alan doluysa POM Doors Open bunu ana kaynak kullanır.", "en": "For integrations such as TeslaMate that expose all doors as one entity. If set, POM Doors Open uses this as the primary source."}, "aliases": ["doors open", "door open", "all doors", "kapilar acik", "kapılar açık"]},
    {"role": "dashboard_vehicle_door_front_left", "category": "dashboard_vehicle_open_close", "expected_entity": "", "labels": {"tr": "Sol ön kapı", "en": "Front left door"}, "descriptions": {"tr": "Sol ön kapı entity'si.", "en": "Front left door entity."}, "aliases": ["front left door", "front driver door", "driver door", "door front left", "sol on kapi", "sol ön kapı"]},
    {"role": "dashboard_vehicle_door_front_right", "category": "dashboard_vehicle_open_close", "expected_entity": "", "labels": {"tr": "Sağ ön kapı", "en": "Front right door"}, "descriptions": {"tr": "Sağ ön kapı entity'si.", "en": "Front right door entity."}, "aliases": ["front right door", "front passenger door", "passenger door", "door front right", "sag on kapi", "sağ ön kapı"]},
    {"role": "dashboard_vehicle_door_rear_left", "category": "dashboard_vehicle_open_close", "expected_entity": "", "labels": {"tr": "Sol arka kapı", "en": "Rear left door"}, "descriptions": {"tr": "Sol arka kapı entity'si.", "en": "Rear left door entity."}, "aliases": ["rear left door", "rear driver door", "door rear left", "sol arka kapi", "sol arka kapı"]},
    {"role": "dashboard_vehicle_door_rear_right", "category": "dashboard_vehicle_open_close", "expected_entity": "", "labels": {"tr": "Sağ arka kapı", "en": "Rear right door"}, "descriptions": {"tr": "Sağ arka kapı entity'si.", "en": "Rear right door entity."}, "aliases": ["rear right door", "rear passenger door", "door rear right", "sag arka kapi", "sağ arka kapı"]},
    {"role": "dashboard_vehicle_trunk", "category": "dashboard_vehicle_open_close", "expected_entity": "", "labels": {"tr": "Bagaj / trunk", "en": "Trunk"}, "descriptions": {"tr": "Bagaj/trunk açık-kapalı entity'si. POM Openings Open içinde kullanılır.", "en": "Trunk open/closed entity. Used by POM Openings Open."}, "aliases": ["trunk", "rear trunk", "boot", "bagaj"]},
    {"role": "dashboard_vehicle_frunk", "category": "dashboard_vehicle_open_close", "expected_entity": "", "labels": {"tr": "Ön bagaj / frunk", "en": "Frunk"}, "descriptions": {"tr": "Ön bagaj/frunk açık-kapalı entity'si. POM Openings Open içinde kullanılır.", "en": "Frunk open/closed entity. Used by POM Openings Open."}, "aliases": ["frunk", "front trunk", "on bagaj", "ön bagaj"]},
    {"role": "dashboard_vehicle_charge_port", "category": "dashboard_vehicle_open_close", "expected_entity": "", "labels": {"tr": "Şarj portu", "en": "Charge port"}, "descriptions": {"tr": "Şarj portu kapağı / şarj portu açık-kapalı entity'si. POM Openings Open içinde kullanılır.", "en": "Charge port door/open state entity. Used by POM Openings Open."}, "aliases": ["charge port", "charge port door", "charge door", "sarj portu", "şarj portu"]},
    {"role": "dashboard_person_track_1", "category": "dashboard_top", "expected_entity": "person.cavidan", "labels": {"tr": "Person 1", "en": "Person 1"}, "descriptions": {"tr": "Dashboard person takip / bottom card için birinci person entity.", "en": "First person entity for dashboard person tracking / bottom card."}, "aliases": ["person track 1", "person 1"]},
    {"role": "dashboard_person_track_2", "category": "dashboard_top", "expected_entity": "person.ali", "labels": {"tr": "Person 2", "en": "Person 2"}, "descriptions": {"tr": "Dashboard person takip / bottom card için ikinci person entity.", "en": "Second person entity for dashboard person tracking / bottom card."}, "aliases": ["person track 2", "person 2"]},
    {"role": "dashboard_person_track_3", "category": "dashboard_top", "expected_entity": "", "labels": {"tr": "Person 3", "en": "Person 3"}, "descriptions": {"tr": "Dashboard person takip / bottom card için üçüncü opsiyonel person entity.", "en": "Third optional person entity for dashboard person tracking / bottom card."}, "aliases": ["person track 3", "person 3"]},

    # Sidebar kontrolleri
    {"role": "dashboard_sidebar_homelink", "category": "dashboard_sidebar", "expected_entity": "button.pom_homelink", "labels": {"tr": "Homelink", "en": "Homelink"}, "descriptions": {"tr": "Sidebar Homelink komutu.", "en": "Sidebar Homelink command."}, "aliases": ["homelink", "garage"]},
    {"role": "dashboard_sidebar_defrost", "category": "dashboard_sidebar", "expected_entity": "button.pom_defrost", "labels": {"tr": "Buz çözme", "en": "Defrost"}, "descriptions": {"tr": "Sidebar buz çözme/defrost komutu.", "en": "Sidebar defrost command."}, "aliases": ["defrost", "buz cozme", "buz çözme"]},
    {"role": "dashboard_sidebar_steering_heater", "category": "dashboard_sidebar", "expected_entity": "switch.pom_steering_heater", "labels": {"tr": "Direksiyon ısıtıcı", "en": "Steering wheel heater"}, "descriptions": {"tr": "Sidebar direksiyon ısıtıcı kontrolü.", "en": "Sidebar steering wheel heater control."}, "aliases": ["steering heater", "direksiyon isitici"]},
    {"role": "dashboard_bottom_flash_lights_action", "category": "dashboard_sidebar", "expected_entity": "button.pom_flash_lights", "labels": {"tr": "Flash Lights", "en": "Flash lights"}, "descriptions": {"tr": "Sidebar far yak/söndür komutu.", "en": "Sidebar flash lights command."}, "aliases": ["flash lights", "far"]},
    {"role": "dashboard_bottom_honk_action", "category": "dashboard_sidebar", "expected_entity": "button.pom_honk_horn", "labels": {"tr": "Korna", "en": "Horn"}, "descriptions": {"tr": "Sidebar korna çalma komutu.", "en": "Sidebar honk horn command."}, "aliases": ["honk", "horn", "korna"]},
    {"role": "dashboard_bottom_sentry", "category": "dashboard_sidebar", "expected_entity": "switch.pom_sentry_mode_2", "labels": {"tr": "Sentry Mode", "en": "Sentry mode"}, "descriptions": {"tr": "Sidebar Sentry modu kontrolü.", "en": "Sidebar Sentry mode control."}, "aliases": ["sentry", "sentry mode"]},
    {"role": "dashboard_bottom_fart_action", "category": "dashboard_sidebar", "expected_entity": "button.pom_play_fart", "labels": {"tr": "Fart", "en": "Fart"}, "descriptions": {"tr": "Sidebar fart/eğlence komutu.", "en": "Sidebar fart/entertainment command."}, "aliases": ["fart"]},
    {"role": "dashboard_sidebar_wake", "category": "dashboard_sidebar", "expected_entity": "button.pom_wake_vehicle", "labels": {"tr": "Wake", "en": "Wake"}, "descriptions": {"tr": "Sidebar aracı uyandırma komutu.", "en": "Sidebar wake vehicle command."}, "aliases": ["wake", "wake vehicle", "uyandir"]},
    {"role": "dashboard_sidebar_valet_mode", "category": "dashboard_sidebar", "expected_entity": "switch.pom_valet_mode", "labels": {"tr": "Vale Mode", "en": "Valet mode"}, "descriptions": {"tr": "Sidebar vale modu kontrolü.", "en": "Sidebar valet mode control."}, "aliases": ["valet", "valet mode"]},

    # Şarj popup - mevcut alanlar korunur
    {"role": "dashboard_charge_popup_charge_cable", "category": "dashboard_charge_popup", "expected_entity": "binary_sensor.pom_charge_cable", "labels": {"tr": "Şarj kablosu", "en": "Charge cable"}, "descriptions": {"tr": "Şarj popup'ta kablo takılı/takılı değil bilgisi.", "en": "Cable connected state shown in the charge popup."}, "aliases": ["charge cable"]},
    {"role": "dashboard_charge_popup_battery_level", "category": "dashboard_charge_popup", "expected_entity": "sensor.pom_battery_level", "labels": {"tr": "Popup batarya yüzdesi", "en": "Popup battery level"}, "descriptions": {"tr": "Şarj popup batarya yüzdesi.", "en": "Battery percentage shown in the charge popup."}, "aliases": ["battery level"]},
    {"role": "dashboard_charge_popup_battery_range", "category": "dashboard_charge_popup", "expected_entity": "sensor.pom_battery_range", "labels": {"tr": "Popup menzil", "en": "Popup range"}, "descriptions": {"tr": "Şarj popup ana menzil değeri.", "en": "Primary range value shown in the charge popup."}, "aliases": ["battery range"]},
    {"role": "dashboard_charge_popup_range_estimate", "category": "dashboard_charge_popup", "expected_entity": "sensor.pom_battery_range_estimate", "labels": {"tr": "Popup tahmini menzil", "en": "Popup estimated range"}, "descriptions": {"tr": "Şarj popup tahmini menzil değeri.", "en": "Estimated range value shown in the charge popup."}, "aliases": ["range estimate"]},
    {"role": "dashboard_charge_popup_energy_added", "category": "dashboard_charge_popup", "expected_entity": "sensor.pom_charge_energy_added", "labels": {"tr": "Popup eklenen enerji", "en": "Popup energy added"}, "descriptions": {"tr": "Şarj popup oturumda eklenen kWh değeri.", "en": "kWh added during the current charge session."}, "aliases": ["energy added"]},
    {"role": "dashboard_charge_popup_charge_rate", "category": "dashboard_charge_popup", "expected_entity": "sensor.pom_charge_rate", "labels": {"tr": "Şarj hızı", "en": "Charge rate"}, "descriptions": {"tr": "Şarj popup'ta gösterilen km/saat veya menzil kazanım hızı.", "en": "Range gain/charge rate shown in the charge popup."}, "aliases": ["charge rate"]},
    {"role": "dashboard_charge_popup_current", "category": "dashboard_charge_popup", "expected_entity": "sensor.pom_charger_current", "labels": {"tr": "Şarj akımı", "en": "Charger current"}, "descriptions": {"tr": "Şarj popup akım değeri.", "en": "Charging current shown in the charge popup."}, "aliases": ["charger current"]},
    {"role": "dashboard_charge_popup_voltage", "category": "dashboard_charge_popup", "expected_entity": "sensor.pom_charger_voltage", "labels": {"tr": "Şarj voltajı", "en": "Charger voltage"}, "descriptions": {"tr": "Şarj popup voltaj değeri.", "en": "Charging voltage shown in the charge popup."}, "aliases": ["charger voltage"]},
    {"role": "dashboard_charge_popup_time_to_full", "category": "dashboard_charge_popup", "expected_entity": "sensor.pom_time_to_full_charge", "labels": {"tr": "Tam doluma süre", "en": "Time to full"}, "descriptions": {"tr": "Şarj popup tam doluma kalan süre.", "en": "Time remaining to full charge."}, "aliases": ["time to full"]},
    {"role": "dashboard_charge_popup_last_charge", "category": "dashboard_charge_popup", "expected_entity": "sensor.pom_tesla_dashboard_last_charge", "labels": {"tr": "Son şarj özeti", "en": "Last charge summary"}, "descriptions": {"tr": "Dashboard şarj popup son şarj özet sensörü.", "en": "Last charge summary sensor for the dashboard charge popup."}, "aliases": ["last charge"]},

    # Custom Home Assistant entities
    {"role": "dashboard_home_entity_1", "category": "dashboard_custom_home", "expected_entity": "", "labels": {"tr": "Custom Home Assistant Entity 1", "en": "Custom Home Assistant Entity 1"}, "descriptions": {"tr": "Dashboard bottom bar için kullanıcı seçimli Home Assistant entity. Icon boşsa dashboard varsayılan iconu kullanır.", "en": "User-selected Home Assistant entity for the dashboard bottom bar. If icon is empty, the dashboard default icon is used."}, "aliases": ["home entity 1", "custom entity 1"]},
    {"role": "dashboard_home_entity_2", "category": "dashboard_custom_home", "expected_entity": "", "labels": {"tr": "Custom Home Assistant Entity 2", "en": "Custom Home Assistant Entity 2"}, "descriptions": {"tr": "Dashboard bottom bar için ikinci kullanıcı seçimli Home Assistant entity. Icon boşsa dashboard varsayılan iconu kullanır.", "en": "Second user-selected Home Assistant entity for the dashboard bottom bar. If icon is empty, the dashboard default icon is used."}, "aliases": ["home entity 2", "custom entity 2"]},
    {"role": "dashboard_home_entity_3", "category": "dashboard_custom_home", "expected_entity": "", "labels": {"tr": "Custom Home Assistant Entity 3", "en": "Custom Home Assistant Entity 3"}, "descriptions": {"tr": "Dashboard bottom bar için üçüncü kullanıcı seçimli Home Assistant entity. Icon boşsa dashboard varsayılan iconu kullanır.", "en": "Third user-selected Home Assistant entity for the dashboard bottom bar. If icon is empty, the dashboard default icon is used."}, "aliases": ["home entity 3", "custom entity 3"]},
]

DASHBOARD_ENTITY_MANAGER_ROLES: list[str] = [str(item["role"]) for item in DASHBOARD_ENTITY_SLOT_DEFINITIONS]
DASHBOARD_SLOT_BY_ROLE = {str(item["role"]): item for item in DASHBOARD_ENTITY_SLOT_DEFINITIONS}

DRIVE_DASHBOARD_ENTITY_KEY_BY_ROLE: dict[str, str] = {
    "dashboard_top_battery_level": "battery_level",
    "dashboard_charge_popup_battery_level": "battery_level",
    "dashboard_top_rated_range": "battery_range",
    "dashboard_charge_popup_battery_range": "battery_range",
    "dashboard_top_est_range": "battery_range_estimate",
    "dashboard_charge_popup_range_estimate": "battery_range_estimate",
    "dashboard_top_energy_remaining": "energy_remaining",
    "dashboard_top_speed": "speed",
    "dashboard_top_power": "power",
    "dashboard_drive_power": "power",
    "dashboard_top_elevation": "elevation",
    "dashboard_sidebar_inside_temp": "inside_temperature",
    "dashboard_top_outside_temp": "outside_temperature",
    "dashboard_top_odometer": "odometer",
    "dashboard_top_location": "location_tracker",
    "dashboard_drive_location_label": "location_label",
    "dashboard_drive_shift_state": "shift_state",
    "dashboard_drive_destination": "destination",
    "dashboard_drive_distance_to_arrival": "distance_to_arrival",
    "dashboard_drive_time_to_arrival": "time_to_arrival",
    "dashboard_drive_traffic_delay": "traffic_delay",
    "dashboard_drive_soc_at_arrival": "energy_at_arrival",
    "dashboard_drive_driver_temperature_setting": "driver_temperature_setting",
    "dashboard_drive_passenger_temperature_setting": "passenger_temperature_setting",
    "dashboard_drive_charging_state": "charging_state",
    "dashboard_charge_popup_charge_cable": "charge_cable",
    "dashboard_drive_dashcam": "dashcam",
    "dashboard_drive_lock": "lock",
    "dashboard_drive_battery_heater": "battery_heater",
    "dashboard_drive_tire_pressure_front_left": "tire_pressure_front_left",
    "dashboard_drive_tire_pressure_front_right": "tire_pressure_front_right",
    "dashboard_drive_tire_pressure_rear_left": "tire_pressure_rear_left",
    "dashboard_drive_tire_pressure_rear_right": "tire_pressure_rear_right",
    "dashboard_drive_phantom_drain": "phantom_drain",
    "dashboard_sidebar_battery_module_temp": "battery_module_temperature_max",
    "dashboard_drive_battery_pack_temperature": "battery_pack_temperature",
    "dashboard_drive_bluetooth_status": "bluetooth_status",
    "dashboard_drive_lifetime_energy_used": "lifetime_energy_used",
}


def _drive_dashboard_entities_from_options_panel(options: dict[str, Any] | None) -> dict[str, str]:
    data = dict(options or {})
    entries = _normalize_panel_dashboard_entity_map_panel(data.get(CONF_PANEL_DASHBOARD_ENTITY_MAP, DEFAULT_PANEL_DASHBOARD_ENTITY_MAP))
    if not entries:
        entries = _normalize_dashboard_entity_map_panel(data.get(CONF_DASHBOARD_ENTITY_MAP, []))
    entities: dict[str, str] = {}
    for item in entries:
        if not isinstance(item, dict):
            continue
        key = DRIVE_DASHBOARD_ENTITY_KEY_BY_ROLE.get(str(item.get("role") or "").strip())
        entity_id = str(item.get("entity_id") or "").strip()
        if key and entity_id and key not in entities:
            entities[key] = entity_id
    return entities


def _yaml_quote_panel(value: str) -> str:
    return json.dumps(str(value or ""), ensure_ascii=False)


def _drive_dashboard_entities_yaml_panel(options: dict[str, Any] | None) -> str:
    entities = _drive_dashboard_entities_from_options_panel(options)
    if not entities:
        return ""
    preferred_order = ["battery_level", "battery_range", "battery_range_estimate", "energy_remaining", "speed", "power", "shift_state", "destination", "distance_to_arrival", "time_to_arrival", "traffic_delay", "energy_at_arrival", "inside_temperature", "outside_temperature", "driver_temperature_setting", "passenger_temperature_setting", "elevation", "odometer", "location_tracker", "location_label", "charging_state", "charge_cable", "dashcam", "lock", "battery_heater", "tire_pressure_front_left", "tire_pressure_front_right", "tire_pressure_rear_left", "tire_pressure_rear_right", "phantom_drain", "battery_module_temperature_max", "battery_pack_temperature", "bluetooth_status", "lifetime_energy_used"]
    lines = ["            entities:"]
    seen: set[str] = set()
    for key in preferred_order:
        if key in entities:
            lines.append(f"              {key}: {_yaml_quote_panel(entities[key])}")
            seen.add(key)
    for key in sorted(k for k in entities if k not in seen):
        lines.append(f"              {key}: {_yaml_quote_panel(entities[key])}")
    return "\n".join(lines) + "\n"

# alpha222: Reports and Dashboard use the same Vehicle Master Auto Find backbone
# as AI. Dashboard has visual/action-specific roles, so it can use master roles as
# a seed before running dashboard-specific technical matching.
DASHBOARD_MASTER_ROLE_FALLBACKS_PANEL: dict[str, list[str]] = {
    "dashboard_top_battery_level": [VEHICLE_ROLE_BATTERY_LEVEL],
    "dashboard_top_est_range": ["tessie_battery_range_estimate", VEHICLE_ROLE_BATTERY_RANGE],
    "dashboard_top_rated_range": [VEHICLE_ROLE_BATTERY_RANGE],
    "dashboard_top_energy_remaining": [VEHICLE_ROLE_ENERGY_REMAINING],
    "dashboard_top_speed": [VEHICLE_ROLE_SPEED],
    "dashboard_top_power": ["tessie_power"],
    "dashboard_top_elevation": [VEHICLE_ROLE_ELEVATION],
    "dashboard_top_odometer": [VEHICLE_ROLE_ODOMETER],
    "dashboard_drive_shift_state": [VEHICLE_ROLE_SHIFT_STATE],
    "dashboard_drive_destination": ["tessie_destination"],
    "dashboard_drive_distance_to_arrival": ["tessie_distance_to_arrival"],
    "dashboard_drive_time_to_arrival": ["tessie_time_to_arrival"],
    "dashboard_drive_traffic_delay": ["tessie_traffic_delay"],
    "dashboard_drive_soc_at_arrival": ["tessie_soc_at_arrival"],
    "dashboard_drive_driver_temperature_setting": ["tessie_driver_temperature_setting"],
    "dashboard_drive_passenger_temperature_setting": ["tessie_passenger_temperature_setting"],
    "dashboard_drive_charging_state": [VEHICLE_ROLE_CHARGING_STATE],
    "dashboard_drive_dashcam": ["tessie_dashcam"],
    "dashboard_drive_lock": [VEHICLE_ROLE_LOCK_STATE],
    "dashboard_drive_battery_heater": ["tessie_battery_heater"],
    "dashboard_drive_tire_pressure_front_left": [VEHICLE_ROLE_TIRE_PRESSURE_FRONT_LEFT],
    "dashboard_drive_tire_pressure_front_right": [VEHICLE_ROLE_TIRE_PRESSURE_FRONT_RIGHT],
    "dashboard_drive_tire_pressure_rear_left": [VEHICLE_ROLE_TIRE_PRESSURE_REAR_LEFT],
    "dashboard_drive_tire_pressure_rear_right": [VEHICLE_ROLE_TIRE_PRESSURE_REAR_RIGHT],
    "dashboard_drive_phantom_drain": ["tessie_phantom_drain"],
    "dashboard_drive_battery_pack_temperature": [VEHICLE_ROLE_BATTERY_TEMPERATURE],
    "dashboard_drive_bluetooth_status": [VEHICLE_ROLE_VEHICLE_STATE],
    "dashboard_drive_location_label": [VEHICLE_ROLE_LOCATION_TRACKER],
    "dashboard_drive_power": ["tessie_power"],
    "dashboard_drive_lifetime_energy_used": ["tessie_lifetime_energy_used"],
    "dashboard_top_outside_temp": [VEHICLE_ROLE_OUTSIDE_TEMPERATURE],
    "dashboard_sidebar_inside_temp": [VEHICLE_ROLE_INSIDE_TEMPERATURE],
    "dashboard_sidebar_battery_module_temp": [VEHICLE_ROLE_BATTERY_TEMPERATURE, "tessie_battery_module_temperature_max"],
    "dashboard_vehicle_windows_aggregate": [VEHICLE_ROLE_DOOR_WINDOW],
    "dashboard_vehicle_doors_aggregate": [VEHICLE_ROLE_DOOR_WINDOW],
    "dashboard_vehicle_charge_port": ["tessie_charge_port_door"],
    "dashboard_charge_popup_charge_cable": ["tessie_charge_cable"],
    "dashboard_charge_popup_battery_level": [VEHICLE_ROLE_BATTERY_LEVEL],
    "dashboard_charge_popup_battery_range": [VEHICLE_ROLE_BATTERY_RANGE],
    "dashboard_charge_popup_range_estimate": ["tessie_battery_range_estimate", VEHICLE_ROLE_BATTERY_RANGE],
    "dashboard_charge_popup_energy_added": [VEHICLE_ROLE_CHARGE_ENERGY_ADDED],
    "dashboard_charge_popup_charge_rate": ["tessie_charge_rate"],
    "dashboard_charge_popup_current": ["tessie_charger_current"],
    "dashboard_charge_popup_voltage": ["tessie_charger_voltage"],
    "dashboard_charge_popup_time_to_full": ["tessie_time_to_full_charge"],
    "dashboard_bottom_sentry": ["tessie_sentry_mode"],
    "dashboard_sidebar_defrost": ["tessie_defrost_mode"],
    "dashboard_sidebar_steering_heater": ["tessie_steering_wheel_heater"],
    "dashboard_sidebar_valet_mode": ["tessie_valet_mode"],
    "dashboard_sidebar_wake": ["tessie_wake"],
    "dashboard_sidebar_homelink": ["tessie_homelink"],
    "dashboard_bottom_flash_lights_action": ["tessie_flash_lights"],
    "dashboard_bottom_honk_action": ["tessie_honk_horn"],
    "dashboard_bottom_fart_action": ["tessie_play_fart"],
}

def _merge_vehicle_master_entries_panel(existing: Any, discovered: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge existing Vehicle Master rows with newly discovered rows by role."""
    master_by_role: dict[str, dict[str, Any]] = {}
    for item in _normalize_vehicle_entity_map_panel(existing):
        if isinstance(item, dict) and item.get("role"):
            master_by_role[str(item.get("role"))] = item
    for item in discovered:
        if isinstance(item, dict) and item.get("role") and item.get("entity_id"):
            master_by_role[str(item.get("role"))] = item
    ordered: list[dict[str, Any]] = []
    for role in AI_ENTITY_MANAGER_ROLES:
        if role in master_by_role:
            ordered.append(master_by_role.pop(role))
    ordered.extend(master_by_role.values())
    return _normalize_vehicle_entity_map_panel(ordered)


def _master_entries_by_role_panel(entries: Any) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("role") or ""): item
        for item in _normalize_vehicle_entity_map_panel(entries)
        if isinstance(item, dict) and item.get("role") and item.get("entity_id")
    }


def _report_entries_from_vehicle_master_panel(hass: HomeAssistant, master_entries: Any) -> list[dict[str, Any]]:
    """Build Report Entity Manager rows from Vehicle Master rows."""
    master_by_role = _master_entries_by_role_panel(master_entries)
    rows: list[dict[str, Any]] = []
    for role in REPORT_ENTITY_MANAGER_ROLES:
        item = master_by_role.get(role)
        if not item:
            continue
        entity_id = str(item.get("entity_id") or "").strip()
        if not entity_id:
            continue
        entry = _report_entry_for_panel(hass, entity_id, role=role, source="panel_report_vehicle_master")
        entry = _entry_with_match_meta_panel(entry, item)
        if entry:
            rows.append(entry)
    return _normalize_panel_report_entity_map_panel(rows)


def _dashboard_entries_from_vehicle_master_panel(hass: HomeAssistant, master_entries: Any) -> list[dict[str, Any]]:
    """Seed Dashboard Entity Manager rows from Vehicle Master rows.

    Dashboard role names are UI-specific, so this maps compatible master roles
    into dashboard slots before dashboard-specific Auto Find fills the rest.
    """
    master_by_role = _master_entries_by_role_panel(master_entries)
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for dash_role, master_roles in DASHBOARD_MASTER_ROLE_FALLBACKS_PANEL.items():
        if dash_role not in DASHBOARD_ENTITY_MANAGER_ROLES or dash_role in seen:
            continue
        chosen: dict[str, Any] | None = None
        for master_role in master_roles:
            item = master_by_role.get(str(master_role))
            if item and item.get("entity_id"):
                chosen = item
                break
        if not chosen:
            continue
        entity_id = str(chosen.get("entity_id") or "").strip()
        entry = _dashboard_entry_for_panel(hass, entity_id, role=dash_role, source="panel_dashboard_vehicle_master")
        entry = _entry_with_match_meta_panel(entry, chosen)
        if entry:
            rows.append(entry)
            seen.add(dash_role)
    return _normalize_panel_dashboard_entity_map_panel(rows)



# alpha219: language-independent role hints. These are technical HA registry
# keys used by Tessie / Tesla Fleet. They do not change with UI language, so
# Turkish/German/English friendly_name differences no longer break Auto Find.
TECHNICAL_ENTITY_KEYS_BY_ROLE_PANEL: dict[str, list[str]] = {
    VEHICLE_ROLE_BATTERY_LEVEL: ["charge_state_usable_battery_level", "charge_state_battery_level"],
    VEHICLE_ROLE_BATTERY_RANGE: ["charge_state_battery_range", "charge_state_est_battery_range", "charge_state_ideal_battery_range"],
    VEHICLE_ROLE_ENERGY_REMAINING: ["charge_state_energy_remaining", "energy_remaining"],
    VEHICLE_ROLE_CHARGING_STATE: ["charge_state_charging_state", "charge_state_conn_charge_cable"],
    VEHICLE_ROLE_CHARGE_ENERGY_ADDED: ["charge_state_charge_energy_added"],
    VEHICLE_ROLE_CHARGER_POWER: ["charge_state_charger_power"],
    VEHICLE_ROLE_SPEED: ["drive_state_speed"],
    VEHICLE_ROLE_SHIFT_STATE: ["drive_state_shift_state"],
    VEHICLE_ROLE_ODOMETER: ["vehicle_state_odometer"],
    VEHICLE_ROLE_ELEVATION: ["elevation", "drive_state_elevation"],
    VEHICLE_ROLE_CLIMATE: ["primary", "driver_temp"],
    VEHICLE_ROLE_INSIDE_TEMPERATURE: ["climate_state_inside_temp"],
    VEHICLE_ROLE_OUTSIDE_TEMPERATURE: ["climate_state_outside_temp"],
    VEHICLE_ROLE_BATTERY_TEMPERATURE: ["module_temp_max", "module_temp_min", "battery_module_temperature_max", "battery_module_temperature_min"],
    VEHICLE_ROLE_TIRE_PRESSURE_FRONT_LEFT: ["vehicle_state_tpms_pressure_fl"],
    VEHICLE_ROLE_TIRE_PRESSURE_FRONT_RIGHT: ["vehicle_state_tpms_pressure_fr"],
    VEHICLE_ROLE_TIRE_PRESSURE_REAR_LEFT: ["vehicle_state_tpms_pressure_rl"],
    VEHICLE_ROLE_TIRE_PRESSURE_REAR_RIGHT: ["vehicle_state_tpms_pressure_rr"],
    VEHICLE_ROLE_DOOR_WINDOW: ["windows", "vehicle_state_fd_window", "vehicle_state_fp_window", "vehicle_state_rd_window", "vehicle_state_rp_window", "vehicle_state_df", "vehicle_state_pf", "vehicle_state_dr", "vehicle_state_pr"],
    VEHICLE_ROLE_LOCK_STATE: ["vehicle_state_locked"],
    VEHICLE_ROLE_LOCATION_TRACKER: ["location", "route"],
    VEHICLE_ROLE_VEHICLE_STATE: ["state"],
    VEHICLE_ROLE_USER_PRESENT: ["vehicle_state_is_user_present"],

    "tessie_charge_switch": ["charge_state_charging_state", "charge_state_user_charge_enable_request"],
    "tessie_charge_cable_lock": ["charge_state_charge_port_latch"],
    "tessie_charge_port_door": ["charge_state_charge_port_door_open"],
    "tessie_defrost_mode": ["climate_state_defrost_mode"],
    "tessie_flash_lights": ["flash_lights"],
    "tessie_frunk": ["vehicle_state_ft"],
    "tessie_homelink": ["trigger_homelink", "homelink"],
    "tessie_honk_horn": ["honk"],
    "tessie_keyless_driving": ["enable_keyless_driving"],
    "tessie_media_player": ["media"],
    "tessie_play_fart": ["boombox"],
    "tessie_seat_heater_left": ["climate_state_seat_heater_left"],
    "tessie_seat_heater_right": ["climate_state_seat_heater_right"],
    "tessie_seat_heater_rear_left": ["climate_state_seat_heater_rear_left"],
    "tessie_seat_heater_rear_center": ["climate_state_seat_heater_rear_center"],
    "tessie_seat_heater_rear_right": ["climate_state_seat_heater_rear_right"],
    "tessie_sentry_mode": ["vehicle_state_sentry_mode"],
    "tessie_steering_wheel_heater": ["climate_state_steering_wheel_heater", "climate_state_steering_wheel_heat_level"],
    "tessie_trunk": ["vehicle_state_rt"],
    "tessie_valet_mode": ["vehicle_state_valet_mode"],
    "tessie_vent_windows": ["windows"],
    "tessie_wake": ["wake"],
    "tessie_battery_range_estimate": ["charge_state_est_battery_range"],
    "tessie_battery_range_ideal": ["charge_state_ideal_battery_range"],
    "tessie_distance_to_arrival": ["drive_state_active_route_miles_to_arrival"],
    "tessie_time_to_arrival": ["drive_state_active_route_minutes_to_arrival"],
    "tessie_traffic_delay": ["drive_state_active_route_traffic_minutes_delay"],
    "tessie_auto_seat_climate_left": ["climate_state_auto_seat_climate_left"],
    "tessie_auto_seat_climate_right": ["climate_state_auto_seat_climate_right"],
    "tessie_auto_steering_wheel_heater": ["climate_state_auto_steering_wheel_heat"],
    "tessie_battery_heater": ["climate_state_battery_heater", "charge_state_battery_heater_on"],
    "tessie_battery_pack_current": ["pack_current"],
    "tessie_battery_pack_voltage": ["pack_voltage"],
    "tessie_cabin_overheat_protection": ["climate_state_cabin_overheat_protection"],
    "tessie_cabin_overheat_cooling": ["climate_state_cabin_overheat_protection_actively_cooling"],
    "tessie_charge_cable": ["charge_state_conn_charge_cable"],
    "tessie_charge_rate": ["charge_state_charge_rate"],
    "tessie_charger_current": ["charge_state_charger_actual_current"],
    "tessie_charger_voltage": ["charge_state_charger_voltage"],
    "tessie_dashcam": ["vehicle_state_dashcam_state"],
    "tessie_destination": ["drive_state_active_route_destination"],
    "tessie_driver_temperature_setting": ["climate_state_driver_temp_setting"],
    "tessie_front_driver_door": ["vehicle_state_df"],
    "tessie_front_driver_window": ["vehicle_state_fd_window"],
    "tessie_front_passenger_door": ["vehicle_state_pf"],
    "tessie_front_passenger_window": ["vehicle_state_fp_window"],
    "tessie_lifetime_energy_used": ["lifetime_energy_used"],
    "tessie_passenger_temperature_setting": ["climate_state_passenger_temp_setting"],
    "tessie_phantom_drain": ["phantom_drain_percent"],
    "tessie_power": ["drive_state_power"],
    "tessie_preconditioning_enabled": ["charge_state_preconditioning_enabled"],
    "tessie_rear_driver_door": ["vehicle_state_dr"],
    "tessie_rear_driver_window": ["vehicle_state_rd_window"],
    "tessie_rear_passenger_door": ["vehicle_state_pr"],
    "tessie_rear_passenger_window": ["vehicle_state_rp_window"],
    "tessie_route_tracker": ["route"],
    "tessie_scheduled_charging_pending": ["charge_state_scheduled_charging_pending"],
    "tessie_soc_at_arrival": ["drive_state_active_route_energy_at_arrival"],
    "tessie_time_to_full_charge": ["charge_state_minutes_to_full_charge"],
    "tessie_tire_pressure_warning_front_left": ["vehicle_state_tpms_soft_warning_fl"],
    "tessie_tire_pressure_warning_front_right": ["vehicle_state_tpms_soft_warning_fr"],
    "tessie_tire_pressure_warning_rear_left": ["vehicle_state_tpms_soft_warning_rl"],
    "tessie_tire_pressure_warning_rear_right": ["vehicle_state_tpms_soft_warning_rr"],
    "tessie_trip_charging": ["charge_state_trip_charging"],

    "dashboard_top_power": ["drive_state_power"],
    "dashboard_top_speed": ["drive_state_speed"],
    "dashboard_top_elevation": ["elevation", "drive_state_elevation"],
    "dashboard_top_battery_level": ["charge_state_usable_battery_level", "charge_state_battery_level"],
    "dashboard_top_est_range": ["charge_state_est_battery_range"],
    "dashboard_top_outside_temp": ["climate_state_outside_temp"],
    "dashboard_top_location": ["location"],
    "dashboard_top_rated_range": ["charge_state_battery_range"],
    "dashboard_top_energy_remaining": ["charge_state_energy_remaining"],
    "dashboard_sidebar_inside_temp": ["climate_state_inside_temp"],
    "dashboard_sidebar_battery_module_temp": ["module_temp_max", "module_temp_min"],
    "dashboard_top_odometer": ["vehicle_state_odometer"],

    "dashboard_drive_shift_state": ["drive_state_shift_state"],
    "dashboard_drive_destination": ["drive_state_active_route_destination"],
    "dashboard_drive_distance_to_arrival": ["drive_state_active_route_miles_to_arrival"],
    "dashboard_drive_time_to_arrival": ["drive_state_active_route_minutes_to_arrival"],
    "dashboard_drive_traffic_delay": ["drive_state_active_route_traffic_minutes_delay"],
    "dashboard_drive_soc_at_arrival": ["drive_state_active_route_energy_at_arrival"],
    "dashboard_drive_driver_temperature_setting": ["climate_state_driver_temp_setting"],
    "dashboard_drive_passenger_temperature_setting": ["climate_state_passenger_temp_setting"],
    "dashboard_drive_charging_state": ["charge_state_charging_state"],
    "dashboard_drive_dashcam": ["vehicle_state_dashcam_state"],
    "dashboard_drive_lock": ["vehicle_state_locked"],
    "dashboard_drive_battery_heater": ["climate_state_battery_heater", "charge_state_battery_heater_on"],
    "dashboard_drive_tire_pressure_front_left": ["vehicle_state_tpms_pressure_fl"],
    "dashboard_drive_tire_pressure_front_right": ["vehicle_state_tpms_pressure_fr"],
    "dashboard_drive_tire_pressure_rear_left": ["vehicle_state_tpms_pressure_rl"],
    "dashboard_drive_tire_pressure_rear_right": ["vehicle_state_tpms_pressure_rr"],
    "dashboard_drive_phantom_drain": ["phantom_drain_percent"],
    "dashboard_drive_battery_pack_temperature": ["battery_pack_temperature", "pack_temperature", "pack_temp"],
    "dashboard_drive_bluetooth_status": ["bluetooth", "connection", "state"],
    "dashboard_drive_location_label": ["location", "address", "geofence"],
    "dashboard_drive_power": ["drive_state_power"],
    "dashboard_drive_lifetime_energy_used": ["lifetime_energy_used"],

    "dashboard_vehicle_windows_aggregate": ["windows"],
    "dashboard_vehicle_window_front_left": ["vehicle_state_fd_window"],
    "dashboard_vehicle_window_front_right": ["vehicle_state_fp_window"],
    "dashboard_vehicle_window_rear_left": ["vehicle_state_rd_window"],
    "dashboard_vehicle_window_rear_right": ["vehicle_state_rp_window"],
    "dashboard_vehicle_doors_aggregate": ["vehicle_state_df", "vehicle_state_pf", "vehicle_state_dr", "vehicle_state_pr"],
    "dashboard_vehicle_door_front_left": ["vehicle_state_df"],
    "dashboard_vehicle_door_front_right": ["vehicle_state_pf"],
    "dashboard_vehicle_door_rear_left": ["vehicle_state_dr"],
    "dashboard_vehicle_door_rear_right": ["vehicle_state_pr"],
    "dashboard_vehicle_trunk": ["vehicle_state_rt"],
    "dashboard_vehicle_frunk": ["vehicle_state_ft"],
    "dashboard_vehicle_charge_port": ["charge_state_charge_port_door_open"],

    "dashboard_sidebar_homelink": ["trigger_homelink", "homelink"],
    "dashboard_sidebar_defrost": ["climate_state_defrost_mode"],
    "dashboard_sidebar_steering_heater": ["climate_state_steering_wheel_heater", "climate_state_steering_wheel_heat_level"],
    "dashboard_bottom_flash_lights_action": ["flash_lights"],
    "dashboard_bottom_honk_action": ["honk"],
    "dashboard_bottom_sentry": ["vehicle_state_sentry_mode"],
    "dashboard_bottom_fart_action": ["boombox"],
    "dashboard_sidebar_wake": ["wake"],
    "dashboard_sidebar_valet_mode": ["vehicle_state_valet_mode"],
    "dashboard_charge_popup_charge_cable": ["charge_state_conn_charge_cable"],
    "dashboard_charge_popup_battery_level": ["charge_state_usable_battery_level", "charge_state_battery_level"],
    "dashboard_charge_popup_battery_range": ["charge_state_battery_range"],
    "dashboard_charge_popup_range_estimate": ["charge_state_est_battery_range"],
    "dashboard_charge_popup_energy_added": ["charge_state_charge_energy_added"],
    "dashboard_charge_popup_charge_rate": ["charge_state_charge_rate"],
    "dashboard_charge_popup_current": ["charge_state_charger_actual_current"],
    "dashboard_charge_popup_voltage": ["charge_state_charger_voltage"],
    "dashboard_charge_popup_time_to_full": ["charge_state_minutes_to_full_charge"],
}



def _panel_lang_key(lang: str) -> str:
    return "en" if lang == APP_LANGUAGE_EN else "tr"


def _role_label(role: str, lang: str) -> str:
    key = _panel_lang_key(lang)
    # Preserve labels of the original semantic roles; use slot labels only for
    # new Tessie/Teslamate-specific slots.
    item = VEHICLE_ROLE_LABELS_PANEL.get(role) or {}
    slot = PANEL_SLOT_BY_ROLE.get(str(role)) or {}
    slot_labels = slot.get("labels") if isinstance(slot.get("labels"), dict) else {}
    return item.get(key) or slot_labels.get(key) or role


def _role_description(role: str, lang: str) -> str:
    key = _panel_lang_key(lang)
    # Preserve existing role explanations; custom slots provide their own text.
    item = VEHICLE_ROLE_DESCRIPTIONS_PANEL.get(role) or {}
    slot = PANEL_SLOT_BY_ROLE.get(str(role)) or {}
    slot_descriptions = slot.get("descriptions") if isinstance(slot.get("descriptions"), dict) else {}
    return item.get(key) or slot_descriptions.get(key) or ""


def _category_label(category: str, lang: str) -> str:
    item = ENTITY_CATEGORY_LABELS_PANEL.get(str(category) or "other") or ENTITY_CATEGORY_LABELS_PANEL["other"]
    return item.get(_panel_lang_key(lang)) or item.get("tr") or str(category or "other")


def _slot_expected_entity(role: str) -> str:
    slot = PANEL_SLOT_BY_ROLE.get(str(role)) or {}
    return str(slot.get("expected_entity") or "").strip()


def _slot_category(role: str) -> str:
    slot = PANEL_SLOT_BY_ROLE.get(str(role)) or {}
    return str(slot.get("category") or "other").strip() or "other"


def _normalize_vehicle_entity_map_panel(value: Any) -> list[dict[str, Any]]:
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
        if role not in PANEL_ACCEPTED_ENTITY_ROLES:
            role = VEHICLE_ROLE_OTHER
        label = str(item.get("label") or _role_label(role, APP_LANGUAGE_TR)).strip()
        result.append({
            "entity_id": entity_id,
            "role": role,
            "label": label,
            "use_report": _to_bool(item.get("use_report"), role in {
                VEHICLE_ROLE_BATTERY_LEVEL,
                VEHICLE_ROLE_ENERGY_REMAINING,
                VEHICLE_ROLE_CHARGING_STATE,
                VEHICLE_ROLE_CHARGE_ENERGY_ADDED,
                VEHICLE_ROLE_SPEED,
                VEHICLE_ROLE_SHIFT_STATE,
                VEHICLE_ROLE_ODOMETER,
                VEHICLE_ROLE_ELEVATION,
                VEHICLE_ROLE_CLIMATE,
            }),
            "use_ai": _to_bool(item.get("use_ai"), True),
            "use_alerts": _to_bool(item.get("use_alerts"), role not in {VEHICLE_ROLE_LOCATION_TRACKER, VEHICLE_ROLE_OTHER}),
            "use_map": _to_bool(item.get("use_map"), role == VEHICLE_ROLE_LOCATION_TRACKER),
            "source": str(item.get("source") or "panel_manual").strip() or "panel_manual",
            **_match_meta_from_item(item),
        })
    return result


def _normalize_panel_ai_entity_map_panel(value: Any) -> list[dict[str, Any]]:
    """Normalize Flow-independent panel AI Entity Manager store."""
    rows: list[dict[str, Any]] = []
    if not isinstance(value, list):
        return rows
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, dict):
            continue
        entity_id = str(item.get("entity_id") or "").strip()
        if not entity_id or entity_id in seen:
            continue
        seen.add(entity_id)
        role = str(item.get("role") or VEHICLE_ROLE_OTHER).strip()
        if role not in PANEL_ACCEPTED_ENTITY_ROLES:
            role = VEHICLE_ROLE_OTHER
        rows.append({
            "entity_id": entity_id,
            "role": role,
            "label": str(item.get("label") or _role_label(role, APP_LANGUAGE_TR)).strip(),
            "use_report": _to_bool(item.get("use_report"), False),
            "use_ai": _to_bool(item.get("use_ai"), True),
            "use_alerts": _to_bool(item.get("use_alerts"), False),
            "use_map": _to_bool(item.get("use_map"), False),
            "source": str(item.get("source") or "panel_ai_entity_map").strip() or "panel_ai_entity_map",
            **_match_meta_from_item(item),
        })
    return rows


def _normalize_panel_dashboard_entity_map_panel(value: Any) -> list[dict[str, Any]]:
    """Normalize Flow-independent panel Dashboard Entity Manager store."""
    return _normalize_dashboard_entity_map_panel(value)


def _prefer_fixed_role_entities_panel(value: Any) -> list[dict[str, Any]]:
    """Return entries with fixed role assignments preferred over Extra AI rows.

    The panel may temporarily contain the same entity both in a fixed role slot
    and in the custom/other list. A fixed-role assignment is authoritative, so
    the extra row must be pruned before persisting options or rebuilding the UI.
    """
    if not isinstance(value, list):
        return []
    by_entity: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        entity_id = str(item.get("entity_id") or "").strip()
        if not entity_id:
            continue
        role = str(item.get("role") or VEHICLE_ROLE_OTHER).strip()
        is_fixed = role in AI_ENTITY_MANAGER_ROLES
        current = by_entity.get(entity_id)
        if current is None:
            by_entity[entity_id] = item
            order.append(entity_id)
            continue
        current_role = str(current.get("role") or VEHICLE_ROLE_OTHER).strip()
        current_fixed = current_role in AI_ENTITY_MANAGER_ROLES
        if is_fixed and not current_fixed:
            by_entity[entity_id] = item
    return [by_entity[entity_id] for entity_id in order if entity_id in by_entity]


def _registry_entry_for_entity(hass: HomeAssistant, entity_id: str) -> Any | None:
    try:
        registry = er.async_get(hass)
        return registry.async_get(str(entity_id or "").strip())
    except Exception:
        return None


def _entity_exists_for_panel(hass: HomeAssistant, entity_id: str) -> bool:
    entity_id = str(entity_id or "").strip()
    if not entity_id:
        return False
    if hass.states.get(entity_id) is not None:
        return True
    return _registry_entry_for_entity(hass, entity_id) is not None


def _panel_match_text(value: Any) -> str:
    """Return a language-agnostic ASCII-ish match key for entity matching.

    Auto Find must not depend on the user's UI language. Entity IDs, registry
    original names, unique IDs and translation keys are far more stable than
    localized/friendly names. This normalizer keeps those technical tokens easy
    to compare across Turkish/English/German/Japanese renamed UIs.
    """
    text = str(value or "")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    replacements = {
        "ı": "i", "İ": "i", "ş": "s", "ğ": "g", "ü": "u", "ö": "o", "ç": "c",
        "ä": "a", "ö": "o", "ü": "u", "ß": "ss", "ñ": "n", "é": "e", "è": "e",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    for ch in "-. /:\\()[]{}|+":
        text = text.replace(ch, "_")
    while "__" in text:
        text = text.replace("__", "_")
    return text.strip("_")


def _expected_object_id(expected_entity: str) -> str:
    expected_entity = str(expected_entity or "").strip()
    return expected_entity.split(".", 1)[1] if "." in expected_entity else expected_entity


def _slot_match_tokens(slot: dict[str, Any]) -> set[str]:
    expected = str(slot.get("expected_entity") or "").strip()
    tokens: set[str] = set()
    if expected:
        obj = _expected_object_id(expected)
        tokens.add(_panel_match_text(expected))
        tokens.add(_panel_match_text(obj))
        # Common registry unique_id shapes include the object id with a vendor,
        # VIN, device prefix or integration prefix around it. Also keep the last
        # components so renamed entity IDs can still match.
        parts = [part for part in obj.split("_") if part]
        for size in range(2, min(5, len(parts)) + 1):
            tokens.add(_panel_match_text("_".join(parts[-size:])))
    for alias in slot.get("aliases") or []:
        normalized = _panel_match_text(alias)
        if normalized:
            tokens.add(normalized)
    return {token for token in tokens if token}


def _entity_friendly_name(hass: HomeAssistant, entity_id: str) -> str:
    state = hass.states.get(entity_id)
    if state is not None:
        friendly = str(state.attributes.get("friendly_name") or "").strip()
        if friendly:
            return friendly
    reg = _registry_entry_for_entity(hass, entity_id)
    if reg:
        return str(getattr(reg, "name", "") or getattr(reg, "original_name", "") or "").strip()
    return ""


def _registry_metadata_text(hass: HomeAssistant, entity_id: str) -> str:
    reg = _registry_entry_for_entity(hass, entity_id)
    if not reg:
        return ""
    parts = [
        str(getattr(reg, "name", "") or ""),
        str(getattr(reg, "original_name", "") or ""),
        str(getattr(reg, "unique_id", "") or ""),
        str(getattr(reg, "translation_key", "") or ""),
        str(getattr(reg, "platform", "") or ""),
        str(getattr(reg, "device_id", "") or ""),
    ]
    return " ".join(parts)



def _registry_parts_for_match(hass: HomeAssistant, entity_id: str) -> dict[str, str]:
    """Return stable technical registry fields for language-independent matching."""
    reg = _registry_entry_for_entity(hass, entity_id)
    state = hass.states.get(str(entity_id or "").strip())
    attrs = state.attributes if state is not None else {}
    domain = str(entity_id or "").split(".", 1)[0] if "." in str(entity_id or "") else ""
    return {
        "entity_id": str(entity_id or "").strip(),
        "domain": domain,
        "state": str(state.state if state is not None else ""),
        "unit": str(attrs.get("unit_of_measurement") or ""),
        "device_class": str(attrs.get("device_class") or ""),
        "state_class": str(attrs.get("state_class") or ""),
        "original_name": str(getattr(reg, "original_name", "") or "") if reg else "",
        "registry_name": str(getattr(reg, "name", "") or "") if reg else "",
        "unique_id": str(getattr(reg, "unique_id", "") or "") if reg else "",
        "translation_key": str(getattr(reg, "translation_key", "") or "") if reg else "",
        "platform": str(getattr(reg, "platform", "") or "") if reg else "",
        "device_id": str(getattr(reg, "device_id", "") or "") if reg else "",
    }



def _entity_source_info_panel(hass: HomeAssistant, entity_id: str) -> dict[str, str]:
    """Return source metadata for a vehicle entity.

    This is shown in the UI and used by Dashboard Auto Find to avoid mixing
    TeslaMate fallback entities with a Tessie/Fleet Vehicle Master source.
    """
    parts = _registry_parts_for_match(hass, entity_id)
    platform = _panel_match_text(parts.get("platform"))
    entity_lc = _panel_match_text(parts.get("entity_id"))
    unique_lc = _panel_match_text(parts.get("unique_id"))
    text = f"{platform} {entity_lc} {unique_lc}"

    source_key = platform or "unknown"
    source_label = platform or "Unknown"
    if "tessie" in text:
        source_key = "tessie"
        source_label = "Tessie"
    elif "teslamate" in text or entity_lc.startswith("sensor.tesla_") or entity_lc.startswith("binary_sensor.tesla_") or entity_lc.startswith("device_tracker.tesla"):
        source_key = "teslamate"
        source_label = "TeslaMate"
    elif "tesla_fleet" in text or "fleet" in text:
        source_key = "tesla_fleet"
        source_label = "Tesla Fleet"
    elif entity_lc.startswith(("sensor.pom_", "binary_sensor.pom_", "device_tracker.pom_", "button.pom_", "switch.pom_", "cover.pom_", "lock.pom_", "select.pom_", "number.pom_", "climate.pom_")):
        # POM helpers are usually generated from the selected vehicle source.
        source_key = platform or "pom"
        source_label = "POM" if not platform else platform.replace("_", " ").title()

    return {
        "source_key": source_key,
        "source_label": source_label,
        "source_platform": str(parts.get("platform") or ""),
        "source_device_id": str(parts.get("device_id") or ""),
    }


def _add_source_meta_panel(hass: HomeAssistant, entry: dict[str, Any] | None, entity_id: str) -> dict[str, Any] | None:
    if not entry:
        return entry
    try:
        info = _entity_source_info_panel(hass, entity_id)
        for key, value in info.items():
            if value and not entry.get(key):
                entry[key] = value
    except Exception:
        pass
    return entry


def _source_lock_from_entries_panel(hass: HomeAssistant, entries: Any) -> dict[str, str]:
    """Pick the dominant real vehicle source from Vehicle Master entries."""
    counts: dict[tuple[str, str, str], int] = {}
    labels: dict[tuple[str, str, str], str] = {}
    for item in _normalize_vehicle_entity_map_panel(entries):
        if not isinstance(item, dict):
            continue
        entity_id = str(item.get("entity_id") or "").strip()
        if not entity_id:
            continue
        try:
            info = _entity_source_info_panel(hass, entity_id)
        except Exception:
            info = {}
        source_key = str(item.get("source_key") or info.get("source_key") or "").strip()
        platform = str(item.get("source_platform") or info.get("source_platform") or "").strip()
        device_id = str(item.get("source_device_id") or info.get("source_device_id") or "").strip()
        source_label = str(item.get("source_label") or info.get("source_label") or source_key or platform or "").strip()
        if source_key in {"", "unknown", "pom"} and not platform and not device_id:
            continue
        # Avoid person/home helper rows dominating the vehicle source.
        if entity_id.startswith("person."):
            continue
        key = (source_key, platform, device_id)
        weight = 1
        if source_key in {"tessie", "teslamate", "tesla_fleet"}:
            weight += 3
        if device_id:
            weight += 2
        counts[key] = counts.get(key, 0) + weight
        labels[key] = source_label
    if not counts:
        return {}
    best = max(counts.items(), key=lambda item: item[1])[0]
    return {
        "source_key": best[0],
        "source_platform": best[1],
        "source_device_id": best[2],
        "source_label": labels.get(best, best[0] or best[1] or ""),
    }


def _entity_matches_source_lock_panel(hass: HomeAssistant, entity_id: str, source_lock: dict[str, str] | None) -> bool:
    if not source_lock:
        return True
    try:
        info = _entity_source_info_panel(hass, entity_id)
    except Exception:
        return False
    lock_device = str(source_lock.get("source_device_id") or "").strip()
    lock_key = str(source_lock.get("source_key") or "").strip()
    lock_platform = str(source_lock.get("source_platform") or "").strip()
    if lock_device and str(info.get("source_device_id") or "") == lock_device:
        return True
    if lock_key and lock_key not in {"unknown", "pom"} and str(info.get("source_key") or "") == lock_key:
        return True
    if lock_platform and str(info.get("source_platform") or "") == lock_platform:
        return True
    return False


def _source_locked_slot_panel(slot: dict[str, Any], source_lock: dict[str, str] | None) -> dict[str, Any]:
    if not source_lock:
        return slot
    locked = dict(slot or {})
    locked["source_lock"] = dict(source_lock)
    return locked

def _match_meta_from_item(item: Any) -> dict[str, Any]:
    """Preserve Auto Find confidence metadata through normalizers."""
    if not isinstance(item, dict):
        return {}
    meta: dict[str, Any] = {}
    if "confidence" in item:
        try:
            meta["confidence"] = max(0, min(100, int(float(item.get("confidence") or 0))))
        except Exception:
            meta["confidence"] = 0
    for key in ("confidence_label", "match_source", "match_reason", "auto_find_score", "manual", "review", "source_key", "source_label", "source_platform", "source_device_id", "source_lock_label"):
        if key in item:
            meta[key] = item.get(key)
    return meta


def _confidence_label_panel(confidence: int) -> str:
    confidence = max(0, min(100, int(confidence or 0)))
    if confidence >= 95:
        return "very_high"
    if confidence >= 85:
        return "high"
    if confidence >= 70:
        return "medium"
    if confidence >= 50:
        return "low"
    return "very_low"


def _confidence_from_score_panel(score: int) -> int:
    score = int(score or 0)
    if score >= 100000:
        return 100
    if score >= 40000:
        return 99
    if score >= 25000:
        return 97
    if score >= 12000:
        return 93
    if score >= 6500:
        return 88
    if score >= 3000:
        return 78
    if score >= 1800:
        return 68
    if score > 0:
        return 45
    return 0


def _technical_match_detail_panel(hass: HomeAssistant, slot: dict[str, Any], entity_id: str) -> dict[str, Any]:
    """Score exact technical registry keys before localized names.

    Returns additive score plus confidence explanation.
    """
    role = str(slot.get("role") or "")
    parts = _registry_parts_for_match(hass, entity_id)
    translation_key = _panel_match_text(parts.get("translation_key"))
    unique_id = _panel_match_text(parts.get("unique_id"))
    entity_lc = _panel_match_text(parts.get("entity_id"))
    platform = _panel_match_text(parts.get("platform"))
    state_lc = _panel_match_text(parts.get("state"))
    domain = parts.get("domain") or ""

    best = {"score": 0, "source": "", "reason": ""}
    technical_keys = [_panel_match_text(key) for key in TECHNICAL_ENTITY_KEYS_BY_ROLE_PANEL.get(role, []) if key]
    for index, key in enumerate(technical_keys):
        if not key:
            continue
        priority_bonus = max(0, 900 - (index * 40))
        if translation_key == key:
            return {"score": 43000 + priority_bonus, "source": "translation_key", "reason": f"translation_key exact match: {key}"}
        if unique_id.endswith("_" + key) or unique_id.endswith("-" + key) or unique_id == key or key in unique_id:
            best = max(best, {"score": 39000 + priority_bonus, "source": "unique_id", "reason": f"unique_id contains technical key: {key}"}, key=lambda x: x["score"])
        elif key in entity_lc:
            best = max(best, {"score": 17000 + priority_bonus, "source": "entity_id", "reason": f"entity_id contains technical key: {key}"}, key=lambda x: x["score"])

    # Extremely distinctive value/domain patterns that survive localization.
    if role == VEHICLE_ROLE_SHIFT_STATE:
        if state_lc in {"p", "r", "n", "d", "park", "reverse", "neutral", "drive"}:
            best = max(best, {"score": 9000, "source": "state_pattern", "reason": "state pattern looks like P/R/N/D shift state"}, key=lambda x: x["score"])
        if domain == "sensor":
            best["score"] = int(best.get("score", 0)) + 250
    if role == VEHICLE_ROLE_BATTERY_LEVEL and (parts.get("unit") == "%" or parts.get("device_class") == "battery"):
        best = max(best, {"score": 8000, "source": "unit_device_class", "reason": "battery-like % sensor on vehicle device"}, key=lambda x: x["score"])
    if role in {VEHICLE_ROLE_INSIDE_TEMPERATURE, VEHICLE_ROLE_OUTSIDE_TEMPERATURE, VEHICLE_ROLE_BATTERY_TEMPERATURE} and ("°" in parts.get("unit", "") or parts.get("device_class") == "temperature"):
        best["score"] = int(best.get("score", 0)) + 400
    if platform in {"tessie", "tesla_fleet"}:
        best["score"] = int(best.get("score", 0)) + 300

    return best


def _entry_with_match_meta_panel(entry: dict[str, Any] | None, match: dict[str, Any] | None) -> dict[str, Any] | None:
    if not entry:
        return entry
    if not isinstance(match, dict):
        return entry
    score = int(match.get("score") or 0)
    confidence = int(match.get("confidence") or _confidence_from_score_panel(score))
    if confidence:
        entry["confidence"] = confidence
        entry["confidence_label"] = _confidence_label_panel(confidence)
        entry["match_source"] = str(match.get("source") or match.get("match_source") or "score").strip()
        entry["match_reason"] = str(match.get("reason") or match.get("match_reason") or f"score={score}").strip()
        entry["auto_find_score"] = score
        entry["review"] = confidence < 75
    for key in ("source_key", "source_label", "source_platform", "source_device_id"):
        value = match.get(key)
        if value and not entry.get(key):
            entry[key] = value
    return entry


def _registry_metadata_payload(hass: HomeAssistant, entity_id: str) -> dict[str, str]:
    reg = _registry_entry_for_entity(hass, entity_id)
    if not reg:
        return {}
    return {
        "original_name": str(getattr(reg, "original_name", "") or ""),
        "registry_name": str(getattr(reg, "name", "") or ""),
        "unique_id": str(getattr(reg, "unique_id", "") or ""),
        "translation_key": str(getattr(reg, "translation_key", "") or ""),
        "platform": str(getattr(reg, "platform", "") or ""),
    }


def _all_panel_entity_ids(hass: HomeAssistant) -> list[str]:
    ids: list[str] = list(hass.states.async_entity_ids())
    try:
        registry = er.async_get(hass)
        ids.extend(str(getattr(reg_entry, "entity_id", "") or "").strip() for reg_entry in registry.entities.values())
    except Exception:
        pass
    return [entity_id for entity_id in dict.fromkeys(ids) if entity_id]

def _infer_vehicle_role_panel(entity_id: str, friendly_name: str = "", metadata_text: str = "") -> str:
    exact_role = PANEL_EXPECTED_ROLE_BY_ENTITY.get(str(entity_id or "").lower())
    if exact_role:
        return exact_role
    # Technical fields first: entity_id, registry original_name, unique_id,
    # translation_key and platform. Localized friendly_name is appended but is
    # deliberately not the primary matching source.
    technical = _panel_match_text(f"{entity_id} {metadata_text}")
    friendly = _panel_match_text(friendly_name)
    raw_text = f"{technical} {friendly}".strip()
    for _slot in PANEL_ENTITY_SLOT_DEFINITIONS:
        _role = str(_slot.get("role") or "")
        for _token in _slot_match_tokens(_slot):
            if _token and _token in raw_text:
                return _role
    text = raw_text
    if str(entity_id or "").startswith("device_tracker.") or any(k in text for k in ["location", "gps", "latitude", "longitude", "drive_state_latitude", "drive_state_longitude", "konum"]):
        return VEHICLE_ROLE_LOCATION_TRACKER
    if any(k in text for k in ["battery_module_temperature", "battery_temp", "battery_temperature", "pack_temperature", "pack_temp"]):
        return VEHICLE_ROLE_BATTERY_TEMPERATURE
    if any(k in text for k in ["outside_temperature", "ambient_temperature", "outside_temp", "exterior_temperature", "external_temperature", "dis_sicaklik"]):
        return VEHICLE_ROLE_OUTSIDE_TEMPERATURE
    if any(k in text for k in ["inside_temperature", "cabin_temperature", "interior_temperature", "inside_temp", "ic_sicaklik"]):
        return VEHICLE_ROLE_INSIDE_TEMPERATURE
    if any(k in text for k in ["front_left", "fl", "on_sol"]) and any(k in text for k in ["tire", "tyre", "pressure", "tpms", "lastik"]):
        return VEHICLE_ROLE_TIRE_PRESSURE_FRONT_LEFT
    if any(k in text for k in ["front_right", "fr", "on_sag"]) and any(k in text for k in ["tire", "tyre", "pressure", "tpms", "lastik"]):
        return VEHICLE_ROLE_TIRE_PRESSURE_FRONT_RIGHT
    if any(k in text for k in ["rear_left", "rl", "arka_sol"]) and any(k in text for k in ["tire", "tyre", "pressure", "tpms", "lastik"]):
        return VEHICLE_ROLE_TIRE_PRESSURE_REAR_LEFT
    if any(k in text for k in ["rear_right", "rr", "arka_sag"]) and any(k in text for k in ["tire", "tyre", "pressure", "tpms", "lastik"]):
        return VEHICLE_ROLE_TIRE_PRESSURE_REAR_RIGHT
    if any(k in text for k in ["battery_level", "state_of_charge", "usable_battery_level", "soc", "charge_state_battery_level"]):
        return VEHICLE_ROLE_BATTERY_LEVEL
    if any(k in text for k in ["battery_range", "rated_range", "ideal_range", "est_battery_range", "range", "menzil"]):
        return VEHICLE_ROLE_BATTERY_RANGE
    if any(k in text for k in ["energy_remaining", "remaining_energy", "kwh_remaining", "usable_energy", "energy_at_arrival"]):
        return VEHICLE_ROLE_ENERGY_REMAINING
    if any(k in text for k in ["charge_energy_added", "energy_added", "charge_state_charge_energy_added"]):
        return VEHICLE_ROLE_CHARGE_ENERGY_ADDED
    if any(k in text for k in ["charger_power", "charging_power", "charge_state_charger_power", "charge_rate"]):
        return VEHICLE_ROLE_CHARGER_POWER
    if any(k in text for k in ["charging_state", "charge_cable", "plugged", "conn_charge_cable", "sarj"]):
        return VEHICLE_ROLE_CHARGING_STATE
    if any(k in text for k in ["speed", "drive_state_speed", "hiz"]):
        return VEHICLE_ROLE_SPEED
    if any(k in text for k in ["shift", "shift_state", "gear", "vites"]):
        return VEHICLE_ROLE_SHIFT_STATE
    if any(k in text for k in ["odometer", "kilometre", "km_total"]):
        return VEHICLE_ROLE_ODOMETER
    if any(k in text for k in ["elevation", "rakim"]):
        return VEHICLE_ROLE_ELEVATION
    if str(entity_id or "").startswith("climate.") or any(k in text for k in ["climate", "hvac", "klima"]):
        return VEHICLE_ROLE_CLIMATE
    if any(k in text for k in ["door", "window", "open", "cam", "kapi", "frunk", "trunk"]):
        return VEHICLE_ROLE_DOOR_WINDOW
    if str(entity_id or "").startswith("lock.") or any(k in text for k in ["lock", "locked", "kilit"]):
        return VEHICLE_ROLE_LOCK_STATE
    if any(k in text for k in ["vehicle_state", "car_state", "online", "asleep", "sleep", "state"]):
        return VEHICLE_ROLE_VEHICLE_STATE
    if any(k in text for k in ["user_present", "presence", "occupancy", "occupied", "inside_vehicle", "driver_present"]):
        return VEHICLE_ROLE_USER_PRESENT
    return VEHICLE_ROLE_OTHER

def _entity_option_payload(hass: HomeAssistant, *, limit: int = 5000) -> list[dict[str, Any]]:
    """Return entity picker options for the app panel.

    The picker contains all HA states plus entity-registry-only rows. Registry
    original_name/unique_id/translation_key are included so search and Auto Find
    can work independently from localized or user-renamed friendly names.
    """
    rows: list[tuple[int, str, str]] = []
    for entity_id in _all_panel_entity_ids(hass):
        state = hass.states.get(entity_id)
        friendly = str(state.attributes.get("friendly_name") or "") if state is not None else _entity_friendly_name(hass, entity_id)
        metadata = _registry_metadata_text(hass, entity_id)
        haystack = _panel_match_text(f"{entity_id} {metadata} {friendly}")
        score = 0
        for token in ("tesla", "tessie", "teslamate", "pom", "model_y", "modely"):
            if token in haystack:
                score += 100
        if any(entity_id.startswith(prefix) for prefix in ("sensor.pom_", "binary_sensor.pom_", "device_tracker.pom_", "button.pom_", "switch.pom_", "cover.pom_", "lock.pom_", "select.pom_", "climate.pom_", "media_player.pom_")):
            score += 80
        if entity_id.startswith(("sensor.tesla_", "binary_sensor.tesla_", "device_tracker.tesla_")):
            score += 70
        if entity_id.startswith(("sensor.", "binary_sensor.", "device_tracker.", "climate.", "lock.", "cover.", "switch.")):
            score += 15
        elif entity_id.startswith(("input_boolean.", "input_number.", "input_text.", "button.", "select.", "number.")):
            score += 8
        rows.append((-score, (friendly or entity_id).lower(), entity_id))

    options: list[dict[str, Any]] = []
    for _, _, entity_id in sorted(rows)[:limit]:
        state = hass.states.get(entity_id)
        friendly = str(state.attributes.get("friendly_name") or "") if state is not None else _entity_friendly_name(hass, entity_id)
        metadata = _registry_metadata_text(hass, entity_id)
        registry_meta = _registry_metadata_payload(hass, entity_id)
        role = _infer_vehicle_role_panel(entity_id, friendly, metadata)
        domain = entity_id.split(".", 1)[0] if "." in entity_id else "entity"
        row = {
            "entity_id": entity_id,
            "name": friendly or entity_id,
            "state": str(state.state)[:80] if state is not None else "",
            "domain": domain,
            "role_guess": role,
            "category": _slot_category(role),
            "expected_entity": _slot_expected_entity(role),
            "match_text": _panel_match_text(f"{entity_id} {metadata} {friendly}"),
            "has_state": state is not None,
        }
        row.update(registry_meta)
        options.append(row)
    return options

def _vehicle_entry_for_panel(hass: HomeAssistant, entity_id: str, *, role: str, source: str = "panel_manual") -> dict[str, Any] | None:
    entity_id = str(entity_id or "").strip()
    if not entity_id:
        return None
    if role not in PANEL_ACCEPTED_ENTITY_ROLES:
        role = _infer_vehicle_role_panel(entity_id, _entity_friendly_name(hass, entity_id), _registry_metadata_text(hass, entity_id))
    if role not in PANEL_ACCEPTED_ENTITY_ROLES:
        role = VEHICLE_ROLE_OTHER
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
    entry = {
        "entity_id": entity_id,
        "role": role,
        "label": _entity_friendly_name(hass, entity_id) or _role_label(role, _app_language(hass)),
        "use_report": role in use_report_roles,
        "use_ai": True,
        "use_alerts": role in alert_roles,
        "use_map": role == VEHICLE_ROLE_LOCATION_TRACKER,
        "source": "panel_test",
    }
    return _add_source_meta_panel(hass, entry, entity_id)


def _report_entry_for_panel(hass: HomeAssistant, entity_id: str, *, role: str, source: str = "panel_report_manual") -> dict[str, Any] | None:
    """Build a vehicle_entity_map row that mirrors Options Flow report fields."""
    entry = _vehicle_entry_for_panel(hass, entity_id, role=role, source=source)
    if not entry:
        return None
    entry["role"] = role if role in PANEL_ACCEPTED_ENTITY_ROLES else VEHICLE_ROLE_OTHER
    entry["label"] = REPORT_SOURCE_LABEL_BY_ROLE.get(role) or _role_label(role, APP_LANGUAGE_EN)
    entry["use_report"] = True
    # Options Flow keeps report selections available to AI context as well.
    entry["use_ai"] = True
    entry["use_alerts"] = role in {VEHICLE_ROLE_BATTERY_LEVEL, VEHICLE_ROLE_CHARGING_STATE}
    entry["use_map"] = role == VEHICLE_ROLE_LOCATION_TRACKER
    entry["source"] = source
    return entry


def _report_role_default_entity(data: dict[str, Any], entries: list[dict[str, Any]], role: str) -> str:
    """Return report entity for a role, preferring panel store then map then legacy keys."""
    selected = _panel_report_role_entity(data, role)
    if selected:
        return selected
    for item in entries:
        if item.get("role") == role and item.get("use_report"):
            entity_id = str(item.get("entity_id") or "").strip()
            if entity_id:
                return entity_id
    for item in entries:
        if item.get("role") == role:
            entity_id = str(item.get("entity_id") or "").strip()
            if entity_id:
                return entity_id
    legacy_key = REPORT_LEGACY_OPTION_BY_ROLE.get(role)
    if legacy_key:
        return str(data.get(legacy_key) or "").strip()
    return ""


def _sync_report_legacy_options(merged_options: dict[str, Any], entries: list[dict[str, Any]]) -> None:
    """Keep legacy report option keys in sync with the report entity manager."""
    for role, key in REPORT_LEGACY_OPTION_BY_ROLE.items():
        selected = ""
        for item in entries:
            if item.get("role") == role and item.get("use_report"):
                selected = str(item.get("entity_id") or "").strip()
                break
        merged_options[key] = selected


def _auto_find_main_entity(hass: HomeAssistant, data: dict[str, Any]) -> str:
    current = str(data.get(CONF_AI_MAIN_TESLA_ENTITY) or "").strip()
    if current and _entity_exists_for_panel(hass, current):
        return current
    # Prefer the canonical POM/Tessie battery entity as the stable anchor.
    for expected in (DEFAULT_AI_MAIN_TESLA_ENTITY, "sensor.pom_battery_level", "sensor.tesla_battery_level"):
        expected = str(expected or "").strip()
        if expected and _entity_exists_for_panel(hass, expected):
            return expected
    scored: list[tuple[int, str]] = []
    for entity_id in _all_panel_entity_ids(hass):
        technical = _panel_match_text(f"{entity_id} {_registry_metadata_text(hass, entity_id)}")
        friendly = _panel_match_text(_entity_friendly_name(hass, entity_id))
        score = 0
        for token in ("pom", "tesla", "tessie", "teslamate", "model_y", "modely"):
            if token in technical:
                score += 20
            elif token in friendly:
                score += 3
        if entity_id.startswith("device_tracker."):
            score += 5
        if entity_id == "sensor.pom_battery_level":
            score += 100
        if score:
            scored.append((-score, entity_id))
    return sorted(scored)[0][1] if scored else ""

def _score_entity_for_slot(hass: HomeAssistant, slot: dict[str, Any], entity_id: str) -> int:
    return int(_best_entity_match_for_slot(hass, slot, [entity_id]).get("score") or 0)


def _best_entity_match_for_slot(hass: HomeAssistant, slot: dict[str, Any], candidate_ids: list[str]) -> dict[str, Any]:
    expected = str(slot.get("expected_entity") or "").strip()
    role = str(slot.get("role") or "")

    source_lock = slot.get("source_lock") if isinstance(slot.get("source_lock"), dict) else {}
    if expected and _entity_exists_for_panel(hass, expected) and _entity_matches_source_lock_panel(hass, expected, source_lock):
        info = _entity_source_info_panel(hass, expected)
        return {
            "entity_id": expected,
            "score": 100000,
            "confidence": 100,
            "source": "expected_entity",
            "reason": f"expected entity exists in selected source: {expected}",
            **info,
        }

    best: dict[str, Any] = {"score": 0, "entity_id": "", "source": "", "reason": ""}
    seen: set[str] = set()
    for candidate in candidate_ids:
        entity_id = str(candidate or "").strip()
        if not entity_id or entity_id in seen:
            continue
        seen.add(entity_id)

        expected_domain = expected.split(".", 1)[0] if "." in expected else ""
        expected_obj = expected.split(".", 1)[1] if "." in expected else ""
        entity_domain = entity_id.split(".", 1)[0] if "." in entity_id else ""
        entity_obj = entity_id.split(".", 1)[1] if "." in entity_id else entity_id

        friendly = _entity_friendly_name(hass, entity_id)
        metadata = _registry_metadata_text(hass, entity_id)
        technical_hay = _panel_match_text(f"{entity_id} {metadata}")
        friendly_hay = _panel_match_text(friendly)

        technical_detail = _technical_match_detail_panel(hass, slot, entity_id)
        score = int(technical_detail.get("score") or 0)
        source = str(technical_detail.get("source") or "")
        reason = str(technical_detail.get("reason") or "")
        entity_source_info = _entity_source_info_panel(hass, entity_id)
        if source_lock:
            if _entity_matches_source_lock_panel(hass, entity_id, source_lock):
                score += 70000
                source = source or "source_lock"
                reason = reason or f"same source as Vehicle Master: {source_lock.get('source_label') or source_lock.get('source_key') or source_lock.get('source_platform')}"
            else:
                # Do not let old Dashboard expected_entity defaults such as sensor.tesla_*
                # beat a Tessie/Fleet master source. Keep them as weak fallback only.
                score -= 42000
                if not source:
                    source = "source_mismatch"
                if not reason:
                    reason = f"source differs from Vehicle Master: {source_lock.get('source_label') or source_lock.get('source_key') or source_lock.get('source_platform')}"

        if expected_domain and entity_domain == expected_domain:
            score += 400
        if expected_obj and entity_obj == expected_obj:
            score += 50000
            source = source or "entity_id"
            reason = reason or f"entity object exact match: {expected_obj}"
        elif expected_obj and (entity_obj.endswith("_" + expected_obj) or expected_obj.endswith("_" + entity_obj)):
            score += 12000
            source = source or "entity_id"
            reason = reason or f"entity object suffix match: {expected_obj}"

        for token in _slot_match_tokens(slot):
            if token and token in technical_hay:
                score += 6500
                source = source or "technical_token"
                reason = reason or f"technical token match: {token}"
            elif token and token in friendly_hay:
                score += 600
                source = source or "friendly_name"
                reason = reason or f"friendly name fallback match: {token}"

        if _infer_vehicle_role_panel(entity_id, friendly, metadata) == role:
            score += 1800
            source = source or "role_inference"
            reason = reason or "role inference matched"

        if any(token in technical_hay for token in ("pom", "tessie", "tesla_fleet", "teslamate", "tesla")):
            score += 120
        elif any(token in friendly_hay for token in ("pom", "tessie", "tesla", "teslamate")):
            score += 20

        if entity_id.startswith(("sensor.pom_", "binary_sensor.pom_", "device_tracker.pom_", "button.pom_", "switch.pom_", "cover.pom_", "lock.pom_", "select.pom_", "climate.pom_", "media_player.pom_")):
            score += 250
        if entity_id.startswith(("sensor.tesla_", "binary_sensor.tesla_", "device_tracker.tesla_")):
            score += 180

        if score > int(best.get("score") or 0):
            confidence = _confidence_from_score_panel(score)
            best = {
                "entity_id": entity_id,
                "score": score,
                "confidence": confidence,
                "source": "panel_test" or "score",
                "reason": reason or f"score={score}",
                **entity_source_info,
            }

    return best if int(best.get("score") or 0) >= 1800 else {"score": 0, "entity_id": "", "source": "", "reason": ""}


def _best_entity_for_slot(hass: HomeAssistant, slot: dict[str, Any], candidate_ids: list[str]) -> str:
    return str(_best_entity_match_for_slot(hass, slot, candidate_ids).get("entity_id") or "")



FAST_AUTOFIND_MAX_CANDIDATES_PANEL = 260
FAST_AUTOFIND_DASHBOARD_MAX_CANDIDATES_PANEL = 320


def _fast_autofind_prefixes_panel(main_entity: str, data: dict[str, Any]) -> set[str]:
    """Return likely entity_id prefixes for a low-resource scan."""
    prefixes: set[str] = set()
    for value in (
        main_entity,
        data.get(CONF_AI_MAIN_TESLA_ENTITY),
        data.get(CONF_DASHBOARD_MAIN_ENTITY),
        data.get("dashboard_main_entity"),
        data.get(CONF_TRIP_MAP_TRACKER_ENTITY),
    ):
        text = str(value or "").strip()
        if "." not in text:
            continue
        obj = text.split(".", 1)[1].lower()
        for part in obj.split("_"):
            if len(part) >= 3 and part not in {"sensor", "binary", "tesla", "battery", "level", "range"}:
                prefixes.add(part)
                break
        if obj.startswith("pom_"):
            prefixes.add("pom")
        if obj.startswith("tesla_"):
            prefixes.add("tesla")
    prefixes.update({"pom", "tesla"})
    return prefixes


def _fast_autofind_expected_ids_panel(hass: HomeAssistant, slots: list[dict[str, Any]]) -> list[str]:
    result: list[str] = []
    for slot in slots:
        entity_id = str(slot.get("expected_entity") or "").strip()
        if entity_id and _entity_exists_for_panel(hass, entity_id):
            result.append(entity_id)
    return result


def _fast_vehicle_candidate_pool_panel(
    hass: HomeAssistant,
    data: dict[str, Any],
    *,
    main_entity: str = "",
    slots: list[dict[str, Any]] | None = None,
    max_candidates: int = FAST_AUTOFIND_MAX_CANDIDATES_PANEL,
    include_expected: bool = True,
    source_lock: dict[str, str] | None = None,
) -> list[str]:
    """Low-resource candidate pool for old/low-RAM machines.

    It deliberately avoids registry/friendly-name scans over every HA entity.
    Priority:
    1. Main entity and same-device entity-registry rows.
    2. Existing panel selections.
    3. Source-locked/device/prefix-looking Tesla/POM/Tessie/TeslaMate IDs.
    4. Expected IDs only as a last bounded fallback.
    """
    slots = slots or PANEL_ENTITY_SLOT_DEFINITIONS
    candidates: list[str] = []
    main_entity = str(main_entity or "").strip()
    if main_entity:
        candidates.append(main_entity)

    # Same device is cheap because it uses registry once and only returns linked rows.
    try:
        candidates.extend(_device_entity_ids_for_panel(hass, main_entity))
    except Exception:
        pass

    # Current saved entries are cheap and should be preserved/available.
    for item in _normalize_vehicle_entity_map_panel(data.get(CONF_VEHICLE_ENTITY_MAP, DEFAULT_VEHICLE_ENTITY_MAP)):
        entity_id = str(item.get("entity_id") or "").strip()
        if entity_id:
            candidates.append(entity_id)
    for key in (CONF_PANEL_AI_ENTITY_MAP, CONF_PANEL_REPORT_ENTITY_MAP, CONF_PANEL_DASHBOARD_ENTITY_MAP):
        raw = data.get(key)
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, dict):
                    entity_id = str(item.get("entity_id") or "").strip()
                    if entity_id:
                        candidates.append(entity_id)

    prefixes = _fast_autofind_prefixes_panel(main_entity, data)
    vehicle_tokens = {
        "pom", "tesla", "tessie", "teslamate", "model_y", "modely",
        "battery", "range", "energy", "charge", "charger", "speed",
        "shift", "drive", "odometer", "elevation", "location", "tracker",
        "climate", "inside", "outside", "temperature", "sentry", "door",
        "window", "lock", "power", "voltage", "current",
    }
    allowed_domains = (
        "sensor.", "binary_sensor.", "device_tracker.", "button.", "switch.",
        "cover.", "lock.", "select.", "number.", "climate."
    )

    source_lock = source_lock or {}
    all_ids = _all_panel_entity_ids(hass)
    for entity_id in all_ids:
        entity_lc = entity_id.lower()
        if not entity_lc.startswith(allowed_domains):
            continue
        obj = entity_lc.split(".", 1)[1] if "." in entity_lc else entity_lc
        if any(obj.startswith(f"{prefix}_") or obj == prefix for prefix in prefixes):
            candidates.append(entity_id)
            continue
        if any(token in obj for token in vehicle_tokens):
            # In fast mode, only pay source-lock metadata cost for vehicle-looking IDs.
            if source_lock and not _entity_matches_source_lock_panel(hass, entity_id, source_lock):
                continue
            candidates.append(entity_id)

    if include_expected:
        candidates.extend(_fast_autofind_expected_ids_panel(hass, slots))

    return [
        entity_id
        for entity_id in dict.fromkeys(candidates)
        if entity_id and not _is_dashboard_self_output_entity_panel(entity_id)
    ][:max_candidates]


def _fast_discover_vehicle_entries_panel(hass: HomeAssistant, data: dict[str, Any], *, main_entity: str = "") -> list[dict[str, Any]]:
    main_entity = str(main_entity or _auto_find_main_entity(hass, data)).strip()
    candidate_pool = _fast_vehicle_candidate_pool_panel(hass, data, main_entity=main_entity)
    by_role: dict[str, dict[str, Any]] = {}

    for slot in PANEL_ENTITY_SLOT_DEFINITIONS:
        role = str(slot.get("role") or "")
        if not role or role == VEHICLE_ROLE_OTHER:
            continue
        match = _best_entity_match_for_slot(hass, slot, candidate_pool)
        entity_id = str(match.get("entity_id") or "")
        if not entity_id:
            continue
        entry = _vehicle_entry_for_panel(hass, entity_id, role=role, source="panel_fast_auto_find")
        entry = _entry_with_match_meta_panel(entry, match)
        if entry:
            by_role[role] = entry

    # Infer pass is bounded to the same small candidate pool.
    for entity_id in candidate_pool:
        friendly = _entity_friendly_name(hass, entity_id)
        role = _infer_vehicle_role_panel(entity_id, friendly, _registry_metadata_text(hass, entity_id))
        if role == VEHICLE_ROLE_OTHER or role not in PANEL_ACCEPTED_ENTITY_ROLES:
            continue
        entry = _vehicle_entry_for_panel(hass, entity_id, role=role, source="panel_fast_auto_find")
        match = _best_entity_match_for_slot(hass, PANEL_SLOT_BY_ROLE.get(role) or {}, [entity_id])
        entry = _entry_with_match_meta_panel(entry, match)
        if not entry:
            continue
        current = by_role.get(role)
        if current is None:
            by_role[role] = entry
            continue
        current_score = _score_entity_for_slot(hass, PANEL_SLOT_BY_ROLE.get(role) or {}, str(current.get("entity_id") or ""))
        new_score = _score_entity_for_slot(hass, PANEL_SLOT_BY_ROLE.get(role) or {}, str(entry.get("entity_id") or ""))
        if new_score > current_score:
            by_role[role] = entry

    _LOGGER.info("POM Fast Vehicle Auto Find finished. found=%s candidates=%s main=%s", len(by_role), len(candidate_pool), main_entity or "-")
    return [by_role[role] for role in AI_ENTITY_MANAGER_ROLES if role in by_role]


def _auto_discover_vehicle_entries_panel(hass: HomeAssistant, data: dict[str, Any], *, main_entity: str = "", fast_mode: bool = False) -> list[dict[str, Any]]:
    if fast_mode:
        return _fast_discover_vehicle_entries_panel(hass, data, main_entity=main_entity)
    main_entity = str(main_entity or _auto_find_main_entity(hass, data)).strip()
    candidate_ids: list[str] = []
    try:
        registry = er.async_get(hass)
        main_reg = registry.async_get(main_entity) if main_entity else None
        device_id = getattr(main_reg, "device_id", None) if main_reg is not None else None
        if device_id:
            for reg_entry in registry.entities.values():
                if getattr(reg_entry, "device_id", None) == device_id:
                    entity_id = str(getattr(reg_entry, "entity_id", "") or "").strip()
                    if entity_id:
                        candidate_ids.append(entity_id)
    except Exception:
        candidate_ids = []

    if fast_mode:
        return _fast_vehicle_candidate_pool_panel(
            hass,
            data or {},
            main_entity=main_entity,
            slots=DASHBOARD_ENTITY_SLOT_DEFINITIONS,
            max_candidates=FAST_AUTOFIND_DASHBOARD_MAX_CANDIDATES_PANEL,
            include_expected=False,
            source_lock=source_lock,
        )

    all_state_ids = _all_panel_entity_ids(hass)
    expected_ids = [str(slot.get("expected_entity") or "").strip() for slot in PANEL_ENTITY_SLOT_DEFINITIONS if slot.get("expected_entity")]
    candidate_ids.extend([entity_id for entity_id in expected_ids if _entity_exists_for_panel(hass, entity_id)])

    if not candidate_ids:
        prefix = ""
        if main_entity and "." in main_entity:
            obj = main_entity.split(".", 1)[1]
            prefix = obj.split("_", 1)[0]
        for entity_id in all_state_ids:
            technical = _panel_match_text(f"{entity_id} {_registry_metadata_text(hass, entity_id)}")
            friendly = _panel_match_text(_entity_friendly_name(hass, entity_id))
            if (prefix and prefix in entity_id) or any(token in technical for token in ("pom", "tesla", "tessie", "teslamate", "model_y", "modely")) or any(token in friendly for token in ("pom", "tesla", "tessie", "teslamate")):
                candidate_ids.append(entity_id)

    # Keep all HA states available as a lower-priority fallback so Auto Find can
    # still work when a user changed the prefix or imported Teslamate entities.
    candidate_pool = [
        entity_id
        for entity_id in dict.fromkeys(candidate_ids + all_state_ids)
        if not _is_dashboard_self_output_entity_panel(entity_id)
    ]

    by_role: dict[str, dict[str, Any]] = {}
    for slot in PANEL_ENTITY_SLOT_DEFINITIONS:
        role = str(slot.get("role") or "")
        if not role or role == VEHICLE_ROLE_OTHER:
            continue
        match = _best_entity_match_for_slot(hass, slot, candidate_pool)
        entity_id = str(match.get("entity_id") or "")
        if not entity_id:
            continue
        entry = _vehicle_entry_for_panel(hass, entity_id, role=role, source="panel_auto_find")
        entry = _entry_with_match_meta_panel(entry, match)
        if entry:
            by_role[role] = entry

    for entity_id in dict.fromkeys(candidate_ids):
        friendly = _entity_friendly_name(hass, entity_id)
        role = _infer_vehicle_role_panel(entity_id, friendly, _registry_metadata_text(hass, entity_id))
        if role == VEHICLE_ROLE_OTHER or role not in PANEL_ACCEPTED_ENTITY_ROLES:
            continue
        entry = _vehicle_entry_for_panel(hass, entity_id, role=role, source="panel_auto_find")
        match = _best_entity_match_for_slot(hass, PANEL_SLOT_BY_ROLE.get(role) or {}, [entity_id])
        entry = _entry_with_match_meta_panel(entry, match)
        if not entry:
            continue
        current = by_role.get(role)
        if current is None:
            by_role[role] = entry
            continue
        current_score = _score_entity_for_slot(hass, PANEL_SLOT_BY_ROLE.get(role) or {}, str(current.get("entity_id") or ""))
        new_score = _score_entity_for_slot(hass, PANEL_SLOT_BY_ROLE.get(role) or {}, str(entry.get("entity_id") or ""))
        if new_score > current_score:
            by_role[role] = entry
    return [by_role[role] for role in AI_ENTITY_MANAGER_ROLES if role in by_role]



def _enrich_entries_with_confidence_panel(
    hass: HomeAssistant,
    entries: list[dict[str, Any]],
    slots_by_role: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Attach confidence metadata to existing/manual entries for UI display."""
    enriched: list[dict[str, Any]] = []
    for item in entries:
        if not isinstance(item, dict):
            continue
        row = dict(item)
        role = str(row.get("role") or "")
        entity_id = str(row.get("entity_id") or "").strip()
        slot = slots_by_role.get(role) or {}
        if entity_id and slot and not row.get("confidence"):
            try:
                match = _best_entity_match_for_slot(hass, slot, [entity_id])
                row = _entry_with_match_meta_panel(row, match) or row
            except Exception:
                pass
        enriched.append(row)
    return enriched


def _entity_confidence_summary_panel(entries: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [item for item in entries if isinstance(item, dict) and item.get("entity_id")]
    with_conf = [item for item in rows if item.get("confidence") is not None]
    review = [item for item in with_conf if int(item.get("confidence") or 0) < 75]
    very_high = [item for item in with_conf if int(item.get("confidence") or 0) >= 95]
    high = [item for item in with_conf if 85 <= int(item.get("confidence") or 0) < 95]
    return {
        "total": len(rows),
        "scored": len(with_conf),
        "very_high": len(very_high),
        "high": len(high),
        "review": len(review),
        "review_roles": [
            {
                "role": str(item.get("role") or ""),
                "entity_id": str(item.get("entity_id") or ""),
                "confidence": int(item.get("confidence") or 0),
                "reason": str(item.get("match_reason") or ""),
            }
            for item in review[:12]
        ],
    }


def _ai_entity_manager_payload(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    lang = _app_language(hass)
    panel_ai_entries = _normalize_panel_ai_entity_map_panel(data.get(CONF_PANEL_AI_ENTITY_MAP, DEFAULT_PANEL_AI_ENTITY_MAP))
    entries = panel_ai_entries or _normalize_vehicle_entity_map_panel(data.get(CONF_VEHICLE_ENTITY_MAP, DEFAULT_VEHICLE_ENTITY_MAP))
    entries = _enrich_entries_with_confidence_panel(hass, entries, PANEL_SLOT_BY_ROLE)
    return {
        "main_entity": str(data.get(CONF_AI_MAIN_TESLA_ENTITY) or DEFAULT_AI_MAIN_TESLA_ENTITY or "").strip(),
        "auto_discover_device_entities": _to_bool(data.get(CONF_AI_AUTO_DISCOVER_DEVICE_ENTITIES), DEFAULT_AI_AUTO_DISCOVER_DEVICE_ENTITIES),
        "extra_context_entities": list(data.get(CONF_AI_EXTRA_CONTEXT_ENTITIES, DEFAULT_AI_EXTRA_CONTEXT_ENTITIES) or []),
        "excluded_context_entities": list(data.get(CONF_AI_EXCLUDED_CONTEXT_ENTITIES, DEFAULT_AI_EXCLUDED_CONTEXT_ENTITIES) or []),
        "entries": entries,
        "auto_find_summary": _entity_confidence_summary_panel(entries),
        "roles": [
            {
                "role": role,
                "label": _role_label(role, lang),
                "description": _role_description(role, lang),
                "category": _slot_category(role),
                "category_label": _category_label(_slot_category(role), lang),
                "expected_entity": _slot_expected_entity(role),
            }
            for role in AI_ENTITY_MANAGER_ROLES
        ],
        "entity_options": _entity_option_payload(hass),
        "summary": {
            "entry_count": len(entries),
            "ai_count": len([item for item in entries if item.get("use_ai")]),
            "report_count": len([item for item in entries if item.get("use_report")]),
            "map_count": len([item for item in entries if item.get("use_map")]),
            "source": "panel_ai_entity_map" if panel_ai_entries else "legacy_flow_fallback",
        },
    }

def _report_entity_manager_payload(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Return the app-panel Reports Entity Manager payload.

    The payload mirrors Options Flow's reports_entity_manager step: these roles
    are the primary sources for trip/charge visuals, maps and legacy report keys.
    """
    lang = _app_language(hass)
    panel_store_entries = _normalize_panel_report_entity_map_panel(data.get(CONF_PANEL_REPORT_ENTITY_MAP, DEFAULT_PANEL_REPORT_ENTITY_MAP))
    entries = panel_store_entries or _normalize_vehicle_entity_map_panel(data.get(CONF_VEHICLE_ENTITY_MAP, DEFAULT_VEHICLE_ENTITY_MAP))
    report_entries: list[dict[str, Any]] = []
    for role in REPORT_ENTITY_MANAGER_ROLES:
        entity_id = _report_role_default_entity(data, entries, role)
        if not entity_id:
            continue
        existing = next((item for item in entries if item.get("entity_id") == entity_id and item.get("role") == role), None)
        if existing:
            item = dict(existing)
            item["use_report"] = True
            item["use_ai"] = _to_bool(item.get("use_ai"), True)
            item["use_map"] = role == VEHICLE_ROLE_LOCATION_TRACKER or _to_bool(item.get("use_map"), False)
            report_entries.append(item)
        else:
            entry = _report_entry_for_panel(hass, entity_id, role=role, source="panel_report_existing")
            if entry:
                report_entries.append(entry)

    report_entries = _enrich_entries_with_confidence_panel(hass, report_entries, PANEL_SLOT_BY_ROLE)
    return {
        "main_entity": _report_role_default_entity(data, entries, VEHICLE_ROLE_BATTERY_LEVEL) or _auto_find_main_entity(hass, data),
        "entries": report_entries,
        "auto_find_summary": _entity_confidence_summary_panel(report_entries),
        "roles": [
            {
                "role": role,
                "label": _role_label(role, lang),
                "description": _role_description(role, lang),
                "category": _slot_category(role),
                "category_label": _category_label(_slot_category(role), lang),
                "expected_entity": _slot_expected_entity(role),
            }
            for role in REPORT_ENTITY_MANAGER_ROLES
        ],
        "entity_options": _entity_option_payload(hass),
        "summary": {
            "report_count": len([item for item in report_entries if item.get("entity_id")]),
            "role_count": len(REPORT_ENTITY_MANAGER_ROLES),
            "map_count": len([item for item in report_entries if item.get("use_map")]),
            "binding": _report_binding_audit_panel(data),
            "source": "panel_report_entity_map" if panel_store_entries else "legacy_flow_fallback",
        },
    }



def _dashboard_role_label(role: str, lang: str) -> str:
    key = _panel_lang_key(lang)
    slot = DASHBOARD_SLOT_BY_ROLE.get(str(role)) or {}
    labels = slot.get("labels") if isinstance(slot.get("labels"), dict) else {}
    return labels.get(key) or labels.get("tr") or str(role)


def _dashboard_role_description(role: str, lang: str) -> str:
    key = _panel_lang_key(lang)
    slot = DASHBOARD_SLOT_BY_ROLE.get(str(role)) or {}
    descriptions = slot.get("descriptions") if isinstance(slot.get("descriptions"), dict) else {}
    return descriptions.get(key) or descriptions.get("tr") or ""


def _dashboard_entry_for_panel(hass: HomeAssistant, entity_id: str, *, role: str, source: str = "panel_dashboard_manual") -> dict[str, Any] | None:
    entity_id = str(entity_id or "").strip()
    role = str(role or "").strip()
    if not entity_id or role not in DASHBOARD_ENTITY_MANAGER_ROLES:
        return None
    if _is_invalid_dashboard_role_source_panel(role, entity_id):
        _LOGGER.warning(
            "POM Dashboard Entity Manager rejected self/output entity assignment. role=%s entity=%s",
            role,
            entity_id,
        )
        return None
    entry = {
        "entity_id": entity_id,
        "role": role,
        "label": _entity_friendly_name(hass, entity_id) or _dashboard_role_label(role, _app_language(hass)),
        "icon": "",
        "name": "",
        "source": "panel_test",
    }
    return _add_source_meta_panel(hass, entry, entity_id)


def _normalize_dashboard_entity_map_panel(raw: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not isinstance(raw, list):
        return rows
    seen_roles: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "").strip()
        entity_id = str(item.get("entity_id") or "").strip()
        if not role or role not in DASHBOARD_ENTITY_MANAGER_ROLES or not entity_id or role in seen_roles:
            continue
        if _is_invalid_dashboard_role_source_panel(role, entity_id):
            _LOGGER.warning(
                "POM Dashboard Entity Manager ignored invalid self/output row from stored config. role=%s entity=%s",
                role,
                entity_id,
            )
            continue
        rows.append({
            "role": role,
            "entity_id": entity_id,
            "label": str(item.get("label") or "").strip(),
            "icon": str(item.get("icon") or "").strip(),
            "name": str(item.get("name") or "").strip(),
            "source": str(item.get("source") or "panel_dashboard_existing").strip(),
            **_match_meta_from_item(item),
        })
        seen_roles.add(role)
    return rows



def _dashboard_legacy_entries_for_panel(hass: HomeAssistant, data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return dashboard entity rows from the old dashboard Options Flow keys."""
    rows: list[dict[str, Any]] = []
    legacy = {
        "dashboard_person_track_1": ("person_track_1_entity", "person_track_1_name", ""),
        "dashboard_person_track_2": ("person_track_2_entity", "person_track_2_name", ""),
        "dashboard_person_track_3": ("person_track_3_entity", "person_track_3_name", ""),
        "dashboard_home_entity_1": ("entity_home_entity_1", "", "entity_home_entity_1_icon"),
        "dashboard_home_entity_2": ("entity_home_entity_2", "", "entity_home_entity_2_icon"),
        "dashboard_home_entity_3": ("entity_home_entity_3", "", "entity_home_entity_3_icon"),
    }
    for role, (entity_key, name_key, icon_key) in legacy.items():
        entity_id = str(data.get(entity_key) or "").strip()
        if not entity_id:
            continue
        entry = _dashboard_entry_for_panel(hass, entity_id, role=role, source="panel_dashboard_legacy_options")
        if not entry:
            continue
        if name_key:
            entry["name"] = str(data.get(name_key) or entry.get("label") or "").strip()
        if icon_key:
            entry["icon"] = str(data.get(icon_key) or "").strip()
        rows.append(entry)
    return rows


def _device_entity_ids_for_panel(hass: HomeAssistant, main_entity: str) -> list[str]:
    """Return entity registry IDs that share the same HA device as main_entity."""
    main_entity = str(main_entity or "").strip()
    if not main_entity:
        return []
    try:
        registry = er.async_get(hass)
        main_reg = registry.async_get(main_entity)
        device_id = getattr(main_reg, "device_id", None) if main_reg is not None else None
        if not device_id:
            return []
        result: list[str] = []
        for reg_entry in registry.entities.values():
            if getattr(reg_entry, "device_id", None) != device_id:
                continue
            entity_id = str(getattr(reg_entry, "entity_id", "") or "").strip()
            if entity_id:
                result.append(entity_id)
        return list(dict.fromkeys(result))
    except Exception:
        return []


def _dashboard_autofind_candidate_pool(hass: HomeAssistant, main_entity: str, source_lock: dict[str, str] | None = None, *, fast_mode: bool = False, data: dict[str, Any] | None = None) -> list[str]:
    """Return a bounded candidate pool for Dashboard Auto Find.

    The old implementation scanned every Home Assistant entity for every
    dashboard role. On large systems that can block HA for tens of seconds.
    This pool keeps the useful candidates: exact expected entities, entities on
    the same HA device as the selected vehicle entity, and Tesla/POM/Tessie/
    TeslaMate-looking entities or entities matching dashboard role tokens.
    """
    all_state_ids = [
        entity_id
        for entity_id in _all_panel_entity_ids(hass)
        if not _is_dashboard_self_output_entity_panel(entity_id)
    ]
    device_ids = [
        entity_id
        for entity_id in _device_entity_ids_for_panel(hass, main_entity)
        if not _is_dashboard_self_output_entity_panel(entity_id)
    ]
    expected_ids = [
        str(slot.get("expected_entity") or "").strip()
        for slot in DASHBOARD_ENTITY_SLOT_DEFINITIONS
        if slot.get("expected_entity")
    ]
    source_ids: list[str] = []
    if source_lock:
        for entity_id in all_state_ids:
            if _entity_matches_source_lock_panel(hass, entity_id, source_lock):
                source_ids.append(entity_id)

    token_set: set[str] = {
        "pom", "tesla", "tessie", "teslamate", "model_y", "modely",
        "window", "windows", "cam", "camlar",
        "door", "doors", "kapi", "kapilar", "kapı", "kapılar",
        "trunk", "frunk", "boot", "bagaj", "charge_port", "charge port",
        "battery", "range", "power", "odometer", "location", "tracker",
        "inside", "outside", "climate", "sentry", "homelink", "defrost",
    }
    for slot in DASHBOARD_ENTITY_SLOT_DEFINITIONS:
        for token in _slot_match_tokens(slot):
            token = str(token or "").strip()
            if token:
                token_set.add(token)

    filtered: list[str] = []
    for entity_id in all_state_ids:
        if entity_id in expected_ids or entity_id in device_ids:
            filtered.append(entity_id)
            continue
        # Fast entity_id/object_id check first; only ask registry/friendly text for
        # likely vehicle domains. This avoids expensive metadata lookups for every
        # unrelated Home Assistant entity.
        entity_lc = _panel_match_text(entity_id)
        if any(token in entity_lc for token in token_set):
            filtered.append(entity_id)
            continue
        if not entity_id.startswith((
            "sensor.", "binary_sensor.", "device_tracker.", "button.", "switch.",
            "cover.", "lock.", "select.", "number.", "climate."
        )):
            continue
        # Metadata/friendly fallback is bounded by vehicle-ish domains.
        metadata = _panel_match_text(_registry_metadata_text(hass, entity_id))
        if metadata and any(token in metadata for token in token_set):
            filtered.append(entity_id)
            continue
        friendly = _panel_match_text(_entity_friendly_name(hass, entity_id))
        if friendly and any(token in friendly for token in token_set):
            filtered.append(entity_id)

    # Keep deterministic priority:
    # 1 exact expected old IDs
    # 2 same-device entities
    # 3 filtered vehicle-like candidates
    # Hard cap protects very large HA instances from accidental UI lockups.
    pool = list(dict.fromkeys(
        source_ids
        + device_ids
        + filtered
        + [entity_id for entity_id in expected_ids if _entity_exists_for_panel(hass, entity_id)]
    ))
    return pool[:900]


def _auto_discover_dashboard_entries_panel(hass: HomeAssistant, data: dict[str, Any], *, fast_mode: bool = False) -> list[dict[str, Any]]:
    main_entity = str(
        data.get(CONF_DASHBOARD_MAIN_ENTITY)
        or data.get("dashboard_main_entity")
        or data.get(CONF_AI_MAIN_TESLA_ENTITY)
        or DEFAULT_AI_MAIN_TESLA_ENTITY
        or ""
    ).strip()

    source_lock = data.get("_vehicle_source_lock") if isinstance(data.get("_vehicle_source_lock"), dict) else {}
    candidate_pool = _dashboard_autofind_candidate_pool(hass, main_entity, source_lock, fast_mode=fast_mode, data=data)
    _LOGGER.info(
        "POM Dashboard Auto Find started. roles=%s candidates=%s main_entity=%s source=%s",
        len(DASHBOARD_ENTITY_SLOT_DEFINITIONS),
        len(candidate_pool),
        main_entity or "-",
        source_lock.get("source_label") or source_lock.get("source_key") or "-",
    )

    by_role: dict[str, dict[str, Any]] = {}
    for slot in DASHBOARD_ENTITY_SLOT_DEFINITIONS:
        role = str(slot.get("role") or "").strip()
        if not role:
            continue
        match = _best_entity_match_for_slot(hass, _source_locked_slot_panel(slot, source_lock), candidate_pool)
        entity_id = str(match.get("entity_id") or "")
        if not entity_id or _is_invalid_dashboard_role_source_panel(role, entity_id):
            continue
        entry = _dashboard_entry_for_panel(hass, entity_id, role=role, source="panel_dashboard_auto_find")
        entry = _entry_with_match_meta_panel(entry, match)
        if entry:
            by_role[role] = entry

    _LOGGER.info(
        "POM Dashboard Auto Find finished. found=%s roles=%s candidates=%s",
        len(by_role),
        len(DASHBOARD_ENTITY_SLOT_DEFINITIONS),
        len(candidate_pool),
    )
    return [by_role[role] for role in DASHBOARD_ENTITY_MANAGER_ROLES if role in by_role]


def _dashboard_legacy_entry_fallbacks(hass: HomeAssistant, data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return dashboard entries from old Options Flow keys when dashboard_entity_map is still empty/stale."""
    mapping = {
        "dashboard_person_track_1": "person_track_1_entity",
        "dashboard_person_track_2": "person_track_2_entity",
        "dashboard_person_track_3": "person_track_3_entity",
        "dashboard_home_entity_1": "entity_home_entity_1",
        "dashboard_home_entity_2": "entity_home_entity_2",
    }
    icon_mapping = {
        "dashboard_home_entity_1": "entity_home_entity_1_icon",
        "dashboard_home_entity_2": "entity_home_entity_2_icon",
    }
    rows: list[dict[str, Any]] = []
    for role, key in mapping.items():
        entity_id = str(data.get(key) or "").strip()
        if not entity_id:
            continue
        entry = _dashboard_entry_for_panel(hass, entity_id, role=role, source="panel_dashboard_legacy")
        if not entry:
            continue
        entry["icon"] = str(data.get(icon_mapping.get(role, "")) or "").strip() if role in icon_mapping else ""
        rows.append(entry)
    return rows


def _dashboard_entity_manager_payload(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    lang = _app_language(hass)
    panel_dashboard_entries = _normalize_panel_dashboard_entity_map_panel(data.get(CONF_PANEL_DASHBOARD_ENTITY_MAP, DEFAULT_PANEL_DASHBOARD_ENTITY_MAP))
    entries = panel_dashboard_entries or _normalize_dashboard_entity_map_panel(data.get(CONF_DASHBOARD_ENTITY_MAP, []))
    if not entries:
        # alpha222: when Dashboard has not been filled yet, derive what we can
        # from the shared Vehicle Master map so users do not need to re-enter
        # the same Tessie/Tesla entities a third time.
        entries = _dashboard_entries_from_vehicle_master_panel(hass, data.get(CONF_VEHICLE_ENTITY_MAP, DEFAULT_VEHICLE_ENTITY_MAP))
    by_role = {str(item.get("role") or ""): item for item in entries}
    for legacy_item in _dashboard_legacy_entry_fallbacks(hass, data):
        role = str(legacy_item.get("role") or "")
        if role and role not in by_role:
            entries.append(legacy_item)
            by_role[role] = legacy_item
    entries = _enrich_entries_with_confidence_panel(hass, entries, DASHBOARD_SLOT_BY_ROLE)
    return {
        "main_entity": str(data.get(CONF_DASHBOARD_MAIN_ENTITY) or data.get(CONF_AI_MAIN_TESLA_ENTITY) or DEFAULT_AI_MAIN_TESLA_ENTITY or "").strip(),
        "entries": entries,
        "auto_find_summary": _entity_confidence_summary_panel(entries),
        "roles": [
            {
                "role": str(slot.get("role") or ""),
                "label": _dashboard_role_label(str(slot.get("role") or ""), lang),
                "description": _dashboard_role_description(str(slot.get("role") or ""), lang),
                "category": str(slot.get("category") or "other"),
                "category_label": _category_label(str(slot.get("category") or "other"), lang),
                "expected_entity": str(slot.get("expected_entity") or "").strip(),
            }
            for slot in DASHBOARD_ENTITY_SLOT_DEFINITIONS
        ],
        "entity_options": _entity_option_payload(hass),
        "summary": {
            "dashboard_count": len([item for item in entries if item.get("entity_id")]),
            "role_count": len(DASHBOARD_ENTITY_MANAGER_ROLES),
            "missing_count": max(0, len(DASHBOARD_ENTITY_MANAGER_ROLES) - len([item for item in entries if item.get("entity_id")])),
            "source": "panel_dashboard_entity_map" if panel_dashboard_entries else "legacy_flow_fallback",
        },
    }


def _sync_dashboard_legacy_options(merged_options: dict[str, Any], entries: list[dict[str, Any]]) -> None:
    """Keep old dashboard option keys in sync with the Dashboard Entity Manager."""
    role_to_option = {
        "dashboard_person_track_1": "person_track_1_entity",
        "dashboard_person_track_2": "person_track_2_entity",
        "dashboard_person_track_3": "person_track_3_entity",
        "dashboard_home_entity_1": "entity_home_entity_1",
        "dashboard_home_entity_2": "entity_home_entity_2",
        "dashboard_home_entity_3": "entity_home_entity_3",
    }
    role_to_name_option = {
        "dashboard_person_track_1": "person_track_1_name",
        "dashboard_person_track_2": "person_track_2_name",
        "dashboard_person_track_3": "person_track_3_name",
    }
    role_to_enabled_option = {
        "dashboard_person_track_1": "person_track_1_enabled",
        "dashboard_person_track_2": "person_track_2_enabled",
        "dashboard_person_track_3": "person_track_3_enabled",
    }
    role_to_icon_option = {
        "dashboard_home_entity_1": "entity_home_entity_1_icon",
        "dashboard_home_entity_2": "entity_home_entity_2_icon",
        "dashboard_home_entity_3": "entity_home_entity_3_icon",
    }
    by_role = {str(item.get("role") or ""): item for item in entries if isinstance(item, dict)}
    for role, option_key in role_to_option.items():
        item = by_role.get(role) or {}
        entity_id = str(item.get("entity_id") or "").strip()
        merged_options[option_key] = entity_id
        if role in role_to_enabled_option:
            merged_options[role_to_enabled_option[role]] = bool(entity_id)
        if role in role_to_name_option and entity_id:
            label = str(item.get("name") or item.get("label") or "").strip()
            if label:
                merged_options[role_to_name_option[role]] = label
        if role in role_to_icon_option:
            merged_options[role_to_icon_option[role]] = str(item.get("icon") or "").strip()




def _ai_settings_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Return Options Flow AI behavior/settings for the app panel.

    Deprecated entity-discovery toggles are intentionally not exposed here:
    ai_auto_discover_device_entities and ai_include_unavailable.
    """
    return {
        "ai_enabled": _to_bool(data.get(CONF_AI_ENABLED), DEFAULT_AI_ENABLED),
        "ai_personality": _supported_ai_personality_panel(data.get(CONF_AI_PERSONALITY)),
        "ai_answer_length": str(data.get(CONF_AI_ANSWER_LENGTH) or DEFAULT_AI_ANSWER_LENGTH),
        "ai_context_mode": str(data.get(CONF_AI_CONTEXT_MODE) or DEFAULT_AI_CONTEXT_MODE),
        "ai_name": str(data.get(CONF_AI_NAME) or DEFAULT_AI_NAME or "").strip(),
        "ai_user_address": str(data.get(CONF_AI_USER_ADDRESS) or DEFAULT_AI_USER_ADDRESS or "").strip(),
        "openai_api_key": _mask_secret_for_panel(data.get(CONF_OPENAI_API_KEY)),
        "openai_api_key_configured": bool(str(data.get(CONF_OPENAI_API_KEY) or "").strip()),
        "openai_api_key_last4": _secret_last4(data.get(CONF_OPENAI_API_KEY)),
        "openai_model": str(data.get(CONF_OPENAI_MODEL) or DEFAULT_OPENAI_MODEL or "").strip(),
        "reverse_geocoding_enabled": _to_bool(data.get(CONF_REVERSE_GEOCODING_ENABLED), DEFAULT_REVERSE_GEOCODING_ENABLED),
        "reverse_geocoding_cache_minutes": max(5, _positive_int(data.get(CONF_REVERSE_GEOCODING_CACHE_MINUTES), DEFAULT_REVERSE_GEOCODING_CACHE_MINUTES, minimum=5, maximum=1440)),
        "reverse_geocoding_use_in_ai": _to_bool(data.get(CONF_REVERSE_GEOCODING_USE_IN_AI), DEFAULT_REVERSE_GEOCODING_USE_IN_AI),
        "ai_max_output_tokens": _positive_int(data.get(CONF_AI_MAX_OUTPUT_TOKENS), DEFAULT_AI_MAX_OUTPUT_TOKENS, minimum=128, maximum=4096),
        "ai_telegram_include_context": _to_bool(data.get(CONF_AI_TELEGRAM_INCLUDE_CONTEXT), DEFAULT_AI_TELEGRAM_INCLUDE_CONTEXT),
        "ai_confirm_optional_controls": True,
        "ai_alerts_enabled": _to_bool(data.get(CONF_AI_ALERTS_ENABLED), DEFAULT_AI_ALERTS_ENABLED),
        "ai_alert_style": str(data.get(CONF_AI_ALERT_STYLE) or DEFAULT_AI_ALERT_STYLE),
        "ai_alert_cooldown_minutes": _positive_int(data.get(CONF_AI_ALERT_COOLDOWN_MINUTES), DEFAULT_AI_ALERT_COOLDOWN_MINUTES, minimum=1, maximum=240),
        "ai_alert_low_battery_enabled": _to_bool(data.get(CONF_AI_ALERT_LOW_BATTERY_ENABLED), DEFAULT_AI_ALERT_LOW_BATTERY_ENABLED),
        "ai_alert_low_battery_threshold": round(_positive_float(data.get(CONF_AI_ALERT_LOW_BATTERY_THRESHOLD), DEFAULT_AI_ALERT_LOW_BATTERY_THRESHOLD, minimum=1, maximum=100), 2),
        "ai_alert_post_trip_summary_enabled": _to_bool(data.get(CONF_AI_ALERT_POST_TRIP_SUMMARY_ENABLED), DEFAULT_AI_ALERT_POST_TRIP_SUMMARY_ENABLED),
        "ai_alert_charge_finished_enabled": _to_bool(data.get(CONF_AI_ALERT_CHARGE_FINISHED_ENABLED), DEFAULT_AI_ALERT_CHARGE_FINISHED_ENABLED),
        "ai_alert_charging_stopped_enabled": _to_bool(data.get(CONF_AI_ALERT_CHARGING_STOPPED_ENABLED), DEFAULT_AI_ALERT_CHARGING_STOPPED_ENABLED),
        "ai_alert_tire_pressure_enabled": _to_bool(data.get(CONF_AI_ALERT_TIRE_PRESSURE_ENABLED), DEFAULT_AI_ALERT_TIRE_PRESSURE_ENABLED),
        "ai_alert_tire_pressure_threshold_bar": round(_positive_float(data.get(CONF_AI_ALERT_TIRE_PRESSURE_THRESHOLD_BAR), DEFAULT_AI_ALERT_TIRE_PRESSURE_THRESHOLD_BAR, minimum=0.1, maximum=80.0), 2),
        "ai_alert_high_battery_temp_enabled": _to_bool(data.get(CONF_AI_ALERT_HIGH_BATTERY_TEMP_ENABLED), DEFAULT_AI_ALERT_HIGH_BATTERY_TEMP_ENABLED),
        "ai_alert_high_battery_temp_threshold_c": round(_positive_float(data.get(CONF_AI_ALERT_HIGH_BATTERY_TEMP_THRESHOLD_C), DEFAULT_AI_ALERT_HIGH_BATTERY_TEMP_THRESHOLD_C, minimum=1, maximum=120), 2),
        "ai_alert_climate_left_on_enabled": _to_bool(data.get(CONF_AI_ALERT_CLIMATE_LEFT_ON_ENABLED), DEFAULT_AI_ALERT_CLIMATE_LEFT_ON_ENABLED),
        "ai_alert_climate_left_on_delay_minutes": _positive_int(data.get(CONF_AI_ALERT_CLIMATE_LEFT_ON_DELAY_MINUTES), DEFAULT_AI_ALERT_CLIMATE_LEFT_ON_DELAY_MINUTES, minimum=1, maximum=240),
        "ai_alert_unlocked_enabled": _to_bool(data.get(CONF_AI_ALERT_UNLOCKED_ENABLED), DEFAULT_AI_ALERT_UNLOCKED_ENABLED),
        "ai_alert_unlocked_delay_minutes": _positive_int(data.get(CONF_AI_ALERT_UNLOCKED_DELAY_MINUTES), DEFAULT_AI_ALERT_UNLOCKED_DELAY_MINUTES, minimum=1, maximum=120),
        "ai_alert_door_window_open_enabled": _to_bool(data.get(CONF_AI_ALERT_DOOR_WINDOW_OPEN_ENABLED), DEFAULT_AI_ALERT_DOOR_WINDOW_OPEN_ENABLED),
        "ai_alert_door_window_open_delay_minutes": _positive_int(data.get(CONF_AI_ALERT_DOOR_WINDOW_OPEN_DELAY_MINUTES), DEFAULT_AI_ALERT_DOOR_WINDOW_OPEN_DELAY_MINUTES, minimum=1, maximum=120),
        "ai_alert_window_open_instant_enabled": _to_bool(data.get(CONF_AI_ALERT_WINDOW_OPEN_INSTANT_ENABLED), DEFAULT_AI_ALERT_WINDOW_OPEN_INSTANT_ENABLED),
    }



def _panel_entity_store_audit(data: dict[str, Any]) -> dict[str, Any]:
    """Return source/count status for app-panel entity stores."""
    report_entries = _normalize_panel_report_entity_map_panel(data.get(CONF_PANEL_REPORT_ENTITY_MAP, DEFAULT_PANEL_REPORT_ENTITY_MAP))
    ai_entries = _normalize_panel_ai_entity_map_panel(data.get(CONF_PANEL_AI_ENTITY_MAP, DEFAULT_PANEL_AI_ENTITY_MAP))
    dashboard_entries = _normalize_panel_dashboard_entity_map_panel(data.get(CONF_PANEL_DASHBOARD_ENTITY_MAP, DEFAULT_PANEL_DASHBOARD_ENTITY_MAP))
    vehicle_entries = _normalize_vehicle_entity_map_panel(data.get(CONF_VEHICLE_ENTITY_MAP, DEFAULT_VEHICLE_ENTITY_MAP))
    legacy_dashboard_entries = _normalize_dashboard_entity_map_panel(data.get(CONF_DASHBOARD_ENTITY_MAP, []))
    return {
        "reports": {
            "source": "panel_report_entity_map" if report_entries else "legacy_flow_fallback",
            "panel_count": len(report_entries),
            "fallback_vehicle_count": len([item for item in vehicle_entries if item.get("use_report")]),
            "ready": bool(report_entries),
        },
        "ai": {
            "source": "panel_ai_entity_map" if ai_entries else "legacy_flow_fallback",
            "panel_count": len(ai_entries),
            "fallback_vehicle_count": len([item for item in vehicle_entries if item.get("use_ai")]),
            "ready": bool(ai_entries),
        },
        "dashboard": {
            "source": "panel_dashboard_entity_map" if dashboard_entries else "legacy_flow_fallback",
            "panel_count": len(dashboard_entries),
            "fallback_dashboard_count": len(legacy_dashboard_entries),
            "ready": bool(dashboard_entries),
        },
        "migration_needed": not (report_entries and ai_entries and dashboard_entries),
    }


def _build_panel_store_migration_options(hass: HomeAssistant, current: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build non-destructive panel store migration updates from legacy/Flow data."""
    updates: dict[str, Any] = {}
    details: dict[str, Any] = {}

    report_entries = _normalize_panel_report_entity_map_panel(current.get(CONF_PANEL_REPORT_ENTITY_MAP, DEFAULT_PANEL_REPORT_ENTITY_MAP))
    if not report_entries:
        source_entries = _normalize_vehicle_entity_map_panel(current.get(CONF_VEHICLE_ENTITY_MAP, DEFAULT_VEHICLE_ENTITY_MAP))
        migrated: list[dict[str, Any]] = []
        seen_roles: set[str] = set()
        for role in REPORT_ENTITY_MANAGER_ROLES:
            entity_id = _report_role_default_entity(current, source_entries, role)
            if not entity_id or role in seen_roles:
                continue
            item = _report_entry_for_panel(hass, entity_id, role=role, source="migration_from_legacy_flow")
            if item:
                migrated.append(item)
                seen_roles.add(role)
        if migrated:
            updates[CONF_PANEL_REPORT_ENTITY_MAP] = _normalize_panel_report_entity_map_panel(migrated)
            details["reports"] = {"migrated": True, "count": len(migrated)}
        else:
            details["reports"] = {"migrated": False, "count": 0}

    ai_entries = _normalize_panel_ai_entity_map_panel(current.get(CONF_PANEL_AI_ENTITY_MAP, DEFAULT_PANEL_AI_ENTITY_MAP))
    if not ai_entries:
        source_entries = _normalize_vehicle_entity_map_panel(current.get(CONF_VEHICLE_ENTITY_MAP, DEFAULT_VEHICLE_ENTITY_MAP))
        migrated = [item for item in source_entries if item.get("use_ai") and item.get("entity_id")]
        if migrated:
            updates[CONF_PANEL_AI_ENTITY_MAP] = _normalize_panel_ai_entity_map_panel([
                {**item, "source": "migration_from_legacy_flow"} for item in migrated
            ])
            details["ai"] = {"migrated": True, "count": len(updates[CONF_PANEL_AI_ENTITY_MAP])}
        else:
            details["ai"] = {"migrated": False, "count": 0}

    dashboard_entries = _normalize_panel_dashboard_entity_map_panel(current.get(CONF_PANEL_DASHBOARD_ENTITY_MAP, DEFAULT_PANEL_DASHBOARD_ENTITY_MAP))
    if not dashboard_entries:
        source_entries = _normalize_dashboard_entity_map_panel(current.get(CONF_DASHBOARD_ENTITY_MAP, []))
        by_role: dict[str, dict[str, Any]] = {str(item.get("role") or ""): item for item in source_entries if isinstance(item, dict)}
        for legacy_item in _dashboard_legacy_entry_fallbacks(hass, current):
            role = str(legacy_item.get("role") or "")
            if role and role not in by_role:
                by_role[role] = legacy_item
        migrated = []
        for role in DASHBOARD_ENTITY_MANAGER_ROLES:
            item = by_role.get(role)
            if item and str(item.get("entity_id") or "").strip():
                migrated.append({**item, "source": "migration_from_legacy_flow"})
        if migrated:
            updates[CONF_PANEL_DASHBOARD_ENTITY_MAP] = _normalize_panel_dashboard_entity_map_panel(migrated)
            details["dashboard"] = {"migrated": True, "count": len(updates[CONF_PANEL_DASHBOARD_ENTITY_MAP])}
        else:
            details["dashboard"] = {"migrated": False, "count": 0}

    return updates, details


def _ensure_panel_entity_store_migration(hass: HomeAssistant) -> dict[str, Any]:
    """Persist one-time panel store migration if any panel store is empty."""
    entry = _first_config_entry(hass)
    if entry is None:
        return {"success": False, "error": "config_entry_not_found", "changed": False}
    current = {**dict(entry.data or {}), **dict(entry.options or {})}
    updates, details = _build_panel_store_migration_options(hass, current)
    if not updates:
        return {"success": True, "changed": False, "details": details, "audit": _panel_entity_store_audit(current)}
    merged_options = dict(entry.options or {})
    merged_options.update(updates)
    try:
        hass.config_entries.async_update_entry(entry, options=merged_options)
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {**dict(entry.data or {}), **merged_options}
    except Exception as err:
        _LOGGER.exception("Could not migrate panel entity stores")
        return {"success": False, "changed": False, "error": str(err), "details": details}
    migrated = {**dict(entry.data or {}), **merged_options}
    return {"success": True, "changed": True, "details": details, "audit": _panel_entity_store_audit(migrated)}

def _settings_payload(hass: HomeAssistant) -> dict[str, Any]:
    """Return all settings currently managed by the app panel.

    Alpha73 keeps Charging and Trip Settings, and adds Telegram Settings.
    The payload intentionally mirrors existing Options keys so the panel and
    Options Flow remain compatible during the migration period.
    """
    data = _entry_config(hass)
    default_currency = _normalize_currency(data.get(CONF_REPORT_CURRENCY), default=DEFAULT_REPORT_CURRENCY)
    return {
        "success": True,
        "language": _app_language(hass),
        "currency": default_currency,
        "currency_options": list(REPORT_CURRENCY_OPTIONS),
        "general_settings": {
            "app_language": str(data.get(CONF_APP_LANGUAGE) or DEFAULT_APP_LANGUAGE),
            "debug_enabled": _to_bool(data.get("panel_debug_enabled"), False),
            "default_open_tab": str(data.get("panel_default_open_tab") or "settings"),
            "resource_summary": (_dashboard_resources_payload(hass).get("summary", {}) if "_dashboard_resources_payload" in globals() else {}),
            "system": {
                "integration_version": str((hass.config_entries.async_entries(DOMAIN)[0].version if hass.config_entries.async_entries(DOMAIN) else "") or ""),
                "has_config_entry": _first_config_entry(hass) is not None,
                "panel_js_file": PANEL_JS_FILE,
                "panel_js_url": f"/{DOMAIN}/{PANEL_JS_FILE}",
                "emergency_build": "alpha187",
            },
            "entity_store_audit": _panel_entity_store_audit(data),
            "health": _system_health_payload(hass, data),
        },
        "charging": {
            "report_currency": default_currency,
            "charging_report_mode": str(data.get(CONF_CHARGING_REPORT_MODE) or DEFAULT_CHARGING_REPORT_MODE),
            "supercharger_price": round(_to_float(data.get(CONF_SUPERCHARGER_PRICE), DEFAULT_SUPERCHARGER_PRICE), 4),
            "zes_price": round(_to_float(data.get(CONF_ZES_PRICE), DEFAULT_ZES_PRICE), 4),
            "astor_price": round(_to_float(data.get(CONF_ASTOR_PRICE), DEFAULT_ASTOR_PRICE), 4),
            "provider_presets": _effective_provider_presets(data, default_currency=default_currency),
        },
        "ai_settings": _ai_settings_payload(data),
        "dashboard_settings": _dashboard_settings_payload(hass),
        "telegram": {
            "builtin_telegram_enabled": _to_bool(data.get(CONF_BUILTIN_TELEGRAM_ENABLED), DEFAULT_BUILTIN_TELEGRAM_ENABLED),
            "builtin_telegram_bot_token": _mask_secret_for_panel(data.get(CONF_BUILTIN_TELEGRAM_BOT_TOKEN)),
            "builtin_telegram_bot_token_configured": bool(str(data.get(CONF_BUILTIN_TELEGRAM_BOT_TOKEN) or "").strip()),
            "builtin_telegram_bot_token_last4": _secret_last4(data.get(CONF_BUILTIN_TELEGRAM_BOT_TOKEN)),
            "builtin_telegram_poll_enabled": _to_bool(data.get(CONF_BUILTIN_TELEGRAM_POLL_ENABLED), DEFAULT_BUILTIN_TELEGRAM_POLL_ENABLED),
            "builtin_telegram_poll_interval_seconds": _positive_int(
                data.get(CONF_BUILTIN_TELEGRAM_POLL_INTERVAL_SECONDS),
                DEFAULT_BUILTIN_TELEGRAM_POLL_INTERVAL_SECONDS,
                minimum=1,
                maximum=3600,
            ),
            "replies_enabled": bool(str(data.get(CONF_TELEGRAM_TARGET) or data.get(CONF_AI_TELEGRAM_TARGET) or "").strip()),
            "telegram_group_id": str(
                data.get(CONF_AI_TELEGRAM_LISTENER_CHAT_ID)
                or data.get(CONF_AI_TELEGRAM_TARGET)
                or data.get(CONF_TELEGRAM_TARGET)
                or ""
            ).strip(),
            "ai_group_listener_enabled": _to_bool(
                data.get(CONF_AI_TELEGRAM_LISTENER_ENABLED),
                DEFAULT_AI_TELEGRAM_LISTENER_ENABLED,
            ),
            "report_commands": _telegram_report_commands_payload(data),
        },
        "ai_entity_manager": _ai_entity_manager_payload(hass, data),
        "report_entity_manager": _report_entity_manager_payload(hass, data),
        "dashboard_entity_manager": _dashboard_entity_manager_payload(hass, data),
        "trip_reports": {
            "auto_trip_tracking": _to_bool(data.get(CONF_AUTO_TRIP_TRACKING), DEFAULT_AUTO_TRIP_TRACKING),
            "auto_start_speed_threshold": round(_positive_float(data.get(CONF_AUTO_START_SPEED_THRESHOLD), DEFAULT_AUTO_START_SPEED_THRESHOLD, minimum=0.0, maximum=250.0), 2),
            "live_trip_enabled": _to_bool(data.get(CONF_LIVE_TRIP_ENABLED), DEFAULT_LIVE_TRIP_ENABLED),
            "live_trip_update_interval_seconds": _positive_int(data.get(CONF_LIVE_TRIP_UPDATE_INTERVAL_SECONDS), DEFAULT_LIVE_TRIP_UPDATE_INTERVAL_SECONDS, minimum=1, maximum=300),
            "live_trip_traffic_speed_threshold": round(_positive_float(data.get(CONF_LIVE_TRIP_TRAFFIC_SPEED_THRESHOLD), DEFAULT_LIVE_TRIP_TRAFFIC_SPEED_THRESHOLD, minimum=0.0, maximum=250.0), 2),
            "live_trip_finish_delay_seconds": _positive_int(data.get(CONF_LIVE_TRIP_FINISH_DELAY_SECONDS), DEFAULT_LIVE_TRIP_FINISH_DELAY_SECONDS, minimum=1, maximum=3600),
            "live_trip_min_distance_km": round(_positive_float(data.get(CONF_LIVE_TRIP_MIN_DISTANCE_KM), DEFAULT_LIVE_TRIP_MIN_DISTANCE_KM, minimum=0.0, maximum=10000.0), 3),
            "live_trip_ignore_short_maneuvers": _to_bool(data.get(CONF_LIVE_TRIP_IGNORE_SHORT_MANEUVERS), DEFAULT_LIVE_TRIP_IGNORE_SHORT_MANEUVERS),
            "live_trip_candidate_min_distance_km": round(_positive_float(data.get(CONF_LIVE_TRIP_CANDIDATE_MIN_DISTANCE_KM), DEFAULT_LIVE_TRIP_CANDIDATE_MIN_DISTANCE_KM, minimum=0.0, maximum=100.0), 3),
            "live_trip_candidate_min_duration_seconds": _positive_int(data.get(CONF_LIVE_TRIP_CANDIDATE_MIN_DURATION_SECONDS), DEFAULT_LIVE_TRIP_CANDIDATE_MIN_DURATION_SECONDS, minimum=0, maximum=3600),
            "live_trip_ai_segment_distance_km": _live_trip_ai_segment_distance_for_panel(data.get(CONF_LIVE_TRIP_AI_SEGMENT_DISTANCE_KM)),
            "live_trip_ai_segment_distance_options": list(LIVE_TRIP_AI_SEGMENT_DISTANCE_OPTIONS),
            "ai_trip_story_enabled": _to_bool(data.get(CONF_AI_ALERT_POST_TRIP_SUMMARY_ENABLED), DEFAULT_AI_ALERT_POST_TRIP_SUMMARY_ENABLED),
            "ai_trip_story_detail_level": str(data.get(CONF_AI_TRIP_STORY_DETAIL_LEVEL) or DEFAULT_AI_TRIP_STORY_DETAIL_LEVEL) if str(data.get(CONF_AI_TRIP_STORY_DETAIL_LEVEL) or DEFAULT_AI_TRIP_STORY_DETAIL_LEVEL) in AI_TRIP_STORY_DETAIL_OPTIONS else DEFAULT_AI_TRIP_STORY_DETAIL_LEVEL,
            "ai_trip_story_delay_mode": "follow_live_trip_report_delay",
            "trip_map_enabled": _to_bool(data.get(CONF_TRIP_MAP_ENABLED), DEFAULT_TRIP_MAP_ENABLED),
            "trip_map_tracker_entity": str(data.get(CONF_TRIP_MAP_TRACKER_ENTITY) or DEFAULT_TRIP_MAP_TRACKER_ENTITY or "").strip(),
            "trip_map_sample_interval_seconds": _positive_int(data.get(CONF_TRIP_MAP_SAMPLE_INTERVAL_SECONDS), DEFAULT_TRIP_MAP_SAMPLE_INTERVAL_SECONDS, minimum=1, maximum=300),
            "trip_map_min_movement_meters": round(_positive_float(data.get(CONF_TRIP_MAP_MIN_MOVEMENT_METERS), DEFAULT_TRIP_MAP_MIN_MOVEMENT_METERS, minimum=0.0, maximum=10000.0), 2),
            "trip_map_send_separate_png": _to_bool(data.get(CONF_TRIP_MAP_SEND_SEPARATE_PNG), DEFAULT_TRIP_MAP_SEND_SEPARATE_PNG),
            "show_distance": _to_bool(data.get(CONF_SHOW_DISTANCE), DEFAULT_SHOW_DISTANCE),
            "show_duration": _to_bool(data.get(CONF_SHOW_DURATION), DEFAULT_SHOW_DURATION),
            "show_traffic": _to_bool(data.get(CONF_SHOW_TRAFFIC), DEFAULT_SHOW_TRAFFIC),
            "show_average_speed": _to_bool(data.get(CONF_SHOW_AVERAGE_SPEED), DEFAULT_SHOW_AVERAGE_SPEED),
            "show_energy": _to_bool(data.get(CONF_SHOW_ENERGY), DEFAULT_SHOW_ENERGY),
            "show_consumption": _to_bool(data.get(CONF_SHOW_CONSUMPTION), DEFAULT_SHOW_CONSUMPTION),
            "show_battery": _to_bool(data.get(CONF_SHOW_BATTERY), DEFAULT_SHOW_BATTERY),
            "show_cost": _to_bool(data.get(CONF_SHOW_COST), DEFAULT_SHOW_COST),
            "show_climate": _to_bool(data.get(CONF_SHOW_CLIMATE), DEFAULT_SHOW_CLIMATE),
            "show_elevation": _to_bool(data.get(CONF_SHOW_ELEVATION), DEFAULT_SHOW_ELEVATION),
            "show_trip_map": _to_bool(data.get(CONF_SHOW_TRIP_MAP), DEFAULT_SHOW_TRIP_MAP),
        },
    }


def _settings_payload_fast(hass: HomeAssistant) -> dict[str, Any]:
    """Return a lightweight Settings payload for normal panel opens.

    The previous full payload scanned entity options, dashboard resources and
    entity-manager data. On large HA installations that can take ~17-20 seconds
    and block the event loop. Normal Settings opens now receive this fast
    payload; expensive full data can be requested explicitly with ?mode=full.
    """
    data = _entry_config(hass)
    default_currency = _normalize_currency(data.get(CONF_REPORT_CURRENCY), default=DEFAULT_REPORT_CURRENCY)
    lang = _app_language(hass)
    return {
        "success": True,
        "payload_mode": "fast",
        "deferred_full": True,
        "language": lang,
        "currency": default_currency,
        "currency_options": list(REPORT_CURRENCY_OPTIONS),
        "general_settings": {
            "app_language": str(data.get(CONF_APP_LANGUAGE) or DEFAULT_APP_LANGUAGE),
            "debug_enabled": _to_bool(data.get("panel_debug_enabled"), False),
            "default_open_tab": str(data.get("panel_default_open_tab") or "settings"),
            "resource_summary": {"status_deferred": True, "fast_payload": True},
            "system": {
                "integration_version": DASHBOARD_PANEL_VERSION,
                "has_config_entry": _first_config_entry(hass) is not None,
                "panel_js_file": PANEL_JS_FILE,
                "panel_js_url": f"/{DOMAIN}/{PANEL_JS_FILE}",
                "payload_mode": "fast",
            },
            "entity_store_audit": _panel_entity_store_audit(data),
            "health": _system_health_payload(hass, data),
        },
        "charging": {
            "report_currency": default_currency,
            "charging_report_mode": str(data.get(CONF_CHARGING_REPORT_MODE) or DEFAULT_CHARGING_REPORT_MODE),
            "supercharger_price": round(_to_float(data.get(CONF_SUPERCHARGER_PRICE), DEFAULT_SUPERCHARGER_PRICE), 4),
            "zes_price": round(_to_float(data.get(CONF_ZES_PRICE), DEFAULT_ZES_PRICE), 4),
            "astor_price": round(_to_float(data.get(CONF_ASTOR_PRICE), DEFAULT_ASTOR_PRICE), 4),
            "provider_presets": _effective_provider_presets(data, default_currency=default_currency),
        },
        "ai_settings": _ai_settings_payload(data),
        "dashboard_settings": _dashboard_settings_payload_fast(hass, data),
        "telegram": {
            "builtin_telegram_enabled": _to_bool(data.get(CONF_BUILTIN_TELEGRAM_ENABLED), DEFAULT_BUILTIN_TELEGRAM_ENABLED),
            "builtin_telegram_bot_token": _mask_secret_for_panel(data.get(CONF_BUILTIN_TELEGRAM_BOT_TOKEN)),
            "builtin_telegram_bot_token_configured": bool(str(data.get(CONF_BUILTIN_TELEGRAM_BOT_TOKEN) or "").strip()),
            "builtin_telegram_bot_token_last4": _secret_last4(data.get(CONF_BUILTIN_TELEGRAM_BOT_TOKEN)),
            "builtin_telegram_poll_enabled": _to_bool(data.get(CONF_BUILTIN_TELEGRAM_POLL_ENABLED), DEFAULT_BUILTIN_TELEGRAM_POLL_ENABLED),
            "builtin_telegram_poll_interval_seconds": _positive_int(
                data.get(CONF_BUILTIN_TELEGRAM_POLL_INTERVAL_SECONDS),
                DEFAULT_BUILTIN_TELEGRAM_POLL_INTERVAL_SECONDS,
                minimum=1,
                maximum=3600,
            ),
            "replies_enabled": bool(str(data.get(CONF_TELEGRAM_TARGET) or data.get(CONF_AI_TELEGRAM_TARGET) or "").strip()),
            "telegram_group_id": str(
                data.get(CONF_AI_TELEGRAM_LISTENER_CHAT_ID)
                or data.get(CONF_AI_TELEGRAM_TARGET)
                or data.get(CONF_TELEGRAM_TARGET)
                or ""
            ).strip(),
            "ai_group_listener_enabled": _to_bool(
                data.get(CONF_AI_TELEGRAM_LISTENER_ENABLED),
                DEFAULT_AI_TELEGRAM_LISTENER_ENABLED,
            ),
            "report_commands": _telegram_report_commands_payload(data),
        },
        "ai_entity_manager": _ai_entity_manager_payload_fast(hass, data),
        "report_entity_manager": _report_entity_manager_payload_fast(hass, data),
        "dashboard_entity_manager": _dashboard_entity_manager_payload_fast(hass, data),
        "trip_reports": _trip_reports_settings_payload(data),
    }


def _trip_reports_settings_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Return trip/live-trip settings without scanning entities."""
    return {
        "auto_trip_tracking": _to_bool(data.get(CONF_AUTO_TRIP_TRACKING), DEFAULT_AUTO_TRIP_TRACKING),
        "auto_start_speed_threshold": round(_positive_float(data.get(CONF_AUTO_START_SPEED_THRESHOLD), DEFAULT_AUTO_START_SPEED_THRESHOLD, minimum=0.0, maximum=250.0), 2),
        "live_trip_enabled": _to_bool(data.get(CONF_LIVE_TRIP_ENABLED), DEFAULT_LIVE_TRIP_ENABLED),
        "live_trip_update_interval_seconds": _positive_int(data.get(CONF_LIVE_TRIP_UPDATE_INTERVAL_SECONDS), DEFAULT_LIVE_TRIP_UPDATE_INTERVAL_SECONDS, minimum=1, maximum=300),
        "live_trip_traffic_speed_threshold": round(_positive_float(data.get(CONF_LIVE_TRIP_TRAFFIC_SPEED_THRESHOLD), DEFAULT_LIVE_TRIP_TRAFFIC_SPEED_THRESHOLD, minimum=0.0, maximum=250.0), 2),
        "live_trip_finish_delay_seconds": _positive_int(data.get(CONF_LIVE_TRIP_FINISH_DELAY_SECONDS), DEFAULT_LIVE_TRIP_FINISH_DELAY_SECONDS, minimum=1, maximum=3600),
        "live_trip_min_distance_km": round(_positive_float(data.get(CONF_LIVE_TRIP_MIN_DISTANCE_KM), DEFAULT_LIVE_TRIP_MIN_DISTANCE_KM, minimum=0.0, maximum=10000.0), 3),
        "live_trip_ignore_short_maneuvers": _to_bool(data.get(CONF_LIVE_TRIP_IGNORE_SHORT_MANEUVERS), DEFAULT_LIVE_TRIP_IGNORE_SHORT_MANEUVERS),
        "live_trip_candidate_min_distance_km": round(_positive_float(data.get(CONF_LIVE_TRIP_CANDIDATE_MIN_DISTANCE_KM), DEFAULT_LIVE_TRIP_CANDIDATE_MIN_DISTANCE_KM, minimum=0.0, maximum=100.0), 3),
        "live_trip_candidate_min_duration_seconds": _positive_int(data.get(CONF_LIVE_TRIP_CANDIDATE_MIN_DURATION_SECONDS), DEFAULT_LIVE_TRIP_CANDIDATE_MIN_DURATION_SECONDS, minimum=0, maximum=3600),
        "live_trip_ai_segment_distance_km": _live_trip_ai_segment_distance_for_panel(data.get(CONF_LIVE_TRIP_AI_SEGMENT_DISTANCE_KM)),
        "live_trip_ai_segment_distance_options": list(LIVE_TRIP_AI_SEGMENT_DISTANCE_OPTIONS),
        "ai_trip_story_enabled": _to_bool(data.get(CONF_AI_ALERT_POST_TRIP_SUMMARY_ENABLED), DEFAULT_AI_ALERT_POST_TRIP_SUMMARY_ENABLED),
        "ai_trip_story_detail_level": str(data.get(CONF_AI_TRIP_STORY_DETAIL_LEVEL) or DEFAULT_AI_TRIP_STORY_DETAIL_LEVEL) if str(data.get(CONF_AI_TRIP_STORY_DETAIL_LEVEL) or DEFAULT_AI_TRIP_STORY_DETAIL_LEVEL) in AI_TRIP_STORY_DETAIL_OPTIONS else DEFAULT_AI_TRIP_STORY_DETAIL_LEVEL,
        "ai_trip_story_delay_mode": "follow_live_trip_report_delay",
        "trip_map_enabled": _to_bool(data.get(CONF_TRIP_MAP_ENABLED), DEFAULT_TRIP_MAP_ENABLED),
        "trip_map_tracker_entity": str(data.get(CONF_TRIP_MAP_TRACKER_ENTITY) or DEFAULT_TRIP_MAP_TRACKER_ENTITY or "").strip(),
        "trip_map_sample_interval_seconds": _positive_int(data.get(CONF_TRIP_MAP_SAMPLE_INTERVAL_SECONDS), DEFAULT_TRIP_MAP_SAMPLE_INTERVAL_SECONDS, minimum=1, maximum=300),
        "trip_map_min_movement_meters": round(_positive_float(data.get(CONF_TRIP_MAP_MIN_MOVEMENT_METERS), DEFAULT_TRIP_MAP_MIN_MOVEMENT_METERS, minimum=0.0, maximum=10000.0), 2),
        "trip_map_send_separate_png": _to_bool(data.get(CONF_TRIP_MAP_SEND_SEPARATE_PNG), DEFAULT_TRIP_MAP_SEND_SEPARATE_PNG),
        "show_distance": _to_bool(data.get(CONF_SHOW_DISTANCE), DEFAULT_SHOW_DISTANCE),
        "show_duration": _to_bool(data.get(CONF_SHOW_DURATION), DEFAULT_SHOW_DURATION),
        "show_traffic": _to_bool(data.get(CONF_SHOW_TRAFFIC), DEFAULT_SHOW_TRAFFIC),
        "show_average_speed": _to_bool(data.get(CONF_SHOW_AVERAGE_SPEED), DEFAULT_SHOW_AVERAGE_SPEED),
        "show_energy": _to_bool(data.get(CONF_SHOW_ENERGY), DEFAULT_SHOW_ENERGY),
        "show_consumption": _to_bool(data.get(CONF_SHOW_CONSUMPTION), DEFAULT_SHOW_CONSUMPTION),
        "show_battery": _to_bool(data.get(CONF_SHOW_BATTERY), DEFAULT_SHOW_BATTERY),
        "show_cost": _to_bool(data.get(CONF_SHOW_COST), DEFAULT_SHOW_COST),
        "show_climate": _to_bool(data.get(CONF_SHOW_CLIMATE), DEFAULT_SHOW_CLIMATE),
        "show_elevation": _to_bool(data.get(CONF_SHOW_ELEVATION), DEFAULT_SHOW_ELEVATION),
        "show_trip_map": _to_bool(data.get(CONF_SHOW_TRIP_MAP), DEFAULT_SHOW_TRIP_MAP),
        "telegram_weekly_trip_report_enabled": _to_bool(data.get(CONF_TELEGRAM_WEEKLY_TRIP_REPORT_ENABLED), DEFAULT_TELEGRAM_WEEKLY_TRIP_REPORT_ENABLED),
        "telegram_monthly_trip_report_enabled": _to_bool(data.get(CONF_TELEGRAM_MONTHLY_TRIP_REPORT_ENABLED), DEFAULT_TELEGRAM_MONTHLY_TRIP_REPORT_ENABLED),
        "telegram_weekly_charge_report_enabled": _to_bool(data.get(CONF_TELEGRAM_WEEKLY_CHARGE_REPORT_ENABLED), DEFAULT_TELEGRAM_WEEKLY_CHARGE_REPORT_ENABLED),
        "telegram_monthly_charge_report_enabled": _to_bool(data.get(CONF_TELEGRAM_MONTHLY_CHARGE_REPORT_ENABLED), DEFAULT_TELEGRAM_MONTHLY_CHARGE_REPORT_ENABLED),
    }


def _ai_entity_manager_payload_fast(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Return stored AI entity-manager data without building global entity options."""
    lang = _app_language(hass)
    panel_ai_entries = _normalize_panel_ai_entity_map_panel(data.get(CONF_PANEL_AI_ENTITY_MAP, DEFAULT_PANEL_AI_ENTITY_MAP))
    entries = panel_ai_entries or _normalize_vehicle_entity_map_panel(data.get(CONF_VEHICLE_ENTITY_MAP, DEFAULT_VEHICLE_ENTITY_MAP))
    return {
        "main_entity": str(data.get(CONF_AI_MAIN_TESLA_ENTITY) or DEFAULT_AI_MAIN_TESLA_ENTITY or "").strip(),
        "auto_discover_device_entities": _to_bool(data.get(CONF_AI_AUTO_DISCOVER_DEVICE_ENTITIES), DEFAULT_AI_AUTO_DISCOVER_DEVICE_ENTITIES),
        "extra_context_entities": list(data.get(CONF_AI_EXTRA_CONTEXT_ENTITIES, DEFAULT_AI_EXTRA_CONTEXT_ENTITIES) or []),
        "excluded_context_entities": list(data.get(CONF_AI_EXCLUDED_CONTEXT_ENTITIES, DEFAULT_AI_EXCLUDED_CONTEXT_ENTITIES) or []),
        "entries": entries,
        "auto_find_summary": _entity_confidence_summary_panel(entries),
        "roles": [
            {
                "role": role,
                "label": _role_label(role, lang),
                "description": _role_description(role, lang),
                "category": _slot_category(role),
                "category_label": _category_label(_slot_category(role), lang),
                "expected_entity": _slot_expected_entity(role),
            }
            for role in AI_ENTITY_MANAGER_ROLES
        ],
        "entity_options": [],
        "summary": {
            "entry_count": len(entries),
            "ai_count": len([item for item in entries if item.get("use_ai")]),
            "report_count": len([item for item in entries if item.get("use_report")]),
            "map_count": len([item for item in entries if item.get("use_map")]),
            "source": "panel_ai_entity_map" if panel_ai_entries else "legacy_flow_fallback",
            "entity_options_deferred": True,
        },
    }


def _report_entity_manager_payload_fast(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Return stored Report entity-manager data without building global entity options."""
    lang = _app_language(hass)
    panel_store_entries = _normalize_panel_report_entity_map_panel(data.get(CONF_PANEL_REPORT_ENTITY_MAP, DEFAULT_PANEL_REPORT_ENTITY_MAP))
    entries = panel_store_entries or _normalize_vehicle_entity_map_panel(data.get(CONF_VEHICLE_ENTITY_MAP, DEFAULT_VEHICLE_ENTITY_MAP))
    return {
        "main_entity": _report_role_default_entity(data, entries, VEHICLE_ROLE_BATTERY_LEVEL) or str(data.get(CONF_AI_MAIN_TESLA_ENTITY) or DEFAULT_AI_MAIN_TESLA_ENTITY or "").strip(),
        "entries": entries,
        "roles": [
            {
                "role": role,
                "label": _role_label(role, lang),
                "description": _role_description(role, lang),
                "category": _slot_category(role),
                "category_label": _category_label(_slot_category(role), lang),
                "expected_entity": _slot_expected_entity(role),
            }
            for role in REPORT_ENTITY_MANAGER_ROLES
        ],
        "entity_options": [],
        "summary": {
            "report_count": len([item for item in entries if item.get("entity_id")]),
            "role_count": len(REPORT_ENTITY_MANAGER_ROLES),
            "map_count": len([item for item in entries if item.get("use_map")]),
            "binding": _report_binding_audit_panel(data),
            "source": "panel_report_entity_map" if panel_store_entries else "legacy_flow_fallback",
            "entity_options_deferred": True,
        },
    }


def _dashboard_entity_manager_payload_fast(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Return stored Dashboard entity-manager data without legacy fallback scans."""
    lang = _app_language(hass)
    panel_dashboard_entries = _normalize_panel_dashboard_entity_map_panel(data.get(CONF_PANEL_DASHBOARD_ENTITY_MAP, DEFAULT_PANEL_DASHBOARD_ENTITY_MAP))
    entries = panel_dashboard_entries or _normalize_dashboard_entity_map_panel(data.get(CONF_DASHBOARD_ENTITY_MAP, []))
    return {
        "main_entity": str(data.get(CONF_DASHBOARD_MAIN_ENTITY) or data.get(CONF_AI_MAIN_TESLA_ENTITY) or DEFAULT_AI_MAIN_TESLA_ENTITY or "").strip(),
        "entries": entries,
        "roles": [
            {
                "role": str(slot.get("role") or ""),
                "label": _dashboard_role_label(str(slot.get("role") or ""), lang),
                "description": _dashboard_role_description(str(slot.get("role") or ""), lang),
                "category": str(slot.get("category") or "other"),
                "category_label": _category_label(str(slot.get("category") or "other"), lang),
                "expected_entity": str(slot.get("expected_entity") or "").strip(),
            }
            for slot in DASHBOARD_ENTITY_SLOT_DEFINITIONS
        ],
        "entity_options": [],
        "summary": {
            "dashboard_count": len([item for item in entries if item.get("entity_id")]),
            "role_count": len(DASHBOARD_ENTITY_MANAGER_ROLES),
            "missing_count": max(0, len(DASHBOARD_ENTITY_MANAGER_ROLES) - len([item for item in entries if item.get("entity_id")])),
            "source": "panel_dashboard_entity_map" if panel_dashboard_entries else "legacy_flow_fallback",
            "entity_options_deferred": True,
        },
    }



# Backward-compatible alias used by older code comments/docs.
def _charging_settings_payload(hass: HomeAssistant) -> dict[str, Any]:
    return _settings_payload_fast(hass)


def _to_float(value: Any, default: float = 0.0) -> float:
    if isinstance(value, (int, float)):
        try:
            return float(value)
        except Exception:
            return default
    text = str(value or "").strip().replace(" ", "")
    if not text:
        return default
    # Accept Turkish/European decimal comma and basic thousands separators.
    if "," in text and "." in text:
        # 1.234,56 -> 1234.56 ; 1,234.56 -> 1234.56
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    else:
        text = text.replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return default


def _display_now() -> str:
    return datetime.now().strftime("%d.%m.%Y %H:%M")


def _month_from_created_or_now(created_at: str | None = None) -> str:
    raw = str(created_at or "").strip()
    if len(raw) >= 7 and raw[4] == "-":
        return raw[:7]
    return datetime.now().strftime("%Y-%m")


def _new_charge_record_id(*, provider: str, added_kwh: float, total_cost: float) -> str:
    now = datetime.now()
    return "|".join(
        [
            now.strftime("%Y-%m"),
            now.isoformat(timespec="seconds"),
            str(provider or "").strip().lower(),
            f"{added_kwh:.3f}",
            f"{total_cost:.2f}",
        ]
    )


def _new_trip_record_id(*, display_at: str, trip_km: float, used_kwh: float, start_address: str, end_address: str) -> str:
    now = datetime.now()
    return "|".join(
        [
            now.strftime("%Y-%m"),
            now.isoformat(timespec="seconds"),
            str(display_at or "").strip(),
            f"{trip_km:.3f}",
            f"{used_kwh:.3f}",
            str(start_address or "").strip().lower(),
            str(end_address or "").strip().lower(),
        ]
    )


def _normalize_charge_record(raw: dict[str, Any], *, default_currency: str) -> dict[str, Any]:
    provider = str(raw.get("provider") or raw.get("name") or "Manual").strip() or "Manual"
    added_kwh = round(_to_float(raw.get("added_kwh"), 0.0), 3)
    total_cost = round(_to_float(raw.get("total_cost"), 0.0), 2)
    price_per_kwh = _to_float(raw.get("price_per_kwh"), 0.0)
    if price_per_kwh <= 0 and added_kwh > 0:
        price_per_kwh = total_cost / added_kwh
    price_per_kwh = round(price_per_kwh, 4)
    currency_label = str(raw.get("currency_label") or default_currency).strip() or default_currency
    created_at = str(raw.get("created_at") or datetime.now().isoformat(timespec="seconds")).strip()
    display_at = str(raw.get("display_at") or _display_now()).strip()
    month_key = str(raw.get("month_key") or _month_from_created_or_now(created_at)).strip()
    record_id = str(raw.get("id") or "").strip() or _new_charge_record_id(
        provider=provider,
        added_kwh=added_kwh,
        total_cost=total_cost,
    )
    return {
        **raw,
        "id": record_id,
        "month_key": month_key,
        "created_at": created_at,
        "display_at": display_at,
        "provider": provider,
        "added_kwh": added_kwh,
        "price_per_kwh": price_per_kwh,
        "total_cost": total_cost,
        "currency_label": currency_label,
        "average_speed": round(_to_float(raw.get("average_speed"), 0.0), 1),
        "average_moving_speed": round(_to_float(raw.get("average_moving_speed", raw.get("average_speed")), 0.0), 1),
        "average_overall_speed": round(_to_float(raw.get("average_overall_speed"), 0.0), 1),
        "moving_seconds": round(_to_float(raw.get("moving_seconds"), 0.0), 0),
        "moving_minutes": round(_to_float(raw.get("moving_minutes"), 0.0), 2),
        "moving_duration_text": str(raw.get("moving_duration_text") or "").strip(),
        "non_moving_seconds": round(_to_float(raw.get("non_moving_seconds"), 0.0), 0),
        "speed_sample_count": int(_to_float(raw.get("speed_sample_count"), 0.0)),
        "moving_speed_sample_count": int(_to_float(raw.get("moving_speed_sample_count"), 0.0)),
        "max_speed": round(_to_float(raw.get("max_speed"), 0.0), 1),
        "moving_speed_threshold": round(_to_float(raw.get("moving_speed_threshold"), 1.0), 1),
        "speed_sampler_interval_seconds": int(_to_float(raw.get("speed_sampler_interval_seconds"), 1.0)),
        "source": str(raw.get("source") or "panel_manual").strip() or "panel_manual",
    }


def _visible_charge_record(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(item.get("id") or ""),
        "month_key": str(item.get("month_key") or ""),
        "created_at": str(item.get("created_at") or ""),
        "display_at": str(item.get("display_at") or ""),
        "provider": str(item.get("provider") or ""),
        "added_kwh": _to_float(item.get("added_kwh"), 0.0),
        "price_per_kwh": _to_float(item.get("price_per_kwh"), 0.0),
        "total_cost": _to_float(item.get("total_cost"), 0.0),
        "currency_label": str(item.get("currency_label") or ""),
        "source": str(item.get("source") or ""),
        "location_label": str(item.get("location_label") or ""),
    }


def _charge_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    now_key = datetime.now().strftime("%Y-%m")
    active = [item for item in records if str(item.get("month_key") or "") == now_key]
    by_currency: dict[str, float] = {}
    total_kwh = 0.0
    for item in active:
        total_kwh += _to_float(item.get("added_kwh"), 0.0)
        currency = str(item.get("currency_label") or "").strip() or "-"
        by_currency[currency] = by_currency.get(currency, 0.0) + _to_float(item.get("total_cost"), 0.0)
    return {
        "month_key": now_key,
        "count": len(active),
        "total_kwh": round(total_kwh, 3),
        "total_cost_by_currency": {key: round(value, 2) for key, value in sorted(by_currency.items())},
    }


def _normalize_trip_record(raw: dict[str, Any], *, default_currency: str) -> dict[str, Any]:
    created_at = str(raw.get("created_at") or datetime.now().isoformat(timespec="seconds")).strip()
    display_at = str(raw.get("display_at") or raw.get("report_date") or _display_now()).strip()
    month_key = str(raw.get("month_key") or _month_from_created_or_now(created_at)).strip()
    start_address = str(raw.get("start_address") or "").strip()
    end_address = str(raw.get("end_address") or "").strip()
    trip_km = round(_to_float(raw.get("trip_km"), 0.0), 3)
    duration_minutes = round(_to_float(raw.get("duration_minutes"), 0.0), 2)
    duration_text = str(raw.get("duration_text") or "").strip()
    used_kwh = round(_to_float(raw.get("used_kwh"), 0.0), 3)
    consumption = _to_float(raw.get("consumption_kwh_100km"), 0.0)
    if consumption <= 0 and trip_km > 0 and used_kwh >= 0:
        consumption = used_kwh / trip_km * 100.0
    total_cost = round(_to_float(raw.get("total_cost"), 0.0), 2)
    currency_label = str(raw.get("currency_label") or default_currency).strip() or default_currency
    record_id = str(raw.get("id") or "").strip() or _new_trip_record_id(
        display_at=display_at,
        trip_km=trip_km,
        used_kwh=used_kwh,
        start_address=start_address,
        end_address=end_address,
    )
    return {
        **raw,
        "id": record_id,
        "month_key": month_key,
        "created_at": created_at,
        "display_at": display_at,
        "start_address": start_address,
        "end_address": end_address,
        "trip_km": trip_km,
        "duration_text": duration_text,
        "duration_minutes": duration_minutes,
        "report_duration_seconds": round(_to_float(raw.get("report_duration_seconds", duration_minutes * 60.0), 0.0), 0),
        "report_duration_text": str(raw.get("report_duration_text") or duration_text).strip(),
        "total_elapsed_seconds": round(_to_float(raw.get("total_elapsed_seconds"), 0.0), 0),
        "total_elapsed_text": str(raw.get("total_elapsed_text") or "").strip(),
        "final_park_wait_seconds": round(_to_float(raw.get("final_park_wait_seconds"), 0.0), 0),
        "final_park_wait_text": str(raw.get("final_park_wait_text") or "").strip(),
        "used_kwh": used_kwh,
        "consumption_kwh_100km": round(consumption, 3),
        "total_cost": total_cost,
        "currency_label": currency_label,
        "average_speed": round(_to_float(raw.get("average_speed"), 0.0), 1),
        "average_moving_speed": round(_to_float(raw.get("average_moving_speed", raw.get("average_speed")), 0.0), 1),
        "average_overall_speed": round(_to_float(raw.get("average_overall_speed"), 0.0), 1),
        "moving_seconds": round(_to_float(raw.get("moving_seconds"), 0.0), 0),
        "moving_minutes": round(_to_float(raw.get("moving_minutes"), 0.0), 2),
        "moving_duration_text": str(raw.get("moving_duration_text") or "").strip(),
        "non_moving_seconds": round(_to_float(raw.get("non_moving_seconds"), 0.0), 0),
        "speed_sample_count": int(_to_float(raw.get("speed_sample_count"), 0.0)),
        "moving_speed_sample_count": int(_to_float(raw.get("moving_speed_sample_count"), 0.0)),
        "max_speed": round(_to_float(raw.get("max_speed"), 0.0), 1),
        "moving_speed_threshold": round(_to_float(raw.get("moving_speed_threshold"), 1.0), 1),
        "speed_sampler_interval_seconds": int(_to_float(raw.get("speed_sampler_interval_seconds"), 1.0)),
        "traffic_seconds": round(_to_float(raw.get("traffic_seconds"), 0.0), 0),
        "stopped_in_drive_seconds": round(_to_float(raw.get("stopped_in_drive_seconds"), 0.0), 0),
        "stopped_in_drive_text": str(raw.get("stopped_in_drive_text") or "").strip(),
        "slow_traffic_seconds": round(_to_float(raw.get("slow_traffic_seconds"), 0.0), 0),
        "slow_traffic_text": str(raw.get("slow_traffic_text") or "").strip(),
        "normal_drive_seconds": round(_to_float(raw.get("normal_drive_seconds"), 0.0), 0),
        "normal_drive_text": str(raw.get("normal_drive_text") or "").strip(),
        "parked_pause_seconds": round(_to_float(raw.get("parked_pause_seconds"), 0.0), 0),
        "parked_pause_text": str(raw.get("parked_pause_text") or "").strip(),
        "last_traffic_class": str(raw.get("last_traffic_class") or "").strip(),
        "effective_traffic_delay_seconds": round(_to_float(raw.get("effective_traffic_delay_seconds"), _to_float(raw.get("traffic_delay_seconds"), 0.0)), 0),
        "effective_traffic_delay_text": str(raw.get("effective_traffic_delay_text") or "").strip(),
        "traffic_effective_impact_label": str(raw.get("traffic_effective_impact_label") or raw.get("effective_traffic_impact") or "").strip(),
        "effective_traffic_impact": str(raw.get("effective_traffic_impact") or raw.get("traffic_effective_impact_label") or "").strip(),
        "slowdown_reason": str(raw.get("slowdown_reason") or "").strip(),
        "slowdown_reason_label": str(raw.get("slowdown_reason_label") or "").strip(),
        "traffic_confidence": str(raw.get("traffic_confidence") or "").strip(),
        "raw_low_speed_percent": round(_to_float(raw.get("raw_low_speed_percent"), _to_float(raw.get("traffic_ratio_moving_percent"), 0.0)), 1),
        "raw_low_speed_seconds": round(_to_float(raw.get("raw_low_speed_seconds"), _to_float(raw.get("traffic_seconds"), 0.0)), 0),
        "raw_low_speed_text": str(raw.get("raw_low_speed_text") or raw.get("traffic_text") or "").strip(),
        "source": str(raw.get("source") or "panel_manual").strip() or "panel_manual",
    }


def _is_manual_tracking_trip_record(item: dict[str, Any] | None) -> bool:
    """Return True for manual tracking entries kept in the shared trip ledger."""
    if not isinstance(item, dict):
        return False
    source = str(item.get("source") or "").strip().lower().replace("-", "_").replace(" ", "_")
    return "manual_tracking" in source or source in {"manual", "manualtracking"}


def _visible_trip_record(item: dict[str, Any]) -> dict[str, Any]:
    display_at = str(item.get("display_at") or item.get("report_date") or item.get("date") or "").strip()
    created_at = str(item.get("created_at") or "").strip()
    start_address = str(item.get("start_address") or item.get("origin") or item.get("from") or "").strip()
    end_address = str(item.get("end_address") or item.get("destination") or item.get("to") or "").strip()
    trip_km = _to_float(item.get("trip_km", item.get("distance_km", item.get("distance"))), 0.0)
    used_kwh = _to_float(item.get("used_kwh", item.get("energy_kwh", item.get("total_energy_kwh"))), 0.0)
    consumption = _to_float(item.get("consumption_kwh_100km", item.get("consumption")), 0.0)
    if consumption <= 0 and trip_km > 0 and used_kwh >= 0:
        consumption = used_kwh / trip_km * 100.0
    duration_minutes = _to_float(item.get("duration_minutes", item.get("duration_min")), 0.0)
    if duration_minutes <= 0:
        duration_seconds = _to_float(item.get("duration_seconds", item.get("duration_sec")), 0.0)
        if duration_seconds > 0:
            duration_minutes = duration_seconds / 60.0
    record_id = str(item.get("id") or "").strip()
    if not record_id:
        record_id = _new_trip_record_id(
            display_at=display_at or created_at or _display_now(),
            trip_km=trip_km,
            used_kwh=used_kwh,
            start_address=start_address,
            end_address=end_address,
        )
    month_key = str(item.get("month_key") or _month_from_created_or_now(created_at)).strip()
    return {
        "id": record_id,
        "month_key": month_key,
        "created_at": created_at,
        "display_at": display_at,
        "start_address": start_address,
        "end_address": end_address,
        "trip_km": trip_km,
        "duration_text": str(item.get("duration_text") or ""),
        "duration_minutes": duration_minutes,
        "report_duration_seconds": round(_to_float(item.get("report_duration_seconds", duration_minutes * 60.0), 0.0), 0),
        "report_duration_text": str(item.get("report_duration_text") or item.get("duration_text") or ""),
        "total_elapsed_seconds": round(_to_float(item.get("total_elapsed_seconds"), 0.0), 0),
        "total_elapsed_text": str(item.get("total_elapsed_text") or ""),
        "final_park_wait_seconds": round(_to_float(item.get("final_park_wait_seconds"), 0.0), 0),
        "final_park_wait_text": str(item.get("final_park_wait_text") or ""),
        "used_kwh": used_kwh,
        "consumption_kwh_100km": consumption,
        "total_cost": _to_float(item.get("total_cost", item.get("cost")), 0.0),
        "currency_label": str(item.get("currency_label") or item.get("currency") or ""),
        "average_speed": round(_to_float(item.get("average_speed"), 0.0), 1),
        "average_moving_speed": round(_to_float(item.get("average_moving_speed", item.get("average_speed")), 0.0), 1),
        "average_overall_speed": round(_to_float(item.get("average_overall_speed"), 0.0), 1),
        "moving_seconds": round(_to_float(item.get("moving_seconds"), 0.0), 0),
        "moving_minutes": round(_to_float(item.get("moving_minutes"), 0.0), 2),
        "moving_duration_text": str(item.get("moving_duration_text") or ""),
        "non_moving_seconds": round(_to_float(item.get("non_moving_seconds"), 0.0), 0),
        "speed_sample_count": int(_to_float(item.get("speed_sample_count"), 0.0)),
        "moving_speed_sample_count": int(_to_float(item.get("moving_speed_sample_count"), 0.0)),
        "max_speed": round(_to_float(item.get("max_speed"), 0.0), 1),
        "moving_speed_threshold": round(_to_float(item.get("moving_speed_threshold"), 1.0), 1),
        "speed_sampler_interval_seconds": int(_to_float(item.get("speed_sampler_interval_seconds"), 1.0)),
        "traffic_seconds": round(_to_float(item.get("traffic_seconds"), 0.0), 0),
        "stopped_in_drive_seconds": round(_to_float(item.get("stopped_in_drive_seconds"), 0.0), 0),
        "stopped_in_drive_text": str(item.get("stopped_in_drive_text") or ""),
        "slow_traffic_seconds": round(_to_float(item.get("slow_traffic_seconds"), 0.0), 0),
        "slow_traffic_text": str(item.get("slow_traffic_text") or ""),
        "normal_drive_seconds": round(_to_float(item.get("normal_drive_seconds"), 0.0), 0),
        "normal_drive_text": str(item.get("normal_drive_text") or ""),
        "parked_pause_seconds": round(_to_float(item.get("parked_pause_seconds"), 0.0), 0),
        "parked_pause_text": str(item.get("parked_pause_text") or ""),
        "last_traffic_class": str(item.get("last_traffic_class") or ""),
        "effective_traffic_delay_seconds": round(_to_float(item.get("effective_traffic_delay_seconds"), _to_float(item.get("traffic_delay_seconds"), 0.0)), 0),
        "effective_traffic_delay_text": str(item.get("effective_traffic_delay_text") or ""),
        "traffic_effective_impact_label": str(item.get("traffic_effective_impact_label") or item.get("effective_traffic_impact") or ""),
        "effective_traffic_impact": str(item.get("effective_traffic_impact") or item.get("traffic_effective_impact_label") or ""),
        "slowdown_reason": str(item.get("slowdown_reason") or ""),
        "slowdown_reason_label": str(item.get("slowdown_reason_label") or ""),
        "traffic_confidence": str(item.get("traffic_confidence") or ""),
        "raw_low_speed_percent": round(_to_float(item.get("raw_low_speed_percent"), _to_float(item.get("traffic_ratio_moving_percent"), 0.0)), 1),
        "raw_low_speed_seconds": round(_to_float(item.get("raw_low_speed_seconds"), _to_float(item.get("traffic_seconds"), 0.0)), 0),
        "raw_low_speed_text": str(item.get("raw_low_speed_text") or item.get("traffic_text") or ""),
        "source": str(item.get("source") or ""),
        "ai_summary": str(item.get("ai_summary") or ""),
        "ai_summary_at": str(item.get("ai_summary_at") or ""),
        "ai_summary_detail_level": str(item.get("ai_summary_detail_level") or item.get("ai_story_detail_level") or ""),
        "ai_summary_telegram_status": str(item.get("ai_summary_telegram_status") or ""),
        "ai_summary_source": str(item.get("ai_summary_source") or ""),
        "map_point_count": int(_to_float(item.get("map_point_count"), 0.0)),
        "map_path": str(item.get("map_path") or item.get("embedded_map_path") or ""),
    }


def _trip_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    now_key = datetime.now().strftime("%Y-%m")
    active = [item for item in records if str(item.get("month_key") or "") == now_key]
    total_distance = sum(_to_float(item.get("trip_km"), 0.0) for item in active)
    total_energy = sum(_to_float(item.get("used_kwh"), 0.0) for item in active)
    total_cost = sum(_to_float(item.get("total_cost"), 0.0) for item in active)
    total_duration = sum(_to_float(item.get("duration_minutes"), 0.0) for item in active)
    avg_consumption = (total_energy / total_distance * 100.0) if total_distance > 0 else 0.0
    return {
        "month_key": now_key,
        "count": len(active),
        "total_distance_km": round(total_distance, 3),
        "total_energy_kwh": round(total_energy, 3),
        "total_cost": round(total_cost, 2),
        "total_duration_minutes": round(total_duration, 2),
        "average_consumption_kwh_100km": round(avg_consumption, 3),
    }



def _record_map_entry_option(hass: HomeAssistant, key: str, default: Any = None) -> Any:
    """Read an integration option safely for panel record-map endpoints."""
    try:
        entries = hass.config_entries.async_entries(DOMAIN)
        if not entries:
            return default
        entry = entries[0]
        combined = {**dict(entry.data or {}), **dict(entry.options or {})}
        return combined.get(key, default)
    except Exception:
        return default


def _record_maps_output_dir(hass: HomeAssistant) -> Path:
    path = Path(hass.config.path("www", DOMAIN, "panel_maps"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def _safe_record_map_token(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode("ascii")
    text = "".join(ch.lower() if ch.isalnum() else "_" for ch in text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "record"


def _public_record_map_url(file_path: Path) -> str:
    stamp = int(file_path.stat().st_mtime_ns) if file_path.exists() else int(time.time() * 1_000_000)
    return f"/local/{DOMAIN}/panel_maps/{file_path.name}?v={stamp}"


def _extract_coord_from_record(item: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        if key in item and item.get(key) not in (None, ""):
            try:
                return float(item.get(key))
            except Exception:
                continue
    return None


def _extract_point_list(raw_points: Any) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    if not isinstance(raw_points, list):
        return points
    for item in raw_points:
        lat: float | None = None
        lon: float | None = None
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            try:
                lat = float(item[0])
                lon = float(item[1])
            except Exception:
                lat = None
                lon = None
        elif isinstance(item, dict):
            lat = _extract_coord_from_record(item, "lat", "latitude")
            lon = _extract_coord_from_record(item, "lon", "lng", "longitude")
        if lat is None or lon is None:
            continue
        points.append((lat, lon))
    return points


def _extract_route_points_with_metadata(raw_points: Any) -> list[dict[str, Any]]:
    """Return map points preserving speed/elevation so Trip Records can show colored routes."""
    points: list[dict[str, Any]] = []
    if not isinstance(raw_points, list):
        return points
    for item in raw_points:
        lat: float | None = None
        lon: float | None = None
        out: dict[str, Any] = {}
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            try:
                lat = float(item[0])
                lon = float(item[1])
            except Exception:
                lat = None
                lon = None
            if len(item) >= 3 and item[2] is not None:
                try:
                    out["speed"] = float(item[2])
                except Exception:
                    pass
            if len(item) >= 4 and item[3] is not None:
                try:
                    out["elevation"] = float(item[3])
                except Exception:
                    pass
        elif isinstance(item, dict):
            lat = _extract_coord_from_record(item, "lat", "latitude")
            lon = _extract_coord_from_record(item, "lon", "lng", "longitude")
            if item.get("speed") is not None:
                try:
                    out["speed"] = float(item.get("speed"))
                except Exception:
                    pass
            if item.get("elevation") is not None:
                try:
                    out["elevation"] = float(item.get("elevation"))
                except Exception:
                    pass
            if item.get("ts") is not None:
                out["ts"] = str(item.get("ts"))
        if lat is None or lon is None:
            continue
        out["lat"] = lat
        out["lon"] = lon
        points.append(out)
    return points


async def _async_geocode_text(hass: HomeAssistant, query: str) -> dict[str, Any] | None:
    text = str(query or "").strip()
    if not text:
        return None
    cache = hass.data.setdefault(DOMAIN, {}).setdefault("panel_geocode_cache", {})
    cache_key = text.casefold()
    cached = cache.get(cache_key)
    if isinstance(cached, dict):
        return cached

    session = async_get_clientsession(hass)
    url = "https://nominatim.openstreetmap.org/search"
    headers = {
        "User-Agent": "POMTeslaReport/alpha173 (Home Assistant custom integration)",
        "Accept": "application/json",
    }
    try:
        async with session.get(
            url,
            params={"format": "jsonv2", "limit": 1, "q": text},
            headers=headers,
            timeout=12,
        ) as response:
            if response.status != 200:
                return None
            payload = await response.json()
    except (ClientError, asyncio.TimeoutError, ValueError):
        return None
    except Exception:
        return None

    if not isinstance(payload, list) or not payload:
        return None
    item = payload[0] or {}
    try:
        lat = float(item.get("lat"))
        lon = float(item.get("lon"))
    except Exception:
        return None
    result = {
        "lat": lat,
        "lon": lon,
        "display_name": str(item.get("display_name") or text).strip() or text,
    }
    cache[cache_key] = result
    return result


async def _async_build_charge_record_map(hass: HomeAssistant, record: dict[str, Any]) -> dict[str, Any]:
    provider = str(record.get("provider") or "Charge").strip() or "Charge"
    display_at = str(record.get("display_at") or "").strip()
    location_label = str(record.get("location_label") or record.get("location") or "").strip()
    full_address = str(record.get("full_address") or record.get("address") or record.get("location_address") or "").strip()
    lat = _extract_coord_from_record(record, "latitude", "lat")
    lon = _extract_coord_from_record(record, "longitude", "lon", "lng")

    if (lat is None or lon is None) and location_label.casefold() in {"ev", "home"}:
        try:
            lat = float(hass.config.latitude)
            lon = float(hass.config.longitude)
            full_address = full_address or location_label
        except Exception:
            pass

    if lat is None or lon is None:
        query = full_address or location_label
        if query:
            geocoded = await _async_geocode_text(hass, query)
            if geocoded:
                lat = geocoded["lat"]
                lon = geocoded["lon"]
                full_address = full_address or str(geocoded.get("display_name") or query)

    image_url = ""
    if lat is not None and lon is not None:
        output_dir = _record_maps_output_dir(hass)
        file_path = output_dir / f"charge_{_safe_record_map_token(record.get('id'))}.png"
        data = {
            "lat": lat,
            "lon": lon,
            "address": full_address or location_label or provider,
            "title": provider,
            "subtitle": display_at or (location_label or f"{lat:.5f}, {lon:.5f}"),
        }
        await asyncio.to_thread(render_vehicle_location_map_png, data, str(file_path))
        image_url = _public_record_map_url(file_path)

    return {
        "success": True,
        "kind": "charge",
        "image_url": image_url,
        "full_address": full_address or location_label,
        "location_label": location_label,
        "lat": lat,
        "lon": lon,
    }


async def _async_build_trip_record_map(hass: HomeAssistant, record: dict[str, Any]) -> dict[str, Any]:
    start_address = str(record.get("start_address") or record.get("origin") or record.get("from") or "").strip()
    end_address = str(record.get("end_address") or record.get("destination") or record.get("to") or "").strip()
    start_lat = _extract_coord_from_record(record, "start_latitude", "start_lat", "origin_latitude", "origin_lat")
    start_lon = _extract_coord_from_record(record, "start_longitude", "start_lon", "origin_longitude", "origin_lon")
    end_lat = _extract_coord_from_record(record, "end_latitude", "end_lat", "destination_latitude", "destination_lat")
    end_lon = _extract_coord_from_record(record, "end_longitude", "end_lon", "destination_longitude", "destination_lon")

    if (start_lat is None or start_lon is None) and start_address:
        geocoded = await _async_geocode_text(hass, start_address)
        if geocoded:
            start_lat = geocoded["lat"]
            start_lon = geocoded["lon"]
    if (end_lat is None or end_lon is None) and end_address:
        geocoded = await _async_geocode_text(hass, end_address)
        if geocoded:
            end_lat = geocoded["lat"]
            end_lon = geocoded["lon"]

    points: list[dict[str, Any]] = []
    map_type = "standard"
    for key in ("map_points", "points", "route_points", "trip_points"):
        points = _extract_route_points_with_metadata(record.get(key))
        if points:
            if any((p.get("speed") is not None or p.get("elevation") is not None) for p in points):
                map_type = "colored"
            break
    if not points:
        if start_lat is not None and start_lon is not None and end_lat is not None and end_lon is not None:
            points = [{"lat": start_lat, "lon": start_lon}, {"lat": end_lat, "lon": end_lon}]
        elif start_lat is not None and start_lon is not None:
            points = [{"lat": start_lat, "lon": start_lon}]
        elif end_lat is not None and end_lon is not None:
            points = [{"lat": end_lat, "lon": end_lon}]

    image_url = ""
    if points:
        output_dir = _record_maps_output_dir(hass)
        suffix = "colored" if map_type == "colored" else "standard"
        file_path = output_dir / f"trip_{_safe_record_map_token(record.get('id'))}_{suffix}.png"
        data = {
            "title": "Tesla AI - Sürüş Haritası",
            "trip_km": round(_to_float(record.get("trip_km"), 0.0), 2),
            "duration_text": str(record.get("duration_text") or "").strip(),
            "points": points,
        }
        await asyncio.to_thread(render_trip_map_png, data, str(file_path))
        image_url = _public_record_map_url(file_path)

    return {
        "success": True,
        "kind": "trip",
        "image_url": image_url,
        "start_address": start_address,
        "end_address": end_address,
        "point_count": len(points),
        "map_type": map_type,
    }


class PomTeslaChargeRecordsView(HomeAssistantView):
    """API endpoint for the POM Tesla charge record app panel."""

    url = API_CHARGE_RECORDS_URL
    name = f"api:{DOMAIN}:charge_records"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request) -> web.Response:
        ledger = await asyncio.to_thread(_load_charge_ledger, self.hass)
        records = [_visible_charge_record(item) for item in list(ledger.get("records") or [])]
        records.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
        return web.json_response(
            {
                "success": True,
                "language": _app_language(self.hass),
                "currency": _report_currency(self.hass),
                "records": records,
                "summary": _charge_summary(records),
                "last_monthly_report_key": str(ledger.get("last_monthly_report_key") or ""),
            }
        )

    async def post(self, request: web.Request) -> web.Response:
        try:
            body = await request.json()
        except Exception:
            body = {}
        if not isinstance(body, dict):
            body = {}

        action = str(body.get("action") or "").strip().lower()
        ledger = await asyncio.to_thread(_load_charge_ledger, self.hass)
        records = [item for item in list(ledger.get("records") or []) if isinstance(item, dict)]
        default_currency = _report_currency(self.hass)

        if action == "delete":
            record_id = str(body.get("id") or "").strip()
            if not record_id:
                return web.json_response({"success": False, "error": "missing_record_id"}, status=400)
            ledger["records"] = [item for item in records if str(item.get("id") or "") != record_id]
            await asyncio.to_thread(_save_charge_ledger, self.hass, ledger)
        elif action in {"add", "update"}:
            raw_record = dict(body.get("record") or {})
            if action == "update":
                record_id = str(body.get("id") or raw_record.get("id") or "").strip()
                if not record_id:
                    return web.json_response({"success": False, "error": "missing_record_id"}, status=400)
                existing = next((item for item in records if str(item.get("id") or "") == record_id), None)
                if not isinstance(existing, dict):
                    return web.json_response({"success": False, "error": "record_not_found"}, status=404)
                merged = {**existing, **raw_record, "id": record_id}
                normalized = _normalize_charge_record(merged, default_currency=default_currency)
                records = [normalized if str(item.get("id") or "") == record_id else item for item in records]
            else:
                raw_record.pop("id", None)
                normalized = _normalize_charge_record(raw_record, default_currency=default_currency)
                records.insert(0, normalized)
            ledger["records"] = records[:1000]
            await asyncio.to_thread(_save_charge_ledger, self.hass, ledger)
        else:
            return web.json_response({"success": False, "error": "unsupported_action"}, status=400)

        refreshed_ledger = await asyncio.to_thread(_load_charge_ledger, self.hass)
        refreshed = [_visible_charge_record(item) for item in list(refreshed_ledger.get("records") or [])]
        refreshed.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
        return web.json_response(
            {
                "success": True,
                "language": _app_language(self.hass),
                "currency": _report_currency(self.hass),
                "records": refreshed,
                "summary": _charge_summary(refreshed),
            }
        )


async def _async_generate_trip_record_ai_summary(hass: HomeAssistant, record: dict[str, Any]) -> str:
    """Generate an AI story for an existing Trip Records item and save it only to the ledger."""
    record_id = str(record.get("id") or "").strip()
    if not record_id:
        raise ValueError("missing_record_id")
    data = _entry_config(hass)
    if not _to_bool(data.get(CONF_AI_ENABLED), DEFAULT_AI_ENABLED):
        raise ValueError("ai_disabled")
    if not str(data.get(CONF_OPENAI_API_KEY) or "").strip():
        raise ValueError("openai_api_key_missing")

    # Lazily import from the integration core to avoid circular import during panel setup.
    from . import async_generate_and_send_post_trip_ai_story

    report_data = dict(record or {})
    report_data.setdefault("trip_km", _to_float(record.get("trip_km"), 0.0))
    report_data.setdefault("used_kwh", _to_float(record.get("used_kwh"), 0.0))
    report_data.setdefault("consumption_kwh_100km", _to_float(record.get("consumption_kwh_100km"), 0.0))
    report_data.setdefault("duration_minutes", _to_float(record.get("duration_minutes"), 0.0))
    report_data.setdefault("duration_text", str(record.get("duration_text") or "").strip())
    report_data.setdefault("source", str(record.get("source") or "trip_records_manual_regenerate").strip())

    story = await async_generate_and_send_post_trip_ai_story(
        hass,
        data,
        report_data,
        telegram_target="",
        source=str(record.get("source") or "trip_records_regenerate"),
        record_id=record_id,
    )
    if not story:
        raise ValueError("ai_story_empty")
    # Mark manual regeneration explicitly after the core helper saves the story.
    from . import async_update_trip_record_ai_summary
    await async_update_trip_record_ai_summary(
        hass,
        record_id,
        story,
        detail_level=str(data.get(CONF_AI_TRIP_STORY_DETAIL_LEVEL) or DEFAULT_AI_TRIP_STORY_DETAIL_LEVEL),
        telegram_status="regenerated_saved",
    )
    return str(story or "").strip()


class PomTeslaTripRecordsView(HomeAssistantView):
    """API endpoint for the POM Tesla trip record app panel."""

    url = API_TRIP_RECORDS_URL
    name = f"api:{DOMAIN}:trip_records"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request) -> web.Response:
        ledger = await asyncio.to_thread(_load_trip_ledger, self.hass)
        records = [_visible_trip_record(item) for item in list(ledger.get("records") or [])]
        records.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
        return web.json_response(
            {
                "success": True,
                "language": _app_language(self.hass),
                "currency": _report_currency(self.hass),
                "records": records,
                "summary": _trip_summary([item for item in records if not _is_manual_tracking_trip_record(item)]),
            }
        )

    async def post(self, request: web.Request) -> web.Response:
        try:
            body = await request.json()
        except Exception:
            body = {}
        if not isinstance(body, dict):
            body = {}

        action = str(body.get("action") or "").strip().lower()
        ledger = await asyncio.to_thread(_load_trip_ledger, self.hass)
        records = [item for item in list(ledger.get("records") or []) if isinstance(item, dict)]
        default_currency = _report_currency(self.hass)

        if action == "regenerate_ai_summary":
            record_id = str(body.get("id") or "").strip()
            if not record_id:
                return web.json_response({"success": False, "error": "missing_record_id"}, status=400)
            existing = next((item for item in records if str(item.get("id") or "") == record_id), None)
            if not isinstance(existing, dict):
                return web.json_response({"success": False, "error": "record_not_found"}, status=404)
            try:
                normalized_existing = _normalize_trip_record(existing, default_currency=default_currency)
                await _async_generate_trip_record_ai_summary(self.hass, normalized_existing)
            except Exception as err:
                _LOGGER.exception("POM Tesla Trip Records AI regeneration failed for %s", record_id)
                return web.json_response({"success": False, "error": "ai_regeneration_failed", "message": str(err)}, status=200)
            refreshed_ledger = await asyncio.to_thread(_load_trip_ledger, self.hass)
            refreshed = [_visible_trip_record(item) for item in list(refreshed_ledger.get("records") or [])]
            refreshed.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
            return web.json_response({
                "success": True,
                "language": _app_language(self.hass),
                "currency": _report_currency(self.hass),
                "records": refreshed,
                "summary": _trip_summary([item for item in refreshed if not _is_manual_tracking_trip_record(item)]),
            })

        if action == "delete":
            record_id = str(body.get("id") or "").strip()
            if not record_id:
                return web.json_response({"success": False, "error": "missing_record_id"}, status=400)
            ledger["records"] = [item for item in records if str(item.get("id") or "") != record_id]
            await asyncio.to_thread(_save_trip_ledger, self.hass, ledger)
        elif action in {"add", "update"}:
            raw_record = dict(body.get("record") or {})
            if action == "update":
                record_id = str(body.get("id") or raw_record.get("id") or "").strip()
                if not record_id:
                    return web.json_response({"success": False, "error": "missing_record_id"}, status=400)
                existing = next((item for item in records if str(item.get("id") or "") == record_id), None)
                if not isinstance(existing, dict):
                    return web.json_response({"success": False, "error": "record_not_found"}, status=404)
                merged = {**existing, **raw_record, "id": record_id}
                normalized = _normalize_trip_record(merged, default_currency=default_currency)
                records = [normalized if str(item.get("id") or "") == record_id else item for item in records]
            else:
                raw_record.pop("id", None)
                normalized = _normalize_trip_record(raw_record, default_currency=default_currency)
                records.insert(0, normalized)
            ledger["records"] = records[:1000]
            await asyncio.to_thread(_save_trip_ledger, self.hass, ledger)
        else:
            return web.json_response({"success": False, "error": "unsupported_action"}, status=400)

        refreshed_ledger = await asyncio.to_thread(_load_trip_ledger, self.hass)
        refreshed = [_visible_trip_record(item) for item in list(refreshed_ledger.get("records") or [])]
        refreshed.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
        return web.json_response(
            {
                "success": True,
                "language": _app_language(self.hass),
                "currency": _report_currency(self.hass),
                "records": refreshed,
                "summary": _trip_summary([item for item in refreshed if not _is_manual_tracking_trip_record(item)]),
            }
        )


class PomTeslaRecordMapView(HomeAssistantView):
    """API endpoint that returns preview map data for charge/trip records."""

    url = API_RECORD_MAP_URL
    name = f"api:{DOMAIN}:record_map"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request) -> web.Response:
        kind = str(request.query.get("kind") or "").strip().lower()
        record_id = str(request.query.get("id") or "").strip()
        if kind not in {"charge", "trip"}:
            return web.json_response({"success": False, "error": "invalid_kind"}, status=400)
        if not record_id:
            return web.json_response({"success": False, "error": "missing_record_id"}, status=400)

        try:
            default_currency = _record_map_entry_option(self.hass, CONF_REPORT_CURRENCY, DEFAULT_REPORT_CURRENCY)
            if kind == "charge":
                ledger = await asyncio.to_thread(_load_charge_ledger, self.hass)
                raw = next((item for item in list(ledger.get("records") or []) if str((item or {}).get("id") or "").strip() == record_id), None)
                if not isinstance(raw, dict):
                    return web.json_response({"success": False, "error": "record_not_found"}, status=404)
                record = _normalize_charge_record(raw, default_currency=default_currency)
                payload = await _async_build_charge_record_map(self.hass, record)
                return web.json_response(payload)

            ledger = await asyncio.to_thread(_load_trip_ledger, self.hass)
            raw = next((item for item in list(ledger.get("records") or []) if str((item or {}).get("id") or "").strip() == record_id), None)
            if not isinstance(raw, dict):
                return web.json_response({"success": False, "error": "record_not_found"}, status=404)
            record = _normalize_trip_record(raw, default_currency=default_currency)
            payload = await _async_build_trip_record_map(self.hass, record)
            return web.json_response(payload)
        except Exception as err:
            _LOGGER.exception("POM Tesla record map preview failed for kind=%s id=%s", kind, record_id)
            return web.json_response({"success": False, "error": "record_map_failed", "message": str(err)}, status=200)


def _dashboard_resources_status_payload(hass: HomeAssistant) -> dict[str, Any]:
    """Return cached dashboard resource status without blocking the event loop.

    The full Lovelace resource scan reads .storage/lovelace_resources. That is
    deliberately performed by _async_dashboard_resources_status_payload() using
    asyncio.to_thread(). Settings payloads use this cached/lightweight snapshot.
    """
    cache = hass.data.setdefault(DOMAIN, {}).get("dashboard_resources_status_cache")
    if isinstance(cache, dict):
        return cache
    desired_resources = _dashboard_panel_desired_resources()
    return {
        "resources": [
            {
                **desired,
                "base_url": _resource_base_url_panel(str(desired.get("url") or "")),
                "installed": None,
                "current_url": "",
                "status": "unknown",
            }
            for desired in desired_resources
        ],
        "missing_resources": [],
        "dependencies": [],
        "missing_dependencies": [],
        "summary": {
            "resources_total": len(desired_resources),
            "resources_missing": 0,
            "dependencies_total": 0,
            "dependencies_missing": 0,
            "ok": True,
            "status_deferred": True,
        },
        "storage_exists": None,
        "storage_error": "",
        "async_status": "deferred",
    }


async def _async_dashboard_resources_status_payload(hass: HomeAssistant) -> dict[str, Any]:
    """Build dashboard resource status off the event loop and cache it."""
    payload = await asyncio.to_thread(_dashboard_resources_status_payload_blocking, hass)
    hass.data.setdefault(DOMAIN, {})["dashboard_resources_status_cache"] = payload
    return payload


def _settings_save_response_payload(
    hass: HomeAssistant,
    merged_options: dict[str, Any],
    *,
    saved_sections: list[str] | None = None,
) -> dict[str, Any]:
    """Return a lightweight response after panel settings saves.

    The full _settings_payload() is intentionally expensive on large HA
    instances because it includes entity managers, dashboard resource audits,
    and system/debug summaries. Calling it after every save blocks the event
    loop long enough to make other HA tabs appear frozen. POST /settings now
    returns only the sections that were just saved; the frontend merges them
    into its already-loaded settings payload.
    """
    saved = [str(item) for item in (saved_sections or []) if item]
    payload: dict[str, Any] = {
        "success": True,
        "partial_update": True,
        "saved_sections": saved,
        "language": str(merged_options.get(CONF_APP_LANGUAGE) or DEFAULT_APP_LANGUAGE),
        "currency": _normalize_currency(
            merged_options.get(CONF_REPORT_CURRENCY, DEFAULT_REPORT_CURRENCY),
            default=DEFAULT_REPORT_CURRENCY,
        ),
        "reload_required": False,
    }

    if "general_settings" in saved:
        payload["general_settings"] = {
            "app_language": str(merged_options.get(CONF_APP_LANGUAGE) or DEFAULT_APP_LANGUAGE),
            "debug_enabled": _to_bool(merged_options.get("panel_debug_enabled"), False),
            "default_open_tab": str(merged_options.get("panel_default_open_tab") or "settings"),
            "system": {
                "integration_version": DASHBOARD_PANEL_VERSION,
                "has_config_entry": _first_config_entry(hass) is not None,
                "panel_js_file": PANEL_JS_FILE,
                "panel_js_url": f"/{DOMAIN}/{PANEL_JS_FILE}",
                "fast_save": True,
            },
        }

    if "charging" in saved:
        currency = _normalize_currency(merged_options.get(CONF_REPORT_CURRENCY, DEFAULT_REPORT_CURRENCY), default=DEFAULT_REPORT_CURRENCY)
        payload["charging"] = {
            "report_currency": currency,
            "charging_report_mode": str(merged_options.get(CONF_CHARGING_REPORT_MODE) or DEFAULT_CHARGING_REPORT_MODE),
            "supercharger_price": _to_float(merged_options.get(CONF_SUPERCHARGER_PRICE), DEFAULT_SUPERCHARGER_PRICE),
            "zes_price": _to_float(merged_options.get(CONF_ZES_PRICE), DEFAULT_ZES_PRICE),
            "astor_price": _to_float(merged_options.get(CONF_ASTOR_PRICE), DEFAULT_ASTOR_PRICE),
            "provider_presets": _normalize_provider_presets(
                merged_options.get(CONF_CHARGE_PROVIDER_PRESETS, []),
                default_currency=currency,
            ),
        }

    if "telegram" in saved:
        payload["telegram"] = {
            "builtin_telegram_enabled": _to_bool(merged_options.get(CONF_BUILTIN_TELEGRAM_ENABLED), DEFAULT_BUILTIN_TELEGRAM_ENABLED),
            "builtin_telegram_bot_token": str(merged_options.get(CONF_BUILTIN_TELEGRAM_BOT_TOKEN) or "").strip(),
            "builtin_telegram_poll_enabled": _to_bool(merged_options.get(CONF_BUILTIN_TELEGRAM_POLL_ENABLED), DEFAULT_BUILTIN_TELEGRAM_POLL_ENABLED),
            "builtin_telegram_poll_interval_seconds": _positive_int(
                merged_options.get(CONF_BUILTIN_TELEGRAM_POLL_INTERVAL_SECONDS),
                DEFAULT_BUILTIN_TELEGRAM_POLL_INTERVAL_SECONDS,
                minimum=1,
                maximum=3600,
            ),
            "replies_enabled": bool(str(merged_options.get(CONF_TELEGRAM_TARGET) or merged_options.get(CONF_AI_TELEGRAM_TARGET) or "").strip()),
            "telegram_group_id": str(
                merged_options.get(CONF_AI_TELEGRAM_LISTENER_CHAT_ID)
                or merged_options.get(CONF_AI_TELEGRAM_TARGET)
                or merged_options.get(CONF_TELEGRAM_TARGET)
                or ""
            ).strip(),
            "ai_group_listener_enabled": _to_bool(
                merged_options.get(CONF_AI_TELEGRAM_LISTENER_ENABLED),
                DEFAULT_AI_TELEGRAM_LISTENER_ENABLED,
            ),
            "report_commands": _telegram_report_commands_payload(merged_options),
        }

    if "trip_reports" in saved:
        payload["trip_reports"] = {
            "auto_trip_tracking": _to_bool(merged_options.get(CONF_AUTO_TRIP_TRACKING), DEFAULT_AUTO_TRIP_TRACKING),
            "auto_start_speed_threshold": round(_positive_float(merged_options.get(CONF_AUTO_START_SPEED_THRESHOLD), DEFAULT_AUTO_START_SPEED_THRESHOLD, minimum=0.0, maximum=250.0), 2),
            "live_trip_enabled": _to_bool(merged_options.get(CONF_LIVE_TRIP_ENABLED), DEFAULT_LIVE_TRIP_ENABLED),
            "live_trip_update_interval_seconds": _positive_int(merged_options.get(CONF_LIVE_TRIP_UPDATE_INTERVAL_SECONDS), DEFAULT_LIVE_TRIP_UPDATE_INTERVAL_SECONDS, minimum=1, maximum=300),
            "live_trip_traffic_speed_threshold": round(_positive_float(merged_options.get(CONF_LIVE_TRIP_TRAFFIC_SPEED_THRESHOLD), DEFAULT_LIVE_TRIP_TRAFFIC_SPEED_THRESHOLD, minimum=0.0, maximum=250.0), 2),
            "live_trip_finish_delay_seconds": _positive_int(merged_options.get(CONF_LIVE_TRIP_FINISH_DELAY_SECONDS), DEFAULT_LIVE_TRIP_FINISH_DELAY_SECONDS, minimum=1, maximum=3600),
            "live_trip_min_distance_km": round(_positive_float(merged_options.get(CONF_LIVE_TRIP_MIN_DISTANCE_KM), DEFAULT_LIVE_TRIP_MIN_DISTANCE_KM, minimum=0.0, maximum=10000.0), 3),
            "live_trip_ignore_short_maneuvers": _to_bool(merged_options.get(CONF_LIVE_TRIP_IGNORE_SHORT_MANEUVERS), DEFAULT_LIVE_TRIP_IGNORE_SHORT_MANEUVERS),
            "live_trip_candidate_min_distance_km": round(_positive_float(merged_options.get(CONF_LIVE_TRIP_CANDIDATE_MIN_DISTANCE_KM), DEFAULT_LIVE_TRIP_CANDIDATE_MIN_DISTANCE_KM, minimum=0.0, maximum=100.0), 3),
            "live_trip_candidate_min_duration_seconds": _positive_int(merged_options.get(CONF_LIVE_TRIP_CANDIDATE_MIN_DURATION_SECONDS), DEFAULT_LIVE_TRIP_CANDIDATE_MIN_DURATION_SECONDS, minimum=0, maximum=3600),
            "live_trip_ai_segment_distance_km": _live_trip_ai_segment_distance_for_panel(merged_options.get(CONF_LIVE_TRIP_AI_SEGMENT_DISTANCE_KM)),
            "live_trip_ai_segment_distance_options": list(LIVE_TRIP_AI_SEGMENT_DISTANCE_OPTIONS),
            "ai_trip_story_enabled": _to_bool(merged_options.get(CONF_AI_ALERT_POST_TRIP_SUMMARY_ENABLED), DEFAULT_AI_ALERT_POST_TRIP_SUMMARY_ENABLED),
            "ai_trip_story_detail_level": str(merged_options.get(CONF_AI_TRIP_STORY_DETAIL_LEVEL) or DEFAULT_AI_TRIP_STORY_DETAIL_LEVEL) if str(merged_options.get(CONF_AI_TRIP_STORY_DETAIL_LEVEL) or DEFAULT_AI_TRIP_STORY_DETAIL_LEVEL) in AI_TRIP_STORY_DETAIL_OPTIONS else DEFAULT_AI_TRIP_STORY_DETAIL_LEVEL,
            "ai_trip_story_delay_mode": "follow_live_trip_report_delay",
            "trip_map_enabled": _to_bool(merged_options.get(CONF_TRIP_MAP_ENABLED), DEFAULT_TRIP_MAP_ENABLED),
            "trip_map_tracker_entity": str(merged_options.get(CONF_TRIP_MAP_TRACKER_ENTITY) or DEFAULT_TRIP_MAP_TRACKER_ENTITY or "").strip(),
            "trip_map_sample_interval_seconds": _positive_int(merged_options.get(CONF_TRIP_MAP_SAMPLE_INTERVAL_SECONDS), DEFAULT_TRIP_MAP_SAMPLE_INTERVAL_SECONDS, minimum=1, maximum=300),
            "trip_map_min_movement_meters": round(_positive_float(merged_options.get(CONF_TRIP_MAP_MIN_MOVEMENT_METERS), DEFAULT_TRIP_MAP_MIN_MOVEMENT_METERS, minimum=0.0, maximum=10000.0), 2),
            "trip_map_send_separate_png": _to_bool(merged_options.get(CONF_TRIP_MAP_SEND_SEPARATE_PNG), DEFAULT_TRIP_MAP_SEND_SEPARATE_PNG),
            "show_distance": _to_bool(merged_options.get(CONF_SHOW_DISTANCE), DEFAULT_SHOW_DISTANCE),
            "show_duration": _to_bool(merged_options.get(CONF_SHOW_DURATION), DEFAULT_SHOW_DURATION),
            "show_traffic": _to_bool(merged_options.get(CONF_SHOW_TRAFFIC), DEFAULT_SHOW_TRAFFIC),
            "show_average_speed": _to_bool(merged_options.get(CONF_SHOW_AVERAGE_SPEED), DEFAULT_SHOW_AVERAGE_SPEED),
            "show_energy": _to_bool(merged_options.get(CONF_SHOW_ENERGY), DEFAULT_SHOW_ENERGY),
            "show_consumption": _to_bool(merged_options.get(CONF_SHOW_CONSUMPTION), DEFAULT_SHOW_CONSUMPTION),
            "show_battery": _to_bool(merged_options.get(CONF_SHOW_BATTERY), DEFAULT_SHOW_BATTERY),
            "show_cost": _to_bool(merged_options.get(CONF_SHOW_COST), DEFAULT_SHOW_COST),
            "show_climate": _to_bool(merged_options.get(CONF_SHOW_CLIMATE), DEFAULT_SHOW_CLIMATE),
            "show_elevation": _to_bool(merged_options.get(CONF_SHOW_ELEVATION), DEFAULT_SHOW_ELEVATION),
            "show_trip_map": _to_bool(merged_options.get(CONF_SHOW_TRIP_MAP), DEFAULT_SHOW_TRIP_MAP),
        }

    if "ai_settings" in saved:
        payload["ai_settings"] = _ai_settings_payload(merged_options)

    if "dashboard_settings" in saved:
        payload["dashboard_settings"] = _dashboard_settings_payload_fast(hass, merged_options)

    if "ai_entity_manager" in saved:
        payload["ai_entity_manager"] = _ai_entity_manager_payload_fast(hass, merged_options)
        payload["ai_entity_manager_saved"] = True
    if "report_entity_manager" in saved:
        payload["report_entity_manager"] = _report_entity_manager_payload_fast(hass, merged_options)
        payload["report_entity_manager_saved"] = True
    if "dashboard_entity_manager" in saved:
        payload["dashboard_entity_manager"] = _dashboard_entity_manager_payload_fast(hass, merged_options)
        payload["dashboard_entity_manager_saved"] = True

    return payload


def _dashboard_settings_payload_fast(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Return a lightweight but complete dashboard settings payload for save responses.

    This avoids expensive resource audits while still returning every dashboard
    setting section. Returning only fullscreen used to make Background/YouTube and
    Bottom Bar look blank immediately after save.
    """
    images: dict[str, str] = {}
    defaults: dict[str, str] = {}
    for slot, (option_key, default_url) in _dashboard_background_slot_map().items():
        images[slot] = str(data.get(option_key) or default_url).strip() or default_url
        defaults[slot] = default_url

    top_values: dict[str, str] = {}
    for key, default in DASHBOARD_TOP_SLOT_KEYS.items():
        allowed = DASHBOARD_CENTER_SLOT_TYPES if key == "top_center_slot" else DASHBOARD_TOP_SLOT_TYPES
        value = str(data.get(key) or default).strip()
        top_values[key] = value if value in allowed else default

    sidebar_values: dict[str, str] = {}
    for index, key in enumerate(DASHBOARD_SIDEBAR_SLOT_KEYS):
        default = DASHBOARD_SIDEBAR_DEFAULTS[index] if index < len(DASHBOARD_SIDEBAR_DEFAULTS) else "empty"
        value = str(data.get(key) or default).strip()
        sidebar_values[key] = value if value in DASHBOARD_SIDEBAR_ACTION_TYPES else default

    return {
        "resources_status": {
            "summary": {"ok": True, "status_deferred": True, "fast_save": True},
            "resources": [],
            "missing_resources": [],
            "dependencies": [],
            "missing_dependencies": [],
        },
        "images": images,
        "defaults": defaults,
        "allowed_extensions": ["png", "jpg", "jpeg", "webp", "gif"],
        "max_bytes": DASHBOARD_BACKGROUND_UPLOAD_MAX_BYTES,
        "youtube_driving_background": {
            "enabled": _to_bool(data.get("youtube_driving_bg_enabled"), False),
            "video": str(data.get("youtube_driving_bg_video") or "").strip(),
            "start_seconds": _positive_int(data.get("youtube_driving_bg_start_seconds"), 0, minimum=0, maximum=86400),
            "mute": _to_bool(data.get("youtube_driving_bg_mute"), True),
            "loop": _to_bool(data.get("youtube_driving_bg_loop"), True),
            "quality": str(data.get("youtube_driving_bg_quality") or "480").strip() if str(data.get("youtube_driving_bg_quality") or "480").strip() in ("360", "480", "720", "1080_lite", "1080", "1080_high") else "480",
        },
        "drive_dashboard": {
            "vehicle_image": str(data.get(DASHBOARD_DRIVE_VEHICLE_IMAGE_KEY) or "").strip(),
            "tire_pressure_image": str(data.get(DASHBOARD_DRIVE_TIRE_PRESSURE_IMAGE_KEY) or "").strip(),
        },
        "fullscreen": {key: _to_bool(data.get(key), default) for key, default in DASHBOARD_FULLSCREEN_KEYS.items()},
        "top_area": {
            "slots": top_values,
            "font_scales": {key: _bounded_float_panel(data.get(key), default) for key, default in DASHBOARD_TOP_FONT_SCALE_KEYS.items()},
            "font_scale_min": 0.7,
            "font_scale_max": 1.6,
            "font_scale_step": 0.05,
            "options": DASHBOARD_TOP_SLOT_TYPES,
            "options_list": [{"value": key, "label": label} for key, label in DASHBOARD_TOP_SLOT_TYPES.items()],
            "center_options": DASHBOARD_CENTER_SLOT_TYPES,
            "center_options_list": [{"value": key, "label": label} for key, label in DASHBOARD_CENTER_SLOT_TYPES.items()],
        },
        "sidebar": {
            "slots": sidebar_values,
            "options": DASHBOARD_SIDEBAR_ACTION_TYPES,
            "options_list": [{"value": key, "label": label} for key, label in DASHBOARD_SIDEBAR_ACTION_TYPES.items()],
        },
        "bottom_bar": {
            "location_display_mode": str(data.get("location_display_mode") or "auto_short"),
            "location_display_modes": DASHBOARD_LOCATION_DISPLAY_MODES,
            "location_display_modes_list": [{"value": key, "label": label} for key, label in DASHBOARD_LOCATION_DISPLAY_MODES.items()],
            "slots": {key: (str(data.get(key) or default).strip() if str(data.get(key) or default).strip() in DASHBOARD_BOTTOM_SLOT_TYPES else default) for key, default in DASHBOARD_BOTTOM_SLOT_KEYS.items()},
            "slot_options": DASHBOARD_BOTTOM_SLOT_TYPES,
            "slot_options_list": [{"value": key, "label": label} for key, label in DASHBOARD_BOTTOM_SLOT_TYPES.items()],
            "toggles": {key: _to_bool(data.get(key), default) for key, default in DASHBOARD_BOTTOM_TOGGLE_KEYS.items()},
        },
        "map": {
            **{key: _positive_int(data.get(key), default, minimum=0, maximum=24) for key, default in DASHBOARD_MAP_KEYS.items()},
            DASHBOARD_MAP_THEME_KEY: str(data.get(DASHBOARD_MAP_THEME_KEY) or DASHBOARD_MAP_THEME_DEFAULT).strip() if str(data.get(DASHBOARD_MAP_THEME_KEY) or DASHBOARD_MAP_THEME_DEFAULT).strip() in DASHBOARD_MAP_THEME_MODES else DASHBOARD_MAP_THEME_DEFAULT,
            "map_theme_modes": DASHBOARD_MAP_THEME_MODES,
            "map_theme_modes_list": [{"value": key, "label": label} for key, label in DASHBOARD_MAP_THEME_MODES.items()],
        },
        "person_track": {
            "person_track_enabled": _to_bool(data.get("person_track_enabled"), True),
            "person_track_show_button": _to_bool(data.get("person_track_show_button"), True),
            "person_track_hours_to_show": _positive_int(data.get("person_track_hours_to_show"), 15, minimum=0, maximum=24),
            "person_track_1_entity": str(data.get("person_track_1_entity") or "person.cavidan").strip(),
            "person_track_1_name": str(data.get("person_track_1_name") or "Cavidan").strip(),
            "person_track_1_enabled": _to_bool(data.get("person_track_1_enabled"), True),
            "person_track_2_entity": str(data.get("person_track_2_entity") or "person.ali").strip(),
            "person_track_2_name": str(data.get("person_track_2_name") or "Ali").strip(),
            "person_track_2_enabled": _to_bool(data.get("person_track_2_enabled"), True),
            "person_track_3_entity": str(data.get("person_track_3_entity") or "").strip(),
            "person_track_3_name": str(data.get("person_track_3_name") or "Person 3").strip(),
            "person_track_3_enabled": _to_bool(data.get("person_track_3_enabled"), False),
        },
    }


PANEL_AUTOFIND_JOB_STORE_KEY = "panel_autofind_jobs"


def _panel_autofind_jobs(hass: HomeAssistant) -> dict[str, dict[str, Any]]:
    """Return in-memory Auto Find job store."""
    return hass.data.setdefault(DOMAIN, {}).setdefault(PANEL_AUTOFIND_JOB_STORE_KEY, {})


def _panel_autofind_job_snapshot(job: dict[str, Any] | None) -> dict[str, Any]:
    """Return frontend-safe Auto Find job status."""
    if not isinstance(job, dict):
        return {
            "status": "idle",
            "kind": "",
            "job_id": "",
            "message": "",
            "found_count": 0,
            "candidate_count": 0,
            "role_count": 0,
            "started_at": "",
            "finished_at": "",
        }
    return {
        "status": str(job.get("status") or "idle"),
        "kind": str(job.get("kind") or ""),
        "job_id": str(job.get("job_id") or ""),
        "message": str(job.get("message") or ""),
        "found_count": int(_to_float(job.get("found_count"), 0.0)),
        "candidate_count": int(_to_float(job.get("candidate_count"), 0.0)),
        "role_count": int(_to_float(job.get("role_count"), 0.0)),
        "started_at": str(job.get("started_at") or ""),
        "finished_at": str(job.get("finished_at") or ""),
        "settings": job.get("settings") if isinstance(job.get("settings"), dict) else None,
        "error": str(job.get("error") or ""),
        "mode": str(job.get("mode") or ""),
    }


def _panel_autofind_now_text() -> str:
    return datetime.now().strftime("%d.%m.%Y %H:%M:%S")


def _start_panel_autofind_job(hass: HomeAssistant, kind: str) -> dict[str, Any]:
    """Create or replace the current background Auto Find job for kind."""
    jobs = _panel_autofind_jobs(hass)
    job_id = f"{kind}_{int(time.time() * 1000)}"
    job = {
        "status": "running",
        "kind": kind,
        "job_id": job_id,
        "message": "Auto Find arka planda başlatıldı.",
        "found_count": 0,
        "candidate_count": 0,
        "role_count": len(AI_ENTITY_MANAGER_ROLES) if kind == "ai" else (len(REPORT_ENTITY_MANAGER_ROLES) if kind == "report" else len(DASHBOARD_ENTITY_MANAGER_ROLES)),
        "started_at": _panel_autofind_now_text(),
        "finished_at": "",
        "settings": None,
        "error": "",
    }
    jobs[kind] = job
    return job


def _settings_payload_for_autofind_done(hass: HomeAssistant, merged_options: dict[str, Any], section: str) -> dict[str, Any]:
    """Return the same lightweight payload shape the panel expects after a save."""
    return _settings_save_response_payload(hass, merged_options, saved_sections=[section])


async def _run_ai_autofind_job_panel(
    hass: HomeAssistant,
    entry_id: str,
    job_id: str,
    request_payload: dict[str, Any],
) -> None:
    """Run AI Auto Find in the background without blocking the HA request."""
    jobs = _panel_autofind_jobs(hass)
    job = jobs.get("ai")
    if not isinstance(job, dict) or job.get("job_id") != job_id:
        return
    try:
        entry = _first_config_entry(hass)
        if entry is None:
            raise RuntimeError("config_entry_not_found")

        merged_options = dict(entry.options or {})
        fast_mode = _to_bool(request_payload.get("fast_mode"), False)
        job["mode"] = "fast" if fast_mode else "deep"
        main_entity = str(request_payload.get("main_entity") or merged_options.get(CONF_AI_MAIN_TESLA_ENTITY, DEFAULT_AI_MAIN_TESLA_ENTITY) or "").strip()
        data_for_find = {**dict(entry.data or {}), **merged_options}

        if not main_entity:
            job["message"] = "Ana Tesla entity aranıyor..."
            main_entity = await asyncio.to_thread(_auto_find_main_entity, hass, data_for_find)

        job["message"] = "Fast AI Auto Find çalışıyor..." if fast_mode else "AI entityleri arka planda aranıyor..."
        discovered = await asyncio.to_thread(_auto_discover_vehicle_entries_panel, hass, data_for_find, main_entity=main_entity, fast_mode=fast_mode)
        job["candidate_count"] = FAST_AUTOFIND_MAX_CANDIDATES_PANEL if fast_mode else int(_to_float(job.get("candidate_count"), 0))
        existing = _normalize_vehicle_entity_map_panel(merged_options.get(CONF_VEHICLE_ENTITY_MAP, DEFAULT_VEHICLE_ENTITY_MAP))
        existing_by_role = {item.get("role"): item for item in existing if item.get("role")}
        for item in discovered:
            if item.get("role"):
                existing_by_role[item["role"]] = item

        merged_entries = [existing_by_role[role] for role in AI_ENTITY_MANAGER_ROLES if role in existing_by_role]
        merged_entries.extend([item for item in existing if item.get("role") not in AI_ENTITY_MANAGER_ROLES])
        panel_ai_entries = _normalize_panel_ai_entity_map_panel(_prefer_fixed_role_entities_panel(merged_entries))

        merged_options[CONF_PANEL_AI_ENTITY_MAP] = panel_ai_entries
        merged_options[CONF_VEHICLE_ENTITY_MAP] = _normalize_vehicle_entity_map_panel(merged_entries)
        merged_options[CONF_AI_MAIN_TESLA_ENTITY] = main_entity
        merged_options[CONF_AI_AUTO_DISCOVER_DEVICE_ENTITIES] = True
        merged_options[CONF_AI_EXTRA_CONTEXT_ENTITIES] = [
            item["entity_id"] for item in panel_ai_entries if item.get("use_ai") and item.get("entity_id")
        ]
        merged_options[CONF_AI_EXCLUDED_CONTEXT_ENTITIES] = []

        hass.config_entries.async_update_entry(entry, options=merged_options)
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {**dict(entry.data or {}), **merged_options}

        job.update({
            "status": "done",
            "message": "AI Auto Find tamamlandı.",
            "found_count": len(panel_ai_entries),
            "candidate_count": len(discovered),
            "finished_at": _panel_autofind_now_text(),
            "settings": _settings_payload_for_autofind_done(hass, merged_options, "ai_entity_manager"),
            "error": "",
        })
        _LOGGER.info("POM AI Auto Find background job finished. found=%s", len(panel_ai_entries))
    except Exception as err:
        _LOGGER.exception("POM AI Auto Find background job failed")
        job.update({
            "status": "error",
            "message": "AI Auto Find hata verdi.",
            "finished_at": _panel_autofind_now_text(),
            "error": str(err),
        })



async def _run_report_autofind_job_panel(
    hass: HomeAssistant,
    entry_id: str,
    job_id: str,
    request_payload: dict[str, Any],
) -> None:
    """Run Reports Auto Find in the background without blocking HA."""
    jobs = _panel_autofind_jobs(hass)
    job = jobs.get("report")
    if not isinstance(job, dict) or job.get("job_id") != job_id:
        return
    try:
        entry = _first_config_entry(hass)
        if entry is None:
            raise RuntimeError("config_entry_not_found")

        merged_options = dict(entry.options or {})
        fast_mode = _to_bool(request_payload.get("fast_mode"), False)
        job["mode"] = "fast" if fast_mode else "deep"
        main_entity = str(request_payload.get("main_entity") or "").strip()
        combined_current = {**dict(entry.data or {}), **merged_options}

        report_entries: list[dict[str, Any]] = []
        by_role: dict[str, dict[str, Any]] = {}
        request_by_role: dict[str, dict[str, Any]] = {}
        raw_entries = request_payload.get("entries") if isinstance(request_payload.get("entries"), list) else []
        for item in raw_entries:
            if not isinstance(item, dict):
                continue
            entity_id = str(item.get("entity_id") or "").strip()
            role = str(item.get("role") or "").strip()
            if not entity_id or role not in REPORT_ENTITY_MANAGER_ROLES:
                continue
            report_entry = _report_entry_for_panel(hass, entity_id, role=role, source="panel_report_manual")
            if report_entry and role not in request_by_role:
                request_by_role[role] = report_entry

        if not main_entity:
            job["message"] = "Rapor ana Tesla entity aranıyor..."
            main_entity = await asyncio.to_thread(_auto_find_main_entity, hass, combined_current)

        job["message"] = "Fast Vehicle Master + Rapor entityleri aranıyor..." if fast_mode else "Vehicle Master + Rapor entityleri arka planda aranıyor..."
        discovered = await asyncio.to_thread(
            _auto_discover_vehicle_entries_panel,
            hass,
            combined_current,
            main_entity=main_entity,
            fast_mode=fast_mode,
        )
        job["candidate_count"] = len(discovered)

        master_entries = _merge_vehicle_master_entries_panel(
            merged_options.get(CONF_VEHICLE_ENTITY_MAP, DEFAULT_VEHICLE_ENTITY_MAP),
            discovered,
        )
        source_lock = _source_lock_from_entries_panel(hass, master_entries)
        # Preserve current selections only when they are on the same vehicle source.
        # This prevents old TeslaMate defaults from blocking Tessie/Fleet Auto Find.
        for role, report_entry in request_by_role.items():
            entity_id = str(report_entry.get("entity_id") or "").strip()
            if not source_lock or _entity_matches_source_lock_panel(hass, entity_id, source_lock):
                by_role[role] = report_entry

        # Same Auto Find structure as AI: first fill Reports from Vehicle Master,
        # then preserve source-compatible manual overrides from the current request.
        for item in _report_entries_from_vehicle_master_panel(hass, master_entries):
            role = str(item.get("role") or "").strip()
            if role and role not in by_role:
                by_role[role] = item

        for item in discovered:
            role = str(item.get("role") or "").strip()
            if role not in REPORT_ENTITY_MANAGER_ROLES or role in by_role:
                continue
            entity_id = str(item.get("entity_id") or "").strip()
            if not entity_id:
                continue
            report_entry = _report_entry_for_panel(hass, entity_id, role=role, source="panel_report_auto_find")
            report_entry = _entry_with_match_meta_panel(report_entry, item)
            if report_entry:
                by_role[role] = report_entry

        for role in REPORT_ENTITY_MANAGER_ROLES:
            if role in by_role:
                report_entries.append(by_role[role])

        panel_report_entries = _normalize_panel_report_entity_map_panel([
            {**item, "source": str(item.get("source") or "panel_report_manual")}
            for item in report_entries
        ])
        merged_options[CONF_PANEL_REPORT_ENTITY_MAP] = panel_report_entries
        merged_options[CONF_VEHICLE_ENTITY_MAP] = master_entries
        if main_entity:
            merged_options[CONF_AI_MAIN_TESLA_ENTITY] = main_entity
            merged_options[CONF_DASHBOARD_MAIN_ENTITY] = str(merged_options.get(CONF_DASHBOARD_MAIN_ENTITY) or main_entity).strip()

        # Keep legacy/effective runtime report keys in sync with the panel store.
        merged_options.update(_bind_report_options_from_vehicle_map_panel(merged_options))

        hass.config_entries.async_update_entry(entry, options=merged_options)
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {**dict(entry.data or {}), **merged_options}

        job.update({
            "status": "done",
            "message": "Rapor Auto Find tamamlandı.",
            "found_count": len(panel_report_entries),
            "candidate_count": len(discovered),
            "finished_at": _panel_autofind_now_text(),
            "settings": _settings_payload_for_autofind_done(hass, merged_options, "report_entity_manager"),
            "error": "",
        })
        _LOGGER.info("POM Report Auto Find background job finished. found=%s", len(panel_report_entries))
    except Exception as err:
        _LOGGER.exception("POM Report Auto Find background job failed")
        job.update({
            "status": "error",
            "message": "Rapor Auto Find hata verdi.",
            "finished_at": _panel_autofind_now_text(),
            "error": str(err),
        })



async def _run_dashboard_autofind_job_panel(
    hass: HomeAssistant,
    entry_id: str,
    job_id: str,
    request_payload: dict[str, Any],
) -> None:
    """Run Dashboard Auto Find in the background without blocking the HA request."""
    jobs = _panel_autofind_jobs(hass)
    job = jobs.get("dashboard")
    if not isinstance(job, dict) or job.get("job_id") != job_id:
        return
    try:
        entry = _first_config_entry(hass)
        if entry is None:
            raise RuntimeError("config_entry_not_found")

        merged_options = dict(entry.options or {})
        fast_mode = _to_bool(request_payload.get("fast_mode"), False)
        job["mode"] = "fast" if fast_mode else "deep"
        dashboard_main_entity = str(
            request_payload.get("main_entity")
            or merged_options.get(CONF_DASHBOARD_MAIN_ENTITY)
            or merged_options.get(CONF_AI_MAIN_TESLA_ENTITY)
            or DEFAULT_AI_MAIN_TESLA_ENTITY
            or ""
        ).strip()
        data_for_main_find = {**dict(entry.data or {}), **merged_options}
        if not dashboard_main_entity or not _entity_exists_for_panel(hass, dashboard_main_entity):
            job["message"] = "Dashboard ana Tesla entity aranıyor..."
            dashboard_main_entity = await asyncio.to_thread(_auto_find_main_entity, hass, data_for_main_find)
        if dashboard_main_entity:
            merged_options[CONF_DASHBOARD_MAIN_ENTITY] = dashboard_main_entity
            merged_options[CONF_AI_MAIN_TESLA_ENTITY] = str(merged_options.get(CONF_AI_MAIN_TESLA_ENTITY) or dashboard_main_entity).strip()

        by_role: dict[str, dict[str, Any]] = {}
        request_by_role: dict[str, dict[str, Any]] = {}
        raw_entries = request_payload.get("entries") if isinstance(request_payload.get("entries"), list) else []
        for item in raw_entries:
            if not isinstance(item, dict):
                continue
            entity_id = str(item.get("entity_id") or "").strip()
            role = str(item.get("role") or "").strip()
            if not entity_id or role not in DASHBOARD_ENTITY_MANAGER_ROLES or role in request_by_role:
                continue
            dash_entry = _dashboard_entry_for_panel(hass, entity_id, role=role, source="panel_dashboard_manual")
            if dash_entry:
                dash_entry["icon"] = str(item.get("icon") or "").strip()
                dash_entry["name"] = str(item.get("name") or "").strip()
                dash_entry.update(_match_meta_from_item(item))
                request_by_role[role] = dash_entry

        data_for_find = {**dict(entry.data or {}), **merged_options, CONF_DASHBOARD_MAIN_ENTITY: dashboard_main_entity}

        job["message"] = "Fast Vehicle Master entityleri aranıyor..." if fast_mode else "Vehicle Master entityleri arka planda aranıyor..."
        vehicle_discovered = await asyncio.to_thread(
            _auto_discover_vehicle_entries_panel,
            hass,
            data_for_find,
            main_entity=dashboard_main_entity,
            fast_mode=fast_mode,
        )
        master_entries = _merge_vehicle_master_entries_panel(
            merged_options.get(CONF_VEHICLE_ENTITY_MAP, DEFAULT_VEHICLE_ENTITY_MAP),
            vehicle_discovered,
        )
        source_lock = _source_lock_from_entries_panel(hass, master_entries)
        if source_lock:
            data_for_find["_vehicle_source_lock"] = source_lock
            job["source_label"] = source_lock.get("source_label") or source_lock.get("source_key") or source_lock.get("source_platform")

        # Preserve current selections only when they are not vehicle-source fields
        # or when they match the Vehicle Master source. This is the key fix that
        # stops old sensor.tesla_* Dashboard defaults from blocking Tessie/Fleet.
        for role, dash_entry in request_by_role.items():
            entity_id = str(dash_entry.get("entity_id") or "").strip()
            if role.startswith("dashboard_person") or role.startswith("dashboard_home") or entity_id.startswith("person."):
                by_role[role] = dash_entry
            elif not source_lock or _entity_matches_source_lock_panel(hass, entity_id, source_lock):
                by_role[role] = dash_entry

        # Same Auto Find structure as AI: use Vehicle Master as dashboard seed,
        # then let dashboard-specific roles fill the remaining UI/action slots.
        for item in _dashboard_entries_from_vehicle_master_panel(hass, master_entries):
            role = str(item.get("role") or "").strip()
            if role and role not in by_role:
                by_role[role] = item

        try:
            candidates = _dashboard_autofind_candidate_pool(hass, dashboard_main_entity, source_lock)
            job["candidate_count"] = len(candidates)
        except Exception:
            # Candidate count is diagnostic only.
            pass

        job["message"] = "Fast Dashboard entityleri aranıyor..." if fast_mode else "Dashboard entityleri arka planda aranıyor..."
        discovered = await asyncio.to_thread(_auto_discover_dashboard_entries_panel, hass, data_for_find, fast_mode=fast_mode)
        for item in discovered:
            role = str(item.get("role") or "").strip()
            if role and role not in by_role:
                by_role[role] = item

        dashboard_entries: list[dict[str, Any]] = []
        for role in DASHBOARD_ENTITY_MANAGER_ROLES:
            if role in by_role:
                dashboard_entries.append(by_role[role])

        panel_dashboard_entries = _normalize_panel_dashboard_entity_map_panel(dashboard_entries)
        merged_options[CONF_VEHICLE_ENTITY_MAP] = master_entries
        merged_options[CONF_PANEL_DASHBOARD_ENTITY_MAP] = panel_dashboard_entries
        merged_options[CONF_DASHBOARD_ENTITY_MAP] = panel_dashboard_entries
        _sync_dashboard_legacy_options(merged_options, panel_dashboard_entries)

        hass.config_entries.async_update_entry(entry, options=merged_options)
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {**dict(entry.data or {}), **merged_options}

        job.update({
            "status": "done",
            "message": "Dashboard Auto Find tamamlandı.",
            "found_count": len(panel_dashboard_entries),
            "candidate_count": int(_to_float(job.get("candidate_count"), len(discovered))) + len(vehicle_discovered),
            "finished_at": _panel_autofind_now_text(),
            "settings": _settings_payload_for_autofind_done(hass, merged_options, "dashboard_entity_manager"),
            "error": "",
        })
        _LOGGER.info(
            "POM Dashboard Auto Find background job finished. found=%s candidates=%s",
            len(panel_dashboard_entries),
            job.get("candidate_count"),
        )
    except Exception as err:
        _LOGGER.exception("POM Dashboard Auto Find background job failed")
        job.update({
            "status": "error",
            "message": "Dashboard Auto Find hata verdi.",
            "finished_at": _panel_autofind_now_text(),
            "error": str(err),
        })






def _write_drive_dashboard_from_panel_sync(path: Path, merged_options: dict[str, Any] | None = None) -> None:
    """Write the standalone Drive Dashboard YAML from panel context.

    alpha283 binds the standalone Drive Dashboard to Entities > Dashboard.
    """
    merged_options = dict(merged_options or {})
    template_path = Path(__file__).resolve().parent / "dashboard" / "drive_dashboard_template.yaml"
    yaml_text = template_path.read_text(encoding="utf-8")
    vehicle_image_url = str(merged_options.get(DASHBOARD_DRIVE_VEHICLE_IMAGE_KEY) or "").strip()
    tire_pressure_image_url = str(merged_options.get(DASHBOARD_DRIVE_TIRE_PRESSURE_IMAGE_KEY) or "").strip()
    app_language = str(merged_options.get(CONF_APP_LANGUAGE) or DEFAULT_APP_LANGUAGE).strip().lower()
    app_language = APP_LANGUAGE_EN if app_language.startswith("en") else APP_LANGUAGE_TR
    insert = f"            language: {_yaml_quote_panel(app_language)}\n"
    if vehicle_image_url:
        insert += f"            vehicle_image: {_yaml_quote_panel(vehicle_image_url)}\n"
    if tire_pressure_image_url:
        insert += f"            tire_pressure_image: {_yaml_quote_panel(tire_pressure_image_url)}\n"
    insert += _drive_dashboard_entities_yaml_panel(merged_options)
    if insert:
        yaml_text = yaml_text.replace(
            "            title: Drive Dashboard\n",
            "            title: Drive Dashboard\n" + insert,
            1,
        )
    dashboard_options = merged_dashboard_options_from_report_config(merged_options)
    yaml_text = apply_fullscreen_options_to_drive_dashboard(yaml_text, dashboard_options)
    path.write_text(yaml_text, encoding="utf-8")


async def _async_write_drive_dashboard_from_panel(hass: HomeAssistant, merged_options: dict[str, Any]) -> Path:
    path = Path(hass.config.path("pom_tesla_drive_dashboard.yaml"))
    await hass.async_add_executor_job(_write_drive_dashboard_from_panel_sync, path, dict(merged_options or {}))
    return path

async def _run_dashboard_rebuild_from_panel(
    hass: HomeAssistant,
    merged_options: dict[str, Any],
    *,
    reason: str = "panel_save",
) -> None:
    """Regenerate the Tesla dashboard YAML after panel dashboard saves.

    Dashboard settings such as bottom-bar visibility are static YAML changes.
    Saving the options alone is not enough; the dashboard file must be rebuilt.
    This runs as a background task so the settings POST returns immediately.
    """
    try:
        merged_options = _ensure_youtube_jsmpeg_token_secret_in_options(hass, dict(merged_options or {}))
        dashboard_options = merged_dashboard_options_from_report_config(dict(merged_options or {}))
        path = await async_write_tesla_dashboard(hass, dashboard_options)
        drive_path = await _async_write_drive_dashboard_from_panel(hass, merged_options)
        _LOGGER.info("POM Tesla dashboard YAML regenerated from panel. reason=%s path=%s", reason, path)
        _LOGGER.info("POM Tesla Drive dashboard YAML regenerated from panel. reason=%s path=%s", reason, drive_path)
    except Exception:
        _LOGGER.exception("POM Tesla dashboard rebuild from panel failed. reason=%s", reason)


def _should_rebuild_dashboard_after_panel_save(saved_sections: list[str], merged_options: dict[str, Any]) -> bool:
    """Return True when a panel save should regenerate the dashboard YAML."""
    if "dashboard_settings" not in saved_sections and "dashboard_entity_manager" not in saved_sections:
        return False
    return _to_bool(merged_options.get("rebuild_on_save"), True)




class PomTeslaSettingsView(HomeAssistantView):
    """API endpoint for app-panel managed POM Tesla settings."""

    url = API_SETTINGS_URL
    name = f"api:{DOMAIN}:settings"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request) -> web.Response:
        admin_response = _admin_required_response(request)
        if admin_response is not None:
            return admin_response
        mode = str(request.query.get("mode") or request.query.get("payload") or "fast").strip().lower()
        try:
            if mode in {"full", "heavy", "legacy"}:
                _ensure_panel_entity_store_migration(self.hass)
                payload = await asyncio.to_thread(_settings_payload, self.hass)
                payload["payload_mode"] = "full"
                payload["deferred_full"] = False
            else:
                payload = _settings_payload_fast(self.hass)
        except Exception as err:
            _LOGGER.exception("POM Tesla settings payload failed; returning minimal safe payload")
            payload = {
                "success": False,
                "safe_mode": True,
                "error": str(err),
                "language": APP_LANGUAGE_TR,
                "currency": DEFAULT_REPORT_CURRENCY,
                "currency_options": list(REPORT_CURRENCY_OPTIONS),
                "general_settings": {
                    "app_language": DEFAULT_APP_LANGUAGE,
                    "debug_enabled": True,
                    "default_open_tab": "settings",
                    "resource_summary": {},
                    "system": {
                        "integration_version": DASHBOARD_PANEL_VERSION,
                        "has_config_entry": _first_config_entry(self.hass) is not None,
                        "panel_js_file": PANEL_JS_FILE,
                        "panel_js_url": f"/{DOMAIN}/{PANEL_JS_FILE}",
                    },
                    "entity_store_audit": {},
                    "health": {
                        "status": "critical",
                        "severity": "critical",
                        "status_label": "Critical",
                        "red_alert": True,
                        "warning_alert": True,
                        "safe_mode_recommended": True,
                        "memory": {},
                        "counts": {},
                        "self_reference": {"issue_count": 0, "issues": []},
                        "autofind": {},
                        "warnings": ["Settings payload failed; panel is in safe diagnostics mode."],
                    },
                },
                "charging": {
                    "report_currency": DEFAULT_REPORT_CURRENCY,
                    "charging_report_mode": DEFAULT_CHARGING_REPORT_MODE,
                    "supercharger_price": DEFAULT_SUPERCHARGER_PRICE,
                    "zes_price": DEFAULT_ZES_PRICE,
                    "astor_price": DEFAULT_ASTOR_PRICE,
                    "provider_presets": [],
                },
                "ai_settings": {},
                "telegram": {},
                "trip_reports": {},
                "ai_entity_manager": {},
                "report_entity_manager": {},
                "dashboard_entity_manager": {},
                "dashboard_settings": {"resources_status": _dashboard_resources_status_payload(self.hass)},
            }
        return web.json_response(payload)

    async def post(self, request: web.Request) -> web.Response:
        admin_response = _admin_required_response(request)
        if admin_response is not None:
            return admin_response
        entry = _first_config_entry(self.hass)
        if entry is None:
            return web.json_response({"success": False, "error": "config_entry_not_found"}, status=404)
        try:
            body = await request.json()
        except Exception:
            body = {}
        if not isinstance(body, dict):
            body = {}

        general_settings = body.get("general_settings") if isinstance(body.get("general_settings"), dict) else None
        charging = body.get("charging") if isinstance(body.get("charging"), dict) else None
        trip_reports = body.get("trip_reports") if isinstance(body.get("trip_reports"), dict) else None
        ai_settings = body.get("ai_settings") if isinstance(body.get("ai_settings"), dict) else None
        telegram = body.get("telegram") if isinstance(body.get("telegram"), dict) else None
        ai_entity_manager = body.get("ai_entity_manager") if isinstance(body.get("ai_entity_manager"), dict) else None
        report_entity_manager = body.get("report_entity_manager") if isinstance(body.get("report_entity_manager"), dict) else None
        dashboard_entity_manager = body.get("dashboard_entity_manager") if isinstance(body.get("dashboard_entity_manager"), dict) else None
        dashboard_settings = body.get("dashboard_settings") if isinstance(body.get("dashboard_settings"), dict) else None
        action = str(body.get("action") or "").strip().lower()
        saved_sections: list[str] = []
        if action == "migrate_panel_entity_stores":
            result = _ensure_panel_entity_store_migration(self.hass)
            payload = _settings_payload(self.hass)
            payload["migration"] = result
            return web.json_response(payload)

        if action == "auto_find_status":
            kind = str(body.get("kind") or body.get("manager") or "").strip().lower()
            if kind not in {"ai", "report", "dashboard"}:
                return web.json_response({"success": False, "error": "invalid_auto_find_kind"}, status=400)
            job = _panel_autofind_jobs(self.hass).get(kind)
            return web.json_response({"success": True, "auto_find_job": _panel_autofind_job_snapshot(job)})

        if ai_entity_manager is not None:
            ai_action = str(ai_entity_manager.get("action") or "").strip().lower()
            if ai_action in {"auto_find_async", "start_auto_find", "fast_auto_find_async", "start_fast_auto_find", "fast_auto_find"}:
                payload = dict(ai_entity_manager)
                payload["fast_mode"] = ai_action in {"fast_auto_find_async", "start_fast_auto_find", "fast_auto_find"}
                job = _start_panel_autofind_job(self.hass, "ai")
                self.hass.async_create_task(
                    _run_ai_autofind_job_panel(self.hass, entry.entry_id, job["job_id"], payload)
                )
                return web.json_response({"success": True, "auto_find_job": _panel_autofind_job_snapshot(job)})

        if report_entity_manager is not None:
            report_action = str(report_entity_manager.get("action") or "").strip().lower()
            if report_action in {"auto_find_async", "start_auto_find", "fast_auto_find_async", "start_fast_auto_find", "fast_auto_find"}:
                payload = dict(report_entity_manager)
                payload["fast_mode"] = report_action in {"fast_auto_find_async", "start_fast_auto_find", "fast_auto_find"}
                job = _start_panel_autofind_job(self.hass, "report")
                self.hass.async_create_task(
                    _run_report_autofind_job_panel(self.hass, entry.entry_id, job["job_id"], payload)
                )
                return web.json_response({"success": True, "auto_find_job": _panel_autofind_job_snapshot(job)})

        if dashboard_entity_manager is not None:
            dash_action = str(dashboard_entity_manager.get("action") or "").strip().lower()
            if dash_action in {"auto_find_async", "start_auto_find", "fast_auto_find_async", "start_fast_auto_find", "fast_auto_find"}:
                payload = dict(dashboard_entity_manager)
                payload["fast_mode"] = dash_action in {"fast_auto_find_async", "start_fast_auto_find", "fast_auto_find"}
                job = _start_panel_autofind_job(self.hass, "dashboard")
                self.hass.async_create_task(
                    _run_dashboard_autofind_job_panel(self.hass, entry.entry_id, job["job_id"], payload)
                )
                return web.json_response({"success": True, "auto_find_job": _panel_autofind_job_snapshot(job)})

        merged_options = dict(entry.options or {})

        if general_settings is not None:
            saved_sections.append("general_settings")
            lang = str(general_settings.get("app_language") or DEFAULT_APP_LANGUAGE).strip().lower()
            if lang not in {APP_LANGUAGE_TR, APP_LANGUAGE_EN}:
                lang = DEFAULT_APP_LANGUAGE
            merged_options[CONF_APP_LANGUAGE] = lang
            merged_options["panel_debug_enabled"] = _to_bool(general_settings.get("debug_enabled"), False)
            default_tab = str(general_settings.get("default_open_tab") or "settings").strip()
            if default_tab not in {"settings", "charges", "trips"}:
                default_tab = "settings"
            merged_options["panel_default_open_tab"] = default_tab

        if charging is not None:
            saved_sections.append("charging")
            default_currency = _normalize_currency(
                charging.get("report_currency", merged_options.get(CONF_REPORT_CURRENCY, DEFAULT_REPORT_CURRENCY)),
                default=DEFAULT_REPORT_CURRENCY,
            )
            merged_options[CONF_REPORT_CURRENCY] = default_currency

            report_mode = str(charging.get("charging_report_mode") or merged_options.get(CONF_CHARGING_REPORT_MODE) or DEFAULT_CHARGING_REPORT_MODE).strip()
            if report_mode not in {"direct", "prompt"}:
                report_mode = DEFAULT_CHARGING_REPORT_MODE
            merged_options[CONF_CHARGING_REPORT_MODE] = report_mode

            def _positive_price(key: str, default_value: float) -> float:
                value = _to_float(charging.get(key, merged_options.get(key)), default_value)
                return round(value if value > 0 else default_value, 4)

            if CONF_SUPERCHARGER_PRICE in charging:
                merged_options[CONF_SUPERCHARGER_PRICE] = _positive_price(CONF_SUPERCHARGER_PRICE, DEFAULT_SUPERCHARGER_PRICE)
            if CONF_ZES_PRICE in charging:
                merged_options[CONF_ZES_PRICE] = _positive_price(CONF_ZES_PRICE, DEFAULT_ZES_PRICE)
            if CONF_ASTOR_PRICE in charging:
                merged_options[CONF_ASTOR_PRICE] = _positive_price(CONF_ASTOR_PRICE, DEFAULT_ASTOR_PRICE)
            merged_options[CONF_CHARGE_PROVIDER_PRESETS] = [
                {"name": item["name"], "unit_price": item["unit_price"], "currency": item["currency"]}
                for item in _normalize_provider_presets(
                    charging.get(CONF_CHARGE_PROVIDER_PRESETS, charging.get("provider_presets", [])),
                    default_currency=default_currency,
                )
            ]


        if ai_settings is not None:
            saved_sections.append("ai_settings")
            merged_options[CONF_AI_ENABLED] = _to_bool(ai_settings.get("ai_enabled"), DEFAULT_AI_ENABLED)
            merged_options[CONF_AI_PERSONALITY] = _supported_ai_personality_panel(ai_settings.get("ai_personality"))
            merged_options[CONF_AI_ANSWER_LENGTH] = str(ai_settings.get("ai_answer_length") or DEFAULT_AI_ANSWER_LENGTH)
            merged_options[CONF_AI_CONTEXT_MODE] = str(ai_settings.get("ai_context_mode") or DEFAULT_AI_CONTEXT_MODE)
            merged_options[CONF_AI_NAME] = str(ai_settings.get("ai_name") or DEFAULT_AI_NAME or "").strip() or DEFAULT_AI_NAME
            merged_options[CONF_AI_USER_ADDRESS] = str(ai_settings.get("ai_user_address") or "").strip()[:80]
            if "openai_api_key" in ai_settings:
                raw_openai_key = str(ai_settings.get("openai_api_key") or "").strip()
                if raw_openai_key and not _is_masked_secret_from_panel(raw_openai_key):
                    merged_options[CONF_OPENAI_API_KEY] = raw_openai_key
            merged_options[CONF_OPENAI_MODEL] = str(ai_settings.get("openai_model") or DEFAULT_OPENAI_MODEL or "").strip() or DEFAULT_OPENAI_MODEL
            merged_options[CONF_REVERSE_GEOCODING_ENABLED] = _to_bool(ai_settings.get("reverse_geocoding_enabled"), DEFAULT_REVERSE_GEOCODING_ENABLED)
            merged_options[CONF_REVERSE_GEOCODING_CACHE_MINUTES] = max(5, _positive_int(ai_settings.get("reverse_geocoding_cache_minutes"), DEFAULT_REVERSE_GEOCODING_CACHE_MINUTES, minimum=5, maximum=1440))
            merged_options[CONF_REVERSE_GEOCODING_USE_IN_AI] = _to_bool(ai_settings.get("reverse_geocoding_use_in_ai"), DEFAULT_REVERSE_GEOCODING_USE_IN_AI)
            merged_options[CONF_AI_MAX_OUTPUT_TOKENS] = _positive_int(ai_settings.get("ai_max_output_tokens"), DEFAULT_AI_MAX_OUTPUT_TOKENS, minimum=128, maximum=4096)
            merged_options[CONF_AI_TELEGRAM_INCLUDE_CONTEXT] = _to_bool(ai_settings.get("ai_telegram_include_context"), DEFAULT_AI_TELEGRAM_INCLUDE_CONTEXT)
            merged_options[CONF_AI_CONFIRM_OPTIONAL_CONTROLS] = True
            merged_options[CONF_AI_ALERTS_ENABLED] = _to_bool(ai_settings.get("ai_alerts_enabled"), DEFAULT_AI_ALERTS_ENABLED)
            merged_options[CONF_AI_ALERT_STYLE] = str(ai_settings.get("ai_alert_style") or DEFAULT_AI_ALERT_STYLE)
            merged_options[CONF_AI_ALERT_COOLDOWN_MINUTES] = _positive_int(ai_settings.get("ai_alert_cooldown_minutes"), DEFAULT_AI_ALERT_COOLDOWN_MINUTES, minimum=1, maximum=240)
            merged_options[CONF_AI_ALERT_LOW_BATTERY_ENABLED] = _to_bool(ai_settings.get("ai_alert_low_battery_enabled"), DEFAULT_AI_ALERT_LOW_BATTERY_ENABLED)
            merged_options[CONF_AI_ALERT_LOW_BATTERY_THRESHOLD] = round(_positive_float(ai_settings.get("ai_alert_low_battery_threshold"), DEFAULT_AI_ALERT_LOW_BATTERY_THRESHOLD, minimum=1, maximum=100), 2)
            merged_options[CONF_AI_ALERT_POST_TRIP_SUMMARY_ENABLED] = _to_bool(ai_settings.get("ai_alert_post_trip_summary_enabled"), DEFAULT_AI_ALERT_POST_TRIP_SUMMARY_ENABLED)
            merged_options[CONF_AI_ALERT_CHARGE_FINISHED_ENABLED] = _to_bool(ai_settings.get("ai_alert_charge_finished_enabled"), DEFAULT_AI_ALERT_CHARGE_FINISHED_ENABLED)
            merged_options[CONF_AI_ALERT_CHARGING_STOPPED_ENABLED] = _to_bool(ai_settings.get("ai_alert_charging_stopped_enabled"), DEFAULT_AI_ALERT_CHARGING_STOPPED_ENABLED)
            merged_options[CONF_AI_ALERT_TIRE_PRESSURE_ENABLED] = _to_bool(ai_settings.get("ai_alert_tire_pressure_enabled"), DEFAULT_AI_ALERT_TIRE_PRESSURE_ENABLED)
            merged_options[CONF_AI_ALERT_TIRE_PRESSURE_THRESHOLD_BAR] = round(_positive_float(ai_settings.get("ai_alert_tire_pressure_threshold_bar"), DEFAULT_AI_ALERT_TIRE_PRESSURE_THRESHOLD_BAR, minimum=0.1, maximum=80.0), 2)
            merged_options[CONF_AI_ALERT_HIGH_BATTERY_TEMP_ENABLED] = _to_bool(ai_settings.get("ai_alert_high_battery_temp_enabled"), DEFAULT_AI_ALERT_HIGH_BATTERY_TEMP_ENABLED)
            merged_options[CONF_AI_ALERT_HIGH_BATTERY_TEMP_THRESHOLD_C] = round(_positive_float(ai_settings.get("ai_alert_high_battery_temp_threshold_c"), DEFAULT_AI_ALERT_HIGH_BATTERY_TEMP_THRESHOLD_C, minimum=1, maximum=120), 2)
            merged_options[CONF_AI_ALERT_CLIMATE_LEFT_ON_ENABLED] = _to_bool(ai_settings.get("ai_alert_climate_left_on_enabled"), DEFAULT_AI_ALERT_CLIMATE_LEFT_ON_ENABLED)
            merged_options[CONF_AI_ALERT_CLIMATE_LEFT_ON_DELAY_MINUTES] = _positive_int(ai_settings.get("ai_alert_climate_left_on_delay_minutes"), DEFAULT_AI_ALERT_CLIMATE_LEFT_ON_DELAY_MINUTES, minimum=1, maximum=240)
            merged_options[CONF_AI_ALERT_UNLOCKED_ENABLED] = _to_bool(ai_settings.get("ai_alert_unlocked_enabled"), DEFAULT_AI_ALERT_UNLOCKED_ENABLED)
            merged_options[CONF_AI_ALERT_UNLOCKED_DELAY_MINUTES] = _positive_int(ai_settings.get("ai_alert_unlocked_delay_minutes"), DEFAULT_AI_ALERT_UNLOCKED_DELAY_MINUTES, minimum=1, maximum=120)
            merged_options[CONF_AI_ALERT_DOOR_WINDOW_OPEN_ENABLED] = _to_bool(ai_settings.get("ai_alert_door_window_open_enabled"), DEFAULT_AI_ALERT_DOOR_WINDOW_OPEN_ENABLED)
            merged_options[CONF_AI_ALERT_DOOR_WINDOW_OPEN_DELAY_MINUTES] = _positive_int(ai_settings.get("ai_alert_door_window_open_delay_minutes"), DEFAULT_AI_ALERT_DOOR_WINDOW_OPEN_DELAY_MINUTES, minimum=1, maximum=120)
            merged_options[CONF_AI_ALERT_WINDOW_OPEN_INSTANT_ENABLED] = _to_bool(ai_settings.get("ai_alert_window_open_instant_enabled"), DEFAULT_AI_ALERT_WINDOW_OPEN_INSTANT_ENABLED)


        if telegram is not None:
            saved_sections.append("telegram")
            poll_interval = _positive_int(
                telegram.get("builtin_telegram_poll_interval_seconds", merged_options.get(CONF_BUILTIN_TELEGRAM_POLL_INTERVAL_SECONDS)),
                DEFAULT_BUILTIN_TELEGRAM_POLL_INTERVAL_SECONDS,
                minimum=1,
                maximum=3600,
            )
            existing_group_id = _normalize_telegram_id_panel(
                merged_options.get(CONF_AI_TELEGRAM_LISTENER_CHAT_ID)
                or merged_options.get(CONF_AI_TELEGRAM_TARGET)
                or merged_options.get(CONF_TELEGRAM_TARGET)
            )
            raw_group_value = (
                telegram.get("telegram_group_id")
                if "telegram_group_id" in telegram
                else telegram.get("group_id", existing_group_id)
            )
            group_id = _normalize_telegram_id_panel(raw_group_value)
            replies_enabled = _to_bool(
                telegram.get("replies_enabled", bool(group_id or existing_group_id)),
                bool(group_id or existing_group_id),
            )
            merged_options[CONF_BUILTIN_TELEGRAM_ENABLED] = _to_bool(
                telegram.get("builtin_telegram_enabled", merged_options.get(CONF_BUILTIN_TELEGRAM_ENABLED)),
                DEFAULT_BUILTIN_TELEGRAM_ENABLED,
            )
            raw_bot_token = str(telegram.get("builtin_telegram_bot_token", "") or "").strip()
            if raw_bot_token and not _is_masked_secret_from_panel(raw_bot_token):
                merged_options[CONF_BUILTIN_TELEGRAM_BOT_TOKEN] = raw_bot_token
            merged_options[CONF_BUILTIN_TELEGRAM_POLL_ENABLED] = _to_bool(
                telegram.get("builtin_telegram_poll_enabled", merged_options.get(CONF_BUILTIN_TELEGRAM_POLL_ENABLED)),
                DEFAULT_BUILTIN_TELEGRAM_POLL_ENABLED,
            )
            merged_options[CONF_BUILTIN_TELEGRAM_POLL_INTERVAL_SECONDS] = poll_interval
            merged_options[CONF_TELEGRAM_TARGET] = group_id if replies_enabled else ""
            merged_options[CONF_AI_TELEGRAM_TARGET] = group_id if replies_enabled else ""
            merged_options[CONF_AI_TELEGRAM_LISTENER_CHAT_ID] = group_id
            merged_options[CONF_AI_TELEGRAM_LISTENER_ENABLED] = _to_bool(
                telegram.get("ai_group_listener_enabled", merged_options.get(CONF_AI_TELEGRAM_LISTENER_ENABLED)),
                DEFAULT_AI_TELEGRAM_LISTENER_ENABLED,
            )
            raw_commands = telegram.get("report_commands")
            if isinstance(raw_commands, dict):
                merged_options[TELEGRAM_REPORT_COMMANDS_OPTION_KEY] = {
                    key: _normalize_telegram_report_command_panel(raw_commands.get(key), default)
                    for key, default in DEFAULT_TELEGRAM_REPORT_COMMANDS.items()
                }

        if ai_entity_manager is not None:
            saved_sections.append("ai_entity_manager")
            action = str(ai_entity_manager.get("action") or "save").strip().lower()
            main_entity = str(ai_entity_manager.get("main_entity") or merged_options.get(CONF_AI_MAIN_TESLA_ENTITY, DEFAULT_AI_MAIN_TESLA_ENTITY) or "").strip()
            if action == "auto_find":
                if not main_entity:
                    main_entity = _auto_find_main_entity(self.hass, {**dict(entry.data or {}), **merged_options})
                discovered = _auto_discover_vehicle_entries_panel(self.hass, {**dict(entry.data or {}), **merged_options}, main_entity=main_entity)
                existing = _normalize_vehicle_entity_map_panel(merged_options.get(CONF_VEHICLE_ENTITY_MAP, DEFAULT_VEHICLE_ENTITY_MAP))
                existing_by_role = {item.get("role"): item for item in existing if item.get("role")}
                for item in discovered:
                    if item.get("role"):
                        existing_by_role[item["role"]] = item
                merged_entries = [existing_by_role[role] for role in AI_ENTITY_MANAGER_ROLES if role in existing_by_role]
                # Preserve custom/other entries not represented by a fixed role.
                merged_entries.extend([item for item in existing if item.get("role") not in AI_ENTITY_MANAGER_ROLES])
                panel_ai_entries = _normalize_panel_ai_entity_map_panel(_prefer_fixed_role_entities_panel(merged_entries))
                merged_options[CONF_PANEL_AI_ENTITY_MAP] = panel_ai_entries
                merged_options[CONF_AI_MAIN_TESLA_ENTITY] = main_entity
                merged_options[CONF_AI_AUTO_DISCOVER_DEVICE_ENTITIES] = True
                merged_options[CONF_AI_EXTRA_CONTEXT_ENTITIES] = [item["entity_id"] for item in panel_ai_entries if item.get("use_ai") and item.get("entity_id")]
                merged_options[CONF_AI_EXCLUDED_CONTEXT_ENTITIES] = []
            else:
                raw_entries = ai_entity_manager.get("entries") if isinstance(ai_entity_manager.get("entries"), list) else []
                entries: list[dict[str, Any]] = []
                for item in raw_entries:
                    if not isinstance(item, dict):
                        continue
                    entity_id = str(item.get("entity_id") or "").strip()
                    role = str(item.get("role") or VEHICLE_ROLE_OTHER).strip()
                    if not entity_id or role not in PANEL_ACCEPTED_ENTITY_ROLES:
                        continue
                    entry_item = _vehicle_entry_for_panel(self.hass, entity_id, role=role, source="panel_manual")
                    if entry_item:
                        entry_item["use_ai"] = _to_bool(item.get("use_ai"), True)
                        entry_item["use_report"] = _to_bool(item.get("use_report"), entry_item.get("use_report", False))
                        entry_item["use_alerts"] = _to_bool(item.get("use_alerts"), entry_item.get("use_alerts", False))
                        entry_item["use_map"] = _to_bool(item.get("use_map"), entry_item.get("use_map", False))
                        entries.append(entry_item)
                # The panel can explicitly replace all AI entries so removed custom rows are really removed.
                if not _to_bool(ai_entity_manager.get("replace_all"), False):
                    existing = _normalize_vehicle_entity_map_panel(merged_options.get(CONF_VEHICLE_ENTITY_MAP, DEFAULT_VEHICLE_ENTITY_MAP))
                    entries.extend([item for item in existing if item.get("role") not in AI_ENTITY_MANAGER_ROLES])
                panel_ai_entries = _normalize_panel_ai_entity_map_panel(_prefer_fixed_role_entities_panel(entries))
                merged_options[CONF_PANEL_AI_ENTITY_MAP] = panel_ai_entries
                merged_options[CONF_AI_MAIN_TESLA_ENTITY] = main_entity
                merged_options[CONF_AI_AUTO_DISCOVER_DEVICE_ENTITIES] = _to_bool(
                    ai_entity_manager.get("auto_discover_device_entities", merged_options.get(CONF_AI_AUTO_DISCOVER_DEVICE_ENTITIES)),
                    DEFAULT_AI_AUTO_DISCOVER_DEVICE_ENTITIES,
                )
                merged_options[CONF_AI_EXTRA_CONTEXT_ENTITIES] = [item["entity_id"] for item in panel_ai_entries if item.get("use_ai") and item.get("entity_id")]
                merged_options[CONF_AI_EXCLUDED_CONTEXT_ENTITIES] = []

        if report_entity_manager is not None:
            saved_sections.append("report_entity_manager")
            action = str(report_entity_manager.get("action") or "save").strip().lower()
            main_entity = str(report_entity_manager.get("main_entity") or "").strip()
            combined_current = {**dict(entry.data or {}), **merged_options}
            if action == "auto_find":
                # Match Options Flow behavior: keep any user-filled report fields
                # and only use Auto Find to fill missing report slots.
                report_entries = []
                by_role: dict[str, dict[str, Any]] = {}
                raw_entries = report_entity_manager.get("entries") if isinstance(report_entity_manager.get("entries"), list) else []
                for item in raw_entries:
                    if not isinstance(item, dict):
                        continue
                    entity_id = str(item.get("entity_id") or "").strip()
                    role = str(item.get("role") or "").strip()
                    if not entity_id or role not in REPORT_ENTITY_MANAGER_ROLES:
                        continue
                    report_entry = _report_entry_for_panel(self.hass, entity_id, role=role, source="panel_report_manual")
                    if report_entry and role not in by_role:
                        by_role[role] = report_entry
                if not main_entity:
                    main_entity = _auto_find_main_entity(self.hass, combined_current)
                discovered = _auto_discover_vehicle_entries_panel(self.hass, combined_current, main_entity=main_entity)
                for item in discovered:
                    role = str(item.get("role") or "").strip()
                    if role not in REPORT_ENTITY_MANAGER_ROLES or role in by_role:
                        continue
                    entity_id = str(item.get("entity_id") or "").strip()
                    if not entity_id:
                        continue
                    report_entry = _report_entry_for_panel(self.hass, entity_id, role=role, source="panel_report_auto_find")
                    if report_entry:
                        by_role[role] = report_entry
                for role in REPORT_ENTITY_MANAGER_ROLES:
                    if role in by_role:
                        report_entries.append(by_role[role])
            else:
                raw_entries = report_entity_manager.get("entries") if isinstance(report_entity_manager.get("entries"), list) else []
                report_entries = []
                seen_roles: set[str] = set()
                for item in raw_entries:
                    if not isinstance(item, dict):
                        continue
                    entity_id = str(item.get("entity_id") or "").strip()
                    role = str(item.get("role") or "").strip()
                    if not entity_id or role not in REPORT_ENTITY_MANAGER_ROLES or role in seen_roles:
                        continue
                    report_entry = _report_entry_for_panel(self.hass, entity_id, role=role, source="panel_report_manual")
                    if report_entry:
                        report_entries.append(report_entry)
                        seen_roles.add(role)

            panel_report_entries = _normalize_panel_report_entity_map_panel([
                {**item, "source": str(item.get("source") or "panel_report_manual")} for item in report_entries
            ])
            merged_options[CONF_PANEL_REPORT_ENTITY_MAP] = panel_report_entries
            if main_entity:
                merged_options[CONF_AI_MAIN_TESLA_ENTITY] = main_entity
            # The panel store is now authoritative. Keep effective runtime legacy
            # values in the response/runtime overlay, but do not let future
            # Options Flow edits overwrite panel_report_entity_map.
            merged_options.update(_bind_report_options_from_vehicle_map_panel(merged_options))


        if dashboard_settings is not None:
            saved_sections.append("dashboard_settings")
            fullscreen = dashboard_settings.get("fullscreen") if isinstance(dashboard_settings.get("fullscreen"), dict) else {}
            for key, default in DASHBOARD_FULLSCREEN_KEYS.items():
                if key in fullscreen:
                    merged_options[key] = _to_bool(fullscreen.get(key), default)

            youtube_bg = dashboard_settings.get("youtube_driving_background") if isinstance(dashboard_settings.get("youtube_driving_background"), dict) else {}
            if youtube_bg:
                merged_options["youtube_driving_bg_enabled"] = _to_bool(youtube_bg.get("enabled"), False)
                merged_options["youtube_driving_bg_video"] = str(youtube_bg.get("video") or "").strip()
                merged_options["youtube_driving_bg_start_seconds"] = _positive_int(youtube_bg.get("start_seconds"), 0, minimum=0, maximum=86400)
                merged_options["youtube_driving_bg_mute"] = _to_bool(youtube_bg.get("mute"), True)
                merged_options["youtube_driving_bg_loop"] = _to_bool(youtube_bg.get("loop"), True)
                merged_options["youtube_driving_bg_quality"] = str(youtube_bg.get("quality") or "480").strip() if str(youtube_bg.get("quality") or "480").strip() in ("360", "480", "720", "1080_lite", "1080", "1080_high") else "480"

            drive_dashboard = dashboard_settings.get("drive_dashboard") if isinstance(dashboard_settings.get("drive_dashboard"), dict) else {}
            if "vehicle_image" in drive_dashboard:
                merged_options[DASHBOARD_DRIVE_VEHICLE_IMAGE_KEY] = str(drive_dashboard.get("vehicle_image") or "").strip()
            if "tire_pressure_image" in drive_dashboard:
                merged_options[DASHBOARD_DRIVE_TIRE_PRESSURE_IMAGE_KEY] = str(drive_dashboard.get("tire_pressure_image") or "").strip()

            top_area = dashboard_settings.get("top_area") if isinstance(dashboard_settings.get("top_area"), dict) else {}
            top_slots = top_area.get("slots") if isinstance(top_area.get("slots"), dict) else {}
            for key, default in DASHBOARD_TOP_SLOT_KEYS.items():
                allowed = DASHBOARD_CENTER_SLOT_TYPES if key == "top_center_slot" else DASHBOARD_TOP_SLOT_TYPES
                value = str(top_slots.get(key) or merged_options.get(key) or default).strip()
                merged_options[key] = value if value in allowed else default
            top_font_scales = top_area.get("font_scales") if isinstance(top_area.get("font_scales"), dict) else {}
            for key, default in DASHBOARD_TOP_FONT_SCALE_KEYS.items():
                merged_options[key] = _bounded_float_panel(top_font_scales.get(key, merged_options.get(key, default)), default)

            sidebar = dashboard_settings.get("sidebar") if isinstance(dashboard_settings.get("sidebar"), dict) else {}
            sidebar_slots = sidebar.get("slots") if isinstance(sidebar.get("slots"), dict) else {}
            for index, key in enumerate(DASHBOARD_SIDEBAR_SLOT_KEYS):
                default = DASHBOARD_SIDEBAR_DEFAULTS[index] if index < len(DASHBOARD_SIDEBAR_DEFAULTS) else "empty"
                value = str(sidebar_slots.get(key) or merged_options.get(key) or default).strip()
                merged_options[key] = value if value in DASHBOARD_SIDEBAR_ACTION_TYPES else default

            bottom = dashboard_settings.get("bottom_bar") if isinstance(dashboard_settings.get("bottom_bar"), dict) else {}
            location_mode = str(bottom.get("location_display_mode") or merged_options.get("location_display_mode") or "auto_short").strip()
            merged_options["location_display_mode"] = location_mode if location_mode in DASHBOARD_LOCATION_DISPLAY_MODES else "auto_short"
            bottom_slots = bottom.get("slots") if isinstance(bottom.get("slots"), dict) else {}
            for key, default in DASHBOARD_BOTTOM_SLOT_KEYS.items():
                value = str(bottom_slots.get(key) or merged_options.get(key) or default).strip()
                merged_options[key] = value if value in DASHBOARD_BOTTOM_SLOT_TYPES else default
            bottom_toggles = bottom.get("toggles") if isinstance(bottom.get("toggles"), dict) else {}
            for key, default in DASHBOARD_BOTTOM_TOGGLE_KEYS.items():
                if key in bottom_toggles:
                    merged_options[key] = _to_bool(bottom_toggles.get(key), default)

            map_settings = dashboard_settings.get("map") if isinstance(dashboard_settings.get("map"), dict) else {}
            for key, default in DASHBOARD_MAP_KEYS.items():
                merged_options[key] = _positive_int(map_settings.get(key, merged_options.get(key)), default, minimum=0, maximum=24)
            map_theme_mode = str(map_settings.get(DASHBOARD_MAP_THEME_KEY, merged_options.get(DASHBOARD_MAP_THEME_KEY, DASHBOARD_MAP_THEME_DEFAULT)) or DASHBOARD_MAP_THEME_DEFAULT).strip().lower()
            merged_options[DASHBOARD_MAP_THEME_KEY] = map_theme_mode if map_theme_mode in DASHBOARD_MAP_THEME_MODES else DASHBOARD_MAP_THEME_DEFAULT

            person = dashboard_settings.get("person_track") if isinstance(dashboard_settings.get("person_track"), dict) else {}
            for key, default in DASHBOARD_PERSON_TRACK_KEYS.items():
                if key.endswith("_enabled") or key in {"person_track_enabled", "person_track_show_button"}:
                    if key in person:
                        merged_options[key] = _to_bool(person.get(key), bool(default))
                elif key == "person_track_hours_to_show":
                    merged_options[key] = _positive_int(person.get(key, merged_options.get(key)), int(default), minimum=0, maximum=24)
                elif key in person:
                    merged_options[key] = str(person.get(key) or "").strip()

        if dashboard_entity_manager is not None:
            saved_sections.append("dashboard_entity_manager")
            action = str(dashboard_entity_manager.get("action") or "save").strip().lower()
            dashboard_main_entity = str(dashboard_entity_manager.get("main_entity") or merged_options.get(CONF_DASHBOARD_MAIN_ENTITY) or merged_options.get(CONF_AI_MAIN_TESLA_ENTITY) or DEFAULT_AI_MAIN_TESLA_ENTITY or "").strip()
            if dashboard_main_entity:
                merged_options[CONF_DASHBOARD_MAIN_ENTITY] = dashboard_main_entity
            dashboard_entries: list[dict[str, Any]] = []
            by_role: dict[str, dict[str, Any]] = {}
            raw_entries = dashboard_entity_manager.get("entries") if isinstance(dashboard_entity_manager.get("entries"), list) else []
            for item in raw_entries:
                if not isinstance(item, dict):
                    continue
                entity_id = str(item.get("entity_id") or "").strip()
                role = str(item.get("role") or "").strip()
                if not entity_id or role not in DASHBOARD_ENTITY_MANAGER_ROLES or role in by_role:
                    continue
                dash_entry = _dashboard_entry_for_panel(self.hass, entity_id, role=role, source="panel_dashboard_manual")
                if dash_entry:
                    dash_entry["icon"] = str(item.get("icon") or "").strip()
                    dash_entry["name"] = str(item.get("name") or "").strip()
                    by_role[role] = dash_entry
            if action == "auto_find":
                discovered = _auto_discover_dashboard_entries_panel(self.hass, {**dict(entry.data or {}), **merged_options, CONF_DASHBOARD_MAIN_ENTITY: dashboard_main_entity})
                for item in discovered:
                    role = str(item.get("role") or "").strip()
                    if role and role not in by_role:
                        by_role[role] = item
            for role in DASHBOARD_ENTITY_MANAGER_ROLES:
                if role in by_role:
                    dashboard_entries.append(by_role[role])
            panel_dashboard_entries = _normalize_panel_dashboard_entity_map_panel(dashboard_entries)
            merged_options[CONF_PANEL_DASHBOARD_ENTITY_MAP] = panel_dashboard_entries
            # Keep old dashboard option keys synced for the current dashboard renderer,
            # but the panel_dashboard_entity_map remains authoritative if Flow changes later.
            merged_options[CONF_DASHBOARD_ENTITY_MAP] = panel_dashboard_entries
            _sync_dashboard_legacy_options(merged_options, panel_dashboard_entries)

        if trip_reports is not None:
            saved_sections.append("trip_reports")
            merged_options[CONF_AUTO_TRIP_TRACKING] = _to_bool(
                trip_reports.get("auto_trip_tracking", merged_options.get(CONF_AUTO_TRIP_TRACKING)),
                DEFAULT_AUTO_TRIP_TRACKING,
            )
            merged_options[CONF_AUTO_START_SPEED_THRESHOLD] = round(
                _positive_float(
                    trip_reports.get("auto_start_speed_threshold", merged_options.get(CONF_AUTO_START_SPEED_THRESHOLD)),
                    DEFAULT_AUTO_START_SPEED_THRESHOLD,
                    minimum=0.0,
                    maximum=250.0,
                ),
                2,
            )
            # Live Trip uses the same master switch as automatic trip tracking.
            merged_options[CONF_LIVE_TRIP_ENABLED] = _to_bool(
                trip_reports.get("auto_trip_tracking", trip_reports.get("live_trip_enabled", merged_options.get(CONF_LIVE_TRIP_ENABLED))),
                DEFAULT_LIVE_TRIP_ENABLED,
            )
            merged_options[CONF_LIVE_TRIP_UPDATE_INTERVAL_SECONDS] = _positive_int(
                trip_reports.get("live_trip_update_interval_seconds", merged_options.get(CONF_LIVE_TRIP_UPDATE_INTERVAL_SECONDS)),
                DEFAULT_LIVE_TRIP_UPDATE_INTERVAL_SECONDS,
                minimum=1,
                maximum=300,
            )
            merged_options[CONF_LIVE_TRIP_TRAFFIC_SPEED_THRESHOLD] = round(
                _positive_float(
                    trip_reports.get("live_trip_traffic_speed_threshold", merged_options.get(CONF_LIVE_TRIP_TRAFFIC_SPEED_THRESHOLD)),
                    DEFAULT_LIVE_TRIP_TRAFFIC_SPEED_THRESHOLD,
                    minimum=0.0,
                    maximum=250.0,
                ),
                2,
            )
            merged_options[CONF_LIVE_TRIP_FINISH_DELAY_SECONDS] = _positive_int(
                trip_reports.get("live_trip_finish_delay_seconds", merged_options.get(CONF_LIVE_TRIP_FINISH_DELAY_SECONDS)),
                DEFAULT_LIVE_TRIP_FINISH_DELAY_SECONDS,
                minimum=1,
                maximum=3600,
            )
            merged_options[CONF_LIVE_TRIP_MIN_DISTANCE_KM] = round(
                _positive_float(
                    trip_reports.get("live_trip_min_distance_km", merged_options.get(CONF_LIVE_TRIP_MIN_DISTANCE_KM)),
                    DEFAULT_LIVE_TRIP_MIN_DISTANCE_KM,
                    minimum=0.0,
                    maximum=10000.0,
                ),
                3,
            )
            merged_options[CONF_LIVE_TRIP_IGNORE_SHORT_MANEUVERS] = _to_bool(
                trip_reports.get("live_trip_ignore_short_maneuvers", merged_options.get(CONF_LIVE_TRIP_IGNORE_SHORT_MANEUVERS)),
                DEFAULT_LIVE_TRIP_IGNORE_SHORT_MANEUVERS,
            )
            merged_options[CONF_LIVE_TRIP_CANDIDATE_MIN_DISTANCE_KM] = round(
                _positive_float(
                    trip_reports.get("live_trip_candidate_min_distance_km", merged_options.get(CONF_LIVE_TRIP_CANDIDATE_MIN_DISTANCE_KM)),
                    DEFAULT_LIVE_TRIP_CANDIDATE_MIN_DISTANCE_KM,
                    minimum=0.0,
                    maximum=100.0,
                ),
                3,
            )
            merged_options[CONF_LIVE_TRIP_CANDIDATE_MIN_DURATION_SECONDS] = _positive_int(
                trip_reports.get("live_trip_candidate_min_duration_seconds", merged_options.get(CONF_LIVE_TRIP_CANDIDATE_MIN_DURATION_SECONDS)),
                DEFAULT_LIVE_TRIP_CANDIDATE_MIN_DURATION_SECONDS,
                minimum=0,
                maximum=3600,
            )
            merged_options[CONF_LIVE_TRIP_AI_SEGMENT_DISTANCE_KM] = _live_trip_ai_segment_distance_for_panel(
                trip_reports.get("live_trip_ai_segment_distance_km", merged_options.get(CONF_LIVE_TRIP_AI_SEGMENT_DISTANCE_KM))
            )
            # Live Trip AI story belongs to Live Trip settings. It reuses the
            # existing post-trip AI summary option internally so older configs
            # remain compatible.
            merged_options[CONF_AI_ALERT_POST_TRIP_SUMMARY_ENABLED] = _to_bool(
                trip_reports.get("ai_trip_story_enabled", merged_options.get(CONF_AI_ALERT_POST_TRIP_SUMMARY_ENABLED)),
                DEFAULT_AI_ALERT_POST_TRIP_SUMMARY_ENABLED,
            )
            story_detail_level = str(
                trip_reports.get("ai_trip_story_detail_level", merged_options.get(CONF_AI_TRIP_STORY_DETAIL_LEVEL, DEFAULT_AI_TRIP_STORY_DETAIL_LEVEL))
                or DEFAULT_AI_TRIP_STORY_DETAIL_LEVEL
            ).strip()
            merged_options[CONF_AI_TRIP_STORY_DETAIL_LEVEL] = story_detail_level if story_detail_level in AI_TRIP_STORY_DETAIL_OPTIONS else DEFAULT_AI_TRIP_STORY_DETAIL_LEVEL

            merged_options[CONF_TRIP_MAP_ENABLED] = _to_bool(
                trip_reports.get("trip_map_enabled", merged_options.get(CONF_TRIP_MAP_ENABLED)),
                DEFAULT_TRIP_MAP_ENABLED,
            )
            merged_options[CONF_TRIP_MAP_TRACKER_ENTITY] = str(
                trip_reports.get("trip_map_tracker_entity", merged_options.get(CONF_TRIP_MAP_TRACKER_ENTITY, DEFAULT_TRIP_MAP_TRACKER_ENTITY)) or ""
            ).strip()
            merged_options[CONF_TRIP_MAP_SAMPLE_INTERVAL_SECONDS] = _positive_int(
                trip_reports.get("trip_map_sample_interval_seconds", merged_options.get(CONF_TRIP_MAP_SAMPLE_INTERVAL_SECONDS)),
                DEFAULT_TRIP_MAP_SAMPLE_INTERVAL_SECONDS,
                minimum=1,
                maximum=300,
            )
            merged_options[CONF_TRIP_MAP_MIN_MOVEMENT_METERS] = round(
                _positive_float(
                    trip_reports.get("trip_map_min_movement_meters", merged_options.get(CONF_TRIP_MAP_MIN_MOVEMENT_METERS)),
                    DEFAULT_TRIP_MAP_MIN_MOVEMENT_METERS,
                    minimum=0.0,
                    maximum=10000.0,
                ),
                2,
            )
            merged_options[CONF_TRIP_MAP_SEND_SEPARATE_PNG] = _to_bool(
                trip_reports.get("trip_map_send_separate_png", merged_options.get(CONF_TRIP_MAP_SEND_SEPARATE_PNG)),
                DEFAULT_TRIP_MAP_SEND_SEPARATE_PNG,
            )

            show_flags = {
                CONF_SHOW_DISTANCE: DEFAULT_SHOW_DISTANCE,
                CONF_SHOW_DURATION: DEFAULT_SHOW_DURATION,
                CONF_SHOW_TRAFFIC: DEFAULT_SHOW_TRAFFIC,
                CONF_SHOW_AVERAGE_SPEED: DEFAULT_SHOW_AVERAGE_SPEED,
                CONF_SHOW_ENERGY: DEFAULT_SHOW_ENERGY,
                CONF_SHOW_CONSUMPTION: DEFAULT_SHOW_CONSUMPTION,
                CONF_SHOW_BATTERY: DEFAULT_SHOW_BATTERY,
                CONF_SHOW_COST: DEFAULT_SHOW_COST,
                CONF_SHOW_CLIMATE: DEFAULT_SHOW_CLIMATE,
                CONF_SHOW_ELEVATION: DEFAULT_SHOW_ELEVATION,
                CONF_SHOW_TRIP_MAP: DEFAULT_SHOW_TRIP_MAP,
            }
            for key, default in show_flags.items():
                merged_options[key] = _to_bool(trip_reports.get(key, merged_options.get(key)), default)

            periodic_flags = {
                CONF_TELEGRAM_WEEKLY_TRIP_REPORT_ENABLED: DEFAULT_TELEGRAM_WEEKLY_TRIP_REPORT_ENABLED,
                CONF_TELEGRAM_MONTHLY_TRIP_REPORT_ENABLED: DEFAULT_TELEGRAM_MONTHLY_TRIP_REPORT_ENABLED,
                CONF_TELEGRAM_WEEKLY_CHARGE_REPORT_ENABLED: DEFAULT_TELEGRAM_WEEKLY_CHARGE_REPORT_ENABLED,
                CONF_TELEGRAM_MONTHLY_CHARGE_REPORT_ENABLED: DEFAULT_TELEGRAM_MONTHLY_CHARGE_REPORT_ENABLED,
            }
            for key, default in periodic_flags.items():
                merged_options[key] = _to_bool(trip_reports.get(key, merged_options.get(key)), default)

        try:
            self.hass.config_entries.async_update_entry(entry, options=merged_options)
            self.hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {**dict(entry.data or {}), **merged_options}
            if trip_reports is not None:
                try:
                    from . import async_sync_live_trip_ai_interval_from_options  # pylint: disable=import-outside-toplevel
                    await async_sync_live_trip_ai_interval_from_options(
                        self.hass,
                        entry.entry_id,
                        {**dict(entry.data or {}), **merged_options},
                    )
                except Exception:
                    _LOGGER.exception("Could not sync Live Trip AI interval after panel settings save")
        except Exception as err:
            _LOGGER.exception("Could not update POM Tesla settings from panel")
            return web.json_response({"success": False, "error": str(err)}, status=500)

        dashboard_rebuild_started = _should_rebuild_dashboard_after_panel_save(saved_sections, merged_options)
        if dashboard_rebuild_started:
            self.hass.async_create_task(
                _run_dashboard_rebuild_from_panel(
                    self.hass,
                    {**dict(entry.data or {}), **merged_options},
                    reason=",".join(saved_sections) or "panel_save",
                )
            )

        payload = _settings_save_response_payload(self.hass, merged_options, saved_sections=saved_sections)
        if dashboard_rebuild_started:
            payload["dashboard_rebuild_started"] = True
            payload["dashboard_rebuild_message"] = "Dashboard YAML rebuild started in background. Refresh the dashboard page after a few seconds."
        return web.json_response(payload)



def _trip_visibility_options_from_data(data: dict[str, Any]) -> dict[str, bool]:
    return {
        "show_distance": _to_bool(data.get(CONF_SHOW_DISTANCE), DEFAULT_SHOW_DISTANCE),
        "show_duration": _to_bool(data.get(CONF_SHOW_DURATION), DEFAULT_SHOW_DURATION),
        "show_traffic": _to_bool(data.get(CONF_SHOW_TRAFFIC), DEFAULT_SHOW_TRAFFIC),
        "show_average_speed": _to_bool(data.get(CONF_SHOW_AVERAGE_SPEED), DEFAULT_SHOW_AVERAGE_SPEED),
        "show_energy": _to_bool(data.get(CONF_SHOW_ENERGY), DEFAULT_SHOW_ENERGY),
        "show_consumption": _to_bool(data.get(CONF_SHOW_CONSUMPTION), DEFAULT_SHOW_CONSUMPTION),
        "show_battery": _to_bool(data.get(CONF_SHOW_BATTERY), DEFAULT_SHOW_BATTERY),
        "show_cost": _to_bool(data.get(CONF_SHOW_COST), DEFAULT_SHOW_COST),
        "show_climate": _to_bool(data.get(CONF_SHOW_CLIMATE), DEFAULT_SHOW_CLIMATE),
        "show_elevation": _to_bool(data.get(CONF_SHOW_ELEVATION), DEFAULT_SHOW_ELEVATION),
    }


def _ensure_www_report_dir(hass: HomeAssistant) -> Path:
    out_dir = Path(hass.config.path("www", "pom_tesla_report"))
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def _ensure_www_dashboard_background_dir(hass: HomeAssistant) -> Path:
    out_dir = Path(hass.config.path("www", "pom_tesla_report", "dashboard", "backgrounds"))
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def _dashboard_background_slot_map() -> dict[str, tuple[str, str]]:
    return {
        "parked": (DASHBOARD_IMAGE_PARKED_KEY, DASHBOARD_BUNDLED_IMAGE_PARKED),
        "charging": (DASHBOARD_IMAGE_CHARGING_KEY, DASHBOARD_BUNDLED_IMAGE_CHARGING),
        "driving": (DASHBOARD_IMAGE_DRIVING_KEY, DASHBOARD_BUNDLED_IMAGE_DRIVING),
        "drive_vehicle": (DASHBOARD_DRIVE_VEHICLE_IMAGE_KEY, ""),
        "drive_tire": (DASHBOARD_DRIVE_TIRE_PRESSURE_IMAGE_KEY, ""),
    }




def _dashboard_panel_version() -> str:
    """Return dashboard resource version without reading manifest.json in the event loop."""
    return DASHBOARD_PANEL_VERSION


def _resource_base_url_panel(url: str) -> str:
    return str(url or "").split("?", 1)[0].strip()


def _dashboard_panel_desired_resources() -> list[dict[str, str]]:
    version = _dashboard_panel_version()
    resources: list[dict[str, str]] = []
    for item in DASHBOARD_PANEL_RESOURCE_ITEMS:
        url_path = str(item.get("url_path") or "").strip()
        if not url_path:
            continue
        resources.append({
            "name": str(item.get("name") or ""),
            "url": f"{url_path}?v={version}",
            "type": str(item.get("type") or "module"),
            "github": str(item.get("github") or ""),
            "description": str(item.get("description") or ""),
        })
    return resources


def _dashboard_resources_status_payload_blocking(hass: HomeAssistant) -> dict[str, Any]:
    storage_path = Path(hass.config.path(".storage", "lovelace_resources"))
    existing_by_base: dict[str, dict[str, Any]] = {}
    storage_exists = storage_path.exists()
    storage_error = ""
    if storage_exists:
        try:
            payload = json.loads(storage_path.read_text(encoding="utf-8"))
            items = ((payload or {}).get("data") or {}).get("items") or []
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        base = _resource_base_url_panel(str(item.get("url") or ""))
                        if base:
                            existing_by_base[base] = item
        except Exception as err:
            storage_error = str(err)

    desired_resources = _dashboard_panel_desired_resources()
    resource_rows: list[dict[str, Any]] = []
    missing_resources: list[dict[str, Any]] = []
    for desired in desired_resources:
        base = _resource_base_url_panel(desired["url"])
        existing = existing_by_base.get(base)
        installed = existing is not None
        row = {
            **desired,
            "base_url": base,
            "installed": installed,
            "current_url": str((existing or {}).get("url") or ""),
            "status": "installed" if installed else "missing",
        }
        resource_rows.append(row)
        if not installed:
            missing_resources.append(row)

    dependency_rows: list[dict[str, Any]] = []
    missing_dependencies: list[dict[str, Any]] = []
    for dep in DASHBOARD_PANEL_CUSTOM_DEPENDENCIES:
        checks = [str(path) for path in dep.get("local_checks") or []]
        found_paths = [path for path in checks if Path(hass.config.path(path)).exists()]
        installed = bool(found_paths)
        row = {
            "name": str(dep.get("name") or ""),
            "type": str(dep.get("type") or ""),
            "github": str(dep.get("github") or ""),
            "description": str(dep.get("description") or ""),
            "installed": installed,
            "status": "installed" if installed else "missing",
            "found_paths": found_paths,
            "local_checks": checks,
        }
        dependency_rows.append(row)
        if not installed:
            missing_dependencies.append(row)

    return {
        "resources": resource_rows,
        "missing_resources": missing_resources,
        "dependencies": dependency_rows,
        "missing_dependencies": missing_dependencies,
        "storage_path": str(storage_path),
        "storage_exists": storage_exists,
        "storage_error": storage_error,
        "resource_service_available": hass.services.has_service(DOMAIN, "install_dashboard_resources"),
        "summary": {
            "resources_total": len(resource_rows),
            "resources_missing": len(missing_resources),
            "dependencies_total": len(dependency_rows),
            "dependencies_missing": len(missing_dependencies),
        },
    }

def _bounded_float_panel(value: Any, default: float = 1.0, minimum: float = 0.7, maximum: float = 1.6) -> float:
    """Return a bounded float for dashboard visual scale options."""
    try:
        parsed = float(value)
    except Exception:
        parsed = default
    if parsed < minimum:
        parsed = minimum
    if parsed > maximum:
        parsed = maximum
    return round(parsed, 2)


def _dashboard_settings_payload(hass: HomeAssistant) -> dict[str, Any]:
    data = _entry_config(hass)
    images: dict[str, str] = {}
    defaults: dict[str, str] = {}
    for slot, (option_key, default_url) in _dashboard_background_slot_map().items():
        images[slot] = str(data.get(option_key) or default_url).strip() or default_url
        defaults[slot] = default_url

    top_values: dict[str, str] = {}
    for key, default in DASHBOARD_TOP_SLOT_KEYS.items():
        allowed = DASHBOARD_CENTER_SLOT_TYPES if key == "top_center_slot" else DASHBOARD_TOP_SLOT_TYPES
        value = str(data.get(key) or default).strip()
        top_values[key] = value if value in allowed else default

    sidebar_values: dict[str, str] = {}
    for index, key in enumerate(DASHBOARD_SIDEBAR_SLOT_KEYS):
        default = DASHBOARD_SIDEBAR_DEFAULTS[index] if index < len(DASHBOARD_SIDEBAR_DEFAULTS) else "empty"
        value = str(data.get(key) or default).strip()
        sidebar_values[key] = value if value in DASHBOARD_SIDEBAR_ACTION_TYPES else default

    return {
        "resources_status": _dashboard_resources_status_payload(hass),
        "images": images,
        "defaults": defaults,
        "allowed_extensions": ["png", "jpg", "jpeg", "webp", "gif"],
        "max_bytes": DASHBOARD_BACKGROUND_UPLOAD_MAX_BYTES,
        "youtube_driving_background": {
            "enabled": _to_bool(data.get("youtube_driving_bg_enabled"), False),
            "video": str(data.get("youtube_driving_bg_video") or "").strip(),
            "start_seconds": _positive_int(data.get("youtube_driving_bg_start_seconds"), 0, minimum=0, maximum=86400),
            "mute": _to_bool(data.get("youtube_driving_bg_mute"), True),
            "loop": _to_bool(data.get("youtube_driving_bg_loop"), True),
            "quality": str(data.get("youtube_driving_bg_quality") or "480").strip() if str(data.get("youtube_driving_bg_quality") or "480").strip() in ("360", "480", "720", "1080_lite", "1080", "1080_high") else "480",
        },
        "drive_dashboard": {
            "vehicle_image": str(data.get(DASHBOARD_DRIVE_VEHICLE_IMAGE_KEY) or "").strip(),
            "tire_pressure_image": str(data.get(DASHBOARD_DRIVE_TIRE_PRESSURE_IMAGE_KEY) or "").strip(),
        },
        "fullscreen": {
            key: _to_bool(data.get(key), default)
            for key, default in DASHBOARD_FULLSCREEN_KEYS.items()
        },
        "top_area": {
            "slots": top_values,
            "font_scales": {
                key: _bounded_float_panel(data.get(key), default)
                for key, default in DASHBOARD_TOP_FONT_SCALE_KEYS.items()
            },
            "font_scale_min": 0.7,
            "font_scale_max": 1.6,
            "font_scale_step": 0.05,
            "options": DASHBOARD_TOP_SLOT_TYPES,
            "options_list": [{"value": key, "label": label} for key, label in DASHBOARD_TOP_SLOT_TYPES.items()],
            "center_options": DASHBOARD_CENTER_SLOT_TYPES,
            "center_options_list": [{"value": key, "label": label} for key, label in DASHBOARD_CENTER_SLOT_TYPES.items()],
        },
        "sidebar": {
            "slots": sidebar_values,
            "options": DASHBOARD_SIDEBAR_ACTION_TYPES,
            "options_list": [{"value": key, "label": label} for key, label in DASHBOARD_SIDEBAR_ACTION_TYPES.items()],
        },
        "bottom_bar": {
            "location_display_mode": str(data.get("location_display_mode") or "auto_short"),
            "location_display_modes": DASHBOARD_LOCATION_DISPLAY_MODES,
            "location_display_modes_list": [{"value": key, "label": label} for key, label in DASHBOARD_LOCATION_DISPLAY_MODES.items()],
            "slots": {key: (str(data.get(key) or default).strip() if str(data.get(key) or default).strip() in DASHBOARD_BOTTOM_SLOT_TYPES else default) for key, default in DASHBOARD_BOTTOM_SLOT_KEYS.items()},
            "slot_options": DASHBOARD_BOTTOM_SLOT_TYPES,
            "slot_options_list": [{"value": key, "label": label} for key, label in DASHBOARD_BOTTOM_SLOT_TYPES.items()],
            "toggles": {key: _to_bool(data.get(key), default) for key, default in DASHBOARD_BOTTOM_TOGGLE_KEYS.items()},
        },
        "map": {
            **{
                key: _positive_int(data.get(key), default, minimum=0, maximum=24)
                for key, default in DASHBOARD_MAP_KEYS.items()
            },
            DASHBOARD_MAP_THEME_KEY: str(data.get(DASHBOARD_MAP_THEME_KEY) or DASHBOARD_MAP_THEME_DEFAULT).strip() if str(data.get(DASHBOARD_MAP_THEME_KEY) or DASHBOARD_MAP_THEME_DEFAULT).strip() in DASHBOARD_MAP_THEME_MODES else DASHBOARD_MAP_THEME_DEFAULT,
            "map_theme_modes": DASHBOARD_MAP_THEME_MODES,
            "map_theme_modes_list": [{"value": key, "label": label} for key, label in DASHBOARD_MAP_THEME_MODES.items()],
        },
        "person_track": {
            "person_track_enabled": _to_bool(data.get("person_track_enabled"), True),
            "person_track_show_button": _to_bool(data.get("person_track_show_button"), True),
            "person_track_hours_to_show": _positive_int(data.get("person_track_hours_to_show"), 15, minimum=0, maximum=24),
            "person_track_1_entity": str(data.get("person_track_1_entity") or "person.cavidan").strip(),
            "person_track_1_name": str(data.get("person_track_1_name") or "Cavidan").strip(),
            "person_track_1_enabled": _to_bool(data.get("person_track_1_enabled"), True),
            "person_track_2_entity": str(data.get("person_track_2_entity") or "person.ali").strip(),
            "person_track_2_name": str(data.get("person_track_2_name") or "Ali").strip(),
            "person_track_2_enabled": _to_bool(data.get("person_track_2_enabled"), True),
            "person_track_3_entity": str(data.get("person_track_3_entity") or "").strip(),
            "person_track_3_name": str(data.get("person_track_3_name") or "Person 3").strip(),
            "person_track_3_enabled": _to_bool(data.get("person_track_3_enabled"), False),
        },
    }


def _create_panel_test_trip_map_png(output_path: str, *, lang: str) -> str:
    """Create a lightweight local placeholder route map for the panel test trip.

    This intentionally avoids writing any trip ledger entry and avoids relying on
    OpenStreetMap network access. It exists only to let the user test whether the
    visual trip report embeds a route map when the report map toggle is enabled.
    """
    image = Image.new("RGB", (1200, 680), "#eef2f7")
    draw = ImageDraw.Draw(image)
    # subtle grid / fake city blocks
    for x in range(0, 1200, 90):
        draw.line((x, 0, x, 680), fill="#d7dee8", width=1)
    for y in range(0, 680, 70):
        draw.line((0, y, 1200, y), fill="#d7dee8", width=1)
    draw.rounded_rectangle((34, 34, 1166, 646), radius=28, outline="#94a3b8", width=4)
    route = [(120, 520), (250, 455), (330, 470), (460, 350), (620, 370), (760, 250), (910, 270), (1060, 145)]
    # route glow
    for width, color in [(16, "#bfdbfe"), (8, "#2563eb")]:
        draw.line(route, fill=color, width=width, joint="curve")
    sx, sy = route[0]
    ex, ey = route[-1]
    draw.ellipse((sx - 18, sy - 18, sx + 18, sy + 18), fill="#16a34a", outline="white", width=4)
    draw.ellipse((ex - 18, ey - 18, ex + 18, ey + 18), fill="#dc2626", outline="white", width=4)
    title = "Test route map" if lang == APP_LANGUAGE_EN else "Test sürüş haritası"
    draw.rounded_rectangle((54, 54, 360, 108), radius=16, fill="#0f172a")
    draw.text((74, 70), title, fill="#ffffff")
    image.save(output_path)
    return output_path


def _build_panel_test_trip_report_data(hass: HomeAssistant, data: dict[str, Any], profile: str = "city") -> dict[str, Any]:
    """Build a non-persistent but realistic sample trip payload.

    alpha251 fixes the alpha250 simulator mistake: each direct test button now
    uses a genuinely different route and trip profile, not the same Suadiye →
    Gayrettepe route with different numbers.
    """
    lang = _app_language(hass)
    currency = _report_currency(hass)
    profile = str(profile or "city").strip().lower()
    if profile not in {"city", "traffic", "efficient"}:
        profile = "city"

    profiles = {
        "city": {
            "label_tr": "Kısa Kadıköy sahil sürüşü",
            "label_en": "Short Kadıköy coastal drive",
            "route_tr": "Suadiye → Kalamış",
            "route_en": "Suadiye → Kalamış",
            "start_tr": "Suadiye Mahallesi, Kadıköy, İstanbul, Türkiye",
            "end_tr": "Kalamış Marina, Fenerbahçe Mahallesi, Kadıköy, İstanbul, Türkiye",
            "start_en": "Suadiye, Kadıköy, Istanbul, Turkey",
            "end_en": "Kalamış Marina, Fenerbahçe, Kadıköy, Istanbul, Turkey",
            "trip_km": 4.80,
            "used_kwh": 0.72,
            "duration_min": 14,
            "traffic_min": 4,
            "avg_speed": 31.4,
            "overall_speed": 20.6,
            "consumption": 15.00,
            "start_battery": 66.0,
            "end_battery": 65.0,
            "min_el": 3,
            "max_el": 24,
            "gain": 22,
            "loss": 9,
            "score": 84,
            "traffic_delay_min": 4,
            "free_flow_min": 10,
            "traffic_pct": 29,
            "slow_min": 3,
            "stop_min": 1,
            "normal_min": 10,
            "impact": "Düşük",
            "impact_en": "Low",
            "weather": "Kısa şehir içi kullanımda tüketim normal aralıkta; kısa mesafe nedeniyle yorum sınırlı güvenilirliktedir.",
            "weather_en": "Consumption is normal for a short urban drive; reliability is limited because the trip is short.",
        },
        "traffic": {
            "label_tr": "Trafikli şehir içi sürüş",
            "label_en": "Traffic-heavy urban drive",
            "route_tr": "Suadiye → Gayrettepe",
            "route_en": "Suadiye → Gayrettepe",
            "start_tr": "Suadiye Mahallesi, Kadıköy, İstanbul, Türkiye",
            "end_tr": "Gayrettepe Mahallesi, Beşiktaş, İstanbul, Türkiye",
            "start_en": "Suadiye, Kadıköy, Istanbul, Turkey",
            "end_en": "Gayrettepe, Beşiktaş, Istanbul, Turkey",
            "trip_km": 17.80,
            "used_kwh": 4.72,
            "duration_min": 64,
            "traffic_min": 46,
            "avg_speed": 24.1,
            "overall_speed": 16.7,
            "consumption": 26.52,
            "start_battery": 64.0,
            "end_battery": 56.0,
            "min_el": 3,
            "max_el": 122,
            "gain": 142,
            "loss": 35,
            "score": 61,
            "traffic_delay_min": 28,
            "free_flow_min": 36,
            "traffic_pct": 78,
            "slow_min": 28,
            "stop_min": 18,
            "normal_min": 18,
            "impact": "Yüksek",
            "impact_en": "High",
            "weather": "Dur-kalk ve düşük hız tüketimi hava koşulundan daha fazla etkilemiş görünüyor.",
            "weather_en": "Stop-go traffic appears to affect consumption more than weather.",
        },
        "efficient": {
            "label_tr": "Uzun verimli otoyol sürüşü",
            "label_en": "Long efficient highway drive",
            "route_tr": "İstanbul → İzmit",
            "route_en": "Istanbul → Izmit",
            "start_tr": "Suadiye Mahallesi, Kadıköy, İstanbul, Türkiye",
            "end_tr": "İzmit Merkez, Kocaeli, Türkiye",
            "start_en": "Suadiye, Kadıköy, Istanbul, Turkey",
            "end_en": "Izmit city center, Kocaeli, Turkey",
            "trip_km": 92.50,
            "used_kwh": 13.40,
            "duration_min": 82,
            "traffic_min": 10,
            "avg_speed": 79.5,
            "overall_speed": 67.7,
            "consumption": 14.49,
            "start_battery": 79.0,
            "end_battery": 57.0,
            "min_el": 4,
            "max_el": 210,
            "gain": 260,
            "loss": 110,
            "score": 91,
            "traffic_delay_min": 6,
            "free_flow_min": 76,
            "traffic_pct": 8,
            "slow_min": 6,
            "stop_min": 4,
            "normal_min": 72,
            "impact": "Düşük",
            "impact_en": "Low",
            "weather": "Akıcı otoyol temposu ve sınırlı trafik tüketimi düşük tutmuş.",
            "weather_en": "Smooth highway flow and limited traffic kept consumption low.",
        },
    }
    spec = profiles[profile]
    used_kwh = float(spec["used_kwh"])
    cost_presets = _trip_cost_presets(data, used_kwh=used_kwh)

    if lang == APP_LANGUAGE_EN:
        duration_text = f"{int(spec['duration_min'])} min"
        traffic_text = f"{int(spec['traffic_min'])} min"
        climate_duration_text = f"{max(0, int(spec['duration_min']) - 6)} min"
        delay_text = f"{int(spec['traffic_delay_min'])} min"
        free_flow_text = f"{int(spec['free_flow_min'])} min"
        slow_text = f"{int(spec['slow_min'])} min"
        stop_text = f"{int(spec['stop_min'])} min"
        normal_text = f"{int(spec['normal_min'])} min"
        profile_label = spec["label_en"]
        route_label = spec["route_en"]
        start_address = spec["start_en"]
        end_address = spec["end_en"]
        score_label = "Excellent" if spec["score"] >= 85 else ("Good" if spec["score"] >= 70 else "Traffic affected")
        score_text = f"{spec['score']}/100 · efficiency and flow model"
        grade_text = f"+{spec['gain']} m / -{spec['loss']} m · {spec['impact_en']} elevation impact"
    else:
        duration_text = f"{int(spec['duration_min'])} dk"
        traffic_text = f"{int(spec['traffic_min'])} dk"
        climate_duration_text = f"{max(0, int(spec['duration_min']) - 6)} dk"
        delay_text = f"{int(spec['traffic_delay_min'])} dk"
        free_flow_text = f"{int(spec['free_flow_min'])} dk"
        slow_text = f"{int(spec['slow_min'])} dk"
        stop_text = f"{int(spec['stop_min'])} dk"
        normal_text = f"{int(spec['normal_min'])} dk"
        profile_label = spec["label_tr"]
        route_label = spec["route_tr"]
        start_address = spec["start_tr"]
        end_address = spec["end_tr"]
        score_label = "Çok iyi" if spec["score"] >= 85 else ("İyi" if spec["score"] >= 70 else "Trafik etkili")
        score_text = f"{spec['score']}/100 · verimlilik ve akış modeli"
        grade_text = f"+{spec['gain']} m / -{spec['loss']} m · {spec['impact']} eğim etkisi"

    return {
        "test_profile": profile,
        "test_profile_label": profile_label,
        "test_route_label": route_label,
        "test_mode": True,
        "currency_label": currency,
        "report_date": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "start_address": start_address,
        "end_address": end_address,
        "trip_km": f"{spec['trip_km']:.2f}",
        "duration_text": duration_text,
        "traffic_text": traffic_text,
        "average_speed": f"{spec['avg_speed']:.1f}",
        "average_overall_speed": f"{spec['overall_speed']:.1f}",
        "used_kwh": f"{used_kwh:.2f}",
        "consumption_kwh_100km": f"{spec['consumption']:.2f}",
        "start_battery": f"{spec['start_battery']:.1f}",
        "end_battery": f"{spec['end_battery']:.1f}",
        "climate_duration_minutes": str(max(0, int(spec["duration_min"]) - 6)),
        "climate_duration_text": climate_duration_text,
        "min_elevation": str(int(spec["min_el"])),
        "max_elevation": str(int(spec["max_el"])),
        "elevation_range": str(int(spec["max_el"] - spec["min_el"])),
        "elevation_gain": str(int(spec["gain"])),
        "elevation_loss": str(int(spec["loss"])),
        "elevation_sample_count": "18",
        "elevation_grade_text": grade_text,
        "estimated_climb_energy_kwh": f"{spec['gain'] * 0.002:.2f}",
        "estimated_regen_potential_kwh": f"{spec['loss'] * 0.0012:.2f}",
        "traffic_delay_seconds": str(int(spec["traffic_delay_min"]) * 60),
        "traffic_congestion_percent": str(int(spec["traffic_pct"])),
        "traffic_reference_speed_kmh": "38" if profile != "efficient" else "82",
        "traffic_reference_trip_type_label": profile_label,
        "traffic_impact_label": spec["impact_en"] if lang == APP_LANGUAGE_EN else spec["impact"],
        "traffic_free_flow_text": free_flow_text,
        "traffic_delay_text": delay_text,
        "stopped_in_drive_text": stop_text,
        "slow_traffic_text": slow_text,
        "normal_drive_text": normal_text,
        "driving_score": str(int(spec["score"])),
        "driving_score_label": score_label,
        "driving_score_text": score_text,
        "weather_impact_text": spec["weather_en"] if lang == APP_LANGUAGE_EN else spec["weather"],
        "cost_presets": cost_presets,
        **_trip_visibility_options_from_data(data),
    }


def _build_panel_test_trip_map_data(report_data: dict[str, Any], *, lang: str) -> dict[str, Any]:
    """Return distinct sample routes for the three direct test buttons."""
    profile = str(report_data.get("test_profile") or "city").strip().lower()
    if profile not in {"city", "traffic", "efficient"}:
        profile = "city"

    route_specs = {
        "city": {
            "points": [
                (40.9659, 29.0822, 30, 8),
                (40.9638, 29.0732, 26, 7),
                (40.9652, 29.0630, 22, 9),
                (40.9677, 29.0538, 18, 11),
                (40.9714, 29.0468, 14, 14),
                (40.9767, 29.0392, 18, 17),
            ],
            "footer_tr": "Simüle kısa Kadıköy sahil rotasıdır; Sürüş Kayıtları'na yazılmaz.",
            "footer_en": "Simulated short Kadıköy coastal route; not written to Trip Records.",
        },
        "traffic": {
            "points": [
                (40.9659, 29.0822, 18, 18),
                (40.9727, 29.0757, 9, 24),
                (40.9824, 29.0666, 4, 31),
                (40.9962, 29.0574, 2, 44),
                (41.0139, 29.0461, 7, 58),
                (41.0287, 29.0378, 12, 74),
                (41.0425, 29.0298, 6, 91),
                (41.0528, 29.0188, 3, 106),
                (41.0613, 29.0087, 8, 119),
                (41.0662, 29.0009, 10, 112),
            ],
            "footer_tr": "Simüle trafikli Suadiye → Gayrettepe rotasıdır; Sürüş Kayıtları'na yazılmaz.",
            "footer_en": "Simulated traffic-heavy Suadiye → Gayrettepe route; not written to Trip Records.",
        },
        "efficient": {
            "points": [
                (40.9659, 29.0822, 25, 20),
                (40.9820, 29.1470, 55, 60),
                (40.9970, 29.2450, 85, 105),
                (40.9900, 29.3650, 95, 150),
                (40.9650, 29.5000, 105, 180),
                (40.9100, 29.6300, 100, 210),
                (40.8450, 29.7500, 92, 160),
                (40.7850, 29.8600, 70, 85),
                (40.7667, 29.9400, 35, 45),
            ],
            "footer_tr": "Simüle uzun İstanbul → İzmit otoyol rotasıdır; Sürüş Kayıtları'na yazılmaz.",
            "footer_en": "Simulated long Istanbul → Izmit highway route; not written to Trip Records.",
        },
    }
    spec = route_specs[profile]
    points = [
        {"lat": lat, "lon": lon, "speed": speed, "elevation": elevation}
        for lat, lon, speed, elevation in spec["points"]
    ]

    route_label = str(report_data.get("test_route_label") or "").strip()
    title = f"Tesla AI - {route_label}" if route_label else ("Tesla AI - Test Trip Map" if lang == APP_LANGUAGE_EN else "Tesla AI - Test Sürüş Haritası")
    footer = spec["footer_en"] if lang == APP_LANGUAGE_EN else spec["footer_tr"]
    return {
        "title": title,
        "points": points,
        "trip_km": report_data.get("trip_km"),
        "duration_text": report_data.get("duration_text"),
        "footer": footer,
    }


def _build_panel_test_trip_ai_story(report_data: dict[str, Any], *, lang: str) -> str:
    """Build a deterministic Telegram AI-story style text for simulator reports."""
    profile = str(report_data.get("test_profile_label") or report_data.get("test_profile") or "-")
    route = str(report_data.get("test_route_label") or "-")
    if lang == APP_LANGUAGE_EN:
        return (
            "🤖 Tesla AI Driving Comment · Test\n\n"
            f"Profile: {profile}\n"
            f"Route: {route}\n"
            f"Summary: {report_data.get('trip_km')} km in {report_data.get('duration_text')}; "
            f"overall average {report_data.get('average_overall_speed')} km/h, moving average {report_data.get('average_speed')} km/h.\n"
            f"Traffic: {report_data.get('traffic_impact_label')} impact, delay {report_data.get('traffic_delay_text')}, "
            f"stop-go {report_data.get('stopped_in_drive_text')}, slow flow {report_data.get('slow_traffic_text')}.\n"
            f"Efficiency: {report_data.get('consumption_kwh_100km')} kWh/100 km using {report_data.get('used_kwh')} kWh. "
            f"Score: {report_data.get('driving_score')}/100.\n"
            f"Elevation/weather: {report_data.get('elevation_grade_text')}. {report_data.get('weather_impact_text')}\n\n"
            "This is a simulator output; it does not create a Trip Records entry."
        )
    return (
        "🤖 Tesla AI Sürüş Yorumu · Test\n\n"
        f"Profil: {profile}\n"
        f"Rota: {route}\n"
        f"Genel özet: {report_data.get('trip_km')} km, {report_data.get('duration_text')}; "
        f"genel ortalama {report_data.get('average_overall_speed')} km/sa, hareket ortalaması {report_data.get('average_speed')} km/sa.\n"
        f"Trafik: {report_data.get('traffic_impact_label')} etki, gecikme {report_data.get('traffic_delay_text')}, "
        f"dur-kalk {report_data.get('stopped_in_drive_text')}, yavaş akış {report_data.get('slow_traffic_text')}.\n"
        f"Verimlilik: {report_data.get('used_kwh')} kWh enerjiyle {report_data.get('consumption_kwh_100km')} kWh/100 km. "
        f"Skor: {report_data.get('driving_score')}/100.\n"
        f"Eğim/hava: {report_data.get('elevation_grade_text')}. {report_data.get('weather_impact_text')}\n\n"
        "Bu simülatör çıktısıdır; Sürüş Kayıtları'na kayıt eklemez."
    )

def _short_cached_location_label(hass: HomeAssistant) -> str:
    cache = hass.data.setdefault(DOMAIN, {}).get("reverse_geocode_cache") or {}
    parts = cache.get("address_parts") if isinstance(cache.get("address_parts"), dict) else {}
    labels = []
    for key in ("suburb", "neighbourhood", "town", "road"):
        value = str(parts.get(key) or "").strip()
        if value and value not in labels:
            labels.append(value)
    if labels:
        if len(labels) == 1:
            return labels[0]
        combined = f"{labels[0]} · {labels[1]}"
        return combined if len(combined) <= 32 else labels[0]
    address = str(cache.get("address") or "").strip()
    return str(address.split(",")[0] or "").strip()[:32]


def _current_month_charge_records(hass: HomeAssistant) -> list[dict[str, Any]]:
    ledger = _load_charge_ledger(hass)
    default_currency = _report_currency(hass)
    normalized = [_normalize_charge_record(item, default_currency=default_currency) for item in list(ledger.get("records") or []) if isinstance(item, dict)]
    month_key = datetime.now().strftime("%Y-%m")
    records = [item for item in normalized if str(item.get("month_key") or "") == month_key]
    records.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
    return records


def _build_panel_monthly_charge_test_payload(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    lang = _app_language(hass)
    currency = _report_currency(hass)
    records = _current_month_charge_records(hass)
    if not records:
        presets = _effective_provider_presets(data, default_currency=currency)[:3]
        now = datetime.now()
        location = _short_cached_location_label(hass)
        sample_defs = [
            (presets[0]["name"] if len(presets) > 0 else "Supercharger", _to_float((presets[0] if len(presets) > 0 else {}).get("unit_price"), 9.9), (presets[0] if len(presets) > 0 else {}).get("currency", currency), 21.4),
            (presets[1]["name"] if len(presets) > 1 else "ZES", _to_float((presets[1] if len(presets) > 1 else {}).get("unit_price"), 16.49), (presets[1] if len(presets) > 1 else {}).get("currency", currency), 13.8),
        ]
        records = []
        for idx, (provider, price, row_currency, added_kwh) in enumerate(sample_defs, start=1):
            created_at = now.replace(day=max(1, min(28, idx + 2)), hour=21-idx, minute=15+idx).isoformat(timespec="seconds")
            display_at = now.replace(day=max(1, min(28, idx + 2)), hour=21-idx, minute=15+idx).strftime("%d.%m.%Y %H:%M")
            total_cost = round(added_kwh * price, 2)
            records.append({
                "id": f"sample-{idx}",
                "month_key": now.strftime("%Y-%m"),
                "created_at": created_at,
                "display_at": display_at,
                "provider": provider,
                "added_kwh": round(added_kwh, 3),
                "price_per_kwh": round(price, 4),
                "total_cost": total_cost,
                "currency_label": _normalize_currency(row_currency, default=currency),
                "location_label": location,
                "source": "panel_test",
            })
    total_cost = sum(_to_float(item.get("total_cost"), 0.0) for item in records)
    total_kwh = sum(_to_float(item.get("added_kwh"), 0.0) for item in records)
    return {
        "month_key": datetime.now().strftime("%Y-%m"),
        "report_language": lang,
        "currency_label": currency,
        "summary": {"count": len(records), "total_cost": round(total_cost, 2), "total_kwh": round(total_kwh, 3)},
        "records": records,
    }


async def _panel_telegram_send_message(
    hass: HomeAssistant,
    data: dict[str, Any],
    *,
    target: str,
    message: str,
) -> dict[str, Any] | None:
    """Send a plain Telegram text message for panel-side diagnostics/tests."""
    token = str(data.get(CONF_BUILTIN_TELEGRAM_BOT_TOKEN) or "").strip()
    if token:
        session = async_get_clientsession(hass)
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            async with session.post(url, json={"chat_id": target, "text": message}, timeout=60) as response:
                result = await response.json(content_type=None)
        except ClientError as err:
            raise ValueError(f"Telegram sendMessage request failed: {err}") from err
        except Exception as err:
            raise ValueError(f"Telegram sendMessage request failed: {err}") from err
        if not isinstance(result, dict):
            raise ValueError("Telegram sendMessage returned a non-object response.")
        if not result.get("ok"):
            raise ValueError(str(result.get("description") or result))
        return result
    if hass.services.has_service("telegram_bot", "send_message"):
        await hass.services.async_call(
            "telegram_bot",
            "send_message",
            {"target": target, "parse_mode": "plain_text", "message": message},
            blocking=True,
        )
        return None
    raise ValueError("Neither built-in Telegram sendMessage nor Home Assistant telegram_bot.send_message is available.")


async def _panel_telegram_api_send_photo(
    hass: HomeAssistant,
    data: dict[str, Any],
    *,
    target: str,
    file_path: str,
    caption: str,
) -> dict[str, Any]:
    token = str(data.get(CONF_BUILTIN_TELEGRAM_BOT_TOKEN) or "").strip()
    if not token:
        raise ValueError("Built-in Telegram bot token is empty.")
    path = Path(file_path)
    if not path.exists():
        raise ValueError(f"Photo file does not exist: {file_path}")
    raw = await hass.async_add_executor_job(path.read_bytes)
    form = FormData()
    form.add_field("chat_id", target)
    form.add_field("caption", caption)
    form.add_field("photo", raw, filename=path.name, content_type="image/png")
    session = async_get_clientsession(hass)
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    try:
        async with session.post(url, data=form, timeout=60) as response:
            result = await response.json(content_type=None)
    except ClientError as err:
        raise ValueError(f"Telegram sendPhoto request failed: {err}") from err
    except Exception as err:
        raise ValueError(f"Telegram sendPhoto request failed: {err}") from err
    if not isinstance(result, dict):
        raise ValueError("Telegram sendPhoto returned a non-object response.")
    if not result.get("ok"):
        raise ValueError(str(result.get("description") or result))
    return result


class PomTeslaTripTestView(HomeAssistantView):
    """Generate and send a non-persistent sample trip report from the app panel."""

    url = API_TRIP_TEST_URL
    name = f"api:{DOMAIN}:trip_test"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def post(self, request: web.Request) -> web.Response:
        try:
            body = await request.json()
        except Exception:
            body = {}
        if not isinstance(body, dict):
            body = {}

        data = _entry_config(self.hass)
        lang = _app_language(self.hass)
        target = _normalize_telegram_id_panel(
            body.get("target")
            or data.get(CONF_TELEGRAM_TARGET)
            or data.get(CONF_AI_TELEGRAM_TARGET)
            or data.get(CONF_AI_TELEGRAM_LISTENER_CHAT_ID)
        )
        if not target:
            return web.json_response({"success": False, "error": "telegram_target_empty"}, status=400)

        out_dir = _ensure_www_report_dir(self.hass)
        png_path = str(out_dir / "panel_test_trip_report.png")
        profile = str(body.get("profile") or "city").strip().lower()
        report_data = _build_panel_test_trip_report_data(self.hass, data, profile=profile)

        show_map = _to_bool(data.get(CONF_SHOW_TRIP_MAP), DEFAULT_SHOW_TRIP_MAP) and _to_bool(
            data.get(CONF_TRIP_MAP_ENABLED), DEFAULT_TRIP_MAP_ENABLED
        )
        try:
            if show_map:
                map_path = str(out_dir / "panel_test_trip_route_map.png")
                map_data = _build_panel_test_trip_map_data(report_data, lang=lang)
                rendered_map = await self.hass.async_add_executor_job(
                    render_trip_map_png,
                    map_data,
                    map_path,
                )
                if rendered_map:
                    report_data["embedded_map_path"] = rendered_map

            rendered_path = await self.hass.async_add_executor_job(
                render_trip_report_png,
                report_data,
                png_path,
                lang,
            )
            profile_label = str(report_data.get("test_profile_label") or profile)
            caption = (f"🧪 Tesla AI - Test Trip Report · {profile_label}" if lang == APP_LANGUAGE_EN else f"🧪 Tesla AI - Test Sürüş Raporu · {profile_label}")
            state = _telegram_service_state(self.hass, data)
            sent_via = ""
            if state.get("builtin_enabled") and state.get("builtin_has_token"):
                await _panel_telegram_api_send_photo(
                    self.hass,
                    data,
                    target=target,
                    file_path=rendered_path,
                    caption=caption,
                )
                sent_via = "built_in_telegram"
            elif self.hass.services.has_service("telegram_bot", "send_photo"):
                await self.hass.services.async_call(
                    "telegram_bot",
                    "send_photo",
                    {"target": target, "file": rendered_path, "caption": caption},
                    blocking=True,
                )
                sent_via = "ha_telegram_bot"
            else:
                raise ValueError("Neither built-in Telegram sendPhoto nor Home Assistant telegram_bot.send_photo is available.")

            # alpha250: also send a deterministic AI-story style message so the
            # user can test the post-trip story layout without needing a real drive
            # or writing a Trip Records entry.
            await _panel_telegram_send_message(
                self.hass,
                data,
                target=target,
                message=_build_panel_test_trip_ai_story(report_data, lang=lang),
            )
        except Exception as err:
            _LOGGER.exception("POM Tesla panel test trip report could not be sent")
            return web.json_response({"success": False, "error": str(err)}, status=500)

        return web.json_response({
            "success": True,
            "language": lang,
            "sent_via": sent_via,
            "target": target,
            "file": rendered_path,
            "url": "/local/pom_tesla_report/panel_test_trip_report.png",
            "map_included": bool(report_data.get("embedded_map_path")),
            "ledger_written": False,
            "profile": profile,
            "profile_label": str(report_data.get("test_profile_label") or profile),
            "route_label": str(report_data.get("test_route_label") or ""),
        })



class PomTeslaChargeTestView(HomeAssistantView):
    """Send charge-related test visuals to Telegram from the app panel."""

    url = API_CHARGE_TEST_URL
    name = f"api:{DOMAIN}:charge_test"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def post(self, request: web.Request) -> web.Response:
        try:
            body = await request.json()
        except Exception:
            body = {}
        if not isinstance(body, dict):
            body = {}

        action = str(body.get("action") or "monthly_cost").strip().lower()
        data = _entry_config(self.hass)
        lang = _app_language(self.hass)
        target = _normalize_telegram_id_panel(
            body.get("target")
            or data.get(CONF_TELEGRAM_TARGET)
            or data.get(CONF_AI_TELEGRAM_TARGET)
            or data.get(CONF_AI_TELEGRAM_LISTENER_CHAT_ID)
        )
        if not target:
            return web.json_response({"success": False, "error": "telegram_target_empty"}, status=400)

        try:
            if action == "monthly_cost":
                payload = await asyncio.to_thread(_build_panel_monthly_charge_test_payload, self.hass, data)
                out_dir = _ensure_www_report_dir(self.hass)
                base_path = str(out_dir / "panel_test_monthly_charge_report.png")
                png_paths = await self.hass.async_add_executor_job(
                    render_monthly_charge_cost_report_pngs,
                    payload,
                    base_path,
                    lang,
                )
                if not png_paths:
                    raise ValueError("Monthly charging summary could not be rendered.")
                state = _telegram_service_state(self.hass, data)
                sent_via = ""
                for page_index, png_path in enumerate(png_paths, start=1):
                    caption = "🧪 Tesla AI - Test Charging Cost Summary" if lang == APP_LANGUAGE_EN else "🧪 Tesla AI - Test Şarj Maliyet Özeti"
                    if len(png_paths) > 1:
                        caption = f"{caption} ({page_index}/{len(png_paths)})"
                    if state.get("builtin_enabled") and state.get("builtin_has_token"):
                        await _panel_telegram_api_send_photo(self.hass, data, target=target, file_path=png_path, caption=caption)
                        sent_via = "built_in_telegram"
                    elif self.hass.services.has_service("telegram_bot", "send_photo"):
                        await self.hass.services.async_call("telegram_bot", "send_photo", {"target": target, "file": png_path, "caption": caption}, blocking=True)
                        sent_via = "ha_telegram_bot"
                    else:
                        raise ValueError("Neither built-in Telegram sendPhoto nor Home Assistant telegram_bot.send_photo is available.")
                return web.json_response({"success": True, "action": action, "language": lang, "sent_via": sent_via, "target": target, "file_count": len(png_paths), "ledger_written": False})

            if action == "completion_report":
                out_dir = _ensure_www_report_dir(self.hass)
                png_path = str(out_dir / "panel_test_charge_completed_report.png")
                currency = _report_currency(self.hass)
                presets = _effective_provider_presets(data, default_currency=currency)[:3]
                first = presets[0] if presets else {"name": "Supercharger", "unit_price": 9.9, "currency": currency}
                actual_provider = "Other" if lang == APP_LANGUAGE_EN else "Diğer"
                actual_price = round(_to_float(first.get("unit_price"), 9.9), 2)
                actual_currency = _normalize_currency(first.get("currency"), default=currency)
                added_kwh = 45.1
                report_data = {
                    "test_mode": True,
                    "currency_label": currency,
                    "finished_at": datetime.now().strftime("%d %B %Y · %H:%M"),
                    "meta": datetime.now().strftime("%d %B %Y · %H:%M"),
                    "location_label": _short_cached_location_label(self.hass) or ("Sample location" if lang == APP_LANGUAGE_EN else "Örnek konum"),
                    "added_kwh": added_kwh,
                    "battery_range_km": 342,
                    "battery_range_estimate_km": 278,
                    "duration_minutes": 36,
                    "peak_power_kw": 117,
                    "average_power_kw": 75,
                    "power_samples": [
                        {"minute": 0, "power_kw": 5}, {"minute": 1, "power_kw": 62},
                        {"minute": 4, "power_kw": 68}, {"minute": 8, "power_kw": 88},
                        {"minute": 10, "power_kw": 108}, {"minute": 12, "power_kw": 117},
                        {"minute": 14, "power_kw": 110}, {"minute": 18, "power_kw": 84},
                        {"minute": 22, "power_kw": 75}, {"minute": 28, "power_kw": 57},
                        {"minute": 34, "power_kw": 44}, {"minute": 36, "power_kw": 0},
                    ],
                    "actual_provider": actual_provider,
                    "actual_price_per_kwh": actual_price,
                    "actual_total_cost": round(added_kwh * actual_price, 2),
                    "actual_currency": actual_currency,
                    "provider_presets": presets,
                }
                rendered_path = await self.hass.async_add_executor_job(render_charging_report_png, report_data, png_path, lang)
                caption = "🧪 Tesla AI - Test Charge Completed Report" if lang == APP_LANGUAGE_EN else "🧪 Tesla AI - Test Şarj Tamamlandı Raporu"
                state = _telegram_service_state(self.hass, data)
                sent_via = ""
                if state.get("builtin_enabled") and state.get("builtin_has_token"):
                    await _panel_telegram_api_send_photo(self.hass, data, target=target, file_path=rendered_path, caption=caption)
                    sent_via = "built_in_telegram"
                elif self.hass.services.has_service("telegram_bot", "send_photo"):
                    await self.hass.services.async_call("telegram_bot", "send_photo", {"target": target, "file": rendered_path, "caption": caption}, blocking=True)
                    sent_via = "ha_telegram_bot"
                else:
                    raise ValueError("Neither built-in Telegram sendPhoto nor Home Assistant telegram_bot.send_photo is available.")
                return web.json_response({"success": True, "action": action, "language": lang, "sent_via": sent_via, "target": target, "file": rendered_path, "ledger_written": False})

            raise ValueError(f"Unsupported charge test action: {action}")
        except Exception as err:
            _LOGGER.exception("POM Tesla charge test report could not be sent")
            return web.json_response({"success": False, "error": str(err), "action": action}, status=500)



class PomTeslaTelegramTestView(HomeAssistantView):
    """Telegram diagnostics endpoint for the POM Tesla app panel."""

    url = API_TELEGRAM_TEST_URL
    name = f"api:{DOMAIN}:telegram_test"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request) -> web.Response:
        data = _entry_config(self.hass)
        return web.json_response({
            "success": True,
            "language": _app_language(self.hass),
            "service_state": _telegram_service_state(self.hass, data),
            "logs": list(_telegram_diag_log(self.hass)),
        })

    async def post(self, request: web.Request) -> web.Response:
        try:
            body = await request.json()
        except Exception:
            body = {}
        if not isinstance(body, dict):
            body = {}

        action = str(body.get("action") or "send_test").strip().lower()
        if action == "clear_logs":
            _telegram_diag_log(self.hass).clear()
            return web.json_response({
                "success": True,
                "language": _app_language(self.hass),
                "service_state": _telegram_service_state(self.hass, _entry_config(self.hass)),
                "logs": [],
            })

        data = _telegram_test_config_from_request(self.hass, body.get("telegram"))
        state = _telegram_service_state(self.hass, data)
        target = _normalize_telegram_id_panel(body.get("target") or state.get("group_id"))
        lang = _app_language(self.hass)
        default_message = "POM Telegram test mesajı" if lang != APP_LANGUAGE_EN else "POM Telegram test message"
        message = str(body.get("message") or default_message).strip()

        try:
            if action == "send_test":
                if not target:
                    _add_telegram_diag(self.hass, "error", "Telegram target / group ID is empty.", {"action": action, "service_state": state})
                    return web.json_response({
                        "success": False,
                        "language": lang,
                        "service_state": state,
                        "logs": list(_telegram_diag_log(self.hass)),
                        "error": "Telegram target / group ID is empty.",
                    }, status=400)
                if state["builtin_enabled"] and state["builtin_has_token"]:
                    _add_telegram_diag(self.hass, "info", f"Sending built-in Telegram test message to {target}")
                    result = await _panel_telegram_api_call(
                        self.hass,
                        data,
                        "sendMessage",
                        {"chat_id": target, "text": message},
                    )
                    _add_telegram_diag(self.hass, "success", "Built-in Telegram sendMessage succeeded.", result)
                elif self.hass.services.has_service("telegram_bot", "send_message"):
                    _add_telegram_diag(self.hass, "info", f"Sending HA telegram_bot.send_message test to {target}")
                    await self.hass.services.async_call(
                        "telegram_bot",
                        "send_message",
                        {"target": target, "message": message},
                        blocking=True,
                    )
                    _add_telegram_diag(self.hass, "success", "Home Assistant telegram_bot.send_message call succeeded.")
                else:
                    raise ValueError("Neither built-in Telegram token nor Home Assistant telegram_bot.send_message service is available.")
            elif action == "poll_once":
                if not state["builtin_enabled"] or not state["builtin_has_token"]:
                    raise ValueError("Polling test requires built-in Telegram bot mode and a bot token.")
                _add_telegram_diag(self.hass, "info", "Running built-in Telegram getUpdates poll test.")
                result = await _panel_telegram_api_call(
                    self.hass,
                    data,
                    "getUpdates",
                    {"timeout": 0, "allowed_updates": ["message", "callback_query"]},
                )
                updates = result.get("result") if isinstance(result, dict) else []
                count = len(updates) if isinstance(updates, list) else 0
                _add_telegram_diag(self.hass, "success", f"getUpdates succeeded. Updates returned: {count}.", result)
            else:
                raise ValueError(f"Unsupported telegram test action: {action}")
        except Exception as err:
            err_text = str(err)
            friendly_error = err_text
            status_code = 500
            if "chat not found" in err_text.lower():
                status_code = 400
                friendly_error = (
                    "Telegram chat not found. Bot token bu gruba ait değil, bot gruba ekli değil, "
                    "ya da Telegram group ID yanlış. Botu gruba ekleyip grupta bir mesaj gönder; "
                    "sonra doğru chat_id ile tekrar dene."
                )
                _LOGGER.warning("POM Tesla Telegram test failed: %s", err_text)
            else:
                _LOGGER.exception("POM Tesla Telegram panel diagnostic failed")
            _add_telegram_diag(self.hass, "error", friendly_error, {
                "action": action,
                "service_state": state,
                "raw_error": err_text,
            })
            return web.json_response({
                "success": False,
                "language": lang,
                "service_state": state,
                "logs": list(_telegram_diag_log(self.hass)),
                "error": friendly_error,
                "raw_error": err_text,
            }, status=status_code)

        return web.json_response({
            "success": True,
            "language": lang,
            "service_state": _telegram_service_state(self.hass, data),
            "logs": list(_telegram_diag_log(self.hass)),
        })



class PomTeslaAITestView(HomeAssistantView):
    """AI diagnostics endpoint for the POM Tesla app panel."""

    url = API_AI_TEST_URL
    name = f"api:{DOMAIN}:ai_test"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request) -> web.Response:
        data = _entry_config(self.hass)
        return web.json_response({
            "success": True,
            "language": _app_language(self.hass),
            "service_state": _ai_service_state(self.hass, data),
            "logs": list(_ai_diag_log(self.hass)),
        })

    async def post(self, request: web.Request) -> web.Response:
        try:
            body = await request.json()
        except Exception:
            body = {}
        if not isinstance(body, dict):
            body = {}
        action = str(body.get("action") or "run_test").strip().lower()
        if action == "clear_logs":
            _ai_diag_log(self.hass).clear()
            return web.json_response({
                "success": True,
                "language": _app_language(self.hass),
                "service_state": _ai_service_state(self.hass, _entry_config(self.hass)),
                "logs": [],
            })

        data = _ai_test_config_from_request(self.hass, body.get("ai_settings"))
        state = _ai_service_state(self.hass, data)
        lang = _app_language(self.hass)
        default_prompt = "Kısaca cevap ver: POM Tesla AI bağlantı testi başarılı mı?" if lang != APP_LANGUAGE_EN else "Reply briefly: did the POM Tesla AI connectivity test succeed?"
        prompt = str(body.get("prompt") or default_prompt).strip()
        try:
            if action not in {"run_test", "run_test_send_telegram"}:
                raise ValueError(f"Unsupported AI test action: {action}")
            if not state.get("ai_enabled"):
                raise ValueError("AI is disabled in settings.")
            _add_ai_diag(self.hass, "info", f"Running AI test with model {state.get('model')}", {"prompt": prompt})
            answer = await _panel_openai_test_call(self.hass, data, prompt)
            _add_ai_diag(self.hass, "success", "AI test succeeded.", {"answer": answer, "model": state.get("model")})

            if action == "run_test_send_telegram":
                telegram_data = dict(_entry_config(self.hass))
                telegram_state = _telegram_service_state(self.hass, telegram_data)
                target = _normalize_telegram_id_panel(telegram_state.get("group_id"))
                if not target:
                    raise ValueError("Telegram target / group ID is empty.")
                text = (
                    "🤖 POM Tesla AI test\n\n"
                    f"Prompt: {prompt}\n\n"
                    f"Answer: {answer}"
                )
                if telegram_state["builtin_enabled"] and telegram_state["builtin_has_token"]:
                    _add_ai_diag(self.hass, "info", f"Sending AI test result to Telegram target {target}.")
                    result = await _panel_telegram_api_call(
                        self.hass,
                        telegram_data,
                        "sendMessage",
                        {"chat_id": target, "text": text[:3900]},
                    )
                    _add_ai_diag(self.hass, "success", "AI test result sent to Telegram.", result)
                    _add_telegram_diag(self.hass, "success", "AI test result sent via built-in Telegram bot.", {"target": target})
                elif self.hass.services.has_service("telegram_bot", "send_message"):
                    _add_ai_diag(self.hass, "info", f"Sending AI test result via HA telegram_bot.send_message to {target}.")
                    await self.hass.services.async_call(
                        "telegram_bot",
                        "send_message",
                        {"target": target, "message": text[:3900]},
                        blocking=True,
                    )
                    _add_ai_diag(self.hass, "success", "AI test result sent to Telegram via Home Assistant service.")
                    _add_telegram_diag(self.hass, "success", "AI test result sent via Home Assistant telegram_bot.send_message.", {"target": target})
                else:
                    raise ValueError("Neither built-in Telegram token nor Home Assistant telegram_bot.send_message service is available.")
        except Exception as err:
            _LOGGER.exception("POM Tesla AI panel diagnostic failed")
            _add_ai_diag(self.hass, "error", str(err), {"action": action, "service_state": state})
            return web.json_response({
                "success": False,
                "language": lang,
                "service_state": state,
                "logs": list(_ai_diag_log(self.hass)),
                "error": str(err),
            }, status=500)

        return web.json_response({
            "success": True,
            "language": lang,
            "service_state": _ai_service_state(self.hass, data),
            "logs": list(_ai_diag_log(self.hass)),
        })




def _panel_entity_value(hass: HomeAssistant, entity_id: Any) -> dict[str, Any]:
    """Return a compact state snapshot for a configured entity."""
    eid = str(entity_id or "").strip()
    if not eid:
        return {"entity_id": "", "exists": False, "state": None, "numeric": None, "friendly_name": ""}
    state = hass.states.get(eid)
    if state is None:
        return {"entity_id": eid, "exists": False, "state": None, "numeric": None, "friendly_name": ""}
    raw = state.state
    numeric = None
    try:
        numeric = float(raw)
    except Exception:
        numeric = None
    return {
        "entity_id": eid,
        "exists": True,
        "state": raw,
        "numeric": numeric,
        "friendly_name": state.attributes.get("friendly_name", ""),
        "last_changed": state.last_changed.isoformat() if state.last_changed else "",
        "last_updated": state.last_updated.isoformat() if state.last_updated else "",
    }


def _panel_report_entity_bindings(data: dict[str, Any]) -> dict[str, str]:
    """Return the live-trip/report entities after panel binding priority."""
    bound = _bind_report_options_from_vehicle_map_panel(data)
    return {
        "battery_level": str(bound.get(CONF_BATTERY_LEVEL_ENTITY) or "").strip(),
        "energy_remaining": str(bound.get(CONF_ENERGY_REMAINING_ENTITY) or "").strip(),
        "speed": str(bound.get(CONF_SPEED_ENTITY) or "").strip(),
        "shift_state": str(bound.get(CONF_SHIFT_STATE_ENTITY) or "").strip(),
        "odometer": str(bound.get(CONF_ODOMETER_ENTITY) or "").strip(),
        "elevation": str(bound.get(CONF_ELEVATION_ENTITY) or "").strip(),
        "climate": str(bound.get(CONF_CLIMATE_ENTITY) or "").strip(),
        "charging_state": str(bound.get(CONF_CHARGING_ENTITY) or "").strip(),
        "charge_energy_added": str(bound.get(CONF_CHARGE_ENERGY_ADDED_ENTITY) or "").strip(),
        "location_tracker": str(bound.get(CONF_TRIP_MAP_TRACKER_ENTITY) or "").strip(),
    }


def _live_trip_debug_payload(hass: HomeAssistant) -> dict[str, Any]:
    """Build a diagnostic snapshot for automatic/live trip troubleshooting."""
    data = _entry_config(hass)
    bindings = _panel_report_entity_bindings(data)
    entity_states = {key: _panel_entity_value(hass, entity_id) for key, entity_id in bindings.items()}
    speed_value = entity_states.get("speed", {}).get("numeric")
    threshold = _to_float(data.get(CONF_AUTO_START_SPEED_THRESHOLD), DEFAULT_AUTO_START_SPEED_THRESHOLD)
    min_distance = _to_float(data.get(CONF_LIVE_TRIP_MIN_DISTANCE_KM), DEFAULT_LIVE_TRIP_MIN_DISTANCE_KM)

    live_state: dict[str, Any] = {}
    live_attrs: dict[str, Any] = {}
    try:
        from . import get_live_trip_state, build_live_trip_public_attributes  # imported lazily to avoid panel-registration cycles

        entries = hass.config_entries.async_entries(DOMAIN)
        entry_id = entries[0].entry_id if entries else ""
        if entry_id:
            live_state = dict(get_live_trip_state(hass, entry_id) or {})
            live_attrs = dict(build_live_trip_public_attributes(live_state) or {})
    except Exception as err:
        live_state = {"debug_error": str(err)}
        live_attrs = {}

    missing = [key for key, snap in entity_states.items() if key in {"speed", "shift_state", "odometer"} and not snap.get("exists")]
    non_numeric = [key for key, snap in entity_states.items() if key in {"speed", "odometer", "battery_level", "energy_remaining", "elevation"} and snap.get("exists") and snap.get("numeric") is None]
    warnings: list[str] = []
    if not _to_bool(data.get(CONF_AUTO_TRIP_TRACKING), DEFAULT_AUTO_TRIP_TRACKING):
        warnings.append("auto_trip_tracking is disabled")
    if not _to_bool(data.get(CONF_LIVE_TRIP_ENABLED), DEFAULT_LIVE_TRIP_ENABLED):
        warnings.append("live_trip_enabled is disabled")
    if missing:
        warnings.append("required live-trip entities are missing: " + ", ".join(missing))
    if non_numeric:
        warnings.append("numeric entities returned non-numeric states: " + ", ".join(non_numeric))
    if speed_value is not None and speed_value < threshold:
        warnings.append(f"current speed {speed_value} is below start threshold {threshold}")

    return {
        "success": True,
        "language": _app_language(hass),
        "generated_at": datetime.now().isoformat(),
        "panel_report_binding_priority": True,
        "settings": {
            "auto_trip_tracking": _to_bool(data.get(CONF_AUTO_TRIP_TRACKING), DEFAULT_AUTO_TRIP_TRACKING),
            "live_trip_enabled": _to_bool(data.get(CONF_LIVE_TRIP_ENABLED), DEFAULT_LIVE_TRIP_ENABLED),
            "start_speed_threshold": threshold,
            "live_trip_update_interval_seconds": _to_float(data.get(CONF_LIVE_TRIP_UPDATE_INTERVAL_SECONDS), DEFAULT_LIVE_TRIP_UPDATE_INTERVAL_SECONDS),
            "speed_sampler_interval_seconds": 1,
            "traffic_speed_threshold": _to_float(data.get(CONF_LIVE_TRIP_TRAFFIC_SPEED_THRESHOLD), DEFAULT_LIVE_TRIP_TRAFFIC_SPEED_THRESHOLD),
            "finish_delay_seconds": _to_float(data.get(CONF_LIVE_TRIP_FINISH_DELAY_SECONDS), DEFAULT_LIVE_TRIP_FINISH_DELAY_SECONDS),
            "min_distance_km": min_distance,
            "ignore_short_maneuvers": _to_bool(data.get(CONF_LIVE_TRIP_IGNORE_SHORT_MANEUVERS), DEFAULT_LIVE_TRIP_IGNORE_SHORT_MANEUVERS),
            "candidate_min_distance_km": _to_float(data.get(CONF_LIVE_TRIP_CANDIDATE_MIN_DISTANCE_KM), DEFAULT_LIVE_TRIP_CANDIDATE_MIN_DISTANCE_KM),
            "candidate_min_duration_seconds": _to_float(data.get(CONF_LIVE_TRIP_CANDIDATE_MIN_DURATION_SECONDS), DEFAULT_LIVE_TRIP_CANDIDATE_MIN_DURATION_SECONDS),
            "trip_map_enabled": _to_bool(data.get(CONF_TRIP_MAP_ENABLED), DEFAULT_TRIP_MAP_ENABLED),
        },
        "bindings": bindings,
        "entity_states": entity_states,
        "derived": {
            "speed_numeric": speed_value,
            "speed_above_threshold": bool(speed_value is not None and speed_value >= threshold),
            "required_missing": missing,
            "numeric_state_problems": non_numeric,
            "warnings": warnings,
        },
        "live_trip_state": live_state,
        "live_trip_public_attributes": live_attrs,
        "teslamate_note": "Elevation/Teslamate entity being missing should not block report generation; it should only remove or zero elevation data.",
    }




class PomTeslaLiveTripTestView(HomeAssistantView):
    """Control simulated live trip test actions from the app panel."""

    url = API_LIVE_TRIP_TEST_URL
    name = f"api:{DOMAIN}:live_trip_test"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def post(self, request: web.Request) -> web.Response:
        try:
            body = await request.json()
        except Exception:
            body = {}
        if not isinstance(body, dict):
            body = {}

        action = str(body.get("action") or "").strip().lower()
        if action not in {"start", "finish", "reset"}:
            return web.json_response({"success": False, "error": "unsupported_action"}, status=400)

        data = _entry_config(self.hass)
        target = _normalize_telegram_id_panel(
            body.get("target")
            or data.get(CONF_TELEGRAM_TARGET)
            or data.get(CONF_AI_TELEGRAM_TARGET)
            or data.get(CONF_AI_TELEGRAM_LISTENER_CHAT_ID)
        )
        service_data: dict[str, Any] = {}
        if target:
            service_data["telegram_target"] = target
            service_data["chat_id"] = target

        try:
            if action == "start":
                await self.hass.services.async_call(DOMAIN, "start_live_trip_test", service_data, blocking=True)
                message = "Live Trip test simülasyonu başlatıldı." if _app_language(self.hass) == APP_LANGUAGE_TR else "Live Trip test simulation started."
            elif action == "finish":
                service_data.update({
                    "send_telegram": True,
                    "caption": "🚗 Tesla AI - Live Trip Test",
                })
                await self.hass.services.async_call(DOMAIN, "finish_live_trip_test", service_data, blocking=True)
                message = "Live Trip test bitirildi ve Telegram gönderimi tetiklendi." if _app_language(self.hass) == APP_LANGUAGE_TR else "Live Trip test finished and Telegram sending was triggered."
            else:
                await self.hass.services.async_call(DOMAIN, "reset_live_trip_test", service_data, blocking=True)
                message = "Live Trip test sıfırlandı." if _app_language(self.hass) == APP_LANGUAGE_TR else "Live Trip test reset."

            return web.json_response({
                "success": True,
                "action": action,
                "message": message,
            })
        except Exception as err:
            _LOGGER.exception("Live trip test action failed")
            return web.json_response({"success": False, "error": str(err)}, status=500)



class PomTeslaLiveTripAIIntervalView(HomeAssistantView):
    """Persist Live Trip AI comment interval immediately from the panel."""

    url = API_LIVE_TRIP_AI_INTERVAL_URL
    name = f"api:{DOMAIN}:live_trip_ai_interval"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def post(self, request: web.Request) -> web.Response:
        try:
            body = await request.json()
        except Exception:
            body = {}
        if not isinstance(body, dict):
            body = {}

        entry = _first_config_entry(self.hass)
        if entry is None:
            return web.json_response({"success": False, "error": "config_entry_not_found"}, status=404)

        segment_km = _live_trip_ai_segment_distance_for_panel(
            body.get("segment_km")
            or body.get("live_trip_ai_segment_distance_km")
            or body.get(CONF_LIVE_TRIP_AI_SEGMENT_DISTANCE_KM)
            or DEFAULT_LIVE_TRIP_AI_SEGMENT_DISTANCE_KM
        )
        try:
            merged_options = {**dict(entry.options or {})}
            merged_options[CONF_LIVE_TRIP_AI_SEGMENT_DISTANCE_KM] = segment_km
            self.hass.config_entries.async_update_entry(entry, options=merged_options)
            self.hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {**dict(entry.data or {}), **merged_options}
            try:
                from . import async_sync_live_trip_ai_interval_from_options  # pylint: disable=import-outside-toplevel
                live_data = {**dict(entry.data or {}), **merged_options}
                await async_sync_live_trip_ai_interval_from_options(
                    self.hass,
                    entry.entry_id,
                    live_data,
                )
                # Also sync any already-created Live Trip sensors. This guards
                # against entity-registry suffixes or rare multi-entry installs
                # where the dashboard card is bound to another POM Live Trip entity.
                from . import LIVE_TRIP_SENSOR_STORE  # pylint: disable=import-outside-toplevel
                for _live_entry_id in list(self.hass.data.get(DOMAIN, {}).get(LIVE_TRIP_SENSOR_STORE, {}).keys()):
                    if _live_entry_id != entry.entry_id:
                        await async_sync_live_trip_ai_interval_from_options(self.hass, _live_entry_id, live_data)
            except Exception:
                _LOGGER.exception("Could not sync Live Trip AI interval from dedicated endpoint")
            message = (
                f"AI yorum aralığı {segment_km:g} km olarak kaydedildi."
                if _app_language(self.hass) == APP_LANGUAGE_TR
                else f"AI comment interval saved as {segment_km:g} km."
            )
            return web.json_response({
                "success": True,
                "message": message,
                "segment_km": segment_km,
                "trip_reports": {
                    "live_trip_ai_segment_distance_km": segment_km,
                    "live_trip_ai_segment_distance_options": list(LIVE_TRIP_AI_SEGMENT_DISTANCE_OPTIONS),
                },
            })
        except Exception as err:
            _LOGGER.exception("Could not save Live Trip AI interval")
            return web.json_response({"success": False, "error": str(err)}, status=500)


class PomTeslaLiveTripAITestView(HomeAssistantView):
    """Generate a panel-only Live Trip AI comment without driving."""

    url = API_LIVE_TRIP_AI_TEST_URL
    name = f"api:{DOMAIN}:live_trip_ai_test"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def post(self, request: web.Request) -> web.Response:
        try:
            body = await request.json()
        except Exception:
            body = {}
        if not isinstance(body, dict):
            body = {}

        entry = _first_config_entry(self.hass)
        if entry is None:
            return web.json_response({"success": False, "error": "config_entry_not_found"}, status=404)

        data = dict(_entry_config(self.hass))
        segment_km = _live_trip_ai_segment_distance_for_panel(
            body.get("segment_km")
            or body.get("live_trip_ai_segment_distance_km")
            or data.get(CONF_LIVE_TRIP_AI_SEGMENT_DISTANCE_KM)
        )
        data[CONF_LIVE_TRIP_AI_SEGMENT_DISTANCE_KM] = segment_km
        panel_lang = _app_language(self.hass)
        # Keep the selected interval durable even when the user presses the
        # test button before/without a successful full settings save.
        try:
            merged_options = dict(entry.options or {})
            merged_options[CONF_LIVE_TRIP_AI_SEGMENT_DISTANCE_KM] = segment_km
            self.hass.config_entries.async_update_entry(entry, options=merged_options)
            self.hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {**dict(entry.data or {}), **merged_options}
            data = {**dict(entry.data or {}), **merged_options}
            try:
                from . import async_sync_live_trip_ai_interval_from_options  # pylint: disable=import-outside-toplevel
                await async_sync_live_trip_ai_interval_from_options(self.hass, entry.entry_id, data)
            except Exception:
                _LOGGER.exception("Could not sync interval before Live Trip AI test")
        except Exception:
            _LOGGER.exception("Could not persist Live Trip AI interval from test endpoint")

        try:
            from . import (  # pylint: disable=import-outside-toplevel
                get_live_trip_state,
                notify_live_trip_sensor,
                load_live_trip_ai_segments_payload,
                save_live_trip_ai_segments_payload,
                _build_live_trip_ai_segment,
                _live_trip_ai_snapshot_from_state,
                _live_trip_ai_segment_label,
                _build_live_trip_ai_fallback_comment,
                async_update_reverse_geocode_cache,
                build_live_trip_ai_location_context,
                async_generate_live_trip_ai_comment,
            )

            state = get_live_trip_state(self.hass, entry.entry_id)
            now = datetime.now()
            active_status = str(state.get("status") or "").strip().lower()
            if not state:
                state.update({
                    "active": False,
                    "status": "ai_test",
                    "report_language": panel_lang,
                    "started_at": now.strftime("%d.%m.%Y %H:%M:%S"),
                    "trip_km": 0.0,
                    "duration_seconds": 0.0,
                    "moving_seconds": 0.0,
                    "traffic_seconds": 0.0,
                    "climate_seconds": 0.0,
                    "used_kwh": 0.0,
                    "start_battery": 50.0,
                    "end_battery": 50.0,
                    "max_speed": 0.0,
                    "average_moving_speed": 0.0,
                    "average_overall_speed": 0.0,
                    "min_elevation": 28.0,
                    "max_elevation": 34.0,
                    "last_elevation": 34.0,
                    "trip_status": "Live Trip AI test yorumu hazırlandı." if _app_language(self.hass) == APP_LANGUAGE_TR else "Live Trip AI test comment is ready.",
                })

            existing_segments = state.get("live_ai_segments") if isinstance(state.get("live_ai_segments"), list) else []
            segment_index = int(max([0] + [int(_to_float((item or {}).get("segment_index"), 0.0)) for item in existing_segments])) + 1
            test_baseline = {
                "trip_km": 0.0,
                "duration_seconds": 0.0,
                "moving_seconds": 0.0,
                "traffic_seconds": 0.0,
                "climate_seconds": 0.0,
                "used_kwh": 0.0,
                "start_battery": 51.0,
                "end_battery": 51.0,
                "max_speed": 0.0,
                "average_moving_speed": 0.0,
                "average_overall_speed": 0.0,
                "min_elevation": 28.0,
                "max_elevation": 34.0,
                "last_elevation": 28.0,
                "traffic_model_label": "test",
                "trip_status": "panel_test",
            }
            synthetic_state = dict(state)
            synthetic_state.update({
                "trip_km": segment_km,
                "duration_seconds": max(240.0, segment_km * 420.0),
                "moving_seconds": max(210.0, segment_km * 360.0),
                "traffic_seconds": 60.0 if segment_km <= 1.0 else min(300.0, segment_km * 45.0),
                "climate_seconds": 120.0,
                "used_kwh": round(max(0.12, segment_km * 0.18), 3),
                "start_battery": 51.0,
                "end_battery": max(0.0, 51.0 - max(0.2, segment_km * 0.35)),
                "max_speed": 54.0 if segment_km <= 1.0 else 72.0,
                "average_moving_speed": 32.0 if segment_km <= 1.0 else 46.0,
                "average_overall_speed": 28.0 if segment_km <= 1.0 else 42.0,
                "traffic_model_label": "panel_test",
                "trip_status": "panel_test",
            })
            try:
                await async_update_reverse_geocode_cache(self.hass, data)
            except Exception:
                _LOGGER.debug("Live Trip AI test reverse geocode refresh skipped", exc_info=True)
            segment = _build_live_trip_ai_segment(
                synthetic_state,
                test_baseline,
                segment_index=segment_index,
                size_km=segment_km,
            )
            segment.update(build_live_trip_ai_location_context(self.hass))
            segment["segment_label"] = _live_trip_ai_segment_label(segment_index, segment_km)
            segment["status"] = "generating"
            segment["test_mode"] = True

            state["report_language"] = panel_lang
            state["live_ai_comment_status"] = "generating"
            state["live_ai_comment_error"] = ""
            state["live_ai_segment_size_km"] = segment_km
            state["live_ai_latest_segment"] = segment
            state["live_comment"] = (f"Preparing a test comment for {segment.get('segment_label')}..." if panel_lang == APP_LANGUAGE_EN else f"{segment.get('segment_label')}: test yorumu hazırlanıyor...")
            notify_live_trip_sensor(self.hass, entry.entry_id)

            # Panel test must be deterministic and immediate. It validates the
            # Live Trip AI card, interval persistence, sensor update and popup
            # rendering without waiting on the OpenAI network path. Real driving
            # comments still use async_generate_live_trip_ai_comment().
            comment = _build_live_trip_ai_fallback_comment(segment, data, lang=panel_lang)
            segment["comment"] = str(comment or "").strip()
            segment["source"] = "panel_test"
            segment["status"] = "ready"
            segment["generated_at"] = now.strftime("%d.%m.%Y %H:%M:%S")
            segment["test_mode"] = True
            segments = [item for item in existing_segments if int(_to_float((item or {}).get("segment_index"), 0.0)) != int(segment_index)]
            segments.append(segment)
            segments.sort(key=lambda item: int(_to_float((item or {}).get("segment_index"), 0.0)))
            state["live_ai_segments"] = segments[-8:]
            state["live_ai_latest_segment"] = segment
            if active_status in {"active", "finishing", "finished"}:
                # Panel-only test comments are visual smoke tests. They must not
                # consume a real Live Trip segment, otherwise a 5 km test pushes
                # the real next target to 10 km and the card looks stale.
                real_completed_index = int(_to_float(state.get("live_ai_segment_last_completed_index"), 0.0))
                state["live_ai_segment_last_completed_index"] = max(0, real_completed_index)
                state["live_ai_segment_next_target_km"] = round(max(segment_km, (real_completed_index + 1) * segment_km), 2)
            else:
                state["live_ai_segment_last_completed_index"] = 0
                state["live_ai_segment_next_target_km"] = segment_km
                state["live_ai_segment_baseline"] = _live_trip_ai_snapshot_from_state(state)
            state["live_ai_comment_status"] = "ready"
            state["live_ai_comment_source"] = "panel_test"
            state["live_ai_comment_error"] = ""
            state["live_ai_last_generated_at"] = segment["generated_at"]
            state["live_ai_last_prompt_at"] = segment["generated_at"]
            state["live_ai_last_prompt_ts"] = now.timestamp()
            state["live_comment"] = segment["comment"]
            state["live_ai_scheduler_debug"] = {
                "current_km": round(_to_float(state.get("trip_km"), 0.0), 3),
                "next_target_km": round(_to_float(state.get("live_ai_segment_next_target_km"), segment_km), 3),
                "segment_index": int(segment_index),
                "status": str(state.get("status") or ""),
                "comment_status": "ready",
                "should_schedule": False,
                "reason": "panel_test_comment_ready",
                "updated_at": now.strftime("%d.%m.%Y %H:%M:%S"),
            }
            payload = load_live_trip_ai_segments_payload(self.hass, entry.entry_id)
            payload["entry_id"] = str(entry.entry_id or "")
            payload["started_at"] = str(state.get("started_at") or payload.get("started_at") or "")
            payload["updated_at"] = segment["generated_at"]
            payload["segments"] = state["live_ai_segments"]
            save_live_trip_ai_segments_payload(self.hass, entry.entry_id, payload)
            notify_live_trip_sensor(self.hass, entry.entry_id)
            message = "Live Trip AI test yorumu hazırlandı." if panel_lang == APP_LANGUAGE_TR else "Live Trip AI test comment is ready."
            return web.json_response({
                "success": True,
                "message": message,
                "segment_km": segment_km,
                "segment": segment,
            })
        except Exception as err:
            _LOGGER.exception("Live Trip AI comment test failed")
            return web.json_response({"success": False, "error": str(err)}, status=500)



def _system_logs_payload_blocking(hass: HomeAssistant, max_lines: int = 500) -> dict[str, Any]:
    """Return a bounded tail of Home Assistant's main log file.

    This endpoint is best-effort. Missing HA logs are reported as a non-fatal
    warning so the support report can still be downloaded with POM events and
    health/status data.
    """
    candidates: list[Path] = []
    try:
        candidates.append(Path(hass.config.path("home-assistant.log")))
    except Exception:
        pass
    for raw in (
        "/config/home-assistant.log",
        "/homeassistant/home-assistant.log",
        "/config/home-assistant.log.1",
        "/homeassistant/home-assistant.log.1",
    ):
        candidates.append(Path(raw))

    seen: set[str] = set()
    paths: list[Path] = []
    for candidate in candidates:
        key = str(candidate)
        if key not in seen:
            seen.add(key)
            paths.append(candidate)

    checked = [str(path) for path in paths]
    path = next((candidate for candidate in paths if candidate.exists() and candidate.is_file()), None)
    if path is None:
        return {
            "success": True,
            "log_available": False,
            "warning": "Home Assistant log file was not found. Support report will include POM events only.",
            "paths_checked": checked,
            "path": "",
            "file_size": 0,
            "lines_returned": 0,
            "max_lines": max_lines,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "lines": [],
            "text": "",
        }
    try:
        size = path.stat().st_size
        with path.open("rb") as handle:
            handle.seek(max(0, size - 700_000))
            raw = handle.read()
        text = raw.decode("utf-8", errors="replace")
        lines = text.splitlines()[-max_lines:]
        ts_re = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})")
        timestamps = []
        for line in lines:
            match = ts_re.match(line or "")
            if match:
                timestamps.append(match.group(1))
        first_ts = timestamps[0] if timestamps else ""
        last_ts = timestamps[-1] if timestamps else ""
        today = datetime.now().strftime("%Y-%m-%d")
        is_fallback = str(path).endswith(".log.1")
        is_stale = bool(last_ts and not last_ts.startswith(today))
        lowered_domain = DOMAIN.lower()
        pom_related_count = sum(
            1 for line in lines
            if lowered_domain in str(line).lower() or "pom tesla" in str(line).lower()
        )
        return {
            "success": True,
            "log_available": True,
            "path": str(path),
            "paths_checked": checked,
            "file_size": size,
            "lines_returned": len(lines),
            "max_lines": max_lines,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "is_fallback": is_fallback,
            "is_stale": is_stale,
            "first_timestamp": first_ts,
            "last_timestamp": last_ts,
            "pom_related_count": pom_related_count,
            "lines": lines,
            "text": "\n".join(lines),
        }
    except Exception as err:
        return {
            "success": True,
            "log_available": False,
            "warning": f"Home Assistant log could not be read: {err}",
            "paths_checked": checked,
            "path": str(path),
            "file_size": 0,
            "lines_returned": 0,
            "max_lines": max_lines,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "lines": [],
            "text": "",
        }



def _read_json_file_safely(path: Path) -> Any:
    """Read a JSON file for backup export without breaking the whole export."""
    try:
        if not path.exists() or not path.is_file():
            return None
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as err:
        return {"_read_error": str(err), "_path": str(path)}


def _collect_live_trip_ai_segment_files(hass: HomeAssistant) -> dict[str, Any]:
    """Collect dedicated Live Trip AI segment JSON files from the HA config root."""
    root = Path(hass.config.path())
    files: dict[str, Any] = {}
    try:
        for path in sorted(root.glob("pom_tesla_live_trip_ai_segments_*.json")):
            files[path.name] = _read_json_file_safely(path)
    except Exception as err:
        files["_collection_error"] = str(err)
    return files


def _collect_dashboard_background_files(hass: HomeAssistant) -> list[dict[str, Any]]:
    """Return metadata and bytes for user-uploaded dashboard background files."""
    out_dir = _ensure_www_dashboard_background_dir(hass)
    collected: list[dict[str, Any]] = []
    try:
        for path in sorted(out_dir.glob("*")):
            if not path.is_file():
                continue
            try:
                data = path.read_bytes()
                collected.append({
                    "name": path.name,
                    "path": str(path),
                    "size": len(data),
                    "data": data,
                })
            except Exception as err:
                collected.append({"name": path.name, "path": str(path), "size": 0, "error": str(err), "data": b""})
    except Exception as err:
        collected.append({"name": "_collection_error", "path": str(out_dir), "size": 0, "error": str(err), "data": b""})
    return collected


def _build_full_backup_payload(hass: HomeAssistant) -> dict[str, Any]:
    """Build a complete user-data backup payload for export."""
    settings_payload = _backup_safe_settings_payload(_settings_payload(hass))
    charge_ledger = _load_charge_ledger(hass)
    trip_ledger = _load_trip_ledger(hass)
    trip_records = [item for item in list(trip_ledger.get("records") or []) if isinstance(item, dict)]
    charge_records = [item for item in list(charge_ledger.get("records") or []) if isinstance(item, dict)]
    manual_records = [item for item in trip_records if _is_manual_tracking_trip_record(item)]
    try:
        live_trip_debug = _live_trip_debug_payload(hass)
    except Exception as err:
        live_trip_debug = {"success": False, "error": str(err)}
    try:
        dashboard_resources = {"resources_status": _dashboard_resources_status_payload(hass)}
    except Exception as err:
        dashboard_resources = {"success": False, "error": str(err)}

    return {
        "metadata": {
            "schema": "pom_tesla_full_backup_v1",
            "generated_at": datetime.now().isoformat(),
            "integration_version": DASHBOARD_PANEL_VERSION,
            "language": _app_language(hass),
            "currency": _report_currency(hass),
            "counts": {
                "trip_records": len(trip_records),
                "charge_records": len(charge_records),
                "manual_tracking_records": len(manual_records),
            },
            "restore_note": "This alpha348 export is a safe backup/export package. Restore/import will be added separately to avoid accidental overwrite.",
        },
        "settings": settings_payload,
        "trip_records": {"records": trip_records, "summary": _trip_summary([item for item in trip_records if not _is_manual_tracking_trip_record(item)])},
        "charge_records": {"records": charge_records, "summary": _charge_summary(charge_records), "last_monthly_report_key": str(charge_ledger.get("last_monthly_report_key") or "")},
        "manual_tracking": {"records": manual_records, "count": len(manual_records)},
        "live_trip": live_trip_debug,
        "live_trip_ai_segments": _collect_live_trip_ai_segment_files(hass),
        "dashboard_resources": dashboard_resources,
    }


def _write_backup_zip_to_bytes(hass: HomeAssistant, payload: dict[str, Any]) -> bytes:
    """Serialize the full backup payload as a ZIP archive."""
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("metadata.json", json.dumps(payload.get("metadata") or {}, ensure_ascii=False, indent=2))
        zf.writestr("settings.json", json.dumps(payload.get("settings") or {}, ensure_ascii=False, indent=2))
        zf.writestr("trip_records.json", json.dumps(payload.get("trip_records") or {}, ensure_ascii=False, indent=2))
        zf.writestr("charge_records.json", json.dumps(payload.get("charge_records") or {}, ensure_ascii=False, indent=2))
        zf.writestr("manual_tracking.json", json.dumps(payload.get("manual_tracking") or {}, ensure_ascii=False, indent=2))
        zf.writestr("live_trip_debug.json", json.dumps(payload.get("live_trip") or {}, ensure_ascii=False, indent=2))
        zf.writestr("live_trip_ai_segments.json", json.dumps(payload.get("live_trip_ai_segments") or {}, ensure_ascii=False, indent=2))
        zf.writestr("dashboard_resources.json", json.dumps(payload.get("dashboard_resources") or {}, ensure_ascii=False, indent=2))

        # Generated Lovelace YAML files are not required for restore, but they are helpful
        # when diagnosing a broken HA/dashboard after a backup is created.
        for filename in ("pom_tesla_dashboard.yaml", "pom_tesla_drive_dashboard.yaml"):
            path = Path(hass.config.path(filename))
            if path.exists() and path.is_file():
                try:
                    yaml_text = path.read_text(encoding="utf-8")
                    zf.writestr(f"dashboard_yaml/{filename}", _redact_youtube_signed_tokens_from_text(yaml_text))
                except Exception as err:
                    zf.writestr(f"dashboard_yaml/{filename}.error.txt", str(err))

        bg_manifest: list[dict[str, Any]] = []
        for item in _collect_dashboard_background_files(hass):
            bg_manifest.append({k: v for k, v in item.items() if k != "data"})
            data = item.get("data") or b""
            name = str(item.get("name") or "").strip()
            if name and data:
                zf.writestr(f"dashboard_backgrounds/{name}", data)
        zf.writestr("dashboard_backgrounds/manifest.json", json.dumps(bg_manifest, ensure_ascii=False, indent=2))
    return buffer.getvalue()


class PomTeslaBackupExportView(HomeAssistantView):
    """Download POM Tesla settings/records/media as a full backup export."""

    url = API_BACKUP_EXPORT_URL
    name = f"api:{DOMAIN}:backup_export"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request) -> web.Response:
        admin_response = _admin_required_response(request)
        if admin_response is not None:
            return admin_response
        fmt = str(request.query.get("format") or "zip").strip().lower()
        try:
            payload = await asyncio.to_thread(_build_full_backup_payload, self.hass)
            stamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
            if fmt == "json":
                filename = f"pom_tesla_full_backup_{stamp}.json"
                return web.Response(
                    body=json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"),
                    content_type="application/json",
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'},
                )
            filename = f"pom_tesla_full_backup_{stamp}.zip"
            zip_bytes = await asyncio.to_thread(_write_backup_zip_to_bytes, self.hass, payload)
            return web.Response(
                body=zip_bytes,
                content_type="application/zip",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )
        except Exception as err:
            _LOGGER.exception("POM Tesla full backup export failed")
            return web.json_response({"success": False, "error": str(err)}, status=500)


class PomTeslaSystemLogsView(HomeAssistantView):
    """Expose a bounded tail of the Home Assistant log file to the panel."""

    url = API_SYSTEM_LOGS_URL
    name = f"api:{DOMAIN}:system_logs"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request) -> web.Response:
        admin_response = _admin_required_response(request)
        if admin_response is not None:
            return admin_response
        try:
            payload = await self.hass.async_add_executor_job(_system_logs_payload_blocking, self.hass, 500)
            return web.json_response(payload, status=200)
        except Exception as err:
            _LOGGER.exception("Could not read system logs")
            return web.json_response({"success": False, "error": str(err)}, status=500)

    async def post(self, request: web.Request) -> web.Response:
        admin_response = _admin_required_response(request)
        if admin_response is not None:
            return admin_response
        return await self.get(request)


class PomTeslaLiveTripDebugView(HomeAssistantView):
    """Expose live trip diagnostics to the app panel."""

    url = API_LIVE_TRIP_DEBUG_URL
    name = f"api:{DOMAIN}:live_trip_debug"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request) -> web.Response:
        admin_response = _admin_required_response(request)
        if admin_response is not None:
            return admin_response
        try:
            return web.json_response(_live_trip_debug_payload(self.hass))
        except Exception as err:
            _LOGGER.exception("Could not build live trip debug payload")
            return web.json_response({"success": False, "error": str(err)}, status=500)

    async def post(self, request: web.Request) -> web.Response:
        admin_response = _admin_required_response(request)
        if admin_response is not None:
            return admin_response
        return await self.get(request)




class PomTeslaDashboardResourcesView(HomeAssistantView):
    """Repair/check dashboard Lovelace resources and custom-card dependencies."""

    url = API_DASHBOARD_RESOURCES_URL
    name = f"api:{DOMAIN}:dashboard_resources"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request) -> web.Response:
        return web.json_response({
            "success": True,
            "language": _app_language(self.hass),
            "resources_status": await _async_dashboard_resources_status_payload(self.hass),
        })

    async def post(self, request: web.Request) -> web.Response:
        admin_response = _admin_required_response(request)
        if admin_response is not None:
            return admin_response
        try:
            body = await request.json()
        except Exception:
            body = {}
        if not isinstance(body, dict):
            body = {}
        action = str(body.get("action") or "status").strip().lower()
        try:
            if action == "install_resources":
                if not self.hass.services.has_service(DOMAIN, "install_dashboard_resources"):
                    raise ValueError("install_dashboard_resources service is not available yet.")
                await self.hass.services.async_call(DOMAIN, "install_dashboard_resources", {}, blocking=True)
            elif action in {"status", "show_missing"}:
                pass
            else:
                raise ValueError(f"Unsupported dashboard resources action: {action}")
            return web.json_response({
                "success": True,
                "language": _app_language(self.hass),
                "resources_status": await _async_dashboard_resources_status_payload(self.hass),
            })
        except Exception as err:
            _LOGGER.exception("Dashboard resource action failed")
            return web.json_response({
                "success": False,
                "error": str(err),
                "resources_status": _dashboard_resources_status_payload(self.hass),
            }, status=500)


class PomTeslaDashboardMediaView(HomeAssistantView):
    """Upload/reset dashboard background images for the app panel."""

    url = API_DASHBOARD_MEDIA_URL
    name = f"api:{DOMAIN}:dashboard_media"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def post(self, request: web.Request) -> web.Response:
        admin_response = _admin_required_response(request)
        if admin_response is not None:
            return admin_response
        entry = _first_config_entry(self.hass)
        if entry is None:
            return web.json_response({"success": False, "error": "config_entry_not_found"}, status=404)

        try:
            slots = _dashboard_background_slot_map()
            if str(request.content_type or "").lower().startswith("application/json"):
                body = await request.json()
                if not isinstance(body, dict):
                    body = {}
                action = str(body.get("action") or "").strip().lower()
                slot = str(body.get("slot") or "").strip().lower()
                if slot not in slots:
                    raise ValueError("Unknown dashboard background slot.")
                option_key, default_url = slots[slot]
                merged_options = dict(entry.options or {})

                if action == "reset":
                    merged_options[option_key] = default_url
                    self.hass.config_entries.async_update_entry(entry, options=merged_options)
                    live_options = {**dict(entry.data or {}), **merged_options}
                    self.hass.data.setdefault(DOMAIN, {})[entry.entry_id] = live_options
                    await _run_dashboard_rebuild_from_panel(
                        self.hass,
                        live_options,
                        reason=f"dashboard_media_reset:{slot}",
                    )
                    payload = _settings_payload(self.hass)
                    payload["dashboard_rebuild_completed"] = True
                    return web.json_response(payload)

                if action != "upload":
                    raise ValueError("Unsupported dashboard media action.")

                file_name = str(body.get("filename") or f"{slot}.png").strip()
                ext = Path(file_name).suffix.lower()
                if ext not in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
                    raise ValueError("Only png, jpg, jpeg, webp, and gif files are supported.")

                data_url = str(body.get("data_url") or "").strip()
                if "," not in data_url:
                    raise ValueError("Uploaded image payload is missing.")
                header, encoded = data_url.split(",", 1)
                if not header.lower().startswith("data:image/"):
                    raise ValueError("Only image uploads are supported.")
                try:
                    file_bytes = base64.b64decode(encoded, validate=True)
                except Exception as err:
                    raise ValueError("Uploaded image payload is invalid.") from err
                if not file_bytes:
                    raise ValueError("Uploaded file is empty.")
                if len(file_bytes) > DASHBOARD_BACKGROUND_UPLOAD_MAX_BYTES:
                    raise ValueError("Uploaded file is too large. Limit is 25 MB.")
                try:
                    Image.open(BytesIO(file_bytes)).verify()
                except Exception as err:
                    raise ValueError("Uploaded file is not a valid image.") from err

                out_dir = _ensure_www_dashboard_background_dir(self.hass)
                for old_file in out_dir.glob(f"{slot}.*"):
                    try:
                        old_file.unlink()
                    except Exception:
                        pass

                target = out_dir / f"{slot}{ext}"
                target.write_bytes(file_bytes)
                public_url = f"/local/pom_tesla_report/dashboard/backgrounds/{slot}{ext}?v={int(datetime.utcnow().timestamp())}"
                merged_options[option_key] = public_url
                self.hass.config_entries.async_update_entry(entry, options=merged_options)
                live_options = {**dict(entry.data or {}), **merged_options}
                self.hass.data.setdefault(DOMAIN, {})[entry.entry_id] = live_options
                await _run_dashboard_rebuild_from_panel(
                    self.hass,
                    live_options,
                    reason=f"dashboard_media_upload_json:{slot}",
                )
                payload = _settings_payload(self.hass)
                payload["dashboard_rebuild_completed"] = True
                return web.json_response(payload)

            if not str(request.content_type or "").lower().startswith("multipart/"):
                raise ValueError("Expected multipart upload.")

            reader = await request.multipart()
            slot = ""
            file_name = ""
            file_bytes = b""
            async for part in reader:
                if part.name == "slot":
                    slot = str(await part.text()).strip().lower()
                elif part.name == "file":
                    file_name = str(getattr(part, "filename", "") or "")
                    file_bytes = await part.read(decode=False)

            if slot not in slots:
                raise ValueError("Unknown dashboard background slot.")
            if not file_name:
                raise ValueError("No image file was selected.")

            ext = Path(file_name).suffix.lower()
            if ext not in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
                raise ValueError("Only png, jpg, jpeg, webp, and gif files are supported.")
            if not file_bytes:
                raise ValueError("Uploaded file is empty.")
            if len(file_bytes) > DASHBOARD_BACKGROUND_UPLOAD_MAX_BYTES:
                raise ValueError("Uploaded file is too large. Limit is 25 MB.")
            try:
                Image.open(BytesIO(file_bytes)).verify()
            except Exception as err:
                raise ValueError("Uploaded file is not a valid image.") from err

            out_dir = _ensure_www_dashboard_background_dir(self.hass)
            for old_file in out_dir.glob(f"{slot}.*"):
                try:
                    old_file.unlink()
                except Exception:
                    pass

            target = out_dir / f"{slot}{ext}"
            await asyncio.to_thread(target.write_bytes, file_bytes)
            public_url = f"/local/pom_tesla_report/dashboard/backgrounds/{slot}{ext}?v={int(datetime.utcnow().timestamp())}"
            option_key, _default_url = slots[slot]
            merged_options = dict(entry.options or {})
            merged_options[option_key] = public_url
            self.hass.config_entries.async_update_entry(entry, options=merged_options)
            live_options = {**dict(entry.data or {}), **merged_options}
            self.hass.data.setdefault(DOMAIN, {})[entry.entry_id] = live_options
            await _run_dashboard_rebuild_from_panel(
                self.hass,
                live_options,
                reason=f"dashboard_media_upload_multipart:{slot}",
            )
            payload = _settings_payload(self.hass)
            payload["dashboard_rebuild_completed"] = True
            return web.json_response(payload)
        except Exception as err:
            _LOGGER.exception("Could not update dashboard background media from panel")
            return web.json_response({"success": False, "error": str(err)}, status=400)


YOUTUBE_JSMPEG_QUALITY_MAP = {
    "360": ("640:-2", "900k", "1200k", "600k"),
    "480": ("854:-2", "1300k", "1700k", "800k"),
    "720": ("1280:-2", "2200k", "2800k", "1200k"),
    # Better visual than 720p, much lighter than full 1080p for VM/Tesla browser.
    "1080_lite": ("1600:-2", "3000k", "4200k", "1800k"),
    # Full 1080p; heavier CPU and can stutter on VM/N100/Tesla browser.
    "1080": ("1920:-2", "4500k", "6000k", "2500k"),
    # Sharper 1080p profile; much heavier CPU/network, intended for capable hosts.
    "1080_high": ("1920:-2", "8500k", "12000k", "6000k"),
}

YOUTUBE_JSMPEG_FORMATS = {
    "360": "bestvideo[height<=360][vcodec^=avc1]/best[height<=360][ext=mp4]/best[height<=360]/best",
    "480": "bestvideo[height<=480][vcodec^=avc1]/best[height<=480][ext=mp4]/best[height<=480]/best",
    "720": "bestvideo[height<=720][vcodec^=avc1]/best[height<=720][ext=mp4]/best[height<=720]/best",
    "1080_lite": "bestvideo[height<=1080][vcodec^=avc1]/bestvideo[height<=1080]/best[height<=1080][ext=mp4]/best[height<=1080]/best",
    "1080": "bestvideo[height<=1080][vcodec^=avc1]/bestvideo[height<=1080]/best[height<=1080][ext=mp4]/best[height<=1080]/best",
    "1080_high": "bestvideo[height<=1080][vcodec^=avc1]/bestvideo[height<=1080]/best[height<=1080][ext=mp4]/best[height<=1080]/best",
}

YOUTUBE_JSMPEG_ALLOWED_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
    "www.youtu.be",
    "youtube-nocookie.com",
    "www.youtube-nocookie.com",
}
YOUTUBE_JSMPEG_ALLOWED_HOST_SUFFIXES = (
    ".youtube.com",
    ".youtube-nocookie.com",
)
YOUTUBE_JSMPEG_DIRECT_MEDIA_ALLOWED_HOSTS = {
    "googlevideo.com",
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtube-nocookie.com",
    "www.youtube-nocookie.com",
    "ytimg.com",
    "i.ytimg.com",
}
YOUTUBE_JSMPEG_DIRECT_MEDIA_ALLOWED_HOST_SUFFIXES = (
    ".googlevideo.com",
    ".youtube.com",
    ".youtube-nocookie.com",
    ".ytimg.com",
)
YOUTUBE_JSMPEG_MAX_FFMPEG_PROCESSES = 2
YOUTUBE_JSMPEG_FFMPEG_PROTOCOL_WHITELIST = "file,pipe,fd,http,https,tcp,tls,crypto,httpproxy,data"


def _youtube_jsmpeg_host_allowed(host: str) -> bool:
    host = str(host or "").strip().lower().rstrip(".")
    return bool(host and (host in YOUTUBE_JSMPEG_ALLOWED_HOSTS or any(host.endswith(suffix) for suffix in YOUTUBE_JSMPEG_ALLOWED_HOST_SUFFIXES)))


def _youtube_jsmpeg_validate_youtube_url(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError("Missing YouTube URL.")
    parsed = urlparse(text)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only http/https YouTube URLs are allowed.")
    if not _youtube_jsmpeg_host_allowed(parsed.hostname or ""):
        raise ValueError("Only YouTube URLs are allowed for the driving background.")
    return text


def _youtube_jsmpeg_direct_media_host_allowed(host: str) -> bool:
    host = str(host or "").strip().lower().rstrip(".")
    return bool(
        host
        and (
            host in YOUTUBE_JSMPEG_DIRECT_MEDIA_ALLOWED_HOSTS
            or any(host.endswith(suffix) for suffix in YOUTUBE_JSMPEG_DIRECT_MEDIA_ALLOWED_HOST_SUFFIXES)
        )
    )


def _youtube_jsmpeg_validate_direct_media_url(value: Any) -> str:
    text = str(value or "").strip()
    parsed = urlparse(text)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("yt-dlp returned a non-http media URL, which is blocked.")
    if not _youtube_jsmpeg_direct_media_host_allowed(parsed.hostname or ""):
        raise ValueError("yt-dlp returned a non-YouTube/Google media host, which is blocked.")
    return text


def _youtube_jsmpeg_active_producer_count(hass: HomeAssistant) -> int:
    producers = hass.data.setdefault(DOMAIN, {}).setdefault("youtube_jsmpeg_producers", {})
    for key, producer in list(producers.items()):
        try:
            if getattr(producer, "_stopped", True):
                producers.pop(key, None)
        except Exception:
            producers.pop(key, None)
    return len(producers)


def _youtube_jsmpeg_active_process_count(hass: HomeAssistant) -> int:
    data = hass.data.setdefault(DOMAIN, {})
    legacy_count = int(data.get("youtube_jsmpeg_legacy_process_count") or 0)
    return _youtube_jsmpeg_active_producer_count(hass) + max(0, legacy_count)


def _youtube_jsmpeg_acquire_legacy_process_slot(hass: HomeAssistant) -> bool:
    data = hass.data.setdefault(DOMAIN, {})
    if _youtube_jsmpeg_active_process_count(hass) >= YOUTUBE_JSMPEG_MAX_FFMPEG_PROCESSES:
        return False
    data["youtube_jsmpeg_legacy_process_count"] = max(0, int(data.get("youtube_jsmpeg_legacy_process_count") or 0)) + 1
    return True


def _youtube_jsmpeg_release_legacy_process_slot(hass: HomeAssistant) -> None:
    data = hass.data.setdefault(DOMAIN, {})
    data["youtube_jsmpeg_legacy_process_count"] = max(0, int(data.get("youtube_jsmpeg_legacy_process_count") or 0) - 1)



def _youtube_jsmpeg_quality(value: Any) -> str:
    quality = str(value or "480").strip()
    return quality if quality in YOUTUBE_JSMPEG_QUALITY_MAP else "480"


def _youtube_jsmpeg_ffmpeg_cmd(input_url: str, quality: str, headers: dict[str, str] | None = None, start_offset: int = 0) -> list[str]:
    scale, bitrate, maxrate, bufsize = YOUTUBE_JSMPEG_QUALITY_MAP.get(quality, YOUTUBE_JSMPEG_QUALITY_MAP["480"])
    if quality == "1080_high":
        fps = "30"
    else:
        fps = "24" if quality in ("1080", "1080_lite") else "25"
    headers = headers or {}
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "warning",
        "-protocol_whitelist", YOUTUBE_JSMPEG_FFMPEG_PROTOCOL_WHITELIST,
        "-threads", "0",
        "-reconnect", "1", "-reconnect_streamed", "1", "-reconnect_at_eof", "1", "-reconnect_delay_max", "5",
    ]
    user_agent = headers.get("User-Agent") or headers.get("user-agent")
    if user_agent:
        cmd.extend(["-user_agent", str(user_agent)])

    header_lines = []
    for key in ("Accept", "Accept-Language", "Origin", "Referer", "Cookie"):
        value = headers.get(key) or headers.get(key.lower())
        if value:
            header_lines.append(f"{key}: {value}")
    if header_lines:
        cmd.extend(["-headers", "\r\n".join(header_lines) + "\r\n"])

    try:
        start_offset = int(start_offset or 0)
    except Exception:
        start_offset = 0

    # Important:
    # With `-re`, output-side seek (`-i input -ss 59`) waits ~59 seconds before
    # producing frames. For dashboard start seconds we need fast input-side seek.
    if start_offset > 2:
        cmd.extend(["-ss", str(start_offset)])

    cmd.extend([
        "-re",
        "-i", input_url,
        "-an",
        "-vf", f"scale={scale}",
        "-r", fps,
        "-codec:v", "mpeg1video",
        "-b:v", bitrate,
        "-maxrate", maxrate,
        "-bufsize", bufsize,
        "-bf", "0",
        "-f", "mpegts",
        "-muxdelay", "0",
        "-muxpreload", "0",
        "-flush_packets", "1",
        "-",
    ])
    return cmd

def _youtube_jsmpeg_parse_time(value: Any) -> int:
    """Parse YouTube t/start style values into seconds."""
    raw = str(value or "").strip().lower()
    if not raw:
        return 0
    if raw.isdigit():
        return int(raw)
    total = 0
    match_h = re.search(r"(\d+)\s*h", raw)
    match_m = re.search(r"(\d+)\s*m", raw)
    match_s = re.search(r"(\d+)\s*s", raw)
    if match_h:
        total += int(match_h.group(1)) * 3600
    if match_m:
        total += int(match_m.group(1)) * 60
    if match_s:
        total += int(match_s.group(1))
    return total


def _youtube_jsmpeg_start_from_url(youtube_url: str) -> int:
    """Extract start offset from YouTube URL query params like t=102 or start=102."""
    try:
        parsed = urlparse(str(youtube_url or ""))
        params = parse_qs(parsed.query)
        for key in ("start", "t"):
            if params.get(key):
                return _youtube_jsmpeg_parse_time(params[key][0])
    except Exception:
        return 0
    return 0


def _youtube_jsmpeg_session_offset(
    hass: HomeAssistant,
    session: str,
    youtube_url: str,
    quality: str,
    duration: int = 0,
    loop: bool = True,
    *,
    ttl_seconds: int = 120,
) -> int:
    """Return a safe resume offset for short reconnects.

    Prevents 10-45 second reconnects from restarting at 0, but also avoids
    seeking beyond short video duration.
    """
    session = re.sub(r"[^a-zA-Z0-9_.:-]", "_", str(session or "").strip())[:96]
    if not session:
        return 0

    try:
        duration = int(duration or 0)
    except Exception:
        duration = 0

    now = time.monotonic()
    store = hass.data.setdefault(DOMAIN, {}).setdefault("youtube_jsmpeg_sessions", {})
    key = session
    entry = store.get(key)

    # cleanup
    for stale_key, stale_value in list(store.items()):
        try:
            if now - float(stale_value.get("last_seen", 0)) > max(ttl_seconds * 4, 300):
                store.pop(stale_key, None)
        except Exception:
            store.pop(stale_key, None)

    if (
        not isinstance(entry, dict)
        or entry.get("url") != youtube_url
        or entry.get("quality") != quality
        or now - float(entry.get("last_seen", 0)) > ttl_seconds
    ):
        store[key] = {
            "url": youtube_url,
            "quality": quality,
            "started": now,
            "last_seen": now,
            "duration": duration,
            "reconnects": 0,
        }
        return 0

    entry["last_seen"] = now
    entry["reconnects"] = int(entry.get("reconnects") or 0) + 1
    if duration and not entry.get("duration"):
        entry["duration"] = duration

    elapsed = max(0, int(now - float(entry.get("started", now))))

    # Unknown duration: resume by elapsed, but avoid tiny reconnect offset.
    if duration <= 0:
        return elapsed if elapsed > 2 else 0

    # Known duration: never seek beyond end. If loop is enabled, modulo.
    if elapsed >= max(duration - 2, 1):
        if loop:
            offset = elapsed % max(duration, 1)
            return offset if offset > 2 else 0
        return max(duration - 5, 0)

    return elapsed if elapsed > 2 else 0


def _youtube_jsmpeg_player_html(*, youtube_url: str = "", quality: str = "480", fit: str = "cover", hide: bool = False, session: str = "", resume: bool = False, loop: bool = True, start: int = 0, nocache: bool = False, token: str = "") -> str:
    safe_url = html.escape(youtube_url or "", quote=True)
    safe_quality = html.escape(_youtube_jsmpeg_quality(quality), quote=True)
    fit = "contain" if str(fit or "cover").strip().lower() == "contain" else "cover"
    body_class = "cover" if fit == "cover" else ""
    if hide:
        body_class = (body_class + " hidden-ui").strip()
    stream_url = ""
    if youtube_url:
        from urllib.parse import urlencode
        stream_params = {"url": youtube_url, "quality": safe_quality}
        if session:
            stream_params["session"] = session
        if resume:
            stream_params["resume"] = "1"
        stream_params["loop"] = "1" if loop else "0"
        if start:
            stream_params["start"] = str(start)
        if nocache:
            stream_params["nocache"] = "1"
        if token:
            stream_params["token"] = token
        stream_url = API_YOUTUBE_JSMPEG_WS_URL + "?" + urlencode(stream_params)
    stream_url_json = json.dumps(stream_url)
    safe_body = html.escape(body_class, quote=True)
    quality_json = json.dumps(safe_quality)
    fit_json = json.dumps(fit)
    hide_json = json.dumps("1" if hide else "0")
    return f"""<!doctype html>
<html lang='tr'>
<head>
  <meta charset='utf-8'>
  <meta name='viewport' content='width=device-width,initial-scale=1,viewport-fit=cover'>
  <title>POM Tesla YouTube Canvas</title>
  <style>
    html,body{{margin:0;width:100%;height:100%;overflow:hidden;background:#000;color:#e5edf7;font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;}}
    canvas{{position:fixed;top:50%;left:50%;width:100vw;height:100vh;transform:translate(-50%,-50%);background:#000;}}
    body.cover canvas{{width:120vw;height:120vh;}}
    #panel{{position:fixed;left:20px;right:20px;bottom:20px;z-index:10;background:rgba(15,23,42,.9);border:1px solid rgba(56,189,248,.25);border-radius:18px;padding:16px;backdrop-filter:blur(16px);}}
    #corner{{position:fixed;right:16px;top:16px;z-index:11;display:flex;gap:8px;}}
    #corner span{{background:rgba(2,6,23,.75);border:1px solid rgba(148,163,184,.18);border-radius:999px;padding:7px 11px;font-size:12px;color:#cbd5e1;}}
    input,select,button{{box-sizing:border-box;border-radius:12px;border:1px solid rgba(148,163,184,.25);background:#111827;color:#e5edf7;padding:12px;font:inherit;}}
    input{{width:100%;}}
    button{{border:0;background:linear-gradient(135deg,#0891b2,#2563eb);font-weight:900;cursor:pointer;}}
    .row{{display:grid;grid-template-columns:1fr 120px 120px 120px;gap:10px;align-items:end;}}
    label{{display:block;color:#9fb3ca;font-size:12px;font-weight:800;margin:0 0 5px;}}
    .hidden-ui #panel{{display:none;}}
    .ok{{color:#34d399;}} .err{{color:#f87171;}}
    @media(max-width:900px){{.row{{grid-template-columns:1fr;}}}}
  </style>
</head>
<body class='{safe_body}'>
  <canvas id='canvas'></canvas>
  <div id='corner'><span>POM YouTube Canvas</span><span id='state'>ready</span></div>
  <div id='panel'>
    <b>YouTube → yt-dlp → ffmpeg → MPEG-TS → JSMpeg Canvas2D</b><br><br>
    <div class='row'>
      <div><label>YouTube URL</label><input id='youtubeUrl' value='{safe_url}' placeholder='https://www.youtube.com/watch?v=...'></div>
      <div><label>Kalite</label><select id='quality'><option value='360'>360p</option><option value='480'>480p</option><option value='720'>720p</option><option value='1080_lite'>1080 Lite</option><option value='1080'>1080 Max</option></select></div>
      <div><label>Fit</label><select id='fit'><option value='cover'>Cover</option><option value='contain'>Contain</option></select></div>
      <div><label>UI</label><select id='hide'><option value='1'>Gizli</option><option value='0'>Görünür</option></select></div>
    </div>
    <br>
    <button onclick='openPlayer()'>Player Aç</button>
    <button onclick="document.body.classList.toggle('hidden-ui')">UI Gizle/Göster</button>
    <button onclick='stopPlayer()'>Stop</button>
    <br><br><span id='status'>Hazır.</span>
  </div>
<script src='https://cdn.jsdelivr.net/gh/phoboslab/jsmpeg@master/jsmpeg.min.js'></script>
<script>
const initialStreamUrl = {stream_url_json};
let player = null;
document.getElementById('quality').value = {quality_json};
document.getElementById('fit').value = {fit_json};
document.getElementById('hide').value = {hide_json};
function status(msg, cls=''){{
  document.getElementById('status').innerHTML = '<span class="'+cls+'">'+String(msg).replace(/[&<>]/g, m => ({{'&':'&amp;','<':'&lt;','>':'&gt;'}}[m]))+'</span>';
  document.getElementById('state').textContent = String(msg).slice(0,30);
}}
function openPlayer(){{
  const u = document.getElementById('youtubeUrl').value.trim();
  if(!u){{ alert('YouTube URL gir.'); return; }}
  const q = document.getElementById('quality').value;
  const f = document.getElementById('fit').value;
  const h = document.getElementById('hide').value;
  location.href = '{API_YOUTUBE_JSMPEG_PLAYER_URL}?url=' + encodeURIComponent(u) + '&quality=' + encodeURIComponent(q) + '&fit=' + encodeURIComponent(f) + '&hide=' + encodeURIComponent(h);
}}
function stopPlayer(){{
  try{{ if(player) player.destroy(); }}catch(e){{}}
  player = null;
  status('Durduruldu.');
}}
function makeWsUrl(pathUrl) {{
  if (!pathUrl) return "";
  if (pathUrl.startsWith("ws://") || pathUrl.startsWith("wss://")) return pathUrl;
  const proto = location.protocol === "https:" ? "wss:" : "ws:";
  return proto + "//" + location.host + pathUrl;
}}
function start(streamUrl){{
  if(!streamUrl) return;
  if(!window.JSMpeg){{ status('JSMpeg yüklenemedi.', 'err'); return; }}
  try{{
    const wsUrl = makeWsUrl(streamUrl);
    status('WebSocket stream başlıyor...', 'ok');
    let decodedFrames = 0;
    let firstFrameSeen = false;
    player = new JSMpeg.Player(wsUrl, {{
      canvas: document.getElementById('canvas'),
      autoplay: true,
      audio: false,
      loop: false,
      disableGl: true,
      progressive: false,
      throttled: false,
      videoBufferSize: 1024 * 1024 * 12,
      onSourceEstablished: function() {{
        status('WebSocket bağlantısı kuruldu. Frame bekleniyor...', 'ok');
      }},
      onVideoDecode: function() {{
        decodedFrames += 1;
        if (!firstFrameSeen) {{
          firstFrameSeen = true;
          status('İlk frame geldi. Tesla D testini yap.', 'ok');
        }}
      }}
    }});
    status('Canvas player başladı. Frame bekleniyor...', 'ok');
    setTimeout(function() {{
      if (!firstFrameSeen) {{
        status('WebSocket veri geliyor ama frame decode olmadı. 360p/farklı video deneyin.', 'err');
      }}
    }}, 7000);
  }}catch(err){{ status('Player hata: ' + (err && err.message ? err.message : err), 'err'); }}
}}
window.addEventListener('load', () => {{ if(initialStreamUrl) start(initialStreamUrl); }});
window.addEventListener('error', ev => status('JS hata: ' + ev.message, 'err'));
</script>
</body>
</html>"""


async def _async_youtube_direct_url(hass: HomeAssistant, youtube_url: str, quality: str, use_cache: bool = True) -> tuple[str, dict[str, str], int, bool]:
    """Resolve YouTube URL to direct media URL + headers + duration with cache.

    Repeated dashboard/WebSocket reconnects should not run yt-dlp every time.
    """
    youtube_url = _youtube_jsmpeg_validate_youtube_url(youtube_url)
    fmt = YOUTUBE_JSMPEG_FORMATS.get(quality, YOUTUBE_JSMPEG_FORMATS["480"])
    cache_key = f"{quality}|{youtube_url}"
    now = time.monotonic()
    cache = hass.data.setdefault(DOMAIN, {}).setdefault("youtube_jsmpeg_resolve_cache", {})
    cached = cache.get(cache_key) if use_cache else None
    if isinstance(cached, dict):
        try:
            if now - float(cached.get("ts", 0)) < 1800 and cached.get("url"):
                return str(cached["url"]), dict(cached.get("headers") or {}), int(cached.get("duration") or 0), True
        except Exception:
            cache.pop(cache_key, None)

    def _resolve() -> tuple[str, dict[str, str], int]:
        try:
            from yt_dlp import YoutubeDL
        except Exception as err:
            raise RuntimeError(f"yt-dlp import failed: {err}") from err

        ydl_opts = {
            "format": fmt,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "force_ipv4": True,
            "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
        }
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)

        if not isinstance(info, dict):
            raise RuntimeError("yt-dlp returned invalid info")

        direct_url = str(info.get("url") or "").strip()
        headers = dict(info.get("http_headers") or {})
        try:
            duration = int(float(info.get("duration") or 0))
        except Exception:
            duration = 0

        if not direct_url:
            requested = info.get("requested_formats") or []
            if requested:
                video_fmt = next((f for f in requested if str(f.get("vcodec") or "none") != "none"), requested[0])
                direct_url = str(video_fmt.get("url") or "").strip()
                headers = dict(video_fmt.get("http_headers") or headers)

        if not direct_url:
            formats = info.get("formats") or []
            for candidate in reversed(formats):
                if str(candidate.get("vcodec") or "none") != "none" and candidate.get("url"):
                    direct_url = str(candidate.get("url")).strip()
                    headers = dict(candidate.get("http_headers") or headers)
                    break

        if not direct_url:
            raise RuntimeError("yt-dlp did not return a direct video URL")

        direct_url = _youtube_jsmpeg_validate_direct_media_url(direct_url)
        return direct_url, headers, duration

    direct_url, headers, duration = await hass.async_add_executor_job(_resolve)
    cache[cache_key] = {
        "url": direct_url,
        "headers": headers,
        "duration": duration,
        "ts": now,
    }
    return direct_url, headers, duration, False


class PomTeslaYoutubeJSMpegHealthView(HomeAssistantView):
    """Diagnostics for YouTube JSMpeg live background dependencies."""

    url = API_YOUTUBE_JSMPEG_HEALTH_URL
    name = f"{DOMAIN}:youtube_jsmpeg_health"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request) -> web.Response:
        def _check_ytdlp() -> bool:
            import subprocess
            try:
                proc = subprocess.run([sys.executable, "-m", "yt_dlp", "--version"], capture_output=True, text=True, timeout=10)
                return proc.returncode == 0
            except Exception:
                return False
        return web.json_response({
            "success": True,
            "yt_dlp": await self.hass.async_add_executor_job(_check_ytdlp),
            "ffmpeg": shutil.which("ffmpeg") is not None,
            "player_url": API_YOUTUBE_JSMPEG_PLAYER_URL,
            "stream_url": API_YOUTUBE_JSMPEG_STREAM_URL,
            "websocket_url": API_YOUTUBE_JSMPEG_WS_URL,
            "producer_count": len(self.hass.data.get(DOMAIN, {}).get("youtube_jsmpeg_producers", {})),
            "producer_default": True,
            "legacy_query_param": "legacy=1",
            "last_youtube_jsmpeg": self.hass.data.get(DOMAIN, {}).get("youtube_jsmpeg_last_status", {}),
        })


class PomTeslaYoutubeJSMpegPlayerView(HomeAssistantView):
    """Serve the internal HA YouTube -> JSMpeg canvas player."""

    url = API_YOUTUBE_JSMPEG_PLAYER_URL
    name = f"{DOMAIN}:youtube_jsmpeg_player"
    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request) -> web.Response:
        youtube_url = str(request.query.get("url") or "").strip()
        quality = _youtube_jsmpeg_quality(request.query.get("quality"))
        fit = str(request.query.get("fit") or "cover").strip().lower()
        hide = str(request.query.get("hide") or "0").strip() == "1"
        session = str(request.query.get("session") or "").strip()
        resume = str(request.query.get("resume") or "0").strip() == "1"
        loop = str(request.query.get("loop") or "1").strip() != "0"
        start = _youtube_jsmpeg_parse_time(request.query.get("start")) or _youtube_jsmpeg_start_from_url(youtube_url)
        nocache = str(request.query.get("nocache") or "0").strip() == "1"
        token = str(request.query.get("token") or "").strip()
        if youtube_url:
            try:
                youtube_url = _youtube_jsmpeg_validate_youtube_url(youtube_url)
                _youtube_jsmpeg_validate_signed_token(self.hass, youtube_url, quality, token)
            except ValueError as err:
                return web.Response(text=str(err), status=403)
        return web.Response(text=_youtube_jsmpeg_player_html(youtube_url=youtube_url, quality=quality, fit=fit, hide=hide, session=session, resume=resume, loop=loop, start=start, nocache=nocache, token=token), content_type="text/html", charset="utf-8", headers={"Cache-Control": "no-store"})




class _PomYoutubeJSMpegProducer:
    """Single ffmpeg producer with many WebSocket subscribers.

    The producer is intentionally independent from client WebSocket lifetime.
    If Tesla/Lovelace reconnects the iframe, ffmpeg keeps running and the new
    client subscribes to the existing MPEG-TS stream instead of restarting at 0.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        *,
        key: str,
        youtube_url: str,
        quality: str,
        direct_url: str,
        direct_headers: dict[str, str],
        duration: int,
        start_offset: int = 0,
    ) -> None:
        self.hass = hass
        self.key = key
        self.youtube_url = youtube_url
        self.quality = quality
        self.direct_url = direct_url
        self.direct_headers = direct_headers
        self.duration = duration
        try:
            self.start_offset = max(0, int(start_offset or 0))
        except Exception:
            self.start_offset = 0
        self.proc: asyncio.subprocess.Process | None = None
        self.subscribers: set[asyncio.Queue[bytes | None]] = set()
        self.started_at = time.monotonic()
        self.last_client_at = time.monotonic()
        self.bytes_total = 0
        self.first_chunk = False
        self._reader_task: asyncio.Task | None = None
        self._stderr_task: asyncio.Task | None = None
        self._watchdog_task: asyncio.Task | None = None
        self._stopped = False

    async def start(self) -> None:
        status_store = self.hass.data.setdefault(DOMAIN, {})
        cmd = _youtube_jsmpeg_ffmpeg_cmd(self.direct_url, self.quality, self.direct_headers, self.start_offset)
        status_store["youtube_jsmpeg_last_status"] = {
            "stage": "producer_ffmpeg_starting",
            "quality": self.quality,
            "realtime_input": True,
            "seek_mode": "input_fast" if self.start_offset > 2 else "none",
            "threads": "auto",
            "fps": "30" if self.quality == "1080_high" else ("24" if self.quality in ("1080", "1080_lite") else "25"),
            "profile": "1080_lite" if self.quality == "1080_lite" else self.quality,
            "key": self.key[:160],
            "duration": self.duration,
            "start_offset": self.start_offset,
            "ts": dt_util.utcnow().isoformat(),
        }
        self.proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.DEVNULL,
        )
        self._reader_task = asyncio.create_task(self._read_stdout())
        self._stderr_task = asyncio.create_task(self._read_stderr())
        self._watchdog_task = asyncio.create_task(self._idle_watchdog())

    async def _read_stdout(self) -> None:
        status_store = self.hass.data.setdefault(DOMAIN, {})
        try:
            assert self.proc is not None and self.proc.stdout is not None
            while not self._stopped:
                chunk = await self.proc.stdout.read(64 * 1024)
                if not chunk:
                    break
                if not self.first_chunk:
                    self.first_chunk = True
                    status_store["youtube_jsmpeg_last_status"] = {
                        "stage": "producer_streaming",
                        "quality": self.quality,
                        "key": self.key[:160],
                        "first_chunk_bytes": len(chunk),
                        "subscribers": len(self.subscribers),
                        "duration": self.duration,
                        "ts": dt_util.utcnow().isoformat(),
                    }
                self.bytes_total += len(chunk)
                dead: list[asyncio.Queue[bytes | None]] = []
                for queue in list(self.subscribers):
                    try:
                        if queue.qsize() > 32:
                            # Drop slow subscriber rather than blocking producer.
                            dead.append(queue)
                            continue
                        queue.put_nowait(chunk)
                    except Exception:
                        dead.append(queue)
                for queue in dead:
                    self.subscribers.discard(queue)
                    try:
                        queue.put_nowait(None)
                    except Exception:
                        pass
        except Exception as err:
            _LOGGER.exception("YouTube JSMpeg producer stdout failed")
            status_store["youtube_jsmpeg_last_status"] = {
                "stage": "producer_stream_error",
                "quality": self.quality,
                "error": str(err)[:1000],
                "ts": dt_util.utcnow().isoformat(),
            }
        finally:
            await self.stop(reason="producer_stdout_finished")

    async def _read_stderr(self) -> None:
        status_store = self.hass.data.setdefault(DOMAIN, {})
        try:
            assert self.proc is not None and self.proc.stderr is not None
            while not self._stopped:
                line = await self.proc.stderr.readline()
                if not line:
                    break
                decoded = line.decode("utf-8", "replace").rstrip()
                status_store["youtube_jsmpeg_last_status"] = {
                    "stage": "producer_ffmpeg_log",
                    "quality": self.quality,
                    "message": decoded[-1000:],
                    "key": self.key[:160],
                    "ts": dt_util.utcnow().isoformat(),
                }
                _LOGGER.warning("YouTube JSMpeg producer ffmpeg: %s", decoded)
        except Exception:
            pass

    async def _idle_watchdog(self) -> None:
        while not self._stopped:
            await asyncio.sleep(5)
            if self.subscribers:
                self.last_client_at = time.monotonic()
                continue
            if time.monotonic() - self.last_client_at > 120:
                await self.stop(reason="producer_idle_timeout")
                return

    def subscribe(self) -> asyncio.Queue[bytes | None]:
        queue: asyncio.Queue[bytes | None] = asyncio.Queue(maxsize=64)
        self.subscribers.add(queue)
        self.last_client_at = time.monotonic()
        self.hass.data.setdefault(DOMAIN, {})["youtube_jsmpeg_last_status"] = {
            "stage": "producer_client_subscribed",
            "quality": self.quality,
            "key": self.key[:160],
            "subscribers": len(self.subscribers),
            "bytes_total": self.bytes_total,
            "ts": dt_util.utcnow().isoformat(),
        }
        return queue

    def unsubscribe(self, queue: asyncio.Queue[bytes | None]) -> None:
        self.subscribers.discard(queue)
        self.last_client_at = time.monotonic()
        self.hass.data.setdefault(DOMAIN, {})["youtube_jsmpeg_last_status"] = {
            "stage": "producer_client_unsubscribed",
            "quality": self.quality,
            "key": self.key[:160],
            "subscribers": len(self.subscribers),
            "bytes_total": self.bytes_total,
            "ts": dt_util.utcnow().isoformat(),
        }

    async def stop(self, reason: str = "stop") -> None:
        if self._stopped:
            return
        self._stopped = True
        for queue in list(self.subscribers):
            try:
                queue.put_nowait(None)
            except Exception:
                pass
        self.subscribers.clear()
        try:
            if self.proc is not None and self.proc.returncode is None:
                self.proc.terminate()
                await asyncio.wait_for(self.proc.wait(), timeout=3)
        except Exception:
            try:
                if self.proc is not None:
                    self.proc.kill()
            except Exception:
                pass
        producers = self.hass.data.setdefault(DOMAIN, {}).setdefault("youtube_jsmpeg_producers", {})
        if producers.get(self.key) is self:
            producers.pop(self.key, None)
        self.hass.data.setdefault(DOMAIN, {})["youtube_jsmpeg_last_status"] = {
            "stage": "producer_stopped",
            "quality": self.quality,
            "key": self.key[:160],
            "reason": reason,
            "bytes_total": self.bytes_total,
            "ts": dt_util.utcnow().isoformat(),
        }


async def _async_get_youtube_jsmpeg_producer(
    hass: HomeAssistant,
    youtube_url: str,
    quality: str,
    start_base: int = 0,
) -> _PomYoutubeJSMpegProducer:
    """Get or create one producer per YouTube URL + quality + start offset."""
    try:
        start_base = max(0, int(start_base or 0))
    except Exception:
        start_base = 0
    youtube_url = _youtube_jsmpeg_validate_youtube_url(youtube_url)
    key = f"{quality}|{start_base}|{youtube_url}"
    producers = hass.data.setdefault(DOMAIN, {}).setdefault("youtube_jsmpeg_producers", {})
    existing = producers.get(key)
    if isinstance(existing, _PomYoutubeJSMpegProducer) and not existing._stopped:
        return existing

    if _youtube_jsmpeg_active_process_count(hass) >= YOUTUBE_JSMPEG_MAX_FFMPEG_PROCESSES:
        raise RuntimeError(f"YouTube background process limit reached ({YOUTUBE_JSMPEG_MAX_FFMPEG_PROCESSES}).")

    hass.data.setdefault(DOMAIN, {})["youtube_jsmpeg_last_status"] = {
        "stage": "producer_resolving",
        "quality": quality,
        "url": youtube_url[:160],
        "ts": dt_util.utcnow().isoformat(),
    }
    direct_url, direct_headers, duration, cache_hit = await _async_youtube_direct_url(hass, youtube_url, quality, use_cache=True)
    producer = _PomYoutubeJSMpegProducer(
        hass,
        key=key,
        youtube_url=youtube_url,
        quality=quality,
        direct_url=direct_url,
        direct_headers=direct_headers,
        duration=duration,
        start_offset=start_base,
    )
    producers[key] = producer
    try:
        await producer.start()
    except Exception:
        producers.pop(key, None)
        raise
    hass.data.setdefault(DOMAIN, {})["youtube_jsmpeg_last_status"] = {
        "stage": "producer_started",
        "quality": quality,
        "key": key[:160],
        "cache_hit": cache_hit,
        "duration": duration,
        "start_offset": start_base,
        "ts": dt_util.utcnow().isoformat(),
    }
    return producer


class PomTeslaYoutubeJSMpegWebSocketView(HomeAssistantView):
    """Stream YouTube as MPEG-TS/MPEG1 over WebSocket for JSMpeg canvas playback."""

    url = API_YOUTUBE_JSMPEG_WS_URL
    name = f"{DOMAIN}:youtube_jsmpeg_ws"
    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request) -> web.WebSocketResponse:
        youtube_url = str(request.query.get("url") or "").strip()
        quality = _youtube_jsmpeg_quality(request.query.get("quality"))
        player_id = str(request.query.get("player_id") or "").strip()
        session = str(request.query.get("session") or "").strip()
        resume = str(request.query.get("resume") or "0").strip() == "1"
        loop = str(request.query.get("loop") or "1").strip() != "0"
        nocache = str(request.query.get("nocache") or "0").strip() == "1"
        legacy_mode = str(request.query.get("legacy") or "0").strip() == "1"
        producer_mode = not legacy_mode
        if nocache or producer_mode:
            resume = False
        start_base = _youtube_jsmpeg_parse_time(request.query.get("start")) or _youtube_jsmpeg_start_from_url(youtube_url)
        if nocache:
            start_base = 0
        token = str(request.query.get("token") or "").strip()
        try:
            youtube_url = _youtube_jsmpeg_validate_youtube_url(youtube_url)
            _youtube_jsmpeg_validate_signed_token(self.hass, youtube_url, quality, token)
        except ValueError as err:
            return web.Response(text=str(err), status=403)
        ws = web.WebSocketResponse(autoping=True, heartbeat=30)
        await ws.prepare(request)

        status_store = self.hass.data.setdefault(DOMAIN, {})
        if not youtube_url:
            status_store["youtube_jsmpeg_last_status"] = {"stage": "ws_missing_url", "quality": quality, "ts": dt_util.utcnow().isoformat()}
            await ws.close(message=b"Missing url parameter")
            return ws
        if shutil.which("ffmpeg") is None:
            status_store["youtube_jsmpeg_last_status"] = {"stage": "ws_no_ffmpeg", "quality": quality, "ts": dt_util.utcnow().isoformat()}
            await ws.close(message=b"ffmpeg binary not found")
            return ws

        if producer_mode:
            try:
                producer = await _async_get_youtube_jsmpeg_producer(self.hass, youtube_url, quality, start_base)
                queue = producer.subscribe()
                try:
                    while not ws.closed:
                        chunk = await queue.get()
                        if chunk is None:
                            break
                        await ws.send_bytes(chunk)
                except (ConnectionResetError, asyncio.CancelledError):
                    _LOGGER.debug("YouTube JSMpeg producer WebSocket client disconnected")
                finally:
                    producer.unsubscribe(queue)
                    if not ws.closed:
                        await ws.close()
                return ws
            except Exception as err:
                _LOGGER.exception("YouTube JSMpeg producer mode failed")
                status_store["youtube_jsmpeg_last_status"] = {
                    "stage": "producer_ws_error",
                    "quality": quality,
                    "error": str(err)[:1000],
                    "ts": dt_util.utcnow().isoformat(),
                }
                if not ws.closed:
                    await ws.close(message=str(err).encode("utf-8", "replace")[:500])
                return ws

        status_store["youtube_jsmpeg_last_status"] = {"stage": "ws_resolving", "quality": quality, "url": youtube_url[:160], "ts": dt_util.utcnow().isoformat()}
        try:
            direct_url, direct_headers, duration, cache_hit = await _async_youtube_direct_url(self.hass, youtube_url, quality, use_cache=not nocache)
            status_store["youtube_jsmpeg_last_status"] = {
                "stage": "ws_resolved_cache" if cache_hit else "ws_resolved",
                "quality": quality,
                "has_headers": bool(direct_headers),
                "direct_url_host": direct_url.split("/")[2] if "://" in direct_url else "",
                "duration": duration,
                "session": session,
                "resume": resume,
                "loop": loop,
                "start_base": start_base,
                "cache_hit": cache_hit,
                "ts": dt_util.utcnow().isoformat(),
            }
        except Exception as err:
            _LOGGER.exception("Could not resolve YouTube URL for JSMpeg WebSocket")
            status_store["youtube_jsmpeg_last_status"] = {"stage": "ws_yt_dlp_error", "quality": quality, "error": str(err)[:1000], "ts": dt_util.utcnow().isoformat()}
            await ws.close(message=str(err).encode("utf-8", "replace")[:500])
            return ws

        resume_offset = _youtube_jsmpeg_session_offset(self.hass, session, youtube_url, quality, duration, loop) if resume else 0
        start_offset = int(start_base or 0) + int(resume_offset or 0)
        if duration > 0 and start_offset >= max(duration - 2, 1):
            start_offset = (start_offset % duration) if loop else max(duration - 5, 0)
        if start_offset > 0:
            status_store["youtube_jsmpeg_last_status"] = {"stage": "ws_resume_offset", "quality": quality, "session": session, "resume_offset": resume_offset, "start_base": start_base, "start_offset": start_offset, "duration": duration, "ts": dt_util.utcnow().isoformat()}
        legacy_slot_acquired = False
        if not _youtube_jsmpeg_acquire_legacy_process_slot(self.hass):
            status_store["youtube_jsmpeg_last_status"] = {"stage": "ws_process_limit", "quality": quality, "limit": YOUTUBE_JSMPEG_MAX_FFMPEG_PROCESSES, "ts": dt_util.utcnow().isoformat()}
            await ws.close(message=b"YouTube background process limit reached")
            return ws
        legacy_slot_acquired = True
        cmd = _youtube_jsmpeg_ffmpeg_cmd(direct_url, quality, direct_headers, start_offset)
        status_store["youtube_jsmpeg_last_status"] = {"stage": "ws_ffmpeg_starting", "quality": quality, "session": session, "start_offset": start_offset, "duration": duration, "cache_hit": cache_hit, "ts": dt_util.utcnow().isoformat()}
        try:
            proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, stdin=asyncio.subprocess.DEVNULL)
        except Exception as err:
            _LOGGER.exception("Could not start ffmpeg for YouTube JSMpeg WebSocket")
            status_store["youtube_jsmpeg_last_status"] = {"stage": "ws_ffmpeg_start_error", "quality": quality, "error": str(err)[:1000], "ts": dt_util.utcnow().isoformat()}
            if legacy_slot_acquired:
                _youtube_jsmpeg_release_legacy_process_slot(self.hass)
            await ws.close(message=str(err).encode("utf-8", "replace")[:500])
            return ws

        async def _log_stderr() -> None:
            try:
                assert proc.stderr is not None
                while True:
                    line = await proc.stderr.readline()
                    if not line:
                        break
                    decoded = line.decode("utf-8", "replace").rstrip()
                    status_store["youtube_jsmpeg_last_status"] = {"stage": "ws_ffmpeg_log", "quality": quality, "message": decoded[-1000:], "ts": dt_util.utcnow().isoformat()}
                    _LOGGER.warning("YouTube JSMpeg WS ffmpeg: %s", decoded)
            except Exception:
                pass

        asyncio.create_task(_log_stderr())

        first_chunk = True
        bytes_sent = 0
        try:
            assert proc.stdout is not None
            while not ws.closed:
                chunk = await proc.stdout.read(64 * 1024)
                if not chunk:
                    break
                if first_chunk:
                    first_chunk = False
                    status_store["youtube_jsmpeg_last_status"] = {"stage": "ws_streaming", "quality": quality, "first_chunk_bytes": len(chunk), "player_id": player_id, "session": session, "resume": resume, "loop": loop, "duration": duration, "ts": dt_util.utcnow().isoformat()}
                bytes_sent += len(chunk)
                await ws.send_bytes(chunk)
        except (ConnectionResetError, asyncio.CancelledError):
            _LOGGER.debug("YouTube JSMpeg WebSocket client disconnected")
        except Exception as err:
            _LOGGER.exception("YouTube JSMpeg WebSocket stream failed")
            status_store["youtube_jsmpeg_last_status"] = {"stage": "ws_stream_error", "quality": quality, "error": str(err)[:1000], "ts": dt_util.utcnow().isoformat()}
        finally:
            try:
                proc.terminate()
                await asyncio.wait_for(proc.wait(), timeout=3)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
            if bytes_sent == 0:
                status_store["youtube_jsmpeg_last_status"] = {"stage": "ws_no_output", "quality": quality, "returncode": proc.returncode, "ts": dt_util.utcnow().isoformat()}
            else:
                status_store["youtube_jsmpeg_last_status"] = {"stage": "ws_finished", "quality": quality, "bytes_sent": bytes_sent, "returncode": proc.returncode, "ts": dt_util.utcnow().isoformat()}
            if legacy_slot_acquired:
                _youtube_jsmpeg_release_legacy_process_slot(self.hass)
            if not ws.closed:
                await ws.close()
        return ws


class PomTeslaYoutubeJSMpegStreamView(HomeAssistantView):
    """Stream YouTube as MPEG-TS/MPEG1 for JSMpeg canvas playback."""

    url = API_YOUTUBE_JSMPEG_STREAM_URL
    name = f"{DOMAIN}:youtube_jsmpeg_stream"
    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request) -> web.StreamResponse:
        youtube_url = str(request.query.get("url") or "").strip()
        quality = _youtube_jsmpeg_quality(request.query.get("quality"))
        if not youtube_url:
            return web.Response(text="Missing url parameter", status=400)
        token = str(request.query.get("token") or "").strip()
        try:
            youtube_url = _youtube_jsmpeg_validate_youtube_url(youtube_url)
            _youtube_jsmpeg_validate_signed_token(self.hass, youtube_url, quality, token)
        except ValueError as err:
            return web.Response(text=str(err), status=403)
        if shutil.which("ffmpeg") is None:
            return web.Response(text="ffmpeg binary not found in Home Assistant environment", status=500)
        status_store = self.hass.data.setdefault(DOMAIN, {})
        status_store["youtube_jsmpeg_last_status"] = {"stage": "resolving", "quality": quality, "url": youtube_url[:160], "ts": dt_util.utcnow().isoformat()}
        try:
            direct_url, direct_headers, duration, cache_hit = await _async_youtube_direct_url(self.hass, youtube_url, quality)
            status_store["youtube_jsmpeg_last_status"] = {"stage": "resolved", "quality": quality, "has_headers": bool(direct_headers), "direct_url_host": direct_url.split("/")[2] if "://" in direct_url else "", "ts": dt_util.utcnow().isoformat()}
        except Exception as err:
            _LOGGER.exception("Could not resolve YouTube URL for JSMpeg stream")
            status_store["youtube_jsmpeg_last_status"] = {"stage": "yt_dlp_error", "quality": quality, "error": str(err)[:1000], "ts": dt_util.utcnow().isoformat()}
            return web.Response(text=f"yt-dlp error: {err}", status=500)
        stream_slot_acquired = False
        if not _youtube_jsmpeg_acquire_legacy_process_slot(self.hass):
            status_store["youtube_jsmpeg_last_status"] = {"stage": "stream_process_limit", "quality": quality, "limit": YOUTUBE_JSMPEG_MAX_FFMPEG_PROCESSES, "ts": dt_util.utcnow().isoformat()}
            return web.Response(text="YouTube background process limit reached", status=429)
        stream_slot_acquired = True
        cmd = _youtube_jsmpeg_ffmpeg_cmd(direct_url, quality, direct_headers)
        try:
            proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, stdin=asyncio.subprocess.DEVNULL)
        except Exception as err:
            _LOGGER.exception("Could not start ffmpeg for YouTube JSMpeg stream")
            if stream_slot_acquired:
                _youtube_jsmpeg_release_legacy_process_slot(self.hass)
            return web.Response(text=f"ffmpeg start error: {err}", status=500)

        async def _log_stderr() -> None:
            try:
                assert proc.stderr is not None
                while True:
                    line = await proc.stderr.readline()
                    if not line:
                        break
                    decoded = line.decode("utf-8", "replace").rstrip()
                    status_store["youtube_jsmpeg_last_status"] = {"stage": "ffmpeg_log", "quality": quality, "message": decoded[-1000:], "ts": dt_util.utcnow().isoformat()}
                    _LOGGER.warning("YouTube JSMpeg ffmpeg: %s", decoded)
            except Exception:
                pass
        asyncio.create_task(_log_stderr())
        response = web.StreamResponse(status=200, reason="OK", headers={"Content-Type": "video/MP2T", "Cache-Control": "no-store", "X-Accel-Buffering": "no"})
        await response.prepare(request)
        first_chunk = True
        bytes_sent = 0
        try:
            assert proc.stdout is not None
            while True:
                chunk = await proc.stdout.read(64 * 1024)
                if not chunk:
                    break
                if first_chunk:
                    first_chunk = False
                    status_store["youtube_jsmpeg_last_status"] = {"stage": "streaming", "quality": quality, "first_chunk_bytes": len(chunk), "ts": dt_util.utcnow().isoformat()}
                bytes_sent += len(chunk)
                await response.write(chunk)
        except (ConnectionResetError, asyncio.CancelledError):
            _LOGGER.debug("YouTube JSMpeg client disconnected")
        except Exception:
            _LOGGER.exception("YouTube JSMpeg stream failed")
        finally:
            try:
                proc.terminate()
                await asyncio.wait_for(proc.wait(), timeout=3)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
            if bytes_sent == 0:
                status_store["youtube_jsmpeg_last_status"] = {"stage": "no_output", "quality": quality, "returncode": proc.returncode, "ts": dt_util.utcnow().isoformat()}
            else:
                status_store["youtube_jsmpeg_last_status"] = {"stage": "finished", "quality": quality, "bytes_sent": bytes_sent, "returncode": proc.returncode, "ts": dt_util.utcnow().isoformat()}
            if stream_slot_acquired:
                _youtube_jsmpeg_release_legacy_process_slot(self.hass)
            try:
                await response.write_eof()
            except Exception:
                pass
        return response


class PomTeslaSystemHealthView(HomeAssistantView):
    """Live API endpoint for the POM Tesla System Health card."""

    url = API_HEALTH_URL
    name = f"api:{DOMAIN}:health"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request) -> web.Response:
        data = _entry_config(self.hass)
        health = _system_health_payload(self.hass, data)
        return web.json_response(
            {
                "success": True,
                "language": _app_language(self.hass),
                "health": health,
                "general_settings": {"health": health},
            }
        )


async def async_setup_panel(hass: HomeAssistant, *, version: str = "dev") -> None:
    """Register API endpoints and sidebar panel for the POM Tesla app UI."""
    data = hass.data.setdefault(DOMAIN, {})
    if not data.get("panel_api_registered"):
        hass.http.register_view(PomTeslaChargeRecordsView(hass))
        hass.http.register_view(PomTeslaTripRecordsView(hass))
        hass.http.register_view(PomTeslaRecordMapView(hass))
        hass.http.register_view(PomTeslaSettingsView(hass))
        hass.http.register_view(PomTeslaSystemHealthView(hass))
        data["panel_health_api_registered"] = True
        hass.http.register_view(PomTeslaTelegramTestView(hass))
        hass.http.register_view(PomTeslaAITestView(hass))
        hass.http.register_view(PomTeslaDashboardResourcesView(hass))
        hass.http.register_view(PomTeslaDashboardMediaView(hass))
        hass.http.register_view(PomTeslaBackupExportView(hass))
        hass.http.register_view(PomTeslaTripTestView(hass))
        hass.http.register_view(PomTeslaLiveTripTestView(hass))
        hass.http.register_view(PomTeslaLiveTripAIIntervalView(hass))
        hass.http.register_view(PomTeslaLiveTripAITestView(hass))
        hass.http.register_view(PomTeslaLiveTripDebugView(hass))
        hass.http.register_view(PomTeslaSystemLogsView(hass))
        hass.http.register_view(PomTeslaChargeTestView(hass))
        hass.http.register_view(PomTeslaYoutubeJSMpegHealthView(hass))
        hass.http.register_view(PomTeslaYoutubeJSMpegPlayerView(hass))
        hass.http.register_view(PomTeslaYoutubeJSMpegWebSocketView(hass))
        hass.http.register_view(PomTeslaYoutubeJSMpegStreamView(hass))
        data["panel_api_registered"] = True

    if not data.get("panel_health_api_registered"):
        hass.http.register_view(PomTeslaSystemHealthView(hass))
        data["panel_health_api_registered"] = True

    js_url = f"/{DOMAIN}/{PANEL_JS_FILE}?v={version}"

    # Re-register the panel every setup/reload so Home Assistant does not keep
    # an old custom-panel js_url in hass.data["frontend_panels"]. Without this,
    # backend updates load but the browser can keep using an older
    # pom-tesla-report-panel.js module.
    panels = hass.data.get("frontend_panels", {})
    if PANEL_URL_PATH in panels:
        try:
            remove_panel = getattr(frontend, "async_remove_panel", None)
            if remove_panel is not None:
                remove_panel(hass, PANEL_URL_PATH)
            else:
                panels.pop(PANEL_URL_PATH, None)
            data["panel_registered"] = False
            _LOGGER.debug("Removed existing Tesla AI panel before re-registering")
        except Exception as err:
            _LOGGER.warning("Could not remove existing Tesla AI panel before re-registering: %s", err)
            panels.pop(PANEL_URL_PATH, None)

    try:
        frontend.async_register_built_in_panel(
            hass,
            component_name="custom",
            sidebar_title="Tesla AI",
            sidebar_icon="mdi:car-electric",
            sidebar_default_visible=True,
            frontend_url_path=PANEL_URL_PATH,
            require_admin=False,
            config={
                "_panel_custom": {
                    "name": PANEL_ELEMENT_NAME,
                    "js_url": js_url,
                    "module_url": js_url,
                    "embed_iframe": False,
                },
                "api_base": f"/api/{DOMAIN}",
            },
        )
        data["panel_registered"] = True
        _LOGGER.info("Tesla AI app panel registered at /%s with %s", PANEL_URL_PATH, js_url)
    except Exception as err:
        _LOGGER.warning("Could not register Tesla AI panel: %s", err)
