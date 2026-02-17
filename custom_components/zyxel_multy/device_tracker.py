"""Device tracker platform for Zyxel Multy."""

from __future__ import annotations

import logging

from homeassistant.components.device_tracker import SourceType
from homeassistant.components.device_tracker.config_entry import ScannerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ZyxelMultyCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up device tracker for Zyxel Multy."""
    coordinator: ZyxelMultyCoordinator = hass.data[DOMAIN][entry.entry_id]

    tracked: set[str] = set()

    @callback
    def _async_update_devices() -> None:
        """Update device trackers."""
        devices = coordinator.data.get("devices", [])
        if not isinstance(devices, list):
            return

        new_entities = []
        for device in devices:
            if not isinstance(device, dict):
                continue
            mac = device.get("al-mac", device.get("id", ""))
            if mac and mac not in tracked:
                tracked.add(mac)
                new_entities.append(
                    ZyxelDeviceTracker(coordinator, device, mac)
                )

        if new_entities:
            async_add_entities(new_entities)

    # Initial setup
    _async_update_devices()

    # Listen for updates to add new devices
    entry.async_on_unload(coordinator.async_add_listener(_async_update_devices))


class ZyxelDeviceTracker(CoordinatorEntity[ZyxelMultyCoordinator], ScannerEntity):
    """Zyxel Multy device tracker."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ZyxelMultyCoordinator,
        device_data: dict,
        mac: str,
    ) -> None:
        """Initialize the device tracker."""
        super().__init__(coordinator)
        self._mac = mac
        self._device_data = device_data
        self._attr_unique_id = f"{DOMAIN}_tracker_{mac}"
        device_name = device_data.get("device-name") or device_data.get("host-name") or mac
        self._attr_name = device_name

    @property
    def source_type(self) -> SourceType:
        """Return the source type."""
        return SourceType.ROUTER

    @property
    def is_connected(self) -> bool:
        """Return true if the device is connected."""
        device = self._find_device()
        if device:
            status = device.get("alive-status", "")
            if isinstance(status, str):
                return status.lower() in ("online", "true", "1", "alive")
            if isinstance(status, bool):
                return status
        return False

    @property
    def mac_address(self) -> str | None:
        """Return the MAC address."""
        return self._mac

    @property
    def ip_address(self) -> str | None:
        """Return the IP address."""
        device = self._find_device()
        if device:
            return device.get("ipv4-address")
        return None

    @property
    def hostname(self) -> str | None:
        """Return the hostname."""
        device = self._find_device()
        if device:
            return device.get("host-name")
        return None

    @property
    def extra_state_attributes(self) -> dict | None:
        """Return extra state attributes."""
        device = self._find_device()
        if not device:
            return None

        attrs = {}
        for key in (
            "connection-type",
            "device-type",
            "os-type",
            "manufacturer",
            "guest",
            "host-type",
            "join-time",
            "network-type",
        ):
            val = device.get(key)
            if val is not None:
                attrs[key.replace("-", "_")] = val

        return attrs if attrs else None

    def _find_device(self) -> dict | None:
        """Find this device in coordinator data."""
        devices = self.coordinator.data.get("devices", [])
        if not isinstance(devices, list):
            return None
        for dev in devices:
            if isinstance(dev, dict):
                mac = dev.get("al-mac", dev.get("id", ""))
                if mac == self._mac:
                    return dev
        return self._device_data
