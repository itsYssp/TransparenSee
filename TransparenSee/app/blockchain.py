import os
import hashlib
import json
from decimal import Decimal
from web3 import Web3
from web3.middleware import geth_poa_middleware
from dotenv import load_dotenv
from .blockchain_utils import build_report_snapshot, generate_report_hash

load_dotenv(override=True)

SEPOLIA_URL      = os.getenv("SEPOLIA_URL")
PRIVATE_KEY      = os.getenv("PRIVATE_KEY")
WALLET_ADDRESS   = os.getenv("WALLET_ADDRESS")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")

w3 = Web3(Web3.HTTPProvider(SEPOLIA_URL))
w3.middleware_onion.inject(geth_poa_middleware, layer=0) 

contract_abi = [
    {
        "inputs": [
            {"internalType": "string", "name": "org",        "type": "string"},
            {"internalType": "uint256", "name": "amount",    "type": "uint256"},
            {"internalType": "string", "name": "reportHash", "type": "string"},
            {"internalType": "string", "name": "title",      "type": "string"}
        ],
        "name": "addTransaction",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getTransactions",
        "outputs": [
            {
                "components": [
                    {"internalType": "string",  "name": "organization", "type": "string"},
                    {"internalType": "uint256", "name": "amount",       "type": "uint256"},
                    {"internalType": "address", "name": "sender",       "type": "address"},
                    {"internalType": "uint256", "name": "timestamp",    "type": "uint256"},
                    {"internalType": "string",  "name": "reportHash",   "type": "string"},
                    {"internalType": "string",  "name": "title",        "type": "string"}
                ],
                "internalType": "struct Transparency.Transaction[]",
                "name": "",
                "type": "tuple[]"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "name": "transactions",
        "outputs": [
            {"internalType": "string",  "name": "organization", "type": "string"},
            {"internalType": "uint256", "name": "amount",       "type": "uint256"},
            {"internalType": "address", "name": "sender",       "type": "address"},
            {"internalType": "uint256", "name": "timestamp",    "type": "uint256"},
            {"internalType": "string",  "name": "reportHash",   "type": "string"},
            {"internalType": "string",  "name": "title",        "type": "string"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getTransactionCount",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "internalType": "string",  "name": "organization", "type": "string"},
            {"indexed": False, "internalType": "uint256", "name": "amount",       "type": "uint256"},
            {"indexed": True,  "internalType": "address", "name": "sender",       "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "timestamp",    "type": "uint256"},
            {"indexed": False, "internalType": "string",  "name": "reportHash",   "type": "string"},
            {"indexed": False, "internalType": "string",  "name": "title",        "type": "string"}
        ],
        "name": "TransactionAdded",
        "type": "event"
    }
]

contract = w3.eth.contract(
    address=Web3.to_checksum_address(CONTRACT_ADDRESS),
    abi=contract_abi
)


def record_financial_report_on_blockchain(financial_report):
    if not w3.is_connected():
        raise ConnectionError("No connection to Sepolia")


    snapshot = build_report_snapshot(financial_report)
    report_hash = generate_report_hash(snapshot)

    amount_in_cents = int(financial_report.total_amount * Decimal("100"))

    nonce = w3.eth.get_transaction_count(WALLET_ADDRESS)

    txn = contract.functions.addTransaction(
        financial_report.organization.name,
        amount_in_cents,
        report_hash,
        financial_report.title
    ).build_transaction({
        "from": WALLET_ADDRESS,
        "nonce": nonce,
        "gas": 300000,
        "gasPrice": w3.to_wei("2", "gwei"),
        "chainId": 11155111,
    })

    signed_txn = w3.eth.account.sign_transaction(txn, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

    if receipt.status != 1:
        raise RuntimeError("Blockchain transaction failed")

    return {
        "tx_hash": tx_hash.hex(),
        "block_number": receipt.blockNumber,
        "report_hash": report_hash,
    }


def get_all_transactions() -> list:
    if not w3.is_connected():
        raise ConnectionError("Cannot connect to Sepolia. Check SEPOLIA_URL in .env")
    return contract.functions.getTransactions().call()


def get_transaction_count() -> int:
    
    if not w3.is_connected():
        raise ConnectionError("Cannot connect to Sepolia. Check SEPOLIA_URL in .env")
    return contract.functions.getTransactionCount().call()


def verify_report_hash(financial_report):
    from .blockchain_utils import build_report_snapshot, generate_report_hash

    snapshot = build_report_snapshot(financial_report)
    current_hash = generate_report_hash(snapshot)

    return current_hash == financial_report.blockchain_hash