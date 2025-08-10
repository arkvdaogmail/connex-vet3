from flask import Flask, request, jsonify, render_template
import requests
import os
import secrets
import logging
import binascii
from dotenv import load_dotenv
from thor_devkit.transaction import Transaction
from thor_devkit.cry import secp256k1
from flask_cors import CORS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
NODE_URL = os.getenv("NODE_URL")  # e.g. "https://testnet.vechain.org"
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
PRIVATE_KEY_HEX = os.getenv("PRIVATE_KEY")
MAX_STRING_LENGTH = 64  # For SHA-256 hashes

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

def get_block_ref():
    try:
        resp = requests.get(f"{NODE_URL}/blocks/best", timeout=5)
        resp.raise_for_status()
        block_id = resp.json()['id']
        return block_id[2:18]  # Remove '0x' and take first 16 hex chars
    except Exception as e:
        logger.error(f"Error getting block ref: {str(e)}")
        raise

def is_valid_hex(s):
    try:
        if s.startswith('0x'):
            bytes.fromhex(s[2:])
        else:
            bytes.fromhex(s)
        return True
    except ValueError:
        return False

def send_vechain_transaction(data_to_store_on_chain: str):
    if not PRIVATE_KEY_HEX:
        return None, "Private key not configured."
    
    if not data_to_store_on_chain:
        return None, "Empty data field"
    
    if len(data_to_store_on_chain) > MAX_STRING_LENGTH:
        return None, f"Input exceeds {MAX_STRING_LENGTH} characters."
    
    if not is_valid_hex(data_to_store_on_chain):
        return None, "Invalid hex format"

    try:
        block_ref = get_block_ref()
        logger.info(f"Using block ref: {block_ref}")
        
        # Ensure data starts with 0x
        if not data_to_store_on_chain.startswith('0x'):
            data_to_store_on_chain = '0x' + data_to_store_on_chain
        
        clause = {
            'to': CONTRACT_ADDRESS,
            'value': 0,
            'data': data_to_store_on_chain
        }
        
        tx_body = {
            'chainTag': 0x27,  # Testnet chainTag; use 0x4a for mainnet
            'blockRef': block_ref,
            'expiration': 32,
            'clauses': [clause],
            'gasPriceCoef': 0,
            'gas': 100000,
            'dependsOn': None,
            'nonce': secrets.randbits(64)
        }
        
        tx = Transaction(tx_body)
        signing_hash = tx.get_signing_hash()
        signature = secp256k1.sign(signing_hash, bytes.fromhex(PRIVATE_KEY_HEX))
        tx.set_signature(signature)
        raw_tx = '0x' + tx.encode().hex()

        # Send the signed transaction
        send_resp = requests.post(f"{NODE_URL}/transactions", json={'raw': raw_tx}, timeout=10)
        logger.info(f"Node response: {send_resp.status_code}, {send_resp.text}")
        
        if send_resp.status_code != 200:
            return None, f"Node error: {send_resp.status_code} - {send_resp.text}"
        
        try:
            tx_id = send_resp.json().get('id')
            if not tx_id:
                return None, "Node response missing transaction ID"
            return tx_id, None
        except Exception:
            return None, f"Node did not return JSON. Response: {send_resp.text}"
            
    except Exception as e:
        return None, f"Transaction failed: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/notarize', methods=['POST'])
def notarize_document():
    try:
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Missing request body'}), 400
            
        if 'content' not in data:
            return jsonify({'error': "Missing 'content' field"}), 400
            
        content = data['content']
        logger.info(f"Notarizing content: {content[:20]}...")
            
        tx_id, error = send_vechain_transaction(content)
        
        if error:
            return jsonify({'error': error}), 400
            
        return jsonify({
            'success': True, 
            'transaction_id': tx_id,
            'explorer_link': f"{NODE_URL}/transactions/{tx_id}"
        })
        
    except Exception as e:
        logger.exception("Unexpected error in /notarize")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

# Backward compatibility endpoint
@app.route('/send_transaction', methods=['POST'])
def send_transaction():
    return notarize_document()

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
    return '', 204

if __name__ == '__main__':
    # Validate environment variables
    required_vars = ['NODE_URL', 'CONTRACT_ADDRESS', 'PRIVATE_KEY']
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        logger.critical(f"Missing environment variables: {', '.join(missing)}")
        exit(1)
        
    logger.info("Starting VeChain Notarization Service")
    logger.info(f"Node URL: {NODE_URL}")
    logger.info(f"Contract Address: {CONTRACT_ADDRESS}")
    logger.info(f"Max String Length: {MAX_STRING_LENGTH}")
    
    app.run(host='0.0.0.0', port=5002, debug=True, use_reloader=False)

