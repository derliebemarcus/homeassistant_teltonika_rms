.PHONY: setup test lint format release mutate audit osv validate hassfest lock lock-upgrade snapshot contract

lock:
	@tools/compile_lockfile.sh

lock-upgrade:
	@tools/compile_lockfile.sh --upgrade

setup:
	@echo "Setting up development environment..."
	@python3 -m venv .venv
	@.venv/bin/python3 -m pip install -r requirements.txt
	@tools/install_venv_activation_hook.sh
	@tools/install_git_hooks.sh
	@echo "Setup complete. Git hooks are activated."

snapshot:
	@echo "Updating snapshots..."
	@.venv/bin/python3 -m pytest tests/ha/test_diagnostics_snapshots.py --snapshot-update

contract:
	@echo "Running API contract tests..."
	@.venv/bin/python3 -m pytest tests/unit/test_api_contract.py

test:
	@.venv/bin/python3 -m pytest tests/unit tests/ha

lint:
	@.venv/bin/python3 -m ruff check .
	@.venv/bin/python3 -m mypy .

format:
	@.venv/bin/python3 -m ruff format .
	@.venv/bin/python3 -m ruff check --fix .

mutate:
	@echo "Running mutation testing (this will take a while)..."
	@.venv/bin/python3 -m mutmut run

audit:
	@echo "Running vulnerability audit on dependencies..."
	@.venv/bin/python3 tools/run_pip_audit.py -r requirements.txt
# Engine Detection
ENGINE := $(shell if command -v podman >/dev/null 2>&1; then echo podman; elif command -v docker >/dev/null 2>&1; then echo docker; else echo "none"; fi)

osv:
	@echo "Running OSV-Scanner for comprehensive vulnerability checks using $(ENGINE)..."
	@if [ "$(ENGINE)" = "none" ]; then echo "No container engine found."; exit 1; fi
	@$(ENGINE) run --rm -v $(PWD):/src ghcr.io/google/osv-scanner:latest scan source -r --no-resolve /src

hassfest:
	@echo "Running Home Assistant Hassfest validation via $(ENGINE)..."
	@if [ "$(ENGINE)" = "none" ]; then echo "No container engine found."; exit 1; fi
	@$(ENGINE) run --rm -v $(PWD):/github/workspace ghcr.io/home-assistant/actions/hassfest:latest

validate:
	@echo "Validating translations..."
	@.venv/bin/python3 tools/check_translations.py
	@echo "Validating release notes..."
	@.venv/bin/python3 tools/check_release_notes.py custom_components/teltonika_rms/manifest.json CHANGELOG.md

release:
	@tools/publish_release.sh
