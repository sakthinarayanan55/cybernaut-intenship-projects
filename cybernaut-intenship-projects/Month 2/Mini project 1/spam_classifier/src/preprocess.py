"""Text preprocessing (NLP) used for both training and prediction."""
import re

from nltk.stem import PorterStemmer
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

_stemmer = PorterStemmer()
_STOP = set(ENGLISH_STOP_WORDS)

URL_RE = re.compile(r"(https?://\S+|www\.\S+)", re.I)
EMAIL_RE = re.compile(r"\S+@\S+\.\S+")
LONGNUM_RE = re.compile(r"\b\d{5,}\b")      # phone numbers / short codes
NUM_RE = re.compile(r"\d+")
NON_ALPHA_RE = re.compile(r"[^a-z\s]")


def clean_text(text: str) -> str:
    """Lowercase -> tag URLs/emails/long numbers/currency -> strip punctuation
    -> remove stop-words -> stem (Porter)."""
    text = str(text).lower()
    text = URL_RE.sub(" urltoken ", text)
    text = EMAIL_RE.sub(" emailtoken ", text)
    text = LONGNUM_RE.sub(" longnumtoken ", text)
    text = NUM_RE.sub(" ", text)
    text = text.replace("£", " moneytoken ").replace("$", " moneytoken ")
    text = NON_ALPHA_RE.sub(" ", text)
    tokens = [_stemmer.stem(t) for t in text.split() if t not in _STOP and len(t) > 1]
    return " ".join(tokens)
