# Testing

Create the same project environment used by Jenkins:

```bash
python3.14 -m venv .ci-venv
.ci-venv/bin/python -m pip install --upgrade pip setuptools wheel
.ci-venv/bin/python -m pip install --requirement requirements.txt
```

Run the main checks through that interpreter:

```bash
.ci-venv/bin/python -m pytest tests/unit tests/ha
.ci-venv/bin/python -m ruff check .
.ci-venv/bin/python -m ruff format --check .
.ci-venv/bin/python -m mypy .
.ci-venv/bin/python tools/check_translations.py
```

Jenkins performs this installation once and stashes `.ci-venv` for all parallel
stages. Containers run with the Jenkins UID and GID preserved.

## Repository-rule validation

Pull-request commits must follow the categorized commit-message format described in
`CONTRIBUTING.md`. Jenkins validates those commits on the pull request. A graph-level
merge commit is exempt on `main`, because it only wraps commits that were already
validated before the merge.
