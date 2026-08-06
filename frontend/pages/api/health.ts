import type { NextApiRequest, NextApiResponse } from 'next'

// Minimal health endpoint compatibility shim for legacy tests
export default function handler(req: NextApiRequest, res: NextApiResponse) {
  res.status(200).json({ status: 'healthy', timestamp: new Date().toISOString() })
}
