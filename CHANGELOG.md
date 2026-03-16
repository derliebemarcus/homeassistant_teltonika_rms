# Changelog

All notable changes to this project are documented in this file.

## 0.9.0-beta3 - 2026-03-16

### New Features

- Added support for switching ethernet port states on and off.
- Added support for changing PoE capability.

### Improvements

- None.

### Changes

- None.

### Bugfixes

- None.


## 0.9.0-beta2 - 2026-03-15

### New Features

- Automatically update floating tags ('stable' or 'beta') based on the published release type.

### Improvements

- Clarified supported devices in the README.

### Changes

- None.

### Bugfixes

- None.

## 0.9.0-beta1 - 2026-03-15

### New Features

- Published a new beta version.

### Improvements

- None.

### Changes

- None.

### Bugfixes

- None.

## 0.9.0-beta0 - 2026-03-14

### New Features

- Introduced beta versions (pre-releases) in addition to stable releases.

### Improvements

- Updated documentation to clarify that while the plugin aims to support all Teltonika devices, it has been specifically tested and validated with the RUTX50, TAP200, and TSW202.

### Changes

- None.

### Bugfixes

- None.

## 0.8.8 - 2026-03-14

### New Features

- None.

### Improvements

- Temperature sensor values are now exposed as `float` type and assigned the `MEASUREMENT` state class for better graph tracking.
- SIM slot values are now exposed natively as integer.

### Changes

- None.

### Bugfixes

- Fixed wireless `clients_count` missing for Access Points (TAP200) and Routers (RUTX50) by parsing the newly supported `/devices/{device_id}/wireless` endpoint.
- Fixed an issue where `used_ethernet_ports` and `used_ethernet_port_names` did not populate for certain switches like the TSW202 due to an unhandled API wrapper payload format.
- Fixed PoE switches failing to populate for devices like the TSW202.

## 0.8.7 - 2026-03-14

### New Features

- None.

### Improvements

- None.

### Changes

- None.

### Bugfixes

- Reverted the dependency pinning of `orjson` and `PyJWT` introduced in `0.8.6` because they directly conflicted with the strict dependencies of Home Assistant 2026.3.0 and 2026.3.1. These vulnerability alerts are upstream within Home Assistant Core and will be fixed when the next core version ships them.

## 0.8.6 - 2026-03-14

### New Features

- None.

### Improvements

- None.

### Changes

- None.

### Bugfixes

- Fixed security vulnerabilities by pinning `orjson>=3.11.6` (CVE-2025-67221) and `PyJWT>=2.12.0` (CVE-2026-32597) in the integration dependencies.

## 0.8.5 - 2026-03-14

### New Features

- None.

### Improvements

- Modified the endpoint matrix generator tool to correctly preserve default endpoint scopes when parsing OpenAPI definitions that use `BearerAuth` without explicitly redefining scope sets per path.

### Changes

- None.

### Bugfixes

- Fixed the `endpoint_matrix_frozen.json` scope generation so that PAT users with `devices:read` grants are correctly authorized when using generated matrix files.

## 0.8.4 - 2026-03-14

### New Features

- None.

### Improvements

- Shipped the runtime `python-socketio` dependency at `5.16.1`, so installations now include the latest Dependabot-delivered security and maintenance updates instead of staying on the older `5.14.0` floor.
- Updated QA workflow dependencies alongside the release so repository checks run on the newer `pytest-cov`, `actionlint`, `actions/github-script`, and `actions/upload-artifact` revisions already merged on `main`.

### Changes

- Published a follow-up patch release after the Dependabot merges so the released integration version matches the security-relevant dependency state on `main`.

### Bugfixes

- Fixed the release packaging gap where merged security updates on `main` had not yet been rolled into a tagged Home Assistant release.

## 0.8.3 - 2026-03-14

### New Features

- None.

### Improvements

- Upgraded the bundled `python-socketio` dependency to `5.14.0`, removing a known vulnerability and bringing the shipped integration dependency set back into compliance with the repository security gates.

### Changes

- Tightened the release workflow shell comparison so `actionlint` and ShellCheck can validate release publishing end to end without false-positive script failures.

### Bugfixes

- Fixed the GitHub Actions release workflow lint failure caused by an inline tag comparison pattern that ShellCheck flagged as invalid.
- Fixed the dependency-audit failure by shipping a non-vulnerable `python-socketio` version in both runtime and development dependency manifests.

## 0.8.2 - 2026-03-13

### New Features

- None.

### Improvements

- Firmware update entities now tolerate more RMS firmware metadata shapes, including string-based `current`, `latest`, and `stable` values returned by some devices.

### Changes

- Update entity discovery now also reacts to state coordinator refreshes, not only inventory refreshes.
- RMS status-channel completion detection now accepts both `status: completed` and `response_state: completed`.

### Bugfixes

- Fixed PoE switch discovery when RMS configurator status payloads finish with `completed` instead of `success`, so PoE switch entities can be created after the background port-configuration refresh finishes.
- Fixed missing firmware update entities for devices that expose firmware metadata in alternative RMS shapes that were previously not normalized into the integration model.

