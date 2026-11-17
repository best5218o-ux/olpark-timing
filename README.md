# 올팍 타이밍 (Olpark Timing)

공연 날 올림픽공원의 시간대별 차량 입차·출차와 지하철(9호선 올림픽공원·한성백제, 5호선 올림픽공원·8호선 몽촌토성) 도착·귀가 인원을 공연별로 예보하는 웹 서비스.
2026년도 한국체육산업개발(주) 공공데이터 활용 경진대회 출품작 · 팀 브랜드 AI

- 서비스: https://best5218o-ux.github.io/olpark-timing/ (GitHub Pages, 3시간마다 자동 갱신)
- 보조 주소: https://olpark-timing.netlify.app (Netlify — 실시간 주차·즉시 예보 API 포함)
- 구조: `public/`(화면·정적 예보 JSON) · `netlify/lib/lib.mjs`(공연 일정 해석·특징·예보 엔진) · `netlify/lib/model.json`(학습된 나무 모델) · `scripts/build.mjs`(예보 생성) · `netlify/functions/`(실시간·즉시 예보 API) · `.github/workflows/update.yml`(3시간마다 자동 갱신)
- 학습 코드(Python): `모델/` 폴더(events.py 공연시간 해석, model.py 특징, export.py 모델 내보내기, reval.py 검증)

## 실행
```
node scripts/build.mjs        # 기관 누리집 공연 일정을 받아 public/data 에 60일 예보 생성
python3 -m http.server -d public 8000
```
## 데이터 출처
한국체육산업개발(주) 개방 공공데이터(공공데이터포털 3037877·15138735·15164156·15131671 등), 서울교통공사 역별 시간대별 승하차인원(15060424·15048032), Open-Meteo(CC BY 4.0).
