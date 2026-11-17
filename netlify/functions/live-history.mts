import type { Config } from "@netlify/functions"
import { getStore } from "@netlify/blobs"
export default async (req: Request) => {
  const store = getStore("live-parking"); const out: any[] = []
  const n = Math.min(+(new URL(req.url).searchParams.get("days") || 7), 60)
  for (let i = n - 1; i >= 0; i--) {
    const d = new Date(Date.now() + 9 * 3600e3 - i * 864e5).toISOString().slice(0, 10)
    const v = (await store.get(d, { type: "json" })) as any[] | null
    if (v) out.push(...v)
  }
  return Response.json({ points: out }, { headers: { "cache-control": "public, max-age=300" } })
}
export const config: Config = { path: "/api/live-history" }
