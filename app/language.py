import re
from dataclasses import dataclass

SUPPORTED_LANGUAGES = ("en", "zu")

# Explicit-switch detection (see Section 6 of the project spec): rather than
# matching a fixed list of exact phrases ("speak zulu", "reply in zulu", ...)
# — which is brittle and misses anything phrased differently, e.g. "zulu
# please" or "can you do zulu" — this matches the language name itself as a
# whole word, in either language, anywhere in the message. \b word
# boundaries keep "KwaZulu-Natal" from false-matching "zulu".
_EXPLICIT_SWITCH_PATTERNS = {
    "en": re.compile(r"\benglish\b"),
    "zu": re.compile(r"\b(isi)?zulu\b"),
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
    for language, pattern in _EXPLICIT_SWITCH_PATTERNS.items():
        if pattern.search(lowered):
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
