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

CHECKLIST_GENERATION_PROMPT = """You are generating a contract review checklist for a company's new hires.

Based on this company's contract playbook:
{playbook_json}

Generate a comprehensive contract review checklist in this exact JSON structure:
{{
  "categories": [
    {{
      "name": "I. Tender Submission & Execution Preliminaries",
      "subcategories": [
        {{
          "name": "A. Documents & Dates",
          "items": [
            {{
              "item_clause": "Tender/Contract Name",
              "review_question": "Is the official name or title noted and correct?",
              "is_non_negotiable": false,
              "clause_type": "Scope of Work"
            }}
          ]
        }}
      ]
    }}
  ]
}}

Cover these categories minimum: Submission & Execution, Parties & Authority, Scope & Deliverables, \
Time & Delays, Payment & Financial, Liability & Risk, IP & Confidentiality, Termination, \
Governing Law. Mark is_non_negotiable: true for items that correspond to this org's non-negotiables. \
Include 5-8 items per subcategory. Return ONLY valid JSON."""
