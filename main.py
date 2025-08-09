# main.py
# ==============================================================================
# This is the complete, corrected file.
# Copy and paste all of this code into your main.py file.
# ==============================================================================

# 1. --- NECESSARY IMPORTS ---
# Core Flask imports
from flask import Flask, request, jsonify, render_template

# Imports for VeChain functionality
import requests
from thor_devkit import cry, transaction

# Library to load your private key from a .env file
import os
from dotenv import load_dotenv

# Library for creating a unique transaction nonce
import time

# Load environment variables from a .env file (like your private key)
load_dotenv()

# ==============================================================================

# 2. --- FLASK APP CONFIGURATION ---
app = Flask(__name__)

# --- Load configuration from your .env file ---
NODE_URL = os.getenv("NODE_URL")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
MNEMONIC_PHRASE = os.getenv("PRIVATE_KEY") # This is your 12-word phrase

# --- NEW, CORRECTED CODE ---
try:
    PRIVATE_KEY_BYTES = cry.mnemonic.derive_private_key(MNEMONIC_PHRASE.split(' '))
    SENDER_ADDRESS = cry.to_address(PRIVATE_KEY_BYTES) # <--- THIS IS THE CORRECT FUNCTION NAME
    print(f"SUCCESS: Wallet address derived successfully: {SENDER_ADDRESS}")
except Exception as e:
    print(f"FATAL ERROR: Could not derive private key from mnemonic. Please check your .env file. Error: {e}")
    PRIVATE_KEY_BYTES = None

# ==============================================================================

# 3. --- THE REAL VECHAIN TRANSACTION FUNCTION ---
def send_vechain_transaction(data_to_store_on_chain: str):
    """
    Builds, signs, and sends a transaction to the VeChain testnet to store a string.
    """
    if not PRIVATE_KEY_BYTES:
        print("Error: Private key is not available. Cannot send transaction.")
        return None, "Private key is not configured correctly."

    try:
        # Step 1: Get the latest block information from the network.
        response = requests.get(f"{NODE_URL}/blocks/best")
        response.raise_for_status() # Raises an error if the request failed
        latest_block = response.json()
        chain_tag = int(latest_block['id'][2:4], 16)
        block_ref = latest_block['id'][:18]

        # Step 2: Define what the transaction will do (the "clause").
        # We are calling the 'store' function of your smart contract.
        # The first part '0x6057361d' is the function signature for 'store(string)'.
        encoded_data = data_to_store_on_chain.encode('utf-8').hex()
        clauses = [{
            'to': CONTRACT_ADDRESS,
            'value': 0, # Not sending any VET
            'data': f"0x6057361d{encoded_data}"
        }]

        # Step 3: Build the full transaction body.
        tx_body = {
            'chainTag': chain_tag,
            'blockRef': block_ref,
            'expiration': 32,
            'clauses': clauses,
            'gasPriceCoef': 128,
            'gas': 100000, # A safe amount of gas
            'dependsOn': None,
            'nonce': int(time.time() * 1000) # A unique number for each transaction
        }

        # Step 4: Create the transaction object and sign it with your private key.
        tx = transaction.Transaction(tx_body)
        tx.sign(PRIVATE_KEY_BYTES)

        # Step 5: Send the signed transaction to the VeChain testnet.
        raw_tx = '0x' + tx.encode().hex()
        send_response = requests.post(f"{NODE_URL}/transactions", json={'raw': raw_tx})
        send_response.raise_for_status()
        
        tx_id = send_response.json()['id']
        print(f"SUCCESS: Transaction sent to the network! Transaction ID: {tx_id}")
        return tx_id, None

    except Exception as e:
        print(f"ERROR: An unexpected error occurred during the transaction process: {e}")
        return None, str(e)

# ==============================================================================

# 4. --- FLASK ROUTES (The Web Pages and API) ---

# THIS IS THE CORRECTED ROUTE FOR THE MAIN PAGE
@app.route('/')
def index():
    # This line tells Flask to find and show your index.html file.
    return render_template('index.html')

# This is the API endpoint your frontend will call to create a transaction
@app.route('/notarize', methods=['POST'])
def notarize_document():
    data = request.json
    file_hash = data.get('content')

    if not file_hash:
        return jsonify({"status": "error", "message": "No file hash provided."}), 400

    # Call the real VeChain function
    transaction_id, error_message = send_vechain_transaction(file_hash)

    if transaction_id:
        # Success! Return the real transaction ID to the frontend.
        return jsonify({
            "status": "success",
            "transaction_id": transaction_id
        })
    else:
        # The transaction failed. Return the error message.
        return jsonify({
            "status": "error",
            "message": f"Failed to send transaction: {error_message}"
        }), 500

# ==============================================================================

# 5. --- RUN THE FLASK APP ---
if __name__ == '__main__':
    # The host='0.0.0.0' makes it accessible on your local network
    app.run(host='0.0.0.0', port=5001, debug=True)

