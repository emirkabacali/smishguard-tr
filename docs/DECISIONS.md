# Decision Log

Lightweight records of technical decisions: what was decided, which alternatives were
considered and why. Newest entries at the bottom.

---

## D-001: Supported Python versions

- **Date:** 2026-11-15
- **Decision:** Support Python 3.11+ (`requires-python = ">=3.11"`). CI runs on 3.11, 3.12
  and 3.13; local development uses 3.13.
- **Alternatives:** Pin to 3.11/3.12 only (as originally planned); also test 3.14.
- **Rationale:** 3.11 is the oldest version with the typing and performance features we rely
  on. The development machine has 3.13, so it is added to the CI matrix to keep "works on my
  machine" and "works in CI" identical. 3.14 is left out until all scientific dependencies
  ship stable wheels for it.

## D-002: Build backend and project layout

- **Date:** 2026-11-15
- **Decision:** `src/` layout with setuptools as the build backend, configured entirely in
  `pyproject.toml`. Runtime dependencies are added only in the phase that first needs them.
- **Alternatives:** Flat layout; Poetry / Hatch / uv as project managers.
- **Rationale:** The `src/` layout forces tests to import the *installed* package, which
  catches packaging mistakes early. setuptools + `pip install -e` is the most widely known
  toolchain and needs no extra tool on a fresh machine.
