"""Constants for the Zyxel Multy integration."""

DOMAIN = "zyxel_multy"

# Polling interval in seconds
DEFAULT_SCAN_INTERVAL = 30

# ZAPI Protocol
ZAPI_PATH = "/zapi"
ZAPI_XMLNS = "urn:ietf:params:xml:ns:netconf:base:1.0"

# Namespaces
NS_SYSTEM = "urn:zyxel:cpe:system:zyxel-system"
NS_AUTH = "urn:zyxel:cpe:system:authentication"
NS_EASY123 = "urn:zyxel:cpe:system:zyxel-system-easy123"
NS_SPEED_TEST = "urn:zyxel:cpe:system:zyxel-system-speed-test"
NS_FIRMWARE = "urn:zyxel:cpe:system:zyxel-system-firmware-upgrade"
NS_NETWORK_DEVICE = "urn:zyxel:cpe:system:zyxel-system-network-device"
NS_WIFI_SYSTEM = "urn:zyxel:cpe:system:zyxel-system-wifi-system"
NS_CLOUD = "urn:zyxel:cpe:system:zyxel-system-cloud"
NS_CAPABILITY = "urn:zyxel:cpe:system:zyxel-system-capability"
NS_LOG = "urn:zyxel:cpe:system:zyxel-system-log"
NS_WIFI_LOG = "urn:zyxel:cpe:system:zyxel-wifi-system-log"
NS_WAN_PROFILE = "urn:zyxel:cpe:system:zyxel-system-wan-profile"
NS_LAN_PROFILE = "urn:zyxel:cpe:system:zyxel-system-lan-profile"
NS_OPMODE = "urn:zyxel:cpe:system:zyxel-system-opmode"
NS_MACFILTER = "urn:zyxel:cpe:system:zyxel-system-macfilter"
NS_WIRELESS_SCHEDULING = "urn:zyxel:cpe:system:zyxel-system-wireless-scheduling"
NS_BLE = "urn:zyxel:cpe:system:zyxel-system-bluetooth-low-energy"
NS_ENTITLEMENT = "urn:zyxel:cpe:system:zyxel-system-entitlement"

NS_SSID = "urn:zyxel:cpe:interface:zyxel-interface-ssid"
NS_RADIO = "urn:zyxel:cpe:interface:zyxel-interface-radio"
NS_APPLY = "urn:zyxel:cpe:interface:zyxel-interface-apply"
NS_HOMENETWORK = "urn:zyxel:cpe:interface:zyxel-interface-homenetwork"

NS_PARENTAL = "urn:zyxel:cpe:applications:zyxel-applications-parental-control"
NS_NAT = "urn:zyxel:cpe:applications:zyxel-applications-nat"
NS_NAT_GENERAL = "urn:zyxel:cpe:applications:zyxel-applications-nat-general"
NS_NAT_PORT_TRIGGER = "urn:zyxel:cpe:applications:zyxel-applications-nat-port-trigger"
NS_FIREWALL_V4 = "urn:zyxel:cpe:applications:zyxel-applications-ipv4-firewall"
NS_FIREWALL_V6 = "urn:zyxel:cpe:applications:zyxel-applications-ipv6-firewall"
NS_DHCP_SERVER = "urn:zyxel:cpe:applications:zyxel-applications-dhcp-server"
NS_NOTIFICATION = "urn:zyxel:cpe:applications:zyxel-applications-notification"
NS_CYBER_SECURITY = "urn:zyxel:cpe:applications:zyxel-applications-cyber-security"
NS_OPENVPN = "urn:zyxel:cpe:applications:zyxel-applications-openvpn"
NS_PPTP = "urn:zyxel:cpe:applications:zyxel-applications-pptp-server"
NS_UPNP = "urn:zyxel:cpe:applications:zyxel-applications-upnp"
NS_DDNS = "urn:zyxel:cpe:applications:zyxel-applications-ddns"
NS_BANDWIDTH = "urn:zyxel:cpe:applications:zyxel-applications-bandwidth"
NS_ROUTING = "urn:zyxel:cpe:applications:zyxel-applications-routing"
NS_ECHO_SERVER = "urn:zyxel:cpe:applications:zyxel-applications-echo-server"
