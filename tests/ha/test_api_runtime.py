"""High-value runtime tests for the RMS API client."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from aiohttp import ClientError
from homeassistant.exceptions import ConfigEntryAuthFailed
from teltonika_rms.api import (
    OAuth2RmsAuthClient,
    PatRmsAuthClient,
    RmsApiClient,
    _async_retry_sleep,
    _coerce_list,
    _coerce_state_map,
    _extract_ethernet_ports,
    _extract_port_configurations,
    _has_next_page,
    _parse_envelope,
    _retry_delay,
    _safe_json,
    chunked,
    estimate_monthly_requests,
    normalize_tags,
)
from teltonika_rms.endpoint_matrix import EndpointMatrix, EndpointSpec
from teltonika_rms.exceptions import RmsApiError, RmsAuthError

pytestmark = pytest.mark.ha


class FakeResponse:
    def __init__(
        self,
        status: int,
        payload: Any = None,
        *,
        text: str = "payload",
        headers: dict[str, str] | None = None,
        json_error: Exception | None = None,
    ) -> None:
        self.status = status
        self._payload = payload
        self._text = text
        self.headers = headers or {}
        self._json_error = json_error
        self.released = False

    async def json(self, content_type: Any = None) -> Any:
        if self._json_error is not None:
            raise self._json_error
        return self._payload

    async def text(self) -> str:
        return self._text

    def release(self) -> None:
        self.released = True


class FakeAuthClient:
    def __init__(self, responses: list[Any], token: str | None = "token") -> None:
        self._responses = list(responses)
        self._token = token
        self.calls: list[dict[str, Any]] = []

    async def async_request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None,
        json: dict[str, Any] | None,
        timeout: int,
    ) -> FakeResponse:
        self.calls.append(
            {
                "method": method,
                "url": url,
                "params": params,
                "json": json,
                "timeout": timeout,
            }
        )
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    async def async_get_access_token(self) -> str | None:
        return self._token


class FakeSession:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append({"method": method, "url": url, **kwargs})
        return FakeResponse(200, {"ok": True})


class FakeOAuthSession:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.token: dict[str, Any] = {"access_token": "oauth-token"}
        self.ensure_calls = 0

    async def async_request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append({"method": method, "url": url, **kwargs})
        return FakeResponse(200, {"ok": True})

    async def async_ensure_token_valid(self) -> None:
        self.ensure_calls += 1


def _matrix(*, aggregate: bool = True) -> EndpointMatrix:
    endpoints = {
        "devices_list": EndpointSpec("/v3/devices", tuple(), "safe"),
        "device_detail": EndpointSpec("/v3/devices/{id}", tuple(), "safe"),
        "device_state_single": EndpointSpec("/v3/devices/{id}/status", tuple(), "async-channel"),
        "device_location": EndpointSpec("/v3/devices/{id}/location", tuple(), "high-cost"),
        "device_wireless": EndpointSpec("/devices/{device_id}/wireless", tuple(), "safe"),
    }
    if aggregate:
        endpoints["device_state_aggregate"] = EndpointSpec(
            "/v3/devices/status",
            tuple(),
            "async-channel",
        )
    return EndpointMatrix(source="test", endpoints=endpoints)


def test_pat_auth_client_adds_bearer_token() -> None:
    session = FakeSession()
    client = PatRmsAuthClient(session, " secret-token ")

    asyncio.run(
        client.async_request("GET", "https://example.test", params={"a": 1}, json=None, timeout=30)
    )

    assert session.calls[0]["headers"]["Authorization"] == "Bearer secret-token"
    assert asyncio.run(client.async_get_access_token()) == "secret-token"


def test_api_accessors_expose_matrix_and_access_token() -> None:
    auth = FakeAuthClient([], token="abc")
    matrix = _matrix()
    client = RmsApiClient(auth, matrix)

    assert client.endpoint_matrix is matrix
    assert asyncio.run(client.async_get_access_token()) == "abc"


def test_oauth2_auth_client_uses_session_and_exposes_access_token() -> None:
    session = FakeOAuthSession()
    client = OAuth2RmsAuthClient(session)  # type: ignore[arg-type]

    asyncio.run(
        client.async_request("POST", "https://example.test", params=None, json={"a": 1}, timeout=30)
    )

    assert session.calls[0]["method"] == "POST"
    assert asyncio.run(client.async_get_access_token()) == "oauth-token"
    assert session.ensure_calls == 1

    session.token = {"access_token": 123}
    assert asyncio.run(client.async_get_access_token()) is None


def test_api_request_parses_envelope_and_releases_response() -> None:
    response = FakeResponse(200, {"success": True, "data": {"value": 1}, "meta": {"x": 1}})
    client = RmsApiClient(FakeAuthClient([response]), _matrix())

    data, meta = asyncio.run(client.async_request("GET", "/v3/devices"))

    assert data == {"value": 1}
    assert meta == {"x": 1}
    assert response.released is True


def test_api_request_raises_on_http_error_and_supports_absolute_urls() -> None:
    response = FakeResponse(400, {"error": "bad"})
    client = RmsApiClient(FakeAuthClient([response]), _matrix())

    with pytest.raises(RmsApiError, match="400"):
        asyncio.run(
            client.async_request("GET", "https://status.example.test/channel/1", absolute_url=True)
        )

    assert response.released is True


def test_api_request_retries_on_retry_after(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: list[float] = []

    async def _sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr("teltonika_rms.api.asyncio.sleep", _sleep)
    first = FakeResponse(429, {"retry": True}, headers={"Retry-After": "0"})
    second = FakeResponse(200, {"success": True, "data": {"ok": True}, "meta": {}})
    client = RmsApiClient(FakeAuthClient([first, second]), _matrix())

    data, _meta = asyncio.run(client.async_request("GET", "/v3/devices"))

    assert data == {"ok": True}
    assert sleeps == [0.0]
    assert client.request_counter == 2


def test_api_request_handles_not_found_when_allowed() -> None:
    client = RmsApiClient(FakeAuthClient([FakeResponse(404, {"missing": True})]), _matrix())

    data, meta = asyncio.run(client.async_request("GET", "/v3/devices/42", allow_not_found=True))

    assert data is None
    assert meta == {}


def test_api_request_raises_auth_failed_on_scope_error() -> None:
    client = RmsApiClient(FakeAuthClient([FakeResponse(403, {"error": "denied"})]), _matrix())

    with pytest.raises(ConfigEntryAuthFailed):
        asyncio.run(client.async_request("GET", "/v3/devices"))


def test_api_request_wraps_network_error_after_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _sleep(delay: float) -> None:
        return None

    monkeypatch.setattr("teltonika_rms.api.asyncio.sleep", _sleep)
    client = RmsApiClient(FakeAuthClient([ClientError("boom")] * 5), _matrix())

    with pytest.raises(RmsApiError, match="network error"):
        asyncio.run(client.async_request("GET", "/v3/devices"))


def test_api_request_retries_on_server_error_then_raises() -> None:
    client = RmsApiClient(FakeAuthClient([FakeResponse(500, {"bad": True})] * 5), _matrix())

    with pytest.raises(RmsApiError, match="500"):
        asyncio.run(client.async_request("GET", "/v3/devices"))


def test_api_request_resolves_meta_channel() -> None:
    class FakeChannelManager:
        async def async_wait_for_channel(self, channel_id: str) -> dict[str, Any]:
            assert channel_id == "abc"
            return {"data": [{"id": "device-1", "online": True}]}

    response = FakeResponse(
        200,
        {
            "success": True,
            "data": {},
            "meta": {"channel": "abc"},
        },
    )
    client = RmsApiClient(FakeAuthClient([response]), _matrix())
    client.set_status_channel_manager(FakeChannelManager())

    result = asyncio.run(client.async_get_states_for_devices(["device-1"], max_per_cycle=None))

    assert result == {"device-1": {"id": "device-1", "online": True}}


def test_api_reboot_device_posts_action_payload() -> None:
    response = FakeResponse(200, {"success": True, "data": {"queued": True}, "meta": {}})
    auth = FakeAuthClient([response])
    client = RmsApiClient(auth, _matrix())

    result = asyncio.run(client.async_reboot_device("42"))

    assert result == {"queued": True}
    assert auth.calls[0]["method"] == "POST"
    assert auth.calls[0]["url"].endswith("/devices/actions")
    assert auth.calls[0]["json"] == {"action": "reboot", "device_id": [42]}


def test_api_execute_device_action_keeps_non_numeric_ids() -> None:
    response = FakeResponse(200, {"success": True, "data": {"queued": True}, "meta": {}})
    auth = FakeAuthClient([response])
    client = RmsApiClient(auth, _matrix())

    asyncio.run(client.async_execute_device_action("reboot", ["dev-a"]))

    assert auth.calls[0]["json"] == {"action": "reboot", "device_id": ["dev-a"]}


def test_api_meta_channel_resolution_handles_fallback_variants() -> None:
    client = RmsApiClient(FakeAuthClient([]), _matrix())

    assert asyncio.run(client._resolve_meta_channel({}, {"ok": True})) == {"ok": True}
    assert asyncio.run(client._resolve_meta_channel({"channel": "abc"}, {"ok": True})) == {
        "ok": True
    }

    class FakeChannelManager:
        async def async_wait_for_channel(self, channel_id: str) -> dict[str, Any] | None:
            if channel_id == "empty":
                return None
            return {"completed": True}

    client.set_status_channel_manager(FakeChannelManager())
    assert asyncio.run(client._resolve_meta_channel({"channel": "empty"}, {"ok": True})) == {
        "ok": True
    }
    assert asyncio.run(client._resolve_meta_channel({"channel": "abc"}, {"ok": True})) == {
        "completed": True
    }


def test_api_get_device_state_falls_back_to_detail_on_error() -> None:
    auth = FakeAuthClient(
        [
            FakeResponse(500, {"error": "bad"}),
            FakeResponse(200, {"success": True, "data": {"id": "1", "name": "router"}, "meta": {}}),
        ]
    )
    client = RmsApiClient(auth, _matrix())

    result = asyncio.run(client.async_get_device_state("1"))

    assert result == {"id": "1", "name": "router"}


def test_api_get_device_state_and_location_handle_missing_paths_and_non_dict_responses() -> None:
    matrix = EndpointMatrix(
        source="test",
        endpoints={"devices_list": EndpointSpec("/v3/devices", tuple(), "safe")},
    )
    client = RmsApiClient(FakeAuthClient([]), matrix)

    assert asyncio.run(client.async_get_device_state("1")) == {}
    assert asyncio.run(client.async_get_device_location("1")) == {}

    client = RmsApiClient(
        FakeAuthClient([FakeResponse(200, {"success": True, "data": ["bad"], "meta": {}})]),
        _matrix(),
    )
    assert asyncio.run(client.async_get_device_location("1")) == {}


def test_api_get_device_ethernet_ports_handles_status_channel_and_missing_values() -> None:
    class FakeChannelManager:
        async def async_wait_for_channel(self, channel_id: str) -> dict[str, Any]:
            assert channel_id == "port-scan"
            return {
                "42": [
                    {
                        "status": "completed",
                        "type": "port_scan",
                        "ports": [
                            {"id": 1, "name": "port1", "devices": [{"ip": "192.168.1.5"}]},
                            {"id": 2, "name": "port2", "devices": []},
                        ],
                    }
                ]
            }

    client = RmsApiClient(
        FakeAuthClient(
            [FakeResponse(200, {"success": True, "data": None, "meta": {"channel": "port-scan"}})]
        ),
        _matrix(),
    )
    client.set_status_channel_manager(FakeChannelManager())

    ports = asyncio.run(client.async_get_device_ethernet_ports("42"))

    assert ports == [
        {"id": 1, "name": "port1", "devices": [{"ip": "192.168.1.5"}]},
        {"id": 2, "name": "port2", "devices": []},
    ]

    client = RmsApiClient(FakeAuthClient([FakeResponse(404, {"missing": True})]), _matrix())
    assert asyncio.run(client.async_get_device_ethernet_ports("42")) is None


def test_api_get_device_port_configurations_handles_status_channel_and_missing_values() -> None:
    class FakeChannelManager:
        async def async_wait_for_channel(self, channel_id: str) -> dict[str, Any]:
            assert channel_id == "port-config"
            return {
                "value": "Successfully executed API action.",
                "data": [
                    {
                        "rid": 0,
                        "type": "api_forward",
                        "data": [
                            {
                                "id": "port1",
                                ".type": "switch_port",
                                "poe_enable": "1",
                                "description": "tado",
                            },
                            {"id": "port2", ".type": "switch_port", "poe_enable": "0"},
                            {"id": "sfp1", ".type": "switch_port"},
                        ],
                        "code": 200,
                    }
                ],
                "response_state": "completed",
            }

    client = RmsApiClient(
        FakeAuthClient(
            [FakeResponse(200, {"success": True, "data": None, "meta": {"channel": "port-config"}})]
        ),
        _matrix(),
    )
    client.set_status_channel_manager(FakeChannelManager())

    ports = asyncio.run(client.async_get_device_port_configurations("42"))

    assert ports == [
        {"id": "port1", ".type": "switch_port", "poe_enable": "1", "description": "tado"},
        {"id": "port2", ".type": "switch_port", "poe_enable": "0"},
        {"id": "sfp1", ".type": "switch_port"},
    ]
    assert client._auth.calls[0]["method"] == "POST"
    assert client._auth.calls[0]["url"].endswith("/devices/configurator/configuration")
    assert client._auth.calls[0]["json"] == {
        "device_id": 42,
        "endpoints": [{"path": "/ports_settings/config"}],
    }

    client = RmsApiClient(FakeAuthClient([FakeResponse(404, {"missing": True})]), _matrix())
    assert asyncio.run(client.async_get_device_port_configurations("42")) is None


def test_api_set_device_port_poe_posts_expected_payloads() -> None:
    auth = FakeAuthClient(
        [
            FakeResponse(200, {"success": True, "data": {"queued": True}, "meta": {}}),
            FakeResponse(200, {"success": True, "data": {"queued": True}, "meta": {}}),
        ]
    )
    client = RmsApiClient(auth, _matrix())

    assert asyncio.run(client.async_set_device_port_poe("42", "port3", True)) == {"queued": True}
    assert auth.calls[0]["url"].endswith("/devices/configurator/configure")
    assert auth.calls[0]["json"] == {
        "configuration": [
            {
                "path": "/ports_settings/config/{id}",
                "content_type": "application/json",
                "method": "put",
                "request_data": {"data": {"poe_enable": "1"}},
                "query_parameters": [{"key": "id", "value": "port3"}],
                "device_id": [42],
            }
        ]
    }

    assert asyncio.run(client.async_set_device_port_poe("device-a", "port3", False)) == {
        "queued": True
    }
    assert auth.calls[1]["json"] == {
        "configuration": [
            {
                "path": "/ports_settings/config/{id}",
                "content_type": "application/json",
                "method": "put",
                "request_data": {"data": {"poe_enable": "0"}},
                "query_parameters": [{"key": "id", "value": "port3"}],
                "device_id": ["device-a"],
            }
        ]
    }


def test_api_extract_ethernet_ports_covers_direct_and_empty_payload_shapes() -> None:
    assert _extract_ethernet_ports("42", None) is None
    assert _extract_ethernet_ports("42", {"42": [{"ports": ["bad", {"id": 1}]}]}) == [{"id": 1}]
    assert _extract_ethernet_ports("42", {"ports": [{"id": 2}, "bad"]}) == [{"id": 2}]
    assert _extract_ethernet_ports("42", {"42": [{"status": "completed"}]}) == []
    assert _extract_ethernet_ports("42", {"42": {"status": "completed"}}) == []
    assert _extract_ethernet_ports("42", {"42": ["bad"]}) == []
    assert _extract_ethernet_ports("42", "bad") is None


def test_api_extract_port_configurations_covers_status_payload_shapes() -> None:
    assert _extract_port_configurations(None) is None
    assert _extract_port_configurations("bad") is None
    assert _extract_port_configurations([{"id": "port1"}]) == [{"id": "port1"}]
    assert _extract_port_configurations({"data": "bad"}) == []
    assert _extract_port_configurations(
        {
            "data": [
                {"rid": 0, "data": "bad"},
                {
                    "rid": 1,
                    "data": [
                        {"id": "port1", "poe_enable": "1"},
                        "bad",
                        {"id": "port2", "poe_enable": "0"},
                    ],
                },
            ]
        }
    ) == [{"id": "port1", "poe_enable": "1"}, {"id": "port2", "poe_enable": "0"}]


def test_api_get_states_for_devices_uses_round_robin_without_aggregate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = RmsApiClient(FakeAuthClient([]), _matrix(aggregate=False))

    async def _state(device_id: str) -> dict[str, Any]:
        return {"id": device_id}

    monkeypatch.setattr(client, "async_get_device_state", _state)

    first = asyncio.run(client.async_get_states_for_devices(["a", "b", "c"], max_per_cycle=2))
    second = asyncio.run(client.async_get_states_for_devices(["a", "b", "c"], max_per_cycle=2))

    assert set(first) == {"a", "b"}
    assert set(second) == {"a", "c"}


def test_api_get_states_for_devices_handles_empty_and_unbounded_batches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = RmsApiClient(FakeAuthClient([]), _matrix(aggregate=False))

    async def _state(device_id: str) -> dict[str, Any]:
        return {"id": device_id}

    monkeypatch.setattr(client, "async_get_device_state", _state)

    assert asyncio.run(client.async_get_states_for_devices([], max_per_cycle=None)) == {}
    assert asyncio.run(client.async_get_states_for_devices(["a", "b"], max_per_cycle=0)) == {
        "a": {"id": "a"},
        "b": {"id": "b"},
    }


def test_api_get_states_for_devices_handles_aggregate_fallbacks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = RmsApiClient(
        FakeAuthClient([FakeResponse(404, {"missing": True})]),
        _matrix(),
    )

    async def _per_device(
        device_ids: list[str], *, max_per_cycle: int | None
    ) -> dict[str, dict[str, Any]]:
        assert device_ids == ["a"]
        assert max_per_cycle == 1
        return {"a": {"id": "a", "fallback": True}}

    monkeypatch.setattr(client, "_async_per_device_state", _per_device)
    result = asyncio.run(client.async_get_states_for_devices(["a"], max_per_cycle=1))

    assert result == {"a": {"id": "a", "fallback": True}}
    assert client._aggregate_state_available is False

    client = RmsApiClient(FakeAuthClient([FakeResponse(500, {"bad": True})] * 5), _matrix())
    monkeypatch.setattr(client, "_async_per_device_state", _per_device)
    result = asyncio.run(client.async_get_states_for_devices(["a"], max_per_cycle=1))
    assert result == {"a": {"id": "a", "fallback": True}}
    assert client._aggregate_state_available is False


def test_api_list_devices_paginates_and_applies_filters() -> None:
    auth = FakeAuthClient(
        [
            FakeResponse(
                200,
                {
                    "success": True,
                    "data": [{"id": "1"}],
                    "meta": {"pagination": {"page": 1, "pages": 2}},
                },
            ),
            FakeResponse(
                200,
                {
                    "success": True,
                    "data": [{"id": "2"}],
                    "meta": {"pagination": {"page": 2, "pages": 2}},
                },
            ),
        ]
    )
    client = RmsApiClient(auth, _matrix())

    devices = asyncio.run(
        client.async_list_devices(tags=["a", "b"], device_status="online", page_size=1, max_pages=5)
    )

    assert devices == [{"id": "1"}, {"id": "2"}]
    assert auth.calls[0]["params"] == {"limit": 1, "page": 1, "tags": "a,b", "status": "online"}


def test_api_list_devices_requires_configured_endpoint() -> None:
    client = RmsApiClient(FakeAuthClient([]), EndpointMatrix(source="test", endpoints={}))

    with pytest.raises(RmsApiError, match="devices list endpoint"):
        asyncio.run(client.async_list_devices())


def test_api_validate_connection_uses_single_page_probe(monkeypatch: pytest.MonkeyPatch) -> None:
    client = RmsApiClient(FakeAuthClient([]), _matrix())
    seen: dict[str, Any] = {}

    async def _list_devices(**kwargs: Any) -> list[dict[str, Any]]:
        seen.update(kwargs)
        return []

    monkeypatch.setattr(client, "async_list_devices", _list_devices)
    asyncio.run(client.async_validate_connection())
    assert seen == {"page_size": 1, "max_pages": 1}


def test_api_location_and_status_channel_polling() -> None:
    auth = FakeAuthClient(
        [
            FakeResponse(200, {"success": True, "data": {"lat": 1}, "meta": {}}),
            FakeResponse(200, {"success": True, "data": {"done": True}, "meta": {}}),
        ]
    )
    client = RmsApiClient(auth, _matrix())

    location = asyncio.run(client.async_get_device_location("1"))
    channel = asyncio.run(client.async_poll_status_channel("ch-1"))

    assert location == {"lat": 1}
    assert channel == {"done": True}


def test_api_poll_status_channel_returns_dict_only() -> None:
    client = RmsApiClient(
        FakeAuthClient(
            [
                FakeResponse(200, {"success": True, "data": {"status": "done"}, "meta": {}}),
                FakeResponse(200, {"success": True, "data": ["bad"], "meta": {}}),
            ]
        ),
        _matrix(),
    )

    assert asyncio.run(client.async_poll_status_channel("abc")) == {"status": "done"}
    assert asyncio.run(client.async_poll_status_channel("abc")) is None


def test_api_request_counter_resets_after_30_days() -> None:
    client = RmsApiClient(FakeAuthClient([]), _matrix())
    client._request_counter = 99
    client._request_window_start = datetime.now(tz=UTC) - timedelta(days=31)

    client._increment_request_counter()

    assert client.request_counter == 1


def test_api_helper_functions_cover_error_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    assert _coerce_list({"devices": [{"id": 1}, "bad"]}) == [{"id": 1}]
    assert _coerce_list({"results": [{"id": 2}]}) == [{"id": 2}]
    assert _coerce_list({"rows": [{"id": 3}]}) == [{"id": 3}]
    assert _coerce_state_map({"x": {"id": 1}}) == {"x": {"id": 1}}
    assert _coerce_state_map({"id": "solo"}) == {"solo": {"id": "solo"}}
    assert _coerce_state_map([{"deviceId": "x", "v": 1}, {"device_id": "y", "v": 2}]) == {
        "x": {"deviceId": "x", "v": 1},
        "y": {"device_id": "y", "v": 2},
    }
    assert _has_next_page([], {"pagination": {"page": 1, "pages": 2}}, 50) is True
    assert _has_next_page([], {"pagination": {"next": "/next"}}, 50) is True
    assert normalize_tags(" a, ,b ") == ["a", "b"]
    assert (
        estimate_monthly_requests(
            inventory_interval=60,
            state_interval=120,
            estimated_devices=10,
            aggregate_state_supported=False,
        )
        > 0
    )
    assert chunked(["a", "b", "c"], 2) == [["a", "b"], ["c"]]
    assert _parse_envelope({"plain": True}) == ({"plain": True}, {})

    with pytest.raises(RmsApiError):
        _parse_envelope({"success": False, "errors": ["bad"]})

    response = FakeResponse(200, text="raw-body", json_error=ValueError("bad json"))
    assert asyncio.run(_safe_json(response)) == {"raw": "raw-body"}

    delays: list[float] = []

    async def _sleep(delay: float) -> None:
        delays.append(delay)

    monkeypatch.setattr("teltonika_rms.api.asyncio.sleep", _sleep)
    asyncio.run(_async_retry_sleep(FakeResponse(429, headers={"Retry-After": "x"}), 0))
    assert len(delays) == 1
    delay = _retry_delay(3)
    assert 8.0 <= delay <= 8.5


def test_estimate_max_calls_per_cycle_has_floor() -> None:
    assert RmsApiClient.estimate_max_calls_per_cycle(60) >= 1


def test_rms_auth_error_is_subclass_of_api_error() -> None:
    assert issubclass(RmsAuthError, RmsApiError)


def test_api_get_device_wireless_handles_missing_and_success() -> None:
    client = RmsApiClient(
        FakeAuthClient(
            [
                FakeResponse(200, {"success": True, "data": [{"clients_count": 5}], "meta": {}}),
                FakeResponse(404, {"success": False, "errors": []}),
            ]
        ),
        _matrix(),
    )
    assert asyncio.run(client.async_get_device_wireless("1")) == [{"clients_count": 5}]
    assert asyncio.run(client.async_get_device_wireless("1")) == []

    # Missing endpoint
    client._matrix = EndpointMatrix(
        source="test",
        endpoints={"devices_list": EndpointSpec("/v3/devices", tuple(), "safe")},
    )
    assert asyncio.run(client.async_get_device_wireless("1")) == []


def test_api_extract_nested_data_lists() -> None:
    from teltonika_rms.api import _extract_ethernet_ports, _extract_port_configurations

    nested_payload = {"123": [{"status": "completed", "ports": [{"id": "p1"}]}]}
    assert _extract_ethernet_ports("123", nested_payload) == [{"id": "p1"}]

    config_payload = {
        "123": [
            "not a dict",
            {"status": "pending"},
            {"status": "completed", "data": ["not a dict", {"data": [{"id": "c1"}]}]},
        ]
    }
    assert _extract_port_configurations(config_payload) == [{"id": "c1"}]
