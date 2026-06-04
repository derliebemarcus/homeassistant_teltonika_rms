"""Socket.IO channel handling with HTTP polling fallback."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from .const import STATUS_BASE_URL

LOGGER = logging.getLogger(__name__)

try:
    import socketio
except ImportError:  # pragma: no cover - guarded at runtime
    socketio = None


class RmsStatusChannelManager:
    """Wait for channel completion using Socket.IO, then HTTP fallback."""

    def __init__(self, api_client: Any) -> None:
        self._api_client = api_client

    async def async_wait_for_channel(
        self,
        channel_id: str,
        *,
        timeout_seconds: int = 120,
    ) -> dict[str, Any] | None:
        """Wait for channel result; fallback to polling when socket path fails."""
        if not channel_id:
            return None

        socket_budget = min(20, timeout_seconds)
        payload = await self._async_wait_via_socket(channel_id, socket_budget)
        if payload is not None:
            return payload
        return await self._async_wait_via_polling(channel_id, timeout_seconds)

    async def _async_wait_via_socket(
        self,
        channel_id: str,
        timeout_seconds: int,
    ) -> dict[str, Any] | None:
        """Wait for channel result via Socket.IO."""
        if socketio is None:
            return None

        token = await self._api_client.async_get_access_token()
        if not token:
            return None

        client = socketio.AsyncClient(reconnection=False, logger=False, engineio_logger=False)
        future: asyncio.Future[dict[str, Any] | None] = asyncio.get_running_loop().create_future()

        async def _handle(payload: Any) -> None:
            message = _coerce_payload(payload)
            if message is None:
                return
            msg_channel = message.get("channel") or message.get("id")
            if msg_channel and str(msg_channel) != channel_id:
                return
            if _is_terminal(message) and not future.done():
                future.set_result(message)

        client.on("message")(_handle)
        client.on("status")(_handle)
        client.on(channel_id)(_handle)

        return await self._async_connect_and_subscribe(
            client,
            channel_id,
            token,
            {"timeout": timeout_seconds, "future": future},
        )

    async def _async_connect_and_subscribe(
        self,
        client: socketio.AsyncClient,
        channel_id: str,
        token: str,
        wait_options: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Connect to the status socket and subscribe to the channel."""
        connect_url = f"{STATUS_BASE_URL}?token={token}"
        try:
            await client.connect(
                connect_url,
                transports=["websocket", "polling"],
                wait_timeout=10,
                auth={"token": token},
                headers={"Authorization": f"Bearer {token}"},
            )
            try:
                await client.emit("subscribe", {"channel": channel_id})
            except Exception:  # pylint: disable=broad-except
                LOGGER.debug("RMS socket subscribe event not acknowledged for %s", channel_id)

            return await asyncio.wait_for(wait_options["future"], timeout=wait_options["timeout"])
        except Exception as err:  # pylint: disable=broad-except
            LOGGER.debug("RMS status socket fallback for %s: %s", channel_id, err)
            return None
        finally:
            if client.connected:
                await client.disconnect()

    async def _async_wait_via_polling(
        self,
        channel_id: str,
        timeout_seconds: int,
    ) -> dict[str, Any] | None:
        deadline = datetime.now(tz=UTC) + timedelta(seconds=timeout_seconds)
        while datetime.now(tz=UTC) < deadline:
            payload = await self._api_client.async_poll_status_channel(channel_id)
            if payload and _is_terminal(payload):
                return cast(dict[str, Any], payload)
            await asyncio.sleep(2)
        return None


def _coerce_payload(payload: Any) -> dict[str, Any] | None:
    if isinstance(payload, dict):
        return payload
    return None


def _is_terminal(payload: dict[str, Any]) -> bool:
    """Check if the payload represents a terminal state (completion or error)."""
    if payload.get("completed") is True:
        return True

    # Check root-level keys
    if _has_terminal_status(payload):
        return True

    # Check device-ID grouped payloads (e.g. from configurator or port-scan)
    return _is_device_grouped_terminal(payload)


def _has_terminal_status(data: dict[str, Any]) -> bool:
    """Check if a dictionary contains a terminal status or response_state."""
    for key in ("status", "response_state"):
        status = data.get(key)
        if isinstance(status, str) and status.lower() in {
            "completed",
            "done",
            "finished",
            "failed",
            "error",
            "expired",
            "cancelled",
            "success",
        }:
            return True
    return False


def _is_device_grouped_terminal(payload: dict[str, Any]) -> bool:
    """Check if device-ID grouped payloads contain a terminal event."""
    # The payload is a dict mapping device IDs to lists of events
    is_device_map = all(
        isinstance(v, list) for k, v in payload.items() if str(k).isdigit() or "-" in str(k)
    )
    if not is_device_map:
        return False

    for events in payload.values():
        if not isinstance(events, list) or not events:
            continue
        last_event = events[-1]
        if isinstance(last_event, dict) and _has_terminal_status(last_event):
            return True

    return False
