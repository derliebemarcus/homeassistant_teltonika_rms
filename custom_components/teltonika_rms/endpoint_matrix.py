"""OpenAPI-driven endpoint matrix support for Teltonika RMS."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

LOGGER = logging.getLogger(__name__)

_FROZEN_MATRIX_FILE = "endpoint_matrix_frozen.json"


@dataclass(slots=True, frozen=True)
class EndpointSpec:
    """A normalized endpoint specification entry."""

    path: str
    scopes: tuple[str, ...]
    polling: str


@dataclass(slots=True, frozen=True)
class EndpointMatrix:
    """Resolved endpoint matrix used by the integration."""

    source: str
    endpoints: dict[str, EndpointSpec]

    def path_for(self, key: str) -> str | None:
        """Get the path for a given endpoint key."""
        spec = self.endpoints.get(key)
        return spec.path if spec else None

    def scopes_for(self, key: str) -> tuple[str, ...]:
        """Get the scopes for a given endpoint key."""
        spec = self.endpoints.get(key)
        return spec.scopes if spec else ()

    def format_path(self, key: str, **params: str) -> str | None:
        """Format a path by replacing URL parameters."""
        path = self.path_for(key)
        if path is None:
            return None
        for name, value in params.items():
            path = path.replace(f"{{{name}}}", value)
        return path


def load_endpoint_matrix(spec_path: str | None) -> EndpointMatrix:
    """Load endpoint matrix from OpenAPI spec with frozen fallback."""
    frozen = _load_frozen_matrix()
    if not spec_path:
        return frozen

    spec_file = Path(spec_path)
    if not spec_file.exists():
        LOGGER.debug("RMS compiled spec not found at %s, using frozen matrix", spec_path)
        return frozen

    try:
        spec = yaml.safe_load(spec_file.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as err:
        LOGGER.warning("Failed to load RMS compiled spec at %s: %s", spec_path, err)
        return frozen

    if not isinstance(spec, dict):
        LOGGER.warning("RMS compiled spec has invalid shape, using frozen matrix")
        return frozen

    dynamic = _matrix_from_openapi(spec, frozen)
    return EndpointMatrix(source=spec_path, endpoints=dynamic)


def _load_frozen_matrix() -> EndpointMatrix:
    data = json.loads(Path(__file__).with_name(_FROZEN_MATRIX_FILE).read_text(encoding="utf-8"))
    endpoints: dict[str, EndpointSpec] = {}
    for key, raw in data["endpoints"].items():
        endpoints[key] = EndpointSpec(
            path=raw["path"],
            scopes=tuple(raw.get("scopes", [])),
            polling=raw.get("polling", "safe"),
        )
    return EndpointMatrix(
        source=str(Path(__file__).with_name(_FROZEN_MATRIX_FILE)), endpoints=endpoints
    )


def _matrix_from_openapi(spec: dict[str, Any], frozen: EndpointMatrix) -> dict[str, EndpointSpec]:
    """Build endpoint matrix from OpenAPI spec, using frozen matrix as fallback."""
    paths = spec.get("paths")
    if not isinstance(paths, dict):
        return frozen.endpoints

    security = spec.get("security", [])
    candidates: dict[str, list[EndpointSpec]] = {
        "devices_list": [],
        "device_detail": [],
        "device_state_aggregate": [],
        "device_state_single": [],
        "device_location": [],
    }

    for path, raw_methods in paths.items():
        if not isinstance(path, str) or not isinstance(raw_methods, dict):
            continue
        operation = raw_methods.get("get")
        if not isinstance(operation, dict):
            continue

        _categorize_endpoint(path, operation, security, candidates)

    resolved: dict[str, EndpointSpec] = {}
    for key, frozen_spec in frozen.endpoints.items():
        picked = _pick_best(candidates.get(key, []))
        resolved[key] = picked or frozen_spec

    return resolved


def _categorize_endpoint(
    path: str,
    operation: dict[str, Any],
    global_security: list[Any],
    candidates: dict[str, list[EndpointSpec]],
) -> None:
    """Categorize an OpenAPI operation into potential endpoint candidates."""
    lower_path = path.lower()
    if "devices" not in lower_path:
        return

    scopes = _extract_scopes(operation, global_security)
    spec = EndpointSpec(path=path, scopes=scopes, polling=_polling_hint(path))

    if re.search(r"/devices/?$", lower_path):
        candidates["devices_list"].append(spec)
    elif re.search(r"/devices/\{[^}]+\}/status/?$", lower_path):
        candidates["device_state_single"].append(spec)
    elif re.search(r"/devices/\{[^}]+\}/location/?$", lower_path):
        candidates["device_location"].append(spec)
    elif _is_aggregate_status_candidate(path):
        candidates["device_state_aggregate"].append(spec)
    elif re.search(r"/devices/\{[^}]+\}/?$", lower_path):
        candidates["device_detail"].append(spec)


def _extract_scopes(operation: dict[str, Any], global_security: list[Any]) -> tuple[str, ...]:
    """Extract required OAuth2 scopes from an operation or global security definition."""
    security = operation.get("security", global_security)
    if not isinstance(security, list):
        return ()

    scopes: list[str] = []
    seen: set[str] = set()

    # Flatten nested security structure to reduce complexity
    raw_scope_items: list[list[Any]] = []
    for item in security:
        if isinstance(item, dict):
            raw_scope_items.extend(v for v in item.values() if isinstance(v, list))

    for scope_list in raw_scope_items:
        for s in scope_list:
            if isinstance(s, str) and s not in seen:
                seen.add(s)
                scopes.append(s)

    return tuple(scopes)


def _polling_hint(path: str) -> str:
    lower = path.lower()
    if "location" in lower:
        return "high-cost"
    if "status" in lower:
        return "async-channel"
    return "safe"


def _pick_best(candidates: list[EndpointSpec]) -> EndpointSpec | None:
    if not candidates:
        return None
    return sorted(candidates, key=_endpoint_sort_key)[0]


def _endpoint_sort_key(spec: EndpointSpec) -> tuple[int, int]:
    starts_v3 = 0 if spec.path.startswith("/v3/") else 1
    return starts_v3, len(spec.path)


def _is_aggregate_status_candidate(path: str) -> bool:
    lower = path.lower()
    if "{" in lower:
        return False
    if "devices" not in lower:
        return False
    return lower.endswith("/status") and "/connect/" not in lower