## 0.8.1 - 2026-03-13

### New Features

- None.

### Improvements

- Optional Ethernet port scan and PoE port-configuration refreshes now start in the background after setup, so the core integration becomes available immediately even when RMS status channels are slow or the socket falls back to HTTP polling.

### Changes

- Initialized optional port-scan and port-configuration coordinators with empty data so entity setup stays safe before the first background refresh completes.

### Bugfixes

- Fixed a setup-path regression in `0.8.0` where Home Assistant could remain stuck on `Loading next step for Teltonika RMS` while waiting for optional port-scan or port-configuration first refreshes to finish.

## 0.8.0 - 2026-03-13

### New Features

- Added PoE `switch` entities for configurable switch ports, so supported Teltonika switch ports can now be turned on and off directly from Home Assistant.

### Improvements

- PoE switches are created only for ports where RMS actually exposes a `poe_enable` setting, so non-PoE ports such as SFP uplinks do not create misleading entities.
- PoE state is now read from the RMS configurator port configuration endpoint, which keeps Home Assistant aligned with the actual current device configuration.

### Changes

- Expanded the requested OAuth2 scopes to include:
  - `device_configurations:read`
  - `device_configurations:write`
- Added a dedicated low-frequency port-configuration coordinator alongside the existing Ethernet port-scan coordinator.
- Updated README scope guidance and feature list to document PoE switches and their required permissions.

### Bugfixes

- None.

## 0.7.2 - 2026-03-13

### New Features

- None.

### Improvements

- OAuth2 and PAT scope guidance now matches the actual RMS permission needed for Ethernet port scan sensors.

### Changes

- Added `device_remote_access:read` to the requested OAuth scope set for Teltonika RMS.
- Updated runtime warnings and README scope instructions so Ethernet port scan sensors point to `device_remote_access:read` instead of the incorrect `device_actions:read`.

### Bugfixes

- Fixed the Ethernet port scan permission guidance after live validation showed that `device_actions:read` alone still returns `403` for `/devices/{id}/port-scan/`.

## 0.7.1 - 2026-03-13

### New Features

- None.

### Improvements

- Missing `device_actions:read` permission for the optional Ethernet port scan no longer blocks the whole integration from starting after upgrade.

### Changes

- None.

### Bugfixes

- Fixed startup behavior so Ethernet port scan refresh degrades gracefully to `no Ethernet entities` when the scope is missing, instead of repeatedly forcing Home Assistant into reconnect/reauth behavior.

## 0.7.0 - 2026-03-13

### New Features

- Added a read-only firmware `update` entity per device so Home Assistant now shows the installed firmware alongside the latest version RMS reports for that device.
- Added Ethernet diagnostics sensors that expose how many Ethernet ports are currently in use and which named ports have active downstream devices.

### Improvements

- Reused RMS inventory firmware metadata directly for update availability, so firmware visibility works without extra file-catalog setup.
- Added a dedicated low-frequency port-scan coordinator so Ethernet visibility is available without materially increasing the RMS request budget.

### Changes

- Extended the integration setup and runtime bundle with an `update` platform and an Ethernet port-scan coordinator.
- Updated README scope guidance so `device_actions:read` is called out explicitly for Ethernet port scan sensors.

### Bugfixes

- None.

## 0.6.1 - 2026-03-13

### New Features

- None.

### Improvements

- Changed router uptime presentation from raw seconds to days, making long-running devices easier to read directly in Home Assistant.

### Changes

- None.

### Bugfixes

- Fixed the reboot action to use the correct RMS endpoint `/devices/actions` instead of the invalid versioned path.

## 0.6.0 - 2026-03-13

### New Features

- Added new optional RMS sensors that are created only when the API actually provides the value:
  - clients count
  - router uptime
  - temperature
  - signal strength
  - WAN state
  - connection state
  - connection type
  - SIM slot
- Added a per-device reboot button so supported devices can be restarted directly from Home Assistant.
- Added representative RMS contract fixtures derived from the compiled API schema to validate payload handling against more realistic examples.

### Improvements

- Expanded diagnostics output with auth mode, aggregate-state availability, and monthly request estimate to make support cases easier to debug.
- Added repository quality gates for commit-message format and release-note structure so project rules are enforced in CI, not only by local hooks.
- Added issue templates, a pull-request template, and maintainer contribution guidance to make incoming changes and bug reports more actionable.

### Changes

- Updated README to document the new RMS sensors and clarify that they are only exposed when RMS provides the underlying value.
- Updated OAuth2/PAT scope documentation to include `device_actions:write` for the reboot button.
- Added repository-level governance tooling:
  - `tools/check_commit_messages.py`
  - `tools/check_release_notes.py`
  - `.github/workflows/quality.yml`

### Bugfixes

- Fixed OAuth2 reauthentication flow so it correctly restarts implementation selection instead of calling a non-existent superclass reauth method.

