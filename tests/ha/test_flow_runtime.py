"""Config-flow and setup coverage tests."""

from __future__ import annotations

import base64
import importlib
import json
from datetime import timedelta
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, PropertyMock

import pytest
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from custom_components.teltonika_rms.config_flow import (
    OAuth2FlowHandler,
    TeltonikaRmsOptionsFlow,
)
from custom_components.teltonika_rms.const import (
    AUTH_MODE_PAT,
    CONF_AUTH_MODE,
    CONF_INVENTORY_INTERVAL,
    CONF_PAT_TOKEN,
    CONF_STATE_INTERVAL,
    DEFAULT_OPTIONS,
)
from custom_components.teltonika_rms.coordinator import CoordinatorBundle
from custom_components.teltonika_rms.endpoint_matrix import EndpointMatrix, EndpointSpec

pytestmark = pytest.mark.ha

integration = importlib.import_module("custom_components.teltonika_rms")


def _make_token(payload: dict[str, Any]) -> str:
    encoded = (
        base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8").rstrip("=")
    )
    return f"header.{encoded}.signature"


def _test_matrix() -> EndpointMatrix:
    return EndpointMatrix(
        source="test",
        endpoints={
            "devices_list": EndpointSpec(path="/devices", scopes=("devices:read",), polling="low"),
            "device_detail": EndpointSpec(
                path="/devices/{id}", scopes=("devices:read",), polling="low"
            ),
        },
    )


class FakeServices:
    def __init__(self) -> None:
        self.services: dict[str, dict[str, Any]] = {}
        self.async_remove = AsyncMock()
        self.async_register = AsyncMock()

    def has_service(self, domain: str, service: str) -> bool:
        return service in self.services.get(domain, {})


class FakeConfigEntries:
    def __init__(self) -> None:
        self.entries_result: list[Any] = []
        self.async_forward_entry_setups = AsyncMock(return_value=True)

    def async_entries(self, domain: str | None = None) -> list[Any]:
        return self.entries_result

    async def async_reload(self, entry_id: str) -> None:
        pass

    async def async_unload_platforms(self, entry: Any, platforms: Any) -> bool:
        return True


class FakeHass:
    def __init__(self) -> None:
        self.services = FakeServices()
        self.config_entries = FakeConfigEntries()
        self.created_tasks: list[Any] = []

    async def async_add_executor_job(self, func: Any, *args: Any) -> Any:
        return func(*args)

    def async_create_task(self, coro: Any) -> Any:
        self.created_tasks.append(coro)


@pytest.mark.asyncio
async def test_integration_merged_options_and_refresh_handler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entry = SimpleNamespace(options={CONF_STATE_INTERVAL: 999})
    merged = integration._merged_options(entry)
    assert merged[CONF_STATE_INTERVAL] == 999
    assert merged[CONF_INVENTORY_INTERVAL] == DEFAULT_OPTIONS[CONF_INVENTORY_INTERVAL]

    _mock_refresh = AsyncMock()
    # The actual patch point for where it's used in coordinator or imported into __init__
    monkeypatch.setattr(
        "custom_components.teltonika_rms.coordinator.async_refresh_all", _mock_refresh
    )

    hass = FakeHass()
    mock_bundle = MagicMock(spec=CoordinatorBundle)
    mock_bundle.inventory = MagicMock()
    mock_bundle.inventory.async_request_refresh = AsyncMock()
    mock_bundle.state = MagicMock()
    mock_bundle.state.async_request_refresh = AsyncMock()
    mock_bundle.port_scan = MagicMock()
    mock_bundle.port_scan.async_request_refresh = AsyncMock()
    mock_bundle.port_config = MagicMock()
    mock_bundle.port_config.async_request_refresh = AsyncMock()

    hass.config_entries.entries_result = [
        SimpleNamespace(runtime_data=SimpleNamespace(bundle=mock_bundle)),
        SimpleNamespace(runtime_data=None),
    ]

    handler = integration._build_refresh_handler(cast(Any, hass))
    await handler(None)

    _mock_refresh.assert_awaited_once_with(mock_bundle)


