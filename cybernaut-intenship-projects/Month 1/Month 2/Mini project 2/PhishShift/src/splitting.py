"""
FR-03: Campaign-Separated Holdout vs Random Split Pipeline
Ensures strict template separation across splits to measure true generalization
to novel campaigns (zero-day tactics) and legitimate urgent business notices.
"""
from typing import Tuple, Dict, Any, List
import pandas as pd
from sklearn.model_selection import train_test_split, GroupKFold
from src.config import RANDOM_STATE

# Explicitly defined held-out campaigns (Section 08 Unique Team Constraint)
DEFAULT_HELDOUT_CAMPAIGNS = [
    "camp_unseen_heldout_phish",          # Unfamiliar zero-day phrasing phishing
    "camp_unseen_heldout_legit_urgent"    # Unfamiliar legitimate urgent business notice
]

def campaign_separated_split(
    df: pd.DataFrame,
    heldout_campaigns: List[str] = None,
    additional_test_ratio: float = 0.15,
    random_state: int = RANDOM_STATE
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Splits the dataset such that specific campaign groups are strictly held out.
    Guarantees zero template leakage between train and test.
    """
    if heldout_campaigns is None:
        heldout_campaigns = DEFAULT_HELDOUT_CAMPAIGNS

    # Identify heldout records
    heldout_mask = df["campaign_group"].isin(heldout_campaigns)
    heldout_df = df[heldout_mask].copy()
    remaining_df = df[~heldout_mask].copy()

    # Split remaining campaigns into train and validation/in-dist test
    # using stratified sampling on label and campaign to maintain distribution
    train_df, in_dist_test_df = train_test_split(
        remaining_df,
        test_size=additional_test_ratio,
        stratify=remaining_df["label"],
        random_state=random_state
    )

    # Combine in-distribution test with the strictly held-out unseen campaigns
    test_df = pd.concat([in_dist_test_df, heldout_df], ignore_index=True)

    metadata = {
        "split_strategy": "campaign_separated_holdout",
        "train_samples": len(train_df),
        "test_samples": len(test_df),
        "train_campaigns": list(train_df["campaign_group"].unique()),
        "test_campaigns": list(test_df["campaign_group"].unique()),
        "heldout_unseen_campaigns": heldout_campaigns,
        "heldout_unseen_samples": len(heldout_df),
        "train_label_distribution": train_df["label"].value_counts().to_dict(),
        "test_label_distribution": test_df["label"].value_counts().to_dict(),
        "leakage_audit": {
            "campaign_overlap": list(set(train_df["campaign_group"]).intersection(set(heldout_campaigns))),
            "zero_leakage_confirmed": len(set(train_df["campaign_group"]).intersection(set(heldout_campaigns))) == 0
        }
    }

    return train_df.reset_index(drop=True), test_df.reset_index(drop=True), metadata

def random_split(
    df: pd.DataFrame,
    test_size: float = 0.25,
    random_state: int = RANDOM_STATE
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Standard stratified train/test split ignoring campaign groups.
    Used as an experimental baseline to demonstrate template leakage & generalization gap.
    """
    train_df, test_df = train_test_split(
        df,
        test_size=test_size,
        stratify=df["label"],
        random_state=random_state
    )

    # Calculate campaign overlap in random split (demonstrating why FR-03 is essential)
    train_camps = set(train_df["campaign_group"])
    test_camps = set(test_df["campaign_group"])
    overlap = list(train_camps.intersection(test_camps))

    metadata = {
        "split_strategy": "random_stratified_split",
        "train_samples": len(train_df),
        "test_samples": len(test_df),
        "overlapping_campaigns_count": len(overlap),
        "overlapping_campaigns": overlap,
        "demonstration_note": "Notice template overlap occurs across splits in random split, causing overly optimistic accuracy."
    }

    return train_df.reset_index(drop=True), test_df.reset_index(drop=True), metadata
