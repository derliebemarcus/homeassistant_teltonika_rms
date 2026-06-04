"""Tests for the Teltonika RMS endpoint matrix logic."""

from __future__ import annotations

from pathlib import Path

from custom_components.teltonika_rms.endpoint_matrix import (
    EndpointMatrix,
    EndpointSpec,
    _extract_scopes,
    _is_aggregate_status_candidate,
    _pick_best,
    _polling_hint,
    load_endpoint_matrix,
)


def test_endpoint_matrix_basics() -> None:
    """Test basic functionality of EndpointMatrix and EndpointSpec."""
    spec = EndpointSpec("/test", ("scope1",), "safe")
    matrix = EndpointMatrix("src", {"test": spec})
    assert matrix.path_for("test") == "/test"
    assert matrix.path_for("missing") is None
    assert matrix.scopes_for("test") == ("scope1",)
    assert matrix.scopes_for("missing") == ()
    assert matrix.format_path("test", id="1") == "/test"

    spec2 = EndpointSpec("/test/{id}", ("scope2",), "safe")
    matrix2 = EndpointMatrix("src", {"test": spec2})
    assert matrix2.format_path("test", id="123") == "/test/123"
    assert matrix2.format_path("missing", id="123") is None


def test_extract_scopes() -> None:
    """Test extraction of OAuth2 scopes from OpenAPI operations."""
    global_sec = [{"oauth": ["global"]}]
    op = {"security": [{"oauth": ["local"]}]}
    assert _extract_scopes(op, global_sec) == ("local",)

    op_no_sec = {}
    assert _extract_scopes(op_no_sec, global_sec) == ("global",)

    assert _extract_scopes({"security": "invalid"}, global_sec) == ()


def test_is_aggregate_status_candidate() -> None:
    """Test detection of aggregate status endpoints."""
    assert _is_aggregate_status_candidate("/devices/status") is True
    assert _is_aggregate_status_candidate("/devices/{id}/status") is False
    assert _is_aggregate_status_candidate("/other") is False
    assert _is_aggregate_status_candidate("/devices/connect/status") is False


def test_polling_hint() -> None:
    """Test polling hint generation based on path."""
    assert _polling_hint("/location") == "high-cost"
    assert _polling_hint("/status") == "async-channel"
    assert _polling_hint("/info") == "safe"


def test_pick_best() -> None:
    """Test selection of the best endpoint candidate."""
    c1 = EndpointSpec("/v3/a", (), "safe")
    c2 = EndpointSpec("/v2/a", (), "safe")
    c3 = EndpointSpec("/v3/abc", (), "safe")
    assert _pick_best([c2, c1, c3]) == c1
    assert _pick_best([]) is None


def test_load_endpoint_matrix_fallback(tmp_path: Path) -> None:
    """Test fallback logic when loading endpoint matrix."""
    # Test with None spec_path
    matrix = load_endpoint_matrix(None)
    assert "devices_list" in matrix.endpoints

    # Test with non-existent path
    matrix = load_endpoint_matrix(str(tmp_path / "missing.yaml"))
    assert "devices_list" in matrix.endpoints

    # Test with invalid yaml
    invalid_yaml = tmp_path / "invalid.yaml"
    invalid_yaml.write_text("!!binary", encoding="utf-8")
    matrix = load_endpoint_matrix(str(invalid_yaml))
    assert "devices_list" in matrix.endpoints

    # Test with invalid shape (not a dict)
    not_a_dict = tmp_path / "list.yaml"
    not_a_dict.write_text("- item", encoding="utf-8")
    matrix = load_endpoint_matrix(str(not_a_dict))
    assert "devices_list" in matrix.endpoints


def test_load_endpoint_matrix_dynamic(tmp_path: Path) -> None:
    """Test dynamic loading of endpoint matrix from OpenAPI spec."""
    spec_file = tmp_path / "spec.yaml"
    spec_file.write_text(
        """
paths:
  /v3/devices:
    get:
      security:
        - oauth2: [read]
  /v3/devices/{id}/status:
    get:
      security:
        - oauth2: [read_status]
  /v3/devices/{id}/location:
    get:
      security: []
  /v3/devices/{id}:
    get:
      security: []
  /v3/devices/status:
    get:
      security: []
security:
  - oauth2: [global]
""",
        encoding="utf-8",
    )
    matrix = load_endpoint_matrix(str(spec_file))
    assert matrix.endpoints["devices_list"].path == "/v3/devices"
    assert matrix.endpoints["device_state_single"].path == "/v3/devices/{id}/status"
    assert matrix.endpoints["device_location"].path == "/v3/devices/{id}/location"
    assert matrix.endpoints["device_detail"].path == "/v3/devices/{id}"
    assert matrix.endpoints["device_state_aggregate"].path == "/v3/devices/status"


def test_matrix_from_openapi_invalid_paths() -> None:
    """Test _matrix_from_openapi with invalid path data."""
    from custom_components.teltonika_rms.endpoint_matrix import _matrix_from_openapi

    frozen = load_endpoint_matrix(None)
    assert _matrix_from_openapi({"paths": "invalid"}, frozen) == frozen.endpoints

    from custom_components.teltonika_rms.endpoint_matrix import _categorize_endpoint

    candidates = {"devices_list": []}
    _categorize_endpoint("/other", {}, [], candidates)
    assert len(candidates["devices_list"]) == 0


def test_endpoint_matrix_malformed_spec(tmp_path: Path) -> None:
    """Test endpoint matrix loading with malformed spec data."""
    from custom_components.teltonika_rms.endpoint_matrix import load_endpoint_matrix

    spec_file = tmp_path / "malformed.yaml"
    # This triggers the 'not isinstance(raw_methods, dict)' continue in line 111
    spec_file.write_text("paths:\n  /v3/devices: not_a_dict", encoding="utf-8")
    matrix = load_endpoint_matrix(str(spec_file))
    assert "devices_list" in matrix.endpoints

    # This triggers the 'not isinstance(operation, dict)' continue in line 114
    spec_file.write_text("paths:\n  /v3/devices:\n    get: not_a_dict", encoding="utf-8")
    matrix = load_endpoint_matrix(str(spec_file))
    assert "devices_list" in matrix.endpoints
