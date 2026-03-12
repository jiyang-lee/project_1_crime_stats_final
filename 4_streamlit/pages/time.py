import re
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from orm.database import SessionLocal
from orm.model import CrimeTime, CrimeCategory


st.set_page_config(page_title="시간대별 범죄 통계", page_icon="🚓", layout="wide")

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;900&display=swap');

html, body, [class*="css"], .stMarkdown, .stMetric, .stDataFrame, button, input, select {
    font-family: 'Noto Sans KR', sans-serif !important;
}

.main { background-color: #f4f6fa; }
.block-container {
    padding-top: 2.2rem !important;
    padding-left: 1.8rem !important;
    padding-right: 1.8rem !important;
}

.page-title {
    font-size: 33px;
    font-weight: 900;
    color: #12263a;
    letter-spacing: -0.5px;
    margin-bottom: 2px;
}
.page-sub {
    font-size: 13px;
    color: #8fa8c0;
    margin-bottom: 16px;
    letter-spacing: 0.2px;
}
.page-eyebrow {
    display: inline-block;
    font-size: 12px;
    font-weight: 800;
    color: #1a6fc4;
    letter-spacing: 1.8px;
    text-transform: uppercase;
    line-height: 1.25;
    margin: 0 0 6px 2px;
}

.section-title {
    font-size: 26px;
    font-weight: 800;
    color: #12263a;
    margin-top: 2rem;
    margin-bottom: 0.6rem;
    padding-left: 10px;
    border-left: 4px solid #1a6fc4;
}

.card-label {
    font-size: 13px;
    font-weight: 700;
    color: #1a6fc4;
    letter-spacing: 0.3px;
    padding: 8px 4px 10px 4px;
    margin-bottom: 2px;
    border-bottom: 2px solid #e8eef5;
}

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
section[data-testid="stSidebar"] hr {
    border-color: #1e3d5c !important;
    margin: 0.6rem 0 !important;
}

div[data-testid="stHorizontalBlock"] { gap: 1.1rem; }

div[data-testid="stVerticalBlockBorderWrapper"] > div {
    border-radius: 12px !important;
    border: 2px solid #c9d7e6 !important;
    box-shadow: 0 2px 10px rgba(20, 60, 110, 0.06) !important;
    background: #ffffff !important;
}

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
                CrimeTime.time_range.label("시간대"),
                CrimeTime.crime_count.label("범죄건수"),
                CrimeCategory.sub_cat.label("범죄중분류"),
            )
            .join(CrimeCategory, CrimeTime.category_id == CrimeCategory.id)
        )
        return pd.read_sql(query.statement, db.bind)


def extract_start_hour(time_label: str) -> int:
    if pd.isna(time_label):
        return 99
    match = re.search(r"(\d{1,2})", str(time_label))
    return int(match.group(1)) if match else 99


df = load_data()
if df.empty:
    st.warning("⚠️ 데이터가 없습니다. seed/seed_all.py를 먼저 실행해주세요.")
    st.stop()

sub_cats = sorted(df["범죄중분류"].dropna().unique().tolist())

st.sidebar.markdown(
    """
<div style='padding: 0.6rem 0 1rem 0;'>
  <div style='font-size:20px; font-weight:900; letter-spacing:0.5px; color:#ffffff;'>⏰ 시간대 분석</div>
  <div style='font-size:11px; color:#7aadce; margin-top:2px;'>범죄 유형별 시간대 패턴 비교</div>
</div>
""",
    unsafe_allow_html=True,
)

st.sidebar.markdown(
    "<div style='font-size:11px; font-weight:700; color:#7aadce; letter-spacing:1px; margin-bottom:4px;'>🔍 범죄 유형</div>",
    unsafe_allow_html=True,
)
selected_sub = st.sidebar.selectbox("", sub_cats, label_visibility="collapsed")

st.sidebar.markdown("<hr>", unsafe_allow_html=True)
danger_threshold = st.sidebar.slider("주의 기준(위험지수)", 95, 140, 105, 1)

df_sel = df[df["범죄중분류"] == selected_sub].copy()
time_order = sorted(df["시간대"].dropna().unique().tolist(), key=extract_start_hour)

df_time = (
    df_sel.groupby("시간대", observed=False)["범죄건수"]
    .sum()
    .reindex(time_order, fill_value=0)
    .reset_index()
)

