"""Custom types for stiebel_eltron_http."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .coordinator import StiebelEltronHttpDataUpdateCoordinator
    from .scrapper import StiebelEltronScrapingClient


type StiebelEltronHttpConfigEntry = ConfigEntry[StiebelEltronHttpData]


@dataclass
class StiebelEltronHttpData:
    """Data for the Stiebel Eltron ISG without Modbus integration."""

    client: StiebelEltronScrapingClient
    coordinator: StiebelEltronHttpDataUpdateCoordinator
    integration: Integration
