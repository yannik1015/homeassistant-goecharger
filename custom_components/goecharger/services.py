import logging
import voluptuous as vol

from homeassistant.const import CONF_DEVICE_ID, CONF_ENTITY_ID
from homeassistant.core import ServiceCall, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .charger import Charger

_LOGGER = logging.getLogger(__name__)

_SUPPORTED_SERVICES = [
    "set_max_current",
    "set_absolute_max_current",
    "set_charge_limit"
]

_SERVICE_CONFIG = {
    "set_max_current": {
        "function": "async_handle_set_max_current",
        "schema": vol.Schema(
                    {
                        vol.Required("max_current"): vol.All(vol.Coerce(int), vol.Range(min=6, max=32)),
                    },
                    extra=vol.ALLOW_EXTRA,
                ),
    },
    "set_absolute_max_current": {
        "function": "async_handle_set_absolute_max_current",
        "schema": vol.Schema(
            {
                vol.Required("absolute_max_current"): vol.All(vol.Coerce(int), vol.Range(min=6, max=32)),
            },
            extra=vol.ALLOW_EXTRA,
        ),
    },
    "set_charge_limit": {
        "function": "async_handle_set_charge_limit",
        "schema": vol.Schema(
            {
                vol.Required("charge_limit"): vol.All(vol.Coerce(float), vol.Range(min=0, max=None)),
            },
            extra=vol.ALLOW_EXTRA,
        )
    }
}

@callback
async def async_setup_services(hass):
    """Setups the go-eCharger services."""

    async def async_handle_set_max_current(service_call: ServiceCall) -> None:
        """Handle the set max current service call."""
        # TODO: Implement

        device_registry = dr.async_get(hass)
        entity_registry = er.async_get(hass)

        if CONF_DEVICE_ID in service_call.data:
            device = device_registry.async_get(service_call.data[CONF_DEVICE_ID][0])
            device_name = device.name
        else:
            entity = entity_registry.async_get(service_call.data[CONF_ENTITY_ID][0])
            device_id = entity.device_id
            device = device_registry.async_get(device_id)
            device_name = device.name

        charger: Charger = hass.data[DOMAIN]["api"][device_name]
        max_current_input = service_call.data["max_current"]

        max_current = 0
        if isinstance(max_current_input, str):
            if max_current_input.isnumeric():
                max_current = int(max_current_input)
            else:
                _LOGGER.error(
                    "No valid value for '%s'", max_current
                )
                return
        else:
            max_current = max_current_input

        # TODO: Max current may get lower and less high incase only 1 phase is used
        if max_current < 6:
            max_current = 6
        if max_current > 32:
            max_current = 32

        _LOGGER.debug(f"set max_current for charger '{device_name}' to {max_current}")
        # TODO: Check
        hass.async_add_executor_job(charger.set_tmp_max_current, max_current)

        # TODO: Replace this everywhere with await hass.data[DOMAIN][config.entry_id].async_refresh() maybe for each charger!
        # TODO: Check if this is needed and how we could get the coordinator
        #  hass.data[DOMAIN]["coordinator"].async_refresh()

    async def async_handle_set_absolute_max_current(service_call: ServiceCall) -> None:
        """Handle the absolute max current service call."""

        device_registry = dr.async_get(hass)
        entity_registry = er.async_get(hass)

        if CONF_DEVICE_ID in service_call.data:
            device = device_registry.async_get(service_call.data[CONF_DEVICE_ID][0])
            device_name = device.name
        else:
            entity = entity_registry.async_get(service_call.data[CONF_ENTITY_ID][0])
            device_id = entity.device_id
            device = device_registry.async_get(device_id)
            device_name = device.name

        charger: Charger = hass.data[DOMAIN]["api"][device_name]
        absolute_max_current_input = service_call.data["absolute_max_current"]

        absolute_max_current = 0
        if isinstance(absolute_max_current_input, str):
            if absolute_max_current_input.isnumeric():
                absolute_max_current = int(absolute_max_current_input)
            else:
                _LOGGER.error(
                    "No valid value for '%s'", absolute_max_current
                )
                return
        else:
            absolute_max_current = absolute_max_current_input

        # TODO: Max current may get lower and less high incase only 1 phase is used
        if absolute_max_current < 6:
            absolute_max_current = 6
        if absolute_max_current > 32:
            absolute_max_current = 32

        _LOGGER.debug(f"set absolute_max_current for charger '{device_name}' to {absolute_max_current}")
        # TODO: Check
        hass.async_add_executor_job(charger.set_absolute_max_current, absolute_max_current)

        # TODO: Replace this everywhere with await hass.data[DOMAIN][config.entry_id].async_refresh() maybe for each charger!
        # TODO: Check if this is needed and how we could get the coordinator
        #  hass.data[DOMAIN]["coordinator"].async_refresh()

    async def async_handle_set_charge_limit(service_call: ServiceCall) -> None:
        """Handle the handle set charge limit service call."""

        device_registry = dr.async_get(hass)
        entity_registry = er.async_get(hass)

        if CONF_DEVICE_ID in service_call.data:
            device = device_registry.async_get(service_call.data[CONF_DEVICE_ID][0])
            device_name = device.name
        else:
            entity = entity_registry.async_get(service_call.data[CONF_ENTITY_ID][0])
            device_id = entity.device_id
            device = device_registry.async_get(device_id)
            device_name = device.name

        charger: Charger = hass.data[DOMAIN]["api"][device_name]
        charge_limit_input = service_call.data["charge_limit"]

        charge_limit = 0
        if isinstance(charge_limit_input, str):
            if charge_limit_input.isnumeric():
                charge_limit = float(charge_limit_input)
            else:
                _LOGGER.error(
                    "No valid value for '%s'", charge_limit
                )
                return
        else:
            charge_limit = charge_limit_input

        if charge_limit < 0:
            charge_limit = 0

        _LOGGER.debug(f"set charge limit for charger '{device_name}' to {charge_limit}")
        # TODO: Check
        hass.async_add_executor_job(charger.set_charge_limit, charge_limit)

        # TODO: Replace this everywhere with await hass.data[DOMAIN][config.entry_id].async_refresh() maybe for each charger!
        # TODO: Check if this is needed and how we could get the coordinator
        #  hass.data[DOMAIN]["coordinator"].async_refresh()

    for service in _SUPPORTED_SERVICES:
        if not hass.services.has_service(DOMAIN, service):
            hass.services.async_register(
                DOMAIN,
                service,
                locals()[_SERVICE_CONFIG.get(service).get("function")] if _SERVICE_CONFIG.get(service) else _LOGGER.error(f"Service {service} not supported"),
                schema=_SERVICE_CONFIG.get(service).get("schema") if _SERVICE_CONFIG.get(service) else None,
            )


