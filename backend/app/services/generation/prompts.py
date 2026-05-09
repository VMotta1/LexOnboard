TEXTBOOK_SYSTEM_PROMPT = """
You are a legal training writer creating onboarding materials for non-specialist professionals \
(paralegals, project managers, junior in-house counsel) joining a specific company. \
Your writing is clear, practical, and grounded in how THIS organization actually operates — \
not generic legal theory. Use plain English. Avoid jargon where possible; define it when necessary.
"""

TEXTBOOK_CHAPTER_TEMPLATE = """You are writing Chapter {chapter_num} of an onboarding guide for new hires at this company.

Chapter topic: {clause_type} — {section_title}

This company's actual positions on this topic:
{playbook_section_json}

Write a chapter of approximately 400-600 words covering:
1. What this clause type is and why it matters (2-3 sentences, very plain language)
2. How THIS company handles it (reference the non-negotiables and standard positions directly)
3. What to watch out for (the red flags, explained with examples)
4. A practical tip for when you're reviewing a contract

End with exactly 3 key takeaways formatted as:
KEY_TAKEAWAYS:
- <takeaway 1>
- <takeaway 2>
- <takeaway 3>

Write for someone who studied business, not law."""

QUIZ_GENERATION_TEMPLATE = """Generate a quiz for Chapter {chapter_num}: {section_title}

Based on this chapter content:
{chapter_content}

And this org's actual clause examples:
{example_clauses}

Generate exactly 4 questions in this JSON format:
[
  {{
    "question_type": "mcq",
    "text": "<question>",
    "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
    "correct_answer": "A",
    "explanation": "<why this is correct and why others are wrong>",
    "clause_type": "{clause_type}"
  }},
  {{
    "question_type": "true_false",
    "text": "<statement>",
    "options": ["True", "False"],
    "correct_answer": "True",
    "explanation": "<explanation>",
    "clause_type": "{clause_type}"
  }},
  {{
    "question_type": "scenario",
    "text": "You are reviewing a contract and see the following clause:",
    "context": "<use a real example clause from the org's contracts, lightly sanitized>",
    "options": ["A. Approve — this is standard", "B. Flag for review — this deviates from our position", "C. Reject — this is a non-negotiable violation", "D. Skip — this clause type doesn't apply"],
    "correct_answer": "B",
    "explanation": "<explain the correct action and why>",
    "clause_type": "{clause_type}"
  }},
  {{
    "question_type": "mcq",
    "text": "<another question>",
    "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
    "correct_answer": "<letter>",
    "explanation": "<explanation>",
    "clause_type": "{clause_type}"
  }}
]
Return ONLY the JSON array."""

CHECKLIST_GENERATION_PROMPT = """You are a contract review checklist generator. You will be given a structured playbook object for a single contract clause, including extracted values from the actual contract.

Generate a list of checklist items for this clause. Each item must be a SPECIFIC, BINARY (yes/no) or FACTUAL question that a reviewer can answer by reading the contract.

Clause playbook data:
{section_json}

Rules:
1. ALWAYS embed the actual contract value into the question.
   BAD:  "Have you reviewed the Governing Law clause against org standards?"
   GOOD: "Governing law is set to Delaware — does your org accept US-jurisdiction contracts?"

2. Cover these dimensions for EVERY clause (where applicable):
   - Is the specific value written (jurisdiction, %, mechanism, party) acceptable to your org?
   - Are there missing protections (e.g. no cure period, no consent requirement for assignment)?
   - Are there uncapped exposures (indemnification triggers, IP carve-outs)?
   - Does the clause comply with applicable privacy law (PIPEDA, GDPR)?
   - Are insurance minimums sufficient?
   - Is IP ownership clearly retained by your org?

3. For financial/numeric clauses, always ask:
   - Is the cap formula (e.g. "fees paid in prior 12 months") sufficient in a worst-case scenario?
   - Are there exclusions that effectively make it uncapped?

4. Format each checklist item as:
   {{
     "item": "<specific question embedding the actual contract value>",
     "category": "<Compliance | Key Clause Checklist | Risk Flags>",
     "risk_level": "<high | medium | low>",
     "contract_value": "<the exact value extracted from the contract — if not present, describe what is missing, e.g. 'no cure period specified'>",
     "is_mandatory": <true if this corresponds to a non-negotiable in the playbook, false otherwise>
   }}

5. Generate 4-8 items for this clause. Return a JSON array. No markdown, no preamble."""
