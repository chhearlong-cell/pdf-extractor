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

    def test_export_json(self):
        payload = {
            "format": "json",
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
        parsed = json.loads(response.data.decode("utf-8"))
        self.assertEqual(parsed["filename"], "sample.pdf")

    def test_export_csv(self):
        payload = {
            "format": "csv",
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
        csv_output = response.data.decode("utf-8")
        self.assertIn("filename,page,source,text", csv_output)
        self.assertIn("sample.pdf,1,text,hello", csv_output)

    def test_export_unsupported_format_returns_400(self):
        payload = {
            "format": "xml",
            "result": {
                "filename": "sample.pdf",
                "page_count": 1,
                "pages": [],
                "full_text": "",
            },
        }
        response = self.client.post(
            "/api/export",
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Unsupported format", response.get_json()["error"])

    def test_export_missing_result_returns_400(self):
        response = self.client.post(
            "/api/export",
            data=json.dumps({"format": "txt"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Missing extraction result", response.get_json()["error"])


if __name__ == "__main__":
    unittest.main()
