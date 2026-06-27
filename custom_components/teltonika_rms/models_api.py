"""API models for Teltonika RMS."""

from __future__ import annotations

from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RmsApiBaseModel(BaseModel):
    """Base model for RMS API responses."""

    model_config = ConfigDict(extra="ignore")


class IdentifiedDevice(RmsApiBaseModel):
    """Base for device payloads that need a stable integration identifier."""

    id: str | int | None = None
    serial: str | None = None
    imei: str | None = None
    mac: str | None = None

    @model_validator(mode="after")
    def validate_identifier(self) -> Self:
        """Require at least one identifier that Home Assistant can persist."""
        if all(
            value in (None, "") for value in (self.id, self.serial, self.imei, self.mac)
        ):
            raise ValueError("device payload has no stable identifier")
        return self


class DeviceListItem(IdentifiedDevice):
    """Represents an item in the device list."""

    name: str | None = None
    model_name: str | None = Field(None, alias="model")
    status: int | str | None = None


class DeviceListResponse(RmsApiBaseModel):
    """Represents the device list response."""

    data: list[DeviceListItem]


class DeviceDetail(IdentifiedDevice):
    """Represents detailed device information."""

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
