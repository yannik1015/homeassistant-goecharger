"""Platform for go-eCharger select integration."""
import logging

from homeassistant.components.select import SelectEntity
from homeassistant import core, config_entries

from .coordinator import GoeChargerUpdateCoordinator
from .entity import GoeChargerEntity
from .const import DOMAIN, CONF_NAME, CONF_API_LEVEL
from .charger import CableLockMode, PhaseModeEnum

_LOGGER = logging.getLogger(__name__)

_select_options = {
    "cable_lock_mode": {"name": "Cable lock mode", "options": [f"{enum.value}" for enum in CableLockMode], "default": "0"},
    "phase_mode": {"name": "Phase mode", "options": [f"{enum.value}" for enum in PhaseModeEnum], "default": "0"}
}

_selectsv1: list[str] = [
    "cable_lock_mode",
]
    
_selectsv2: list[str] = [
    "phase_mode",
]


async def async_setup_entry(
        hass: core.HomeAssistant,
        config_entry: config_entries.ConfigEntry,
        async_add_entities,
    ):
        _LOGGER.debug("setup select...")
        _LOGGER.debug(repr(config_entry.as_dict()))

        coordinator: GoeChargerUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
        config = config_entry.as_dict()["data"]

        chargerName = config[CONF_NAME]
        api_level = config[CONF_API_LEVEL]

        def _create_selects_for_charger(chargerName, hass, coordinator):
             
            entities: list = []

            def _add_select(select):
                _LOGGER.debug(f"adding Select: {select} for charger {chargerName}")
                name = _select_options.get(select).get('name') if _select_options.get(select) else select
                options = _select_options.get(select).get('options') if _select_options.get(select) else []
                default_option = _select_options.get(select).get('default') if _select_options.get(select) else None

                entities.append(
                    GoeChargerSelect(
                        coordinator,
                        hass,
                        chargerName,
                        name,
                        select,
                        options,
                        default_option
                    )
                )

            
            for select in _selectsv1:
                _add_select(select)

            if api_level == "2":
                for select in _selectsv2:
                    _add_select(select)

            return entities

        async_add_entities(_create_selects_for_charger(chargerName, hass, coordinator))

class GoeChargerSelect(GoeChargerEntity, SelectEntity):
    def __init__(
        self, 
        coordinator,
        hass, 
        device_name: str, 
        name: str, 
        attribute: str, 
        options: list[str],
        current_option
    ):
        super().__init__(coordinator.charger, coordinator, device_name, name)
        self.hass = hass
        self._attribute = attribute
        self._attr_options = options
        self._attr_current_option = current_option

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""

        if (self._attribute == "cable_lock_mode"):
            ret_val = await self.hass.async_add_executor_job(self.goeCharger.set_cable_lock_mode, CableLockMode(int(option)))
            _LOGGER.debug(f"set_cable_lock_mode returned {ret_val}")
        elif (self._attribute == "phase_mode"):
            ret_val = await self.hass.async_add_executor_job(self.goeCharger.set_phase_mode, PhaseModeEnum(int(option)))
            _LOGGER.debug(f'set_phase_mode returned {ret_val}')

        if ret_val != None:
            self._attr_current_option = option
            self.async_write_ha_state()

    @property
    def unique_id(self):
        """Return the unique_id of the select."""
        return f"select.{DOMAIN}.{self.device_name}_{self._attribute}"