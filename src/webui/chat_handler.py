"""Bridge between Gradio callbacks and the rag_chat_v2 pipeline.

The CLI pipeline returns a result dictionary but does not expose the
retrieved chunks to the caller. ``chat_handler`` re-runs the same
retrieval functions to populate a ``sources`` list for the UI, so the
backend file is left untouched.
"""

from __future__ import annotations

from typing import Any

from rag_chat_v2 import answer_question
from retriever_v2 import retrieve as retrieve_v2_fn
from retriever_v4 import retrieve as retrieve_v4_fn


def _format_v2_sources(results: list[dict], limit: int) -> list[dict]:
    """Normalize retriever_v2 chunks into a UI-friendly shape."""
    sources = []
    for rank, r in enumerate(results[:limit], start=1):
        sources.append(
            {
                "rank": rank,
                "id": r.get("chunk_index"),
                "preview": (r.get("chunk", "") or "")[:240],
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
                "score": round(float(c.get("final_score", 0.0)), 3),
            }
        )
    return sources


def collect_sources(
    pipeline: dict,
    question: str,
    top_k: int,
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
            return _format_v2_sources(v2_hits, top_k)
    except Exception:
        pass

    try:
        v4 = retrieve_v4_fn(
            question, chunks, idx, df,
            final_top_k=top_k,
        )
        if v4 and v4.get("results"):
            return _format_v4_sources(v4, top_k)
    except Exception:
        pass

    return []


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

    sources = collect_sources(pipeline, question, top_k)

    confidence = result.get("confidence")
    if isinstance(confidence, (int, float)):
        confidence = float(confidence)
    else:
        confidence = None

    return {
        "question": question,
        "answer": result.get("answer", ""),
        "confidence": confidence,
        "supported": bool(result.get("supported", False)),
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
