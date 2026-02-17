"""Base entity for Zyxel Multy."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ZyxelMultyCoordinator


class ZyxelMultyEntity(CoordinatorEntity[ZyxelMultyCoordinator]):
    """Base class for Zyxel Multy entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ZyxelMultyCoordinator,
        entity_key: str,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._entity_key = entity_key
        host = coordinator.data.get("host", "unknown")
        self._attr_unique_id = f"{DOMAIN}_{host}_{entity_key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        system_info = self.coordinator.data.get("system_info", {})
        model = "Zyxel Multy"
        if isinstance(system_info, dict):
            model = system_info.get("model-name", "Zyxel Multy")

        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.data.get("host", "unknown"))},
            name=f"Zyxel {model}",
            manufacturer="Zyxel",
            model=model,
        )


class ZyxelMultyMeshNodeEntity(CoordinatorEntity[ZyxelMultyCoordinator]):
    """Base class for Zyxel Multy mesh node entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ZyxelMultyCoordinator,
        node_mac: str,
        node_name: str,
        entity_key: str,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._node_mac = node_mac
        self._node_name = node_name
        self._entity_key = entity_key
        self._attr_unique_id = f"{DOMAIN}_{node_mac}_{entity_key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for this mesh node."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._node_mac)},
            name=f"Zyxel Multy Node ({self._node_name})",
            manufacturer="Zyxel",
            via_device=(DOMAIN, self.coordinator.data.get("host", "unknown")),
        )
