"""StiebelEltronHttpEntity class."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.stiebel_eltron_http.const import LOGGER

from .coordinator import StiebelEltronHttpDataUpdateCoordinator


class StiebelEltronHttpEntity(
    CoordinatorEntity[StiebelEltronHttpDataUpdateCoordinator], SensorEntity
):
    """StiebelEltronHttpEntity class."""

    _attr_has_entity_name = True
    # entity_description = "Test of a description to see if it appears somewhere"

    def __init__(
        self,
        coordinator: StiebelEltronHttpDataUpdateCoordinator,
        entity_description: SensorEntityDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_unique_id = (
            coordinator.config_entry.entry_id + "_" + entity_description.key
        )
        LOGGER.debug("Setting this sensor unique_id to %s", self._attr_unique_id)

        self._attr_device_info = DeviceInfo(
            # configuration_url=router.host,
            # connections={(CONNECTION_NETWORK_MAC, self.status.lan_macaddr)},
            identifiers={
                (
                    coordinator.config_entry.domain,
                    coordinator.config_entry.entry_id,
                ),
            },
            manufacturer="Stiebel Eltron",
            model="ISG",
            name="Test name",
            sw_version="SW1.0",
            hw_version="HW1.0",
        )
