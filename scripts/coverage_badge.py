"""Write reports/coverage.json from a pytest-cov JSON report (used by the README badge).

Usage:
    pytest --cov=smishguard --cov-report=json
    python scripts/coverage_badge.py [coverage.json]
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

from smishguard import config

logger = logging.getLogger("coverage_badge")


def main() -> int:
    """Entry point. Returns a process exit code."""
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else config.PROJECT_ROOT / "coverage.json"
    percent = json.loads(source.read_text(encoding="utf-8"))["totals"]["percent_covered"]
    target = config.REPORTS_DIR / "coverage.json"
    target.write_text(
        json.dumps({"percent": f"{percent:.0f}"}) + "\n", encoding="utf-8", newline="\n"
    )
    logger.info("coverage %.1f%% -> %s", percent, target.relative_to(config.PROJECT_ROOT))
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    sys.exit(main())
