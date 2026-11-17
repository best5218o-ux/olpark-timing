import json,math,numpy as np
P=json.load(open('/home/claude/k/app/data/profile.json'))
def bucket(c,price):
    if not price: return 1
    a,b=P['price_th'][c]; return 0 if price<=a else (1 if price<=b else 2)
def fc(k,sc,dtp,month,events):
    b=np.array(P['base'][k][f'{sc}|{dtp}|{month}'],dtype=float)
    for c,s,price in events:
        if c not in P['classes']: continue
        s=min(max(s,10),22); s0=int(math.floor(s)); s1=min(s0+1,22); w=s-s0; bi=bucket(c,price)
        d0=np.array(P['delta'][k][f'{dtp}|{c}|{s0}|{bi}'],dtype=float); d1=np.array(P['delta'][k][f'{dtp}|{c}|{s1}|{bi}'],dtype=float)
        b=b+(1-w)*d0+w*d1
    return np.clip(b,0,None)
