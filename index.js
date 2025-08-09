// Add to state
const [userComment, setUserComment] = useState('');

// Add to render method
{hash && (
  <div className="hash-display">
    <p>Document Hash:</p>
    <code>{hash}</code>
    
    <label>Document Description (Optional)</label>
    <textarea
      placeholder="Add details about this document"
      value={userComment}
      onChange={(e) => setUserComment(e.target.value)}
      rows="2"
      className="input"
    />
    
    <button onClick={notarize}>Notarize on VeChain</button>
  </div>
)}

// Update notarize function
const notarize = async () => {
  if (!hash || !account) return;
  
  try {
    const response = await fetch('/api/prepaid-tx', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        hash, 
        userAddress: account,
        userComment
      })
    });
    
    const result = await response.json();
    
    if (result.success) {
      setTxId(result.txid);
      console.log('Transaction Comment:', result.comment);
      console.log('View transaction:', result.explorerUrl);
    } else {
      console.error('Notarization failed:', result.error);
    }
  } catch (error) {
    console.error('API request failed:', error);
  }
};
// Add to index.js
async function verifyTransaction(txid) {
  const connex = new Connex({
    node: 'https://testnet.vechain.org',
    network: 'test'
  });

  // Get transaction details
  const tx = await connex.thor.transaction(txid).get();
  console.log('Transaction Comment:', tx.comment);

  // Get receipt
  const receipt = await connex.thor.transaction(txid).getReceipt();

  // Method 1: Contract event
  if (receipt.outputs.length > 0 && receipt.outputs[0].events) {
    const notarizationEvent = receipt.outputs[0].events.find(
      e => e.abi?.name === 'DocumentNotarized'
    );

    if (notarizationEvent) {
      console.log('Contract Event:');
      console.log(' - Sender:', notarizationEvent.decoded.sender);
      console.log(' - Document Hash:', notarizationEvent.decoded.documentHash);
      console.log(' - Comment:', notarizationEvent.decoded.comment);
      return;
    }
  }

  // Method 2: Data extraction
  if (tx.data.startsWith('0x7b')) { // Detects JSON-like data
    try {
      const jsonStr = Buffer.from(tx.data.slice(2), 'hex').toString();
      const data = JSON.parse(jsonStr);
      console.log('Embedded Data:');
      console.log(' - Hash:', data.h);
      console.log(' - Comment:', data.c);
      console.log(' - Timestamp:', data.t);
    } catch (e) {
      console.log('Raw Data:', tx.data);
    }
  }
}

// Usage (when you have txid):
verifyTransaction(txId);
