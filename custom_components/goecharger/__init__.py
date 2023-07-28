"""go-eCharger integration"""

import voluptuous as vol
import ipaddress
import logging
from datetime import timedelta
import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_HOST, CONF_SCAN_INTERVAL
from homeassistant.core import valid_entity_id
from homeassistant import core
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN, CONF_SERIAL, CONF_CHARGERS, CONF_CORRECTION_FACTOR, CONF_NAME, CONF_API_LEVEL, CHARGER_API, PLATFORMS
from .coordinator import GoeChargerUpdateCoordinator
from .charger import Charger
from .services import async_setup_services

_LOGGER = logging.getLogger(__name__)

ABSOLUTE_MAX_CURRENT = "charger_absolute_max_current"
SET_CABLE_LOCK_MODE_ATTR = "cable_lock_mode"
SET_ABSOLUTE_MAX_CURRENT_ATTR = "charger_absolute_max_current"
CHARGE_LIMIT = "charge_limit"
SET_MAX_CURRENT_ATTR = "max_current"
CHARGER_NAME_ATTR = "charger_name"
SET_PHASE_MODE_ATTR = "phase_mode"

MIN_UPDATE_INTERVAL = timedelta(seconds=10)
DEFAULT_UPDATE_INTERVAL = timedelta(seconds=20)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_CHARGERS, default=[]): vol.All([
                    cv.ensure_list, [
                        vol.All({
                            vol.Required(CONF_NAME): vol.All(cv.string),
                            vol.Required(CONF_HOST): vol.All(ipaddress.ip_address, cv.string),
                            vol.Optional(
                                CONF_CORRECTION_FACTOR, default="1.0"
                            ): vol.All(cv.string),
                        })
                    ]
                ]),
                vol.Optional(CONF_HOST): vol.All(ipaddress.ip_address, cv.string),
                vol.Optional(CONF_SERIAL): vol.All(cv.string),
                vol.Optional(
                    CONF_CORRECTION_FACTOR, default="1.0"
                ): vol.All(cv.string),
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_UPDATE_INTERVAL
                ): vol.All(cv.time_period, vol.Clamp(min=MIN_UPDATE_INTERVAL)),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup_entry(hass, config):
    _LOGGER.debug("async_Setup_entry")
    _LOGGER.debug(repr(config.data))

    config.async_on_unload(config.add_update_listener(update_listener))

    name = config.data[CONF_NAME]
    charger = Charger(config.data[CONF_HOST], config.data[CONF_API_LEVEL], hass)
    update_interval = timedelta(config.data[CONF_SCAN_INTERVAL])
    hass.data[DOMAIN]["api"][name] = charger

    # TODO: Check if this works
    # coordinator = GoeChargerUpdateCoordinator(hass, name, charger, update_interval)
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}-{name}",
        update_method=charger.request_status,
        update_interval=update_interval,
    )
    # retVal = await coordinator.async_config_entry_first_refresh()
    retVal = await coordinator.async_refresh()
    _LOGGER.debug(f"Setup result: {retVal}")
    
    hass.data[DOMAIN][config.entry_id] = coordinator

    # TODO: Check if this makes more sense
    await hass.config_entries.async_forward_entry_setups(config, PLATFORMS)
    await async_setup_services(hass)
    
    return True

async def update_listener(hass, config):
    """Handle options update."""
    _LOGGER.debug("update_listener")

    name = config.data[CONF_NAME]
    goeCharger = Charger(config.data[CONF_HOST], config.data[CONF_API_LEVEL], hass)
    hass.data[DOMAIN]["api"][name] = goeCharger

    # TODO: Fix this thing never actually returning
    await hass.data[DOMAIN][config.entry_id].async_refresh()

    # TODO: Fix API-level change not upating the entities
    # await hass.config_entries.async_forward_entry_setups(config, PLATFORMS)
    # hass.async_create_task(
    #     hass.config_entries.async_forward_entry_setup(config, "sensor")
    # )
    # hass.async_create_task(
    #     hass.config_entries.async_forward_entry_setup(config, "switch")
    # )

    return True


async def async_unload_entry(hass, entry):
    _LOGGER.debug(f"Unloading charger '{entry.data[CONF_NAME]}")
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN]["api"].pop(entry.data[CONF_NAME])
    
    return unload_ok

async def async_migrate_entry(hass, config_entry):
    """Migrate old entry"""
    _LOGGER.debug("Migrating from version %s", config_entry.version)

    if config_entry.version == 1:
        new = {**config_entry.data}
        
        new[CONF_API_LEVEL] = "1"
        config_entry.version = 2

        hass.config_entries.async_update_entry(config_entry, data=new)

    _LOGGER.info("Migration to version %s successful", config_entry.version)
    
    return True

async def async_setup(hass: core.HomeAssistant, config: dict) -> bool:
    """Set up go-eCharger platforms and services."""

    _LOGGER.debug("async_setup")

    hass.data[DOMAIN] = {}
    chargerApi = {}
    chargers = []

    # Setup devices configured in the configuration.yaml#
    # TODO Check: May not support multiple chargers
    api_level = -1
    if DOMAIN in config:
        scan_interval = config[DOMAIN].get(CONF_SCAN_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        # TODO: Check if this acutally works
        api_level = config[DOMAIN].get(CONF_API_LEVEL, "1")

        host = config[DOMAIN].get(CONF_HOST, False)
        serial = config[DOMAIN].get(CONF_SERIAL, "unknown")

        try:
            correctionFactor = float(config[DOMAIN].get(CONF_CORRECTION_FACTOR, "1.0"))
        except:
            _LOGGER.warn("can't convert correctionFactor, using 1.0")
            correctionFactor = 1.0

        chargers = config[DOMAIN].get(CONF_CHARGERS, [])

        if host:
            if not serial:
                goeCharger = Charger(host, api_level, hass)
                status = goeCharger.request_status()
                serial = status["serial_number"]
            chargers.append([{CONF_NAME: serial, CONF_HOST: host, CONF_CORRECTION_FACTOR: correctionFactor,
                              CONF_API_LEVEL: api_level}])
        _LOGGER.debug(repr(chargers))

        for charger in chargers:
            chargerName = charger[0][CONF_NAME]
            host = charger[0][CONF_HOST]
            # TODO: Check this
            api_level = charger[0][CONF_API_LEVEL]
            _LOGGER.debug(f"charger: '{chargerName}' host: '{host}' ")

            goeCharger = Charger(host, api_level, hass)
            chargerApi[chargerName] = goeCharger

    hass.data[DOMAIN]["api"] = chargerApi

    return True
