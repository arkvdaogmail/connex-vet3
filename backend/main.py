import os
import requests
from flask import Flask, request, jsonify, send_from_directory
from thor_devkit import cry, transaction
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS

# Get environment variables
NODE_URL = os.environ.get('NODE_URL', 'https://testnet.vechain.org')
CONTRACT_ADDRESS = os.environ.get('CONTRACT_ADDRESS')
PRIVATE_KEY = os.environ.get('PRIVATE_KEY')

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "OK",
        "service": "VeChain Notarization",
        "version": "1.0"
    })

@app.route('/notarize', methods=['POST'])
def notarize():
    """Notarize content hash on VeChain"""
    try:
        # Get and validate content hash
        data = request.get_json()
        content_hash = data.get('content', '').strip()
        
        if not content_hash:
            return jsonify({"error": "Missing content hash"}), 400
            
        if len(content_hash) != 64 or not all(c in '0123456789abcdef' for c in content_hash):
            return jsonify({"error": "Invalid hash format. Must be 64-character hex string"}), 400

        # Create transaction
        clause = {
            'to': CONTRACT_ADDRESS,
            'value': 0,
            'data': '0x' + content_hash
        }

        tx = transaction.Transaction(
            chainTag=0x4a,  # Testnet chain tag
            blockRef=0,
            expiration=720,  # 720 blocks expiration
            clauses=[clause],
            gasPriceCoef=0,
            gas=50000,
            nonce=12345678
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
            timeout=10
        )

        # Handle response
        if response.status_code != 200:
            error_msg = response.json().get('message', 'Blockchain error')
            return jsonify({
                "error": "Transaction failed",
                "details": error_msg
            }), 500

        return jsonify({
            "status": "success",
            "txId": response.json()['id']
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Serve frontend files
@app.route('/')
def serve_index():
    return send_from_directory('frontend', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('frontend', filename)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
