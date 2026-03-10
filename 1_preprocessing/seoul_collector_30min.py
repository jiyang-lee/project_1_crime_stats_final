

##################################3
import requests
import time
import os
import logging
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd
from bs4 import BeautifulSoup
from sqlalchemy import create_engine

# ---------------------------------
# 1. 설정
# ---------------------------------
# Paths and keys (can be overridden with environment variables)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
API_KEY = os.getenv("SEOUL_API_KEY", "[REDACTED_SEOUL_API_KEY]")
CSV_FILE = os.getenv("SEOUL_CSV_FILE", str(PROJECT_ROOT / "data" / "서울시 주요 120장소 목록.csv"))
DB_PATH = os.getenv("SEOUL_DB_PATH", str(PROJECT_ROOT / "data"/"seoul_live_cache.db"))
DB_URL = f"sqlite:///{DB_PATH}"
LIVE_CACHE_CSV = os.getenv("SEOUL_LIVE_CACHE", str(PROJECT_ROOT / "data" / "seoul_live_cache.csv"))

# 수집 간격 설정
TOTAL_CYCLE_GAP = 1800  # 30분 (1800초)
CHUNK_SIZE = 20         # 20개씩 끊어서 호출 (서버 과부하 방지)
BATCH_GAP = 3           # 배치 사이 쉬는 시간

engine = create_engine(DB_URL)

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Ensure data directories exist before creating DB/CSV
DB_PARENT = Path(DB_PATH).parent
LIVE_PARENT = Path(LIVE_CACHE_CSV).parent
DB_PARENT.mkdir(parents=True, exist_ok=True)
LIVE_PARENT.mkdir(parents=True, exist_ok=True)

engine = create_engine(DB_URL)

# ---------------------------------
# 2. 데이터 로드 및 수집 함수
# ---------------------------------
def load_hotspots():
    try:
        try:
            df = pd.read_csv(CSV_FILE, encoding='utf-8')
        except:
            df = pd.read_csv(CSV_FILE, encoding='cp949')
        # Try common column name, fallback to first column
        if "AREA_NM" in df.columns:
            names = df["AREA_NM"].dropna().unique().tolist()
        else:
            first_col = df.columns[0]
            names = df[first_col].dropna().unique().tolist()
        return [str(x).strip() for x in names]
    except Exception as e:
        logger.exception("장소 목록 로드 실패")
        return []

def fetch_citydata(hotspot):
    # URL-encode hotspot to be safe
    encoded = quote_plus(hotspot)
    url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/xml/citydata/1/1/{encoded}"

    # simple retry logic
    for attempt in range(3):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                logger.warning("비정상 응답 %s for %s (attempt %d)", response.status_code, hotspot, attempt + 1)
                time.sleep(1)
                continue

            soup = BeautifulSoup(response.text, "xml")
            if not soup.find("AREA_NM"):
                return None

            def get_text(tag):
                el = soup.find(tag)
                return el.text.strip() if el and el.text else None

            return {
                "area_name": hotspot,
                "congest_lvl": get_text("AREA_CONGEST_LVL") or "정보없음",
                "ppltn_min": int(get_text("AREA_PPLTN_MIN") or 0),
                "ppltn_max": int(get_text("AREA_PPLTN_MAX") or 0),
                "temp": float(get_text("TEMP") or 0.0),
                "update_time": get_text("PPLTN_TIME") or "-",
                "collected_at": time.strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception:
            logger.exception("fetch_citydata 실패: %s (attempt %d)", hotspot, attempt + 1)
            time.sleep(1)
    return None

# ---------------------------------
# 3. 메인 수집 루프 (30분 주기)
# ---------------------------------
def run_30min_collector():
    hotspots = load_hotspots()
    if not hotspots: return
    logger.info("🚀 서울시 데이터 수집기 가동 (주기: %d초)", TOTAL_CYCLE_GAP)

    try:
        while True:
            start_time = time.time()
            current_cycle_data = []  # 수집된 데이터 리스트

            logger.info("수집 시작: %s", time.strftime('%Y-%m-%d %H:%M:%S'))

            # 장소를 CHUNK_SIZE씩 묶어 순회
            for i in range(0, len(hotspots), CHUNK_SIZE):
                batch = hotspots[i: i + CHUNK_SIZE]
                for hotspot in batch:
                    data = fetch_citydata(hotspot)
                    if data:
                        current_cycle_data.append(data)
                        logger.info("%s 완료", data['area_name'])
                    else:
                        logger.warning("%s 실패", hotspot)

                if i + CHUNK_SIZE < len(hotspots):
                    time.sleep(BATCH_GAP)

            if current_cycle_data:
                df_final = pd.DataFrame(current_cycle_data)
                # CSV 저장
                try:
                    df_final.to_csv(LIVE_CACHE_CSV, index=False, encoding='utf-8-sig')
                except Exception:
                    logger.exception("LIVE_CACHE CSV 저장 실패: %s", LIVE_CACHE_CSV)

                # DB 저장
                try:
                    df_final.to_sql('live_status', con=engine, if_exists='replace', index=False)
                    df_final.to_sql('history_logs', con=engine, if_exists='append', index=False)
                except Exception:
                    logger.exception("DB 저장 실패: %s", DB_PATH)

                logger.info("수집 및 캐싱 완료: 총 %d개 데이터 처리됨", len(df_final))

            elapsed_time = time.time() - start_time
            sleep_time = max(0, TOTAL_CYCLE_GAP - elapsed_time)
            logger.info("다음 수집까지 대기: %d초", int(sleep_time))
            time.sleep(sleep_time)
    except KeyboardInterrupt:
        logger.info("수집기 중단(KeyboardInterrupt)")

if __name__ == "__main__":
    run_30min_collector()
