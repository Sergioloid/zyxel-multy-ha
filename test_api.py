#!/usr/bin/env python3
"""Test script to probe the real Zyxel Multy ZAPI and see response formats.

Run this from a machine on the same network as the router:
  python3 test_api.py

This matches the corrected ZAPI protocol format (reverse-engineered from the app).
"""

import asyncio
import json
import ssl
import time

import aiohttp

HOST = "192.168.212.1"
USERNAME = "admin"
PASSWORD = "YOUR_PASSWORD_HERE"
BASE_URL = f"https://{HOST}/zapi"
XMLNS = "urn:ietf:params:xml:ns:netconf:base:1.0"

NS_AUTH = "urn:zyxel:cpe:system:authentication"
NS_SYSTEM = "urn:zyxel:cpe:system:zyxel-system"
NS_EASY123 = "urn:zyxel:cpe:system:zyxel-system-easy123"
NS_NETWORK_DEVICE = "urn:zyxel:cpe:system:zyxel-system-network-device"
NS_SPEED_TEST = "urn:zyxel:cpe:system:zyxel-system-speed-test"
NS_WIFI_SYSTEM = "urn:zyxel:cpe:system:zyxel-system-wifi-system"
NS_FIRMWARE = "urn:zyxel:cpe:system:zyxel-system-firmware-upgrade"


def build_rpc(operation, namespace, root, data=None, source="running"):
    """Build a ZAPI RPC request envelope.

    For 'rpc' operations: data goes under params.<root>
    For 'get-config': filter array in params
    For 'edit-config': config array in params
    """
    params = {}
    if operation == "get-config":
        params["source"] = source
        params["filter"] = [{"xmlns": namespace, "root": root, "type": "subtree"}]
    elif operation == "edit-config":
        params["target"] = "running"
        params["error-option"] = "stop-on-error"
        config_element = {"xmlns": namespace, "root": root}
        if data:
            config_element[root] = data
        params["config"] = [config_element]
    else:  # rpc
        params["xmlns"] = namespace
        params["root"] = root
        params[root] = data or {}

    return {
        "rpc": {
            "xmlns": XMLNS,
            "message-id": int(time.time()),
            "operation": operation,
            "params": params,
        }
    }


def extract_data(response, root=None):
    """Extract data from rpc-reply response."""
    try:
        data_array = response["rpc-reply"]["data"]
        if not data_array:
            return {}
        element = data_array[0]
        if root and root in element:
            return element[root]
        # Try to find the data key
        metadata_keys = {"xmlns", "type", "timestamp", "root", "not-modified"}
        for key, value in element.items():
            if key not in metadata_keys and isinstance(value, dict):
                return value
        return element
    except (KeyError, IndexError, TypeError):
        return response


