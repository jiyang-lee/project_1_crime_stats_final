# 프로젝트 요구사항 충족 현황 (Checklist)

아래는 제공된 항목(필수/선택)에 대해 “했는지/안 했는지”, 했다면 “어디에 구현되어 있는지”, 안 했다면 “무엇을 하면 좋은지”를 정리한 문서입니다.  
파일/기능 기준으로 확인 가능한 범위를 중심으로 작성했습니다.

## 필수
### 1. 데이터 분석 + 정리
- 상태: 완료
- 근거:
  - `1_preprocessing/` 내 노트북에서 CSV 정제 및 가공 수행
  - 예: `1_preprocessing/police.ipynb`, `1_preprocessing/mapping_prepro.ipynb`, `1_preprocessing/jeoncheory.ipynb`
- 상세:
  - 불필요 열 제거, 문자열 정리, melt/long 변환, `_fix` CSV 생성
  - 매핑/누락 데이터 보완

### 2. DB 설계 + 구축
- 상태: 완료
- 근거:
  - ORM 모델: `4_streamlit/orm/model.py`
  - DB 세션/엔진: `4_streamlit/orm/database.py`
- 상세:
  - 3개 이상 ORM 모델 존재(RegionMaster, CrimeCategory, HotspotAPI 등)
  - FK 관계 설정(RegionMapper, CrimeRegion, CrimeTime, CrimeWeek)

### 3. Plotly 차트 5종+
- 상태: 부분 충족
- 확인된 유형:
  - Bar: `4_streamlit/pages/time.py`, `4_streamlit/pages/week.py`, `4_streamlit/pages/region.py`
  - Pie: `4_streamlit/pages/region.py`
  - Scattermapbox(지도 점): `4_streamlit/pages/hotspot.py`
- 부족한 점:
  - 5종 이상 확인이 어려움(라인/히스토그램/박스/히트맵 등 추가 필요)
- 추천:
  - 시간대별 추이를 `px.line`으로 추가
  - 위험도 분포를 `px.histogram` 또는 `px.box`
  - 지역×요일 히트맵(`px.imshow`) 추가

### 4. Streamlit 대시보드 (멀티페이지 3개+, 위젯/필터 3개+)
- 상태: 완료
- 근거:
  - 페이지: `4_streamlit/pages/home.py`, `time.py`, `week.py`, `region.py`, `hotspot.py`
  - 위젯/필터: 각 페이지의 selectbox/토글/슬라이더(확인 가능한 형태)
- 상세:
  - 최소 3페이지 이상 구성
  - 범죄 유형/지역/지표 선택 등 필터 사용

### 5. 배포 (GitHub 저장소 + Streamlit Cloud)
- 상태: 완료
- 근거:
  - GitHub 저장소 운영
  - Streamlit Cloud 배포 진행(사용자 확인 사항)
- 상세:
  - Actions 기반 자동 수집 파이프라인 추가(자동 갱신 구성)

## 선택(가산점)
### 6. 고급 시각화 (Graph Objects, 이중 Y축, 애니메이션, 히트맵)
- 상태: 부분 충족
- 근거:
  - `plotly.graph_objects` 사용 중(`time.py`, `week.py`, `region.py`, `hotspot.py`)
- 부족한 점:
  - 이중 Y축/애니메이션/히트맵은 확인되지 않음
- 추천:
  - 이중 축(예: 범죄건수 vs 위험지수)
  - 요일×시간 히트맵
  - 시간 흐름 애니메이션(선택 사항)

### 7. 캐싱/성능 (@st.cache_data, session_state)
- 상태: 완료
- 근거:
  - `@st.cache_data` 사용: `4_streamlit/pages/time.py`, `4_streamlit/pages/week.py`
  - `st.session_state` 사용: `4_streamlit/pages/region.py`, `4_streamlit/pages/hotspot.py`
- 상세:
  - 데이터 로딩 캐싱
  - UI 상태 유지(테이블 펼치기, 범죄 유형 선택 등)

### 8. CRUD 기능 (Streamlit에서 데이터 추가/수정/삭제)
- 상태: 미완
- 현재 상황:
  - Streamlit UI에서 DB를 직접 수정하는 기능은 없음
- 추천:
  - 관리자용 페이지 추가(`admin.py`) → 입력 폼으로 Hotspot/매핑 데이터 수정
  - 수정 시 ORM으로 DB 반영

### 9. 추가 데이터 (공공데이터 API 연동 또는 추가 데이터셋 활용)
- 상태: 완료
- 근거:
  - 서울시 HOTSPOT API 연동: `4_streamlit/seed/seoul_collector_30min.py`
  - 지역/범죄 통계 CSV 결합
- 확장 아이디어:
  - 지하철 승하차/유동인구 API 추가
  - 날씨/행사 데이터 결합

## 요약
- 필수 항목은 대부분 충족
- “Plotly 차트 5종+”과 “고급 시각화”는 보강 여지가 있음
- CRUD는 가산점 영역에서 미완 → 관리자 페이지로 확장 권장
