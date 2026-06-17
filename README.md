# pdf-extractor

Local, browser-based PDF data extraction tool with OCR fallback for scanned PDFs.

## Features

- Browser UI (HTML/CSS/JavaScript) with drag-and-drop upload
- Local Flask backend (`localhost`) with no external API calls
- Real-time extraction preview while pages are processed
- Text extraction for regular PDFs
- OCR fallback for image-based/scanned PDFs
- Export to JSON, CSV, or TXT
- Responsive layout for desktop/laptop screens

## Run locally

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Start the app with a single command:

   ```bash
   python app.py
   ```

3. Open your browser at:

   ```
   http://127.0.0.1:5000
   ```

## Notes

- Processing is fully local; files are never sent to cloud services.
- OCR uses Tesseract via `pytesseract`. If the Tesseract binary is unavailable on your laptop, normal text extraction still works, and OCR pages may return empty text.
