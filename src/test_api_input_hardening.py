"""Malformed and oversized API input checks that avoid model initialization."""

import unittest
import sys
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src import api_server


class ApiInputHardeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(api_server.app, raise_server_exceptions=False)

    def assert_safe_validation_error(self, response):
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json(), {"error": "Invalid request."})

    def test_empty_payload_is_rejected_safely(self):
        response = self.client.post(
            "/ingest", content=b"", headers={"content-type": "application/json"}
        )
        self.assert_safe_validation_error(response)

    def test_invalid_json_is_rejected_safely(self):
        response = self.client.post(
            "/ingest", content=b'{"text":', headers={"content-type": "application/json"}
        )
        self.assert_safe_validation_error(response)

    def test_wrong_schema_and_unsupported_document_are_rejected(self):
        for payload in (
            {"text": 123},
            {"file": "manual.exe", "document_name": "manual.exe"},
            {"text": "valid", "document_name": " "},
        ):
            with self.subTest(payload=payload):
                self.assert_safe_validation_error(self.client.post("/ingest", json=payload))

    def test_blank_document_is_rejected(self):
        self.assert_safe_validation_error(
            self.client.post("/ingest", json={"text": " \r\n\t"})
        )

    def test_oversized_text_is_rejected(self):
        response = self.client.post(
            "/ingest", json={"text": "x" * (api_server.MAX_INGEST_TEXT_CHARS + 1)}
        )
        self.assert_safe_validation_error(response)

    def test_oversized_request_body_is_rejected(self):
        response = self.client.post(
            "/ingest",
            content=b"x" * (api_server.MAX_API_REQUEST_BYTES + 1),
            headers={"content-type": "application/json"},
        )
        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.json(), {"error": "Request body too large."})

    def test_internal_query_details_are_hidden(self):
        secret = "private traceback detail"

        def fail(*args, **kwargs):
            raise RuntimeError(secret)

        with patch.object(api_server, "get_pipeline", return_value={}), patch.object(
            api_server, "answer_question", side_effect=fail
        ):
            response = self.client.post("/query", json={"question": "valid question"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["error"], "Request processing failed.")
        self.assertNotIn(secret, response.text)


if __name__ == "__main__":
    unittest.main()
