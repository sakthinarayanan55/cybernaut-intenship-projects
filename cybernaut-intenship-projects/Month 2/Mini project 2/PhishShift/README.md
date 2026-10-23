# PhishShift — Message Risk Scanner (ML-07)

[![Vercel Deployment](https://img.shields.io/badge/Deploy-Vercel-black?logo=vercel)](https://vercel.com)
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![Framework](https://img.shields.io/badge/Framework-Flask%203.0-green?logo=flask)](https://flask.palletsprojects.com/)

**PhishShift Message Risk Scanner** is an enterprise-grade cyber-SOC decision support engine for probabilistic message risk evaluation, helpdesk triage, zero-day generalization, and selective abstention under high uncertainty.

---

## Key Features

1. **Live Triage Console**: Real-time simulated email and SMS threat vector assessment with inert URL defanging (`hxxp[:]//`, `[.]`).
2. **Selective Abstention (FR-04)**: Shannon Entropy predictive uncertainty oscilloscope routing ambiguous signals (38%–65% risk band) to human Tier-2 SOC analysts.
3. **Multi-Model Consensus (FR-02)**: Real-time consensus comparison across Rule-based heuristics, TF-IDF linear classification, and deep Domain-NLP hybrid networks.
4. **Generalization Gap & Adversarial Sandbox (FR-03 & FR-05)**: Testing campaign-separated holdout resilience and real-time evasion perturbations (leetspeak, punctuation salting, defanged splitting).

---

## Project Structure

```
PhishShift/
├── api/
│   └── index.py            # Vercel serverless entrypoint
├── data/
│   ├── build_dataset.py    # Dataset synthesis pipeline
│   ├── phishshift_dataset.csv
│   └── test_perturbations.json
├── models/
│   └── saved/              # Trained ML models (.joblib)
├── src/
│   ├── config.py           # Configuration and constants
│   ├── defanger.py         # URL defanging & sanitization (NFR-01)
│   ├── explainer.py        # Token cue explanations
│   ├── feature_extraction.py
│   └── models/             # Heuristic, TF-IDF, and Hybrid models
├── web/
│   ├── app.py              # Flask backend server
│   ├── static/             # CSS & JS assets
│   └── templates/          # Panoramic HTML triage interface
├── vercel.json             # Vercel serverless deployment config
└── requirements.txt        # Production dependencies
```

---

## Local Development

```bash
# Clone the repository
git clone https://github.com/sakthinarayanan55/PhishShift-Message-Risk-Scanner.git
cd PhishShift-Message-Risk-Scanner

# Install dependencies
pip install -r requirements.txt

# Run the web console
python web/app.py
```
Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

---

## Deploy to Vercel

1. Import this repository into [Vercel](https://vercel.com/new).
2. Framework Preset: **Other** (detected via `vercel.json`).
3. Click **Deploy**. Vercel will build and serve the application serverlessly using the `@vercel/python` runtime.
