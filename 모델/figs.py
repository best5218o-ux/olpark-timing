import sys; sys.path.insert(0,'/home/claude/k/m')
from model import *
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.font_manager as fm
plt.rcParams['font.family']='Noto Sans CJK KR'; plt.rcParams['axes.unicode_minus']=False
C={'pri':'#1f4e9e','acc':'#e4572e','base':'#9aa3b5','ok':'#2a9d8f','ink':'#14213d'}
O='/home/claude/k/fig/'
def style(ax):
    for s in ['top','right']: ax.spines[s].set_visible(False)
    ax.grid(axis='y',color='#eef0f5'); ax.tick_params(labelsize=9)
H=list(range(6,24))
# F1 2024-07-20
pk=pd.read_csv('/home/claude/k/m/park_hourly_202407_pred.csv'); pk['date']=pd.to_datetime(pk.date).dt.date
g=pk[(pk.date==dt.date(2024,7,20))&pk.hour.between(6,23)]
fig,ax=plt.subplots(figsize=(8,3.2),dpi=200)
ax.plot(H,g.IN,color=C['pri'],lw=2.2,marker='o',ms=3,label='입차(실측)'); ax.plot(H,g.OUT,color=C['acc'],lw=2.2,marker='o',ms=3,label='출차(실측)')
ax.plot(H,g.IN_p0,color=C['pri'],lw=1.2,ls='--',alpha=.6,label='입차(공연 정보 없이 예보)'); ax.plot(H,g.OUT_p0,color=C['acc'],lw=1.2,ls='--',alpha=.6,label='출차(공연 정보 없이 예보)')
ax.axvline(18,color='#888',ls=':'); ax.text(17.2,1270,'공연 시작 18:00',fontsize=8,color='#555'); ax.axvline(20.5,color='#888',ls=':'); ax.text(19.0,1230,'종료 약 20:30',fontsize=8,color='#555')
ax.annotate('16시 1,117대',(16,1117),(12.3,1100),fontsize=9,color=C['pri'],arrowprops=dict(arrowstyle='->',color=C['pri']))
ax.annotate('21시 1,188대',(21,1188),(21.4,1000),fontsize=9,color=C['acc'],arrowprops=dict(arrowstyle='->',color=C['acc']))
ax.set_xticks(H[::2]); ax.set_xticklabels([f'{h}시' for h in H[::2]]); ax.set_ylabel('대/시간',fontsize=9); ax.set_ylim(0,1320); style(ax)
ax.legend(fontsize=8,ncol=2,frameon=False,loc='upper left'); ax.set_title('2024-07-20(토) 올림픽공원 주차장 입차·출차 — SG워너비(KSPO DOME)·휘인(올림픽홀) 18:00',fontsize=10,loc='left')
fig.text(0.01,0.0,'자료: 한국체육산업개발 올림픽공원 입출차 정보(15138735), 올림픽공원 공연정보. 점선은 같은 모델에서 공연 정보만 뺀 예보',fontsize=7,color='#666')
fig.tight_layout(rect=(0,0.06,1,1)); fig.savefig(O+'F1_공연날두번붐빈다.png'); plt.close()
# F2 2025 만차 고지 vs 대형공연
c=pd.read_csv('/home/claude/k/d/15164156.u.csv'); c['date']=pd.to_datetime(c['등록일']).dt.date
full=set(d for d in c[c.혼잡도=='만차'].date if d.year==2025)
r=events_rows(dt.date(2025,1,1),dt.date(2025,12,31)); bd=bigdays(r)
days=pd.date_range('2025-02-12','2025-12-31').date
fig,ax=plt.subplots(figsize=(8,2.6),dpi=200)
xs=[d.toordinal() for d in days]
ax.scatter([d.toordinal() for d in days if d in bd],[1]*len([d for d in days if d in bd]),marker='|',s=120,color=C['pri'],label=f'대형공연일 ({len([d for d in days if d in bd])}일)')
ax.scatter([d.toordinal() for d in days if d in full],[0]*len([d for d in days if d in full]),marker='v',s=30,color=C['acc'],label=f'만차 고지일 ({len([d for d in days if d in full])}일)')
both=[d for d in full if d in bd]
for d in both: ax.plot([d.toordinal()]*2,[0,1],color='#f2b8a8',lw=.6,zorder=0)
ax.set_yticks([0,1]); ax.set_yticklabels(['만차 고지','대형공연']); ax.set_ylim(-.6,1.6)
mt=pd.date_range('2025-03-01','2025-12-01',freq='MS'); ax.set_xticks([d.toordinal() for d in mt]); ax.set_xticklabels([f'{d.month}월' for d in mt],fontsize=8)
for s in ['top','right','left']: ax.spines[s].set_visible(False)
ax.legend(fontsize=8,frameon=False,loc='upper right',ncol=2,bbox_to_anchor=(1,1.25))
ax.set_title(f'2025년 만차가 고지된 {len(full)}일 중 {len(both)}일이 대형공연일 (고지 기록 기준)',fontsize=10,loc='left')
fig.text(0.01,0.0,'자료: 한국체육산업개발 주차장 혼잡도 정보(15164156, 2025-02-12~12-31), 올림픽공원 공연정보(KSPO DOME·티켓링크 라이브 아레나·올림픽홀·88잔디마당)',fontsize=7,color='#666')
fig.tight_layout(rect=(0,0.08,1,1)); fig.savefig(O+'F2_만차는공연이만든다.png'); plt.close()
print('both',len(both),len(full))
# F3 validation 9호선 2026 three days
V=json.load(open('/home/claude/k/app/public/data/validation.json'))
ks=[k for k in V if k.startswith('l9_')][:3]
fig,axs=plt.subplots(1,3,figsize=(9,2.7),dpi=200,sharey=True)
for ax,k in zip(axs,ks):
    x=V[k]; ax.plot(H,x['순승차'],color='#111',lw=1.8,marker='o',ms=2.5,label='실측'); ax.plot(H,x['순승차_p'],color=C['acc'],lw=2,label='공연 반영 예보'); ax.plot(H,x['순승차_p0'],color=C['base'],lw=1.2,ls='--',label='공연 정보 없이 예보'); ax.plot(H,x['순승차_q'],color='#e9a23b',lw=1.2,label='붐빌 때(상위 20%)')
    ax.set_title(k[3:]+' '+(x['events'][0][0][:22] if x['events'] else ''),fontsize=8); ax.set_xticks(H[::4]); ax.set_xticklabels([f'{h}시' for h in H[::4]],fontsize=7); style(ax)
