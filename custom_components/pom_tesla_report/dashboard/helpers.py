"""Dashboard helpers for POM Tesla Report."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import re
import time
from urllib.parse import urlencode

from homeassistant.components import persistent_notification
from homeassistant.core import HomeAssistant

from .const import *

try:
    STATIC_ASSET_URL_PATH
except NameError:
    STATIC_ASSET_URL_PATH = "/pom_tesla_report/dashboard/png"

PANEL_DASHBOARD_ROLE_TO_OPTION = {
    "dashboard_top_power": "entity_power",
    "dashboard_top_speed": "entity_speed",
    "dashboard_top_elevation": "entity_elevation",
    "dashboard_top_battery_level": "entity_battery_level",
    "dashboard_top_est_range": "entity_est_range",
    "dashboard_top_outside_temp": "entity_outside_temp",
    "dashboard_top_location": "entity_location_sensor",
    "dashboard_top_rated_range": "entity_rated_range",
    "dashboard_top_energy_remaining": "entity_energy_remaining",
    "dashboard_sidebar_inside_temp": "entity_inside_temp",
    "dashboard_sidebar_battery_module_temp": "entity_battery_heater",
    "dashboard_top_odometer": "entity_odometer",
    "dashboard_person_track_1": "person_track_1_entity",
    "dashboard_person_track_2": "person_track_2_entity",
    "dashboard_person_track_3": "person_track_3_entity",
    "dashboard_sidebar_homelink": "entity_homelink",
    "dashboard_sidebar_defrost": "entity_defrost",
    "dashboard_sidebar_steering_heater": "entity_steering_heater",
    "dashboard_bottom_flash_lights_action": "entity_flash_lights",
    "dashboard_bottom_honk_action": "entity_honk",
    "dashboard_bottom_sentry": "entity_sentry_mode",
    "dashboard_bottom_fart_action": "entity_fart",
    "dashboard_sidebar_wake": "entity_wake",
    "dashboard_sidebar_valet_mode": "entity_valet_mode",
    "dashboard_charge_popup_charge_cable": "charge_cable",
    "dashboard_charge_popup_battery_level": "charge_battery_level",
    "dashboard_charge_popup_battery_range": "charge_battery_range",
    "dashboard_charge_popup_range_estimate": "charge_battery_range_estimate",
    "dashboard_charge_popup_energy_added": "charge_energy_added",
    "dashboard_charge_popup_charge_rate": "charge_rate",
    "dashboard_charge_popup_current": "charge_current",
    "dashboard_charge_popup_voltage": "charge_voltage",
    "dashboard_charge_popup_time_to_full": "charge_time_to_full",
    "dashboard_charge_popup_last_charge": "charge_last_charge",
    "dashboard_home_entity_1": "entity_home_entity_1",
    "dashboard_home_entity_2": "entity_home_entity_2",
    "dashboard_home_entity_3": "entity_home_entity_3",
}


DASHBOARD_SELF_OUTPUT_ENTITY_IDS = {
    LOCATION_LABEL_ENTITY_ID,
    "sensor.pom_tesla_dashboard_last_charge",
    *PERSON_TRACK_SENSOR_ENTITY_IDS.values(),
}


def _is_dashboard_self_output_entity(value: Any) -> bool:
    """Return true for dashboard output sensors that must never be source entities."""
    entity_id = str(value or "").strip().lower()
    return entity_id in {str(item).lower() for item in DASHBOARD_SELF_OUTPUT_ENTITY_IDS} or entity_id.startswith("sensor.pom_tesla_dashboard_person_track_")


def _sanitize_person_track_options(options: dict[str, Any]) -> None:
    """Remove self-referential person-track sources before dashboard rendering/sensors."""
    for slot, entity_key, _name_key, enabled_key in PERSON_TRACK_SLOTS:
        entity_id = str(options.get(entity_key) or "").strip()
        if _is_dashboard_self_output_entity(entity_id):
            options[entity_key] = ""
            options[enabled_key] = False


ENTITY_REPLACEMENTS = {
    "sensor.tesla_power": CONF_ENTITY_POWER,
    "sensor.tesla_elevation": CONF_ENTITY_ELEVATION,
    "sensor.tesla_speed": CONF_ENTITY_SPEED,
    "sensor.tesla_battery_level": CONF_ENTITY_BATTERY_LEVEL,
    "sensor.tesla_est_range": CONF_ENTITY_EST_RANGE,
    "sensor.tesla_rated_range": CONF_ENTITY_RATED_RANGE,
    "sensor.pom_energy_remaining": CONF_ENTITY_ENERGY_REMAINING,
    "sensor.pom_charger_power": CONF_CHARGE_CHARGER_POWER,
    "sensor.tesla_inside_temp": CONF_ENTITY_INSIDE_TEMP,
    "sensor.pom_pil_modulu_maksimum_sicakligi": CONF_ENTITY_BATTERY_TEMP,
    "sensor.tesla": CONF_ENTITY_LOCATION_SENSOR,
    "binary_sensor.pom_charging": CONF_ENTITY_CHARGING,
    "binary_sensor.tesla_plugged_in": CONF_ENTITY_PLUGGED_IN,
    "sensor.tesla_shift_state_memory": CONF_ENTITY_SHIFT_STATE,
    "sensor.pom_live_trip": CONF_ENTITY_LIVE_TRIP,
    "person.tesla": CONF_ENTITY_PERSON_TESLA,
    "person.ali": CONF_ENTITY_PERSON_2,
    "person.cavidan": CONF_ENTITY_PERSON_3,
    "input_boolean.tesla_map": CONF_HELPER_MAP,
    "input_boolean.tesla_person_cards_on_map": CONF_HELPER_PERSON_CARDS,
    "input_boolean.tesla_interactive_map": CONF_HELPER_INTERACTIVE_MAP,
    "input_boolean.tesla_controls": CONF_HELPER_CONTROLS,
    "button.pom_flash_lights_2": CONF_ENTITY_FLASH_LIGHTS_STATE,
    "button.pom_flash_lights": CONF_ENTITY_FLASH_LIGHTS,
    "switch.pom_sentry_mode_2": CONF_ENTITY_SENTRY,
    "button.pom_honk_horn_2": CONF_ENTITY_HONK_STATE,
    "button.pom_honk_horn": CONF_ENTITY_HONK,
    "button.pom_play_fart_2": CONF_ENTITY_FART_STATE,
    "button.pom_play_fart": CONF_ENTITY_FART,
    "binary_sensor.tesla_windows_open": CONF_ENTITY_WINDOWS_OPEN,
    "binary_sensor.tesla_doors_open": CONF_ENTITY_DOORS_OPEN,
    "input_boolean.zone_leave_house_activate": CONF_ENTITY_HOME_AUTOMATION,
    "input_boolean.tesla_automation_speed_sections": CONF_ENTITY_MANUAL_TRACKING,
}

ASSET_REPLACEMENTS = {
    "/local/png/tesla/teslacharging.gif": CONF_IMAGE_CHARGING,
    "/local/png/teslacharging.gif": CONF_IMAGE_CHARGING,
    "/local/png/tesla.png": CONF_IMAGE_PARKED,
    "/local/png/tesla/tesla.png": CONF_IMAGE_PARKED,
    "/local/png/tesla/tesladriving.gif": CONF_IMAGE_DRIVING,
    "/local/png/tesladriving.gif": CONF_IMAGE_DRIVING,
}

CHARGE_POPUP_ENTITY_REPLACEMENTS = {
    "binary_sensor.pom_charging": CONF_ENTITY_CHARGING,
    "sensor.pom_battery_level": CONF_CHARGE_BATTERY_LEVEL,
    "sensor.pom_battery_range": CONF_CHARGE_BATTERY_RANGE,
    "sensor.pom_battery_range_estimate": CONF_CHARGE_BATTERY_RANGE_ESTIMATE,
    "sensor.pom_charge_energy_added": CONF_CHARGE_ENERGY_ADDED,
    "sensor.pom_charger_power": CONF_CHARGE_CHARGER_POWER,
    "sensor.pom_pil_modulu_maksimum_sicakligi": CONF_ENTITY_BATTERY_TEMP,
    "sensor.pom_battery_pack_voltage": CONF_CHARGE_BATTERY_PACK_VOLTAGE,
    "binary_sensor.pom_charge_cable": CONF_CHARGE_CABLE,
    "sensor.pom_charge_rate": CONF_CHARGE_RATE,
    "sensor.pom_charger_current": CONF_CHARGE_CURRENT,
    "sensor.pom_charger_voltage": CONF_CHARGE_VOLTAGE,
    "sensor.pom_time_to_full_charge": CONF_CHARGE_TIME_TO_FULL,
    "input_number.tesla_supercharger_kwh_fiyati": CONF_CHARGE_SUPERCHARGER_PRICE,
    "input_number.tesla_zes_kwh_fiyati": CONF_CHARGE_ZES_PRICE,
    "input_number.tesla_astor_kwh_fiyati": CONF_CHARGE_ASTOR_PRICE,
}


def _youtube_video_id_from_value(value: Any) -> str:
    """Extract a safe YouTube video id from a URL or raw id."""
    raw = str(value or "").strip()
    if not raw:
        return ""
    patterns = [
        r"(?:youtube\.com/watch\?v=|youtube\.com/embed/|youtu\.be/|youtube\.com/shorts/)([A-Za-z0-9_-]{6,})",
        r"^([A-Za-z0-9_-]{6,})$",
    ]
    for pattern in patterns:
        match = re.search(pattern, raw)
        if match:
            return match.group(1)[:64]
    return ""


def _youtube_embed_url(video_value: Any, start_seconds: Any = 0, *, mute: bool = True, loop: bool = True) -> str:
    """Build a YouTube embed URL suitable for a background iframe."""
    video_id = _youtube_video_id_from_value(video_value)
    if not video_id:
        return ""
    try:
        start = int(float(start_seconds or 0))
    except Exception:
        start = 0
    if start < 0:
        start = 0
    params = [
        "autoplay=1",
        "controls=0",
        "showinfo=0",
        "rel=0",
        "modestbranding=1",
        "playsinline=1",
        f"mute={1 if mute else 0}",
        f"start={start}",
    ]
    if loop:
        params.extend(["loop=1", f"playlist={video_id}"])
    return f"https://www.youtube.com/embed/{video_id}?{'&'.join(params)}"


def _youtube_wrapper_url(video_value: Any, start_seconds: Any = 0, *, mute: bool = True, loop: bool = True) -> str:
    """Build local wrapper URL for YouTube background playback."""
    video_id = _youtube_video_id_from_value(video_value)
    if not video_id:
        return ""
    try:
        start = int(float(start_seconds or 0))
    except Exception:
        start = 0
    if start < 0:
        start = 0
    params = [
        f"video={video_id}",
        f"start={start}",
        f"mute={1 if mute else 0}",
        f"loop={1 if loop else 0}",
    ]
    return "/pom_tesla_report/dashboard/png/youtube_background.html?" + "&".join(params)


def _youtube_canvas_player_url(video_value: Any, quality: Any = "480", fit: str = "cover", start_seconds: Any = 0, loop: bool = True) -> str:
    """Build the internal HA YouTube -> JSMpeg Canvas player URL for dashboard background."""
    raw = str(video_value or "").strip()
    if not raw:
        return ""
    q = str(quality or "480").strip()
    if q not in ("360", "480", "720", "1080_lite", "1080"):
        q = "480"
    player_id = str(abs(hash(raw + "|" + q)) % 100000000)
    try:
        start_seconds = max(0, int(float(start_seconds or 0)))
    except Exception:
        start_seconds = 0
    query = urlencode({
        "url": raw,
        "quality": q,
        "fit": "cover" if str(fit or "cover").strip().lower() != "contain" else "contain",
        "hide": "1",
        "player_id": player_id,
        "loop": "1" if bool(loop) else "0",
        "start": str(start_seconds),
        "producer": "1",
        "nocache": "0",
        "resume": "0",
    })
    return f"/pom_tesla_report/youtube_jsmpeg_player?{query}"


def apply_youtube_driving_background(template: str, options: dict[str, Any]) -> str:
    """Inject Tesla-safe YouTube Canvas/JSMpeg background as a persistent fullscreen iframe.

    Important: this intentionally avoids Lovelace `conditional` cards. Conditional
    cards can destroy/recreate the iframe when HA state updates, which restarts
    the YouTube/JSMpeg player from the beginning. Instead, the iframe stays alive
    and card-mod only toggles visibility based on shift state.
    """
    enabled = bool(options.get(CONF_YOUTUBE_DRIVING_BG_ENABLED))
    player_url = _youtube_canvas_player_url(
        options.get(CONF_YOUTUBE_DRIVING_BG_VIDEO),
        options.get(CONF_YOUTUBE_DRIVING_BG_QUALITY, "480"),
        "cover",
        options.get(CONF_YOUTUBE_DRIVING_BG_START_SECONDS, 0),
        bool(options.get(CONF_YOUTUBE_DRIVING_BG_LOOP, True)),
    )
    if not enabled or not player_url:
        return template

    shift_entity = str(options.get(CONF_ENTITY_SHIFT_STATE) or "sensor.tesla_shift_state_memory").strip()
    active_state_template = (
        "{% set s = states('" + shift_entity + "') | lower %}"
        "{% if s in ['d','drive','driving'] %}"
        "opacity: 1 !important; visibility: visible !important;"
        "{% else %}"
        "opacity: 0 !important; visibility: hidden !important;"
        "{% endif %}"
    )

    iframe_block = f"""
    - type: custom:mod-card
      card_mod:
        style: |
          :host {{
            position: fixed !important;
            inset: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            min-width: 100vw !important;
            min-height: 100vh !important;
            margin: 0 !important;
            padding: 0 !important;
            z-index: 0 !important;
            pointer-events: none !important;
            display: block !important;
            overflow: hidden !important;
            background: #000 !important;
            {active_state_template}
          }}
          ha-card {{
            position: fixed !important;
            inset: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            min-width: 100vw !important;
            min-height: 100vh !important;
            margin: 0 !important;
            padding: 0 !important;
            border: 0 !important;
            border-radius: 0 !important;
            overflow: hidden !important;
            background: #000 !important;
            box-shadow: none !important;
            pointer-events: none !important;
          }}
      card:
        type: iframe
        url: "{player_url}"
        aspect_ratio: 100%
        card_mod:
          style: |
            :host {{
              position: fixed !important;
              inset: 0 !important;
              width: 100vw !important;
              height: 100vh !important;
              z-index: 0 !important;
              pointer-events: none !important;
              overflow: hidden !important;
              background: #000 !important;
            }}
            ha-card {{
              position: fixed !important;
              inset: 0 !important;
              width: 100vw !important;
              height: 100vh !important;
              border: 0 !important;
              border-radius: 0 !important;
              overflow: hidden !important;
              background: #000 !important;
              box-shadow: none !important;
              pointer-events: none !important;
            }}
            iframe {{
              position: fixed !important;
              top: 50% !important;
              left: 50% !important;
              width: 120vw !important;
              height: 120vh !important;
              transform: translate(-50%, -50%) !important;
              border: 0 !important;
              pointer-events: none !important;
            }}