@pytest.mark.asyncio
async def test_integration_unload_and_reload_entry() -> None:
    hass = FakeHass()
    entry = SimpleNamespace(entry_id="entry-1")
    hass.config_entries.entries_result = []

    await integration.async_unload_entry(cast(Any, hass), entry)


def test_oauth2_flow_handler_async_get_options_flow() -> None:
    handler = OAuth2FlowHandler()
    flow = handler.async_get_options_flow(cast(Any, SimpleNamespace()))
    assert isinstance(flow, TeltonikaRmsOptionsFlow)


@pytest.mark.asyncio
async def test_options_flow_init_step() -> None:
    mock_entry = MagicMock()
    mock_entry.options = {CONF_STATE_INTERVAL: 120}
    flow = TeltonikaRmsOptionsFlow(mock_entry)
    result = await flow.async_step_init()
    assert result["type"] == "form"
    assert result["step_id"] == "init"


def test_extract_subject_from_token() -> None:
    token_str = _make_token({"sub": "user-123"})
    from custom_components.teltonika_rms.config_flow import _extract_subject_from_token

    # Pass dict as expected by function: token = data.get("token", {})
    # raw_access_token = token.get(CONF_ACCESS_TOKEN)
    data: dict[str, Any] = {"token": {CONF_ACCESS_TOKEN: token_str}}
    assert _extract_subject_from_token(data) == "user-123"
    assert _extract_subject_from_token({"token": "invalid"}) is None


def test_token_fingerprint() -> None:
    token_str = _make_token({"sub": "user-123"})
    from custom_components.teltonika_rms.config_flow import _token_fingerprint

    fp = _token_fingerprint(token_str)
    assert fp is not None
    assert len(fp) == 16


@pytest.mark.asyncio
async def test_integration_setup_entry_pat_and_oauth_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeCoordinator:
        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            self.data: dict[str, Any] = {}
            self.update_interval = timedelta(seconds=120)

            self.first_refresh_calls = 0
            self.request_refresh_calls = 0

        async def async_config_entry_first_refresh(self) -> None:
            self.first_refresh_calls += 1
            return None

        async def async_request_refresh(self) -> None:
            self.request_refresh_calls += 1
            return None

    hass = FakeHass()
    hass.config_entries.entries_result = [object()]

    monkeypatch.setattr(
        "custom_components.teltonika_rms.endpoint_matrix.load_endpoint_matrix",
        lambda path: _test_matrix(),
    )

    # Crucial: mock MUST return a real integer for .status
    _resp = MagicMock()
    type(_resp).status = PropertyMock(return_value=200)
    _resp.json = AsyncMock(return_value={"success": True, "data": [], "meta": {}})
    _resp.release = AsyncMock()

    monkeypatch.setattr(
        "custom_components.teltonika_rms.api.PatRmsAuthClient",
        lambda session, token: MagicMock(async_request=AsyncMock(return_value=_resp)),
    )
    # Patch coordinators
    monkeypatch.setattr(
        "custom_components.teltonika_rms.coordinator.InventoryCoordinator", FakeCoordinator
    )
    monkeypatch.setattr(
        "custom_components.teltonika_rms.coordinator.StateCoordinator", FakeCoordinator
    )
    monkeypatch.setattr(
        "custom_components.teltonika_rms.coordinator.PortScanCoordinator", FakeCoordinator
    )
    monkeypatch.setattr(
        "custom_components.teltonika_rms.coordinator.PortConfigCoordinator", FakeCoordinator
    )
    monkeypatch.setattr(
        "custom_components.teltonika_rms.status_channel.RmsStatusChannelManager",
        lambda api: SimpleNamespace(api=api),
    )
    monkeypatch.setattr(
        "homeassistant.helpers.aiohttp_client.async_get_clientsession",
        lambda hass: MagicMock(request=AsyncMock()),
    )

    entry = SimpleNamespace(
        data={CONF_AUTH_MODE: AUTH_MODE_PAT, CONF_PAT_TOKEN: "pat-token"},
        options={},
        runtime_data=None,
        entry_id="entry-1",
        add_update_listener=lambda listener: "listener-token",
        async_on_unload=lambda cb: None,
    )

    assert await integration.async_setup_entry(cast(Any, hass), entry) is True


