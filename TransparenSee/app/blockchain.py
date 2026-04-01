import os
from web3 import Web3
from web3.middleware.geth_poa import geth_poa_middleware
from dotenv import load_dotenv

load_dotenv()

# Connect to Sepolia
SEPOLIA_URL = os.getenv("SEPOLIA_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")

contract_abi = [
    {
        "inputs": [
            {"internalType": "string", "name": "org", "type": "string"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"}
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
                    {"internalType": "string", "name": "organization", "type": "string"},
                    {"internalType": "uint256", "name": "amount", "type": "uint256"},
                    {"internalType": "address", "name": "sender", "type": "address"},
                    {"internalType": "uint256", "name": "timestamp", "type": "uint256"}
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
            {"internalType": "string", "name": "organization", "type": "string"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
            {"internalType": "address", "name": "sender", "type": "address"},
            {"internalType": "uint256", "name": "timestamp", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]  # paste your ABI JSON here



# Example: Add a transaction (write to blockchain)

