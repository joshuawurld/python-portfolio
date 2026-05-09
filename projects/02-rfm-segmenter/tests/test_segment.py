"""Tests for RFM segmentation core logic."""
from datetime import datetime

import pandas as pd

from src.segment import (
    calculate_rfm,
    label_segment,
    score_frequency,
    score_monetary,
    score_recency,
)


def test_score_recency_recent_gets_5():
    assert score_recency(5) == 5
    assert score_recency(7) == 5


def test_score_recency_old_gets_1():
    assert score_recency(365) == 1


def test_score_frequency_high_gets_5():
    assert score_frequency(25) == 5


def test_score_frequency_single_gets_1():
    assert score_frequency(1) == 1


def test_score_monetary_big_spender_gets_5():
    assert score_monetary(1500) == 5


def test_score_monetary_small_gets_1():
    assert score_monetary(10) == 1


def test_label_segment_champions():
    assert label_segment(14) == "Champions"


def test_label_segment_lost():
    assert label_segment(3) == "Lost"


def test_calculate_rfm_smoke_test(tmp_path):
    """End-to-end with dummy CSVs."""
    customers = tmp_path / "customers.csv"
    transactions = tmp_path / "transactions.csv"

    customers.write_text(
        "customer_id,name,email\nC001,Alice,alice@test.com\nC002,Bob,bob@test.com"
    )
    transactions.write_text(
        "transaction_id,customer_id,date,amount\n"
        "T001,C001,2025-04-01,100.00\n"
        "T002,C001,2025-03-01,50.00\n"
        "T003,C002,2024-01-01,20.00"
    )

    ref_date = datetime(2025, 4, 15)
    result = calculate_rfm(customers, transactions, ref_date)

    assert len(result) == 2
    assert "r_score" in result.columns
    assert "segment" in result.columns
    # Alice bought twice recently -> higher score than Bob
    assert result.loc[result["customer_id"] == "C001", "rfm_score"].iloc[0] > \
           result.loc[result["customer_id"] == "C002", "rfm_score"].iloc[0]
