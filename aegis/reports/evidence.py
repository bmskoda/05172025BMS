"""
Evidence chain-of-custody builder with optional ECDSA signing
and Merkle-tree integrity proofs.

When the ``cryptography`` package is present, each piece of evidence
is signed with ECDSA-P384 and linked into a Merkle tree.  Without
the package the chain still works but without cryptographic signatures.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from aegis.models.core import CryptoHash, EvidenceMetadata, Timestamp
from aegis.utils import get_logger, hash_evidence

try:
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


class EvidenceChainBuilder:
    """Tamper-evident, optionally ECDSA-signed evidence chain."""

    def __init__(self, key_dir: Optional[str] = None) -> None:
        self._chains: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._merkle_roots: Dict[str, str] = {}
        self._log = get_logger("Evidence.Chain")
        self._private_key = None

        if CRYPTO_AVAILABLE and key_dir:
            self._private_key = self._load_or_create_key(Path(key_dir))

    # -- key management ------------------------------------------------------

    @staticmethod
    def _load_or_create_key(directory: Path) -> Any:
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "evidence_key.pem"
        if path.exists():
            with open(path, "rb") as fh:
                return serialization.load_pem_private_key(fh.read(), password=None)
        key = ec.generate_private_key(ec.SECP384R1(), default_backend())
        with open(path, "wb") as fh:
            fh.write(key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            ))
        return key

    # -- public API ----------------------------------------------------------

    def add(self, case_id: str, evidence: Any, meta: EvidenceMetadata) -> str:
        eh = hash_evidence(evidence)
        prev = self._chains[case_id][-1]["hash"] if self._chains[case_id] else ""
        entry: Dict[str, Any] = {
            "evidence_id": meta.evidence_id,
            "timestamp": meta.timestamp.to_iso(),
            "hash": eh.digest,
            "previous_hash": prev,
            "investigator": meta.investigator_id,
            "action": "collected",
            "signature": "",
        }
        if self._private_key and CRYPTO_AVAILABLE:
            payload = f"{entry['evidence_id']}:{entry['hash']}:{prev}"
            sig = self._private_key.sign(payload.encode(), ec.ECDSA(hashes.SHA384()))
            entry["signature"] = base64.b64encode(sig).decode()

        self._chains[case_id].append(entry)
        self._update_merkle(case_id)
        self._log.info("Evidence %s added to case %s", meta.evidence_id, case_id)
        return meta.evidence_id

    def verify(self, case_id: str) -> Dict[str, Any]:
        chain = self._chains.get(case_id, [])
        if not chain:
            return {"valid": False, "error": "no chain"}
        issues: List[str] = []
        for i in range(1, len(chain)):
            if chain[i]["previous_hash"] != chain[i - 1]["hash"]:
                issues.append(f"hash-chain break at {i}")
            if chain[i - 1]["timestamp"] > chain[i]["timestamp"]:
                issues.append(f"timestamp order violation at {i}")
        return {"valid": not issues, "length": len(chain), "issues": issues}

    def export(self, case_id: str) -> str:
        return json.dumps({
            "case_id": case_id,
            "exported": Timestamp.now().to_iso(),
            "merkle_root": self._merkle_roots.get(case_id, ""),
            "chain": self._chains.get(case_id, []),
            "verification": {
                "hash_algorithm": "sha3_256",
                "signature_scheme": "ECDSA-P384" if self._private_key else "none",
                "merkle_algorithm": "sha3_256",
            },
        }, indent=2)

    # -- Merkle tree ---------------------------------------------------------

    def _update_merkle(self, case_id: str) -> None:
        hashes = [e["hash"] for e in self._chains[case_id]]
        while len(hashes) > 1:
            nxt: List[str] = []
            for i in range(0, len(hashes), 2):
                pair = hashes[i] + (hashes[i + 1] if i + 1 < len(hashes) else hashes[i])
                nxt.append(hashlib.sha3_256(pair.encode()).hexdigest())
            hashes = nxt
        self._merkle_roots[case_id] = hashes[0] if hashes else ""
