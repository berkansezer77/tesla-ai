"""Dashboard constants for POM Tesla Report."""

DOMAIN = "pom_tesla_report"
STATIC_ASSET_URL_PATH = "/pom_tesla_report/dashboard/png"
LOCATION_LABEL_ENTITY_ID = "sensor.pom_tesla_dashboard_location_label"
BUNDLED_IMAGE_PARKED = f"{STATIC_ASSET_URL_PATH}/tesla.png"
BUNDLED_IMAGE_CHARGING = f"{STATIC_ASSET_URL_PATH}/teslacharging.gif"
BUNDLED_IMAGE_DRIVING = f"{STATIC_ASSET_URL_PATH}/tesladriving.gif"
DEFAULT_DASHBOARD_TITLE = "Tesla"
DEFAULT_DASHBOARD_FILENAME = "pom_tesla_dashboard.yaml"

CONF_DASHBOARD_TITLE = "dashboard_title"
CONF_DASHBOARD_FILENAME = "dashboard_filename"
CONF_REBUILD_ON_SAVE = "rebuild_on_save"
CONF_SECTION = "section"
CONF_ACTION = "action"

# Fullscreen dashboard chrome control
CONF_FULLSCREEN_ENABLED = "fullscreen_enabled"
CONF_FULLSCREEN_HIDE_HEADER = "fullscreen_hide_header"
CONF_FULLSCREEN_HIDE_SIDEBAR = "fullscreen_hide_sidebar"
CONF_FULLSCREEN_DISABLE_SCROLL = "fullscreen_disable_scroll"
CONF_FULLSCREEN_SHOW_BUTTON = "fullscreen_show_button"
CONF_HELPER_FULLSCREEN = "helper_fullscreen"

# Main/top entities
CONF_ENTITY_POWER = "entity_power"
CONF_ENTITY_ELEVATION = "entity_elevation"
CONF_ENTITY_SPEED = "entity_speed"
CONF_ENTITY_BATTERY_LEVEL = "entity_battery_level"
CONF_ENTITY_EST_RANGE = "entity_est_range"
CONF_ENTITY_RATED_RANGE = "entity_rated_range"
CONF_ENTITY_ENERGY_REMAINING = "entity_energy_remaining"
CONF_ENTITY_INSIDE_TEMP = "entity_inside_temp"
CONF_ENTITY_BATTERY_TEMP = "entity_battery_temp"
CONF_ENTITY_OUTSIDE_TEMP = "entity_outside_temp"
CONF_ENTITY_ODOMETER = "entity_odometer"
CONF_ENTITY_BATTERY_HEATER = "entity_battery_heater"
CONF_ENTITY_LOCATION_SENSOR = "entity_location_sensor"
CONF_ENTITY_CHARGING = "entity_charging"
CONF_ENTITY_PLUGGED_IN = "entity_plugged_in"
CONF_ENTITY_SHIFT_STATE = "entity_shift_state"
CONF_ENTITY_LIVE_TRIP = "entity_live_trip"


# Top gauge/header configurable slots
CONF_TOP_LEFT_SLOT_1 = "top_left_slot_1"
CONF_TOP_LEFT_SLOT_2 = "top_left_slot_2"
CONF_TOP_CENTER_SLOT = "top_center_slot"
CONF_TOP_RIGHT_SLOT_1 = "top_right_slot_1"
CONF_TOP_RIGHT_SLOT_2 = "top_right_slot_2"
CONF_TOP_FONT_SCALE = "top_font_scale"
CONF_TOP_LEFT_FONT_SCALE = "top_left_font_scale"
CONF_TOP_CENTER_FONT_SCALE = "top_center_font_scale"
CONF_TOP_RIGHT_FONT_SCALE = "top_right_font_scale"

