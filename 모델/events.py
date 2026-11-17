import re,json,datetime as dt
WD={'월':0,'화':1,'수':2,'목':3,'금':4,'토':5,'일':6}
def vclass(p):
    p=p.replace(' ','')
    out=[]
    if 'DOME' in p.upper() or '체조' in p: out.append('DOME')
    if '핸드볼' in p or '티켓링크' in p: out.append('ARENA')
    if '올림픽홀' in p: out.append('HALL')
    if '우리금융' in p: out.append('ART')
    if '뮤즈' in p: out.append('MUSE')
    if '잔디' in p or '수변' in p: out.append('LAWN')
    return out or ['ETC']
TIME=re.compile(r'(오전|오후)?\s*(\d{1,2})\s*(?::\s*(\d{2})|시\s*(?:(\d{1,2})\s*분|반)?|\s*(PM|AM|pm|am))')
def parse_dur(s):
    s=s or ''
    h=re.search(r'(\d+)\s*시간',s); m=re.search(r'(\d+)\s*분',s)
    v=(int(h.group(1))*60 if h else 0)+(int(m.group(1)) if m else 0)
    return v or None
EN={'MON':0,'TUE':1,'WED':2,'THU':3,'FRI':4,'SAT':5,'SUN':6}
TIME=re.compile(r'(오전|오후)?\s*(\d{1,2})(?:\s*:\s*(\d{2})(?::\d{2})?\s*(PM|AM|pm|am)?|\s*시\s*(?:(\d{1,2})\s*분|(반))?|\s*(PM|AM|pm|am))')
def clean(tm):
    tm=(tm or '').replace('（','(').replace('）',')').replace('〜','~')
    tm=re.sub(r'20\d\d\s*년\s*','',tm)
    tm=re.sub(r'20\d\d\.\s*','',tm)
    # date ranges -> remove
    tm=re.sub(r'\d{1,2}\s*월\s*\d{1,2}\s*일?\s*(\([^)]*\))?\s*[~\-–]\s*(\d{1,2}\s*월\s*)?\d{1,2}\s*일?\s*(\([^)]*\))?','',tm)
    tm=re.sub(r'\d{1,2}\.\d{1,2}\.?\s*(\([^)]*\))?\s*[~\-–]\s*(\d{1,2}\.)?\d{1,2}\.?\s*(\([^)]*\))?','',tm)
    tm=re.sub(r'~\s*(오전|오후)?\s*\d{1,2}\s*(:\s*\d{2}|시(\s*\d{1,2}\s*분)?)','',tm)
    return tm
def times_for(ev,d):
    tm=clean(ev.get('tm'))
    toks=[]
    for m in re.finditer(r'(\d{1,2})\s*월\s*(\d{1,2})\s*일',tm): toks.append((m.start(),'date',(int(m.group(1)),int(m.group(2)))))
    for m in re.finditer(r'(?<![\d:])(\d{1,2})\.(\d{1,2})\.?(?!\d)',tm):
        mo,da=int(m.group(1)),int(m.group(2))
        if 1<=mo<=12 and 1<=da<=31: toks.append((m.start(),'date',(mo,da)))
    for m in re.finditer(r'(?<![월\d.])(\d{1,2})\s*\(\s*(?:[월화수목금토일]|\))',tm): toks.append((m.start(),'dnum',int(m.group(1))))
    for m in re.finditer(r'(?<![가-힣\d])([월화수목금토일])(?:요일)?(?=\s*[\)\(:,/]|\s*(?:오전|오후|\d)|\s*$)',tm):
        toks.append((m.start(),'wd',WD[m.group(1)]))
    for m in re.finditer(r'\b(MON|TUE|WED|THU|FRI|SAT|SUN)\b',tm.upper()): toks.append((m.start(),'wd',EN[m.group(1)]))
    for m in re.finditer(r'평일',tm): toks.append((m.start(),'grp','wkday'))
    for m in re.finditer(r'주말|공휴일',tm): toks.append((m.start(),'grp','wkend'))
    for m in re.finditer(r'([월화수목금토일])\s*~\s*([월화수목금토일])',tm):
        a,b=WD[m.group(1)],WD[m.group(2)]
        for v in range(a,b+1): toks.append((m.start(),'wd',v))
    times=[]
    for m in TIME.finditer(tm):
        ap,h,mi,pm1,mi2,half,pm2=m.groups(); h=int(h)
        pm=(pm1 or pm2 or '').lower()
        if m.group(0).strip().isdigit(): continue
        mi=int(mi or mi2 or (30 if half else 0))
        if (ap=='오후' or pm=='pm') and h<12: h+=12
        if h>24 or mi>59: continue
        if h<9 and not ap and not pm: h+=12
        times.append((m.start(),h+mi/60))
    if not times: return None
    allt=sorted([(p,'T',v) for p,v in times]+toks,key=lambda x:x[0])
    res=[]; active=set(); prevT=False
    for p,k,v in allt:
        if k=='T': res.append((frozenset(active),v)); prevT=True
        else:
            if prevT: active=set(); prevT=False
            active.add((k,v))
    w=d.weekday(); out=[]
    for lab,v in res:
        if not lab: out.append(v); continue
        hasdate=any(k in('date','dnum') for k,_ in lab)
        ok=False
        for k,val in lab:
            if k=='date' and (d.month,d.day)==val: ok=True
            if k=='dnum' and d.day==val: ok=True
            if k=='wd' and w==val and not hasdate: ok=True
            if k=='grp' and ((val=='wkday' and w<5) or (val=='wkend' and w>=5)): ok=True
        if ok: out.append(v)
    labeled=[v for lab,v in res if lab]
    if labeled and not out: return []   # labeled but no show this date
    return sorted(set(out))
def maxprice(s):
    v=[int(x.replace(',','')) for x in re.findall(r'(\d{1,3}(?:,\d{3})+|\d{4,6})\s*원',s or '')]
    v=[x for x in v if 5000<=x<=500000]
    return max(v) if v else None
DEFAULT_DUR={'DOME':150,'ARENA':120,'HALL':120,'ART':80,'MUSE':70,'LAWN':480,'ETC':120}
def expand(events,start,end):
    rows=[]
    for e in events:
        b=dt.date.fromisoformat(e['beginDt']); en=dt.date.fromisoformat(e['endDt'])
        if (en-b).days>45: long=True
        else: long=False
        d=max(b,start)
        while d<=min(en,end):
            ts=times_for(e,d)
            cls=vclass(e['plc'])
            dur=parse_dur(e.get('ndTm')) or DEFAULT_DUR[cls[0]]
            imputed=False
            if ts==[]: d+=dt.timedelta(days=1); continue
            if ts is None:
                ts=[18.0 if d.weekday()>=5 else 19.5]; imputed=True
            for c in cls:
                for t in ts:
                    rows.append(dict(date=d.isoformat(),start=t,end=t+dur/60,cls=c,title=e['title'],evtSeq=e['evtSeq'],long=long,imputed=imputed,tm=e.get('tm'),price=maxprice(e.get('tktPrc')),run=(en-b).days+1))
            d+=dt.timedelta(days=1)
    return rows
if __name__=='__main__':
    ev=json.load(open('/home/claude/k/ev/events_2023_2026.json'))
    import pandas as pd
    r=pd.DataFrame(expand(ev,dt.date(2024,7,1),dt.date(2024,7,31)))
    print(r[['date','start','end','cls','title','imputed']].to_string())
