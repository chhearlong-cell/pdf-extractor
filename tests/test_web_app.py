import io
import json
import unittest
from unittest.mock import patch

from app import app


class WebAppTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_index_page_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"PDF Data Extractor (Local)", response.data)

    @patch("app.extractor.iter_extract")
    def test_extract_stream_returns_ndjson_events(self, mock_iter_extract):
        mock_iter_extract.return_value = iter([
            {"page": 1, "text": "first page", "source": "text"},
            {"page": 2, "text": "second page", "source": "ocr"},
        ])

        response = self.client.post(
            "/api/extract-stream",
            data={"file": (io.BytesIO(b"%PDF-1.4 fake"), "sample.pdf")},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 200)
        events = [json.loads(line) for line in response.data.decode("utf-8").splitlines() if line]
        self.assertEqual(events[0]["type"], "page")
        self.assertEqual(events[1]["type"], "page")
        self.assertEqual(events[2]["type"], "complete")
        self.assertEqual(events[2]["result"]["page_count"], 2)

    def test_export_txt(self):
        payload = {
            "format": "txt",
            "result": {
                "filename": "sample.pdf",
                "page_count": 1,
                "pages": [{"page": 1, "text": "hello", "source": "text"}],
                "full_text": "hello",
            },
        }
        response = self.client.post(
            "/api/export",
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("attachment", response.headers.get("Content-Disposition", ""))
        self.assertEqual(response.data.decode("utf-8"), "hello")


if __name__ == "__main__":
    unittest.main()
