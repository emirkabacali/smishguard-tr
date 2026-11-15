"""scikit-learn pipelines for the text model.

Features: TF-IDF over character n-grams (``char_wb``, 2-5) **and** word n-grams (1-2),
concatenated with a ``FeatureUnion``. Turkish is agglutinative ("kargonuz", "kargonuzu",
"kargoya" share the stem "kargo"), so character n-grams capture stems and suffixes that whole-word
features would treat as unrelated tokens; they also tolerate typos and missing Turkish letters.
"""

from __future__ import annotations

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import FeatureUnion, Pipeline

from smishguard import config
from smishguard.data.anonymize import mask_pii
from smishguard.data.normalize import ascii_fold, normalize_for_matching

MODEL_NAMES = ("logreg", "nb")


def preprocess(text: str) -> str:
    """Model-side text preparation: mask PII, normalize, Turkish lowercase, fold to ASCII.

    Defined at module level (not as a lambda) so that the fitted pipeline can be pickled.
    """
    return ascii_fold(normalize_for_matching(mask_pii(text)))


def build_features() -> FeatureUnion:
    """Return the char + word TF-IDF feature union."""
    char_tfidf = TfidfVectorizer(
        preprocessor=preprocess,
        analyzer="char_wb",
        ngram_range=config.CHAR_NGRAM_RANGE,
        min_df=config.TFIDF_MIN_DF,
        sublinear_tf=True,
    )
    word_tfidf = TfidfVectorizer(
        preprocessor=preprocess,
        analyzer="word",
        ngram_range=config.WORD_NGRAM_RANGE,
        min_df=config.TFIDF_MIN_DF,
        sublinear_tf=True,
        token_pattern=r"(?u)<?\b\w+\b>?",  # keep mask tokens such as <phone> intact
    )
    return FeatureUnion([("char", char_tfidf), ("word", word_tfidf)])


def build_pipeline(name: str = "logreg") -> Pipeline:
    """Build an unfitted pipeline.

    Args:
        name: ``"logreg"`` (Logistic Regression, the main model) or ``"nb"``
            (Multinomial Naive Bayes, a comparison baseline).

    Raises:
        ValueError: If ``name`` is unknown.
    """
    if name == "logreg":
        classifier = LogisticRegression(
            C=config.LOGREG_C,
            class_weight="balanced",
            max_iter=config.LOGREG_MAX_ITER,
            random_state=config.SEED,
        )
    elif name == "nb":
        classifier = MultinomialNB(alpha=config.NB_ALPHA)
    else:
        raise ValueError(f"Unknown model '{name}', expected one of {MODEL_NAMES}")
    return Pipeline([("features", build_features()), ("classifier", classifier)])
