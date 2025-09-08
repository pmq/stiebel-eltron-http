"""DataUpdateCoordinator for Stiebel Eltron ISG without Modbus."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from custom_components.stiebel_eltron_http.const import LOGGER

from .scrapper import (
    StiebelEltronScrapingClientAuthenticationError,
    StiebelEltronScrapingClientError,
)

if TYPE_CHECKING:
    from .data import StiebelEltronHttpConfigEntry


class StiebelEltronHttpDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage refreshing data using the scraping client."""

    config_entry: StiebelEltronHttpConfigEntry

    async def _async_setup(self) -> None:
        """Update data via the scraping client, loading only device info."""
        await super()._async_setup()

        try:
            self.device_data = (
                await self.config_entry.runtime_data.client.async_get_device_info()
            )
            LOGGER.debug(
                "First scraping from Stiebel Eltron ISG: %s",
                self.device_data,
            )

        except StiebelEltronScrapingClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception

        except StiebelEltronScrapingClientError as exception:
            raise UpdateFailed(exception) from exception

    async def _async_update_data(self) -> Any:
        """Update data via the scraping client."""
        try:
            newest_data = await self.config_entry.runtime_data.client.async_fetch_all()
            LOGGER.debug(
                "Scraped up-to-date data from Stiebel Eltron ISG: %s",
                newest_data,
            )

        except StiebelEltronScrapingClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception

        except StiebelEltronScrapingClientError as exception:
            raise UpdateFailed(exception) from exception

        else:
            return newest_data
