"""Train, evaluate and save the spam classifiers.

Usage:  python train.py
"""
import json
import os

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, classification_report, confusion_matrix,
                             f1_score, precision_score, recall_score)
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from src.preprocess import clean_text

DATA_PATH = "data/spam.csv"
MODEL_DIR, REPORT_DIR = "models", "reports"
RANDOM_STATE = 42


def load_data(path=DATA_PATH):
    df = pd.read_csv(path, encoding="latin-1")
    df = df.iloc[:, :2]                       # drop the empty "Unnamed" columns
    df.columns = ["label", "text"]
    df = df.dropna().drop_duplicates().reset_index(drop=True)
    df["target"] = (df["label"] == "spam").astype(int)   # spam = 1, ham = 0
    return df


def make_vectorizer():
    return TfidfVectorizer(preprocessor=clean_text, ngram_range=(1, 2),
                           min_df=2, sublinear_tf=True)


def get_models():
    return {
        "Naive Bayes": MultinomialNB(alpha=0.1),
        "Logistic Regression": LogisticRegression(C=10, max_iter=1000,
                                                  class_weight="balanced"),
        "SVM": CalibratedClassifierCV(LinearSVC(C=1, class_weight="balanced"), cv=5),
    }


def plot_confusion(cm, name, path):
    plt.figure(figsize=(4.2, 3.6))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False,
                xticklabels=["Ham", "Spam"], yticklabels=["Ham", "Spam"])
    plt.title(f"Confusion Matrix - {name}")
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.tight_layout()
    plt.savefig(path, dpi=130)
    plt.close()


def plot_top_words(pipe, path, n=20):
    """Most spam / ham indicating words, from Logistic Regression weights."""
    vec, clf = pipe.named_steps["tfidf"], pipe.named_steps["clf"]
    words = np.array(vec.get_feature_names_out())
    coef = clf.coef_[0]
    order = np.argsort(coef)
    top_spam, top_ham = order[-n:], order[:n]
    fig, ax = plt.subplots(1, 2, figsize=(12, 6))
    ax[0].barh(words[top_spam], coef[top_spam], color="#d9534f")
    ax[0].set_title("Top spam-indicating keywords")
    ax[1].barh(words[top_ham], -coef[top_ham], color="#5cb85c")
    ax[1].set_title("Top ham-indicating keywords")
    plt.tight_layout()
    plt.savefig(path, dpi=130)
    plt.close()


def main():
    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(REPORT_DIR, exist_ok=True)

    df = load_data()
    print(f"Dataset: {len(df)} messages after removing duplicates")
    print(df["label"].value_counts().to_string(), "\n")

    plt.figure(figsize=(4, 3.4))
    sns.countplot(x="label", data=df, hue="label",
                  palette=["#5cb85c", "#d9534f"], legend=False)
    plt.title("Class distribution")
    plt.tight_layout()
    plt.savefig(f"{REPORT_DIR}/class_distribution.png", dpi=130)
    plt.close()

    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], df["target"], test_size=0.2, stratify=df["target"],
        random_state=RANDOM_STATE)

    results, pipes = {}, {}
    for name, model in get_models().items():
        pipe = Pipeline([("tfidf", make_vectorizer()), ("clf", model)])
        pipe.fit(X_train, y_train)
        pred = pipe.predict(X_test)
        cm = confusion_matrix(y_test, pred)
        tn, fp, fn, tp = cm.ravel()
        results[name] = {
            "accuracy": accuracy_score(y_test, pred),
            "precision": precision_score(y_test, pred),
            "recall": recall_score(y_test, pred),
            "f1": f1_score(y_test, pred),
            "false_positive_rate": fp / (fp + tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
        }
        pipes[name] = pipe
        print(f"=== {name} ===")
        print(classification_report(y_test, pred, target_names=["ham", "spam"], digits=4))
        slug = name.replace(" ", "_")
        plot_confusion(cm, name, f"{REPORT_DIR}/cm_{slug}.png")
        joblib.dump(pipe, f"{MODEL_DIR}/{slug.lower()}.joblib")

    # best = highest F1; ties broken by lower false-positive rate
    best = max(results, key=lambda k: (round(results[k]["f1"], 4),
                                       -results[k]["false_positive_rate"]))
    joblib.dump(pipes[best], f"{MODEL_DIR}/best_model.joblib")
    joblib.dump(pipes["Logistic Regression"], f"{MODEL_DIR}/explainer_lr.joblib")

    comp = pd.DataFrame(results).T
    with open(f"{MODEL_DIR}/metrics.json", "w") as f:
        json.dump({"best_model": best, "results": results}, f, indent=2)

    comp[["accuracy", "precision", "recall", "f1"]].plot(
        kind="bar", figsize=(8, 4.5), ylim=(0.8, 1.01))
    plt.title("Model comparison")
    plt.xticks(rotation=0)
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(f"{REPORT_DIR}/model_comparison.png", dpi=130)
    plt.close()

    plot_top_words(pipes["Logistic Regression"], f"{REPORT_DIR}/top_keywords.png")

    print("\nSUMMARY")
    print(comp[["accuracy", "precision", "recall", "f1", "false_positive_rate"]]
          .astype(float).round(4).to_string())
    print(f"\nBest model: {best}  -> saved to {MODEL_DIR}/best_model.joblib")


if __name__ == "__main__":
    main()
