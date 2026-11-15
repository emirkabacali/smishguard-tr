"""REST API.

Run locally:
    uvicorn smishguard.api.main:app --reload

Endpoints:
    GET  /health       service and model status
    POST /v1/analyze   risk score, level and reasons for one SMS

The model is loaded once at startup (lifespan), not on every request. If it is missing, the
service still starts so that /health can report the problem, and /v1/analyze returns 503.
Message texts are never logged; only their length and the resulting score.

Note: this module deliberately does *not* use ``from __future__ import annotations``. FastAPI
reads the type hints of endpoint functions at runtime to build dependencies, and string
annotations that refer to the local ``get_analyzer`` function could not be resolved.
"""

import logging
import os
import time
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

from smishguard import __version__
from smishguard.analyzer import Analyzer
from smishguard.api.schemas import AnalyzeRequest, AnalyzeResponse, HealthResponse, ReasonOut

logger = logging.getLogger("smishguard.api")

AnalyzerLoader = Callable[[], Analyzer]

DESCRIPTION = (
    "Explainable smishing (SMS phishing) risk analysis for Turkish messages. "
    "Research / portfolio project, **not** a production security product. "
    "Links are analyzed as text only and never visited."
)


def configure_logging() -> None:
    """Send ``smishguard.*`` logs to stderr as ``key=value`` lines.

    uvicorn only configures its own loggers, so without this the application's log lines
    would be dropped. The level comes from ``SMISHGUARD_LOG_LEVEL`` (default INFO).
    """
    package_logger = logging.getLogger("smishguard")
    if not package_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s level=%(levelname)s logger=%(name)s %(message)s")
        )
        package_logger.addHandler(handler)
    package_logger.setLevel(os.environ.get("SMISHGUARD_LOG_LEVEL", "INFO").upper())


def create_app(loader: AnalyzerLoader = Analyzer.from_files) -> FastAPI:
    """Build the FastAPI application.

    Args:
        loader: Function that returns a ready :class:`Analyzer`. Tests inject a small
            fixture model here; production loads the trained model from disk.
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        configure_logging()
        try:
            app.state.analyzer = loader()
            logger.info("model_loaded version=%s", app.state.analyzer.model_version)
        except FileNotFoundError as exc:
            app.state.analyzer = None
            logger.warning("model_missing detail=%s", exc)
        yield
        app.state.analyzer = None

    app = FastAPI(
        title="SmishGuard-TR API",
        version=__version__,
        description=DESCRIPTION,
        lifespan=lifespan,
    )

    def get_analyzer(request: Request) -> Analyzer:
        analyzer = getattr(request.app.state, "analyzer", None)
        if analyzer is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Model is not loaded. Train it with `python scripts/train.py`.",
            )
        return analyzer

    @app.get("/health", response_model=HealthResponse, tags=["system"])
    def health(request: Request) -> JSONResponse:
        """Report whether the service can analyze messages."""
        loaded = getattr(request.app.state, "analyzer", None) is not None
        body = HealthResponse(
            status="ok" if loaded else "unavailable", model_loaded=loaded, version=__version__
        )
        code = status.HTTP_200_OK if loaded else status.HTTP_503_SERVICE_UNAVAILABLE
        return JSONResponse(status_code=code, content=body.model_dump())

    @app.post("/v1/analyze", response_model=AnalyzeResponse, tags=["analysis"])
    def analyze(
        payload: AnalyzeRequest, analyzer: Annotated[Analyzer, Depends(get_analyzer)]
    ) -> AnalyzeResponse:
        """Analyze one SMS and explain the result."""
        started = time.perf_counter()
        result = analyzer.analyze(payload.text)
        logger.info(
            "analyze length=%d risk_score=%.4f risk_level=%s reasons=%d latency_ms=%.1f",
            len(payload.text),
            result.risk_score,
            result.risk_level,
            len(result.reasons),
            (time.perf_counter() - started) * 1000,
        )
        return AnalyzeResponse(
            risk_score=result.risk_score,
            risk_level=result.risk_level,
            ml_probability=result.ml_probability,
            rule_score=result.rule_score,
            reasons=[
                ReasonOut(code=r.code, weight=r.weight, message=r.message) for r in result.reasons
            ],
            model_version=result.model_version,
        )

    return app


app = create_app()
