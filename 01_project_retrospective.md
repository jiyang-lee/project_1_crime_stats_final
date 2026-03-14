# 프로젝트 회고

## 1. 프로젝트 개요
- 서울시 경찰청 통계(요일·시간대·지역)와 서울시 HOTSPOT API 데이터를 결합하여 범죄 위험도를 시각화하는 Streamlit 포털을 구축해, 기존 CSV 기반 통계가 입체적으로 제공하지 않던 시간·공간·혼잡도를 통합적으로 보여주는 것을 목표로 삼음.
- "정적 통계는 특정 범죄 유형, 시간, 지역을 빠르게 비교하기 어려우며 실제 혼잡도와도 연결되지 않는다"는 문제 정의를 내세워 정제 → ORM 적재 → Streamlit UI로 연결되는 파이프라인을 구현함.

## 2. 프로젝트 구조
- `1_preprocessing/`: Excel/CSV에서 불필요 열을 제거하고 문자열 트리밍·long 변환을 거쳐 `_fix` 데이터/매핑 테이블을 생성하는 Jupyter 노트북(예: `police.ipynb`, `mapping_prepro.ipynb`).
- `2_eda/`: 정제된 CSV를 바탕으로 요일·시간대별 합계, 평균 대비 위험 지수, 낮/밤 비율 등 통계 인사이트를 정량적으로 점검하는 EDA 노트북.
- `3_orm/` + `4_streamlit/orm/`: SQLAlchemy ORM 모델 및 SQLite 연결/세션 관리 구현으로 범죄/지역/시간/매퍼 테이블의 관계를 정리.
- `4_streamlit/`: Streamlit 앱 본체(`main.py`, `pages/`), 정제 데이터(`data/`), 정적 자산(`static/`), 시딩 스크립트(`seed/`), ORM(`orm/`)으로 “CSV → ORM → Streamlit” 흐름을 완성.
- 루트 엔트리포인트 `main.py`를 추가해 저장소 루트에서 `streamlit run main.py`로 실행 가능하게 구성했고, `2_sub.py`/`crime_db.db` 같은 로컬 산출물은 추적 대상에서 제외함.
- `.streamlit/`, `.env.sample`, `requirements.txt`, `STREAMLIT_SECRETS.md`, `.vscode/settings.json`, `pyrightconfig.json`은 환경설정·배포·개발환경(인터프리터/분석기) 고정에 필요한 파일로 운영함.

## 3. 데이터 설명
- `police_region_fix.csv`: `범죄대분류`, `범죄중분류`, `지역`, `범죄건수` 컬럼으로 구간별 누적 범죄 데이터를 제공해 지역 hex 지도 레이어의 입력으로 쓰임.
- `police_time_fix.csv`: `시간대`, `시간대2` 등 시간 라벨과 `범죄건수`를 담아 위험 스코어·낮/밤 비율 계산에 활용.
- `police_week_fix.csv`: `요일`, `발생건수`를 담아 요일별 Danger Index 및 메트릭 카드 구성을 지탱.
- `mapping_fix.csv`, `서울시_122개_hotspot.csv`: 서울시 주요 지점(AREA_GU/AREA_NM/ENG_NM)을 RegionMaster 매핑과 HOTSPOT API 결과에 연결.
- `서울시_122개_geodata.csv`: Polygon 좌표로 pydeck hexLayer의 공간 판단을 가능하게 하며, `data/before/` 폴더의 원본 CSV는 `_fix` 데이터 생성의 입력 역할.

## 4. 데이터 처리 및 분석 과정
- 전처리: `police.ipynb` 등에서 pandas로 drop 리스트를 반영한 열 제거 → 문자열 트리밍 → 불필요 범죄 필터링 → melt로 long 포맷화 → `_fix` CSV로 저장.
- 핫스팟 매핑: 서울시 및 경찰청 지역 리스트를 조인하고 누락 행(서울대공원, 덕수궁 등)을 보완 → `mapping_fix.csv`/`서울시_122개_hotspot.csv` 생성.
- 시딩: `seed_all.py`가 CSV를 읽어 RegionMaster → CrimeCategory → RegionMapper → CrimeRegion/CrimeTime/CrimeWeek 순으로 ORM/SQLite에 적재.
- 실시간 API: `seoul_collector_30min.py`는 `SEOUL_API_KEY`를 환경변수 또는 Streamlit secrets에서 확보하고 30분 주기로 HOTSPOT API를 호출해 `HotspotAPI` 테이블을 갱신.
- 전체 파이프라인: raw CSV → 전처리 노트북 → `_fix` CSV/GeoJSON → `seed_all.py`로 ORM 채우기 → Streamlit `load_data()`/Hotspot collector → `time/week/region/hotspot` 페이지 렌더링.

