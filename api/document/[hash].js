import { Framework } from '@vechain/connex-framework'
import { Driver, SimpleNet } from '@vechain/connex-driver'

const ABI = {
  getDocumentInfo: {
    constant: true,
    inputs: [{ name: '_hash', type: 'bytes32' }],
    name: 'getDocumentInfo',
    outputs: [
      { name: 'owner', type: 'address' },
      { name: 'timestamp', type: 'uint256' },
      { name: 'metadataURI', type: 'string' },
      { name: 'voteCount', type: 'uint256' },
      { name: 'exists', type: 'bool' }
    ],
    payable: false, stateMutability: 'view', type: 'function'
  }
}

function toBytes32(hex) {
  const clean = hex.startsWith('0x') ? hex.slice(2) : hex
  if (clean.length !== 64) throw new Error('hash must be 32 bytes (64 hex)')
  return '0x' + clean
}

export default async function handler(req, res) {
  try {
    const { NODE_URL, CONTRACT_ADDRESS } = process.env
    if (!CONTRACT_ADDRESS) throw new Error('CONTRACT_ADDRESS missing')
    const { hash } = req.query
    const net = new SimpleNet(NODE_URL || 'https://testnet.veblocks.net')
    const driver = await Driver.connect(net)
    const connex = new Framework(driver)
    const acc = connex.thor.account(CONTRACT_ADDRESS)
    const { decoded } = await acc.method(ABI.getDocumentInfo).call(toBytes32(hash))

    res.status(200).json({
      hash: '0x' + hash.replace(/^0x/, ''),
      owner: decoded[0],
      timestamp: Number(decoded[1]) * 1000,
      metadataURI: decoded[2],
      voteCount: Number(decoded[3]),
      exists: decoded[4]
    })
  } catch (e) {
    res.status(400).json({ ok:false, error: e.message })
  }
}
