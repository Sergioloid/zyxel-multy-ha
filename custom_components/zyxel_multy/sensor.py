"""Sensor platform for Zyxel Multy."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfDataRate, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ZyxelMultyCoordinator
from .entity import ZyxelMultyEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Zyxel Multy sensors."""
    coordinator: ZyxelMultyCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = [
        ZyxelTotalClientsSensor(coordinator),
        ZyxelOnlineClientsSensor(coordinator),
        ZyxelWifiClientsSensor(coordinator),
        ZyxelOnlineWifiClientsSensor(coordinator),
        ZyxelGuestClientsSensor(coordinator),
        ZyxelOnlineGuestClientsSensor(coordinator),
        ZyxelDownloadBandwidthSensor(coordinator),
        ZyxelUploadBandwidthSensor(coordinator),
        ZyxelSpeedTestDownloadSensor(coordinator),
        ZyxelSpeedTestUploadSensor(coordinator),
        ZyxelModelNameSensor(coordinator),
        ZyxelFirmwareVersionSensor(coordinator),
        ZyxelFirmwareAvailableSensor(coordinator),
        ZyxelMeshNodeCountSensor(coordinator),
        ZyxelCpuUsageSensor(coordinator),
        ZyxelMemoryUsageSensor(coordinator),
        ZyxelUptimeSensor(coordinator),
    ]

    async_add_entities(entities)


class ZyxelTotalClientsSensor(ZyxelMultyEntity, SensorEntity):
    """Total connected clients."""

    _attr_name = "Total Clients"
    _attr_icon = "mdi:devices"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: ZyxelMultyCoordinator) -> None:
        super().__init__(coordinator, "total_clients")

    @property
    def native_value(self) -> int | None:
        stats = self.coordinator.data.get("device_stats", {})
        if isinstance(stats, dict):
            output = stats.get("output", stats)
            if isinstance(output, dict):
                return output.get("total-client")
        return None


class ZyxelOnlineClientsSensor(ZyxelMultyEntity, SensorEntity):
    """Online connected clients."""

    _attr_name = "Online Clients"
    _attr_icon = "mdi:account-multiple"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: ZyxelMultyCoordinator) -> None:
        super().__init__(coordinator, "online_clients")

    @property
    def native_value(self) -> int | None:
        stats = self.coordinator.data.get("device_stats", {})
        if isinstance(stats, dict):
            output = stats.get("output", stats)
            if isinstance(output, dict):
                return output.get("total-online-client")
        return None


class ZyxelWifiClientsSensor(ZyxelMultyEntity, SensorEntity):
    """WiFi clients."""

    _attr_name = "WiFi Clients"
    _attr_icon = "mdi:wifi"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: ZyxelMultyCoordinator) -> None:
        super().__init__(coordinator, "wifi_clients")

    @property
    def native_value(self) -> int | None:
        stats = self.coordinator.data.get("device_stats", {})
        if isinstance(stats, dict):
            output = stats.get("output", stats)
            if isinstance(output, dict):
                return output.get("total-WiFi-client")
        return None


class ZyxelOnlineWifiClientsSensor(ZyxelMultyEntity, SensorEntity):
    """Online WiFi clients."""

    _attr_name = "Online WiFi Clients"
    _attr_icon = "mdi:wifi-check"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: ZyxelMultyCoordinator) -> None:
        super().__init__(coordinator, "online_wifi_clients")

    @property
    def native_value(self) -> int | None:
        stats = self.coordinator.data.get("device_stats", {})
        if isinstance(stats, dict):
            output = stats.get("output", stats)
            if isinstance(output, dict):
                return output.get("total-online-WiFi-client")
        return None


