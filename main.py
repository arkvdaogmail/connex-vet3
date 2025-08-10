# main.py - FINAL VERSION. Corrects the 'chain tag mismatch' error.
# ==============================================================================

# 1. --- IMPORTS ---
from flask import Flask, request, jsonify, render_template
import requests
import os
from dotenv import load_dotenv
import secrets
from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes
from thor_devkit.transaction import Transaction
from thor_devkit.cry import secp256k1

# 2. --- INITIALIZATION ---
load_dotenv()
app = Flask(__name__)

# 3. --- CONFIGURATION ---
NODE_URL = os.getenv("NODE_URL")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
MNEMONIC_PHRASE = os.getenv("PRIVATE_KEY")

# 4. --- DERIVE PRIVATE KEY ---
PRIVATE_KEY_BYTES = None
SENDER_ADDRESS = None

if not MNEMONIC_PHRASE:
    print("FATAL ERROR: 'PRIVATE_KEY' not found in .env file.")
else:
    try:
        seed_bytes = Bip39SeedGenerator(MNEMONIC_PHRASE).Generate()
        bip44_mst = Bip44.FromSeed(seed_bytes, Bip44Coins.VECHAIN)
        bip44_acc = bip44_mst.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT)
        bip44_addr = bip44_acc.AddressIndex(0)
        PRIVATE_KEY_BYTES = bip44_addr.PrivateKey().Raw().ToBytes()
        SENDER_ADDRESS = bip44_addr.Address()
        print(f"SUCCESS: Wallet address derived successfully: {SENDER_ADDRESS}")
    except Exception as e:
        print(f"FATAL ERROR: Could not derive private key. Check the 12-word phrase in .env file.")
        print(f"           Underlying Error: {e}")

# 5. --- REAL VECHAIN TRANSACTION FUNCTION (Corrected chainTag) ---
def send_vechain_transaction(data_to_store_on_chain: str):
    if not PRIVATE_KEY_BYTES:
        return None, "Private key is not configured correctly. Check terminal for FATAL ERROR messages on startup."
    
    try:
        response = requests.get(f"{NODE_URL}/blocks/best")
        response.raise_for_status()
        latest_block = response.json()
        
        # THIS IS THE FINAL CORRECTION. The chainTag is a specific field in the block header.
        chain_tag = latest_block['chainTag']
        block_ref = latest_block['id'][0:18]

        hex_data = data_to_store_on_chain.replace('0x', '')
        data_payload = f"0x6057361d{hex_data}"

        clauses = [{
            'to': CONTRACT_ADDRESS,
            'value': "0",
            'data': data_payload
        }]

        tx_body = {
            'chainTag': chain_tag,
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

# 6. --- FLASK ROUTES ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/notarize', methods=['POST'])
def notarize_document():
    data = request.json
    file_hash = data.get('content')
    if not file_hash:
        return jsonify({"status": "error", "message": "No file hash provided."}), 400
    
    transaction_id, error_message = send_vechain_transaction(file_hash)
    
    if transaction_id:
        return jsonify({"status": "success", "transaction_id": transaction_id})
    else:
        return jsonify({"status": "error", "message": f"Error: {error_message}"}), 500

# 7. --- RUN THE APP ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

