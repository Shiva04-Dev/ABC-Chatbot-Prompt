"""Sample in-scope / out-of-scope questions for the assistant. Scope
enforcement is entirely prompt-driven, so these only check structurally
that every question reaches the scope-locked prompt (see test_chat_scope.py).
"""

IN_SCOPE_QUESTIONS = [
    "What services do you offer?",
    "Tell me about your company.",
    "How can I get in touch with you?",
    "How does your company work with clients?",
]

OUT_OF_SCOPE_QUESTIONS = [
    "What's the weather like today?",
    "Can you give me general advice for running a small business?",
    "Which company is better, you or your competitors?",
    "Who specifically will be handling my account?",
    "How do you decide which consultant gets assigned to a lead?",
]
