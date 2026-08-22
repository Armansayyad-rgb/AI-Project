"""Minimal local API server for RALG Engine.

Run from the project root:

    uvicorn src.api_server:app --host 127.0.0.1 --port 8000

Then query:

    curl -X POST http://127.0.0.1:8000/query \
      -H "Content-Type: application/json" \
      -d "{\"question\":\"What safety step is required before opening the electrical panel?\",\"top_k\":5}"

Ingest text:

    curl -X POST http://127.0.0.1:8000/ingest \
      -H "Content-Type: application/json" \
      -d '{"text":"Your document text here...","document_name":"my_doc"}'

Check stats:

    curl http://127.0.0.1:8000/stats

Health check:

    curl http://127.0.0.1:8000/health
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
from webui.document_processor import (
    UploadedDocument,
    chunk_text,
    attach_documents,
)  # noqa: E402


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


class IngestRequest(BaseModel):
    text: str = Field(..., min_length=1)
    document_name: str | None = None


class IngestResponse(BaseModel):
    document_name: str
    added_chunks: int
    total_chunks: int


class StatsResponse(BaseModel):
    device: str
    model_loaded: bool
    chunk_count: int
    knowledge_files: list[str]
    uptime_seconds: float


app = FastAPI(
    title="RALG Engine API",
    version="0.1.0",
    description="Local evidence-grounded question answering API.",
)

_PIPELINE: dict[str, Any] | None = None
_START_TIME = time.perf_counter()


def get_pipeline() -> dict[str, Any]:
    global _PIPELINE
    if _PIPELINE is None:
        _PIPELINE = initialize_pipeline()
    return _PIPELINE


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/stats", response_model=StatsResponse)
def stats() -> StatsResponse:
    pipeline = get_pipeline()
    knowledge_files = [
        str(p) for p in Path("data").glob("*.txt")
    ] if Path("data").exists() else []
    return StatsResponse(
        device=pipeline.get("device", "unknown"),
        model_loaded=pipeline.get("model") is not None,
        chunk_count=len(pipeline.get("chunks", [])),
        knowledge_files=knowledge_files,
        uptime_seconds=round(time.perf_counter() - _START_TIME, 2),
    )


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


@app.post("/ingest", response_model=IngestResponse)
def ingest(request: IngestRequest) -> IngestResponse:
    """Ingest plain text content into the running pipeline.

    Chunks the text using the same logic as the static knowledge base,
    merges chunks into the pipeline, and rebuilds the retrieval index.
    """
    pipeline = get_pipeline()

    # Create a document record
    doc_name = request.document_name or f"doc_{int(time.time())}"
    doc = UploadedDocument(
        name=doc_name,
        path=Path(doc_name),
        ext=".txt",
        text=request.text,
    )

    # Chunk and attach
    doc.chunks = chunk_text(doc.text)
    doc.chunk_count = len(doc.chunks)

    added = attach_documents(pipeline, [doc])

    return IngestResponse(
        document_name=doc_name,
        added_chunks=added,
        total_chunks=len(pipeline.get("chunks", [])),
    )