## 5. 주요 코드 설명
- `main.py`(루트) + `4_streamlit/main.py`: 루트에서 실행 가능한 엔트리포인트와 실제 앱 네비게이션을 분리해 구성. 루트 실행 시 `4_streamlit`를 import 경로에 추가해 `orm` 모듈 로딩 오류를 방지.
- `pages/time.py`: ORM에서 CrimeTime/CrimeCategory를 조인해 시간대별 총합, Danger Index, 낮·밤 비율, 비교 카드(Plotly 바+HTML)를 생성하고, `st.cache_data`로 DB I/O를 최소화.
- `pages/week.py`: CrimeWeek 데이터를 가져와 요일별 라인/바 차트와 위험 카드, `danger_threshold` 기반 스타일링을 수행.
- `pages/region.py`: pydeck HexagonLayer를 위한 서울 좌표 + RegionMaster 매핑을 수동 관리하고, GUI 슬라이더/토글로 hex radius/elevation/pitch를 조정.
- `pages/hotspot.py`: `HotspotAPI` 쿼리 결과를 인구/혼잡도 순으로 정렬하고 메트릭 카드/표로 출력하며, `CONGEST_ORDER`와 `CONGEST_STYLE`로 위험 레벨을 시각화. 강력범죄는 고정 저인구 기준을 사용하고 사용자 슬라이더는 제거.
- `pages/hotspot.py`: `HotspotAPI` 쿼리 결과 기반 시각화에 더해, 화면 내 수동 갱신 버튼으로 수집기 1회 실행(`collect_and_save_once`)을 호출해 즉시 최신값 반영이 가능하도록 확장.
- `orm/model.py` + `orm/database.py`: RegionMaster, CrimeCategory, CrimeRegion/CrimeTime/CrimeWeek, HotspotAPI 등의 테이블과 SQLite 접속/세션 유틸(`get_db`)을 정의, ORM 레이어를 통해 Streamlit과 seed/collector가 공유.
- `seed/seoul_collector_30min.py`: CSV에서 핫스팟 목록을 불러와 API 호출, 응답 파싱 → `HotspotAPI` 테이블에 upsert/활성화(`active`) 기준으로 반영; API 키 유무를 체크해 실패 시 명시적인 오류를 띄움.
- `seed/seoul_collector_30min.py`: API 키 로딩 경로(환경변수, `secrets.toml`, `.env`)를 다중 지원하고, 시작 시 `create_database()`로 테이블을 보장하며, `--once`, `--max-hotspots` 및 `collect_and_save_once()`로 디버그/수동 갱신 시나리오를 지원.
- `seed/seed_all.py`: 각 CSV를 읽어 ORM 테이블을 순차적으로 채우며 중복 시드 차단 로직을 포함, `create_database()` 호출 후 `seed_all()`로 전체 파이프라인을 실행.

## 6. 분석 결과 요약
- `2_eda/1_stat_police.ipynb`에서 요일별 발생 합계가 토-일-금-목-수-화-월 순으로 높아 Danger Index가 평균 대비 110% 이상을 경고로 정의했고, 범죄 대분류별로 순위가 다름을 확인.
- 같은 노트북에서 시간대별 총합/평균을 계산해 오전 6~9시는 비교적 안전, 밤 12시 이후는 위험이 높다는 정성적 관찰을 수치(Plotly 바, metric 카드)로 뒷받침함.
- `2_eda/2_stat_police.ipynb`는 각 CSV에서 동일한 범죄 카테고리가 존재하는지 유니크 체크를 수행해 전처리 일관성을 검증함.
- `3_orm/*` 노트북은 ORM 엔진 설정 → 테이블 생성 → 쿼리 연습을 통해 SQLite 구조를 사전에 숙지하고 Streamlit 쿼리 설계에 적용할 수 있는 기반을 마련.

