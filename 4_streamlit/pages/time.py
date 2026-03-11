import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime
from sqlalchemy import func  # 통계 쿼리(Count, Sum, Avg 등)를 짤 때 필요

# 프로젝트 내부 모듈
from orm.database import engine, SessionLocal, get_db
from orm.model import RegionMaster, CrimeCategory, HotspotAPI, CrimeRegion, CrimeTime, CrimeWeek # 필요한 모델들

@st.cache_data  # 데이터 로딩 결과를 메모리에 저장!
def load_crime_data():
    with get_db() as db:
        # DB에서 데이터를 읽어와서 DataFrame으로 변환하는 무거운 작업
        query = "SELECT * FROM crime_category"
        df = pd.read_sql(query, db.bind)
    return df

# 앱 실행 시 호출
data = load_crime_data() # 처음엔 느리지만, 두 번째부턴 광속!
st.dataframe(data)


