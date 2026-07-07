# Deployment architecture

Teltonika RMS Home Assistant Integration is deployed as Home Assistant custom integration runtime. Deployment and release automation validate the repository before mutating runtime state. See the [deployment diagram](diagrams/deployment.md).

## CI image dependency

The build-time runtime is published centrally as
`registry.home.siczb.de/siczb/homeassistant-integration-ci:3.14`. This repository does
not publish a Teltonika-specific CI image. An immutable shared-image tag can be used as
an explicit runtime override for rollback diagnosis.
