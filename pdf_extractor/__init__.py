"""Public API for PDF extraction utilities."""

from .extractor import PDFExtractionError, PDFExtractor

__all__ = ["PDFExtractor", "PDFExtractionError"]