"""

    marker = "# POM_YOUTUBE_DRIVING_BACKGROUND"
    if marker in template:
        return template.replace(marker, marker + "\n" + iframe_block, 1)
    return template.replace("card:\n  type: vertical-stack\n  cards:\n", "card:\n  type: vertical-stack\n  cards:\n" + iframe_block, 1)


def _normalize_bundled_asset_option(value: Any, asset_kind: str) -> str:
    """Normalize old/stale package asset paths to the current served URL.

    Users can still provide custom /local or external URLs. This only converts
    previous installer defaults, filesystem-style package paths, and the old
    /assets prefix into the current /pom_tesla_report/dashboard/png URL.
    """
    raw = str(value or "").strip().replace("\\", "/")
    if not raw:
        return raw

    bundled = {
        "parked": BUNDLED_IMAGE_PARKED,
        "charging": BUNDLED_IMAGE_CHARGING,
        "driving": BUNDLED_IMAGE_DRIVING,
    }[asset_kind]

    lowered = raw.lower().split("?", 1)[0]
    filename_map = {
        "parked": "tesla.png",
        "charging": "teslacharging.gif",
        "driving": "tesladriving.gif",
    }
    filename = filename_map[asset_kind]

    stale_exact_values = {
        f"/pom_tesla_report/dashboard/assets/{filename}",
        f"/pom_tesla_report/dashboard/png/{filename}",
        f"/local/png/{filename}",
        f"/local/png/tesla/{filename}",
    }
    if lowered in stale_exact_values:
        return bundled

    # A common mistaken input is a filesystem path such as
    # /config/custom_components/pom_tesla_report/dashboard/png/tesla.png
    # or config/pom_tesla_report/dashboard/png/tesla.png. Browsers cannot
    # load those paths, so map them back to the registered static URL.
    if "pom_tesla_report/dashboard" in lowered and lowered.endswith("/" + filename):
        return bundled

    return raw


def _cache_bust_bundled_asset_url(url: str) -> str:
    """Append a rebuild-time cache buster to bundled static image URLs.

    This prevents the browser/HA frontend from showing an older placeholder image
    after the user replaces files under custom_components/.../png.
    Custom /local or external URLs are intentionally left untouched.
    """
    url = str(url or "").strip()
    if not url:
        return url
    base_url = url.split("?", 1)[0]
    if not base_url.startswith(STATIC_ASSET_URL_PATH + "/") and not base_url.startswith("/pom_tesla_report/dashboard/assets/"):
        return url
    filename = base_url.rsplit("/", 1)[-1]
    source_path = Path(__file__).resolve().parent / "png" / filename
    try:
        version = int(source_path.stat().st_mtime)
    except OSError:
        version = int(time.time())
    return f"{base_url}?v={version}"


# These markers identify complete button-card blocks in the original template.
# Blocks are removed before entity replacement, so the markers intentionally use
# the original/default entity IDs and unique icon strings.
SIDEBAR_VISIBILITY_MARKERS = {
    CONF_SHOW_FLASH_LIGHTS: "button.pom_flash_lights_2",
    CONF_SHOW_SENTRY: "switch.pom_sentry_mode_2",
    CONF_SHOW_HONK: "button.pom_honk_horn_2",
    CONF_SHOW_FART: "button.pom_play_fart_2",
    CONF_SHOW_WINDOWS: "binary_sensor.tesla_windows_open",
    CONF_SHOW_DOORS: "binary_sensor.tesla_doors_open",
    CONF_SHOW_HOME_AUTOMATION: "input_boolean.zone_leave_house_activate",
    CONF_SHOW_MANUAL_TRACKING: "input_boolean.tesla_automation_speed_sections",
}

BOTTOM_VISIBILITY_MARKERS = {
    CONF_SHOW_BOTTOM_RANGE: "sensor.tesla_rated_range",
    CONF_SHOW_BOTTOM_ENERGY: "sensor.pom_energy_remaining",
    CONF_SHOW_BOTTOM_INSIDE_TEMP: "sensor.tesla_inside_temp",
    CONF_SHOW_BOTTOM_BATTERY_TEMP: "sensor.pom_pil_modulu_maksimum_sicakligi",
    CONF_SHOW_BOTTOM_LOCATION: "mdi:map-marker-radius-outline",
    CONF_SHOW_BOTTOM_MAP_TOGGLE: "entity: input_boolean.tesla_interactive_map",
    CONF_SHOW_BOTTOM_CONTROLS: "entity: input_boolean.tesla_controls",
    CONF_SHOW_BOTTOM_PERSON_TOGGLE: "mdi:account-convert",
    CONF_SHOW_BOTTOM_PERSON_CARDS: "mdi:smart-card",
    CONF_SHOW_BOTTOM_CHARGING: "binary_sensor.pom_charging",
}

SIDEBAR_VISIBILITY_BLOCK_KEYS = {
    CONF_SHOW_FLASH_LIGHTS: "sidebar_flash_lights",
    CONF_SHOW_SENTRY: "sidebar_sentry",
    CONF_SHOW_HONK: "sidebar_honk",
    CONF_SHOW_FART: "sidebar_fart",
    CONF_SHOW_WINDOWS: "sidebar_windows",
    CONF_SHOW_DOORS: "sidebar_doors",
    CONF_SHOW_HOME_AUTOMATION: "sidebar_home_automation",
    CONF_SHOW_MANUAL_TRACKING: "sidebar_manual_tracking",
}

BOTTOM_VISIBILITY_BLOCK_KEYS = {
    CONF_SHOW_BOTTOM_RANGE: "bottom_range",
    CONF_SHOW_BOTTOM_ENERGY: "bottom_energy",
    CONF_SHOW_BOTTOM_INSIDE_TEMP: "bottom_inside_temp",
    CONF_SHOW_BOTTOM_BATTERY_TEMP: "bottom_battery_temp",
    CONF_SHOW_BOTTOM_LOCATION: "bottom_location",
    CONF_SHOW_BOTTOM_MAP_TOGGLE: "bottom_map_toggle",
    CONF_SHOW_BOTTOM_CONTROLS: "bottom_controls",
    CONF_SHOW_BOTTOM_PERSON_TOGGLE: "bottom_person_toggle",
    CONF_SHOW_BOTTOM_PERSON_CARDS: "bottom_person_cards",
    CONF_SHOW_BOTTOM_CHARGING: "bottom_charging",
}


def merged_options(options: dict[str, Any] | None) -> dict[str, Any]:
    """Merge options with defaults and migrate old built-in helpers to auto-created switches."""
    data = dict(DEFAULT_OPTIONS)
    if options:
        for key, value in options.items():
            if value is not None:
                if isinstance(value, str):
                    value = value.strip()
                if (
                    value != ""
                    or str(key).startswith("entity_")
                    or str(key).startswith("charge_")
                    or str(key) in SIDEBAR_SLOT_KEYS
                ):
                    data[key] = value

    # Dashboard-internal helpers are system switches owned by this integration.
    # They are not user-selectable anymore because they are core building blocks
    # of the generated dashboard. Previous input_boolean values are migrated to
    # defaults. If Home Assistant has assigned a suffix such as _2, runtime
    # resolution can preserve that switch entity ID by storing it in options.
    helper_defaults = {
        CONF_HELPER_MAP: AUTO_HELPER_MAP,
        CONF_HELPER_PERSON_CARDS: AUTO_HELPER_PERSON_CARDS,
        CONF_HELPER_INTERACTIVE_MAP: AUTO_HELPER_INTERACTIVE_MAP,
        CONF_HELPER_CONTROLS: AUTO_HELPER_CONTROLS,
        CONF_HELPER_CHARGE_POPUP: AUTO_HELPER_CHARGE_POPUP,
        CONF_HELPER_ADDRESS_POPUP: AUTO_HELPER_ADDRESS_POPUP,
        CONF_HELPER_PERSON_TRACK_LIST_POPUP: AUTO_HELPER_PERSON_TRACK_LIST_POPUP,
        CONF_HELPER_PERSON_TRACK_POPUP_1: AUTO_HELPER_PERSON_TRACK_POPUP_1,
        CONF_HELPER_PERSON_TRACK_POPUP_2: AUTO_HELPER_PERSON_TRACK_POPUP_2,
        CONF_HELPER_PERSON_TRACK_POPUP_3: AUTO_HELPER_PERSON_TRACK_POPUP_3,
        CONF_HELPER_FULLSCREEN: AUTO_HELPER_FULLSCREEN,
    }
    for helper_key, default_entity_id in helper_defaults.items():
        current = str(data.get(helper_key) or "").strip()
        # Only keep the exact expected helper or HA's suffixed version of that
        # same helper. Earlier alpha builds exposed all helper selectors and it
        # was easy to accidentally store helper_interactive_map as
        # switch.pom_tesla_dashboard_map. That makes the bottom map icon perform
        # the same action as the speed gauge. Reject cross-wired helper IDs here.
        if not (current == default_entity_id or current.startswith(default_entity_id + "_")):
            data[helper_key] = default_entity_id

    # Person map defaults must survive old option forms that saved blank entity fields.
    for person_key, default_person in {
        CONF_ENTITY_PERSON_TESLA: "person.tesla",
        CONF_ENTITY_PERSON_2: "person.ali",
        CONF_ENTITY_PERSON_3: "person.cavidan",
    }.items():
        if not str(data.get(person_key) or "").strip():
            data[person_key] = default_person

    for hours_key, default_hours in {
        CONF_TESLA_MAP_HOURS_TO_SHOW: 1,
        CONF_PERSON_MAP_HOURS_TO_SHOW: 0,
    }.items():
        try:
            data[hours_key] = max(0, min(24, int(float(data.get(hours_key, default_hours)))))
        except (TypeError, ValueError):
            data[hours_key] = default_hours

    if str(data.get(CONF_MAP_THEME_MODE) or DEFAULT_MAP_THEME_MODE).strip().lower() not in MAP_THEME_MODES:
        data[CONF_MAP_THEME_MODE] = DEFAULT_MAP_THEME_MODE
    else:
        data[CONF_MAP_THEME_MODE] = str(data.get(CONF_MAP_THEME_MODE) or DEFAULT_MAP_THEME_MODE).strip().lower()

    # Middle bottom bar slots are configured by type. Keep old per-item
    # visibility flags true so older saved options cannot remove the slot blocks
    # before the slot renderer replaces them. Users now hide a middle slot by
    # choosing the "empty" slot type.
    data[CONF_SHOW_BOTTOM_ENERGY] = True
    data[CONF_SHOW_BOTTOM_INSIDE_TEMP] = True
    data[CONF_SHOW_BOTTOM_BATTERY_TEMP] = True

    for slot_key, default_slot in {
        CONF_BOTTOM_SLOT_1: "energy_remaining",
        CONF_BOTTOM_SLOT_2: "inside_temp",
        CONF_BOTTOM_SLOT_3: "battery_temp",
    }.items():
        if str(data.get(slot_key) or "") not in BOTTOM_SLOT_TYPES:
            data[slot_key] = default_slot

    for slot_key, default_slot in {
        CONF_TOP_LEFT_SLOT_1: "elevation",
        CONF_TOP_LEFT_SLOT_2: "power",
        CONF_TOP_RIGHT_SLOT_1: "battery_level",
        CONF_TOP_RIGHT_SLOT_2: "est_range",
    }.items():
        if str(data.get(slot_key) or "") not in TOP_SLOT_TYPES:
            data[slot_key] = default_slot

    if str(data.get(CONF_TOP_CENTER_SLOT) or "") not in CENTER_GAUGE_SLOT_TYPES:
        data[CONF_TOP_CENTER_SLOT] = "speed"

    # The location pill is a core part of the Tesla dashboard. It stays visible;
    # users choose what it displays instead of removing it.
    data[CONF_SHOW_BOTTOM_LOCATION] = True
    if str(data.get(CONF_LOCATION_DISPLAY_MODE) or "") not in LOCATION_DISPLAY_MODES:
        data[CONF_LOCATION_DISPLAY_MODE] = "auto_short"
    try:
        data[CONF_LOCATION_UPDATE_INTERVAL_MINUTES] = max(5, int(data.get(CONF_LOCATION_UPDATE_INTERVAL_MINUTES) or DEFAULT_LOCATION_UPDATE_INTERVAL_MINUTES))
    except (TypeError, ValueError):
        data[CONF_LOCATION_UPDATE_INTERVAL_MINUTES] = DEFAULT_LOCATION_UPDATE_INTERVAL_MINUTES

    # Normalize stale package-local image paths from previous builds.
    # Custom /local or external URLs are preserved unless they clearly point to
    # this integration's bundled files via an invalid filesystem-style path or
    # old /assets prefix.
    data[CONF_IMAGE_PARKED] = _normalize_bundled_asset_option(data.get(CONF_IMAGE_PARKED), "parked")
    data[CONF_IMAGE_CHARGING] = _normalize_bundled_asset_option(data.get(CONF_IMAGE_CHARGING), "charging")
    data[CONF_IMAGE_DRIVING] = _normalize_bundled_asset_option(data.get(CONF_IMAGE_DRIVING), "driving")

    return data



REPORT_TO_DASHBOARD_ENTITY_MAP = {
    "speed_entity": CONF_ENTITY_SPEED,
    "odometer_entity": CONF_ENTITY_ODOMETER,
    "battery_level_entity": CONF_ENTITY_BATTERY_LEVEL,
    "energy_remaining_entity": CONF_ENTITY_ENERGY_REMAINING,
    "elevation_entity": CONF_ENTITY_ELEVATION,
    "charging_entity": CONF_ENTITY_CHARGING,
    "charge_energy_added_entity": CONF_CHARGE_ENERGY_ADDED,
    "shift_state_entity": CONF_ENTITY_SHIFT_STATE,
    "trip_map_tracker_entity": CONF_ENTITY_LOCATION_SENSOR,
    "ai_main_tesla_entity": CONF_ENTITY_LOCATION_SENSOR,
}

VEHICLE_ROLE_TO_DASHBOARD_ENTITY_MAP = {
    "speed": CONF_ENTITY_SPEED,
    "odometer": CONF_ENTITY_ODOMETER,
    "battery_level": CONF_ENTITY_BATTERY_LEVEL,
    "battery_range": CONF_ENTITY_EST_RANGE,
    "energy_remaining": CONF_ENTITY_ENERGY_REMAINING,
    "elevation": CONF_ENTITY_ELEVATION,
    "charging_state": CONF_ENTITY_CHARGING,
    "charge_energy_added": CONF_CHARGE_ENERGY_ADDED,
    "charger_power": CONF_CHARGE_CHARGER_POWER,
    "shift_state": CONF_ENTITY_SHIFT_STATE,
    "inside_temperature": CONF_ENTITY_INSIDE_TEMP,
    "outside_temperature": CONF_ENTITY_OUTSIDE_TEMP,
    # Battery temperature is intentionally not auto-imported from the
    # Vehicle Entity Manager. Auto-discovery can confuse battery heater
    # on/off entities with a numeric battery temperature sensor. Use the
    # explicit dashboard setting or the safe default instead.
    "location_tracker": CONF_ENTITY_LOCATION_SENSOR,
    "vehicle_state": CONF_ENTITY_PLUGGED_IN,
}



BATTERY_TEMP_CANDIDATES = (
    "sensor.pom_pil_modulu_maksimum_sicakligi",
    "sensor.pom_pil_modulu_maksimum_sicakligi",
)

def _preferred_battery_temperature_entity() -> str:
    """Return the preferred default battery module temperature entity.

    Turkish Tesla/POM installs expose the valid sensor as
    sensor.pom_pil_modulu_maksimum_sicakligi. Older alpha builds used
    sensor.pom_battery_module_temperature_max, which may not exist on the
    user's system and caused the selector to look invalid after restart.
    """
    return BATTERY_TEMP_CANDIDATES[0]


def _is_bad_battery_temperature_entity(value: Any) -> bool:
    """Return true when a battery temperature option is actually a heater entity.

    Older alpha builds could save auto-discovered battery-heater entities under
    entity_battery_temp. Never keep those as the temperature source across
    restarts.
    """
    entity_id = str(value or "").strip().lower()
    if not entity_id:
        return False
    if entity_id == "sensor.pom_battery_module_temperature_max":
        # Legacy alpha fallback. On the target system the real entity is the
        # Turkish POM sensor; keeping this old default after restart makes the
        # selector invalid and the bottom bar shows the wrong thing.
        return True
    if "heater" in entity_id or "isitici" in entity_id or "ısıtıcı" in entity_id:
        return True
    if entity_id.startswith(("binary_sensor.", "switch.", "button.", "input_boolean.")):
        return True
    return False

def merged_options_from_report_config(config: dict[str, Any] | None) -> dict[str, Any]:
    """Build dashboard options from the main POM Tesla Report config/options.

    Dashboard-specific keys stored in the same options dict still win. Missing
    dashboard fields are auto-filled from the report entity selections and the
    Vehicle Entity Manager map.
    """
    raw = dict(config or {})
    options = merged_options(raw)

    def set_if_present(report_key: str, dashboard_key: str) -> None:
        # Dashboard-specific override wins over inherited POM report fields.
        if str(raw.get(dashboard_key) or "").strip():
            return
        value = str(raw.get(report_key) or "").strip()
        if value:
            options[dashboard_key] = value

    for report_key, dashboard_key in REPORT_TO_DASHBOARD_ENTITY_MAP.items():
        set_if_present(report_key, dashboard_key)

    vehicle_map = raw.get("vehicle_entity_map")
    if isinstance(vehicle_map, list):
        for item in vehicle_map:
            if not isinstance(item, dict):
                continue
            entity_id = str(item.get("entity_id") or "").strip()
            role = str(item.get("role") or "").strip()
            dashboard_key = VEHICLE_ROLE_TO_DASHBOARD_ENTITY_MAP.get(role)
            if entity_id and dashboard_key and not str(raw.get(dashboard_key) or "").strip():
                options[dashboard_key] = entity_id

    # Keep battery temperature stable across restarts. If the user explicitly
    # saved entity_battery_temp, that value wins. If not, use the safe default
    # and do not let auto-discovered vehicle roles replace it with a heater
    # switch/binary_sensor such as "Pil Isıtıcısı".
    battery_temp_value = str(raw.get(CONF_ENTITY_BATTERY_TEMP) or "").strip()
    if not battery_temp_value or _is_bad_battery_temperature_entity(battery_temp_value):
        options[CONF_ENTITY_BATTERY_TEMP] = DEFAULT_OPTIONS.get(
            CONF_ENTITY_BATTERY_TEMP,
            _preferred_battery_temperature_entity(),
        )

    # Charging popup should inherit core report values whenever available.
    if str(raw.get("battery_level_entity") or "").strip():
        options[CONF_CHARGE_BATTERY_LEVEL] = str(raw.get("battery_level_entity")).strip()
    if str(raw.get("charge_energy_added_entity") or "").strip():
        options[CONF_CHARGE_ENERGY_ADDED] = str(raw.get("charge_energy_added_entity")).strip()

    # App panel Dashboard Entity Manager is Flow-independent and should win over
    # legacy dashboard entity keys if present.
    panel_dashboard_map = raw.get("panel_dashboard_entity_map")
    if isinstance(panel_dashboard_map, list):
        for item in panel_dashboard_map:
            if not isinstance(item, dict):
                continue
            role = str(item.get("role") or "").strip()
            entity_id = str(item.get("entity_id") or "").strip()
            option_key = PANEL_DASHBOARD_ROLE_TO_OPTION.get(role)
            if option_key and entity_id and not _is_dashboard_self_output_entity(entity_id):
                options[option_key] = entity_id
                # Battery heater is used by the bottom-bar battery_heater slot.
                # Older paths/templates may still read entity_battery_temp, so
                # mirror the panel-selected heater entity there as a compatibility
                # bridge until all dashboard templates use entity_battery_heater.
                if role == "dashboard_sidebar_battery_module_temp":
                    options["entity_battery_heater"] = entity_id
                    options["entity_battery_temp"] = entity_id
                if role in {"dashboard_person_track_1", "dashboard_person_track_2", "dashboard_person_track_3"}:
                    suffix = role.rsplit("_", 1)[-1]
                    label = str(item.get("name") or item.get("label") or "").strip()
                    options[f"person_track_{suffix}_enabled"] = True
                    if label:
                        options[f"person_track_{suffix}_name"] = label
                if role in {"dashboard_home_entity_1", "dashboard_home_entity_2"}:
                    suffix = role.rsplit("_", 1)[-1]
                    icon = str(item.get("icon") or "").strip()
                    if icon:
                        options[f"entity_home_entity_{suffix}_icon"] = icon

    # Safety guard: dashboard output sensors are derived values, not source entities.
    # A stored self-reference such as
    # sensor.pom_tesla_dashboard_person_track_1 -> person_track_1_entity
    # creates a state-update feedback loop and can OOM small Home Assistant VMs.
    _sanitize_person_track_options(options)

    # Keep placeholder/static URLs normalized for the new main integration URL.
    options[CONF_IMAGE_PARKED] = _normalize_bundled_asset_option(options.get(CONF_IMAGE_PARKED), "parked")
    options[CONF_IMAGE_CHARGING] = _normalize_bundled_asset_option(options.get(CONF_IMAGE_CHARGING), "charging")
    options[CONF_IMAGE_DRIVING] = _normalize_bundled_asset_option(options.get(CONF_IMAGE_DRIVING), "driving")
    options[CONF_YOUTUBE_DRIVING_BG_ENABLED] = bool(options.get(CONF_YOUTUBE_DRIVING_BG_ENABLED, False))
    options[CONF_YOUTUBE_DRIVING_BG_VIDEO] = str(options.get(CONF_YOUTUBE_DRIVING_BG_VIDEO, "") or "").strip()
    try:
        options[CONF_YOUTUBE_DRIVING_BG_START_SECONDS] = max(0, int(float(options.get(CONF_YOUTUBE_DRIVING_BG_START_SECONDS, 0) or 0)))
    except Exception:
        options[CONF_YOUTUBE_DRIVING_BG_START_SECONDS] = 0
    options[CONF_YOUTUBE_DRIVING_BG_MUTE] = bool(options.get(CONF_YOUTUBE_DRIVING_BG_MUTE, True))
    options[CONF_YOUTUBE_DRIVING_BG_LOOP] = bool(options.get(CONF_YOUTUBE_DRIVING_BG_LOOP, True))
    return options

def dashboard_path(hass: HomeAssistant, options: dict[str, Any]) -> Path:
    """Return dashboard yaml path under /config."""
    filename = str(options.get(CONF_DASHBOARD_FILENAME) or DEFAULT_DASHBOARD_FILENAME).strip()
    if not filename.endswith((".yaml", ".yml")):
        filename += ".yaml"
    filename = filename.replace("/", "_").replace("\\", "_")
    return Path(hass.config.path(filename))


def lovelace_yaml_block(options: dict[str, Any]) -> str:
    """Return Lovelace YAML block to add manually."""
    title = str(options.get(CONF_DASHBOARD_TITLE) or DEFAULT_DASHBOARD_TITLE).strip() or DEFAULT_DASHBOARD_TITLE
    filename = str(options.get(CONF_DASHBOARD_FILENAME) or DEFAULT_DASHBOARD_FILENAME).strip() or DEFAULT_DASHBOARD_FILENAME
    if not filename.endswith((".yaml", ".yml")):
        filename += ".yaml"
    return (
        "lovelace:\n"
        "  dashboards:\n"
        "    tesla-dashboard:\n"
        "      mode: yaml\n"
        f"      title: {title}\n"
        "      icon: mdi:car-electric\n"
        "      show_in_sidebar: true\n"
        f"      filename: {filename}\n"
    )


def _replace_entity_token(text: str, old: str, new: str) -> str:
    if not new or new == old:
        return text
    # Exact entity-id replacement. Avoid turning button.foo_2 into button.bar_2 accidentally.
    pattern = r"(?<![A-Za-z0-9_\.])" + re.escape(old) + r"(?![A-Za-z0-9_])"
    return re.sub(pattern, new, text)


def _remove_button_card_block_by_marker(text: str, marker: str) -> str:
    """Remove the complete custom:button-card block containing marker."""
    return _remove_button_card_block_by_marker_in_region(text, marker, 0, len(text))


def _remove_button_card_block_by_marker_in_region(text: str, marker: str, region_start: int, region_end: int) -> str:
    """Remove the complete custom:button-card block containing marker inside a safe region.

    The dashboard template contains repeated entity ids in CSS/Jinja conditions.
    Searching the whole template can remove the wrong block. This function first
    limits the search to the known sidebar/bottom-bar region and then removes only
    the nearest button-card block inside that region.
    """
    if not marker:
        return text

    region_start = max(0, int(region_start or 0))
    region_end = min(len(text), int(region_end or len(text)))
    if region_end <= region_start:
        return text

    region = text[region_start:region_end]
    relative_marker = region.find(marker)
    if relative_marker < 0:
        return text

    before_marker = region[:relative_marker]
    relative_start = before_marker.rfind("- type: custom:button-card")
    if relative_start < 0:
        return text

    # Convert relative line start to absolute character index.
    absolute_start = region_start + relative_start
    line_start = text.rfind("\n", 0, absolute_start) + 1
    if line_start >= 0:
        absolute_start = line_start

    first_line_end = text.find("\n", absolute_start)
    if first_line_end < 0:
        first_line_end = len(text)
    first_line = text[absolute_start:first_line_end]
    start_indent = len(first_line) - len(first_line.lstrip())

    # Find next sibling card at the same indentation, but never beyond region_end.
    end_index = region_end
    pos = first_line_end + 1
    while pos < region_end:
        next_line_end = text.find("\n", pos)
        if next_line_end < 0:
            next_line_end = len(text)
        line = text[pos:next_line_end]
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        if indent == start_indent and stripped.startswith("- type:"):
            end_index = pos
            break
        pos = next_line_end + 1

    return text[:absolute_start] + text[end_index:]


def _find_region(text: str, start_marker: str, end_marker: str | None = None) -> tuple[int, int]:
    """Return a safe character region inside template."""
    start = text.find(start_marker)
    if start < 0:
        return 0, len(text)
    end = len(text)
    if end_marker:
        candidate = text.find(end_marker, start + len(start_marker))
        if candidate > start:
            end = candidate
    return start, end


def _remove_marked_block(text: str, block_key: str) -> str:
    """Remove a dashboard block using explicit YAML comment markers.

    This is safer than regex/entity based deletion because some helper entities are
    used in multiple places in the dashboard. The template carries markers around
    each removable block, and only that exact marked range is removed.
    """
    start_marker = f"# POM_BLOCK_START {block_key}"
    end_marker = f"# POM_BLOCK_END {block_key}"
    start = text.find(start_marker)
    if start < 0:
        return text
    start = text.rfind("\n", 0, start) + 1
    end = text.find(end_marker, start)
    if end < 0:
        return text
    end_line = text.find("\n", end)
    if end_line < 0:
        end_line = len(text)
    else:
        end_line += 1
    return text[:start] + text[end_line:]


def _replace_marked_block(text: str, block_key: str, replacement: str) -> str:
    """Replace a dashboard block using explicit YAML comment markers."""
    start_marker = f"# POM_BLOCK_START {block_key}"
    end_marker = f"# POM_BLOCK_END {block_key}"
    start = text.find(start_marker)
    if start < 0:
        return text
    start = text.rfind("\n", 0, start) + 1
    end = text.find(end_marker, start)
    if end < 0:
        return text
    end_line = text.find("\n", end)
    if end_line < 0:
        end_line = len(text)
    else:
        end_line += 1
    if replacement and not replacement.endswith("\n"):
        replacement += "\n"
    return text[:start] + replacement + text[end_line:]


def _dashboard_scale_option(options: dict[str, Any], key: str, default: float = 1.0, minimum: float = 0.7, maximum: float = 1.6) -> float:
    """Return a bounded dashboard visual scale option."""
    try:
        value = float(options.get(key, default))
    except Exception:
        value = default
    if value < minimum:
        return minimum
    if value > maximum:
        return maximum
    return value



def _dashboard_map_theme_mode(options: dict[str, Any]) -> str:
    """Return the configured dashboard map theme mode."""
    mode = str(options.get(CONF_MAP_THEME_MODE) or DEFAULT_MAP_THEME_MODE).strip().lower()
    return mode if mode in MAP_THEME_MODES else DEFAULT_MAP_THEME_MODE


def _dashboard_map_is_light(options: dict[str, Any]) -> bool:
    """Return true when the dashboard map is generated in light mode."""
    return _dashboard_map_theme_mode(options) == MAP_THEME_LIGHT


def _map_overlay_template_value(options: dict[str, Any], on_value: str, off_value: str) -> str:
    """Return a Jinja value that only changes while dashboard map overlay is open."""
    helper_map = str(options.get(CONF_HELPER_MAP) or AUTO_HELPER_MAP).strip()
    return "{% if is_state('" + helper_map + "', 'on') %}" + on_value + "{% else %}" + off_value + "{% endif %}"


def _top_color_for_map(options: dict[str, Any], fallback: str, light_value: str) -> str:
    """Return static top-area colors for the generated dashboard map theme.

    Earlier alpha243/244 builds returned inline Jinja expressions for light mode.
    That is safe inside card_mod CSS blocks but not inside button-card style lists,
    where YAML can fail with "% cannot start any token". Keep this static per
    generated dashboard theme to make the YAML valid and predictable.
    """
    if not _dashboard_map_is_light(options):
        return fallback
    return light_value


def _top_text_shadow_for_map(options: dict[str, Any]) -> str:
    """Return subtle readable text shadow for the selected map mode."""
    if not _dashboard_map_is_light(options):
        return "0 4px 18px rgba(0,0,0,0.42)"
    return "0 1px 0 rgba(255,255,255,0.70), 0 10px 24px rgba(15,23,42,0.16)"


def _top_center_inner_background(options: dict[str, Any]) -> str:
    """Return center gauge inner background that stays decorative on both map modes."""
    dark_bg = "rgba(8,10,18,0.88)"
    if not _dashboard_map_is_light(options):
        return dark_bg
    return "linear-gradient(145deg, rgba(255,255,255,0.86), rgba(226,232,240,0.66))"


def _top_center_inner_border(options: dict[str, Any]) -> str:
    """Return center gauge inner border for the selected map mode."""
    dark_border = "rgba(255,255,255,0.08)"
    if not _dashboard_map_is_light(options):
        return dark_border
    return "rgba(14,116,144,0.20)"


def _top_center_inner_shadow(options: dict[str, Any]) -> str:
    """Return center gauge inner shadow for the selected map mode."""
    dark_shadow = "inset 0 0 30px rgba(0,0,0,0.42)"
    if not _dashboard_map_is_light(options):
        return dark_shadow
    return "inset 0 0 24px rgba(255,255,255,0.42), 0 16px 42px rgba(15,23,42,0.18)"


def _dashboard_language(options: dict[str, Any]) -> str:
    """Return dashboard language from merged options without affecting calculations."""
    raw = str((options or {}).get("app_language") or (options or {}).get("report_language") or "tr").strip().lower()
    return "en" if raw.startswith("en") else "tr"


def _top_label(options: dict[str, Any], tr: str, en: str) -> str:
    """Return the top-area display label in the selected UI language."""
    return en if _dashboard_language(options) == "en" else tr


def _top_slot_config(slot_type: str, options: dict[str, Any]) -> dict[str, str] | None:
    """Return render config for one top gauge/header slot."""
    slot_type = str(slot_type or "empty")
    configs: dict[str, dict[str, str]] = {
        "elevation": {
            "entity": str(options.get(CONF_ENTITY_ELEVATION) or "sensor.tesla_elevation").strip(),
            "label": _top_label(options, "EĞİM", "ELEVATION"),
            "value_js": """const v = Number(states['{entity}']?.state);
