# Resume Action: What Happened Until Now

## Project Overview
This repository contains the `teltonika_rms` custom component for Home Assistant. It manages API interactions, coordinators, and entities for Teltonika RMS.

## What Was Done Successfully
1. **Runner Migration:** Transitioned the project's GitHub Actions from `ubuntu-latest` to self-hosted runners (`klymene` / `X64`). Docker-specific tasks (`actionlint`, `hacs/action`, `hassfest`) were kept on `ubuntu-latest` to avoid complex podman/docker socket configurations on the self-hosted instances.
2. **Pyenv Integration:** Completely removed the `actions/setup-python@v6` step. All Python tasks on the self-hosted runner now use the pre-installed global `pyenv` (`3.14.3-final-0`).
3. **Virtual Environments:** Implemented ephemeral virtual environments (`.venv`) for all workflows to bypass global `pyenv` write-permission issues during `pip install`. All `pytest`, `ruff`, `mypy`, and `mutmut` commands have been refactored to explicitly execute within the activated `.venv`.
4. **Root Path Discovery:** Refactored multiple test files (`test_platforms.py`, `test_translations.py`, `test_ha_imports.py`) to dynamically search upward for `manifest.json` rather than relying on hardcoded `parents[2]`. This was necessary because `mutmut` runs tests from an isolated `mutants/` subdirectory.

## The Outstanding Challenge
The **Mutation Testing** GitHub Action (`mutation.yml`) stops immediately after generating mutants with the following error:
`Stopping early, because we could not find any test case for any mutant. It seems that the selected tests do not cover any code that we mutated.`

**The discrepancy:** `mutmut run` behaves correctly in the local macOS development environment, locating tests and processing the mutants successfully. However, it fails completely on the self-hosted GitHub Actions runner. 

It is highly likely that when `mutmut` attempts to run `pytest` silently to gather stats (associating tests with code lines), `pytest` is either crashing (e.g., `ModuleNotFoundError` or `sys.path` issue) or returning 0 tests inside the runner environment.

## Actions Taken to Help Debug
To help the successor fix this:
1. Added `debug = true` under `[tool.mutmut]` in `pyproject.toml`. This forces `mutmut` to print every `pytest` sub-command it executes along with the exact exit code and error output.
2. Updated `tests/conftest.py` to ensure `sys.path` is explicitly injected with the `mutants/custom_components` directory in case `mutmut` struggles with imports during the isolated `mutants/` test phase.
3. Triggered a fresh `mutation.yml` workflow run on GitHub.

## Next Steps for the Successor Agent
1. **Check the GitHub Action Logs:** Fetch the logs for the latest `Mutation Testing` workflow run (e.g., using `gh run list --workflow="mutation.yml" -L 1` and `gh run view <ID> --log-failed`). 
2. **Analyze the Debug Output:** Because `debug = true` is now active, the log will reveal the exact `python -m pytest` command `mutmut` tried to run during the `Running stats` phase and why it failed.
3. **Fix the Execution Environment:** The debug logs will likely reveal a missing dependency, an import path issue inside the `mutants/` folder, or an issue with the virtual environment propagation to `mutmut`'s subprocesses on the Linux runner.