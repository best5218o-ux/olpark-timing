import sys; sys.path.insert(0,'/home/claude/k/m')
from fit import *
from sklearn.ensemble import HistGradientBoostingRegressor as HGB
BIG=['DOME','ARENA','HALL','LAWN','ART']
def ev_offsets(df,r):
    # for each row, per class: hours since nearest start (h - start) within [-6,6] else 99; hours since end
    feats={}
    g={}
    for _,x in r.iterrows(): g.setdefault((x.date,x.cls),[]).append((x.start,x.end,x.price if x.price==x.price and x.price else 0,x.run))
    for c in BIG:
        so=[];eo=[];n=[];pr=[];rn=[]
        for d,h in zip(df.date,df.hour):
            L=g.get((d.isoformat(),c),[])
            hh=h+0.5
            s=min([hh-a for a,b,p,ru in L],key=abs,default=99); e=min([hh-b for a,b,p,ru in L],key=abs,default=99)
            so.append(s if abs(s)<=8 else 99); eo.append(e if abs(e)<=6 else 99); n.append(len(L))
            pr.append(max([p for a,b,p,ru in L],default=0)); rn.append(max([ru for a,b,p,ru in L],default=0))
        feats[f'{c}_so']=so; feats[f'{c}_eo']=eo; feats[f'{c}_n']=n; feats[f'{c}_price']=pr; feats[f'{c}_run']=rn
    return pd.DataFrame(feats,index=df.index)
def basef(df):
    X=pd.DataFrame(index=df.index)
    X['hour']=df.hour; X['dtype']=df.dt_h.str.split('_').str[0].map({'wk':0,'fri':1,'sat':2,'sun':3})
    X['rain']=df.rain; X['temp']=df.temp
    if 'month' in df: X['month']=df.month
    return X
def cv_gbm(df,y,r,big,folds=5,seed=0):
    X=pd.concat([basef(df),ev_offsets(df,r)],axis=1); X0=basef(df)
    ds=np.array(sorted(set(df.date))); rng=np.random.default_rng(seed); fold={d:i%folds for i,d in enumerate(rng.permutation(ds))}
    f=np.array([fold[d] for d in df.date]); pr=np.zeros(len(y)); pr0=np.zeros(len(y))
    for k in range(folds):
        tr=f!=k
        pr[~tr]=HGB(max_iter=400,learning_rate=0.05,categorical_features=[1]).fit(X[tr],y[tr]).predict(X[~tr])
        pr0[~tr]=HGB(max_iter=400,learning_rate=0.05,categorical_features=[1]).fit(X0[tr],y[tr]).predict(X0[~tr])
    bm=df.date.isin(big).values
    D=pd.DataFrame({'d':df.date,'y':y,'p':pr,'p0':pr0})[bm].groupby('d').max()
    res=dict(mae=np.abs(pr-y)[bm].mean(),mae0=np.abs(pr0-y)[bm].mean(),pk=(D.p-D.y).abs().mean(),pk0=(D.p0-D.y).abs().mean())
    return res,pr,pr0,X
