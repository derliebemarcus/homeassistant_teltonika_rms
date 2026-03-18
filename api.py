"""RMS API client and transport behavior."""

from __future__ import annotations

import asyncio
import logging
import random
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any, Protocol

from aiohttp import ClientError, ClientResponse, ClientSession, ClientTimeout
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.config_entry_oauth2_flow import OAuth2Session

from .const import API_BASE_URL, MAX_MONTHLY_REQUESTS, REQUEST_BUDGET_HEADROOM, STATUS_BASE_URL
from .endpoint_matrix import EndpointMatrix
from .exceptions import RmsApiError

LOGGER = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 30
_MAX_RETRIES = 4
_RETRIABLE_STATUS_CODES = {429, 500, 502, 503, 504}
_DEVICE_ACTIONS_PATH = "/devices/actions"
_DEVICE_CONFIGURATION_READ_PATH = "/devices/configurator/configuration"
_DEVICE_CONFIGURATION_WRITE_PATH = "/devices/configurator/configure"


class RmsAuthClient(Protocol):
    """Authentication transport abstraction used by RMS API client."""

    async def async_request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None,
        json: dict[str, Any] | None,
        timeout: int,
    ) -> ClientResponse:
        """Perform HTTP request with auth attached."""

    async def async_get_access_token(self) -> str | None:
        """Return bearer token for status socket usage."""


class OAuth2RmsAuthClient:
    """OAuth2 auth provider backed by Home Assistant OAuth2Session."""

    def __init__(self, oauth_session: OAuth2Session) -> None:
        self._oauth_session = oauth_session

    async def async_request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None,
        json: dict[str, Any] | None,
        timeout: int,
    ) -> ClientResponse:
        return await self._oauth_session.async_request(
            method,
            url,
            params=params,
            json=json,
            timeout=timeout,
        )

    async def async_get_access_token(self) -> str | None:
        await self._oauth_session.async_ensure_token_valid()
        token = self._oauth_session.token.get("access_token")
        return token if isinstance(token, str) else None


class PatRmsAuthClient:
    """PAT auth provider using static bearer token."""

    def __init__(self, session: ClientSession, pat_token: str) -> None:
        self._session = session
        self._pat_token = pat_token.strip()

    async def async_request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None,
        json: dict[str, Any] | None,
        timeout: int,
    ) -> ClientResponse:
        headers = {
            "Authorization": f"Bearer {self._pat_token}",
        }
        return await self._session.request(
            method,
            url,
            params=params,
            json=json,
            timeout=ClientTimeout(total=timeout),
            headers=headers,
        )

    async def async_get_access_token(self) -> str | None:
        return self._pat_token


