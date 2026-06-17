# pdf-extractor

A comprehensive PDF data extraction tool with OCR support for scanned images.

## Features

- Extract text from regular PDFs with selectable text
- OCR fallback for scanned/image-based PDFs
- Batch processing for multiple files
- Structured output as Python dictionaries, JSON, and CSV
- Simple import-first API

## Installation

```bash
pip install -r requirements.txt
```

> OCR requires the Tesseract binary installed on your system.

## Quick start

```python
from pdf_extractor import PDFExtractor
from pathlib import Path

extractor = PDFExtractor(use_ocr=True, ocr_lang="eng")
result = extractor.extract("/absolute/path/to/file.pdf")
# Path objects are also supported:
result_from_path = extractor.extract(Path("/absolute/path/to/file.pdf"))

print(result["full_text"])
print(extractor.to_json(result))
print(extractor.to_csv(result))
```

## Batch processing

```python
from pdf_extractor import PDFExtractor

extractor = PDFExtractor()
results = extractor.extract_batch(
    [
        "/absolute/path/to/invoice.pdf",
        "/absolute/path/to/scanned-receipt.pdf",
    ]
)

json_payload = extractor.to_json(results)
csv_payload = extractor.to_csv(results)
```

## Data shape

`extract()` returns:

```json
{
  "file_path": "...",
  "page_count": 2,
  "full_text": "...",
  "pages": [
    {
      "page_number": 1,
      "source": "text",
      "text": "...",
      "char_count": 123
    }
  ]
}
```

## Error handling

- Raises `PDFExtractionError` when a file is missing or cannot be read
- `extract_batch()` continues processing and stores per-file errors in output
- Uses Python logging for OCR/dependency warnings and runtime extraction failures
