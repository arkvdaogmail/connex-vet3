import { Framework } from '@vechain/connex-framework'
import { Driver, SimpleNet, SimpleWallet } from '@vechain/connex-driver'

export default async function handler(req, res) {
  if (req.method !== 'GET') return res.status(405).json({ ok:false, error:'Method not allowed' })
  
  try {
    const { NODE_URL, CONTRACT_ADDRESS, PRIVATE_KEY } = process.env
    if (!CONTRACT_ADDRESS) throw new Error('CONTRACT_ADDRESS missing')

    const net = new SimpleNet(NODE_URL || 'https://testnet.veblocks.net')
    const wallet = new SimpleWallet()
    if (PRIVATE_KEY) wallet.import(PRIVATE_KEY)
    const driver = await Driver.connect(net, wallet)
    const connex = new Framework(driver)

    // Get wallet balance
    const walletAddress = wallet.list[0]?.address
    let balance = 0
    if (walletAddress) {
      const account = await connex.thor.account(walletAddress).get()
      balance = parseInt(account.balance, 16) / Math.pow(10, 18) // Convert to VET
    }

    // Get current gas price
    const bestBlock = await connex.thor.status.head
    const gasPrice = bestBlock.gasLimit

    // Estimate costs for different operations
    const singleDocGas = 50000 // Estimated gas for single document
    const batchDocGas = 35000  // Estimated gas per document in batch

    const costs = {
      singleDocument: {
        gasEstimate: singleDocGas,
        costInVTHO: singleDocGas * 0.000001, // Rough VTHO cost
      },
      batchDocument: {
        gasEstimate: batchDocGas,
        costInVTHO: batchDocGas * 0.000001,
        savings: `${Math.round((1 - batchDocGas/singleDocGas) * 100)}%`
      }
    }

    return res.status(200).json({
      ok: true,
      wallet: {
        address: walletAddress,
        balanceVET: balance.toFixed(4)
      },
      network: NODE_URL?.includes('testnet') ? 'testnet' : 'mainnet',
      costs,
      recommendations: [
        balance < 1 ? 'Low wallet balance - consider topping up' : null,
        'Use batch operations for multiple documents',
        'Monitor gas usage regularly'
      ].filter(Boolean)
    })
  } catch (e) {
    return res.status(400).json({ ok:false, error: e.message })
  }
}

