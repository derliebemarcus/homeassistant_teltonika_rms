# First local run

## Goal

Create a verified local or test execution of Teltonika RMS Home Assistant Integration.

## Prerequisites

- A checkout of `homeassistant_teltonika_rms`
- Tooling compatible with Python, Home Assistant, Teltonika RMS API, OAuth2/PAT, Socket.IO
- No production secrets in the repository working tree

## Procedure

1. Install through HACS as a custom Integration repository and restart Home Assistant.
2. For a manual installation, copy `custom_components/teltonika_rms` into the Home Assistant `custom_components` directory.
3. Configure OAuth2 application credentials or a Personal Access Token.

## Verification

```bash
make validate
python3 -m pytest tests/unit tests/ha
ruff check .
ruff format --check .
mypy .
```