time_mean = df_time["범죄건수"].mean() if len(df_time) else 0
df_time["위험지수"] = (df_time["범죄건수"] / time_mean * 100).round(0) if time_mean else 0
df_time["상태"] = df_time["위험지수"].apply(lambda x: "주의" if x >= danger_threshold else "안정")

total_count = int(df_time["범죄건수"].sum())
peak_row = df_time.iloc[df_time["범죄건수"].idxmax()] if len(df_time) else pd.Series({"시간대": "-", "범죄건수": 0, "위험지수": 0})
low_row = df_time.iloc[df_time["범죄건수"].idxmin()] if len(df_time) else pd.Series({"시간대": "-", "범죄건수": 0, "위험지수": 0})
danger_count = int((df_time["위험지수"] >= danger_threshold).sum()) if len(df_time) else 0

st.markdown("<div class='page-eyebrow'>TIME CRIME ANALYSIS</div>", unsafe_allow_html=True)
st.markdown("<div class='page-title'>🚓 시간대별 범죄 통계 분석</div>", unsafe_allow_html=True)
st.markdown("<div class='page-sub'>발생 건수 · 위험지수 · 집중 시간대를 카드형 대시보드로 제공합니다.</div>", unsafe_allow_html=True)

col_left, col_right = st.columns([2, 2.3])

