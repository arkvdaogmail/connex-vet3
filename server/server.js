
// server/server.js
import 'dotenv/config'
import express from 'express'
import cors from 'cors'
import { Framework } from '@vechain/connex-framework'
import { Driver, SimpleNet, SimpleWallet } from '@vechain/connex-driver'

const {
  NODE_URL = 'https://testnet.vechain.org',
  CONTRACT_ADDRESS,
  PRIVATE_KEY
} = process.env

if (!CONTRACT_ADDRESS) console.warn('⚠️ CONTRACT_ADDRESS not set in .env')
if (!PRIVATE_KEY) console.warn('⚠️ PRIVATE_KEY not set in .env')

const app = express()
app.use(cors())
app.use(express.json())

let connex
let driver

async function initConnex() {
  const net = new SimpleNet(NODE_URL)
  const wallet = new SimpleWallet()
  if (PRIVATE_KEY) wallet.import(PRIVATE_KEY)
  driver = await Driver.connect(net, wallet)
  connex = new Framework(driver)
  console.log('✅ Connected to VeChain node:', NODE_URL)
}
await initConnex()

// Minimal ABI for your VDaoRegistry
const ABI = {
  registerDocument: {
    "constant": false,
    "inputs": [
      {"name":"_hash","type":"bytes32"},
      {"name":"_reference","type":"string"},
      {"name":"_metadataURI","type":"string"}
    ],
    "name":"registerDocument",
    "outputs":[],
    "payable": false,
    "stateMutability":"nonpayable",
    "type":"function"
  },
  getDocumentInfo: {
    "constant": true,
    "inputs":[{"name":"_hash","type":"bytes32"}],
    "name":"getDocumentInfo",
    "outputs":[
      {"name":"owner","type":"address"},
      {"name":"timestamp","type":"uint256"},
      {"name":"metadataURI","type":"string"},
      {"name":"voteCount","type":"uint256"},
      {"name":"exists","type":"bool"}
    ],
    "payable": false,
    "stateMutability":"view",
    "type":"function"
  }
}

// Helper to hexify 32-byte hash
function toBytes32(hex) {
  const clean = hex.startsWith('0x') ? hex.slice(2) : hex
  if (clean.length !== 64) throw new Error('hash must be 32 bytes (64 hex)')
  return '0x' + clean
}

// Health
app.get('/api/health', (req,res)=>{
  res.json({ ok:true, node: NODE_URL, hasWallet: !!PRIVATE_KEY, contract: CONTRACT_ADDRESS || null })
})

// Read
app.get('/api/document/:hash', async (req, res) => {
  try {
    const hash = toBytes32(req.params.hash)
    const acc = connex.thor.account(CONTRACT_ADDRESS)
    const m = ABI.getDocumentInfo
    const { decoded } = await acc.method(m).call(hash)
    res.json({
      hash,
      owner: decoded[0],
      timestamp: Number(decoded[1]) * 1000,
      metadataURI: decoded[2],
      voteCount: Number(decoded[3]),
      exists: decoded[4]
    })
  } catch (e) {
    res.status(400).json({ ok:false, error: e.message })
  }
})

// Write
app.post('/api/register', async (req, res) => {
  try {
    const { hash, reference, metadataURI } = req.body
    if (!hash || !reference || !metadataURI) throw new Error('hash, reference, metadataURI required')
    if (!PRIVATE_KEY) throw new Error('Server PRIVATE_KEY missing. Add to .env')
    const acc = connex.thor.account(CONTRACT_ADDRESS)
    const m = ABI.registerDocument
    const clause = acc.method(m).asClause(toBytes32(hash), reference, metadataURI)
    const tx = await connex.vendor.sign('tx', [clause]).request()
    res.json({ ok:true, txid: tx.txid })
  } catch (e) {
    res.status(400).json({ ok:false, error: e.message })
  }
})

const PORT = process.env.PORT || 8787
app.listen(PORT, () => console.log(`🚀 API on http://localhost:${PORT}`))
