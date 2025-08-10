MAX_STRING_LENGTH = 18

def send_vechain_transaction(data_to_store_on_chain: str):
    if not PRIVATE_KEY_BYTES:
        return None, "Private key is not configured correctly. Check terminal for FATAL ERROR messages on startup."
    try:
        # Truncate or validate the input string
        if len(data_to_store_on_chain) > MAX_STRING_LENGTH:
            return None, f"Input string exceeds max allowed length of {MAX_STRING_LENGTH}."

        response = requests.get(f"{NODE_URL}/blocks/best")
        response.raise_for_status()
        latest_block = response.json()
        block_ref = latest_block['id'][2:18]

        hex_data = data_to_store_on_chain.replace('0x', '')
        data_payload = f"0x6057361d{hex_data}"

        clauses = [{
            'to': CONTRACT_ADDRESS,
            'value': 0,
            'data': data_payload
        }]

        tx_body = {
            'chainTag': 0x27,
            'blockRef': block_ref,
            'expiration': 32,
            'clauses': clauses,
            'gasPriceCoef': 0,
            'gas': 100000,
            'dependsOn': None,
            'nonce': secrets.randbits(64)
        }

        tx = Transaction(tx_body)
        signing_hash = tx.get_signing_hash()
        signature = secp256k1.sign(signing_hash, PRIVATE_KEY_BYTES)
        tx.set_signature(signature)
        raw_tx = '0x' + tx.encode().hex()

        send_response = requests.post(f"{NODE_URL}/transactions", json={'raw': raw_tx})
        if send_response.status_code != 200:
            raise Exception(f"API Error {send_response.status_code}: {send_response.text}")

        tx_id = send_response.json()['id']
        print(f"SUCCESS: Transaction sent! ID: {tx_id}")
        return tx_id, None
    except Exception as e:
        print(f"ERROR sending transaction: {e}")
        return None, str(e)




