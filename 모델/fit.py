import pandas as pd,numpy as np,json,datetime as dt,sys
sys.path.insert(0,'/home/claude/k/m'); from events import expand
from sklearn.linear_model import Ridge
EV=json.load(open('/home/claude/k/ev/events_2023_2026.json'))
CLS=['DOME','ARENA','HALL','LAWN','ART','MUSE']
HOL={'2025-01-01','2025-01-27','2025-01-28','2025-01-29','2025-01-30','2025-03-03','2025-05-05','2025-05-06','2025-06-03','2025-06-06','2025-08-15','2025-10-03','2025-10-06','2025-10-07','2025-10-08','2025-10-09','2025-12-25'}
def daytype(d): 
    w=d.weekday(); 
    if d.isoformat() in HOL or w==6: return 'sun'
    if w==5: return 'sat'
    if w==4: return 'fri'
    return 'wk'
def ev_features(dates, mode, offs):
    # mode 'start' or 'end': for each date-hour, count events whose start(end) hour + off == hour
    r=pd.DataFrame(expand(EV,min(dates),max(dates)))
    r=r[~r.long | r.cls.isin(['DOME','ARENA','HALL','LAWN'])]
    F={}
    for c in CLS:
        for o in offs: F[f'{c}_{mode}{o:+d}']={}
    for _,x in r.iterrows():
        if x.cls not in CLS: continue
        base=int(np.floor(x.start if mode=='start' else x.end))
        for o in offs:
            h=base+o; d=dt.date.fromisoformat(x.date)+dt.timedelta(days=h//24); h%=24
            F[f'{x.cls}_{mode}{o:+d}'][(d,h)]=F[f'{x.cls}_{mode}{o:+d}'].get((d,h),0)+1
    return F,r
def design(df,F,extra_cols):
    X=pd.get_dummies(df['dt_h'],prefix='dh').astype(float)
    for c in extra_cols: X[c]=df[c]
    for k,dd in F.items(): X[k]=[dd.get((d,h),0) for d,h in zip(df.date,df.hour)]
    return X
def fit_eval(df,y,F,extra,alpha=1.0,group='date'):
    X=design(df,F,extra); evcols=[c for c in X.columns if '_start' in c or '_end' in c]
    m=Ridge(alpha=alpha).fit(X,y)
    # leave-one-date-out CV on event-affected dates
    evdates=sorted(set(d for k in F for (d,h) in F[k] if (d in set(df.date))))
    errs=[];errs0=[];rows=[]
    Xn=X.copy(); Xn[evcols]=0
    for d in sorted(set(df.date)):
        tr=df.date!=d
        mm=Ridge(alpha=alpha).fit(X[tr],y[tr])
        p=mm.predict(X[~tr]); 
        mm0=Ridge(alpha=alpha).fit(Xn[tr],y[tr]); p0=mm0.predict(Xn[~tr])
        rows.append(dict(date=d,ev=d in evdates,mae=np.mean(np.abs(p-y[~tr])),mae0=np.mean(np.abs(p0-y[~tr])),peak_err=abs(p.max()-y[~tr].max()),peak_err0=abs(p0.max()-y[~tr].max())))
    return m,X,pd.DataFrame(rows)
