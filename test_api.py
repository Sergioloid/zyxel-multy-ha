#!/usr/bin/env python3
"""Test script for Zyxel Multy ZAPI - corrected protocol."""

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

msg_id = 0

def next_id():
    global msg_id
    msg_id += 1
    return msg_id

def build_rpc(operation, namespace, root, data=None):
    params = {}
    if operation == "get-config":
        params["source"] = "running"
        # IMPORTANT: include root key as empty dict, or router returns 5156
        params["filter"] = [{"xmlns": namespace, "root": root, "type": "subtree", root: {}}]
    else:
        params["xmlns"] = namespace
        params["root"] = root
        params[root] = data or {}
    return {"rpc": {"xmlns": XMLNS, "message-id": next_id(), "operation": operation, "params": params}}


async def main():
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    conn = aiohttp.TCPConnector(ssl=ssl_ctx)

    async with aiohttp.ClientSession(connector=conn) as session:
        # === AUTH ===
        print("=" * 60)
        print("1. AUTHENTICATE")
        auth_payload = build_rpc("rpc", NS_AUTH, "authentication",
            {"input": {"name": USERNAME, "password": PASSWORD}})

        async with session.post(BASE_URL, json=auth_payload,
            headers={"Content-Type": "application/json;charset=UTF-8"}) as resp:
            sysauth = None
            sc = resp.headers.get("Set-Cookie", "")
            if "sysauth=" in sc:
                sysauth = sc.split("sysauth=")[1].split(";")[0].strip()

            data = await resp.json(content_type=None)
            token = data["rpc-reply"]["data"][0]["authentication"]["output"]["token"]
            print(f"  TOKEN: {token}")
            print(f"  SYSAUTH: {sysauth}")

        # Common headers for all subsequent requests
        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "ZAPI_TOKEN": token,
        }
        cookies = {"sysauth": sysauth} if sysauth else {}

        async def do_request(name, payload):
            print(f"\n{'=' * 60}")
            print(f"{name}")
            try:
                async with session.post(BASE_URL, json=payload,
                    headers=headers, cookies=cookies,
                    timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    text = await resp.text()
                    try:
                        result = json.loads(text)
                        reply = result.get("rpc-reply", {})
                        if reply.get("result") == "ok":
                            d = reply.get("data", [{}])[0]
                            # Remove metadata keys for cleaner display
                            display = {k: v for k, v in d.items() if k not in ("xmlns", "root", "type", "timestamp")}
                            print(f"  OK: {json.dumps(display, indent=4, ensure_ascii=False)[:2000]}")
                        else:
                            err = reply.get("rpc-error", {}).get("error-message", {}).get("text", "?")
                            print(f"  ERROR {err}: {json.dumps(reply, indent=2)[:500]}")
                    except json.JSONDecodeError:
                        print(f"  NON-JSON: {text[:500]}")
            except Exception as e:
                print(f"  EXCEPTION: {e}")

        # === RPC ENDPOINTS ===
        await do_request("2. DEVICE STATISTICS (rpc)",
            build_rpc("rpc", NS_NETWORK_DEVICE, "get-device-statistics"))

        await do_request("3. CURRENT BANDWIDTH (rpc)",
            build_rpc("rpc", NS_SYSTEM, "current-band-width"))

        await do_request("4. CURRENT PORT STATE (rpc)",
            build_rpc("rpc", NS_SYSTEM, "current-port-state"))

        await do_request("5. WAN CONNECTED (rpc)",
            build_rpc("rpc", NS_EASY123, "is-wan-port-connected"))

        await do_request("6. INTERNET STATUS (rpc)",
            build_rpc("rpc", NS_EASY123, "access-internet-status"))

        await do_request("7. SPEED TEST RESULT (rpc)",
            build_rpc("rpc", NS_SPEED_TEST, "test-result"))

        await do_request("8. API VERSION (rpc)",
            build_rpc("rpc", NS_SYSTEM, "api-version"))

        await do_request("9. FIRMWARE CHECK (rpc)",
            build_rpc("rpc", NS_FIRMWARE, "on-line-check"))

        # === GET-CONFIG ENDPOINTS (require root key in filter) ===
        await do_request("10. BASIC SYSTEM INFO (get-config)",
            build_rpc("get-config", NS_SYSTEM, "basic-system-info"))

        await do_request("11. SYSTEM STATE (get-config)",
            build_rpc("get-config", NS_SYSTEM, "system-state"))

        await do_request("12. MESH DEVICES STATE (get-config)",
            build_rpc("get-config", NS_WIFI_SYSTEM, "system-devices-state"))

        await do_request("13. NETWORK DEVICES (get-config)",
            build_rpc("get-config", NS_NETWORK_DEVICE, "network-devices"))

    print("\n\nDONE!")

if __name__ == "__main__":
    asyncio.run(main())
