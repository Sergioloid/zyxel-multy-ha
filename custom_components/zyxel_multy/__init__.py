"""Zyxel Multy mesh router integration for Home Assistant."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import ZyxelMultyCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.BUTTON,
    Platform.DEVICE_TRACKER,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Zyxel Multy from a config entry."""
    coordinator = ZyxelMultyCoordinator(
        hass,
        host=entry.data[CONF_HOST],
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    await async_setup_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up Zyxel Multy services."""

    async def handle_reboot(call) -> None:
        """Handle the reboot service call."""
        entry_id = call.data.get("entry_id")
        mac = call.data.get("mac")
        coordinator: ZyxelMultyCoordinator = _get_coordinator(hass, entry_id)
        if mac:
            await coordinator.api.restart_mesh_node(mac)
        else:
            await coordinator.api.system_restart()
        await coordinator.async_request_refresh()

    async def handle_speed_test(call) -> None:
        """Handle the speed test service call."""
        entry_id = call.data.get("entry_id")
        coordinator: ZyxelMultyCoordinator = _get_coordinator(hass, entry_id)
        await coordinator.api.start_speed_test()
        await coordinator.async_request_refresh()

    async def handle_block_device(call) -> None:
        """Handle block device service call."""
        entry_id = call.data.get("entry_id")
        mac = call.data["mac_address"]
        duration = call.data.get("duration", 0)
        coordinator: ZyxelMultyCoordinator = _get_coordinator(hass, entry_id)
        await coordinator.api.block_device(mac, duration)
        await coordinator.async_request_refresh()

    async def handle_unblock_device(call) -> None:
        """Handle unblock device service call."""
        entry_id = call.data.get("entry_id")
        index = call.data["index"]
        coordinator: ZyxelMultyCoordinator = _get_coordinator(hass, entry_id)
        await coordinator.api.unblock_device(index)
        await coordinator.async_request_refresh()

    async def handle_set_wifi(call) -> None:
        """Handle set WiFi service call."""
        entry_id = call.data.get("entry_id")
        coordinator: ZyxelMultyCoordinator = _get_coordinator(hass, entry_id)
        await coordinator.api.set_wifi(
            ssid=call.data.get("ssid"),
            ssid_5g=call.data.get("ssid_5g"),
            password=call.data.get("password"),
            network=call.data.get("network", "main"),
        )
        await coordinator.async_request_refresh()

    async def handle_switch_led(call) -> None:
        """Handle LED switch service call."""
        entry_id = call.data.get("entry_id")
        mac = call.data["mac"]
        state = call.data["state"]
        brightness = call.data.get("brightness", 100)
        coordinator: ZyxelMultyCoordinator = _get_coordinator(hass, entry_id)
        await coordinator.api.switch_led(mac, state, brightness)
        await coordinator.async_request_refresh()

    async def handle_add_port_forward(call) -> None:
        """Handle add port forwarding rule."""
        entry_id = call.data.get("entry_id")
        coordinator: ZyxelMultyCoordinator = _get_coordinator(hass, entry_id)
        await coordinator.api.add_port_forward(
            service=call.data["service"],
            protocol=call.data.get("protocol", "TCP"),
            external_port=call.data["external_port"],
            external_port_end=call.data.get("external_port_end"),
            internal_port=call.data["internal_port"],
            local_ip=call.data["local_ip"],
        )
        await coordinator.async_request_refresh()

    async def handle_remove_port_forward(call) -> None:
        """Handle remove port forwarding rule."""
        entry_id = call.data.get("entry_id")
        index = call.data["index"]
        coordinator: ZyxelMultyCoordinator = _get_coordinator(hass, entry_id)
        await coordinator.api.remove_port_forward(index)
        await coordinator.async_request_refresh()

    async def handle_parental_block(call) -> None:
        """Handle parental control block."""
        entry_id = call.data.get("entry_id")
        coordinator: ZyxelMultyCoordinator = _get_coordinator(hass, entry_id)
        await coordinator.api.parental_block(call.data["profile_index"])
        await coordinator.async_request_refresh()

    async def handle_parental_unblock(call) -> None:
        """Handle parental control unblock."""
        entry_id = call.data.get("entry_id")
        coordinator: ZyxelMultyCoordinator = _get_coordinator(hass, entry_id)
        await coordinator.api.parental_unblock(call.data["profile_index"])
        await coordinator.async_request_refresh()

    async def handle_parental_bonus(call) -> None:
        """Handle parental control bonus time."""
        entry_id = call.data.get("entry_id")
        coordinator: ZyxelMultyCoordinator = _get_coordinator(hass, entry_id)
        await coordinator.api.parental_bonus(
            call.data["profile_index"], call.data["minutes"]
        )
        await coordinator.async_request_refresh()

    async def handle_wake_on_lan(call) -> None:
        """Handle Wake on LAN."""
        entry_id = call.data.get("entry_id")
        mac = call.data["mac_address"]
        coordinator: ZyxelMultyCoordinator = _get_coordinator(hass, entry_id)
        await coordinator.api.wake_on_lan(mac)

    async def handle_firmware_check(call) -> None:
        """Handle firmware check."""
        entry_id = call.data.get("entry_id")
        coordinator: ZyxelMultyCoordinator = _get_coordinator(hass, entry_id)
        await coordinator.api.firmware_check()
        await coordinator.async_request_refresh()

    services = {
        "reboot": handle_reboot,
        "speed_test": handle_speed_test,
        "block_device": handle_block_device,
        "unblock_device": handle_unblock_device,
        "set_wifi": handle_set_wifi,
        "switch_led": handle_switch_led,
        "add_port_forward": handle_add_port_forward,
        "remove_port_forward": handle_remove_port_forward,
        "parental_block": handle_parental_block,
        "parental_unblock": handle_parental_unblock,
        "parental_bonus": handle_parental_bonus,
        "wake_on_lan": handle_wake_on_lan,
        "firmware_check": handle_firmware_check,
    }

    for name, handler in services.items():
        if not hass.services.has_service(DOMAIN, name):
            hass.services.async_register(DOMAIN, name, handler)


def _get_coordinator(hass: HomeAssistant, entry_id: str | None) -> ZyxelMultyCoordinator:
    """Get coordinator from entry_id or first available."""
    if entry_id and entry_id in hass.data[DOMAIN]:
        return hass.data[DOMAIN][entry_id]
    return next(iter(hass.data[DOMAIN].values()))
