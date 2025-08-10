# main.py - The Final Version (Fixes SyntaxError and All Previous Bugs)
# ==============================================================================

# 1. --- IMPORTS ---
from flask import Flask, request, jsonify, render_template
import requests
from thor_devkit import cry, transaction
import os
from dotenv import load_dotenv
import time

# 2. --- INITIALIZATION ---
load_dotenv()
app = Flask(__name__)

# 3. --- CONFIGURATION ---
NODE_URL = os.getenv("NODE_URL")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
MNEMONIC_PHRASE = os.getenv("PRIVATE_KEY")

# 4. --- DERIVE PRIVATE KEY (with all corrections) ---
PRIVATE_KEY_BYTES = None

if not MNEMONIC_PHRASE:
    print("FATAL ERROR: 'PRIVATE_KEY' not found in .env file.")
else:
    # This is the corrected try/except block
    try:
        PRIVATE_KEY_BYTES = cry.mnemonic.derive_private_key(MNEMONIC_PHRASE.split(' '))
        # This is the corrected function call
        SENDER_ADDRESS = cry.public_key_to_address(cry.private_key_to_public_key(PRIVATE_KEY_BYTES))
        print(f"SUCCESS: Wallet address derived successfully: {SENDER_ADDRESS}")
    except Exception as e:
        print(f"FATAL ERROR: Could not derive private key from the mnemonic phrase.")
        print(f"           Underlying Error: {e}")
        PRIVATE_KEY_BYTES = None

# 5. --- REAL VECHAIN TRANSACTION FUNCTION ---
def send_vechain_transaction(data_to_store_on_chain: str):
    if not PRIVATE_KEY_BYTES:
        return None, "Private key is not configured correctly. Check terminal for FATAL ERROR messages on startup."
    
    try:
        response = requests.get(f"{NODE_URL}/blocks/best")
        response.raise_for_status()
        latest_block = response.json()
        chain_tag = int(latest_block['id'][2:4], 16)
        block_ref = latest_block['id'][:18]

        encoded_data = data_to_store_on_chain.encode('utf-8').hex()
        clauses = [{'to': CONTRACT_ADDRESS, 'value': 0, 'data': f"0x6057361d{encoded_data}"}]

        tx_body = {
            'chainTag': chain_tag, 'blockRef': block_ref, 'expiration': 32,
            'clauses': clauses, 'gasPriceCoef': 128, 'gas': 100000,
            'dependsOn': None, 'nonce': int(time.time() * 1000)
        }

        tx = transaction.Transaction(tx_body)
        tx.sign(PRIVATE_KEY_BYTES)
        raw_tx = '0x' + tx.encode().hex()
        send_response = requests.post(f"{NODE_URL}/transactions", json={'raw': raw_tx})
        send_response.raise_for_status()
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



