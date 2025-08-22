"""
Custom integration to integrate Stiebel Eltron ISG without Modbus with Home Assistant.

For more details about this integration, please refer to
https://github.com/pmq/stiebel_eltron_http
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.const import CONF_HOST, Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.loader import async_get_loaded_integration

from .const import DOMAIN, LOGGER
from .coordinator import StiebelEltronHttpDataUpdateCoordinator
from .data import StiebelEltronHttpConfigEntry, StiebelEltronHttpData
from .scrapper import StiebelEltronScrapingClient

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: StiebelEltronHttpConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    coordinator = StiebelEltronHttpDataUpdateCoordinator(
        hass=hass,
        logger=LOGGER,
        name=DOMAIN,
        update_interval=timedelta(minutes=1),
    )

    entry.runtime_data = StiebelEltronHttpData(
        client=StiebelEltronScrapingClient(
            host=entry.data[CONF_HOST],
            session=async_get_clientsession(hass),
        ),
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinator=coordinator,
    )

    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: StiebelEltronHttpConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: StiebelEltronHttpConfigEntry,
) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
