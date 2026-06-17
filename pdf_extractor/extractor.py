"""PDF extraction with optional OCR fallback."""

from __future__ import annotations

import csv
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

logger = logging.getLogger(__name__)


class PDFExtractionError(Exception):
    """Raised when a PDF cannot be extracted."""


@dataclass
class ExtractedPage:
    page_number: int
    text: str
    source: str


class PDFExtractor:
    """Extract text data from regular and scanned PDFs."""

    def __init__(
        self,
        use_ocr: bool = True,
        ocr_lang: str = "eng",
        min_text_length: int = 5,
    ) -> None:
        self.use_ocr = use_ocr
        self.ocr_lang = ocr_lang
        self.min_text_length = min_text_length

    def extract(
        self,
        pdf_path: str | Path,
        force_ocr: bool = False,
    ) -> Dict[str, Any]:
        path = Path(pdf_path)
        if not path.exists() or not path.is_file():
            raise PDFExtractionError(f"PDF not found: {path}")

        pages = self._extract_pages(path, force_ocr=force_ocr)
        full_text = "\n".join(page.text for page in pages if page.text).strip()

        return {
            "file_path": str(path),
            "page_count": len(pages),
            "full_text": full_text,
            "pages": [
                {
                    "page_number": page.page_number,
                    "source": page.source,
                    "text": page.text,
                    "char_count": len(page.text),
                }
                for page in pages
            ],
        }

    def extract_batch(
        self,
        pdf_paths: Sequence[str | Path],
        force_ocr: bool = False,
    ) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for pdf_path in pdf_paths:
            try:
                results.append(self.extract(pdf_path, force_ocr=force_ocr))
            except PDFExtractionError as exc:
                logger.error("Failed to process %s: %s", pdf_path, exc)
                results.append(
                    {
                        "file_path": str(pdf_path),
                        "error": str(exc),
                        "page_count": 0,
                        "full_text": "",
                        "pages": [],
                    }
                )
        return results

    def to_json(self, extracted_data: Dict[str, Any] | List[Dict[str, Any]]) -> str:
        return json.dumps(extracted_data, ensure_ascii=False, indent=2)

    def to_csv(self, extracted_data: Dict[str, Any] | List[Dict[str, Any]]) -> str:
        records = extracted_data if isinstance(extracted_data, list) else [extracted_data]

        output_lines: List[str] = []
        writer = csv.writer(_CSVListWriter(output_lines))
        writer.writerow(["file_path", "page_number", "source", "char_count", "text"])

        for record in records:
            if record.get("error"):
                writer.writerow([record.get("file_path", ""), "", "error", "", record["error"]])
                continue
            for page in record.get("pages", []):
                writer.writerow(
                    [
                        record.get("file_path", ""),
                        page.get("page_number", ""),
                        page.get("source", ""),
                        page.get("char_count", ""),
                        page.get("text", "").replace("\n", " "),
                    ]
                )

        return "\n".join(output_lines)

    def _extract_pages(self, path: Path, force_ocr: bool) -> List[ExtractedPage]:
        reader = self._load_reader(path)
        pages: List[ExtractedPage] = []

        for idx, page in enumerate(reader.pages, start=1):
            text = ""
            source = "text"
            if not force_ocr:
                text = (page.extract_text() or "").strip()

            needs_ocr = force_ocr or (self.use_ocr and len(text) < self.min_text_length)
            if needs_ocr:
                ocr_text = self._ocr_page(path, idx - 1)
                if ocr_text:
                    text = ocr_text
                    source = "ocr"
                elif not text:
                    source = "empty"

            pages.append(ExtractedPage(page_number=idx, text=text, source=source))

        return pages

    def _load_reader(self, path: Path):
        try:
            from pypdf import PdfReader
        except ImportError as exc:  # pragma: no cover
            raise PDFExtractionError(
                "pypdf is required for PDF extraction. Install dependencies from requirements.txt"
            ) from exc

        try:
            return PdfReader(str(path))
        except Exception as exc:  # pragma: no cover
            raise PDFExtractionError(f"Failed to read PDF {path}: {exc}") from exc

    def _ocr_page(self, path: Path, page_index: int) -> str:
        if not self.use_ocr:
            return ""

        try:
            import pypdfium2 as pdfium
            import pytesseract
        except ImportError:
            logger.warning("OCR dependencies unavailable; skipping OCR for %s", path)
            return ""

        try:
            pdf = pdfium.PdfDocument(str(path))
            bitmap = pdf[page_index].render(scale=2).to_pil()
            text = pytesseract.image_to_string(bitmap, lang=self.ocr_lang).strip()
            return text
        except Exception as exc:  # pragma: no cover
            logger.warning("OCR failed on %s page %s: %s", path, page_index + 1, exc)
            return ""


class _CSVListWriter:
    """Minimal file-like adapter for csv.writer that appends lines to a list."""

    def __init__(self, lines: List[str]) -> None:
        self._lines = lines

    def write(self, value: str) -> int:
        self._lines.append(value.rstrip("\r\n"))
        return len(value)
