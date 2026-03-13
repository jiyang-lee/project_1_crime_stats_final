import streamlit as st
import base64
import os

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")

def img_to_b64(path):
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()

# ── CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;900&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif !important; }
.main { background-color: #f4f6fa; }
.block-container {
    max-width: 1344px !important;
    margin-left: auto !important;
    margin-right: auto !important;
    padding-top: 1rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    padding-bottom: 2rem !important;
}



/* 캐러셀 iframe 컨테이너 확장 ← 여기 숫자(95vw)를 바꾸면 캐러셀 크기 조절 */
div[data-testid="stIframe"] {
    width: 95vw !important;
    max-width: none !important;
    position: relative !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
}

/* 네비 버튼 스타일 */
div[data-testid="stPageLink"] a {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    background: #ffffff !important;
    border: 1.5px solid #dde6f0 !important;
    border-radius: 30px !important;
    padding: 10px 0 !important;
    font-size: 14px !important;
    font-weight: 700 !important;
    color: #1E3A5F !important;
    text-decoration: none !important;
    box-shadow: 0 2px 6px rgba(20,60,110,0.08) !important;
    transition: all 0.2s !important;
}
div[data-testid="stPageLink"] a:hover {
    background: #e8f0fb !important;
    color: #1E3A5F !important;
    border-color: #a8c4e8 !important;
}

/* 통계 배너 */
.stat-banner {
    background: linear-gradient(135deg, #1E3A5F 0%, #2a5298 100%);
    border-radius: 20px; padding: 32px 20px; margin: 20px 0;
    display: flex; justify-content: space-around; align-items: center;
    box-sizing: border-box; width: 100%;
}
.stat-item { text-align: center; }
.stat-num { font-size: 34px; font-weight: 900; color: #ffffff; }
.stat-label { font-size: 13px; color: #a8c5e0; margin-top: 6px; font-weight: 600; letter-spacing: 0.5px; }
.stat-divider { width: 1px; height: 54px; background: rgba(255,255,255,0.2); }

/* 소개 카드 공통 */
.intro-card {
    background: #ffffff; border-radius: 18px; padding: 28px 24px;
    box-shadow: 0 2px 12px rgba(20,60,110,0.08);
    border-top: 4px solid #1E3A5F; height: 100%; min-height: 260px; box-sizing: border-box;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    cursor: default; display: flex; flex-direction: column;
}
.intro-card:hover {
    transform: translateY(-6px);
    box-shadow: 0 10px 28px rgba(20,60,110,0.16);
}
.intro-card h3 { font-size: 16px; font-weight: 800; color: #12263a; margin: 10px 0 10px 0; }
.intro-card p  { font-size: 13px; color: #5a7080; line-height: 1.7; margin: 0; }
.intro-icon    { font-size: 32px; }

/* 하이라이트 박스 */
.highlight-box {
    background: linear-gradient(120deg, #e8f0fe 0%, #f0f4ff 100%);
    border-left: 5px solid #1E3A5F; border-radius: 12px;
    padding: 20px 24px; margin: 0; box-sizing: border-box;
    height: 100%; min-height: 200px;
}
.highlight-box h4 { font-size: 15px; font-weight: 800; color: #1E3A5F; margin: 0 0 8px 0; }
.highlight-box p  { font-size: 13px; color: #3a5070; line-height: 1.7; margin: 0; }

/* 범죄 유형 태그 */
.crime-tags { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }
.crime-tag {
    background: #1E3A5F; color: #ffffff; border-radius: 20px;
    padding: 5px 14px; font-size: 12px; font-weight: 700; letter-spacing: 0.3px;
}

/* 섹션 제목 */
.section-title {
    display: flex; align-items: center; gap: 12px;
    font-size: 17px; font-weight: 800; color: #12263a;
    margin: 24px 0 12px 0;
}
.section-title::after {
    content: ''; flex: 1; height: 2px;
    background: linear-gradient(90deg, #1E3A5F 0%, rgba(30,58,95,0) 100%);
    border-radius: 2px;
}

/* 데이터 출처 카드 */
.source-card {
    background: #ffffff; border-radius: 14px; padding: 18px 22px;
    box-shadow: 0 1px 8px rgba(20,60,110,0.07); box-sizing: border-box;
    display: flex; align-items: flex-start; gap: 14px;
}
.source-icon { font-size: 26px; flex-shrink: 0; margin-top: 2px; }
.source-title { font-size: 14px; font-weight: 800; color: #12263a; margin-bottom: 4px; }
.source-desc  { font-size: 12px; color: #7a90a8; line-height: 1.6; }
.source-card-0 { border-top: 3px solid #1E3A5F; }
.source-card-1 { border-top: 3px solid #2a7ae2; }
.source-card-2 { border-top: 3px solid #17a589; }

/* 푸터 */
.footer { text-align: center; font-size: 12px; color: #a0b4c8; margin-top: 36px; padding-top: 18px; border-top: 1px solid #e4edf5; }

/* 사이드바 */
section[data-testid="stSidebar"] { background: #1E3A5F; border-right: 1px solid #1e3d5c; }
section[data-testid="stSidebar"] * { color: #cce0f5 !important; }
</style>
""", unsafe_allow_html=True)

# ── 헤더 ────────────────────────────────────────────────────────────
st.markdown("""
<div style='text-align:center;font-size:11px;font-weight:700;color:#1a6fc4;letter-spacing:2.5px;margin-bottom:8px;'>SEOUL CRIME ANALYSIS DASHBOARD</div>
<div style='display:flex;align-items:center;justify-content:center;gap:14px;margin-bottom:4px;'>
  <div style='flex:1;height:1.5px;background:linear-gradient(90deg,transparent 0%,#1E3A5F 100%);'></div>
  <div style='text-align:center;font-size:40px;font-weight:900;color:#12263a;white-space:nowrap;'>범죄 현황 분석 시스템</div>
  <div style='flex:1;height:1.5px;background:linear-gradient(90deg,#1E3A5F 0%,transparent 100%);'></div>
</div>
<div style='text-align:center;font-size:13px;color:#8fa8c0;margin-bottom:6px;'>경찰청 공공데이터 기반 &nbsp;·&nbsp; 서울 25개 자치구 + 경기도 1개 시 &nbsp;·&nbsp; 2024년 기준</div>
""", unsafe_allow_html=True)

import streamlit.components.v1 as _c
_c.html("""
<div style="text-align:center;padding:0 0 10px 0;">
  <div id="lc" style="font-size:12px;color:#a8c5e0;font-family:'Noto Sans KR',sans-serif;letter-spacing:0.5px;"></div>
</div>
<script>
(function(){
  var days=['일','월','화','수','목','금','토'];
  function tick(){
    var n=new Date();
    var HH=String(n.getHours()).padStart(2,'0');
    var MM=String(n.getMinutes()).padStart(2,'0');
    var SS=String(n.getSeconds()).padStart(2,'0');
    document.getElementById('lc').textContent=
      n.getFullYear()+'년 '+(n.getMonth()+1)+'월 '+n.getDate()+'일 ('+days[n.getDay()]+')  '+HH+':'+MM+':'+SS;
  }
  tick(); setInterval(tick,1000);
})();
</script>
""", height=30, scrolling=False)

# ── 네비게이션 ────────────────────────────────────────────────────────
nav0, nav1, nav2, nav3 = st.columns(4)
with nav0:
    st.page_link("pages/hotspot.py", label="📍  핫스팟 분석", use_container_width=True)
with nav1:
    st.page_link("pages/time.py",    label="🕐  시간대 분석", use_container_width=True)
with nav2:
    st.page_link("pages/week.py",    label="📅  요일 분석",   use_container_width=True)
with nav3:
    st.page_link("pages/region.py",  label="🗺️  지역 분석",   use_container_width=True)

st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)

# ── 캐러셀 ──────────────────────────────────────────────────────────
_i1 = img_to_b64(os.path.join(BASE, "pic1.png"))
_i2 = img_to_b64(os.path.join(BASE, "pic2.png"))
_i3 = img_to_b64(os.path.join(BASE, "pic3.png"))
import streamlit.components.v1 as components
components.html(f"""
<div style="width:100%;margin:0;">
  <div id="hc" style="position:relative;overflow:hidden;border-radius:20px;height:450px;background:#eee;">
    <div id="hc-track" style="display:flex;height:100%;transition:transform 0.5s ease;">
      <div class="hc-slide"><img src="{_i1}" style="width:100%;height:450px;object-fit:cover;display:block;"></div>
      <div class="hc-slide"><img src="{_i2}" style="width:100%;height:450px;object-fit:cover;display:block;"></div>
      <div class="hc-slide"><img src="{_i3}" style="width:100%;height:450px;object-fit:cover;display:block;"></div>
    </div>
    <button onclick="hcPrev()" style="position:absolute;left:14px;top:50%;transform:translateY(-50%);background:rgba(255,255,255,0.85);border:none;border-radius:50%;width:38px;height:38px;font-size:20px;cursor:pointer;z-index:10;">&#8249;</button>
    <button onclick="hcNext()" style="position:absolute;right:14px;top:50%;transform:translateY(-50%);background:rgba(255,255,255,0.85);border:none;border-radius:50%;width:38px;height:38px;font-size:20px;cursor:pointer;z-index:10;">&#8250;</button>
    <div style="position:absolute;bottom:14px;left:50%;transform:translateX(-50%);display:flex;gap:8px;">
      <span id="hd0" style="width:22px;height:3px;background:#fff;border-radius:2px;cursor:pointer;" onclick="hcGo(0)"></span>
      <span id="hd1" style="width:22px;height:3px;background:#fff;border-radius:2px;opacity:0.45;cursor:pointer;" onclick="hcGo(1)"></span>
      <span id="hd2" style="width:22px;height:3px;background:#fff;border-radius:2px;opacity:0.45;cursor:pointer;" onclick="hcGo(2)"></span>
    </div>
  </div>
</div>
<script>
var _idx=0,_n=3,_w=0;
function _hcSetW(){{
  _w = document.getElementById('hc').offsetWidth;
  var slides = document.querySelectorAll('.hc-slide');
  slides.forEach(function(s){{ s.style.width=_w+'px'; s.style.minWidth=_w+'px'; s.style.flexShrink='0'; }});
  _hcUpd();
}}
function _hcUpd(){{
  var t=document.getElementById('hc-track');
  if(t) t.style.transform='translateX(-'+(_idx*_w)+'px)';
  for(var i=0;i<_n;i++){{
    var d=document.getElementById('hd'+i);
    if(d) d.style.opacity=i===_idx?'1':'0.45';
  }}
}}
function hcNext(){{_idx=(_idx+1)%_n;_hcUpd();}}
function hcPrev(){{_idx=(_idx-1+_n)%_n;_hcUpd();}}
function hcGo(i){{_idx=i;_hcUpd();}}
window.addEventListener('load', _hcSetW);
window.addEventListener('resize', _hcSetW);
setTimeout(_hcSetW, 100);
setInterval(hcNext,5000);
</script>
""", height=452, scrolling=False)

# ── 프로젝트 소개 ────────────────────────────────────────────────────
st.markdown("<div class='section-title'>📌 분석 메뉴 안내</div>", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
cards = [
    ("📍", "핫스팟 분석",   "pages/hotspot.py",
     "서울 시내 120여 개 주요 장소를 지도 위에 시각화합니다. 범죄 유형별 위험 반경을 히트맵으로 확인하세요."),
    ("🕐", "시간대 분석",   "pages/time.py",
     "0시~23시 각 시간대별 범죄 발생 패턴을 분석합니다. 어느 시간대가 가장 위험한지 한눈에 파악하세요."),
    ("📅", "요일 분석",     "pages/week.py",
     "월~일 요일별 범죄 발생 추이를 비교합니다. 주말과 주중의 범죄 패턴 차이를 확인할 수 있습니다."),
    ("🗺️", "지역 분석",    "pages/region.py",
     "서울 25개 자치구 + 경기도 1개 시 범죄 발생 현황을 비교합니다. 구별 범죄 집중도를 순위와 차트로 확인하세요."),
]
for col, (icon, title, page, desc) in zip([c1, c2, c3, c4], cards):
    with col:
        st.markdown(f"""
<div class='intro-card'>
  <div class='intro-icon'>{icon}</div>
  <h3>{title}</h3>
  <p>{desc}</p>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

# ── 분석 범죄 유형 + 데이터 개요 ────────────────────────────────────
left, right = st.columns([1, 1])

with left:
    st.markdown("""
<div class='highlight-box'>
  <h4>🔍 분석 대상 범죄 5종</h4>
  <p>본 시스템은 경찰청 공공데이터 기준 5대 범죄를 중심으로 분석합니다.<br>
  각 범죄 유형은 발생 건수 기준으로 시간·요일·지역을 교차 분석하여 패턴을 도출합니다.</p>
  <div class='crime-tags'>
    <span class='crime-tag'>🔪 강도</span>
    <span class='crime-tag'>💥 폭력</span>
    <span class='crime-tag'>🚗 절도</span>
    <span class='crime-tag'>⚠️ 살인</span>
    <span class='crime-tag'>🚨 성범죄</span>
  </div>
</div>
""", unsafe_allow_html=True)

with right:
    st.markdown("""
<div class='highlight-box'>
  <h4>📊 데이터 개요</h4>
  <p>
  · 기준 연도 : 2024년<br>
  · 공간 범위 : 서울특별시 25개 자치구 + 경기도 1개 시<br>
  · 시간 단위 : 0시 ~ 23시 (3시간 간격)<br>
  · 요일 범위 : 월요일 ~ 일요일<br>
  · 핫스팟 : 서울시 주요 120개 장소
  </p>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

# ── 데이터 출처 ──────────────────────────────────────────────────────
st.markdown("<div class='section-title'>📂 데이터 출처</div>", unsafe_allow_html=True)

s1, s2, s3 = st.columns(3)
sources = [
    ("🏛️", "경찰청 공공데이터포털",
     "5대 범죄(살인·강도·절도·폭력·성범죄) 발생 건수\n서울 25개 자치구 × 시간대 × 요일별 집계 데이터"),
    ("🗺️", "서울시 공간정보 오픈플랫폼",
     "서울시 자치구 경계 Shapefile\n주요 120개 장소 위경도 좌표 및 영역 정보"),
    ("📡", "실시간 유동인구 API",
     "서울시 주요 120개 핫스팟 지점의\n30분 단위 실시간 유동인구 수집 데이터"),
]
for i, (col, (icon, title, desc)) in enumerate(zip([s1, s2, s3], sources)):
    with col:
        st.markdown(f"""
<div class='source-card source-card-{i}'>
  <div class='source-icon'>{icon}</div>
  <div>
    <div class='source-title'>{title}</div>
    <div class='source-desc'>{desc.replace(chr(10), '<br>')}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── 푸터 ────────────────────────────────────────────────────────────
st.markdown("""
<div class='footer'>
  데이터 출처 : 경찰청 공공데이터포털 &nbsp;|&nbsp; 서울 25개 자치구 + 과천시 포함 &nbsp;|&nbsp; 본 대시보드는 학습 목적으로 제작되었습니다.
</div>
""", unsafe_allow_html=True)