TOP_SLOT_TYPES = {
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

CENTER_GAUGE_SLOT_TYPES = {
    "speed": "Speed",
    "battery_level": "Battery level",
    "power": "Power",
    "energy_remaining": "Energy remaining",
    "empty": "Empty / hidden",
}

# Map/person helpers
CONF_ENTITY_PERSON_TESLA = "entity_person_tesla"
CONF_ENTITY_PERSON_2 = "entity_person_2"
CONF_ENTITY_PERSON_3 = "entity_person_3"
CONF_TESLA_MAP_HOURS_TO_SHOW = "tesla_map_hours_to_show"
CONF_PERSON_MAP_HOURS_TO_SHOW = "person_map_hours_to_show"
CONF_MAP_THEME_MODE = "map_theme_mode"
MAP_THEME_DARK = "dark"
MAP_THEME_LIGHT = "light"
DEFAULT_MAP_THEME_MODE = MAP_THEME_DARK
MAP_THEME_MODES = {
    MAP_THEME_DARK: "Dark / eski okunabilir dashboard haritası",
    MAP_THEME_LIGHT: "Light / gündüz haritası",
}
CONF_HELPER_MAP = "helper_map"
CONF_HELPER_PERSON_CARDS = "helper_person_cards"
CONF_HELPER_INTERACTIVE_MAP = "helper_interactive_map"
CONF_HELPER_CONTROLS = "helper_controls"
CONF_HELPER_ENERGY_SLOT_SELECT = "helper_energy_slot_select"

# Auto-created dashboard switch entity IDs
AUTO_HELPER_MAP = "switch.pom_tesla_dashboard_map"
AUTO_HELPER_PERSON_CARDS = "switch.pom_tesla_dashboard_person_cards_on_map"
AUTO_HELPER_INTERACTIVE_MAP = "switch.pom_tesla_dashboard_interactive_map"
AUTO_HELPER_CONTROLS = "switch.pom_tesla_dashboard_controls"
AUTO_HELPER_CHARGE_POPUP = "switch.pom_tesla_dashboard_charge_popup"
AUTO_HELPER_ADDRESS_POPUP = "switch.pom_tesla_dashboard_address_popup"
AUTO_HELPER_FULLSCREEN = "switch.pom_tesla_dashboard_fullscreen"
AUTO_HELPER_ENERGY_SLOT_SELECT = "select.pom_tesla_dashboard_energy_slot_choice"

# Charging popup
CONF_HELPER_CHARGE_POPUP = "helper_charge_popup"
CONF_HELPER_ADDRESS_POPUP = "helper_address_popup"
CONF_ENABLE_CHARGE_POPUP = "enable_charge_popup"
CONF_CHARGE_BATTERY_LEVEL = "charge_battery_level"
CONF_CHARGE_BATTERY_RANGE = "charge_battery_range"
CONF_CHARGE_BATTERY_RANGE_ESTIMATE = "charge_battery_range_estimate"
CONF_CHARGE_ENERGY_ADDED = "charge_energy_added"
CONF_CHARGE_CHARGER_POWER = "charge_charger_power"
CONF_CHARGE_BATTERY_PACK_VOLTAGE = "charge_battery_pack_voltage"
CONF_CHARGE_CABLE = "charge_cable"
CONF_CHARGE_RATE = "charge_rate"
CONF_CHARGE_CURRENT = "charge_current"
CONF_CHARGE_VOLTAGE = "charge_voltage"
CONF_CHARGE_TIME_TO_FULL = "charge_time_to_full"
CONF_CHARGE_SUPERCHARGER_PRICE = "charge_supercharger_price"
CONF_CHARGE_ZES_PRICE = "charge_zes_price"
CONF_CHARGE_ASTOR_PRICE = "charge_astor_price"

# Control/sidebar entities
CONF_ENTITY_FLASH_LIGHTS = "entity_flash_lights"
CONF_ENTITY_FLASH_LIGHTS_STATE = "entity_flash_lights_state"
CONF_ENTITY_SENTRY = "entity_sentry"
CONF_ENTITY_HONK = "entity_honk"
CONF_ENTITY_HONK_STATE = "entity_honk_state"
CONF_ENTITY_FART = "entity_fart"
CONF_ENTITY_FART_STATE = "entity_fart_state"
CONF_ENTITY_WINDOWS_OPEN = "entity_windows_open"
CONF_ENTITY_DOORS_OPEN = "entity_doors_open"
CONF_ENTITY_HOME_AUTOMATION = "entity_home_automation"
CONF_ENTITY_MANUAL_TRACKING = "entity_manual_tracking"
CONF_ENTITY_HORN = "entity_horn"
CONF_ENTITY_REAR_MIDDLE_SEAT_HEATER = "entity_rear_middle_seat_heater"
CONF_ENTITY_REAR_RIGHT_SEAT_HEATER = "entity_rear_right_seat_heater"
CONF_ENTITY_REAR_LEFT_SEAT_HEATER = "entity_rear_left_seat_heater"
CONF_ENTITY_RIGHT_SEAT_HEATER = "entity_right_seat_heater"
CONF_ENTITY_LEFT_SEAT_HEATER = "entity_left_seat_heater"
CONF_ENTITY_CHARGE_CABLE_LOCK = "entity_charge_cable_lock"
CONF_ENTITY_CHARGE_PORT = "entity_charge_port"
CONF_ENTITY_VALET_MODE = "entity_valet_mode"
CONF_ENTITY_WAKE = "entity_wake"
CONF_ENTITY_HOMELINK = "entity_homelink"
CONF_ENTITY_DEFROST = "entity_defrost"
CONF_ENTITY_STEERING_HEATER = "entity_steering_heater"
CONF_ENTITY_HOME_ENTITY_1 = "entity_home_entity_1"
CONF_ENTITY_HOME_ENTITY_2 = "entity_home_entity_2"
CONF_ENTITY_HOME_ENTITY_3 = "entity_home_entity_3"
CONF_ENTITY_HOME_ENTITY_1_ICON = "entity_home_entity_1_icon"
CONF_ENTITY_HOME_ENTITY_2_ICON = "entity_home_entity_2_icon"
CONF_ENTITY_HOME_ENTITY_3_ICON = "entity_home_entity_3_icon"

CONF_SIDEBAR_SLOT_1 = "sidebar_slot_1"
CONF_SIDEBAR_SLOT_2 = "sidebar_slot_2"
CONF_SIDEBAR_SLOT_3 = "sidebar_slot_3"
CONF_SIDEBAR_SLOT_4 = "sidebar_slot_4"
CONF_SIDEBAR_SLOT_5 = "sidebar_slot_5"
CONF_SIDEBAR_SLOT_6 = "sidebar_slot_6"
CONF_SIDEBAR_SLOT_7 = "sidebar_slot_7"
CONF_SIDEBAR_SLOT_8 = "sidebar_slot_8"
SIDEBAR_SLOT_KEYS = [
    CONF_SIDEBAR_SLOT_1,
    CONF_SIDEBAR_SLOT_2,
    CONF_SIDEBAR_SLOT_3,
    CONF_SIDEBAR_SLOT_4,
    CONF_SIDEBAR_SLOT_5,
    CONF_SIDEBAR_SLOT_6,
    CONF_SIDEBAR_SLOT_7,
    CONF_SIDEBAR_SLOT_8,
]

SIDEBAR_ACTION_TYPES = {
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
    "homelink": "Homelink",
    "defrost": "Defrost",
    "steering_heater": "Steering wheel heater",
    "home_entity_1": "Home entity 1",
    "home_entity_2": "Home entity 2",
    "home_entity_3": "Home entity 3",
}

SIDEBAR_ACTION_CONFIG = {
    "honk": {"entity": CONF_ENTITY_HONK, "icon": "mdi:bullhorn-outline"},
    "flash_lights": {"entity": CONF_ENTITY_FLASH_LIGHTS, "state_entity": CONF_ENTITY_FLASH_LIGHTS_STATE, "icon": "mdi:car-light-high"},
    "sentry": {"entity": CONF_ENTITY_SENTRY, "icon": "mdi:record-circle-outline"},
    "horn": {"entity": CONF_ENTITY_HORN, "icon": "mdi:volume-high"},
    "fart": {"entity": CONF_ENTITY_FART, "state_entity": CONF_ENTITY_FART_STATE, "icon": "mdi:emoticon-poop-outline"},
    "windows": {"entity": CONF_ENTITY_WINDOWS_OPEN, "icon_on": "mdi:window-open", "icon": "mdi:window-closed"},
    "rear_middle_seat_heater": {"entity": CONF_ENTITY_REAR_MIDDLE_SEAT_HEATER, "icon": "mdi:car-seat-heater"},
    "rear_right_seat_heater": {"entity": CONF_ENTITY_REAR_RIGHT_SEAT_HEATER, "icon": "mdi:car-seat-heater"},
    "rear_left_seat_heater": {"entity": CONF_ENTITY_REAR_LEFT_SEAT_HEATER, "icon": "mdi:car-seat-heater"},
    "right_seat_heater": {"entity": CONF_ENTITY_RIGHT_SEAT_HEATER, "icon": "mdi:car-seat-heater"},
    "left_seat_heater": {"entity": CONF_ENTITY_LEFT_SEAT_HEATER, "icon": "mdi:car-seat-heater"},
    "charge_cable_lock": {"entity": CONF_ENTITY_CHARGE_CABLE_LOCK, "icon": "mdi:lock"},
    "charge_port": {"entity": CONF_ENTITY_CHARGE_PORT, "icon": "mdi:ev-plug-type2"},
    "valet_mode": {"entity": CONF_ENTITY_VALET_MODE, "icon": "mdi:account-key-outline"},
    "wake": {"entity": CONF_ENTITY_WAKE, "icon": "mdi:power"},
    "homelink": {"entity": CONF_ENTITY_HOMELINK, "icon": "mdi:garage"},
    "defrost": {"entity": CONF_ENTITY_DEFROST, "icon": "mdi:snowflake-melt"},
    "steering_heater": {"entity": CONF_ENTITY_STEERING_HEATER, "icon": "mdi:steering"},
    "home_entity_1": {"entity": CONF_ENTITY_HOME_ENTITY_1, "icon": "mdi:home-automation"},
    "home_entity_2": {"entity": CONF_ENTITY_HOME_ENTITY_2, "icon": "mdi:home-lightning-bolt"},
    "home_entity_3": {"entity": CONF_ENTITY_HOME_ENTITY_3, "icon": "mdi:home-circle"},
}

# Location label / OpenStreetMap reverse geocoding
CONF_LOCATION_DISPLAY_MODE = "location_display_mode"
CONF_LOCATION_UPDATE_INTERVAL_MINUTES = "location_update_interval_minutes"
DEFAULT_LOCATION_UPDATE_INTERVAL_MINUTES = 5

LOCATION_DISPLAY_MODES = {
    "auto_short": "Auto short address",
    "neighbourhood": "Neighborhood / quarter",
    "suburb": "Suburb",
    "district": "District",
    "city": "City / town",
    "road": "Road / street",
}

# Visuals
CONF_IMAGE_CHARGING = "image_charging"
CONF_IMAGE_PARKED = "image_parked"
CONF_IMAGE_DRIVING = "image_driving"
CONF_YOUTUBE_DRIVING_BG_ENABLED = "youtube_driving_bg_enabled"
CONF_YOUTUBE_DRIVING_BG_VIDEO = "youtube_driving_bg_video"
CONF_YOUTUBE_DRIVING_BG_START_SECONDS = "youtube_driving_bg_start_seconds"
CONF_YOUTUBE_DRIVING_BG_MUTE = "youtube_driving_bg_mute"
CONF_YOUTUBE_DRIVING_BG_LOOP = "youtube_driving_bg_loop"
CONF_YOUTUBE_DRIVING_BG_QUALITY = "youtube_driving_bg_quality"

# Sidebar visibility toggles
CONF_SHOW_FLASH_LIGHTS = "show_flash_lights"
CONF_SHOW_SENTRY = "show_sentry"
CONF_SHOW_HONK = "show_honk"
CONF_SHOW_FART = "show_fart"
CONF_SHOW_WINDOWS = "show_windows"
CONF_SHOW_DOORS = "show_doors"
CONF_SHOW_HOME_AUTOMATION = "show_home_automation"
CONF_SHOW_MANUAL_TRACKING = "show_manual_tracking"

# Bottom bar visibility toggles
CONF_SHOW_BOTTOM_RANGE = "show_bottom_range"
CONF_SHOW_BOTTOM_ENERGY = "show_bottom_energy"
CONF_SHOW_BOTTOM_INSIDE_TEMP = "show_bottom_inside_temp"
CONF_SHOW_BOTTOM_BATTERY_TEMP = "show_bottom_battery_temp"
CONF_SHOW_BOTTOM_LOCATION = "show_bottom_location"
CONF_SHOW_BOTTOM_MAP_TOGGLE = "show_bottom_map_toggle"
CONF_SHOW_BOTTOM_CONTROLS = "show_bottom_controls"
CONF_SHOW_BOTTOM_PERSON_TOGGLE = "show_bottom_person_toggle"
CONF_SHOW_BOTTOM_PERSON_CARDS = "show_bottom_person_cards"
CONF_SHOW_BOTTOM_CHARGING = "show_bottom_charging"
CONF_SHOW_BOTTOM_PERSON_TRACK_1 = "show_bottom_person_track_1"
CONF_SHOW_BOTTOM_PERSON_TRACK_2 = "show_bottom_person_track_2"
CONF_SHOW_BOTTOM_PERSON_TRACK_3 = "show_bottom_person_track_3"

# Middle bottom bar configurable slots
CONF_BOTTOM_SLOT_1 = "bottom_slot_1"
CONF_BOTTOM_SLOT_2 = "bottom_slot_2"
CONF_BOTTOM_SLOT_3 = "bottom_slot_3"

BOTTOM_SLOT_TYPES = {
    "energy_remaining": "Energy remaining",
    "inside_temp": "Inside temperature",
    "battery_temp": "Battery/module temperature",
    "outside_temp": "Outside temperature",
    "odometer": "Odometer",
    "battery_heater": "Battery heater",
    "empty": "Empty / hidden",
}



# Dashboard Person Track
CONF_PERSON_TRACK_ENABLED = "person_track_enabled"
CONF_PERSON_TRACK_SHOW_BUTTON = "person_track_show_button"
CONF_PERSON_TRACK_HOURS_TO_SHOW = "person_track_hours_to_show"
CONF_HELPER_PERSON_TRACK_LIST_POPUP = "helper_person_track_list_popup"
CONF_HELPER_PERSON_TRACK_POPUP_1 = "helper_person_track_popup_1"
CONF_HELPER_PERSON_TRACK_POPUP_2 = "helper_person_track_popup_2"
CONF_HELPER_PERSON_TRACK_POPUP_3 = "helper_person_track_popup_3"

CONF_PERSON_TRACK_1_ENTITY = "person_track_1_entity"
CONF_PERSON_TRACK_1_NAME = "person_track_1_name"
CONF_PERSON_TRACK_1_ENABLED = "person_track_1_enabled"
CONF_PERSON_TRACK_2_ENTITY = "person_track_2_entity"
CONF_PERSON_TRACK_2_NAME = "person_track_2_name"
CONF_PERSON_TRACK_2_ENABLED = "person_track_2_enabled"
CONF_PERSON_TRACK_3_ENTITY = "person_track_3_entity"
CONF_PERSON_TRACK_3_NAME = "person_track_3_name"
CONF_PERSON_TRACK_3_ENABLED = "person_track_3_enabled"

PERSON_TRACK_SLOTS = (
    (1, CONF_PERSON_TRACK_1_ENTITY, CONF_PERSON_TRACK_1_NAME, CONF_PERSON_TRACK_1_ENABLED),
    (2, CONF_PERSON_TRACK_2_ENTITY, CONF_PERSON_TRACK_2_NAME, CONF_PERSON_TRACK_2_ENABLED),
    (3, CONF_PERSON_TRACK_3_ENTITY, CONF_PERSON_TRACK_3_NAME, CONF_PERSON_TRACK_3_ENABLED),
)

AUTO_HELPER_PERSON_TRACK_LIST_POPUP = "switch.pom_tesla_dashboard_person_track_popup"
AUTO_HELPER_PERSON_TRACK_POPUP_1 = "switch.pom_tesla_dashboard_person_track_1_popup"
AUTO_HELPER_PERSON_TRACK_POPUP_2 = "switch.pom_tesla_dashboard_person_track_2_popup"
AUTO_HELPER_PERSON_TRACK_POPUP_3 = "switch.pom_tesla_dashboard_person_track_3_popup"

PERSON_TRACK_SENSOR_ENTITY_IDS = {
    1: "sensor.pom_tesla_dashboard_person_track_1",
    2: "sensor.pom_tesla_dashboard_person_track_2",
    3: "sensor.pom_tesla_dashboard_person_track_3",
}

# Missing/custom dependency metadata
CONF_DEPENDENCY_STATUS = "dependency_status"
CONF_DEPENDENCY_STATUS_FIELD = "dependency_status_field"

CUSTOM_DEPENDENCIES = [
    {
        "name": "Button Card",
        "type": "custom:button-card",
        "github": "https://github.com/custom-cards/button-card",
        "local_checks": [
            "www/community/button-card/button-card.js",
            "www/community/button-card/button-card.js.gz",
        ],
    },
    {
        "name": "Card Mod",
        "type": "card_mod + custom:mod-card",
        "github": "https://github.com/thomasloven/lovelace-card-mod",
        "local_checks": [
            "www/community/lovelace-card-mod/card-mod.js",
            "www/community/lovelace-card-mod/card-mod.js.gz",
            "www/community/card-mod/card-mod.js",
        ],
    },
    {
        "name": "Bubble Card",
        "type": "custom:bubble-card",
        "github": "https://github.com/Clooos/Bubble-Card",
        "local_checks": [
            "www/community/Bubble-Card/bubble-card.js",
            "www/community/bubble-card/bubble-card.js",
            "www/community/Bubble-Card/bubble-card.js.gz",
            "www/community/bubble-card/bubble-card.js.gz",
        ],
    },
    {
        "name": "POM Tesla Trip Report Card",
        "type": "custom:pom-tesla-trip-report-card",
        "github": "Bundled with POM Tesla Report integration",
        "local_checks": [
            "www/pom_tesla_report/pom-tesla-trip-report-card.js",
            "www/community/pom_tesla_report/pom-tesla-trip-report-card.js",
            "custom_components/pom_tesla_report/www/pom-tesla-trip-report-card.js",
        ],
    },
    {
        "name": "POM Tesla Live Trip Card Alias",
        "type": "custom:pom-tesla-live-trip-card",
        "github": "Bundled with POM Tesla Report integration",
        "local_checks": [
            "www/pom_tesla_report/pom-tesla-live-trip-card.js",
            "www/community/pom_tesla_report/pom-tesla-live-trip-card.js",
            "custom_components/pom_tesla_report/www/pom-tesla-live-trip-card.js",
        ],
    },
]

BUNDLED_ASSET_FILENAMES = [
    "tesla.png",
    "teslacharging.gif",
    "tesladriving.gif",
]
BUNDLED_ASSET_TARGET_DIR = "www/png"

DEFAULT_OPTIONS = {
    CONF_DASHBOARD_TITLE: DEFAULT_DASHBOARD_TITLE,
    CONF_DASHBOARD_FILENAME: DEFAULT_DASHBOARD_FILENAME,
    CONF_REBUILD_ON_SAVE: True,
    CONF_FULLSCREEN_ENABLED: True,
    CONF_FULLSCREEN_HIDE_HEADER: True,
    CONF_FULLSCREEN_HIDE_SIDEBAR: True,
    CONF_FULLSCREEN_DISABLE_SCROLL: True,
    CONF_FULLSCREEN_SHOW_BUTTON: True,
    CONF_HELPER_FULLSCREEN: AUTO_HELPER_FULLSCREEN,
    CONF_ENTITY_POWER: "sensor.tesla_power",
    CONF_ENTITY_ELEVATION: "sensor.tesla_elevation",
    CONF_ENTITY_SPEED: "sensor.tesla_speed",
    CONF_ENTITY_BATTERY_LEVEL: "sensor.pom_battery_level",
    CONF_ENTITY_EST_RANGE: "sensor.pom_battery_range_estimate",
    CONF_ENTITY_RATED_RANGE: "sensor.pom_battery_range",
    CONF_ENTITY_ENERGY_REMAINING: "sensor.pom_energy_remaining",
    CONF_ENTITY_INSIDE_TEMP: "sensor.tesla_inside_temp",
    CONF_ENTITY_BATTERY_TEMP: "sensor.pom_pil_modulu_maksimum_sicakligi",
    CONF_ENTITY_OUTSIDE_TEMP: "sensor.tesla_outside_temp",
    CONF_ENTITY_ODOMETER: "sensor.tesla_odometer",
    CONF_ENTITY_BATTERY_HEATER: "binary_sensor.tesla_battery_heater",
    CONF_TOP_LEFT_SLOT_1: "elevation",
    CONF_TOP_LEFT_SLOT_2: "power",
    CONF_TOP_CENTER_SLOT: "speed",
    CONF_TOP_RIGHT_SLOT_1: "battery_level",
    CONF_TOP_RIGHT_SLOT_2: "est_range",
    CONF_TOP_FONT_SCALE: 1.0,
    CONF_TOP_LEFT_FONT_SCALE: 1.0,
    CONF_TOP_CENTER_FONT_SCALE: 1.0,
    CONF_TOP_RIGHT_FONT_SCALE: 1.0,
    CONF_ENTITY_LOCATION_SENSOR: "sensor.tesla",
    CONF_ENTITY_CHARGING: "binary_sensor.pom_charging",
    CONF_ENTITY_PLUGGED_IN: "binary_sensor.pom_charge_cable",
    CONF_ENTITY_SHIFT_STATE: "sensor.tesla_shift_state_memory",
    CONF_ENTITY_LIVE_TRIP: "sensor.pom_live_trip",
    CONF_ENTITY_PERSON_TESLA: "person.tesla",
    CONF_ENTITY_PERSON_2: "person.ali",
    CONF_ENTITY_PERSON_3: "person.cavidan",
    CONF_TESLA_MAP_HOURS_TO_SHOW: 1,
    CONF_PERSON_MAP_HOURS_TO_SHOW: 0,
    CONF_MAP_THEME_MODE: DEFAULT_MAP_THEME_MODE,
    CONF_HELPER_MAP: AUTO_HELPER_MAP,
    CONF_HELPER_PERSON_CARDS: AUTO_HELPER_PERSON_CARDS,
    CONF_HELPER_INTERACTIVE_MAP: AUTO_HELPER_INTERACTIVE_MAP,
    CONF_HELPER_CONTROLS: AUTO_HELPER_CONTROLS,
    CONF_HELPER_ENERGY_SLOT_SELECT: AUTO_HELPER_ENERGY_SLOT_SELECT,
    CONF_HELPER_ADDRESS_POPUP: AUTO_HELPER_ADDRESS_POPUP,
    CONF_ENTITY_FLASH_LIGHTS: "button.pom_flash_lights",
    CONF_ENTITY_FLASH_LIGHTS_STATE: "button.pom_flash_lights",
    CONF_ENTITY_SENTRY: "switch.pom_sentry_mode",
    CONF_ENTITY_HONK: "button.pom_honk_horn",
    CONF_ENTITY_HONK_STATE: "button.pom_honk_horn",
    CONF_ENTITY_FART: "button.pom_play_fart",
    CONF_ENTITY_FART_STATE: "button.pom_play_fart",
    CONF_ENTITY_WINDOWS_OPEN: "binary_sensor.tesla_windows_open",
    CONF_ENTITY_DOORS_OPEN: "binary_sensor.tesla_doors_open",
    CONF_ENTITY_HOME_AUTOMATION: "input_boolean.zone_leave_house_activate",
    CONF_ENTITY_MANUAL_TRACKING: "input_boolean.tesla_automation_speed_sections",
    CONF_ENTITY_HORN: "button.pom_horn",
    CONF_ENTITY_REAR_MIDDLE_SEAT_HEATER: "",
    CONF_ENTITY_REAR_RIGHT_SEAT_HEATER: "",
    CONF_ENTITY_REAR_LEFT_SEAT_HEATER: "",
    CONF_ENTITY_RIGHT_SEAT_HEATER: "",
    CONF_ENTITY_LEFT_SEAT_HEATER: "",
    CONF_ENTITY_CHARGE_CABLE_LOCK: "",
    CONF_ENTITY_CHARGE_PORT: "",
    CONF_ENTITY_VALET_MODE: "",
    CONF_ENTITY_WAKE: "",
    CONF_ENTITY_HOME_ENTITY_1: "",
    CONF_ENTITY_HOME_ENTITY_2: "",
    CONF_ENTITY_HOME_ENTITY_1_ICON: "",
    CONF_ENTITY_HOME_ENTITY_2_ICON: "",
    CONF_SIDEBAR_SLOT_1: "flash_lights",
    CONF_SIDEBAR_SLOT_2: "sentry",
    CONF_SIDEBAR_SLOT_3: "honk",
    CONF_SIDEBAR_SLOT_4: "fart",
    CONF_SIDEBAR_SLOT_5: "windows",
    CONF_SIDEBAR_SLOT_6: "empty",
    CONF_SIDEBAR_SLOT_7: "empty",
    CONF_SIDEBAR_SLOT_8: "empty",
    CONF_ENABLE_CHARGE_POPUP: True,
    CONF_HELPER_CHARGE_POPUP: AUTO_HELPER_CHARGE_POPUP,
    CONF_HELPER_ADDRESS_POPUP: AUTO_HELPER_ADDRESS_POPUP,
    CONF_CHARGE_BATTERY_LEVEL: "sensor.pom_battery_level",
    CONF_CHARGE_BATTERY_RANGE: "sensor.pom_battery_range",
    CONF_CHARGE_BATTERY_RANGE_ESTIMATE: "sensor.pom_battery_range_estimate",
    CONF_CHARGE_ENERGY_ADDED: "sensor.pom_charge_energy_added",
    CONF_CHARGE_CHARGER_POWER: "sensor.pom_charger_power",
    CONF_CHARGE_BATTERY_PACK_VOLTAGE: "sensor.pom_battery_pack_voltage",
    CONF_CHARGE_CABLE: "binary_sensor.pom_charge_cable",
    CONF_CHARGE_RATE: "sensor.pom_charge_rate",
    CONF_CHARGE_CURRENT: "sensor.pom_charger_current",
    CONF_CHARGE_VOLTAGE: "sensor.pom_charger_voltage",
    CONF_CHARGE_TIME_TO_FULL: "sensor.pom_time_to_full_charge",
    CONF_CHARGE_SUPERCHARGER_PRICE: "input_number.tesla_supercharger_kwh_fiyati",
    CONF_CHARGE_ZES_PRICE: "input_number.tesla_zes_kwh_fiyati",
    CONF_CHARGE_ASTOR_PRICE: "input_number.tesla_astor_kwh_fiyati",
    CONF_SHOW_FLASH_LIGHTS: True,
    CONF_SHOW_SENTRY: True,
    CONF_SHOW_HONK: True,
    CONF_SHOW_FART: True,
    CONF_SHOW_WINDOWS: True,
    CONF_SHOW_DOORS: True,
    CONF_SHOW_HOME_AUTOMATION: True,
    CONF_SHOW_MANUAL_TRACKING: True,
    CONF_SHOW_BOTTOM_RANGE: True,
    CONF_SHOW_BOTTOM_ENERGY: True,
    CONF_SHOW_BOTTOM_INSIDE_TEMP: True,
    CONF_SHOW_BOTTOM_BATTERY_TEMP: True,
    CONF_BOTTOM_SLOT_1: "energy_remaining",
    CONF_BOTTOM_SLOT_2: "inside_temp",
    CONF_BOTTOM_SLOT_3: "battery_temp",
    CONF_SHOW_BOTTOM_LOCATION: True,
    CONF_LOCATION_DISPLAY_MODE: "auto_short",
    CONF_LOCATION_UPDATE_INTERVAL_MINUTES: DEFAULT_LOCATION_UPDATE_INTERVAL_MINUTES,
    CONF_SHOW_BOTTOM_MAP_TOGGLE: True,
    CONF_SHOW_BOTTOM_CONTROLS: True,
    CONF_SHOW_BOTTOM_PERSON_TOGGLE: True,
    CONF_SHOW_BOTTOM_PERSON_CARDS: True,
    CONF_SHOW_BOTTOM_CHARGING: True,
    CONF_SHOW_BOTTOM_PERSON_TRACK_1: True,
    CONF_SHOW_BOTTOM_PERSON_TRACK_2: True,
    CONF_SHOW_BOTTOM_PERSON_TRACK_3: True,
    CONF_IMAGE_CHARGING: BUNDLED_IMAGE_CHARGING,
    CONF_IMAGE_PARKED: BUNDLED_IMAGE_PARKED,
    CONF_IMAGE_DRIVING: BUNDLED_IMAGE_DRIVING,
    CONF_YOUTUBE_DRIVING_BG_ENABLED: False,
    CONF_YOUTUBE_DRIVING_BG_VIDEO: "",
    CONF_YOUTUBE_DRIVING_BG_START_SECONDS: 0,
    CONF_YOUTUBE_DRIVING_BG_MUTE: True,
    CONF_YOUTUBE_DRIVING_BG_LOOP: True,
    CONF_PERSON_TRACK_ENABLED: True,
    CONF_PERSON_TRACK_SHOW_BUTTON: True,
    CONF_PERSON_TRACK_HOURS_TO_SHOW: 15,
    CONF_HELPER_PERSON_TRACK_LIST_POPUP: AUTO_HELPER_PERSON_TRACK_LIST_POPUP,
    CONF_HELPER_PERSON_TRACK_POPUP_1: AUTO_HELPER_PERSON_TRACK_POPUP_1,
    CONF_HELPER_PERSON_TRACK_POPUP_2: AUTO_HELPER_PERSON_TRACK_POPUP_2,
    CONF_HELPER_PERSON_TRACK_POPUP_3: AUTO_HELPER_PERSON_TRACK_POPUP_3,
    CONF_PERSON_TRACK_1_ENTITY: "person.cavidan",
    CONF_PERSON_TRACK_1_NAME: "Cavidan",
    CONF_PERSON_TRACK_1_ENABLED: True,
    CONF_PERSON_TRACK_2_ENTITY: "person.ali",
    CONF_PERSON_TRACK_2_NAME: "Ali",
    CONF_PERSON_TRACK_2_ENABLED: True,
    CONF_PERSON_TRACK_3_ENTITY: "",
    CONF_PERSON_TRACK_3_NAME: "Person 3",
    CONF_PERSON_TRACK_3_ENABLED: False,
}
