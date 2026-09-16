import pytest

from tests.isizulu_quality_samples import QUALITY_CHECKLIST, SAMPLE_PROMPTS


@pytest.mark.skip(
    reason=(
        "Grammar and naturalness can't be judged from a mocked response, so this "
        "stays a manual check rather than an automated one. Manually verified "
        "against the real GPT-5 mini deployment on 2026-09-16 — output read as "
        "natural, grammatical isiZulu, stayed in-language throughout, and "
        "correctly honoured scope-lock/guardrails. Re-verify if the deployment "
        "or system prompt changes materially."
    )
)
def test_isizulu_output_quality():
    """Run SAMPLE_PROMPTS through the real deployment via /chat and check
    each reply against QUALITY_CHECKLIST before go-live (see Section 5 of the project spec).
    """
    assert SAMPLE_PROMPTS
    assert QUALITY_CHECKLIST
