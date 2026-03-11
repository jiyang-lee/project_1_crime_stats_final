from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from model import Base

# 1. DB 경로
DATABASE_URL = "sqlite:///crime_db.db"

# 2. 엔진 생성
engine = create_engine(
    DATABASE_URL,
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
    Base.metadata.create_all(engine)

# 5. DB 세션 반환
def get_db():
    """Streamlit / Python에서 사용할 DB 세션"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()