"""Single entry point for inference, shared by the API and the demo UI.

Flow: clean text -> mask PII -> text model probability + rule engine -> fusion -> level.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from sklearn.pipeline import Pipeline

from smishguard import __version__, config
from smishguard.data.anonymize import mask_pii
from smishguard.data.normalize import clean_text
from smishguard.features.reasons import Reason, evaluate_rules, rule_score
from smishguard.model.predict import load_model, predict_proba
from smishguard.scoring.fusion import FusionParams, RiskLevel, fuse, load_fusion_params, risk_level


@dataclass(frozen=True)
class AnalysisResult:
    """Everything the system knows about one message."""

    risk_score: float
    risk_level: RiskLevel
    ml_probability: float
    rule_score: float
    reasons: tuple[Reason, ...]
    model_version: str


class Analyzer:
    """Analyze SMS messages with the fused ML + rule system.

    Args:
        model: A fitted text-model pipeline.
        params: Fusion weight and thresholds.
        model_version: Version string reported with every result.
    """

    def __init__(
        self, model: Pipeline, params: FusionParams | None = None, model_version: str = __version__
    ) -> None:
        self.model = model
        self.params = params or FusionParams()
        self.model_version = model_version

    @classmethod
    def from_files(
        cls,
        model_path: Path = config.TEXT_MODEL_PATH,
        metadata_path: Path = config.MODEL_METADATA_PATH,
        fusion_path: Path = config.FUSION_PARAMS_PATH,
    ) -> Analyzer:
        """Load the trained model, its metadata and the tuned fusion parameters.

        Raises:
            FileNotFoundError: If the model file does not exist.
        """
        model = load_model(model_path)
        version = __version__
        if metadata_path.exists():
            version = json.loads(metadata_path.read_text(encoding="utf-8")).get(
                "model_version", version
            )
        return cls(model, load_fusion_params(fusion_path), version)

    @staticmethod
    def prepare(text: str) -> str:
        """Apply the same cleaning and PII masking that was used to build the dataset."""
        return mask_pii(clean_text(text))

    def analyze(self, text: str) -> AnalysisResult:
        """Analyze a single message."""
        return self.analyze_batch([text])[0]

    def analyze_batch(self, texts: Sequence[str]) -> list[AnalysisResult]:
        """Analyze several messages at once (one vectorized model call)."""
        prepared = [self.prepare(text) for text in texts]
        probabilities = predict_proba(self.model, prepared) if prepared else []
        results = []
        for text, probability in zip(prepared, probabilities, strict=True):
            reasons = tuple(evaluate_rules(text))
            rules = rule_score(reasons)
            score = round(fuse(float(probability), rules, self.params.alpha), 4)
            results.append(
                AnalysisResult(
                    risk_score=score,
                    risk_level=risk_level(score, self.params),
                    ml_probability=round(float(probability), 4),
                    rule_score=rules,
                    reasons=reasons,
                    model_version=self.model_version,
                )
            )
        return results
