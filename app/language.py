import re
from dataclasses import dataclass

SUPPORTED_LANGUAGES = ("en", "zu")

# Explicit-switch phrases (see Section 6 of the project spec). Checked as substrings of the
# lowercased message, so phrasing/punctuation around them doesn't matter.
_EXPLICIT_SWITCH_PHRASES = {
    "en": [
        "speak english",
        "reply in english",
        "respond in english",
        "english please",
        "switch to english",
    ],
    "zu": [
        "speak zulu",
        "speak isizulu",
        "khuluma isizulu",
        "khuluma izulu",
        "reply in zulu",
        "reply in isizulu",
        "respond in zulu",
        "respond in isizulu",
        "isizulu please",
        "switch to zulu",
        "switch to isizulu",
    ],
}

# Small, curated marker-word sets for the lightweight implicit heuristic
# (see Section 6 of the project spec) — not a general-purpose language identifier, just
# enough to distinguish English from isiZulu, or notice that a message is
# neither.
_MARKER_WORDS = {
    "en": {
        "the", "hello", "hi", "hey", "thanks", "thank", "please", "yes", "no",
        "what", "how", "where", "when", "why", "who", "can", "could", "would",
        "services", "help", "you", "are", "is", "tell", "about", "contact",
        "business", "company",
    },
    "zu": {
        "sawubona", "yebo", "cha", "ngiyabonga", "siyabonga", "unjani",
        "kunjani", "ngicela", "kanjani", "futhi", "kodwa", "ukuthi",
        "ngesikhathi", "uxolo", "ngiyaxolisa", "ngingakusiza", "usizo",
        "inkampani", "imisebenzi", "ubuchwepheshe", "sicela", "siyakwazi",
    },
}

FALLBACK_NOTICE = (
    "I can only reply in English or isiZulu. "
    "Please continue in one of those languages and I'll be happy to help."
)


@dataclass
class LanguageResolution:
    language: str
    used_fallback: bool


def _tokenize(message: str) -> list[str]:
    return re.findall(r"[a-zA-Z']+", message.lower())


def detect_explicit_switch(message: str) -> str | None:
    lowered = message.lower()
    for language, phrases in _EXPLICIT_SWITCH_PHRASES.items():
        if any(phrase in lowered for phrase in phrases):
            return language
    return None


def detect_implicit_language(message: str) -> str | None:
    words = set(_tokenize(message))
    en_hits = len(words & _MARKER_WORDS["en"])
    zu_hits = len(words & _MARKER_WORDS["zu"])
    if en_hits == 0 and zu_hits == 0:
        return None
    return "zu" if zu_hits > en_hits else "en"


def resolve_language(message: str, session_language: str | None) -> LanguageResolution:
    """Resolve the reply language for this turn (see Section 6 of the project spec).

    An explicit switch phrase always wins. Otherwise a language already
    established for this session persists turn to turn, so a stray English
    or isiZulu word in an unrelated message can't flip it — only an
    explicit switch can. Only on the *first* turn of a session (nothing
    persisted yet) does the implicit marker-word heuristic decide; if it
    can't tell, that's the third-language fallback.
    """
    explicit = detect_explicit_switch(message)
    if explicit is not None:
        return LanguageResolution(language=explicit, used_fallback=False)

    if session_language in SUPPORTED_LANGUAGES:
        return LanguageResolution(language=session_language, used_fallback=False)

    implicit = detect_implicit_language(message)
    if implicit is not None:
        return LanguageResolution(language=implicit, used_fallback=False)

    return LanguageResolution(language="en", used_fallback=True)
