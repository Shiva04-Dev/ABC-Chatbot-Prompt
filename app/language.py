import re
from dataclasses import dataclass

SUPPORTED_LANGUAGES = ("en", "zu")

# Matches the language name as a whole word anywhere in the message, rather
# than a fixed phrase list (which missed things like "zulu please"). \b
# boundaries keep "KwaZulu-Natal" from false-matching "zulu".
_EXPLICIT_SWITCH_PATTERNS = {
    "en": re.compile(r"\benglish\b"),
    "zu": re.compile(r"\b(isi)?zulu\b"),
}

# Small curated marker words for the lightweight implicit-detection heuristic.
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
    """Resolve the reply language for this turn.

    An explicit switch always wins. Otherwise a session's established
    language persists turn to turn; only on a session's first turn does
    the implicit heuristic decide, falling back if it can't tell.
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
