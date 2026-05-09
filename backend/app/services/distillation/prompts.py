SYNTHESIS_SYSTEM_PROMPT = """
You are a legal knowledge engineer specializing in extracting institutional knowledge from \
corporate contracts. You receive multiple examples of the same clause type from a company's \
actual signed contracts. Your job is to identify patterns that represent this organization's \
real practices and positions.

Return ONLY valid JSON. No preamble, no markdown fences, no explanation outside the JSON.
"""

SYNTHESIS_USER_TEMPLATE = """Clause type: {clause_type}

Here are {n_clauses} examples of this clause type from this organization's contracts:

{clauses_text}

Extract and return this JSON structure:
{{
  "clause_type": "{clause_type}",
  "title": "<human-friendly section title>",
  "non_negotiables": ["<absolute requirement 1>", "<absolute requirement 2>"],
  "standard_positions": [
    {{"description": "...", "acceptable_range": "...", "rationale": "..."}}
  ],
  "red_flags": ["<pattern that should trigger escalation 1>"],
  "industry_baseline": "<what is typical in this sector for this clause type>",
  "example_clauses": ["<sanitized example clause text 1>", "<sanitized example clause text 2>"],
  "source_doc_ids": []
}}

Base everything strictly on the provided examples. Do not invent positions not evidenced in the text."""
