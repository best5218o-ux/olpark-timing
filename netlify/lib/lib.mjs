// 올팍 타이밍 — 공연 일정 해석·특징 생성·예보(그래디언트 부스팅 나무) 공용 모듈
// Python 학습 코드(m/events.py, m/model.py)와 같은 규칙을 그대로 옮겼다. 결과 일치는 test_parity로 확인.
const WD = { '월': 0, '화': 1, '수': 2, '목': 3, '금': 4, '토': 5, '일': 6 };
const EN = { MON: 0, TUE: 1, WED: 2, THU: 3, FRI: 4, SAT: 5, SUN: 6 };
export const CLS = ['DOME', 'ARENA', 'HALL', 'LAWN', 'ART'];
const DEFAULT_DUR = { DOME: 150, ARENA: 120, HALL: 120, ART: 80, MUSE: 70, LAWN: 480, ETC: 120 };

export function vclass(p) {
  p = (p || '').replace(/ /g, '');
  const out = [];
  if (p.toUpperCase().includes('DOME') || p.includes('체조')) out.push('DOME');
  if (p.includes('핸드볼') || p.includes('티켓링크')) out.push('ARENA');
  if (p.includes('올림픽홀')) out.push('HALL');
  if (p.includes('우리금융')) out.push('ART');
  if (p.includes('뮤즈')) out.push('MUSE');
  if (p.includes('잔디') || p.includes('수변')) out.push('LAWN');
  return out.length ? out : ['ETC'];
}
function parseDur(s) {
  s = s || '';
  const h = s.match(/(\d+)\s*시간/), m = s.match(/(\d+)\s*분/);
  const v = (h ? +h[1] * 60 : 0) + (m ? +m[1] : 0);
  return v || null;
}
function clean(tm) {
  tm = (tm || '').replace(/（/g, '(').replace(/）/g, ')').replace(/〜/g, '~');
  tm = tm.replace(/20\d\d\s*년\s*/g, '');
  tm = tm.replace(/20\d\d\.\s*/g, '');
  tm = tm.replace(/\d{1,2}\s*월\s*\d{1,2}\s*일?\s*(\([^)]*\))?\s*[~\-–]\s*(\d{1,2}\s*월\s*)?\d{1,2}\s*일?\s*(\([^)]*\))?/g, '');
  tm = tm.replace(/\d{1,2}\.\d{1,2}\.?\s*(\([^)]*\))?\s*[~\-–]\s*(\d{1,2}\.)?\d{1,2}\.?\s*(\([^)]*\))?/g, '');
  tm = tm.replace(/~\s*(오전|오후)?\s*\d{1,2}\s*(:\s*\d{2}|시(\s*\d{1,2}\s*분)?)/g, '');
  return tm;
}
const TIME = /(오전|오후)?\s*(\d{1,2})(?:\s*:\s*(\d{2})(?::\d{2})?\s*(PM|AM|pm|am)?|\s*시\s*(?:(\d{1,2})\s*분|(반))?|\s*(PM|AM|pm|am))/g;
function pyWeekday(d) { return (d.getUTCDay() + 6) % 7; }
export function timesFor(ev, d) {
  const tm = clean(ev.tm);
  const toks = [];
  for (const m of tm.matchAll(/(\d{1,2})\s*월\s*(\d{1,2})\s*일/g)) toks.push([m.index, 'date', [+m[1], +m[2]]]);
  for (const m of tm.matchAll(/(?<![\d:])(\d{1,2})\.(\d{1,2})\.?(?!\d)/g)) {
    const mo = +m[1], da = +m[2];
    if (mo >= 1 && mo <= 12 && da >= 1 && da <= 31) toks.push([m.index, 'date', [mo, da]]);
  }
  for (const m of tm.matchAll(/(?<![월\d.])(\d{1,2})\s*\(\s*(?:[월화수목금토일]|\))/g)) toks.push([m.index, 'dnum', +m[1]]);
  for (const m of tm.matchAll(/(?<![가-힣\d])([월화수목금토일])(?:요일)?(?=\s*[\)\(:,/]|\s*(?:오전|오후|\d)|\s*$)/g)) toks.push([m.index, 'wd', WD[m[1]]]);
  const up = tm.toUpperCase();
  for (const m of up.matchAll(/\b(MON|TUE|WED|THU|FRI|SAT|SUN)\b/g)) toks.push([m.index, 'wd', EN[m[1]]]);
  for (const m of tm.matchAll(/평일/g)) toks.push([m.index, 'grp', 'wkday']);
  for (const m of tm.matchAll(/주말|공휴일/g)) toks.push([m.index, 'grp', 'wkend']);
  for (const m of tm.matchAll(/([월화수목금토일])\s*~\s*([월화수목금토일])/g)) {
    const a = WD[m[1]], b = WD[m[2]];
    for (let v = a; v <= b; v++) toks.push([m.index, 'wd', v]);
  }
  const times = [];
  for (const m of tm.matchAll(TIME)) {
    let [all, ap, h, mi, pm1, mi2, half, pm2] = m;
    h = +h;
    const pm = (pm1 || pm2 || '').toLowerCase();
    if (/^\d+$/.test(all.trim())) continue;
    const mm = +(mi || mi2 || (half ? 30 : 0));
    if ((ap === '오후' || pm === 'pm') && h < 12) h += 12;
    if (h > 24 || mm > 59) continue;
    if (h < 9 && !ap && !pm) h += 12;
    times.push([m.index, h + mm / 60]);
  }
  if (!times.length) return null;
  const allt = [...times.map(([p, v]) => [p, 'T', v]), ...toks];
  allt.sort((x, y) => x[0] - y[0]);
  const res = []; let active = []; let prevT = false;
  for (const [, k, v] of allt) {
    if (k === 'T') { res.push([active.slice(), v]); prevT = true; }
    else { if (prevT) { active = []; prevT = false; } active.push([k, v]); }
  }
  const w = pyWeekday(d), out = [];
  for (const [lab, v] of res) {
    if (!lab.length) { out.push(v); continue; }
    const hasdate = lab.some(([k]) => k === 'date' || k === 'dnum');
    let ok = false;
    for (const [k, val] of lab) {
      if (k === 'date' && d.getUTCMonth() + 1 === val[0] && d.getUTCDate() === val[1]) ok = true;
      if (k === 'dnum' && d.getUTCDate() === val) ok = true;
      if (k === 'wd' && w === val && !hasdate) ok = true;
      if (k === 'grp' && ((val === 'wkday' && w < 5) || (val === 'wkend' && w >= 5))) ok = true;
    }
    if (ok) out.push(v);
  }
  const labeled = res.filter(([lab]) => lab.length);
  if (labeled.length && !out.length) return [];
  return [...new Set(out)].sort((a, b) => a - b);
}
function maxPrice(s) {
  const v = [...(s || '').matchAll(/(\d{1,3}(?:,\d{3})+|\d{4,6})\s*원/g)].map(m => +m[1].replace(/,/g, '')).filter(x => x >= 5000 && x <= 500000);
  return v.length ? Math.max(...v) : null;
}
const iso = d => d.toISOString().slice(0, 10);
const D = s => new Date(s + 'T00:00:00Z');
// 공연 → 회차(날짜·시작·종료·공연장·가격·기간)
export function expand(events, start, end) {
  const rows = [];
  for (const e of events) {
    const b = D(e.beginDt), en = D(e.endDt);
    const long = (en - b) / 864e5 > 45;
    let d = new Date(Math.max(b, D(start)));
    const last = new Date(Math.min(en, D(end)));
    while (d <= last) {
      let ts = timesFor(e, d);
      const cls = vclass(e.plc), dur = parseDur(e.ndTm) || DEFAULT_DUR[cls[0]];
      let imputed = false;
      if (ts && ts.length === 0) { d = new Date(+d + 864e5); continue; }
      if (ts === null) { ts = [pyWeekday(d) >= 5 ? 18.0 : 19.5]; imputed = true; }
      for (const c of cls) for (const t of ts)
        rows.push({ date: iso(d), start: t, end: t + dur / 60, cls: c, title: e.title, evtSeq: e.evtSeq, long, imputed, price: maxPrice(e.tktPrc), run: Math.round((en - b) / 864e5) + 1, plc: e.plc, link: e.evtLink || '' });
      d = new Date(+d + 864e5);
    }
  }
  return rows.filter(r => !r.long);
}
// ---------- 특징 ----------
export function dtype(dstr, hol) {
  const d = D(dstr), w = pyWeekday(d);
  if (hol.has(dstr) || w === 6) return 3;
  return w === 5 ? 2 : (w === 4 ? 1 : 0);
}
export function features(dstr, hours, rows, meta, rainMm, hol, useMonth) {
  const d = D(dstr), month = d.getUTCMonth() + 1;
  const next = iso(new Date(+d + 864e5));
  const dt = dtype(dstr, hol), nh = dtype(next, hol) >= 2 ? 1 : 0;
  const g = {};
  for (const r of rows) if (r.date === dstr) (g[r.cls] = g[r.cls] || []).push(r);
  return hours.map(h => {
    const f = { hour: h, dtype: dt, month, rain: (h >= 16 && h <= 22) ? rainMm : 0, temp: meta.clim[`${month}|${h}`], nextday_hol: nh };
    const hh = h + 0.5;
    for (const c of CLS) {
      const L = g[c] || [];
      let s = 99, e = 99;
      for (const r of L) { const a = hh - r.start, b = hh - r.end; if (Math.abs(a) < Math.abs(s)) s = a; if (Math.abs(b) < Math.abs(e)) e = b; }
      f[c + '_so'] = Math.abs(s) <= 8 ? s : 99; f[c + '_eo'] = Math.abs(e) <= 6 ? e : 99;
      f[c + '_n'] = L.length; f[c + '_price'] = L.reduce((m, r) => Math.max(m, r.price || 0), 0); f[c + '_run'] = L.reduce((m, r) => Math.max(m, r.run), 0);
    }
    return f;
  });
}
export function strip(f) { // 공연 정보만 비운 같은 날(평소 기준)
  const o = { ...f };
  for (const c of CLS) { o[c + '_so'] = 99; o[c + '_eo'] = 99; o[c + '_n'] = 0; o[c + '_price'] = 0; o[c + '_run'] = 0; }
  return o;
}
export function predict(m, f) {
  const x = m.cols.map(c => f[c]);
  let s = m.base;
  for (const [fi, th, le, ri, leaf, val, mgl] of m.trees) {
    let n = 0;
    while (!leaf[n]) { const v = x[fi[n]]; n = (v === null || v === undefined || Number.isNaN(v)) ? (mgl[n] ? le[n] : ri[n]) : (v <= th[n] ? le[n] : ri[n]); }
    s += val[n];
  }
  return s;
}
const HOURS = Array.from({ length: 18 }, (_, i) => i + 6);
export function forecastDay(model, events, dstr, rainMm) {
  const meta = model._meta, hol = new Set(meta.holidays);
  const rows = expand(events, dstr, dstr);
  const out = { date: dstr, dtype: dtype(dstr, hol), holiday: hol.has(dstr), hours: HOURS, events: rows.filter(r => CLS.includes(r.cls)).map(r => ({ title: r.title, cls: r.cls, start: r.start, end: r.end, imputed: r.imputed, link: r.link })), series: {} };
  for (const k of ['l9_off', 'l9_on', 'l58_off', 'l58_on', 'pk_IN', 'pk_OUT']) {
    const usem = !k.startsWith('pk');
    const F = features(dstr, HOURS, rows, meta, rainMm, hol, usem);
    const s = usem ? 1 : meta.seasonal[String(D(dstr).getUTCMonth() + 1)];
    const mean = [], base = [], q80 = [];
    for (const f of F) {
      const p = predict(model[k].mean, f), p0 = predict(model[k].mean, strip(f)), q = predict(model[k].q80, f);
      const adj = usem ? 0 : p0 * s - p0; // 주차: 평소 몫만 계절 보정
      const mv = Math.max(0, Math.round(p + adj)); mean.push(mv); base.push(Math.max(0, Math.round(p0 + adj))); q80.push(Math.max(mv, Math.round(q + adj))); // 붐빌 때 값은 예보보다 작게 두지 않는다
    }
    out.series[k] = { mean, base, q80 };
  }
  return out;
}
