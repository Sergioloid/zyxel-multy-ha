"""Switch platform for Zyxel Multy."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ZyxelMultyCoordinator
from .entity import ZyxelMultyMeshNodeEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Zyxel Multy switches."""
    coordinator: ZyxelMultyCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SwitchEntity] = []

    # Create LED switches for each mesh node
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
                            ZyxelMeshNodeLedSwitch(coordinator, mac, name)
                        )

    async_add_entities(entities)


class ZyxelMeshNodeLedSwitch(ZyxelMultyMeshNodeEntity, SwitchEntity):
    """LED switch for a mesh node."""

    _attr_name = "LED"
    _attr_icon = "mdi:led-on"

    def __init__(
        self,
        coordinator: ZyxelMultyCoordinator,
        node_mac: str,
        node_name: str,
    ) -> None:
        super().__init__(coordinator, node_mac, node_name, "led")
        self._is_on: bool | None = True

    @property
    def is_on(self) -> bool | None:
        return self._is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the LED."""
        await self.coordinator.api.switch_led(self._node_mac, "On", 100)
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the LED."""
        await self.coordinator.api.switch_led(self._node_mac, "Off", 0)
        self._is_on = False
        self.async_write_ha_state()
