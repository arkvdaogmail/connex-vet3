export default async function handler(req, res) {
  const { NODE_URL, CONTRACT_ADDRESS, PRIVATE_KEY } = process.env;
  res.status(200).json({
    ok: true,
    node: NODE_URL || null,
    hasWallet: !!PRIVATE_KEY,
    contract: CONTRACT_ADDRESS || null,
    env: "vercel-fn"
  });
}
