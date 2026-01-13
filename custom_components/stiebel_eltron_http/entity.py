"""StiebelEltronHttpEntity class."""

from __future__ import annotations

from homeassistant.const import ATTR_SW_VERSION, CONF_HOST
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.entity import Entity, EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.stiebel_eltron_http.const import LOGGER, MAC_ADDRESS_KEY

from .coordinator import StiebelEltronHttpDataUpdateCoordinator


class StiebelEltronHttpEntity(
    CoordinatorEntity[StiebelEltronHttpDataUpdateCoordinator], Entity
):
    """StiebelEltronHttpEntity class."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: StiebelEltronHttpDataUpdateCoordinator,
        entity_description: EntityDescription,
    ) -> None:
        """Initialize entity."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_unique_id = (
            coordinator.config_entry.entry_id + "_" + entity_description.key
        )
        LOGGER.debug("Setting this sensor unique_id to %s", self._attr_unique_id)

        self._attr_device_info = DeviceInfo(
            configuration_url=f"http://{coordinator.config_entry.data[CONF_HOST]}",
            connections={
                (CONNECTION_NETWORK_MAC, coordinator.device_data[MAC_ADDRESS_KEY])
            },
            identifiers={
                (
                    coordinator.config_entry.domain,
                    coordinator.config_entry.entry_id,
                ),
            },
            manufacturer="Stiebel Eltron",
            model="Internet Service Gateway (ISG)",
            name="Stiebel Eltron ISG",
            sw_version=coordinator.device_data.get(ATTR_SW_VERSION, "-"),
        )
