"""Automated API and validation tests for CalcAI FastAPI backend."""

import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import unittest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.config import settings


class TestBackendAPI(unittest.TestCase):
    """Test suite for FastAPI endpoints and validation rules."""

    def setUp(self):
        self.client = TestClient(app)

    def test_root_endpoint(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "online")
        self.assertIn("docs", data)

    def test_health_endpoint(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("api_key_configured", data)
        self.assertIn("model", data)
        self.assertEqual(data["version"], "0.1.0")

    def test_chat_input_validation_empty_message(self):
        # Empty message should fail validation with 422
        response = self.client.post("/api/chat", json={"message": ""})
        self.assertEqual(response.status_code, 422)

    def test_chat_input_validation_excessive_length(self):
        # Message longer than 4000 chars should fail validation
        long_message = "A" * 4001
        response = self.client.post("/api/chat", json={"message": long_message})
        self.assertEqual(response.status_code, 422)

    def test_chat_request_structure(self):
        # Test valid request payload format
        payload = {
            "message": "Hello CalcAI, what is 2+2?",
            "session_id": "test-session-123",
            "context": {
                "type": "explain_calculation",
                "expression": "2 + 2",
                "result": "4"
            }
        }
        response = self.client.post("/api/chat", json=payload)
        # If API key is configured and valid, it returns 200;
        # If key is unconfigured or rejected by Google, it returns 503, 401, or 502 with structured detail
        self.assertIn(response.status_code, [200, 401, 502, 503])
        data = response.json()
        if response.status_code == 200:
            self.assertIn("reply", data)
            self.assertEqual(data["session_id"], "test-session-123")
        else:
            self.assertIn("detail", data)


if __name__ == "__main__":
    unittest.main()
