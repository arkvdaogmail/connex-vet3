import { Framework } from '@vechain/connex-framework'
import { Driver, SimpleNet, SimpleWallet } from '@vechain/connex-driver'

const ABI = {
  registerDocument: {
    constant: false,
    inputs: [
      { name: '_hash', type: 'bytes32' },
      { name: '_reference', type: 'string' },
      { name: '_metadataURI', type: 'string' }
    ],
    name: 'registerDocument',
    outputs: [], payable: false, stateMutability: 'nonpayable', type: 'function'
  }
}

function toBytes32(hex) {
  const clean = hex.startsWith('0x') ? hex.slice(2) : hex
  if (clean.length !== 64) throw new Error('hash must be 32 bytes (64 hex)')
  return '0x' + clean
}

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ ok:false, error:'Method not allowed' })
  
  try {
    const { NODE_URL, CONTRACT_ADDRESS, PRIVATE_KEY } = process.env
    if (!CONTRACT_ADDRESS) throw new Error('CONTRACT_ADDRESS missing')
    if (!PRIVATE_KEY) throw new Error('PRIVATE_KEY missing on server')

    const { documents } = req.body || {}
    if (!documents || !Array.isArray(documents) || documents.length === 0) {
      throw new Error('documents array required')
    }

    // Validate all documents first
    for (const doc of documents) {
      if (!doc.hash || !doc.reference || !doc.metadataURI) {
        throw new Error('Each document needs hash, reference, metadataURI')
      }
    }

    const net = new SimpleNet(NODE_URL || 'https://testnet.veblocks.net')
    const wallet = new SimpleWallet()
    wallet.import(PRIVATE_KEY)
    const driver = await Driver.connect(net, wallet)
    const connex = new Framework(driver)

    const acc = connex.thor.account(CONTRACT_ADDRESS)
    
    // Create clauses for batch transaction
    const clauses = documents.map(doc => 
      acc.method(ABI.registerDocument).asClause(
        toBytes32(doc.hash), 
        doc.reference, 
        doc.metadataURI
      )
    )

    // Estimate gas before sending
    const gasEstimate = await connex.thor.explain(clauses).execute()
    const totalGas = gasEstimate.reduce((sum, result) => sum + result.gasUsed, 0)

    console.log(`Batch registering ${documents.length} documents, estimated gas: ${totalGas}`)

    const tx = await connex.vendor.sign('tx', clauses).request()
    
    return res.status(200).json({ 
      ok: true, 
      txid: tx.txid,
      documentsCount: documents.length,
      estimatedGas: totalGas,
      gasPerDocument: Math.round(totalGas / documents.length)
    })
  } catch (e) {
    console.error('Batch registration error:', e.message)
    return res.status(400).json({ ok:false, error: e.message })
  }
}

