import model from './model.json' with { type: 'json' };
import snapshot from './events_snapshot.json' with { type: 'json' };
export { model };
const SRC = 'https://www.ksponco.or.kr/olympicpark/eventInfo/eventInfoListAjax.es';
const kst = () => new Date(Date.now() + 9 * 3600e3);
// 기관 누리집 공연 일정(공공데이터 3037877과 같은 원천)을 월별로 받아 합친다. 실패한 달은 내장 사본으로 채운다.
export async function getEvents(monthsBack = 1, monthsAhead = 4) {
  const now = kst(); const byId = new Map(); let live = 0, fail = 0;
  for (const e of snapshot) byId.set(e.evtSeq, e);
  const jobs = [];
  for (let k = -monthsBack; k <= monthsAhead; k++) {
    const d = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() + k, 1));
    const ym = `${d.getUTCFullYear()}${String(d.getUTCMonth() + 1).padStart(2, '0')}`;
    jobs.push(fetch(SRC, { method: 'POST', headers: { 'content-type': 'application/json;charset=UTF-8', 'user-agent': 'olpark-timing/1.0 (public data contest)' }, body: JSON.stringify({ nowYM: ym, plcCd: '' }) })
      .then(r => r.json()).then(j => { live++; for (const part of j) for (const e of part) { delete e.content; byId.set(e.evtSeq, e); } }).catch(() => { fail++; }));
  }
  await Promise.all(jobs);
  return { events: [...byId.values()], liveMonths: live, failedMonths: fail, fetchedAt: now.toISOString().slice(0, 16) };
}
export const todayKST = () => kst().toISOString().slice(0, 10);