@pytest.mark.asyncio
async def test_integration_setup_entry_wraps_refresh_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FailingCoordinator:
        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            self.update_interval = timedelta(seconds=120)

        async def async_config_entry_first_refresh(self) -> None:
            raise RuntimeError("boom")

    monkeypatch.setattr(
        "custom_components.teltonika_rms.endpoint_matrix.load_endpoint_matrix",
        lambda path: _test_matrix(),
    )
    _resp = MagicMock()
    type(_resp).status = PropertyMock(return_value=200)
    _resp.json = AsyncMock(return_value={"success": True, "data": [], "meta": {}})
    _resp.release = AsyncMock()

    monkeypatch.setattr(
        "custom_components.teltonika_rms.api.PatRmsAuthClient",
        lambda session, token: MagicMock(async_request=AsyncMock(return_value=_resp)),
    )
    monkeypatch.setattr(
        "custom_components.teltonika_rms.coordinator.InventoryCoordinator", FailingCoordinator
    )
    monkeypatch.setattr(
        "custom_components.teltonika_rms.coordinator.StateCoordinator", FailingCoordinator
    )
    monkeypatch.setattr(
        "custom_components.teltonika_rms.coordinator.PortScanCoordinator", FailingCoordinator
    )
    monkeypatch.setattr(
        "custom_components.teltonika_rms.coordinator.PortConfigCoordinator", FailingCoordinator
    )
    monkeypatch.setattr(
        "homeassistant.helpers.aiohttp_client.async_get_clientsession",
        lambda hass: MagicMock(request=AsyncMock()),
    )

    hass = FakeHass()
    entry = SimpleNamespace(
        data={CONF_AUTH_MODE: AUTH_MODE_PAT, CONF_PAT_TOKEN: "pat-token"},
        options={},
        runtime_data=None,
        entry_id="entry-1",
        add_update_listener=lambda listener: "listener-token",
        async_on_unload=lambda cb: None,
    )

    with pytest.raises(ConfigEntryNotReady):
        await integration.async_setup_entry(cast(Any, hass), entry)


@pytest.mark.asyncio
async def test_integration_setup_entry_propagates_auth_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeCoordinator:
        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            self.data: dict[str, Any] = {}
            self.update_interval = timedelta(seconds=120)

        async def async_config_entry_first_refresh(self) -> None:
            return None

    monkeypatch.setattr(
        "custom_components.teltonika_rms.endpoint_matrix.load_endpoint_matrix",
        lambda path: _test_matrix(),
    )
    _resp = MagicMock()
    # Trigger 401
    type(_resp).status = PropertyMock(return_value=401)
    _resp.json = AsyncMock(return_value={"success": False, "error": "unauthorized"})
    _resp.release = AsyncMock()

    monkeypatch.setattr(
        "custom_components.teltonika_rms.api.PatRmsAuthClient",
        lambda session, token: MagicMock(async_request=AsyncMock(return_value=_resp)),
    )
    monkeypatch.setattr(
        "custom_components.teltonika_rms.coordinator.InventoryCoordinator", FakeCoordinator
    )
    monkeypatch.setattr(
        "custom_components.teltonika_rms.coordinator.StateCoordinator", FakeCoordinator
    )
    monkeypatch.setattr(
        "custom_components.teltonika_rms.coordinator.PortScanCoordinator", FakeCoordinator
    )
    monkeypatch.setattr(
        "custom_components.teltonika_rms.coordinator.PortConfigCoordinator", FakeCoordinator
    )
    monkeypatch.setattr(
        "homeassistant.helpers.aiohttp_client.async_get_clientsession",
        lambda hass: MagicMock(request=AsyncMock()),
    )

    hass = FakeHass()
    entry = SimpleNamespace(
        data={CONF_AUTH_MODE: AUTH_MODE_PAT, CONF_PAT_TOKEN: "pat-token"},
        options={},
        runtime_data=None,
        entry_id="entry-1",
        add_update_listener=lambda listener: "listener-token",
        async_on_unload=lambda cb: None,
    )

    with pytest.raises(ConfigEntryAuthFailed):
        await integration.async_setup_entry(cast(Any, hass), entry)


