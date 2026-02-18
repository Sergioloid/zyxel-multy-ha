"""Zyxel Multy ZAPI client.

Protocol (reverse-engineered from web GUI + Android app):

Auth:
  POST /zapi  {"rpc": {..., "operation": "rpc", "params": {
    "root": "authentication", "xmlns": NS_AUTH,
    "authentication": {"input": {"name": "<user>", "password": "<pass>"}}}}}
  Response Set-Cookie: sysauth=<UUID>
  Response JSON: rpc-reply.data[0].authentication.output.token = <UUID>

Subsequent requests require BOTH:
  - Cookie: sysauth=<UUID>     (from Set-Cookie header)
  - Header: ZAPI_TOKEN: <UUID> (from JSON output.token)

RPC calls:
  params: {"xmlns": "<ns>", "root": "<root>", "<root>": {<data>}}

get-config calls:
  params: {"source": "running", "filter": [{"xmlns": "<ns>", "root": "<root>", "type": "subtree", "<root>": {}}]}
  NOTE: The root key as empty dict in filter is REQUIRED or the router returns 5156.

Response:
  {"rpc-reply": {"result": "ok", "data": [{"<root>": {<response>}, "xmlns": "...", "root": "..."}]}}
"""

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
        self._host = host
        self._username = username
        self._password = password
        self._session = session
        self._token: str | None = None
        self._sysauth: str | None = None
        self._own_session = session is None
        self._base_url = f"https://{host}{ZAPI_PATH}"
        self._msg_id = 0

    def _next_id(self) -> int:
        self._msg_id += 1
        return self._msg_id

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            self._session = aiohttp.ClientSession(connector=connector)
            self._own_session = True
        return self._session

    async def close(self) -> None:
        if self._own_session and self._session and not self._session.closed:
            await self._session.close()

    def _build_rpc(
        self,
        operation: str,
        namespace: str,
        root: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}

        if operation == "get-config":
            params["source"] = "running"
            params["filter"] = [
                {"xmlns": namespace, "root": root, "type": "subtree", root: {}}
            ]
        elif operation == "edit-config":
            params["target"] = "running"
            params["error-option"] = "stop-on-error"
            config_element: dict[str, Any] = {"xmlns": namespace, "root": root}
            if data:
                config_element[root] = data
            params["config"] = [config_element]
        else:  # rpc
            params["xmlns"] = namespace
            params["root"] = root
            params[root] = data if data is not None else {}

        return {
            "rpc": {
                "xmlns": ZAPI_XMLNS,
                "message-id": self._next_id(),
                "operation": operation,
                "params": params,
            }
        }

    async def _request(
        self, payload: dict[str, Any], is_auth: bool = False
    ) -> dict[str, Any]:
        session = await self._ensure_session()

        headers: dict[str, str] = {
            "Content-Type": "application/json;charset=UTF-8",
        }
        cookies: dict[str, str] = {}

        if not is_auth:
            if self._token:
                headers["ZAPI_TOKEN"] = self._token
            if self._sysauth:
                cookies["sysauth"] = self._sysauth

        _LOGGER.debug("ZAPI request: %s", payload)

        try:
            async with session.post(
                self._base_url,
                json=payload,
                headers=headers,
                cookies=cookies,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                # Extract sysauth from Set-Cookie on auth requests
                if is_auth:
                    sc = resp.headers.get("Set-Cookie", "")
                    if "sysauth=" in sc:
                        val = sc.split("sysauth=")[1].split(";")[0].strip()
                        if val:
                            self._sysauth = val
                            _LOGGER.debug("Got sysauth cookie: %s", val)

                # The router sometimes puts error info in HTTP headers which
                # makes aiohttp choke. Try to read text first.
                try:
                    response_data = await resp.json(content_type=None)
                except Exception:
                    text = await resp.text()
                    _LOGGER.debug("Non-JSON response: %s", text[:500])
                    raise ZapiError(f"Non-JSON response (HTTP {resp.status}): {text[:200]}")

                _LOGGER.debug("ZAPI response: %s", response_data)

                reply = response_data.get("rpc-reply", {})
                result = reply.get("result", "")

                if result and result != "ok":
                    rpc_error = reply.get("rpc-error", {})
                    error_msg_obj = rpc_error.get("error-message", {})
                    if isinstance(error_msg_obj, dict):
                        error_code = error_msg_obj.get("text", result)
                    else:
                        error_code = str(error_msg_obj)
                    error_tag = rpc_error.get("error-tag", "")

                    if error_code == "2002":
                        raise ZapiAuthError(
                            f"Access denied (2002) for operation"
                        )
                    raise ZapiError(
                        f"ZAPI error {error_code} (tag={error_tag})"
                    )

                return response_data

        except aiohttp.ClientResponseError as err:
            # Router puts errors in HTTP headers causing parse failures
            error_str = str(err)
            if "4143" in error_str or "parse_request" in error_str:
                raise ZapiError(f"Request format rejected by router: {error_str}")
            if "2002" in error_str:
                raise ZapiAuthError(f"Access denied: {error_str}")
            raise ZapiError(f"HTTP error: {err}") from err
        except aiohttp.ClientError as err:
            raise ZapiError(f"Connection error: {err}") from err

    async def authenticate(self) -> str:
        """Authenticate and get session token + sysauth cookie."""
        self._token = None
        self._sysauth = None

        payload = self._build_rpc(
            "rpc",
            NS_AUTH,
            "authentication",
            data={"input": {"name": self._username, "password": self._password}},
        )

        result = await self._request(payload, is_auth=True)

        # Extract token from rpc-reply.data[0].authentication.output.token
        try:
            token = result["rpc-reply"]["data"][0]["authentication"]["output"]["token"]
        except (KeyError, IndexError, TypeError):
            # Fallback: search for token in any output
            token = None
            try:
                for v in result["rpc-reply"]["data"][0].values():
                    if isinstance(v, dict) and "output" in v:
                        token = v["output"].get("token")
                        if token:
                            break
            except (KeyError, IndexError, TypeError):
                pass

        if not token:
            raise ZapiAuthError(f"No token in auth response: {result}")

        self._token = token
        _LOGGER.info("Authenticated with Zyxel Multy (token=%s...)", token[:8])
        return token

    async def _authenticated_request(
        self, payload: dict[str, Any]
    ) -> dict[str, Any]:
        if not self._token:
            await self.authenticate()
        try:
            return await self._request(payload)
        except ZapiAuthError:
            _LOGGER.debug("Token expired, re-authenticating")
            await self.authenticate()
            return await self._request(payload)

    def _extract_data(
        self, result: dict[str, Any], root: str | None = None
    ) -> Any:
        """Extract data from rpc-reply.data[0].<root>."""
        try:
            data_array = result["rpc-reply"]["data"]
            if not data_array:
                return {}
            element = data_array[0]
            if root and root in element:
                return element[root]
            metadata_keys = {"xmlns", "type", "timestamp", "root", "not-modified"}
            for key, value in element.items():
                if key not in metadata_keys and isinstance(value, dict):
                    return value
            return element
        except (KeyError, IndexError, TypeError):
            _LOGGER.debug("Could not extract data from: %s", result)
            return {}

    # ===== System =====

    async def get_system_info(self) -> dict[str, Any]:
        """Get basic system info via get-config."""
        payload = self._build_rpc("get-config", NS_SYSTEM, "basic-system-info")
        result = await self._authenticated_request(payload)
        return self._extract_data(result, "basic-system-info")

    async def get_system_state(self) -> dict[str, Any]:
        """Get system state (uptime, firmware, CPU/memory usage)."""
        payload = self._build_rpc("get-config", NS_SYSTEM, "system-state")
        result = await self._authenticated_request(payload)
        return self._extract_data(result, "system-state")

    async def get_api_version(self) -> dict[str, Any]:
        payload = self._build_rpc("rpc", NS_SYSTEM, "api-version")
        result = await self._authenticated_request(payload)
        return self._extract_data(result, "api-version")

    async def get_current_bandwidth(self) -> dict[str, Any]:
        payload = self._build_rpc("rpc", NS_SYSTEM, "current-band-width")
        result = await self._authenticated_request(payload)
        return self._extract_data(result, "current-band-width")

    async def get_port_state(self) -> dict[str, Any]:
        payload = self._build_rpc("rpc", NS_SYSTEM, "current-port-state")
        result = await self._authenticated_request(payload)
        return self._extract_data(result, "current-port-state")

    async def system_restart(self) -> dict[str, Any]:
        payload = self._build_rpc("rpc", NS_SYSTEM, "system-restart")
        return await self._authenticated_request(payload)

    async def system_shutdown(self) -> dict[str, Any]:
        payload = self._build_rpc("rpc", NS_SYSTEM, "system-shutdown")
        return await self._authenticated_request(payload)

    async def wake_on_lan(self, mac_address: str) -> dict[str, Any]:
        payload = self._build_rpc(
            "rpc", NS_SYSTEM, "system-wake-on-lan",
            data={"input": {"mac-address": mac_address}},
        )
        return await self._authenticated_request(payload)

    # ===== Easy123 (WAN/Internet/WiFi) =====

    async def is_wan_connected(self) -> dict[str, Any]:
        payload = self._build_rpc("rpc", NS_EASY123, "is-wan-port-connected")
        result = await self._authenticated_request(payload)
        return self._extract_data(result, "is-wan-port-connected")

    async def get_internet_status(self) -> dict[str, Any]:
        payload = self._build_rpc("rpc", NS_EASY123, "access-internet-status")
        result = await self._authenticated_request(payload)
        return self._extract_data(result, "access-internet-status")

    async def get_wifi_config(self, network: str = "main") -> dict[str, Any]:
        payload = self._build_rpc(
            "rpc", NS_EASY123, "get-wifi-configuration",
            data={"input": {"network": network}},
        )
        result = await self._authenticated_request(payload)
        return self._extract_data(result, "get-wifi-configuration")

    async def set_wifi(
        self,
        ssid: str | None = None,
        ssid_5g: str | None = None,
        password: str | None = None,
        network: str = "main",
    ) -> dict[str, Any]:
        input_data: dict[str, Any] = {"network": network}
        if ssid:
            input_data["ssid"] = ssid
        if ssid_5g:
            input_data["ssid-5g"] = ssid_5g
        if password:
            input_data["psk"] = {"key": password}
        payload = self._build_rpc(
            "rpc", NS_EASY123, "set-wifi", data={"input": input_data}
        )
        return await self._authenticated_request(payload)

    # ===== Speed Test =====

    async def start_speed_test(self) -> dict[str, Any]:
        payload = self._build_rpc(
            "rpc", NS_SPEED_TEST, "speed-test",
            data={"input": {"originator": 1, "device-mac": "",
                            "test-id": str(int(time.time())), "target": "Internet"}},
        )
        return await self._authenticated_request(payload)

    async def get_speed_test_result(self) -> dict[str, Any]:
        payload = self._build_rpc("rpc", NS_SPEED_TEST, "test-result")
        result = await self._authenticated_request(payload)
        return self._extract_data(result, "test-result")

    # ===== Network Devices =====

    async def get_device_statistics(self) -> dict[str, Any]:
        payload = self._build_rpc("rpc", NS_NETWORK_DEVICE, "get-device-statistics")
        result = await self._authenticated_request(payload)
        return self._extract_data(result, "get-device-statistics")

    async def get_network_devices(self) -> list[dict[str, Any]]:
        """Get all connected devices via get-config."""
        payload = self._build_rpc("get-config", NS_NETWORK_DEVICE, "network-devices")
        result = await self._authenticated_request(payload)
        data = self._extract_data(result, "network-devices")
        if isinstance(data, dict):
            return data.get("device", [])
        return []

    async def set_device_name(self, device_id: str, name: str) -> dict[str, Any]:
        payload = self._build_rpc(
            "rpc", NS_NETWORK_DEVICE, "set-device-name",
            data={"input": {"id": device_id, "name": name}},
        )
        return await self._authenticated_request(payload)

    # ===== Firewall / Block =====

    async def block_device(self, mac_address: str, lasting_time: int = 0) -> dict[str, Any]:
        payload = self._build_rpc(
            "rpc", NS_FIREWALL_V4, "block",
            data={"input": {"mac-address": mac_address, "lasting-time": lasting_time}},
        )
        return await self._authenticated_request(payload)

    async def unblock_device(self, index: str) -> dict[str, Any]:
        payload = self._build_rpc(
            "rpc", NS_FIREWALL_V4, "unblock",
            data={"input": {"index": index}},
        )
        return await self._authenticated_request(payload)

    # ===== NAT / Port Forwarding =====

    async def add_port_forward(
        self, service: str, protocol: str, external_port: int,
        internal_port: int, local_ip: str, external_port_end: int | None = None,
    ) -> dict[str, Any]:
        if external_port_end is None:
            external_port_end = external_port
        payload = self._build_rpc(
            "rpc", NS_NAT_GENERAL, "add-rule",
            data={"input": {
                "service": service, "service-index": 0, "protocol": protocol,
                "external-port": external_port, "external-port-end": external_port_end,
                "internal-port": internal_port, "local-ip": local_ip,
            }},
        )
        return await self._authenticated_request(payload)

    async def remove_port_forward(self, index: int) -> dict[str, Any]:
        payload = self._build_rpc(
            "rpc", NS_NAT_GENERAL, "remove-rule",
            data={"input": {"index": index}},
        )
        return await self._authenticated_request(payload)

    # ===== Parental Control =====

    async def parental_block(self, profile_index: str) -> dict[str, Any]:
        payload = self._build_rpc(
            "rpc", NS_PARENTAL, "block",
            data={"input": {"index": profile_index}},
        )
        return await self._authenticated_request(payload)

    async def parental_unblock(self, profile_index: str) -> dict[str, Any]:
        payload = self._build_rpc(
            "rpc", NS_PARENTAL, "unblock",
            data={"input": {"index": profile_index}},
        )
        return await self._authenticated_request(payload)

    async def parental_bonus(self, profile_index: str, minutes: int) -> dict[str, Any]:
        payload = self._build_rpc(
            "rpc", NS_PARENTAL, "bonus",
            data={"input": {"index": profile_index, "minute": minutes}},
        )
        return await self._authenticated_request(payload)

    # ===== Mesh / WiFi System =====

    async def get_mesh_devices_state(self) -> dict[str, Any]:
        """Get mesh devices state via get-config."""
        payload = self._build_rpc("get-config", NS_WIFI_SYSTEM, "system-devices-state")
        result = await self._authenticated_request(payload)
        return self._extract_data(result, "system-devices-state")

    async def restart_mesh_node(self, mac: str) -> dict[str, Any]:
        payload = self._build_rpc(
            "rpc", NS_WIFI_SYSTEM, "restart",
            data={"input": {"mac": mac}},
        )
        return await self._authenticated_request(payload)

    async def switch_led(self, mac: str, state: str, brightness: int = 100) -> dict[str, Any]:
        payload = self._build_rpc(
            "rpc", NS_WIFI_SYSTEM, "switch-led",
            data={"input": {"mac": mac, "led-switch": state, "led-brightness-level": brightness}},
        )
        return await self._authenticated_request(payload)

    async def rename_mesh_node(self, mac: str, name: str) -> dict[str, Any]:
        payload = self._build_rpc(
            "rpc", NS_WIFI_SYSTEM, "naming",
            data={"input": {"mac": mac, "name": name}},
        )
        return await self._authenticated_request(payload)

    # ===== Firmware =====

    async def firmware_check(self) -> dict[str, Any]:
        payload = self._build_rpc("rpc", NS_FIRMWARE, "on-line-check")
        result = await self._authenticated_request(payload)
        return self._extract_data(result, "on-line-check")
