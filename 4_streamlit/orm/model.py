"""ORM 모델 정의: DB 테이블과 매핑되는 SQLAlchemy 클래스들입니다."""

from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

# 3. ORM 클래스 정의 (기존 구조 그대로)

class RegionMaster(Base):
    """지역 마스터 (예: 서울 강남구, 서울 종로구)"""
    __tablename__ = 'region_master'
    id = Column(Integer, primary_key=True, autoincrement=True)
    region_name = Column(String, unique=True, nullable=False)
    mappers = relationship("RegionMapper", back_populates="region")
    region_crimes = relationship("CrimeRegion", back_populates="region")

class CrimeCategory(Base):
    """범죄 종류 마스터 (예: 절도, 폭행)"""
    __tablename__ = 'crime_category'
    id = Column(Integer, primary_key=True, autoincrement=True)
    main_cat = Column(String)
    sub_cat = Column(String, unique=True)
    region_stats = relationship("CrimeRegion", back_populates="category")
    time_stats = relationship("CrimeTime", back_populates="category")
    week_stats = relationship("CrimeWeek", back_populates="category")

class RegionMapper(Base):
    """핫스팟과 지역 마스터를 잇는 중간 다리"""
    __tablename__ = 'region_mapper'
    id = Column(Integer, primary_key=True, autoincrement=True)
    AREA_GU = Column(String)
    CATEGORY = Column(String)
    NO = Column(Integer)
    AREA_CD = Column(String)
    AREA_NM = Column(String)
    ENG_NM = Column(String)
    hotspot_id = Column(Integer, ForeignKey('hotspot_api.id'))
    region_id = Column(Integer, ForeignKey('region_master.id'))
    hotspot = relationship("HotspotAPI", back_populates="mapper")
    region = relationship("RegionMaster", back_populates="mappers")

class HotspotAPI(Base):
    """핫스팟 API 정보"""
    __tablename__ = 'hotspot_api'
    id = Column(Integer, primary_key=True, autoincrement=True)
    area_name = Column(String, index=True)
    area_code = Column(String, index=True)
    congest_lvl = Column(Integer)
    ppltn_min = Column(Integer)
    ppltn_max = Column(Integer)
    temp = Column(Float)
    update_time = Column(String)
    collected_at = Column(String)
    active = Column(Integer, default=1)
    mapper = relationship("RegionMapper", back_populates="hotspot")

class CrimeRegion(Base):
    """지역별 범죄 통계"""
    __tablename__ = 'crime_region'
    id = Column(Integer, primary_key=True, autoincrement=True)
    crime_count = Column(Integer)
    region_id = Column(Integer, ForeignKey('region_master.id'))
    category_id = Column(Integer, ForeignKey('crime_category.id'))
    region = relationship("RegionMaster", back_populates="region_crimes")
    category = relationship("CrimeCategory", back_populates="region_stats")

class CrimeTime(Base):
    """시간대별 범죄 통계"""
    __tablename__ = 'crime_time'
    id = Column(Integer, primary_key=True, autoincrement=True)
    time_range = Column(String)
    crime_count = Column(Float)
    category_id = Column(Integer, ForeignKey('crime_category.id'))
    category = relationship("CrimeCategory", back_populates="time_stats")

class CrimeWeek(Base):
    """요일별 범죄 통계"""
    __tablename__ = 'crime_week'
    id = Column(Integer, primary_key=True, autoincrement=True)
    day_of_week = Column(String)
    crime_count = Column(Integer)
    category_id = Column(Integer, ForeignKey('crime_category.id'))
    category = relationship("CrimeCategory", back_populates="week_stats")
