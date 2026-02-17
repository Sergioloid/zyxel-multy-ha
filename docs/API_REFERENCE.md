# Zyxel Multy ZAPI - Complete API Reference

> Reverse-engineered from Zyxel Multy App v2.6.4 (APK decompilation)

## Table of Contents

1. [Protocol Overview](#protocol-overview)
2. [Authentication](#authentication)
3. [System Management](#system-management)
4. [WiFi Configuration](#wifi-configuration)
5. [Speed Test](#speed-test)
6. [Connected Devices](#connected-devices)
7. [Parental Control](#parental-control)
8. [Firewall](#firewall)
9. [NAT / Port Forwarding](#nat--port-forwarding)
10. [WAN / LAN Network](#wan--lan-network)
11. [Mesh WiFi System](#mesh-wifi-system)
12. [Firmware Management](#firmware-management)
13. [VPN](#vpn)
14. [Notifications](#notifications)
15. [Cyber Security (AiShield)](#cyber-security-aishield)
16. [Cloud Services](#cloud-services)
17. [Backup & Restore](#backup--restore)
18. [Miscellaneous Services](#miscellaneous-services)
19. [Enum Reference](#enum-reference)

---

## Protocol Overview

### Endpoint
All API calls are **HTTPS POST** requests to a single endpoint:

```
POST https://<ROUTER_IP>/zapi
Content-Type: application/json
```

The router uses a **self-signed TLS certificate** - your HTTP client must accept it.

### Request Envelope (NETCONF-like JSON-RPC)

Every request follows this envelope structure:

```json
{
  "rpc": {
    "xmlns": "urn:ietf:params:xml:ns:netconf:base:1.0",
    "message-id": <unix_timestamp_seconds>,
    "operation": "<operation_type>",
    "edit-config-operation": "replace",
    "params": {
      "source": "running",
      "xmlns": "<namespace>",
      "root": "<action_root>",
      "config": { <payload> }
    }
  }
}
```

### Operation Types

| Operation | Use | Description |
|-----------|-----|-------------|
| `get-config` | Read | Fetches current configuration |
| `edit-config` | Write | Modifies configuration |
| `rpc` | Action | Executes a remote procedure call |
| `copy-config` | Copy | Copies configuration between sources |

### Edit Config Operations
- `replace` - Replace existing config
- `merge` - Merge with existing
- `delete` - Delete config entry
- `create` - Create new entry

### Config Sources
- `running` - Current running configuration
- `candidate` - Candidate configuration
- `startup` - Startup configuration

### Filter Types
- `subtree` - Subtree filtering for get-config

### Response Format
Responses follow the same JSON-RPC envelope structure with results in the `params` section.

### Supported Router Models
- **WSQ50** - Multy X
- **WSQ50C** - Multy X (variant)
- **WSQ60** - Multy Plus
- **WSR30** - Multy U
- **WSQ20** - Multy Mini
- **WSM20** - Multy M1
- **WSQ65** - Multy Max

---

## Authentication

### Local Authentication (Username/Password)

Login with local credentials to obtain a session token.

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:authentication`
- **Root**: `authentication`

**Request payload:**
```json
{
  "user-authentication-order": ["local"],
  "user": [
    {
      "name": "admin",
      "password": "your_password"
    }
  ]
}
```

**Response:**
```json
{
  "output": {
    "token": "SESSION_TOKEN_STRING"
  }
}
```

The token must be included in subsequent requests (typically as a cookie or in the request envelope).

### SSO Authentication (Zyxel Cloud)

Login via Zyxel MyCloud SSO OAuth flow.

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:authentication`
- **Root**: `authentication-by-SSO`

**SSO OAuth URL:**
```
https://mycloud-sso.zyxel.com/oauth/authorize
  ?client_id=378d32da0c5d28be004a0c76cd33654413a282a2544d4ef2ea49c73c3335e338
  &redirect_uri=multyauth://callback.rb
  &response_type=code
  &theme=blue
  &locale=<locale>
```

**Request payload (after OAuth redirect):**
```json
{
  "input": {
    "redirect-uri": "multyauth://callback.rb",
    "grant-code": "<oauth_code_from_redirect>"
  }
}
```

**Response:**
```json
{
  "output": {
    "token": "SESSION_TOKEN_STRING"
  }
}
```

### SSO Logout URL
```
https://mycloud-sso.zyxel.com/oauth/logout
  ?client_id=378d32da0c5d28be004a0c76cd33654413a282a2544d4ef2ea49c73c3335e338
  &logout_redirect_uri=multyoauth://logout.rb
  &theme=blue
```

### Get Client ID for SSO

- **Root**: `get-client-id-for-SSO`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-cloud`

**Response:**
```json
{
  "output": {
    "client-id": "string",
    "error-code": 0
  }
}
```

---

## System Management

### Get Basic System Info

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system`
- **Root**: `basic-system-info`
- **Parameters**: None

**Response:**
```json
{
  "model-name": "WSQ50",
  "features": { ... }
}
```

### Get System Configuration

- **Operation**: `get-config`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system`
- **Root**: `system`

**Response fields:**
| Field | Type | Description |
|-------|------|-------------|
| `led` | Object | LED configuration |
| `clock` | Object | Clock settings |
| `ntp` | Object | NTP server settings |
| `general` | Object | General system settings |
| `set-gui-password` | Object | GUI password settings |
| `authentication` | Object | Auth configuration |
| `contact` | String | Contact information |
| `radius` | Object | RADIUS settings |
| `remote-management` | Object | Remote management config |
| `dns-resolver` | Object | DNS resolver settings |
| `set-root-password` | Object | Root password settings |
| `daylight-savings` | Object | DST settings |
| `users` | Object | User accounts |

### Get System State

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system`
- **Root**: `system-state`

**Response fields:**
| Field | Type | Description |
|-------|------|-------------|
| `printer` | Object | Printer info |
| `clock` | Object | Current system clock |
| `platform` | Object | Platform info (model, serial, etc.) |
| `usage` | Object | CPU/memory usage |

### System Restart (Reboot)

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system`
- **Root**: `system-restart`
- **Parameters**: None (empty payload)

```json
{}
```

### System Shutdown

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system`
- **Root**: `system-shutdown`
- **Parameters**: None

### System Reset to Default (Factory Reset)

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system`
- **Root**: `system-reset-to-default`
- **Parameters**: None

### Set Current Date/Time

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system`
- **Root**: `set-current-datetime`

**Request:**
```json
{
  "input": {
    "current-datetime": "2024-01-15T10:30:00Z"
  }
}
```

### Get Current Bandwidth

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system`
- **Root**: `current-band-width`

**Response:**
```json
{
  "output": {
    "download": 125000000,
    "upload": 25000000
  }
}
```

### Wake on LAN

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system`
- **Root**: `system-wake-on-lan`

**Request:**
```json
{
  "input": {
    "mac-address": "AA:BB:CC:DD:EE:FF"
  }
}
```

### Get API Version

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system`
- **Root**: `api-version`

**Response:**
```json
{
  "output": {
    "version": "1.0",
    "minimum-app-version": "2.0.0"
  }
}
```

### Get System Capability

- **Operation**: `get-config`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-capability`
- **Root**: `capability`

---

## WiFi Configuration

### Set WiFi (SSID & Password)

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-easy123`
- **Root**: `set-wifi`

**Request:**
```json
{
  "input": {
    "ssid": "MyNetwork",
    "ssid-5g": "MyNetwork_5G",
    "psk": { "key": "wifi_password_here" },
    "network": "main"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `ssid` | String | 2.4GHz SSID name |
| `ssid-5g` | String | 5GHz SSID name |
| `psk` | Object | Pre-shared key (password) |
| `network` | Enum | Network type: `main` or `guest` |

### Get WiFi Configuration

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-easy123`
- **Root**: `get-wifi-configuration`

**Request:**
```json
{
  "input": {
    "network": "main"
  }
}
```

**Response:**
```json
{
  "output": {
    "ssid": "MyNetwork",
    "ssid-5g": "MyNetwork_5G",
    "psk": { "key": "wifi_password" }
  }
}
```

### Is WiFi Button On

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-easy123`
- **Root**: `is-wifi-button-on`

**Response:**
```json
{
  "output": { }
}
```

### Apply WiFi Interface Setting

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:interface:zyxel-interface-apply`
- **Root**: `apply-wifi-interface-setting`

**Request:**
```json
{
  "input": {
    "config": "string_config_data"
  }
}
```

### Get Channel List

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:interface:zyxel-interface-radio`
- **Root**: `get-channel-list`

**Request:**
```json
{
  "input": {
    "band": "2.4G",
    "bandwidth": "20MHz"
  }
}
```

**Response:**
```json
{
  "output": {
    "channel-list": "1,2,3,4,5,6,7,8,9,10,11,12,13"
  }
}
```

| Input Field | Type | Values |
|-------------|------|--------|
| `band` | EnumBand | `2.4G`, `5G` |
| `bandwidth` | EnumBandwidth | `20MHz`, `40MHz`, `80MHz`, `160MHz` |

### WiFi Schedule

- **Operation**: `get-config` / `edit-config`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-wireless-scheduling`
- **Root**: `wifi-schedule`

**Config (array of schedule elements):**
Each schedule element contains its own scheduling rules.

### Set WiFi Schedule Rule

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-wireless-scheduling`
- **Root**: `set-rule`

**Request:**
```json
{
  "input": {
    "band": "2.4G",
    "name": "rule_name"
  }
}
```

### Get Remaining Time

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-wireless-scheduling`
- **Root**: `get-remaining-time`

**Response:**
```json
{
  "output": {
    "remaining-time-list": [ ... ]
  }
}
```

---

## Speed Test

### Start Speed Test

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-speed-test`
- **Root**: `speed-test`

**Request:**
```json
{
  "input": {
    "originator": 1,
    "device-mac": "AA:BB:CC:DD:EE:FF",
    "test-id": "unique_test_id",
    "target": "Internet"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `originator` | Integer | Originator ID (1 = app) |
| `device-mac` | String | MAC of device to test from |
| `test-id` | String | Unique identifier for the test |
| `target` | EnumTarget | `Internet`, `Intranet` |

### Get Speed Test Result

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-speed-test`
- **Root**: `test-result`

**Response:**
```json
{
  "output": {
    "download": 95500000,
    "upload": 47200000,
    "test-id": "unique_test_id"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `download` | Integer | Download speed in bps |
| `upload` | Integer | Upload speed in bps |
| `test-id` | String | Test identifier |

### Get Speed Test History

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-speed-test`
- **Root**: `get-history`

**Request:**
```json
{
  "input": {
    "device-mac": "AA:BB:CC:DD:EE:FF",
    "number": 10
  }
}
```

### Clean All Speed Test History

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-speed-test`
- **Root**: `clean-all-history`
- **Parameters**: None

### Clean Single History Entry

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-speed-test`
- **Root**: `clean-history`

**Request:**
```json
{
  "input": {
    "test-id": "test_id_to_remove"
  }
}
```

---

## Connected Devices

### Get Network Devices List

- **Operation**: `get-config`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-network-device`
- **Root**: `network-devices`

**Response (array of device elements):**
```json
{
  "device": [
    {
      "id": "device_unique_id",
      "device-name": "iPhone di Mario",
      "host-name": "Marios-iPhone",
      "ipv4-address": "192.168.212.100",
      "ipv6-address": "fe80::1",
      "al-mac": "AA:BB:CC:DD:EE:FF",
      "alive-status": "online",
      "connection-type": "WiFi",
      "device-type": "mobile",
      "guest": false,
      "host-type": 1,
      "os-type": "iOS",
      "manufacturer": "Apple",
      "manufacturer-cyber-security": "Apple Inc.",
      "device-category-cyber-security-detected": "smartphone",
      "device-category-cyber-security-user-defined": "",
      "device-type-cyber-security-detected": "iPhone",
      "join-time": 1705312800,
      "last-active-cyber-security": 1705316400,
      "lease-time": 86400,
      "network-type": 1,
      "tag": "",
      "extra-info": "",
      "neighbor": "",
      "wifi-status": { ... }
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | String | Unique device identifier |
| `device-name` | String | User-assigned name |
| `host-name` | String | DHCP hostname |
| `ipv4-address` | String | IPv4 address |
| `ipv6-address` | String | IPv6 address |
| `al-mac` | String | MAC address |
| `alive-status` | String | `online` / `offline` |
| `connection-type` | Enum | `WiFi`, `Ethernet` |
| `device-type` | Enum | Device type |
| `guest` | Boolean | On guest network |
| `host-type` | Integer | Host type ID |
| `os-type` | String | Detected OS |
| `manufacturer` | String | Device manufacturer |
| `join-time` | Integer | Unix timestamp of first connection |
| `last-active-cyber-security` | Integer | Last activity timestamp |
| `lease-time` | Integer | DHCP lease time (seconds) |
| `network-type` | Integer | Network type ID |
| `wifi-status` | Object | WiFi-specific status (RSSI, band, etc.) |

### Get Device Statistics

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-network-device`
- **Root**: `get-device-statistics`

**Response:**
```json
{
  "output": {
    "total-client": 15,
    "total-online-client": 12,
    "total-WiFi-client": 10,
    "total-online-WiFi-client": 8,
    "total-guest-client": 3,
    "total-guest-online-client": 2
  }
}
```

### Get Device Information

- **Operation**: `get-config`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-network-device`
- **Root**: `device-information`

**Response:**
```json
{
  "device-information": [
    {
      "id": "device_id",
      "device-function": { ... }
    }
  ]
}
```

### Get Device Status

- **Operation**: `get-config`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-network-device`
- **Root**: `device-status`

**Response:**
```json
{
  "device-status": [
    {
      "id": "device_id",
      "connecting-type": { ... }
    }
  ]
}
```

### Set Device Name

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-network-device`
- **Root**: `set-device-name`

**Request:**
```json
{
  "input": {
    "id": "device_id",
    "name": "Living Room TV"
  }
}
```

### Set Host Name

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-network-device`
- **Root**: `set-host-name`

**Request:**
```json
{
  "input": {
    "id": "device_id",
    "name": "new-hostname"
  }
}
```

### Set Host Type

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-network-device`
- **Root**: `set-host-type`

**Request:**
```json
{
  "input": {
    "id": "device_id",
    "host-type": 1
  }
}
```

### Set Device Category

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-network-device`
- **Root**: `set-device-category`

**Request:**
```json
{
  "input": {
    "id": "device_id",
    "category": "smartphone"
  }
}
```

### Remove Device Customized Data

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-network-device`
- **Root**: `remove-device-customized-data`

**Request:**
```json
{
  "input": { ... }
}
```

---

## Parental Control

### Get Parental Control Config

- **Operation**: `get-config`
- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-parental-control`
- **Root**: `top`

Returns full parental control configuration with all profiles.

### Block Profile (Pause Internet)

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-parental-control`
- **Root**: `block`

### Unblock Profile (Resume Internet)

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-parental-control`
- **Root**: `unblock`

### Block Single Device in Profile

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-parental-control`
- **Root**: `profile-device-block`

### Unblock Single Device in Profile

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-parental-control`
- **Root**: `profile-device-unblock`

**Request:**
```json
{
  "input": {
    "index": "profile_index",
    "mac": "AA:BB:CC:DD:EE:FF"
  }
}
```

### Add Device to Profile

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-parental-control`
- **Root**: `add-device`

**Request:**
```json
{
  "input": {
    "devices": [ ... ]
  }
}
```

### Remove Device from Profile

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-parental-control`
- **Root**: `remove-device`

**Request:**
```json
{
  "input": {
    "index": "profile_index",
    "mac": "AA:BB:CC:DD:EE:FF"
  }
}
```

### Delete Profile

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-parental-control`
- **Root**: `delete-profile`

**Request:**
```json
{
  "input": {
    "index": "profile_index"
  }
}
```

### Modify Profile

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-parental-control`
- **Root**: `modify-profile-stuff`

**Request:**
```json
{
  "input": {
    "index": "profile_index",
    "profile-name": "Kids",
    "profile-avatar-id": 3
  }
}
```

### Give Bonus Time

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-parental-control`
- **Root**: `bonus`

**Request:**
```json
{
  "input": {
    "index": "profile_index",
    "minute": 30
  }
}
```

### Cancel Profile Immediate Action

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-parental-control`
- **Root**: `cancel-profile-immediate-action`

### Cancel Profile Device Immediate Action

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-parental-control`
- **Root**: `cancel-profile-device-immediate-action`

### Set Policy Extension Time

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-cyber-security`
- **Root**: `set-policy-extension-time`

---

## Firewall

### Get Firewall Config (IPv4)

- **Operation**: `get-config`
- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-ipv4-firewall`
- **Root**: `firewall`

**Response:**
```json
{
  "target": "LAN_TO_WAN",
  "enable-firewall-rule": true,
  "enable-simple-security": true,
  "filter-rule": [
    {
      "rule-index": 1,
      "service-name": "HTTP",
      "protocol": "TCP",
      "source-ip-address": "192.168.212.0",
      "source-port-start": 0,
      "source-port-end": 65535,
      "dest-ip-address": "",
      "dest-port-start": 80,
      "dest-port-end": 80,
      "mac-address": ""
    }
  ]
}
```

### Get Firewall Config (IPv6)

- **Operation**: `get-config`
- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-ipv6-firewall`
- **Root**: `firewall`

### Block Device (Internet Block by MAC)

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-ipv4-firewall`
- **Root**: `block`

**Request:**
```json
{
  "input": {
    "mac-address": "AA:BB:CC:DD:EE:FF",
    "lasting-time": 3600
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `mac-address` | String | Device MAC to block |
| `lasting-time` | Integer | Duration in seconds (0 = permanent) |

### Unblock Device

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-ipv4-firewall`
- **Root**: `unblock`

**Request:**
```json
{
  "input": {
    "index": "rule_index_to_remove"
  }
}
```

### Cancel Immediate Action

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-ipv4-firewall`
- **Root**: `cancel-immediate-action`

### MAC Filter Profile

- **Operation**: `get-config` / `edit-config`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-macfilter`
- **Root**: `macfilter-profile`

---

## NAT / Port Forwarding

### Get NAT Config

- **Operation**: `get-config`
- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-nat`
- **Root**: `nat`

**Response:**
```json
{
  "nat-interface-setting": [
    {
      "index": 1,
      "alias": "WAN",
      "interface": "wan0"
    }
  ],
  "nat-port-mapping": [
    {
      "index": 1,
      "alias": "Minecraft Server",
      "protocol": "TCP",
      "external-port": 25565,
      "external-port-end-range": 25565,
      "internal-port": 25565,
      "internal-client": "192.168.212.50",
      "remote-host": "",
      "interface": "wan0",
      "all-interfaces": false,
      "lease-duration": 0
    }
  ]
}
```

### Add Port Forwarding Rule

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-nat-general`
- **Root**: `add-rule`

**Request:**
```json
{
  "input": {
    "service": "Custom Service",
    "service-index": 0,
    "protocol": "TCP",
    "external-port": 8080,
    "external-port-end": 8080,
    "internal-port": 80,
    "local-ip": "192.168.212.50",
    "support-service": { ... }
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `service` | String | Service name/description |
| `service-index` | Integer | Service index |
| `protocol` | Enum | `TCP`, `UDP`, `TCP/UDP` |
| `external-port` | Integer | External port start |
| `external-port-end` | Integer | External port end (for ranges) |
| `internal-port` | Integer | Internal (destination) port |
| `local-ip` | String | Internal IP address |

### Remove Port Forwarding Rule

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-nat-general`
- **Root**: `remove-rule`

**Request:**
```json
{
  "input": {
    "index": 1
  }
}
```

### Get System Ports

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-nat-general`
- **Root**: `get-system-port`

### Get Web Port Black List

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-nat-general`
- **Root**: `get-web-port-black-list`

---

## WAN / LAN Network

### Get WAN Config

- **Operation**: `get-config`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-wan-profile`
- **Root**: `wan`

**Response:**
```json
{
  "wan-settings": [
    {
      "name": "WAN1",
      "wan-encapsulation": "IPoE",
      "ipv4-ipv6": "IPv4",
      "base-interface": "wan0",
      "multicast-setup": "IGMP",
      "auto-ip-change-enable": true,
      "ip-address": { ... },
      "ipv4-dns-server": { ... },
      "ipv6-dns-server": { ... },
      "ipv6-address": { ... },
      "ipv6-tunneling": { ... },
      "wan-ip-assignment": { ... },
      "wan-mac": { ... },
      "ppp-setting": { ... },
      "pptp-config": { ... },
      "pptp-setting": { ... },
      "support-encapsulation": { ... }
    }
  ]
}
```

### Get LAN Config

- **Operation**: `get-config`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-lan-profile`
- **Root**: `lan`

**Response:**
```json
{
  "network": [
    {
      "name": "LAN1",
      "base-interface": "lan0",
      "opmode": { ... }
    }
  ]
}
```

### Is WAN Port Connected

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-easy123`
- **Root**: `is-wan-port-connected`

### Detect WAN Protocol

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-easy123`
- **Root**: `detect-wan-proto`

**Response:**
```json
{
  "output": {
    "proto": "IPoE"
  }
}
```

### Access Internet Status

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-easy123`
- **Root**: `access-internet-status`

### Is WAN IP Duplicated

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-easy123`
- **Root**: `is-wan-ip-duplicated`

### Validate DNS Server

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-wan-profile`
- **Root**: `validate-dns-server`

### DHCP Server Config

- **Operation**: `get-config` / `edit-config`
- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-dhcp-server`
- **Root**: `top`

### Add Static IP (DHCP Reservation)

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-dhcp-server`
- **Root**: `add-static-ip`

### IPv4 Routing / Forwarding

- **Operation**: `get-config` / `edit-config`
- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-routing`
- **Root**: `ipv4-forwarding`

### IPv6 Routing / Forwarding

- **Operation**: `get-config` / `edit-config`
- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-routing`
- **Root**: `ipv6-forwarding`

---

## Mesh WiFi System

### Get Mesh Devices State

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-wifi-system`
- **Root**: `system-devices-state`

**Response:**
```json
{
  "firmware-version": "V5.50(ACFK.0)C0",
  "system-firmware-version": { ... },
  "daisy-chain": true,
  "device": [ ... ]
}
```

### Restart Mesh Node

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-wifi-system`
- **Root**: `restart`

### Authorize Device (Add Satellite)

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-wifi-system`
- **Root**: `authorize-device`

**Request:**
```json
{
  "input": {
    "mac": "AA:BB:CC:DD:EE:FF",
    "model": "WSQ50",
    "hardware-version": "V1.0"
  }
}
```

### Unauthorize Device (Remove Satellite)

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-wifi-system`
- **Root**: `unauthorize-device`

**Request:**
```json
{
  "input": {
    "mac": "AA:BB:CC:DD:EE:FF"
  }
}
```

### Retrieve Device Information

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-wifi-system`
- **Root**: `retrive-device-information`

**Response:**
```json
{
  "output": {
    "mac": "AA:BB:CC:DD:EE:FF",
    "hardware-version": "V1.0"
  }
}
```

### Switch LED

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-wifi-system`
- **Root**: `switch-led`

**Request:**
```json
{
  "input": {
    "mac": "AA:BB:CC:DD:EE:FF",
    "led-switch": "On",
    "led-brightness-level": 100,
    "rgb": { ... }
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `mac` | String | Node MAC address |
| `led-switch` | Enum | `On`, `Off` |
| `led-brightness-level` | Integer | 0-100 brightness |
| `rgb` | Object | RGB color values |

### Rename Mesh Node

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-wifi-system`
- **Root**: `naming`

**Request:**
```json
{
  "input": {
    "mac": "AA:BB:CC:DD:EE:FF",
    "name": "Living Room"
  }
}
```

### Reset WiFi System

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-wifi-system`
- **Root**: `reset-wifi-system`

### Daisy Chain Config

- **Operation**: `get-config` / `edit-config`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-wifi-system`
- **Root**: `daisy-chain`

### Finish Setup

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-wifi-system`
- **Root**: `finish-setup`

### Setup State

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-wifi-system`
- **Root**: `setup-state`

### Support Extender

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-wifi-system`
- **Root**: `support-extender`

### Get Uninstall Device

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-wifi-system`
- **Root**: `get-uninstall-device`

### Clone Backhaul to Enrolee

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-easy123`
- **Root**: `clone-backhaul-to-enrolee`

---

## Firmware Management

### Check for Updates (Online)

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-firmware-upgrade`
- **Root**: `on-line-check`

**Response:**
```json
{
  "output": {
    "result": "new_firmware_available",
    "version": "V5.51(ACFK.0)C0",
    "firmware-name": "WSQ50_V5.51.bin",
    "firmware-size": "15728640",
    "release-date": "2024-01-15",
    "release-note": "Bug fixes and improvements",
    "note": ""
  }
}
```

### Check for Updates via RMS

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-firmware-upgrade`
- **Root**: `on-line-check-rms`

**Response:**
```json
{
  "output": {
    "result": "string",
    "firmware-list": [ ... ]
  }
}
```

### Download Firmware

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-firmware-upgrade`
- **Root**: `on-line-download`

### Get Download Status

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-firmware-upgrade`
- **Root**: `on-line-download-status`

**Response:**
```json
{
  "output": {
    "download-percent": 75,
    "result": "downloading"
  }
}
```

### Upgrade Firmware (Online)

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-firmware-upgrade`
- **Root**: `on-line-upgrade`
- **Parameters**: None

### Cancel Online Update

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-firmware-upgrade`
- **Root**: `on-line-cancel`

### Upload Firmware File

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-firmware-upgrade`
- **Root**: `upload`

### Upload Firmware by Chunk

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-firmware-upgrade`
- **Root**: `upload-firmware-by-chunk`

### Upgrade After Upload

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-firmware-upgrade`
- **Root**: `upgrade-after-upload`

### Get Upgrade Status

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-firmware-upgrade`
- **Root**: `upgrade-status`

---

## VPN

### OpenVPN Configuration

- **Operation**: `get-config` / `edit-config`
- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-openvpn`
- **Root**: `openvpn`

**Config fields:**
| Field | Type | Description |
|-------|------|-------------|
| `enable-ddns` | Boolean | Enable DDNS |
| `enable-dns` | Boolean | Enable DNS push |
| `protocol` | Enum | `UDP`, `TCP` |
| `port` | Integer | Server port |
| `vpn-device` | Enum | VPN device type |
| `server-subnet` | String | VPN subnet |
| `server-netmask` | String | VPN netmask |
| `pool-start-IP` | String | IP pool start |
| `pool-size` | Integer | IP pool size |
| `FQDN` | String | FQDN for external access |
| `ddns-hostname` | String | DDNS hostname |
| `allow-lan-to-lan` | Boolean | Allow LAN-to-LAN |
| `allow-lan-to-wan` | Boolean | Allow LAN-to-WAN |
| `auth-pam-enable` | Boolean | PAM auth enabled |
| `server-bridge-dhcp-enable` | Boolean | Bridge DHCP |
| `client-connect-list` | String | Connected clients |
| `openvpn-client-account` | Array | Client accounts |
| `openvpn-client-list` | Array | Client list |

### Export OpenVPN Config File

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-openvpn`
- **Root**: `export-openvpn-config-file`

### Change OpenVPN Server Key

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-openvpn`
- **Root**: `change-openvpn-server-key`

### PPTP Server

- **Operation**: `get-config` / `edit-config`
- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-pptp-server`
- **Root**: `pptp-server`

---

## Notifications

### Get/Set Notification Config

- **Operation**: `get-config` / `edit-config`
- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-notification`
- **Root**: `notification`

**Config fields:**
| Field | Type | Description |
|-------|------|-------------|
| `notification-setting` | Object | General settings |
| `apn-setting` | Object | APN push settings |
| `led-setting` | Object | LED notification settings |
| `email-setting` | Object | Email notification settings |
| `gcm-setting` | Object | GCM/FCM push settings |
| `sms-setting` | Object | SMS notification settings |

### Notification WebSocket Events

- **Operation**: `get-config`
- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-notification`
- **Root**: `notification-ws`

**Events available:**
| Field | Type | Description |
|-------|------|-------------|
| `notify-speed-test` | Object | Speed test completion event |
| `notify-new-client` | Object | New device connected event |
| `notify-new-firmware` | Object | New firmware available event |

---

## Cyber Security (AiShield)

### Get Cyber Security Config

- **Operation**: `get-config`
- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-cyber-security`
- **Root**: `cyber-security`

**Config fields:**
| Field | Type | Description |
|-------|------|-------------|
| `content-filter` | Object | Content filter config |
| `ips` | Object | IPS config |
| `ip-reputation` | Object | IP reputation settings |
| `anti-virus` | Object | Anti-virus settings |
| `application-control` | Object | App control |
| `device-identification` | Object | Device identification |
| `profile-policy` | Object | Security profiles |
| `notify-setting` | Object | Notification settings |
| `hash-key` | String | Security hash key |
| `path-to-working-directory` | String | Working dir path |
| `path-to-temp-directory` | String | Temp dir path |
| `enable-debug-feature-flags` | Integer | Debug flags |

### Get Cyber Security Status

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-cyber-security`
- **Root**: `cyber-security-status`

**Response fields:**
- `content-filter` - Content filter status
- `application-usage` - Application usage data

### Get Activation Info

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-cyber-security`
- **Root**: `cyber-security-activation-info`

### Update Signatures

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-cyber-security`
- **Root**: `update-signature`

---

## Cloud Services

### Cloud Service Info

- **Operation**: `get-config`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-cloud`
- **Root**: `cloud-service-related-info`

**Response:**
```json
{
  "cloud-id": "device_cloud_id",
  "network-id": "network_id"
}
```

### Pair/Unpair with Cloud

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-cloud`
- **Root**: `pair-unpair`

**Request:**
```json
{
  "input": {
    "token": "cloud_token",
    "cloud-id": "cloud_id"
  }
}
```

**Response:**
```json
{
  "output": {
    "state": "paired"
  }
}
```

### Device Get Access Token

- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-cloud`
- **Root**: `device-get-access-token`

### Device Refresh Access Token

- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-cloud`
- **Root**: `device-refresh-access-token`

### Get User Information

- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-cloud`
- **Root**: `device-get-user-information`

### Send Push Notification

- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-cloud`
- **Root**: `device-send-push-notification`

### Object Storage (Cloud Storage for router config)

| Root | Description |
|------|-------------|
| `object-storage-create-domain` | Create storage domain |
| `object-storage-get-domain` | Get domain info |
| `object-storage-update-domain` | Update domain |
| `object-storage-delete-domain` | Delete domain |
| `object-storage-list-domains` | List all domains |
| `object-storage-create-object` | Create object |
| `object-storage-get-object` | Get object |
| `object-storage-update-object` | Update object |
| `object-storage-delete-object` | Delete object |
| `object-storage-list-object` | List objects |

### Create Shortened URL

- **Root**: `create-zyxelto-shorten-url`

---

## Backup & Restore

### Backup Configuration

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system`
- **Root**: `system-config-backup`

### Restore Configuration

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system`
- **Root**: `system-config-restore`

### Upload Configuration

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system`
- **Root**: `system-config-upload`

### Get Factory Password

- **Operation**: `rpc`
- **Namespace**: `urn:zyxel:cpe:system:zyxel-system`
- **Root**: `system-factory-password`

---

## Miscellaneous Services

### UPnP

- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-upnp`
- **Root**: `top`

### DLNA

- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-dlna`
- **Root**: `top` (config), `rescan` (action)

### Samba

- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-samba`
- **Root**: `top`

### FTP Server

- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-ftp-server`
- **Root**: `top`

### USB Storage

- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-usb-storage`
- **Root**: `usb-storage`

### USB Port

- **Namespace**: `urn:zyxel:cpe:application:zyxel-applications-usb-port`
- **Root**: `usb-port`

### DDNS

- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-ddns`
- **Root**: `top`

### Captive Portal

- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-captive-portal`
- **Root**: `captive-portal`, `current-portal-info-for-user`, `request-internet-access`, `remove-portal-configuration`

### Server Control

- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-server-control`
- **Root**: `server-control`

### BLE (Bluetooth Low Energy)

- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-bluetooth-low-energy`
- **Root**: `ble-state` (read), `action-for-ble` (action)

### System Log

- **Namespace**: `urn:zyxel:cpe:system:zyxel-system-log`
- **Root**: `get-log` (read), `clear` (clear logs)

### WiFi System Log

- **Namespace**: `urn:zyxel:cpe:system:zyxel-wifi-system-log`
- **Root**: `get-log`, `clear`, `dump-file`

### Bandwidth Management

- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-bandwidth`
- **Root**: `top`

### Passthrough

- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-passthrough`
- **Root**: `top`

### Network Interfaces

- **Namespace**: `urn:ietf:params:xml:ns:yang:ietf-interfaces`
- **Root**: `interfaces`, `interfaces-state`

### Get MAC Address

- **Namespace**: `urn:zyxel:cpe:applications:zyxel-applications-echo-server`
- **Root**: `get-mac`

---

## Enum Reference

### EnumOperationType
`get-config`, `edit-config`, `rpc`, `copy-config`

### EnumEditConfigOperationType
`replace`, `merge`, `delete`, `create`

### EnumConfigSource
`running`, `candidate`, `startup`

### EnumAction
`Pair`, `Unpair`

### EnumActionMode
`Start`, `Stop`, `Restart`

### EnumActionType
`permit`, `deny`

### EnumConnectionType
`WiFi`, `Ethernet`

### EnumTarget (Speed Test)
`Internet`, `Intranet`

### EnumBand
`2.4G`, `5G`

### EnumProtocol (NAT)
`TCP`, `UDP`, `TCP/UDP`

### EnumResultOutput
`begin firmware upgrade`

### EnumAdminStatus
Various admin status values

### EnumFilterType
`subtree`

---

## Example: Full Reboot Request

```json
POST https://192.168.212.1/zapi
Content-Type: application/json

{
  "rpc": {
    "xmlns": "urn:ietf:params:xml:ns:netconf:base:1.0",
    "message-id": 1705312800,
    "operation": "rpc",
    "params": {
      "xmlns": "urn:zyxel:cpe:system:zyxel-system",
      "root": "system-restart"
    }
  }
}
```

## Example: Get Connected Devices

```json
POST https://192.168.212.1/zapi
Content-Type: application/json

{
  "rpc": {
    "xmlns": "urn:ietf:params:xml:ns:netconf:base:1.0",
    "message-id": 1705312800,
    "operation": "get-config",
    "params": {
      "source": "running",
      "filter": [
        {
          "xmlns": "urn:zyxel:cpe:system:zyxel-system-network-device",
          "root": "network-devices",
          "type": "subtree"
        }
      ]
    }
  }
}
```
