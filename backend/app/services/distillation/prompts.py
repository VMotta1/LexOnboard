SYNTHESIS_SYSTEM_PROMPT = """
You are a contract analysis engine. You receive extracted text from specific clauses in a \
Master Service Agreement. Your job is to produce a structured JSON object for that clause type.

Return ONLY valid JSON. No markdown, no preamble.
"""

SYNTHESIS_USER_TEMPLATE = """Clause type: {clause_type}

Here are {n_clauses} examples of this clause type from this organization's contracts:

{clauses_text}

Produce this JSON structure:
{{
  "clause_type": "{clause_type}",
  "title": "<human-friendly section title>",
  "extracted_values": {{
    "jurisdiction": "<exact governing law state/country, e.g. 'Delaware' — or null>",
    "courts": "<exact courts specified, e.g. 'federal courts of New York' — or null>",
    "cap_formula": "<exact liability cap formula, e.g. 'fees paid in prior 12 months' — or null>",
    "cap_absolute": "<absolute dollar cap if stated, e.g. '$500,000' — or null>",
    "cap_exclusions": ["<items explicitly excluded from the cap, e.g. 'gross negligence', 'IP infringement'>"],
    "indemnification_triggers": ["<specific triggers, e.g. 'IP infringement', 'gross negligence'>"],
    "indemnification_uncapped": "<true if indemnification is explicitly uncapped, false if capped, null if unclear>",
    "ip_customer_assigns_to_vendor": "<true/false — does customer assign IP to vendor — or null>",
    "ip_vendor_retains_all": "<true/false — does vendor retain all IP — or null>",
    "ip_carve_outs": ["<carve-outs stated, e.g. 'pre-existing IP', 'derivatives'>"],
    "dispute_mechanism": "<exact mechanism, e.g. 'binding arbitration' — or null>",
    "dispute_venue": "<exact venue, e.g. 'San Francisco, CA' — or null>",
    "dispute_governing_rules": "<e.g. 'JAMS', 'AAA' — or null>",
    "insurance_required_types": ["<types required, e.g. 'general liability', 'E&O'>"],
    "insurance_minimums": {{"general_liability": "<amount or null>", "errors_and_omissions": "<amount or null>"}},
    "data_owner": "<'vendor' or 'customer' or null>",
    "subprocessors_allowed": "<true/false or null>",
    "privacy_jurisdictions": ["<e.g. 'GDPR', 'PIPEDA', 'CCPA'>"],
    "auto_renewal": "<true/false or null>",
    "auto_renewal_notice_days": "<integer or null>",
    "assignment_vendor_without_consent": "<true/false — can vendor assign without consent — or null>",
    "assignment_acquisition_carve_out": "<true/false — is there a carve-out for acquisition — or null>",
    "termination_for_convenience": "<true/false or null>",
    "termination_notice_days": "<integer or null>",
    "cure_period_days": "<integer or null>"
  }},
  "non_negotiables": [
    "<absolute requirement phrased as a rule, e.g. 'Governing law must be Ontario or a Canadian province'>"
  ],
  "standard_positions": [
    {{"description": "...", "acceptable_range": "...", "rationale": "..."}}
  ],
  "red_flags": [
    "<specific concern about this clause AS WRITTEN — must reference an extracted_value, e.g. 'Liability cap excludes IP infringement — this creates uncapped exposure'>"
  ],
  "industry_baseline": "<what is typical in this sector for this clause type>",
  "example_clauses": ["<sanitized example clause text>"],
  "source_doc_ids": []
}}

Rules:
- extracted_values must reflect what the CONTRACT says, not what is ideal. Use null for values not stated.
- red_flags must reference the actual extracted values, not generic risks.
- Base non_negotiables and standard_positions strictly on evidence in the provided examples."""
