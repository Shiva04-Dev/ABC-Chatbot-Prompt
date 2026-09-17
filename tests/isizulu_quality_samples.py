"""isiZulu output-quality samples. Grammar/naturalness can't be judged from
a mocked response, so these run against the real deployment before shipping.
"""

SAMPLE_PROMPTS = [
    "Sawubona, ngingathola njani imininingwane yenkampani yenu?",
    "Yiziphi izinsizakalo enizinikezayo?",
    "Ngingaxhumana kanjani nani uma ngifuna usizo?",
]

QUALITY_CHECKLIST = [
    "Grammatically correct isiZulu — not just technically 'in the language'.",
    "Reads naturally to a first-language isiZulu speaker, not a literal/awkward translation.",
    "Stays in isiZulu throughout — no unexplained code-switching into English mid-reply.",
    "Still honours the scope lock and brand guardrails (Section 7) while responding in isiZulu.",
]
