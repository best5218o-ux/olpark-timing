import sys; sys.path.insert(0,'/home/claude/k/m')
from model import *
out={}
# ---- parking: leave-one-event-series-out
pk=pd.read_csv('m/park_hourly_202407_pred.csv'); pk['date']=pd.to_datetime(pk.date).dt.date
r=events_rows(dt.date(2024,7,1),dt.date(2024,7,31)); days=bigdays(r)
X=X_of(pk,r).drop(columns='month'); X0=X_of(pk,r,False).drop(columns='month')
groups=[[dt.date(2024,7,6),dt.date(2024,7,7)],[dt.date(2024,7,12),dt.date(2024,7,13),dt.date(2024,7,14)],[dt.date(2024,7,20),dt.date(2024,7,21)],[dt.date(2024,7,27),dt.date(2024,7,28)]]
gid={d:i for i,g in enumerate(groups) for d in g}
other=[d for d in sorted(set(pk.date)) if d not in gid]
mk2=lambda: HGB(max_iter=300,learning_rate=0.05,min_samples_leaf=10,random_state=0)
res={}
for col in ['IN','OUT','OCC']:
    y=pk[col].values.astype(float); P=np.zeros(len(y)); P0=np.zeros(len(y))
    folds=groups+[[d] for d in other]
    for f in folds:
        te=pk.date.isin(f).values
        P[te]=mk2().fit(X[~te],y[~te]).predict(X[te]); P0[te]=mk2().fit(X0[~te],y[~te]).predict(X0[te])
    m=metrics(pk,y,P,P0,days)
    # simple rule baseline: same daytype-hour mean of other big-event days (excluding same group)
    R=np.zeros(len(y))
    for i,(d,h) in enumerate(zip(pk.date,pk.hour)):
        sel=pk[(pk.hour==h)&(pk.date!=d)&pk.date.isin(days)&(~pk.date.isin(groups[gid[d]] if d in gid else [d]))&(pk.dtype.isin([2,3]) if dtype(d)>=2 else pk.dtype.isin([0,1]))]
        R[i]=sel[col].mean() if len(sel) else y[i]
    bm=pk.date.isin(days).values
    D=pd.DataFrame({'d':pk.date,'y':y,'r':R})[bm].groupby('d').max()
    m['mape_peak_rule']=float(((D.r-D.y).abs()/D.y).mean())
    res[col]=m; print(col,{k:round(v,3) for k,v in m.items()})
out['park_series']=res
# ---- 9호선 holdout: peak timing + rule baseline
M=pd.read_csv('m/l9_hourly_2023_2026.csv'); M['date']=pd.to_datetime(M['날짜']).dt.date
M=M[M.hour.between(6,23)].dropna().reset_index(drop=True); df=frame(M[['date','hour','순승차','순하차']].copy())
r=events_rows(dt.date(2023,1,1),dt.date(2026,7,31)); days=bigdays(r)
X=X_of(df,r); X0=X_of(df,r,False); tr=(df.date<dt.date(2026,1,1)).values
for col in ['순승차','순하차']:
    y=df[col].values.astype(float)
    p=mk().fit(X[tr],y[tr]).predict(X[~tr]); p0=mk().fit(X0[tr],y[tr]).predict(X0[~tr])
    from sklearn.ensemble import HistGradientBoostingRegressor as H
    q=mk(0.8).fit(X[tr],y[tr]).predict(X[~tr])
    te=df[~tr].copy(); te['y']=y[~tr]; te['p']=p; te['p0']=p0; te['q']=q
    tb=te[te.date.isin(days)]
    g=tb.groupby('date')
    ph=g.apply(lambda x:x.loc[x.y.idxmax(),'hour']); pp=g.apply(lambda x:x.loc[x.p.idxmax(),'hour'])
    exact=(ph==pp).mean(); within1=((ph-pp).abs()<=1).mean()
    # rule: mean of training big-event days same dtype-group & hour
    trn=df[tr].copy(); trn['y']=y[tr]; trn=trn[trn.date.isin(days)]; trn['wk']=trn.dtype>=2
    rule=trn.groupby(['wk','hour']).y.mean()
    tb=tb.assign(rule=[rule[(dd>=2,h)] for dd,h in zip(tb.dtype,tb.hour)])
    D=tb.groupby('date').agg(y=('y','max'),p=('p','max'),p0=('p0','max'),r=('rule','max'),q=('q','max'))
    cover=(D.y<=D.q).mean(); under=(D.p<D.y).mean()
    o=dict(peak_hour_exact=float(exact),peak_hour_pm1=float(within1),mape_peak=float(((D.p-D.y).abs()/D.y).mean()),mape_peak0=float(((D.p0-D.y).abs()/D.y).mean()),mape_peak_rule=float(((D.r-D.y).abs()/D.y).mean()),p80_cover=float(cover),under_share=float(under),q_mape=float(((D.q-D.y).abs()/D.y).mean()))
    out['l9_'+col]=o; print(col,{k:round(v,3) for k,v in o.items()})
json.dump(out,open('m/eval_round2.json','w'),indent=1,ensure_ascii=False)
