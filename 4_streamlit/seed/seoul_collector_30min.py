"""Seoul hotspot collector: OpenAPI에서 실시간 핫스팟을 수집해 DB에 저장합니다.

이 모듈은 `data/` 폴더의 POI CSV를 자동으로 찾아 사용합니다.
"""

import os
import sys
import time
import logging
import importlib
from pathlib import Path
from datetime import datetime
from urllib.parse import quote_plus
from typing import Any, cast

import requests
import pandas as pd
from bs4 import BeautifulSoup

# 프로젝트 루트 경로 설정
BASE_DIR = Path(__file__).resolve().parent.parent  # 4_streamlit 폴더 기준
sys.path.append(str(BASE_DIR))

# 로깅
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# DB 관련 객체: SessionLocal, HotspotAPI
SessionLocal = None
HotspotAPI = None
DB_IMPORT_ERROR = None

try:
    orm_dir = BASE_DIR / "orm"
    if str(orm_dir) not in sys.path:
        sys.path.append(str(orm_dir))

    database_mod = importlib.import_module("database")
    model_mod = importlib.import_module("model")
    SessionLocal = getattr(database_mod, "SessionLocal", None)
    HotspotAPI = getattr(model_mod, "HotspotAPI", None)
except Exception as exc:
    DB_IMPORT_ERROR = exc

# ---------------------------------
# 2. 설정
# ---------------------------------
API_KEY = os.environ.get("SEOUL_API_KEY")
if not API_KEY:
    try:
        import streamlit as st
        API_KEY = st.secrets.get("SEOUL_API_KEY")
    except Exception:
        API_KEY = None

if not API_KEY:
    logger.error(
        "Missing SEOUL_API_KEY. Set the SEOUL_API_KEY environment variable or add it to .streamlit/secrets.toml/.env"
    )
    raise RuntimeError("Missing SEOUL_API_KEY environment variable")
# 장소 목록 파일 discovery (현재 폴더 기준으로 재설정)
def find_poi_csv():
    data_dir = BASE_DIR / "data"
    if not data_dir.exists():
        return None

    # Prefer files that look like the updated list (122) then fallback to any 서울시 주요*장소*.csv
    candidates_csv = list(data_dir.glob("*서울시*장소*.csv"))
    candidates_CSV = list(data_dir.glob("*서울시*장소*.CSV"))
    # On Windows, case-insensitive glob can return duplicated paths.
    candidates = list({str(p): p for p in (candidates_csv + candidates_CSV)}.values())
    # prefer filenames containing '122' then '120'
    def score(p):
        name = p.name
        if "122" in name:
            return 2
        if "120" in name:
            return 1
        return 0

    if not candidates:
        return None
    candidates.sort(key=score, reverse=True)
    return str(candidates[0])

TOTAL_CYCLE_GAP = 1800  # 30분
CHUNK_SIZE = 20         # API 과부하 방지 분할 수집
BATCH_GAP = 3


def ensure_db_dependencies() -> tuple[Any, Any]:
    """Return DB session factory and model class, or raise a clear runtime error."""
    if SessionLocal is None or HotspotAPI is None:
        raise RuntimeError(f"DB import failed: {DB_IMPORT_ERROR}")

    return cast(Any, SessionLocal), cast(Any, HotspotAPI)


# ---------------------------------
# 3. 데이터 로드 및 수집 함수
# ---------------------------------
def load_hotspot_names():
    """CSV 파일에서 장소 이름 목록을 가져옵니다.

    Supports files with columns like '장소명', 'AREA_NM' or uses the first column as fallback.
    """
    csv_path = find_poi_csv()
    if not csv_path:
        logger.error("장소 목록 CSV 파일을 찾지 못했습니다. data/ 폴더에 파일을 넣어주세요.")
        return []

    logger.info("Using POI list file: %s", csv_path)
    try:
        df = pd.read_csv(csv_path, encoding='utf-8')
    except Exception:
        try:
            df = pd.read_csv(csv_path, encoding='cp949')
        except Exception as e:
            logger.error("CSV 로드 실패: %s", e)
            return []

    # common korean column names for place name
    name_cols = ["장소명", "AREA_NM", "area_name", "name", "장소_명"]
    for col in name_cols:
        if col in df.columns:
            return [str(x).strip() for x in df[col].dropna().astype(str).unique().tolist()]

    # if there's a '장소코드' and '장소명' pair
    if "장소명" in df.columns and "장소코드" in df.columns:
        return [str(x).strip() for x in df["장소명"].dropna().astype(str).unique().tolist()]

    # fallback to first column
    first_col = df.columns[0]
    return [str(x).strip() for x in df[first_col].dropna().astype(str).unique().tolist()]

