"""Sensor platform for Stiebel Eltron ISG without Modbus."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfTemperature

from custom_components.stiebel_eltron_http.const import LOGGER

from .const import (
    AUXILIARY_HEATER_STATUS_KEY,
    BOOSTER_HEATER_1_STATUS_KEY,
    BOOSTER_HEATER_2_STATUS_KEY,
    COMPRESSOR_STARTS_KEY,
    COMPRESSOR_STATUS_KEY,
    DEFROST_STATUS_KEY,
    FLOW_TEMPERATURE_KEY,
    HEATING_KEY,
    OUTSIDE_TEMPERATURE_KEY,
    POWER_CONSUMPTION_KEY,
    ROOM_HUMIDITY_KEY,
    ROOM_TEMPERATURE_KEY,
    TARGET_FLOW_TEMPERATURE_KEY,
    TOTAL_HEATING_KEY,
    TOTAL_POWER_CONSUMPTION_KEY,
)
from .entity import StiebelEltronHttpEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import StiebelEltronHttpDataUpdateCoordinator
    from .data import StiebelEltronHttpConfigEntry


SENSOR_ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key=ROOM_TEMPERATURE_KEY,
        name="Room temperature",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=ROOM_HUMIDITY_KEY,
        name="Room relative humidity",
        icon="mdi:water-percent",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=OUTSIDE_TEMPERATURE_KEY,
        name="Outside temperature",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=HEATING_KEY,
        name="Heating",
        icon="mdi:radiator",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SensorEntityDescription(
        key=TOTAL_HEATING_KEY,
        name="Total heating",
        icon="mdi:radiator",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
    ),
    SensorEntityDescription(
        key=POWER_CONSUMPTION_KEY,
        name="Energy consumption",
        icon="mdi:lightning-bolt",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SensorEntityDescription(
        key=TOTAL_POWER_CONSUMPTION_KEY,
        name="Total energy consumption",
        icon="mdi:lightning-bolt",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
    ),
    SensorEntityDescription(
        key=FLOW_TEMPERATURE_KEY,
        name="Flow temperature",
        icon="mdi:water-thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=TARGET_FLOW_TEMPERATURE_KEY,
        name="Target flow temperature",
        icon="mdi:water-thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=COMPRESSOR_STARTS_KEY,
        name="Compressor starts",
        icon="mdi:heat-pump",
        native_unit_of_measurement=None,
        device_class=None,
        state_class=SensorStateClass.TOTAL,
    ),
)

BINARY_SENSOR_ENTITY_DESCRIPTIONS = (
    BinarySensorEntityDescription(
        key=COMPRESSOR_STATUS_KEY,
        name="Compressor status",
        icon="mdi:heat-pump",
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
    BinarySensorEntityDescription(
        key=AUXILIARY_HEATER_STATUS_KEY,
        name="Auxiliary heater status",
        icon="mdi:heating-coil",
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
    BinarySensorEntityDescription(
        key=BOOSTER_HEATER_1_STATUS_KEY,
        name="Booster heater stage 1 status",
        icon="mdi:heat-wave",
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
    BinarySensorEntityDescription(
        key=BOOSTER_HEATER_2_STATUS_KEY,
        name="Booster heater stage 2 status",
        icon="mdi:heat-wave",
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
    BinarySensorEntityDescription(
        key=DEFROST_STATUS_KEY,
        name="Defrost status",
        icon="mdi:snowflake-melt",
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: StiebelEltronHttpConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    async_add_entities(
        StiebelEltronHttpSensor(
            coordinator=entry.runtime_data.coordinator,
            entity_description=entity_description,
        )
        for entity_description in SENSOR_ENTITY_DESCRIPTIONS
    )
    async_add_entities(
        StiebelEltronHttpBinarySensor(
            coordinator=entry.runtime_data.coordinator,
            entity_description=entity_description,
        )
        for entity_description in BINARY_SENSOR_ENTITY_DESCRIPTIONS
    )


class StiebelEltronHttpSensor(StiebelEltronHttpEntity, SensorEntity):
    """Stiebel Eltron HTTP Sensor class."""

    def __init__(
        self,
        coordinator: StiebelEltronHttpDataUpdateCoordinator,
        entity_description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator, entity_description)

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        LOGGER.debug("Coordinator update received: %s", self.coordinator.data)

        new_value = self.coordinator.data.get(self.entity_description.key)
        LOGGER.debug(
            "Sensor %s updated with new value: %s",
            self.entity_description.key,
            new_value,
        )
        # update the sensor state based on the coordinator data
        self._attr_native_value = new_value

        return super()._handle_coordinator_update()


class StiebelEltronHttpBinarySensor(StiebelEltronHttpEntity, BinarySensorEntity):
    """Stiebel Eltron HTTP Binary Sensor class."""

    def __init__(
        self,
        coordinator: StiebelEltronHttpDataUpdateCoordinator,
        entity_description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor class."""
        super().__init__(coordinator, entity_description)

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        LOGGER.debug("Coordinator update received: %s", self.coordinator.data)

        new_value = self.coordinator.data.get(self.entity_description.key)
        LOGGER.debug(
            "Binary sensor %s updated with new value: %s",
            self.entity_description.key,
            new_value,
        )
        # update the sensor state based on the coordinator data
        self._attr_is_on = new_value

        return super()._handle_coordinator_update()
