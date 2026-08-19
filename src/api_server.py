"""Minimal local API server for RALG Engine.

Run from the project root:

    uvicorn src.api_server:app --host 127.0.0.1 --port 8000

Then query:

    curl -X POST http://127.0.0.1:8000/query \
      -H "Content-Type: application/json" \
      -d "{\"question\":\"What safety step is required before opening the electrical panel?\",\"top_k\":5}"
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from rag_chat_v2 import answer_question, initialize_pipeline  # noqa: E402
from webui.chat_handler import collect_sources  # noqa: E402


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    include_sources: bool = True


class QueryResponse(BaseModel):
    answer: str
    supported: bool
    confidence: float | None
    answer_type: str
    sources: list[dict[str, Any]]
    latency_ms: float
    error: str | None = None


app = FastAPI(
    title="RALG Engine API",
    version="0.1.0",
    description="Local evidence-grounded question answering API.",
)

_PIPELINE: dict[str, Any] | None = None


def get_pipeline() -> dict[str, Any]:
    global _PIPELINE
    if _PIPELINE is None:
        _PIPELINE = initialize_pipeline()
    return _PIPELINE


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    started = time.perf_counter()
    pipeline = get_pipeline()

    try:
        result = answer_question(
            pipeline,
            request.question.strip(),
            verbose=False,
        )
        sources = (
            collect_sources(
                pipeline,
                request.question.strip(),
                request.top_k,
            )
            if request.include_sources
            else []
        )

        confidence = result.get("confidence")
        if not isinstance(confidence, (int, float)):
            confidence = None

        return QueryResponse(
            answer=str(result.get("answer", "")),
            supported=bool(result.get("supported", False)),
            confidence=float(confidence) if confidence is not None else None,
            answer_type=str(result.get("answer_type", "unknown")),
            sources=sources,
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
        )

    except Exception as exc:
        return QueryResponse(
            answer="",
            supported=False,
            confidence=None,
            answer_type="error",
            sources=[],
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
            error=repr(exc),
        )
