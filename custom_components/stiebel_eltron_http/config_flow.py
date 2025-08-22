"""Config flow for the Stiebel Eltron ISG without Modbus integration."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_MODEL, CONF_NAME
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.service_info.ssdp import (
    ATTR_UPNP_FRIENDLY_NAME,
    ATTR_UPNP_MODEL_NAME,
    ATTR_UPNP_PRESENTATION_URL,
    ATTR_UPNP_SERIAL,
    SsdpServiceInfo,
)
from slugify import slugify

from .const import DOMAIN, LOGGER

# FIXME
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
            try:
                await self._test_connect(host=user_input[CONF_HOST])

            except StiebelEltronScrapingClientAuthenticationError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "auth"
            except StiebelEltronScrapingClientCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except StiebelEltronScrapingClientError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"

            else:
                ## Do NOT use this in production code (PMQ: use the MAC address)
                ## The unique_id should never be something that can change
                ## https://developers.home-assistant.io/docs/config_entries_config_flow_handler#unique-ids
                unique_id = slugify(user_input[CONF_HOST])
                LOGGER.debug("Setting unique_id to %s", unique_id)

                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=user_input[CONF_HOST],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HOST,
                        default=(user_input or {}).get(CONF_HOST, vol.UNDEFINED),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    )
                },
            ),
            errors=_errors,
        )

    async def async_step_ssdp(
        self, discovery_info: SsdpServiceInfo
    ) -> ConfigFlowResult:
        """Prepare configuration for a SSDP discovered device."""
        LOGGER.debug("Discovered via SSDP: %s", discovery_info)
        LOGGER.debug("UPnP info: %s", discovery_info.upnp)
        url = urlsplit(discovery_info.upnp[ATTR_UPNP_PRESENTATION_URL])
        return await self._process_discovered_device(
            {
                CONF_HOST: url.hostname,
                CONF_MAC: format_mac(discovery_info.upnp[ATTR_UPNP_SERIAL]),
                CONF_NAME: discovery_info.upnp[ATTR_UPNP_FRIENDLY_NAME],
                CONF_MODEL: discovery_info.upnp[ATTR_UPNP_MODEL_NAME],
            }
        )

    async def _process_discovered_device(
        self, discovery_info: dict[str, Any]
    ) -> ConfigFlowResult:
        """Prepare configuration for a discovered device."""
        await self.async_set_unique_id(discovery_info[CONF_MAC])

        self._abort_if_unique_id_configured(
            updates={CONF_HOST: discovery_info[CONF_HOST]}
        )

        self.context.update(
            {
                "title_placeholders": {
                    CONF_NAME: discovery_info[CONF_NAME],
                    CONF_HOST: discovery_info[CONF_HOST],
                },
                "configuration_url": f"http://{discovery_info[CONF_HOST]}",
            }
        )

        self.discovery_schema = {
            vol.Required(CONF_HOST, default=discovery_info[CONF_HOST]): str,
        }

        return await self.async_step_user()

    async def _test_connect(self, host: str) -> None:
        """Validate connection to ISG."""
        client = StiebelEltronScrapingClient(
            host=host,
            session=async_create_clientsession(self.hass),
        )
        await client.async_test_connect()