axs[0].set_ylabel('9호선 2개 역 승차(명/시간)',fontsize=8); axs[0].legend(fontsize=7,frameon=False)
fig.suptitle('2025년까지만 학습하고 2026년을 맞혀 보기 — 9호선 올림픽공원·한성백제역 귀가 승차',fontsize=10,x=0.01,ha='left')
fig.text(0.01,0.0,'자료: 서울교통공사 9호선 2·3단계 역별 시간대별 승하차인원(15060424), 올림픽공원 공연정보',fontsize=7,color='#666')
fig.tight_layout(rect=(0,0.09,1,0.93)); fig.savefig(O+'F3_2026분리검증.png'); plt.close()
# F4 error bars
m=json.load(open('/home/claude/k/m/eval_round2.json'))
items=[('9호선 귀가 승차\n2026.1~7 · 83일',m['l9_순승차']),('9호선 도착 하차\n2026.1~7 · 83일',m['l9_순하차']),('주차장 입차\n2024-07 · 9일',m['park_series']['IN']),('주차장 출차\n2024-07 · 9일',m['park_series']['OUT'])]
fig,ax=plt.subplots(figsize=(8,2.9),dpi=200); import numpy as np
xx=np.arange(len(items)); a=[i[1]['mape_peak0']*100 for i in items]; r=[i[1]['mape_peak_rule']*100 for i in items]; b=[i[1]['mape_peak']*100 for i in items]
ax.bar(xx-0.26,a,0.26,color='#c9cfdb',label='공연 정보 없이'); ax.bar(xx,r,0.26,color=C['base'],label='단순 규칙(대형공연일 평균)'); ax.bar(xx+0.26,b,0.26,color=C['acc'],label='올팍 타이밍')
for i,(u,w,v) in enumerate(zip(a,r,b)):
    ax.text(i-0.26,u+1,f'{u:.0f}%',ha='center',fontsize=7.5); ax.text(i,w+1,f'{w:.0f}%',ha='center',fontsize=7.5); ax.text(i+0.26,v+1,f'{v:.0f}%',ha='center',fontsize=8.5,color=C['acc'],fontweight='bold')
ax.set_xticks(xx); ax.set_xticklabels([i[0] for i in items],fontsize=8); ax.set_ylabel('그날 최대치 오차율',fontsize=9); style(ax); ax.legend(fontsize=7.5,frameon=False,ncol=3,loc='upper right'); ax.set_ylim(0,65)
ax.set_title('학습에 쓰지 않은 날로 잰 대형공연일 최대치 오차율 (주차는 같은 공연 묶음째 빼고 검증)',fontsize=10,loc='left')
fig.tight_layout(); fig.savefig(O+'F4_오차감소.png'); plt.close()
# F5 60-day from summary
S=json.load(open('/home/claude/k/app/public/data/summary.json'))
rows=[]
for d in S['days']:
    big=any(e['cls'] in('DOME','ARENA','HALL','LAWN') for e in d['events'])
    if 'peaks' in d and big:
        p=d['peaks']['l9_on']; rows.append((d['date'],p['v'],p['q'],p['base']))
R=pd.DataFrame(rows,columns=['d','v','q','b'])
fig,ax=plt.subplots(figsize=(8,2.7),dpi=200)
x=np.arange(len(R)); ax.bar(x,R.q,color='#f6d39a',label='붐빌 때(상위 20%)'); ax.bar(x,R.v,color=C['acc'],label='예보'); ax.scatter(x,R.b,color=C['ink'],s=10,zorder=3,label='공연 정보 뺀 같은 날')
ax.set_xticks(x); ax.set_xticklabels([pd.Timestamp(d).strftime('%m/%d') for d in R.d],fontsize=6.5,rotation=60); style(ax); ax.set_ylabel('명/시간',fontsize=8)
ax.legend(fontsize=7.5,frameon=False,ncol=3,loc='upper left'); ax.set_title(f"다가오는 대형공연일 {len(R)}일의 9호선 귀가 승차 피크 예보 ({S['days'][0]['date']} 기준 60일)",fontsize=10,loc='left')
fig.tight_layout(); fig.savefig(O+'F5_60일예보.png'); plt.close()
print('F5 days',len(R))