## 7. 개발 과정에서의 문제와 해결
- 원본 엑셀/CSV에 불필요 열/잘못된 지역명이 섞여 있어 `police.ipynb`에서 drop list, 문자열 strip, 숫자 타입 캐스팅/정렬을 거쳐 long 포맷을 확보하고 `police_week_fix.csv`로 저장.
- 매핑 처리에서 서울대공원·덕수궁 등 서울 외 지역 또는 누락 행을 수동으로 추가하고 `NO` 기준 정렬 → `mapping_fix.csv`/`서울시_122개_hotspot.csv`로 반영해 ORM/Hotspot API 연결 안정화.
- Streamlit 앱 초기 실행 시 세션 캐시/DB I/O를 고려해 `@st.cache_data`와 `SessionLocal` 컨텍스트 매니저를 결합하고, DB가 비어 있으면 시드 스크립트 실행 안내 메시지(`st.warning`, `st.code`)를 띄워 UX를 개선.
- Seoul API 키(`SEOUL_API_KEY`)는 환경변수 또는 `.streamlit/secrets.toml`에서 주입해야 하므로 `STREAMLIT_SECRETS.md`와 `.env.sample`을 통해 가이드하고, 키가 없으면 collector가 명시적으로 예외를 던져 런타임 실패를 예방.
- 루트 실행(`streamlit run main.py`)에서 `ModuleNotFoundError: orm`가 발생한 이슈는 루트 엔트리포인트에 `sys.path` 보강 로직을 추가해 해결.
- `st.navigation` 사용 시 `st.page_link("pages/...")` 경로 해석 오류(`StreamlitPageNotFoundError`)를 경험했고, 페이지 경로를 엔트리포인트 기준 절대 경로로 통일해 해결.
- VS Code에서 `reportMissingImports`가 반복된 문제는 `.vscode/settings.json`과 `pyrightconfig.json`을 통해 `.venv` 인터프리터/분석 경로를 고정해 해결.
- 실행 디렉터리가 `4_streamlit`일 때 `.\.venv` 경로를 찾지 못하는 문제가 반복되어, 실행 위치별 명령(루트: `.\\.venv\\...`, `4_streamlit`: `..\\.venv\\...`)을 분리 운영하고 시드/실행 경로를 표준화.
- `seed_all.py` 실행 후에도 시간/요일 페이지에서 비어 보이는 증상은 Streamlit 캐시 영향이 있어 `streamlit cache clear` + 프로세스 재시작 절차를 운영 가이드에 반영.

## 8. 배운 점
- CSV 정제 → ORM/SQLite → Streamlit으로 이어지는 데이터 파이프라인은 다른 도시나 범죄 카테고리 확장 시에도 재사용 가능하며 `seed_all.py`가 그 핵심.
- Plotly/pydeck + Streamlit Components 조합으로 정량적 Danger Index, 낮/밤, hex 지도, HOTSPOT 카드 등 다양한 뷰를 하나의 포털 안에 안정적으로 배치할 수 있다는 것을 경험.
- SQLAlchemy ORM 모델을 먼저 주노트북(`3_orm/`)에서 연습하고 Streamlit 페이지에서 쿼리하는 방식은 개발 이중성을 줄이고, `@st.cache_data` + `SessionLocal` 조합은 DB 연결 수를 제어하는 데 유용함.
- HTML/Plotly 커스터마이징(components.html, style 태그)과 Streamlit 페이지 구성으로 대시보드의 브랜드화, 사용자 안내 메시지를 직접 구현하는 노하우를 축적.

## 9. 향후 개선 방향
1. 전체 ETL을 makefile/스크립트로 묶어서 `data/before/*.csv` → `_fix` → SQLite → Streamlit(Seed+Collector)까지 자동화하고, `seed_all.py`와 `collector`를 CLI화해 테스트 가능하게 만들 것.
2. Streamlit 페이지별 리소스(Plotly/pydeck, ORM 쿼리) 사용량을 모니터링하고 캐시 정책을 재검토해 실시간 API 실패 시 실패한 데이터를 보여줄 fallback(예: latest timestamp)과 warn/notify를 추가.
3. GeoJSON/Spatial DB(예: GeoPackage)로 지역/핫스팟 좌표를 옮기고, Seoul HOTSPOT API 외 추가 데이터(예: 유동인구 API)를 scheduler(curl/cron/Task Scheduler) 기반으로 연동하여 파이프라인 신뢰성을 높일 것.

