"""
Sentiment classification using VADER (tuned for short, informal text like
product reviews — handles emphasis, negation, and punctuation well).
"""
import re
from collections import Counter
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

STOPWORDS = set("""
a an the is was were are be been being this that these those it its i you he she
they we my your his her their our of in on at to for with and or but not so very
product good bad item price quality really just like would could regarding
""".split())


class SentimentAnalyzer:
    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()

    def analyze(self, text):
        scores = self.vader.polarity_scores(text)
        compound = scores['compound']

        if compound >= 0.05:
            label = 'positive'
        elif compound <= -0.05:
            label = 'negative'
        else:
            label = 'neutral'

        return {'sentiment': label, 'score': round(compound, 3)}

    def get_word_frequency(self, texts, top_n=20):
        words = []
        for text in texts:
            cleaned = re.sub(r'[^a-zA-Z\s]', '', text.lower())
            words.extend([
                w for w in cleaned.split()
                if w not in STOPWORDS and len(w) > 2
            ])

        counts = Counter(words).most_common(top_n)
        return [{'word': w, 'count': c} for w, c in counts]
