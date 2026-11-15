"""Smoke tests: the package is importable and its version metadata is consistent."""

import re
from importlib.metadata import version

import smishguard

SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")


def test_package_exposes_semantic_version() -> None:
    assert SEMVER_PATTERN.match(smishguard.__version__)


def test_installed_metadata_matches_package_version() -> None:
    assert version("smishguard-tr") == smishguard.__version__
