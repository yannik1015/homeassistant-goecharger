"""Platform for go-eCharger sensor integration."""
import logging
from .coordinator import GoeChargerUpdateCoordinator
from .entity import GoeChargerEntity

from homeassistant.const import (
    TEMP_CELSIUS,
    ENERGY_KILO_WATT_HOUR
)

from homeassistant import core, config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_platform
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.sensor import (
    STATE_CLASS_TOTAL_INCREASING,
    DEVICE_CLASS_ENERGY,
    SensorEntity
)


from .const import CONF_CHARGERS, DOMAIN, CONF_NAME, CONF_CORRECTION_FACTOR, CONF_API_LEVEL
from .charger import InvalidAPILevelError

AMPERE = 'A'
VOLT = 'V'
POWER_KILO_WATT = 'kW'
CARD_ID = 'Card ID'
PERCENT = '%'

_LOGGER = logging.getLogger(__name__)

_sensorUnits = {
    'charger_temp': {'unit': TEMP_CELSIUS, 'name': 'Charger Temp'},
    'charger_temp0': {'unit': TEMP_CELSIUS, 'name': 'Charger Temp 0'},
    'charger_temp1': {'unit': TEMP_CELSIUS, 'name': 'Charger Temp 1'},
    'charger_temp2': {'unit': TEMP_CELSIUS, 'name': 'Charger Temp 2'},
    'charger_temp3': {'unit': TEMP_CELSIUS, 'name': 'Charger Temp 3'},
    'p_l1': {'unit': POWER_KILO_WATT, 'name': 'Power L1'},
    'p_l2': {'unit': POWER_KILO_WATT, 'name': 'Power L2'},
    'p_l3': {'unit': POWER_KILO_WATT, 'name': 'Power L3'},
    'p_n': {'unit': POWER_KILO_WATT, 'name': 'Power N'},
    'p_all': {'unit': POWER_KILO_WATT, 'name': 'Power All'},
    'current_session_charged_energy': {'unit': ENERGY_KILO_WATT_HOUR, 'name': 'Current Session charged'},
    'current_session_charged_energy_corrected': {'unit': ENERGY_KILO_WATT_HOUR, 'name': 'Current Session charged corrected'},
    'energy_total': {'unit': ENERGY_KILO_WATT_HOUR, 'name': 'Total Charged'},
    'energy_total_corrected': {'unit': ENERGY_KILO_WATT_HOUR, 'name': 'Total Charged corrected'},
    'charge_limit': {'unit': ENERGY_KILO_WATT_HOUR, 'name': 'Charge limit'},
    'u_l1': {'unit': VOLT, 'name': 'Voltage L1'},
    'u_l2': {'unit': VOLT, 'name': 'Voltage L2'},
    'u_l3': {'unit': VOLT, 'name': 'Voltage L3'},
    'u_n': {'unit': VOLT, 'name': 'Voltage N'},
    'i_l1': {'unit': AMPERE, 'name': 'Current L1'},
    'i_l2': {'unit': AMPERE, 'name': 'Current L2'},
    'i_l3': {'unit': AMPERE, 'name': 'Current L3'},
    'charger_max_current': {'unit': AMPERE, 'name': 'Charger max current setting'},
    'charger_absolute_max_current': {'unit': AMPERE, 'name': 'Charger absolute max current setting'},
    'cable_max_current': {'unit': AMPERE, 'name': 'Cable max current'},
    'unlocked_by_card': {'unit': CARD_ID, 'name': 'Card used'},
    'lf_l1': {'unit': PERCENT, 'name': 'Power factor L1'},
    'lf_l2': {'unit': PERCENT, 'name': 'Power factor L2'},
    'lf_l3': {'unit': PERCENT, 'name': 'Power factor L3'},
    'lf_n': {'unit': PERCENT, 'name': 'Loadfactor N'},
    'car_status': {'unit': '', 'name': 'Status'},
}

_sensorStateClass = {
    'energy_total': STATE_CLASS_TOTAL_INCREASING,
    'energy_total_corrected': STATE_CLASS_TOTAL_INCREASING,
    'current_session_charged_energy': STATE_CLASS_TOTAL_INCREASING,
    'current_session_charged_energy_corrected': STATE_CLASS_TOTAL_INCREASING
}

_sensorDeviceClass = {
    'energy_total': DEVICE_CLASS_ENERGY,
    'energy_total_corrected': DEVICE_CLASS_ENERGY,
    'current_session_charged_energy': DEVICE_CLASS_ENERGY,
    'current_session_charged_energy_corrected': DEVICE_CLASS_ENERGY
}