return isNaN(v) ? '-' : `${v.toFixed(1)} M`;""",
            "color": "rgba(255,255,255,0.78)",
        },
        "power": {
            "entity": str(options.get(CONF_ENTITY_POWER) or "sensor.tesla_power").strip(),
            "label": "POWER",
            "value_js": """const v = Number(states['{entity}']?.state);
return isNaN(v) ? '-' : `${v.toFixed(1)}kW`;""",
            "color": "rgba(255,255,255,0.78)",
        },
        "speed": {
            "entity": str(options.get(CONF_ENTITY_SPEED) or "sensor.tesla_speed").strip(),
            "label": "SPEED",
            "value_js": """const v = Number(states['{entity}']?.state);
return isNaN(v) ? '-' : `${Math.round(v)}`;""",
            "color": "rgba(255,255,255,0.78)",
        },
        "battery_level": {
            "entity": str(options.get(CONF_ENTITY_BATTERY_LEVEL) or "sensor.tesla_battery_level").strip(),
            "label": _top_label(options, "BATARYA", "BATTERY"),
            "value_js": """const v = Number(states['{entity}']?.state);
return isNaN(v) ? '-' : `${Math.round(v)}%`;""",
            "color": "#ffffff",
        },
        "est_range": {
            "entity": str(options.get(CONF_ENTITY_EST_RANGE) or "sensor.tesla_est_range").strip(),
            "label": _top_label(options, "MENZİL", "RANGE"),
            "value_js": """const v = Number(states['{entity}']?.state);
return isNaN(v) ? '-' : `${v.toFixed(1)} km`;""",
            "color": "#18af85",
        },
        "rated_range": {
            "entity": str(options.get(CONF_ENTITY_RATED_RANGE) or "sensor.tesla_rated_range").strip(),
            "label": "RANGE",
            "value_js": """const v = Number(states['{entity}']?.state);
return isNaN(v) ? '-' : `${Math.round(v)} km`;""",
            "color": "#18af85",
        },
        "energy_remaining": {
            "entity": str(options.get(CONF_ENTITY_ENERGY_REMAINING) or "sensor.pom_energy_remaining").strip(),
            "label": _top_label(options, "ENERJİ", "ENERGY"),
            "value_js": """const v = Number(states['{entity}']?.state);
return isNaN(v) ? '-' : `${v.toFixed(1)} kWh`;""",
            "color": "#facc15",
        },
        "inside_temp": {
            "entity": str(options.get(CONF_ENTITY_INSIDE_TEMP) or "sensor.tesla_inside_temp").strip(),
            "label": _top_label(options, "İÇ ISI", "INSIDE TEMP"),
            "value_js": """const v = Number(states['{entity}']?.state);
return isNaN(v) ? '-' : `${v.toFixed(1)}°`;""",
            "color": "#4ade80",
        },
        "outside_temp": {
            "entity": str(options.get(CONF_ENTITY_OUTSIDE_TEMP) or "sensor.tesla_outside_temp").strip(),
            "label": _top_label(options, "DIŞ ISI", "OUTSIDE TEMP"),
            "value_js": """const v = Number(states['{entity}']?.state);
return isNaN(v) ? '-' : `${v.toFixed(1)}°`;""",
            "color": "#38bdf8",
        },
        "battery_temp": {
            "entity": str(options.get(CONF_ENTITY_BATTERY_TEMP) or  _preferred_battery_temperature_entity()).strip(),
            "label": _top_label(options, "PİL ISI", "BATTERY TEMP"),
            "value_js": """const raw = states['{entity}']?.state;
if (raw === undefined || raw === null || raw === '' || ['unknown','unavailable','none'].includes(String(raw).toLowerCase())) return '-';
const v = Number(String(raw).replace(',', '.'));
if (isNaN(v)) return String(raw);
return `${v.toFixed(1)}°`;""",
            "color": "#facc15",
        },
        "odometer": {
            "entity": str(options.get(CONF_ENTITY_ODOMETER) or "sensor.tesla_odometer").strip(),
            "label": _top_label(options, "KM", "ODOMETER"),
            "value_js": """const v = Number(states['{entity}']?.state);
return isNaN(v) ? '-' : `${Math.round(v).toLocaleString()} km`;""",
            "color": "#d6eaff",
        },
        "battery_heater": {
            "entity": str(options.get(CONF_ENTITY_BATTERY_HEATER) or options.get(CONF_ENTITY_BATTERY_TEMP) or "binary_sensor.tesla_battery_heater").strip(),
            "label": _top_label(options, "PİL ISITICI", "BATTERY HEATER"),
            "value_js": """const raw = String(states['{entity}']?.state ?? '').toLowerCase();
if (!raw || raw === 'unknown' || raw === 'unavailable' || raw === 'none') return '-';
const on = ['on', 'true', '1', 'heating', 'heat', 'active'].includes(raw);
return on ? 'On' : 'Off';""",
            "color": "#facc15",
        },
    }
    cfg = configs.get(slot_type)
    if not cfg:
        return None
    # Fill entity placeholder inside the JS snippet after the final entity has been resolved.
    cfg = dict(cfg)
    cfg["value_js"] = cfg["value_js"].replace("{entity}", cfg["entity"])
    return cfg


def _render_top_pair_card(block_key: str, slot_1: str, slot_2: str, options: dict[str, Any], *, side: str) -> str:
    """Render left/right top gauge text pair card."""
    cfg1 = _top_slot_config(slot_1, options)
    cfg2 = _top_slot_config(slot_2, options)

    def render_js_value(cfg: dict[str, str] | None, default: str = "-") -> str:
        if not cfg:
            return f"return `{default}`;"
        return cfg["value_js"]

    def render_label(cfg: dict[str, str] | None) -> str:
        return cfg["label"] if cfg else ""

    value1_js = _indent_js(render_js_value(cfg1), "                      ")
    value2_js = _indent_js(render_js_value(cfg2), "                      ")
    label1 = render_label(cfg1)
    label2 = render_label(cfg2)
    color1 = cfg1.get("color", "rgba(255,255,255,0.78)") if cfg1 else "rgba(255,255,255,0.25)"
    color2 = cfg2.get("color", "rgba(255,255,255,0.78)") if cfg2 else "rgba(255,255,255,0.25)"
    label_color = _top_color_for_map(options, "rgba(255,255,255,0.28)", "rgba(30,41,59,0.56)")
    color1 = _top_color_for_map(options, color1, "#2563eb")
    color2 = _top_color_for_map(options, color2, "#0f766e")
    text_shadow = _top_text_shadow_for_map(options)
    align = "right" if side == "left" else "left"
    justify = "end" if side == "left" else "start"
    padding = "padding-right: 22px" if side == "left" else "padding-left: 28px"
    width = "250px" if side == "left" else "260px"
    wrap = "left-wrap" if side == "left" else "right-wrap"
    global_scale = _dashboard_scale_option(options, CONF_TOP_FONT_SCALE)
    group_key = CONF_TOP_LEFT_FONT_SCALE if side == "left" else CONF_TOP_RIGHT_FONT_SCALE
    group_scale = _dashboard_scale_option(options, group_key)
    scale = round(global_scale * group_scale, 3)
    label_size = round(17 * scale, 2)
    value_size = round((52 if side == "right" else 26) * scale, 2)
    small_size = round((20 if side == "right" else 26) * scale, 2)
    return f"""              # POM_BLOCK_START {block_key}
              - type: custom:button-card
                show_icon: false
                show_name: false
                show_state: false
                tap_action:
                  action: none
                custom_fields:
                  info: |
                    [[[
                      const value1 = (() => {{
{value1_js}
                      }})();
                      const value2 = (() => {{
{value2_js}
                      }})();
                      return `
                        <div class=\"{wrap}\">
                          <div class=\"label\">{label1}</div>
                          <div class=\"value primary\">${{value1}}</div>
                          <div class=\"label second\">{label2}</div>
                          <div class=\"value small\">${{value2}}</div>
                        </div>
                      `;
                    ]]]
                styles:
                  card:
                    - height: 230px
                    - width: {width}
                    - background: transparent
                    - box-shadow: none
                    - border: 0
                    - padding: 0
                  grid:
                    - grid-template-areas: \"\\\"info\\\"\"
                    - grid-template-columns: 1fr
                    - grid-template-rows: 1fr
                  custom_fields:
                    info:
                      - align-self: center
                      - justify-self: {justify}
                      - text-align: {align}
                      - {padding}
                card_mod:
                  style: |
                    .{wrap} {{
                      line-height: 1.05;
                      font-family: inherit;
                    }}
                    .label {{
                      color: {label_color};
                      font-size: {label_size}px;
                      font-weight: 500;
                      letter-spacing: 1.2px;
                      text-transform: uppercase;
                      text-shadow: {text_shadow};
                    }}
                    .label:empty {{ display: none; }}
                    .label.second {{
                      margin-top: 14px;
                    }}
                    .value {{
                      color: {color1};
                      font-size: {value_size}px;
                      font-weight: {"900" if side == "right" else "800"};
                      letter-spacing: -0.5px;
                      line-height: 0.95;
                      white-space: nowrap;
                      text-shadow: {text_shadow};
                    }}
                    .value.small {{
                      color: {color2};
                      font-size: {small_size}px;
                      font-weight: {"600" if side == "right" else "800"};
                      margin-top: {"8px" if side == "right" else "0"};
                    }}
              # POM_BLOCK_END {block_key}
"""


def _render_top_center_card(slot_type: str, options: dict[str, Any]) -> str:
    """Render center circular top gauge."""
    cfg = _top_slot_config(slot_type, options)
    if cfg is None:
        label = ""
        value_js = "return '-';"
        entity = str(options.get(CONF_ENTITY_SPEED) or "sensor.tesla_speed").strip()
    else:
        label = cfg["label"]
        value_js = cfg["value_js"]
        entity = cfg["entity"]
    value_js_ind = _indent_js(value_js, "                      ")
    helper_map = str(options.get(CONF_HELPER_MAP) or AUTO_HELPER_MAP).strip()
    global_scale = _dashboard_scale_option(options, CONF_TOP_FONT_SCALE)
    center_scale = _dashboard_scale_option(options, CONF_TOP_CENTER_FONT_SCALE)
    scale = round(global_scale * center_scale, 3)
    value_size = round(62 * scale, 2)
    label_size = round(13 * scale, 2)
    center_text_color = _top_color_for_map(options, "white", "#0f766e")
    center_label_color = _top_color_for_map(options, "rgba(255,255,255,0.65)", "rgba(30,41,59,0.70)")
    center_shadow = _top_text_shadow_for_map(options)
    center_inner_bg = _top_center_inner_background(options)
    center_inner_border = _top_center_inner_border(options)
    center_inner_shadow = _top_center_inner_shadow(options)
    return f"""              # POM_BLOCK_START top_center
              - type: custom:button-card
                entity: {entity}
                tap_action:
                  action: call-service
                  service: homeassistant.toggle
                  target:
                    entity_id: {helper_map}
                show_name: false
                show_icon: false
                show_state: false
                styles:
                  card:
                    - width: 180px
                    - height: 180px
                    - border-radius: 50%
                    - padding: 0
                    - border: none
                    - background: |
                        [[[
                          const v = Number(entity?.state) || 0;
                          const isPct = '{slot_type}' === 'battery_level';
                          const max = isPct ? 100 : ('{slot_type}' === 'power' ? 250 : 180);
                          const pct = Math.min(Math.abs(v) / max, 1);
                          const deg = pct * 360;
                          const color = v < 50 ? '#60a5fa' : v < 100 ? '#fbbf24' : '#f87171';
                          return `conic-gradient(
                            ${{color}} ${{deg}}deg,
                            rgba(255,255,255,0.06) ${{deg}}deg
                          )`;
                        ]]]
                    - box-shadow: |
                        [[[ 
                          const v = Number(entity?.state) || 0;
                          const glow = v < 50
                            ? '0 0 25px rgba(96,165,250,0.35)'
                            : v < 100
                            ? '0 0 25px rgba(251,191,36,0.35)'
                            : '0 0 25px rgba(248,113,113,0.35)';
                          return glow;
                        ]]]
                  custom_fields:
                    inner:
                      - position: absolute
                      - inset: 18px
                      - border-radius: 50%
                      - background: {center_inner_bg}
                      - border: 1px solid {center_inner_border}
                      - box-shadow: {center_inner_shadow}
                      - backdrop-filter: blur(10px) saturate(135%)
                      - -webkit-backdrop-filter: blur(10px) saturate(135%)
                      - display: flex
                      - align-items: center
                      - justify-content: center
                      - flex-direction: column
                custom_fields:
                  inner: |
                    [[[
                      const value = (() => {{
{value_js_ind}
                      }})();
                      return `
                        <div class=\"center-value\">${{value}}</div>
                        <div class=\"center-label\">{label}</div>
                      `;
                    ]]]
                card_mod:
                  style: |
                    ha-card {{
                      z-index: 2 !important;
                    }}
                    :host {{
                      margin-top: 20px !important;
                    }}
                    .center-value {{
                      font-size: {value_size}px;
                      font-weight: 700;
                      line-height: 1;
                      color: {center_text_color};
                      white-space: nowrap;
                      text-shadow: {center_shadow};
                    }}
                    .center-label {{
                      font-size: {label_size}px;
                      opacity: 0.85;
                      color: {center_label_color};
                      letter-spacing: 1.5px;
                      text-transform: uppercase;
                      text-shadow: {center_shadow};
                    }}
              # POM_BLOCK_END top_center
