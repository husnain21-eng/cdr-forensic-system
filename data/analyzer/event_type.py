"""Analyzer for breaking down CDR data by Call Type."""
from __future__ import annotations
import pandas as pd


def standardize_call_types(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure call types are standardized to INCOMING, OUTGOING, SMS."""
    if "call_type" not in df.columns:
        return df

    def map_type(val):
        val = str(val).upper()
        if "OUT" in val: return "OUTGOING"
        if "INC" in val or "IN" in val: return "INCOMING"
        if "SMS" in val or "TEXT" in val: return "SMS"
        if "MISS" in val: return "MISSED"
        return "OTHER"

    df = df.copy()
    df["call_type"] = df["call_type"].apply(map_type)
    return df


def get_call_type_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Returns counts and percentages of each call type."""
    if df.empty or "call_type" not in df.columns:
        return pd.DataFrame(columns=["Type", "Count", "Percentage"])

    counts = df["call_type"].value_counts().reset_index()
    counts.columns = ["Type", "Count"]

    total = counts["Count"].sum()
    counts["Percentage"] = (counts["Count"] / total * 100).round(1)
    return counts