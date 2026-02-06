"""Constants for stiebel_eltron_http."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "stiebel_eltron_http"
HTTP_CONNECTION_TIMEOUT = 30  # seconds

# Magic strings in the ISG web interface
EXPECTED_HTML_TITLE = "STIEBEL ELTRON Reglersteuerung"  # hardcoded title in all langs
ICON_ON_SRC = "ste-symbol_an-"  # icon src path start for "on" (as in on/off) icons
LANGUAGE_DIV_CLASS = "eingestelle_sprache"  # div class name containing current language

# URL subpaths
INFO_SYSTEM_PATH = "/?s=1,0"
INFO_HEATPUMP_PATH = "/?s=1,1"
DIAGNOSIS_SYSTEM_STATUS_PATH = "/?s=2,0"
DIAGNOSIS_HEAT_PUMP_STATUS_PATH = "/?s=2,2"
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
FLOW_TEMPERATURE_KEY = "flow_temperature"
TARGET_FLOW_TEMPERATURE_KEY = "target_flow_temperature"
COMPRESSOR_STARTS_KEY = "compressor_starts"
COMPRESSOR_STATUS_KEY = "compressor_status"
AUXILIARY_HEATER_STATUS_KEY = "auxiliary_heater_status"
BOOSTER_HEATER_1_STATUS_KEY = "booster_heater_1_status"
BOOSTER_HEATER_2_STATUS_KEY = "booster_heater_2_status"
DEFROST_STATUS_KEY = "defrost_status"

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
        "ACTUAL TEMPERATURE HK 1": "ACTUAL TEMPERATURE HK 1",
        "SET TEMPERATURE HK 1": "SET TEMPERATURE HK 1",
        "STARTS": "STARTS",
        "COMPRESSOR": "COMPRESSOR",
        "HEAT PUMP STATUS": "HEAT PUMP STATUS",
        "AUXILIARY HEATER": "AUXILIARY HEATER",
        "BOOSTER HEATER STAGE 1": "BOOSTER HEATER STAGE 1",
        "BOOSTER HEATER STAGE 2": "BOOSTER HEATER STAGE 2",
        "OPERATING MODE": "OPERATING MODE",
        "DEFROST": "DEFROST",
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
        "ACTUAL TEMPERATURE HK 1": "ISTTEMPERATUR HK 1",
        "SET TEMPERATURE HK 1": "SOLLTEMPERATUR HK 1",
        "STARTS": "STARTS",
        "COMPRESSOR": "VERDICHTER",
        "HEAT PUMP STATUS": "STATUS WÄRMEPUMPE",
        "AUXILIARY HEATER": "BEGLEITHEIZUNG",
        "BOOSTER HEATER STAGE 1": "NHZ STUFE 1",
        "BOOSTER HEATER STAGE 2": "NHZ STUFE 2",
        "OPERATING MODE": "BETRIEBSSTATUS",
        "DEFROST": "ABTAUEN",
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
