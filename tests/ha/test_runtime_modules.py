"""Coordinator, entity, diagnostics, and status-channel tests."""

from __future__ import annotations

import asyncio
import tempfile
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers.update_coordinator import UpdateFailed
from teltonika_rms import TeltonikaRmsRuntime
from teltonika_rms.binary_sensor import (
    RmsOnlineBinarySensor,
    RmsPortLinkBinarySensor,
)
from teltonika_rms.binary_sensor import (
    async_setup_entry as binary_setup,
)
from teltonika_rms.button import RmsRebootButton
from teltonika_rms.button import async_setup_entry as button_setup
from teltonika_rms.coordinator import (
    CoordinatorBundle,
    InventoryCoordinator,
    PortConfigCoordinator,
    PortScanCoordinator,
    StateCoordinator,
    async_refresh_all,
    validate_request_budget,
)
from teltonika_rms.device_tracker import RmsDeviceTracker
from teltonika_rms.device_tracker import async_setup_entry as tracker_setup
from teltonika_rms.diagnostics import TO_REDACT, async_get_config_entry_diagnostics
from teltonika_rms.endpoint_matrix import EndpointMatrix, EndpointSpec
from teltonika_rms.entity import TeltonikaRmsEntity
from teltonika_rms.exceptions import RmsApiError
from teltonika_rms.models import NormalizedDevice
from teltonika_rms.sensor import (
    RmsClientsCountSensor,
    RmsConnectionStateSensor,
    RmsConnectionTypeSensor,
    RmsFirmwareSensor,
    RmsLastSeenSensor,
    RmsModelSensor,
    RmsRouterUptimeSensor,
    RmsSerialSensor,
    RmsSignalStrengthSensor,
    RmsSimSlotSensor,
    RmsTemperatureSensor,
    RmsWanStateSensor,
)
from teltonika_rms.sensor import (
    async_setup_entry as sensor_setup,
)
from teltonika_rms.status_channel import (
    RmsStatusChannelManager,
    _coerce_payload,
    _is_terminal,
)
from teltonika_rms.switch import RmsPoeSwitch, RmsPortSwitch
from teltonika_rms.switch import async_setup_entry as switch_setup
from teltonika_rms.update import RmsFirmwareUpdateEntity
from teltonika_rms.update import async_setup_entry as update_setup

pytestmark = pytest.mark.ha


class FakeListenerCoordinator:
    def __init__(self, data: dict[str, Any] | None = None) -> None:
        self.data = data or {}
        self.listeners: list[Any] = []
        self.refresh_calls = 0
        self.update_interval = timedelta(seconds=120)

    def async_add_listener(self, callback: Any) -> Any:
        self.listeners.append(callback)
        return lambda: None

    async def async_request_refresh(self) -> None:
        self.refresh_calls += 1


def _normalized(
    *,
    device_id: str = "dev-1",
    online: bool | None = True,
    latitude: float | None = 47.0,
    longitude: float | None = 8.0,
) -> NormalizedDevice:
    return NormalizedDevice(
        device_id=device_id,
        name="Router",
        model="RUTX",
        firmware="1.0",
        latest_firmware="1.1",
        stable_firmware="1.0",
        firmware_update_available=True,
        serial="SERIAL",
        online=online,
        last_seen=datetime(2026, 3, 13, 12, 0, tzinfo=UTC),
        clients_count=4,
        router_uptime=3600,
        temperature=360,
        signal_strength=-81,
        wan_state="Mobile",
        connection_state="connected",
        connection_type="LTE",
        sim_slot=1,
        latitude=latitude,
        longitude=longitude,
        location_label="Zurich",
        raw={"id": device_id},
    )


def _bundle(normalized: NormalizedDevice | None) -> Any:
    inventory = FakeListenerCoordinator({"dev-1": {"id": "dev-1"}})
    state = FakeListenerCoordinator({"dev-1": {"state": {"online": True}}})
    port_scan = FakeListenerCoordinator(
        {
            "dev-1": [
                {"id": 0, "name": "port1", "type": "ETH", "devices": [{"ip": "192.168.1.5"}]},
                {"id": 1, "name": "port2", "type": "ETH", "devices": []},
            ]
        }
    )
    port_config = FakeListenerCoordinator(
        {
            "dev-1": [
                {
                    "id": "port1",
                    "poe_enable": "1",
                    "description": "tado",
                    "enabled": "1",
                    "autoneg": "on",
                    "isolated": "0",
                },
                {
                    "id": "port2",
                    "poe_enable": "0",
                    "enabled": "1",
                },
                {
                    "id": "sfp1",
                    "enabled": "1",
                },
            ]
        }
    )
    return SimpleNamespace(
        inventory=inventory,
        state=state,
        port_scan=port_scan,
        port_config=port_config,
        api=SimpleNamespace(
            async_reboot_device=lambda device_id: asyncio.sleep(0, result={"id": device_id})
        ),
        merged_device=lambda device_id: normalized if device_id == "dev-1" else None,
    )


