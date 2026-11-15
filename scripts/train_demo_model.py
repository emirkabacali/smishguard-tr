"""Train a tiny demo model on the 20-message test fixture (no licensed data needed).

The demo model only proves that the service works end to end, e.g. in the Docker smoke
test in CI. Its predictions are NOT meaningful; train the real model with
``scripts/train.py`` for actual use.

Usage:
    python scripts/train_demo_model.py --output demo-models
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

from smishguard import config
from smishguard.model.pipeline import build_pipeline
from smishguard.model.train import fit_pipeline, save_model
from smishguard.scoring.fusion import FusionParams, save_fusion_params

logger = logging.getLogger("train_demo_model")

FIXTURE = config.PROJECT_ROOT / "tests" / "fixtures" / "sms_fixture.csv"


def main() -> int:
    """Entry point. Returns a process exit code."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output", type=Path, required=True, help="directory for the model")
    args = parser.parse_args()

    data = pd.read_csv(FIXTURE, keep_default_na=False)
    model = fit_pipeline(build_pipeline("logreg"), data)
    args.output.mkdir(parents=True, exist_ok=True)
    save_model(
        model,
        "logreg-demo-fixture",
        {"train_rows": len(data), "note": "demo model trained on the test fixture"},
        {},
        model_path=args.output / config.TEXT_MODEL_PATH.name,
        metadata_path=args.output / config.MODEL_METADATA_PATH.name,
    )
    save_fusion_params(FusionParams(), args.output / config.FUSION_PARAMS_PATH.name)
    logger.info("Demo model written to %s (not meaningful for real predictions)", args.output)
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    sys.exit(main())
