"""Quick check: can this computer read text from images? Run:  python test_ocr.py
Optionally test your own image:  python test_ocr.py path\\to\\image.png hi
(the second value is the language code: en, hi, gu, mr, bn, ta, te, kn, ml, pa, ur, or, as)
"""
import sys

from PIL import Image, ImageDraw, ImageFont

import ocr

try:
    langs = sorted(ocr.installed_languages())
except ocr.OCRUnavailable as exc:
    print("PROBLEM:", exc)
    sys.exit(1)

import pytesseract

print("Tesseract found at:", pytesseract.pytesseract.tesseract_cmd)
print("Installed language packs:", ", ".join(langs))
missing = [c for c, t in ocr.TESS_CODES.items() if t not in langs]
if missing:
    print("Language packs NOT installed for codes:", ", ".join(missing),
          "(re-run the Tesseract installer to add them)")

if len(sys.argv) > 1:
    image = Image.open(sys.argv[1])
    code = sys.argv[2] if len(sys.argv) > 2 else "auto"
else:
    image = Image.new("RGB", (900, 160), "white")
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("arial.ttf", 34)
    except OSError:
        font = ImageFont.load_default()
    draw.text((20, 30), "Government announces new infrastructure plan.", fill="black", font=font)
    draw.text((20, 90), "Officials said funding will come on Tuesday.", fill="black", font=font)
    code = "en"
    print("Using a generated test image.")

try:
    print("Text read from the image:\n", ocr.extract_text(image, code))
except Exception as exc:
    print("OCR ERROR:", type(exc).__name__, "-", exc)
