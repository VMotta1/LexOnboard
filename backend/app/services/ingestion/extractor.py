import re
import unicodedata

from app.services.ingestion.chunker import chunk_by_clause
from app.services.ingestion.parser import parse_document

# Common PDF ligature and typographic character replacements
_LIGATURES: dict[str, str] = {
    "ﬁ": "fi",
    "ﬂ": "fl",
    "ﬀ": "ff",
    "ﬃ": "ffi",
    "ﬄ": "ffl",
    "’": "'",
    "‘": "'",
    "“": '"',
    "”": '"',
    "–": "-",
    "—": "--",
    "\xad": "",   # soft hyphen (line-break artifact)
}


def clean_text(text: str) -> str:
    """Remove control characters, normalize unicode, fix common PDF artifacts."""
    for char, replacement in _LIGATURES.items():
        text = text.replace(char, replacement)

    # NFC normalization
    text = unicodedata.normalize("NFC", text)

    # Strip control characters (preserve \n and \t)
    text = "".join(
        c for c in text
        if unicodedata.category(c) != "Cc" or c in "\n\t"
    )

    # Normalize whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def extract_and_chunk(file_path: str, doc_type: str) -> list[dict]:
    """Parse → clean text → chunk by clause. Returns enriched clause dicts."""
    elements = parse_document(file_path, doc_type)

    cleaned: list[dict] = []
    for el in elements:
        cleaned_text = clean_text(el["text"])
        if cleaned_text:
            cleaned.append({**el, "text": cleaned_text})

    chunks = chunk_by_clause(cleaned)

    # Enrich each chunk with page_number and char_offset
    enriched: list[dict] = []
    char_offset = 0

    for chunk in chunks:
        # Heuristic: find first element whose text appears in the chunk for page number
        page_number = 0
        chunk_prefix = chunk["text"][:60]
        for el in cleaned:
            if el.get("text", "")[:60] in chunk_prefix or chunk_prefix[:40] in el.get("text", ""):
                page_number = el.get("metadata", {}).get("page_number", 0) or 0
                break

        enriched.append({
            **chunk,
            "page_number": page_number,
            "char_offset": char_offset,
        })
        char_offset += len(chunk["text"])

    return enriched