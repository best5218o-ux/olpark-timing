import sys; sys.path.insert(0,'/home/claude/k/m')
from fit import *
def load():
    p=pd.read_csv('/home/claude/k/d/15138735.u.csv'); p['in']=pd.to_datetime(p['입차일시']); p['out']=pd.to_datetime(p['출차일시'])
    idx=pd.date_range('2024-07-01','2024-07-31 23:00',freq='h')
    IN=p.groupby(p['in'].dt.floor('h')).size().reindex(idx,fill_value=0)
    OUT=p.groupby(p['out'].dt.floor('h')).size().reindex(idx,fill_value=0)
    # occupancy: cars present at hour h (in<=h+30m<out)
    occ=[]
    ins=p['in'].values; outs=p['out'].values
    for t in idx:
        tt=np.datetime64(t+pd.Timedelta(minutes=30)); occ.append(int(((ins<=tt)&(outs>tt)).sum()))
    wx=pd.DataFrame(json.load(open('/home/claude/k/wx_202407.json'))['hourly']); wx['time']=pd.to_datetime(wx.time); wx=wx.set_index('time').reindex(idx)
    df=pd.DataFrame({'ts':idx}); df['date']=df.ts.dt.date; df['hour']=df.ts.dt.hour
    df['dt_h']=[daytype(d)+'_'+str(h) for d,h in zip(df.date,df.hour)]
    df['rain']=(wx.precipitation.values>0.5).astype(float); df['temp']=wx.temperature_2m.values
    df['IN']=IN.values; df['OUT']=OUT.values; df['OCC']=occ
    return p,df
