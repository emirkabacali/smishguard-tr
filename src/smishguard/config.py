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

# --- Text model --------------------------------------------------------------------------
CHAR_NGRAM_RANGE = (2, 5)
WORD_NGRAM_RANGE = (1, 2)
TFIDF_MIN_DF = 1
LOGREG_C = 1.0
LOGREG_MAX_ITER = 2000
NB_ALPHA = 0.1
CV_FOLDS = 5
# Model order = preference order. A later model must beat the preferred one by more than this
# validation-F1 margin (about one message on a ~110-message validation set) to be selected.
MODEL_SELECTION_TOLERANCE = 0.01
# Probability above which the text model alone calls a message malicious.
ML_DECISION_THRESHOLD = 0.5

TEXT_MODEL_PATH = MODELS_DIR / "text_model.joblib"
MODEL_METADATA_PATH = MODELS_DIR / "metadata.json"
BASELINE_METRICS_PATH = REPORTS_DIR / "metrics_baseline.json"
TOP_FEATURES_COUNT = 20

# --- Rule engine -------------------------------------------------------------------------
# Weight of each rule. rule_score = min(1.0, sum of the weights of the rules that fired).
RULE_WEIGHTS = {
    # URL-based
    "BRAND_IMPERSONATION": 0.35,
    "IP_IN_URL": 0.30,
    "PUNYCODE": 0.30,
    "SHORTENER": 0.20,
    "SUSPICIOUS_TLD": 0.20,
    "EXCESSIVE_HYPHENS_DIGITS": 0.10,
    # Text-based
    "CREDENTIAL_REQUEST": 0.30,
    "PRIZE_CLAIM": 0.20,
    "URGENCY_LANGUAGE": 0.15,
    "ADDRESS_ISSUE": 0.15,
    "MONEY_OR_FINE": 0.10,
}

URL_SHORTENERS = frozenset(
    {
        "bit.ly",
        "cutt.ly",
        "goo.gl",
        "is.gd",
        "ow.ly",
        "rb.gy",
        "rebrand.ly",
        "s.id",
        "shorturl.at",
        "t.co",
        "t.ly",
        "tiny.cc",
        "tinyurl.com",
        "v.gd",
    }
)

# Top-level domains that are cheap to register and over-represented in scam campaigns.
SUSPICIOUS_TLDS = frozenset(
    {
        "buzz",
        "cfd",
        "click",
        "club",
        "icu",
        "info",
        "link",
        "live",
        "monster",
        "online",
        "rest",
        "sbs",
        "shop",
        "site",
        "store",
        "top",
        "vip",
        "work",
        "xyz",
    }
)

# Domains written without "http://" or "www." are only recognized for these TLDs, so that
# sentences without a space after the period ("geldi.de") are not mistaken for links.
BARE_DOMAIN_TLDS = SUSPICIOUS_TLDS | {
    "com",
    "net",
    "org",
    "tr",
    "io",
    "co",
    "me",
    "ly",
    "biz",
    "cc",
}

# Brand keywords looked for inside link hostnames (ASCII-folded). Short keywords (<= 4 chars)
# must start or end a hostname label to avoid accidental matches ("aras" in "paras").
BRAND_KEYWORDS = (
    "akbank",
    "aras",
    "denizbank",
    "edevlet",
    "e-devlet",
    "enerjisa",
    "garanti",
    "getir",
    "gib",
    "halkbank",
    "hepsiburada",
    "hgs",
    "isbank",
    "kgm",
    "migros",
    "mng",
    "netflix",
    "ogs",
    "ptt",
    "sahibinden",
    "sgk",
    "trendyol",
    "turkcell",
    "turkiye",
    "turktelekom",
    "vakifbank",
    "vodafone",
    "yapikredi",
    "yurtici",
    "ziraat",
)
SHORT_BRAND_MAX_LENGTH = 4

