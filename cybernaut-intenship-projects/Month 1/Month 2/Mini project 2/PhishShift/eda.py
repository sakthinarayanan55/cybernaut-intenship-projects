"""
T3: Exploratory Data Analysis (EDA) and Validity Inspection
Generates statistical distribution logs and 3 labelled visualizations for Section 12 of Final Report:
1. figure1_class_campaign_distribution.png: Class balance and campaign taxonomy
2. figure2_lexical_urgency_distributions.png: Message length and urgency token density across classes
3. figure3_model_generalization_gap.png: Comparative performance & campaign holdout drop
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

from src.config import DATASET_PATH, FIGURES_DIR, REPORTS_DIR, URGENCY_KEYWORDS

def generate_eda():
    print("[*] Performing Exploratory Data Analysis (EDA)...")
    df = pd.read_csv(DATASET_PATH)

    sns.set_theme(style="whitegrid", palette="muted")
    plt.rcParams.update({'font.sans-serif': 'DejaVu Sans', 'font.size': 10})

    # =========================================================================
    # Figure 1: Class Balance & Campaign Distribution Across Channels
    # =========================================================================
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Subplot 1A: Class distribution by channel
    channel_counts = df.groupby(['channel', 'label']).size().unstack(fill_value=0)
    channel_counts.columns = ['Benign (0)', 'Phishing (1)']
    channel_counts.plot(kind='bar', stacked=True, ax=axes[0], color=['#2ca02c', '#d62728'], alpha=0.85)
    axes[0].set_title("Figure 1A: Class & Channel Distribution", fontsize=12, fontweight='bold', pad=10)
    axes[0].set_xlabel("Communication Channel", fontweight='bold')
    axes[0].set_ylabel("Message Count", fontweight='bold')
    axes[0].set_xticklabels(axes[0].get_xticklabels(), rotation=0)
    for p in axes[0].patches:
        h = p.get_height()
        if h > 0:
            axes[0].annotate(f"{int(h)}", (p.get_x() + p.get_width() / 2., p.get_y() + h / 2.),
                             ha='center', va='center', color='white', fontweight='bold', fontsize=10)

    # Subplot 1B: Campaign Group record count
    camp_counts = df['campaign_group'].value_counts()
    colors = ['#d62728' if 'phish' in c else '#2ca02c' for c in camp_counts.index]
    camp_counts.plot(kind='barh', ax=axes[1], color=colors, alpha=0.85)
    axes[1].set_title("Figure 1B: Campaign Taxonomy & Balance", fontsize=12, fontweight='bold', pad=10)
    axes[1].set_xlabel("Number of Samples", fontweight='bold')
    axes[1].invert_yaxis()
    for i, v in enumerate(camp_counts):
        axes[1].text(v + 1, i, str(v), va='center', fontweight='bold', fontsize=9)

    plt.tight_layout()
    fig1_path = FIGURES_DIR / "figure1_class_campaign_distribution.png"
    plt.savefig(fig1_path, dpi=300)
    plt.close()
    print(f"[+] Figure 1 generated: {fig1_path}")

    # =========================================================================
    # Figure 2: Lexical Length and Urgency Token Density Distributions
    # =========================================================================
    df['char_length'] = df['body_text'].apply(lambda x: len(str(x)))
    df['word_count'] = df['body_text'].apply(lambda x: len(str(x).split()))
    df['urgency_token_count'] = df['body_text'].apply(
        lambda x: sum(1 for kw in URGENCY_KEYWORDS if kw in str(x).lower())
    )

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Subplot 2A: Character length by label
    sns.kdeplot(data=df[df['label'] == 0]['char_length'], ax=axes[0], label='Benign Messages', color='#2ca02c', fill=True, alpha=0.3)
    sns.kdeplot(data=df[df['label'] == 1]['char_length'], ax=axes[0], label='Phishing Messages', color='#d62728', fill=True, alpha=0.3)
    axes[0].set_title("Figure 2A: Message Character Length Density", fontsize=12, fontweight='bold', pad=10)
    axes[0].set_xlabel("Character Count", fontweight='bold')
    axes[0].set_ylabel("Density", fontweight='bold')
    axes[0].legend()

    # Subplot 2B: Urgency tokens across classes
    sns.countplot(data=df, x='urgency_token_count', hue='label', ax=axes[1], palette=['#2ca02c', '#d62728'])
    axes[1].set_title("Figure 2B: Frequency of Coercive Urgency Cues", fontsize=12, fontweight='bold', pad=10)
    axes[1].set_xlabel("Count of High-Urgency Cues in Message", fontweight='bold')
    axes[1].set_ylabel("Number of Messages", fontweight='bold')
    axes[1].legend(['Benign', 'Phishing'], title="Label")

    plt.tight_layout()
    fig2_path = FIGURES_DIR / "figure2_lexical_urgency_distributions.png"
    plt.savefig(fig2_path, dpi=300)
    plt.close()
    print(f"[+] Figure 2 generated: {fig2_path}")

    # =========================================================================
    # Figure 3: Generalization Gap and False-Positive Rate Comparison
    # =========================================================================
    # Load evaluation results if available
    eval_path = REPORTS_DIR / "evaluation_results.json"
    if eval_path.exists():
        with open(eval_path, "r", encoding="utf-8") as f:
            eval_data = json.load(f)

        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        # Subplot 3A: Model Accuracy & F1 on Campaign-Separated Test
        models = list(eval_data["models_evaluation"].keys())
        accs = [eval_data["models_evaluation"][m]["accuracy"] for m in models]
        f1s = [eval_data["models_evaluation"][m]["f1_score"] for m in models]

        x = np.arange(len(models))
        width = 0.35
        axes[0].bar(x - width/2, accs, width, label='Accuracy', color='#1f77b4')
        axes[0].bar(x + width/2, f1s, width, label='F1-Score', color='#ff7f0e')
        axes[0].set_title("Figure 3A: Comparative Model Performance (Campaign Holdout)", fontsize=12, fontweight='bold', pad=10)
        axes[0].set_ylabel("Score", fontweight='bold')
        axes[0].set_xticks(x)
        axes[0].set_xticklabels([m.split('(')[0].strip() for m in models], rotation=15, ha='right', fontsize=9)
        axes[0].set_ylim(0.5, 1.05)
        axes[0].legend()
        for i in range(len(models)):
            axes[0].text(x[i] - width/2, accs[i] + 0.01, f"{accs[i]:.2f}", ha='center', fontsize=9, fontweight='bold')
            axes[0].text(x[i] + width/2, f1s[i] + 0.01, f"{f1s[i]:.2f}", ha='center', fontsize=9, fontweight='bold')

        # Subplot 3B: FPR on Legitimate Urgent Messages (FR-05)
        fpr_urgent = [eval_data["urgent_benign_fpr_analysis"][m]["fpr_on_urgent_benign"] for m in models]
        fpr_general = [eval_data["urgent_benign_fpr_analysis"][m]["fpr_general_benign"] for m in models]

        axes[1].bar(x - width/2, fpr_general, width, label='General Benign FPR', color='#2ca02c')
        axes[1].bar(x + width/2, fpr_urgent, width, label='Urgent Benign FPR (Passwords/Payroll)', color='#d62728')
        axes[1].set_title("Figure 3B: False-Positive Inflation on Urgent Benign Messages", fontsize=12, fontweight='bold', pad=10)
        axes[1].set_ylabel("False Positive Rate", fontweight='bold')
        axes[1].set_xticks(x)
        axes[1].set_xticklabels([m.split('(')[0].strip() for m in models], rotation=15, ha='right', fontsize=9)
        axes[1].set_ylim(0.0, max(max(fpr_urgent) + 0.1, 0.4))
        axes[1].legend()
        for i in range(len(models)):
            axes[1].text(x[i] - width/2, fpr_general[i] + 0.005, f"{fpr_general[i]:.1%}", ha='center', fontsize=9, fontweight='bold')
            axes[1].text(x[i] + width/2, fpr_urgent[i] + 0.005, f"{fpr_urgent[i]:.1%}", ha='center', fontsize=9, fontweight='bold')

        plt.tight_layout()
        fig3_path = FIGURES_DIR / "figure3_model_generalization_gap.png"
        plt.savefig(fig3_path, dpi=300)
        plt.close()
        print(f"[+] Figure 3 generated: {fig3_path}")

    # Generate EDA Summary stats text
    eda_summary = {
        "dataset_total_samples": len(df),
        "total_phishing": int((df['label'] == 1).sum()),
        "total_benign": int((df['label'] == 0).sum()),
        "channels": df['channel'].value_counts().to_dict(),
        "sender_domain_types": df['sender_domain_type'].value_counts().to_dict(),
        "missing_values": df.isnull().sum().to_dict(),
        "avg_char_length_benign": round(float(df[df['label'] == 0]['char_length'].mean()), 2),
        "avg_char_length_phish": round(float(df[df['label'] == 1]['char_length'].mean()), 2),
        "visualizations_generated": [
            "figure1_class_campaign_distribution.png",
            "figure2_lexical_urgency_distributions.png",
            "figure3_model_generalization_gap.png"
        ]
    }

    with open(REPORTS_DIR / "eda_summary.json", "w", encoding="utf-8") as f:
        json.dump(eda_summary, f, indent=2)
    print(f"[+] EDA Summary saved to: {REPORTS_DIR / 'eda_summary.json'}")

if __name__ == "__main__":
    generate_eda()
