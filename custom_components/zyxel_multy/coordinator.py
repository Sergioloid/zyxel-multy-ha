"""Data update coordinator for Zyxel Multy."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ZapiAuthError, ZapiError, ZyxelMultyApi
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class ZyxelMultyCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage fetching Zyxel Multy data."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        username: str,
        password: str,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.api = ZyxelMultyApi(host, username, password)
        self._host = host

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the router."""
        try:
            # Fetch all data in parallel-ish fashion
            system_info = await self.api.get_system_info()
            devices = await self.api.get_network_devices()
            device_stats = await self.api.get_device_statistics()
            mesh_state = await self.api.get_mesh_devices_state()
            bandwidth = await self.api.get_current_bandwidth()

            # Try to get WAN status (may fail on some models)
            wan_connected = {}
            try:
                wan_connected = await self.api.is_wan_connected()
            except ZapiError:
                _LOGGER.debug("Could not fetch WAN status")

            internet_status = {}
            try:
                internet_status = await self.api.get_internet_status()
            except ZapiError:
                _LOGGER.debug("Could not fetch internet status")

            # Try speed test result (non-blocking, may be empty)
            speed_test = {}
            try:
                speed_test = await self.api.get_speed_test_result()
            except ZapiError:
                pass

            # Try firmware check
            firmware = {}
            try:
                firmware = await self.api.firmware_check()
            except ZapiError:
                _LOGGER.debug("Could not check firmware")

            return {
                "system_info": system_info,
                "devices": devices,
                "device_stats": device_stats,
                "mesh_state": mesh_state,
                "bandwidth": bandwidth,
                "wan_connected": wan_connected,
                "internet_status": internet_status,
                "speed_test": speed_test,
                "firmware": firmware,
                "host": self._host,
            }

        except ZapiAuthError as err:
            raise UpdateFailed(f"Authentication error: {err}") from err
        except ZapiError as err:
            raise UpdateFailed(f"Error communicating with router: {err}") from err
