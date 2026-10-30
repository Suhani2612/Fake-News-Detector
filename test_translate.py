"""Quick check: can this computer translate? Run:  python test_translate.py"""
import sys
from importlib.metadata import version

print("Python:", sys.version.split()[0])
try:
    print("deep-translator:", version("deep-translator"))
except Exception as exc:
    print("deep-translator NOT installed:", exc)
    sys.exit(1)

import requests

try:
    r = requests.get("https://translate.google.com", timeout=15)
    print("Reach translate.google.com: HTTP", r.status_code)
except Exception as exc:
    print("Cannot reach translate.google.com:", type(exc).__name__, exc)

from deep_translator import GoogleTranslator

try:
    out = GoogleTranslator(source="auto", target="en").translate("सरकार ने मंगलवार को घोषणा की")
    print("Translation result:", out)
except Exception as exc:
    print("TRANSLATION ERROR:", type(exc).__name__, "-", exc)
