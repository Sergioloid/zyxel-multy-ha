"""Button platform for Zyxel Multy."""

from __future__ import annotations

import logging

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ZyxelMultyCoordinator
from .entity import ZyxelMultyEntity, ZyxelMultyMeshNodeEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Zyxel Multy buttons."""
    coordinator: ZyxelMultyCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[ButtonEntity] = [
        ZyxelRebootButton(coordinator),
        ZyxelSpeedTestButton(coordinator),
        ZyxelFirmwareCheckButton(coordinator),
    ]

    # Create reboot buttons for each mesh node
    mesh_state = coordinator.data.get("mesh_state", {})
    if isinstance(mesh_state, dict):
        devices = mesh_state.get("device", [])
        if isinstance(devices, list):
            for device in devices:
                if isinstance(device, dict):
                    mac = device.get("mac", device.get("al-mac", ""))
                    name = device.get("name", mac)
                    if mac:
                        entities.append(
                            ZyxelMeshNodeRebootButton(coordinator, mac, name)
                        )

    async_add_entities(entities)


class ZyxelRebootButton(ZyxelMultyEntity, ButtonEntity):
    """Reboot the router."""

    _attr_name = "Reboot"
    _attr_device_class = ButtonDeviceClass.RESTART
    _attr_icon = "mdi:restart"

    def __init__(self, coordinator: ZyxelMultyCoordinator) -> None:
        super().__init__(coordinator, "reboot")

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.api.system_restart()


class ZyxelSpeedTestButton(ZyxelMultyEntity, ButtonEntity):
    """Start a speed test."""

    _attr_name = "Speed Test"
    _attr_icon = "mdi:speedometer"

    def __init__(self, coordinator: ZyxelMultyCoordinator) -> None:
        super().__init__(coordinator, "speed_test")

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.api.start_speed_test()
        # Refresh data after a delay to get results
        await self.coordinator.async_request_refresh()


class ZyxelFirmwareCheckButton(ZyxelMultyEntity, ButtonEntity):
    """Check for firmware updates."""

    _attr_name = "Check Firmware"
    _attr_icon = "mdi:update"

    def __init__(self, coordinator: ZyxelMultyCoordinator) -> None:
        super().__init__(coordinator, "firmware_check")

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.api.firmware_check()
        await self.coordinator.async_request_refresh()


class ZyxelMeshNodeRebootButton(ZyxelMultyMeshNodeEntity, ButtonEntity):
    """Reboot a mesh node."""

    _attr_name = "Reboot"
    _attr_device_class = ButtonDeviceClass.RESTART
    _attr_icon = "mdi:restart"

    def __init__(
        self,
        coordinator: ZyxelMultyCoordinator,
        node_mac: str,
        node_name: str,
    ) -> None:
        super().__init__(coordinator, node_mac, node_name, "reboot")

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.api.restart_mesh_node(self._node_mac)