"""


def apply_top_gauge_options(template: str, options: dict[str, Any]) -> str:
    """Replace top header/gauge blocks with configured dropdown slots."""
    result = template
    result = _replace_marked_block(
        result,
        "top_left",
        _render_top_pair_card(
            "top_left",
            str(options.get(CONF_TOP_LEFT_SLOT_1) or "elevation"),
            str(options.get(CONF_TOP_LEFT_SLOT_2) or "power"),
            options,
            side="left",
        ),
    )
    result = _replace_marked_block(
        result,
        "top_center",
        _render_top_center_card(str(options.get(CONF_TOP_CENTER_SLOT) or "speed"), options),
    )
    result = _replace_marked_block(
        result,
        "top_right",
        _render_top_pair_card(
            "top_right",
            str(options.get(CONF_TOP_RIGHT_SLOT_1) or "battery_level"),
            str(options.get(CONF_TOP_RIGHT_SLOT_2) or "est_range"),
            options,
            side="right",
        ),
    )
    return result


def _bottom_slot_config(slot_type: str, options: dict[str, Any]) -> dict[str, str] | None:
    """Return render config for one middle bottom-bar slot."""
    slot_type = str(slot_type or "empty")
    configs: dict[str, dict[str, str]] = {
        "energy_remaining": {
            "entity": str(options.get(CONF_ENTITY_ENERGY_REMAINING) or "sensor.pom_energy_remaining").strip(),
            "icon": "mdi:flash",
            "value_js": """const v = Number(entity?.state);
return isNaN(v) ? "-" : `${v.toFixed(1)} kWh`;""",
            "color_js": """const kwh = Number(entity?.state) || 0;
const pct = (kwh / 54.5) * 100;
if (pct > 60) return "#50f5cf";
if (pct > 30) return "#facc15";
return "#ff6b6b";""",
        },
        "inside_temp": {
            "entity": str(options.get(CONF_ENTITY_INSIDE_TEMP) or "sensor.tesla_inside_temp").strip(),
            "icon": "mdi:thermometer",
            "value_js": """const v = Number(entity?.state);
return isNaN(v) ? "-" : `${v.toFixed(1)}°`;""",
            "color_js": """const t = Number(entity?.state) || 0;
if (t < 18) return "#63a8ff";
if (t < 26) return "#4ade80";
if (t < 32) return "#facc15";
return "#ff6b6b";""",
        },
        "battery_temp": {
            "entity": str(options.get(CONF_ENTITY_BATTERY_TEMP) or  _preferred_battery_temperature_entity()).strip(),
            "icon": "mdi:engine",
            "value_js": """const raw = entity?.state;
if (raw === undefined || raw === null || raw === '' || ['unknown','unavailable','none'].includes(String(raw).toLowerCase())) return "-";
const v = Number(String(raw).replace(',', '.'));
if (isNaN(v)) return String(raw);
return `${v.toFixed(1)}°`;""",
            "color_js": """const raw = entity?.state;
const t = Number(String(raw ?? '').replace(',', '.'));
if (isNaN(t)) {
  const on = ['on','true','1','heating','heat','active'].includes(String(raw ?? '').toLowerCase());
  return on ? "#facc15" : "rgba(255,255,255,0.48)";
}
if (t < 20) return "#3b82f6";
if (t < 30) return "#facc15";
if (t < 40) return "#22c55e";
return "#b8a8ff";""",
        },
        "outside_temp": {
            "entity": str(options.get(CONF_ENTITY_OUTSIDE_TEMP) or "sensor.tesla_outside_temp").strip(),
            "icon": "mdi:thermometer-lines",
            "value_js": """const v = Number(entity?.state);
return isNaN(v) ? "-" : `${v.toFixed(1)}°`;""",
            "color_js": """const t = Number(entity?.state) || 0;
if (t < 5) return "#63a8ff";
if (t < 18) return "#38bdf8";
if (t < 28) return "#4ade80";
if (t < 35) return "#facc15";
return "#ff6b6b";""",
        },
        "odometer": {
            "entity": str(options.get(CONF_ENTITY_ODOMETER) or "sensor.tesla_odometer").strip(),
            "icon": "mdi:counter",
            "value_js": """const v = Number(entity?.state);
return isNaN(v) ? "-" : `${Math.round(v).toLocaleString()} km`;""",
            "color_js": "return \"#d6eaff\";",
        },
        "battery_heater": {
            "entity": str(options.get(CONF_ENTITY_BATTERY_HEATER) or "binary_sensor.tesla_battery_heater").strip(),
            "icon": "mdi:heat-wave",
            "value_js": """const raw = String(entity?.state ?? "").toLowerCase();
if (!raw || raw === "unknown" || raw === "unavailable" || raw === "none") return "-";
const on = ["on", "true", "1", "heating", "heat", "active"].includes(raw);
return on ? "On" : "Off";""",
            "color_js": """const raw = String(entity?.state ?? "").toLowerCase();
const on = ["on", "true", "1", "heating", "heat", "active"].includes(raw);
return on ? "#facc15" : "rgba(255,255,255,0.48)";""",
        },
    }
    return configs.get(slot_type)


def _indent_js(js: str, indent: str) -> str:
    """Indent a JavaScript template body for YAML."""
    return "\n".join(indent + line.strip() for line in str(js or "").split("\n"))



def _energy_select_entity(options: dict[str, Any], slot_number: int = 1) -> str:
    """Return the actual live bottom-slot select entity id."""
    slot_number = int(slot_number or 1)
    if slot_number < 1 or slot_number > 3:
        slot_number = 1
    if slot_number == 1:
        default_entity = AUTO_HELPER_ENERGY_SLOT_SELECT
        option_key = CONF_HELPER_ENERGY_SLOT_SELECT
    else:
        default_entity = f"select.pom_tesla_dashboard_bottom_slot_{slot_number}_choice"
        option_key = f"helper_bottom_slot_{slot_number}_select"
    try:
        return str(merged_options(options).get(option_key) or default_entity).strip() or default_entity
    except Exception:
        return default_entity


def _energy_popup_entity(slot_number: int = 1) -> str:
    slot_number = int(slot_number or 1)
    if slot_number == 2:
        return "switch.pom_tesla_dashboard_energy_popup_2"
    if slot_number == 3:
        return "switch.pom_tesla_dashboard_energy_popup_3"
    return "switch.pom_tesla_dashboard_energy_popup"


def _energy_popup_helper_key(slot_number: int = 1) -> str:
    slot_number = int(slot_number or 1)
    if slot_number == 2:
        return "energy_popup_2"
    if slot_number == 3:
        return "energy_popup_3"
    return "energy_popup"


def _energy_popup_dynamic_card(options: dict[str, Any], default_key: str = "energy_remaining", slot_number: int = 1) -> str:
    """Render one live popup-enabled bottom slot."""
    slot_number = int(slot_number or 1)
    if slot_number < 1 or slot_number > 3:
        slot_number = 1

    energy_entity = str(options.get(CONF_ENTITY_ENERGY_REMAINING) or "sensor.pom_energy_remaining").strip()
    battery_entity = str(options.get(CONF_ENTITY_BATTERY_LEVEL) or "sensor.pom_battery_level").strip()
    range_entity = str(options.get(CONF_ENTITY_RATED_RANGE) or "sensor.pom_battery_range").strip()
    inside_entity = str(options.get(CONF_ENTITY_INSIDE_TEMP) or "sensor.tesla_inside_temp").strip()
    outside_entity = str(options.get(CONF_ENTITY_OUTSIDE_TEMP) or "sensor.tesla_outside_temp").strip()
    odometer_entity = str(options.get(CONF_ENTITY_ODOMETER) or "sensor.tesla_odometer").strip()
    heater_entity = str(options.get(CONF_ENTITY_BATTERY_HEATER) or "binary_sensor.tesla_battery_heater").strip()
    battery_temp_entity = str(options.get(CONF_ENTITY_BATTERY_TEMP) or _preferred_battery_temperature_entity()).strip()

    select_entity = _energy_select_entity(options, slot_number)
    popup_entity = _energy_popup_entity(slot_number)
    default_key = str(default_key or "energy_remaining").strip()
    if default_key not in {"energy_remaining", "battery_level", "battery_range", "inside_temp", "outside_temp", "odometer", "battery_heater", "battery_temp", "empty"}:
        default_key = "energy_remaining"

    value_js = f"""const select = states['{select_entity}'];
const defaultKey = '{default_key}';
const key = select?.attributes?.user_selected ? (select?.attributes?.selected_key || defaultKey) : defaultKey;
const cfg = {{
  energy_remaining: {{entity: '{energy_entity}', unit: ' kWh', decimals: 1}},
  battery_level: {{entity: '{battery_entity}', unit: '%', decimals: 0}},
  battery_range: {{entity: '{range_entity}', unit: ' km', decimals: 0}},
  inside_temp: {{entity: '{inside_entity}', unit: '°', decimals: 1}},
  outside_temp: {{entity: '{outside_entity}', unit: '°', decimals: 1}},
  odometer: {{entity: '{odometer_entity}', unit: ' km', decimals: 0}},
  battery_temp: {{entity: '{battery_temp_entity}', unit: '°', decimals: 1}},
  battery_heater: {{entity: '{heater_entity}', bool: true}},
  empty: {{empty: true}}
}};
const item = cfg[key] || cfg.energy_remaining;
if (item.empty) return '-';
const st = states[item.entity];
if (!st || ['unknown','unavailable','none',''].includes(String(st.state).toLowerCase())) return '-';
if (item.bool) {{
  const raw = String(st.state).toLowerCase();
  return ['on','true','1','heating','heat','active'].includes(raw) ? 'On' : 'Off';
}}
const n = Number(String(st.state).replace(',', '.'));
if (isNaN(n)) return st.state;
if (key === 'odometer') return `${{Math.round(n).toLocaleString()}}${{item.unit}}`;
return `${{n.toFixed(item.decimals)}}${{item.unit}}`;"""

    icon_js = f"""const select = states['{select_entity}'];
const defaultKey = '{default_key}';
const key = select?.attributes?.user_selected ? (select?.attributes?.selected_key || defaultKey) : defaultKey;
const icons = {{
  energy_remaining: 'mdi:flash',
  battery_level: 'mdi:battery-high',
  battery_range: 'mdi:map-marker-distance',
  inside_temp: 'mdi:thermometer',
  outside_temp: 'mdi:thermometer-lines',
  odometer: 'mdi:counter',
  battery_temp: 'mdi:car-battery',
  battery_heater: 'mdi:heat-wave',
  empty: 'mdi:minus-circle-outline'
}};
return icons[key] || 'mdi:flash';"""

    color_js = f"""const select = states['{select_entity}'];
const defaultKey = '{default_key}';
const key = select?.attributes?.user_selected ? (select?.attributes?.selected_key || defaultKey) : defaultKey;
const entityMap = {{
  energy_remaining: '{energy_entity}',
  battery_level: '{battery_entity}',
  battery_range: '{range_entity}',
  inside_temp: '{inside_entity}',
  outside_temp: '{outside_entity}',
  odometer: '{odometer_entity}',
  battery_temp: '{battery_temp_entity}',
  battery_heater: '{heater_entity}'
}};
if (key === 'empty') return 'rgba(255,255,255,0.35)';
const st = states[entityMap[key]];
const n = Number(String(st?.state ?? '').replace(',', '.'));
if (key === 'battery_heater') {{
  const raw = String(st?.state ?? '').toLowerCase();
  return ['on','true','1','heating','heat','active'].includes(raw) ? '#facc15' : 'rgba(255,255,255,0.48)';
}}
if (key === 'energy_remaining') {{
  const pct = ((isNaN(n) ? 0 : n) / 54.5) * 100;
  if (pct > 60) return '#50f5cf';
  if (pct > 30) return '#facc15';
  return '#ff6b6b';
}}
if (key === 'inside_temp' || key === 'outside_temp' || key === 'battery_temp') {{
  const t = isNaN(n) ? 0 : n;
  if (t < 18) return '#63a8ff';
  if (t < 28) return '#4ade80';
  if (t < 35) return '#facc15';
  return '#ff6b6b';
}}
return '#d6eaff';"""

    trigger_entities = [select_entity, energy_entity, battery_entity, range_entity, inside_entity, outside_entity, odometer_entity, battery_temp_entity, heater_entity]
    triggers = "\n".join(f"                  - {entity_id}" for entity_id in trigger_entities)

    return f"""              # POM_DYNAMIC_SLOT_{slot_number} live_popup
              - type: custom:button-card
                entity: {select_entity}
                triggers_update:
{triggers}
                show_icon: true
                show_name: false
                show_state: false
                icon: |
                  [[[
{_indent_js(icon_js, '                    ')}
                  ]]]
                custom_fields:
                  value: |
                    [[[
{_indent_js(value_js, '                      ')}
                    ]]]
                styles:
                  card:
                    - height: 42px
                    - width: fit-content
                    - padding: 0 18px
                    - background: transparent
                    - box-shadow: none
                    - border-radius: 0
                    - border-left: 1px solid rgba(255,255,255,0.14)
                    - border-right: 0
                    - cursor: pointer
                  grid:
                    - grid-template-areas: \"\\\"i value\\\"\"
                    - grid-template-columns: min-content max-content
                    - grid-template-rows: 42px
                    - column-gap: 9px
                    - justify-content: center
                    - align-content: center
                  img_cell:
                    - align-self: center
                    - justify-self: center
                    - width: 18px
                    - height: 18px
                  icon:
                    - color: |
                        [[[
{_indent_js(color_js, '                          ')}
                        ]]]
                    - width: 16px
                    - height: 16px
                  custom_fields:
                    value:
                      - align-self: center
                      - justify-self: start
                      - color: rgba(255,255,255,0.78)
                      - font-size: 16px
                      - font-weight: 800
                      - white-space: nowrap
                tap_action:
                  action: call-service
                  service: switch.turn_on
                  target:
                    entity_id: {popup_entity}
"""


def _energy_select_option_button(label: str, icon: str, key: str, options: dict[str, Any], slot_number: int = 1) -> str:
    select_entity = _energy_select_entity(options, slot_number)
    return f"""              - type: custom:button-card
                entity: {select_entity}
                icon: {icon}
                name: {label}
                show_icon: true
                show_name: true
                show_state: false
                styles:
                  card:
                    - height: 44px
                    - border-radius: 18px
                    - padding: 0 14px
                    - background: |
                        [[[
                          return entity?.state === '{label}' ? 'rgba(80,245,207,0.18)' : 'rgba(255,255,255,0.06)';
                        ]]]
                    - border: |
                        [[[
                          return entity?.state === '{label}' ? '1px solid rgba(80,245,207,0.55)' : '1px solid rgba(255,255,255,0.10)';
                        ]]]
                    - box-shadow: none
                  grid:
                    - grid-template-areas: \"\\\"i n\\\"\"
                    - grid-template-columns: min-content 1fr
                    - column-gap: 9px
                  icon:
                    - color: |
                        [[[
                          return entity?.state === '{label}' ? '#50f5cf' : 'rgba(255,255,255,0.72)';
                        ]]]
                    - width: 18px
                    - height: 18px
                  name:
                    - justify-self: start
                    - color: rgba(255,255,255,0.88)
                    - font-size: 13px
                    - font-weight: 700
                tap_action:
                  action: call-service
                  service: pom_tesla_report.set_dashboard_energy_field
                  data:
                    field: {key}
                    slot: {slot_number}
"""


def _build_energy_field_popup_card(options: dict[str, Any] | None = None, slot_number: int = 1) -> str:
    options = options or {}
    slot_number = int(slot_number or 1)
    if slot_number < 1 or slot_number > 3:
        slot_number = 1
    popup_entity = _energy_popup_entity(slot_number)
    buttons = [
        ("Energy remaining", "mdi:flash", "energy_remaining"),
        ("Battery level", "mdi:battery-high", "battery_level"),
        ("Battery range", "mdi:map-marker-distance", "battery_range"),
        ("Inside temperature", "mdi:thermometer", "inside_temp"),
        ("Outside temperature", "mdi:thermometer-lines", "outside_temp"),
        ("Odometer", "mdi:counter", "odometer"),
        ("Battery/module temperature", "mdi:car-battery", "battery_temp"),
        ("Battery heater", "mdi:heat-wave", "battery_heater"),
        ("Empty / hidden", "mdi:minus-circle-outline", "empty"),
    ]
    option_cards = "\n".join(_energy_select_option_button(label, icon, key, options, slot_number).rstrip() for label, icon, key in buttons)
    return f"""
    - type: conditional
      conditions:
        - entity: {popup_entity}
          state: "on"
      card:
        type: custom:mod-card
        card_mod:
          style: |
            :host {{
              position: fixed !important;
              left: 50% !important;
              bottom: 118px !important;
              transform: translateX(-50%) !important;
              width: min(560px, calc(100vw - 36px)) !important;
              z-index: 80 !important;
              pointer-events: auto !important;
            }}
            ha-card {{
              background: rgba(10, 14, 24, 0.88) !important;
              backdrop-filter: blur(18px) saturate(160%);
              -webkit-backdrop-filter: blur(18px) saturate(160%);
              border: 1px solid rgba(255,255,255,0.12) !important;
              border-radius: 24px !important;
              box-shadow: 0 18px 52px rgba(0,0,0,0.45) !important;
              padding: 14px !important;
              overflow: hidden !important;
            }}
        card:
          type: vertical-stack
          cards:
            - type: horizontal-stack
              cards:
                - type: custom:button-card
                  name: Bottom slot {slot_number}
                  icon: mdi:form-select
                  show_icon: true
                  show_name: true
                  styles:
                    card:
                      - height: 42px
                      - background: transparent
                      - box-shadow: none
                      - border: 0
                      - padding: 0 6px
                    grid:
                      - grid-template-areas: \"\\\"i n\\\"\"
                      - grid-template-columns: min-content 1fr
                      - column-gap: 10px
                    icon:
                      - color: '#50f5cf'
                      - width: 20px
                      - height: 20px
                    name:
                      - justify-self: start
                      - color: white
                      - font-size: 15px
                      - font-weight: 900
                  tap_action:
                    action: none
                - type: custom:button-card
                  icon: mdi:close
                  show_name: false
                  show_icon: true
                  styles:
                    card:
                      - width: 42px
                      - height: 42px
                      - border-radius: 16px
                      - background: rgba(255,255,255,0.07)
                      - box-shadow: none
                      - border: 1px solid rgba(255,255,255,0.12)
                    icon:
                      - color: rgba(255,255,255,0.86)
                      - width: 22px
                      - height: 22px
                  tap_action:
                    action: call-service
                    service: switch.turn_off
                    target:
                      entity_id: {popup_entity}
            - type: grid
              columns: 2
              square: false
              cards:
{option_cards}
"""


def apply_energy_field_popup_options(template: str, options: dict[str, Any]) -> str:
    """Insert live bottom-slot popups as root cards inside the main vertical-stack."""
    if "# POM_ENERGY_FIELD_POPUP" in template:
        return template

    popup_cards = []
    for slot_number in (1, 2, 3):
        popup_cards.append(_build_energy_field_popup_card(options, slot_number).strip("\n"))
    popup = "    # POM_ENERGY_FIELD_POPUP\n" + "\n".join(popup_cards) + "\n"
    marker = "\nview_layout:"
    if marker in template:
        return template.replace(marker, "\n" + popup + "view_layout:", 1)

    return template


def _render_bottom_slot_card(slot_number: int, slot_type: str, options: dict[str, Any]) -> str:
    """Render one configurable middle bottom bar slot as button-card YAML."""
    slot_type = str(slot_type or "empty").strip()
    popup_supported = {"energy_remaining", "battery_level", "battery_range", "inside_temp", "outside_temp", "odometer", "battery_heater", "battery_temp", "empty"}
    if slot_type in popup_supported:
        return _energy_popup_dynamic_card(options, default_key=slot_type, slot_number=slot_number)
    cfg = _bottom_slot_config(slot_type, options)
    if cfg is None:
        return f"              # POM_DYNAMIC_SLOT_{slot_number} empty\n"
    entity = cfg["entity"]
    icon = cfg["icon"]
    value_js = _indent_js(cfg["value_js"], "                      ")
    color_js = _indent_js(cfg["color_js"], "                          ")
    return f"""              # POM_DYNAMIC_SLOT_{slot_number} {slot_type}
              - type: custom:button-card
                entity: {entity}
                show_icon: true
                show_name: false
                show_state: false
                icon: {icon}
                custom_fields:
                  value: |
                    [[[
{value_js}
                    ]]]
                styles:
                  card:
                    - height: 42px
                    - width: fit-content
                    - padding: 0 18px
                    - background: transparent
                    - box-shadow: none
                    - border-radius: 0
                    - border-left: 1px solid rgba(255,255,255,0.14)
                    - border-right: 0
                  grid:
                    - grid-template-areas: \"\\\"i value\\\"\"
                    - grid-template-columns: min-content max-content
                    - grid-template-rows: 42px
                    - column-gap: 9px
                    - justify-content: center
                    - align-content: center
                  img_cell:
                    - align-self: center
                    - justify-self: center
                    - width: 18px
                    - height: 18px
                  icon:
                    - color: |
                        [[[
{color_js}
                        ]]]
                    - width: 16px
                    - height: 16px
                  custom_fields:
                    value:
                      - align-self: center
                      - justify-self: start
                      - color: rgba(255,255,255,0.78)
                      - font-size: 16px
                      - font-weight: 800
                      - white-space: nowrap
                tap_action:
                  action: none
