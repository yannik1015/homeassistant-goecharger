import logging
from datetime import timedelta
import voluptuous as vol

from typing import Any

# from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, OptionsFlow, ConfigFlow
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.data_entry_flow import FlowResult

from homeassistant.const import CONF_HOST, CONF_SCAN_INTERVAL
from .const import DOMAIN, CONF_NAME, CONF_CORRECTION_FACTOR, CONF_API_LEVEL
_LOGGER = logging.getLogger(__name__)


DEFAULT_UPDATE_INTERVAL = timedelta(seconds=20)
MIN_UPDATE_INTERVAL = timedelta(seconds=10)


class ConfigFlowHandler(ConfigFlow, domain=DOMAIN):
    """Config flow for go-eCharger setup."""
    VERSION = 1

    @staticmethod
    @callback
    async def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return OptionsFlowHandler(config_entry)

    async def async_step_user(self, info):
        if info is not None:
            _LOGGER.debug(info)
            return self.async_create_entry(title=info[CONF_NAME], data=info)

        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_NAME): str,
                    vol.Optional(
                        CONF_SCAN_INTERVAL, default=20
                    ): int,
                    vol.Required(
                        CONF_CORRECTION_FACTOR, default="1.0"
                    ): str,
                    vol.Required(CONF_API_LEVEL, default="1"): selector.selector(
                        {"select": {"mode": "dropdown", "options": ["1", "2"]}}
                    ),
                }
            ),
        )

class OptionsFlowHandler(OptionsFlow):
    """Options flow for the go-eCharger"""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """"Initialize options flow"""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Manage options for the goe-Charger component"""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Optional(
                        CONF_SCAN_INTERVAL, default=20
                    ): int,
                    vol.Required(
                        CONF_CORRECTION_FACTOR, default="1.0"
                    ): str,
                    vol.Required(CONF_API_LEVEL, default="1"): selector.selector(
                        {"select": {"mode": "dropdown", "options": ["1", "2"]}}
                    ),
                }
            )
        )