class ZyxelGuestClientsSensor(ZyxelMultyEntity, SensorEntity):
    """Guest network clients."""

    _attr_name = "Guest Clients"
    _attr_icon = "mdi:account-group"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: ZyxelMultyCoordinator) -> None:
        super().__init__(coordinator, "guest_clients")

    @property
    def native_value(self) -> int | None:
        stats = self.coordinator.data.get("device_stats", {})
        if isinstance(stats, dict):
            output = stats.get("output", stats)
            if isinstance(output, dict):
                return output.get("total-guest-client")
        return None


class ZyxelOnlineGuestClientsSensor(ZyxelMultyEntity, SensorEntity):
    """Online guest network clients."""

    _attr_name = "Online Guest Clients"
    _attr_icon = "mdi:account-group-outline"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: ZyxelMultyCoordinator) -> None:
        super().__init__(coordinator, "online_guest_clients")

    @property
    def native_value(self) -> int | None:
        stats = self.coordinator.data.get("device_stats", {})
        if isinstance(stats, dict):
            output = stats.get("output", stats)
            if isinstance(output, dict):
                return output.get("total-guest-online-client")
        return None


class ZyxelDownloadBandwidthSensor(ZyxelMultyEntity, SensorEntity):
    """Current download bandwidth."""

    _attr_name = "Download Bandwidth"
    _attr_device_class = SensorDeviceClass.DATA_RATE
    _attr_native_unit_of_measurement = UnitOfDataRate.BITS_PER_SECOND
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:download"

    def __init__(self, coordinator: ZyxelMultyCoordinator) -> None:
        super().__init__(coordinator, "download_bandwidth")

    @property
    def native_value(self) -> int | None:
        bw = self.coordinator.data.get("bandwidth", {})
        if isinstance(bw, dict):
            output = bw.get("output", bw)
            if isinstance(output, dict):
                return output.get("download")
        return None


class ZyxelUploadBandwidthSensor(ZyxelMultyEntity, SensorEntity):
    """Current upload bandwidth."""

    _attr_name = "Upload Bandwidth"
    _attr_device_class = SensorDeviceClass.DATA_RATE
    _attr_native_unit_of_measurement = UnitOfDataRate.BITS_PER_SECOND
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:upload"

    def __init__(self, coordinator: ZyxelMultyCoordinator) -> None:
        super().__init__(coordinator, "upload_bandwidth")

    @property
    def native_value(self) -> int | None:
        bw = self.coordinator.data.get("bandwidth", {})
        if isinstance(bw, dict):
            output = bw.get("output", bw)
            if isinstance(output, dict):
                return output.get("upload")
        return None


class ZyxelSpeedTestDownloadSensor(ZyxelMultyEntity, SensorEntity):
    """Last speed test download result."""

    _attr_name = "Speed Test Download"
    _attr_device_class = SensorDeviceClass.DATA_RATE
    _attr_native_unit_of_measurement = UnitOfDataRate.BITS_PER_SECOND
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:speedometer"

    def __init__(self, coordinator: ZyxelMultyCoordinator) -> None:
        super().__init__(coordinator, "speed_test_download")

    @property
    def native_value(self) -> int | None:
        st = self.coordinator.data.get("speed_test", {})
        if isinstance(st, dict):
            output = st.get("output", st)
            if isinstance(output, dict):
                return output.get("download")
        return None


class ZyxelSpeedTestUploadSensor(ZyxelMultyEntity, SensorEntity):
    """Last speed test upload result."""

    _attr_name = "Speed Test Upload"
    _attr_device_class = SensorDeviceClass.DATA_RATE
    _attr_native_unit_of_measurement = UnitOfDataRate.BITS_PER_SECOND
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:speedometer"

    def __init__(self, coordinator: ZyxelMultyCoordinator) -> None:
        super().__init__(coordinator, "speed_test_upload")

    @property
    def native_value(self) -> int | None:
        st = self.coordinator.data.get("speed_test", {})
        if isinstance(st, dict):
            output = st.get("output", st)
            if isinstance(output, dict):
                return output.get("upload")
        return None


