"""Train and compare the baseline text models, then save the selected one.

Both candidates (Logistic Regression and Multinomial Naive Bayes) are cross-validated on
the training set and compared on the validation set. The test set is not touched here.

Usage:
    python scripts/train.py [--model best|logreg|nb]
"""

from __future__ import annotations

import argparse
import json
import logging
import sys

import pandas as pd

from smishguard import config
from smishguard.model.pipeline import MODEL_NAMES, build_pipeline
from smishguard.model.predict import top_ngrams
from smishguard.model.train import (
    cross_validate_pipeline,
    evaluate_pipeline,
    file_sha256,
    fit_pipeline,
    save_model,
    select_model,
)

logger = logging.getLogger("train")


def load_split(name: str) -> pd.DataFrame:
    """Read a processed split, failing with a helpful message if it does not exist."""
    path = config.PROCESSED_DIR / f"{name}.csv"
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Run `python scripts/build_dataset.py` first.")
    return pd.read_csv(path, keep_default_na=False)


def main() -> int:
    """Entry point. Returns a process exit code."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--model",
        choices=("best", *MODEL_NAMES),
        default="best",
        help="model to save; 'best' selects by validation F1 with a tolerance (default)",
    )
    args = parser.parse_args()

    try:
        train, val = load_split("train"), load_split("val")
    except FileNotFoundError as exc:
        logger.error("%s", exc)
        return 1

    results: dict[str, dict] = {}
    fitted = {}
    for name in MODEL_NAMES:
        pipeline = build_pipeline(name)
        logger.info("Cross-validating %s ...", name)
        cv = cross_validate_pipeline(pipeline, train)
        fitted[name] = fit_pipeline(pipeline, train)
        results[name] = {"cv_train": cv, "validation": evaluate_pipeline(fitted[name], val)}
        logger.info(
            "%-6s CV F1 %.3f +/- %.3f | val F1 %.4f",
            name,
            cv["f1"]["mean"],
            cv["f1"]["std"],
            results[name]["validation"]["f1"],
        )

    best = select_model({name: results[name]["validation"]["f1"] for name in MODEL_NAMES})
    chosen = best if args.model == "best" else args.model
    logger.info("Best on validation: %s, saving: %s", best, chosen)

    data_summary = {
        "train_rows": len(train),
        "val_rows": len(val),
        "train_synthetic_rows": int((train["source"] == config.SOURCE_SYNTHETIC).sum()),
        "train_sha256": file_sha256(config.PROCESSED_DIR / "train.csv"),
    }
    report = {
        "selection_metric": "validation f1",
        "selection_tolerance": config.MODEL_SELECTION_TOLERANCE,
        "model_preference_order": list(MODEL_NAMES),
        "decision_threshold": config.ML_DECISION_THRESHOLD,
        "cv_folds": config.CV_FOLDS,
        "cv_note": "CV folds evaluate real messages only; synthetic rows stay in every fit fold",
        "data": data_summary,
        "models": results,
        "best_model": best,
        "saved_model": chosen,
    }
    if chosen == "logreg":
        report["top_features"] = top_ngrams(fitted["logreg"])

    config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    config.BASELINE_METRICS_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
    logger.info("Wrote %s", config.BASELINE_METRICS_PATH.relative_to(config.PROJECT_ROOT))

    save_model(fitted[chosen], chosen, data_summary, results[chosen]["validation"])
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    sys.exit(main())