def _matrix(aggregate: bool = True) -> EndpointMatrix:
    endpoints = {
        "devices_list": EndpointSpec("/v3/devices", tuple(), "safe"),
        "device_detail": EndpointSpec("/v3/devices/{id}", tuple(), "safe"),
        "device_state_single": EndpointSpec("/v3/devices/{id}/status", tuple(), "async-channel"),
        "device_location": EndpointSpec("/v3/devices/{id}/location", tuple(), "high-cost"),
    }
    if aggregate:
        endpoints["device_state_aggregate"] = EndpointSpec(
            "/v3/devices/status", tuple(), "async-channel"
        )
    return EndpointMatrix(source="test", endpoints=endpoints)


def test_base_entity_and_platform_entities_expose_values() -> None:
    bundle = _bundle(_normalized())

    base = TeltonikaRmsEntity(bundle, "dev-1")
    binary = RmsOnlineBinarySensor(bundle, "dev-1")
    port_link = RmsPortLinkBinarySensor(bundle, "dev-1", "port1")
    model = RmsModelSensor(bundle, "dev-1")
    firmware = RmsFirmwareSensor(bundle, "dev-1")
    serial = RmsSerialSensor(bundle, "dev-1")
    last_seen = RmsLastSeenSensor(bundle, "dev-1")
    clients = RmsClientsCountSensor(bundle, "dev-1")
    uptime = RmsRouterUptimeSensor(bundle, "dev-1")
    temperature = RmsTemperatureSensor(bundle, "dev-1")
    signal = RmsSignalStrengthSensor(bundle, "dev-1")
    wan_state = RmsWanStateSensor(bundle, "dev-1")
    connection_state = RmsConnectionStateSensor(bundle, "dev-1")
    connection_type = RmsConnectionTypeSensor(bundle, "dev-1")
    sim_slot = RmsSimSlotSensor(bundle, "dev-1")
    reboot = RmsRebootButton(bundle, "dev-1")
    poe = RmsPoeSwitch(bundle, "dev-1", "port1")
    port_sw = RmsPortSwitch(bundle, "dev-1", "port1")
    firmware_update = RmsFirmwareUpdateEntity(bundle, "dev-1")
    tracker = RmsDeviceTracker(bundle, "dev-1")

    assert base.available is True
    assert base.device_info is not None
    assert binary.is_on is True
    assert port_link.is_on is True
    assert model.native_value == "RUTX"
    assert firmware.native_value == "1.0"
    assert serial.native_value == "SERIAL"
    assert last_seen.native_value is not None
    assert clients.native_value == 4
    assert uptime.native_value == 0.04
    assert temperature.native_value == 360
    assert signal.native_value == -81
    assert wan_state.native_value == "Mobile"
    assert connection_state.native_value == "connected"
    assert connection_type.native_value == "LTE"
    assert sim_slot.native_value == 1
    assert poe.is_on is True
    assert poe.extra_state_attributes["description"] == "tado"
    assert port_sw.is_on is True
    assert port_sw.extra_state_attributes["description"] == "tado"
    assert firmware_update.installed_version == "1.0"
    assert firmware_update.latest_version == "1.1"
    assert reboot.available is True
    assert tracker.available is True
    assert tracker.latitude == 47.0
    assert tracker.longitude == 8.0
    assert tracker.extra_state_attributes["location_detail"] == "Zurich"
    assert tracker.location_accuracy == 100


def test_tracker_and_base_entity_handle_missing_location() -> None:
    bundle = _bundle(_normalized(latitude=None, longitude=None))

    tracker = RmsDeviceTracker(bundle, "dev-1")
    base = TeltonikaRmsEntity(bundle, "missing")
    clients = RmsClientsCountSensor(bundle, "dev-1")

    assert tracker.available is False
    assert tracker.extra_state_attributes == {"location_detail": "Zurich"}
    assert base.available is False
    assert base.device_info is None
    assert clients.available is True


def test_uptime_sensor_returns_none_without_runtime_value() -> None:
    normalized = _normalized()
    normalized.router_uptime = None
    bundle = _bundle(normalized)

    uptime = RmsRouterUptimeSensor(bundle, "dev-1")

    assert uptime.native_value is None
    assert uptime.available is False


def test_new_sensor_and_update_edge_paths() -> None:
    normalized = _normalized()
    normalized.latest_firmware = "2.0"
    normalized.stable_firmware = "1.9"
    bundle = _bundle(normalized)
    update_with_summary = RmsFirmwareUpdateEntity(bundle, "dev-1")
    assert update_with_summary.release_summary == "Latest: 2.0; Stable: 1.9"

    unknown_device = RmsModelSensor(bundle, "missing")
    assert unknown_device.native_value is None

    missing_update = RmsFirmwareUpdateEntity(bundle, "missing")
    assert missing_update.latest_version is None
    assert missing_update.release_summary is None

    no_summary_device = _normalized()
    no_summary_device.stable_firmware = no_summary_device.latest_firmware
    no_summary_bundle = _bundle(no_summary_device)
    no_summary = RmsFirmwareUpdateEntity(no_summary_bundle, "dev-1")
    assert no_summary.release_summary is None
    assert RmsFirmwareUpdateEntity.should_create(_normalized()) is True
    assert RmsFirmwareUpdateEntity.should_create(no_summary_device) is True
    no_firmware = _normalized()
    no_firmware.latest_firmware = None
    no_firmware.stable_firmware = None
    assert RmsFirmwareUpdateEntity.should_create(no_firmware) is False
    assert RmsFirmwareUpdateEntity.should_create(None) is False


