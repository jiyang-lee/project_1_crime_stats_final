import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from orm.database import SessionLocal
from orm.model import HotspotAPI

st.set_page_config(page_title="실시간 범죄 위험도 분석", page_icon="🛡️", layout="wide")

CONGEST_ORDER = {'붐빔': 0, '약간 붐빔': 1, '보통': 2, '여유': 3, '원활': 4}

# 강력범죄 → 여유/원활일수록 위험 (인적 드묾)
# 절도범죄 → 붐빔일수록 위험 (혼잡 틈 소매치기)
CRIME_CONFIG = {
    '🗡️ 강력범죄': {
        'desc':         '살인·강도·강간 등 인적이 드물수록 위험합니다 (혼잡도+인구수 동시 판단)',
        'danger_lvls':  ['여유', '원활'],          # 이 혼잡도가 위험
        'safe_lvls':    ['붐빔', '약간 붐빔'],
        'danger_reason':'여유/원활이면서 인구수가 낮은 경우를 위험으로 봅니다',
        'safe_reason':  '사람이 많아 목격자가 있고 범죄 억제 효과가 있습니다',
        'accent':       '#e11d48',
        'soft':         '#fff1f2',
        'border':       '#fda4af',
        'map_color':    [225, 29, 72],
    },
    '👜 절도범죄': {
        'desc':         '소매치기·날치기 등 혼잡할수록 위험합니다',
        'danger_lvls':  ['붐빔', '약간 붐빔'],     # 이 혼잡도가 위험
        'safe_lvls':    ['여유', '원활'],
        'danger_reason':'혼잡한 틈을 타 소매치기·날치기가 발생하기 쉽습니다',
        'safe_reason':  '한산해서 주변 시야 확보가 쉽고 기회범죄가 줄어듭니다',
        'accent':       '#16a34a',
        'soft':         '#f0fdf4',
        'border':       '#86efac',
        'map_color':    [22, 163, 74],
    },
}

# 강력범죄 저인구 기준(최소 인구수) 고정값
VIOLENT_LOW_POP_THRESHOLD = 5000

CONGEST_STYLE = {
    '붐빔':      {'color':'#e11d48', 'bg':'#fff1f2', 'border':'#fda4af'},
    '약간 붐빔': {'color':'#ea580c', 'bg':'#fff7ed', 'border':'#fdba74'},
    '보통':      {'color':'#2563eb', 'bg':'#eff6ff', 'border':'#93c5fd'},
    '여유':      {'color':'#7c3aed', 'bg':'#f5f3ff', 'border':'#c4b5fd'},
    '원활':      {'color':'#16a34a', 'bg':'#f0fdf4', 'border':'#86efac'},
}

HOTSPOT_COORDS = {
    '강남 MICE 관광특구':(37.5120,127.0596),'동대문 관광특구':(37.5664,127.0093),
    '명동 관광특구':(37.5635,126.9830),'이태원 관광특구':(37.5345,126.9940),
    '잠실 관광특구':(37.5133,127.1000),'종로·청계 관광특구':(37.5704,126.9825),
    '홍대 관광특구':(37.5571,126.9245),'경복궁':(37.5796,126.9770),
    '광화문·덕수궁':(37.5720,126.9768),'보신각':(37.5700,126.9825),
    '북촌한옥마을':(37.5826,126.9830),'창덕궁·종묘':(37.5794,126.9910),
    '가산디지털단지역':(37.4815,126.8826),'강남역':(37.4979,127.0276),
    '건대입구역':(37.5403,127.0699),'교대역':(37.4930,127.0142),
    '구로디지털단지역':(37.4853,126.9012),'국립중앙박물관·용산가족공원':(37.5239,126.9803),
    '낙산공원·이화마을':(37.5796,127.0068),'동대문 DDP':(37.5668,127.0097),
    '뚝섬·성수':(37.5444,127.0556),'망원한강공원':(37.5558,126.8970),
    '목동 운동장·학원가':(37.5257,126.8785),'미아사거리역':(37.6133,127.0294),
    '발산역':(37.5583,126.8384),'북한산':(37.6596,126.9770),
    '사당·이수':(37.4766,126.9815),'서울대입구역':(37.4811,126.9527),
    '서울숲공원':(37.5450,127.0374),'서울식물원·마곡나루역':(37.5594,126.8352),
    '서울역':(37.5554,126.9723),'선릉역':(37.5048,127.0490),
    '성신여대입구역':(37.5928,127.0165),'수서역':(37.4852,127.1028),
    '시청·서울광장':(37.5658,126.9769),'신논현역·논현역':(37.5050,127.0250),
    '신도림역':(37.5082,126.8912),'신림역':(37.4845,126.9291),
    '신촌·이대':(37.5576,126.9369),'압구정로데오거리':(37.5275,127.0396),
    '양재역':(37.4841,127.0341),'여의도공원':(37.5271,126.9243),
    '여의도한강공원':(37.5277,126.9332),'연남동':(37.5620,126.9230),
    '연신내역':(37.6191,126.9196),'영등포 타임스퀘어':(37.5158,126.9047),
    '왕십리역':(37.5614,127.0378),'용산역':(37.5298,126.9648),
    '월드컵공원':(37.5680,126.9005),'이촌한강공원':(37.5225,126.9661),
    '인사동·익선동':(37.5736,126.9874),'잠실한강공원':(37.5109,127.0901),
    '천호역':(37.5387,127.1236),'청량리 제기동':(37.5800,127.0424),
    '합정역':(37.5500,126.9139),'혜화역':(37.5822,127.0016),
    '홍대입구역(2호선)':(37.5571,126.9245),'화곡역':(37.5368,126.8492),
    'DMC(디지털미디어시티)':(37.5766,126.8869),'가락시장':(37.4935,127.1170),
    '가양역':(37.5613,126.8541),'광나루한강공원':(37.5452,127.1148),
    '남산공원':(37.5512,126.9882),'노량진':(37.5133,126.9427),
    '뚝섬한강공원':(37.5305,127.0667),'반포한강공원':(37.5106,126.9998),
    '봉은사역':(37.5146,127.0591),'불광천':(37.5985,126.9275),
    '수유리 먹자골목':(37.6390,127.0256),'독립문역':(37.5721,126.9618),
    '난지한강공원':(37.5703,126.8975),'노원·도봉':(37.6550,127.0630),
}

