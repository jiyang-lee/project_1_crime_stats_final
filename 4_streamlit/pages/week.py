import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime
from sqlalchemy import func  # 통계 쿼리(Count, Sum, Avg 등)를 짤 때 필요

# 프로젝트 내부 모듈
from orm.database import engine, SessionLocal
from orm.model import RegionMaster, CrimeCategory, HotspotAPI, CrimeRegion, CrimeTime, CrimeWeek # 필요한 모델들

st.title("범죄 분석")
st.markdown("""범죄""")