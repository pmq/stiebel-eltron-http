"""DataUpdateCoordinator for Stiebel Eltron ISG without Modbus."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .scrapper import (
    StiebelEltronScrapingClientAuthenticationError,
    StiebelEltronScrapingClientError,
)

if TYPE_CHECKING:
    from .data import StiebelEltronHttpConfigEntry


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class StiebelEltronHttpDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the scraping client."""

    config_entry: StiebelEltronHttpConfigEntry

    async def _async_update_data(self) -> Any:
        """Update data via library."""
        try:
            return await self.config_entry.runtime_data.client.async_fetch_all()

        except StiebelEltronScrapingClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except StiebelEltronScrapingClientError as exception:
            raise UpdateFailed(exception) from exception
