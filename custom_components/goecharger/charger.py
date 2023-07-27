from enum import Enum
from goecharger import GoeCharger as GoeChargerV1
from goecharger_api_lite import GoeCharger as GoeChargerV2

import logging

_LOGGER = logging.getLogger(__name__)

class CableLockMode(Enum):
    UNLOCKCARFIRST = 0
    AUTOMATIC = 1
    LOCKED = 2

    def __str__(self):
        names = {
            0: "Unlock car first",
            1: "Automatic",
            2: "Locked",
        }
        return names[self.value]
    

    def _to_v1_enum(self):
        if self.value == 0:
            return GoeChargerV1.CableLockMode.UNLOCKCARFIRST
        elif self.value == 1:
            return GoeChargerV1.CableLockMode.AUTOMATIC
        elif self.value == 2:
            return GoeChargerV1.CableLockMode.LOCKED
        else:
            raise ValueError(f"Invalid value for CableLockMode: {self.value}")


class PhaseModeEnum(Enum):
    AUTO = 0
    ONE_PHASE = 1
    THREE_PHASE = 2

    def __str__(self):
        names = {
            0: "Automatic",
            1: "1 Phase",
            2: "3 Phase",
        }
        return names[self.value] 

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
            raise InvalidAPILevelError(f"Invalid API level {api_level}. Allowed values are 1 and 2.")

    def request_status(self):
        if self.api_level == "1":
            return self.goecharger.requestStatus()
        elif self.api_level == "2":
            # TODO: Check the return format with v1
            return self.goecharger.get_status(status_type=GoeChargerV2.STATUS_FULL)
        else:
            raise InvalidAPILevelError(f"Invalid API level {self.api_level}. Allowed values are 1 and 2.")
    
    def set_tmp_max_current(self, maxCurrent):
        if self.api_level == "1":
            return self.goecharger.setTmpMaxCurrent(maxCurrent)
        elif self.api_level == "2":
            # TODO: Check
            return self.goecharger.set_ampere(maxCurrent)
        else:
            raise InvalidAPILevelError(f"Invalid API level {self.api_level}. Allowed values are 1 and 2.")
    
    def set_absolute_max_current(self, absoluteMaxCurrent):
        if self.api_level == "1":
            return self.goecharger.setAbsoluteMaxCurrent(absoluteMaxCurrent)
        elif self.api_level == "2":
            # TODO: Implement in charging APIv2 (key ama)
            # return self.goecharger.set_absolute_max_current(absoluteMaxCurrent)
            return self.goecharger.set_key("ama", absoluteMaxCurrent)
        else:
            raise InvalidAPILevelError(f"Invalid API level {self.api_level}. Allowed values are 1 and 2.")
    
    def set_cable_lock_mode(self, cableLockModeEnum: CableLockMode):
        if self.api_level == "1":
        #    return self.goecharger.setCableLockMode(cableLockModeEnum._to_v1_enum())
            retval = self.goecharger.setCableLockMode(cableLockModeEnum._to_v1_enum())
            return retval
        elif self.api_level == "2":
            # TODO: Implement in charging APIv2 (key ust)
            # return self.goecharger.set_cable_lock_mode(cableLockModeEnum)
            return self.goecharger.set_key("ust", cableLockModeEnum.value)
        else:
            raise InvalidAPILevelError(f"Invalid API level {self.api_level}. Allowed values are 1 and 2.")
    
    def set_charge_limit(self, chargeLimit):
        if self.api_level == "1":
            return self.goecharger.setChargeLimit(chargeLimit)
        elif self.api_level == "2":
            # TODO: Implement in charging APIv2 (key dwo)
            
            # Conversion from kWh to Wh
            chargeLimit = chargeLimit * 1000
            # return self.goecharger.set_charge_limit(chargeLimit)
            return self.goecharger.set_key("dwo", chargeLimit)
        else:
            raise InvalidAPILevelError(f"Invalid API level {self.api_level}. Allowed values are 1 and 2.")
    
    def set_phase_mode(self, phaseModeEnum: PhaseModeEnum):
        if self.api_level != "1":
            raise InvalidAPILevelError("Invalid API level. Only APIv2 can switch the phase mode.")
        
        # TODO: Check maybe replace if auto value is supported
        # return self.goecharger.set_phase_mode(phaseModeEnum)
        return self.goecharger.set_key("psm", phaseModeEnum.value)

    def set_allow_charging(self, allowCharging: bool):
        if self.api_level == "1":
            return self.goecharger.setAllowCharging(allowCharging)
        elif self.api_level == "2":
            # TODO: Check
            if allowCharging:
                return self.goecharger.set_charging_mode(GoeChargerV2.SettableValueEnum.ChargingMode.on)
            else:
                return self.goecharger.set_charging_mode(GoeChargerV2.SettableValueEnum.ChargingMode.off)
        else:
            raise InvalidAPILevelError(f"Invalid API level {self.api_level}. Allowed values are 1 and 2.")
    
class InvalidAPILevelError(ValueError):
    pass