def fetch_api_data(hotspot):
    """서울시 API를 호출하여 장소 정보를 가져옵니다."""
    encoded = quote_plus(hotspot)
    url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/xml/citydata/1/1/{encoded}"
    
    try:
        response = requests.get(url, timeout=15)
        if response.status_code != 200: return None
        
        soup = BeautifulSoup(response.text, "xml")
        if not soup.find("AREA_NM"): return None

        def get_tag_text(tag):
            el = soup.find(tag)
            return el.text.strip() if el and el.text else None

        # 모델 필드에 맞게 매핑
        return {
            "area_name": hotspot,
            "congest_lvl": get_tag_text("AREA_CONGEST_LVL") or "정보없음",
            "ppltn_min": int(get_tag_text("AREA_PPLTN_MIN") or 0),
            "ppltn_max": int(get_tag_text("AREA_PPLTN_MAX") or 0),
            "temp": float(get_tag_text("TEMP") or 0.0),
            "update_time": get_tag_text("PPLTN_TIME") or "-",
            "collected_at": datetime.now()
        }
    except Exception as e:
        logger.error("API 호출 실패 (%s): %s", hotspot, e)
        return None

# ---------------------------------
# 4. 메인 실행 루프
# ---------------------------------
def run_sync_collector():
    session_factory, hotspot_model = ensure_db_dependencies()
    hotspots = load_hotspot_names()
    if not hotspots:
        logger.error("수집할 장소 목록이 없습니다. 종료합니다.")
        return

    logger.info("🚀 실시간 핫스팟 수집기 가동 시작")

    while True:
        start_time = time.time()
        collected_results = []

        # 1. 데이터 수집 단계
        for i in range(0, len(hotspots), CHUNK_SIZE):
            batch = hotspots[i: i + CHUNK_SIZE]
            for name in batch:
                data = fetch_api_data(name)
                if data:
                    collected_results.append(data)
                    logger.info("수집 성공: %s", name)
            
            if i + CHUNK_SIZE < len(hotspots):
                time.sleep(BATCH_GAP)

        # 2. DB 업데이트 단계 (SessionLocal 사용) - upsert 방식 및 inactive 마크
        if collected_results:
            with session_factory() as db:
                try:
                    # 현재 CSV에서의 장소 목록 기준으로 active 상태를 관리
                    current_names = set(hotspots)

                    # upsert: 수집된 항목은 추가/갱신, 기존 DB의 항목은 남겨두되 CSV에 없으면 inactive 처리
                    updated_count = 0
                    for item in collected_results:
                        # item may contain area_name; we also try to use area_code if present
                        area = item.get("area_name")
                        obj = db.query(hotspot_model).filter(hotspot_model.area_name == area).first()
                        if obj:
                            # update fields
                            for k, v in item.items():
                                if hasattr(obj, k):
                                    setattr(obj, k, v)
                            setattr(obj, "active", 1)
                        else:
                            # create new object, ensure active=1
                            item_copy = dict(item)
                            item_copy["active"] = 1
                            new_obj = hotspot_model(**item_copy)
                            db.add(new_obj)
                        updated_count += 1

                    # mark DB rows as inactive if their area_name is not in current_names
                    db.query(hotspot_model).filter(
                        ~hotspot_model.area_name.in_(list(current_names))
                    ).update({"active": 0})

                    db.commit()
                    logger.info("✅ DB upsert 완료: %d건 처리; CSV 기준 외 항목은 inactive 처리됨", updated_count)
                except Exception as e:
                    db.rollback()
                    logger.error("❌ DB 저장 오류: %s", e)
        
        # 3. 주기 대기
        elapsed = time.time() - start_time
        wait_time = max(0, TOTAL_CYCLE_GAP - elapsed)
        logger.info("수집 주기 완료. %d초 후 재시작합니다.", int(wait_time))
        time.sleep(wait_time)

if __name__ == "__main__":
    try:
        run_sync_collector()
    except KeyboardInterrupt:
        logger.info("수집기 수동 종료")