class ZyxelModelNameSensor(ZyxelMultyEntity, SensorEntity):
    """Router model name."""

    _attr_name = "Model"
    _attr_icon = "mdi:router-wireless"

    def __init__(self, coordinator: ZyxelMultyCoordinator) -> None:
        super().__init__(coordinator, "model_name")

    @property
    def native_value(self) -> str | None:
        info = self.coordinator.data.get("system_info", {})
        if isinstance(info, dict):
            return info.get("model-name")
        return None


class ZyxelFirmwareVersionSensor(ZyxelMultyEntity, SensorEntity):
    """Current firmware version."""

    _attr_name = "Firmware Version"
    _attr_icon = "mdi:chip"

    def __init__(self, coordinator: ZyxelMultyCoordinator) -> None:
        super().__init__(coordinator, "firmware_version")

    @property
    def native_value(self) -> str | None:
        state = self.coordinator.data.get("system_state", {})
        if isinstance(state, dict):
            platform = state.get("platform", {})
            if isinstance(platform, dict):
                return platform.get("software-version")
        return None


class ZyxelFirmwareAvailableSensor(ZyxelMultyEntity, SensorEntity):
    """Available firmware version."""

    _attr_name = "Available Firmware"
    _attr_icon = "mdi:update"

    def __init__(self, coordinator: ZyxelMultyCoordinator) -> None:
        super().__init__(coordinator, "firmware_available")

    @property
    def native_value(self) -> str | None:
        fw = self.coordinator.data.get("firmware", {})
        if isinstance(fw, dict):
            output = fw.get("output", fw)
            if isinstance(output, dict):
                return output.get("version")
        return None


class ZyxelMeshNodeCountSensor(ZyxelMultyEntity, SensorEntity):
    """Number of mesh nodes."""

    _attr_name = "Mesh Nodes"
    _attr_icon = "mdi:access-point-network"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: ZyxelMultyCoordinator) -> None:
        super().__init__(coordinator, "mesh_node_count")

    @property
    def native_value(self) -> int | None:
        mesh = self.coordinator.data.get("mesh_state", {})
        if isinstance(mesh, dict):
            devices = mesh.get("device", [])
            if isinstance(devices, list):
                return len(devices)
        return None


class ZyxelCpuUsageSensor(ZyxelMultyEntity, SensorEntity):
    """CPU usage percentage."""

    _attr_name = "CPU Usage"
    _attr_icon = "mdi:cpu-64-bit"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: ZyxelMultyCoordinator) -> None:
        super().__init__(coordinator, "cpu_usage")

    @property
    def native_value(self) -> int | None:
        state = self.coordinator.data.get("system_state", {})
        if isinstance(state, dict):
            usage = state.get("usage", {})
            if isinstance(usage, dict):
                return usage.get("cpu")
        return None


class ZyxelMemoryUsageSensor(ZyxelMultyEntity, SensorEntity):
    """Memory usage percentage."""

    _attr_name = "Memory Usage"
    _attr_icon = "mdi:memory"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: ZyxelMultyCoordinator) -> None:
        super().__init__(coordinator, "memory_usage")

    @property
    def native_value(self) -> int | None:
        state = self.coordinator.data.get("system_state", {})
        if isinstance(state, dict):
            usage = state.get("usage", {})
            if isinstance(usage, dict):
                return usage.get("memory")
        return None


class ZyxelUptimeSensor(ZyxelMultyEntity, SensorEntity):
    """Router uptime in seconds."""

    _attr_name = "Uptime"
    _attr_icon = "mdi:clock-outline"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, coordinator: ZyxelMultyCoordinator) -> None:
        super().__init__(coordinator, "uptime")

    @property
    def native_value(self) -> int | None:
        state = self.coordinator.data.get("system_state", {})
        if isinstance(state, dict):
            clock = state.get("clock", {})
            if isinstance(clock, dict):
                return clock.get("uptime")
        return None
