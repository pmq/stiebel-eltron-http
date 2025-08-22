"""Stiebel Eltron ISG scraping client."""

from __future__ import annotations

import socket
from typing import Any

import aiohttp
import async_timeout
import bs4

from .const import (
    EXPECTED_HTML_TITLE,
    HTTP_CONNECTION_TIMEOUT,
    INFO_HEATPUMP_PATH,
    INFO_SYSTEM_PATH,
    LOGGER,
    OUTSIDE_TEMPERATURE_KEY,
    ROOM_HUMIDITY_KEY,
    ROOM_TEMPERATURE_KEY,
    TOTAL_HEATING_KEY,
    TOTAL_POWER_CONSUMPTION_KEY,
)


class StiebelEltronScrapingClientError(Exception):
    """Exception to indicate a general scraping error."""

    def __init__(self, message: str) -> None:
        """Initialize with an explanation message."""
        super().__init__(message)


class StiebelEltronScrapingClientCommunicationError(
    StiebelEltronScrapingClientError,
):
    """Exception to indicate a communication error."""


class StiebelEltronScrapingClientAuthenticationError(
    StiebelEltronScrapingClientError,
):
    """Exception to indicate an authentication error."""


def _verify_response_or_raise(response: aiohttp.ClientResponse) -> None:
    """Verify that the response is valid."""
    if response.status in (401, 403):
        msg = "Invalid credentials"
        raise StiebelEltronScrapingClientAuthenticationError(
            msg,
        )
    response.raise_for_status()


def _convert_temperature(value: str) -> float | None:
    """Convert a Stiebel Eltron ISG temperature format (23,3°C) to a float."""
    if isinstance(value, str):
        value = value.replace(",", ".").replace("°C", "").strip()
    try:
        return float(value)
    except ValueError:
        return None


def _convert_percentage(value: str) -> float | None:
    """Convert a Stiebel Eltron ISG temperature format (53,3%) to a float."""
    if isinstance(value, str):
        value = value.replace(",", ".").replace("%", "").strip()
    try:
        return float(value)
    except ValueError:
        return None


def _convert_energy(value: str) -> float | None:
    """Convert a Stiebel Eltron ISG energy format (24,249MWh) to a float in KWh."""
    is_kwh = "KWh" in value
    is_mwh = "MWh" in value
    if not (is_kwh or is_mwh):
        return None  # not a valid energy value

    clean_value = value.replace(",", ".").replace("MWh", "").replace("KWh", "").strip()
    try:
        result = float(clean_value)
        if is_mwh:
            result *= 1000  # Convert MWh to kWh

    except ValueError:
        return None
    else:
        return result