async def main():
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    connector = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=connector) as session:

        # === 1. AUTHENTICATE ===
        print("=" * 60)
        print("1. AUTHENTICATE")
        print("=" * 60)
        auth_payload = build_rpc(
            "rpc",
            NS_AUTH,
            "authentication",
            data={
                "user-authentication-order": ["local"],
                "user": [{"name": USERNAME, "password": PASSWORD}],
            },
        )
        print(f"REQUEST:\n{json.dumps(auth_payload, indent=2)}\n")

        async with session.post(
            BASE_URL,
            json=auth_payload,
            headers={"Content-Type": "application/json"},
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            print(f"STATUS: {resp.status}")
            auth_text = await resp.text()
            print(f"RESPONSE:\n{auth_text}\n")

            try:
                auth_result = json.loads(auth_text)
            except json.JSONDecodeError:
                print("FAILED TO PARSE JSON")
                return

        # Extract token from rpc-reply.data[0].authentication.output.token
        token = None
        for path_desc, extract_fn in [
            ("rpc-reply.data[0].authentication.output.token",
             lambda r: r["rpc-reply"]["data"][0]["authentication"]["output"]["token"]),
            ("rpc-reply.data[0].output.token",
             lambda r: r["rpc-reply"]["data"][0]["output"]["token"]),
        ]:
            try:
                token = extract_fn(auth_result)
                print(f"TOKEN FOUND at path: {path_desc}")
                print(f"TOKEN: {token[:30]}..." if len(str(token)) > 30 else f"TOKEN: {token}")
                break
            except (KeyError, IndexError, TypeError):
                continue

        if not token:
            print("COULD NOT FIND TOKEN!")
            print("Full response structure:")
            print(json.dumps(auth_result, indent=2))
            return

        cookies = {"token": token}

        # === 2. SYSTEM INFO ===
        print("\n" + "=" * 60)
        print("2. GET SYSTEM INFO")
        print("=" * 60)
        payload = build_rpc("rpc", NS_SYSTEM, "basic-system-info")
        async with session.post(
            BASE_URL, json=payload, cookies=cookies,
            headers={"Content-Type": "application/json"},
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            text = await resp.text()
            result = json.loads(text)
            data = extract_data(result, "basic-system-info")
            print(f"STATUS: {resp.status}")
            print(f"EXTRACTED DATA:\n{json.dumps(data, indent=2)}\n")

        # === 3. DEVICE STATISTICS ===
        print("\n" + "=" * 60)
        print("3. GET DEVICE STATISTICS")
        print("=" * 60)
        payload = build_rpc("rpc", NS_NETWORK_DEVICE, "get-device-statistics")
        async with session.post(
            BASE_URL, json=payload, cookies=cookies,
            headers={"Content-Type": "application/json"},
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            text = await resp.text()
            result = json.loads(text)
            data = extract_data(result, "get-device-statistics")
            print(f"STATUS: {resp.status}")
            print(f"EXTRACTED DATA:\n{json.dumps(data, indent=2)}\n")

        # === 4. NETWORK DEVICES ===
        print("\n" + "=" * 60)
        print("4. GET NETWORK DEVICES (get-config)")
        print("=" * 60)
        payload = build_rpc("get-config", NS_NETWORK_DEVICE, "network-devices")
        async with session.post(
            BASE_URL, json=payload, cookies=cookies,
            headers={"Content-Type": "application/json"},
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            text = await resp.text()
            result = json.loads(text)
            data = extract_data(result, "network-devices")
            if isinstance(data, dict):
                devices = data.get("device", [])
                print(f"STATUS: {resp.status}")
                print(f"Number of devices: {len(devices)}")
                for d in devices[:3]:
                    print(f"  Device: {json.dumps(d, indent=4)}")
                if len(devices) > 3:
                    print(f"  ... and {len(devices) - 3} more")
            else:
                print(f"Unexpected data format: {str(data)[:500]}")

        # === 5. MESH DEVICES STATE ===
        print("\n" + "=" * 60)
        print("5. GET MESH DEVICES STATE")
        print("=" * 60)
        payload = build_rpc("rpc", NS_WIFI_SYSTEM, "system-devices-state")
        async with session.post(
            BASE_URL, json=payload, cookies=cookies,
            headers={"Content-Type": "application/json"},
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            text = await resp.text()
            result = json.loads(text)
            data = extract_data(result, "system-devices-state")
            print(f"STATUS: {resp.status}")
            print(f"EXTRACTED DATA:\n{json.dumps(data, indent=2)[:2000]}\n")

        # === 6. CURRENT BANDWIDTH ===
        print("\n" + "=" * 60)
        print("6. GET CURRENT BANDWIDTH")
        print("=" * 60)
        payload = build_rpc("rpc", NS_SYSTEM, "current-band-width")
        async with session.post(
            BASE_URL, json=payload, cookies=cookies,
            headers={"Content-Type": "application/json"},
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            text = await resp.text()
            result = json.loads(text)
            data = extract_data(result, "current-band-width")
            print(f"STATUS: {resp.status}")
            print(f"EXTRACTED DATA:\n{json.dumps(data, indent=2)}\n")

        # === 7. WAN CONNECTED ===
        print("\n" + "=" * 60)
        print("7. IS WAN PORT CONNECTED")
        print("=" * 60)
        payload = build_rpc("rpc", NS_EASY123, "is-wan-port-connected")
        async with session.post(
            BASE_URL, json=payload, cookies=cookies,
            headers={"Content-Type": "application/json"},
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            text = await resp.text()
            result = json.loads(text)
            data = extract_data(result, "is-wan-port-connected")
            print(f"STATUS: {resp.status}")
            print(f"EXTRACTED DATA:\n{json.dumps(data, indent=2)}\n")

        # === 8. INTERNET STATUS ===
        print("\n" + "=" * 60)
        print("8. ACCESS INTERNET STATUS")
        print("=" * 60)
        payload = build_rpc("rpc", NS_EASY123, "access-internet-status")
        async with session.post(
            BASE_URL, json=payload, cookies=cookies,
            headers={"Content-Type": "application/json"},
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            text = await resp.text()
            result = json.loads(text)
            data = extract_data(result, "access-internet-status")
            print(f"STATUS: {resp.status}")
            print(f"EXTRACTED DATA:\n{json.dumps(data, indent=2)}\n")

        # === 9. SPEED TEST RESULT ===
        print("\n" + "=" * 60)
        print("9. GET SPEED TEST RESULT")
        print("=" * 60)
        payload = build_rpc("rpc", NS_SPEED_TEST, "test-result")
        async with session.post(
            BASE_URL, json=payload, cookies=cookies,
            headers={"Content-Type": "application/json"},
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            text = await resp.text()
            result = json.loads(text)
            data = extract_data(result, "test-result")
            print(f"STATUS: {resp.status}")
            print(f"EXTRACTED DATA:\n{json.dumps(data, indent=2)}\n")

        # === 10. FIRMWARE CHECK ===
        print("\n" + "=" * 60)
        print("10. FIRMWARE CHECK")
        print("=" * 60)
        payload = build_rpc("rpc", NS_FIRMWARE, "on-line-check")
        async with session.post(
            BASE_URL, json=payload, cookies=cookies,
            headers={"Content-Type": "application/json"},
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            text = await resp.text()
            result = json.loads(text)
            data = extract_data(result, "on-line-check")
            print(f"STATUS: {resp.status}")
            print(f"EXTRACTED DATA:\n{json.dumps(data, indent=2)}\n")

    print("\n\nDONE!")


if __name__ == "__main__":
    asyncio.run(main())
