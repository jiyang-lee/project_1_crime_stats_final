import sys
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime
from sqlalchemy import func  # 통계 쿼리(Count, Sum, Avg 등)를 짤 때 필요
import os

# 프로젝트 내부 모듈
from orm.database import engine, SessionLocal, get_db
from orm.model import RegionMaster, CrimeCategory, HotspotAPI, CrimeRegion, CrimeTime, CrimeWeek # 필요한 모델들

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# ─────────────────────────────────────────
# CSS - 파란/청록 계열
# ─────────────────────────────────────────
st.markdown("""
<style>
.main { background-color: #f0f4f8; }

.page-title {
    font-size: 28px;
    font-weight: 800;
    color: #0d2137;
    margin-bottom: 2px;
}
.page-sub {
    font-size: 13px;
    color: #7a9bb5;
    margin-bottom: 12px;
}
.section-box {
    background: white;
    border-radius: 14px;
    padding: 14px 18px;
    margin-bottom: 12px;
    box-shadow: 0 3px 12px rgba(30,90,160,0.10);
    border-left: 5px solid #1a6fc4;
}
.section-title {
    font-size: 14px;
    font-weight: 700;
    color: #0d2137;
    margin-bottom: 2px;
}
.section-sub {
    font-size: 11px;
    color: #90aec6;
    margin-bottom: 6px;
}
.metric-box {
    background: white;
    border-radius: 12px;
    padding: 14px 10px;
    text-align: center;
    box-shadow: 0 3px 10px rgba(30,90,160,0.10);
    border-top: 4px solid #1a6fc4;
}
.metric-val {
    font-size: 20px;
    font-weight: 800;
    color: #1a6fc4;
}
.metric-lbl {
    font-size: 11px;
    color: #7a9bb5;
    margin-top: 3px;
}
section[data-testid="stSidebar"] {
    background-color: #0d2137;
}
section[data-testid="stSidebar"] * {
    color: #cce0f5 !important;
}
</style>
""", unsafe_allow_html=True)

BLUE_SEQ = [
    "#1a6fc4", "#2196f3", "#42a5f5",
    "#64b5f6", "#90caf9", "#1565c0",
    "#0d47a1", "#1e88e5"
]

# ─────────────────────────────────────────
# 데이터 로드
# ─────────────────────────────────────────
@st.cache_data
def load_data():
    with get_db() as db:
        rows = (
            db.query(
                CrimeTime.time_range,
                CrimeTime.crime_count,
                CrimeCategory.main_cat,
                CrimeCategory.sub_cat,
            )
            .join(CrimeCategory, CrimeTime.category_id == CrimeCategory.id)
            .all()
        )
    return pd.DataFrame(rows, columns=["시간대", "범죄건수", "범죄대분류", "범죄중분류"])

df = load_data()

# ─────────────────────────────────────────
# 사이드바
# ─────────────────────────────────────────
st.sidebar.markdown("## 🔍 필터")
st.sidebar.markdown("---")

main_cats     = sorted(df["범죄대분류"].unique().tolist())
selected_main = st.sidebar.selectbox("1. 범죄대분류", ["전체"] + main_cats)

sub_cats = (
    sorted(df["범죄중분류"].unique().tolist()) if selected_main == "전체"
    else sorted(df[df["범죄대분류"] == selected_main]["범죄중분류"].unique().tolist())
)
selected_subs = st.sidebar.multiselect("2. 범죄중분류", sub_cats, default=sub_cats)

# ─────────────────────────────────────────
# 필터 적용
# ─────────────────────────────────────────
df_f = df.copy()
if selected_main != "전체":
    df_f = df_f[df_f["범죄대분류"] == selected_main]
if selected_subs:
    df_f = df_f[df_f["범죄중분류"].isin(selected_subs)]

