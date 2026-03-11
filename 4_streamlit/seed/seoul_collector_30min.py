import requests
import time
import os
import logging
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from datetime import datetime

# 프로젝트 경로 설정을 위한 import
import sys
from pathlib import Path

# 1. 경로 설정 (프로젝트 루트를 파이썬 경로에 추가)
BASE_DIR = Path(__file__).resolve().parent.parent # 4_streamlit 폴더 기준
sys.path.append(str(BASE_DIR))

# database.py와 models.py에서 필요한 객체 임포트
# (파일명이나 경로가 다를 경우 프로젝트 구조에 맞게 수정하세요)
try:
    from orm.database import engine, SessionLocal, get_db
    from orm.model import HotspotAPI
except ImportError:
    # 경로가 다를 경우를 대비한 폴더명 직접 지정 예시
    pass

# ---------------------------------
# 2. 설정
# ---------------------------------
API_KEY = "[REDACTED_SEOUL_API_KEY]"
# 장소 목록 파일 경로 (현재 폴더 기준으로 재설정)
CSV_FILE = os.path.join(BASE_DIR, "data", "서울시 주요 120장소 목록.csv")

TOTAL_CYCLE_GAP = 1800  # 30분
CHUNK_SIZE = 20         # API 과부하 방지 분할 수집
BATCH_GAP = 3

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# ---------------------------------
# 3. 데이터 로드 및 수집 함수
# ---------------------------------
def load_hotspot_names():
    """CSV 파일에서 장소 이름 목록을 가져옵니다."""
    try:
        df = pd.read_csv(CSV_FILE, encoding='utf-8')
    except:
        df = pd.read_csv(CSV_FILE, encoding='cp949')
    
    col = "AREA_NM" if "AREA_NM" in df.columns else df.columns[0]
    return [str(x).strip() for x in df[col].dropna().unique().tolist()]

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
        logger.error(f"API 호출 실패 ({hotspot}): {e}")
        return None

# ---------------------------------
# 4. 메인 실행 루프
# ---------------------------------
def run_sync_collector():
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
                    logger.info(f"수집 성공: {name}")
            
            if i + CHUNK_SIZE < len(hotspots):
                time.sleep(BATCH_GAP)

        # 2. DB 업데이트 단계 (SessionLocal 사용)
        if collected_results:
            with SessionLocal() as db:
                try:
                    # 기존 실시간 정보 삭제 (기존 데이터 비우기)
                    db.execute(HotspotAPI.__table__.delete())
                    
                    # 새로운 데이터 객체 생성 및 삽입
                    new_objects = [HotspotAPI(**item) for item in collected_results]
                    db.add_all(new_objects)
                    
                    db.commit()
                    logger.info(f"✅ DB 업데이트 완료: {len(new_objects)}건 반영")
                except Exception as e:
                    db.rollback()
                    logger.error(f"❌ DB 저장 오류: {e}")
        
        # 3. 주기 대기
        elapsed = time.time() - start_time
        wait_time = max(0, TOTAL_CYCLE_GAP - elapsed)
        logger.info(f"수집 주기 완료. {int(wait_time)}초 후 재시작합니다.")
        time.sleep(wait_time)

if __name__ == "__main__":
    try:
        run_sync_collector()
    except KeyboardInterrupt:
        logger.info("수집기 수동 종료")