#!/usr/bin/env bash
set -euo pipefail

task="${1:-}"
: "${SB_NAME:?SB_NAME is required}"

case "$task" in
    pytest)
        mkdir -p "$SB_NAME/sonar/tests"
        python3 -m pytest tests/unit tests/ha \
            --junitxml="$SB_NAME/sonar/tests/pytest.xml" \
            --cov=. --cov-config=.coveragerc \
            --cov-report="xml:$SB_NAME/sonar/tests/coverage.xml" \
            --cov-report=term-missing
        python3 tools/check_coverage_threshold.py "$SB_NAME/sonar/tests/coverage.xml" 97.1
        ;;
    ruff-lint)
        mkdir -p "$SB_NAME/sonar/ruff"
        python3 -m ruff check . --output-format=json \
            --output-file="$SB_NAME/sonar/ruff/ruff-report.json"
        ;;
    ruff-format)
        mkdir -p "$SB_NAME/sonar/ruff-format"
        status=0
        python3 -m ruff format --check . \
            > "$SB_NAME/sonar/ruff-format/ruff-format.txt" 2>&1 || status=$?
        cat "$SB_NAME/sonar/ruff-format/ruff-format.txt"
        exit "$status"
        ;;
    mypy)
        mkdir -p "$SB_NAME/sonar/mypy"
        status=0
        python3 -m mypy . --show-column-numbers \
            > "$SB_NAME/sonar/mypy/mypy-report.txt" 2>&1 || status=$?
        cat "$SB_NAME/sonar/mypy/mypy-report.txt"
        exit "$status"
        ;;
    translations)
        mkdir -p "$SB_NAME/sonar/translations"
        status=0
        python3 tools/check_translations.py \
            > "$SB_NAME/sonar/translations/translations.txt" 2>&1 || status=$?
        cat "$SB_NAME/sonar/translations/translations.txt"
        exit "$status"
        ;;
    pip-audit)
        mkdir -p "$SB_NAME/sonar/pip-audit"
        python3 tools/run_pip_audit.py -r requirements.txt --format json \
            --output "$SB_NAME/sonar/pip-audit/pip-audit-report.json"
        ;;
    mutation)
        mkdir -p "$SB_NAME/mutation"
        python3 -m pytest --cov=custom_components/teltonika_rms \
            --cov-context=test --cov-config=.coveragerc tests/
        python3 -m mutmut run
        python3 -m mutmut results > "$SB_NAME/mutation/mutation-results.txt" || true
        ;;
    *)
        echo "Unknown Python quality task: $task" >&2
        exit 2
        ;;
esac
