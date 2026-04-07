"""Tests for the AEGIS Blockchain Forensics Engine."""

from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from aegis.blockchain.forensics_engine import (
    BLOCKCHAIN_NETWORKS,
    DEFI_METHOD_SIGS,
    KNOWN_BRIDGES,
    KNOWN_DEFI,
    KNOWN_MIXERS,
    OFAC_SANCTIONED,
    BlockchainForensicsEngine,
    BlockchainLayer,
    BlockchainNetworkConfig,
    BlockchainTransaction,
    EntityType,
    EtherscanCompatibleClient,
    EvidenceChainManager,
    HyperGraphGNN,
    PrivacyProtocol,
    RateLimiter,
    RiskLevel,
    RiskScorer,
    TransactionGraphBuilder,
    TransactionType,
    WalletEntity,
    validate_address,
    normalize_address,
    BLOCKCHAIN_FEATURES,
)


# ── helpers ──────────────────────────────────────────────────────────────


def _make_tx(**overrides) -> BlockchainTransaction:
    defaults = {
        "tx_hash": "0x" + "a1" * 32,
        "timestamp": datetime(2025, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
        "from_address": "0x" + "11" * 20,
        "to_address": "0x" + "22" * 20,
        "amount": Decimal("1.5"),
        "currency": "ETH",
        "blockchain": "ethereum",
        "block_height": 20_000_000,
        "layer": BlockchainLayer.L1,
    }
    defaults.update(overrides)
    return BlockchainTransaction(**defaults)


# ── Enum tests ───────────────────────────────────────────────────────────


class TestEnums:
    def test_blockchain_layer_values(self):
        assert BlockchainLayer.L1 is not None
        assert BlockchainLayer.L2 is not None
        assert BlockchainLayer.ROLLUP is not None

    def test_transaction_type_coverage(self):
        assert len(TransactionType) >= 18

    def test_risk_level_ordering(self):
        assert RiskLevel.NO_RISK.value < RiskLevel.LOW.value
        assert RiskLevel.LOW.value < RiskLevel.CRITICAL.value
        assert RiskLevel.CRITICAL.value < RiskLevel.SANCTIONED.value

    def test_entity_type_has_unknown(self):
        assert EntityType.UNKNOWN is not None
        assert EntityType.EXCHANGE is not None

    def test_privacy_protocol_has_tornado(self):
        assert PrivacyProtocol.TORNADO_CASH is not None
        assert PrivacyProtocol.MONERO is not None


# ── Network registry ────────────────────────────────────────────────────


class TestNetworkRegistry:
    def test_has_major_networks(self):
        for name in ("bitcoin", "ethereum", "polygon", "arbitrum", "solana"):
            assert name in BLOCKCHAIN_NETWORKS

    def test_network_count(self):
        assert len(BLOCKCHAIN_NETWORKS) >= 14

    def test_ethereum_config(self):
        eth = BLOCKCHAIN_NETWORKS["ethereum"]
        assert eth.chain_id == 1
        assert eth.native_currency == "ETH"
        assert eth.is_evm is True
        assert eth.layer == BlockchainLayer.L1

    def test_bitcoin_is_utxo(self):
        btc = BLOCKCHAIN_NETWORKS["bitcoin"]
        assert btc.is_utxo is True
        assert btc.is_evm is False

    def test_l2_networks_are_l2(self):
        for name in ("polygon", "arbitrum", "optimism", "base", "zksync"):
            assert BLOCKCHAIN_NETWORKS[name].layer == BlockchainLayer.L2

    def test_privacy_coins_support_privacy(self):
        assert BLOCKCHAIN_NETWORKS["monero"].supports_privacy is True
        assert BLOCKCHAIN_NETWORKS["zcash"].supports_privacy is True


# ── Known-address sets ───────────────────────────────────────────────────


class TestKnownAddresses:
    def test_ofac_has_ethereum(self):
        assert "ethereum" in OFAC_SANCTIONED
        assert len(OFAC_SANCTIONED["ethereum"]) >= 5

    def test_mixers_has_entries(self):
        assert len(KNOWN_MIXERS.get("ethereum", set())) >= 5

    def test_bridges_has_entries(self):
        assert len(KNOWN_BRIDGES.get("ethereum", set())) >= 5

    def test_defi_has_uniswap(self):
        assert "uniswap" in KNOWN_DEFI

    def test_method_sigs(self):
        assert "0xa9059cbb" in DEFI_METHOD_SIGS
        assert DEFI_METHOD_SIGS["0xa9059cbb"] == TransactionType.TOKEN_TRANSFER


# ── BlockchainTransaction ───────────────────────────────────────────────


class TestBlockchainTransaction:
    def test_creation(self):
        tx = _make_tx()
        assert tx.tx_hash.startswith("0x")
        assert tx.amount == Decimal("1.5")
        assert tx.layer == BlockchainLayer.L1

    def test_quantum_signature_generated(self):
        tx = _make_tx()
        assert len(tx.quantum_signature) == 64  # sha3-256 hex

    def test_cryptographic_proof_generated(self):
        tx = _make_tx()
        assert len(tx.cryptographic_proof) == 128  # sha3-512 hex

    def test_to_dict_roundtrip(self):
        tx = _make_tx()
        d = tx.to_dict()
        assert d["tx_hash"] == tx.tx_hash
        assert d["amount"] == "1.5"
        assert d["risk_level"] == "NO_RISK"
        assert d["layer"] == "L1"

    def test_amount_coercion(self):
        tx = _make_tx(amount=42)
        assert tx.amount == Decimal("42")

    def test_flags_default_false(self):
        tx = _make_tx()
        assert tx.is_sanctioned is False
        assert tx.is_mixer is False
        assert tx.is_bridge is False
        assert tx.is_defi is False


# ── WalletEntity ────────────────────────────────────────────────────────


class TestWalletEntity:
    def test_creation(self):
        w = WalletEntity(
            address="0x" + "ab" * 20,
            blockchain="ethereum",
            entity_type=EntityType.EXCHANGE,
            entity_name="Binance",
        )
        assert w.entity_name == "Binance"
        assert w.risk_score == 0.0

    def test_defaults(self):
        w = WalletEntity(
            address="0x1", blockchain="ethereum", entity_type=EntityType.UNKNOWN
        )
        assert w.balance == Decimal("0")
        assert w.transaction_count == 0


# ── RiskScorer ───────────────────────────────────────────────────────────


class TestRiskScorer:
    def test_clean_tx_low_risk(self):
        scorer = RiskScorer()
        tx = _make_tx()
        score = scorer.score_transaction(tx)
        assert score < 0.3
        assert tx.risk_level == RiskLevel.NO_RISK

    def test_sanctioned_tx_max_risk(self):
        scorer = RiskScorer()
        tx = _make_tx()
        tx.is_sanctioned = True
        score = scorer.score_transaction(tx)
        assert score == 1.0

    def test_mixer_tx_high_risk(self):
        scorer = RiskScorer()
        tx = _make_tx(is_mixer=True)
        score = scorer.score_transaction(tx)
        assert score >= 0.9
        assert tx.risk_level == RiskLevel.CRITICAL

    def test_bridge_tx_medium_risk(self):
        scorer = RiskScorer()
        tx = _make_tx(is_bridge=True)
        score = scorer.score_transaction(tx)
        assert 0.3 <= score <= 0.7

    def test_large_amount_adds_risk(self):
        scorer = RiskScorer()
        tx = _make_tx(amount=Decimal("5000000"))
        score = scorer.score_transaction(tx)
        assert score > 0.0

    def test_wallet_scoring(self):
        scorer = RiskScorer()
        w = WalletEntity(
            address="0x1", blockchain="ethereum",
            entity_type=EntityType.MIXER, is_mixer=True,
        )
        score = scorer.score_wallet(w)
        assert score >= 0.9


# ── TransactionGraphBuilder ─────────────────────────────────────────────


class TestTransactionGraphBuilder:
    def test_add_transaction(self):
        gb = TransactionGraphBuilder()
        tx = _make_tx()
        gb.add_transaction(tx)
        assert gb.num_nodes == 2
        assert gb.num_edges == 1

    def test_multiple_transactions_share_nodes(self):
        gb = TransactionGraphBuilder()
        addr_a = "0x" + "aa" * 20
        addr_b = "0x" + "bb" * 20
        addr_c = "0x" + "cc" * 20

        gb.add_transaction(_make_tx(from_address=addr_a, to_address=addr_b))
        gb.add_transaction(_make_tx(from_address=addr_b, to_address=addr_c))

        assert gb.num_nodes == 3
        assert gb.num_edges == 2

    def test_max_nodes_respected(self):
        gb = TransactionGraphBuilder(max_nodes=4)
        for i in range(10):
            gb.add_transaction(
                _make_tx(
                    from_address=f"0x{'0' * 39}{i:01x}",
                    to_address=f"0x{'f' * 39}{i:01x}",
                )
            )
        assert gb.num_nodes <= 4

    def test_get_address(self):
        gb = TransactionGraphBuilder()
        addr = "0x" + "dd" * 20
        gb.add_transaction(_make_tx(from_address=addr))
        found = gb.get_address(0)
        assert found is not None
        assert addr in found


# ── EvidenceChainManager ────────────────────────────────────────────────


class TestEvidenceChainManager:
    def test_add_and_verify(self, tmp_path):
        mgr = EvidenceChainManager(tmp_path)
        mgr.add("CASE-001", "blockchain_tx", "etherscan", {"tx": "0xabc"})
        mgr.add("CASE-001", "risk_score", "chainalysis", {"score": 0.8})
        assert mgr.verify("CASE-001") is True

    def test_chain_linkage(self, tmp_path):
        mgr = EvidenceChainManager(tmp_path)
        link1 = mgr.add("C1", "a", "s", {"k": "v1"})
        link2 = mgr.add("C1", "b", "s", {"k": "v2"})
        assert link1.previous_hash == "0" * 64
        assert link2.previous_hash == link1.content_hash

    def test_export(self, tmp_path):
        mgr = EvidenceChainManager(tmp_path)
        mgr.add("C2", "tx", "src", {"data": 1})
        path = mgr.export("C2")
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["case_id"] == "C2"
        assert data["count"] == 1

    def test_empty_chain_verifies(self, tmp_path):
        mgr = EvidenceChainManager(tmp_path)
        assert mgr.verify("NONEXISTENT") is True

    def test_signature_present(self, tmp_path):
        mgr = EvidenceChainManager(tmp_path)
        link = mgr.add("C3", "t", "s", {"x": 1})
        assert len(link.signature) > 0


# ── Address validation ──────────────────────────────────────────────────


class TestAddressValidation:
    def test_valid_ethereum(self):
        assert validate_address("0x" + "ab" * 20, "ethereum") is True

    def test_invalid_ethereum_short(self):
        assert validate_address("0xabc", "ethereum") is False

    def test_empty_address(self):
        assert validate_address("", "ethereum") is False

    def test_bitcoin_legacy(self):
        assert validate_address("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "bitcoin") is True

    def test_bitcoin_bech32(self):
        assert validate_address(
            "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq", "bitcoin"
        ) is True

    def test_bitcoin_invalid(self):
        assert validate_address("xyz", "bitcoin") is False

    def test_solana_valid(self):
        assert validate_address("11111111111111111111111111111112", "solana") is True

    def test_normalize_evm(self):
        addr = "0x" + "ab" * 20
        result = normalize_address(addr, "ethereum")
        assert result == addr.lower()


# ── EtherscanCompatibleClient classification ────────────────────────────


class TestTxClassification:
    def _make_client(self):
        net = BLOCKCHAIN_NETWORKS["ethereum"]
        return EtherscanCompatibleClient(net, "test_key")

    def test_sanctioned_detection(self):
        client = self._make_client()
        sanctioned_addr = list(OFAC_SANCTIONED["ethereum"])[0]
        tx = _make_tx(to_address=sanctioned_addr)
        client._classify_tx(tx)
        assert tx.is_sanctioned is True
        assert tx.risk_score == 1.0

    def test_mixer_detection(self):
        client = self._make_client()
        mixer_addr = list(KNOWN_MIXERS["ethereum"])[0]
        tx = _make_tx(to_address=mixer_addr)
        client._classify_tx(tx)
        assert tx.is_mixer is True
        assert tx.privacy_protocol == PrivacyProtocol.TORNADO_CASH

    def test_bridge_detection(self):
        client = self._make_client()
        bridge_addr = list(KNOWN_BRIDGES["ethereum"])[0]
        tx = _make_tx(to_address=bridge_addr)
        client._classify_tx(tx)
        assert tx.is_bridge is True
        assert tx.tx_type == TransactionType.BRIDGE_DEPOSIT

    def test_defi_method_sig_detection(self):
        client = self._make_client()
        tx = _make_tx(input_data="0xa9059cbb" + "00" * 32)
        client._classify_tx(tx)
        assert tx.tx_type == TransactionType.TOKEN_TRANSFER

    def test_swap_method_sig(self):
        client = self._make_client()
        tx = _make_tx(input_data="0x38ed1739" + "00" * 32)
        client._classify_tx(tx)
        assert tx.tx_type == TransactionType.DEFI_SWAP

    def test_clean_tx_stays_clean(self):
        client = self._make_client()
        tx = _make_tx()
        client._classify_tx(tx)
        assert tx.is_sanctioned is False
        assert tx.is_mixer is False
        assert tx.is_bridge is False


# ── RateLimiter ─────────────────────────────────────────────────────────


class TestRateLimiter:
    @pytest.mark.asyncio
    async def test_acquire_returns(self):
        rl = RateLimiter(max_requests=10, time_window=1.0)
        await rl.acquire()

    @pytest.mark.asyncio
    async def test_multiple_acquires(self):
        rl = RateLimiter(max_requests=100, time_window=1.0)
        for _ in range(10):
            await rl.acquire()


# ── BlockchainForensicsEngine ───────────────────────────────────────────


class TestBlockchainForensicsEngine:
    def test_instantiation(self):
        engine = BlockchainForensicsEngine(
            api_keys={"etherscan": "test"},
            enable_gpu=False,
        )
        assert engine.api_keys["etherscan"] == "test"

    def test_get_client_ethereum(self):
        engine = BlockchainForensicsEngine(
            api_keys={"etherscan": "test_key"},
            enable_gpu=False,
        )
        client = engine.get_client("ethereum")
        assert client is not None
        assert isinstance(client, EtherscanCompatibleClient)

    def test_get_client_unknown(self):
        engine = BlockchainForensicsEngine(enable_gpu=False)
        client = engine.get_client("nonexistent_chain")
        assert client is None

    def test_stats_initial(self):
        engine = BlockchainForensicsEngine(enable_gpu=False)
        stats = engine.get_stats()
        assert stats["txs_analyzed"] == 0
        assert stats["networks"] >= 14


# ── HyperGraphGNN ───────────────────────────────────────────────────────


class TestHyperGraphGNN:
    def test_stub_when_no_torch(self):
        gnn = HyperGraphGNN()
        assert gnn is not None


# ── Feature flags ───────────────────────────────────────────────────────


class TestFeatureFlags:
    def test_features_dict_exists(self):
        assert isinstance(BLOCKCHAIN_FEATURES, dict)
        assert "aiohttp" in BLOCKCHAIN_FEATURES
        assert "numpy" in BLOCKCHAIN_FEATURES
        assert "torch" in BLOCKCHAIN_FEATURES