class RmsApiClient:
    """Typed RMS API client with retry and envelope parsing."""

    def __init__(
        self,
        auth: RmsAuthClient,
        endpoint_matrix: EndpointMatrix,
    ) -> None:
        self._auth = auth
        self._matrix = endpoint_matrix
        self._request_counter = 0
        self._request_window_start = datetime.now(tz=UTC)
        self._status_channel_manager: Any = None
        self._round_robin_cursor = 0
        self._aggregate_state_available: bool | None = None

    @property
    def endpoint_matrix(self) -> EndpointMatrix:
        """Expose the resolved endpoint matrix."""
        return self._matrix

    @property
    def request_counter(self) -> int:
        """Current rolling request counter."""
        return self._request_counter

    def set_status_channel_manager(self, manager: Any) -> None:
        """Set channel manager used when RMS returns meta.channel."""
        self._status_channel_manager = manager

    async def async_get_access_token(self) -> str | None:
        """Return current bearer token."""
        return await self._auth.async_get_access_token()

    async def async_validate_connection(self) -> None:
        """Validate credentials by loading the first page of devices."""
        await self.async_list_devices(page_size=1, max_pages=1)

    async def async_list_devices(
        self,
        *,
        tags: list[str] | None = None,
        device_status: str | None = None,
        page_size: int = 50,
        max_pages: int = 20,
    ) -> list[dict[str, Any]]:
        """Fetch devices using matrix-defined list endpoint and pagination helpers."""
        path = self._matrix.path_for("devices_list")
        if not path:
            raise RmsApiError("No devices list endpoint configured")

        page = 1
        devices: list[dict[str, Any]] = []

        while page <= max_pages:
            params: dict[str, Any] = {"limit": page_size, "page": page}
            if tags:
                params["tags"] = ",".join(tags)
            if device_status:
                params["status"] = device_status

            data, meta = await self.async_request("GET", path, params=params)
            batch = _coerce_list(data)
            devices.extend(batch)

            if not _has_next_page(batch, meta, page_size):
                break
            page += 1

        return devices

    async def async_get_device_state(self, device_id: str) -> dict[str, Any]:
        """Fetch device state details for a single device."""
        state_path = self._matrix.format_path("device_state_single", id=device_id)
        detail_path = self._matrix.format_path("device_detail", id=device_id)

        if state_path:
            try:
                data, _meta = await self.async_request("GET", state_path, allow_not_found=True)
                if isinstance(data, dict):
                    return data
            except RmsApiError:
                LOGGER.debug("State endpoint failed for %s, falling back to detail", device_id)

        if detail_path:
            data, _meta = await self.async_request("GET", detail_path, allow_not_found=True)
            if isinstance(data, dict):
                return data

        return {}

    async def async_get_device_location(self, device_id: str) -> dict[str, Any]:
        """Fetch location data for a single device when available."""
        location_path = self._matrix.format_path("device_location", id=device_id)
        if not location_path:
            return {}

        data, _meta = await self.async_request("GET", location_path, allow_not_found=True)
        if isinstance(data, dict):
            return data
        return {}

    async def async_get_device_wireless(self, device_id: str) -> list[dict[str, Any]]:
        """Fetch wireless access point info for a device."""
        wireless_path = self._matrix.format_path("device_wireless", device_id=device_id)
        if not wireless_path:
            return []

        data, _meta = await self.async_request("GET", wireless_path, allow_not_found=True)
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        return []

    async def async_get_device_ethernet_ports(self, device_id: str) -> list[dict[str, Any]] | None:
        """Fetch Ethernet port usage data for one device."""
        data, meta = await self.async_request(
            "GET",
            f"/devices/{device_id}/port-scan/",
            params={"type": "ethernet"},
            allow_not_found=True,
        )
        if data is None and not meta:
            return None

        resolved = await self._resolve_meta_channel(meta, data)
        return _extract_ethernet_ports(device_id, resolved)

    async def async_get_device_port_configurations(
        self, device_id: str
    ) -> list[dict[str, Any]] | None:
        """Fetch switch port configuration data for one device."""
        payload = {
            "device_id": _normalize_device_identifier(device_id),
            "endpoints": [{"path": "/ports_settings/config"}],
        }
        data, meta = await self.async_request(
            "POST",
            _DEVICE_CONFIGURATION_READ_PATH,
            json_body=payload,
            allow_not_found=True,
        )
        if data is None and not meta:
            return None

        resolved = await self._resolve_meta_channel(meta, data)
        return _extract_port_configurations(resolved)

    async def async_set_device_port_poe(self, device_id: str, port_id: str, enabled: bool) -> Any:
        """Enable or disable PoE on one configurable port."""
        payload = {
            "configuration": [
                {
                    "path": "/ports_settings/config/{id}",
                    "content_type": "application/json",
                    "method": "put",
                    "request_data": {"data": {"poe_enable": "1" if enabled else "0"}},
                    "query_parameters": [{"key": "id", "value": port_id}],
                    "device_id": [_normalize_device_identifier(device_id)],
                }
            ]
        }
        data, meta = await self.async_request(
            "POST",
            _DEVICE_CONFIGURATION_WRITE_PATH,
            json_body=payload,
        )
        return await self._resolve_meta_channel(meta, data)

    async def async_execute_device_action(
        self,
        action: str,
        device_ids: list[str],
    ) -> Any:
        """Execute a device action and resolve async-channel results when available."""
        payload = {
            "action": action,
            "device_id": [_normalize_device_identifier(device_id) for device_id in device_ids],
        }
        data, meta = await self.async_request("POST", _DEVICE_ACTIONS_PATH, json_body=payload)
        return await self._resolve_meta_channel(meta, data)

    async def async_reboot_device(self, device_id: str) -> Any:
        """Trigger a reboot for one RMS device."""
        return await self.async_execute_device_action("reboot", [device_id])

    async def async_get_states_for_devices(
        self,
        device_ids: list[str],
        *,
        max_per_cycle: int | None,
    ) -> dict[str, dict[str, Any]]:
        """Fetch state data with aggregate-first strategy and request-budget fallback."""
        if not device_ids:
            return {}

        aggregate_path = self._matrix.path_for("device_state_aggregate")
        if aggregate_path and self._aggregate_state_available is not False:
            params = {"ids": ",".join(device_ids)}
            try:
                data, meta = await self.async_request(
                    "GET", aggregate_path, params=params, allow_not_found=True
                )
                if data is None:
                    self._aggregate_state_available = False
                    return await self._async_per_device_state(
                        device_ids, max_per_cycle=max_per_cycle
                    )
                resolved = await self._resolve_meta_channel(meta, data)
                state_map = _coerce_state_map(resolved)
                if state_map:
                    self._aggregate_state_available = True
                    return state_map
                self._aggregate_state_available = False
            except RmsApiError:
                self._aggregate_state_available = False
                LOGGER.debug("Aggregate state endpoint failed; switching to per-device fallback")

        return await self._async_per_device_state(device_ids, max_per_cycle=max_per_cycle)

    async def _async_per_device_state(
        self,
        device_ids: list[str],
        *,
        max_per_cycle: int | None,
    ) -> dict[str, dict[str, Any]]:
        """Fetch per-device state while respecting budget via round-robin slicing."""
        if max_per_cycle is None or max_per_cycle <= 0:
            ids_for_cycle = list(device_ids)
        else:
            cursor = self._round_robin_cursor % len(device_ids)
            ordered = device_ids[cursor:] + device_ids[:cursor]
            ids_for_cycle = ordered[:max_per_cycle]
            self._round_robin_cursor = (cursor + len(ids_for_cycle)) % len(device_ids)

        results: dict[str, dict[str, Any]] = {}
        for device_id in ids_for_cycle:
            results[device_id] = await self.async_get_device_state(device_id)
        return results

    async def async_poll_status_channel(self, channel_id: str) -> dict[str, Any] | None:
        """Poll status channel endpoint directly."""
        url = f"{STATUS_BASE_URL}/channel/{channel_id}"
        data, _meta = await self.async_request("GET", url, absolute_url=True, allow_not_found=True)
        if isinstance(data, dict):
            return data
        return None

    async def async_request(
        self,
        method: str,
        path_or_url: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        absolute_url: bool = False,
        allow_not_found: bool = False,
    ) -> tuple[Any, dict[str, Any]]:
        """Perform RMS API request with retries and envelope parsing."""
        url = path_or_url if absolute_url else f"{API_BASE_URL}{path_or_url}"

        for attempt in range(_MAX_RETRIES + 1):
            self._increment_request_counter()
            response: ClientResponse | None = None
            try:
                response = await self._auth.async_request(
                    method,
                    url,
                    params=params,
                    json=json_body,
                    timeout=_DEFAULT_TIMEOUT,
                )
                if response.status in (401, 403):
                    raise ConfigEntryAuthFailed("Teltonika RMS auth failed or missing scopes")

                if allow_not_found and response.status == 404:
                    return None, {}

                if response.status in _RETRIABLE_STATUS_CODES and attempt < _MAX_RETRIES:
                    await _async_retry_sleep(response, attempt)
                    continue

                if response.status >= 400:
                    body = await _safe_json(response)
                    raise RmsApiError(f"RMS request failed ({response.status}): {body}")

                payload = await _safe_json(response)
                data, meta = _parse_envelope(payload)
                return data, meta
            except ConfigEntryAuthFailed:
                raise
            except ClientError as err:
                if attempt >= _MAX_RETRIES:
                    raise RmsApiError(f"RMS network error: {err}") from err
                await asyncio.sleep(_retry_delay(attempt))
            finally:
                if response is not None:
                    response.release()

        raise RmsApiError("Unexpected retry exhaustion")

    async def _resolve_meta_channel(self, meta: dict[str, Any], current_data: Any) -> Any:
        channel = meta.get("channel")
        if not isinstance(channel, str) or not channel:
            return current_data
        if self._status_channel_manager is None:
            return current_data
        channel_payload = await self._status_channel_manager.async_wait_for_channel(channel)
        if channel_payload is None:
            return current_data
        if isinstance(channel_payload, dict) and "data" in channel_payload:
            return channel_payload["data"]
        return channel_payload

    def _increment_request_counter(self) -> None:
        now = datetime.now(tz=UTC)
        if (now - self._request_window_start).days >= 30:
            self._request_counter = 0
            self._request_window_start = now
        self._request_counter += 1

    @staticmethod
    def estimate_max_calls_per_cycle(state_interval_seconds: int) -> int:
        """Estimate per-cycle call allowance from monthly budget."""
        cycles_per_month = max(int((30 * 24 * 3600) / max(1, state_interval_seconds)), 1)
        monthly_allowance = int(MAX_MONTHLY_REQUESTS * REQUEST_BUDGET_HEADROOM)
        return max(1, monthly_allowance // cycles_per_month)


async def _safe_json(response: ClientResponse) -> Any:
    try:
        return await response.json(content_type=None)
    except Exception:
        text = await response.text()
        return {"raw": text}


def _parse_envelope(payload: Any) -> tuple[Any, dict[str, Any]]:
    if not isinstance(payload, dict):
        return payload, {}
    if "success" not in payload:
        return payload, {}

    success = payload.get("success")
    if success is False:
        raise RmsApiError(str(payload.get("errors") or "RMS returned unsuccessful response"))
    return payload.get("data"), payload.get("meta") or {}


def _coerce_list(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        for key in ("items", "devices", "results", "rows"):
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def _coerce_state_map(data: Any) -> dict[str, dict[str, Any]]:
    if isinstance(data, dict):
        if "devices" in data and isinstance(data["devices"], list):
            return _coerce_state_map(data["devices"])
        if all(isinstance(value, dict) for value in data.values()):
            return {str(key): value for key, value in data.items()}
        if "id" in data:
            return {str(data["id"]): data}
    if isinstance(data, list):
        result: dict[str, dict[str, Any]] = {}
        for item in data:
            if not isinstance(item, dict):
                continue
            identifier = item.get("id") or item.get("device_id") or item.get("deviceId")
            if identifier is None:
                continue
            result[str(identifier)] = item
        return result
    return {}


def _has_next_page(batch: list[dict[str, Any]], meta: dict[str, Any], page_size: int) -> bool:
    pagination = meta.get("pagination")
    if isinstance(pagination, dict):
        if pagination.get("next_page"):
            return True
        if pagination.get("next"):
            return True
        current = pagination.get("page")
        pages = pagination.get("pages")
        if isinstance(current, int) and isinstance(pages, int):
            return current < pages
    return len(batch) >= page_size


def _retry_delay(attempt: int) -> float:
    return min(2**attempt, 30) + random.uniform(0.0, 0.5)


async def _async_retry_sleep(response: ClientResponse, attempt: int) -> None:
    retry_after = response.headers.get("Retry-After")
    if retry_after:
        try:
            delay = max(0.0, float(retry_after))
            await asyncio.sleep(delay)
            return
        except ValueError:
            pass
    await asyncio.sleep(_retry_delay(attempt))


def normalize_tags(raw: str) -> list[str]:
    """Split comma-delimited tags into list."""
    return [tag.strip() for tag in raw.split(",") if tag.strip()]


def estimate_monthly_requests(
    *,
    inventory_interval: int,
    state_interval: int,
    estimated_devices: int,
    aggregate_state_supported: bool,
) -> int:
    """Estimate monthly requests for options validation."""
    month_seconds = 30 * 24 * 3600
    inventory_calls = month_seconds / max(1, inventory_interval)
    if aggregate_state_supported:
        state_calls = month_seconds / max(1, state_interval)
    else:
        state_calls = (month_seconds / max(1, state_interval)) * max(1, estimated_devices)

    # Wireless endpoints are fetched per-device alongside state
    wireless_calls = (month_seconds / max(1, state_interval)) * max(1, estimated_devices)

    return int(inventory_calls + state_calls + wireless_calls)


def chunked(iterable: Iterable[str], size: int) -> list[list[str]]:
    """Chunk helper for APIs that accept grouped identifiers."""
    chunk: list[str] = []
    chunks: list[list[str]] = []
    for item in iterable:
        chunk.append(item)
        if len(chunk) >= size:
            chunks.append(chunk)
            chunk = []
    if chunk:
        chunks.append(chunk)
    return chunks


def _normalize_device_identifier(device_id: str) -> int | str:
    """Use integer identifiers for RMS actions when possible."""
    try:
        return int(device_id)
    except (TypeError, ValueError):
        return device_id


def _extract_ethernet_ports(device_id: str, payload: Any) -> list[dict[str, Any]] | None:
    """Extract Ethernet ports from direct or status-channel payloads."""
    if payload is None:
        return None

    items: Any = payload
    if isinstance(payload, dict):
        items = payload.get(
            str(device_id), payload.get(_normalize_device_identifier(device_id), payload)
        )

    if isinstance(items, list):
        for item in reversed(items):
            if not isinstance(item, dict):
                continue
            ports = item.get("ports")
            if isinstance(ports, list):
                return [port for port in ports if isinstance(port, dict)]
        return []

    if isinstance(items, dict):
        ports = items.get("ports")
        if isinstance(ports, list):
            return [port for port in ports if isinstance(port, dict)]
        return []

    return None


def _extract_port_configurations(payload: Any) -> list[dict[str, Any]] | None:
    """Extract switch port configuration rows from configurator status payloads."""
    if payload is None:
        return None

    if isinstance(payload, list):
        if payload and all(
            isinstance(item, dict) and isinstance(item.get("data"), list) for item in payload
        ):
            rows: list[dict[str, Any]] = []
            for item in payload:
                rows.extend(row for row in item["data"] if isinstance(row, dict))
            return rows
        return [item for item in payload if isinstance(item, dict)]

    if not isinstance(payload, dict):
        return None

    # Handle device-grouped configurator payloads (e.g. {"1791608": [{"status": "completed", "data": [{"data": [...]}]}]})
    if all(isinstance(v, list) for k, v in payload.items() if str(k).isdigit() or "-" in str(k)):
        for events in payload.values():
            if not isinstance(events, list) or not events:
                continue
            for event in reversed(events):
                if not isinstance(event, dict):
                    continue
                inner_data = event.get("data")
                if isinstance(inner_data, list):
                    for inner_item in inner_data:
                        if isinstance(inner_item, dict) and isinstance(
                            inner_item.get("data"), list
                        ):
                            return [row for row in inner_item["data"] if isinstance(row, dict)]

    items = payload.get("data")
    if not isinstance(items, list):
        return []

    for item in items:
        if not isinstance(item, dict):
            continue
        data = item.get("data")
        if isinstance(data, list):
            return [row for row in data if isinstance(row, dict)]

    return []