# Registered domains that legitimately carry a brand name.
OFFICIAL_DOMAINS = frozenset(
    {
        "akbank.com",
        "araskargo.com.tr",
        "denizbank.com",
        "enerjisa.com.tr",
        "garantibbva.com.tr",
        "getir.com",
        "halkbank.com.tr",
        "hepsiburada.com",
        "isbank.com.tr",
        "migros.com.tr",
        "mngkargo.com.tr",
        "netflix.com",
        "sahibinden.com",
        "trendyol.com",
        "turkcell.com.tr",
        "turktelekom.com.tr",
        "vakifbank.com.tr",
        "vodafone.com.tr",
        "yapikredi.com.tr",
        "yurticikargo.com",
        "ziraatbank.com.tr",
    }
)
# Second-level zones whose registration is restricted to Turkish institutions.
OFFICIAL_SUFFIXES = frozenset({"gov.tr", "edu.tr", "bel.tr", "pol.tr", "tsk.tr", "k12.tr"})

MAX_DOMAIN_HYPHENS = 2  # a registered domain label with >= this many hyphens is suspicious
MAX_DOMAIN_DIGITS = 3  # ... or with >= this many digits

# Text rules: regular expressions matched on Turkish-lowercased, ASCII-folded text.
# Patterns are stems anchored on the left, so Turkish suffixes still match
# ("ceza" matches "cezaniz", "cezali"). "exclude" patterns veto the rule.
TEXT_RULES = {
    "URGENCY_LANGUAGE": {
        "patterns": (
            r"\b\d{1,2} saat (?:icinde|icerisinde)",
            r"\bson (?:gun|\d+ saat|firsat)",
            r"\bhemen\b",
            r"\bacil\b",
            r"\bderhal\b",
            r"\baksi (?:halde|takdirde)",
            r"\b(?:iptal|bloke|askiya|kapatil|kesil)\w*",
        ),
        "exclude": (),
    },
    "MONEY_OR_FINE": {
        "patterns": (
            r"\bceza",
            r"\bborc",
            r"\bodeme",
            r"\bodey",
            r"\bucret",
            r"\biade",
            r"\btazminat",
            r"\d\s?tl\b",
            r"\btl\b",
        ),
        "exclude": (),
    },
    "CREDENTIAL_REQUEST": {
        "patterns": (
            r"\bsifre",
            r"\bparola",
            r"\bkart bilgi",
            r"\bkredi karti bilgi",
            r"\b(?:dogrulama|onay|guvenlik) kod",
            r"\bcvv\b",
            r"\bkimlik (?:bilgi|dogrula|no)",
            r"\btc kimlik",
        ),
        # Legitimate OTP messages warn the reader *not* to share the code.
        "exclude": (r"\bkimse(?:yle| ile)? paylasma", r"\bpaylasmayin"),
    },
    "PRIZE_CLAIM": {
        "patterns": (
            r"\bkazandin",
            r"\bhediye",
            r"\bcekilis",
            r"\bodul",
            r"\bbedava\b",
            r"\bikramiye",
        ),
        "exclude": (),
    },
    "ADDRESS_ISSUE": {
        "patterns": (
            r"\badres\w* (?:eksik|hatali|yanlis|bilgi|guncelle|dogrula)",
            r"\bteslim edilemed",
            r"\bteslim edilemeyen",
            r"\bdagitima cikamad",
            r"\bgumruk",
            r"\bdepoda bekle",
        ),
        "exclude": (),
    },
}

RULE_MESSAGES = {
    "BRAND_IMPERSONATION": (
        "Domain imitates a known brand ({detail}) but is not an official domain."
    ),
    "IP_IN_URL": "Link points to a raw IP address ({detail}) instead of a domain name.",
    "PUNYCODE": "Link uses a punycode (xn--) domain that can imitate other characters ({detail}).",
    "SHORTENER": "Link uses a URL shortener ({detail}) that hides the real destination.",
    "SUSPICIOUS_TLD": "Link uses a TLD frequently abused in scams (.{detail}).",
    "EXCESSIVE_HYPHENS_DIGITS": "Domain contains many hyphens or digits ({detail}).",
    "CREDENTIAL_REQUEST": "Message asks for passwords, card details or verification codes.",
    "PRIZE_CLAIM": "Message claims the reader won a prize or gift.",
    "URGENCY_LANGUAGE": "Message pressures the reader to act quickly.",
    "ADDRESS_ISSUE": "Message claims a delivery or address problem.",
    "MONEY_OR_FINE": "Message mentions a payment, debt, fine or refund.",
}