def load_hotspot():
    with SessionLocal() as db:
        rows = (
            db.query(
                HotspotAPI.area_name, HotspotAPI.congest_lvl,
                HotspotAPI.ppltn_min, HotspotAPI.ppltn_max,
                HotspotAPI.temp,      HotspotAPI.update_time,
                HotspotAPI.collected_at,
            ).all()
        )
    df = pd.DataFrame(rows, columns=['area_name','congest_lvl','ppltn_min','ppltn_max','temp','update_time','collected_at'])
    df['ppltn_avg'] = ((df['ppltn_min'] + df['ppltn_max']) / 2).astype(int)
    df['lat'] = df['area_name'].map(lambda x: HOTSPOT_COORDS.get(x,(None,None))[0])
    df['lon'] = df['area_name'].map(lambda x: HOTSPOT_COORDS.get(x,(None,None))[1])
    df['order'] = df['congest_lvl'].map(lambda x: CONGEST_ORDER.get(x, 9))
    return df.sort_values('order').reset_index(drop=True)

df = load_hotspot()
if df.empty:
    update_time = "-"
    collected_time = "-"
else:
    ts = pd.to_datetime(df["update_time"], errors="coerce")
    latest = ts.max()
    update_time = latest.strftime("%Y-%m-%d %H:%M") if pd.notna(latest) else str(df["update_time"].iloc[0])[:16]
    cs = pd.to_datetime(df["collected_at"], errors="coerce")
    clatest = cs.max()
    collected_time = clatest.strftime("%Y-%m-%d %H:%M") if pd.notna(clatest) else str(df["collected_at"].iloc[0])[:16]
# st.markdown(
#     """
#     <div style="display:flex; flex-direction:column; gap:10px;">
#       <div style="font-size:11px; font-weight:700; letter-spacing:2.5px; color:#1a6fc4;">REAL-TIME RISK ANALYSIS</div>
#       <div style="font-size:32px; font-weight:900; color:#12263a;">핫스팟 실시간 위험도</div>
#       <div style="font-size:14px; color:#8fa8c0;">실시간 혼잡도 API를 기반으로 현장 대응도를 보여줍니다.</div>
#     </div>
#     """,
#     unsafe_allow_html=True,
# )



