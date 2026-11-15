import logging
import subprocess
import sys

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from smishguard import __version__, config
from smishguard.analyzer import Analyzer
from smishguard.api.main import create_app
from smishguard.model.pipeline import build_pipeline
from smishguard.model.train import fit_pipeline

SCAM = (
    "PTT: Kargonuz adres eksikligi nedeniyle bekliyor. "
    "24 saat icinde guncelleyin: hxxps://ptt-kargo-takip[.]xyz"
)


@pytest.fixture(scope="module")
def fixture_analyzer(sms_fixture: pd.DataFrame) -> Analyzer:
    return Analyzer(fit_pipeline(build_pipeline("logreg"), sms_fixture), model_version="fixture")


@pytest.fixture
def client(fixture_analyzer: Analyzer):
    with TestClient(create_app(loader=lambda: fixture_analyzer)) as test_client:
        yield test_client


@pytest.fixture
def client_without_model():
    def missing() -> Analyzer:
        raise FileNotFoundError("models/text_model.joblib not found")

    with TestClient(create_app(loader=missing)) as test_client:
        yield test_client


def test_health_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "model_loaded": True, "version": __version__}


def test_analyze_returns_score_level_and_reasons(client: TestClient) -> None:
    response = client.post("/v1/analyze", json={"text": SCAM})
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "risk_score",
        "risk_level",
        "ml_probability",
        "rule_score",
        "reasons",
        "model_version",
    }
    assert body["risk_level"] == "high"
    assert body["model_version"] == "fixture"
    codes = [reason["code"] for reason in body["reasons"]]
    assert codes[0] == "BRAND_IMPERSONATION"
    assert all(set(r) == {"code", "weight", "message"} for r in body["reasons"])


def test_analyze_legitimate_message(client: TestClient) -> None:
    body = client.post("/v1/analyze", json={"text": "yarin okulda gorusuruz kanka"}).json()
    assert body["risk_level"] == "low"
    assert body["reasons"] == []


@pytest.mark.parametrize(
    "payload",
    [
        {"text": ""},
        {"text": "    "},  # whitespace only is stripped to empty
        {"text": "a" * (config.API_MAX_TEXT_LENGTH + 1)},
        {},
        {"text": 123},
        {"message": "wrong field"},
    ],
)
def test_invalid_input_returns_422(client: TestClient, payload: dict) -> None:
    assert client.post("/v1/analyze", json=payload).status_code == 422


def test_max_length_text_is_accepted(client: TestClient) -> None:
    response = client.post("/v1/analyze", json={"text": "a" * config.API_MAX_TEXT_LENGTH})
    assert response.status_code == 200


def test_missing_model_returns_503(client_without_model: TestClient) -> None:
    health = client_without_model.get("/health")
    assert health.status_code == 503
    assert health.json()["model_loaded"] is False

    response = client_without_model.post("/v1/analyze", json={"text": SCAM})
    assert response.status_code == 503
    assert "train.py" in response.json()["detail"]


def test_message_text_is_never_logged(client: TestClient, caplog: pytest.LogCaptureFixture) -> None:
    secret = "GIZLI-MESAJ-ICERIGI kargonuz bekliyor"
    with caplog.at_level(logging.INFO, logger="smishguard.api"):
        client.post("/v1/analyze", json={"text": secret})
    assert "analyze length=" in caplog.text
    assert "GIZLI" not in caplog.text


def test_api_runs_without_pandas() -> None:
    # The Docker image ships only the core dependencies; pandas/pyarrow are a "data" extra.
    code = (
        "import sys\n"
        "class Block:\n"
        "    def find_spec(self, name, path=None, target=None):\n"
        "        if name.split('.')[0] in ('pandas', 'pyarrow'):\n"
        "            raise ImportError(name)\n"
        "sys.meta_path.insert(0, Block())\n"
        "from fastapi.testclient import TestClient\n"
        "from smishguard.api.main import create_app\n"
        "with TestClient(create_app()) as client:\n"
        "    client.get('/health')\n"
        "assert 'pandas' not in sys.modules\n"
    )
    subprocess.run([sys.executable, "-c", code], check=True)


def test_openapi_docs_are_available(client: TestClient) -> None:
    assert client.get("/docs").status_code == 200
    schema = client.get("/openapi.json").json()
    assert "/v1/analyze" in schema["paths"]
