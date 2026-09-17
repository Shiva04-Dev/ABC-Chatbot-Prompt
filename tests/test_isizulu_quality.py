import pytest

from tests.isizulu_quality_samples import QUALITY_CHECKLIST, SAMPLE_PROMPTS


@pytest.mark.skip(
    reason="Manual check — grammar/naturalness can't be judged from a mocked response."
)
def test_isizulu_output_quality():
    """Run SAMPLE_PROMPTS through the real deployment and check each reply
    against QUALITY_CHECKLIST before go-live."""
    assert SAMPLE_PROMPTS
    assert QUALITY_CHECKLIST
