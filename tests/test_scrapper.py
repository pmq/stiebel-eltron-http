"""Tests for parsing localized ISG pages."""

# This project uses unittest discovery; the parser methods are intentionally
# exercised directly so the fixtures stay independent of Home Assistant I/O.
# ruff: noqa: PT009, SLF001

from pathlib import Path
from unittest import TestCase

from custom_components.stiebel_eltron_http.const import (
    DHW_TEMPERATURE_KEY,
    TARGET_DHW_TEMPERATURE_KEY,
)
from custom_components.stiebel_eltron_http.scrapper import (
    StiebelEltronScrapingClient,
)
from custom_components.stiebel_eltron_http.sensor import SENSOR_ENTITY_DESCRIPTIONS

FIXTURE_DIR = Path(__file__).parent / "fixtures"


class InfoSystemParserTests(TestCase):
    """Test model-independent values from the Info > System page."""

    def setUp(self) -> None:
        """Create a parser without making network requests."""
        self.client = StiebelEltronScrapingClient(
            host="example.invalid",
            session=None,  # type: ignore[arg-type]
        )

    def test_extracts_dhw_temperatures_in_supported_languages(self) -> None:
        """DHW values are parsed from the localized DHW table."""
        cases = (
            ("info_system_en.html", 44.0, 43.0),
            ("info_system_de.html", 45.1, 42.5),
            ("info_system_fr.html", 49.7, 43.0),
        )

        for fixture_name, actual_temperature, target_temperature in cases:
            with self.subTest(fixture=fixture_name):
                response = (FIXTURE_DIR / fixture_name).read_text(encoding="utf-8")

                result = self.client._extract_info_system(response)

                self.assertEqual(result[DHW_TEMPERATURE_KEY], actual_temperature)
                self.assertEqual(result[TARGET_DHW_TEMPERATURE_KEY], target_temperature)

    def test_ignores_generic_temperature_rows_outside_dhw_table(self) -> None:
        """Nested generic rows in a layout table do not override DHW readings."""
        response = (FIXTURE_DIR / "info_system_en.html").read_text(encoding="utf-8")

        result = self.client._extract_info_system(response)

        self.assertEqual(result[DHW_TEMPERATURE_KEY], 44.0)
        self.assertEqual(result[TARGET_DHW_TEMPERATURE_KEY], 43.0)

    def test_omits_dhw_values_when_table_is_not_available(self) -> None:
        """Systems without a DHW table keep the optional sensors unavailable."""
        response = """
            <html>
              <div class="eingestelle_sprache">ENGLISH</div>
              <table>
                <tr><th>HEATING</th></tr>
                <tr><td>OUTSIDE TEMPERATURE</td><td>8,5°C</td></tr>
              </table>
            </html>
        """

        result = self.client._extract_info_system(response)

        self.assertNotIn(DHW_TEMPERATURE_KEY, result)
        self.assertNotIn(TARGET_DHW_TEMPERATURE_KEY, result)


class SensorDescriptionTests(TestCase):
    """Test that parsed DHW values are exposed as Home Assistant sensors."""

    def test_registers_both_dhw_temperature_sensors(self) -> None:
        """Actual and target DHW temperatures have entity descriptions."""
        sensor_keys = {description.key for description in SENSOR_ENTITY_DESCRIPTIONS}

        self.assertTrue(
            {DHW_TEMPERATURE_KEY, TARGET_DHW_TEMPERATURE_KEY} <= sensor_keys
        )
