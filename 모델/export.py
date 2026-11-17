import sys; sys.path.insert(0,'/home/claude/k/m')
from model import *
import pickle
M=pd.read_csv('/home/claude/k/m/l9_hourly_2023_2026.csv'); M['date']=pd.to_datetime(M['날짜']).dt.date
M=M[M.hour.between(6,23)].dropna().reset_index(drop=True); dfl9=frame(M[['date','hour','순승차','순하차']].copy())
r9=events_rows(dt.date(2023,1,1),dt.date(2026,7,31))
P=pd.read_csv('/home/claude/k/m/subway_hourly_2025.csv'); P['date']=pd.to_datetime(P.date).dt.date
d58=frame(P[['date','hour','하차','승차']].copy()); r58=events_rows(dt.date(2025,1,1),dt.date(2025,12,31))
pk=pd.read_csv('/home/claude/k/m/park_hourly_202407_pred.csv'); pk['date']=pd.to_datetime(pk.date).dt.date
pkf=frame(pk[['date','hour','IN','OUT']].copy()); rpk=events_rows(dt.date(2024,7,1),dt.date(2024,7,31))
spec={'l9_off':(dfl9,r9,'순하차',True),'l9_on':(dfl9,r9,'순승차',True),'l58_off':(d58,r58,'하차',True),'l58_on':(d58,r58,'승차',True),'pk_IN':(pkf,rpk,'IN',False),'pk_OUT':(pkf,rpk,'OUT',False)}
def small(q=None):
    kw=dict(max_iter=300,learning_rate=0.05,min_samples_leaf=10,random_state=0)
    if q: kw.update(loss='quantile',quantile=q)
    return HGB(**kw)
out={}
def dump(est,cols):
    trees=[]
    for (pr,) in est._predictors:
        n=pr.nodes
        assert not n['is_categorical'].any()
        trees.append([n['feature_idx'].tolist(),[round(float(x),6) for x in n['num_threshold']],n['left'].tolist(),n['right'].tolist(),n['is_leaf'].astype(int).tolist(),[round(float(x),4) for x in n['value']],n['missing_go_to_left'].astype(int).tolist()])
    return dict(cols=cols,base=float(est._baseline_prediction.ravel()[0]),trees=trees)
models={}
for k,(df,r,col,usem) in spec.items():
    X=X_of(df,r)
    if not usem: X=X.drop(columns='month')
    y=df[col].values.astype(float)
    a=(mk() if usem else small()).fit(X,y); b=(mk(0.8) if usem else small(0.8)).fit(X,y)
    out[k]={'mean':dump(a,list(X.columns)),'q80':dump(b,list(X.columns))}; models[k]=(a,b,list(X.columns))
    print(k,len(a._predictors),len(b._predictors))
mon=pd.read_csv('/home/claude/k/d/15131671.u.csv'); mon=mon[mon.주차장소=='올림픽공원']; mon['m']=mon.월.str[:2].astype(int)
mi=mon.groupby('m').주차대수.mean(); SEAS={int(k):float(v) for k,v in (mi/mi[7]).items()}
clim=WX[WX.time.dt.year<=2025].groupby([WX.time.dt.month,WX.time.dt.hour]).temperature_2m.mean()
meta={'seasonal':SEAS,'clim':{f'{m}|{h}':round(float(v),2) for (m,h),v in clim.items()},'holidays':sorted(str(d) for d in KR if d.year>=2026),'generated':dt.datetime.now().isoformat(timespec='minutes'),
 'train':{'l9':'서울교통공사 9호선 2023-01~2026-07','l58':'서울교통공사 1~8호선 2025','pk':'올림픽공원 입출차 2024-07'}}
out['_meta']=meta
json.dump(out,open('/home/claude/k/app/netlify/functions/model.json','w'),separators=(',',':'))
pickle.dump(models,open('/home/claude/k/m/models_final.pkl','wb'))
import os; print(os.path.getsize('/home/claude/k/app/netlify/functions/model.json'))
