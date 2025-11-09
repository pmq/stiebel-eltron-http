"""Constants for stiebel_eltron_http."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "stiebel_eltron_http"
HTTP_CONNECTION_TIMEOUT = 30  # seconds
EXPECTED_HTML_TITLE = "STIEBEL ELTRON Reglersteuerung"

INFO_SYSTEM_PATH = "/?s=1,0"
INFO_HEATPUMP_PATH = "/?s=1,1"
DIAGNOSIS_SYSTEM_PATH = "/?s=2,7"
PROFILE_NETWORK_PATH = "/?s=5,0"

# Sensor keys
ROOM_TEMPERATURE_KEY = "room_temperature"
ROOM_HUMIDITY_KEY = "room_relative_humidity"
OUTSIDE_TEMPERATURE_KEY = "outside_temperature"
TOTAL_HEATING_KEY = "total_heating_energy"
TOTAL_POWER_CONSUMPTION_KEY = "total_power_consumption"
HEATING_KEY = "heating_energy"
POWER_CONSUMPTION_KEY = "power_consumption"

# Other keys
MAC_ADDRESS_KEY = "mac_address"

# Text markers in the different ISG languages
FIELDS_I18N = {
    "ENGLISH": {
        "MAJOR_VERSION": "Major version",
        "MINOR_VERSION": "Minor version",
        "REVISION": "Revision",
        "ACTUAL TEMPERATURE 1": "ACTUAL TEMPERATURE 1",
        "RELATIVE HUMIDITY 1": "RELATIVE HUMIDITY 1",
        "OUTSIDE TEMPERATURE": "OUTSIDE TEMPERATURE",
        "AMOUNT OF HEAT": "AMOUNT OF HEAT",
        "POWER CONSUMPTION": "POWER CONSUMPTION",
        "VD HEATING DAY": "VD HEATING DAY",
        "VD HEATING TOTAL": "VD HEATING TOTAL",
    },
    "DEUTSCH": {
        "MAJOR_VERSION": "Hauptversionsnummer",
        "MINOR_VERSION": "Nebenversionsnummer",
        "REVISION": "Revisionsnummer",
        "ACTUAL TEMPERATURE 1": "ISTTEMPERATUR 1",
        "RELATIVE HUMIDITY 1": "RAUMFEUCHTE 1",
        "OUTSIDE TEMPERATURE": "AUSSENTEMPERATUR",
        "AMOUNT OF HEAT": "WÄRMEMENGE",
        "POWER CONSUMPTION": "LEISTUNGSAUFNAHME",
        "VD HEATING DAY": "VD HEIZEN TAG",
        "VD HEATING TOTAL": "VD HEIZEN SUMME",
    },
    "FRANÇAIS": "TODO",
    "NEDERLANDS": "TODO",
    "ITALIANO": "TODO",
    "SVENSKA": "TODO",
    "POLSKI": "TODO",
    "ČEŠTINA": "TODO",
    "MAGYAR": "TODO",
    "ESPAÑOL": "TODO",
    "SUOMI": "TODO",
    "DANSK": "TODO",
}
