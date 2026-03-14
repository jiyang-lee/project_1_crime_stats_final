"""Seoul hotspot collector: OpenAPI에서 실시간 핫스팟을 수집해 DB에 저장합니다."""

import argparse
import importlib
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, cast
from urllib.parse import quote_plus

import pandas as pd
import requests
from bs4 import BeautifulSoup

try:
    import tomllib
except Exception:  # pragma: no cover
    tomllib = None  # type: ignore[assignment]


BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

TOTAL_CYCLE_GAP = 1800
CHUNK_SIZE = 20
BATCH_GAP = 3

SessionLocal = None
HotspotAPI = None
CreateDatabase = None
DB_IMPORT_ERROR = None


def load_api_key() -> str | None:
    key = os.environ.get("SEOUL_API_KEY")
    if key:
        return key.strip()

    secrets_path = BASE_DIR.parent / ".streamlit" / "secrets.toml"
    if tomllib and secrets_path.exists():
        try:
            data = tomllib.loads(secrets_path.read_text(encoding="utf-8"))
            key = data.get("SEOUL_API_KEY")
            if isinstance(key, str) and key.strip():
                return key.strip()
        except Exception as exc:
            logger.warning("secrets.toml 파싱 실패: %s", exc)

    env_path = BASE_DIR.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.strip().startswith("SEOUL_API_KEY="):
                key = line.split("=", 1)[1].strip().strip("\"").strip("'")
                if key:
                    return key

    return None


def load_db_dependencies() -> tuple[Any, Any, Any]:
    global SessionLocal, HotspotAPI, CreateDatabase, DB_IMPORT_ERROR

    if SessionLocal is not None and HotspotAPI is not None and CreateDatabase is not None:
        return cast(Any, SessionLocal), cast(Any, HotspotAPI), cast(Any, CreateDatabase)

    try:
        from orm.database import SessionLocal as session_local  # type: ignore
        from orm.database import create_database as create_database_fn  # type: ignore
        from orm.model import HotspotAPI as hotspot_model  # type: ignore

        SessionLocal = session_local
        HotspotAPI = hotspot_model
        CreateDatabase = create_database_fn
    except Exception as primary_exc:
        try:
            orm_dir = BASE_DIR / "orm"
            if str(orm_dir) not in sys.path:
                sys.path.insert(0, str(orm_dir))
            database_mod = importlib.import_module("database")
            model_mod = importlib.import_module("model")
            SessionLocal = getattr(database_mod, "SessionLocal", None)
            CreateDatabase = getattr(database_mod, "create_database", None)
            HotspotAPI = getattr(model_mod, "HotspotAPI", None)
        except Exception as secondary_exc:
            DB_IMPORT_ERROR = (primary_exc, secondary_exc)

    if SessionLocal is None or HotspotAPI is None or CreateDatabase is None:
        raise RuntimeError(f"DB import failed: {DB_IMPORT_ERROR}")

    return cast(Any, SessionLocal), cast(Any, HotspotAPI), cast(Any, CreateDatabase)


def find_poi_csv() -> str | None:
    data_dir = BASE_DIR / "data"
    if not data_dir.exists():
        return None

    candidates_csv = list(data_dir.glob("*서울시*장소*.csv"))
    candidates_csv_upper = list(data_dir.glob("*서울시*장소*.CSV"))
    candidates = list({str(p): p for p in (candidates_csv + candidates_csv_upper)}.values())

    if not candidates:
        return None

    def score(path_obj: Path) -> int:
        name = path_obj.name
        if "122" in name:
            return 2
        if "120" in name:
            return 1
        return 0

    candidates.sort(key=score, reverse=True)
    return str(candidates[0])


