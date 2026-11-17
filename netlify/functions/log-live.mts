import type { Config } from "@netlify/functions"
import { getStore } from "@netlify/blobs"
// 15분마다 올림픽공원 누리집 실시간 주차 표시값을 기록한다(기관 계수기의 야간 잔류값 확인용).
export default async () => {
  const kst = new Date(Date.now() + 9 * 3600e3).toISOString().slice(0, 16)
  try {
    const html = await (await fetch("https://www.ksponco.or.kr/online/main/parking.do", { headers: { "user-agent": "olpark-timing/1.0 (public data contest)" } })).text()
    const m = html.match(/실시간 주차대수[^<]*<strong[^>]*>\s*([\d,]+)\s*대\s*<\/strong>\s*주차 중\s*\/\s*([\d,]+)\s*대/)
    if (!m) return
    const store = getStore("live-parking")
    const day = kst.slice(0, 10)
    const prev = (await store.get(day, { type: "json" })) as any[] || []
    prev.push([kst, Number(m[1].replace(/,/g, "")), Number(m[2].replace(/,/g, ""))])
    await store.setJSON(day, prev)
  } catch (e) { console.log("log-live fail", String(e)) }
}
// 15분마다(UTC 기준 cron, 한국시간과 무관하게 15분 간격)
export const config: Config = { schedule: "*/15 * * * *" }
