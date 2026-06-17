from __future__ import annotations

import csv
import json
from io import StringIO
from pathlib import Path
from typing import Dict, Iterable, List, Optional


class PDFExtractor:
    """Local PDF text extractor with optional OCR fallback."""

    def __init__(self, use_ocr: bool = True, ocr_lang: str = "eng") -> None:
        self.use_ocr = use_ocr
        self.ocr_lang = ocr_lang

    def iter_extract(self, pdf_path: str | Path) -> Iterable[Dict[str, str | int]]:
        from pypdf import PdfReader

        reader = PdfReader(str(pdf_path))
        for index, page in enumerate(reader.pages, start=1):
            extracted = (page.extract_text() or "").strip()
            source = "text"
            if not extracted and self.use_ocr:
                extracted = self._ocr_page(pdf_path, index - 1).strip()
                source = "ocr" if extracted else "none"
            yield {"page": index, "text": extracted, "source": source}

    def extract(self, pdf_path: str | Path) -> Dict[str, object]:
        pages = list(self.iter_extract(pdf_path))
        full_text = "\n\n".join(page["text"] for page in pages if page["text"])
        return {
            "filename": Path(pdf_path).name,
            "page_count": len(pages),
            "pages": pages,
            "full_text": full_text,
        }

    def _ocr_page(self, pdf_path: str | Path, page_index: int) -> str:
        try:
            import pypdfium2 as pdfium
            import pytesseract
        except ImportError:
            return ""

        pdf = pdfium.PdfDocument(str(pdf_path))
        page = pdf[page_index]
        pil_image = page.render(scale=2.0).to_pil()
        return pytesseract.image_to_string(pil_image, lang=self.ocr_lang)

    @staticmethod
    def to_json(result: Dict[str, object]) -> str:
        return json.dumps(result, indent=2, ensure_ascii=False)

    @staticmethod
    def to_txt(result: Dict[str, object]) -> str:
        return str(result.get("full_text", ""))

    @staticmethod
    def to_csv(results: List[Dict[str, object]]) -> str:
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["filename", "page", "source", "text"])
        for result in results:
            filename = result.get("filename", "")
            for page in result.get("pages", []):
                writer.writerow([
                    filename,
                    page.get("page", ""),
                    page.get("source", ""),
                    page.get("text", ""),
                ])
        return output.getvalue()