"""



def _entity_domain(entity_id: str) -> str:
    """Return the HA domain for an entity id."""
    entity_id = str(entity_id or "").strip()
    return entity_id.split(".", 1)[0] if "." in entity_id else ""


def _sidebar_tap_action_yaml(entity_id: str) -> str:
    """Return the tap_action YAML for a sidebar entity.

    Important: this intentionally uses explicit service calls with an explicit
    target entity. Using `action: toggle` broke when the visible entity and the
    action entity were not exactly the same, and also behaved inconsistently
    in the Tesla browser.
    """
    domain = _entity_domain(entity_id)
    entity_id = str(entity_id or "").strip()
    if not entity_id:
        return "  tap_action:\n    action: none"
    if domain == "button":
        return f"  tap_action:\n    action: call-service\n    service: button.press\n    target:\n      entity_id: {entity_id}"
    if domain == "cover":
        return f"  tap_action:\n    action: call-service\n    service: cover.toggle\n    target:\n      entity_id: {entity_id}"
    if domain == "lock":
        return f"  tap_action:\n    action: call-service\n    service: lock.unlock\n    target:\n      entity_id: {entity_id}"
    if domain in {"switch", "input_boolean"}:
        return f"  tap_action:\n    action: call-service\n    service: homeassistant.toggle\n    target:\n      entity_id: {entity_id}"
    if domain in {"sensor", "binary_sensor"}:
        return "  tap_action:\n    action: more-info"
    if domain in {"select", "number"}:
        return "  tap_action:\n    action: more-info"
    return f"  tap_action:\n    action: call-service\n    service: homeassistant.toggle\n    target:\n      entity_id: {entity_id}"

def _render_sidebar_slot_card(index: int, action_key: str, options: dict[str, Any]) -> str:
    """Render one left sidebar slot card from the configured action type."""
    action_key = str(action_key or "empty").strip()
    if action_key == "empty" or action_key not in SIDEBAR_ACTION_CONFIG:
        return ""
    cfg = SIDEBAR_ACTION_CONFIG[action_key]
    action_entity = str(options.get(cfg["entity"]) or "").strip()
    if not action_entity:
        # Old alpha builds sometimes saved a blank entity override. Fall back to
        # the known POM default for that action.
        action_entity = str(DEFAULT_OPTIONS.get(cfg["entity"], "") or "").strip()

    # Keep the visible entity and the service target the same for controllable
    # sidebar actions. The earlier separate state/control entity split caused
    # exactly the failure Berkan saw: the card displayed one entity but pressed
    # another one, so button/switch actions silently did nothing.
    display_entity = action_entity

    # If the user selected a slot but the matching entity is still empty, render
    # a disabled placeholder instead of dropping the slot. This makes 5th/6th
    # sidebar items visibly appear inside the bar while still avoiding broken
    # service calls.
    disabled_slot = not bool(action_entity)
    if disabled_slot:
        display_entity = "sensor.pom_tesla_dashboard_location_label"
    icon = str(cfg.get("icon") or "mdi:gesture-tap-button")
    if action_key == "home_entity_1":
        icon = str(options.get("entity_home_entity_1_icon") or icon).strip() or icon
    elif action_key == "home_entity_2":
        icon = str(options.get("entity_home_entity_2_icon") or icon).strip() or icon
    label = SIDEBAR_ACTION_TYPES.get(action_key, action_key)
    margin = "0 auto" if index == 8 else "0 auto 12px auto"
    tap_action = "  tap_action:\n    action: none" if disabled_slot else _sidebar_tap_action_yaml(action_entity)

    # Flash lights is a momentary button. It does not stay "on", so state-based
    # styling makes the original always-glowing top flash button disappear. Keep
    # the old green glow for this specific action, while the other sidebar slots
    # remain state-driven.
    if action_key == "flash_lights":
        background_js = '            return "rgba(0,115,85,0.72)";'
        border_js = '            return "1px solid rgba(80,255,207,0.85)";'
        shadow_js = '            return "0 0 18px rgba(80,255,207,0.28), inset 0 0 14px rgba(80,255,207,0.10)";'
        icon_color_js = '            return "#b8ffe8";'
        icon_size = "34px"
    else:
        background_js = '            const state = entity?.state;\n            const active = [\'on\', \'true\', \'locked\', \'open\', \'opening\', \'heat\', \'heating\', \'active\'].includes(String(state).toLowerCase());\n            return active ? "rgba(15, 40, 72, 0.72)" : "transparent";'
        border_js = '            const state = entity?.state;\n            const active = [\'on\', \'true\', \'locked\', \'open\', \'opening\', \'heat\', \'heating\', \'active\'].includes(String(state).toLowerCase());\n            return active ? "1px solid rgba(0,145,255,0.95)" : "1px solid transparent";'
        shadow_js = '            const state = entity?.state;\n            const active = [\'on\', \'true\', \'locked\', \'open\', \'opening\', \'heat\', \'heating\', \'active\'].includes(String(state).toLowerCase());\n            return active ? "0 0 18px rgba(0,145,255,0.28), inset 0 0 14px rgba(0,145,255,0.10)" : "none";'
        icon_color_js = '            const state = entity?.state;\n            const active = [\'on\', \'true\', \'locked\', \'open\', \'opening\', \'heat\', \'heating\', \'active\'].includes(String(state).toLowerCase());\n            return active ? "#5bbcff" : "rgba(255,255,255,0.42)";'
        icon_size = "28px"

    return f"""# POM_DYNAMIC_SIDEBAR_SLOT_{index}_{action_key}
- type: custom:button-card
  entity: {display_entity}
  icon: {icon}
  show_icon: true
  show_name: false
  show_state: false
  layout: icon
  tooltip: {label}
  styles:
    card:
      - width: 60px
      - height: 60px
      - padding: 0
      - margin: {margin}
      - border-radius: 18px
      - background: |
          [[[
{background_js}
          ]]]
      - border: |
          [[[
{border_js}
          ]]]
      - box-shadow: |
          [[[
{shadow_js}
          ]]]
    grid:
      - grid-template-areas: '"i"'
      - grid-template-columns: 1fr
      - grid-template-rows: 1fr
    img_cell:
      - width: 100%
      - height: 100%
      - display: flex
      - align-items: center
      - justify-content: center
    icon:
      - color: |
          [[[
{icon_color_js}
          ]]]
      - width: {icon_size}
      - height: {icon_size}
  state:
    - value: unavailable
      styles:
        icon:
          - color: rgba(255,255,255,0.22)
{tap_action}
"""


def apply_sidebar_slot_options(template: str, options: dict[str, Any]) -> str:
    """Replace the original fixed sidebar buttons with eight configurable slots."""
    start_marker = "            # POM_BLOCK_START sidebar_flash_lights"
    end_marker = "            # POM_BLOCK_END sidebar_manual_tracking"
    start = template.find(start_marker)
    end = template.find(end_marker)
    if start < 0 or end < 0:
        return template
    end += len(end_marker)
    blocks: list[str] = []
    for index, conf_key in enumerate(SIDEBAR_SLOT_KEYS, start=1):
        block = _render_sidebar_slot_card(index, str(options.get(conf_key) or "empty"), options).rstrip()
        if block:
            blocks.append(_indent_yaml_block(block, 12))
    replacement = "\n".join(blocks)
    if replacement:
        replacement = "            # POM_DYNAMIC_SIDEBAR_START\n" + replacement + "\n            # POM_DYNAMIC_SIDEBAR_END"
    else:
        replacement = "            # POM_DYNAMIC_SIDEBAR_EMPTY"
    return template[:start] + replacement + template[end:]

def apply_bottom_slot_options(template: str, options: dict[str, Any]) -> str:
    """Replace the three middle bottom-bar blocks with configured slot cards."""
    result = template
    slot_blocks = [
        ("bottom_energy", CONF_BOTTOM_SLOT_1),
        ("bottom_inside_temp", CONF_BOTTOM_SLOT_2),
        ("bottom_battery_temp", CONF_BOTTOM_SLOT_3),
    ]
    for index, (block_key, conf_key) in enumerate(slot_blocks, start=1):
        replacement = _render_bottom_slot_card(index, str(options.get(conf_key) or "empty"), options)
        result = _replace_marked_block(result, block_key, replacement)
    return result


def apply_visibility_options(template: str, options: dict[str, Any]) -> str:
    """Remove disabled sidebar/bottom button-card blocks from marked template regions."""
    result = template

    # Prefer explicit POM_BLOCK markers. They preserve the original Lovelace design
    # while preventing accidental parent/wrapper deletion.
    for conf_key, block_key in BOTTOM_VISIBILITY_BLOCK_KEYS.items():
        if options.get(conf_key, True) is False:
            result = _remove_marked_block(result, block_key)

    for conf_key, block_key in SIDEBAR_VISIBILITY_BLOCK_KEYS.items():
        if options.get(conf_key, True) is False:
            result = _remove_marked_block(result, block_key)

    # Fallback for older templates without markers.
    bottom_end_marker = (
        '    - type: conditional\n'
        '      conditions:\n'
        '        - entity: input_boolean.tesla_controls\n'
        '          state: "on"'
    )
    if "# POM_BLOCK_START" not in template:
        bottom_start, bottom_end = _find_region(result, "entity: sensor.tesla_rated_range", bottom_end_marker)
        for conf_key, marker in BOTTOM_VISIBILITY_MARKERS.items():
            if options.get(conf_key, True) is False:
                result = _remove_button_card_block_by_marker_in_region(result, marker, bottom_start, bottom_end)
                bottom_start, bottom_end = _find_region(result, "entity: sensor.tesla_rated_range", bottom_end_marker)

        sidebar_start, sidebar_end = _find_region(result, "entity: button.pom_flash_lights_2", "view_layout:")
        for conf_key, marker in SIDEBAR_VISIBILITY_MARKERS.items():
            if options.get(conf_key, True) is False:
                result = _remove_button_card_block_by_marker_in_region(result, marker, sidebar_start, sidebar_end)
                sidebar_start, sidebar_end = _find_region(result, "entity: button.pom_flash_lights_2", "view_layout:")

    return result


def _indent_yaml_block(block: str, spaces: int) -> str:
    """Indent a YAML block by a fixed amount."""
    prefix = " " * spaces
    return "\n".join(prefix + line if line else line for line in str(block or "").splitlines())


def _indent_yaml_card_list_item(block: str, list_indent: int) -> str:
    """Indent a single card YAML block as one item under a Lovelace cards: list."""
    lines = str(block or "").rstrip().splitlines()
    if not lines:
        return ""
    first_prefix = " " * list_indent
    child_prefix = " " * (list_indent + 2)
    out = [first_prefix + "- " + lines[0]]
    out.extend(child_prefix + line if line else line for line in lines[1:])
    return "\n".join(out)




def _dashboard_charge_cost_presets(options: dict[str, Any]) -> list[dict[str, Any]]:
    """Return exactly three charge-cost presets for the dashboard charge popup.

    The first three saved `charge_provider_presets` are the authoritative
    dashboard cost cards. Legacy Supercharger/ZES/Astor price keys are only
    used as fallback/backfill for older installs that do not have presets yet.
    """
    default_currency = str(options.get("report_currency") or options.get("currency") or "TL").strip().upper() or "TL"

    def _currency(value: Any) -> str:
        raw = str(value or default_currency).strip().upper()
        return "TL" if raw == "TRY" else (raw or default_currency)

    def _price(value: Any, fallback: float = 0.0) -> float:
        try:
            number = float(str(value if value is not None else fallback).replace(",", "."))
        except Exception:
            number = fallback
        return round(number if number > 0 else fallback, 4)

    def _item(name: Any, price: Any, currency: Any = None, fallback: float = 0.0) -> dict[str, Any] | None:
        label = str(name or "").strip()
        unit_price = _price(price, fallback)
        if not label or unit_price <= 0:
            return None
        return {"name": label, "unit_price": unit_price, "currency": _currency(currency)}

    raw_presets = options.get("charge_provider_presets")
    if not isinstance(raw_presets, list):
        raw_presets = []

    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in raw_presets:
        if not isinstance(raw, dict):
            continue
        item = _item(raw.get("name"), raw.get("unit_price", raw.get("price")), raw.get("currency", raw.get("currency_label")))
        if not item:
            continue
        key = item["name"].casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
        if len(result) >= 3:
            break

    fallback_items = [
        _item("Supercharger", options.get("supercharger_price"), default_currency, 9.9),
        _item("ZES", options.get("zes_price"), default_currency, 16.49),
        _item("Astor", options.get("astor_price"), default_currency, 12.49),
    ]
    for item in fallback_items:
        if len(result) >= 3:
            break
        if not item:
            continue
        key = item["name"].casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(item)

    return result[:3]

def _apply_charge_popup_entity_options(panel_yaml: str, options: dict[str, Any]) -> str:
    """Replace default charging popup entities with configured options."""
    result = panel_yaml
    for old, conf_key in sorted(CHARGE_POPUP_ENTITY_REPLACEMENTS.items(), key=lambda item: len(item[0]), reverse=True):
        result = _replace_entity_token(result, old, str(options.get(conf_key) or old).strip())
    return result


def _build_charge_popup_overlay(options: dict[str, Any]) -> str:
    """Build a Bubble-free fixed overlay charging popup."""
    if options.get(CONF_ENABLE_CHARGE_POPUP, True) is False:
        return ""
    popup_switch = str(options.get(CONF_HELPER_CHARGE_POPUP) or AUTO_HELPER_CHARGE_POPUP).strip()
    panel_path = Path(__file__).resolve().parent / "charge_popup_panel.yaml"
    try:
        panel_yaml = panel_path.read_text(encoding="utf-8").rstrip()
    except OSError:
        return ""
    panel_yaml = panel_yaml.replace("__POM_CHARGE_COST_PRESETS__", json.dumps(_dashboard_charge_cost_presets(options), ensure_ascii=False))
    panel_yaml = panel_yaml.replace("__POM_CHARGE_POPUP_SWITCH__", popup_switch)
    panel_yaml = _apply_charge_popup_entity_options(panel_yaml, options)
    panel_yaml = _indent_yaml_card_list_item(panel_yaml, 12)
    return f"""    # POM_BLOCK_START charge_popup_overlay
    - type: conditional
      conditions:
        - entity: {popup_switch}
          state: "on"
      card:
        type: custom:mod-card
        card_mod:
          style: |
            :host {{
              position: fixed !important;
              inset: 0 !important;
              width: 100vw !important;
              height: 100vh !important;
              z-index: 999 !important;
              pointer-events: auto !important;
              display: block !important;
            }}
            ha-card {{
              position: fixed !important;
              inset: 0 !important;
              width: 100vw !important;
              height: 100vh !important;
              margin: 0 !important;
              padding: 72px 0 38px !important;
              overflow-y: auto !important;
              overflow-x: hidden !important;
              background: rgba(0,0,0,0.42) !important;
              box-shadow: none !important;
              border: 0 !important;
              border-radius: 0 !important;
              backdrop-filter: blur(4px) saturate(130%);
              -webkit-backdrop-filter: blur(4px) saturate(130%);
            }}
        card:
          type: vertical-stack
          cards:
            - type: custom:mod-card
              card_mod:
                style: |
                  :host {{
                    display: block !important;
                    position: relative !important;
                    z-index: 10050 !important;
                    width: 100vw !important;
                    max-width: 100vw !important;
                    height: 52px !important;
                    margin-left: calc(50% - 50vw) !important;
                    margin-right: calc(50% - 50vw) !important;
                    margin-bottom: -48px !important;
                    pointer-events: none !important;
                  }}
                  ha-card {{
                    width: min(1220px, calc(100vw - 84px)) !important;
                    max-width: 1220px !important;
                    height: 52px !important;
                    padding: 0 !important;
                    margin: 0 auto !important;
                    background: transparent !important;
                    border: 0 !important;
                    box-shadow: none !important;
                    overflow: visible !important;
                    transform: scale(0.92) !important;
                    transform-origin: top center !important;
                    pointer-events: none !important;
                  }}
                  @media (min-width: 1500px) {{
                    ha-card {{
                      width: calc(100vw - 96px) !important;
                      max-width: 1280px !important;
                      transform: scale(0.90) !important;
                    }}
                  }}
                  @media (max-width: 1220px) {{
                    ha-card {{
                      width: min(930px, calc(100vw - 34px)) !important;
                      max-width: 930px !important;
                      transform: scale(0.94) !important;
                    }}
                  }}
                  @media (max-width: 1185px) and (max-height: 940px) {{
                    ha-card {{
                      width: min(930px, calc(100vw - 36px)) !important;
                      max-width: 930px !important;
                      transform: scale(0.94) !important;
                    }}
                  }}
                  @media (max-width: 1143px) and (max-height: 686px) {{
                    ha-card {{
                      width: calc(100vw - 38px) !important;
                      max-width: 1098px !important;
                      transform: scale(0.79) !important;
                    }}
                  }}
                  @media (max-width: 900px) {{
                    ha-card {{
                      width: calc(100vw - 24px) !important;
                      max-width: 820px !important;
                      transform: scale(0.86) !important;
                    }}
                  }}
              card:
                type: custom:button-card
                icon: mdi:close
                show_name: false
                show_state: false
                show_icon: true
                styles:
                  card:
                    - width: 52px
                    - height: 52px
                    - border-radius: 26px
                    - padding: 0
                    - margin-left: auto
                    - background: rgba(8,10,18,0.92)
                    - box-shadow: 0 10px 30px rgba(0,0,0,0.48)
                    - border: 1px solid rgba(255,255,255,0.18)
                    - pointer-events: auto
                  grid:
                    - grid-template-areas: '"i"'
                    - grid-template-columns: 52px
                    - grid-template-rows: 52px
                  img_cell:
                    - display: flex
                    - align-items: center
                    - justify-content: center
                    - width: 52px
                    - height: 52px
                  icon:
                    - color: rgba(255,255,255,0.92)
                    - width: 28px
                    - height: 28px
                tap_action:
                  action: call-service
                  service: homeassistant.turn_off
                  target:
                    entity_id: {popup_switch}
{panel_yaml}
    # POM_BLOCK_END charge_popup_overlay
