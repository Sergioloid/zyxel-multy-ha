"""Zyxel Multy ZAPI client."""

from __future__ import annotations

import logging
import ssl
import time
from typing import Any

import aiohttp

from .const import (
    NS_AUTH,
    NS_EASY123,
    NS_FIREWALL_V4,
    NS_FIRMWARE,
    NS_NAT_GENERAL,
    NS_NETWORK_DEVICE,
    NS_PARENTAL,
    NS_SPEED_TEST,
    NS_SYSTEM,
    NS_WIFI_SYSTEM,
    ZAPI_PATH,
    ZAPI_XMLNS,
)

_LOGGER = logging.getLogger(__name__)


class ZapiError(Exception):
    """ZAPI error."""


class ZapiAuthError(ZapiError):
    """Authentication error."""


class ZyxelMultyApi:
    """Client for the Zyxel Multy ZAPI."""

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        """Initialize the API client."""
        self._host = host
        self._username = username
        self._password = password
        self._session = session
        self._token: str | None = None
        self._own_session = session is None
        self._base_url = f"https://{host}{ZAPI_PATH}"

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure we have an active session."""
        if self._session is None or self._session.closed:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            self._session = aiohttp.ClientSession(connector=connector)
            self._own_session = True
        return self._session

    async def close(self) -> None:
        """Close the session."""
        if self._own_session and self._session and not self._session.closed:
            await self._session.close()

    def _build_rpc(
        self,
        operation: str,
        namespace: str,
        root: str,
        config: dict[str, Any] | None = None,
        source: str = "running",
        edit_operation: str | None = None,
    ) -> dict[str, Any]:
        """Build an RPC request envelope."""
        params: dict[str, Any] = {}

        if operation == "get-config":
            params["source"] = source
            params["filter"] = [
                {
                    "xmlns": namespace,
                    "root": root,
                    "type": "subtree",
                }
            ]
        elif operation == "edit-config":
            params["target"] = "running"
            params["xmlns"] = namespace
            params["root"] = root
            if config:
                params["config"] = [
                    {
                        "xmlns": namespace,
                        "root": root,
                        **config,
                    }
                ]
        else:  # rpc
            params["xmlns"] = namespace
            params["root"] = root
            if config:
                params["config"] = [
                    {
                        "xmlns": namespace,
                        "root": root,
                        **config,
                    }
                ]

        rpc: dict[str, Any] = {
            "rpc": {
                "xmlns": ZAPI_XMLNS,
                "message-id": int(time.time()),
                "operation": operation,
                "params": params,
            }
        }

        if edit_operation:
            rpc["rpc"]["edit-config-operation"] = edit_operation

        return rpc

    async def _request(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Send a request to the ZAPI endpoint."""
        session = await self._ensure_session()

        headers = {"Content-Type": "application/json"}
        cookies = {}
        if self._token:
            cookies["token"] = self._token

        try:
            async with session.post(
                self._base_url,
                json=payload,
                headers=headers,
                cookies=cookies,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status == 401:
                    self._token = None
                    raise ZapiAuthError("Authentication failed or token expired")
                if resp.status != 200:
                    text = await resp.text()
                    raise ZapiError(f"HTTP {resp.status}: {text}")
                return await resp.json()
        except aiohttp.ClientError as err:
            raise ZapiError(f"Connection error: {err}") from err

    async def authenticate(self) -> str:
        """Authenticate and get a session token."""
        payload = self._build_rpc(
            operation="rpc",
            namespace=NS_AUTH,
            root="authentication",
            config={
                "user-authentication-order": ["local"],
                "user": [
                    {
                        "name": self._username,
                        "password": self._password,
                    }
                ],
            },
        )

        result = await self._request(payload)
        try:
            token = result["rpc"]["params"]["config"][0]["output"]["token"]
        except (KeyError, IndexError, TypeError):
            # Try alternative response paths
            try:
                token = result["output"]["token"]
            except (KeyError, TypeError) as err:
                raise ZapiAuthError(
                    f"Could not extract token from response: {result}"
                ) from err

        self._token = token
        _LOGGER.debug("Successfully authenticated with Zyxel Multy router")
        return token

    async def _authenticated_request(
        self, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Make an authenticated request, re-authenticating if needed."""
        if not self._token:
            await self.authenticate()

        try:
            return await self._request(payload)
        except ZapiAuthError:
            _LOGGER.debug("Token expired, re-authenticating")
            await self.authenticate()
            return await self._request(payload)

    def _extract_config(self, result: dict[str, Any]) -> Any:
        """Extract config data from response."""
        try:
            return result["rpc"]["params"]["config"][0]
        except (KeyError, IndexError, TypeError):
            try:
                return result["rpc"]["params"]
            except (KeyError, TypeError):
                return result

    # ===== System =====

    async def get_system_info(self) -> dict[str, Any]:
        """Get basic system information."""
        payload = self._build_rpc("rpc", NS_SYSTEM, "basic-system-info")
        result = await self._authenticated_request(payload)
        return self._extract_config(result)

    async def get_system_state(self) -> dict[str, Any]:
        """Get system state (clock, platform, usage)."""
        payload = self._build_rpc("rpc", NS_SYSTEM, "system-state")
        result = await self._authenticated_request(payload)
        return self._extract_config(result)

    async def get_api_version(self) -> dict[str, Any]:
        """Get API version."""
        payload = self._build_rpc("rpc", NS_SYSTEM, "api-version")
        result = await self._authenticated_request(payload)
        return self._extract_config(result)

    async def get_current_bandwidth(self) -> dict[str, Any]:
        """Get current bandwidth usage."""
        payload = self._build_rpc("rpc", NS_SYSTEM, "current-band-width")
        result = await self._authenticated_request(payload)
        return self._extract_config(result)

    async def system_restart(self) -> dict[str, Any]:
        """Reboot the router."""
        payload = self._build_rpc("rpc", NS_SYSTEM, "system-restart")
        return await self._authenticated_request(payload)

    async def system_shutdown(self) -> dict[str, Any]:
        """Shutdown the router."""
        payload = self._build_rpc("rpc", NS_SYSTEM, "system-shutdown")
        return await self._authenticated_request(payload)

    async def wake_on_lan(self, mac_address: str) -> dict[str, Any]:
        """Send Wake on LAN packet."""
        payload = self._build_rpc(
            "rpc",
            NS_SYSTEM,
            "system-wake-on-lan",
            config={"input": {"mac-address": mac_address}},
        )
        return await self._authenticated_request(payload)

    # ===== WiFi =====

    async def get_wifi_config(self, network: str = "main") -> dict[str, Any]:
        """Get WiFi configuration."""
        payload = self._build_rpc(
            "rpc",
            NS_EASY123,
            "get-wifi-configuration",
            config={"input": {"network": network}},
        )
        result = await self._authenticated_request(payload)
        return self._extract_config(result)

    async def set_wifi(
        self,
        ssid: str | None = None,
        ssid_5g: str | None = None,
        password: str | None = None,
        network: str = "main",
    ) -> dict[str, Any]:
        """Set WiFi SSID and/or password."""
        input_data: dict[str, Any] = {"network": network}
        if ssid:
            input_data["ssid"] = ssid
        if ssid_5g:
            input_data["ssid-5g"] = ssid_5g
        if password:
            input_data["psk"] = {"key": password}

        payload = self._build_rpc(
            "rpc", NS_EASY123, "set-wifi", config={"input": input_data}
        )
        return await self._authenticated_request(payload)

    async def is_wan_connected(self) -> dict[str, Any]:
        """Check if WAN port is connected."""
        payload = self._build_rpc("rpc", NS_EASY123, "is-wan-port-connected")
        result = await self._authenticated_request(payload)
        return self._extract_config(result)

    async def get_internet_status(self) -> dict[str, Any]:
        """Get internet access status."""
        payload = self._build_rpc("rpc", NS_EASY123, "access-internet-status")
        result = await self._authenticated_request(payload)
        return self._extract_config(result)

    # ===== Speed Test =====

    async def start_speed_test(
        self,
        device_mac: str = "",
        target: str = "Internet",
    ) -> dict[str, Any]:
        """Start a speed test."""
        test_id = str(int(time.time()))
        payload = self._build_rpc(
            "rpc",
            NS_SPEED_TEST,
            "speed-test",
            config={
                "input": {
                    "originator": 1,
                    "device-mac": device_mac,
                    "test-id": test_id,
                    "target": target,
                }
            },
        )
        return await self._authenticated_request(payload)

    async def get_speed_test_result(self) -> dict[str, Any]:
        """Get speed test result."""
        payload = self._build_rpc("rpc", NS_SPEED_TEST, "test-result")
        result = await self._authenticated_request(payload)
        return self._extract_config(result)

    async def get_speed_test_history(
        self, device_mac: str = "", count: int = 10
    ) -> dict[str, Any]:
        """Get speed test history."""
        payload = self._build_rpc(
            "rpc",
            NS_SPEED_TEST,
            "get-history",
            config={"input": {"device-mac": device_mac, "number": count}},
        )
        result = await self._authenticated_request(payload)
        return self._extract_config(result)

    # ===== Network Devices =====

    async def get_network_devices(self) -> list[dict[str, Any]]:
        """Get all connected devices."""
        payload = self._build_rpc("get-config", NS_NETWORK_DEVICE, "network-devices")
        result = await self._authenticated_request(payload)
        config = self._extract_config(result)
        if isinstance(config, dict):
            return config.get("device", [])
        return []

    async def get_device_statistics(self) -> dict[str, Any]:
        """Get device statistics (total clients, online, etc.)."""
        payload = self._build_rpc("rpc", NS_NETWORK_DEVICE, "get-device-statistics")
        result = await self._authenticated_request(payload)
        return self._extract_config(result)

    async def set_device_name(self, device_id: str, name: str) -> dict[str, Any]:
        """Set device friendly name."""
        payload = self._build_rpc(
            "rpc",
            NS_NETWORK_DEVICE,
            "set-device-name",
            config={"input": {"id": device_id, "name": name}},
        )
        return await self._authenticated_request(payload)

    # ===== Firewall / Block =====

    async def block_device(
        self, mac_address: str, lasting_time: int = 0
    ) -> dict[str, Any]:
        """Block a device by MAC address."""
        payload = self._build_rpc(
            "rpc",
            NS_FIREWALL_V4,
            "block",
            config={
                "input": {
                    "mac-address": mac_address,
                    "lasting-time": lasting_time,
                }
            },
        )
        return await self._authenticated_request(payload)

    async def unblock_device(self, index: str) -> dict[str, Any]:
        """Unblock a device by rule index."""
        payload = self._build_rpc(
            "rpc",
            NS_FIREWALL_V4,
            "unblock",
            config={"input": {"index": index}},
        )
        return await self._authenticated_request(payload)

    # ===== NAT / Port Forwarding =====

    async def get_nat_config(self) -> dict[str, Any]:
        """Get NAT/port forwarding configuration."""
        payload = self._build_rpc(
            "get-config",
            "urn:zyxel:cpe:applications:zyxel-applications-nat",
            "nat",
        )
        result = await self._authenticated_request(payload)
        return self._extract_config(result)

    async def add_port_forward(
        self,
        service: str,
        protocol: str,
        external_port: int,
        internal_port: int,
        local_ip: str,
        external_port_end: int | None = None,
    ) -> dict[str, Any]:
        """Add a port forwarding rule."""
        if external_port_end is None:
            external_port_end = external_port

        payload = self._build_rpc(
            "rpc",
            NS_NAT_GENERAL,
            "add-rule",
            config={
                "input": {
                    "service": service,
                    "service-index": 0,
                    "protocol": protocol,
                    "external-port": external_port,
                    "external-port-end": external_port_end,
                    "internal-port": internal_port,
                    "local-ip": local_ip,
                }
            },
        )
        return await self._authenticated_request(payload)

    async def remove_port_forward(self, index: int) -> dict[str, Any]:
        """Remove a port forwarding rule."""
        payload = self._build_rpc(
            "rpc",
            NS_NAT_GENERAL,
            "remove-rule",
            config={"input": {"index": index}},
        )
        return await self._authenticated_request(payload)

    # ===== Parental Control =====

    async def get_parental_config(self) -> dict[str, Any]:
        """Get parental control configuration."""
        payload = self._build_rpc("get-config", NS_PARENTAL, "top")
        result = await self._authenticated_request(payload)
        return self._extract_config(result)

    async def parental_block(self, profile_index: str) -> dict[str, Any]:
        """Block a parental control profile (pause internet)."""
        payload = self._build_rpc(
            "rpc",
            NS_PARENTAL,
            "block",
            config={"input": {"index": profile_index}},
        )
        return await self._authenticated_request(payload)

    async def parental_unblock(self, profile_index: str) -> dict[str, Any]:
        """Unblock a parental control profile (resume internet)."""
        payload = self._build_rpc(
            "rpc",
            NS_PARENTAL,
            "unblock",
            config={"input": {"index": profile_index}},
        )
        return await self._authenticated_request(payload)

    async def parental_bonus(
        self, profile_index: str, minutes: int
    ) -> dict[str, Any]:
        """Give bonus time to a parental control profile."""
        payload = self._build_rpc(
            "rpc",
            NS_PARENTAL,
            "bonus",
            config={"input": {"index": profile_index, "minute": minutes}},
        )
        return await self._authenticated_request(payload)

    # ===== Mesh / WiFi System =====

    async def get_mesh_devices_state(self) -> dict[str, Any]:
        """Get state of all mesh devices."""
        payload = self._build_rpc("rpc", NS_WIFI_SYSTEM, "system-devices-state")
        result = await self._authenticated_request(payload)
        return self._extract_config(result)

    async def restart_mesh_node(self, mac: str) -> dict[str, Any]:
        """Restart a specific mesh node."""
        payload = self._build_rpc(
            "rpc",
            NS_WIFI_SYSTEM,
            "restart",
            config={"input": {"mac": mac}},
        )
        return await self._authenticated_request(payload)

    async def switch_led(
        self, mac: str, state: str, brightness: int = 100
    ) -> dict[str, Any]:
        """Switch LED on a mesh node."""
        payload = self._build_rpc(
            "rpc",
            NS_WIFI_SYSTEM,
            "switch-led",
            config={
                "input": {
                    "mac": mac,
                    "led-switch": state,
                    "led-brightness-level": brightness,
                }
            },
        )
        return await self._authenticated_request(payload)

    async def rename_mesh_node(self, mac: str, name: str) -> dict[str, Any]:
        """Rename a mesh node."""
        payload = self._build_rpc(
            "rpc",
            NS_WIFI_SYSTEM,
            "naming",
            config={"input": {"mac": mac, "name": name}},
        )
        return await self._authenticated_request(payload)

    # ===== Firmware =====

    async def firmware_check(self) -> dict[str, Any]:
        """Check for firmware updates."""
        payload = self._build_rpc("rpc", NS_FIRMWARE, "on-line-check")
        result = await self._authenticated_request(payload)
        return self._extract_config(result)

    async def firmware_download(self) -> dict[str, Any]:
        """Start firmware download."""
        payload = self._build_rpc("rpc", NS_FIRMWARE, "on-line-download")
        return await self._authenticated_request(payload)

    async def firmware_download_status(self) -> dict[str, Any]:
        """Get firmware download status."""
        payload = self._build_rpc("rpc", NS_FIRMWARE, "on-line-download-status")
        result = await self._authenticated_request(payload)
        return self._extract_config(result)

    async def firmware_upgrade(self) -> dict[str, Any]:
        """Start firmware upgrade."""
        payload = self._build_rpc("rpc", NS_FIRMWARE, "on-line-upgrade")
        return await self._authenticated_request(payload)

    async def firmware_upgrade_status(self) -> dict[str, Any]:
        """Get firmware upgrade status."""
        payload = self._build_rpc("rpc", NS_FIRMWARE, "upgrade-status")
        result = await self._authenticated_request(payload)
        return self._extract_config(result)

    # ===== WAN =====

    async def get_wan_config(self) -> dict[str, Any]:
        """Get WAN configuration."""
        payload = self._build_rpc(
            "get-config",
            "urn:zyxel:cpe:system:zyxel-system-wan-profile",
            "wan",
        )
        result = await self._authenticated_request(payload)
        return self._extract_config(result)
