"""Bridge between Gradio callbacks and the rag_chat_v2 pipeline.

The CLI pipeline returns a result dictionary but does not expose the
retrieved chunks to the caller. ``chat_handler`` re-runs the same
retrieval functions to populate a ``sources`` list for the UI, so the
backend file is left untouched.
"""

from __future__ import annotations

import re
from typing import Any

from rag_chat_v2 import answer_question
from retriever_v2 import retrieve as retrieve_v2_fn
from retriever_v4 import retrieve as retrieve_v4_fn


_TRACEABILITY_STOPWORDS = {
    "about", "after", "again", "also", "around", "because", "been",
    "being", "between", "both", "could", "does", "each", "from", "has",
    "have", "into", "more", "most", "other", "over", "same", "some",
    "such", "than", "that", "their", "there", "these", "they", "this",
    "those", "through", "under", "were", "which", "while", "with",
    "would", "your", "what", "when", "where", "who", "why", "how",
    "answer", "following", "several", "important", "ways", "main", "was",
    "are", "and", "the", "for", "not", "but", "its", "all", "can", "also",
}


def _traceability_terms(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]{3,}", (text or "").casefold())
        if token not in _TRACEABILITY_STOPWORDS
    }


def evidence_overlap(answer: str, sources: list[dict]) -> int:
    """Count distinct content terms shared by an answer and its previews."""
    answer_terms = _traceability_terms(answer)
    source_terms = _traceability_terms(
        " ".join(
            str(source.get("evidence") or source.get("preview", ""))
            for source in sources
        )
    )
    return len(answer_terms & source_terms)


def is_traceable_support(answer: str, supported: bool, sources: list[dict]) -> bool:
    """Require source presence and meaningful lexical evidence for support."""
    if not supported or not answer.strip() or not sources:
        return False
    required_terms = 1 if len(_traceability_terms(answer)) <= 4 else 2
    return evidence_overlap(answer, sources) >= required_terms


def _format_v2_sources(results: list[dict], limit: int) -> list[dict]:
    """Normalize retriever_v2 chunks into a UI-friendly shape."""
    sources = []
    for rank, r in enumerate(results[:limit], start=1):
        sources.append(
            {
                "rank": rank,
                "id": r.get("chunk_index"),
                "preview": (r.get("chunk", "") or "")[:240],
                "evidence": r.get("chunk", "") or "",
                "score": round(float(r.get("final_score", 0.0)), 3),
            }
        )
    return sources


def _format_v4_sources(retrieval: dict, limit: int) -> list[dict]:
    """Normalize retriever_v4 results into a UI-friendly shape."""
    chunks = (retrieval or {}).get("results") or []
    sources = []
    for rank, c in enumerate(chunks[:limit], start=1):
        sources.append(
            {
                "rank": rank,
                "id": c.get("chunk_index"),
                "preview": (c.get("chunk", "") or "")[:240],
                "evidence": c.get("chunk", "") or "",
                "score": round(float(c.get("final_score", 0.0)), 3),
            }
        )
    return sources


def collect_sources(
    pipeline: dict,
    question: str,
    top_k: int,
    answer: str | None = None,
) -> list[dict]:
    """Run the V2 extractor retriever to grab source chunks.

    The extractor path is the cheapest retrieval that produces
    ``chunk_index``/``final_score`` pairs and matches the chunks that
    surface as citations in the answer. If nothing matches, falls
    back to the V4 reasoning retriever.
    """
    chunks = pipeline["chunks"]
    idx = pipeline["retrieval_index"]
    df = pipeline["document_frequency"]

    try:
        v2_hits = retrieve_v2_fn(
            question, chunks, idx, df, final_top_k=top_k
        )
        if v2_hits:
            v2_sources = _format_v2_sources(v2_hits, top_k)
            if answer is None or is_traceable_support(answer, True, v2_sources):
                return v2_sources
        else:
            v2_sources = []
    except Exception:
        v2_sources = []

    try:
        v4 = retrieve_v4_fn(
            question, chunks, idx, df,
            final_top_k=top_k,
        )
        if v4 and v4.get("results"):
            v4_sources = _format_v4_sources(v4, top_k)
            if answer is None or is_traceable_support(answer, True, v4_sources):
                return v4_sources
    except Exception:
        pass

    return v2_sources


def chat_turn(
    pipeline: dict,
    question: str,
    top_k: int,
) -> dict[str, Any]:
    """Run one Q&A turn and return UI-ready fields.

    Returned keys:

    - question      the user input (echoed for the caller)
    - answer        assistant text from the pipeline
    - confidence    float | None
    - supported     bool
    - answer_type   str
    - intent        str
    - sources       list of {rank, id, preview, score}
    - error         str | None  (set on unexpected failure)
    """
    if not question or not question.strip():
        return {
            "question": question,
            "answer": "Please enter a question.",
            "confidence": None,
            "supported": False,
            "answer_type": "empty",
            "intent": "general",
            "sources": [],
            "error": None,
        }

    try:
        result = answer_question(pipeline, question.strip(), verbose=False)
    except Exception as exc:  # defensive — surface to UI instead of crashing
        return {
            "question": question,
            "answer": (
                "Sorry, something went wrong while answering. "
                "Please try again."
            ),
            "confidence": None,
            "supported": False,
            "answer_type": "error",
            "intent": "general",
            "sources": [],
            "error": repr(exc),
        }

    plan = result.get("runtime_plan") or {}
    intent = plan.get("intent") or "general"

    sources = collect_sources(pipeline, question, top_k, answer=result.get("answer", ""))
    supported = is_traceable_support(
        str(result.get("answer", "")), bool(result.get("supported", False)), sources
    )

    confidence = result.get("confidence")
    if isinstance(confidence, (int, float)):
        confidence = float(confidence)
    else:
        confidence = None

    return {
        "question": question,
        "answer": result.get("answer", ""),
        "confidence": confidence,
        "supported": supported,
        "answer_type": result.get("answer_type", "unknown"),
        "intent": intent,
        "sources": sources,
        "error": None,
    }


def format_sources_markdown(sources: list[dict]) -> str:
    """Render a sources list as a small markdown block for the chat bubble.

    Kept compact: one line per source with the score and a short
    snippet. Long snippets are truncated with an ellipsis so a long
    sources list does not dominate the answer bubble.
    """
    if not sources:
        return ""
    lines = ["", "<details><summary>**Sources**</summary>", ""]
    for s in sources:
        snippet = s.get("preview", "").strip().replace("\n", " ")
        if len(snippet) > 160:
            snippet = snippet[:160].rstrip() + "..."
        lines.append(
            f"- `[{s['rank']}]` chunk **{s.get('id')}** "
            f"(score {s.get('score')}): {snippet}"
        )
    lines.append("")
    lines.append("</details>")
    return "\n".join(lines)
