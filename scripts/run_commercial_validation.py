#!/usr/bin/env python3
"""Run the held-out commercial validation through the in-process FastAPI app."""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src import api_server  # noqa: E402

DATASET = PROJECT_ROOT / "evaluation" / "heldout_commercial_v1.json"
OUTPUT = PROJECT_ROOT / "logs" / "heldout_commercial_v1_results.json"
ABSTENTION_TEXT = "couldn't find enough reliable evidence"


def contains(text: str, term: str) -> bool:
    return term.casefold() in text.casefold()


def percentile_95(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, round(0.95 * (len(ordered) - 1))))
    return ordered[index]


def main() -> int:
    dataset = json.loads(DATASET.read_text(encoding="utf-8"))
    api_server._PIPELINE = None
    client = TestClient(api_server.app)

    for document in dataset["documents"]:
        response = client.post(
            "/ingest",
            json={"text": document["text"], "document_name": document["name"]},
        )
        response.raise_for_status()

    results = []
    for case in dataset["cases"]:
        response = client.post(
            "/query",
            json={"question": case["question"], "top_k": 5, "include_sources": True},
        )
        response.raise_for_status()
        payload = response.json()
        answer = payload.get("answer") or ""
        sources = payload.get("sources") or []
        source_text = " ".join(source.get("preview") or "" for source in sources)

        expected_supported = bool(case["supported"])
        actual_supported = bool(payload.get("supported"))
        groups = case.get("required_answer_groups", [])
        answer_complete = expected_supported and actual_supported and all(
            any(contains(answer, term) for term in group) for group in groups
        )
        source_terms = case.get("required_source_terms", [])
        retrieval_correct = expected_supported and bool(sources) and all(
            contains(source_text, term) for term in source_terms
        )
        safely_abstained = (
            not expected_supported
            and not actual_supported
            and contains(answer, ABSTENTION_TEXT)
        )

        results.append(
            {
                "id": case["id"],
                "expected_supported": expected_supported,
                "actual_supported": actual_supported,
                "answer": answer,
                "answer_type": payload.get("answer_type"),
                "retrieval_correct": retrieval_correct,
                "answer_complete": answer_complete,
                "safely_abstained": safely_abstained,
                "source_count": len(sources),
                "top_source": sources[0] if sources else None,
                "latency_ms": float(payload.get("latency_ms") or 0.0),
                "error": payload.get("error"),
            }
        )

    supported = [item for item in results if item["expected_supported"]]
    unsupported = [item for item in results if not item["expected_supported"]]
    latencies = [item["latency_ms"] for item in results]
    false_supports = sum(item["actual_supported"] for item in unsupported)
    metrics = {
        "dataset": dataset["name"],
        "cases": len(results),
        "retrieval_correctness": sum(item["retrieval_correct"] for item in supported) / len(supported),
        "answer_completeness": sum(item["answer_complete"] for item in supported) / len(supported),
        "unsupported_rejection": sum(not item["actual_supported"] for item in unsupported) / len(unsupported),
        "safe_abstention": sum(item["safely_abstained"] for item in unsupported) / len(unsupported),
        "false_support_rate": false_supports / len(unsupported),
        "average_latency_ms": statistics.fmean(latencies),
        "p95_latency_ms": percentile_95(latencies),
        "runtime_errors": sum(item["error"] is not None for item in results),
    }
    report = {"metrics": metrics, "results": results}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(metrics, indent=2))
    for item in results:
        print(
            f"{item['id']}: supported={item['actual_supported']} "
            f"retrieval={item['retrieval_correct']} complete={item['answer_complete']} "
            f"abstained={item['safely_abstained']} latency_ms={item['latency_ms']:.2f}"
        )
    print(f"results={OUTPUT}")
    return 0 if metrics["runtime_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
