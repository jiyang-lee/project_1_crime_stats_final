import streamlit as st
import pandas as pd
import pydeck as pdk
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from orm.database import get_db
from orm.model import CrimeRegion, CrimeCategory, RegionMaster

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;900&display=swap');

/* ── 전체 폰트 ── */
html, body, [class*="css"], .stMarkdown, .stMetric, .stDataFrame, button, input, select {
    font-family: 'Noto Sans KR', sans-serif !important;
}

/* ── 전체 배경 ── */
.main { background-color: #f4f6fa; }
.block-container { padding-top: 2.5rem !important; padding-left: 2.5cm !important; padding-right: 2.5cm !important; }

/* ── 페이지 타이틀 ── */
.page-title {
    font-size: 33px; font-weight: 900; color: #12263a;
    letter-spacing: -0.5px; margin-bottom: 2px;
}
.page-sub {
    font-size: 13px; color: #8fa8c0; margin-bottom: 18px;
    letter-spacing: 0.2px;
}

/* ── 섹션 구분 타이틀 ── */
.section-title {
    font-size: 26px; font-weight: 800; color: #12263a;
    margin-top: 2rem; margin-bottom: 0.6rem;
    padding-left: 10px;
    border-left: 4px solid #1a6fc4;
}

/* ── 카드 상단 레이블 ── */
.map-label {
    font-size: 13px; font-weight: 700; color: #1a6fc4;
    letter-spacing: 0.3px;
    padding: 8px 4px 10px 4px;
    margin-bottom: 2px;
    border-bottom: 2px solid #e8eef5;
}

/* ── 사이드바 ── */
section[data-testid="stSidebar"] {
    background: #1F3B5B;
    border-right: 1px solid #1e3d5c;
}
section[data-testid="stSidebar"] * { color: #cce0f5 !important; }
section[data-testid="stSidebar"] .stSelectbox > div > div {
    background-color: #1e3d5c !important;
    border: 1px solid #2e5a80 !important;
    border-radius: 8px !important;
}
section[data-testid="stSidebar"] .stSlider > div { padding: 0 4px; }
section[data-testid="stSidebar"] hr {
    border-color: #1e3d5c !important;
    margin: 0.6rem 0 !important;
}
section[data-testid="stSidebar"] h2 {
    font-size: 18px !important;
    font-weight: 800 !important;
    letter-spacing: 0.5px;
    color: #ffffff !important;
}

/* ── 컬럼 간격 ── */
div[data-testid="stHorizontalBlock"] { gap: 1.2rem; }

/* ── st.container(border) 카드 ── */
div[data-testid="stVerticalBlockBorderWrapper"] > div {
    border-radius: 12px !important;
    border: 1px solid #dde6f0 !important;
    box-shadow: 0 2px 10px rgba(20,60,110,0.06) !important;
    background: #ffffff !important;
}

/* ── 메트릭 ── */
div[data-testid="stMetric"] {
    background: transparent;
}
div[data-testid="stMetricLabel"] p { font-size: 12px !important; color: #7a96b0 !important; }
div[data-testid="stMetricValue"] { font-size: 26px !important; font-weight: 800 !important; color: #12263a !important; }

/* ── 버튼 ── */
div[data-testid="stButton"] > button {
    background: #f0f5fb !important;
    border: 1px solid #c8d8ea !important;
    border-radius: 8px !important;
    color: #1a6fc4 !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    transition: all 0.2s;
}
div[data-testid="stButton"] > button:hover {
    background: #1a6fc4 !important;
    color: #ffffff !important;
    border-color: #1a6fc4 !important;
}

/* ── 데이터프레임 ── */
div[data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; }

/* ── divider ── */
hr { border-color: #e8eef5 !important; margin: 0.5rem 0 !important; }
</style>
""", unsafe_allow_html=True)

SEOUL_COORDS = {
    "서울 강남구": (37.5172, 127.0473), "서울 강동구": (37.5301, 127.1238),
    "서울 강북구": (37.6396, 127.0257), "서울 강서구": (37.5509, 126.8495),
    "서울 관악구": (37.4784, 126.9516), "서울 광진구": (37.5384, 127.0822),
    "서울 구로구": (37.4954, 126.8874), "서울 금천구": (37.4569, 126.8956),
    "서울 노원구": (37.6541, 127.0568), "서울 도봉구": (37.6688, 127.0471),
    "서울 동대문구": (37.5744, 127.0396), "서울 동작구": (37.5124, 126.9393),
    "서울 마포구": (37.5663, 126.9014), "서울 서대문구": (37.5791, 126.9368),
    "서울 서초구": (37.4837, 127.0324), "서울 성동구": (37.5634, 127.0369),
    "서울 성북구": (37.5894, 127.0167), "서울 송파구": (37.5145, 127.1058),
    "서울 양천구": (37.5170, 126.8664), "서울 영등포구": (37.5260, 126.8963),
    "서울 용산구": (37.5324, 126.9902), "서울 은평구": (37.6026, 126.9291),
    "서울 종로구": (37.5730, 126.9794), "서울 중구":   (37.5640, 126.9975),
    "서울 중랑구": (37.6063, 127.0927),
    "경기 과천시": (37.4292, 126.9872),
}

# ✅ 서울 + 과천만 선명, 나머지 흐릿하게 처리할 기준
FOCUS_REGIONS = {k for k in SEOUL_COORDS}   # 현재 딕셔너리에 있는 전부 = 서울 + 과천

def load_data():
    with get_db() as db:
        rows = (
            db.query(
                RegionMaster.region_name,
                CrimeCategory.main_cat,
                CrimeCategory.sub_cat,
                CrimeRegion.crime_count,
            )
            .join(CrimeRegion,   CrimeRegion.region_id   == RegionMaster.id)
            .join(CrimeCategory, CrimeRegion.category_id == CrimeCategory.id)
            .all()
        )
    return pd.DataFrame(rows, columns=["지역", "범죄대분류", "범죄중분류", "범죄건수"])

df = load_data()

if df.empty:
    st.warning("⚠️ 데이터가 없습니다. seed_all.py를 먼저 실행해주세요.")
    st.code("cd C:\\project_1.0\\4_streamlit\npython seed/seed_all.py")
    st.stop()

df["lat"] = df["지역"].map(lambda x: SEOUL_COORDS.get(x, (None, None))[0])
df["lon"] = df["지역"].map(lambda x: SEOUL_COORDS.get(x, (None, None))[1])
df = df.dropna(subset=["lat", "lon"])

# ─────────────────────────────────────────
# 사이드바
# ─────────────────────────────────────────
st.sidebar.markdown("""
<div style='padding: 0.6rem 0 1rem 0;'>
  <div style='font-size:20px; font-weight:900; letter-spacing:0.5px; color:#ffffff;'>🗺️ 범죄 지도</div>
  <div style='font-size:11px; color:#7aadce; margin-top:2px;'>서울 자치구 범죄 현황 필터</div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("<div style='font-size:11px; font-weight:700; color:#7aadce; letter-spacing:1px; margin-bottom:4px;'>🔍 범죄 유형</div>", unsafe_allow_html=True)
sub_cats     = sorted(df["범죄중분류"].unique().tolist())
selected_sub = st.sidebar.selectbox("", sub_cats, label_visibility="collapsed")

st.sidebar.markdown("<hr style='border-color:#1e3d5c;margin:0.8rem 0;'>", unsafe_allow_html=True)
st.sidebar.markdown("<div style='font-size:11px; font-weight:700; color:#7aadce; letter-spacing:1px; margin-bottom:4px;'>⚙️ HEXAGON 설정</div>", unsafe_allow_html=True)
hex_radius     = st.sidebar.slider("🔵 반경 (m)",  100, 1000, 1000, step=50)
hex_elev_scale = st.sidebar.slider("📈 높이 배율",    1,   30,  30, step=1)

st.sidebar.markdown("<hr style='border-color:#1e3d5c;margin:0.8rem 0;'>", unsafe_allow_html=True)
auto_pitch = st.sidebar.toggle("🔄 3D 시점 (pitch)", value=True)

st.sidebar.markdown("""
<hr style='border-color:#1e3d5c;margin:1rem 0 0.6rem 0;'>
<div style='font-size:10px; color:##1E3A5F; text-align:center; line-height:1.6;'>
  데이터 출처 : 경찰청<br>
  서울 25개 자치구 + 과천시 포함
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# 필터 적용 & 집계
# ─────────────────────────────────────────
df_f   = df[df["범죄중분류"] == selected_sub]
agg_df = df_f.groupby(["지역", "lat", "lon"])["범죄건수"].sum().reset_index()

# HexagonLayer용 expanded (서울/과천만 진하게 → 포인트 수 조절)
df_focus  = df_f[df_f["지역"].isin(FOCUS_REGIONS)]
df_others = df_f[~df_f["지역"].isin(FOCUS_REGIONS)]

expanded_focus = df_focus[["lat", "lon"]].loc[
    df_focus.index.repeat(
        (df_focus["범죄건수"] / df_focus["범죄건수"].max() * 10)
        .astype(int).clip(lower=1)
    )
].reset_index(drop=True) if not df_focus.empty else pd.DataFrame(columns=["lat", "lon"])

# 비서울은 포인트 1개씩만 → 낮은 밀도로 흐릿하게
expanded_others = df_others[["lat", "lon"]].reset_index(drop=True) if not df_others.empty else pd.DataFrame(columns=["lat", "lon"])

expanded = pd.concat([expanded_focus, expanded_others], ignore_index=True)

# ─────────────────────────────────────────
# 헤더
# ─────────────────────────────────────────
st.markdown("""
<div style='font-size:11px;font-weight:700;color:#1a6fc4;letter-spacing:2.5px;text-transform:uppercase;margin-bottom:4px;'>CRIME MAP · SEOUL DISTRICT</div>
<div class='page-title'>🗺️ 3D 범죄 지도</div>
<div class='page-sub'>서울 자치구별 범죄 발생 건수 3D 시각화 &nbsp;·&nbsp; 경찰청 데이터 기반</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# ViewState
# ─────────────────────────────────────────
pitch_val = 45 if auto_pitch else 0

view = pdk.ViewState(
    latitude=37.5500,
    longitude=126.9780,
    zoom=10.5,
    pitch=pitch_val,
    bearing=0,
)

col_left, col_right = st.columns([2, 2.3])

# ── 왼쪽: HexagonLayer ───────────────────
with col_left:
    with st.container(border=True):
        st.markdown("<div class='map-label'>🔵 HexagonLayer &nbsp;·&nbsp; 등도 기반 육각형</div>",
                    unsafe_allow_html=True)

        hex_layer = pdk.Layer(
            "HexagonLayer",
            data=expanded,
            get_position="[lon, lat]",
            radius=hex_radius,
            elevation_scale=hex_elev_scale,
            elevation_range=[0, 500],
            pickable=True,
            extruded=True,
            coverage=0.9,
            color_range=[
                [1,   152, 189, 200],
                [73,  227, 206, 200],
                [216, 254, 181, 200],
                [254, 237, 177, 200],
                [254, 173,  84, 200],
                [209,  55,  78, 220],
            ],
        )
        st.pydeck_chart(
            pdk.Deck(
                layers=[hex_layer],
                initial_view_state=view,
                tooltip={"text": "밀도: {elevationValue}"},
                map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
            ),
            width="stretch",
            height=524,
        )

# ── 오른쪽: 요약 카드 + 테이블 ────────────
with col_right:
    # ── 집계 데이터 준비 ──────────────────────
    table_df = (
        df_f.groupby(["지역", "범죄대분류", "범죄중분류"])["범죄건수"]
        .sum()
        .reset_index()
        .sort_values("범죄건수", ascending=False)
        .reset_index(drop=True)
    )

    # ── 섹션 1: 요약 메트릭 카드 ─────────────
    with st.container(border=True):
        st.markdown("<div class='map-label'>📊 서울 전체 범죄 현황 &nbsp;·&nbsp; 범죄 유형별</div>",
                    unsafe_allow_html=True)
        if not table_df.empty:
            avg_val    = table_df["범죄건수"].mean()
            max_row    = table_df.iloc[0]
            region_cnt = len(table_df["지역"].unique())

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"""
                <div style='background:#fff;border-radius:12px;padding:16px 20px;border:1px solid #e4ecf5;margin:4px 4px 8px 4px;'>
                  <div style='font-size:13px;color:#8fa8c0;font-weight:600;margin-bottom:6px;'>📍 선택 범죄 유형</div>
                  <div style='display:flex;align-items:baseline;gap:10px;'>
                    <span style='font-size:23px;font-weight:900;color:#12263a;'>{selected_sub}</span>
                    <span style='font-size:19px;font-weight:600;color:#7a96b0;'>전체 {region_cnt}개 지역</span>
                  </div>
                </div>""", unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div style='background:#fff;border-radius:12px;padding:16px 20px;border:1px solid #e4ecf5;margin:4px 4px 8px 4px;'>
                  <div style='font-size:13px;color:#8fa8c0;font-weight:600;margin-bottom:6px;'>🔴 최다 범죄 지역</div>
                  <div style='display:flex;align-items:baseline;gap:10px;'>
                    <span style='font-size:23px;font-weight:900;color:#12263a;'>{max_row["지역"].replace("서울 ", "")}</span>
                    <span style='font-size:19px;font-weight:600;color:#e85d5d;'>{int(max_row["범죄건수"]):,}건</span>
                  </div>
                </div>""", unsafe_allow_html=True)
            with c3:
                st.markdown(f"""
                <div style='background:#fff;border-radius:12px;padding:16px 20px;border:1px solid #e4ecf5;margin:4px 4px 8px 4px;'>
                  <div style='font-size:13px;color:#8fa8c0;font-weight:600;margin-bottom:6px;'>🟢 최소 범죄 지역</div>
                  <div style='display:flex;align-items:baseline;gap:10px;'>
                    <span style='font-size:23px;font-weight:900;color:#12263a;'>{table_df.iloc[-1]["지역"].replace("서울 ", "")}</span>
                    <span style='font-size:19px;font-weight:600;color:#2e9e6b;'>{int(table_df.iloc[-1]["범죄건수"]):,}건</span>
                  </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("필터 조건에 맞는 데이터가 없습니다.")

    # ── 섹션 2: 상세 데이터 테이블 ───────────
    with st.container(border=True):
        st.markdown("<div class='map-label'>📋 상세 데이터</div>",
                    unsafe_allow_html=True)

        # HexagonLayer 색상 팔레트
        _HEX_PALETTE = [
            (1,   152, 189),
            (73,  227, 206),
            (216, 254, 181),
            (254, 237, 177),
            (254, 173,  84),
            (209,  55,  78),
        ]

        def _apply_hex_gradient(series):
            min_v, max_v = series.min(), series.max()
            styles = []
            for val in series:
                ratio = (val - min_v) / (max_v - min_v) if max_v > min_v else 0
                pos = ratio * (len(_HEX_PALETTE) - 1)
                lo = int(pos); hi = min(lo + 1, len(_HEX_PALETTE) - 1); t = pos - lo
                r = int(_HEX_PALETTE[lo][0] * (1 - t) + _HEX_PALETTE[hi][0] * t)
                g = int(_HEX_PALETTE[lo][1] * (1 - t) + _HEX_PALETTE[hi][1] * t)
                b = int(_HEX_PALETTE[lo][2] * (1 - t) + _HEX_PALETTE[hi][2] * t)
                brightness = 0.299 * r + 0.587 * g + 0.114 * b
                text = "#0d2137" if brightness > 150 else "white"
                styles.append(f"background-color: rgb({r},{g},{b}); color: {text};")
            return styles

        if "tbl_expanded" not in st.session_state:
            st.session_state["tbl_expanded"] = False

        tbl_height = 654 if st.session_state["tbl_expanded"] else 283
        btn_label  = "▲ 접기" if st.session_state["tbl_expanded"] else "▼ 크게 펼치기"

        if not table_df.empty:
            styled_table = table_df.style.apply(_apply_hex_gradient, subset=["범죄건수"])
            st.dataframe(styled_table, use_container_width=True, height=tbl_height)
        else:
            st.info("데이터가 없습니다.")

        if st.button(btn_label, key="tbl_toggle", use_container_width=True):
            st.session_state["tbl_expanded"] = not st.session_state["tbl_expanded"]
            st.rerun()

# ─────────────────────────────────────────
# 하단 통계 섹션
# ─────────────────────────────────────────
if not table_df.empty:
    import plotly.express as px
    import plotly.graph_objects as go

    st.markdown("<div style='font-size:11px;font-weight:700;color:#1a6fc4;letter-spacing:2.5px;text-transform:uppercase;margin-top:2rem;margin-bottom:2px;'>CRIME STATISTICS ANALYSIS</div><div class='section-title' style='margin-top:0;'>📊 범죄 통계 분석</div>", unsafe_allow_html=True)

    total_val  = int(table_df["범죄건수"].sum())
    avg_val2   = table_df["범죄건수"].mean()
    med_val    = float(table_df["범죄건수"].median())
    std_val    = table_df["범죄건수"].std()
    max_row2   = table_df.iloc[0]
    min_row2   = table_df[table_df["범죄건수"] > 0].iloc[-1] if (table_df["범죄건수"] > 0).any() else table_df.iloc[-1]
    top3_sum   = int(table_df.head(3)["범죄건수"].sum())
    top3_ratio = top3_sum / total_val * 100 if total_val else 0
    q75        = float(table_df["범죄건수"].quantile(0.75))
    q25        = float(table_df["범죄건수"].quantile(0.25))
    region_cnt2 = len(table_df)

    top10 = table_df.head(10).copy()
    top10["지역²"] = top10["지역"].str.replace("서울 ", "", regex=False)
    pie_df = table_df.copy()
    pie_df["지역²"] = pie_df["지역"].str.replace("서울 ", "", regex=False)

    _COLORS = ["rgb(1,152,189)", "rgb(73,227,206)", "rgb(254,173,84)", "rgb(209,55,78)"]
    _CHART_LAYOUT = dict(
        margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=240,
    )

    col1, col2, col3 = st.columns(3)

    # ── 1. 전체 건수 + 막대 차트 ──────────
    with col1:
        with st.container(border=True):
            st.metric("📌 전체 범죄 건수", f"{total_val:,}건")
            st.caption(f"상위 3개 지역이 전체의 **{top3_ratio:.1f}%** 차지")
            st.divider()
            fig1 = px.bar(
                top10, x="지역²", y="범죄건수",
                color="범죄건수",
                color_continuous_scale=[[0,"rgb(1,152,189)"],[0.5,"rgb(254,173,84)"],[1,"rgb(209,55,78)"]],
                labels={"범죄건수": "건수", "지역²": ""},
            )
            fig1.update_layout(**_CHART_LAYOUT, coloraxis_showscale=False,
                               xaxis_tickangle=-40, xaxis_tickfont_size=20)
            st.plotly_chart(fig1, use_container_width=True)
            st.markdown(
                f"<div style='display:flex;gap:8px;flex-wrap:wrap;padding:4px 0;'>"
                f"<div style='flex:1;background:#eef4fb;border-radius:10px;padding:10px 14px;text-align:center;'><div style='font-size:12px;color:#7a96b0;margin-bottom:2px;'>상위 3개 합산</div><div style='font-size:20px;font-weight:800;color:#1a6fc4;'>{top3_sum:,}건</div></div>"
                f"<div style='flex:1;background:#fff3f3;border-radius:10px;padding:10px 14px;text-align:center;'><div style='font-size:12px;color:#7a96b0;margin-bottom:2px;'>집중 비율</div><div style='font-size:20px;font-weight:800;color:#e85d5d;'>{top3_ratio:.1f}%</div></div>"
                f"<div style='flex:1;background:#f4f8f4;border-radius:10px;padding:10px 14px;text-align:center;'><div style='font-size:12px;color:#7a96b0;margin-bottom:2px;'>분산 지역</div><div style='font-size:20px;font-weight:800;color:#2e9e6b;'>{region_cnt2-3}개</div></div>"
                "</div>",
                unsafe_allow_html=True
            )

    # ── 2. 지역 평균 + 파이 차트 ──────────
    with col2:
        with st.container(border=True):
            st.metric("📊 지역 평균", f"{avg_val2:,.1f}건")
            st.caption(f"최다 **{max_row2['지역'].replace('서울 ','')}** {int(max_row2['범죄건수'])}건 · 최소 **{min_row2['지역'].replace('서울 ','')}** {int(min_row2['범죄건수'])}건")
            st.divider()
            top5_labels_pie = pie_df.head(5)["지역²"].tolist()
            hidden_labels   = [l for l in pie_df["지역²"] if l not in top5_labels_pie]
            _top5_colors    = ["rgb(209,55,78)","rgb(254,173,84)","rgb(216,254,181)","rgb(73,227,206)","rgb(1,152,189)"]
            _pie_color_map  = {label: _top5_colors[i] for i, label in enumerate(top5_labels_pie)}
            _pie_color_map.update({label: "#cccccc" for label in hidden_labels})
            fig2 = px.pie(
                pie_df, names="지역²", values="범죄건수",
                color="지역²",
                color_discrete_map=_pie_color_map,
                hole=0.4,
            )
            fig2.update_layout(
                **_CHART_LAYOUT,
                legend=dict(font=dict(size=18)),
                hiddenlabels=hidden_labels,
            )
            fig2.update_traces(textinfo="none")
            st.plotly_chart(fig2, use_container_width=True)
            st.markdown(
                f"<div style='display:flex;gap:8px;flex-wrap:wrap;padding:4px 0;'>"
                f"<div style='flex:1;background:#fff3f3;border-radius:10px;padding:10px 14px;text-align:center;'><div style='font-size:12px;color:#7a96b0;margin-bottom:2px;'>최다 지역</div><div style='font-size:18px;font-weight:800;color:#e85d5d;'>{max_row2['지역'].replace('서울 ','')} {int(max_row2['범죄건수']):,}건</div></div>"
                f"<div style='flex:1;background:#eef4fb;border-radius:10px;padding:10px 14px;text-align:center;'><div style='font-size:12px;color:#7a96b0;margin-bottom:2px;'>최소 지역</div><div style='font-size:18px;font-weight:800;color:#1a6fc4;'>{min_row2['지역'].replace('서울 ','')} {int(min_row2['범죄건수']):,}건</div></div>"
                f"<div style='flex:1;background:#f9f4ff;border-radius:10px;padding:10px 14px;text-align:center;'><div style='font-size:12px;color:#7a96b0;margin-bottom:2px;'>표준편차</div><div style='font-size:20px;font-weight:800;color:#8e44ad;'>{std_val:,.0f}건</div></div>"
                "</div>",
                unsafe_allow_html=True
            )

    # ── 3. 중앙값 + 박스플롯 ──────────────
    with col3:
        with st.container(border=True):
            top5 = table_df.head(5).copy()
            bot5 = table_df.tail(5).copy()
            top5["지역²"] = top5["지역"].str.replace("서울 ", "", regex=False)
            bot5["지역²"] = bot5["지역"].str.replace("서울 ", "", regex=False)
            top5_sum = int(top5["범죄건수"].sum())
            bot5_sum = int(bot5["범죄건수"].sum())
            gap = top5_sum - bot5_sum

            st.metric("🏆 상위 vs 하위 격차", f"{gap:,}건")
            st.caption(f"상위 5개 합계 **{top5_sum:,}건** · 하위 5개 합계 **{bot5_sum:,}건**")
            st.divider()

            cmp_df = pd.concat([
                top5[["지역²", "범죄건수"]].assign(구분="상위 5"),
                bot5[["지역²", "범죄건수"]].assign(구분="하위 5"),
            ])
            fig3 = px.bar(
                cmp_df, x="범죄건수", y="지역²",
                color="구분",
                orientation="h",
                color_discrete_map={"상위 5": "rgb(209,55,78)", "하위 5": "rgb(1,152,189)"},
                text="범죄건수",
                labels={"범죄건수": "건수", "지역²": ""},
            )
            fig3.update_traces(textposition="outside", textfont_size=20)
            fig3.update_layout(
                **_CHART_LAYOUT,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=20)),
                yaxis=dict(autorange="reversed", tickfont=dict(size=20)),
                xaxis=dict(showgrid=True, gridcolor="#eef2f7", tickfont=dict(size=20)),
            )
            st.plotly_chart(fig3, use_container_width=True)
            st.markdown(
                f"<div style='display:flex;gap:8px;flex-wrap:wrap;padding:4px 0;'>"
                f"<div style='flex:1;background:#fff3f3;border-radius:10px;padding:10px 14px;text-align:center;'><div style='font-size:12px;color:#7a96b0;margin-bottom:2px;'>상위 5 합계</div><div style='font-size:20px;font-weight:800;color:#e85d5d;'>{top5_sum:,}건</div></div>"
                f"<div style='flex:1;background:#eef4fb;border-radius:10px;padding:10px 14px;text-align:center;'><div style='font-size:12px;color:#7a96b0;margin-bottom:2px;'>하위 5 합계</div><div style='font-size:20px;font-weight:800;color:#1a6fc4;'>{bot5_sum:,}건</div></div>"
                f"<div style='flex:1;background:#fffbee;border-radius:10px;padding:10px 14px;text-align:center;'><div style='font-size:12px;color:#7a96b0;margin-bottom:2px;'>상위/하위 배율</div><div style='font-size:20px;font-weight:800;color:#e6a817;'>{top5_sum/bot5_sum:.1f}배</div></div>"
                "</div>",
                unsafe_allow_html=True
            )

    # ─── 범죄 현황 분석 리포트 ───────────────────────────────────────
    st.markdown("<div style='font-size:11px;font-weight:700;color:#1a6fc4;letter-spacing:2.5px;text-transform:uppercase;margin-top:2rem;margin-bottom:2px;'>CRIME ANALYSIS REPORT</div><div class='section-title' style='margin-top:0;'>📋 범죄 현황 분석 리포트</div>", unsafe_allow_html=True)

    max_name      = max_row2["지역"].replace("서울 ", "")
    min_name      = min_row2["지역"].replace("서울 ", "")
    max_val_r     = int(max_row2["범죄건수"])
    min_val_r     = int(min_row2["범죄건수"])
    avg_int_r     = int(round(avg_val2))
    above_avg_cnt = len(table_df[table_df["범죄건수"] > avg_val2])
    max_vs_avg    = max_val_r - avg_int_r
    ratio_mm      = max_val_r / min_val_r if min_val_r > 0 else None

    rep1, rep2, rep3 = st.columns(3)

    # ── 섹션 1: 요약 텍스트 ──────────────────
    below_avg_cnt  = region_cnt2 - above_avg_cnt
    max_share      = max_val_r / total_val * 100 if total_val else 0
    if min_val_r > 0:
        ratio_mm_str = f"{max_val_r / min_val_r:.1f}배"
    else:
        next_min = table_df[table_df["범죄건수"] > 0]["범죄건수"].min()
        ratio_mm_str = f"{max_val_r / next_min:.1f}배" if next_min > 0 else "산출불가"
    with rep1:
        with st.container(border=True):
            st.markdown(
                f"<div style='min-height:400px;display:flex;flex-direction:column;justify-content:space-between;'>"
                f"<div>"
                f"<div style='font-size:15px;color:#7a96b0;font-weight:600;margin-bottom:10px;'>{selected_sub} · 서울 자치구 분석</div>"
                f"<div style='font-size:18px;color:#12263a;font-weight:700;line-height:1.7;margin-bottom:16px;'>"
                f"{max_name}은 서울 평균 대비<br>"
                f"<span style='color:#e85d5d;font-size:30px;font-weight:900;'>↑ {max_vs_avg:,}건</span> 높아요. 🚨"
                f"</div>"
                f"<div style='background:#f4f7fb;border-radius:10px;padding:16px 18px;font-size:16px;line-height:2.6;color:#4a6080;'>"
                f"• 선택 유형 전체 범죄건수 <b style='color:#12263a;'>{total_val:,}건</b><br>"
                f"• 지역당 평균 <b style='color:#1a6fc4;'>{avg_int_r:,}건</b> &nbsp;(평균 초과 <b style='color:#1a6fc4;'>{above_avg_cnt}곳</b> / 이하 <b style='color:#7a96b0;'>{below_avg_cnt}곳</b>)<br>"
                f"• 최다 <b style='color:#e85d5d;'>{max_name}</b> {max_val_r:,}건 &nbsp;— 전체의 <b style='color:#e85d5d;'>{max_share:.1f}%</b> 점유<br>"
                f"• 최다 <b style='color:#e85d5d;'>{max_name}</b> ({max_val_r:,}건) vs 최소 <b style='color:#1a6fc4;'>{min_name}</b> ({min_val_r:,}건)<br>"
                f"• 최다/최소 배율 <b style='color:#12263a;'>{ratio_mm_str}</b> &nbsp;·&nbsp; 상위 3개 집중 <b style='color:#e85d5d;'>{top3_ratio:.1f}%</b>"
                f"</div>"
                f"</div>"
                f"</div>",
                unsafe_allow_html=True
            )

    # ── 섹션 2: 최다 vs 서울평균 vs 최소 ────
    with rep2:
        with st.container(border=True):
            _ymax1 = max(max_val_r, avg_int_r, min_val_r) * 1.3 or 1
            st.markdown(
                f"<div style='font-size:13px;color:#7a96b0;font-weight:600;margin-bottom:6px;'>최다 지역은 서울 평균 대비</div>"
                f"<div style='font-size:22px;font-weight:900;color:#e85d5d;margin-bottom:10px;'>↑ {max_vs_avg:,}건 높아요. 🚨</div>",
                unsafe_allow_html=True
            )
            fig_rep1 = go.Figure()
            for label, val, color in [
                (max_name, max_val_r, "#e85d5d"),
                ("서울평균", avg_int_r, "#c8d8ea"),
                (min_name, min_val_r, "#1a6fc4"),
            ]:
                fig_rep1.add_trace(go.Bar(
                    x=[label], y=[val],
                    marker_color=color,
                    text=[f"{val:,}건"],
                    textposition="outside",
                    textfont=dict(size=15, color="#4a6080"),
                    width=0.5,
                    showlegend=False,
                ))
            fig_rep1.update_layout(
                height=310, margin=dict(l=10, r=10, t=30, b=10),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                barmode="group",
                xaxis=dict(tickfont=dict(size=13), showgrid=False, zeroline=False, fixedrange=True),
                yaxis=dict(visible=False, range=[0, _ymax1]),
            )
            st.plotly_chart(fig_rep1, use_container_width=True)

    # ── 섹션 3: 상위 5 vs 하위 5 ───────────
    with rep3:
        with st.container(border=True):
            top5_avg_r = int(top5_sum / 5)
            bot5_avg_r = int(bot5_sum / 5)
            _ymax2 = max(top5_avg_r, avg_int_r, bot5_avg_r) * 1.3 or 1
            st.markdown(
                f"<div style='font-size:13px;color:#7a96b0;font-weight:600;margin-bottom:6px;'>상위 5개 지역은 하위 5개 대비</div>"
                f"<div style='font-size:22px;font-weight:900;color:#e6a817;margin-bottom:10px;'>{top5_sum/bot5_sum:.1f}배 수준이에요. 📊</div>",
                unsafe_allow_html=True
            )
            fig_rep2 = go.Figure()
            for label, val, color in [
                ("상위 5 평균", top5_avg_r, "#e85d5d"),
                ("서울평균", avg_int_r, "#c8d8ea"),
                ("하위 5 평균", bot5_avg_r, "#1a6fc4"),
            ]:
                fig_rep2.add_trace(go.Bar(
                    x=[label], y=[val],
                    marker_color=color,
                    text=[f"{val:,}건"],
                    textposition="outside",
                    textfont=dict(size=15, color="#4a6080"),
                    width=0.5,
                    showlegend=False,
                ))
            fig_rep2.update_layout(
                height=310, margin=dict(l=10, r=10, t=30, b=10),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                barmode="group",
                xaxis=dict(tickfont=dict(size=13), showgrid=False, zeroline=False, fixedrange=True),
                yaxis=dict(visible=False, range=[0, _ymax2]),
            )
            st.plotly_chart(fig_rep2, use_container_width=True)