# ─────────────────────────────────────────
# 헤더
# ─────────────────────────────────────────
st.markdown("""
<div class='page-title'>⏰ 시간대별 범죄 분석</div>
<div class='page-sub'>경찰청 범죄 통계 데이터 기반</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# SECTION 1 : Metric 3개
# ─────────────────────────────────────────
total     = df_f["범죄건수"].sum()
peak_time = df_f.groupby("시간대")["범죄건수"].sum().idxmax()
peak_cat  = df_f.groupby("범죄중분류")["범죄건수"].sum().idxmax()

m1, m2, m3 = st.columns(3)
for col, val, lbl in zip(
    [m1, m2, m3],
    [f"{total:,.0f} 건", peak_time, peak_cat],
    ["📊 총 범죄 건수", "🕐 최다 발생 시간대", "⚠️ 최다 범죄 유형"]
):
    col.markdown(f"""
    <div class='metric-box'>
        <div class='metric-val'>{val}</div>
        <div class='metric-lbl'>{lbl}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────
# SECTION 2 : Pie + Bar (나란히)
# ─────────────────────────────────────────
st.markdown("""
<div class='section-box'>
    <div class='section-title'>📌 점유율 및 범죄 유형 비교</div>
    <div class='section-sub'>범죄 유형별 비율 · 건수 비교</div>
</div>""", unsafe_allow_html=True)

c1, c2 = st.columns(2)

with c1:
    pie_df  = df_f.groupby("범죄중분류")["범죄건수"].sum().reset_index()
    fig_pie = px.pie(
        pie_df, names="범죄중분류", values="범죄건수",
        hole=0.42,
        color_discrete_sequence=BLUE_SEQ
    )
    fig_pie.update_traces(
        textposition="inside",
        textinfo="percent+label",
        textfont_size=11,
        pull=[0.03] * len(pie_df)   # 살짝 분리감
    )
    fig_pie.update_layout(
        showlegend=True,
        legend=dict(
            orientation="v",
            x=1.0, y=0.5,
            font=dict(size=11),
            bgcolor="rgba(0,0,0,0)"
        ),
        height=280,
        margin=dict(t=10, b=10, l=10, r=80),
        paper_bgcolor="white"
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with c2:
    bar_df  = df_f.groupby("범죄중분류")["범죄건수"].sum().reset_index().sort_values("범죄건수", ascending=True)
    fig_bar = px.bar(
        bar_df,
        x="범죄건수", y="범죄중분류",
        orientation="h",
        color="범죄건수",
        color_continuous_scale="Blues",
        text="범죄건수"
    )
    fig_bar.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    fig_bar.update_layout(
        height=280,
        margin=dict(t=10, b=10, l=10, r=20),
        paper_bgcolor="white", plot_bgcolor="#fafcff",
        coloraxis_showscale=False,
        xaxis=dict(showgrid=True, gridcolor="#e8f0fa"),
        yaxis=dict(tickfont=dict(size=11))
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# ─────────────────────────────────────────
# SECTION 3 : Line + Radar (나란히)
# ─────────────────────────────────────────
st.markdown("""
<div class='section-box'>
    <div class='section-title'>📈 시간대별 추이 · 🕐 시계면 분포</div>
    <div class='section-sub'>시간대별 범죄 변화 · 레이더 차트</div>
</div>""", unsafe_allow_html=True)

c3, c4 = st.columns(2)

with c3:
    line_df = df_f.groupby(["시간대", "범죄중분류"])["범죄건수"].sum().reset_index()
    time_order = sorted(df["시간대"].unique().tolist())
    line_df["시간대"] = pd.Categorical(line_df["시간대"], categories=time_order, ordered=True)
    line_df = line_df.sort_values("시간대")

    fig_line = px.line(
        line_df, x="시간대", y="범죄건수",
        color="범죄중분류", markers=True,
        color_discrete_sequence=BLUE_SEQ
    )
    fig_line.update_layout(
        height=280,
        margin=dict(t=10, b=50, l=10, r=10),
        paper_bgcolor="white", plot_bgcolor="#fafcff",
        legend=dict(orientation="h", y=-0.40, font=dict(size=10)),
        xaxis=dict(tickangle=-30, tickfont=dict(size=10), gridcolor="#e8f0fa"),
        yaxis=dict(gridcolor="#e8f0fa")
    )
    st.plotly_chart(fig_line, use_container_width=True)

with c4:
    radar_df = df_f.groupby("시간대")["범죄건수"].sum().reset_index().sort_values("시간대")
    fig_radar = go.Figure(go.Scatterpolar(
        r     = radar_df["범죄건수"].tolist() + [radar_df["범죄건수"].iloc[0]],
        theta = radar_df["시간대"].tolist()   + [radar_df["시간대"].iloc[0]],
        fill  = "toself",
        fillcolor = "rgba(26,111,196,0.18)",
        line  = dict(color="#1a6fc4", width=2.5),
        name  = "범죄 건수"
    ))
    fig_radar.update_layout(
        polar=dict(
            bgcolor="#fafcff",
            radialaxis=dict(visible=True, color="#90aec6", gridcolor="#d0e4f7"),
            angularaxis=dict(tickfont=dict(size=10))
        ),
        height=280,
        margin=dict(t=20, b=20, l=30, r=30),
        paper_bgcolor="white",
        showlegend=False,
    )
    st.plotly_chart(fig_radar, use_container_width=True)

# ─────────────────────────────────────────
# SECTION 4 : 데이터프레임 (expander)
# ─────────────────────────────────────────
with st.expander("📋 원본 데이터 보기"):
    st.dataframe(
        df_f.sort_values("범죄건수", ascending=False).reset_index(drop=True),
        use_container_width=True,
        height=200
    )