# Zyxel Multy - Home Assistant Integration

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Sergioloid&repository=zyxel-multy-ha&category=integration)

Custom Home Assistant integration for **Zyxel Multy** mesh routers (Multy X, Multy Plus, Multy U, Multy Mini, Multy M1, Multy Max).

Reverse-engineered from the official Zyxel Multy Android app (ZAPI protocol).

## Supported Models

| Model | Name |
|-------|------|
| WSQ50 | Multy X |
| WSQ60 | Multy Plus |
| WSR30 | Multy U |
| WSQ20 | Multy Mini |
| WSM20 | Multy M1 |
| WSQ65 | Multy Max |

## Features

### Entities

#### Sensors
- Total connected clients
- Online clients
- WiFi clients / Online WiFi clients
- Guest clients / Online guest clients
- Download / Upload bandwidth (real-time)
- Speed test results (download / upload)
- Router model name
- Current firmware version
- Available firmware version
- Mesh node count

#### Binary Sensors
- WAN connected
- Internet connected
- Firmware update available (with version details)

#### Switches
- LED on/off for each mesh node (with brightness control)

#### Buttons
- Reboot router
- Reboot individual mesh nodes
- Start speed test
- Check firmware updates

#### Device Tracker
- Automatic tracking of all connected devices (presence detection)
- Shows: IP, hostname, MAC, connection type, OS, manufacturer, guest status

### Services

| Service | Description |
|---------|-------------|
| `zyxel_multy.reboot` | Reboot router or specific mesh node |
| `zyxel_multy.speed_test` | Start a speed test |
| `zyxel_multy.block_device` | Block internet for a device (by MAC) |
| `zyxel_multy.unblock_device` | Unblock a device |
| `zyxel_multy.set_wifi` | Change SSID and/or password |
| `zyxel_multy.switch_led` | Control mesh node LEDs |
| `zyxel_multy.add_port_forward` | Add port forwarding rule |
| `zyxel_multy.remove_port_forward` | Remove port forwarding rule |
| `zyxel_multy.parental_block` | Pause internet for a profile |
| `zyxel_multy.parental_unblock` | Resume internet for a profile |
| `zyxel_multy.parental_bonus` | Give extra time to a profile |
| `zyxel_multy.wake_on_lan` | Send WoL packet |
| `zyxel_multy.firmware_check` | Check for firmware updates |

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the 3 dots in the top right > **Custom repositories**
3. Add this repository URL with category **Integration**
4. Search for "Zyxel Multy" and install
5. Restart Home Assistant
6. Go to **Settings > Devices & Services > Add Integration > Zyxel Multy**

### Manual

1. Copy `custom_components/zyxel_multy` to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Go to **Settings > Devices & Services > Add Integration > Zyxel Multy**

## Configuration

Enter:
- **Router IP Address** (default: `192.168.212.1`)
- **Username** (default: `admin`)
- **Password**: Your router admin password

## How It Works

- Uses the **ZAPI** protocol (NETCONF-like JSON-RPC over HTTPS)
- Polls the router every **30 seconds** for updated data
- All communication is local (no cloud dependency)
- Accepts the router's self-signed TLS certificate

## API Documentation

Full API reference is available in [docs/API_REFERENCE.md](docs/API_REFERENCE.md).

## Automation Examples

### Reboot router every night at 4 AM
```yaml
automation:
  - alias: "Nightly Router Reboot"
    trigger:
      - platform: time
        at: "04:00:00"
    action:
      - service: zyxel_multy.reboot
```

### Block kids' devices after 10 PM
```yaml
automation:
  - alias: "Block Kids Internet"
    trigger:
      - platform: time
        at: "22:00:00"
    action:
      - service: zyxel_multy.parental_block
        data:
          profile_index: "1"
```

### Speed test every 6 hours
```yaml
automation:
  - alias: "Periodic Speed Test"
    trigger:
      - platform: time_pattern
        hours: "/6"
    action:
      - service: zyxel_multy.speed_test
```

### Presence detection notification
```yaml
automation:
  - alias: "Someone arrived home"
    trigger:
      - platform: state
        entity_id: device_tracker.iphone_mario
        to: "home"
    action:
      - service: notify.mobile_app
        data:
          message: "Mario is home!"
```

## License

MIT
