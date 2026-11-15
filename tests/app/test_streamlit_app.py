"""UI tests with Streamlit's headless AppTest runner (no browser needed)."""

from pathlib import Path

import pandas as pd
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from smishguard.analyzer import Analyzer
from smishguard.model.pipeline import build_pipeline
from smishguard.model.train import fit_pipeline

APP = str(Path(__file__).resolve().parents[2] / "app" / "streamlit_app.py")


@pytest.fixture
def with_fixture_model(monkeypatch: pytest.MonkeyPatch, sms_fixture: pd.DataFrame) -> None:
    analyzer = Analyzer(fit_pipeline(build_pipeline("logreg"), sms_fixture), model_version="fx")
    monkeypatch.setattr(Analyzer, "from_files", classmethod(lambda cls: analyzer))
    st.cache_resource.clear()


def test_default_example_is_analyzed(with_fixture_model: None) -> None:
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert not at.exception
    page = " ".join(md.value for md in at.markdown)
    assert "HIGH RISK" in page
    assert "BRAND_IMPERSONATION" in page
    assert any("not a security product" in c.value for c in at.caption)


def test_legitimate_example_has_no_reasons(with_fixture_model: None) -> None:
    at = AppTest.from_file(APP, default_timeout=30).run()
    at.selectbox[0].select("Personal message (legitimate)").run()
    page = " ".join(md.value for md in at.markdown)
    assert "LOW RISK" in page
    assert any("No rule fired" in md.value for md in at.markdown)


def test_missing_model_shows_instructions(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing(cls):
        raise FileNotFoundError("no model")

    monkeypatch.setattr(Analyzer, "from_files", classmethod(missing))
    st.cache_resource.clear()
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert at.error and "train.py" in at.error[0].value
