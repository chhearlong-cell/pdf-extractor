from __future__ import annotations

import json
import os
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Dict

from flask import Flask, Response, jsonify, render_template, request, send_file

from pdf_extractor import PDFExtractor

app = Flask(__name__)
extractor = PDFExtractor(use_ocr=True, ocr_lang="eng")


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/extract-stream")
def extract_stream() -> Response:
    upload = request.files.get("file")
    if upload is None or upload.filename is None or upload.filename.strip() == "":
        return jsonify({"error": "No file uploaded"}), 400

    if not upload.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are supported"}), 400

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        upload.save(tmp.name)
        tmp_path = tmp.name

    def stream_lines():
        pages = []
        full_text_parts = []
        try:
            for page in extractor.iter_extract(tmp_path):
                pages.append(page)
                if page.get("text"):
                    full_text_parts.append(str(page["text"]))
                yield json.dumps({"type": "page", "page": page}) + "\n"

            result = {
                "filename": upload.filename,
                "page_count": len(pages),
                "pages": pages,
                "full_text": "\n\n".join(full_text_parts),
            }
            yield json.dumps({"type": "complete", "result": result}) + "\n"
        except Exception as exc:  # pragma: no cover
            yield json.dumps({"type": "error", "error": str(exc)}) + "\n"
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    return Response(stream_lines(), mimetype="application/x-ndjson")


@app.post("/api/export")
def export_result():
    payload: Dict[str, object] = request.get_json(silent=True) or {}
    result = payload.get("result")
    export_format = str(payload.get("format", "")).lower()

    if not isinstance(result, dict):
        return jsonify({"error": "Missing extraction result"}), 400

    filename_root = Path(str(result.get("filename", "extracted"))).stem

    if export_format == "json":
        content = extractor.to_json(result)
        mime = "application/json"
        suffix = "json"
    elif export_format == "csv":
        content = extractor.to_csv([result])
        mime = "text/csv"
        suffix = "csv"
    elif export_format == "txt":
        content = extractor.to_txt(result)
        mime = "text/plain"
        suffix = "txt"
    else:
        return jsonify({"error": "Unsupported format"}), 400

    output = BytesIO(content.encode("utf-8"))
    return send_file(
        output,
        as_attachment=True,
        download_name=f"{filename_root}.{suffix}",
        mimetype=mime,
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
