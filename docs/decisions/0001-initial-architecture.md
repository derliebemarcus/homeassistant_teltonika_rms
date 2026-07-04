# 0001: Use Socket.IO first with HTTP polling as a safe fallback.

## Status

Accepted

## Date

2026-07-04

## Context

Home Assistant custom integration for monitoring and controlling supported Teltonika RMS-managed networking devices.

## Decision drivers

- Reliable device discovery and state updates
- Quota-aware and resilient API access
- Secure secret and token handling

## Considered options

1. Retain the established architecture
2. Replace it with a tightly coupled alternative
3. Defer the architectural boundary to deployment-specific code

## Decision

Use Socket.IO first with HTTP polling as a safe fallback.

## Rationale

Status-channel updates reduce latency while polling preserves operation when the channel is unavailable or unreliable.

## Consequences

- The documented building blocks and interfaces remain explicit contracts.
- Changes to the decision require a superseding ADR.

## Risks

- RMS endpoint behavior and OpenAPI definitions can change.
- OAuth scope changes may require reauthentication.

## References

- maintenance issue #37
