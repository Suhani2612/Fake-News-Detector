"""Read text from an image of a news article (screenshot, photo, newspaper clipping).

Uses the free Tesseract OCR program through the `pytesseract` package.
Tesseract itself must be installed on the computer (see README), plus a language pack
for each language you want to read (English is included; Hindi, Gujarati, etc. are optional).
"""
import os
import shutil

from PIL import Image, ImageOps

# App language code -> Tesseract language-pack name
TESS_CODES = {
    "en": "eng",
    "hi": "hin",
    "gu": "guj",
    "mr": "mar",
    "bn": "ben",
    "ta": "tam",
    "te": "tel",
    "kn": "kan",
    "ml": "mal",
    "pa": "pan",
    "ur": "urd",
    "or": "ori",
    "as": "asm",
}

# Tesseract is often not on PATH after a Windows install, so these places are checked too
COMMON_WINDOWS_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
]

MAX_AUTO_LANGS = 5   # more languages at once makes Tesseract slower and less accurate
MIN_WIDTH = 1200     # small images are enlarged, which helps Tesseract a lot
MAX_WIDTH = 3000     # huge photos are shrunk to keep OCR quick


class OCRUnavailable(Exception):
    """Tesseract (or one of its language packs) is not installed."""


def _setup_tesseract():
    try:
        import pytesseract
    except ImportError as exc:
        raise OCRUnavailable("The 'pytesseract' package is not installed. Run: pip install pytesseract") from exc

    exe = os.environ.get("TESSERACT_CMD") or shutil.which("tesseract")
    if not exe:
        exe = next((p for p in COMMON_WINDOWS_PATHS if os.path.exists(p)), None)
    if not exe:
        raise OCRUnavailable(
            "Tesseract OCR is not installed (or not found). Install it and restart the app - see the README."
        )
    pytesseract.pytesseract.tesseract_cmd = exe
    return pytesseract


def installed_languages():
    """Tesseract language packs installed on this computer."""
    pytesseract = _setup_tesseract()
    return set(pytesseract.get_languages(config=""))


def prepare_image(img: Image.Image) -> Image.Image:
    """Straighten phone photos, convert to grey, resize sensibly and boost contrast."""
    img = ImageOps.exif_transpose(img)
    img = img.convert("L")
    width = img.width
    if width < MIN_WIDTH:
        scale = min(MIN_WIDTH / width, 3)
        img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
    elif width > MAX_WIDTH:
        scale = MAX_WIDTH / width
        img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
    return ImageOps.autocontrast(img)


def pick_languages(lang_code: str, installed: set) -> str:
    """Build the Tesseract language string, e.g. 'hin+eng'. `lang_code` may be 'auto'."""
    if lang_code == "auto":
        extras = [t for c, t in TESS_CODES.items() if c != "en" and t in installed]
        return "+".join((["eng"] if "eng" in installed else []) + extras[: MAX_AUTO_LANGS - 1]) or "eng"
    tess = TESS_CODES[lang_code]
    if tess not in installed:
        raise OCRUnavailable(
            f"The Tesseract language pack '{tess}' is not installed. "
            "Re-run the Tesseract installer and tick this language under 'Additional language data'."
        )
    return tess if tess == "eng" or "eng" not in installed else f"{tess}+eng"


def extract_text(img: Image.Image, lang_code: str = "auto") -> str:
    """Return the text found in the image as one clean, single-spaced string."""
    pytesseract = _setup_tesseract()
    langs = pick_languages(lang_code, set(pytesseract.get_languages(config="")))
    raw = pytesseract.image_to_string(prepare_image(img), lang=langs)
    lines = [" ".join(line.split()) for line in raw.splitlines()]
    return " ".join(line for line in lines if line).strip()
