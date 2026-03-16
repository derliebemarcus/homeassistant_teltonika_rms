"""Constants for the Teltonika RMS integration."""

from __future__ import annotations

DOMAIN = "teltonika_rms"

AUTHORIZE_URL = "https://rms.teltonika-networks.com/account/authorize"
TOKEN_URL = "https://rms.teltonika-networks.com/account/token"
API_BASE_URL = "https://api.rms.teltonika-networks.com"
STATUS_BASE_URL = "https://rms.teltonika-networks.com/status"

CONF_AUTH_MODE = "auth_mode"
CONF_PAT_TOKEN = "pat_token"
AUTH_MODE_OAUTH2 = "oauth2"
AUTH_MODE_PAT = "pat"

OAUTH2_SCOPES: tuple[str, ...] = (
    "devices:read",
    "device_location:read",
    "device_actions:read",
    "device_remote_access:read",
    "device_actions:write",
    "device_configurations:read",
    "device_configurations:write",
)

CONF_INVENTORY_INTERVAL = "inventory_interval"
CONF_STATE_INTERVAL = "state_interval"
CONF_TAGS = "tags"
CONF_DEVICE_STATUS = "device_status"
CONF_ESTIMATED_DEVICES = "estimated_devices"
CONF_SPEC_PATH = "spec_path"
CONF_ENABLE_LOCATION = "enable_location"

DEFAULT_INVENTORY_INTERVAL = 3600
DEFAULT_STATE_INTERVAL = 300
DEFAULT_PORT_SCAN_INTERVAL = 6 * 60 * 60
DEFAULT_PORT_CONFIG_INTERVAL = 6 * 60 * 60
DEFAULT_ESTIMATED_DEVICES = 20
DEFAULT_ENABLE_LOCATION = True
DEFAULT_SPEC_PATH = ""

MAX_MONTHLY_REQUESTS = 100_000
REQUEST_BUDGET_HEADROOM = 0.80

SERVICE_REFRESH = "refresh"
SERVICE_REBOOT = "reboot"

UPDATE_PLATFORMS: tuple[str, ...] = (
    "binary_sensor",
    "sensor",
    "device_tracker",
    "button",
    "switch",
    "update",
)

DEFAULT_OPTIONS: dict[str, object] = {
    CONF_INVENTORY_INTERVAL: DEFAULT_INVENTORY_INTERVAL,
    CONF_STATE_INTERVAL: DEFAULT_STATE_INTERVAL,
    CONF_TAGS: "",
    CONF_DEVICE_STATUS: "",
    CONF_ESTIMATED_DEVICES: DEFAULT_ESTIMATED_DEVICES,
    CONF_SPEC_PATH: DEFAULT_SPEC_PATH,
    CONF_ENABLE_LOCATION: DEFAULT_ENABLE_LOCATION,
}