## 0.5.2 - 2026-03-13

### New Features

- None.

### Improvements

- Added repository-level `icon.png` compatibility branding alongside `brand/icon.png` so HACS can resolve the integration icon more reliably.
- Raised automated test coverage to 97%, giving stronger regression protection for config flow, coordinators, API fallback paths, and repository metadata.
- Added enforcement for structured release notes so GitHub releases consistently highlight product impact first and maintenance/testing items afterwards.

### Changes

- Standardized README badges so all top-level badges use a consistent `for-the-badge` height and styling.
- Enforced categorized commit-message bodies through a `commit-msg` hook:
  - `add:`
  - `change:`
  - `deprecate:`
  - `remove:`
  - `fix:`

### Bugfixes

- Fixed OAuth2 reauthentication to restart implementation selection correctly instead of calling a non-existent superclass reauth method.
- Replaced the unstable dynamic license badge with a stable MIT badge so the repository page no longer shows `repo not found`.

## 0.5.1 - 2026-03-13

### New Features

- None.

### Improvements

- Increased automated test coverage to 94% across the integration codebase, improving regression protection for authentication, coordinator updates, and status-channel handling.
- Expanded runtime coverage for RMS API retries, pagination, aggregate-state fallback, and channel resolution so remote-device state handling is validated more thoroughly.
- Expanded unit coverage for endpoint-matrix parsing and device normalization helpers, reducing the chance of API-schema or payload-shape regressions.

### Changes

- Kept the Coveralls workflow aligned with the current HA/runtime dependency floor so published coverage stays current and comparable across releases.

### Bugfixes

- None.

## 0.5.0 - 2026-03-13

- Added README badges for HACS, GitHub releases, license, and downloads.
- Expanded OAuth setup documentation:
  - `my.home-assistant.io` link requirement is now documented explicitly.
  - RMS OAuth redirect URL is documented as `https://my.home-assistant.io/redirect/oauth`.
  - Post-credential setup steps in Home Assistant are documented more clearly.
- Simplified integration branding assets to a single local icon:
  - kept `brand/icon.png`
  - removed unused logo and dark-variant files
- Raised the minimum supported Home Assistant version to `2026.3.0`:
  - aligns with local brand icon support for custom integrations
  - mirrored in both `manifest.json` and `hacs.json`
- Added a metadata consistency test to keep `manifest.json` and `hacs.json` aligned.

## 0.4.0 - 2026-03-11

- Updated integration metadata documentation URL:
  - Home Assistant "help/documentation" link now points to the project repository:
    - `https://github.com/derliebemarcus/teltonika_rms`

## 0.3.1 - 2026-03-11

- Refined test execution split:
  - Added `tests/unit/` for pure unit tests that run without Home Assistant dependencies.
  - Added `tests/ha/` for Home Assistant-dependent tests.
- Updated `pre-commit` hook behavior:
  - Without `homeassistant` installed: runs all unit tests.
  - With `homeassistant` installed: runs unit + HA test suites.
  - Keeps `--maxfail=0` and blocks commit only after all selected tests completed.
- Added HA-test marker configuration in `pytest.ini`.
- Refactored integration module imports in `__init__.py` to avoid importing heavy HA/runtime dependencies at module import time, improving testability outside HA.

## 0.3.0 - 2026-03-11

- Added versioned repository Git hooks (`.githooks`):
  - `pre-commit` runs all tests, prints per-test name/duration/result, and blocks commit on failures.
  - `pre-push` enforces an existing release tag `v<manifest.version>`.
- Added tooling scripts:
  - `tools/install_git_hooks.sh`
  - `tools/print_pytest_summary.py`
  - `tools/create_version_tag.sh`
- Extended location normalization to detect more coordinate formats (`lat/lng`, `lon`, GeoJSON coordinate arrays, coordinate strings).
- Device tracker now exposes explicit location attributes:
  - `location_detail`
  - `coordinates`
  - `google_maps_url`

## 0.2.0 - 2026-03-11

- Added dual authentication modes:
  - OAuth2 (Authorization Code + PKCE)
  - Personal Access Token (PAT)
- Added PAT reauthentication flow.
- Added diagnostics endpoint with token redaction.
- Added HACS metadata and Python-specific `.gitignore`.
- Switched `last_seen` from `datetime` entity to `sensor` timestamp entity.
- Ensured device tracker entities are only created when valid coordinates exist.
- Added and localized translation files for EU languages and additional requested languages.
- Expanded README:
  - Installation via HACS and manual copy
  - Configuration flow
  - Detailed credential setup steps for OAuth2 and PAT
- Added endpoint matrix tooling and regenerated frozen matrix support.
- Added issue tracker URL in manifest and bumped integration version to `0.2.0`.

## 0.1.0 - 2026-03-11

- Initial custom integration scaffold for Teltonika RMS.
- OAuth2 config flow, API client, coordinators, and basic entities.
- Request budget estimation and channel-status fallback support.
