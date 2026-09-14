import pytest

from tests.isizulu_quality_samples import QUALITY_CHECKLIST, SAMPLE_PROMPTS


@pytest.mark.skip(
    reason=(
        "Needs a live Azure OpenAI call against real credentials (M7) — "
        "grammar and naturalness can't be judged from a mocked response."
    )
)
def test_isizulu_output_quality():
    """Run SAMPLE_PROMPTS through the real deployment via /chat and check
    each reply against QUALITY_CHECKLIST before go-live (see Section 5 of the project spec).
    """
    assert SAMPLE_PROMPTS
    assert QUALITY_CHECKLIST