"""


def apply_map_options(template: str, options: dict[str, Any]) -> str:
    """Apply map-specific options such as trail length.

    The dashboard intentionally keeps two map cards because the native HA map
    card cannot template its entity list reliably. The person toggle switches
    visibility between Tesla-only and Tesla+people maps.
    """
    result = template
    try:
        tesla_hours = max(0, min(24, int(float(options.get(CONF_TESLA_MAP_HOURS_TO_SHOW, 1)))))
    except (TypeError, ValueError):
        tesla_hours = 1
    try:
        person_hours = max(0, min(24, int(float(options.get(CONF_PERSON_MAP_HOURS_TO_SHOW, 0)))))
    except (TypeError, ValueError):
        person_hours = 0

    map_theme_mode = _dashboard_map_theme_mode(options)
    # alpha247: restore the old dashboard map behavior.
    # Dark uses the original Home Assistant auto map theme with no forced tile filters.
    # This matches the pre-alpha243/244 dashboard look and avoids the over-dark/black map.
    # Light still lets the user force daytime tiles from Dashboard Settings, but we do not
    # apply any extra Leaflet tile filter in either mode.
    if map_theme_mode == MAP_THEME_LIGHT:
        result = result.replace("theme_mode: auto", "theme_mode: light", 2)
    else:
        result = result.replace("theme_mode: light", "theme_mode: auto", 2)

    # Keep this narrow so charging/history cards are not touched.
    result = result.replace(
        "entities:\n                    - entity: person.tesla\n                  hours_to_show: 1",
        f"entities:\n                    - entity: person.tesla\n                  hours_to_show: {tesla_hours}",
        1,
    )
    result = result.replace(
        "entities:\n                    - entity: person.tesla\n                    - entity: person.ali\n                    - entity: person.cavidan\n                  hours_to_show: 0",
        f"entities:\n                    - entity: person.tesla\n                    - entity: person.ali\n                    - entity: person.cavidan\n                  hours_to_show: {person_hours}",
        1,
    )
    return result


def apply_charge_popup_options(template: str, options: dict[str, Any]) -> str:
    """Add charging popup overlay and wire the bottom charging button to it."""
    result = template
    popup_switch = str(options.get(CONF_HELPER_CHARGE_POPUP) or AUTO_HELPER_CHARGE_POPUP).strip()
    result = result.replace(
        'tap_action:\n                  action: navigate\n                  navigation_path: "#charge"',
        f'tap_action:\n                  action: call-service\n                  service: homeassistant.toggle\n                  target:\n                    entity_id: {popup_switch}',
    )
    overlay = _build_charge_popup_overlay(options)
    if overlay:
        marker = "view_layout:\n  grid-area: sidebar"
        pos = result.rfind(marker)
        if pos >= 0:
            result = result[:pos] + overlay + result[pos:]
        else:
            result = result.rstrip() + "\n" + overlay
    return result


def _build_fullscreen_controller(options: dict[str, Any]) -> str:
    """Build a dashboard-only fullscreen controller.

    Runtime on/off state is no longer kept in a separate localStorage flag.
    The floating button toggles the integration-owned helper switch
    (switch.pom_tesla_dashboard_fullscreen, or its actual suffixed entity id).
    This makes the dashboard button and Home Assistant state model use one
    source of truth.
    """
    if not bool(options.get(CONF_FULLSCREEN_ENABLED, True)):
        return ""
    hide_header = "true" if bool(options.get(CONF_FULLSCREEN_HIDE_HEADER, False)) else "false"
    hide_sidebar = "true" if bool(options.get(CONF_FULLSCREEN_HIDE_SIDEBAR, False)) else "false"
    disable_scroll = "true" if bool(options.get(CONF_FULLSCREEN_DISABLE_SCROLL, True)) else "false"
    show_button = "true" if bool(options.get(CONF_FULLSCREEN_SHOW_BUTTON, True)) else "false"
    fullscreen_switch = str(options.get(CONF_HELPER_FULLSCREEN) or AUTO_HELPER_FULLSCREEN).strip()
    return f"""    - type: custom:button-card
      entity: {fullscreen_switch}
      triggers_update:
        - {fullscreen_switch}
      show_icon: false
      show_name: false
      show_state: false
      tap_action:
        action: none
      styles:
        card:
          - display: none
          - height: 0
          - width: 0
          - padding: 0
          - margin: 0
          - overflow: hidden
      custom_fields:
        controller: |
          [[[ 
            const opts = {{
              hideHeader: {hide_header},
              hideSidebar: {hide_sidebar},
              disableScroll: {disable_scroll},
              showButton: {show_button},
              fullscreenSwitch: '{fullscreen_switch}',
            }};

            const touched = window.__pomTeslaDashboardTouchedStyles = window.__pomTeslaDashboardTouchedStyles || new Map();

            const showStartupOverlay = () => {{
              try {{
                if (window.__pomTeslaDashboardStartupOverlayDone) return;
                window.__pomTeslaDashboardStartupOverlayDone = true;
                const mask = document.createElement('div');
                mask.id = 'pom-tesla-dashboard-startup-overlay';
                mask.textContent = '';
                mask.style.cssText = [
                  'position:fixed!important',
                  'inset:0!important',
                  'z-index:2147483646!important',
                  'background:#05080d!important',
                  'opacity:1!important',
                  'pointer-events:none!important',
                  'transition:opacity 360ms ease!important'
                ].join(';') + ';';
                document.body.appendChild(mask);
                setTimeout(() => {{
                  try {{ mask.style.setProperty('opacity', '0', 'important'); }} catch(e) {{}}
                  setTimeout(() => {{ try {{ mask.remove(); }} catch(e) {{}} }}, 420);
                }}, 700);
              }} catch(e) {{}}
            }};
            showStartupOverlay();

            const collectRoots = () => {{
              const roots = [];
              const seen = new Set();
              const collect = (root, depth = 0) => {{
                if (!root || depth > 9 || seen.has(root)) return;
                seen.add(root);
                roots.push(root);
                let nodes = [];
                try {{ nodes = root.querySelectorAll ? root.querySelectorAll('*') : []; }} catch(e) {{ nodes = []; }}
                nodes.forEach((node) => {{ if (node.shadowRoot) collect(node.shadowRoot, depth + 1); }});
              }};
              collect(document, 0);
              return roots;
            }};

            const remember = (el, prop) => {{
              if (!el) return;
              let rec = touched.get(el);
              if (!rec) {{ rec = {{}}; touched.set(el, rec); }}
              if (!(prop in rec)) {{
                try {{
                  rec[prop] = {{
                    value: el.style.getPropertyValue(prop),
                    priority: el.style.getPropertyPriority(prop),
                  }};
                }} catch(e) {{
                  rec[prop] = {{ value: '', priority: '' }};
                }}
              }}
            }};

            const setImportant = (el, prop, value) => {{
              if (!el) return;
              try {{
                remember(el, prop);
                el.style.setProperty(prop, value, 'important');
              }} catch(e) {{}}
            }};

            const restoreTouched = () => {{
              try {{
                touched.forEach((props, el) => {{
                  Object.entries(props).forEach(([prop, old]) => {{
                    try {{
                      if (old.value) el.style.setProperty(prop, old.value, old.priority || '');
                      else el.style.removeProperty(prop);
                    }} catch(e) {{}}
                  }});
                }});
                touched.clear();
              }} catch(e) {{}}
            }};

            const hideEl = (el) => {{
              setImportant(el, 'display', 'none');
              setImportant(el, 'visibility', 'hidden');
              setImportant(el, 'pointer-events', 'none');
            }};

            const applySizing = (roots, activeScrollLock) => {{
              if (activeScrollLock) {{
                setImportant(document.documentElement, 'overflow', 'hidden');
                setImportant(document.documentElement, 'height', '100vh');
                setImportant(document.body, 'overflow', 'hidden');
                setImportant(document.body, 'height', '100vh');
                setImportant(document.body, 'margin', '0');
              }}
              roots.forEach((root) => {{
                ['ha-panel-lovelace', 'hui-root', 'hui-view', '#view'].forEach((sel) => {{
                  try {{
                    root.querySelectorAll(sel).forEach((el) => {{
                      setImportant(el, 'height', '100vh');
                      setImportant(el, 'min-height', '100vh');
                      setImportant(el, 'margin-top', '0px');
                    }});
                  }} catch(e) {{}}
                }});
              }});
            }};

            const applyHeader = (roots, active) => {{
              if (!active) return;
              const selectors = [
                'app-header',
                'app-toolbar',
                'ha-top-app-bar-fixed',
                'ha-top-app-bar',
                'ha-header-bar',
                '.toolbar[slot="toolbar"]',
                '[slot="toolbar"]',
                '.toolbar',
                '.header',
                '.top-app-bar',
                '.main-title'
              ];
              const topChromeSelectors = [
                'ha-menu-button',
                'ha-button-menu',
                'ha-control-button-menu',
                'ha-icon-button',
                'mwc-icon-button',
                'paper-icon-button',
                'ha-assist-chip'
              ];
              const isTopChrome = (el) => {{
                try {{
                  const r = el.getBoundingClientRect();
                  return r && r.width > 0 && r.height > 0 && r.top <= 86 && r.bottom <= 128;
                }} catch(e) {{
                  return false;
                }}
              }};
              const hideIfTopChrome = (el) => {{
                if (isTopChrome(el)) hideEl(el);
              }};
              roots.forEach((root) => {{
                selectors.forEach((sel) => {{
                  try {{ root.querySelectorAll(sel).forEach(hideEl); }} catch(e) {{}}
                }});
                topChromeSelectors.forEach((sel) => {{
                  try {{ root.querySelectorAll(sel).forEach(hideIfTopChrome); }} catch(e) {{}}
                }});
                try {{
                  root.querySelectorAll('div, span').forEach((el) => {{
                    const text = (el.textContent || '').trim();
                    if ((text === 'Tesla' || text === 'Home' || text === 'Overview') && isTopChrome(el)) hideEl(el);
                  }});
                }} catch(e) {{}}
              }});
              setImportant(document.documentElement, '--header-height', '0px');
              setImportant(document.documentElement, '--app-toolbar-height', '0px');
              setImportant(document.body, '--header-height', '0px');
              setImportant(document.body, '--app-toolbar-height', '0px');
            }};

            const applySidebar = (roots, active) => {{
              if (!active) return;
              const selectors = ['ha-sidebar', '.sidebar', '[data-panel="sidebar"]'];
              roots.forEach((root) => {{
                selectors.forEach((sel) => {{
                  try {{ root.querySelectorAll(sel).forEach(hideEl); }} catch(e) {{}}
                }});
                ['home-assistant-main', 'app-drawer-layout', 'ha-drawer', 'mwc-drawer'].forEach((sel) => {{
                  try {{
                    root.querySelectorAll(sel).forEach((el) => {{
                      setImportant(el, '--mdc-drawer-width', '0px');
                      setImportant(el, '--app-drawer-width', '0px');
                      setImportant(el, '--sidebar-width', '0px');
                      setImportant(el, '--mdc-drawer-modal-width', '0px');
                    }});
                  }} catch(e) {{}}
                }});
              }});
            }};

            const getFullscreenElement = () => (
              document.fullscreenElement ||
              document.webkitFullscreenElement ||
              document.mozFullScreenElement ||
              document.msFullscreenElement ||
              null
            );

            const browserFullscreenOn = () => {{
              try {{
                if (!getFullscreenElement()) {{
                  const target = document.documentElement || document.body;
                  const request = target.requestFullscreen || target.webkitRequestFullscreen || target.mozRequestFullScreen || target.msRequestFullscreen;
                  if (request) request.call(target);
                }}
              }} catch(e) {{}}
            }};

            const browserFullscreenOff = () => {{
              try {{
                const exit = document.exitFullscreen || document.webkitExitFullscreen || document.mozCancelFullScreen || document.msExitFullscreen;
                if (exit) exit.call(document);
              }} catch(e) {{}}
            }};

            const isImmersive = () => {{
              const switchState = states[opts.fullscreenSwitch]?.state;
              if (switchState === 'on') {{
                try {{ window.localStorage.setItem('pomTeslaDashboardFullscreen', 'on'); }} catch(e) {{}}
                return true;
              }}
              if (switchState === 'off') {{
                try {{ window.localStorage.setItem('pomTeslaDashboardFullscreen', 'off'); }} catch(e) {{}}
                return false;
              }}
              try {{
                const stored = window.localStorage.getItem('pomTeslaDashboardFullscreen');
                if (stored === 'off') return false;
                if (stored === 'on') return true;
              }} catch(e) {{}}
              // Safe default for repeated test installs where HA may suffix the
              // helper entity or the state is not hydrated yet: fullscreen mode
              // should still apply instead of leaving HA chrome visible.
              return true;
            }};

            const applyPomTeslaFullscreen = () => {{
              const immersive = isImmersive();
              const activeHeader = Boolean(opts.hideHeader && immersive);
              const activeSidebar = Boolean(opts.hideSidebar && immersive);
              const activeScrollLock = Boolean(opts.disableScroll && immersive);

              restoreTouched();
              const roots = collectRoots();
              applySizing(roots, activeScrollLock);
              applyHeader(roots, activeHeader);
              applySidebar(roots, activeSidebar);
              ensureFullscreenButton();
            }};

            const ensureFullscreenButton = () => {{
              let btn = document.getElementById('pom-tesla-dashboard-fullscreen-button');
              if (!opts.showButton) {{
                if (btn) btn.remove();
                return;
              }}
              if (!btn) {{
                btn = document.createElement('button');
                btn.id = 'pom-tesla-dashboard-fullscreen-button';
                btn.type = 'button';
                btn.textContent = '⛶';
                btn.title = 'Toggle dashboard fullscreen mode';
                btn.style.cssText = 'position:fixed!important;right:18px!important;bottom:18px!important;z-index:2147483647!important;width:42px!important;height:42px!important;border-radius:999px!important;border:1px solid rgba(255,255,255,0.16)!important;background:rgba(5,10,18,0.55)!important;color:rgba(255,255,255,0.84)!important;font-size:22px!important;line-height:38px!important;backdrop-filter:blur(12px) saturate(160%)!important;-webkit-backdrop-filter:blur(12px) saturate(160%)!important;box-shadow:0 8px 24px rgba(0,0,0,0.25)!important;cursor:pointer!important;';
                btn.addEventListener('click', async (ev) => {{
                  ev.preventDefault();
                  ev.stopPropagation();
                  const activeNow = isImmersive();
                  try {{
                    window.localStorage.setItem('pomTeslaDashboardFullscreen', activeNow ? 'off' : 'on');
                  }} catch(e) {{}}
                  try {{
                    if (states[opts.fullscreenSwitch]) {{
                      await hass.callService('homeassistant', 'toggle', {{ entity_id: opts.fullscreenSwitch }});
                    }}
                  }} catch(e) {{}}
                  setTimeout(applyPomTeslaFullscreen, 40);
                  setTimeout(applyPomTeslaFullscreen, 240);
                  if (!activeNow) setTimeout(browserFullscreenOn, 80);
                  else setTimeout(browserFullscreenOff, 80);
                }});
                document.body.appendChild(btn);
              }}
              btn.style.setProperty('background', isImmersive() ? 'rgba(230,111,72,0.78)' : 'rgba(5,10,18,0.55)', 'important');
            }};

            if (!window.__pomTeslaDashboardFullscreenChangeBound) {{
              window.__pomTeslaDashboardFullscreenChangeBound = true;
              const onFsChange = () => setTimeout(applyPomTeslaFullscreen, 50);
              document.addEventListener('fullscreenchange', onFsChange);
              document.addEventListener('webkitfullscreenchange', onFsChange);
              document.addEventListener('mozfullscreenchange', onFsChange);
              document.addEventListener('MSFullscreenChange', onFsChange);
            }}

            window.__pomTeslaDashboardFullscreenTimer = window.__pomTeslaDashboardFullscreenTimer || setInterval(applyPomTeslaFullscreen, 1500);
            setTimeout(applyPomTeslaFullscreen, 0);
            setTimeout(applyPomTeslaFullscreen, 700);
            return '';
          ]]]
