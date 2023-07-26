"""Platform for go-eCharger switch integration."""
import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.const import CONF_HOST
# from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant import core, config_entries

from goecharger import GoeCharger

from .const import DOMAIN, CONF_CHARGERS, CONF_NAME, CHARGER_API
from .coordinator import GoeChargerUpdateCoordinator
from .entity import GoeChargerEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    _LOGGER.debug("setup switch...")
    _LOGGER.debug(repr(config_entry.as_dict()))
    
    coordinator: GoeChargerUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    config = config_entry.as_dict()["data"]

    chargerName = config[CONF_NAME]

    entities: list = []

    # TODO: Get the attribute into here
    attribute = "allow_charging"
    entities.append(
        GoeChargerSwitch(
            coordinator,
            hass,
            f"switch.goecharger_{chargerName}_{attribute}",
            chargerName,
            "Charging allowed",
        )
    )

    async_add_entities(entities)


# async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
#     """Set up go-eCharger Switch platform."""
#     if discovery_info is None:
#         return
#     _LOGGER.debug("setup_platform")

#     chargers = discovery_info[CONF_CHARGERS]
#     chargerApi = discovery_info[CHARGER_API]

#     entities = []

#     for charger in chargers:
#         chargerName = charger[0][CONF_NAME]

#         attribute = "allow_charging"
#         entities.append(
#             GoeChargerSwitch(
#                 hass.data[DOMAIN]["coordinator"],
#                 hass,
#                 chargerApi[chargerName],
#                 f"switch.goecharger_{chargerName}_{attribute}",
#                 chargerName,
#                 "Charging allowed",
#                 attribute,
#             )
#         )
#     async_add_entities(entities)


class GoeChargerSwitch(GoeChargerEntity, SwitchEntity):
    def __init__(
        self, coordinator, hass, entity_id, device_name, name
    ):
        """Initialize the go-eCharger switch."""
        super().__init__(coordinator.charger, coordinator, entity_id, device_name, name)
        self.hass = hass
        self._state = None
        self._attribute = "allow_charging"

        # TODO: Check if this is needed
        # self._attr_unique_id = f"{self._chargername}_allow_charging"

    # @property
    # def icon(self) -> str:
    #     """Return the icon."""
    #     return "mdi:ev-station"

    # TODO: Fix state changing to on/off even though no connection can be made
    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        await self.hass.async_add_executor_job(self.goeCharger.setAllowCharging, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        await self.hass.async_add_executor_job(self.goeCharger.setAllowCharging, False)
        await self.coordinator.async_request_refresh()

    @property
    def is_on(self):
        """Return the state of the switch."""
        # TODO: Check if this is still correct and maybe remove the try/except and check if the sensor is getting set up
        try:
            return True if self.coordinator.data[self.device_name][self._attr_unique_id] == "on" else False
        except KeyError:
            return False
