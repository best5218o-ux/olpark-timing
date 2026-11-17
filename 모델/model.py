import sys,json,datetime as dt; sys.path.insert(0,'/home/claude/k/m')
import pandas as pd,numpy as np,holidays
from events import expand
from sklearn.ensemble import HistGradientBoostingRegressor as HGB
EV=json.load(open('/home/claude/k/ev/events_2023_2026.json'))
KR=holidays.KR(years=range(2023,2030))
CLS=['DOME','ARENA','HALL','LAWN','ART']
WX=pd.DataFrame(json.load(open('/home/claude/k/wx_all.json'))['hourly']); WX['time']=pd.to_datetime(WX.time)
WX['date']=WX.time.dt.date; WX['hour']=WX.time.dt.hour
def dtype(d):
    if d in KR or d.weekday()==6: return 3
    return {5:2,4:1}.get(d.weekday(),0)
def events_rows(d0,d1):
    r=pd.DataFrame(expand(EV,d0,d1)); return r[~r.long]
def frame(df):
    df=df.merge(WX[['date','hour','precipitation','temperature_2m']],on=['date','hour'],how='left')
    df['dtype']=[dtype(d) for d in df.date]; df['month']=[d.month for d in df.date]
    df['rain']=df.precipitation.fillna(0); df['temp']=df.temperature_2m
    df['nextday_hol']=[int(dtype(d+dt.timedelta(days=1))>=2) for d in df.date]
    return df
def ev_feats(df,r):
    g={}
    for _,x in r.iterrows(): g.setdefault((x.date,x.cls),[]).append((x.start,x.end,x.price if x.price==x.price and x.price else 0,x.run))
    F={}
    for c in CLS:
        so=[];eo=[];n=[];pr=[];rn=[]
        for d,h in zip(df.date,df.hour):
            L=g.get((d.isoformat(),c),[]); hh=h+0.5
            s=min([hh-a for a,b,p,u in L],key=abs,default=99); e=min([hh-b for a,b,p,u in L],key=abs,default=99)
            so.append(s if abs(s)<=8 else 99); eo.append(e if abs(e)<=6 else 99); n.append(len(L))
            pr.append(max([p for a,b,p,u in L],default=0)); rn.append(max([u for a,b,p,u in L],default=0))
        F[f'{c}_so']=so;F[f'{c}_eo']=eo;F[f'{c}_n']=n;F[f'{c}_price']=pr;F[f'{c}_run']=rn
    return pd.DataFrame(F,index=df.index)
BASE=['hour','dtype','month','rain','temp','nextday_hol']
def X_of(df,r,use_ev=True):
    X=df[BASE].copy()
    return pd.concat([X,ev_feats(df,r)],axis=1) if use_ev else X
def mk(q=None):
    kw=dict(max_iter=300,learning_rate=0.05,max_leaf_nodes=31,random_state=0)
    if q: kw.update(loss="quantile",quantile=q)
    return HGB(**kw)
def bigdays(r): return set(dt.date.fromisoformat(x) for x in r[r.cls.isin(['DOME','ARENA','HALL','LAWN'])].date)
def metrics(df,y,p,p0,days):
    bm=df.date.isin(days).values
    D=pd.DataFrame({'d':df.date,'y':y,'p':p,'p0':p0})[bm].groupby('d').max()
    return dict(n_days=int(len(D)),mae=float(np.abs(p-y)[bm].mean()),mae0=float(np.abs(p0-y)[bm].mean()),
                peak=float((D.p-D.y).abs().mean()),peak0=float((D.p0-D.y).abs().mean()),
                mape_peak=float(((D.p-D.y).abs()/D.y).mean()),mape_peak0=float(((D.p0-D.y).abs()/D.y).mean()))
