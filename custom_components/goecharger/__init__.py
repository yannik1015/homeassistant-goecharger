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
    charger = Charger(config.data[CONF_HOST], config.data[CONF_API_LEVEL])
    update_interval = timedelta(config.data[CONF_SCAN_INTERVAL])
    hass.data[DOMAIN]["api"][name] = charger

    hass.data[DOMAIN][config.entry_id] = GoeChargerUpdateCoordinator(hass, name, charger, update_interval)

    await hass.data[DOMAIN][config.entry_id].async_refresh()

    await hass.config_entries.async_forward_entry_setups(config, PLATFORMS)
    
    return True

async def update_listener(hass, config):
    """Handle options update."""
    _LOGGER.debug("update_listener")

    name = config.data[CONF_NAME]
    goeCharger = Charger(config.data[CONF_HOST], config.data[CONF_API_LEVEL])
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
                goeCharger = Charger(host, api_level)
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

            goeCharger = Charger(host, api_level)
            chargerApi[chargerName] = goeCharger

    hass.data[DOMAIN]["api"] = chargerApi

    async def async_handle_set_max_current(call):
        """Handle the service call to set the absolute max current."""
        chargerNameInput = call.data.get(CHARGER_NAME_ATTR, '')

        maxCurrentInput = call.data.get(
            SET_MAX_CURRENT_ATTR, 32  # TODO: dynamic based on chargers absolute_max-setting
        )
        maxCurrent = 0
        if isinstance(maxCurrentInput, str):
            if maxCurrentInput.isnumeric():
                maxCurrent = int(maxCurrentInput)
            elif valid_entity_id(maxCurrentInput):
                maxCurrent = int(hass.states.get(maxCurrentInput).state)
            else:
                _LOGGER.error(
                    "No valid value for '%s': %s", SET_MAX_CURRENT_ATTR, maxCurrent
                )
                return
        else:
            maxCurrent = maxCurrentInput

        # TODO: Max current may get lower and less high incase only 1 phase is used
        if maxCurrent < 6:
            maxCurrent = 6
        if maxCurrent > 32:
            maxCurrent = 32

        if len(chargerNameInput) > 0:
            _LOGGER.debug(f"set max_current for charger '{chargerNameInput}' to {maxCurrent}")
            try:
                # TODO: Check
                await hass.async_add_executor_job(hass.data[DOMAIN]["api"][chargerNameInput].set_tmp_max_current, maxCurrent)
            except KeyError:
                _LOGGER.error(f"Charger with name '{chargerName}' not found!")

        else:
            for charger in hass.data[DOMAIN]["api"].keys():
                try:
                    _LOGGER.debug(f"set max_current for charger '{charger}' to {maxCurrent}")
                    # TODO: Check
                    await hass.async_add_executor_job(hass.data[DOMAIN]["api"][charger].set_tmp_max_current, maxCurrent)
                except KeyError:
                    _LOGGER.error(f"Charger with name '{chargerName}' not found!")

        # TODO: Replace this everywhere with await hass.data[DOMAIN][config.entry_id].async_refresh() maybe for each charger!
        await hass.data[DOMAIN]["coordinator"].async_refresh()

    async def async_handle_set_absolute_max_current(call):
        """Handle the service call to set the absolute max current."""
        chargerNameInput = call.data.get(CHARGER_NAME_ATTR, '')
        absoluteMaxCurrentInput = call.data.get(SET_ABSOLUTE_MAX_CURRENT_ATTR, 16)
        if isinstance(absoluteMaxCurrentInput, str):
            if absoluteMaxCurrentInput.isnumeric():
                absoluteMaxCurrent = int(absoluteMaxCurrentInput)
            elif valid_entity_id(absoluteMaxCurrentInput):
                absoluteMaxCurrent = int(hass.states.get(absoluteMaxCurrentInput).state)
            else:
                _LOGGER.error(
                    "No valid value for '%s': %s",
                    SET_ABSOLUTE_MAX_CURRENT_ATTR,
                    absoluteMaxCurrentInput,
                )
                return
        else:
            absoluteMaxCurrent = absoluteMaxCurrentInput

        if absoluteMaxCurrent < 6:
            absoluteMaxCurrent = 6
        if absoluteMaxCurrent > 32:
            absoluteMaxCurrent = 32

        if len(chargerNameInput) > 0:
            _LOGGER.debug(f"set absolute_max_current for charger '{chargerNameInput}' to {absoluteMaxCurrent}")
            try:
                await hass.async_add_executor_job(
                    # TODO: Check
                    hass.data[DOMAIN]["api"][chargerNameInput].set_absolute_max_current, absoluteMaxCurrent
                )
            except KeyError:
                _LOGGER.error(f"Charger with name '{chargerName}' not found!")

        else:
            for charger in hass.data[DOMAIN]["api"].keys():
                try:
                    _LOGGER.debug(f"set absolute_max_current for charger '{charger}' to {absoluteMaxCurrent}")
                    await hass.async_add_executor_job(
                        # TODO: Check
                        hass.data[DOMAIN]["api"][charger].set_absolute_max_current, absoluteMaxCurrent
                    )
                except KeyError:
                    _LOGGER.error(f"Charger with name '{chargerName}' not found!")

        await hass.data[DOMAIN]["coordinator"].async_refresh()

    # async def async_handle_set_cable_lock_mode(call):
    #     """Handle the service call to set the cable lock mode."""
    #     chargerNameInput = call.data.get(CHARGER_NAME_ATTR, '')
    #     cableLockModeInput = call.data.get(SET_CABLE_LOCK_MODE_ATTR, 0)
    #     if isinstance(cableLockModeInput, str):
    #         if cableLockModeInput.isnumeric():
    #             cableLockMode = int(cableLockModeInput)
    #         elif valid_entity_id(cableLockModeInput):
    #             cableLockMode = int(hass.states.get(cableLockModeInput).state)
    #         else:
    #             _LOGGER.error(
    #                 "No valid value for '%s': %s",
    #                 SET_CABLE_LOCK_MODE_ATTR,
    #                 cableLockModeInput,
    #             )
    #             return
    #     else:
    #         cableLockMode = cableLockModeInput

    #     cableLockModeEnum = Charger.CableLockMode.UNLOCKCARFIRST
    #     if cableLockModeInput == 1:
    #         cableLockModeEnum = Charger.CableLockMode.AUTOMATIC
    #     if cableLockMode >= 2:
    #         cableLockModeEnum = Charger.CableLockMode.LOCKED

    #     if len(chargerNameInput) > 0:
    #         _LOGGER.debug(f"set set_cable_lock_mode for charger '{chargerNameInput}' to {cableLockModeEnum}")
    #         try:
    #             await hass.async_add_executor_job(
    #                 # TODO: Check
    #                 hass.data[DOMAIN]["api"][chargerNameInput].set_cable_lock_mode, cableLockModeEnum
    #             )
    #         except KeyError:
    #             _LOGGER.error(f"Charger with name '{chargerName}' not found!")

    #     else:
    #         for charger in hass.data[DOMAIN]["api"].keys():
    #             try:
    #                 _LOGGER.debug(f"set set_cable_lock_mode for charger '{charger}' to {cableLockModeEnum}")
    #                 # TODO: Check
    #                 await hass.async_add_executor_job(
    #                     hass.data[DOMAIN]["api"][charger].set_cable_lock_mode, cableLockModeEnum
    #                 )
    #             except KeyError:
    #                 _LOGGER.error(f"Charger with name '{chargerName}' not found!")

    #     await hass.data[DOMAIN]["coordinator"].async_refresh()

    # async def async_handle_set_phase_mode(call):
    #     """Handle the service to set the phase mode."""
    #     # TODO: Check

    #     chargerNameInput = call.data.get(CHARGER_NAME_ATTR, '')
    #     phaseModeInput = call.data.get(SET_PHASE_MODE_ATTR, 0)
    #     if isinstance(phaseModeInput, str):
    #         if phaseModeInput.isnumeric():
    #             phaseMode = int(phaseModeInput)
    #         elif valid_entity_id(phaseModeInput):
    #             phaseMode = int(hass.states.get(phaseModeInput).state)
    #         else:
    #             _LOGGER.error(
    #                 "No valid value for '%s': %s",
    #                 SET_PHASE_MODE_ATTR,
    #                 phaseModeInput,
    #             )
    #             return
    #     else:
    #         phaseMode = phaseModeInput

    #     phaseModeEnum = Charger.PhaseModeEnum.three
    #     if phaseModeInput == 1:
    #         phaseModeEnum = Charger.PhaseModeEnum.one
    #     if phaseMode >= 2:
    #         phaseModeEnum = Charger.PhaseModeEnum.three

    #     if len(chargerNameInput) > 0:
    #         _LOGGER.debug(f"set set_phase_mode for charger '{chargerNameInput}' to {phaseModeEnum}")
    #         try:
    #             await hass.async_add_executor_job(
    #                 # TODO: Check
    #                 hass.data[DOMAIN]["api"][chargerNameInput].set_phase_mode, phaseModeEnum
    #             )
    #         except KeyError:
    #             _LOGGER.error(f"Charger with name '{chargerName}' not found!")

    #     else:
    #         for charger in hass.data[DOMAIN]["api"].keys():
    #             try:
    #                 _LOGGER.debug(f"set set_phase_mode for charger '{charger}' to {phaseModeEnum}")
    #                 # TODO: Check
    #                 await hass.async_add_executor_job(
    #                     hass.data[DOMAIN]["api"][charger].set_phase_mode, phaseModeEnum
    #                 )
    #             except KeyError:
    #                 _LOGGER.error(f"Charger with name '{chargerName}' not found!")

    #     await hass.data[DOMAIN]["coordinator"].async_refresh()

    async def async_handle_set_charge_limit(call):
        """Handle the service call to set charge limit."""
        chargerNameInput = call.data.get(CHARGER_NAME_ATTR, '')
        chargeLimitInput = call.data.get(CHARGE_LIMIT, 0.0)
        if isinstance(chargeLimitInput, str):
            if chargeLimitInput.isnumeric():
                chargeLimit = float(chargeLimitInput)
            elif valid_entity_id(chargeLimitInput):
                chargeLimit = float(hass.states.get(chargeLimitInput).state)
            else:
                _LOGGER.error(
                    "No valid value for '%s': %s", CHARGE_LIMIT, chargeLimitInput
                )
                return
        else:
            chargeLimit = chargeLimitInput

        if chargeLimit < 0:
            chargeLimit = 0

        if len(chargerNameInput) > 0:
            _LOGGER.debug(f"set set_charge_limit for charger '{chargerNameInput}' to {chargeLimit}")
            try:
                # TODO: Check
                await hass.async_add_executor_job(
                    hass.data[DOMAIN]["api"][chargerNameInput].set_charge_limit, chargeLimit
                )
            except KeyError:
                _LOGGER.error(f"Charger with name '{chargerName}' not found!")

        else:
            for charger in hass.data[DOMAIN]["api"].keys():
                try:
                    _LOGGER.debug(f"set set_charge_limit for charger '{charger}' to {chargeLimit}")
                    # TODO: Check
                    await hass.async_add_executor_job(
                        hass.data[DOMAIN]["api"][charger].set_charge_limit, chargeLimit
                    )
                except KeyError:
                    _LOGGER.error(f"Charger with name '{chargerName}' not found!")

        await hass.data[DOMAIN]["coordinator"].async_refresh()

    # TODO: Register services for each entity
    # TODO: Filter available services based on attribute (https://developers.home-assistant.io/docs/dev_101_services/) => Find out how to set a API-Level attribute
    hass.services.async_register(DOMAIN, "set_max_current", async_handle_set_max_current)
    hass.services.async_register(
        DOMAIN, "set_absolute_max_current", async_handle_set_absolute_max_current
    )

    # if api_level == 1:
    #     hass.services.async_register(DOMAIN, "set_cable_lock_mode", async_handle_set_cable_lock_mode)
    # elif api_level == 2:
    #     hass.services.async_register(DOMAIN, "set_phase_mode", async_handle_set_phase_mode)

    hass.services.async_register(DOMAIN, "set_charge_limit", async_handle_set_charge_limit)

    return True
