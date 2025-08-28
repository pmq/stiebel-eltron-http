"""Config flow for the Stiebel Eltron ISG without Modbus integration."""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import urlsplit

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_DEVICE_ID, CONF_HOST, CONF_NAME

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigFlowResult

from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.service_info.ssdp import (
    ATTR_UPNP_FRIENDLY_NAME,
    ATTR_UPNP_PRESENTATION_URL,
    ATTR_UPNP_SERIAL,
    SsdpServiceInfo,
)
from slugify import slugify

from .const import DOMAIN, LOGGER, MAC_ADDRESS_KEY
from .scrapper import (
    StiebelEltronScrapingClient,
    StiebelEltronScrapingClientAuthenticationError,
    StiebelEltronScrapingClientCommunicationError,
    StiebelEltronScrapingClientError,
)


class StiebelEltronIsgHttpFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Stiebel Eltron ISG without Modbus."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}

        if user_input is not None:
            _default_host = user_input[CONF_HOST]
            self.config = {
                CONF_HOST: user_input[CONF_HOST],
            }

            try:
                # try to connect and verify that it looks like a Stiebel Eltron ISG
                await self._test_connect(host=self.config[CONF_HOST])

                # retrieve the MAC address from the device
                self.config[CONF_DEVICE_ID] = await self._get_mac_address(
                    host=self.config[CONF_HOST]
                )

                LOGGER.debug("Discovered device with config: %s", self.config)

                # set a unique ID based on the MAC address
                await self._format_and_set_unique_id(self.config[CONF_DEVICE_ID])

                return self.async_create_entry(
                    title=self.config[CONF_HOST],
                    data=user_input,
                )

            except StiebelEltronScrapingClientAuthenticationError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "auth"
            except StiebelEltronScrapingClientCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except StiebelEltronScrapingClientError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"

        _default_host = self.config[CONF_HOST] if hasattr(self, "config") else ""

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=_default_host): str,
                },
            ),
            errors=_errors,
        )

    async def async_step_ssdp(
        self, discovery_info: SsdpServiceInfo
    ) -> ConfigFlowResult:
        """Prepare configuration for a SSDP discovered device."""
        LOGGER.info("Discovered SSDP device with UPnP info: %s", discovery_info.upnp)
        url = urlsplit(discovery_info.upnp[ATTR_UPNP_PRESENTATION_URL])
        mac_address = format_mac(discovery_info.upnp[ATTR_UPNP_SERIAL])
        LOGGER.debug("Found MAC address from UPnP: %s", mac_address)

        self.config = {
            CONF_HOST: url.hostname,
        }

        self._async_abort_entries_match({CONF_HOST: self.config[CONF_HOST]})

        # set a unique ID based on the MAC address
        await self._format_and_set_unique_id(mac_address)

        self.context["title_placeholders"] = {
            CONF_NAME: discovery_info.upnp[ATTR_UPNP_FRIENDLY_NAME],
            CONF_HOST: self.config[CONF_HOST],
        }

        return await self.async_step_user()

    async def _test_connect(self, host: str) -> None:
        """Validate connection to ISG."""
        client = StiebelEltronScrapingClient(
            host=host,
            session=async_create_clientsession(self.hass),
        )
        await client.async_test_connect()

    async def _get_mac_address(self, host: str) -> str:
        """Retrieve the MAC address from the ISG."""
        client = StiebelEltronScrapingClient(
            host=host,
            session=async_create_clientsession(self.hass),
        )
        mac_address_result = await client.async_get_mac_address()

        if not mac_address_result:
            msg = "Could not retrieve MAC address"
            raise StiebelEltronScrapingClientError(msg)

        mac_address = mac_address_result.get(MAC_ADDRESS_KEY)
        LOGGER.debug("Found MAC address from ISG: %s", mac_address)

        return mac_address

    async def _format_and_set_unique_id(self, mac_address: str) -> None:
        """Format the MAC address and use it for unique ID."""
        _unique_id = slugify(mac_address)
        LOGGER.debug(
            "Formatting MAC address %s into unique ID %s", mac_address, _unique_id
        )
        await self.async_set_unique_id(_unique_id)
        self._abort_if_unique_id_configured(updates=self.config)
