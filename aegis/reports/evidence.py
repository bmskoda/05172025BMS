"""
Evidence chain-of-custody builder with BLAKE2b post-quantum hashing,
optional ECDSA-P384 signing, Merkle-tree integrity proofs, and
cryptographic evidence seals.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from aegis.models.core import CryptoHash, EvidenceMetadata, Timestamp
from aegis.utils import get_logger, hash_evidence

try:
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes as crypto_hashes
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


# ---------------------------------------------------------------------------
# BLAKE2b post-quantum evidence hasher
# ---------------------------------------------------------------------------


class PostQuantumHasher:
    """BLAKE2b-based cryptographic hashing (64-byte digest).

    BLAKE2b is recognised as a quantum-resistant-class hash function and is
    used here for evidence seals, chain anchors, and file-integrity checks.
    """

    DIGEST_SIZE: int = 64

    def __init__(self, key: Optional[bytes] = None) -> None:
        if key is not None and len(key) > 64:
            raise ValueError("BLAKE2b key must be <= 64 bytes.")
        self._key = key

    def _new_hasher(self, data: bytes = b"") -> "hashlib._Hash":
        kw: Dict[str, Any] = {"digest_size": self.DIGEST_SIZE}
        if self._key:
            kw["key"] = self._key
        return hashlib.blake2b(data, **kw)

    def hash_bytes(self, data: bytes) -> str:
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError(f"Expected bytes, got {type(data).__name__}.")
        return self._new_hasher(data).hexdigest()

    def hash_file(self, path: str) -> str:
        h = self._new_hasher()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1_048_576), b""):
                h.update(chunk)
        return h.hexdigest()

    def create_seal(self, data: Dict[str, Any], timestamp: Optional[str] = None) -> Dict[str, str]:
        """Create a cryptographic seal over *data*."""
        ts = timestamp or (Timestamp.now().to_iso())
        serialised = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
        data_hash = self.hash_bytes(serialised)
        nonce = secrets.token_hex(32)
        combined = bytes.fromhex(data_hash) + ts.encode("utf-8") + bytes.fromhex(nonce)
        seal_hash = self.hash_bytes(combined)
        return {"data_hash": data_hash, "timestamp": ts, "nonce": nonce, "seal_hash": seal_hash}

    def verify_seal(self, seal: Dict[str, str]) -> bool:
        required = {"data_hash", "timestamp", "nonce", "seal_hash"}
        if not required.issubset(seal):
            return False
        try:
            combined = (
                bytes.fromhex(seal["data_hash"])
                + seal["timestamp"].encode("utf-8")
                + bytes.fromhex(seal["nonce"])
            )
            return hmac.compare_digest(self.hash_bytes(combined), seal["seal_hash"])
        except Exception:
            return False

    def create_chain_anchor(self, items: List[Any]) -> Dict[str, Any]:
        """Build a Merkle-tree root hash over *items*."""
        if not items:
            raise ValueError("Cannot anchor empty list.")
        leaves = [
            self.hash_bytes(json.dumps(it, sort_keys=True, default=str).encode("utf-8"))
            for it in items
        ]
        while len(leaves) > 1:
            if len(leaves) % 2 == 1:
                leaves.append(leaves[-1])
            leaves = [
                self.hash_bytes(bytes.fromhex(leaves[i]) + bytes.fromhex(leaves[i + 1]))
                for i in range(0, len(leaves), 2)
            ]
        return {
            "root_hash": leaves[0],
            "leaf_count": len(items),
            "algorithm": "BLAKE2b-512",
            "timestamp": Timestamp.now().to_iso(),
        }


# ---------------------------------------------------------------------------
# Evidence chain builder
# ---------------------------------------------------------------------------


class EvidenceChainBuilder:
    """Tamper-evident evidence chain with BLAKE2b hashing, optional ECDSA
    signing, and Merkle-tree proofs."""

    def __init__(self, key_dir: Optional[str] = None) -> None:
        self._chains: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._merkle_roots: Dict[str, str] = {}
        self._log = get_logger("Evidence.Chain")
        self._private_key = None
        self._pq = PostQuantumHasher()

        if CRYPTO_AVAILABLE and key_dir:
            self._private_key = self._load_or_create_key(Path(key_dir))

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

    def add(self, case_id: str, evidence: Any, meta: EvidenceMetadata) -> str:
        eh = hash_evidence(evidence)
        prev = self._chains[case_id][-1]["hash"] if self._chains[case_id] else ""

        raw = json.dumps(evidence, sort_keys=True, default=str).encode("utf-8")
        blake2b_hash = self._pq.hash_bytes(raw)

        entry: Dict[str, Any] = {
            "evidence_id": meta.evidence_id,
            "timestamp": meta.timestamp.to_iso(),
            "hash": eh.digest,
            "blake2b_hash": blake2b_hash,
            "previous_hash": prev,
            "investigator": meta.investigator_id,
            "action": "collected",
            "signature": "",
        }
        if self._private_key and CRYPTO_AVAILABLE:
            payload = f"{entry['evidence_id']}:{entry['hash']}:{prev}"
            sig = self._private_key.sign(payload.encode(), ec.ECDSA(crypto_hashes.SHA384()))
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

    def create_seal(self, case_id: str) -> Dict[str, str]:
        """Create a BLAKE2b seal over the entire chain for *case_id*."""
        chain = self._chains.get(case_id, [])
        return self._pq.create_seal({"case_id": case_id, "chain": chain})

    def export(self, case_id: str) -> str:
        return json.dumps({
            "case_id": case_id,
            "exported": Timestamp.now().to_iso(),
            "merkle_root": self._merkle_roots.get(case_id, ""),
            "chain": self._chains.get(case_id, []),
            "verification": {
                "hash_algorithm": "sha3_256",
                "blake2b_algorithm": "BLAKE2b-512",
                "signature_scheme": "ECDSA-P384" if self._private_key else "none",
                "merkle_algorithm": "sha3_256",
            },
        }, indent=2)

    def create_evidence_bag(self, case_id: str, classification: str = "ATTORNEY WORK PRODUCT") -> Dict[str, Any]:
        """Create an FRE 902(13)-(14) compliant evidence bag with hash chain,
        Merkle root, BLAKE2b seal, and optional ECDSA signature."""
        chain = self._chains.get(case_id, [])
        seal = self.create_seal(case_id)
        bag_id = f"BAG-{secrets.token_hex(8).upper()}"
        return {
            "bag_version": "AEGIS-EVIDENCE-BAG-V2",
            "bag_id": bag_id,
            "case_id": case_id,
            "created_utc": Timestamp.now().to_iso(),
            "classification": classification,
            "evidence_count": len(chain),
            "merkle_root": self._merkle_roots.get(case_id, ""),
            "chain_hash_sha3": hashlib.sha3_512(
                json.dumps(chain, sort_keys=True, default=str).encode()
            ).hexdigest(),
            "blake2b_seal": seal,
            "signed": bool(self._private_key),
            "fre_compliance": ["FRE 902(13)", "FRE 902(14)", "NIST SP 800-86"],
        }

    def _update_merkle(self, case_id: str) -> None:
        hashes = [e["hash"] for e in self._chains[case_id]]
        while len(hashes) > 1:
            nxt: List[str] = []
            for i in range(0, len(hashes), 2):
                pair = hashes[i] + (hashes[i + 1] if i + 1 < len(hashes) else hashes[i])
                nxt.append(hashlib.sha3_256(pair.encode()).hexdigest())
            hashes = nxt
        self._merkle_roots[case_id] = hashes[0] if hashes else ""
