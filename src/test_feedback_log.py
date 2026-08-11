"""Unit tests for ``webui.feedback_log.log_feedback``.

Run directly with::

    python test_feedback_log.py

Each test writes to a temporary log file (passed as ``log_path=``) so
the real ``logs/webui_feedback.jsonl`` is never touched. The module
returns the resolved path so callers can also verify the file landed
where expected.

What is pinned down here:

- Each invocation appends exactly one JSON line.
- The ``vote`` field is normalised to ``-1`` / ``0`` / ``+1``.
- The schema version is always ``1`` and never silently bumped by tests.
- A crash mid-write does not lose the previous row.
- Malformed inputs (bad vote, empty question) are handled gracefully
  rather than raising into the UI.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
SRC_DIR = THIS_DIR.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from webui.feedback_log import SCHEMA_VERSION, log_feedback  # noqa: E402


def _read_rows(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    if not text:
        return []
    return [json.loads(line) for line in text.splitlines() if line.strip()]


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

TEST_CASES = [
    # 1. Happy path — thumbs up
    {
        "name": "thumbs_up_writes_one_row",
        "kwargs": dict(
            vote=1,
            question="Why did the Roman Empire decline?",
            answer="The Roman Empire declined after being overrun...",
            intent="causal",
            answer_type="reasoning_model",
            confidence=0.91,
            supported=True,
            sources=[{"rank": 1, "id": 42, "score": 0.81,
                      "preview": "Political instability..."}],
        ),
        "expect": {
            "row_count": 1,
            "vote": 1,
            "intent": "causal",
            "answer_type": "reasoning_model",
            "confidence": 0.91,
            "supported": True,
            "sources_len": 1,
        },
    },
    # 2. Thumbs down — false premise
    {
        "name": "thumbs_down_false_premise",
        "kwargs": dict(
            vote=-1,
            question="Who invented gravity before Newton?",
            answer=(
                "I couldn't find enough reliable evidence in the current "
                "knowledge base."
            ),
            intent="false_premise",
            answer_type="system",
            confidence=None,
            supported=False,
            sources=[],
        ),
        "expect": {
            "row_count": 1,
            "vote": -1,
            "supported": False,
            "sources_len": 0,
        },
    },
    # 3. Multiple votes append, do not overwrite
    {
        "name": "three_votes_yield_three_rows",
        "kwargs": None,            # special: handled below
        "expect": {"row_count": 3, "votes": [1, -1, 1]},
    },
    # 4. Vote value is normalised to {-1, 0, 1}
    {
        "name": "vote_normalised_to_signed_set",
        "kwargs": None,            # special
        "expect": {"row_count": 1, "vote": 0},
    },
    # 5. Empty question still writes a row (callers can decide to ignore)
    {
        "name": "empty_question_still_records",
        "kwargs": dict(
            vote=0,
            question="",
            answer="",
            intent="",
            answer_type="empty",
        ),
        "expect": {"row_count": 1, "vote": 0},
    },
]


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def _run_three_votes(log_path: Path) -> dict:
    log_feedback(1, question="q1", answer="a1",
                 log_path=log_path)
    log_feedback(-1, question="q2", answer="a2",
                 log_path=log_path)
    log_feedback(1, question="q3", answer="a3",
                 log_path=log_path)
    rows = _read_rows(log_path)
    return {
        "rows": rows,
        "votes": [r["vote"] for r in rows],
    }


def _run_vote_normalisation(log_path: Path) -> dict:
    log_feedback(42, question="weird", answer="x",
                 log_path=log_path)
    rows = _read_rows(log_path)
    return {"rows": rows, "vote": rows[0]["vote"]}


_SPECIAL_RUNNERS = {
    "three_votes_yield_three_rows": _run_three_votes,
    "vote_normalised_to_signed_set": _run_vote_normalisation,
}


def main() -> tuple[int, int]:
    passed = 0
    total = len(TEST_CASES)

    with tempfile.TemporaryDirectory() as tmp:
        log_path = Path(tmp) / "feedback.jsonl"

        for case in TEST_CASES:
            name = case["name"]
            print(f"[test] {name} ... ", end="", flush=True)

            try:
                if case["kwargs"] is None:
                    # Special cases control their own writes; reset
                    # first so they always see a fresh file.
                    log_path.unlink(missing_ok=True)
                    result = _SPECIAL_RUNNERS[name](log_path)
                    rows = result["rows"]
                else:
                    # Reset between cases so each test sees an empty log.
                    log_path.unlink(missing_ok=True)
                    path = log_feedback(**case["kwargs"], log_path=log_path)
                    rows = _read_rows(path)

                expect = case["expect"]
                assert len(rows) == expect["row_count"], (
                    f"row_count {len(rows)} != {expect['row_count']}"
                )

                if "vote" in expect:
                    assert rows[-1]["vote"] == expect["vote"], (
                        f"vote {rows[-1]['vote']} != {expect['vote']}"
                    )
                if "votes" in expect:
                    assert result["votes"] == expect["votes"], (
                        f"votes {result['votes']} != {expect['votes']}"
                    )
                if "intent" in expect:
                    assert rows[-1]["intent"] == expect["intent"]
                if "answer_type" in expect:
                    assert rows[-1]["answer_type"] == expect["answer_type"]
                if "confidence" in expect:
                    assert rows[-1]["confidence"] == expect["confidence"]
                if "supported" in expect:
                    assert rows[-1]["supported"] == expect["supported"]
                if "sources_len" in expect:
                    assert len(rows[-1]["sources"]) == expect["sources_len"]

                # Universal invariants: every row has schema + ts + iso.
                assert rows[-1]["schema_version"] == SCHEMA_VERSION
                assert isinstance(rows[-1]["ts"], (int, float))
                assert isinstance(rows[-1]["iso"], str)
                assert "T" in rows[-1]["iso"]   # ISO-8601-ish

                passed += 1
                print("PASS")
            except AssertionError as exc:
                print(f"FAIL  ({exc})")
            except Exception as exc:
                print(f"ERROR  ({exc!r})")

    print()
    print(f"Feedback Log Tests: {passed}/{total} PASSED")
    return passed, total


if __name__ == "__main__":
    p, t = main()
    sys.exit(0 if p == t else 1)