with col_left:
    with st.container(border=True):
        st.markdown("<div class='card-label'>📌 핵심 지표</div>", unsafe_allow_html=True)
        m1, m2, m3 = st.columns(3)

        metric_card = (
            "background:#fff;border-radius:12px;padding:14px 16px;"
            "border:2px solid #c9d7e6;margin:4px 4px 8px 4px;height:140px;"
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
  <div style='font-size:12px;color:#7a96b0;font-weight:600;margin-bottom:8px;'>피크 시간대</div>
  <div style='font-size:22px;font-weight:900;color:#e85d5d;line-height:1.25;'>{peak_row['시간대']}</div>
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
  <div style='font-size:12px;color:#7a96b0;margin-top:6px;'>주의 시간대 {danger_count}개</div>
</div>
""",
            unsafe_allow_html=True,
        )

    # spacer so metric card and risk card are visually separated
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("<div class='card-label'>⚠️ 시간대 위험지수</div>", unsafe_allow_html=True)
        # 시간대 기준 오름차순 정렬 (시작시간 기준)
        risk_sorted = df_time.sort_values(by="시간대", key=lambda s: s.map(extract_start_hour)).reset_index(drop=True)
        max_risk = float(risk_sorted["위험지수"].max()) if len(risk_sorted) else 1.0

        # 개별 행을 안전하게 문자열로 생성하여 리스트에 모은 뒤 한 번에 렌더
        risk_rows = []
        for _, row in risk_sorted.iterrows():
            val = float(row["위험지수"])
            width = max(min((val / max_risk) * 100, 100), 6)
            is_danger = val >= danger_threshold
            color = "#e85d5d" if is_danger else "#2e9e6b"

            # 폰트 크기 약간 증가(약 +2px) 및 행 최소 높이 조정
            risk_rows.append(
                f"""
<div style='display:grid;grid-template-columns:95px 1fr 74px;column-gap:12px;align-items:center;margin-bottom:10px;min-height:30px;'>
    <div style='font-size:15px;color:#4a6080;font-weight:600;'>{row['시간대']}</div>
    <div style='height:10px;background:#edf2f7;border-radius:999px;overflow:hidden;'>
        <div style='height:100%;width:{width:.1f}%;background:{color};border-radius:999px;'></div>
    </div>
    <div style='font-size:14px;text-align:right;font-weight:800;color:{color};'>{int(val)}</div>
</div>
"""
            )

        # 고정 높이 스크롤 영역으로 만들어 오른쪽 차트 높이와 시각적으로 맞춤
        # metric height (140) + spacer (20) + risk (400) = chart height (560)
        st.markdown(
            f"<div style='height:330px; overflow-y:auto; padding-right:8px;'>{''.join(risk_rows)}</div>",
            unsafe_allow_html=True,
        )

with col_right:
    with st.container(border=True):
        st.markdown("<div class='card-label'>📈 시간대별 발생 추이</div>", unsafe_allow_html=True)

        fig = go.Figure()
        bar_colors = ["#e85d5d" if x >= danger_threshold else "#4f86c6" for x in df_time["위험지수"]]
        fig.add_trace(
            go.Bar(
                x=df_time["시간대"],
                y=df_time["범죄건수"],
                marker_color=bar_colors,
                text=[f"{int(v):,}" for v in df_time["범죄건수"]],
                textposition="outside",
                name="범죄건수",
            )
        )
        # (변경) 꺾은선(위험지수)을 제거하고 막대만 표시
        fig.update_layout(
            template="plotly_white",
            height=560,
            margin=dict(l=12, r=12, t=12, b=12),
            xaxis=dict(title=None, tickangle=-20),
            yaxis=dict(title="범죄건수", showgrid=True, gridcolor="#eef2f7"),
            legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0),
        )
        st.plotly_chart(fig, use_container_width=True)

st.markdown(
    "<div style='font-size:11px;font-weight:700;color:#1a6fc4;letter-spacing:2.5px;text-transform:uppercase;margin-top:2rem;margin-bottom:2px;'>TIME CRIME STATISTICS REPORT</div>"
    "<div class='section-title' style='margin-top:0;'>📊 시간대 통계 분석 리포트</div>",
    unsafe_allow_html=True,
)

report_col1, report_col2, report_col3 = st.columns(3)

top3 = df_time.sort_values("범죄건수", ascending=False).head(3)
top3_sum = int(top3["범죄건수"].sum())
top3_ratio = (top3_sum / total_count * 100) if total_count else 0
avg_count = float(df_time["범죄건수"].mean()) if len(df_time) else 0
std_count = float(df_time["범죄건수"].std()) if len(df_time) else 0

with report_col1:
    with st.container(border=True):
        st.metric("📌 전체 발생 건수", f"{total_count:,}건")
        st.caption(f"상위 3개 시간대 집중도: **{top3_ratio:.1f}%**")
        st.divider()

        fig_top = px.bar(
            top3,
            x="시간대",
            y="범죄건수",
            color="범죄건수",
            color_continuous_scale=[[0, "#93c5fd"], [1, "#ef4444"]],
            labels={"범죄건수": "건수", "시간대": ""},
        )
        fig_top.update_layout(height=250, margin=dict(l=10, r=10, t=10, b=10), coloraxis_showscale=False)
        st.plotly_chart(fig_top, use_container_width=True)

with report_col2:
    with st.container(border=True):
        st.metric("📊 시간대 평균", f"{avg_count:,.1f}건")
        st.caption(f"표준편차: **{std_count:,.1f}건**")
        st.divider()

        dist_df = pd.DataFrame(
            {
                "구분": ["주의", "안정"],
                "개수": [danger_count, max(len(df_time) - danger_count, 0)],
            }
        )
        fig_pie = px.pie(dist_df, names="구분", values="개수", hole=0.5, color="구분", color_discrete_map={"주의": "#ef4444", "안정": "#22c55e"})
        fig_pie.update_layout(height=250, margin=dict(l=10, r=10, t=10, b=10), showlegend=True)
        fig_pie.update_traces(textinfo="label+percent")
        st.plotly_chart(fig_pie, use_container_width=True)

with report_col3:
    with st.container(border=True):
        st.metric("🚨 최고 위험지수", f"{int(peak_row['위험지수']):,}")
        st.caption(f"최저 시간대: **{low_row['시간대']}** ({int(low_row['범죄건수']):,}건)")
        st.divider()

        cmp_df = pd.DataFrame(
            {
                "구간": ["피크", "평균", "저위험"],
                "건수": [int(peak_row["범죄건수"]), int(round(avg_count)), int(low_row["범죄건수"])],
                "색상": ["#ef4444", "#94a3b8", "#22c55e"],
            }
        )
        fig_cmp = go.Figure(
            go.Bar(
                x=cmp_df["구간"],
                y=cmp_df["건수"],
                marker_color=cmp_df["색상"],
                text=[f"{x:,}" for x in cmp_df["건수"]],
                textposition="outside",
            )
        )
        fig_cmp.update_layout(
            height=250,
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(title=None),
            yaxis=dict(title=None, showgrid=True, gridcolor="#eef2f7"),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_cmp, use_container_width=True)