def classify_risk(df: pd.DataFrame, selected_crime: str, cfg: dict, violent_max_ppl: int):
    """범죄 유형별 위험/안전/기타를 분류합니다."""
    danger_lvls = cfg['danger_lvls']
    safe_lvls = cfg['safe_lvls']

    if selected_crime == '🗡️ 강력범죄':
        # 여유/원활 + 저인구(최소 인구 기준)만 위험으로 분류
        danger_mask = (
            df['congest_lvl'].isin(danger_lvls)
            & (pd.to_numeric(df['ppltn_min'], errors='coerce').fillna(0) < violent_max_ppl)
        )
        # 붐빔/약간붐빔은 안전, 또는 여유/원활이어도 최소인구가 충분히 높으면 안전
        safe_mask = (
            df['congest_lvl'].isin(safe_lvls)
            | (
                df['congest_lvl'].isin(danger_lvls)
                & (pd.to_numeric(df['ppltn_min'], errors='coerce').fillna(0) >= violent_max_ppl)
            )
        )
    else:
        # 절도범죄는 기존 기준 유지: 혼잡할수록 위험
        danger_mask = df['congest_lvl'].isin(danger_lvls)
        safe_mask = df['congest_lvl'].isin(safe_lvls)

    danger_df = df[danger_mask].copy()
    safe_df = df[safe_mask].copy()
    other_df = df[~(danger_mask | safe_mask)].copy()
    return danger_df, safe_df, other_df

# ════════════════════════════════════════════════════════════
# 공통 스타일 (home 제외 다른 페이지와 타이틀 위치 정렬)
# ════════════════════════════════════════════════════════════
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;900&display=swap');

html, body, [class*="css"], .stMarkdown, .stMetric, .stDataFrame, button, input, select {
    font-family: 'Noto Sans KR', sans-serif !important;
}

