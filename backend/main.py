import os
from dotenv import load_dotenv  # Environment loader
load_dotenv()  # Load .env file BEFORE other imports

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
from thor_devkit import cry, transaction

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS

# ===== Environment Variables =====
NODE_URL = os.environ.get('NODE_URL', 'https://testnet.vechain.org')
CONTRACT_ADDRESS = os.environ.get('CONTRACT_ADDRESS')
PRIVATE_KEY = os.environ.get('PRIVATE_KEY')

# Verify critical variables
if not CONTRACT_ADDRESS or not PRIVATE_KEY:
    raise ValueError("Missing required environment variables: CONTRACT_ADDRESS or PRIVATE_KEY")

# ===== API Endpoints =====
@app.route('/health', methods=['GET'])
def health_check():
    """Service health check"""
    return jsonify({
        "status": "OK",
        "service": "VeChain Notarization",
        "version": "1.0",
        "contract": CONTRACT_ADDRESS[:6] + "..." + CONTRACT_ADDRESS[-4:]
    })

@app.route('/notarize', methods=['POST'])
def notarize():
    """Notarize content hash on VeChain"""
    try:
        # Validate request
        if not request.is_json:
            return jsonify({"error": "Missing JSON body"}), 400
            
        data = request.get_json()
        content_hash = data.get('content', '').strip()
        
        # Validate content hash
        if not content_hash:
            return jsonify({"error": "Missing content hash"}), 400
            
        if len(content_hash) != 64 or not all(c in '0123456789abcdef' for c in content_hash):
            return jsonify({"error": "Invalid hash format. Must be 64-character hex string"}), 400

        # ===== Create VeChain Transaction =====
        clause = {
            'to': CONTRACT_ADDRESS,
            'value': 0,
            'data': '0x' + content_hash
        }

        tx = transaction.Transaction(
            chainTag=0x4a,  # Testnet chain tag
            blockRef=0,
            expiration=720,  # Expires in 720 blocks (~3 hours)
            clauses=[clause],
            gasPriceCoef=0,
            gas=50000,
            nonce=12345678  # Unique identifier
        )

        # Sign transaction
        private_key_bytes = bytes.fromhex(PRIVATE_KEY)
        message_hash = tx.get_signing_hash()
        signature = cry.secp256k1.sign(message_hash, private_key_bytes)
        tx.signature = signature

        # Serialize transaction
        raw_tx = '0x' + tx.encode().hex()

        # Send to VeChain node
        response = requests.post(
            f"{NODE_URL}/transactions",
            json={"raw": raw_tx},
            headers={'Content-Type': 'application/json'},
            timeout=15  # 15-second timeout
        )

        # Handle blockchain response
        if response.status_code != 200:
            error_data = response.json()
            return jsonify({
                "error": "Blockchain transaction failed",
                "code": error_data.get('code'),
                "message": error_data.get('message')
            }), 502  # Bad Gateway

        tx_id = response.json()['id']
        return jsonify({
            "status": "success",
            "txId": tx_id,
            "explorer": f"https://explore-testnet.vechain.org/transactions/{tx_id}"
        })

    except Exception as e:
        app.logger.error(f"Notarization error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

# ===== Frontend Serving =====
@app.route('/')
def serve_index():
    """Serve main frontend page"""
    return send_from_directory('frontend', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static frontend files"""
    return send_from_directory('frontend', filename)

# ===== Main Entry Point =====
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
