"""Constants for stiebel_eltron_http."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "stiebel_eltron_http"
HTTP_CONNECTION_TIMEOUT = 30  # seconds
EXPECTED_HTML_TITLE = "STIEBEL ELTRON Reglersteuerung"

INFO_SYSTEM_PATH = "/?s=1,0"

# Sensor keys
ROOM_TEMPERATURE_KEY = "room_temperature"
ROOM_HUMIDITY_KEY = "room_relative_humidity"
OUTSIDE_TEMPERATURE_KEY = "outside_temperature"
