import sys; sys.path.insert(0,'/home/claude/k/m')
from model import *
V={}
M=pd.read_csv('m/l9_hourly_2023_2026.csv'); M['date']=pd.to_datetime(M['날짜']).dt.date
M=M[M.hour.between(6,23)].dropna().reset_index(drop=True); df=frame(M[['date','hour','순승차','순하차']].copy())
r=events_rows(dt.date(2023,1,1),dt.date(2026,7,31)); X=X_of(df,r); X0=X_of(df,r,False); tr=(df.date<dt.date(2026,1,1)).values
te=df[~tr].copy()
for col in ['순승차','순하차']:
    y=df[col].values.astype(float)
    te[col+'_p']=mk().fit(X[tr],y[tr]).predict(X[~tr]); te[col+'_p0']=mk().fit(X0[tr],y[tr]).predict(X0[~tr]); te[col+'_q']=mk(0.8).fit(X[tr],y[tr]).predict(X[~tr])
NM={'DOME':'KSPO DOME','ARENA':'티켓링크 라이브 아레나','HALL':'올림픽홀','LAWN':'88잔디마당','ART':'우리금융아트홀'}
for d in ['2026-06-20','2026-07-04','2026-01-03','2026-03-08']:
    g=te[te.date==dt.date.fromisoformat(d)]; ev=r[(r.date==d)&r.cls.isin(list(NM))].drop_duplicates(['title','cls','start'])
    V['l9_'+d]=dict(events=[(NM[x.cls]+' '+x.title,x.start,x.end,bool(x.imputed)) for _,x in ev.iterrows()],**{c:g[c].round().astype(int).tolist() for c in ['순승차','순승차_p','순승차_p0','순승차_q','순하차','순하차_p','순하차_p0','순하차_q']})
pk=pd.read_csv('m/park_hourly_202407_pred.csv'); pk['date']=pd.to_datetime(pk.date).dt.date
rp=events_rows(dt.date(2024,7,1),dt.date(2024,7,31)); Xp=X_of(pk,rp).drop(columns='month')
groups=[[dt.date(2024,7,6),dt.date(2024,7,7)],[dt.date(2024,7,12),dt.date(2024,7,13),dt.date(2024,7,14)],[dt.date(2024,7,20),dt.date(2024,7,21)],[dt.date(2024,7,27),dt.date(2024,7,28)]]
small=lambda: HGB(max_iter=300,learning_rate=0.05,min_samples_leaf=10,random_state=0)
for g in groups:
    tem=pk.date.isin(g).values
    for col in ['IN','OUT']: pk.loc[tem,col+'_s']=small().fit(Xp[~tem],pk[col][~tem]).predict(Xp[tem])
for d in ['2024-07-20','2024-07-21','2024-07-12']:
    g=pk[(pk.date==dt.date.fromisoformat(d))&pk.hour.between(6,23)]; ev=rp[(rp.date==d)&rp.cls.isin(list(NM))].drop_duplicates(['title','cls','start'])
    V['park_'+d]=dict(events=[(NM[x.cls]+' '+x.title,x.start,x.end,bool(x.imputed)) for _,x in ev.iterrows()],**{c:g[c].round().astype(int).tolist() for c in ['IN','IN_s','OUT','OUT_s']})
V['metrics']=json.load(open('m/eval_round2.json'))
json.dump(V,open('app/data/validation.json','w'),ensure_ascii=False,default=str); print(list(V))