def test_switch_device_generates_fallback_ports() -> None:
    bundle = _bundle(_normalized())
    bundle.inventory.data["dev-1"] = {"model": "TSW202", "id": "dev-1"}
    bundle.port_config.data = {}
    bundle.port_scan.data = {}

    added_binary: list[Any] = []
    added_switch: list[Any] = []
    entry = SimpleNamespace(
        runtime_data=TeltonikaRmsRuntime(bundle=bundle), async_on_unload=lambda cb: None
    )

    asyncio.run(binary_setup(None, entry, added_binary.extend))
    asyncio.run(switch_setup(None, entry, added_switch.extend))

    # Expect 1 online sensor + 8 ethernet ports + 2 sfp ports = 11 binary sensors
    assert len(added_binary) == 11
    # Expect 8 ethernet ports + 2 sfp ports = 10 switches
    assert len(added_switch) == 10

    # Pick an auto-generated port and ensure it is off (disconnected)
    sfp1 = next((s for s in added_binary if s._attr_unique_id == "dev-1_sfp1_link"), None)
    assert sfp1 is not None
    assert sfp1.available is True
    assert sfp1.is_on is False


def test_platform_setup_entry_adds_expected_entities() -> None:
    bundle = _bundle(_normalized())
    runtime = TeltonikaRmsRuntime(bundle=bundle)
    entry = SimpleNamespace(runtime_data=runtime, async_on_unload=lambda cb: None)
    added_binary: list[Any] = []
    added_sensor: list[Any] = []
    added_button: list[Any] = []
    added_switch: list[Any] = []
    added_update: list[Any] = []
    added_tracker: list[Any] = []

    asyncio.run(binary_setup(None, entry, added_binary.extend))
    asyncio.run(sensor_setup(None, entry, added_sensor.extend))
    asyncio.run(button_setup(None, entry, added_button.extend))
    asyncio.run(switch_setup(None, entry, added_switch.extend))
    asyncio.run(update_setup(None, entry, added_update.extend))
    asyncio.run(tracker_setup(None, entry, added_tracker.extend))

    assert len(added_binary) == 4
    assert len(added_sensor) == 12
    assert len(added_button) == 1
    assert len(added_switch) == 5
    assert len(added_update) == 1
    assert len(added_tracker) == 1


def test_sensor_and_update_setup_skip_duplicates_and_optional_entities() -> None:
    normalized = _normalized()
    normalized.latest_firmware = None
    normalized.stable_firmware = None
    bundle = _bundle(normalized)
    bundle.port_scan.data = {}
    runtime = TeltonikaRmsRuntime(bundle=bundle)
    unloaders: list[Any] = []
    entry = SimpleNamespace(
        runtime_data=runtime,
        async_on_unload=unloaders.append,
    )
    added_sensor: list[Any] = []
    added_switch: list[Any] = []
    added_update: list[Any] = []

    asyncio.run(sensor_setup(None, entry, added_sensor.extend))
    asyncio.run(switch_setup(None, entry, added_switch.extend))
    asyncio.run(update_setup(None, entry, added_update.extend))

    assert len(added_switch) == 5
    assert added_update == []

    for listener in (
        bundle.inventory.listeners
        + bundle.state.listeners
        + bundle.port_scan.listeners
        + bundle.port_config.listeners
    ):
        listener()

    assert added_update == []
    assert len(added_sensor) == len({entity.unique_id for entity in added_sensor})
    assert len(added_switch) == 5
    assert len(unloaders) == 8

    bundle_with_update = _bundle(_normalized())
    runtime_with_update = TeltonikaRmsRuntime(bundle=bundle_with_update)
    entry_with_update = SimpleNamespace(
        runtime_data=runtime_with_update,
        async_on_unload=lambda cb: None,
    )
    added_update_once: list[Any] = []
    asyncio.run(update_setup(None, entry_with_update, added_update_once.extend))
    assert len(added_update_once) == 1
    for listener in bundle_with_update.inventory.listeners:
        listener()
    assert len(added_update_once) == 1


