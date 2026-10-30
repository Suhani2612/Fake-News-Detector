"""Multilingual support: script detection and translation.

How it works
- The classifier is trained on English news, so non-English articles are first translated
  to English and then classified.
- Main translator: Google Translate through deep-translator (retries when rate-limited).
- Backup translator: the free MyMemory web API, used automatically if Google fails.
  Optional: set the environment variable MYMEMORY_EMAIL to raise its daily free quota.
- The interface can be shown in any supported language (translated once and cached).
- Needs an internet connection at run time.
"""
import os
import re
import time

import requests
from deep_translator import GoogleTranslator

# Display name -> language code
LANGUAGES = {
    "English": "en",
    "हिन्दी (Hindi)": "hi",
    "ગુજરાતી (Gujarati)": "gu",
    "मराठी (Marathi)": "mr",
    "বাংলা (Bengali)": "bn",
    "தமிழ் (Tamil)": "ta",
    "తెలుగు (Telugu)": "te",
    "ಕನ್ನಡ (Kannada)": "kn",
    "മലയാളം (Malayalam)": "ml",
    "ਪੰਜਾਬੀ (Punjabi)": "pa",
    "اردو (Urdu)": "ur",
    "ଓଡ଼ିଆ (Odia)": "or",
    "অসমীয়া (Assamese)": "as",
}

# Unicode blocks used to recognise the writing system
SCRIPT_RANGES = {
    "Devanagari": (0x0900, 0x097F),
    "Bengali/Assamese": (0x0980, 0x09FF),
    "Gurmukhi": (0x0A00, 0x0A7F),
    "Gujarati": (0x0A80, 0x0AFF),
    "Odia": (0x0B00, 0x0B7F),
    "Tamil": (0x0B80, 0x0BFF),
    "Telugu": (0x0C00, 0x0C7F),
    "Kannada": (0x0C80, 0x0CFF),
    "Malayalam": (0x0D00, 0x0D7F),
    "Arabic/Urdu": (0x0600, 0x06FF),
}

# Best-guess language for each script (used only by the backup translator, which needs a language)
SCRIPT_TO_CODE = {
    "Devanagari": "hi",
    "Bengali/Assamese": "bn",
    "Gurmukhi": "pa",
    "Gujarati": "gu",
    "Odia": "or",
    "Tamil": "ta",
    "Telugu": "te",
    "Kannada": "kn",
    "Malayalam": "ml",
    "Arabic/Urdu": "ur",
}

# MyMemory wants region-qualified codes
MYMEMORY_CODES = {
    "hi": "hi-IN", "gu": "gu-IN", "mr": "mr-IN", "bn": "bn-IN", "ta": "ta-IN",
    "te": "te-IN", "kn": "kn-IN", "ml": "ml-IN", "pa": "pa-IN", "ur": "ur-PK",
    "or": "or-IN", "as": "as-IN", "en": "en-GB",
}

MAX_CHARS = 4000        # Google Translate accepts at most 5000 characters per request
MYMEMORY_MAX_BYTES = 450  # MyMemory accepts at most 500 bytes per request (Indic letters use 3 bytes)


class TranslationError(Exception):
    pass


def detect_script(text: str) -> str:
    """Return the dominant non-Latin script name, or 'Latin' for English/Latin-script text."""
    counts = {name: 0 for name in SCRIPT_RANGES}
    letters = 0
    for ch in text:
        if not ch.isalpha():
            continue
        letters += 1
        code = ord(ch)
        for name, (lo, hi) in SCRIPT_RANGES.items():
            if lo <= code <= hi:
                counts[name] += 1
                break
    if letters == 0:
        return "Latin"
    best = max(counts, key=counts.get)
    return best if counts[best] / letters >= 0.3 else "Latin"


