import streamlit as st

st.set_page_config(
    page_title="범죄 분석",
      page_icon="🚓", 
      layout="wide"
)


# 페이지 등록
# title = st.page("파일경로", title='메뉴이름', icon="아이콘")

# 네비게이션
# pg = st.navigation({
#     "메인": [ ],
#     "분석": [ ],
#     "설정": [ ]
# })

# 페이지 실행
# pg.run()


# 1. 홈 화면
home = st.Page("pages/home.py", title='홈')

# 2.
time = st.Page("pages/time.py", title='시간')

# 3. 
week = st.Page("pages/week.py", title='요일')

# 4. 
region = st.Page("pages/region.py", title='지역')

hotspot = st.Page("pages/hotspot.py", title='핫스팟')


# 네비게이션
pg = st.navigation({
    "메인": [home],
    "분석": [hotspot, region, time, week],

})


pg.run()


