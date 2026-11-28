// 정적 예보 생성: 기관 누리집 공연 일정 → 60일 예보 JSON (Netlify 빌드·GitHub Actions 어디서나 실행)
import fs from 'fs'; import path from 'path';
import { model, getEvents, todayKST } from '../netlify/lib/shared.mjs';
import { forecastDay, expand, dtype, CLS } from '../netlify/lib/lib.mjs';
const OUT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../public/data');
fs.mkdirSync(path.join(OUT, 'fc'), { recursive: true });
const { events, liveMonths, failedMonths, fetchedAt } = await getEvents();
const from = process.env.FROM || todayKST(); const N = +(process.env.DAYS || 60);
const hol = new Set(model._meta.holidays); const days = [];
for (const f of fs.readdirSync(path.join(OUT, 'fc'))) if (f.slice(0, 10) >= from) fs.unlinkSync(path.join(OUT, 'fc', f)); // 지난 날짜 예보는 보관(그날 실제로 냈던 예보를 나중에도 확인)
for (let i = 0; i < N; i++) {
  const ds = new Date(Date.parse(from + 'T00:00:00Z') + i * 864e5).toISOString().slice(0, 10);
  const clear = forecastDay(model, events, ds, 0), rain = forecastDay(model, events, ds, 3);
  fs.writeFileSync(path.join(OUT, 'fc', ds + '.json'), JSON.stringify({ ...clear, series: { clear: clear.series, rain: rain.series } }));
  const big = clear.events.filter(r => ['DOME', 'ARENA', 'HALL', 'LAWN'].includes(r.cls));
  const item = { date: ds, dtype: clear.dtype, holiday: clear.holiday, events: clear.events.map(r => ({ title: r.title, cls: r.cls, start: r.start, end: r.end })) };
  if (big.length || clear.dtype >= 2) {
    const f = clear.series, lastEnd = big.length ? Math.max(...big.map(r => r.end)) : 0, firstEnd = big.length ? Math.min(...big.map(r => r.end)) : 0, fi = big.length ? Math.max(0, Math.floor(firstEnd) - 6 - 1) : 0; // 가장 먼저 끝나는 공연 종료 1시간 전부터 퇴장 피크를 찾는다
    const pk = (s, a = 0) => { let i = a; for (let k = a; k < 18; k++) if (s.mean[k] > s.mean[i]) i = k; return { h: i + 6, v: s.mean[i], q: s.q80[i], base: s.base[i] }; };
    const si = big.length ? Math.max(0, Math.floor(Math.min(...big.map(r => r.start))) - 6 - 6) : 0; // 도착 몰림은 첫 공연 시작 6시간 전부터 찾는다
    item.peaks = { pk_IN: pk(f.pk_IN, si), pk_OUT: pk(f.pk_OUT, fi), l9_on: pk(f.l9_on, fi), l58_on: pk(f.l58_on, fi) };
    if (f.lp) item.peaks.lp = pk(f.lp);
    if (f.spd) { let i = 0; for (let k = 0; k < 18; k++) if (f.spd.mean[k] < f.spd.mean[i]) i = k; item.peaks.spd = { h: i + 6, v: f.spd.mean[i], q: f.spd.q80[i], base: f.spd.base[i] }; }
  }
  days.push(item);
}
fs.writeFileSync(path.join(OUT, 'summary.json'), JSON.stringify({ meta: { model: model._meta.generated, train: model._meta.train, eventsFetchedAt: fetchedAt, liveMonths, failedMonths, built: new Date(Date.now() + 9 * 3600e3).toISOString().slice(0, 16) }, from, days }));
// 실시간 표시값 기록(빌드할 때마다 1점 추가)
try {
  const html = await (await fetch('https://www.ksponco.or.kr/online/main/parking.do', { headers: { 'user-agent': 'olpark-timing/1.0 (public data contest)' } })).text();
  const m = html.match(/실시간 주차대수[^<]*<strong[^>]*>\s*([\d,]+)\s*대\s*<\/strong>\s*주차 중\s*\/\s*([\d,]+)\s*대/);
  if (m) { const p = path.join(OUT, 'live_log.json'); const log = fs.existsSync(p) ? JSON.parse(fs.readFileSync(p)) : [];
    log.push([new Date(Date.now() + 9 * 3600e3).toISOString().slice(0, 16), +m[1].replace(/,/g, ''), +m[2].replace(/,/g, '')]); fs.writeFileSync(p, JSON.stringify(log.slice(-3000))); }
} catch (e) { console.log('live log skip', String(e)); }
console.log('built', N, 'days from', from, 'events', events.length, 'live months', liveMonths, 'fail', failedMonths);
