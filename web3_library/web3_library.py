import json
from web3 import Web3
import os

infura_url = os.environ["INFURA_URL"]
address = os.environ["ADDRESS"]
abi = os.environ["ABI"]
bytecode = os.environ["BYTECODE"]
private_key = os.environ["PRIVATE_KEY"]

w3 = Web3(Web3.HTTPProvider(infura_url))

# TODO: this address should be sent to the function or got from the database
def get_contract(address="0x9Db8B2e2bac516CE88b27cF6A3A7a53161AE3eBf"):
    pay_contract = w3.eth.contract(address=address, abi=abi)
    print(pay_contract)
    return pay_contract


def create_contract():
    pay_contract_to_deploy = w3.eth.contract(abi=abi, bytecode=bytecode)
    nonce = w3.eth.getTransactionCount(w3.eth.defaultAccount)
    transaction = pay_contract_to_deploy.constructor().buildTransaction({
        'gas': 70000,
        'gasPrice': w3.toWei('1', 'gwei'),
        'from': w3.eth.defaultAccount,
        'nonce': nonce
    })
    signed_txn = w3.eth.account.signTransaction(transaction, private_key=private_key)
    tx_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    pay_contract = w3.eth.contract(
        address=tx_receipt.contractAddress,
        abi=abi
    )
    # pay_contract.address for address of the contract
    return pay_contract


def add_node(contract, storage_address, payment_date):
    # add storage node
    nonce = w3.eth.getTransactionCount(w3.eth.defaultAccount)
    transaction = contract.addStorageNode(storage_address).buildTransaction({
        'gas': 70000,
        'gasPrice': w3.toWei('1', 'gwei'),
        'from': w3.eth.defaultAccount,
        'nonce': nonce
    })
    signed_txn = w3.eth.account.signTransaction(transaction, private_key=private_key)
    tx_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
    w3.eth.waitForTransactionReceipt(tx_hash)

    # add payment date for the storage node
    nonce = w3.eth.getTransactionCount(w3.eth.defaultAccount)
    transaction = contract.addPaymentDate(payment_date).buildTransaction({
        'gas': 70000,
        'gasPrice': w3.toWei('1', 'gwei'),
        'from': w3.eth.defaultAccount,
        'nonce': nonce
    })
    signed_txn = w3.eth.account.signTransaction(transaction, private_key=private_key)
    tx_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
    w3.eth.waitForTransactionReceipt(tx_hash)
    # pay_contract.address for address of the contract
    return True


def delete_node(contract, storage_address):
    # add storage node
    nonce = w3.eth.getTransactionCount(w3.eth.defaultAccount)
    transaction = contract.deletePaymentDate(storage_address).buildTransaction({
        'gas': 70000,
        'gasPrice': w3.toWei('1', 'gwei'),
        'from': w3.eth.defaultAccount,
        'nonce': nonce
    })
    signed_txn = w3.eth.account.signTransaction(transaction, private_key=private_key)
    tx_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
    w3.eth.waitForTransactionReceipt(tx_hash)

    # add payment date for the storage node
    nonce = w3.eth.getTransactionCount(w3.eth.defaultAccount)
    transaction = contract.deleteStorageNode(storage_address).buildTransaction({
        'gas': 70000,
        'gasPrice': w3.toWei('1', 'gwei'),
        'from': w3.eth.defaultAccount,
        'nonce': nonce
    })
    signed_txn = w3.eth.account.signTransaction(transaction, private_key=private_key)
    tx_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
    w3.eth.waitForTransactionReceipt(tx_hash)
    # pay_contract.address for address of the contract
    return True


def swap_nodes(contract, storage_address1, storage_address2, payment_date):
    nonce = w3.eth.getTransactionCount(w3.eth.defaultAccount)
    transaction = contract.swapStorageNode(storage_address1, storage_address2, payment_date).buildTransaction({
        'gas': 70000,
        'gasPrice': w3.toWei('1', 'gwei'),
        'from': w3.eth.defaultAccount,
        'nonce': nonce
    })
    signed_txn = w3.eth.account.signTransaction(transaction, private_key=private_key)
    tx_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
    w3.eth.waitForTransactionReceipt(tx_hash)

    return True


def get_storage_nodes(contract):
    return contract.functions.getStorageNodes().call()


def get_payment_dates(contract):
    return contract.functions.getPaymentDates().call()


def get_web_user(contract):
    return contract.functions.getwebUser().call()


def get_balance(contract):
    return contract.functions.getBalance().call()


def get_balance(contract):
    return contract.functions.getBalance().call()