class StiebelEltronScrapingClient:
    """Scrape data from the Stiebel Eltron ISG web portal."""

    def __init__(
        self,
        host: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Stiebel Eltron scraping client."""
        self._host = host
        self._session = session

    async def async_test_connect(self) -> Any:
        """Test that we can connect."""
        url = f"http://{self._host}/"

        try:
            response = await self._api_wrapper(
                method="GET",
                url=url,
            )
            self._check_title(response)

        except aiohttp.ClientResponseError as exception:
            msg = f"Failed to connect to {self._host} - {exception}"
            raise StiebelEltronScrapingClientError(
                msg,
            ) from exception
        else:
            return response

    async def async_fetch_all(self) -> Any:
        """Scrape all available data from the ISG web portal."""
        result = {}

        info_system_result = await self.async_scrape_info_system()
        result.update(info_system_result)

        info_system_heatpump = await self.async_scrape_info_heatpump()
        result.update(info_system_heatpump)

        LOGGER.debug("Scraped data: %s", result)
        return result

    async def async_scrape_info_system(self) -> Any:
        """Scrape data from the Info / System page."""
        url = f"http://{self._host}{INFO_SYSTEM_PATH}"

        try:
            response = await self._api_wrapper(
                method="GET",
                url=url,
            )
            result = self._extract_info_system(response)

        except aiohttp.ClientResponseError as exception:
            msg = f"Failed to connect to {self._host} - {exception}"
            raise StiebelEltronScrapingClientError(
                msg,
            ) from exception
        else:
            return result

    async def async_scrape_info_heatpump(self) -> Any:
        """Scrape data from the Info / Heat Pump page."""
        url = f"http://{self._host}{INFO_HEATPUMP_PATH}"

        try:
            response = await self._api_wrapper(
                method="GET",
                url=url,
            )
            result = self._extract_info_heatpump(response)

        except aiohttp.ClientResponseError as exception:
            msg = f"Failed to connect to {self._host} - {exception}"
            raise StiebelEltronScrapingClientError(
                msg,
            ) from exception
        else:
            return result

    def _check_title(self, response: str) -> None:
        """Check if the title matches the expected."""
        soup = bs4.BeautifulSoup(response, "html.parser")
        title = soup.title.string if soup.title and soup.title.string else None
        LOGGER.debug(
            "Potential ISG replied with an HTML doc containing title: %s", title
        )
        if not title or EXPECTED_HTML_TITLE not in title:
            raise StiebelEltronScrapingClientError(title or "No title found")

    def _extract_energy(
        self, table: bs4.element.Tag, expected_header: str
    ) -> float | None:
        table_rows = table.find_all("tr")
        for curr_table_row in table_rows:
            curr_table_elems = curr_table_row.find_all(["td", "th"])  # type: ignore  # noqa: PGH003

            if not curr_table_elems:
                continue
            curr_table_elems = [elem.get_text(strip=True) for elem in curr_table_elems]

            if len(curr_table_elems) < 2:  # noqa: PLR2004
                continue

            if curr_table_elems[0] == expected_header:
                total_heat_output = _convert_energy(curr_table_elems[1])
                LOGGER.debug(f">>> Total energy found: {total_heat_output}")
                return total_heat_output

        return None  # not found

    def _extract_info_system(self, response: str) -> dict:
        """Extract the interesting values from the Info > System page."""
        soup = bs4.BeautifulSoup(response, "html.parser")
        result = {}

        for curr_row in soup.find_all("tr"):
            curr_row_elems = curr_row.find_all(["td", "th"])  # type: ignore  # noqa: PGH003

            if not curr_row_elems:
                continue

            curr_row_elems = [elem.get_text(strip=True) for elem in curr_row_elems]

            # find the requested data
            match curr_row_elems[0]:
                case "ACTUAL TEMPERATURE 1":
                    result[ROOM_TEMPERATURE_KEY] = _convert_temperature(
                        curr_row_elems[1]
                    )
                case "OUTSIDE TEMPERATURE":
                    result[OUTSIDE_TEMPERATURE_KEY] = _convert_temperature(
                        curr_row_elems[1]
                    )
                case "RELATIVE HUMIDITY 1":
                    result[ROOM_HUMIDITY_KEY] = _convert_percentage(curr_row_elems[1])

        # return the scraped data
        LOGGER.debug("Extracted data from Info > System page: %s", result)
        return result

    def _extract_info_heatpump(self, response: str) -> dict:
        """Extract the interesting values from the Info > Heat Pump page."""
        soup = bs4.BeautifulSoup(response, "html.parser")
        result = {}

        # find all tables
        all_tables = soup.find_all("table")

        for curr_table in all_tables:
            all_rows = curr_table.find_all("tr")  # type: ignore  # noqa: PGH003
            all_headers = all_rows[0].find_all(["th"])  # type: ignore  # noqa: PGH003

            curr_headers = [header.get_text(strip=True) for header in all_headers]
            match curr_headers[0]:
                case "AMOUNT OF HEAT":
                    result[TOTAL_HEATING_KEY] = self._extract_energy(
                        curr_table,  # type: ignore  # noqa: PGH003
                        "VD HEATING TOTAL",
                    )
                case "POWER CONSUMPTION":
                    result[TOTAL_POWER_CONSUMPTION_KEY] = self._extract_energy(
                        curr_table,  # type: ignore  # noqa: PGH003
                        "VD HEATING TOTAL",
                    )

        # return the scraped data
        LOGGER.debug("Extracted data from Info > Heat Pump page: %s", result)
        return result

    async def _api_wrapper(
        self,
        method: str,
        url: str,
        data: dict | None = None,
    ) -> Any:
        """Get information from the API."""
        try:
            headers = {"User-Agent": "StiebelEltronScrapingClient/1.0"}

            async with async_timeout.timeout(HTTP_CONNECTION_TIMEOUT):
                response = await self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                )
                _verify_response_or_raise(response)
                return await response.text()

        except TimeoutError as exception:
            msg = f"Timeout error fetching information - {exception}"
            raise StiebelEltronScrapingClientCommunicationError(
                msg,
            ) from exception

        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Error fetching information - {exception}"
            raise StiebelEltronScrapingClientCommunicationError(
                msg,
            ) from exception

        except Exception as exception:  # pylint: disable=broad-except
            msg = f"Something really wrong happened! - {exception}"
            raise StiebelEltronScrapingClientError(
                msg,
            ) from exception
