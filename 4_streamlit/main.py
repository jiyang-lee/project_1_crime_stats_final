import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
PAGES_DIR = BASE_DIR / "pages"


st.set_page_config(
    page_title="범죄 분석",
      page_icon="🚓", 
      layout="wide"
)

# 네비게이션
home = st.Page(str(PAGES_DIR / "home.py"), title='홈')
time = st.Page(str(PAGES_DIR / "time.py"), title='시간')
week = st.Page(str(PAGES_DIR / "week.py"), title='요일')
region = st.Page(str(PAGES_DIR / "region.py"), title='지역')
hotspot = st.Page(str(PAGES_DIR / "hotspot.py"), title='핫스팟')
admin = st.Page(str(PAGES_DIR / "admin.py"), title="관리자")

pg = st.navigation({
  "메인": [home],
  "분석": [hotspot, region, time, week],
  "관리": [admin],
})


pg.run()