def test_update_setup_can_add_entity_after_state_listener_refresh() -> None:
    normalized = _normalized()
    normalized.latest_firmware = None
    normalized.stable_firmware = None
    current = {"value": normalized}

    bundle = _bundle(normalized)
    runtime = TeltonikaRmsRuntime(bundle=bundle)
    entry = SimpleNamespace(
        runtime_data=runtime,
        async_on_unload=lambda cb: None,
    )
    added_update: list[Any] = []

    bundle.merged_device = lambda device_id: current["value"] if device_id == "dev-1" else None

    asyncio.run(update_setup(None, entry, added_update.extend))
    assert added_update == []

    current["value"] = _normalized()
    for listener in bundle.state.listeners:
        listener()

    assert len(added_update) == 1


def test_reboot_button_executes_action_and_refreshes_state() -> None:
    calls: list[str] = []
    bundle = _bundle(_normalized())

    async def _async_reboot_device(device_id: str) -> dict[str, str]:
        calls.append(device_id)
        return {"id": device_id}

    bundle.api = SimpleNamespace(async_reboot_device=_async_reboot_device)
    button = RmsRebootButton(bundle, "dev-1")

    asyncio.run(button.async_press())

    assert calls == ["dev-1"]
    assert bundle.state.refresh_calls == 1


def test_reboot_button_surfaces_scope_error() -> None:
    bundle = _bundle(_normalized())

    async def _async_reboot_device(device_id: str) -> None:
        raise ConfigEntryAuthFailed("denied")

    bundle.api = SimpleNamespace(async_reboot_device=_async_reboot_device)
    button = RmsRebootButton(bundle, "dev-1")

    with pytest.raises(HomeAssistantError, match="device_actions:write"):
        asyncio.run(button.async_press())


def test_port_switch_updates_port_configuration_and_surfaces_scope_error() -> None:
    calls: list[tuple[str, str, bool]] = []
    bundle = _bundle(_normalized())

    async def _async_set_device_port_enabled(device_id: str, port_id: str, enabled: bool) -> None:
        calls.append((device_id, port_id, enabled))

    bundle.api = SimpleNamespace(async_set_device_port_enabled=_async_set_device_port_enabled)
    switch = RmsPortSwitch(bundle, "dev-1", "port1")

    asyncio.run(switch.async_turn_off())
    asyncio.run(switch.async_turn_on())

    assert calls == [("dev-1", "port1", False), ("dev-1", "port1", True)]
    assert bundle.port_config.refresh_calls == 2

    async def _raise_auth(device_id: str, port_id: str, enabled: bool) -> None:
        raise ConfigEntryAuthFailed("denied")

    bundle.api = SimpleNamespace(async_set_device_port_enabled=_raise_auth)
    with pytest.raises(HomeAssistantError, match="device_configurations:write"):
        asyncio.run(switch.async_turn_on())


def test_poe_switch_updates_port_configuration_and_surfaces_scope_error() -> None:
    calls: list[tuple[str, str, bool]] = []
    bundle = _bundle(_normalized())

    async def _async_set_device_port_poe(device_id: str, port_id: str, enabled: bool) -> None:
        calls.append((device_id, port_id, enabled))

    bundle.api = SimpleNamespace(async_set_device_port_poe=_async_set_device_port_poe)
    switch = RmsPoeSwitch(bundle, "dev-1", "port1")

    asyncio.run(switch.async_turn_off())
    asyncio.run(switch.async_turn_on())

    assert calls == [("dev-1", "port1", False), ("dev-1", "port1", True)]
    assert bundle.port_config.refresh_calls == 2

    async def _raise_auth(device_id: str, port_id: str, enabled: bool) -> None:
        raise ConfigEntryAuthFailed("denied")

    bundle.api = SimpleNamespace(async_set_device_port_poe=_raise_auth)
    with pytest.raises(HomeAssistantError, match="device_configurations:write"):
        asyncio.run(switch.async_turn_on())


def test_port_switch_uses_port_scan_state_if_config_missing() -> None:
    bundle = _bundle(_normalized())
    bundle.inventory.data["dev-1"] = {"model": "TSW202", "id": "dev-1"}
    bundle.port_config.data = {}
    bundle.port_scan.data = {
        "dev-1": [{"name": "port1", "state": "UP"}, {"name": "port2", "state": "DOWN"}]
    }

    switch_up = RmsPortSwitch(bundle, "dev-1", "port1")
    switch_down = RmsPortSwitch(bundle, "dev-1", "port2")
    switch_missing = RmsPortSwitch(bundle, "dev-1", "port3")

    assert switch_up.available is True
    assert switch_up.is_on is None
    assert switch_up._port == {"id": "port1", "state": "UP"}

    assert switch_down.available is True
    assert switch_down.is_on is None
    assert switch_down._port == {"id": "port2", "state": "DOWN"}

    assert switch_missing.available is True
    assert switch_missing.is_on is False
    assert switch_missing._port is None


def test_port_switch_handles_missing_port() -> None:
    bundle = _bundle(_normalized())
    missing = RmsPortSwitch(bundle, "dev-1", "missing-port")

    assert missing.available is False
    assert missing.is_on is False
    assert missing.extra_state_attributes["port_id"] == "missing-port"


