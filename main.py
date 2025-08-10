from flask import Flask, request, jsonify, render_template
import requests
import os
import secrets
import logging
from dotenv import load_dotenv
from thor_devkit.transaction import Transaction
from thor_devkit.cry import secp256k1
from flask_cors import CORS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
NODE_URL = os.getenv("NODE_URL", "https://testnet.vechain.org").rstrip('/')
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
PRIVATE_KEY_HEX = os.getenv("PRIVATE_KEY", "").strip()
MAX_STRING_LENGTH = 64

app = Flask(__name__)
CORS(app)

def get_block_ref():
    try:
        resp = requests.get(f"{NODE_URL}/blocks/best", timeout=10)
        resp.raise_for_status()
        block_id = resp.json()['id']
        return block_id[2:18].lower()  # Ensure lowercase hex
    except Exception as e:
        logger.error(f"Node connection error: {str(e)}")
        return "0x0000000000000000"  # Fallback blockref

def send_vechain_transaction(data_to_store_on_chain: str):
    if not PRIVATE_KEY_HEX:
        return None, "Private key not configured."
    
    if not data_to_store_on_chain:
        return None, "Empty data field"
    
    if len(data_to_store_on_chain) > MAX_STRING_LENGTH:
        return None, f"Input exceeds {MAX_STRING_LENGTH} characters."

    try:
        block_ref = get_block_ref()
        logger.info(f"Using block ref: {block_ref}")
        
        # Prepare data - ensure it starts with 0x
        if not data_to_store_on_chain.startswith('0x'):
            data_to_store_on_chain = '0x' + data_to_store_on_chain
        
        clause = {
            'to': CONTRACT_ADDRESS,
            'value': 0,
            'data': data_to_store_on_chain
        }
        
        tx_body = {
            'chainTag': 0x27,  # Testnet chainTag
            'blockRef': block_ref,
            'expiration': 32,
            'clauses': [clause],
            'gasPriceCoef': 0,
            'gas': 200000,  # Increased gas limit
            'dependsOn': None,
            'nonce': secrets.randbits(64)
        }
        
        tx = Transaction(tx_body)
        signing_hash = tx.get_signing_hash()
        
        # Handle private key formatting
        private_key_bytes = bytes.fromhex(PRIVATE_KEY_HEX)
        if len(private_key_bytes) != 32:
            return None, "Invalid private key length"
            
        signature = secp256k1.sign(signing_hash, private_key_bytes)
        tx.set_signature(signature)
        raw_tx = '0x' + tx.encode().hex()
        logger.info(f"Created raw transaction: {raw_tx[:50]}...")

        # Send transaction
        send_resp = requests.post(
            f"{NODE_URL}/transactions", 
            json={'raw': raw_tx},
            timeout=30
        )
        
        logger.info(f"Node response: {send_resp.status_code}, {send_resp.text}")
        
        if send_resp.status_code != 200:
            return None, f"Node error: {send_resp.text}"
        
        try:
            tx_id = send_resp.json().get('id')
            if not tx_id:
                return None, "Node response missing transaction ID"
                
            logger.info(f"Transaction successful! ID: {tx_id}")
            return tx_id, None
        except Exception:
            return None, f"Invalid node response: {send_resp.text}"
            
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
            logger.error(f"Notarization error: {error}")
            return jsonify({'error': error}), 400
            
        return jsonify({
            'success': True, 
            'transaction_id': tx_id,
            'explorer_link': f"{NODE_URL}/transactions/{tx_id}"
        })
        
    except Exception as e:
        logger.exception("Unexpected error")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/send_transaction', methods=['POST'])
def send_transaction():
    return notarize_document()

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'node_url': NODE_URL,
        'contract_address': CONTRACT_ADDRESS,
        'max_string_length': MAX_STRING_LENGTH
    })

@app.route('/favicon.ico')
def favicon():
    return '', 204

if __name__ == '__main__':
    # Validate environment
    errors = []
    if not NODE_URL:
        errors.append("NODE_URL missing")
    if not CONTRACT_ADDRESS or not CONTRACT_ADDRESS.startswith("0x") or len(CONTRACT_ADDRESS) != 42:
        errors.append("Invalid CONTRACT_ADDRESS")
    if not PRIVATE_KEY_HEX or len(PRIVATE_KEY_HEX) != 64:
        errors.append("Invalid PRIVATE_KEY format (should be 64 hex characters)")
    
    if errors:
        logger.critical("Configuration errors: " + ", ".join(errors))
        exit(1)
        
    logger.info("Starting VeChain Notarization Service")
    app.run(host='0.0.0.0', port=5002, debug=True, use_reloader=False)
