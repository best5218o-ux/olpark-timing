import type { Config } from "@netlify/functions"

// 올림픽공원 누리집 「주차장 예상 이용률」 화면에 공개된 실시간 주차대수(동2·남2·북2문)를 읽어 온다.
// 공공데이터포털 인증키(DATA_GO_KR_KEY)가 등록되면 같은 자리에서 오픈API로 바꾼다.
const SRC = "https://www.ksponco.or.kr/online/main/parking.do"

export default async (req: Request) => {
  const now = new Date(Date.now() + 9 * 3600 * 1000).toISOString().slice(0, 19)
  try {
    const r = await fetch(SRC, { headers: { "user-agent": "olpark-timing/1.0 (public data contest)" } })
    const html = await r.text()
    const m = html.match(/실시간 주차대수[^<]*<strong[^>]*>\s*([\d,]+)\s*대\s*<\/strong>\s*주차 중\s*\/\s*([\d,]+)\s*대/)
    if (!m) throw new Error("pattern")
    const parked = Number(m[1].replace(/,/g, "")), capacity = Number(m[2].replace(/,/g, ""))
    return Response.json(
      { parked, capacity, fetchedAt: now, source: "올림픽공원 누리집 공개값", note: "기관 설명: 장기주차 차량은 출차일이 비어 실제 대수와 다를 수 있음" },
      { headers: { "cache-control": "public, max-age=60" } }
    )
  } catch (e) {
    return Response.json({ parked: null, capacity: 2200, fetchedAt: now, source: "연결 대기" }, { status: 200 })
  }
}

export const config: Config = { path: "/api/live" }
