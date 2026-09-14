"""isiZulu output-quality samples (see the project spec's Section 5, the Zulu-quality caveat).

isiZulu is a lower-resource language for most LLMs, including GPT-5 nano.
Whether output is grammatical and natural — not just "technically in
isiZulu" — can't be judged from a mocked response, so these prompts are for
running against the real Azure OpenAI deployment as soon as credentials
exist (M7), before shipping. If GPT-5 nano's isiZulu is weak, Section 5
says step up to GPT-5 mini for isiZulu turns (or across the board).
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