"""

def apply_fullscreen_options(template: str, options: dict[str, Any]) -> str:
    controller = _build_fullscreen_controller(options)
    if not controller:
        return template
    marker = "card:\n  type: vertical-stack\n  cards:\n"
    if marker not in template:
        return template
    return template.replace(marker, marker + controller, 1)

def apply_fullscreen_options_to_drive_dashboard(template: str, options: dict[str, Any]) -> str:
    """Inject the same fullscreen controller into the standalone Drive Dashboard.

    The normal Tesla dashboard template has a top-level vertical-stack under a
    mod-card.  The Drive dashboard uses a Lovelace panel view with a nested
    vertical-stack, so the controller block must be indented to the nested
    card-list level.
    """
    controller = _build_fullscreen_controller(options)
    if not controller:
        return template
    marker = "        cards:\n"
    if marker not in template:
        return template
    indented_controller = "\n".join(("      " + line) if line.strip() else line for line in controller.rstrip("\n").splitlines()) + "\n"
    return template.replace(marker, marker + indented_controller, 1)


def _build_address_popup_card(options: dict[str, Any]) -> str:
    """Build the address popup shown from the bottom location pill.

    The popup is rendered as a fixed dashboard overlay and is intentionally
    independent from Bubble Card hash navigation. Keep this card compact: Tesla
    browser can clip tall overlays, especially when the HA top chrome is hidden.
    """
    popup_switch = str(options.get(CONF_HELPER_ADDRESS_POPUP) or AUTO_HELPER_ADDRESS_POPUP).strip()
    return """    # POM_BLOCK_START address_popup_overlay
    - type: conditional
      conditions:
        - entity: __ADDRESS_POPUP_SWITCH__
          state: \"on\"
      card:
        type: custom:mod-card
        card_mod:
          style: |
            :host {
              position: fixed !important;
              inset: 0 !important;
              z-index: 9997 !important;
              display: flex !important;
              align-items: center !important;
              justify-content: center !important;
              background: rgba(0,0,0,0.46) !important;
              backdrop-filter: blur(2px);
              -webkit-backdrop-filter: blur(2px);
              pointer-events: auto !important;
              overflow: hidden !important;
            }
            ha-card {
              width: min(1040px, calc(100vw - 150px)) !important;
              max-width: 1040px !important;
              max-height: calc(100vh - 90px) !important;
              background: rgba(43, 44, 42, 0.98) !important;
              box-shadow: 0 18px 40px rgba(0,0,0,0.35) !important;
              border: 1px solid rgba(255,255,255,0.12) !important;
              border-radius: 28px !important;
              overflow: hidden !important;
              padding: 0 !important;
              margin: 0 !important;
            }
            @media (max-width: 1143px) and (max-height: 686px) {
              ha-card {
                width: min(1000px, calc(100vw - 130px)) !important;
                transform: scale(0.92) !important;
                transform-origin: center center !important;
              }
            }
        card:
          type: vertical-stack
          cards:
            - type: custom:mod-card
              card_mod:
                style: |
                  :host {
                    position: fixed !important;
                    top: max(24px, calc((100vh - 610px) / 2 + 12px)) !important;
                    right: max(36px, calc((100vw - 1040px) / 2 + 10px)) !important;
                    width: 52px !important;
                    height: 52px !important;
                    z-index: 10050 !important;
                    pointer-events: auto !important;
                    display: block !important;
                  }
                  ha-card {
                    width: 52px !important;
                    height: 52px !important;
                    border-radius: 26px !important;
                    padding: 0 !important;
                    margin: 0 !important;
                    background: rgba(8,10,18,0.92) !important;
                    border: 1px solid rgba(255,255,255,0.18) !important;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.48) !important;
                    backdrop-filter: blur(12px) saturate(150%);
                    -webkit-backdrop-filter: blur(12px) saturate(150%);
                  }
              card:
                type: custom:button-card
                icon: mdi:close
                show_name: false
                show_state: false
                show_icon: true
                styles:
                  card:
                    - width: 52px
                    - height: 52px
                    - border-radius: 26px
                    - padding: 0
                    - background: transparent
                    - box-shadow: none
                    - border: 0
                  grid:
                    - grid-template-areas: '"i"'
                    - grid-template-columns: 52px
                    - grid-template-rows: 52px
                  img_cell:
                    - display: flex
                    - align-items: center
                    - justify-content: center
                    - width: 52px
                    - height: 52px
                  icon:
                    - color: rgba(255,255,255,0.92)
                    - width: 28px
                    - height: 28px
                tap_action:
                  action: call-service
                  service: homeassistant.turn_off
                  target:
                    entity_id: __ADDRESS_POPUP_SWITCH__
            - type: map
              entities:
                - entity: person.tesla
              hours_to_show: 15
              default_zoom: 17
              cluster: false
              theme_mode: light
              auto_fit: true
              aspect_ratio: \"3.25:1\"
              card_mod:
                style:
                  ha-map $: |
                    .leaflet-control-container {
                      display: none !important;
                    }
                    .leaflet-container {
                      border-radius: 28px 28px 0 0 !important;
                      overflow: hidden !important;
                      background: #eef3f8 !important;
                    }
                  .: |
                    ha-card {
                      border-radius: 28px 28px 0 0 !important;
                      box-shadow: none !important;
                      border: none !important;
                      overflow: hidden !important;
                      margin: 0 !important;
                    }
            - type: custom:button-card
              entity: sensor.pom_tesla_dashboard_location_label
              show_icon: false
              show_name: false
              show_state: false
              tap_action:
                action: none
              hold_action:
                action: none
              custom_fields:
                address: |
                  [[[
                    const attrs = entity?.attributes || {};
                    const source = attrs.source_entity;
                    const srcAttrs = source && states[source] ? (states[source].attributes || {}) : {};
                    const address = attrs.display_name || srcAttrs.formatted_address || srcAttrs.address || entity?.state || \"-\";
                    return `
                      <div class=\"adres-address-wrap\">
                        <div class=\"adres-icon\">
                          <ha-icon icon=\"mdi:map-marker-outline\"></ha-icon>
                        </div>
                        <div class=\"adres-text\">${address}</div>
                      </div>
                    `;
                  ]]]
                line: |
                  [[[
                    return `<div class=\"adres-divider\"></div>`;
                  ]]]
                stats: |
                  [[[
                    const attrs = entity?.attributes || {};
                    const source = attrs.source_entity;
                    const srcAttrs = source && states[source] ? (states[source].attributes || {}) : {};
                    const addressObj = attrs.address || {};
                    const first = (...values) => {
                      for (const value of values) {
                        if (value !== undefined && value !== null && String(value).trim() !== \"\") return String(value).trim();
                      }
                      return \"-\";
                    };
                    const mahalle = first(
                      addressObj.neighbourhood,
                      addressObj.quarter,
                      addressObj.suburb,
                      addressObj.city_district,
                      srcAttrs.neighbourhood,
                      srcAttrs.suburb,
                      attrs.label,
                      entity?.state
                    ).replace(\" Mahallesi\", \"\");
                    const rawDistance = parseFloat(
                      first(attrs.distance_from_home_km, srcAttrs.distance_from_home_km, srcAttrs.distance_km, \"NaN\")
                    );
                    const mesafe = Number.isFinite(rawDistance) ? rawDistance.toFixed(1) + \" km\" : \"-\";
                    const plakaRaw = first(
                      attrs.state_abbr,
                      srcAttrs.state_abbr,
                      srcAttrs.plate,
                      srcAttrs.plate_code,
                      srcAttrs.province_code,
                      addressObj[\"ISO3166-2-lvl4\"],
                      addressObj[\"ISO3166-2-lvl6\"],
                      addressObj.state,
                      \"-\"
                    );
                    const plakaClean = String(plakaRaw).replace(/^TR-/, \"\").trim();
                    const plaka = /^\\d$/.test(plakaClean) ? plakaClean.padStart(2, \"0\") : plakaClean;
                    return `
                      <div class=\"adres-stats-row\">
                        <div class=\"adres-stat-box\">
                          <div class=\"adres-stat-title\">MAHALLE</div>
                          <div class=\"adres-stat-value\">${mahalle}</div>
                        </div>
                        <div class=\"adres-stat-box\">
                          <div class=\"adres-stat-title\">MESAFE</div>
                          <div class=\"adres-stat-value\">${mesafe}</div>
                        </div>
                        <div class=\"adres-stat-box\">
                          <div class=\"adres-stat-title\">PLAKA</div>
                          <div class=\"adres-stat-value adres-plate\">${plaka}</div>
                        </div>
                      </div>
                    `;
                  ]]]
              styles:
                card:
                  - padding: 0
                  - overflow: hidden
                  - border-radius: 0 0 28px 28px
                  - background: rgba(43, 44, 42, 0.98)
                  - border: none
                  - box-shadow: none
                  - position: relative
                grid:
                  - grid-template-areas: |
                      \"address\"
                      \"line\"
                      \"stats\"
                  - grid-template-columns: 1fr
                  - grid-template-rows: auto 1px auto
                  - row-gap: 0
                custom_fields:
                  address:
                    - grid-area: address
                    - width: 100%
                    - min-width: 0
                  line:
                    - grid-area: line
                    - width: 100%
                  stats:
                    - grid-area: stats
                    - width: 100%
              extra_styles: |
                .adres-address-wrap {
                  display: flex;
                  align-items: center;
                  gap: 18px;
                  padding: 26px 36px 22px 36px;
                  box-sizing: border-box;
                  width: 100%;
                  max-width: 100%;
                  overflow: hidden;
                }
                .adres-icon {
                  width: 48px;
                  height: 48px;
                  min-width: 48px;
                  border-radius: 14px;
                  display: flex;
                  align-items: center;
                  justify-content: center;
                  background: rgba(226,214,255,0.95);
                  color: #7c3cff;
                  flex-shrink: 0;
                }
                .adres-icon ha-icon {
                  width: 26px;
                  height: 26px;
                }
                .adres-text {
                  color: #f3f3f3;
                  font-size: 22px;
                  font-weight: 700;
                  line-height: 1.32;
                  text-align: left;
                  white-space: normal;
                  word-break: break-word;
                  overflow-wrap: anywhere;
                  min-width: 0;
                  flex: 1;
                }
                .adres-divider {
                  height: 1px;
                  margin: 0 36px;
                  background: rgba(255,255,255,0.12);
                }
                .adres-stats-row {
                  display: grid;
                  grid-template-columns: repeat(3, minmax(0, 1fr));
                  gap: 14px;
                  padding: 20px 36px 28px 36px;
                  box-sizing: border-box;
                }
                .adres-stat-box {
                  height: 96px;
                  border-radius: 16px;
                  background: rgba(22,23,22,0.62);
                  display: flex;
                  flex-direction: column;
                  justify-content: center;
                  padding: 0 22px;
                  box-sizing: border-box;
                  text-align: left;
                  overflow: hidden;
                }
                .adres-stat-title {
                  color: rgba(255,255,255,0.52);
                  font-size: 17px;
                  font-weight: 800;
                  letter-spacing: 1px;
                  margin-bottom: 7px;
                }
                .adres-stat-value {
                  color: #ffffff;
                  font-size: 23px;
                  font-weight: 800;
                  line-height: 1.18;
                  white-space: normal;
                  overflow-wrap: anywhere;
                  word-break: break-word;
                }
                .adres-plate {
                  color: #6f73ff;
                  font-size: 34px;
                  font-weight: 700;
                }
                @media (max-width: 700px) {
                  .adres-address-wrap {
                    padding: 22px 24px 20px 24px;
                    gap: 14px;
                  }
                  .adres-icon {
                    width: 44px;
                    height: 44px;
                    min-width: 44px;
                  }
                  .adres-text {
                    font-size: 18px;
                    line-height: 1.32;
                  }
                  .adres-divider {
                    margin: 0 24px;
                  }
                  .adres-stats-row {
                    grid-template-columns: 1fr;
                    padding: 18px 24px 24px 24px;
                  }
                  .adres-stat-box {
                    height: 78px;
                  }
                }
    # POM_BLOCK_END address_popup_overlay
""".replace("__ADDRESS_POPUP_SWITCH__", popup_switch)



def _build_person_track_button(options: dict[str, Any]) -> str:
    """Return bottom-bar person avatar buttons that open detail popups directly."""
    if not bool(options.get(CONF_PERSON_TRACK_ENABLED, True)) or not bool(options.get(CONF_PERSON_TRACK_SHOW_BUTTON, True)):
        return ""

    blocks: list[str] = []
    for slot in (1, 2, 3):
        cfg = _person_track_slot_config(options, slot)
        show_key = {1: CONF_SHOW_BOTTOM_PERSON_TRACK_1, 2: CONF_SHOW_BOTTOM_PERSON_TRACK_2, 3: CONF_SHOW_BOTTOM_PERSON_TRACK_3}.get(slot)
        if show_key and options.get(show_key, True) is False:
            continue
        if not cfg["enabled"]:
            continue
        block = """              # POM_BLOCK_START bottom_person_track_slot___SLOT__
              - type: custom:button-card
                entity: __PERSON_ENTITY__
                show_icon: true
                show_name: false
                show_state: false
                show_entity_picture: true
                icon: mdi:account-location-outline
                styles:
                  card:
                    - height: 42px
                    - width: 42px
                    - min-width: 42px
                    - padding: 0
                    - border-radius: 21px
                    - background: transparent
                    - box-shadow: none
                    - border: 0
                    - overflow: hidden
                  grid:
                    - grid-template-areas: '"i"'
                    - grid-template-columns: 42px
                    - grid-template-rows: 42px
                  img_cell:
                    - align-self: center
                    - justify-self: center
                    - width: 42px
                    - height: 42px
                    - border-radius: 21px
                    - overflow: hidden
                    - display: flex
                    - align-items: center
                    - justify-content: center
                    - background: rgba(255,255,255,0.06)
                  entity_picture:
                    - width: 34px
                    - height: 34px
                    - border-radius: 17px
                    - object-fit: cover
                  icon:
                    - color: rgba(255,255,255,0.78)
                    - width: 22px
                    - height: 22px
                tap_action:
                  action: call-service
                  service: homeassistant.turn_on
                  target:
                    entity_id: __HELPER__
              # POM_BLOCK_END bottom_person_track_slot___SLOT__
"""
        blocks.append(
            block.replace("__SLOT__", str(slot))
                 .replace("__PERSON_ENTITY__", str(cfg["entity"]))
                 .replace("__HELPER__", str(cfg["helper"]))
        )
    if not blocks:
        return ""
    return "".join(blocks)

def _person_track_slot_config(options: dict[str, Any], slot: int) -> dict[str, str | bool | int]:
    """Return normalized dashboard person-track slot config."""
    slot_map = {
        1: (CONF_PERSON_TRACK_1_ENTITY, CONF_PERSON_TRACK_1_NAME, CONF_PERSON_TRACK_1_ENABLED, CONF_HELPER_PERSON_TRACK_POPUP_1, AUTO_HELPER_PERSON_TRACK_POPUP_1),
        2: (CONF_PERSON_TRACK_2_ENTITY, CONF_PERSON_TRACK_2_NAME, CONF_PERSON_TRACK_2_ENABLED, CONF_HELPER_PERSON_TRACK_POPUP_2, AUTO_HELPER_PERSON_TRACK_POPUP_2),
        3: (CONF_PERSON_TRACK_3_ENTITY, CONF_PERSON_TRACK_3_NAME, CONF_PERSON_TRACK_3_ENABLED, CONF_HELPER_PERSON_TRACK_POPUP_3, AUTO_HELPER_PERSON_TRACK_POPUP_3),
    }
    entity_key, name_key, enabled_key, helper_key, default_helper = slot_map[slot]
    entity = str(options.get(entity_key) or "").strip()
    name = str(options.get(name_key) or f"Person {slot}").strip() or f"Person {slot}"
    helper = str(options.get(helper_key) or default_helper).strip()
    sensor = PERSON_TRACK_SENSOR_ENTITY_IDS.get(slot, f"sensor.pom_tesla_dashboard_person_track_{slot}")
    try:
        hours = max(0, min(24, int(float(options.get(CONF_PERSON_TRACK_HOURS_TO_SHOW) or 15))))
    except (TypeError, ValueError):
        hours = 15
    return {"enabled": bool(options.get(enabled_key, False)) and bool(entity), "entity": entity, "name": name, "helper": helper, "sensor": sensor, "hours": hours}


def _build_person_track_list_item(options: dict[str, Any], slot: int) -> str:
    cfg = _person_track_slot_config(options, slot)
    if not cfg["enabled"]:
        return ""
    return """            - type: custom:button-card
              entity: __SENSOR__
              show_icon: true
              show_name: false
              show_state: false
              icon: mdi:account-location-outline
              custom_fields:
                content: |
                  [[[ 
                    const attrs = entity?.attributes || {};
                    const name = attrs.person_name || '__NAME__';
                    const dist = Number(attrs.distance_to_tesla_km);
                    const d = Number.isFinite(dist) ? `${dist.toFixed(1)} km` : '-';
                    const addr = attrs.short_address || entity?.state || '-';
                    return `<div class=\"pt-row\"><div><div class=\"pt-name\">${name}</div><div class=\"pt-addr\">${addr}</div></div><div class=\"pt-dist\">${d}</div></div>`;
                  ]]]
              styles:
                card:
                  - padding: 14px 16px
                  - border-radius: 16px
                  - background: rgba(20,22,28,0.86)
                  - border: 1px solid rgba(255,255,255,0.08)
                  - box-shadow: none
                grid:
                  - grid-template-areas: '"i content"'
                  - grid-template-columns: 36px 1fr
                  - column-gap: 12px
                icon:
                  - color: "#8b5cf6"
                  - width: 24px
                  - height: 24px
                custom_fields:
                  content:
                    - justify-self: stretch
                    - align-self: center
              extra_styles: |
                .pt-row { display:flex; align-items:center; justify-content:space-between; gap:14px; width:100%; min-height:48px; text-align:left; }
                .pt-row > div:first-child { min-width:0; flex:1; text-align:left; }
                .pt-name { color:#fff; font-size:17px; font-weight:850; line-height:1.1; text-align:left; }
                .pt-addr { color:rgba(255,255,255,0.58); font-size:13px; font-weight:650; margin-top:4px; text-align:left; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:100%; }
                .pt-dist { color:#50f5cf; font-size:16px; font-weight:850; white-space:nowrap; text-align:right; }
              tap_action:
                action: call-service
                service: homeassistant.turn_on
                target:
                  entity_id: __HELPER__
""".replace("__SENSOR__", str(cfg["sensor"])).replace("__HELPER__", str(cfg["helper"])).replace("__NAME__", str(cfg["name"]))


def _build_person_track_list_popup(options: dict[str, Any]) -> str:
    if not bool(options.get(CONF_PERSON_TRACK_ENABLED, True)):
        return ""
    list_switch = str(options.get(CONF_HELPER_PERSON_TRACK_LIST_POPUP) or AUTO_HELPER_PERSON_TRACK_LIST_POPUP).strip()
    items = "".join(_build_person_track_list_item(options, slot) for slot in (1, 2, 3)).rstrip()
    if not items:
        items = """            - type: markdown
              content: "Person Track için 17. menüden en az bir person entity ekle."
"""
    template = """    # POM_BLOCK_START person_track_list_popup
    - type: conditional
      conditions:
        - entity: __LIST_SWITCH__
          state: "on"
      card:
        type: custom:mod-card
        card_mod:
          style: |
            :host {
              position: fixed !important;
              inset: 0 !important;
              z-index: 84 !important;
              display: flex !important;
              align-items: center !important;
              justify-content: center !important;
              pointer-events: auto !important;
              background: rgba(0,0,0,0.52) !important;
              backdrop-filter: blur(6px) saturate(120%) !important;
              -webkit-backdrop-filter: blur(6px) saturate(120%) !important;
            }
            ha-card {
              width: min(560px, calc(100vw - 48px)) !important;
              background: rgba(10,13,20,0.96) !important;
              border: 1px solid rgba(255,255,255,0.10) !important;
              border-radius: 26px !important;
              box-shadow: 0 22px 70px rgba(0,0,0,0.58) !important;
              padding: 20px !important;
              overflow: hidden !important;
            }
        card:
          type: vertical-stack
          cards:
            - type: custom:button-card
              show_icon: false
              show_name: false
              show_state: false
              custom_fields:
                title: |
                  [[[ return `<div class=\"pt-titlebar\"><div><div class=\"pt-title\">Person Track</div><div class=\"pt-sub\">Adres, Tesla uzaklığı ve Google Maps bağlantısı</div></div><button>×</button></div>`; ]]]
              styles:
                card:
                  - background: transparent
                  - box-shadow: none
                  - padding: 0 0 14px 0
                custom_fields:
                  title:
                    - width: 100%
              extra_styles: |
                .pt-titlebar { display:flex; align-items:center; justify-content:space-between; gap:16px; }
                .pt-title { color:#fff; font-size:22px; font-weight:900; }
                .pt-sub { color:rgba(255,255,255,0.56); font-size:13px; font-weight:650; margin-top:4px; }
                .pt-titlebar button { width:42px; height:42px; border:0; border-radius:999px; background:rgba(255,255,255,0.08); color:#fff; font-size:28px; line-height:38px; }
              tap_action:
                action: call-service
                service: homeassistant.turn_off
                target:
                  entity_id: __LIST_SWITCH__
__ITEMS__
    # POM_BLOCK_END person_track_list_popup
"""
    return template.replace("__LIST_SWITCH__", list_switch).replace("__ITEMS__", items)


def _build_person_track_detail_popup(options: dict[str, Any], slot: int) -> str:
    cfg = _person_track_slot_config(options, slot)
    if not cfg["enabled"]:
        return ""
    template = """    # POM_BLOCK_START person_track_detail_popup___SLOT__
    - type: conditional
      conditions:
        - entity: __HELPER__
          state: "on"
      card:
        type: custom:mod-card
        card_mod:
          style: |
            :host {
              position: fixed !important;
              inset: 0 !important;
              z-index: 85 !important;
              display: flex !important;
              align-items: center !important;
              justify-content: center !important;
              pointer-events: auto !important;
              background: rgba(0,0,0,0.58) !important;
              backdrop-filter: blur(8px) saturate(120%) !important;
              -webkit-backdrop-filter: blur(8px) saturate(120%) !important;
            }
            ha-card {
              width: min(950px, calc(100vw - 70px)) !important;
              max-height: calc(100vh - 80px) !important;
              background: rgba(43,44,42,0.98) !important;
              border: 1px solid rgba(255,255,255,0.12) !important;
              border-radius: 28px !important;
              box-shadow: 0 24px 80px rgba(0,0,0,0.62) !important;
              overflow: hidden !important;
            }
        card:
          type: vertical-stack
          cards:
            - type: custom:mod-card
              card_mod:
                style: |
                  :host {
                    position: fixed !important;
                    top: max(22px, calc((100vh - 700px) / 2 + 12px)) !important;
                    right: max(42px, calc((100vw - 950px) / 2 + 10px)) !important;
                    width: 52px !important;
                    height: 52px !important;
                    z-index: 10060 !important;
                    pointer-events: auto !important;
                    display: block !important;
                  }
                  ha-card {
                    width: 52px !important;
                    height: 52px !important;
                    border-radius: 26px !important;
                    padding: 0 !important;
                    margin: 0 !important;
                    background: rgba(8,10,18,0.92) !important;
                    border: 1px solid rgba(255,255,255,0.18) !important;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.48) !important;
                    backdrop-filter: blur(12px) saturate(150%);
                    -webkit-backdrop-filter: blur(12px) saturate(150%);
                  }
              card:
                type: custom:button-card
                icon: mdi:close
                show_name: false
                show_state: false
                show_icon: true
                styles:
                  card:
                    - width: 52px
                    - height: 52px
                    - border-radius: 26px
                    - padding: 0
                    - background: transparent
                    - box-shadow: none
                    - border: 0
                  grid:
                    - grid-template-areas: '"i"'
                    - grid-template-columns: 52px
                    - grid-template-rows: 52px
                  img_cell:
                    - display: flex
                    - align-items: center
                    - justify-content: center
                    - width: 52px
                    - height: 52px
                  icon:
                    - color: rgba(255,255,255,0.92)
                    - width: 28px
                    - height: 28px
                tap_action:
                  action: call-service
                  service: homeassistant.turn_off
                  target:
                    entity_id: __HELPER__
            - type: map
              entities:
                - entity: __PERSON_ENTITY__
              hours_to_show: __HOURS__
              default_zoom: 16
              cluster: false
              theme_mode: light
              auto_fit: true
              aspect_ratio: "5:2"
              card_mod:
                style:
                  ha-map $: |
                    .leaflet-control-container { display: none !important; }
                  .: |
                    ha-card { border-radius: 28px 28px 0 0 !important; box-shadow: none !important; border: none !important; overflow: hidden !important; }
            - type: custom:button-card
              entity: __SENSOR__
              show_icon: false
              show_name: false
              show_state: false
              custom_fields:
                address: |
                  [[[ 
                    const a = entity?.attributes || {};
                    const personEntityId = '__PERSON_ENTITY__';
                    const personState = states[personEntityId];
                    const picture = personState?.attributes?.entity_picture || a.entity_picture || '';
                    const full = a.full_address || a.display_name || entity?.state || '-';
                    const name = a.person_name || personState?.attributes?.friendly_name || '__NAME__';
                    const avatar = picture
                      ? `<img class="pt-avatar-img" src="${picture}" />`
                      : `<ha-icon icon="mdi:account-location-outline"></ha-icon>`;
                    return `<div class="pt-address-wrap"><div class="pt-avatar">${avatar}</div><div class="pt-address-content"><div class="pt-person">${name}</div><div class="pt-address">${full}</div></div></div>`;
                  ]]]
                stats: |
                  [[[ 
                    const a = entity?.attributes || {};
                    const distTesla = Number(a.distance_to_tesla_km);
                    let distHome = Number(a.distance_to_home_km);
                    // If zone.home is stale/wrong but the tracked person is effectively next
                    // to the Tesla, show the Tesla distance as home distance too. This avoids
                    // bogus values like 2223 km on migrated HA installs.
                    if (Number.isFinite(distTesla) && distTesla < 1.0 && Number.isFinite(distHome) && distHome > 500) {
                      distHome = distTesla;
                    }
                    const dTesla = Number.isFinite(distTesla) ? `${distTesla.toFixed(1)} km` : '-';
                    const dHome = Number.isFinite(distHome) ? `${distHome.toFixed(1)} km` : '-';
                    const mahalle = (a.neighbourhood || a.short_address || entity?.state || '-').replace(' Mahallesi','');
                    return `<div class=\"pt-stats\"><div class=\"pt-box\"><div>MAHALLE</div><b>${mahalle}</b></div><div class=\"pt-box\"><div>TESLA UZAKLIK</div><b>${dTesla}</b></div><div class=\"pt-box\"><div>EVE UZAKLIK</div><b>${dHome}</b></div></div>`;
                  ]]]
                actions: |
                  [[[ return `<div class=\"pt-actions\"><span>Google Maps ve Telegram işlemleri</span></div>`; ]]]
              styles:
                card:
                  - padding: 0
                  - background: rgba(43,44,42,0.98)
                  - box-shadow: none
                  - border: none
                  - border-radius: 0 0 28px 28px
                  - position: relative
                grid:
                  - grid-template-areas: |
                      "address"
                      "stats"
                      "actions"
                  - grid-template-columns: 1fr
                  - grid-template-rows: auto auto auto
                custom_fields:
                  address:
                    - width: 100%
                    - justify-self: stretch
                    - text-align: left
                  stats:
                    - width: 100%
                    - justify-self: stretch
                    - text-align: center
                  actions:
                    - width: 100%
                    - justify-self: stretch
                    - text-align: center
              extra_styles: |
                .pt-address-wrap { display:flex; align-items:center; justify-content:flex-start; gap:18px; padding:28px 36px 22px 36px; border-bottom:1px solid rgba(255,255,255,.12); box-sizing:border-box; width:100%; overflow:hidden; text-align:left; }
                .pt-address-content { min-width:0; flex:1 1 auto; overflow:hidden; text-align:left; }
                .pt-avatar { width:54px; height:54px; min-width:54px; border-radius:18px; display:flex; align-items:center; justify-content:center; background:rgba(226,214,255,.95); color:#7c3cff; flex:0 0 54px; overflow:hidden; }
                .pt-avatar ha-icon { width:28px; height:28px; }
                .pt-avatar-img { width:54px; height:54px; object-fit:cover; display:block; }
                .pt-person { color:#fff; font-size:20px; font-weight:900; margin-bottom:4px; text-align:left; }
                .pt-address { color:#f3f3f3; font-size:22px; font-weight:750; line-height:1.35; text-align:left; white-space:normal; word-break:break-word; overflow-wrap:anywhere; max-width:100%; }
                .pt-stats { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px; padding:22px 36px 8px 36px; }
                .pt-box { height:92px; border-radius:16px; background:rgba(22,23,22,.62); display:flex; flex-direction:column; align-items:center; justify-content:center; padding:0 16px; text-align:center; overflow:hidden; }
                .pt-box div { color:rgba(255,255,255,.52); font-size:15px; font-weight:850; letter-spacing:1px; margin-bottom:8px; text-align:center; width:100%; }
                .pt-box b { color:#fff; font-size:24px; font-weight:900; line-height:1.18; text-align:center; width:100%; }
                .pt-actions { padding:8px 36px 28px 36px; color:rgba(255,255,255,.48); font-size:13px; font-weight:700; }
              tap_action:
                action: none
              hold_action:
                action: none
            - type: horizontal-stack
              cards:
                - type: custom:button-card
                  entity: __SENSOR__
                  name: Google Maps
                  icon: mdi:google-maps
                  tap_action:
                    action: url
                    url_path: |
                      [[[ return entity?.attributes?.google_maps_url || 'https://www.google.com/maps'; ]]]
                  styles:
                    card:
                      - margin: 0 0 28px 36px
                      - height: 54px
                      - border-radius: 16px
                      - background: rgba(33,104,184,0.88)
                      - color: white
                    name:
                      - font-weight: 900
                - type: custom:button-card
                  entity: __SENSOR__
                  name: Telegram'a gönder
                  icon: mdi:telegram
                  tap_action:
                    action: call-service
                    service: pom_tesla_report.send_dashboard_person_track_telegram
                    data:
                      slot: __SLOT__
                  styles:
                    card:
                      - margin: 0 36px 28px 0
                      - height: 54px
                      - border-radius: 16px
                      - background: rgba(34,197,94,0.84)
                      - color: white
                    name:
                      - font-weight: 900
    # POM_BLOCK_END person_track_detail_popup___SLOT__
"""
    return (template
        .replace("__SLOT__", str(slot))
        .replace("__HELPER__", str(cfg["helper"]))
        .replace("__PERSON_ENTITY__", str(cfg["entity"]))
        .replace("__SENSOR__", str(cfg["sensor"]))
        .replace("__HOURS__", str(cfg["hours"]))
        .replace("__NAME__", str(cfg["name"]))
    )


def _build_person_track_popups(options: dict[str, Any]) -> str:
    if not bool(options.get(CONF_PERSON_TRACK_ENABLED, True)):
        return ""
    parts: list[str] = []
    for slot in (1, 2, 3):
        detail = _build_person_track_detail_popup(options, slot)
        if detail:
            parts.append(detail)
    return "\n".join(part.rstrip() for part in parts if part).rstrip() + "\n"

def apply_person_track_options(template: str, options: dict[str, Any]) -> str:
    """Insert person track bottom button and popups."""
    if "# POM_BLOCK_START bottom_person_track_slot_" not in template:
        button = _build_person_track_button(options)
        if button:
            marker = "              # POM_BLOCK_START bottom_charging"
            if marker in template:
                template = template.replace(marker, button + marker, 1)
    if "# POM_BLOCK_START person_track_detail_popup_" not in template:
        popups = _build_person_track_popups(options)
        if popups:
            marker = "view_layout:\n  grid-area: sidebar"
            pos = template.rfind(marker)
            if pos >= 0:
                template = template[:pos] + popups + template[pos:]
            else:
                template = template.rstrip() + "\n" + popups
    return template

def apply_address_popup_options(template: str, options: dict[str, Any]) -> str:
    """Wire the location pill and insert the address popup overlay.

    This mirrors the working charge-popup path: the generated dashboard must
    target the actual helper switch entity id because repeated test installs
    can leave Home Assistant using a suffixed entity id such as
    switch.pom_tesla_dashboard_address_popup_2.
    """
    popup_switch = str(options.get(CONF_HELPER_ADDRESS_POPUP) or AUTO_HELPER_ADDRESS_POPUP).strip()
    result = template.replace("entity_id: switch.pom_tesla_dashboard_address_popup", f"entity_id: {popup_switch}")
    if "# POM_BLOCK_START address_popup_overlay" in result:
        return result
    popup = _build_address_popup_card(options).rstrip() + "\n"
    marker = "view_layout:\n  grid-area: sidebar"
    pos = result.rfind(marker)
    if pos >= 0:
        return result[:pos] + popup + result[pos:]
    marker2 = "\nview_layout:"
    if marker2 in result:
        return result.replace(marker2, "\n" + popup + "view_layout:", 1)
    return result.rstrip() + "\n" + popup

def apply_template_options(template: str, options: dict[str, Any]) -> str:
    """Apply safe literal entity/asset replacements to the original dashboard template."""
    result = template
    for old, conf_key in sorted(ENTITY_REPLACEMENTS.items(), key=lambda item: len(item[0]), reverse=True):
        result = _replace_entity_token(result, old, str(options.get(conf_key) or old).strip())

    # Dashboard helper controls are now auto-created switch entities, not input_booleans.
    # `homeassistant.toggle` works for both switch.* and input_boolean.* targets, so it
    # avoids service/domain mismatch when old template buttons are migrated to switches.
    result = result.replace("service: input_boolean.toggle", "service: homeassistant.toggle")

    for old, conf_key in ASSET_REPLACEMENTS.items():
        new = str(options.get(conf_key) or old).strip()
        new = _cache_bust_bundled_asset_url(new)
        if new and new != old:
            result = result.replace(old, new)
    return result


def _wrap_card_template(template: str, title: str, options: dict[str, Any] | None = None) -> str:
    """Wrap a single Lovelace card YAML into a full YAML dashboard."""
    title = str(title or DEFAULT_DASHBOARD_TITLE).strip() or DEFAULT_DASHBOARD_TITLE
    template = template.rstrip() + "\n"
    lines = template.splitlines()
    body: list[str] = []
    for index, line in enumerate(lines):
        if index == 0:
            body.append("      - " + line)
        else:
            body.append("        " + line)
    return (
        f"title: {title}\n"
        "views:\n"
        f"  - title: {title}\n"
        "    path: tesla\n"
        "    type: panel\n"
        "    cards:\n"
        + "\n".join(body)
        + "\n"
    )

def build_dashboard_yaml(options: dict[str, Any]) -> str:
    """Build full dashboard YAML from the original Berkan Tesla dashboard template."""
    options = merged_options(options)
    template_path = Path(__file__).resolve().parent / "dashboard_template.yaml"
    template = template_path.read_text(encoding="utf-8")
    template = apply_fullscreen_options(template, options)
    template = apply_top_gauge_options(template, options)
    template = apply_bottom_slot_options(template, options)
    template = apply_sidebar_slot_options(template, options)
    template = apply_map_options(template, options)
    template = apply_visibility_options(template, options)
    template = apply_charge_popup_options(template, options)
    template = apply_energy_field_popup_options(template, options)
    template = apply_address_popup_options(template, options)
    template = apply_person_track_options(template, options)
    template = apply_youtube_driving_background(template, options)
    template = apply_template_options(template, options)
    return _wrap_card_template(template, str(options.get(CONF_DASHBOARD_TITLE) or DEFAULT_DASHBOARD_TITLE), options)


def bundled_asset_source_path() -> Path:
    """Return the package-local bundled PNG/GIF directory."""
    return Path(__file__).resolve().parent / "png"


def get_bundled_asset_help_text() -> str:
    """Return readable asset URL help text."""
    return (
        "Bundled backgrounds are served directly from this integration; no /local copy is needed.\n"
        f"Parked: `{BUNDLED_IMAGE_PARKED}`\n"
        f"Charging: `{BUNDLED_IMAGE_CHARGING}`\n"
        f"Driving: `{BUNDLED_IMAGE_DRIVING}`\n\n"
        "To use custom images, put them under `/config/www/...` and enter their `/local/...` URL here, "
        "or enter any externally reachable image/GIF URL."
    )


async def async_copy_bundled_assets(hass: HomeAssistant, options: dict[str, Any] | None = None) -> list[str]:
    """Legacy no-op. Assets are now served directly from the integration static path."""
    return []


def check_custom_dependencies(hass: HomeAssistant) -> str:
    """Return a readable status report for required dashboard custom cards."""
    lines: list[str] = []
    missing: list[str] = []
    for dep in CUSTOM_DEPENDENCIES:
        paths = dep.get("local_checks", [])
        found_path = ""
        for relative_path in paths:
            if Path(hass.config.path(relative_path)).exists():
                found_path = relative_path
                break
        if found_path:
            lines.append(f"✅ {dep['name']} ({dep['type']})\nFound: /config/{found_path}")
        else:
            lines.append(f"❌ {dep['name']} ({dep['type']})\nInstall: {dep['github']}")
            missing.append(str(dep["name"]))
    if missing:
        header = "Missing custom dashboard dependencies detected. Install these before using the Tesla dashboard fully:\n"
    else:
        header = "All checked custom dashboard dependencies were detected:\n"
    return header + "\n\n".join(lines)


async def async_show_dependency_notification(hass: HomeAssistant) -> None:
    """Show a persistent notification with dependency status."""
    status = check_custom_dependencies(hass)
    persistent_notification.async_create(
        hass,
        status.replace("\n", "\n\n"),
        title="POM Tesla Dashboard - Custom card dependencies",
        notification_id="pom_tesla_dashboard_dependencies",
    )


def _actual_dashboard_helper_entities(hass: HomeAssistant, options: dict[str, Any]) -> dict[str, Any]:
    """Return options with the actual runtime helper switch entity IDs.

    On repeated install/uninstall cycles Home Assistant can keep old entity
    registry entries and assign suffixes like switch.pom_tesla_dashboard_controls_2.
    The dashboard must target the actual entity IDs, otherwise button presses
    toggle non-existing helpers and conditional cards never change.
    """
    data = merged_options(options)
    helper_map = {
        "map": (CONF_HELPER_MAP, AUTO_HELPER_MAP),
        "person_cards_on_map": (CONF_HELPER_PERSON_CARDS, AUTO_HELPER_PERSON_CARDS),
        "interactive_map": (CONF_HELPER_INTERACTIVE_MAP, AUTO_HELPER_INTERACTIVE_MAP),
        "controls": (CONF_HELPER_CONTROLS, AUTO_HELPER_CONTROLS),
        "charge_popup": (CONF_HELPER_CHARGE_POPUP, AUTO_HELPER_CHARGE_POPUP),
        "address_popup": (CONF_HELPER_ADDRESS_POPUP, AUTO_HELPER_ADDRESS_POPUP),
        "fullscreen": (CONF_HELPER_FULLSCREEN, AUTO_HELPER_FULLSCREEN),
        "energy_slot_choice": (CONF_HELPER_ENERGY_SLOT_SELECT, AUTO_HELPER_ENERGY_SLOT_SELECT),
    }

    # First prefer live states because they prove the entity exists right now.
    try:
        for state in list(hass.states.async_all("switch")) + list(hass.states.async_all("select")):
            if state.attributes.get("dashboard_helper") is True or state.attributes.get("dashboard_live_select") is True:
                helper_key = str(state.attributes.get("helper_key") or state.attributes.get("slot_key") or "")
                if helper_key == "energy_field":
                    helper_key = "energy_slot_choice"
                if helper_key in helper_map:
                    conf_key, _default_entity_id = helper_map[helper_key]
                    data[conf_key] = state.entity_id
    except Exception:  # pragma: no cover - defensive only
        pass

    # Fallback to entity registry if states are not populated at write time.
    try:
        from homeassistant.helpers import entity_registry as er

        registry = er.async_get(hass)
        for entity_entry in registry.entities.values():
            if getattr(entity_entry, "platform", "") != DOMAIN:
                continue
            entity_id = str(getattr(entity_entry, "entity_id", "") or "")
            if not (entity_id.startswith("switch.") or entity_id.startswith("select.")):
                continue
            unique_id = str(getattr(entity_entry, "unique_id", "") or "")
            for helper_key, (conf_key, default_entity_id) in helper_map.items():
                if (
                    unique_id == f"{DOMAIN}_{helper_key}"
                    or unique_id.endswith(f"_{helper_key}")
                    or entity_id == default_entity_id
                    or entity_id.startswith(default_entity_id + "_")
                ):
                    # Do not override a live-state match unless the conf still has
                    # the default. Live states are more authoritative.
                    if data.get(conf_key) == default_entity_id:
                        data[conf_key] = entity_id
    except Exception:  # pragma: no cover - defensive only
        pass

    return data


def _write_dashboard_file_sync(path: Path, options: dict[str, Any]) -> None:
    """Build and write the dashboard file synchronously.

    This helper is intentionally run in Home Assistant's executor from
    async_write_dashboard because it reads template files and writes YAML.
    Doing pathlib read_text/write_text directly inside the event loop can
    break setup on newer Home Assistant versions.
    """
    yaml_text = build_dashboard_yaml(options)
    path.write_text(yaml_text, encoding="utf-8")


async def async_write_dashboard(hass: HomeAssistant, options: dict[str, Any]) -> Path:
    """Write dashboard YAML file without blocking the Home Assistant event loop."""
    options = _actual_dashboard_helper_entities(hass, options)
    path = dashboard_path(hass, options)
    await hass.async_add_executor_job(_write_dashboard_file_sync, path, options)
    return path


async def async_show_install_notification(hass: HomeAssistant, options: dict[str, Any]) -> None:
    """Silently acknowledge dashboard YAML generation.

    Dashboard YAML can be regenerated often from startup, settings, services or
    panel actions. Do not create the old persistent notification every time; keep
    this helper for backwards-compatible callers and dismiss any stale legacy
    dashboard notification if it is still visible.
    """
    options = merged_options(options)
    path = dashboard_path(hass, options)
    try:
        async_dismiss = getattr(persistent_notification, "async_dismiss", None)
        if async_dismiss is not None:
            async_dismiss(hass, "pom_tesla_report_dashboard")
    except Exception:
        pass
    try:
        import logging
        logging.getLogger(__name__).info("POM Tesla dashboard YAML generated silently at %s", path)
    except Exception:
        pass
