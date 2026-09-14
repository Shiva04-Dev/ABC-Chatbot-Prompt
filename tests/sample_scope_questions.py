"""Sample in-scope / out-of-scope questions for the AfriBiz Connect assistant
(CLAUDE.md M3: "refusal behavior tested with a set of in-scope and
out-of-scope sample questions").

Scope enforcement here is entirely prompt-driven (no code-level classifier —
CLAUDE.md Section 4/Non-Goals rule that out), so these questions can only be
used to structurally check that every question — in- or out-of-scope — is
sent through the scope-locked system prompt (see test_chat_scope.py).
Judging whether the model actually *behaves* correctly on them (redirecting
out-of-scope questions naturally, answering in-scope ones from real company
content) needs a live model and real content, so that check happens
empirically once Shiv supplies both (M7), not here.
"""

IN_SCOPE_QUESTIONS = [
    "What services does AfriBiz Connect offer?",
    "Tell me about AfriBiz Connect.",
    "How can I get in touch with AfriBiz Connect?",
    "How does AfriBiz Connect work with clients?",
]

OUT_OF_SCOPE_QUESTIONS = [
    "What's the weather like today?",
    "Can you give me general advice for running a small business?",
    "Which company is better, AfriBiz Connect or its competitors?",
    "Who specifically will be handling my account?",
    "How do you decide which consultant gets assigned to a lead?",
]
