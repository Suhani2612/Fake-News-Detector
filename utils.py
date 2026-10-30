"""Shared helpers used by both train.py and app.py."""
import re

_AGENCY_TAG = re.compile(r"^.*?\(reuters\)\s*-\s*", re.IGNORECASE)


def clean_text(text: str) -> str:
    """Lowercase and strip the news-agency tag (e.g. 'WASHINGTON (Reuters) -').

    The tag appears only in real articles of the dataset, so removing it stops
    the model from 'cheating' by learning that tag instead of the writing style.
    """
    text = str(text)
    text = _AGENCY_TAG.sub("", text, count=1)
    return text.lower().strip()