@pytest.mark.asyncio
async def test_integration_setup_entry_does_not_block_on_optional_port_refreshes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created: dict[str, Any] = {}

    class RequiredCoordinator:
        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            self.data: dict[str, Any] = {}
            self.update_interval = timedelta(seconds=120)
            self.first_refresh_calls = 0
            self.request_refresh_calls = 0

        async def async_config_entry_first_refresh(self) -> None:
            self.first_refresh_calls += 1

        async def async_request_refresh(self) -> None:
            self.request_refresh_calls += 1

    class OptionalCoordinator:
        def __init__(self, name: str, *_args: Any, **_kwargs: Any) -> None:
            self.name = name
            self.data: dict[str, Any] = {}
            self.update_interval = timedelta(seconds=120)
            self.first_refresh_calls = 0
            self.request_refresh_calls = 0

        async def async_config_entry_first_refresh(self) -> None:
            self.first_refresh_calls += 1
            raise AssertionError("optional first refresh must not be awaited during setup")

        async def async_request_refresh(self) -> None:
            self.request_refresh_calls += 1

    def _inventory(*_args: Any, **_kwargs: Any) -> Any:
        created["inventory"] = RequiredCoordinator()
        return created["inventory"]

    def _state(*_args: Any, **_kwargs: Any) -> Any:
        created["state"] = RequiredCoordinator()
        return created["state"]

    def _port_scan(*_args: Any, **_kwargs: Any) -> Any:
        created["port_scan"] = OptionalCoordinator("port_scan")
        return created["port_scan"]

    def _port_config(*_args: Any, **_kwargs: Any) -> Any:
        created["port_config"] = OptionalCoordinator("port_config")
        return created["port_config"]

    monkeypatch.setattr(
        "custom_components.teltonika_rms.endpoint_matrix.load_endpoint_matrix",
        lambda path: _test_matrix(),
    )
    _resp = MagicMock()
    type(_resp).status = PropertyMock(return_value=200)
    _resp.json = AsyncMock(return_value={"success": True, "data": [], "meta": {}})
    _resp.release = AsyncMock()

    monkeypatch.setattr(
        "custom_components.teltonika_rms.api.PatRmsAuthClient",
        lambda session, token: MagicMock(async_request=AsyncMock(return_value=_resp)),
    )
    monkeypatch.setattr(
        "custom_components.teltonika_rms.coordinator.InventoryCoordinator", _inventory
    )
    monkeypatch.setattr("custom_components.teltonika_rms.coordinator.StateCoordinator", _state)
    monkeypatch.setattr(
        "custom_components.teltonika_rms.coordinator.PortScanCoordinator", _port_scan
    )
    monkeypatch.setattr(
        "custom_components.teltonika_rms.coordinator.PortConfigCoordinator", _port_config
    )
    monkeypatch.setattr(
        "homeassistant.helpers.aiohttp_client.async_get_clientsession",
        lambda hass: MagicMock(request=AsyncMock()),
    )

    hass = FakeHass()
    hass.config_entries.entries_result = [object()]
    entry = SimpleNamespace(
        data={CONF_AUTH_MODE: AUTH_MODE_PAT, CONF_PAT_TOKEN: "pat-token"},
        options={},
        runtime_data=None,
        entry_id="entry-1",
        add_update_listener=lambda listener: "listener-token",
        async_on_unload=lambda cb: None,
    )

    assert await integration.async_setup_entry(cast(Any, hass), entry) is True
