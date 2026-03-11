from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .model import Base
from contextlib import contextmanager # 추가
import os

# 1. DB 경로
BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH      = os.path.join(BASE_DIR, "crime_db.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# 2. 엔진 생성
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

# 3. 세션 생성
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 4. DB 테이블 생성
def create_database():
    """ORM 테이블 생성"""
    Base.metadata.create_all(bind=engine)

# 5. DB 세션 반환
@contextmanager
def get_db():
    """
    with get_db() as db: 형태로 사용
    → 자동으로 commit/rollback/close 처리
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

