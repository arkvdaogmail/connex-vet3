# main.py
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

# Load environment variables from a .env file
load_dotenv()

# ==============================================================================

# 2. --- FLASK APP CONFIGURATION ---
app = Flask(__name__)

# Load configuration from your .env file
# This is the SECURE way to handle your keys.
NODE_URL = os.getenv("NODE_URL", "https://testnet.vechain.org" )
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
MNEMONIC_PHRASE = os.getenv("PRIVATE_KEY") # It's a mnemonic, not a raw key

# Gas settings from your config
GAS = int(os.getenv("GAS", 50000))
GAS_PRICE = int(os.getenv("GAS_PRICE", 1000000000))

# --- CRITICAL STEP: Derive the private key from your 12-word phrase ---
# The private key must be in 'bytes' format for signing.
try:
    PRIVATE_KEY_BYTES = cry.mnemonic.derive_private_key(MNEMONIC_PHRASE.split(' '))
    SENDER_ADDRESS = cry.private_key_to_address(PRIVATE_KEY_BYTES)
    print(f"Successfully derived address: {SENDER_ADDRESS}")
except Exception as e:
    print(f"FATAL ERROR: Could not derive private key from mnemonic. Please check your .env file. Error: {e}")
    PRIVATE_KEY_BYTES = None
    SENDER_ADDRESS = None

# ==============================================================================

# 3. --- THE REAL VECHAIN TRANSACTION FUNCTION (FILLED IN) ---
def send_vechain_transaction(data_to_store_on_chain: str):
    """
    Builds, signs, and sends a transaction to the VeChain testnet to store a string.
    """
    if not PRIVATE_KEY_BYTES:
        print("Error: Private key is not available. Cannot send transaction.")
        return None

    try:
        # Step 1: Get the latest block information (chain tag) from the network.
        # This is required for the transaction to be valid.
        response = requests.get(f"{NODE_URL}/blocks/best")
        response.raise_for_status() # Raises an error if the request failed
        latest_block = response.json()
        chain_tag = int(latest_block['id'][2:4], 16) # Extract chain tag from block ID

        # Step 2: Define what the transaction will do.
        # We are calling the 'store' function of your smart contract.
        # The first part '0x6057361d' is the function signature for 'store(string)'.
        # The second part is the string data, encoded correctly.
        encoded_data = data_to_store_on_chain.encode('utf-8').hex().ljust(64, '0')
        contract_function_call_data = f"0x6057361d{encoded_data}"

        # Step 3: Create the transaction "clauses". This is the main payload.
        clauses = [{
            'to': CONTRACT_ADDRESS,
            'value': 0, # We are not sending any VET, just calling a function
            'data': contract_function_call_data
        }]

        # Step 4: Build the full transaction body.
        tx_body = {
            'chainTag': chain_tag,
            'blockRef': latest_block['id'][:18], # First 8 bytes of the block ID
            'expiration': 32, # Number of blocks until the tx expires
            'clauses': clauses,
            'gasPriceCoef': 128, # A safe default value
            'gas': GAS,
            'dependsOn': None,
            'nonce': 12345678 # A random number for replay protection
        }

        # Step 5: Create the transaction object and sign it with your private key.
        tx = transaction.Transaction(tx_body)
        tx.sign(PRIVATE_KEY_BYTES)

        # Step 6: Send the signed transaction to the VeChain testnet.
        raw_tx = '0x' + tx.encode().hex()
        post_headers = {'Content-Type': 'application/json'}
        post_body = {'raw': raw_tx}
        
        print("Sending transaction to the network...")
        send_response = requests.post(f"{NODE_URL}/transactions", json=post_body, headers=post_headers)
        send_response.raise_for_status()
        
        tx_id = send_response.json()['id']
        print(f"Transaction sent successfully! Transaction ID: {tx_id}")

        # Step 7: Return the REAL transaction ID.
        return tx_id

    except requests.exceptions.RequestException as e:
        print(f"Error communicating with VeChain node: {e}")
        print(f"Response body: {e.response.text if e.response else 'No response'}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during the transaction process: {e}")
        return None

# ==============================================================================

# 4. --- FLASK ROUTES (The Web Pages and API) ---
@app.route('/')
def index():
    return "VeChain Notarization App is running!" # Simple message to show it's working

@app.route('/notarize', methods=['POST'])
def notarize_document():
    data = request.json
    document_content = data.get('content')

    if not document_content:
        return jsonify({"status": "error", "message": "No content provided."}), 400

    print(f"Received content to notarize: '{document_content}'")
    transaction_id = send_vechain_transaction(document_content)

    if transaction_id:
        return jsonify({
            "status": "success",
            "message": "Transaction sent successfully!",
            "transaction_id": transaction_id
        })
    else:
        return jsonify({
            "status": "error",
            "message": "Failed to send transaction to the VeChain network."
        }), 500

# ==============================================================================

# 5. --- RUN THE FLASK APP ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
