from collections.abc import Awaitable, Callable, Coroutine
from typing import Any, Concatenate, ParamSpec, TypeVar

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
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self.goeCharger: GoeCharger = device
        self._attr_unique_id = attr_unique_id
        self.device_name = device_name

    @property
    def device_info(self) -> DeviceInfo:
        """Return information about the device."""
        return DeviceInfo(
            # connections={(dr.CONNECTION_NETWORK_MAC)},
            identifiers={(DOMAIN, str(self.device_name))},
            manufacturer="go-e",
            model="HOME",
            name=self.name,
        )
    
    @property
    def name(self):
        """Return the name of the device."""
        return self.device_name