"""Command-line classifier.

Usage:
  python predict_cli.py "Congratulations! You won a free prize, call now"
  python predict_cli.py            (interactive mode)
"""
import sys
from src.predictor import SpamPredictor


def show(p, text):
    r = p.predict(text)
    print(f"\n  -> {r['label'].upper()}  (spam probability {r['spam_probability']:.2%})")
    if r["spam_keywords"]:
        print("     spam keywords:", ", ".join(k["word"] for k in r["spam_keywords"]))


if __name__ == "__main__":
    pred = SpamPredictor()
    if len(sys.argv) > 1:
        show(pred, " ".join(sys.argv[1:]))
    else:
        print("Type a message (empty line to quit)")
        while True:
            t = input("\n> ").strip()
            if not t:
                break
            show(pred, t)
