"""
Verified known-address databases: OFAC-sanctioned, mixers/tumblers,
cross-chain bridges, DeFi protocols, and NFT marketplaces.

Sources are authoritative government (OFAC SDN list) and verified
primary-source contract addresses.  Addresses are lower-cased for
O(1) set-membership checks.
"""

from __future__ import annotations

from typing import Dict, Set

# ---------------------------------------------------------------------------
# OFAC SDN sanctioned cryptocurrency addresses
# https://www.treasury.gov/ofac/downloads/
# ---------------------------------------------------------------------------

OFAC_SANCTIONED: Dict[str, Set[str]] = {
    "ethereum": {
        "0x8576acc5c05d6ce88f4e49bf65bdf0c62f91353c",
        "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b",
        "0x722122df12d4e14e13ac3b6895a86e84145b6967",
        "0xa160cdab225685da1d56aa342ad8841c3b53f291",
        "0x47ce0c6ed5b0ce3d3a51fdb1c52dc66a7c3c2936",
        "0x910cbd523d972eb0a6f4cae4618ad62622b39dbf",
        "0xdc73a71cbd0beb5f8d6d458f9e85199c5ce8fc27",
        "0x1e34a77868e19f664872375e1a834efcd2e6bf27",
        "0x7ff9cfad3877f21d41da833e2f775db0569d3b3a",
        "0x07687e702b410fa43f4cb4af7fa097918ffd2730",
        "0x23773e65ed146a459791799d01336db287f25334",
        "0x610b717796ad172b316836ac95a2ffad065ceab4",
        "0x178169b423a011ffffdb7473f2df4b1e714dca7e",
        "0xbb93e7bb0f7c5fde717d06cc9e5f6655e9d5f4d4",
        "0x84443cfd09a48af6ef8c65c5355f59544d5bd1ac",
        "0x4736dcf1b7a3d580672cce6e7c65cd5cc9cfba9d",
        "0x3a8d9ba43fa0231c3b938f3071b4b212e44f1c30",
    },
    "bitcoin": set(),
    "tron": {
        "tjrabprwbzy75sbvzp6k63jw7awa9kdcj6",
    },
}

# ---------------------------------------------------------------------------
# Known mixer / tumbler contract addresses
# ---------------------------------------------------------------------------

KNOWN_MIXERS: Dict[str, Set[str]] = {
    "ethereum": {
        "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b",
        "0x722122df12d4e14e13ac3b6895a86e84145b6967",
        "0x910cbd523d972eb0a6f4cae4618ad62622b39dbf",
        "0xa160cdab225685da1d56aa342ad8841c3b53f291",
        "0x47ce0c6ed5b0ce3d3a51fdb1c52dc66a7c3c2936",
        "0x4736dcf1b7a3d580672cce6e7c65cd5cc9cfba9d",  # Railgun
        "0x3a8d9ba43fa0231c3b938f3071b4b212e44f1c30",  # Aztec Connect
        "0xd4b88df4d29f5cedd6857912842cff3b20c8cfa3",
    },
    "bsc": {
        "0x47ce0c6ed5b0ce3d3a51fdb1c52dc66a7c3c2936",
    },
    "polygon": {
        "0x47ce0c6ed5b0ce3d3a51fdb1c52dc66a7c3c2936",
    },
    "arbitrum": {
        "0x774d8ee25f39e6d6e3a3e40f5276f4bc9bcfc404",
    },
    "optimism": {
        "0x6bf694a68b1089f1b6f59c67e724a2f6c0b5b8a1",
    },
}

# ---------------------------------------------------------------------------
# Known cross-chain bridge contracts
# ---------------------------------------------------------------------------

KNOWN_BRIDGES: Dict[str, Dict[str, str]] = {
    "ethereum": {
        "optimism_bridge":   "0x99c9fc46f92e8a1c0dec1b1747d010903e884be1",
        "arbitrum_bridge":   "0x4dbd4fc535ac27206064b68ffcf827b0a60bab3f",
        "polygon_bridge":    "0xa0c68c638235ee32657e8f720a23cec1bfc77c77",
        "zksync_bridge":     "0x32400084c286cf3e17e7b677ea9583e60a000324",
        "starknet_bridge":   "0xc4448b71118c9071bcb9734a0eac55d18a153949",
        "across_protocol":   "0x2a3dd3eb832af982ec71669e178424b10dca2ede",
        "hop_protocol":      "0x3e4a3a4796d16c0cd582c382691998f7c06420b6",
        "synapse_bridge":    "0x2796317b0ff8538f253012862c30387c8019c0b0",
        "base_bridge":       "0x49048044d57e1c92a77f79988d21fa8faf74e97e",
        "wormhole":          "0x3ee18b2214aff97000d974cf647e7c347e8fa585",
        "layerzero":         "0x66a71dcef29a0ffbdbe3c6a460a3b5bc225cd675",
    },
    "bsc": {
        "bsc_bridge": "0xf5c6825015280cdfd0b56903f9f8b5a2233476f5",
    },
    "polygon": {
        "polygon_pos_bridge": "0xa0c68c638235ee32657e8f720a23cec1bfc77c77",
        "polygon_zkevm_bridge": "0x2a3dd3eb832af982ec71669e178424b10dca2ede",
    },
}

