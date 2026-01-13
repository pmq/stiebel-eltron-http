"""Stiebel Eltron ISG scraping client."""

from __future__ import annotations

import re
import socket
from typing import Any

import aiohttp
import async_timeout
import bs4
from homeassistant.const import ATTR_SW_VERSION

from .const import (
    AUXILIARY_HEATER_STATUS_KEY,
    BOOSTER_HEATER_1_STATUS_KEY,
    BOOSTER_HEATER_2_STATUS_KEY,
    COMPRESSOR_STARTS_KEY,
    COMPRESSOR_STATUS_KEY,
    DEFROST_STATUS_KEY,
    DIAGNOSIS_HEAT_PUMP_STATUS_PATH,
    DIAGNOSIS_SYSTEM_PATH,
    DIAGNOSIS_SYSTEM_STATUS_PATH,
    EXPECTED_HTML_TITLE,
    FIELDS_I18N,
    FLOW_TEMPERATURE_KEY,
    HEATING_KEY,
    HTTP_CONNECTION_TIMEOUT,
    INFO_HEATPUMP_PATH,
    INFO_SYSTEM_PATH,
    LOGGER,
    MAC_ADDRESS_KEY,
    OUTSIDE_TEMPERATURE_KEY,
    POWER_CONSUMPTION_KEY,
    PROFILE_NETWORK_PATH,
    ROOM_HUMIDITY_KEY,
    ROOM_TEMPERATURE_KEY,
    TARGET_FLOW_TEMPERATURE_KEY,
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


def _get_field_i18n(field_key: str, language: str) -> str:
    """Get the internationalized field name for a given key and language."""
    lang_dict = FIELDS_I18N.get(language)
    if isinstance(lang_dict, dict):
        result = lang_dict.get(field_key)
        if result:
            return result

    error_msg = f"Unsupported language for i18n: {language}"
    raise ValueError(error_msg)


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


def _convert_number(value: str) -> float | None:
    """Convert a Stiebel Eltron ISG number to a float."""
    if isinstance(value, str):
        value = value.replace(",", ".").strip()
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
            language = self._extract_language_from_page_content(response)
            LOGGER.debug(
                "Connection test to %s successful, found language '%s'",
                self._host,
                language,
            )

        except aiohttp.ClientResponseError as exception:
            msg = f"Failed to connect to {self._host} - {exception}"
            raise StiebelEltronScrapingClientError(
                msg,
            ) from exception
        else:
            return response

    async def async_get_device_info(self) -> Any:
        """Retrieve device info from the ISG device."""
        result = {}

        result.update(await self.async_get_mac_address())
        result.update(await self.async_get_versions())

        return result

    async def async_get_mac_address(self) -> Any:
        """Retrieve the MAC address from the ISG device."""
        return await self.async_scrape_profile_network()

    async def async_get_versions(self) -> Any:
        """Retrieve the hardware and software versions from the ISG device."""
        return await self.async_scrape_diagnosis_system()

    async def async_fetch_all(self) -> Any:
        """Scrape all available data from the ISG web portal."""
        result = {}

        info_system_result = await self.async_scrape_info_system()
        result.update(info_system_result)

        info_system_heatpump = await self.async_scrape_info_heatpump()
        result.update(info_system_heatpump)

        diagnosis_heat_pump_status = (
            await self.async_scrape_diagnosis_heat_pump_status()
        )
        result.update(diagnosis_heat_pump_status)

        diagnosis_system_status = await self.async_scrape_diagnosis_system_status()
        result.update(diagnosis_system_status)

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

    async def async_scrape_diagnosis_system_status(self) -> Any:
        """Scrape data from the Diagnosis / System Status page."""
        url = f"http://{self._host}{DIAGNOSIS_SYSTEM_STATUS_PATH}"

        try:
            response = await self._api_wrapper(
                method="GET",
                url=url,
            )
            result = self._extract_diagnosis_system_status(response)

        except aiohttp.ClientResponseError as exception:
            msg = f"Failed to connect to {self._host} - {exception}"
            raise StiebelEltronScrapingClientError(
                msg,
            ) from exception
        else:
            return result

    async def async_scrape_diagnosis_heat_pump_status(self) -> Any:
        """Scrape data from the Diagnosis / Heat Pump Status page."""
        url = f"http://{self._host}{DIAGNOSIS_HEAT_PUMP_STATUS_PATH}"

        try:
            response = await self._api_wrapper(
                method="GET",
                url=url,
            )
            result = self._extract_diagnosis_heat_pump_status(response)

        except aiohttp.ClientResponseError as exception:
            msg = f"Failed to connect to {self._host} - {exception}"
            raise StiebelEltronScrapingClientError(
                msg,
            ) from exception
        else:
            return result

    async def async_scrape_diagnosis_system(self) -> Any:
        """Scrape data from the Diagnosis / System page."""
        url = f"http://{self._host}{DIAGNOSIS_SYSTEM_PATH}"

        try:
            response = await self._api_wrapper(
                method="GET",
                url=url,
            )
            result = self._extract_diagnosis_system(response)

        except aiohttp.ClientResponseError as exception:
            msg = f"Failed to connect to {self._host} - {exception}"
            raise StiebelEltronScrapingClientError(
                msg,
            ) from exception
        else:
            return result

    async def async_scrape_profile_network(self) -> Any:
        """Scrape data from the Profile / Network page."""
        url = f"http://{self._host}{PROFILE_NETWORK_PATH}"

        try:
            response = await self._api_wrapper(
                method="GET",
                url=url,
            )
            result = self._extract_profile_network(response)

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

    def _extract_language_from_page_content(self, page_content: str) -> str:
        """Extract the language from the HTML response."""
        soup = bs4.BeautifulSoup(page_content, "html.parser")
        return self._extract_language(soup)

    def _extract_language(self, soup: bs4.BeautifulSoup) -> str:
        """Extract the language from the HTML response."""
        lang_divs = soup.find_all("div", class_="eingestelle_sprache")

        if not lang_divs or not lang_divs[0].get_text(strip=True):
            LOGGER.warning(
                "No language div found, defaulting to English",
            )
            # try English as default
            return "ENGLISH"

        if len(lang_divs) > 1:
            LOGGER.warning(
                "Multiple language divs found, using the first one: %s",
                lang_divs,
            )

        return lang_divs[0].get_text(strip=True)

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
                return _convert_energy(curr_table_elems[1])

        return None  # not found

    def _extract_number(
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
                return _convert_number(curr_table_elems[1])

        return None  # not found

    def _extract_boolean(self, table: bs4.element.Tag, expected_header: str) -> bool:
        """
        Extract a boolean flag from the given table.

        Returns True if the 'on' icon is detected for the given header.
        Returns False if another icon is detected or the header is missing
        altogether.
        """
        table_rows = table.find_all("tr")
        for curr_table_row in table_rows:
            curr_table_elems = curr_table_row.find_all(["td", "th"])  # type: ignore  # noqa: PGH003

            if not curr_table_elems or len(curr_table_elems) < 2:  # noqa: PLR2004
                continue

            if curr_table_elems[0].get_text(strip=True) != expected_header:
                continue

            icon = curr_table_elems[1].find("img")
            if not icon:
                continue

            icon_name = icon.get("src")
            if not icon_name:
                continue

            return "ste-symbol_an-" in icon_name

        return False

    def _extract_version(self, table: bs4.element.Tag, language: str) -> float | str:
        major_version, minor_version, revision = None, None, None

        table_rows = table.find_all("tr")
        for curr_table_row in table_rows:
            curr_table_elems = curr_table_row.find_all(["td", "th"])  # type: ignore  # noqa: PGH003

            if not curr_table_elems:
                continue
            curr_table_elems = [elem.get_text(strip=True) for elem in curr_table_elems]

            if len(curr_table_elems) < 2:  # noqa: PLR2004
                continue

            if curr_table_elems[0] == _get_field_i18n("MAJOR_VERSION", language):
                major_version = curr_table_elems[1]
            elif curr_table_elems[0] == _get_field_i18n("MINOR_VERSION", language):
                minor_version = curr_table_elems[1]
            elif curr_table_elems[0] == _get_field_i18n("REVISION", language):
                revision = curr_table_elems[1]

        return f"{major_version}.{minor_version}.{revision}"

    def _extract_info_system(self, response: str) -> dict:
        """Extract the interesting values from the Info > System page."""
        soup = bs4.BeautifulSoup(response, "html.parser")
        result = {}

        # determine language
        language = self._extract_language(soup)
        LOGGER.debug("Detected language on Info > System page: %s", language)

        for curr_row in soup.find_all("tr"):
            curr_row_elems = curr_row.find_all(["td", "th"])  # type: ignore  # noqa: PGH003

            if not curr_row_elems:
                continue

            curr_row_elems = [elem.get_text(strip=True) for elem in curr_row_elems]

            # find the requested data
            if curr_row_elems[0] == _get_field_i18n("ACTUAL TEMPERATURE 1", language):
                result[ROOM_TEMPERATURE_KEY] = _convert_temperature(curr_row_elems[1])
            elif curr_row_elems[0] == _get_field_i18n("OUTSIDE TEMPERATURE", language):
                result[OUTSIDE_TEMPERATURE_KEY] = _convert_temperature(
                    curr_row_elems[1]
                )
            elif curr_row_elems[0] == _get_field_i18n("RELATIVE HUMIDITY 1", language):
                result[ROOM_HUMIDITY_KEY] = _convert_percentage(curr_row_elems[1])
            elif curr_row_elems[0] == _get_field_i18n(
                "ACTUAL TEMPERATURE HK 1", language
            ):
                result[FLOW_TEMPERATURE_KEY] = _convert_temperature(curr_row_elems[1])
            elif curr_row_elems[0] == _get_field_i18n("SET TEMPERATURE HK 1", language):
                result[TARGET_FLOW_TEMPERATURE_KEY] = _convert_temperature(
                    curr_row_elems[1]
                )

        # return the scraped data
        LOGGER.debug("Extracted data from Info > System page: %s", result)
        return result

    def _extract_info_heatpump(self, response: str) -> dict:
        """Extract the interesting values from the Info > Heat Pump page."""
        soup = bs4.BeautifulSoup(response, "html.parser")
        result = {}

        # determine language
        language = self._extract_language(soup)
        LOGGER.debug("Detected language on Info > Heat Pump page: %s", language)

        # find all tables
        all_tables = soup.find_all("table")

        for curr_table in all_tables:
            all_rows = curr_table.find_all("tr")  # type: ignore  # noqa: PGH003
            all_headers = all_rows[0].find_all(["th"])  # type: ignore  # noqa: PGH003

            curr_headers = [header.get_text(strip=True) for header in all_headers]

            if curr_headers[0] == _get_field_i18n("AMOUNT OF HEAT", language):
                result[HEATING_KEY] = self._extract_energy(
                    curr_table,  # type: ignore  # noqa: PGH003
                    _get_field_i18n("VD HEATING DAY", language),
                )
                result[TOTAL_HEATING_KEY] = self._extract_energy(
                    curr_table,  # type: ignore  # noqa: PGH003
                    _get_field_i18n("VD HEATING TOTAL", language),
                )
            elif curr_headers[0] == _get_field_i18n("POWER CONSUMPTION", language):
                result[POWER_CONSUMPTION_KEY] = self._extract_energy(
                    curr_table,  # type: ignore  # noqa: PGH003
                    _get_field_i18n("VD HEATING DAY", language),
                )
                result[TOTAL_POWER_CONSUMPTION_KEY] = self._extract_energy(
                    curr_table,  # type: ignore  # noqa: PGH003
                    _get_field_i18n("VD HEATING TOTAL", language),
                )
            elif curr_headers[0] == _get_field_i18n("STARTS", language):
                result[COMPRESSOR_STARTS_KEY] = self._extract_number(
                    curr_table,  # type: ignore  # noqa: PGH003
                    _get_field_i18n("COMPRESSOR", language),
                )

        # return the scraped data
        LOGGER.debug("Extracted data from Info > Heat Pump page: %s", result)
        return result

    def _extract_diagnosis_system_status(self, response: str) -> dict:
        """Extract the interesting values from the Diagnosis > System Status page."""
        soup = bs4.BeautifulSoup(response, "html.parser")

        # initialize value as 'off'
        result = {
            DEFROST_STATUS_KEY: False,
        }

        # determine language
        language = self._extract_language(soup)
        LOGGER.debug(
            "Detected language on Diagnosis > System Status page: %s", language
        )

        # find all tables
        all_tables = soup.find_all("table")

        for curr_table in all_tables:
            all_rows = curr_table.find_all("tr")  # type: ignore  # noqa: PGH003
            all_headers = all_rows[0].find_all(["th"])  # type: ignore  # noqa: PGH003

            curr_headers = [header.get_text(strip=True) for header in all_headers]

            if curr_headers[0] == _get_field_i18n("OPERATING MODE", language):
                result[DEFROST_STATUS_KEY] = self._extract_boolean(
                    curr_table,  # type: ignore  # noqa: PGH003
                    _get_field_i18n("DEFROST", language),
                )

        # return the scraped data
        LOGGER.debug("Extracted data from Diagnosis > System Status page: %s", result)
        return result

    def _extract_diagnosis_heat_pump_status(self, response: str) -> dict:
        """Extract the interesting values from the Diagnosis > Heat Pump Status page."""
        soup = bs4.BeautifulSoup(response, "html.parser")

        # initialize all values as 'off'
        result = {
            AUXILIARY_HEATER_STATUS_KEY: False,
            BOOSTER_HEATER_1_STATUS_KEY: False,
            BOOSTER_HEATER_2_STATUS_KEY: False,
            COMPRESSOR_STATUS_KEY: False,
        }

        # determine language
        language = self._extract_language(soup)
        LOGGER.debug(
            "Detected language on Diagnosis > Heat Pump Status page: %s", language
        )

        # find all tables
        all_tables = soup.find_all("table")

        for curr_table in all_tables:
            all_rows = curr_table.find_all("tr")  # type: ignore  # noqa: PGH003
            all_headers = all_rows[0].find_all(["th"])  # type: ignore  # noqa: PGH003

            curr_headers = [header.get_text(strip=True) for header in all_headers]

            if curr_headers[0] == _get_field_i18n("HEAT PUMP STATUS", language):
                result[COMPRESSOR_STATUS_KEY] = self._extract_boolean(
                    curr_table,  # type: ignore  # noqa: PGH003
                    _get_field_i18n("COMPRESSOR", language),
                )
                result[AUXILIARY_HEATER_STATUS_KEY] = self._extract_boolean(
                    curr_table,  # type: ignore  # noqa: PGH003
                    _get_field_i18n("AUXILIARY HEATER", language),
                )
                result[BOOSTER_HEATER_1_STATUS_KEY] = self._extract_boolean(
                    curr_table,  # type: ignore  # noqa: PGH003
                    _get_field_i18n("BOOSTER HEATER STAGE 1", language),
                )
                result[BOOSTER_HEATER_2_STATUS_KEY] = self._extract_boolean(
                    curr_table,  # type: ignore  # noqa: PGH003
                    _get_field_i18n("BOOSTER HEATER STAGE 2", language),
                )

        # return the scraped data
        LOGGER.debug(
            "Extracted data from Diagnosis > Heat Pump Status page: %s", result
        )
        return result

    def _extract_diagnosis_system(self, response: str) -> dict:
        """Extract the interesting values from the Diagnosis > System page."""
        soup = bs4.BeautifulSoup(response, "html.parser")
        result = {}

        # determine language
        language = self._extract_language(soup)
        LOGGER.debug("Detected language on Diagnosis > System page: %s", language)

        # find all tables
        all_tables = soup.find_all("table")

        for curr_table in all_tables:
            all_rows = curr_table.find_all("tr")  # type: ignore  # noqa: PGH003
            all_headers = all_rows[0].find_all(["th"])  # type: ignore  # noqa: PGH003

            curr_headers = [header.get_text(strip=True) for header in all_headers]
            match curr_headers[0]:
                case "ISG":
                    result[ATTR_SW_VERSION] = self._extract_version(
                        curr_table,  # type: ignore  # noqa: PGH003
                        language,
                    )

        # return the scraped data
        LOGGER.debug("Extracted data from Diagnosis > System page: %s", result)
        return result

    def _extract_profile_network(self, response: str) -> dict:
        """Extract the interesting values from the Profile > Network page."""
        soup = bs4.BeautifulSoup(response, "html.parser")
        result = {}

        full_text = soup.get_text()

        mac_addr_pattern = re.compile(r"(?:[0-9a-fA-F]:?){12}")
        found_mac_addresses = re.findall(mac_addr_pattern, full_text)
        if found_mac_addresses:
            result[MAC_ADDRESS_KEY] = found_mac_addresses[0]
        else:
            LOGGER.error("No MAC address found on Profile > Network page")

        # return the scraped data
        LOGGER.debug("Extracted data from Profile > Network page: %s", result)
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
                return await response.text(encoding="utf-8", errors="replace")

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
