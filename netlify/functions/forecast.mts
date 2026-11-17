import type { Config } from "@netlify/functions"
import { model, getEvents, todayKST } from "../lib/shared.mjs"
import { forecastDay, expand, dtype, CLS } from "../lib/lib.mjs"

// /api/forecast?d=YYYY-MM-DD  → 그날 시간대별 예보(맑음·저녁 비), 공연 목록
// /api/forecast?from=YYYY-MM-DD&days=N → N일 요약(운영자 표)
export default async (req: Request) => {
  const u = new URL(req.url)
  const { events, liveMonths, failedMonths, fetchedAt } = await getEvents()
  const meta = { model: model._meta.generated, train: model._meta.train, eventsFetchedAt: fetchedAt, liveMonths, failedMonths }
  const d = u.searchParams.get("d")
  const headers = { "cache-control": "public, max-age=600", "netlify-cdn-cache-control": "public, s-maxage=3600, stale-while-revalidate=86400" }
  if (d) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(d)) return Response.json({ error: "날짜 형식은 YYYY-MM-DD" }, { status: 400 })
    const clear = forecastDay(model, events, d, 0), rain = forecastDay(model, events, d, 3)
    return Response.json({ meta, ...clear, series: { clear: clear.series, rain: rain.series } }, { headers })
  }
  const from = u.searchParams.get("from") || todayKST()
  const n = Math.min(+(u.searchParams.get("days") || 60), 92)
  const hol = new Set(model._meta.holidays)
  const days = []
  for (let i = 0; i < n; i++) {
    const ds = new Date(Date.parse(from + "T00:00:00Z") + i * 864e5).toISOString().slice(0, 10)
    const rows = expand(events, ds, ds).filter(r => CLS.includes(r.cls))
    const big = rows.filter(r => ["DOME", "ARENA", "HALL", "LAWN"].includes(r.cls))
    const dt = dtype(ds, hol)
    const item: any = { date: ds, dtype: dt, holiday: hol.has(ds), events: rows.map(r => ({ title: r.title, cls: r.cls, start: r.start, end: r.end })) }
    if (big.length || dt >= 2) {
      const f = forecastDay(model, events, ds, 0).series
      const lastEnd = big.length ? Math.max(...big.map(r => r.end)) : 0
      const from_i = big.length ? Math.max(0, Math.floor(Math.min(...big.map(r => r.end))) - 6 - 1) : 0
      const pk = (s: any, a = 0) => { let i = a; for (let k = a; k < 18; k++) if (s.mean[k] > s.mean[i]) i = k; return { h: i + 6, v: s.mean[i], q: s.q80[i], base: s.base[i] } }
      item.peaks = { pk_IN: pk(f.pk_IN), pk_OUT: pk(f.pk_OUT, from_i), l9_on: pk(f.l9_on, from_i), l58_on: pk(f.l58_on, from_i) }
    }
    days.push(item)
  }
  return Response.json({ meta, from, days }, { headers })
}
export const config: Config = { path: "/api/forecast" }
