"""Shared fixtures. Everything here works without the real (licensed) dataset."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def sms_fixture() -> pd.DataFrame:
    """20 labelled synthetic messages (10 malicious, 10 legitimate)."""
    return pd.read_csv(FIXTURES_DIR / "sms_fixture.csv", keep_default_na=False)
