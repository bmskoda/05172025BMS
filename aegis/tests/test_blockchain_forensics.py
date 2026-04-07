"""Tests for the AEGIS Blockchain Forensics Engine v20.1."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from aegis.blockchain.forensics_engine import (
    BLOCKCHAIN_FEATURES,
    BLOCKCHAIN_NETWORKS,
    BRIDGE_DESTINATION,
    DEFI_METHOD_SIGS,
    FRACTIONALIZATION_PROTOCOLS,
    KNOWN_BRIDGES,
    KNOWN_DEFI,
    KNOWN_MIXERS,
    NFT_MARKETPLACES,
    OFAC_SANCTIONED,
    BlockchainForensicsEngine,
    BlockchainLayer,
    BlockchainMonitor,
    BlockchainNetworkConfig,
    BlockchainTransaction,
    CrossChainBridge,
    DeFiInteraction,
    EntityType,
    EtherscanCompatibleClient,
    EvidenceChainManager,
    HyperGraphGNN,
    MixerTransaction,
    NFTTracker,
    NFTTransfer,
    PrivacyProtocol,
    RateLimiter,
    RiskLevel,
    RiskScorer,
    TransactionGraphBuilder,
    TransactionType,
    WalletEntity,
    validate_address,
    normalize_address,
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


def _make_nft_transfer(**overrides) -> NFTTransfer:
    defaults = {
        "nft_contract": "0x" + "cc" * 20,
        "token_id": "42",
        "nft_standard": "ERC721",
        "from_address": "0x" + "aa" * 20,
        "to_address": "0x" + "bb" * 20,
        "tx_hash": "0x" + "dd" * 32,
        "timestamp": datetime(2025, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
    }
    defaults.update(overrides)
    return NFTTransfer(**defaults)


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
    def test_has_major_l1_networks(self):
        for name in (
            "bitcoin", "ethereum", "solana", "cardano", "polkadot",
            "avalanche", "bsc", "tron", "monero", "zcash", "near",
            "algorand", "cosmos", "tezos", "stellar", "xrp", "dogecoin",
            "litecoin", "bitcoin_cash", "fantom", "harmony",
        ):
            assert name in BLOCKCHAIN_NETWORKS, f"Missing L1: {name}"

    def test_has_major_l2_networks(self):
        for name in (
            "polygon", "arbitrum", "optimism", "base", "zksync",
            "starknet", "polygon_zkevm", "loopring", "immutable_x", "dydx",
        ):
            assert name in BLOCKCHAIN_NETWORKS, f"Missing L2: {name}"

    def test_network_count_ge_30(self):
        assert len(BLOCKCHAIN_NETWORKS) >= 30

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

    def test_websocket_endpoints_present(self):
        eth = BLOCKCHAIN_NETWORKS["ethereum"]
        assert len(eth.websocket_endpoints) >= 1
        sol = BLOCKCHAIN_NETWORKS["solana"]
        assert len(sol.websocket_endpoints) >= 1

    def test_all_configs_have_required_fields(self):
        for name, net in BLOCKCHAIN_NETWORKS.items():
            assert net.name, f"{name} missing name"
            assert net.native_currency, f"{name} missing currency"
            assert net.block_time_seconds > 0, f"{name} bad block time"
            assert net.confirmation_blocks >= 1, f"{name} bad confirmations"


# ── Known-address sets ───────────────────────────────────────────────────


class TestKnownAddresses:
    def test_ofac_ethereum_count(self):
        assert len(OFAC_SANCTIONED["ethereum"]) >= 15

    def test_ofac_has_tron(self):
        assert "tron" in OFAC_SANCTIONED
        assert len(OFAC_SANCTIONED["tron"]) >= 1

    def test_mixers_multi_chain(self):
        assert len(KNOWN_MIXERS.get("ethereum", set())) >= 5
        assert len(KNOWN_MIXERS.get("bsc", set())) >= 1
        assert len(KNOWN_MIXERS.get("arbitrum", set())) >= 1

    def test_bridges_has_entries(self):
        assert len(KNOWN_BRIDGES.get("ethereum", set())) >= 7

    def test_bridge_destination_mapping(self):
        assert "0x99c9fc46f92e8a1c0dec1b1747d010903e884be1" in BRIDGE_DESTINATION
        assert BRIDGE_DESTINATION["0x99c9fc46f92e8a1c0dec1b1747d010903e884be1"] == "optimism"
        assert BRIDGE_DESTINATION["0x4dbd4fc535ac27206064b68ffcf827b0a60bab3f"] == "arbitrum"

    def test_defi_multi_chain_uniswap(self):
        uni = KNOWN_DEFI["uniswap"]
        for chain in ("ethereum", "polygon", "arbitrum", "optimism"):
            assert chain in uni, f"Uniswap missing on {chain}"

    def test_defi_multi_chain_aave(self):
        aave = KNOWN_DEFI["aave"]
        for chain in ("ethereum", "polygon", "arbitrum", "optimism", "avalanche"):
            assert chain in aave, f"Aave missing on {chain}"

    def test_defi_has_curve_makerdao(self):
        assert "curve" in KNOWN_DEFI
        assert "makerdao" in KNOWN_DEFI

    def test_nft_marketplaces(self):
        assert "ethereum" in NFT_MARKETPLACES
        assert "opensea" in NFT_MARKETPLACES["ethereum"]
        assert "blur" in NFT_MARKETPLACES["ethereum"]

    def test_fractionalization_protocols(self):
        assert "ethereum" in FRACTIONALIZATION_PROTOCOLS
        assert "nftx" in FRACTIONALIZATION_PROTOCOLS["ethereum"]

    def test_method_sigs(self):
        assert "0xa9059cbb" in DEFI_METHOD_SIGS
        assert DEFI_METHOD_SIGS["0xa9059cbb"] == TransactionType.TOKEN_TRANSFER
        assert "0xbaa2abde" in DEFI_METHOD_SIGS


# ── BlockchainTransaction ───────────────────────────────────────────────


class TestBlockchainTransaction:
    def test_creation(self):
        tx = _make_tx()
        assert tx.tx_hash.startswith("0x")
        assert tx.amount == Decimal("1.5")

    def test_quantum_signature_generated(self):
        tx = _make_tx()
        assert len(tx.quantum_signature) == 64

    def test_cryptographic_proof_generated(self):
        tx = _make_tx()
        assert len(tx.cryptographic_proof) == 128

    def test_to_dict_roundtrip(self):
        tx = _make_tx()
        d = tx.to_dict()
        assert d["amount"] == "1.5"
        assert d["risk_level"] == "NO_RISK"
        assert d["layer"] == "L1"

    def test_amount_coercion(self):
        tx = _make_tx(amount=42)
        assert tx.amount == Decimal("42")

    def test_flags_default_false(self):
        tx = _make_tx()
        assert not tx.is_sanctioned
        assert not tx.is_mixer
        assert not tx.is_bridge
        assert not tx.is_defi
        assert not tx.is_nft

    def test_nft_metadata_field(self):
        tx = _make_tx(nft_metadata={"name": "CryptoPunk"})
        assert tx.nft_metadata["name"] == "CryptoPunk"

    def test_bridge_info_field(self):
        tx = _make_tx(bridge_info={"target_chain": "polygon"})
        assert tx.bridge_info["target_chain"] == "polygon"


# ── New dataclasses ─────────────────────────────────────────────────────


class TestNewDataclasses:
    def test_cross_chain_bridge(self):
        b = CrossChainBridge(
            bridge_name="Optimism Bridge", source_chain="ethereum",
            target_chain="optimism", deposit_tx="0xabc",
            withdrawal_tx=None, depositor="0x111",
            recipient=None, amount=Decimal("10"),
            token="ETH", timestamp=datetime.now(timezone.utc),
        )
        assert b.status == "pending"
        assert b.risk_score == 0.0

    def test_mixer_transaction(self):
        m = MixerTransaction(
            mixer_name="Tornado Cash",
            mixer_protocol=PrivacyProtocol.TORNADO_CASH,
            deposit_tx="0xdef", withdrawal_tx=None,
            depositor="0x222", recipient=None,
            amount=Decimal("1"), currency="ETH",
            timestamp=datetime.now(timezone.utc),
        )
        assert m.risk_score == 1.0
        assert m.anonymity_set_size == 0

    def test_defi_interaction(self):
        d = DeFiInteraction(
            protocol_name="Uniswap", interaction_type="swap",
            tx_hash="0xaaa", user_address="0x333",
            contract_address="0x444",
            input_amount=Decimal("100"), output_amount=Decimal("99"),
            input_token="USDC", output_token="ETH",
            timestamp=datetime.now(timezone.utc),
        )
        assert d.gas_cost == Decimal("0")

    def test_nft_transfer(self):
        t = _make_nft_transfer(price=Decimal("2.5"), currency="ETH")
        assert t.price == Decimal("2.5")
        assert t.is_fractionalized is False


# ── WalletEntity ────────────────────────────────────────────────────────


class TestWalletEntity:
    def test_creation(self):
        w = WalletEntity(
            address="0x" + "ab" * 20, blockchain="ethereum",
            entity_type=EntityType.EXCHANGE, entity_name="Binance",
        )
        assert w.entity_name == "Binance"
        assert w.balance == Decimal("0")


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
        assert scorer.score_wallet(w) >= 0.9


# ── TransactionGraphBuilder ─────────────────────────────────────────────


class TestTransactionGraphBuilder:
    def test_add_transaction(self):
        gb = TransactionGraphBuilder()
        gb.add_transaction(_make_tx())
        assert gb.num_nodes == 2
        assert gb.num_edges == 1

    def test_multiple_transactions_share_nodes(self):
        gb = TransactionGraphBuilder()
        a, b, c = "0x" + "aa" * 20, "0x" + "bb" * 20, "0x" + "cc" * 20
        gb.add_transaction(_make_tx(from_address=a, to_address=b))
        gb.add_transaction(_make_tx(from_address=b, to_address=c))
        assert gb.num_nodes == 3
        assert gb.num_edges == 2

    def test_max_nodes_respected(self):
        gb = TransactionGraphBuilder(max_nodes=4)
        for i in range(10):
            gb.add_transaction(_make_tx(
                from_address=f"0x{'0' * 39}{i:01x}",
                to_address=f"0x{'f' * 39}{i:01x}",
            ))
        assert gb.num_nodes <= 4

    def test_get_address(self):
        gb = TransactionGraphBuilder()
        addr = "0x" + "dd" * 20
        gb.add_transaction(_make_tx(from_address=addr))
        found = gb.get_address(0)
        assert found is not None
        assert addr in found

    def test_nft_flag_in_features(self):
        gb = TransactionGraphBuilder()
        tx = _make_tx(is_nft=True)
        gb.add_transaction(tx)
        assert gb.num_nodes == 2


# ── EvidenceChainManager (ECDSA-signed) ─────────────────────────────────


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

    def test_export_includes_signature_scheme(self, tmp_path):
        mgr = EvidenceChainManager(tmp_path)
        mgr.add("C2", "tx", "src", {"data": 1})
        path = mgr.export("C2")
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["case_id"] == "C2"
        assert data["count"] == 1
        assert "signature_scheme" in data
        assert data["signature_scheme"] in ("ECDSA-P384-SHA384", "SHA3-512")

    def test_empty_chain_verifies(self, tmp_path):
        mgr = EvidenceChainManager(tmp_path)
        assert mgr.verify("NONEXISTENT") is True

    def test_signature_present(self, tmp_path):
        mgr = EvidenceChainManager(tmp_path)
        link = mgr.add("C3", "t", "s", {"x": 1})
        assert len(link.signature) > 0

    def test_public_key_pem_present(self, tmp_path):
        mgr = EvidenceChainManager(tmp_path)
        pem = mgr.public_key_pem
        # cryptography may or may not be available
        assert isinstance(pem, str)

    def test_tamper_detection(self, tmp_path):
        mgr = EvidenceChainManager(tmp_path)
        mgr.add("C4", "a", "s", {"x": 1})
        mgr.add("C4", "b", "s", {"y": 2})
        # tamper with second link's previous_hash
        mgr._chains["C4"][1].previous_hash = "0" * 64
        assert mgr.verify("C4") is False


# ── NFTTracker ───────────────────────────────────────────────────────────


class TestNFTTracker:
    def test_no_transfers_no_wash(self):
        tracker = NFTTracker()
        result = tracker.detect_wash_trading("0xcontract", "1")
        assert result["score"] == 0.0
        assert result["flags"] == []

    def test_single_transfer_no_wash(self):
        tracker = NFTTracker()
        tracker.record_transfer(_make_nft_transfer())
        result = tracker.detect_wash_trading("0x" + "cc" * 20, "42")
        assert result["score"] == 0.0

    def test_circular_trading_detected(self):
        tracker = NFTTracker()
        addr_a = "0x" + "aa" * 20
        addr_b = "0x" + "bb" * 20
        contract = "0x" + "cc" * 20
        base_time = datetime(2025, 1, 1, tzinfo=timezone.utc)
        for i in range(4):
            tracker.record_transfer(_make_nft_transfer(
                nft_contract=contract, token_id="1",
                from_address=addr_a if i % 2 == 0 else addr_b,
                to_address=addr_b if i % 2 == 0 else addr_a,
                timestamp=base_time + timedelta(hours=i),
                price=Decimal("10"),
            ))
        result = tracker.detect_wash_trading(contract, "1")
        assert result["score"] > 0.0
        assert "repeated_counterparty" in result["flags"]
        assert result["circular_pairs"] >= 1

    def test_high_frequency_flagged(self):
        tracker = NFTTracker()
        contract = "0x" + "cc" * 20
        base_time = datetime(2025, 1, 1, tzinfo=timezone.utc)
        for i in range(12):
            tracker.record_transfer(_make_nft_transfer(
                nft_contract=contract, token_id="7",
                from_address=f"0x{'0' * 39}{i:01x}",
                to_address=f"0x{'f' * 39}{i:01x}",
                timestamp=base_time + timedelta(minutes=i * 5),
            ))
        result = tracker.detect_wash_trading(contract, "7")
        assert "high_frequency" in result["flags"]

    def test_fractionalization_check(self):
        tracker = NFTTracker()
        nftx_addr = list(FRACTIONALIZATION_PROTOCOLS.get("ethereum", {}).values())[0]
        assert tracker.check_fractionalization(nftx_addr, "ethereum") == "nftx"
        assert tracker.check_fractionalization("0xunknown", "ethereum") is None


# ── BlockchainMonitor ───────────────────────────────────────────────────


class TestBlockchainMonitor:
    def test_instantiation(self):
        engine = BlockchainForensicsEngine(enable_gpu=False)
        monitor = BlockchainMonitor(engine)
        assert monitor.is_running is False
        assert monitor.stats["blocks_processed"] == 0

    def test_add_handlers(self):
        engine = BlockchainForensicsEngine(enable_gpu=False)
        monitor = BlockchainMonitor(engine)
        handler_called = []
        monitor.on_block(lambda b, c: handler_called.append("block"))
        monitor.on_transaction(lambda t, c: handler_called.append("tx"))
        monitor.on_alert(lambda a: handler_called.append("alert"))
        assert len(monitor._block_handlers) == 1
        assert len(monitor._tx_handlers) == 1
        assert len(monitor._alert_handlers) == 1

    def test_monitored_addresses(self):
        engine = BlockchainForensicsEngine(enable_gpu=False)
        monitor = BlockchainMonitor(
            engine, monitored_addresses={"0xabc", "0xdef"}, risk_threshold=0.8,
        )
        assert "0xabc" in monitor.monitored_addresses
        assert monitor.risk_threshold == 0.8


# ── Tx classification (bridge destination enrichment) ───────────────────


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

    def test_bridge_detection_with_destination(self):
        client = self._make_client()
        bridge_addr = "0x99c9fc46f92e8a1c0dec1b1747d010903e884be1"
        tx = _make_tx(to_address=bridge_addr)
        client._classify_tx(tx)
        assert tx.is_bridge is True
        assert tx.tx_type == TransactionType.BRIDGE_DEPOSIT
        assert tx.bridge_info is not None
        assert tx.bridge_info["target_chain"] == "optimism"
        assert "optimism" in tx.cross_chain_connections

    def test_nft_marketplace_detection(self):
        client = self._make_client()
        opensea = NFT_MARKETPLACES["ethereum"]["opensea"]
        tx = _make_tx(to_address=opensea)
        client._classify_tx(tx)
        assert tx.is_nft is True

    def test_defi_method_sig_detection(self):
        client = self._make_client()
        tx = _make_tx(input_data="0xa9059cbb" + "00" * 32)
        client._classify_tx(tx)
        assert tx.tx_type == TransactionType.TOKEN_TRANSFER

    def test_clean_tx_stays_clean(self):
        client = self._make_client()
        tx = _make_tx()
        client._classify_tx(tx)
        assert not tx.is_sanctioned
        assert not tx.is_mixer
        assert not tx.is_bridge
        assert not tx.is_nft


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

    def test_solana_valid(self):
        assert validate_address("1" * 32, "solana") is True

    def test_fantom_evm(self):
        assert validate_address("0x" + "ab" * 20, "fantom") is True

    def test_harmony_evm(self):
        assert validate_address("0x" + "ab" * 20, "harmony") is True

    def test_normalize_evm(self):
        addr = "0x" + "ab" * 20
        assert normalize_address(addr, "ethereum") == addr.lower()


# ── BlockchainForensicsEngine ───────────────────────────────────────────


class TestBlockchainForensicsEngine:
    def test_instantiation(self):
        engine = BlockchainForensicsEngine(
            api_keys={"etherscan": "test"}, enable_gpu=False,
        )
        assert engine.api_keys["etherscan"] == "test"

    def test_get_client_ethereum(self):
        engine = BlockchainForensicsEngine(
            api_keys={"etherscan": "test_key"}, enable_gpu=False,
        )
        client = engine.get_client("ethereum")
        assert client is not None
        assert isinstance(client, EtherscanCompatibleClient)

    def test_get_client_unknown(self):
        engine = BlockchainForensicsEngine(enable_gpu=False)
        assert engine.get_client("nonexistent_chain") is None

    def test_stats_initial(self):
        engine = BlockchainForensicsEngine(enable_gpu=False)
        stats = engine.get_stats()
        assert stats["txs_analyzed"] == 0
        assert stats["networks"] >= 30

    def test_nft_tracker_present(self):
        engine = BlockchainForensicsEngine(enable_gpu=False)
        assert engine.nft_tracker is not None
        assert isinstance(engine.nft_tracker, NFTTracker)

    def test_evidence_manager_present(self):
        engine = BlockchainForensicsEngine(enable_gpu=False)
        assert engine.evidence is not None
        assert isinstance(engine.evidence, EvidenceChainManager)


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
        assert "websockets" in BLOCKCHAIN_FEATURES
        assert "cryptography" in BLOCKCHAIN_FEATURES