def test_poe_switch_handles_missing_port_and_setup_skips_invalid_ports() -> None:
    bundle = _bundle(_normalized())
    missing = RmsPoeSwitch(bundle, "dev-1", "missing-port")

    assert missing.available is False
    assert missing.is_on is False
    assert missing.extra_state_attributes["port_id"] == "missing-port"

    bundle.port_config.data = {
        "dev-1": [
            {"poe_enable": "1"},
            {"enabled": "1"},
        ]
    }
    runtime = TeltonikaRmsRuntime(bundle=bundle)
    entry = SimpleNamespace(runtime_data=runtime, async_on_unload=lambda cb: None)
    added_switch: list[Any] = []

    asyncio.run(switch_setup(None, entry, added_switch.extend))

    assert added_switch == []


def test_coordinator_bundle_and_budget_validation() -> None:
    inventory = FakeListenerCoordinator({"dev-1": {"id": "dev-1", "name": "Router"}})
    state = FakeListenerCoordinator(
        {"dev-1": {"state": {"online": True}, "location": {"latitude": 1, "longitude": 2}}}
    )
    bundle = CoordinatorBundle(
        inventory=inventory,  # type: ignore[arg-type]
        state=state,  # type: ignore[arg-type]
        port_scan=FakeListenerCoordinator(),  # type: ignore[arg-type]
        port_config=FakeListenerCoordinator(),  # type: ignore[arg-type]
        status_channels=SimpleNamespace(),
        api=SimpleNamespace(),
    )

    merged = bundle.merged_device("dev-1")

    assert merged is not None
    assert merged.online is True
    assert (
        validate_request_budget(
            inventory_interval=900,
            state_interval=300,
            estimated_devices=1,
            aggregate_state_supported=True,
        )
        is True
    )
    assert bundle.merged_device("missing") is None


def test_coordinator_constructors_cover_default_option_parsing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _fake_super_init(
        self: Any, hass: Any, logger: Any, *, name: str, update_interval: timedelta
    ) -> None:
        self.hass = hass
        self.logger = logger
        self.name = name
        self.update_interval = update_interval

    monkeypatch.setattr(
        "homeassistant.helpers.update_coordinator.DataUpdateCoordinator.__init__",
        _fake_super_init,
    )

    hass = SimpleNamespace()
    api = SimpleNamespace(
        endpoint_matrix=_matrix(), estimate_max_calls_per_cycle=lambda interval: 2
    )
    inventory = InventoryCoordinator(
        hass,  # type: ignore[arg-type]
        api,  # type: ignore[arg-type]
        {"tags": " alpha,beta ", "device_status": " online ", "inventory_interval": 30},
    )
    state = StateCoordinator(
        hass,  # type: ignore[arg-type]
        api,  # type: ignore[arg-type]
        inventory,
        {"enable_location": False, "estimated_devices": 5, "state_interval": 30},
    )
    port_scan = PortScanCoordinator(
        hass,  # type: ignore[arg-type]
        api,  # type: ignore[arg-type]
        inventory,
    )
    port_config = PortConfigCoordinator(
        hass,  # type: ignore[arg-type]
        api,  # type: ignore[arg-type]
        inventory,
    )

    assert inventory._tags == ["alpha", "beta"]
    assert inventory._device_status == "online"
    assert int(inventory.update_interval.total_seconds()) == 60
    assert state._enable_location is False
    assert state._estimated_devices == 5
    assert int(state.update_interval.total_seconds()) == 60
    assert int(port_scan.update_interval.total_seconds()) == 21600
    assert int(port_config.update_interval.total_seconds()) == 21600


