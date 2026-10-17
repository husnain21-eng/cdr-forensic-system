"""Contact network construction and centrality analysis."""
from __future__ import annotations

import networkx as nx
import pandas as pd


def build_call_graph(df: pd.DataFrame) -> nx.Graph:
    """Build an undirected weighted graph where nodes = phone numbers."""
    g = nx.Graph()
    if df.empty or "party_a" not in df.columns or "party_b" not in df.columns:
        return g

    pairs = df.dropna(subset=["party_a", "party_b"])[["party_a", "party_b"]]
    if pairs.empty:
        return g

    counts = pairs.groupby(["party_a", "party_b"]).size().reset_index(name="weight")

    for _, row in counts.iterrows():
        g.add_edge(str(row["party_a"]), str(row["party_b"]), weight=int(row["weight"]))
    return g


def centrality_table(g: nx.Graph) -> pd.DataFrame:
    """Return multiple mathematical centrality metrics for each node."""
    if g.number_of_nodes() == 0:
        return pd.DataFrame(columns=["Phone Number", "Degree", "Betweenness", "Eigenvector"])

    degree = nx.degree_centrality(g)
    betweenness = nx.betweenness_centrality(g)

    try:
        eigenvector = nx.eigenvector_centrality(g, max_iter=1000)
    except nx.PowerIterationFailedConvergence:
        eigenvector = {node: 0.0 for node in g.nodes()}

    df = pd.DataFrame([
        {
            "Phone Number": node,
            "Degree": round(degree.get(node, 0), 4),
            "Betweenness": round(betweenness.get(node, 0), 4),
            "Eigenvector": round(eigenvector.get(node, 0), 4)
        }
        for node in g.nodes()
    ])

    return df.sort_values("Betweenness", ascending=False).reset_index(drop=True)


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


def detect_communities(g: nx.Graph) -> dict[str, int]:
    """Detect communities using Greedy Modularity Optimization."""
    if g.number_of_nodes() == 0:
        return {}

    try:
        communities = nx.community.greedy_modularity_communities(g)
        community_map = {}
        for i, comm in enumerate(communities):
            for node in comm:
                community_map[node] = i
        return community_map
    except Exception:
        return {node: 0 for node in g.nodes()}