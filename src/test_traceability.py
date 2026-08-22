"""Generic evidence-traceability checks for supported API answers."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src import api_server  # noqa: E402
from src.webui.chat_handler import (  # noqa: E402
    evidence_overlap,
    is_traceable_support,
)


class TraceabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        api_server._PIPELINE = None
        cls.client = TestClient(api_server.app, raise_server_exceptions=False)

    def assert_supported_is_grounded(self, payload):
        self.assertTrue(payload["supported"], payload)
        self.assertTrue(payload["sources"], payload)
        self.assertTrue(
            is_traceable_support(
                payload["answer"], payload["supported"], payload["sources"]
            ),
            payload,
        )
        self.assertGreaterEqual(evidence_overlap(payload["answer"], payload["sources"]), 2)

    def test_supported_factual_answer_is_traceable(self):
        payload = self.client.post(
            "/query", json={"question": "Who were the main leaders of the French Revolution?"}
        ).json()
        self.assert_supported_is_grounded(payload)

    def test_supported_procedural_answer_is_traceable(self):
        payload = self.client.post(
            "/query", json={"question": "How was the Roman army organized?"}
        ).json()
        self.assert_supported_is_grounded(payload)

    def test_supported_paraphrased_answer_is_traceable(self):
        payload = self.client.post(
            "/query", json={"question": "How did the Roman Empire evolve?"}
        ).json()
        self.assert_supported_is_grounded(payload)

    def test_runtime_ingested_supported_answer_is_traceable(self):
        document = (
            "PILOT SERVICE CARD. Isolate power at the main disconnect before servicing "
            "the pump. Verify zero pressure before work begins."
        )
        ingest = self.client.post(
            "/ingest", json={"text": document, "document_name": "pilot_service_card"}
        )
        self.assertEqual(ingest.status_code, 200)

        generated = {
            "answer": "Power must be isolated at the main disconnect before servicing.",
            "supported": True,
            "answer_type": "procedural",
        }
        with patch.object(api_server, "answer_question", return_value=generated):
            payload = self.client.post(
                "/query", json={"question": "What must happen before servicing the pump?"}
            ).json()
        self.assert_supported_is_grounded(payload)

    def test_unrelated_evidence_cannot_support_an_answer(self):
        generated = {
            "answer": "The pump requires isolation at the main disconnect.",
            "supported": True,
            "answer_type": "procedural",
        }
        unrelated = [
            {"rank": 1, "id": 1, "preview": "A history of Roman political reforms.", "score": 1.0}
        ]
        with patch.object(api_server, "answer_question", return_value=generated), patch.object(
            api_server, "collect_sources", return_value=unrelated
        ):
            payload = self.client.post(
                "/query", json={"question": "How is the pump serviced?"}
            ).json()
        self.assertFalse(payload["supported"])
        self.assertFalse(is_traceable_support(generated["answer"], False, unrelated))

    def test_unsupported_answer_is_not_grounded(self):
        payload = self.client.post(
            "/query", json={"question": "How did DNA cause the Roman Empire?"}
        ).json()
        self.assertFalse(payload["supported"])
        self.assertFalse(is_traceable_support(payload["answer"], False, payload["sources"]))


if __name__ == "__main__":
    unittest.main()
