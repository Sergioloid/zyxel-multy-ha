"""Binary sensor platform for Zyxel Multy."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ZyxelMultyCoordinator
from .entity import ZyxelMultyEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Zyxel Multy binary sensors."""
    coordinator: ZyxelMultyCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[BinarySensorEntity] = [
        ZyxelWanConnectedSensor(coordinator),
        ZyxelInternetStatusSensor(coordinator),
        ZyxelFirmwareUpdateAvailableSensor(coordinator),
    ]

    async_add_entities(entities)


class ZyxelWanConnectedSensor(ZyxelMultyEntity, BinarySensorEntity):
    """WAN port connected."""

    _attr_name = "WAN Connected"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_icon = "mdi:ethernet"

    def __init__(self, coordinator: ZyxelMultyCoordinator) -> None:
        super().__init__(coordinator, "wan_connected")

    @property
    def is_on(self) -> bool | None:
        wan = self.coordinator.data.get("wan_connected", {})
        if isinstance(wan, dict):
            output = wan.get("output", wan)
            if isinstance(output, dict):
                # The response may vary; check for common patterns
                val = output.get("is-connected", output.get("result"))
                if isinstance(val, bool):
                    return val
                if isinstance(val, str):
                    return val.lower() in ("true", "connected", "yes", "1")
        return None


class ZyxelInternetStatusSensor(ZyxelMultyEntity, BinarySensorEntity):
    """Internet connectivity status."""

    _attr_name = "Internet Connected"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_icon = "mdi:web"

    def __init__(self, coordinator: ZyxelMultyCoordinator) -> None:
        super().__init__(coordinator, "internet_status")

    @property
    def is_on(self) -> bool | None:
        status = self.coordinator.data.get("internet_status", {})
        if isinstance(status, dict):
            output = status.get("output", status)
            if isinstance(output, dict):
                val = output.get("status", output.get("result"))
                if isinstance(val, bool):
                    return val
                if isinstance(val, str):
                    return val.lower() in ("true", "connected", "yes", "1", "ok")
        return None


class ZyxelFirmwareUpdateAvailableSensor(ZyxelMultyEntity, BinarySensorEntity):
    """Firmware update available."""

    _attr_name = "Firmware Update Available"
    _attr_device_class = BinarySensorDeviceClass.UPDATE
    _attr_icon = "mdi:update"

    def __init__(self, coordinator: ZyxelMultyCoordinator) -> None:
        super().__init__(coordinator, "firmware_update_available")

    @property
    def is_on(self) -> bool | None:
        fw = self.coordinator.data.get("firmware", {})
        if isinstance(fw, dict):
            output = fw.get("output", fw)
            if isinstance(output, dict):
                result = output.get("result", "")
                version = output.get("version")
                if version and result:
                    return "new" in str(result).lower() or "available" in str(result).lower()
        return False

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        fw = self.coordinator.data.get("firmware", {})
        if isinstance(fw, dict):
            output = fw.get("output", fw)
            if isinstance(output, dict):
                return {
                    "version": output.get("version", ""),
                    "release_date": output.get("release-date", ""),
                    "release_note": output.get("release-note", ""),
                    "firmware_name": output.get("firmware-name", ""),
                }
        return None