def test_inventory_and_state_coordinator_update_methods(monkeypatch: pytest.MonkeyPatch) -> None:
    inventory = object.__new__(InventoryCoordinator)
    inventory._api = SimpleNamespace(
        async_list_devices=lambda **kwargs: asyncio.sleep(
            0, result=[{"id": "dev-1", "name": "Router"}]
        )
    )
    inventory._tags = ["alpha"]
    inventory._device_status = None

    updated = asyncio.run(inventory._async_update_data())
    assert updated == {"dev-1": {"id": "dev-1", "name": "Router"}}

    failing_inventory = object.__new__(InventoryCoordinator)
    failing_inventory._api = SimpleNamespace(
        async_list_devices=lambda **kwargs: asyncio.sleep(0, result=None)
    )
    failing_inventory._tags = []
    failing_inventory._device_status = None

    async def _raise_list(**kwargs: Any) -> Any:
        raise RmsApiError("bad inventory")

    failing_inventory._api.async_list_devices = _raise_list
    with pytest.raises(UpdateFailed):
        asyncio.run(failing_inventory._async_update_data())

    inventory_skip = object.__new__(InventoryCoordinator)
    inventory_skip._api = SimpleNamespace(
        async_list_devices=lambda **kwargs: asyncio.sleep(
            0, result=[{"id": "dev-1"}, {"name": "missing"}]
        )
    )
    inventory_skip._tags = []
    inventory_skip._device_status = None
    assert asyncio.run(inventory_skip._async_update_data()) == {"dev-1": {"id": "dev-1"}}

    state = object.__new__(StateCoordinator)
    state._api = SimpleNamespace(
        endpoint_matrix=_matrix(aggregate=False),
        async_get_states_for_devices=lambda device_ids, max_per_cycle: asyncio.sleep(
            0, result={"dev-1": {"online": True}}
        ),
        async_get_device_location=lambda device_id: asyncio.sleep(
            0, result={"latitude": 1.0, "longitude": 2.0}
        ),
        async_get_device_wireless=lambda device_id: asyncio.sleep(0, result=[{"clients_count": 5}]),
        estimate_max_calls_per_cycle=lambda interval: 3,
    )
    state._inventory = SimpleNamespace(
        data={"dev-1": {"id": "dev-1"}}, update_interval=timedelta(seconds=900)
    )
    state._enable_location = True
    state._estimated_devices = 10
    state._state_interval = 120

    result = asyncio.run(state._async_update_data())

    assert result["dev-1"]["state"] == {"online": True, "clients_count": 5}
    assert result["dev-1"]["location"] == {"latitude": 1.0, "longitude": 2.0}
    assert state.monthly_request_estimate > 0

    async def _raise_state(device_ids: list[str], max_per_cycle: int | None) -> Any:
        raise RmsApiError("bad state")

    state._api.async_get_states_for_devices = _raise_state
    with pytest.raises(UpdateFailed):
        asyncio.run(state._async_update_data())

    async def _auth_state(device_ids: list[str], max_per_cycle: int | None) -> Any:
        raise ConfigEntryAuthFailed("denied")

    state._api.async_get_states_for_devices = _auth_state
    with pytest.raises(ConfigEntryAuthFailed):
        asyncio.run(state._async_update_data())

    state_empty = object.__new__(StateCoordinator)
    state_empty._inventory = SimpleNamespace(data={}, update_interval=timedelta(seconds=900))
    assert asyncio.run(state_empty._async_update_data()) == {}

    port_scan = object.__new__(PortScanCoordinator)
    port_scan._api = SimpleNamespace(
        async_get_device_ethernet_ports=lambda device_id: asyncio.sleep(
            0, result=[{"name": "port1"}]
        )
    )
    port_scan._inventory = SimpleNamespace(data={"dev-1": {"id": "dev-1"}})

    assert asyncio.run(port_scan._async_update_data()) == {"dev-1": [{"name": "port1"}]}

    async def _raise_ports(device_id: str) -> Any:
        raise RmsApiError("bad ports")

    port_scan._api.async_get_device_ethernet_ports = _raise_ports
    assert asyncio.run(port_scan._async_update_data()) == {}

    auth_port_scan = object.__new__(PortScanCoordinator)
    auth_port_scan._api = SimpleNamespace()
    auth_port_scan._inventory = SimpleNamespace(data={"dev-1": {"id": "dev-1"}})
    auth_port_scan._scope_warning_logged = False

    async def _raise_auth_ports(device_id: str) -> Any:
        raise ConfigEntryAuthFailed("missing scope")

    auth_port_scan._api.async_get_device_ethernet_ports = _raise_auth_ports
    assert asyncio.run(auth_port_scan._async_update_data()) == {}
    assert auth_port_scan._scope_warning_logged is True

    empty_port_scan = object.__new__(PortScanCoordinator)
    empty_port_scan._api = SimpleNamespace(
        async_get_device_ethernet_ports=lambda device_id: asyncio.sleep(
            0, result=[{"name": "unused"}]
        )
    )
    empty_port_scan._inventory = SimpleNamespace(data={})
    assert asyncio.run(empty_port_scan._async_update_data()) == {}

    port_config = object.__new__(PortConfigCoordinator)
    port_config._api = SimpleNamespace(
        async_get_device_port_configurations=lambda device_id: asyncio.sleep(
            0, result=[{"id": "port1", "poe_enable": "1"}]
        )
    )
    port_config._inventory = SimpleNamespace(data={"dev-1": {"id": "dev-1"}})
    port_config._scope_warning_logged = False
    assert asyncio.run(port_config._async_update_data()) == {
        "dev-1": [{"id": "port1", "poe_enable": "1"}]
    }

    async def _raise_bad_config(device_id: str) -> Any:
        raise RmsApiError("bad config")

    port_config._api.async_get_device_port_configurations = _raise_bad_config
    assert asyncio.run(port_config._async_update_data()) == {}

    auth_port_config = object.__new__(PortConfigCoordinator)
    auth_port_config._api = SimpleNamespace()
    auth_port_config._inventory = SimpleNamespace(data={"dev-1": {"id": "dev-1"}})
    auth_port_config._scope_warning_logged = False

    async def _raise_auth_config(device_id: str) -> Any:
        raise ConfigEntryAuthFailed("missing scope")

    auth_port_config._api.async_get_device_port_configurations = _raise_auth_config
    assert asyncio.run(auth_port_config._async_update_data()) == {}
    assert auth_port_config._scope_warning_logged is True

    empty_port_config = object.__new__(PortConfigCoordinator)
    empty_port_config._api = SimpleNamespace(
        async_get_device_port_configurations=lambda device_id: asyncio.sleep(
            0, result=[{"id": "port1", "poe_enable": "1"}]
        )
    )
    empty_port_config._inventory = SimpleNamespace(data={})
    assert asyncio.run(empty_port_config._async_update_data()) == {}


