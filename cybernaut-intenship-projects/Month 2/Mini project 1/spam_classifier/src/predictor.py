"""Loads the trained models and classifies new messages."""
import json
import os

import re

import joblib
import numpy as np
from nltk.stem import PorterStemmer

_stem = PorterStemmer().stem
_SPECIAL = {"longnumtoken": "phone number/code", "urltoken": "link",
            "emailtoken": "email address", "moneytoken": "currency symbol"}

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE, "models")


class SpamPredictor:
    def __init__(self, model_dir=MODEL_DIR):
        self.model = joblib.load(os.path.join(model_dir, "best_model.joblib"))
        self.explainer = joblib.load(os.path.join(model_dir, "explainer_lr.joblib"))
        with open(os.path.join(model_dir, "metrics.json")) as f:
            self.metrics = json.load(f)
        vec = self.explainer.named_steps["tfidf"]
        self._vec = vec
        self._words = np.array(vec.get_feature_names_out())
        self._coef = self.explainer.named_steps["clf"].coef_[0]

    @staticmethod
    def _readable(feature, text):
        """Turn a stemmed feature (e.g. 'entri') back into the word in the message."""
        originals = {}
        for w in re.findall(r"[a-zA-Z]+", text.lower()):
            originals.setdefault(_stem(w), w)
        parts = [_SPECIAL.get(t) or originals.get(t, t) for t in feature.split()]
        return " ".join(parts)

    def keywords(self, text, top_n=8):
        """Words in `text` that pushed the decision towards spam / ham
        (contribution = Logistic Regression weight x TF-IDF value)."""
        row = self._vec.transform([text])
        idx = row.nonzero()[1]
        contrib = [(self._readable(self._words[i], text), float(self._coef[i] * row[0, i])) for i in idx]
        contrib.sort(key=lambda x: x[1], reverse=True)
        spam = [{"word": w, "score": round(s, 3)} for w, s in contrib if s > 0][:top_n]
        ham = [{"word": w, "score": round(s, 3)} for w, s in reversed(contrib) if s < 0][:top_n]
        return spam, ham

    def predict(self, text):
        text = (text or "").strip()
        if not text:
            raise ValueError("Empty message")
        proba = float(self.model.predict_proba([text])[0][1])
        is_spam = proba >= 0.5
        spam_words, ham_words = self.keywords(text)
        return {
            "label": "spam" if is_spam else "ham",
            "spam_probability": round(proba, 4),
            "confidence": round(proba if is_spam else 1 - proba, 4),
            "spam_keywords": spam_words,
            "ham_keywords": ham_words,
        }
