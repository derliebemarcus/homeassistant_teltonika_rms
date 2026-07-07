# Repository structure

- `custom_components/teltonika_rms/`: integration runtime
- `tests/unit/`: isolated unit and contract tests
- `tests/ha/`: Home Assistant integration tests
- `tools/`: CI, release, translation, API-matrix, and security helpers
- `docs/`: user, architecture, decision, and operational documentation

The root `Jenkinsfile` is the only Jenkins pipeline definition. No generated
`Dockerfile.ci`, local image builder, or repository-specific Jenkins module tree is
retained.
