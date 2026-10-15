"""Contact network construction and centrality analysis.

Pure functions — no UI, no globals. Takes a DataFrame, returns objects.
"""
from __future__ import annotations

import networkx as nx
import pandas as pd


def build_call_graph(df: pd.DataFrame) -> nx.Graph:
    """Build an undirected weighted graph where:
      - nodes = phone numbers
      - edges = at least one call between them
      - edge weight = number of calls

    Rows with missing party_a or party_b are silently skipped.
    """
    g = nx.Graph()
    if df.empty or "party_a" not in df.columns or "party_b" not in df.columns:
        return g

    pairs = df.dropna(subset=["party_a", "party_b"])[["party_a", "party_b"]]
    if pairs.empty:
        return g

    counts = (
        pairs.groupby(["party_a", "party_b"])
             .size()
             .reset_index(name="weight")
    )

    for _, row in counts.iterrows():
        g.add_edge(
            str(row["party_a"]),
            str(row["party_b"]),
            weight=int(row["weight"]),
        )
    return g


def centrality_table(g: nx.Graph) -> pd.DataFrame:
    """Return a DataFrame of degree centrality per phone number.

    Degree centrality = fraction of nodes each node is directly connected to.
    Higher score = more central communicator.
    """
    if g.number_of_nodes() == 0:
        return pd.DataFrame(columns=["Phone Number", "Centrality"])

    scores = nx.degree_centrality(g)
    df = pd.DataFrame(
        [
            {"Phone Number": node, "Centrality": round(score, 4)}
            for node, score in scores.items()
        ]
    )
    return df.sort_values("Centrality", ascending=False).reset_index(drop=True)


def top_edges(g: nx.Graph, limit: int = 20) -> pd.DataFrame:
    """Return the top `limit` edges by weight (busiest communication pairs)."""
    if g.number_of_edges() == 0:
        return pd.DataFrame(columns=["From", "To", "Calls"])

    edges = [
        {"From": u, "To": v, "Calls": data["weight"]}
        for u, v, data in g.edges(data=True)
    ]
    df = pd.DataFrame(edges)
    return df.sort_values("Calls", ascending=False).head(limit).reset_index(drop=True)