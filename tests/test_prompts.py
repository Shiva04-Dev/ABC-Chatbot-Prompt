from app.prompts import build_system_prompt
from content.company import COMPANY_DESCRIPTION, CONTACT_DETAILS, DIRECTOR_NAME, SERVICE_TIERS


def test_default_prompt_includes_company_content():
    prompt = build_system_prompt()
    assert COMPANY_DESCRIPTION in prompt
    assert CONTACT_DETAILS in prompt
    assert SERVICE_TIERS in prompt


def test_default_prompt_locks_scope():
    prompt = build_system_prompt()
    assert "only discuss AfriBiz Connect" in prompt
    assert "briefly and naturally steer the conversation back" in prompt


def test_default_prompt_has_brand_guardrails():
    prompt = build_system_prompt()
    assert DIRECTOR_NAME in prompt
    assert "Never name any other individual staff member" in prompt
    assert "internal lead-allocation" in prompt
    assert "Never mention or compare AfriBiz Connect to any competitor" in prompt


def test_default_prompt_limits_lead_handling_to_contact_details():
    prompt = build_system_prompt()
    assert "don't attempt to schedule anything, collect structured information" in prompt


def test_default_prompt_directs_pricing_questions_to_contact_details():
    prompt = build_system_prompt()
    assert "never quote or estimate prices" in prompt
    assert "direct the visitor to the contact details above" in prompt


def test_default_prompt_restricts_contact_details_to_explicit_triggers():
    prompt = build_system_prompt()
    assert "explicitly asks how to contact or reach AfriBiz Connect" in prompt
    assert "Do not include them in any other reply" in prompt


def test_default_prompt_caps_reply_length_and_bans_bullets():
    prompt = build_system_prompt()
    assert "3 sentences or fewer" in prompt
    assert "no bullet points, numbered lists, or headings" in prompt


def test_english_directive():
    assert "Reply only in English." in build_system_prompt("en")


def test_zulu_directive():
    assert "Reply only in isiZulu." in build_system_prompt("zu")


def test_unsupported_language_falls_back_to_english():
    prompt = build_system_prompt("fr")
    assert "Reply only in English." in prompt
