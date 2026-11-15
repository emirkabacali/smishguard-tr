"""Central configuration: paths, random seed, dataset sources and label definitions.

Every constant that would otherwise be a "magic number" somewhere in the code lives here.
"""

from __future__ import annotations

import os
from pathlib import Path

# --- Paths -------------------------------------------------------------------------------
# Defaults to the repository root (src/smishguard/config.py -> parents[2]). Can be overridden
# with the SMISHGUARD_ROOT environment variable, e.g. inside a Docker image.
PROJECT_ROOT = Path(os.environ.get("SMISHGUARD_ROOT", Path(__file__).resolve().parents[2]))

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
CURATED_DIR = DATA_DIR / "curated"
CURATED_CSV = CURATED_DIR / "smishing_tr_curated.csv"
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"

# --- Reproducibility -----------------------------------------------------------------------
SEED = 42

# --- Labels, categories, sources -----------------------------------------------------------
LABEL_LEGITIMATE = 0
LABEL_MALICIOUS = 1  # spam + smishing
LABELS = (LABEL_LEGITIMATE, LABEL_MALICIOUS)

CATEGORIES = (
    "cargo",
    "e_government",
    "toll_fine",
    "bank",
    "prize",
    "investment",
    "telecom",
    "generic_spam",
    "other",
)

SOURCE_TURKISHSMS = "turkishsms"
SOURCE_CURATED_REAL = "curated_real"
SOURCE_SYNTHETIC = "synthetic"
SOURCES = (SOURCE_TURKISHSMS, SOURCE_CURATED_REAL, SOURCE_SYNTHETIC)

# Columns shared by every loaded dataset.
SCHEMA_COLUMNS = ("text", "label", "category", "source")

# --- TurkishSMS dataset (Uysal et al., 2013) -------------------------------------------------
# Mirror published by the first author on Hugging Face, pinned to an exact revision so that
# every download is byte-for-byte reproducible.
TURKISHSMS_HF_REPO = "akuysal/turkishSMS-ds"
TURKISHSMS_HF_REVISION = "66fde603d92a65c3942250535084971ac7ceffc7"
TURKISHSMS_FILES = {
    # local file name: (path inside the HF repo, expected SHA-256)
    "turkishsms_train.parquet": (
        "data/train-00000-of-00001-59e75adfecabf4d4.parquet",
        "c8eeff8c9fc706e6a320402dc091d85d17fcf8fa0f5869c5f46a0272d2473777",
    ),
    "turkishsms_validation.parquet": (
        "data/validation-00000-of-00001-806ae48564fe3c4c.parquet",
        "51c1c52f70598073c13f5fdff0e99b10de718813f590206a5bce1c7fafeb61f3",
    ),
}
# Original distribution pages from the paper; listed for manual download instructions.
TURKISHSMS_MANUAL_SOURCES = (
    "http://ceng.eskisehir.edu.tr/par/",
    "http://ceng.anadolu.edu.tr/par/",
)
TURKISHSMS_LABEL_MAP = {"legitimate": LABEL_LEGITIMATE, "spam": LABEL_MALICIOUS}

DOWNLOAD_TIMEOUT_SECONDS = 30

# --- Splitting -------------------------------------------------------------------------------
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15
SPLIT_NAMES = ("train", "val", "test")
