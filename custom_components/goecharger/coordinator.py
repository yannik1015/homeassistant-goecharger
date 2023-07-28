from datetime import timedelta
import logging
import async_timeout

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .charger import Charger

_LOGGER = logging.getLogger(__name__)

class GoeChargerUpdateCoordinator(DataUpdateCoordinator):
    """DataUpdateCoordinator to gather data for a specific go-eCharger."""

    def __init__(
            self, 
            hass: HomeAssistant,
            name: str,
            charger: Charger,
            update_interval: timedelta,
    ) -> None:
        """Initalize the DataUpdateCoordinator to gather data for specific go-eCharger."""
        self.hass = hass
        self.name = name
        self.charger = charger
        
        super().__init__(
            hass,
            _LOGGER,
            name=name,
            update_interval=update_interval,
        )

    async def _async_update_data(self):
        """Fetch data from API endpoint."""

        try:
            _LOGGER.debug(f"update for charger '{self.name}'..")

            data = self.data if self.data else {}
            fetched_status = await self.hass.async_add_executor_job(self.charger.request_status)

            if fetched_status is not None and fetched_status.get("car_status", "unknown") != "unknown":
                self.data = fetched_status
            else:
                _LOGGER.error(f"Unable to fetch state for charger {self.name}")
            
            # TODO: Check if the return values of the requestStatus are matching the self._attribute in the entities
            return data
        except:
            _LOGGER.exception(f"Error fetching state for charger {self.name}")
            raise


