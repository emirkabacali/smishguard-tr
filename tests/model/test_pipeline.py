import json

import numpy as np
import pandas as pd
import pytest

from smishguard import config
from smishguard.metrics import classification_metrics
from smishguard.model.pipeline import build_pipeline, preprocess
from smishguard.model.predict import load_model, predict_proba, top_ngrams
from smishguard.model.train import cv_splits, fit_pipeline, save_model, select_model


def test_preprocess_masks_lowercases_and_folds() -> None:
    assert preprocess("ÖDEME İçin Tıkla: 0532 123 45 67") == "odeme icin tikla: <phone>"


@pytest.mark.parametrize("name", ["logreg", "nb"])
def test_pipeline_fits_and_predicts_probabilities(name: str, sms_fixture: pd.DataFrame) -> None:
    model = fit_pipeline(build_pipeline(name), sms_fixture)
    proba = predict_proba(model, sms_fixture["text"])
    assert proba.shape == (20,)
    assert ((proba >= 0) & (proba <= 1)).all()
    # The fixture is easy; the model must at least fit its own training data.
    assert ((proba >= 0.5).astype(int) == sms_fixture["label"]).mean() >= 0.9


def test_unseen_messages_are_ranked_sensibly(sms_fixture: pd.DataFrame) -> None:
    model = fit_pipeline(build_pipeline("logreg"), sms_fixture)
    scam, normal = predict_proba(
        model,
        ["Kargonuz bekliyor, ucreti odeyin: hxxps://kargo-odeme[.]xyz", "yarin gorusuruz kanka"],
    )
    assert scam > normal


def test_training_is_deterministic(sms_fixture: pd.DataFrame) -> None:
    first = predict_proba(fit_pipeline(build_pipeline("logreg"), sms_fixture), sms_fixture["text"])
    second = predict_proba(fit_pipeline(build_pipeline("logreg"), sms_fixture), sms_fixture["text"])
    np.testing.assert_array_equal(first, second)


def test_unknown_model_name_raises() -> None:
    with pytest.raises(ValueError, match="Unknown model"):
        build_pipeline("svm")


def test_cv_splits_keep_synthetic_rows_in_fit_folds() -> None:
    real, synth = config.SOURCE_TURKISHSMS, config.SOURCE_SYNTHETIC
    rows = [{"text": f"t{i}", "label": i % 2, "source": real} for i in range(20)]
    rows += [{"text": f"s{i}", "label": 1, "source": synth} for i in range(4)]
    train = pd.DataFrame(rows)
    synthetic = set(range(20, 24))
    folds = list(cv_splits(train, n_splits=5))
    assert len(folds) == 5
    for fit_idx, eval_idx in folds:
        assert synthetic <= set(fit_idx)
        assert synthetic.isdisjoint(eval_idx)
    all_eval = np.concatenate([e for _, e in folds])
    assert sorted(all_eval) == list(range(20))  # every real row evaluated exactly once


@pytest.mark.parametrize(
    ("scores", "expected"),
    [
        ({"logreg": 0.9608, "nb": 0.9615}, "logreg"),  # within tolerance -> preferred model
        ({"logreg": 0.90, "nb": 0.95}, "nb"),  # clearly better -> challenger
        ({"logreg": 0.95, "nb": 0.90}, "logreg"),
    ],
)
def test_select_model_prefers_first_within_tolerance(scores: dict, expected: str) -> None:
    assert select_model(scores, tolerance=0.01) == expected


def test_top_ngrams_lists_both_classes(sms_fixture: pd.DataFrame) -> None:
    model = fit_pipeline(build_pipeline("logreg"), sms_fixture)
    top = top_ngrams(model, n=5)
    assert len(top["malicious"]) == len(top["legitimate"]) == 5
    assert all(item["weight"] > 0 for item in top["malicious"])
    assert all(item["weight"] < 0 for item in top["legitimate"])


def test_top_ngrams_rejects_naive_bayes(sms_fixture: pd.DataFrame) -> None:
    with pytest.raises(TypeError):
        top_ngrams(fit_pipeline(build_pipeline("nb"), sms_fixture))


def test_save_and_load_roundtrip(sms_fixture: pd.DataFrame, tmp_path) -> None:
    model = fit_pipeline(build_pipeline("logreg"), sms_fixture)
    model_path, meta_path = tmp_path / "m.joblib", tmp_path / "meta.json"
    save_model(model, "logreg", {"train_rows": 20}, {"f1": 1.0}, model_path, meta_path)

    loaded = load_model(model_path)
    np.testing.assert_allclose(
        predict_proba(loaded, sms_fixture["text"]), predict_proba(model, sms_fixture["text"])
    )
    meta = json.loads(meta_path.read_text())
    assert meta["model_name"] == "logreg"
    assert meta["data"] == {"train_rows": 20}


def test_load_model_missing_file_raises(tmp_path) -> None:
    with pytest.raises(FileNotFoundError, match="train.py"):
        load_model(tmp_path / "missing.joblib")


def test_classification_metrics_counts_and_rates() -> None:
    m = classification_metrics([1, 1, 0, 0, 0], [1, 0, 1, 0, 0], [0.9, 0.4, 0.6, 0.2, 0.1])
    assert (m["tp"], m["fn"], m["fp"], m["tn"]) == (1, 1, 1, 2)
    assert m["precision"] == 0.5
    assert m["recall"] == 0.5
    assert m["false_positive_rate"] == pytest.approx(0.3333, abs=1e-4)
    assert "roc_auc" in m
