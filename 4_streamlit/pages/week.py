import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from orm.database import SessionLocal
from orm.model import CrimeWeek, CrimeCategory


st.set_page_config(page_title="요일별 범죄 통계", page_icon="🚓", layout="wide")

st.markdown(
    """
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
section[data-testid="stSidebar"] .stSelectbox > div > div, section[data-testid="stSidebar"] .stMultiSelect > div > div {
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

/* ── Plotly chart rounding ── */
div[data-testid="stPlotlyChart"] {
    border-radius: 10px;
    overflow: hidden;
}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data
def load_data() -> pd.DataFrame:
    with SessionLocal() as db:
        query = (
            db.query(
                CrimeWeek.day_of_week.label("요일"),
                CrimeWeek.crime_count.label("범죄건수"),
                CrimeCategory.sub_cat.label("범죄중분류"),
            )
            .join(CrimeCategory, CrimeWeek.category_id == CrimeCategory.id)
        )
        return pd.read_sql(query.statement, db.bind)


df = load_data()
if df.empty:
    st.warning("⚠️ 데이터가 없습니다. seed/seed_all.py를 먼저 실행해주세요.")
    st.stop()

# 요일 정리
weekday_order = ["월", "화", "수", "목", "금", "토", "일"]
replace_map = {
    "월요일": "월",
    "화요일": "화",
    "수요일": "수",
    "목요일": "목",
    "금요일": "금",
    "토요일": "토",
    "일요일": "일",
    "Mon": "월",
    "Tue": "화",
    "Wed": "수",
    "Thu": "목",
    "Fri": "금",
    "Sat": "토",
    "Sun": "일",
}

df["요일"] = df["요일"].astype(str).str.strip().replace(replace_map)
df = df[df["요일"].isin(weekday_order)].copy()
df["요일"] = pd.Categorical(df["요일"], categories=weekday_order, ordered=True)
df = df.sort_values("요일")

sub_cats = sorted(df["범죄중분류"].dropna().unique().tolist())

# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
st.sidebar.markdown("""
<div style='padding: 0.6rem 0 1rem 0;'>
  <div style='font-size:20px; font-weight:900; letter-spacing:0.5px; color:#ffffff;'>🗓️ 메인 분석</div>
</div>
""", unsafe_allow_html=True)

st.sidebar.caption("위쪽 큰 분석 화면 변경")
selected_sub = st.sidebar.selectbox("", sub_cats, label_visibility="collapsed")

st.sidebar.markdown("""
<div style='padding: 0.6rem 0 1rem 0;'>
  <div style='font-size:20px; font-weight:900; letter-spacing:0.5px; color:#ffffff;'>🗂️ 비교 분석</div>
</div>
""", unsafe_allow_html=True)
st.sidebar.caption("아래 여러 카드 선택")

compare_subs = st.sidebar.multiselect(
    "목록에서 클릭해서 최대 9개까지 선택",
    sub_cats,
    default=[selected_sub],
)

if len(compare_subs) > 9:
    st.sidebar.warning("비교 카드는 최대 9개까지만 표시됩니다.")
    compare_subs = compare_subs[:9]

st.sidebar.caption(f"현재 {len(compare_subs)}개 선택됨")

st.sidebar.markdown("<hr>", unsafe_allow_html=True)
danger_threshold = 105

df_sel = df[df["범죄중분류"] == selected_sub].copy()

df_day = (
    df_sel.groupby("요일", observed=False)["범죄건수"]
    .sum()
    .reindex(weekday_order, fill_value=0)
    .reset_index()
)

day_mean = df_day["범죄건수"].mean() if len(df_day) else 0
df_day["위험지수"] = (df_day["범죄건수"] / day_mean * 100).round(0) if day_mean else 0
df_day["상태"] = df_day["위험지수"].apply(lambda x: "주의" if x >= danger_threshold else "안정")

total_count = int(df_day["범죄건수"].sum())
peak_row = (
    df_day.iloc[df_day["범죄건수"].idxmax()]
    if len(df_day)
    else pd.Series({"요일": "-", "범죄건수": 0, "위험지수": 0})
)
low_row = (
    df_day.iloc[df_day["범죄건수"].idxmin()]
    if len(df_day)
    else pd.Series({"요일": "-", "범죄건수": 0, "위험지수": 0})
)
danger_count = int((df_day["위험지수"] >= danger_threshold).sum()) if len(df_day) else 0

st.markdown("""
<div style='font-size:11px;font-weight:700;color:#1a6fc4;letter-spacing:2.5px;text-transform:uppercase;margin-bottom:4px;'>DAILY-BASED CRIME ANALYSIS</div>
<div class='page-title'> 🗓️ 요일별 범죄 메인 분석</div>
<div class='page-sub'>사이드바의 <b>메인 분석 </b> 선택값 기준으로 표시됩니다.</div>
""", unsafe_allow_html=True)

col_left, col_right = st.columns([2, 2.3])

with col_left:
    with st.container(border=True):
        st.markdown("<div class='map-label'>📌 핵심 지표</div>", unsafe_allow_html=True)
        m1, m2, m3 = st.columns(3)

        metric_card = (
            "background:#fff;border-radius:12px;padding:14px 16px;"
            "border:2px solid #c9d7e6;margin:4px 4px 8px 4px;min-height:112px;"
        )

        m1.markdown(
            f"""
<div style='{metric_card}'>
  <div style='font-size:12px;color:#7a96b0;font-weight:600;margin-bottom:8px;'>선택 범죄 유형</div>
  <div style='font-size:22px;font-weight:900;color:#12263a;line-height:1.25;'>{selected_sub}</div>
</div>
""",
            unsafe_allow_html=True,
        )
        m2.markdown(
            f"""
<div style='{metric_card}'>
  <div style='font-size:12px;color:#7a96b0;font-weight:600;margin-bottom:8px;'>최다 요일</div>
  <div style='font-size:22px;font-weight:900;color:#e85d5d;line-height:1.25;'>{peak_row['요일']}요일</div>
  <div style='font-size:12px;color:#7a96b0;margin-top:6px;'>{int(peak_row['범죄건수']):,}건</div>
</div>
""",
            unsafe_allow_html=True,
        )
        m3.markdown(
            f"""
<div style='{metric_card}'>
  <div style='font-size:12px;color:#7a96b0;font-weight:600;margin-bottom:8px;'>총 발생 건수</div>
  <div style='font-size:22px;font-weight:900;color:#12263a;line-height:1.25;'>{total_count:,}건</div>
  <div style='font-size:12px;color:#7a96b0;margin-top:6px;'>주의 요일 {danger_count}개</div>
</div>
""",
            unsafe_allow_html=True,
        )

    with st.container(border=True):
        st.markdown(f"""
<div style='display:flex;align-items:center;justify-content:space-between;padding:8px 4px 10px 4px;margin-bottom:2px;border-bottom:2px solid #e8eef5;'>
  <div style='font-size:13px;font-weight:700;color:#1a6fc4;letter-spacing:0.3px;'>⚠️ 요일별 위험지수</div>
  <div style='display:flex;align-items:center;gap:14px;'>
    <span style='display:flex;align-items:center;gap:6px;font-size:13px;color:#4a6080;font-weight:700;'>
      <span style='display:inline-block;width:13px;height:13px;border-radius:50%;background:#e85d5d;'></span>
      주의 (≥ {danger_threshold})
    </span>
    <span style='display:flex;align-items:center;gap:6px;font-size:13px;color:#4a6080;font-weight:700;'>
      <span style='display:inline-block;width:13px;height:13px;border-radius:50%;background:#2e9e6b;'></span>
      안정 (&lt; {danger_threshold})
    </span>
  </div>
</div>
""", unsafe_allow_html=True)
        risk_sorted = df_day.copy().reset_index(drop=True)
        max_risk = float(risk_sorted["위험지수"].max()) if len(risk_sorted) else 1.0

        risk_rows = []
        for _, row in risk_sorted.iterrows():
            val = float(row["위험지수"])
            width = max(min((val / max_risk) * 100, 100), 6)
            is_danger = val >= danger_threshold
            color = "#e85d5d" if is_danger else "#2e9e6b"
            risk_rows.append(
                f"""
<div style='display:grid;grid-template-columns:95px 1fr 74px;column-gap:10px;align-items:center;margin-bottom:26.4px;'>
  <div style='font-size:13px;color:#4a6080;font-weight:600;'>{row['요일']}요일</div>
  <div style='height:8px;background:#edf2f7;border-radius:999px;overflow:hidden;'>
    <div style='height:100%;width:{width:.1f}%;background:{color};border-radius:999px;'></div>
  </div>
  <div style='font-size:12px;text-align:right;font-weight:800;color:{color};'>{int(val)}</div>
</div>
"""
            )

        st.markdown(
            f"<div style='height:310px; overflow-y:auto; padding-right:8px;'>{''.join(risk_rows)}</div>",
            unsafe_allow_html=True,
        )

with col_right:
    with st.container(border=True):
        st.markdown("<div class='map-label'>📈 요일별 발생 추이</div>", unsafe_allow_html=True)

        fig = go.Figure()
        bar_colors = ["#e85d5d" if x >= danger_threshold else "#4f86c6" for x in df_day["위험지수"]]

        fig.add_trace(
            go.Bar(
                x=df_day["요일"],
                y=df_day["범죄건수"],
                marker_color=bar_colors,
                text=[f"{int(v):,}" for v in df_day["범죄건수"]],
                textposition="outside",
                name="범죄건수",
            )
        )
        
        


        fig.update_layout(
            template="plotly_white",
            height=493,
            margin=dict(l=12, r=12, t=12, b=12),
            xaxis=dict(title=None, categoryorder="array", categoryarray=weekday_order),
            yaxis=dict(title="범죄건수", showgrid=True, gridcolor="#eef2f7"),
            yaxis2=dict(title="위험지수", overlaying="y", side="right", showgrid=False),
            legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0))
        st.plotly_chart(fig, use_container_width=True)

st.markdown(
    "<div style='font-size:11px;font-weight:700;color:#1a6fc4;letter-spacing:2.5px;text-transform:uppercase;margin-top:2rem;margin-bottom:2px;'>CRIME SUMMARY CARD</div>"
    "<div class='section-title' style='margin-top:0;'>🗂️ 범죄별 요약 카드</div>",
    unsafe_allow_html=True,
)
st.caption("사이드바의 '비교 분석'에서 선택한 범죄들이 여기에 표시됩니다.")

compare_cols = range(0, len(compare_subs), 3)

if compare_subs:
    for row_start in range(0, len(compare_subs), 3):
        row_items = compare_subs[row_start:row_start + 3]
        compare_cols = st.columns(3)

        for i, crime_name in enumerate(row_items):
            compare_df = df[df["범죄중분류"] == crime_name].copy()

            df_compare_day = (
                compare_df.groupby("요일", observed=False)["범죄건수"]
                .sum()
                .reindex(weekday_order, fill_value=0)
                .reset_index()
            )

            total_count_compare = int(df_compare_day["범죄건수"].sum())

            if not df_compare_day.empty:
                compare_top_day = df_compare_day.loc[
                    df_compare_day["범죄건수"].idxmax(), "요일"
                ]
                compare_top_day_label = f"{compare_top_day}요일"
            else:
                compare_top_day_label = "-"

            weekend_count = int(
                df_compare_day[df_compare_day["요일"].isin(["토", "일"])]["범죄건수"].sum()
            )
            weekend_ratio = round((weekend_count / total_count_compare) * 100, 1) if total_count_compare else 0

            with compare_cols[i]:
                components.html(
                    f"""
                    <style>
                    .compare-card {{
                        background: #ffffff;
                        border: 1px solid #dde6f0;
                        border-radius: 12px;
                        padding: 18px 20px;
                        min-height: 190px;
                        font-family: 'Noto Sans KR', sans-serif;
                        box-sizing: border-box;
                        box-shadow: 0 2px 10px rgba(20,60,110,0.06);
                    }}
                    .compare-title {{
                        font-size: 18px;
                        font-weight: 800;
                        color: #222222;
                        margin-bottom: 14px;
                    }}
                    .compare-main {{
                        font-size: 30px;
                        font-weight: 800;
                        color: #5B8FF9;
                        margin-bottom: 16px;
                    }}
                    .compare-row {{
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-bottom: 8px;
                    }}
                    .compare-label {{
                        font-size: 13px;
                        color: #666666;
                    }}
                    .compare-value {{
                        font-size: 14px;
                        font-weight: 700;
                        color: #222222;
                    }}
                    </style>

                    <div class="compare-card">
                        <div class="compare-title">{crime_name}</div>
                        <div class="compare-main">{total_count_compare:,}건</div>
                        <div class="compare-row">
                            <div class="compare-label">최다 발생 요일</div>
                            <div class="compare-value">{compare_top_day_label}</div>
                        </div>
                        <div class="compare-row">
                            <div class="compare-label">주말 비중</div>
                            <div class="compare-value">{weekend_ratio}%</div>
                        </div>
                    </div>
                    """,
                    height=220,
                )
else:
    st.info("사이드바에서 비교할 범죄를 선택해 주세요.")
