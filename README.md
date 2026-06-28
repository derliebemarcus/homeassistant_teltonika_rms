# Teltonika RMS Home Assistant Integration

[![HACS Badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/derliebemarcus/teltonika_rms?style=for-the-badge)](https://github.com/derliebemarcus/teltonika_rms/releases)
[![License](https://img.shields.io/badge/License-MIT-1f6feb?style=for-the-badge)](https://github.com/derliebemarcus/teltonika_rms/blob/main/LICENSE)
[![Downloads](https://img.shields.io/github/downloads/derliebemarcus/teltonika_rms/total?style=for-the-badge)](https://github.com/derliebemarcus/teltonika_rms/releases)
[![Coverage Status](https://img.shields.io/coverallsCoverage/github/derliebemarcus/teltonika_rms?branch=main&style=for-the-badge)](https://coveralls.io/github/derliebemarcus/teltonika_rms)

<a href="https://www.teltonika-networks.com?utm_source=store&utm_medium=referral&utm_campaign=rms&utm_term=homeassistant&utm_content=product">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="custom_components/teltonika_rms/brand/TELTONIKA-LOGO-WHITE-RGB.png">
    <source media="(prefers-color-scheme: light)" srcset="custom_components/teltonika_rms/brand/TELTONIKA-LOGO-BLUE-RGB.png">
    <img alt="Teltonika Networks" src="custom_components/teltonika_rms/brand/TELTONIKA-LOGO-BLUE-RGB.png">
  </picture>
</a>

## Table of Contents

- [Teltonika RMS Home Assistant Integration](#teltonika-rms-home-assistant-integration)
  - [Table of Contents](#table-of-contents)
  - [Summary](#summary)
  - [What This Component Provides](#what-this-component-provides)
  - [Roadmap](#roadmap)
  - [Installation](#installation)
    - [Option 1: Install with HACS](#option-1-install-with-hacs)
    - [Option 2: Manual Installation](#option-2-manual-installation)
  - [Removal](#removal)
  - [Credentials Setup](#credentials-setup)
    - [OAuth2 (recommended)](#oauth2-recommended)
    - [Personal Access Token (PAT)](#personal-access-token-pat)
  - [Configuration in Home Assistant](#configuration-in-home-assistant)
  - [Endpoint Matrix](#endpoint-matrix)
  - [Conventions and Tests](#conventions-and-tests)
  - [Git Hooks and Version Tags](#git-hooks-and-version-tags)
  - [About Teltonika](#about-teltonika)

## Summary

A custom Home Assistant integration for monitoring devices managed with Teltonika RMS, with optional reboot and PoE control actions from Home Assistant. 

The integration connects to the RMS API, discovers your devices, and creates Home Assistant entities for connectivity, diagnostics, firmware availability, Ethernet port usage, timestamps, and optional location tracking.

**Supported Devices:** Though the plugin should support all Teltonika devices, it was tested only with RUTX50, TAP200, and TSW202. So those three are the supported devices.

## What This Component Provides

- Per-device entities:
  - `binary_sensor`: online connectivity, and individual link state per Ethernet port
  - `sensor`: model, firmware, serial number, last seen timestamp
  - additional `sensor` entities when RMS provides the data:
    - router uptime
    - temperature
    - signal strength
    - WAN state
    - connection state
    - connection type
    - SIM slot
  - `button`: per-device reboot action
  - `update`: firmware availability view with installed and latest stable RMS firmware versions
  - `device_tracker` (optional): GPS location only for devices that provide coordinates, including detailed location attributes (`location_detail`, `coordinates`, `google_maps_url`)
- Service:
  - `teltonika_rms.refresh` to trigger immediate refresh
- Authentication with either:
  - OAuth2 (authorization code + PKCE)
  - Personal Access Token (PAT)
- Device polling with request-budget safeguards (RMS monthly quota aware)
- API envelope parsing (`success`, `data`, `errors`, `meta`)
- Status-channel handling (`meta.channel`) with Socket.IO first, HTTP polling fallback
- Low-frequency Ethernet port scans to surface which ports are in use

## Roadmap

See our [ROADMAP.md](ROADMAP.md) for planned features and future improvements.

## Installation

### Option 1: Install with HACS

1. Open HACS in Home Assistant.
2. Go to Integrations.
3. Add this repository as a Custom Repository (type: `Integration`).
4. Search for `Teltonika RMS`.
5. Install and restart Home Assistant.

### Option 2: Manual Installation

1. Copy this folder to your Home Assistant config:
   - `/config/custom_components/teltonika_rms`
2. Ensure files like `manifest.json` and `__init__.py` are directly inside that folder.
3. Restart Home Assistant.

## Removal

1. Go to `Settings -> Devices & Services` in Home Assistant.
2. Select the `Teltonika RMS` integration and click `Delete`.
3. If installed via HACS, go to HACS -> Integrations, locate `Teltonika RMS`, click the three dots, and select `Remove`.
4. If installed manually, delete the `/config/custom_components/teltonika_rms` directory.
5. Restart Home Assistant.

## Credentials Setup

### OAuth2 (recommended)

1. Ensure [my.home-assistant.io](https://my.home-assistant.io/) is linked to your current Home Assistant instance.
   - Open [my.home-assistant.io](https://my.home-assistant.io/).
   - Confirm it resolves to the Home Assistant instance where you want to add this integration.
   - If it does not open the correct instance, fix that first before creating the RMS OAuth application.
2. Log in to RMS.
   - Open [RMS](https://rms.teltonika-networks.com/).
   - Sign in with the RMS account that owns the devices you want to monitor.
   - Complete two-factor authentication if your account requires it.
3. Create an OAuth application in [RMS Account Settings](https://account.rms.teltonika-networks.com/settings/application).
4. Configure redirect URL:
   - `https://my.home-assistant.io/redirect/oauth`
5. Set the application type to `Confidential`.
5. Grant at least this scope to the application:
   - `devices:read`
6. Add these scopes if needed:
   - `device_location:read` for GPS tracker entities
   - `device_actions:read` for broader status/channel visibility
   - `device_remote_access:read` for Ethernet port scan sensors
   - `device_actions:write` for the reboot button
   - `device_configurations:read` for PoE switch state
   - `device_configurations:write` for PoE switch control
7. In Home Assistant, go to:
   - `Settings -> Devices & Services` then click on the three dots in the upper right corner and select `Application Credentials`
8. Add `Teltonika RMS` credentials (client ID + client secret).
9. Go to `Settings -> Devices & Services -> Add Integration`.
10. Select `Teltonika RMS`.
11. When the integration asks for the authentication mode, select `OAuth2 (recommended)`.
12. Confirm the dialog that opens to link the Teltonika OAuth application with Home Assistant.
13. Confirm the dialog that opens to link the Teltonika account to Home Assistant.
14. After successful authorization, Home Assistant imports the RMS devices and lets you assign them to areas.

### Personal Access Token (PAT)

1. Log in to RMS.
   - Open [RMS](https://rms.teltonika-networks.com/).
   - Sign in with the RMS account that owns the devices you want to monitor.
   - Open [Account Settings](https://account.rms.teltonika-networks.com/settings/profile).
   - Complete [two-factor authentication](https://account.rms.teltonika-networks.com/settings/security) (required for PAT generation).
2. In RMS, generate a [Personal Access Token](https://account.rms.teltonika-networks.com/settings/tokens):
   1. Create a new token and copy it immediately.
   2. Grant at least:
      - `devices:read`
   3. Add these if needed:
      - `device_location:read` for GPS tracker entities
      - `device_actions:read` for broader status/channel visibility
      - `device_remote_access:read` for Ethernet port scan sensors
      - `device_actions:write` for the reboot button
      - `device_configurations:read` for PoE switch state
      - `device_configurations:write` for PoE switch control

## Configuration in Home Assistant

1. Go to `Settings -> Devices & Services -> Add Integration`.
2. Select `Teltonika RMS`.
3. Choose auth mode:
   - `OAuth2 (recommended)` or `Personal access token (PAT)`.
4. Finish authentication.
5. If you want to use the reboot button with OAuth2 and you authenticated before version `0.6.0`, reauthenticate once so Home Assistant can request `device_actions:write`.
6. If you want to use PoE switches and you authenticated before version `0.8.0`, reauthenticate once so Home Assistant can request `device_configurations:read` and `device_configurations:write`.
7. Open integration options to tune:
   - Inventory polling interval
   - State polling interval
   - Device count estimate
   - Optional tag/status filters
   - Enable/disable location tracker entities
   - Optional `spec_path` (compiled OpenAPI YAML on HA filesystem)

## Endpoint Matrix

- Runtime endpoint matrix is loaded from `spec_path` when configured.
- If unavailable or invalid, bundled `endpoint_matrix_frozen.json` is used.
- Regenerate bundled matrix from OpenAPI YAML:

```bash
python3 tools/generate_rms_endpoint_matrix.py /path/to/compiled.yaml
```

## Conventions and Tests

### Quickstart for Developers

To instantly set up your local development environment with all required dependencies and activated Git Hooks (best-practice), run:

```bash
make setup
```

`make setup` also installs a virtualenv activation hook that runs `pip install --upgrade pip` whenever a developer enters `.venv` or `.venv-test`.

You can run code quality tools and tests using the `Makefile` (e.g., `make lint`, `make test`, `make mutate`, `make audit`, `make osv`, `make hassfest`, `make validate`, `make lock`, `make snapshot`, `make contract`).

- Development conventions are aligned with Home Assistant custom integration guidance:
  - [Home Assistant Developer Docs](https://developers.home-assistant.io/docs/development_index/)
- Translation consistency can be validated with:

```bash
python3 tools/check_translations.py
```

- Test suite follows HA-style layout under:
  - `tests/unit/` (runs without Home Assistant dependencies)
  - `tests/ha/` (requires Home Assistant Python dependencies)
- The RMS API client performs runtime contract validation with `pydantic` models, and dedicated contract coverage lives in:
  - `tests/unit/test_api_contract.py`
- Diagnostics payload stability is protected by Syrupy snapshots:
  - `tests/ha/test_diagnostics_snapshots.py`
- Dependencies are pinned with `pip-tools`:
  - update the lockfile with `make lock`
  - CI rejects drift between `requirements-dev.in` and `requirements.txt`
- Static analysis is enforced with:
  - `ruff check .`
  - `ruff format --check .`
  - `mypy .`

- Run tests with:

```bash
python3 -m pytest
```

Note: HA-related tests under `tests/ha/` will only run in a suitable Home Assistant development environment (see [Developer Docs](https://developers.home-assistant.io/docs/development_index/)).

- Release notes are tracked in:
  - `CHANGELOG.md`

## Git Hooks and Version Tags

Install repository hooks once:

```bash
make setup
```

`pre-commit` hook behavior:

- Runs always with `--maxfail=0`:
  - without `homeassistant`: `tests/unit`
  - with `homeassistant`: `tests/unit` + `tests/ha`
- Always prints per-test summary with:
  - test name
  - duration
  - result
- Blocks commit when at least one test fails

`pre-push` hook behavior:

- Runs OSV-Scanner via Docker and blocks the push if vulnerabilities are found
- Fails closed when Docker is unavailable so vulnerability scanning cannot be skipped silently
- Ensures a version tag `v<manifest.version>` exists before push
- Ensures the tag is part of current branch history

Publish the current version for automated GitHub release creation:

```bash
tools/publish_release.sh
```

This will:

- create the local version tag if it does not exist yet
- push the current branch and tags to GitHub
- let GitHub Actions create or update the matching entry on the GitHub Releases page after `Quality Gates` and `Tests and Coverage` both succeed

If a tag was pushed successfully but the GitHub release needs manual repair, open `Actions -> Publish Release -> Run workflow` and enter the existing tag, for example `v0.6.1`.

## About Teltonika

[Teltonika](https://www.teltonika-networks.com?utm_source=store&utm_medium=referral&utm_campaign=rms&utm_term=homeassistant&utm_content=product) is a Lithuanian tech company group specializing in IoT solutions. Founded in 1998, it has since grown into a global provider of telematics and networking equipment.

Their portfolio includes industrial 4G/5G routers, network switches, GPS vehicle trackers, smart EV chargers, and telemedicine devices.

<br/>

---
<br/>

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-derliebemarcus-FFDD00?style=for-the-badge&logo=buymeacoffee&logoColor=000000)](https://buymeacoffee.com/derliebemarcus)