_sensorsv1 = [
    'car_status',
    'charger_max_current',
    'charger_absolute_max_current',
    'charger_err',
    'charger_access',
    'stop_mode',
    'cable_max_current',
    'pre_contactor_l1',
    'pre_contactor_l2',
    'pre_contactor_l3',
    'post_contactor_l1',
    'post_contactor_l2',
    'post_contactor_l3',
    'charger_temp',
    'charger_temp0',
    'charger_temp1',
    'charger_temp2',
    'charger_temp3',
    'current_session_charged_energy',
    'current_session_charged_energy_corrected',
    'charge_limit',
    'adapter',
    'unlocked_by_card',
    'energy_total',
    'energy_total_corrected',
    'wifi',

    'u_l1',
    'u_l2',
    'u_l3',
    'u_n',
    'i_l1',
    'i_l2',
    'i_l3',
    'p_l1',
    'p_l2',
    'p_l3',
    'p_n',
    'p_all',
    'lf_l1',
    'lf_l2',
    'lf_l3',
    'lf_n',

    'firmware',
    'serial_number',
    'wifi_ssid',
    'wifi_enabled',
    'timezone_offset',
    'timezone_dst_offset',
]

# TODO: Add Sensor for APIv2
_sensorsv2 = [
]

async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    _LOGGER.debug("Setup sensors...")
    
    def _create_sensors_for_charger(chargerName, hass, correctionFactor, coordinator, charger):
        entities = []

        def _add_sensor(sensor):
            _LOGGER.debug(f"adding Sensor: {sensor} for charger {chargerName}")
            sensorUnit = _sensorUnits.get(sensor).get('unit') if _sensorUnits.get(sensor) else ''
            sensorName = _sensorUnits.get(sensor).get('name') if _sensorUnits.get(sensor) else sensor
            sensorStateClass = _sensorStateClass[sensor] if sensor in _sensorStateClass else ''
            sensorDeviceClass = _sensorDeviceClass[sensor] if sensor in _sensorDeviceClass else ''
            entities.append(
                GoeChargerSensor(
                    coordinator,
                    chargerName, 
                    sensorName, 
                    sensor, 
                    sensorUnit, 
                    sensorStateClass, 
                    sensorDeviceClass, 
                    correctionFactor,
                    charger
                )
            )

        for sensor in _sensorsv1:
            _add_sensor(sensor)

        if api_level == "2":
            for sensor in _sensorsv2:
                _add_sensor(sensor)
            
        return entities
    
    config = config_entry.as_dict()["data"]
    coordinator: GoeChargerUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    await coordinator.async_config_entry_first_refresh()

    chargerName = config[CONF_NAME]
    api_level = config[CONF_API_LEVEL]

    correctionFactor = 1.0
    if CONF_CORRECTION_FACTOR in config:
        try:
            correctionFactor = float(config[CONF_CORRECTION_FACTOR])
        except:
            correctionFactor = 1.0 

    _LOGGER.debug(f"charger name: '{chargerName}'")
    _LOGGER.debug(f"config: '{config}'")

    async_add_entities(_create_sensors_for_charger(chargerName, hass, correctionFactor, coordinator, None))


class GoeChargerSensor(CoordinatorEntity, SensorEntity):
    def __init__(
            self, coordinator, device_name, name, attribute, unit, stateClass, deviceClass, correctionFactor, charger
        ):
        """Initialize the go-eCharger sensor."""

        # super().__init__(coordinator.charger, coordinator, device_name, name)
        super().__init__(coordinator)

        self.attrs = {}

        self._attribute = attribute
        self._unit = unit
        self._attr_state_class = stateClass
        self._attr_device_class = deviceClass

        self.goeCharger = charger
        self.device_name = device_name
        self._name = f"{device_name} {name}"
        self.correctionFactor = correctionFactor

    @callback
    async def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        
        self._value = self.coordinator.data[self._attribute]["state"]
        self.async_write_ha_state()

    @property
    def state(self):
        """Return the state of the sensor."""

        # # TODO: Check if this try/exept is needed
        try:
            if (self._attribute == 'energy_total_corrected'):
                return self.coordinator.data['energy_total'] * self.correctionFactor
            if (self._attribute == 'current_session_charged_energy_corrected'):
                return self.coordinator.data['current_session_charged_energy'] * self.correctionFactor   
            return self.coordinator.data[self._attribute]
        except KeyError:
            return None

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit

    @property
    def unique_id(self):
        """Return the unique_id of the sensor."""
        return f"sensor.{DOMAIN}.{self.device_name}_{self._attribute}"
    