def split_text(text: str, limit: int = MAX_CHARS, by_bytes: bool = False):
    """Split on sentence ends (including the Hindi danda and Urdu question mark) into chunks <= limit."""
    size = (lambda s: len(s.encode("utf-8"))) if by_bytes else len

    def hard_split(piece):
        parts, cur = [], ""
        for ch in piece:
            if size(cur + ch) > limit:
                parts.append(cur)
                cur = ch
            else:
                cur += ch
        if cur:
            parts.append(cur)
        return parts

    sentences = [s for s in re.split(r"(?<=[.!?।॥؟\n])\s*", text) if s.strip()]
    chunks, current = [], ""
    for sentence in sentences:
        if size(sentence) > limit:  # a single very long sentence
            if current:
                chunks.append(current)
                current = ""
            pieces = hard_split(sentence)
            chunks.extend(pieces[:-1])
            current = pieces[-1]
            continue
        if current and size(current) + size(sentence) + 1 > limit:
            chunks.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        chunks.append(current)
    return chunks


def _google(translator, text: str) -> str:
    """One Google request, retried with a pause when Google answers 'too many requests'."""
    for attempt in range(3):
        try:
            return translator.translate(text) or ""
        except Exception as exc:
            if type(exc).__name__ == "TooManyRequests" and attempt < 2:
                time.sleep(2 * (attempt + 1))
                continue
            raise
    return ""


def _mymemory(text: str, code: str) -> str:
    """Backup translator (free MyMemory API). `code` is a language code such as 'hi'."""
    if code not in MYMEMORY_CODES or code == "en":
        raise TranslationError(f"backup translator does not support language '{code}'")
    pair = f"{MYMEMORY_CODES[code]}|{MYMEMORY_CODES['en']}"
    email = os.environ.get("MYMEMORY_EMAIL")
    out = []
    for chunk in split_text(text, MYMEMORY_MAX_BYTES, by_bytes=True):
        params = {"q": chunk, "langpair": pair}
        if email:
            params["de"] = email
        resp = requests.get("https://api.mymemory.translated.net/get", params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        if str(data.get("responseStatus")) != "200":
            raise TranslationError(f"MyMemory: {data.get('responseDetails') or data.get('responseStatus')}")
        out.append(data["responseData"]["translatedText"])
    return " ".join(out).strip()


def translate_to_english(text: str, source: str = "auto") -> str:
    """Translate text to English. `source` is a language code or 'auto'.

    Tries Google first; if that fails, falls back to the MyMemory API.
    """
    try:
        translator = GoogleTranslator(source=source, target="en")
        return " ".join(_google(translator, chunk) for chunk in split_text(text)).strip()
    except Exception as google_exc:
        code = source if source != "auto" else SCRIPT_TO_CODE.get(detect_script(text))
        try:
            if not code:
                raise TranslationError("could not work out the language for the backup translator")
            return _mymemory(text, code)
        except Exception as backup_exc:
            raise TranslationError(
                f"Google: {type(google_exc).__name__} | Backup: {str(backup_exc)[:150]}"
            ) from backup_exc


def translate_ui(strings: dict, lang: str) -> dict:
    """Translate a dict of short interface strings from English into `lang`.

    All strings are sent together in one request (one per line). Raises TranslationError
    on failure; the app catches it and keeps the English interface.
    """
    if lang == "en":
        return dict(strings)
    keys = list(strings)
    values = [strings[k] for k in keys]
    try:
        translated, batch, size = [], [], 0
        groups = []
        for v in values:
            if batch and size + len(v) + 1 > MAX_CHARS:
                groups.append(batch)
                batch, size = [], 0
            batch.append(v)
            size += len(v) + 1
        if batch:
            groups.append(batch)
        translator = GoogleTranslator(source="en", target=lang)
        for group in groups:
            parts = _google(translator, "\n".join(group)).split("\n")
            if len(parts) != len(group):
                raise ValueError("line count changed during translation")
            translated += [p.strip() for p in parts]
        return dict(zip(keys, translated))
    except Exception as exc:
        raise TranslationError(f"{type(exc).__name__}: {str(exc)[:200]}") from exc
