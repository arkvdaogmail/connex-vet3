const { ThorClient, VeChainProvider, ProviderInternalBaseWallet, Clause, Transaction } = require('@vechain/sdk-core');
const { abi } = require('thor-devkit');

module.exports = async (req, res) => {
  try {
    const THOR_NODE_URL = 'https://testnet.vechain.org';
    const PREPAID_PK = process.env.PREPAID_PK;
    const PREPAID_ADDRESS = process.env.PREPAID_ADDRESS;
    const CONTRACT_ADDRESS = process.env.CONTRACT_ADDRESS; // Optional

    const { hash, userAddress, userComment } = req.body;
    if (!hash || !userAddress) {
      return res.status(400).json({ error: 'Missing hash or userAddress' });
    }

    const thorClient = ThorClient.fromUrl(THOR_NODE_URL);
    const provider = new VeChainProvider(
      thorClient,
      new ProviderInternalBaseWallet([{
        privateKey: Buffer.from(PREPAID_PK.replace('0x', ''), 'hex'),
        address: PREPAID_ADDRESS
      }])
    );

    // 1. Prepare transaction data
    const clauses = [];
    let txComment = `Notarized: ${hash.substring(0, 8)}...`;
    
    // Option 1: Smart contract event (if contract address provided)
    if (CONTRACT_ADDRESS) {
      // ABI for event emission
      const eventAbi = {
        name: 'DocumentNotarized',
        type: 'event',
        inputs: [
          { name: 'sender', type: 'address' },
          { name: 'documentHash', type: 'string' },
          { name: 'comment', type: 'string' }
        ]
      };
      
      // Encode function call
      const functionAbi = {
        name: 'notarizeDocument',
        type: 'function',
        inputs: [
          { type: 'string', name: '_hash' },
          { type: 'string', name: '_comment' }
        ]
      };
      
      const coder = new abi.Function(functionAbi);
      const data = coder.encode([hash, userComment || '']);
      
      clauses.push({
        to: CONTRACT_ADDRESS,
        value: '0x0',
        data: '0x' + data.toString('hex')
      });
      
      txComment = `Contract notarize: ${userComment?.substring(0, 30) || hash.substring(0, 12)}...`;
    } 
    // Option 2: Data transaction with embedded comment
    else {
      const data = {
        h: hash,
        c: userComment || '',
        t: new Date().toISOString()
      };
      
      clauses.push({
        to: null,
        value: '0x0',
        data: '0x' + Buffer.from(JSON.stringify(data)).toString('hex')
      });
      
      if (userComment) {
        txComment = userComment.length > 50 
          ? `${userComment.substring(0, 47)}...` 
          : userComment;
      }
    }

    // 2. Create and sign transaction
    const signer = await provider.getSigner(PREPAID_ADDRESS);
    const txBody = await signer.buildTransaction(clauses);
    txBody.comment = txComment;
    
    const rawSignedTx = await signer.signTransaction(txBody);
    const signedTx = Transaction.decode(Buffer.from(rawSignedTx.slice(2), 'hex'));
    const sendResult = await thorClient.transactions.sendTransaction(signedTx);

    // 3. Return result
    res.status(200).json({ 
      success: true,
      txid: sendResult.id,
      comment: txComment,
      explorerUrl: `https://explore-testnet.vechain.org/transactions/${sendResult.id}`,
      method: CONTRACT_ADDRESS ? 'contract-event' : 'data-embed'
    });

  } catch (error) {
    console.error('Prepaid TX error:', error);
    res.status(500).json({ 
      success: false,
      error: error.message,
      details: error.response?.data || error.stack
    });
  }
};