def load_hotspot_names() -> list[str]:
    csv_path = find_poi_csv()
    if not csv_path:
        logger.error("장소 목록 CSV 파일을 찾지 못했습니다. data 폴더를 확인하세요.")
        return []

    logger.info("Using POI list file: %s", csv_path)
    try:
        df = pd.read_csv(csv_path, encoding="utf-8")
    except Exception:
        try:
            df = pd.read_csv(csv_path, encoding="cp949")
        except Exception as exc:
            logger.error("CSV 로드 실패: %s", exc)
            return []

    name_cols = ["장소명", "AREA_NM", "area_name", "name", "장소_명"]
    for col in name_cols:
        if col in df.columns:
            return [str(x).strip() for x in df[col].dropna().astype(str).unique().tolist()]

    first_col = df.columns[0]
    return [str(x).strip() for x in df[first_col].dropna().astype(str).unique().tolist()]


def parse_int(value: str | None) -> int:
    try:
        return int(float(value or 0))
    except Exception:
        return 0


def parse_float(value: str | None) -> float:
    try:
        return float(value or 0.0)
    except Exception:
        return 0.0


def fetch_api_data(hotspot: str, api_key: str) -> dict[str, Any] | None:
    encoded = quote_plus(hotspot)
    url = f"http://openapi.seoul.go.kr:8088/{api_key}/xml/citydata/1/1/{encoded}"

    try:
        response = requests.get(url, timeout=15)
        if response.status_code != 200:
            logger.warning("응답 코드 비정상 (%s): %s", hotspot, response.status_code)
            return None

        soup = BeautifulSoup(response.text, "xml")
        if not soup.find("AREA_NM"):
            result = soup.find("RESULT")
            code_el = result.find("CODE") if result else soup.find("CODE")
            msg_el = result.find("MESSAGE") if result else soup.find("MESSAGE")
            code = code_el.text.strip() if code_el and code_el.text else "-"
            msg = msg_el.text.strip() if msg_el and msg_el.text else "-"
            logger.warning("API 응답에 AREA_NM 없음 (%s): %s %s", hotspot, code, msg)
            return None

        def get_tag_text(tag: str) -> str | None:
            el = soup.find(tag)
            return el.text.strip() if el and el.text else None

        return {
            "area_name": hotspot,
            "area_code": get_tag_text("AREA_CD"),
            "congest_lvl": get_tag_text("AREA_CONGEST_LVL") or "정보없음",
            "ppltn_min": parse_int(get_tag_text("AREA_PPLTN_MIN")),
            "ppltn_max": parse_int(get_tag_text("AREA_PPLTN_MAX")),
            "temp": parse_float(get_tag_text("TEMP")),
            "update_time": get_tag_text("PPLTN_TIME") or "-",
            "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    except Exception as exc:
        logger.error("API 호출 실패 (%s): %s", hotspot, exc)
        return None


def collect_hotspot_data(api_key: str, hotspots: list[str]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    for i in range(0, len(hotspots), CHUNK_SIZE):
        batch = hotspots[i : i + CHUNK_SIZE]
        for name in batch:
            data = fetch_api_data(name, api_key)
            if data:
                results.append(data)
                logger.info("?섏쭛 ?깃났: %s", name)

        if i + CHUNK_SIZE < len(hotspots):
            time.sleep(BATCH_GAP)

    return results


def persist_hotspot_results(
    session_factory: Any,
    hotspot_model: Any,
    hotspots: list[str],
    collected_results: list[dict[str, Any]],
) -> int:
    if not collected_results:
        return 0

    current_names = set(hotspots)
    updated_count = 0
    with session_factory() as db:
        try:
            for item in collected_results:
                area = item.get("area_name")
                obj = db.query(hotspot_model).filter(hotspot_model.area_name == area).first()
                if obj:
                    for key, value in item.items():
                        if hasattr(obj, key):
                            setattr(obj, key, value)
                    setattr(obj, "active", 1)
                else:
                    item_copy = dict(item)
                    item_copy["active"] = 1
                    db.add(hotspot_model(**item_copy))
                updated_count += 1

            db.query(hotspot_model).filter(~hotspot_model.area_name.in_(list(current_names))).update(
                {"active": 0}, synchronize_session=False
            )

            db.commit()
            logger.info("DB upsert ?꾨즺: %d嫄?", updated_count)
        except Exception as exc:
            db.rollback()
            logger.error("DB ????ㅻ쪟: %s", exc)
            return 0

    return updated_count


def run_collection_once(
    api_key: str,
    session_factory: Any,
    hotspot_model: Any,
    hotspots: list[str],
) -> int:
    collected_results = collect_hotspot_data(api_key, hotspots)
    return persist_hotspot_results(session_factory, hotspot_model, hotspots, collected_results)


def run_sync_collector(once: bool = False, max_hotspots: int = 0) -> None:
    api_key = load_api_key()
    if not api_key:
        raise RuntimeError("Missing SEOUL_API_KEY. 환경변수, .streamlit/secrets.toml, .env를 확인하세요.")

    session_factory, hotspot_model, create_database = load_db_dependencies()
    create_database()
    hotspots = load_hotspot_names()
    if not hotspots:
        logger.error("수집할 장소 목록이 없습니다. 종료합니다.")
        return

    if max_hotspots > 0:
        hotspots = hotspots[:max_hotspots]
        logger.info("디버그 모드: 상위 %d개 장소만 수집", len(hotspots))

    logger.info("실시간 핫스팟 수집기 시작")

    while True:
        start_time = time.time()
        collected_results: list[dict[str, Any]] = []

        for i in range(0, len(hotspots), CHUNK_SIZE):
            batch = hotspots[i : i + CHUNK_SIZE]
            for name in batch:
                data = fetch_api_data(name, api_key)
                if data:
                    collected_results.append(data)
                    logger.info("수집 성공: %s", name)

            if i + CHUNK_SIZE < len(hotspots):
                time.sleep(BATCH_GAP)

        if collected_results:
            with session_factory() as db:
                try:
                    current_names = set(hotspots)
                    updated_count = 0
                    for item in collected_results:
                        area = item.get("area_name")
                        obj = db.query(hotspot_model).filter(hotspot_model.area_name == area).first()
                        if obj:
                            for key, value in item.items():
                                if hasattr(obj, key):
                                    setattr(obj, key, value)
                            setattr(obj, "active", 1)
                        else:
                            item_copy = dict(item)
                            item_copy["active"] = 1
                            db.add(hotspot_model(**item_copy))
                        updated_count += 1

                    db.query(hotspot_model).filter(
                        ~hotspot_model.area_name.in_(list(current_names))
                    ).update({"active": 0}, synchronize_session=False)

                    db.commit()
                    logger.info("DB upsert 완료: %d건", updated_count)
                except Exception as exc:
                    db.rollback()
                    logger.error("DB 저장 오류: %s", exc)
        else:
            logger.warning("이번 주기에서 수집 성공 데이터가 없습니다.")

        if once:
            logger.info("1회 실행 모드 종료")
            return

        elapsed = time.time() - start_time
        wait_time = max(0, TOTAL_CYCLE_GAP - elapsed)
        logger.info("수집 주기 완료. %d초 후 재시작", int(wait_time))
        time.sleep(wait_time)


def collect_and_save_once(max_hotspots: int = 0) -> int:
    api_key = load_api_key()
    if not api_key:
        raise RuntimeError("Missing SEOUL_API_KEY. 환경변수 또는 secrets에 세팅하세요.")

    session_factory, hotspot_model, create_database = load_db_dependencies()
    create_database()
    hotspots = load_hotspot_names()
    if not hotspots:
        logger.error("수집할 장소 목록이 없습니다.")
        return 0

    if max_hotspots > 0:
        hotspots = hotspots[:max_hotspots]
        logger.info("수집 범위 제한: 상위 %d 장소만 수집", len(hotspots))

    return run_collection_once(api_key, session_factory, hotspot_model, hotspots)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seoul hotspot collector")
    parser.add_argument("--once", action="store_true", help="한 번만 수집하고 종료")
    parser.add_argument("--max-hotspots", type=int, default=0, help="테스트용 수집 장소 개수 제한")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    try:
        run_sync_collector(once=args.once, max_hotspots=max(0, args.max_hotspots))
    except KeyboardInterrupt:
        logger.info("수집기 수동 종료")
