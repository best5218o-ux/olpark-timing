import sys; sys.path.insert(0,'/home/claude/k/m')
from model import *
from sklearn.ensemble import HistGradientBoostingRegressor as HG
OUT='/home/claude/k/app/data/profile.json'
TG={}
# training sets
M=pd.read_csv('/home/claude/k/m/l9_hourly_2023_2026.csv'); M['date']=pd.to_datetime(M['날짜']).dt.date
M=M[M.hour.between(6,23)].dropna().reset_index(drop=True); dfl9=frame(M[['date','hour','순승차','순하차']].copy())
r9=events_rows(dt.date(2023,1,1),dt.date(2026,7,31))
P=pd.read_csv('/home/claude/k/m/subway_hourly_2025.csv'); P['date']=pd.to_datetime(P.date).dt.date
d58=frame(P[['date','hour','하차','승차']].copy()); r58=events_rows(dt.date(2025,1,1),dt.date(2025,12,31))
pk=pd.read_csv('/home/claude/k/m/park_hourly_202407_pred.csv'); pk['date']=pd.to_datetime(pk.date).dt.date
pk=pk[['date','hour','IN','OUT']]; pkf=frame(pk.copy()); rpk=events_rows(dt.date(2024,7,1),dt.date(2024,7,31))
spec={'l9_off':(dfl9,r9,'순하차',True),'l9_on':(dfl9,r9,'순승차',True),'l58_off':(d58,r58,'하차',True),'l58_on':(d58,r58,'승차',True),'pk_IN':(pkf,rpk,'IN',False),'pk_OUT':(pkf,rpk,'OUT',False)}
def mdl(q=None,small=False):
    kw=dict(max_iter=300 if small else 500,learning_rate=0.05,random_state=0)
    if small: kw['min_samples_leaf']=10
    else: kw['categorical_features']=[1]
    if q: kw.update(loss='quantile',quantile=q)
    return HG(**kw)
models={}
for k,(df,r,col,usem) in spec.items():
    X=X_of(df,r); 
    if not usem: X=X.drop(columns='month')
    y=df[col].values.astype(float)
    models[k]=(mdl(small=not usem).fit(X,y),mdl(0.8,small=not usem).fit(X,y),list(X.columns))
    print('trained',k)
clim=WX[WX.time.dt.year<=2025].groupby([WX.time.dt.month,WX.time.dt.hour]).temperature_2m.mean()
mon=pd.read_csv('/home/claude/k/d/15131671.u.csv'); mon=mon[mon.주차장소=='올림픽공원']; mon['m']=mon.월.str[:2].astype(int)
mi=mon.groupby('m').주차대수.mean(); SEAS=(mi/mi[7]).to_dict()
HRS=list(range(6,24)); CL=['DOME','ARENA','HALL','LAWN','ART']
DUR={'DOME':2.5,'ARENA':2.0,'HALL':2.0,'LAWN':8.0,'ART':7/6}
allr=events_rows(dt.date(2023,1,1),dt.date(2026,12,31))
PR={c:[float(allr[allr.cls==c].price.quantile(q)) for q in (0.25,0.5,0.75)] for c in CL}
TH={c:[float(allr[allr.cls==c].price.quantile(1/3)),float(allr[allr.cls==c].price.quantile(2/3))] for c in CL}
NEXT={0:0,1:1,2:1,3:0}
def rows(dtp,month,rain,events):
    d=pd.DataFrame({'hour':HRS}); d['dtype']=dtp; d['month']=month
    d['temp']=[clim[(month,h)] for h in HRS]; d['rain']=[rain if 16<=h<=22 else 0.0 for h in HRS]; d['nextday_hol']=NEXT[dtp]
    for c in CL:
        L=[e for e in events if e[0]==c]
        so=[];eo=[]
        for h in HRS:
            hh=h+0.5
            s=min([hh-a for _,a,b,p in L],key=abs,default=99); e=min([hh-b for _,a,b,p in L],key=abs,default=99)
            so.append(s if abs(s)<=8 else 99); eo.append(e if abs(e)<=6 else 99)
        d[c+'_so']=so; d[c+'_eo']=eo; d[c+'_n']=len(L); d[c+'_price']=max([p for *_,p in L],default=0); d[c+'_run']=2 if L else 0
    return d
def pred(k,d):
    m,q,cols=models[k]; X=d[cols]; return m.predict(X),q.predict(X)
prof={'hours':HRS,'classes':CL,'dur':DUR,'price_th':TH,'seasonal':SEAS,'base':{},'delta':{},'starts':list(range(10,23))}
for k in spec:
    prof['base'][k]={}; prof['delta'][k]={}
    for sc,rain in (('clear',0.0),('rain',3.0)):
        for dtp in range(4):
            for mo in range(1,13):
                mm=mo if spec[k][3] else 7
                p,qq=pred(k,rows(dtp,mm,rain,[]))
                if not spec[k][3]: s=SEAS[mo]; p=p*s; qq=qq*s
                prof['base'][k][f'{sc}|{dtp}|{mo}']=[np.round(p).astype(int).tolist(),np.round(qq).astype(int).tolist()]
    for dtp in range(4):
        b,bq=pred(k,rows(dtp,11,0.0,[]))
        for c in CL:
            for st in prof['starts']:
                for pi,pv in enumerate(PR[c]):
                    p,qq=pred(k,rows(dtp,11,0.0,[(c,st,st+DUR[c],pv)]))
                    prof['delta'][k][f'{dtp}|{c}|{st}|{pi}']=[np.round(p-b).astype(int).tolist(),np.round(qq-bq).astype(int).tolist()]
    print('profiled',k)
json.dump(prof,open(OUT,'w'),separators=(',',':'))
import os; print(os.path.getsize(OUT))
# store models for approximation check
import pickle; pickle.dump({k:(v[0],v[1],v[2]) for k,v in models.items()},open('/home/claude/k/m/models_final.pkl','wb'))
