"""API models for Teltonika RMS."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RmsApiBaseModel(BaseModel):
    """Base model for RMS API responses."""

    model_config = ConfigDict(extra="ignore")


class DeviceListItem(RmsApiBaseModel):
    """Represents an item in the device list."""

    id: str | int | None = None
    name: str | None = None
    serial: str | None = None
    mac: str | None = None
    model_name: str | None = Field(None, alias="model")
    status: int | str | None = None


class DeviceListResponse(RmsApiBaseModel):
    """Represents the device list response."""

    data: list[DeviceListItem]


class DeviceDetail(RmsApiBaseModel):
    """Represents detailed device information."""

    id: str | int | None = None
    serial: str | None = None
    mac: str | None = None
    name: str | None = None
    model_name: str | None = Field(None, alias="model")
    status: int | str | None = None


class DeviceDetailResponse(RmsApiBaseModel):
    """Represents the device detail response."""

    data: DeviceDetail


class DeviceState(RmsApiBaseModel):
    """Represents the current state of a device."""

    id: str | int | None = None
    online: bool | None = None
    last_communication: str | None = None
    wan_ip: str | None = None
    mobile_signal: int | None = None
    temperature: float | None = None


class DeviceStateResponse(RmsApiBaseModel):
    """Represents the device state response."""

    data: DeviceState | dict[str, Any] | list[Any]
