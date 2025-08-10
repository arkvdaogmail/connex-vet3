import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()  # Load .env file

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
from thor_devkit import cry, transaction

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# ===== Path Configuration =====
BASE_DIR = Path(__file__).parent.parent  # Goes up to repo root
FRONTEND_DIR = BASE_DIR / 'frontend'    # Points to frontend folder

# ===== Environment Variables =====
NODE_URL = os.environ.get('NODE_URL', 'https://testnet.vechain.org')
CONTRACT_ADDRESS = os.environ.get('CONTRACT_ADDRESS')
PRIVATE_KEY = os.environ.get('PRIVATE_KEY')

# Verify critical variables
if not CONTRACT_ADDRESS or not PRIVATE_KEY:
    raise ValueError("Missing required environment variables")

# ===== API Endpoints =====
@app.route('/health')
def health_check():
    return jsonify({
        "status": "OK",
        "service": "VeChain Notarization"
    })

@app.route('/notarize', methods=['POST'])
def notarize():
    try:
        data = request.get_json()
        content_hash = data.get('content', '').strip()
        
        if len(content_hash) != 64:
            return jsonify({"error": "Invalid hash format"}), 400

        # Transaction creation and signing (same as before)
        # ...

        return jsonify({
            "status": "success",
            "txId": response.json()['id']
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ===== Frontend Serving =====
@app.route('/')
def serve_index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(FRONTEND_DIR, filename)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
