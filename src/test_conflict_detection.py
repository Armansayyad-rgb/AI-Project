"""Focused checks for conservative handling of conflicting evidence."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src import api_server  # noqa: E402
from src.webui.chat_handler import detect_evidence_conflict  # noqa: E402
from retriever_v2 import build_index  # noqa: E402


def sources(*texts):
    return [
        {"rank": rank, "id": None, "score": 10.0 - rank, "evidence": text}
        for rank, text in enumerate(texts, start=1)
    ]


class ConflictDetectionTests(unittest.TestCase):
    def test_conflicting_numeric_values(self):
        self.assertTrue(
            detect_evidence_conflict(
                "What is the pump pressure limit?",
                sources(
                    "The pump pressure limit is 10 PSI.",
                    "The pump pressure limit is 20 PSI.",
                ),
            )
        )

    def test_conflicting_dates(self):
        self.assertTrue(
            detect_evidence_conflict(
                "What is the inspection date?",
                sources(
                    "The inspection date is 2024-05-01.",
                    "The inspection date is 2025-05-01.",
                ),
            )
        )

    def test_conflicting_named_identifiers(self):
        self.assertTrue(
            detect_evidence_conflict(
                "What is the installed unit identifier?",
                sources(
                    "The installed unit identifier is UNIT-A12.",
                    "The installed unit identifier is UNIT-B14.",
                ),
            )
        )

    def test_conflicting_operational_instructions(self):
        self.assertTrue(
            detect_evidence_conflict(
                "What should the operator do before startup?",
                sources(
                    "Before startup, the operator must open the isolation valve.",
                    "Before startup, the operator must close the isolation valve.",
                ),
            )
        )

    def test_equivalent_paraphrases_are_not_conflicts(self):
        self.assertFalse(
            detect_evidence_conflict(
                "What is the pump pressure limit?",
                sources(
                    "The pump pressure limit is 10 PSI.",
                    "Pump pressure must not exceed 10 pounds per square inch.",
                ),
            )
        )

    def test_complementary_evidence_is_not_a_conflict(self):
        self.assertFalse(
            detect_evidence_conflict(
                "What are the pump operating limits?",
                sources(
                    "The pump pressure limit is 10 PSI.",
                    "The pump temperature limit is 80 C.",
                ),
            )
        )

    def test_opposing_actions_on_different_objects_are_not_a_conflict(self):
        self.assertFalse(
            detect_evidence_conflict(
                "What should the operator do during startup?",
                sources(
                    "During startup, the operator must open the inlet valve.",
                    "During startup, the operator must close the drain valve.",
                ),
            )
        )

    def test_unrelated_evidence_is_not_a_conflict(self):
        self.assertFalse(
            detect_evidence_conflict(
                "What is the pump pressure limit?",
                sources(
                    "The pump pressure limit is 10 PSI.",
                    "The battery identifier is UNIT-B14 and its voltage is 24 V.",
                ),
            )
        )

    def test_runtime_ingested_conflict_returns_conservative_response(self):
        pipeline = {"chunks": []}
        pipeline["retrieval_index"], pipeline["document_frequency"] = build_index([])
        client = TestClient(api_server.app, raise_server_exceptions=False)
        generated = {
            "answer": "The pump pressure limit is 10 PSI.",
            "supported": True,
            "answer_type": "factual",
        }
        with patch.object(api_server, "get_pipeline", return_value=pipeline), patch.object(
            api_server, "answer_question", return_value=generated
        ):
            self.assertEqual(
                client.post(
                    "/ingest",
                    json={"text": "The pump pressure limit is 10 PSI.", "document_name": "card_a"},
                ).status_code,
                200,
            )
            self.assertEqual(
                client.post(
                    "/ingest",
                    json={"text": "The pump pressure limit is 20 PSI.", "document_name": "card_b"},
                ).status_code,
                200,
            )
            response = client.post(
                "/query", json={"question": "What is the pump pressure limit?", "top_k": 5}
            )
        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(payload["supported"])
        self.assertEqual(payload["answer_type"], "conflict")
        self.assertIn("conflicting evidence", payload["answer"])
        self.assertGreaterEqual(len(payload["sources"]), 2)


if __name__ == "__main__":
    unittest.main()
