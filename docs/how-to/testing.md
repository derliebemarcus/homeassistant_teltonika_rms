# Testing

Run the repository's local quality checks before opening a pull request:

```bash
make validate
python3 -m pytest tests/unit tests/ha
ruff check .
ruff format --check .
mypy .
```

Jenkins remains authoritative for the complete quality, analysis, security, and release contract.
