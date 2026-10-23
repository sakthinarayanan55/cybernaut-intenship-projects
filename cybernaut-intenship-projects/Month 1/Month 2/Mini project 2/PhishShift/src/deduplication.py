"""
FR-01: Near-Duplicate Template Deduplication Pipeline
Audits and removes near-identical templates before train/test splitting
to prevent data leakage across splits.
"""
import re
import json
from typing import Tuple, List, Dict, Any
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from src.config import REPORTS_DIR

def normalize_template_text(text: str) -> str:
    """
    Normalizes text to detect underlying campaign template:
    - Replaces ticket numbers, amounts, dates, and names with generic tokens
    - Lowercases and collapses whitespace
    """
    if not isinstance(text, str):
        return ""
    s = text.lower()
    # Mask numbers / ticket IDs / amounts
    s = re.sub(r'#?\d+', '<NUM>', s)
    s = re.sub(r'\$\s*<NUM>', '<MONEY>', s)
    # Mask defanged URLs
    s = re.sub(r'hxxps?\[:\]//[^\s]+', '<URL>', s)
    s = re.sub(r'[a-z0-9_\-\.]+\[\.\][a-z0-9_\-\./]+', '<URL>', s)
    # Collapse whitespace and punctuation
    s = re.sub(r'[^\w\s<>]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def deduplicate_templates(
    df: pd.DataFrame,
    similarity_threshold: float = 0.88,
    audit_file_path: str = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Identifies and removes near-identical templates based on cosine similarity of character 3-grams.
    Ensures that identical or slightly varied phishing templates don't bleed across train/test splits.
    
    Returns:
        (deduplicated_df, audit_log)
    """
    if df.empty:
        return df, {}

    df = df.copy().reset_index(drop=True)
    
    # Generate normalized text representations
    normalized_texts = [
        normalize_template_text(f"{row['subject_or_title']} {row['body_text']}")
        for _, row in df.iterrows()
    ]
    
    # Character n-gram vectorizer for robust fuzzy template matching
    vectorizer = TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 4), min_df=1)
    tfidf_matrix = vectorizer.fit_transform(normalized_texts)
    
    sim_matrix = cosine_similarity(tfidf_matrix)
    
    num_samples = len(df)
    visited = set()
    kept_indices = []
    removed_records = []
    clusters = []

    for i in range(num_samples):
        if i in visited:
            continue
        
        # New cluster with representative i
        cluster_members = [i]
        visited.add(i)
        
        for j in range(i + 1, num_samples):
            if j in visited:
                continue
            
            sim = sim_matrix[i, j]
            # Must belong to same label and channel to be considered a duplicate template
            if sim >= similarity_threshold and df.loc[i, 'label'] == df.loc[j, 'label']:
                cluster_members.append(j)
                visited.add(j)
                removed_records.append({
                    "removed_message_id": df.loc[j, 'message_id'],
                    "canonical_message_id": df.loc[i, 'message_id'],
                    "similarity": round(float(sim), 4),
                    "campaign_group": df.loc[j, 'campaign_group'],
                    "sample_text_snippet": df.loc[j, 'body_text'][:120]
                })

        kept_indices.append(i)
        if len(cluster_members) > 1:
            clusters.append({
                "canonical_id": df.loc[i, 'message_id'],
                "duplicate_ids": [df.loc[idx, 'message_id'] for idx in cluster_members[1:]],
                "cluster_size": len(cluster_members)
            })

    dedup_df = df.iloc[kept_indices].copy().reset_index(drop=True)
    
    audit_log = {
        "requirement": "FR-01: Deduplicate near-identical templates before splitting train and test",
        "original_count": num_samples,
        "deduplicated_count": len(dedup_df),
        "removed_count": len(removed_records),
        "similarity_threshold": similarity_threshold,
        "clusters_detected": len(clusters),
        "sample_clusters": clusters[:5],
        "removed_details": removed_records[:15]
    }

    if audit_file_path is None:
        audit_file_path = str(REPORTS_DIR / "deduplication_audit.json")
        
    with open(audit_file_path, "w", encoding="utf-8") as f:
        json.dump(audit_log, f, indent=2)

    return dedup_df, audit_log
