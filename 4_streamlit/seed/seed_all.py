import sys
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(BASE_DIR)

from orm.database import SessionLocal, create_database, get_db
from orm.model import RegionMaster, CrimeCategory, CrimeRegion, CrimeTime, CrimeWeek, RegionMapper


REGION_DATA_PATH = os.path.join(BASE_DIR, "data", "police_region_fix.csv")
WEEK_DATA_PATH = os.path.join(BASE_DIR, "data", "police_week_fix.csv")
TIME_DATA_PATH = os.path.join(BASE_DIR, "data", "police_time_fix.csv")
MAPPING_DATA_PATH = os.path.join(BASE_DIR, "data", "mapping_fix.csv")

### 1. Region_master 함수 ###

def seed_region_master():

    df_region_master = pd.read_csv(
        REGION_DATA_PATH,
        encoding="utf-8-sig"
    )

    insert_master = df_region_master["지역"].unique()

    with get_db() as db:

        if db.query(RegionMaster).first():
            print("RegionMaster already seeded")
            return

        regions = [RegionMaster(region_name=r) for r in insert_master]

        db.add_all(regions)   # bulk_save_objects 대신 이걸 추천

        print("RegionMaster seed 완료")
        print("insert rows:", len(regions))

### 2. Crime_category 함수 ###

def seed_crime_category():

    df_crime_category = pd.read_csv(
        REGION_DATA_PATH,
        encoding="utf-8-sig"
    )

    insert_category = list(df_crime_category[['범죄대분류', '범죄중분류']].drop_duplicates().itertuples(index=False, name=None))

    with get_db() as db:

        if db.query(CrimeCategory).first():
            print("CrimeCategory already seeded")
            return

        crimes = [CrimeCategory(main_cat=r[0], sub_cat=r[1]) for r in insert_category]

        db.add_all(crimes)   # bulk_save_objects 대신 이걸 추천

        print("CrimeCategory seed 완료")
        print("insert rows:", len(crimes))


### 3. 매핑 테이블 ###
def seed_region_mapper():
    df = pd.read_csv(MAPPING_DATA_PATH, encoding="utf-8-sig")

    with get_db() as db:
        if db.query(RegionMapper).first():
            print("RegionMapper already seeded")
            return

        # region_id 매핑 (AREA_GU → region_master.id)
        region_map = {r.region_name: r.id for r in db.query(RegionMaster).all()}

        mappers = [
            RegionMapper(
                AREA_GU    = row['AREA_GU'],
                CATEGORY   = row['CATEGORY'],
                NO         = row['NO'],
                AREA_CD    = row['AREA_CD'],
                AREA_NM    = row['AREA_NM'],
                ENG_NM     = row['ENG_NM'],
                region_id  = region_map.get(row['AREA_GU']),  # 없으면 None
                hotspot_id = None  # seed_HotspotAPI.py 실행 후 채워짐
            )
            for _, row in df.iterrows()
        ]

        # 서울 외 지역 경고
        null_count = sum(1 for m in mappers if m.region_id is None)
        if null_count:
            print(f"⚠️  region_id NULL {null_count}건 (서울 외 지역)")

        db.add_all(mappers)

        print("RegionMapper seed 완료")
        print("insert rows:", len(mappers))


def seed_crime_region():
    df = pd.read_csv(REGION_DATA_PATH, encoding="utf-8-sig")

    with get_db() as db:
        if db.query(CrimeRegion).first():
            print("CrimeRegion already seeded")
            return

        region_map   = {r.region_name: r.id for r in db.query(RegionMaster).all()}
        category_map = {c.sub_cat: c.id     for c in db.query(CrimeCategory).all()}

        crimes = [
            CrimeRegion(
                crime_count = row['범죄건수'],
                region_id   = region_map.get(row['지역']),
                category_id = category_map.get(row['범죄중분류'])
            )
            for _, row in df.iterrows()
        ]
        db.add_all(crimes)

        print("CrimeRegion seed 완료")
        print("insert rows:", len(crimes))


def seed_crime_time():
    df = pd.read_csv(TIME_DATA_PATH, encoding="utf-8-sig")

    with get_db() as db:
        if db.query(CrimeTime).first():
            print("CrimeTime already seeded")
            return

        category_map = {c.sub_cat: c.id for c in db.query(CrimeCategory).all()}

        times = [
            CrimeTime(
                time_range  = row['시간대2'],
                crime_count = row['범죄건수'],
                category_id = category_map.get(row['범죄중분류'])
            )
            for _, row in df.iterrows()
        ]
        db.add_all(times)

        print("CrimeTime seed 완료")
        print("insert rows:", len(times))


def seed_crime_week():
    df = pd.read_csv(WEEK_DATA_PATH, encoding="utf-8-sig")

    with get_db() as db:
        if db.query(CrimeWeek).first():
            print("CrimeWeek already seeded")
            return

        category_map = {c.sub_cat: c.id for c in db.query(CrimeCategory).all()}

        weeks = [
            CrimeWeek(
                day_of_week = row['요일'],
                crime_count = row['발생건수'],
                category_id = category_map.get(row['범죄중분류'])
            )
            for _, row in df.iterrows()
        ]
        db.add_all(weeks)

        print("CrimeWeek seed 완료")
        print("insert rows:", len(weeks))


def seed_all():
    print("DB 테이블 생성...")

    create_database()

    print("Seeding RegionMaster...")
    seed_region_master()

    print("Seeding CrimeCategory...")
    seed_crime_category()
    
    print("Seeding RegionMapper...")
    seed_region_mapper()

    print("Seeding CrimeRegion...")
    seed_crime_region()

    print("Seeding CrimeTime...")
    seed_crime_time()

    print("Seeding CrimeWeek...")
    seed_crime_week()

    print("Seed 완료")


if __name__ == "__main__":
    seed_all()