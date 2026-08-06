import type { NextApiRequest, NextApiResponse } from 'next'

// Minimal compatibility shim for legacy pages/api/chat.ts
// Forwards POST /message to the configured backend when available, otherwise returns a safe placeholder.

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  try {
    if (req.method === 'POST') {
      // Forward message to backend if possible
      const body = req.body || {}
      const forwardUrl = `${BACKEND}/api/chat/message`
      try {
        const r = await fetch(forwardUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        })
        const json = await r.json()
        return res.status(r.status).json(json)
      } catch (err) {
        // Backend unreachable - return a safe canned response
        return res.status(200).json({ response: "JARVIS is currently offline (shim).", agent: 'jarvis', timestamp: new Date().toISOString() })
      }
    }

    if (req.method === 'GET') {
      return res.status(200).json({ ok: true, message: 'Chat shim active' })
    }

    res.setHeader('Allow', ['GET', 'POST'])
    res.status(405).end(`Method ${req.method} Not Allowed`)
  } catch (e) {
    res.status(500).json({ error: 'internal_error', details: String(e) })
  }
}
