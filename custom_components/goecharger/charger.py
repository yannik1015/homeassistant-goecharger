from enum import Enum
from goecharger import GoeCharger as GoeChargerV1
from goecharger_api_lite import GoeCharger as GoeChargerV2

import logging

_LOGGER = logging.getLogger(__name__)

class Charger:
    def __init__(self, host, api_level):
        _LOGGER.debug(f"Creating Charger at {host} with API {api_level}")
        self.host = host
        self.api_level = api_level
        
        if api_level == "1":
            self.goecharger = GoeChargerV1(host)
        elif api_level == "2":
            self.goecharger = GoeChargerV2(host)
        else:
            raise InvalidAPILevelError("Invalid API level. Allowed values are 1 and 2.")

    def request_status(self):
        if self.api_level == "1":
            return GoeChargerV1.requestStatus()
        elif self.api_level == "2":
            # TODO: Check the return format with v1
            return GoeChargerV2.get_status(status_type=GoeChargerV2.STATUS_FULL)
        else:
            raise InvalidAPILevelError("Invalid API level. Allowed values are 1 and 2.")
    
    def set_tmp_max_current(self, maxCurrent):
        if self.api_level == "1":
            return GoeChargerV1.setTmpMaxCurrent(maxCurrent)
        elif self.api_level == "2":
            # TODO: Check
            return GoeChargerV2.set_ampere(maxCurrent)
        else:
            raise InvalidAPILevelError("Invalid API level. Allowed values are 1 and 2.")
    
    def set_absolute_max_current(self, absoluteMaxCurrent):
        if self.api_level == "1":
            return GoeChargerV1.setAbsoluteMaxCurrent(absoluteMaxCurrent)
        elif self.api_level == "2":
            # TODO: Implement in charging APIv2 (key ama)
            # return GoeChargerV2.(absoluteMaxCurrent)
            raise NotImplemented
        else:
            raise InvalidAPILevelError("Invalid API level. Allowed values are 1 and 2.")
    
    def set_cable_lock_mode(self, cableLockModeEnum):
        if self.api_level == "1":
           return GoeChargerV1.setCableLockMode(cableLockModeEnum)
        elif self.api_level == "2":
            # TODO: Implement in charging APIv2 (key ust)
            # return GoeChargerV2.(cableLockModeEnum)
            raise NotImplemented
        else:
            raise InvalidAPILevelError("Invalid API level. Allowed values are 1 and 2.")
    
    def set_charge_limit(self, chargeLimit):
        if self.api_level == "1":
            return GoeChargerV1.setChargeLimit(chargeLimit)
        elif self.api_level == "2":
            # TODO: Implement in charging APIv2 (key dwo)
            
            # Conversion from kWh to Wh
            chargeLimit = chargeLimit * 1000
            # return GoeChargerV2.set_ampere(maxCurrent)

            raise NotImplemented
        else:
            raise InvalidAPILevelError("Invalid API level. Allowed values are 1 and 2.")
    
    def set_phase_mode(self, phaseModeEnum):
        if self.api_level != "1":
            raise InvalidAPILevelError("Invalid API level. Only APIv2 can switch the phase mode.")
        
        # TODO: Check
        return GoeChargerV2.set_phase_mode(phaseModeEnum)

    def set_allow_charging(self, allowCharging: bool):
        if self.api_level == "1":
            return GoeChargerV1.setAllowCharging(allowCharging)
        elif self.api_level == "2":
            # TODO: Check
            if allowCharging:
                return GoeChargerV2.set_charging_mode(GoeChargerV2.SettableValueEnum.ChargingMode.on)
            else:
                return GoeChargerV2.set_charging_mode(GoeChargerV2.SettableValueEnum.ChargingMode.off)
        else:
            raise InvalidAPILevelError("Invalid API level. Allowed values are 1 and 2.")
    
    class CableLockMode(Enum):
        UNLOCKCARFIRST = 0
        AUTOMATIC = 1
        LOCKED = 2
    
    @property
    def PhaseModeEnum(self):
        return GoeChargerV2.SettableValueEnum.PhaseMode
    

class InvalidAPILevelError(ValueError):
    pass