def test_coordinator_handles_auth_failed_and_refresh_all() -> None:
    inventory = object.__new__(InventoryCoordinator)

    async def _auth_fail(**kwargs: Any) -> Any:
        raise ConfigEntryAuthFailed("denied")

    inventory._api = SimpleNamespace(async_list_devices=_auth_fail)
    inventory._tags = []
    inventory._device_status = None
    with pytest.raises(ConfigEntryAuthFailed):
        asyncio.run(inventory._async_update_data())

    bundle = SimpleNamespace(
        inventory=FakeListenerCoordinator(),
        state=FakeListenerCoordinator(),
        port_scan=FakeListenerCoordinator(),
        port_config=FakeListenerCoordinator(),
    )
    asyncio.run(async_refresh_all(bundle))
    assert bundle.inventory.refresh_calls == 1
    assert bundle.state.refresh_calls == 1
    assert bundle.port_scan.refresh_calls == 1
    assert bundle.port_config.refresh_calls == 1


def test_state_coordinator_handles_location_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _raise_location(device_id: str) -> Any:
        raise RmsApiError("bad location")

    state = object.__new__(StateCoordinator)
    state._api = SimpleNamespace(
        endpoint_matrix=_matrix(aggregate=False),
        async_get_states_for_devices=lambda device_ids, max_per_cycle: asyncio.sleep(
            0, result={"dev-1": {"online": True}}
        ),
        async_get_device_location=_raise_location,
        async_get_device_wireless=lambda device_id: asyncio.sleep(0, result=[]),
        estimate_max_calls_per_cycle=lambda interval: 2,
    )
    state._inventory = SimpleNamespace(
        data={"dev-1": {"id": "dev-1"}}, update_interval=timedelta(seconds=900)
    )
    state._enable_location = True
    state._estimated_devices = 1
    state._state_interval = 120

    result = asyncio.run(state._async_update_data())

    assert result == {"dev-1": {"state": {"online": True}}}


def test_diagnostics_redacts_sensitive_fields() -> None:
    bundle = SimpleNamespace(
        api=SimpleNamespace(request_counter=7, endpoint_matrix=_matrix()),
        inventory=SimpleNamespace(data={"a": {}}),
        state=SimpleNamespace(data={"a": {}}),
    )
    entry = SimpleNamespace(
        entry_id="entry-1",
        title="Teltonika RMS",
        data={"access_token": "secret", "pat_token": "secret", "auth_mode": "pat", "other": "keep"},
        options={"interval": 60},
        runtime_data=TeltonikaRmsRuntime(bundle=bundle),
    )

    diagnostics = asyncio.run(async_get_config_entry_diagnostics(None, entry))

    assert diagnostics["entry"]["data"]["other"] == "keep"
    for key in TO_REDACT:
        if key in diagnostics["entry"]["data"]:
            assert diagnostics["entry"]["data"][key] == "**REDACTED**"
    assert diagnostics["runtime"]["auth_mode"] == "pat"
    assert diagnostics["runtime"]["aggregate_state_available"] is None
    assert diagnostics["runtime"]["request_counter"] == 7


def test_status_channel_manager_and_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    manager = RmsStatusChannelManager(SimpleNamespace())

    async def _socket(channel_id: str, timeout_seconds: int) -> dict[str, Any] | None:
        return {"completed": True}

    async def _poll(channel_id: str, timeout_seconds: int) -> dict[str, Any] | None:
        return {"completed": True}

    monkeypatch.setattr(manager, "_async_wait_via_socket", _socket)
    monkeypatch.setattr(manager, "_async_wait_via_polling", _poll)
    assert asyncio.run(manager.async_wait_for_channel("abc")) == {"completed": True}
    assert asyncio.run(manager.async_wait_for_channel("")) is None

    async def _done_payload(channel_id: str) -> dict[str, Any]:
        return {"status": "done"}

    async def _no_token() -> None:
        return None

    polling_api = SimpleNamespace(
        async_poll_status_channel=_done_payload,
        async_get_access_token=_no_token,
    )
    polling_manager = RmsStatusChannelManager(polling_api)

    async def _sleep(delay: float) -> None:
        return None

    monkeypatch.setattr("teltonika_rms.status_channel.asyncio.sleep", _sleep)
    assert asyncio.run(polling_manager._async_wait_via_polling("abc", 2)) == {"status": "done"}
    assert asyncio.run(polling_manager._async_wait_via_socket("abc", 1)) is None

    assert _coerce_payload({"ok": True}) == {"ok": True}
    assert _coerce_payload("bad") is None
    assert _is_terminal({"completed": True}) is True
    assert _is_terminal({"status": "completed"}) is True
    assert _is_terminal({"123": [{"status": "pending"}, {"status": "success"}]}) is True
    assert _is_terminal({"123": [{"status": "pending"}, "not_a_dict"]}) is False
    assert _is_terminal({"123": []}) is False
    assert _is_terminal({"response_state": "completed"}) is True
    assert _is_terminal({"status": "success"}) is True
    assert _is_terminal({"status": "pending"}) is False
    assert _is_terminal({"status": 1}) is False


