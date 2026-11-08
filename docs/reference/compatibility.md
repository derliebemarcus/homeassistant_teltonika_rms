# Compatibility

- Supported Home Assistant version declared in the integration manifest
- Python 3.14 in CI
- Teltonika RMS API with OAuth2 or PAT authentication
- Validated devices include RUTX50, TAP200, and TSW202

Breaking compatibility changes require an explicit major release or migration note.

## Home Assistant 2026.11 qualification

CI must install Home Assistant Core 2026.11.0 and run `tests/ha/test_ha_version.py`
as a fail-closed guard. Import and mocked unit tests are not substitutes for full
runtime validation. Changes to the installed integration should not be released
until real HA 2026.11 integration tests, independent review and all CI gates pass.
