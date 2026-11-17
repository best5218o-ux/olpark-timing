import type { Config } from "@netlify/functions"
import { getEvents } from "../lib/shared.mjs"
import { expand, CLS } from "../lib/lib.mjs"
export default async (req: Request) => {
  const u = new URL(req.url); const from = u.searchParams.get("from") || "2026-01-01", to = u.searchParams.get("to") || "2027-12-31"
  const { events, liveMonths, failedMonths, fetchedAt } = await getEvents()
  const rows = expand(events, from, to).filter(r => CLS.includes(r.cls))
  return Response.json({ fetchedAt, liveMonths, failedMonths, sessions: rows }, { headers: { "cache-control": "public, max-age=600", "netlify-cdn-cache-control": "public, s-maxage=3600" } })
}
export const config: Config = { path: "/api/events" }