## 10. 최근 변경 요약 (2026-03-14)
1. 서울시 핫스팟 기준 데이터를 120개에서 122개 기준으로 전환하고 파생 파일(`서울시_122개_hotspot.csv`, `서울시_122개_geodata.csv`)을 갱신.
2. 루트 실행 진입점(`main.py`)을 도입해 협업자가 저장소 루트에서 동일한 명령으로 앱을 실행할 수 있도록 표준화.
3. 실시간 수집기/ORM 스키마를 보강(`area_code`, `active`)해 upsert 및 비활성 처리까지 반영.
4. `hotspot.py` 위험도 로직 중 사용자 슬라이더를 제거하고 강력범죄 기준을 고정값으로 정리.
5. 저장소 정리 정책을 적용해 로컬 산출물(`crime_db.db` 등)은 제외하고 실행 필수 코드/데이터 중심으로 추적.
6. 핫스팟 페이지에 수동 데이터 갱신 버튼을 추가하고, 수집기 함수를 앱 내부에서 1회 실행해 즉시 DB를 갱신하도록 연결.
7. 수집기 실행 안정화를 위해 테이블 자동 생성/1회 실행 옵션/테스트 범위 제한 옵션을 반영하고, 경로/캐시 관련 운영 이슈를 문서화.
8. Streamlit Cloud 자동 반영을 위해 GitHub Actions 워크플로(`.github/workflows/hotspot-sync.yml`)를 추가하고 30분 주기 수집 → DB 커밋/푸시 파이프라인을 구성.
9. 핫스팟 페이지 헤더에서 수동 업데이트 버튼의 위치를 ‘혼잡도 기준/시간’ 영역과 함께 노출하도록 UI를 조정하고 여백 상수로 위치 튜닝이 가능하게 정리.
10. 자동 수집이 안정화된 이후에는 중복 실행/지연을 피하기 위해 `hotspot.py`의 수동 업데이트 버튼을 제거하고, 화면에는 갱신 시각만 노출하도록 단순화.

## 11. GitHub Actions 자동 수집/배포 흐름 (2026-03-15)
1. 목표: 사람이 버튼을 누르지 않아도, 30분마다 자동으로 데이터를 수집해서 Streamlit 화면이 최신값을 보여주게 만들기.
2. “자동 실행 스위치”는 GitHub에 있는 `.github/workflows/hotspot-sync.yml` 파일이다. 이 파일이 있으면 GitHub가 주기적으로 Python 스크립트를 실행한다.
3. 실행되는 내용은 단순하다: 필요한 패키지를 설치하고 `python -m 4_streamlit.seed.seoul_collector_30min --once`를 한 번 돌린다.
4. 이 스크립트는 서울시 API 키가 필요하다. 그래서 GitHub Secrets에 `SEOUL_API_KEY`를 넣고, 워크플로가 그 값을 읽어 쓴다.
5. 수집이 성공하면 `4_streamlit/crime_db.db` 파일이 바뀐다. 워크플로가 이 파일을 자동으로 커밋/푸시한다.
6. Streamlit Cloud는 GitHub의 `main` 브랜치를 보고 있으니, 새 커밋이 올라오면 몇 분 안에 최신 DB로 화면이 갱신된다.
7. 자주 막히는 포인트는 두 가지다:
   - API 키가 틀리면 “AREA_NM 없음” 같은 경고가 뜬다. 이때 로그에 `INFO-xxx` 코드가 나오니 그 코드를 보면 원인을 알 수 있다.
   - GitHub Actions가 커밋하려면 Repository Settings에서 `Workflow permissions`를 `Read and write`로 켜야 한다.
8. 수동으로 바로 실행해 보고 싶다면 Actions 탭에서 `Hotspot Sync` → `Run workflow`를 누르면 된다. 이 실행이 성공하면 DB 커밋이 생기고 Streamlit도 따라 바뀐다.
