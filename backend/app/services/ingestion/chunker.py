import re

# Patterns that signal a new clause/section heading
_HEADING_PATTERNS = [
    re.compile(r"^(?:ARTICLE|SECTION|PART)\s+[IVX\d]", re.IGNORECASE),
    re.compile(r"^\d+\.\d+\s+\w"),    # "3.1 Payment Terms"
    re.compile(r"^[IVX]+\.\s+\w"),    # "IV. Termination"
    re.compile(r"^\d+\.\s+[A-Z]"),    # "4. Governing Law"
]

# ~1500 tokens at ~4 chars/token
_MAX_CHUNK_CHARS = 6000
_MIN_CHUNK_CHARS = 100


def _is_heading(element: dict) -> bool:
    el_type = element.get("type", "")
    text = element.get("text", "").strip()

    if el_type == "Title":
        return True

    for pattern in _HEADING_PATTERNS:
        if pattern.match(text):
            return True

    return False


def _update_section_path(path: list[str], heading_text: str) -> list[str]:
    """Push heading onto the section path stack, respecting depth."""
    text = heading_text.strip()

    if re.match(r"^\d+\.\d+\.\d+", text):   # 1.2.3 — depth 3
        return path[:2] + [text]
    if re.match(r"^\d+\.\d+\s", text):       # 1.2 — depth 2
        return path[:1] + [text]
    if re.match(r"^\d+\.\s", text) or re.match(r"^[IVX]+\.", text, re.IGNORECASE):
        return [text]  # top-level replaces entire path

    # Unknown depth — append and cap at 3 levels
    return (path + [text])[-3:]


def chunk_by_clause(elements: list[dict]) -> list[dict]:
    """
    Group elements into logical clause chunks.
    A new chunk starts at each heading or when the 1500-token budget is hit.
    """
    chunks: list[dict] = []
    current_section_path: list[str] = []
    current_texts: list[str] = []
    current_types: list[str] = []

    def flush():
        if not current_texts:
            return
        combined = " ".join(current_texts)
        if len(combined) >= _MIN_CHUNK_CHARS:
            chunks.append(
                {
                    "text": combined,
                    "section_path": list(current_section_path),
                    "element_types": list(current_types),
                }
            )

    for element in elements:
        el_type = element.get("type", "")
        text = element.get("text", "").strip()

        if not text:
            continue

        if _is_heading(element):
            flush()
            current_texts = []
            current_types = []
            current_section_path = _update_section_path(current_section_path, text)
            # Include heading text in the new chunk for context
            current_texts.append(text)
            current_types.append(el_type)
        else:
            prospective_len = len(" ".join(current_texts + [text]))
            if prospective_len > _MAX_CHUNK_CHARS and current_texts:
                flush()
                current_texts = []
                current_types = []
                # section_path unchanged — still same section

            current_texts.append(text)
            current_types.append(el_type)

    flush()
    return chunks