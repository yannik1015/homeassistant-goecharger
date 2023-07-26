from typing import Final
from homeassistant.const import Platform

DOMAIN: Final = "goecharger"
CONF_NAME: Final = "name"
CONF_SERIAL: Final = "serial"
CONF_CHARGERS: Final = "chargers"
CONF_CORRECTION_FACTOR: Final = "correction_factor"
CHARGER_API: Final  = "charger_api"
CONF_API_LEVEL: Final = "api_level"
PLATFORMS: Final = [Platform.SENSOR, Platform.SWITCH]
