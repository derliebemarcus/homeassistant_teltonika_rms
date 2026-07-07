# Contributing

## Project Rules

- Version bumps are semantic:
  - patch: fixes, compatibility, diagnostics, documentation, testing
  - minor: new entities, services, or user-visible capabilities without breaking config
  - major: breaking config or behavior changes
- Commit messages must follow repository rules:
  - single-line: `add:`, `change:`, `deprecate:`, `remove:`, or `fix:`
  - multi-line: short summary, blank line, then categorized body lines
  - generated merge commits are exempt because their pull-request commits were validated
- Release notes must contain these headings in this order:
  - `### New Features`
  - `### Improvements`
  - `### Changes`
  - `### Bugfixes`

## Required Test Rules

- New optional features must degrade gracefully when their backing data or capability is not available.
- Any change that adds a new RMS scope or depends on a scope that existing installs may not yet have must include:
  - a success-path test
  - a missing-scope test
  - a test proving the base integration still starts when the feature is optional
- High coverage is not enough by itself. Tests must lock the intended runtime behavior, especially for setup, reauth, and feature degradation paths.

## Home Assistant Direction

This repository aims to stay close to Home Assistant integration conventions:

- config flow first
- diagnostics available for supportability
- entity creation only when data is actually present
- tests for runtime logic and Home Assistant imports
- branding, translations, and metadata kept consistent
