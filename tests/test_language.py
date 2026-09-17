from app.language import (
    detect_explicit_switch,
    detect_implicit_language,
    resolve_language,
)


def test_explicit_switch_to_zulu():
    assert detect_explicit_switch("Hey, can you khuluma isizulu please?") == "zu"


def test_explicit_switch_to_english():
    assert detect_explicit_switch("Ngicela, speak english now") == "en"


def test_explicit_switch_none_when_absent():
    assert detect_explicit_switch("What services do you offer?") is None


def test_explicit_switch_matches_language_name_in_any_phrasing():
    # Regression test: a fixed phrase list missed phrasings like "zulu
    # please". Any phrasing with the language name as a whole word now matches.
    for message in [
        "zulu please",
        "can you do zulu",
        "talk to me in zulu",
        "Can we continue in isiZulu?",
    ]:
        assert detect_explicit_switch(message) == "zu", message


def test_explicit_switch_does_not_false_positive_on_kwazulu_natal():
    assert detect_explicit_switch("Are you based in KwaZulu-Natal?") is None


def test_implicit_detects_zulu_markers():
    assert detect_implicit_language("Sawubona, ngicela usizo") == "zu"


def test_implicit_detects_english_markers():
    assert detect_implicit_language("Hello, can you tell me about your services?") == "en"


def test_implicit_returns_none_for_unrecognised_text():
    assert detect_implicit_language("Bonjour, comment allez-vous?") is None


def test_resolve_language_explicit_switch_overrides_session():
    resolution = resolve_language("khuluma isizulu please", session_language="en")
    assert resolution.language == "zu"
    assert resolution.used_fallback is False


def test_resolve_language_persists_session_language_over_new_markers():
    # Session already resolved to isiZulu; a stray English word in a new
    # message must not flip it without an explicit switch.
    resolution = resolve_language("hello", session_language="zu")
    assert resolution.language == "zu"
    assert resolution.used_fallback is False


def test_resolve_language_first_turn_uses_implicit_detection():
    resolution = resolve_language("Sawubona, ngicela usizo", session_language=None)
    assert resolution.language == "zu"
    assert resolution.used_fallback is False


def test_resolve_language_falls_back_to_english_for_third_language():
    resolution = resolve_language("Bonjour, comment allez-vous?", session_language=None)
    assert resolution.language == "en"
    assert resolution.used_fallback is True
