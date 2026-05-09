"""Core RFM segmentation logic.

RFM = Recency, Frequency, Monetary
Simple scoring (1-5) per dimension, summed to 3-15, then labeled.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import pandas as pd


@dataclass(frozen=True)
class RFMScores:
    r: int  # 1-5 (5 = most recent)
    f: int  # 1-5 (5 = most frequent)
    m: int  # 1-5 (5 = highest spend)

    @property
    def total(self) -> int:
        return self.r + self.f + self.m


def score_recency(days_since_last: int) -> int:
    """Map days since last purchase to 1-5 score."""
    if days_since_last <= 7:
        return 5
    if days_since_last <= 30:
        return 4
    if days_since_last <= 90:
        return 3
    if days_since_last <= 180:
        return 2
    return 1


def score_frequency(count: int) -> int:
    """Map purchase count to 1-5 score."""
    if count >= 20:
        return 5
    if count >= 10:
        return 4
    if count >= 5:
        return 3
    if count >= 2:
        return 2
    return 1


def score_monetary(total_spend: float) -> int:
    """Map total spend to 1-5 score."""
    if total_spend >= 1000:
        return 5
    if total_spend >= 500:
        return 4
    if total_spend >= 200:
        return 3
    if total_spend >= 50:
        return 2
    return 1


def label_segment(rfm_total: int) -> str:
    """Map RFM total (3-15) to marketing segment."""
    if rfm_total >= 13:
        return "Champions"
    if rfm_total >= 10:
        return "Loyal"
    if rfm_total >= 7:
        return "At Risk"
    if rfm_total >= 5:
        return "Hibernating"
    return "Lost"


def calculate_rfm(
    customers_path: Path,
    transactions_path: Path,
    reference_date: datetime | None = None,
) -> pd.DataFrame:
    """Calculate RFM scores for all customers.

    Args:
        customers_path: CSV with customer_id, name, email columns
        transactions_path: CSV with transaction_id, customer_id, date, amount columns
        reference_date: Date to calculate recency from (default: today)

    Returns:
        DataFrame with one row per customer + R/F/M scores and segment label
    """
    if reference_date is None:
        reference_date = datetime.now()

    customers = pd.read_csv(customers_path)
    transactions = pd.read_csv(transactions_path)
    transactions["date"] = pd.to_datetime(transactions["date"])

    # Aggregate transactions per customer
    tx_agg = (
        transactions.groupby("customer_id")
        .agg(
            last_purchase=("date", "max"),
            count=("transaction_id", "count"),
            total_spend=("amount", "sum"),
        )
        .reset_index()
    )

    tx_agg["days_since_last"] = (
        reference_date - tx_agg["last_purchase"]
    ).dt.days

    # Score each dimension
    tx_agg["r_score"] = tx_agg["days_since_last"].apply(score_recency)
    tx_agg["f_score"] = tx_agg["count"].apply(score_frequency)
    tx_agg["m_score"] = tx_agg["total_spend"].apply(score_monetary)
    tx_agg["rfm_score"] = tx_agg["r_score"] + tx_agg["f_score"] + tx_agg["m_score"]
    tx_agg["segment"] = tx_agg["rfm_score"].apply(label_segment)

    # Join back to customer details
    result = customers.merge(
        tx_agg[["customer_id", "r_score", "f_score", "m_score", "rfm_score", "segment"]],
        on="customer_id",
        how="left",
    )
    result["segment"] = result["segment"].fillna("No purchases")

    return result
