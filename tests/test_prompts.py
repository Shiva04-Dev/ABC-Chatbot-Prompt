from app.prompts import build_system_prompt
from content.company import COMPANY_DESCRIPTION, CONTACT_DETAILS, SERVICE_CATALOG


def test_default_prompt_includes_company_content():
    prompt = build_system_prompt()
    assert COMPANY_DESCRIPTION in prompt
    assert CONTACT_DETAILS in prompt
    for service in SERVICE_CATALOG:
        assert service in prompt


def test_default_prompt_locks_scope():
    prompt = build_system_prompt()
    assert "only discuss AfriBiz Connect" in prompt
    assert "briefly and naturally steer the conversation back" in prompt


def test_default_prompt_has_brand_guardrails():
    prompt = build_system_prompt()
    assert "Never name or refer to a specific AfriBiz Connect staff member" in prompt
    assert "internal lead-allocation" in prompt
    assert "Never mention or compare AfriBiz Connect to any competitor" in prompt


def test_default_prompt_limits_lead_handling_to_contact_details():
    prompt = build_system_prompt()
    assert "Do not attempt to schedule anything, collect structured information" in prompt


def test_english_directive():
    assert "Reply only in English." in build_system_prompt("en")


def test_zulu_directive():
    assert "Reply only in isiZulu." in build_system_prompt("zu")


def test_unsupported_language_falls_back_to_english():
    prompt = build_system_prompt("fr")
    assert "Reply only in English." in prompt
