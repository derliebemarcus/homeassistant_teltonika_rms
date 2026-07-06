# Quality requirements

- Reliable device discovery and state updates
- Quota-aware and resilient API access
- Secure secret and token handling
- Stable diagnostics and API contracts
- High automated coverage and mutation confidence

## CI isolation

- The shared image contains no repository source, tests, or dependency declarations.
- The project virtual environment is created once from `requirements.txt`.
- Container stages preserve Jenkins UID and GID ownership with `--userns=keep-id`.
- Existing quality gates and report locations remain unchanged.
