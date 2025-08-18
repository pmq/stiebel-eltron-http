"""Config flow for the Stiebel Eltron ISG without Modbus integration."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession
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

    async def _test_connect(self, host: str) -> None:
        """Validate connection to ISG."""
        client = StiebelEltronScrapingClient(
            host=host,
            session=async_create_clientsession(self.hass),
        )
        await client.async_test_connect()
