"""OpenAPI-compatible device inventory client behavior."""

from __future__ import annotations

import logging
from typing import Any

from .api import RmsApiClient, _coerce_list, _validate_contract_list
from .exceptions import RmsApiError
from .models_api import DeviceListResponse

LOGGER = logging.getLogger(__name__)

_RMS_STATUS_MAP: dict[int | None, str] = {
    None: "offline",
    0: "offline",
    1: "online",
    2: "pending",
}


class SpecCompatibleRmsApiClient(RmsApiClient):
    """RMS API client matching the current device inventory specification."""

    async def async_list_devices(
        self,
        *,
        tags: list[str] | None = None,
        device_status: str | None = None,
        page_size: int = 50,
        max_pages: int | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch all devices using documented limit/offset pagination."""
        path = self.endpoint_matrix.path_for("devices_list")
        if not path:
            raise RmsApiError("No devices list endpoint configured")

        offset = 0
        page_count = 0
        devices: list[dict[str, Any]] = []
        seen_records: set[str] = set()
        previous_page_signature: tuple[str, ...] | None = None

        while max_pages is None or page_count < max_pages:
            params = _device_list_params(page_size, offset, tags, device_status)
            data, meta = await self.async_request("GET", path, params=params)
            raw_batch = _coerce_list(data)
            batch = [_normalize_device_record(item) for item in raw_batch]
            _validate_contract_list(batch, "devices_list", DeviceListResponse)

            page_signature = tuple(_device_identity(item) for item in batch)
            if page_signature and page_signature == previous_page_signature:
                LOGGER.warning(
                    "RMS repeated the same device page at offset %s; stopping pagination",
                    offset,
                )
                break
            previous_page_signature = page_signature

            _append_unseen_devices(devices, batch, seen_records)

            page_count += 1
            response_count = len(raw_batch)
            if not _has_next_offset_page(response_count, meta, offset, page_size):
                break
            offset += response_count

        return devices

    async def async_get_device_state(self, device_id: str) -> dict[str, Any]:
        """Normalize documented numeric status values returned by device detail."""
        return _normalize_device_record(await super().async_get_device_state(device_id))


def _device_list_params(
    page_size: int,
    offset: int,
    tags: list[str] | None,
    device_status: str | None,
) -> dict[str, Any]:
    """Build device-list query parameters while preserving legacy filters."""
    params: dict[str, Any] = {"limit": page_size, "offset": offset}
    if tags:
        # The current OpenAPI contract exposes tag_id rather than tag names.
        # Preserve the existing option until that migration is handled separately.
        params["tags"] = ",".join(tags)
    if device_status:
        params["status"] = device_status
    return params


def _append_unseen_devices(
    devices: list[dict[str, Any]],
    batch: list[dict[str, Any]],
    seen_records: set[str],
) -> None:
    """Append only records not already returned by an earlier page."""
    for item in batch:
        identity = _device_identity(item)
        if identity in seen_records:
            continue
        seen_records.add(identity)
        devices.append(item)


def _normalize_device_record(record: dict[str, Any]) -> dict[str, Any]:
    """Normalize RMS status codes without discarding unknown future values."""
    normalized = dict(record)
    if "status" in normalized and normalized["status"] in _RMS_STATUS_MAP:
        normalized["status"] = _RMS_STATUS_MAP[normalized["status"]]
    return normalized


def _device_identity(record: dict[str, Any]) -> str:
    """Build a stable identity for de-duplication and repeated-page detection."""
    for key in ("id", "device_id", "serial", "imei", "mac"):
        value = record.get(key)
        if value not in (None, ""):
            return f"{key}:{value}"
    return repr(sorted(record.items(), key=lambda item: str(item[0])))


def _has_next_offset_page(
    response_count: int,
    meta: dict[str, Any],
    offset: int,
    page_size: int,
) -> bool:
    """Return whether another offset page exists according to RMS metadata."""
    if response_count == 0:
        return False

    total = meta.get("total")
    if isinstance(total, int):
        return offset + response_count < total
    return response_count >= page_size