.main { background-color: #f4f6fa; }
.block-container { padding-top: 2.5rem !important; padding-left: 2.5cm !important; padding-right: 2.5cm !important; }

.page-title {
    font-size: 33px; font-weight: 900; color: #12263a;
    letter-spacing: -0.5px; margin-bottom: 2px;
}
.page-sub {
    font-size: 13px; color: #8fa8c0; margin-bottom: 18px;
    letter-spacing: 0.2px;
}

/* ── 사이드바 ── */
section[data-testid="stSidebar"] {
    background: #1F3B5B;
    border-right: 1px solid #1e3d5c;
}
section[data-testid="stSidebar"] * { color: #cce0f5 !important; }

/* ── 컬럼 간격 ── */
div[data-testid="stHorizontalBlock"] { gap: 1.2rem; }

</style>
""",
    unsafe_allow_html=True,
)

HEADER_SPACER_PX = 30  # increase/decrease this value to nudge the header block downward
st.markdown(f"<div style='height:{HEADER_SPACER_PX}px'></div>", unsafe_allow_html=True)

header_cols = st.columns([20, 2], gap="large")
with header_cols[0]:
    st.markdown(
        """
<div style="display:flex; flex-direction:column; gap:4px;">
  <div style='font-size:11px;font-weight:700;color:#1a6fc4;letter-spacing:2.5px;text-transform:uppercase;'>REAL-TIME RISK ANALYSIS</div>
  <div class='page-title'>🛡️ 실시간 범죄 위험도 분석</div>
  <div class='page-sub'>범죄 유형을 선택하면 실시간 혼잡도 기반으로 위험 장소를 분석합니다</div>
</div>
""",
        unsafe_allow_html=True,
    )
with header_cols[1]:
    st.markdown(
        f"""
<div style="text-align:right; padding-bottom:4px;">
  <div style="font-size:0.66rem; color:#9ca3af; margin-bottom:2px;">혼잡도 기준</div>
  <div style="font-size:0.84rem; font-weight:600; color:#374151;">🕐 {update_time}</div>
  <div style="font-size:0.66rem; color:#9ca3af; margin:6px 0 2px;">수집 시각</div>
  <div style="font-size:0.84rem; font-weight:600; color:#374151;">⏱ {collected_time}</div>
</div>
""",
        unsafe_allow_html=True,
    )

# ════════════════════════════════════════════════════════════
# 범죄 유형 선택 버튼
# ════════════════════════════════════════════════════════════
if 'crime_type' not in st.session_state:
    st.session_state.crime_type = '🗡️ 강력범죄'

btn_cols = st.columns(2, gap="medium")
for col, crime_key in zip(btn_cols, CRIME_CONFIG.keys()):
    cfg      = CRIME_CONFIG[crime_key]
    selected = st.session_state.crime_type == crime_key
    bg       = cfg['accent'] if selected else '#ffffff'
    text_c   = '#ffffff'     if selected else cfg['accent']
    border_c = cfg['accent']
    shadow   = f"0 4px 14px {cfg['accent']}44" if selected else '0 1px 4px rgba(0,0,0,0.06)'

    if col.button(
        crime_key,
        key=f"btn_{crime_key}",
        width="stretch",
    ):
        st.session_state.crime_type = crime_key
        st.rerun()

    # 선택 상태 시각적 표시 (버튼 아래 밑줄)
    if selected:
        col.markdown(f"""
        <div style="height:3px; background:{cfg['accent']};
                    border-radius:2px; margin-top:-8px; margin-bottom:4px;">
        </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='height:0.45rem'></div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# 선택된 범죄 기준 적용
# ════════════════════════════════════════════════════════════
selected_crime = st.session_state.crime_type
cfg            = CRIME_CONFIG[selected_crime]
accent         = cfg['accent']
danger_lvls    = cfg['danger_lvls']
safe_lvls      = cfg['safe_lvls']
r, g, b        = cfg['map_color']

# 강력범죄 임계값은 고정값 사용 (슬라이더 제거)
violent_threshold = VIOLENT_LOW_POP_THRESHOLD if selected_crime == '🗡️ 강력범죄' else 0

# 위험 / 안전 장소 분류
danger_df, safe_df, other_df = classify_risk(df, selected_crime, cfg, violent_threshold)

# TOP 3 정렬 기준
# 강력범죄: 인구가 적을수록 위험(오름차순), 절도범죄: 인구가 많을수록 위험(내림차순)
if selected_crime == '🗡️ 강력범죄':
    top5 = danger_df.sort_values('ppltn_avg', ascending=True).head(3).reset_index(drop=True)
    danger_title = f"{' · '.join(danger_lvls)}"
else:
    top5 = danger_df.sort_values('ppltn_avg', ascending=False).head(3).reset_index(drop=True)
    danger_title = ' · '.join(danger_lvls)

# ── 설명 배너 ─────────────────────────────────────────────────────────────────
# ── 설명 배너 ─────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:{cfg['soft']}; border:1.5px solid {cfg['border']};
            border-left:4px solid {accent}; border-radius:12px;
            padding:0.75rem 1.0rem; margin-bottom:1.05rem;">
  <div style="font-size:0.75rem; font-weight:800; color:{accent}; margin-bottom:5px;">
    ⚠️ 위험한 상황 — {danger_title}
  </div>
  <div style="font-size:0.78rem; color:#374151; line-height:1.65;">
    {cfg['danger_reason']}
  </div>
</div>
""", unsafe_allow_html=True)
# 지도 + TOP 5
# ════════════════════════════════════════════════════════════
map_col, panel_col = st.columns([6, 4], gap="large")

# ── 지도 ─────────────────────────────────────────────────────────────────────
with map_col:
    st.markdown(f'<p style="font-size:0.8rem; font-weight:700; color:#374151; margin-bottom:0.25rem;">🗺️ {danger_title} 지역 집중 표시</p>', unsafe_allow_html=True)

    fig = go.Figure()

    # 위험 장소 (강조)
    d_map = danger_df.dropna(subset=['lat','lon'])
    if not d_map.empty:
        fig.add_trace(go.Scattermapbox(
            lat=d_map['lat'], lon=d_map['lon'], mode='markers',
            marker=dict(
                size=d_map['ppltn_avg'].apply(lambda x: 13 + min(x/8000, 18)),
                color=f'rgba({r},{g},{b},0.88)',
            ),
            text=d_map.apply(lambda row:
                f"<b>{row['area_name']}</b><br>"
                f"혼잡도: {row['congest_lvl']} ⚠️ 위험<br>"
                f"👥 {int(row['ppltn_avg']):,}명",
                axis=1),
            hoverinfo='text',
            name=f"⚠️ 위험 ({danger_title})",
        ))

    # 기타 장소 (흐리게)
    o_map = pd.concat([safe_df, other_df]).dropna(subset=['lat','lon'])
    if not o_map.empty:
        fig.add_trace(go.Scattermapbox(
            lat=o_map['lat'], lon=o_map['lon'], mode='markers',
            marker=dict(
                size=8,
                color='rgba(156,163,175,0.35)',
            ),
            text=o_map.apply(lambda row:
                f"<b>{row['area_name']}</b><br>"
                f"혼잡도: {row['congest_lvl']}<br>"
                f"👥 {int(row['ppltn_avg']):,}명",
                axis=1),
            hoverinfo='text',
            name='기타',
        ))

    fig.update_layout(
        mapbox=dict(style='carto-positron',
                    center=dict(lat=37.5665, lon=126.978), zoom=10.3),
        legend=dict(
            orientation='h', yanchor='top', y=0.99, xanchor='left', x=0.01,
            bgcolor='rgba(255,255,255,0.90)', bordercolor='#e5e7eb', borderwidth=1,
            font=dict(size=10, color='#374151'),
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=480,
        paper_bgcolor='white',
    )
    st.markdown('<div style="border:1px solid #e5e7eb; border-radius:14px; overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,0.07);">', unsafe_allow_html=True)
    st.plotly_chart(fig, width="stretch")
    st.markdown('</div>', unsafe_allow_html=True)

# ── TOP 5 패널 ────────────────────────────────────────────────────────────────
with panel_col:
    st.markdown(f"""
    <p style="font-size:0.8rem; font-weight:700; color:#374151; margin-bottom:0.35rem;">
      ⚠️ 지금 가장 위험한 장소 TOP 3
    </p>
    """, unsafe_allow_html=True)

    if top5.empty:
        st.markdown(f"""
        <div style="background:#f9fafb; border:1px dashed #e5e7eb; border-radius:12px;
                    padding:2rem; text-align:center; color:#9ca3af; font-size:0.85rem;">
          현재 {' · '.join(danger_lvls)} 장소가 없습니다
        </div>
        """, unsafe_allow_html=True)
    else:
        for rank, row in enumerate(top5.itertuples(index=False), start=1):
            ppltn_value = pd.to_numeric(row.ppltn_avg, errors='coerce')
            ppltn_num = int(ppltn_value) if pd.notna(ppltn_value) else 0
            ppltn = f"{ppltn_num:,}"

            temp_value = pd.to_numeric(row.temp, errors='coerce')
            temp_s = f"{float(temp_value):.1f}°C" if pd.notna(temp_value) else "—"

            congest_label = str(row.congest_lvl)
            cs = CONGEST_STYLE.get(congest_label, CONGEST_STYLE['보통'])
            # 인구수 비율로 바 너비 계산
            bar_pct = int(min(ppltn_num / (top5['ppltn_avg'].max() + 1) * 100, 100))

            st.markdown(f"""
            <div style="background:#ffffff; border:1px solid #f0f0f0;
                        border-radius:14px; padding:0.88rem 1.05rem;
                        margin-bottom:0.5rem;
                        box-shadow:0 1px 6px rgba(0,0,0,0.05);">

              <!-- 순위 + 장소명 -->
              <div style="display:flex; align-items:flex-start;
                          justify-content:space-between; margin-bottom:0.6rem;">
                <div style="display:flex; align-items:center; gap:0.55rem;">
                  <div style="width:26px; height:26px; border-radius:8px;
                              background:{accent}; display:flex; align-items:center;
                              justify-content:center; flex-shrink:0;">
                    <span style="font-size:0.75rem; font-weight:800;
                                 color:#ffffff;">{rank}</span>
                  </div>
                  <span style="font-size:0.88rem; font-weight:700; color:#111827;
                               line-height:1.3; word-break:keep-all;">
                    {str(row.area_name)}
                  </span>
                </div>
                <span style="font-size:0.68rem; font-weight:700;
                             color:{cs['color']}; background:{cs['bg']};
                             border:1px solid {cs['border']};
                             border-radius:6px; padding:2px 8px;
                             white-space:nowrap; flex-shrink:0; margin-left:0.4rem;">
                  {congest_label}
                </span>
              </div>

              <!-- 인구수 바 -->
              <div style="margin-bottom:0.5rem;">
                <div style="display:flex; justify-content:space-between;
                            margin-bottom:4px;">
                  <span style="font-size:0.68rem; color:#9ca3af;">현재 인구</span>
                  <span style="font-size:0.72rem; font-weight:700;
                               color:{accent};">👥 {ppltn}명</span>
                </div>
                <div style="background:#f3f4f6; border-radius:4px; height:6px; overflow:hidden;">
                  <div style="background:{accent}; width:{bar_pct}%;
                              height:100%; border-radius:4px;"></div>
                </div>
              </div>

              <!-- 기온 -->
              <div style="font-size:0.68rem; color:#9ca3af;">🌡 {temp_s}</div>

            </div>
            """, unsafe_allow_html=True)

    # 전체 위험 장소 수 요약
    st.markdown(f"""
    <div style="background:{cfg['soft']}; border:1px solid {cfg['border']};
                border-radius:10px; padding:0.75rem 1rem; text-align:center;
                margin-top:0.15rem;">
      <span style="font-size:0.78rem; color:{accent}; font-weight:600;">
        현재 {selected_crime.split()[-1]} 위험 장소
      </span>
      <span style="font-size:1.5rem; font-weight:800; color:{accent};
                   display:block; line-height:1.3;">
        {len(danger_df)}곳
      </span>
      <span style="font-size:0.7rem; color:#9ca3af;">
        전체 {len(df)}개 핫스팟 중
      </span>
    </div>
    """, unsafe_allow_html=True)


