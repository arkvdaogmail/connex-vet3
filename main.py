from flask import Flask, request, jsonify, render_template, send_from_directory
import requests
import os
import secrets
from dotenv import load_dotenv
from thor_devkit.transaction import Transaction
from thor_devkit.cry import secp256k1
from flask_cors import CORS  # Fixes CORS issues

# Load environment variables
load_dotenv()
NODE_URL = os.getenv("NODE_URL")  # e.g. "https://testnet.vechain.org"
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
PRIVATE_KEY_HEX = os.getenv("PRIVATE_KEY")
MAX_STRING_LENGTH = 18

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

def get_block_ref():
    # Fetch the latest block to get blockRef (first 8 bytes of block id)
    resp = requests.get(f"{NODE_URL}/blocks/best")
    resp.raise_for_status()
    block_id = resp.json()['id']
    return block_id[2:18]  # Remove '0x' and take first 16 hex chars

def send_vechain_transaction(data_to_store_on_chain: str):
    if not PRIVATE_KEY_HEX:
        return None, "Private key not configured."
    if len(data_to_store_on_chain) > MAX_STRING_LENGTH:
        return None, f"Input exceeds {MAX_STRING_LENGTH} chars."

    try:
        block_ref = get_block_ref()
        clause = {
            'to': CONTRACT_ADDRESS,
            'value': 0,
            'data': data_to_store_on_chain if data_to_store_on_chain.startswith('0x') else '0x' + data_to_store_on_chain
        }
        tx_body = {
            'chainTag': 0x27,  # Testnet chainTag; use 0x4a for mainnet
            'blockRef': block_ref,
            'expiration': 32,
            'clauses': [clause],
            'gasPriceCoef': 0,
            'gas': 100000,  # For production, estimate gas dynamically
            'dependsOn': None,
            'nonce': secrets.randbits(64)
        }
        tx = Transaction(tx_body)
        signing_hash = tx.get_signing_hash()
        signature = secp256k1.sign(signing_hash, bytes.fromhex(PRIVATE_KEY_HEX))
        tx.set_signature(signature)
        raw_tx = '0x' + tx.encode().hex()

        # Send the signed transaction
        send_resp = requests.post(f"{NODE_URL}/transactions", json={'raw': raw_tx})
        # Print the raw response for troubleshooting
        print("Status code:", send_resp.status_code)
        print("Response text:", send_resp.text)
        send_resp.raise_for_status()
        try:
            tx_id = send_resp.json()['id']
            return tx_id, None
        except Exception:
            return None, f"Node did not return JSON. Response: {send_resp.text}"
    except Exception as e:
        return None, str(e)

@app.route('/')
def index():
    return render_template('index.html')

# Route for document notarization
@app.route('/notarize', methods=['POST'])
def notarize_document():
    data = request.get_json()
    if not data or 'data' not in data:
        return jsonify({'error': 'Missing data field'}), 400
    tx_id, error = send_vechain_transaction(data['data'])
    if error:
        return jsonify({'error': error}), 400
    return jsonify({'success': True, 'transaction_id': tx_id})

# Alias to match your frontend call
@app.route('/send_transaction', methods=['POST'])
def send_transaction():
    return notarize_document()  # Reuse the same logic

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'node_url': NODE_URL,
        'contract_address': CONTRACT_ADDRESS,
        'max_string_length': MAX_STRING_LENGTH
    })

# Fix favicon 404 error
@app.route('/favicon.ico')
def favicon():
    return '', 204  # No content response

if __name__ == '__main__':
    if not NODE_URL or not CONTRACT_ADDRESS or not PRIVATE_KEY_HEX:
        print("FATAL ERROR: NODE_URL, CONTRACT_ADDRESS, or PRIVATE_KEY not configured in .env")
        exit(1)
    app.run(host='0.0.0.0', port=5002, debug=True, use_reloader=False)  # Added use_reloader



