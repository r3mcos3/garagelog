"""Constants. The integration name lives here (and in the folder/manifest/translations) only."""

from __future__ import annotations

DOMAIN = "garagelog"
NAME = "Garagelog"
EVENT_PREFIX = f"{DOMAIN}_"

STORAGE_VERSION = 1
STORAGE_KEY_PREFIX = f"{DOMAIN}."
SAVE_DELAY = 1.0
EXPORT_FORMAT = f"{DOMAIN}/1"

# config entry data
CONF_PLATE = "plate"
CONF_NAME = "name"
CONF_SKIP_RDW = "skip_rdw"
CONF_ODOMETER_ENTITY = "odometer_entity"
CONF_FUEL_LEVEL_ENTITY = "fuel_level_entity"
CONF_TYRE_ENTITIES = "tyre_entities"
CONF_OIL_LIFE_ENTITY = "oil_life_entity"

# options
CONF_NOTIFY_TARGETS = "notify_targets"
CONF_TYRE_TARGET = "tyre_target_bar"
CONF_TYRE_THRESHOLD = "tyre_threshold_bar"
CONF_WASH_SOON_DAYS = "wash_soon_days"
CONF_WASH_DUE_DAYS = "wash_due_days"
CONF_APK_DAYS = "apk_days"
CONF_OIL_CHECK_DAY = "oil_check_day"
CONF_SERVICE_INTERVAL_KM = "service_interval_km"
CONF_SERVICE_INTERVAL_DAYS = "service_interval_days"

DEFAULT_TYRE_TARGET = 2.5
DEFAULT_TYRE_THRESHOLD = 0.2
TYRE_HYSTERESIS = 0.05
DEFAULT_WASH_SOON_DAYS = 30
DEFAULT_WASH_DUE_DAYS = 60
DEFAULT_APK_DAYS = 30
DEFAULT_OIL_CHECK_DAY = 25
DEFAULT_SERVICE_INTERVAL_KM = 15000
DEFAULT_SERVICE_INTERVAL_DAYS = 365
SERVICE_SOON_DAYS = 30
SERVICE_SOON_KM = 1000
OIL_CHANGE_SOON_DAYS = 30
OIL_CHANGE_SOON_KM = 1000
OIL_MIN_DROP_PCT = 3.0
OIL_MIN_KM = 100.0
RDW_REFRESH_HOURS = 24

# service types
SERVICE_TYPES = ["maintenance", "oil_change", "tyres", "brakes", "apk", "repair", "other"]
SERVICE_MAINTENANCE = "maintenance"
SERVICE_OIL_CHANGE = "oil_change"

# stored collections
REFUELS = "refuels"
SERVICES = "services"
WASHES = "washes"
OIL_CHECKS = "oil_checks"
OIL_SAMPLES = "oil_samples"
COLLECTIONS = (REFUELS, SERVICES, WASHES, OIL_CHECKS)

# wash status
WASH_OK = "ok"
WASH_SOON = "soon"
WASH_DUE = "due"

# events
EVENT_APK_DUE = f"{EVENT_PREFIX}apk_due"
EVENT_SERVICE_DUE = f"{EVENT_PREFIX}service_due"
EVENT_WASH_DUE = f"{EVENT_PREFIX}wash_due"
EVENT_TYRE_PRESSURE = f"{EVENT_PREFIX}tyre_pressure"
EVENT_OIL_CHECK_DUE = f"{EVENT_PREFIX}oil_check_due"
EVENT_OIL_CHANGE_DUE = f"{EVENT_PREFIX}oil_change_due"

# websocket / frontend
CARD_URL = f"/{DOMAIN}_static/{DOMAIN}-card.js"
