"""Every number in the README results table must match reports/metrics_test.json."""

import json
import re

from smishguard import config

README = config.PROJECT_ROOT / "README.md"
SYSTEM_NAMES = {"ML only": "ml_only", "Rules only": "rules_only", "Hybrid": "hybrid"}


def results_rows() -> dict[str, list[str]]:
    text = README.read_text(encoding="utf-8")
    block = re.search(r"<!-- results:start -->(.*?)<!-- results:end -->", text, re.DOTALL)
    assert block, "README results markers not found"
    rows = {}
    for line in block.group(1).strip().splitlines()[2:]:  # skip header + separator
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        rows[cells[0]] = cells[1:]
    return rows


def test_readme_results_match_reports() -> None:
    report = json.loads(config.TEST_METRICS_PATH.read_text(encoding="utf-8"))["test"]
    rows = results_rows()
    assert set(rows) == set(SYSTEM_NAMES)
    for label, key in SYSTEM_NAMES.items():
        metrics, (low, high) = report[key]["metrics"], report[key]["f1_ci95"]
        expected = [
            f"{metrics['precision']:.4f}",
            f"{metrics['recall']:.4f}",
            f"{metrics['f1']:.4f}",
            f"{metrics['false_positive_rate']:.4f}",
            f"{low:.4f} – {high:.4f}",
        ]
        assert rows[label] == expected, label


def test_readme_fusion_parameters_match() -> None:
    params = json.loads(config.FUSION_PARAMS_PATH.read_text(encoding="utf-8"))
    text = README.read_text(encoding="utf-8")
    expected = (
        f"α = {params['alpha']}, medium ≥ {params['medium_threshold']}, "
        f"high ≥ {params['high_threshold']}"
    )
    assert expected in text
