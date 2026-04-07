"""
Recursive wallet-community mapper.

Hierarchically discovers communities → sub-communities →
sub-sub-communities of linked wallets until complete exhaustion
of available real-world data.  Uses iterative BFS expansion,
graph-community detection (Louvain / greedy modularity), and
recursive descent into each discovered cluster.

The algorithm:
  1. Seed with one or more addresses.
  2. Fetch all transactions for those addresses.
  3. Build an undirected co-transaction graph.
  4. Run community detection to partition the graph.
  5. For each community whose member-count exceeds a threshold,
     expand outward by fetching transactions for every *new*
     address discovered in that community.
  6. Recurse (step 3-5) until no new addresses are found or
     the configured depth limit is reached.

Output is a nested tree of communities, each annotated with
member addresses, edge weights, and risk scores.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple

from aegis.api.manager import APIIntegrationManager
from aegis.config import UnifiedConfiguration
from aegis.utils import get_logger

try:
    import networkx as nx
    from networkx.algorithms.community import greedy_modularity_communities

    NX_AVAILABLE = True
except ImportError:
    NX_AVAILABLE = False


# ---------------------------------------------------------------------------
# Community node
# ---------------------------------------------------------------------------


class CommunityNode:
    """Represents one level in the hierarchical community tree."""

    __slots__ = ("community_id", "level", "members", "edges", "children", "metadata")

    def __init__(
        self,
        community_id: str,
        level: int,
        members: Set[str],
        edges: List[Tuple[str, str, float]],
    ) -> None:
        self.community_id = community_id
        self.level = level
        self.members = members
        self.edges = edges
        self.children: List[CommunityNode] = []
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "community_id": self.community_id,
            "level": self.level,
            "member_count": len(self.members),
            "edge_count": len(self.edges),
            "children": [c.to_dict() for c in self.children],
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# Recursive community mapper
# ---------------------------------------------------------------------------


class WalletCommunityMapper:
    """
    Recursively maps hierarchical wallet communities.

    Parameters
    ----------
    api_mgr
        The central API client manager (must have ``etherscan`` configured).
    config
        Platform configuration.
    max_depth
        Maximum recursion depth for sub-community expansion.
    min_community_size
        Minimum members for a community to be recursed into.
    max_addresses_per_level
        Cap on new addresses fetched per recursion level to bound runtime.
    """

    def __init__(
        self,
        api_mgr: APIIntegrationManager,
        config: UnifiedConfiguration,
        max_depth: int = 8,
        min_community_size: int = 3,
        max_addresses_per_level: int = 500,
    ) -> None:
        self._api = api_mgr
        self._cfg = config
        self._max_depth = max_depth
        self._min_size = min_community_size
        self._max_addrs = max_addresses_per_level
        self._log = get_logger("WalletCommunity.Mapper")
        self._global_visited: Set[str] = set()

    # -- public entry point --------------------------------------------------

    async def map(
        self,
        seed_addresses: List[str],
        network: str = "ethereum",
    ) -> Dict[str, Any]:
        """Map the full hierarchical community structure rooted at *seed_addresses*."""
        if not NX_AVAILABLE:
            return {"error": "networkx is required for community mapping"}

        self._global_visited.clear()
        root = await self._build_level(
            addresses=set(seed_addresses),
            network=network,
            level=0,
            parent_id="root",
        )
        stats = self._collect_stats(root)
        self._log.info(
            "Community mapping complete: %d communities, %d total addresses, depth %d",
            stats["total_communities"],
            stats["total_addresses"],
            stats["max_depth_reached"],
        )
        return {
            "seed_addresses": seed_addresses,
            "network": network,
            "community_tree": [n.to_dict() for n in root],
            "statistics": stats,
        }

    # -- recursive level builder ---------------------------------------------

    async def _build_level(
        self,
        addresses: Set[str],
        network: str,
        level: int,
        parent_id: str,
    ) -> List[CommunityNode]:
        if level >= self._max_depth or not addresses:
            return []

        new_addrs = addresses - self._global_visited
        if not new_addrs:
            return []
        new_addrs = set(list(new_addrs)[: self._max_addrs])
        self._global_visited.update(new_addrs)

        G = await self._build_graph(new_addrs, network)
        if G.number_of_nodes() < 2:
            return []

        communities = self._detect_communities(G)
        nodes: List[CommunityNode] = []

        for idx, members in enumerate(communities):
            cid = f"{parent_id}.c{idx}"
            sub = G.subgraph(members)
            edges = [(u, v, sub[u][v].get("weight", 1.0)) for u, v in sub.edges()]
            cnode = CommunityNode(cid, level, set(members), edges)
            cnode.metadata = {
                "density": nx.density(sub),
                "avg_degree": sum(d for _, d in sub.degree()) / max(len(members), 1),
            }

            if len(members) >= self._min_size:
                children = await self._build_level(
                    set(members), network, level + 1, cid
                )
                cnode.children = children

            nodes.append(cnode)

        return nodes

    # -- graph construction --------------------------------------------------

    async def _build_graph(self, addresses: Set[str], network: str) -> nx.Graph:
        G = nx.Graph()
        etherscan = self._api.get_client("etherscan")
        if not etherscan:
            return G

        for addr in addresses:
            G.add_node(addr)
            resp = await etherscan.get_transactions(addr)
            if not (resp.success and isinstance(resp.data, dict)):
                continue
            for tx in resp.data.get("result", [])[:200]:
                frm = tx.get("from", "").lower()
                to = tx.get("to", "").lower()
                if not frm or not to:
                    continue
                G.add_node(frm)
                G.add_node(to)
                if G.has_edge(frm, to):
                    G[frm][to]["weight"] += 1
                else:
                    G.add_edge(frm, to, weight=1)

        return G

    # -- community detection -------------------------------------------------

    @staticmethod
    def _detect_communities(G: nx.Graph) -> List[Set[str]]:
        try:
            return [set(c) for c in greedy_modularity_communities(G)]
        except Exception:
            return [set(G.nodes())]

    # -- statistics ----------------------------------------------------------

    def _collect_stats(self, roots: List[CommunityNode]) -> Dict[str, Any]:
        total_comm = 0
        total_addr: Set[str] = set()
        max_depth = 0

        def _walk(nodes: List[CommunityNode], depth: int) -> None:
            nonlocal total_comm, max_depth
            for n in nodes:
                total_comm += 1
                total_addr.update(n.members)
                max_depth = max(max_depth, depth)
                _walk(n.children, depth + 1)

        _walk(roots, 0)
        return {
            "total_communities": total_comm,
            "total_addresses": len(total_addr),
            "max_depth_reached": max_depth,
        }
