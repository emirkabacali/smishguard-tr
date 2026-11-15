import json

import pandas as pd
import pytest

from smishguard.analyzer import AnalysisResult, Analyzer
from smishguard.model.pipeline import build_pipeline
from smishguard.model.train import fit_pipeline, save_model
from smishguard.scoring.fusion import FusionParams, save_fusion_params

SCAM = (
    "PTT: Kargonuz adres eksikligi nedeniyle bekliyor. "
    "24 saat icinde guncelleyin: hxxps://ptt-kargo-takip[.]xyz"
)
NORMAL = "cnm aksam yemege geliyor musun"


@pytest.fixture(scope="module")
def analyzer(sms_fixture: pd.DataFrame) -> Analyzer:
    model = fit_pipeline(build_pipeline("logreg"), sms_fixture)
    return Analyzer(
        model, FusionParams(alpha=0.7, medium_threshold=0.35, high_threshold=0.65), "test"
    )


def test_analyze_returns_complete_result(analyzer: Analyzer) -> None:
    result = analyzer.analyze(SCAM)
    assert isinstance(result, AnalysisResult)
    assert 0 <= result.risk_score <= 1
    assert result.risk_score == pytest.approx(
        0.7 * result.ml_probability + 0.3 * result.rule_score, abs=1e-3
    )
    assert result.model_version == "test"
    assert {r.code for r in result.reasons} >= {"BRAND_IMPERSONATION", "SUSPICIOUS_TLD"}


def test_scam_scores_higher_than_normal_message(analyzer: Analyzer) -> None:
    scam, normal = analyzer.analyze_batch([SCAM, NORMAL])
    assert scam.risk_score > normal.risk_score
    assert scam.risk_level == "high"
    assert normal.risk_level == "low"
    assert normal.reasons == ()


def test_batch_matches_single_calls(analyzer: Analyzer) -> None:
    assert analyzer.analyze_batch([SCAM, NORMAL]) == [
        analyzer.analyze(SCAM),
        analyzer.analyze(NORMAL),
    ]
    assert analyzer.analyze_batch([]) == []


def test_prepare_masks_pii_and_refangs() -> None:
    assert Analyzer.prepare("Ara: 0532 123 45 67  hxxps://a[.]xyz") == "Ara: <PHONE> https://a.xyz"


def test_from_files_loads_model_metadata_and_params(sms_fixture: pd.DataFrame, tmp_path) -> None:
    model_path, meta_path, fusion_path = (tmp_path / n for n in ("m.joblib", "meta.json", "f.json"))
    save_model(
        fit_pipeline(build_pipeline("logreg"), sms_fixture), "logreg", {}, {}, model_path, meta_path
    )
    meta = json.loads(meta_path.read_text())
    params = FusionParams(alpha=0.8, medium_threshold=0.4, high_threshold=0.7)
    save_fusion_params(params, fusion_path)

    loaded = Analyzer.from_files(model_path, meta_path, fusion_path)
    assert loaded.params == params
    assert loaded.model_version == meta["model_version"]
    assert loaded.analyze(SCAM).model_version == meta["model_version"]


def test_from_files_without_model_raises(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        Analyzer.from_files(tmp_path / "missing.joblib")
