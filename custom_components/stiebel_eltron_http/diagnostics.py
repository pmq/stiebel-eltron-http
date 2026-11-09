"""Diagnostics support for Stiebel Eltron ISG without Modbus."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_DEVICE_ID, CONF_HOST

from .const import MAC_ADDRESS_KEY

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.device_registry import DeviceEntry

    from .data import StiebelEltronHttpConfigEntry

# Keys whose values identify the user's network or device and must not leak
# into a diagnostics file posted on a public issue tracker.
TO_REDACT = {
    CONF_HOST,
    CONF_DEVICE_ID,
    MAC_ADDRESS_KEY,
    "unique_id",
    "title",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,  # noqa: ARG001
    entry: StiebelEltronHttpConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data.coordinator
    integration = entry.runtime_data.integration

    return {
        "entry": async_redact_data(entry.as_dict(), TO_REDACT),
        "integration": {
            "domain": integration.domain,
            "version": str(integration.version),
        },
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "last_exception": (
                repr(coordinator.last_exception) if coordinator.last_exception else None
            ),
            "update_interval": (
                coordinator.update_interval.total_seconds()
                if coordinator.update_interval
                else None
            ),
        },
        "device_data": async_redact_data(
            getattr(coordinator, "device_data", None) or {}, TO_REDACT
        ),
        "data": async_redact_data(coordinator.data or {}, TO_REDACT),
    }


async def async_get_device_diagnostics(
    hass: HomeAssistant,
    entry: StiebelEltronHttpConfigEntry,
    device: DeviceEntry,
) -> dict[str, Any]:
    """Return diagnostics for a device (one ISG per config entry)."""
    diagnostics = await async_get_config_entry_diagnostics(hass, entry)
    diagnostics["device"] = {
        "id": device.id,
        "name": device.name,
        "manufacturer": device.manufacturer,
        "model": device.model,
        "sw_version": device.sw_version,
        "configuration_url": "**REDACTED**" if device.configuration_url else None,
    }
    return diagnostics
