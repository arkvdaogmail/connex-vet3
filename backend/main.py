from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
from thor_devkit import cry, transaction
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Environment variables
NODE_URL = os.getenv('NODE_URL', 'https://testnet.vechain.org')
CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS')
PRIVATE_KEY = os.getenv('PRIVATE_KEY')

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

@app.route('/notarize', methods=['POST'])
def notarize():
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({"error": "Missing 'content' in request body"}), 400
        
    content = data['content']
    
    # Validate content (64-character hex string)
    if len(content) != 64 or not all(c in '0123456789abcdef' for c in content):
        return jsonify({"error": "Invalid content format"}), 400

    # Create transaction
    tx = {
        "chainTag": 39,
        "blockRef": "0x0000000000000000",
        "expiration": 32,
        "clauses": [{
            "to": CONTRACT_ADDRESS,
            "value": "0x0",
            "data": f"0x{content}"
        }],
        "gasPriceCoef": 0,
        "gas": 50000,
        "dependsOn": None,
        "nonce": 12345678
    }

    # Sign transaction
    encoded = transaction.encode(tx)
    hashed = cry.blake2b256(encoded)
    signature = cry.secp256k1.sign(hashed, bytes.fromhex(PRIVATE_KEY))
    tx["signature"] = signature

    # Send transaction
    response = requests.post(
        f"{NODE_URL}/transactions",
        json=tx,
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code != 200:
        return jsonify({
            "error": "Blockchain transaction failed",
            "details": response.text
        }), 500

    return jsonify({
        "status": "success",
        "txId": response.json()['id']
    }), 200

if __name__ == '__main__':
    app.run(port=5002, debug=True)
