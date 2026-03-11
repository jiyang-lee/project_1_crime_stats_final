import sys
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(BASE_DIR)

from orm.database import SessionLocal, create_database
from orm.model import RegionMaster

DATA_PATH = os.path.join(BASE_DIR, "data", "police_region_fix.csv")


def seed_region_master():

    df_region_master = pd.read_csv(
        DATA_PATH,
        encoding="utf-8-sig"
    )

    insert_master = df_region_master["지역"].unique()

    db = SessionLocal()

    try:

        if db.query(RegionMaster).first():
            print("RegionMaster already seeded")
            return

        regions = [RegionMaster(region_name=r) for r in insert_master]

        db.bulk_save_objects(regions)

        db.commit()

        print("RegionMaster seed 완료")
        print("insert rows:", len(regions))

    except Exception as e:
        db.rollback()
        print("seed 실패:", e)

    finally:
        db.close()


def seed_all():
    print("DB 테이블 생성...")
    create_database()

    print("Seeding RegionMaster...")
    seed_region_master()

    print("Seed 완료")


if __name__ == "__main__":
    create_database()
    seed_all()