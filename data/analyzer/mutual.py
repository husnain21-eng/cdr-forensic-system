"""Mutual contact detection between two targets.

Given Target A's CDR and Target B's CDR, find phone numbers that
appear in BOTH datasets as a contact (party_b).
"""
from __future__ import annotations

import pandas as pd


def mutual_contacts(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
) -> pd.DataFrame:
    """Return sorted list of shared contacts between Target A and Target B.

    Both DataFrames must contain a 'party_b' column. Empty input returns
    an empty result — never raises.
    """
    empty = pd.DataFrame(columns=["Mutual Contact", "Calls A", "Calls B"])

    if df_a.empty or df_b.empty:
        return empty
    if "party_b" not in df_a.columns or "party_b" not in df_b.columns:
        return empty

    contacts_a = df_a["party_b"].dropna().astype(str)
    contacts_b = df_b["party_b"].dropna().astype(str)

    counts_a = contacts_a.value_counts()
    counts_b = contacts_b.value_counts()

    shared = sorted(set(counts_a.index) & set(counts_b.index))
    if not shared:
        return empty

    rows = [
        {
            "Mutual Contact": num,
            "Calls A": int(counts_a[num]),
            "Calls B": int(counts_b[num]),
        }
        for num in shared
    ]
    df = pd.DataFrame(rows)
    df["Combined Calls"] = df["Calls A"] + df["Calls B"]
    return df.sort_values("Combined Calls", ascending=False).reset_index(drop=True)