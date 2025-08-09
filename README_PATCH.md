
# TrustSeal Fix Patch (connex-vet2-main)

This adds a **real backend** that signs transactions with your prepaid wallet.

## Install (from project root)
```bash
# add backend deps
npm i -D dotenv
npm i @vechain/connex-framework @vechain/connex-driver express cors
```

## Configure
1. Copy `server/.env.example` to `server/.env` and fill:
```
NODE_URL=https://testnet.vechain.org
CONTRACT_ADDRESS=0x...   # from your deployed VDaoRegistry
PRIVATE_KEY=0x...        # prepaid wallet
PORT=8787
```

## Run
```bash
node server/server.js
# Health check
curl http://localhost:8787/api/health
```

## Frontend change
Replace any direct Connex calls in the browser with HTTP calls to the backend:
```js
// register
await fetch('/api/register', {
  method:'POST',
  headers:{'Content-Type':'application/json'},
  body: JSON.stringify({ hash, reference, metadataURI })
})

// read
const r = await fetch('/api/document/' + hash)
```

This ensures **real transactions** and **real lookups** using your prepaid gas.
