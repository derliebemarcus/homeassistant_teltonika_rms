# 0000: Use MADR for architecture decisions

## Status

Accepted

## Date

2026-07-04

## Context

The repository needs durable records for decisions affecting architecture, compatibility, security, operations, and releases.

## Decision drivers

- Preserve rationale beyond implementation details.
- Keep decisions reviewable and linkable.
- Record consequences and supersession explicitly.

## Considered options

1. Informal notes
2. Custom decision documents
3. MADR-compatible ADRs

## Decision

Use MADR-compatible ADRs below `docs/decisions/`.

## Rationale

MADR is concise, structured, and compatible with Markdown review.

## Consequences

- Major decisions require an ADR.
- Changed decisions create a superseding ADR.

## Risks

- Minor decisions can be over-documented; apply proportionality.

## References

- maintenance issue #37
