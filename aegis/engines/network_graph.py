"""
Network-graph analyser: hypergraph structure, GNN risk scoring,
centrality analysis, community detection, pattern detection
(layering, smurfing, round-tripping).
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple

from aegis.config import UnifiedConfiguration
from aegis.constants import GNN_HIDDEN_DIM, GNN_NUM_LAYERS
from aegis.models.core import NetworkEdge, NetworkNode, Transaction
from aegis.utils import get_logger

try:
    import networkx as nx
    from networkx.algorithms import community

    NX = True
except ImportError:
    NX = False

try:
    import numpy as np

    NP = True
except ImportError:
    NP = False

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    TORCH = True
except ImportError:
    TORCH = False

try:
    from torch_geometric.nn import GCNConv

    PYG = True
except ImportError:
    PYG = False


# ---------------------------------------------------------------------------
# Hypergraph
# ---------------------------------------------------------------------------


class HyperGraph:
    """Multi-node edges (hyperedges) for complex relationship modelling."""

    def __init__(self) -> None:
        self._nodes: Dict[str, NetworkNode] = {}
        self._hyperedges: Dict[str, Set[str]] = {}
        self._node_edges: Dict[str, Set[str]] = defaultdict(set)
        self._edge_attrs: Dict[str, Dict[str, Any]] = {}

    def add_node(self, node: NetworkNode) -> None:
        self._nodes[node.node_id] = node

    def add_hyperedge(self, eid: str, node_ids: Set[str], attrs: Optional[Dict] = None) -> None:
        self._hyperedges[eid] = node_ids
        self._edge_attrs[eid] = attrs or {}
        for nid in node_ids:
            if nid in self._nodes:
                self._node_edges[nid].add(eid)

    def neighbors(self, nid: str) -> Set[str]:
        out: Set[str] = set()
        for eid in self._node_edges.get(nid, set()):
            out.update(self._hyperedges.get(eid, set()))
        out.discard(nid)
        return out

    def degree(self, nid: str) -> int:
        return len(self._node_edges.get(nid, set()))

    def to_networkx(self) -> Optional[Any]:
        if not NX:
            return None
        G = nx.Graph()
        for nid, node in self._nodes.items():
            G.add_node(nid, **node.to_dict())
        for eid, nids in self._hyperedges.items():
            ns = list(nids)
            for i in range(len(ns)):
                for j in range(i + 1, len(ns)):
                    G.add_edge(ns[i], ns[j], **self._edge_attrs.get(eid, {}))
        return G

    def stats(self) -> Dict[str, Any]:
        return {
            "nodes": len(self._nodes),
            "hyperedges": len(self._hyperedges),
            "avg_degree": (
                sum(self.degree(n) for n in self._nodes) / len(self._nodes)
                if self._nodes
                else 0
            ),
        }


# ---------------------------------------------------------------------------
# GNN (GCN-based) for node-risk prediction
# ---------------------------------------------------------------------------


if TORCH and PYG:
    class _GCNModel(nn.Module):
        def __init__(self, in_dim: int, hidden: int, layers: int, out: int) -> None:
            super().__init__()
            self.convs = nn.ModuleList()
            self.convs.append(GCNConv(in_dim, hidden))
            for _ in range(layers - 2):
                self.convs.append(GCNConv(hidden, hidden))
            self.convs.append(GCNConv(hidden, out))
            self.drop = nn.Dropout(0.5)

        def forward(self, x, edge_index):
            for conv in self.convs[:-1]:
                x = self.drop(F.relu(conv(x, edge_index)))
            return F.log_softmax(self.convs[-1](x, edge_index), dim=1)
else:
    _GCNModel = None  # type: ignore[assignment,misc]


class GraphNeuralNetwork:
    def __init__(self, in_dim: int = 64, hidden: int = GNN_HIDDEN_DIM, layers: int = GNN_NUM_LAYERS, classes: int = 2) -> None:
        self._model = None
        self._log = get_logger("GNN")
        if TORCH and PYG and _GCNModel is not None:
            self._model = _GCNModel(in_dim, hidden, layers, classes)
            self._log.info("GNN model built (%d layers, hidden=%d)", layers, hidden)

    def predict_risk(self, features: Any, edge_index: Any) -> Any:
        if self._model is None or not TORCH:
            if NP:
                return np.random.random(len(features))
            return [0.5] * len(features)
        self._model.eval()
        with torch.no_grad():
            x = torch.FloatTensor(features)
            ei = torch.LongTensor(edge_index)
            logits = self._model(x, ei)
            return torch.exp(logits)[:, 1].numpy()


# ---------------------------------------------------------------------------
# Pattern detectors
# ---------------------------------------------------------------------------


class NetworkPatternDetector:
    def __init__(self) -> None:
        self._log = get_logger("Network.Patterns")

    def detect_layering(self, txns: List[Transaction], min_hops: int = 3) -> Dict[str, Any]:
        if not NX:
            return {"layering_detected": False, "error": "networkx unavailable"}
        G = nx.DiGraph()
        for t in txns:
            G.add_edge(t.from_address.address, t.to_address.address if t.to_address else "null")
        longest = 0
        for src in list(G.nodes())[:200]:
            for tgt in list(G.nodes())[:200]:
                if src == tgt:
                    continue
                try:
                    longest = max(longest, nx.shortest_path_length(G, src, tgt))
                except nx.NetworkXNoPath:
                    pass
        return {
            "layering_detected": longest >= min_hops,
            "longest_path": longest,
            "confidence": min(longest / min_hops, 1.0) if longest >= min_hops else 0.0,
        }

    def detect_smurfing(
        self, txns: List[Transaction], threshold: float = 10_000, window_h: int = 24
    ) -> Dict[str, Any]:
        by_src: Dict[str, List[Transaction]] = defaultdict(list)
        for t in txns:
            by_src[t.from_address.address].append(t)
        suspicious: List[Dict[str, Any]] = []
        for src, ts in by_src.items():
            ts.sort(key=lambda x: x.timestamp.nanoseconds)
            ws = 0
            for i in range(len(ts)):
                while ts[i].timestamp.nanoseconds - ts[ws].timestamp.nanoseconds > window_h * 3.6e12:
                    ws += 1
                window = ts[ws : i + 1]
                total = sum(float(t.value.value) for t in window)
                if len(window) >= 3 and total >= threshold * 0.8:
                    avg = total / len(window)
                    if avg < threshold * 0.5:
                        suspicious.append({"address": src, "count": len(window), "total": total})
        return {
            "smurfing_detected": bool(suspicious),
            "suspicious_sources": suspicious,
            "confidence": min(len(suspicious) * 0.2, 1.0),
        }

    def detect_round_tripping(self, txns: List[Transaction]) -> Dict[str, Any]:
        if not NX:
            return {"round_tripping_detected": False, "error": "networkx unavailable"}
        G = nx.DiGraph()
        for t in txns:
            if t.to_address:
                G.add_edge(t.from_address.address, t.to_address.address)
        cycles = list(nx.simple_cycles(G))
        return {
            "round_tripping_detected": bool(cycles),
            "cycle_count": len(cycles),
            "cycles_sample": cycles[:10],
            "confidence": min(len(cycles) * 0.1, 1.0),
        }


# ---------------------------------------------------------------------------
# Composite network analyser
# ---------------------------------------------------------------------------


class NetworkGraphAnalyzer:
    def __init__(self, config: UnifiedConfiguration) -> None:
        self.hg = HyperGraph()
        self.gnn = GraphNeuralNetwork()
        self.patterns = NetworkPatternDetector()
        self._log = get_logger("Network.Analyzer")

    def build(self, entities: List[NetworkNode], edges: List[NetworkEdge]) -> None:
        for e in entities:
            self.hg.add_node(e)
        groups: Dict[str, List[NetworkEdge]] = defaultdict(list)
        for edge in edges:
            groups[edge.relationship_type.value].append(edge)
        for rel_type, rels in groups.items():
            for i, r in enumerate(rels):
                self.hg.add_hyperedge(f"{rel_type}_{i}", {r.source_id, r.target_id}, {"weight": r.weight})
        self._log.info("Network built: %d nodes, %d edges", len(entities), len(edges))

    def centrality(self) -> Dict[str, Any]:
        G = self.hg.to_networkx()
        if not G or G.number_of_nodes() == 0:
            return {}
        return {
            "degree": nx.degree_centrality(G),
            "betweenness": nx.betweenness_centrality(G),
            "closeness": nx.closeness_centrality(G),
            "pagerank": nx.pagerank(G),
        }

    def communities(self) -> Dict[str, Any]:
        G = self.hg.to_networkx()
        if not G or G.number_of_nodes() < 2:
            return {"communities": []}
        try:
            coms = list(community.greedy_modularity_communities(G))
            return {
                "count": len(coms),
                "communities": [list(c) for c in coms],
                "modularity": community.modularity(G, coms),
            }
        except Exception as exc:
            return {"error": str(exc)}

    def key_players(self, top_n: int = 10) -> List[Dict[str, Any]]:
        cent = self.centrality()
        if not cent:
            return []
        combined: Dict[str, float] = {}
        for nid in self.hg._nodes:
            combined[nid] = (
                cent.get("degree", {}).get(nid, 0) * 0.2
                + cent.get("betweenness", {}).get(nid, 0) * 0.3
                + cent.get("closeness", {}).get(nid, 0) * 0.2
                + cent.get("pagerank", {}).get(nid, 0) * 0.3
            )
        ranked = sorted(combined.items(), key=lambda x: x[1], reverse=True)
        return [
            {"node_id": nid, "score": sc, "entity": self.hg._nodes[nid].to_dict()}
            for nid, sc in ranked[:top_n]
        ]
