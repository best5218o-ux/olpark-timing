import sys; sys.path.insert(0,'/home/claude/k/m')
from model import *
from sklearn.ensemble import HistGradientBoostingClassifier as HGC
OUT='/home/claude/k/app/data/'
D0,D1=dt.date(2026,11,16),dt.date(2026,12,31)
fut=pd.DataFrame([(D0+dt.timedelta(days=i),h) for i in range((D1-D0).days+1) for h in range(6,24)],columns=['date','hour'])
# climatology temp by month-hour
clim=WX[WX.time.dt.year<=2025].groupby([WX.time.dt.month,WX.time.dt.hour]).temperature_2m.mean()
def futframe(rainmm):
    f=fut.copy(); f['dtype']=[dtype(d) for d in f.date]; f['month']=[d.month for d in f.date]
    f['temp']=[clim[(d.month,h)] for d,h in zip(f.date,f.hour)]
    f['rain']=[rainmm if 16<=h<=22 else 0.0 for h in f.hour]
    f['nextday_hol']=[int(dtype(d+dt.timedelta(days=1))>=2) for d in f.date]
    return f
rF=events_rows(D0,D1)
res={}
# ---- 9호선
M=pd.read_csv('/home/claude/k/m/l9_hourly_2023_2026.csv'); M['date']=pd.to_datetime(M['날짜']).dt.date
M=M[M.hour.between(6,23)].dropna().reset_index(drop=True); dfl9=frame(M[['date','hour','순승차','순하차']].copy())
r_l9=events_rows(dt.date(2023,1,1),dt.date(2026,7,31))
Xl9=X_of(dfl9,r_l9); Xl90=X_of(dfl9,r_l9,False)
# ---- 5·8호선 2025
P=pd.read_csv('/home/claude/k/m/subway_hourly_2025.csv'); P['date']=pd.to_datetime(P.date).dt.date
P=P[['date','hour','하차','승차']]; dfl58=frame(P.copy()); r_58=events_rows(dt.date(2025,1,1),dt.date(2025,12,31))
X58=X_of(dfl58,r_58); X580=X_of(dfl58,r_58,False)
# ---- parking July 2024
pk=pd.read_csv('/home/claude/k/m/park_hourly_202407_pred.csv'); pk['date']=pd.to_datetime(pk.date).dt.date
r_pk=events_rows(dt.date(2024,7,1),dt.date(2024,7,31))
Xpk=X_of(pk,r_pk).drop(columns='month'); Xpk0=X_of(pk,r_pk,False).drop(columns='month')
mon=pd.read_csv('/home/claude/k/d/15131671.u.csv'); mon=mon[mon.주차장소=='올림픽공원']; mon['m']=mon.월.str[:2].astype(int)
mi=mon.groupby('m').주차대수.mean(); SEAS=(mi/mi[7]).to_dict()
models={}
for key,(X,X0,df,col) in {'l9_off':(Xl9,Xl90,dfl9,'순하차'),'l9_on':(Xl9,Xl90,dfl9,'순승차'),'l58_off':(X58,X580,dfl58,'하차'),'l58_on':(X58,X580,dfl58,'승차')}.items():
    y=df[col].values.astype(float); models[key]=(mk().fit(X,y),mk().fit(X0,y),False)
for key in ['IN','OUT','OCC']:
    y=pk[key].values.astype(float)
    models['pk_'+key]=(HGB(max_iter=300,learning_rate=0.05,min_samples_leaf=10,random_state=0).fit(Xpk,y),HGB(max_iter=300,learning_rate=0.05,min_samples_leaf=10,random_state=0).fit(Xpk0,y),True)
out={}
for sc,rain in [('clear',0.0),('rain',3.0)]:
    f=futframe(rain); Xf=X_of(f,rF); Xf0=X_of(f,rF,False)
    for key,(m,m0,ispk) in models.items():
        A=Xf.drop(columns='month') if ispk else Xf; B=Xf0.drop(columns='month') if ispk else Xf0
        p=m.predict(A)
        Acf=A.copy()
        for c in Acf.columns:
            if c.endswith(('_so','_eo')): Acf[c]=99
            elif c.endswith(('_n','_price','_run')): Acf[c]=0
        p0=m.predict(Acf)
        if ispk:
            s=np.array([SEAS[d.month] for d in f.date]); p=p0*s+(p-p0); p0=p0*s
        f[key]=np.clip(p,0,None).round(); f[key+'_base']=np.clip(p0,0,None).round()
    out[sc]=f
# daily full-risk classifier (2025 notices)
Dd=pd.read_csv('/home/claude/k/m/fullrisk_daily_2025.csv'); feat=[c for c in Dd.columns if c not in('date','y')]
clf=HGC(max_iter=200,learning_rate=0.05,min_samples_leaf=8,random_state=0).fit(Dd[feat],Dd.y)
W=WX.groupby('date').agg(rain=('precipitation','sum'),tmax=('temperature_2m','max'))
climmax=WX[WX.time.dt.year<=2025].groupby(WX.time.dt.month).temperature_2m.apply(lambda s:s.groupby(WX.loc[s.index,'date']).max().mean())
risk={}
for i in range((D1-D0).days+1):
    d=D0+dt.timedelta(days=i); e=rF[rF.date==d.isoformat()]
    f=dict(dtype=dtype(d),month=d.month,rain=0.0,tmax=climmax[d.month])
    for cl in CLS:
        ee=e[e.cls==cl]; f[cl+'_n']=len(ee); f[cl+'_minstart']=ee.start.min() if len(ee) else 99; f[cl+'_price']=ee.price.max() if len(ee) and ee.price.notna().any() else 0
    risk[d.isoformat()]=float(clf.predict_proba(pd.DataFrame([f])[feat])[:,1][0])
# pack
days={}
for d in sorted(set(fut.date)):
    k=d.isoformat(); dd={}
    for sc,f in out.items():
        g=f[f.date==d]
        dd[sc]={c:g[c].astype(int).tolist() for c in g.columns if c.startswith(('l9_','l58_','pk_'))}
    e=rF[rF.date==k]
    dd['events']=[dict(title=x.title,cls=x.cls,start=round(x.start,2),end=round(x.end,2),evtSeq=int(x.evtSeq)) for _,x in e.sort_values('start').iterrows() if x.cls!='MUSE']
    dd['dtype']=dtype(d); dd['risk']=round(risk[k],3); dd['holiday']=KR.get(d) or ''
    days[k]=dd
json.dump(dict(generated=dt.datetime.now().isoformat(timespec='minutes'),hours=list(range(6,24)),seasonal_index=SEAS,days=days),open(OUT+'forecast_2026-11-16_2026-12-31.json','w'),ensure_ascii=False)
print('ok',len(days)); 
k='2026-11-21'; print(days[k]['events']); print(days[k]['clear']['pk_OCC']); print(days[k]['clear']['pk_OCC_base']); print(days[k]['clear']['l9_on']); print(days[k]['clear']['l9_on_base']); print(days[k]['risk'])