def test_status_channel_socket_success_and_disconnect(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, Any] = {"handlers": {}}

    class FakeAsyncClient:
        def __init__(self, **kwargs: Any) -> None:
            self.connected = False
            seen["client"] = self

        def on(self, event: str) -> Any:
            def _register(callback: Any) -> Any:
                seen["handlers"][event] = callback
                return callback

            return _register

        async def connect(self, url: str, **kwargs: Any) -> None:
            self.connected = True
            seen["connect_url"] = url
            seen["connect_kwargs"] = kwargs

        async def emit(self, event: str, payload: dict[str, Any]) -> None:
            seen["emit"] = (event, payload)
            await seen["handlers"]["message"]({"channel": "other", "status": "done"})
            await seen["handlers"]["message"]("invalid")
            await seen["handlers"]["status"]({"channel": "abc", "status": "done"})

        async def disconnect(self) -> None:
            seen["disconnected"] = True
            self.connected = False

    monkeypatch.setattr(
        "teltonika_rms.status_channel.socketio",
        SimpleNamespace(AsyncClient=FakeAsyncClient),
    )
    manager = RmsStatusChannelManager(
        SimpleNamespace(async_get_access_token=lambda: asyncio.sleep(0, result="token-123"))
    )

    result = asyncio.run(manager._async_wait_via_socket("abc", 1))

    assert result == {"channel": "abc", "status": "done"}
    assert seen["connect_url"].endswith("?token=token-123")
    assert seen["connect_kwargs"]["auth"] == {"token": "token-123"}
    assert seen["emit"] == ("subscribe", {"channel": "abc"})
    assert seen["disconnected"] is True


def test_status_channel_socket_handles_connect_failures_and_emit_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeAsyncClient:
        def __init__(self, **kwargs: Any) -> None:
            self.connected = True

        def on(self, event: str) -> Any:
            return lambda callback: callback

        async def connect(self, url: str, **kwargs: Any) -> None:
            return None

        async def emit(self, event: str, payload: dict[str, Any]) -> None:
            raise RuntimeError("emit failed")

        async def disconnect(self) -> None:
            self.connected = False

    monkeypatch.setattr(
        "teltonika_rms.status_channel.socketio",
        SimpleNamespace(AsyncClient=FakeAsyncClient),
    )
    manager = RmsStatusChannelManager(
        SimpleNamespace(async_get_access_token=lambda: asyncio.sleep(0, result="token-123"))
    )

    assert asyncio.run(manager._async_wait_via_socket("abc", 0)) is None

    class FailingClient(FakeAsyncClient):
        async def connect(self, url: str, **kwargs: Any) -> None:
            raise RuntimeError("connect failed")

    monkeypatch.setattr(
        "teltonika_rms.status_channel.socketio",
        SimpleNamespace(AsyncClient=FailingClient),
    )
    assert asyncio.run(manager._async_wait_via_socket("abc", 1)) is None


def test_status_channel_polling_times_out(monkeypatch: pytest.MonkeyPatch) -> None:
    polls: list[str] = []

    async def _pending(channel_id: str) -> dict[str, Any]:
        polls.append(channel_id)
        return {"status": "pending"}

    async def _sleep(delay: float) -> None:
        return None

    now = datetime(2026, 3, 13, 12, 0, tzinfo=UTC)
    times = iter([now, now, now + timedelta(seconds=3)])

    class FakeDateTime(datetime):
        @classmethod
        def now(cls, tz: Any = None) -> datetime:
            return next(times)

    monkeypatch.setattr("teltonika_rms.status_channel.asyncio.sleep", _sleep)
    monkeypatch.setattr("teltonika_rms.status_channel.datetime", FakeDateTime)
    manager = RmsStatusChannelManager(
        SimpleNamespace(
            async_poll_status_channel=_pending,
            async_get_access_token=lambda: asyncio.sleep(0, result="token"),
        )
    )

    assert asyncio.run(manager._async_wait_via_polling("abc", 2)) is None
    assert polls == ["abc"]


def test_homeassistant_can_be_constructed_for_coordinator_compatibility() -> None:
    async def _build() -> str:
        with tempfile.TemporaryDirectory() as tmpdir:
            hass = HomeAssistant(tmpdir)
            return hass.config.config_dir

    assert asyncio.run(_build())
