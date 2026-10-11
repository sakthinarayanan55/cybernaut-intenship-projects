# 📧 Email Spam Classifier

A machine-learning system that classifies messages as **spam** or **ham** (legitimate) using NLP (TF-IDF, stemming, stop-word removal) and probability-calibrated SVM & Logistic Regression. Includes a modern web UI, REST API, CLI, and keyword explanations.

The project is optimized for deployment on **Vercel** (serverless) as well as standard local execution.

---

## Results (20% held-out test set)

| Model               | Accuracy | Precision | Recall | F1     | False-positive rate |
|---------------------|----------|-----------|--------|--------|---------------------|
| Naive Bayes         | 98.84%   | 97.60%    | 93.13% | 95.31% | 0.33%               |
| Logistic Regression | 98.84%   | 95.42%    | 95.42% | 95.42% | 0.66%               |
| **SVM (best)**      | 99.13%   | 98.41%    | 94.66% | 96.50% | 0.22%               |

---

## Project Structure

```
spam_classifier/
├── api/
│   └── index.py               # Vercel serverless entrypoint
├── models/
│   ├── best_model.joblib      # Pre-trained calibrated SVM pipeline
│   ├── explainer_lr.joblib    # Logistic Regression model for keyword weights
│   └── metrics.json           # Benchmark metrics displayed on web UI
├── reports/
│   └── top_keywords.png       # Spam-indicating keywords visual chart
├── src/
│   ├── __init__.py
│   ├── preprocess.py          # NLP tokenization & Porter stemming
│   └── predictor.py           # Classifier logic & keyword explanations
├── templates/
│   └── index.html             # Responsive Web UI
├── app.py                     # Flask application & REST API
├── predict_cli.py             # Command-line classification tool
├── test_app.py                # Automated test suite
├── vercel.json                # Vercel routing configuration
├── requirements.txt           # Production serverless runtime dependencies
└── requirements-dev.txt       # Optional dependencies for model retraining
```

---

## 1. How to Host on Vercel

1. Push your repository to GitHub:
   ```bash
   git push origin main
   ```
2. Go to [vercel.com](https://vercel.com) and log in.
3. Click **Add New...** → **Project**.
4. Select your repository (`sakthinarayanan55/Email-Spam-Classifier`).
5. Vercel automatically detects `vercel.json` and `api/index.py`.
6. Click **Deploy**.
7. In ~1 minute, your app will be live with a URL like `https://email-spam-classifier.vercel.app`.

---

## 2. Running Locally

Requires **Python 3.9+**.

```bash
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate       # On Windows
# source venv/bin/activate  # On macOS/Linux

# 2. Install production dependencies
pip install -r requirements.txt

# 3. Start the Flask application
python app.py
```

Open **http://localhost:5000** in your browser.

### Command Line Tool

```bash
# Single message
python predict_cli.py "Congratulations! You won a free £1000 prize, call now"

# Interactive prompt
python predict_cli.py
```

### Run Tests

```bash
python test_app.py
```

### Retraining (Optional)

If you have a dataset and wish to re-train the models:

```bash
pip install -r requirements-dev.txt
# Place dataset at data/spam.csv
python train.py
```

---

## 3. REST API Reference

| Endpoint        | Method | Purpose                       |
|-----------------|--------|-------------------------------|
| `/`             | GET    | Web UI                        |
| `/predict`      | POST   | Classify `{"text": "..."}`    |
| `/api/metrics`  | GET    | Evaluation metrics            |
| `/health`       | GET    | Health check endpoint         |

### Sample Request
```bash
curl -X POST https://your-app.vercel.app/predict \
     -H "Content-Type: application/json" \
     -d '{"text": "WINNER!! Claim your free £900 prize now, call 09061701461"}'
```

### Sample Response
```json
{
  "label": "spam",
  "spam_probability": 0.9975,
  "confidence": 0.9975,
  "spam_keywords": [{"word": "prize", "score": 1.8}],
  "ham_keywords": []
}
```
