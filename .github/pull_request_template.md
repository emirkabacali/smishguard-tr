## Summary

<!-- What does this PR do and why? -->

## Changes

-

## How to test

```bash
pip install -e ".[dev]"
ruff check . && ruff format --check .
pytest
```

## Checklist

- [ ] `ruff check` and `ruff format --check` pass
- [ ] `pytest` passes locally
- [ ] No raw dataset files, secrets or personal data committed
- [ ] Links in data / docs are defanged (`hxxps://example[.]xyz`)
- [ ] Docs (README / DATA.md / DECISIONS.md / CHANGELOG.md) updated if behaviour changed