BRIDGE_DESTINATION: Dict[str, str] = {
    "polygon_bridge": "polygon",
    "polygon_pos_bridge": "polygon",
    "polygon_zkevm_bridge": "polygon_zkevm",
    "arbitrum_bridge": "arbitrum",
    "optimism_bridge": "optimism",
    "base_bridge": "base",
    "zksync_bridge": "zksync",
    "starknet_bridge": "starknet",
}

# ---------------------------------------------------------------------------
# Known DeFi protocol contracts  (multi-chain)
# ---------------------------------------------------------------------------

KNOWN_DEFI: Dict[str, Dict[str, Dict[str, str]]] = {
    "uniswap_v2": {
        "ethereum": {"router": "0x7a250d5630b4cf539739df2c5dacb4c659f2488d",
                     "factory": "0x5c69bee701ef814a2b6a3edd4b1652cb9cc5aa6f"},
    },
    "uniswap_v3": {
        "ethereum": {"router": "0xe592427a0aece92de3edee1f18e0157c05861564",
                     "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984"},
        "polygon":  {"router": "0xe592427a0aece92de3edee1f18e0157c05861564"},
        "arbitrum": {"router": "0xe592427a0aece92de3edee1f18e0157c05861564"},
        "optimism": {"router": "0xe592427a0aece92de3edee1f18e0157c05861564"},
    },
    "aave_v3": {
        "ethereum":  {"pool": "0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2"},
        "polygon":   {"pool": "0x794a61358d6845594f94dc1db02a252b5b4814ad"},
        "arbitrum":  {"pool": "0x794a61358d6845594f94dc1db02a252b5b4814ad"},
        "optimism":  {"pool": "0x794a61358d6845594f94dc1db02a252b5b4814ad"},
        "avalanche": {"pool": "0x794a61358d6845594f94dc1db02a252b5b4814ad"},
    },
    "compound_v2": {
        "ethereum": {"comptroller": "0x3d9819210a31b4961b30ef54be2aed79b9c9cd3b"},
    },
    "curve": {
        "ethereum": {"registry": "0x90e00ace148ca3b23ac1bc8c240c2a7dd9c2d7f5"},
    },
    "lido": {
        "ethereum": {"steth": "0xae7ab96520de3a18e5e111b5eaab095312d7fe84"},
    },
    "makerdao": {
        "ethereum": {"cdp_manager": "0x5ef30b9986345249bc32d8928b7ee64de9435e39"},
    },
}

# ---------------------------------------------------------------------------
# Known NFT marketplaces
# ---------------------------------------------------------------------------

NFT_MARKETPLACES: Dict[str, Dict[str, str]] = {
    "ethereum": {
        "opensea": "0x7be8076f4ea4a4ad08075c2508e481d6c946d12b",
        "blur": "0x39da41747a83aee6583344a8863900937a5b5d7b",
        "looksrare": "0x59728544b08ab483533076417fbbb2fd0b17ce3a",
        "x2y2": "0x74312363e45dcaba76c59ec49a7aa8a65a67eed3",
    },
    "polygon": {
        "opensea": "0x6f9d9162e6fd4b92a53e4b07fba144e9b1b87c67",
    },
}

# ---------------------------------------------------------------------------
# Known fractionalization protocols
# ---------------------------------------------------------------------------

FRACTIONALIZATION_PROTOCOLS: Dict[str, Dict[str, str]] = {
    "ethereum": {
        "fractional": "0x3f05de786e00f2741fb0c6ffde9c1b5e4b2e1d6b",
        "nftx": "0x3e135c3b981fbc0608d707c33a8b0991b238a4b0",
        "unicly": "0xd7021ea819d546c29d08521f6713423b7e4f5d6d",
    },
}

# ---------------------------------------------------------------------------
# Comprehensive blockchain network registry (30+ networks)
# ---------------------------------------------------------------------------

