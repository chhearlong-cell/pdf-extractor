import unittest
from pathlib import Path
from unittest import mock

from pdf_extractor import PDFExtractionError, PDFExtractor


class _FakePDFPage:
    def __init__(self, text):
        self._text = text

    def extract_text(self):
        return self._text


class _FakeReader:
    def __init__(self, texts):
        self.pages = [_FakePDFPage(t) for t in texts]


class TestPDFExtractor(unittest.TestCase):
    def test_extract_uses_text_when_available(self):
        with unittest.mock.patch("pathlib.Path.exists", return_value=True), unittest.mock.patch(
            "pathlib.Path.is_file", return_value=True
        ):
            extractor = PDFExtractor(use_ocr=True, min_text_length=3)

            with mock.patch.object(PDFExtractor, "_load_reader", return_value=_FakeReader(["Hello world"])):
                with mock.patch.object(PDFExtractor, "_ocr_page", return_value="OCR text") as ocr_mock:
                    result = extractor.extract("sample.pdf")

        self.assertEqual(result["page_count"], 1)
        self.assertEqual(result["pages"][0]["source"], "text")
        self.assertEqual(result["pages"][0]["text"], "Hello world")
        ocr_mock.assert_not_called()

    def test_extract_falls_back_to_ocr(self):
        with unittest.mock.patch("pathlib.Path.exists", return_value=True), unittest.mock.patch(
            "pathlib.Path.is_file", return_value=True
        ):
            extractor = PDFExtractor(use_ocr=True, min_text_length=3)

            with mock.patch.object(PDFExtractor, "_load_reader", return_value=_FakeReader([""])):
                with mock.patch.object(PDFExtractor, "_ocr_page", return_value="Detected text"):
                    result = extractor.extract("scan.pdf")

        self.assertEqual(result["pages"][0]["source"], "ocr")
        self.assertEqual(result["pages"][0]["text"], "Detected text")

    def test_extract_batch_continues_after_error(self):
        good_pdf = Path("good.pdf")
        bad_pdf = Path("missing.pdf")

        extractor = PDFExtractor(use_ocr=False)

        def side_effect(path, force_ocr=False):
            if Path(path) == good_pdf:
                return {
                    "file_path": str(good_pdf),
                    "page_count": 1,
                    "full_text": "ok",
                    "pages": [{"page_number": 1, "source": "text", "text": "ok", "char_count": 2}],
                }
            raise PDFExtractionError("broken")

        with mock.patch.object(PDFExtractor, "extract", side_effect=side_effect):
            results = extractor.extract_batch([good_pdf, bad_pdf])

        self.assertEqual(len(results), 2)
        self.assertNotIn("error", results[0])
        self.assertEqual(results[1]["error"], "broken")

    def test_to_csv_includes_header_and_rows(self):
        extractor = PDFExtractor()
        csv_text = extractor.to_csv(
            {
                "file_path": "a.pdf",
                "pages": [{"page_number": 1, "source": "text", "char_count": 4, "text": "test"}],
            }
        )

        self.assertIn("file_path,page_number,source,char_count,text", csv_text)
        self.assertIn("a.pdf,1,text,4,test", csv_text)


if __name__ == "__main__":
    unittest.main()
