<<<<<<< HEAD
from typing import Final
from homeassistant.const import Platform

DOMAIN: Final = "goecharger"
CONF_NAME: Final = "name"
CONF_SERIAL: Final = "serial"
CONF_CHARGERS: Final = "chargers"
CONF_CORRECTION_FACTOR: Final = "correction_factor"
CHARGER_API: Final  = "charger_api"
PLATFORMS: Final = [Platform.SENSOR, Platform.SWITCH]
=======
DOMAIN = "goecharger"
CONF_NAME = "name"
CONF_SERIAL = "serial"
CONF_CHARGERS = "chargers"
CONF_CORRECTION_FACTOR = "correction_factor"
CONF_API_LEVEL = "api_level"
CHARGER_API = "charger_api"

>>>>>>> main