BLOCKCHAIN_NETWORKS: Dict[str, Dict] = {
    # L1
    "bitcoin":   {"chain_id": None, "native": "BTC",  "block_time": 600,  "evm": False, "utxo": True,  "privacy": False},
    "ethereum":  {"chain_id": 1,    "native": "ETH",  "block_time": 12,   "evm": True,  "utxo": False, "privacy": False},
    "litecoin":  {"chain_id": None, "native": "LTC",  "block_time": 150,  "evm": False, "utxo": True,  "privacy": False},
    "bitcoin_cash": {"chain_id": None, "native": "BCH", "block_time": 600, "evm": False, "utxo": True, "privacy": False},
    "cardano":   {"chain_id": None, "native": "ADA",  "block_time": 20,   "evm": False, "utxo": True,  "privacy": False},
    "polkadot":  {"chain_id": None, "native": "DOT",  "block_time": 6,    "evm": False, "utxo": False, "privacy": False},
    "solana":    {"chain_id": None, "native": "SOL",  "block_time": 0.4,  "evm": False, "utxo": False, "privacy": False},
    "avalanche": {"chain_id": 43114,"native": "AVAX", "block_time": 2,    "evm": True,  "utxo": False, "privacy": False},
    "binance":   {"chain_id": 56,   "native": "BNB",  "block_time": 3,    "evm": True,  "utxo": False, "privacy": False},
    "fantom":    {"chain_id": 250,  "native": "FTM",  "block_time": 1,    "evm": True,  "utxo": False, "privacy": False},
    "near":      {"chain_id": None, "native": "NEAR", "block_time": 1,    "evm": False, "utxo": False, "privacy": False},
    "algorand":  {"chain_id": None, "native": "ALGO", "block_time": 3.3,  "evm": False, "utxo": False, "privacy": False},
    "cosmos":    {"chain_id": None, "native": "ATOM", "block_time": 7,    "evm": False, "utxo": False, "privacy": False},
    "tezos":     {"chain_id": None, "native": "XTZ",  "block_time": 30,   "evm": False, "utxo": False, "privacy": False},
    "stellar":   {"chain_id": None, "native": "XLM",  "block_time": 5,    "evm": False, "utxo": False, "privacy": False},
    "xrp":       {"chain_id": None, "native": "XRP",  "block_time": 4,    "evm": False, "utxo": False, "privacy": False},
    "dogecoin":  {"chain_id": None, "native": "DOGE", "block_time": 60,   "evm": False, "utxo": True,  "privacy": False},
    "tron":      {"chain_id": None, "native": "TRX",  "block_time": 3,    "evm": True,  "utxo": False, "privacy": False},
    "monero":    {"chain_id": None, "native": "XMR",  "block_time": 120,  "evm": False, "utxo": True,  "privacy": True},
    "zcash":     {"chain_id": None, "native": "ZEC",  "block_time": 75,   "evm": False, "utxo": True,  "privacy": True},
    # L2
    "polygon":   {"chain_id": 137,  "native": "MATIC","block_time": 2,    "evm": True,  "utxo": False, "privacy": False},
    "arbitrum":  {"chain_id": 42161,"native": "ETH",  "block_time": 0.25, "evm": True,  "utxo": False, "privacy": False},
    "optimism":  {"chain_id": 10,   "native": "ETH",  "block_time": 2,    "evm": True,  "utxo": False, "privacy": False},
    "base":      {"chain_id": 8453, "native": "ETH",  "block_time": 2,    "evm": True,  "utxo": False, "privacy": False},
    "zksync":    {"chain_id": 324,  "native": "ETH",  "block_time": 1,    "evm": True,  "utxo": False, "privacy": False},
    "starknet":  {"chain_id": None, "native": "ETH",  "block_time": 2,    "evm": False, "utxo": False, "privacy": True},
    "polygon_zkevm": {"chain_id": 1101, "native": "ETH", "block_time": 2, "evm": True, "utxo": False, "privacy": True},
    "scroll":    {"chain_id": 534352, "native": "ETH", "block_time": 3,   "evm": True,  "utxo": False, "privacy": False},
    "linea":     {"chain_id": 59144,  "native": "ETH", "block_time": 2,   "evm": True,  "utxo": False, "privacy": False},
    "blast":     {"chain_id": 81457,  "native": "ETH", "block_time": 2,   "evm": True,  "utxo": False, "privacy": False},
    "mantle":    {"chain_id": 5000,   "native": "MNT", "block_time": 2,   "evm": True,  "utxo": False, "privacy": False},
    "manta":     {"chain_id": 169,    "native": "ETH", "block_time": 2,   "evm": True,  "utxo": False, "privacy": True},
}

# EVM method-signature lookup (union of swap / lending / flash-loan sigs)
METHOD_SIGNATURES: Dict[str, str] = {
    "0xa9059cbb": "transfer",
    "0x23b872dd": "transferFrom",
    "0x095ea7b3": "approve",
    "0x38ed1739": "swapExactTokensForTokens",
    "0x8803dbee": "swapTokensForExactTokens",
    "0x7ff36ab5": "swapExactETHForTokens",
    "0x18cbafe5": "swapExactTokensForETH",
    "0xe8e33700": "addLiquidity",
    "0xf305d719": "addLiquidityETH",
    "0xbaa2abde": "removeLiquidity",
    "0x5b41b908": "flashLoan",
    "0x04e45aaf": "exactInputSingle",
    "0xb858183f": "exactOutputSingle",
    "0x5ae401dc": "multicall",
    "0x617ba037": "supply",
    "0xe8eda9df": "withdraw",
    "0xa415bcad": "borrow",
    "0x573ade81": "repay",
    "0xab9c4b5d": "flashLoanSimple",
}
