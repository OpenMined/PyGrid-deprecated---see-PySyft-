from ethereum import utils
from ethereum import transactions
import os
import rlp


def create_wallet():
    # TODO is urandom secure??? maybe need to use something else
    private_key = utils.sha3(os.urandom(4096))

    # TODO encrypt and store these keys somewhere for user?!?!
    raw_address = utils.privtoaddr(private_key)
    account_address = utils.checksum_encode(raw_address)

    print("DO NOT LOSS PRIVATE KEY OR PUBLIC KEY NO WAY TO RECOVER")
    print("PRIVATE KEY", private_key.hex(), "PUBLIC KEY", account_address)

    return private_key, account_address


def sign_transactions(abi, priv_key, to):
    nonce = 0
    gasprice = 18000000000
    startgas = 1500000

    # [nonce, gasprice, startgas, to, value, data, v, r, s]
    tx = transactions.Transaction(nonce, gasprice, startgas, to, 1, "")
    signed_tx = tx.sign(priv_key)

    return rlp.encode(signed_tx).hex()
