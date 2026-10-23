"""
FR-02: Model 3 - Advanced Cybersecurity Hybrid Classifier (Deep Domain-NLP Neural Network)
Combines Lexical TF-IDF N-grams with Structured Cybersecurity Domain Features
(Defanged URL indicators, sender domain types, urgency cues) using a Multi-Layer Perceptron (MLP)
with probability calibration.
"""
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from scipy.sparse import hstack, csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neural_network import MLPClassifier
from sklearn.calibration import CalibratedClassifierCV
import joblib

from src.feature_extraction import extract_features_dataframe, extract_domain_features

class AdvancedHybridClassifier:
    """
    Robust hybrid model combining text NLP with domain cybersecurity signals
    via a Multi-Layer Perceptron (MLP) Neural Network.
    """
    def __init__(self, max_text_features: int = 500, hidden_layers: Tuple[int, ...] = (64, 32)):
        self.name = "Advanced Hybrid Domain-NLP Classifier (Neural MLP)"
        self.max_text_features = max_text_features
        self.hidden_layers = hidden_layers
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=max_text_features,
            sublinear_tf=True,
            stop_words='english'
        )
        self.feature_columns = None
        self.base_clf = MLPClassifier(
            hidden_layer_sizes=self.hidden_layers,
            activation='relu',
            solver='adam',
            alpha=0.002,
            batch_size=32,
            learning_rate_init=0.005,
            max_iter=300,
            early_stopping=True,
            n_iter_no_change=15,
            random_state=42
        )
        self.calibrated_clf = None
        self.is_fitted = False

    def _prepare_text(self, df: pd.DataFrame) -> List[str]:
        texts = []
        for _, row in df.iterrows():
            subj = str(row.get("subject_or_title", ""))
            body = str(row.get("body_text", ""))
            texts.append(f"{subj} {body}")
        return texts

    def _extract_combined_features(self, df: pd.DataFrame, is_training: bool = False):
        texts = self._prepare_text(df)
        if is_training:
            X_text = self.vectorizer.fit_transform(texts)
        else:
            X_text = self.vectorizer.transform(texts)

        df_feats = extract_features_dataframe(df)
        if is_training:
            self.feature_columns = list(df_feats.columns)
        else:
            for col in self.feature_columns:
                if col not in df_feats.columns:
                    df_feats[col] = 0.0
            df_feats = df_feats[self.feature_columns]

        X_domain = csr_matrix(df_feats.values.astype(np.float32))
        X_combined = hstack([X_text, X_domain]).toarray().astype(np.float32)
        return X_combined

    def fit(self, train_df: pd.DataFrame, y_train: np.ndarray):
        """
        Fits vectorizer, domain features, and calibrated neural classifier using 3-fold CV.
        """
        X_combined = self._extract_combined_features(train_df, is_training=True)
        
        # Fit base MLP model for feature analysis
        self.base_clf.fit(X_combined, y_train)

        # Wrap with CalibratedClassifierCV
        self.calibrated_clf = CalibratedClassifierCV(
            estimator=MLPClassifier(
                hidden_layer_sizes=self.hidden_layers,
                activation='relu',
                solver='adam',
                alpha=0.002,
                batch_size=32,
                learning_rate_init=0.005,
                max_iter=300,
                early_stopping=True,
                random_state=42
            ),
            method='sigmoid',
            cv=3
        )
        self.calibrated_clf.fit(X_combined, y_train)
        self.is_fitted = True
        return self

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        """
        Returns calibrated class probabilities: [P(benign), P(phishing)].
        """
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted yet.")
        X_combined = self._extract_combined_features(df, is_training=False)
        return self.calibrated_clf.predict_proba(X_combined)

    def predict(self, df: pd.DataFrame, threshold: float = 0.50) -> np.ndarray:
        probs = self.predict_proba(df)[:, 1]
        return (probs >= threshold).astype(int)

    def get_feature_importances(self, top_n: int = 15) -> List[Tuple[str, float]]:
        """
        Returns highest magnitude weights from the first neural network layer.
        """
        if not self.is_fitted:
            return []
        
        text_names = [f"word_{name}" for name in self.vectorizer.get_feature_names_out()]
        all_names = list(text_names) + list(self.feature_columns)
        
        weights_l1 = np.abs(self.base_clf.coefs_[0]).sum(axis=1)
        top_idx = np.argsort(weights_l1)[-top_n:][::-1]
        results = [(all_names[i], round(float(weights_l1[i]), 4)) for i in top_idx]
        return results

    def save(self, filepath: str):
        joblib.dump(self, filepath)

    @classmethod
    def load(cls, filepath: str):
        return joblib.load(filepath)
