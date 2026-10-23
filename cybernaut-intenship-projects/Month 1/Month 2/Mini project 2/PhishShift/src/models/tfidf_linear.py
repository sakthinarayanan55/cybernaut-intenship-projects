"""
FR-02: Model 2 - TF-IDF Linear Classifier
Uses word and sub-word n-gram TF-IDF representations paired with
a balanced, calibrated linear logistic regression model.
"""
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
import joblib

class TfidfLinearClassifier:
    """
    TF-IDF Linear Classifier with calibrated probability estimation.
    """
    def __init__(self, c_param: float = 1.0, max_features: int = 5000):
        self.name = "TF-IDF Linear Classifier (Logistic Regression)"
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            max_features=max_features,
            stop_words='english',
            token_pattern=r'(?u)\b\w+\b|[\[\]:]+'
        )
        self.base_clf = LogisticRegression(
            C=c_param,
            class_weight='balanced',
            max_iter=1000,
            random_state=42,
            solver='lbfgs'
        )
        self.calibrated_clf = None
        self.is_fitted = False

    def _prepare_text(self, df: pd.DataFrame) -> List[str]:
        """
        Combines subject and body into a single unified text corpus.
        """
        texts = []
        for _, row in df.iterrows():
            subj = str(row.get("subject_or_title", ""))
            body = str(row.get("body_text", ""))
            texts.append(f"{subj} {body}")
        return texts

    def fit(self, train_df: pd.DataFrame, y_train: np.ndarray):
        """
        Fits TF-IDF vectorizer and calibrated linear model using 3-fold CV.
        """
        texts = self._prepare_text(train_df)
        X_tfidf = self.vectorizer.fit_transform(texts)
        
        # Fit base model
        self.base_clf.fit(X_tfidf, y_train)
        
        # Fit calibrated classifier with 3-fold cross validation
        self.calibrated_clf = CalibratedClassifierCV(
            estimator=LogisticRegression(
                C=self.base_clf.C,
                class_weight='balanced',
                max_iter=1000,
                random_state=42
            ),
            method='sigmoid',
            cv=3
        )
        self.calibrated_clf.fit(X_tfidf, y_train)
        self.is_fitted = True
        return self

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        """
        Predicts calibrated posterior probabilities [P(benign), P(phishing)].
        """
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted yet.")
        texts = self._prepare_text(df)
        X_tfidf = self.vectorizer.transform(texts)
        return self.calibrated_clf.predict_proba(X_tfidf)

    def predict(self, df: pd.DataFrame, threshold: float = 0.50) -> np.ndarray:
        """
        Predicts binary class based on decision threshold.
        """
        probs = self.predict_proba(df)[:, 1]
        return (probs >= threshold).astype(int)

    def get_top_features(self, n_top: int = 10) -> Tuple[List[Tuple[str, float]], List[Tuple[str, float]]]:
        """
        Returns top phishing-associated and benign-associated n-grams.
        """
        if not self.is_fitted:
            return [], []
        
        feature_names = np.array(self.vectorizer.get_feature_names_out())
        coefs = self.base_clf.coef_[0]
        
        top_phish_idx = np.argsort(coefs)[-n_top:][::-1]
        top_phish = [(feature_names[i], round(float(coefs[i]), 3)) for i in top_phish_idx]
        
        top_benign_idx = np.argsort(coefs)[:n_top]
        top_benign = [(feature_names[i], round(float(coefs[i]), 3)) for i in top_benign_idx]
        
        return top_phish, top_benign

    def save(self, filepath: str):
        joblib.dump(self, filepath)

    @classmethod
    def load(cls, filepath: str):
        return joblib.load(filepath)
