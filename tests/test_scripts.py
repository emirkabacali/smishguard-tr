"""Smoke tests for helper scripts that must work without the licensed dataset."""

import json
import subprocess
import sys

from smishguard import config
from smishguard.analyzer import Analyzer

SCRIPTS = config.PROJECT_ROOT / "scripts"


def test_demo_model_script_produces_a_loadable_model(tmp_path) -> None:
    subprocess.run(
        [sys.executable, str(SCRIPTS / "train_demo_model.py"), "--output", str(tmp_path)],
        check=True,
    )
    analyzer = Analyzer.from_files(
        tmp_path / config.TEXT_MODEL_PATH.name,
        tmp_path / config.MODEL_METADATA_PATH.name,
        tmp_path / config.FUSION_PARAMS_PATH.name,
    )
    result = analyzer.analyze("Kargonuz bekliyor, odeme yapin: hxxps://kargo-odeme[.]xyz")
    assert 0 <= result.risk_score <= 1
    meta = json.loads((tmp_path / config.MODEL_METADATA_PATH.name).read_text())
    assert meta["model_name"] == "logreg-demo-fixture"


def test_scripts_print_help_without_data() -> None:
    for script in ("download_data.py", "train.py", "evaluate.py", "train_demo_model.py"):
        completed = subprocess.run(
            [sys.executable, str(SCRIPTS / script), "--help"], capture_output=True, text=True
        )
        assert completed.returncode == 0, completed.stderr
        assert "usage" in completed.stdout.lower()
