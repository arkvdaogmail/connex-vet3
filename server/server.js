const express = require('express')
const cors = require('cors')
const path = require('path')
require('dotenv').config({ path: path.join(__dirname, '.env') })

const app = express()
const PORT = process.env.PORT || 8787

// Middleware
app.use(cors({ origin: process.env.CORS_ORIGIN || '*' }))
app.use(express.json())
app.use(express.static('public'))

// Health check
app.get('/api/health', (req, res) => {
  res.json({ 
    ok: true, 
    service: 'TrustSeal Optimized',
    version: '3.0.0',
    network: process.env.NODE_URL?.includes('testnet') ? 'testnet' : 'mainnet',
    timestamp: new Date().toISOString()
  })
})

// Import API routes (these would be converted to CommonJS)
app.post('/api/register', async (req, res) => {
  // Single document registration (existing functionality)
  res.json({ ok: true, message: 'Single registration endpoint - implement as needed' })
})

app.post('/api/batch-register', async (req, res) => {
  // Batch registration for cost optimization
  res.json({ ok: true, message: 'Batch registration endpoint - implement as needed' })
})

app.get('/api/cost-monitor', async (req, res) => {
  // Cost monitoring and wallet status
  try {
    const mockData = {
      ok: true,
      wallet: {
        address: '0x...',
        balanceVET: '10.0000'
      },
      network: process.env.NODE_URL?.includes('testnet') ? 'testnet' : 'mainnet',
      costs: {
        singleDocument: {
          gasEstimate: 50000,
          costInVTHO: 0.05
        },
        batchDocument: {
          gasEstimate: 35000,
          costInVTHO: 0.035,
          savings: '30%'
        }
      },
      recommendations: [
        'Use batch operations for multiple documents',
        'Monitor gas usage regularly'
      ]
    }
    res.json(mockData)
  } catch (error) {
    res.status(400).json({ ok: false, error: error.message })
  }
})

app.get('/api/document/:hash', async (req, res) => {
  // Document lookup
  res.json({ ok: true, message: 'Document lookup endpoint - implement as needed' })
})

// Error handling
app.use((err, req, res, next) => {
  console.error(err.stack)
  res.status(500).json({ ok: false, error: 'Internal server error' })
})

// 404 handler
app.use((req, res) => {
  res.status(404).json({ ok: false, error: 'Endpoint not found' })
})

app.listen(PORT, '0.0.0.0', () => {
  console.log(`🚀 TrustSeal Optimized Server running on port ${PORT}`)
  console.log(`📊 Network: ${process.env.NODE_URL?.includes('testnet') ? 'testnet' : 'mainnet'}`)
  console.log(`💰 Cost monitoring available at /api/cost-monitor`)
  console.log(`🔄 Batch processing available at /api/batch-register`)
})

