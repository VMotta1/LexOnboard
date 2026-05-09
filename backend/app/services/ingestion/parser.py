import logging
from typing import Any

logger = logging.getLogger(__name__)


def parse_document(file_path: str, doc_type: str) -> list[dict]:
    """Parse a PDF or DOCX into a list of typed element dicts."""
    file_type = "pdf" if file_path.lower().endswith(".pdf") else "docx"
    if file_type == "pdf":
        return _parse_pdf(file_path)
    return _parse_docx(file_path)


def _is_scanned_pdf(file_path: str) -> bool:
    """Return True if the PDF appears to be image-based (scanned)."""
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(file_path)
        total_text = ""
        for page_num in range(min(3, len(doc))):
            total_text += doc[page_num].get_text()
        doc.close()
        return len(total_text.strip()) < 100
    except Exception:
        return False


def _parse_pdf(file_path: str) -> list[dict]:
    try:
        from unstructured.partition.pdf import partition_pdf
    except ImportError:
        raise ImportError(
            "unstructured not installed. "
            "Run: pip install 'unstructured[pdf,local-inference]'"
        )

    is_ocr = _is_scanned_pdf(file_path)

    if is_ocr:
        logger.info(f"Using OCR strategy for {file_path} — this may take longer")
        try:
            elements = partition_pdf(
                file_path,
                strategy="hi_res",
                ocr_languages=["eng"],
                pdf_image_dpi=300,
            )
        except RuntimeError as exc:
            msg = str(exc).lower()
            if "tesseract" in msg or "poppler" in msg:
                raise RuntimeError(
                    "OCR dependencies missing. "
                    "Run: brew install tesseract poppler (macOS) or "
                    "apt-get install tesseract-ocr poppler-utils (Linux)"
                ) from exc
            raise
    else:
        elements = partition_pdf(file_path, strategy="fast")

    return _elements_to_dicts(elements, is_ocr=is_ocr, file_type="pdf")


def _parse_docx(file_path: str) -> list[dict]:
    try:
        from unstructured.partition.docx import partition_docx
    except ImportError:
        raise ImportError(
            "unstructured not installed. Run: pip install 'unstructured[docx]'"
        )

    elements = partition_docx(file_path)
    return _elements_to_dicts(elements, is_ocr=False, file_type="docx")


def _elements_to_dicts(elements: list[Any], is_ocr: bool, file_type: str) -> list[dict]:
    result = []
    for element in elements:
        text = str(element).strip()
        if not text:
            continue

        element_type = type(element).__name__
        metadata: dict = {"is_ocr": is_ocr, "file_type": file_type}

        if hasattr(element, "metadata") and element.metadata is not None:
            if hasattr(element.metadata, "page_number"):
                metadata["page_number"] = element.metadata.page_number

        result.append({"type": element_type, "text": text, "metadata": metadata})

    return result