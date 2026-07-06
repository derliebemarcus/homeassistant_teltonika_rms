# Runtime scenarios

## Normal operation

1. Configuration and protected credentials are loaded.
2. External dependencies are contacted through explicit interfaces.
3. Data is validated and normalized by the responsible building blocks.
4. Results are exposed through the project runtime interface.

## Failure handling

1. Failures are logged without secrets.
2. Retry or fallback behavior is applied only where safe.
3. Health, diagnostics, or unavailable states expose the failure.
4. Operators follow the troubleshooting or rollback procedure.

## Continuous-integration runtime

Jenkins runs the shared Home Assistant integration image with `--userns=keep-id`.
Project dependencies remain in the repository and are installed once into `.ci-venv`
per build. Parallel stages restore the environment from the bootstrap stash.
