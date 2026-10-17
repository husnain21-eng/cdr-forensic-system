"""Markov Chain Predictive Modeling for CDR Sequences."""
from __future__ import annotations

import pandas as pd


def predict_next_call(df: pd.DataFrame) -> pd.DataFrame:
    """Build a Markov transition matrix to predict the next call.

    Returns a DataFrame with probabilities based on the most recent call.
    """
    if df.empty or "timestamp" not in df.columns or "party_b" not in df.columns:
        return pd.DataFrame()

    # 1. Sort chronologically to get the true sequence of states
    work = df.dropna(subset=["timestamp", "party_b"]).sort_values("timestamp")
    states = work["party_b"].astype(str).tolist()

    if len(states) < 2:
        return pd.DataFrame()

    # 2. Build transition counts (State i -> State j)
    transitions: dict[str, dict[str, int]] = {}
    for i in range(len(states) - 1):
        curr = states[i]
        nxt = states[i + 1]
        if curr not in transitions:
            transitions[curr] = {}
        transitions[curr][nxt] = transitions[curr].get(nxt, 0) + 1

    # 3. Predict based on the last known state
    last_state = states[-1]

    if last_state not in transitions:
        return pd.DataFrame()

    # 4. Calculate probabilities: P(j|i) = count(i->j) / total(i)
    next_options = transitions[last_state]
    total_transitions = sum(next_options.values())

    predictions = []
    for nxt, count in next_options.items():
        prob = (count / total_transitions) * 100
        predictions.append({
            "Target's Last Call": last_state,
            "Predicted Next Call": nxt,
            "Probability (%)": round(prob, 1),
            "Support (Times)": count
        })

    df_pred = pd.DataFrame(predictions)
    return df_pred.sort_values("Probability (%)", ascending=False).reset_index(drop=True)