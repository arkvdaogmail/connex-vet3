import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
from thor_devkit import cry, transaction

app = Flask(__name__, static_folder='frontend')
CORS(app)

# Environment variables
NODE_URL = os.environ.get('NODE_URL', 'https://testnet.vechain.org')
CONTRACT_ADDRESS = os.environ.get('CONTRACT_ADDRESS')
PRIVATE_KEY = os.environ.get('PRIVATE_KEY')

# API Endpoints
@app.route('/health')
def health_check():
    return jsonify({"status": "OK", "service": "VeChain Notarization"})

@app.route('/notarize', methods=['POST'])
def notarize():
    try:
        data = request.get_json()
        content_hash = data.get('content')
        
        if not content_hash or len(content_hash) != 64:
            return jsonify({"error": "Invalid hash format"}), 400

        # Create transaction
        clause = {
            'to': CONTRACT_ADDRESS,
            'value': 0,
            'data': '0x' + content_hash
        }

        tx = transaction.Transaction(
            chainTag=0x4a,
            blockRef=0,
            expiration=720,
            clauses=[clause],
            gasPriceCoef=0,
            gas=50000,
            nonce=12345678
        )

        # Sign and send
        private_key_bytes = bytes.fromhex(PRIVATE_KEY)
        signature = cry.secp256k1.sign(tx.get_signing_hash(), private_key_bytes)
        tx.signature = signature
        raw_tx = '0x' + tx.encode().hex()

        response = requests.post(
            f"{NODE_URL}/transactions",
            json={"raw": raw_tx},
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code != 200:
            return jsonify({"error": "Blockchain error"}), 500

        return jsonify({
            "status": "success",
            "txId": response.json()['id']
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Frontend Serving
@app.route('/')
def serve_index():
    return send_from_directory('frontend', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('frontend', filename)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)