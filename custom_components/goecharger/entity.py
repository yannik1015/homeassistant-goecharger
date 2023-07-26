from collections.abc import Awaitable, Callable, Coroutine
from typing import Any, Concatenate, ParamSpec, TypeVar

from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from goecharger import GoeCharger

from .const import DOMAIN
from .coordinator import GoeChargerUpdateCoordinator

_T = TypeVar("_T", bound="GoeChargerEntity")
_P = ParamSpec("_P")

def async_refresh_after(
    func: Callable[Concatenate[_T, _P], Awaitable[None]]
) -> Callable[Concatenate[_T, _P], Coroutine[Any, Any, None]]:
    """Define a wrapper to refresh after."""

    async def _async_wrap(self: _T, *args: _P.args, **kwargs: _P.kwargs) -> None:
        await func(self, *args, **kwargs)
        # TODO: Check if this works
        await self.coordinator.async_request_refresh()

    return _async_wrap

class GoeChargerEntity(CoordinatorEntity[GoeChargerUpdateCoordinator]):
    """Common base class for all coordinatd go-eCharger entities."""

    def __init__(
        self, 
        device: GoeCharger, 
        coordinator: GoeChargerUpdateCoordinator, 
        attr_unique_id: str,
        device_name: str,
        name: str
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self.goeCharger: GoeCharger = device
        self._attr_unique_id = attr_unique_id
        self.device_name = device_name
        self._name = name

    @property
    def device_info(self) -> DeviceInfo:
        """Return information about the entity."""
        return DeviceInfo(
            # connections={(dr.CONNECTION_NETWORK_MAC)},
            identifiers={(DOMAIN, str(self.device_name))},
            manufacturer="go-e",
            model="HOME",
            name=self._name,
        )
    
    @property
    def name(self):
        """Return the name of the entity."""
        return self._name
    
    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # TODO: Implement here or in the sensor/switch class
        # self._attr_is_on = self.coordinator.data[self.idx]["state"]
        self.async_write_ha_state()

    @property
    def unique_id(self):
        """Return the unique_id of the entity."""
        return self._attr_unique_id