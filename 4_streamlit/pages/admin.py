import os

import pandas as pd
import streamlit as st

from orm.database import get_db
from orm.model import HotspotAPI, RegionMapper, RegionMaster


st.set_page_config(page_title="관리자", page_icon="🔧", layout="wide")


def _get_admin_password() -> str | None:
    pw = None
    try:
        pw = st.secrets.get("ADMIN_PASSWORD")
    except Exception:
        pw = None
    return pw or os.getenv("ADMIN_PASSWORD")


def _require_admin() -> None:
    admin_pw = _get_admin_password()
    if not admin_pw:
        st.warning("관리자 페이지 비밀번호가 설정되지 않았습니다.")
        st.markdown("`.streamlit/secrets.toml`에 아래처럼 추가하세요.")
        st.code('ADMIN_PASSWORD = "your-password-here"', language="toml")
        st.stop()

    input_pw = st.text_input("관리자 비밀번호", type="password")
    if not input_pw:
        st.info("비밀번호를 입력하세요.")
        st.stop()
    if input_pw != admin_pw:
        st.error("비밀번호가 올바르지 않습니다.")
        st.stop()


def _load_hotspots_df(active_only: bool, search: str) -> pd.DataFrame:
    with get_db() as db:
        q = db.query(
            HotspotAPI.id,
            HotspotAPI.area_name,
            HotspotAPI.area_code,
            HotspotAPI.congest_lvl,
            HotspotAPI.ppltn_min,
            HotspotAPI.ppltn_max,
            HotspotAPI.temp,
            HotspotAPI.update_time,
            HotspotAPI.collected_at,
            HotspotAPI.active,
        )
        if active_only:
            q = q.filter(HotspotAPI.active == 1)
        rows = q.order_by(HotspotAPI.area_name.asc()).all()

    df = pd.DataFrame(
        rows,
        columns=[
            "id",
            "area_name",
            "area_code",
            "congest_lvl",
            "ppltn_min",
            "ppltn_max",
            "temp",
            "update_time",
            "collected_at",
            "active",
        ],
    )
    if search:
        s = search.strip()
        if s:
            df = df[df["area_name"].astype(str).str.contains(s, case=False, na=False)]
    return df.reset_index(drop=True)


def _get_current_region_name(db, hotspot_id: int | None, area_name: str | None) -> str | None:
    mapper = None
    if hotspot_id is not None:
        mapper = db.query(RegionMapper).filter(RegionMapper.hotspot_id == hotspot_id).first()
    if not mapper and area_name:
        mapper = db.query(RegionMapper).filter(RegionMapper.AREA_NM == area_name).first()
    if not mapper or not mapper.region_id:
        return None
    region = db.query(RegionMaster).filter(RegionMaster.id == mapper.region_id).first()
    return region.region_name if region else None


st.markdown("## 🔧 관리자")
st.caption("핫스팟 활성/비활성, 핫스팟↔지역 매핑을 관리합니다.")

_require_admin()

tab_hotspot, tab_mapping, tab_status = st.tabs(["핫스팟", "매핑", "DB 상태"])

with tab_hotspot:
    st.markdown("### 1) 핫스팟 Active(활성/비활성) 관리")

    col_a, col_b = st.columns([1, 2])
    with col_a:
        active_only = st.checkbox("활성(Active=1)만 보기", value=False)
    with col_b:
        search = st.text_input("검색(핫스팟명)", placeholder="예: 강남역")

    df_hotspots = _load_hotspots_df(active_only=active_only, search=search)
    st.dataframe(df_hotspots, use_container_width=True, hide_index=True)

    with st.expander("활성/비활성 변경", expanded=True):
        if df_hotspots.empty:
            st.info("표시할 데이터가 없습니다.")
        else:
            options = df_hotspots["area_name"].dropna().astype(str).tolist()
            selected = st.multiselect("대상 핫스팟", options=options)
            new_active = st.radio(
                "변경 값",
                options=[1, 0],
                format_func=lambda x: "활성(1)" if x == 1 else "비활성(0)",
                horizontal=True,
            )

            if st.button("적용", type="primary", disabled=(len(selected) == 0)):
                with get_db() as db:
                    (
                        db.query(HotspotAPI)
                        .filter(HotspotAPI.area_name.in_(selected))
                        .update({HotspotAPI.active: int(new_active)}, synchronize_session=False)
                    )
                st.success(f"{len(selected)}개 핫스팟의 active 값을 {new_active}로 변경했습니다.")
                st.rerun()

with tab_mapping:
    st.markdown("### 2) 핫스팟 ↔ 지역(구) 매핑 관리")
    st.caption("핫스팟(AREA_NM/area_name)을 RegionMaster(region_name)와 연결합니다.")

    with get_db() as db:
        hotspot_rows = (
            db.query(HotspotAPI.area_name)
            .order_by(HotspotAPI.area_name.asc())
            .all()
        )
        region_rows = (
            db.query(RegionMaster.region_name)
            .order_by(RegionMaster.region_name.asc())
            .all()
        )

    hotspot_names = [row[0] for row in hotspot_rows if row and row[0]]
    region_names = [row[0] for row in region_rows if row and row[0]]

    if not hotspot_names or not region_names:
        st.warning("핫스팟 또는 지역 마스터 데이터가 부족합니다. seed를 먼저 확인하세요.")
    else:
        col1, col2 = st.columns([1.4, 1.2])
        with col1:
            selected_hotspot_name = st.selectbox("핫스팟 선택", options=hotspot_names)
        with col2:
            selected_region_name = st.selectbox("연결할 지역(RegionMaster)", options=region_names)

        with get_db() as db:
            hotspot = db.query(HotspotAPI).filter(HotspotAPI.area_name == selected_hotspot_name).first()
            hotspot_id = hotspot.id if hotspot else None
            area_name = hotspot.area_name if hotspot else selected_hotspot_name
            current_region = _get_current_region_name(db, hotspot_id, area_name)

        st.markdown(f"현재 매핑: **{current_region if current_region else '없음'}**")

        if st.button("매핑 저장", type="primary", disabled=(hotspot is None)):
            with get_db() as db:
                hotspot = db.query(HotspotAPI).filter(HotspotAPI.area_name == selected_hotspot_name).first()
                region = db.query(RegionMaster).filter(RegionMaster.region_name == selected_region_name).first()

                mapper = db.query(RegionMapper).filter(RegionMapper.hotspot_id == hotspot.id).first()
                if not mapper:
                    mapper = db.query(RegionMapper).filter(RegionMapper.AREA_NM == hotspot.area_name).first()

                if mapper:
                    mapper.hotspot_id = hotspot.id
                    mapper.region_id = region.id
                    mapper.AREA_NM = hotspot.area_name
                    mapper.AREA_CD = hotspot.area_code
                else:
                    gu = selected_region_name.split(" ", 1)[-1] if " " in selected_region_name else selected_region_name
                    mapper = RegionMapper(
                        AREA_GU=gu,
                        CATEGORY="manual",
                        NO=0,
                        AREA_CD=hotspot.area_code,
                        AREA_NM=hotspot.area_name,
                        ENG_NM="",
                        hotspot_id=hotspot.id,
                        region_id=region.id,
                    )
                    db.add(mapper)

            st.success(f"'{selected_hotspot_name}' → '{selected_region_name}'로 매핑을 저장했습니다.")
            st.rerun()

    st.markdown("---")
    st.markdown("#### 매핑 현황")
    map_search = st.text_input("매핑 검색(핫스팟/지역)", placeholder="예: 홍대, 강남구")
    with get_db() as db:
        mapper_rows = (
            db.query(
                RegionMapper.AREA_NM.label("hotspot"),
                RegionMaster.region_name.label("region"),
                RegionMapper.AREA_NM.label("AREA_NM"),
                RegionMapper.AREA_GU.label("AREA_GU"),
                RegionMapper.AREA_CD.label("AREA_CD"),
                HotspotAPI.area_name.label("hotspot_api"),
            )
            .select_from(RegionMapper)
            .join(RegionMaster, RegionMapper.region_id == RegionMaster.id, isouter=True)
            .join(HotspotAPI, RegionMapper.hotspot_id == HotspotAPI.id, isouter=True)
            .order_by(RegionMapper.AREA_NM.asc())
            .all()
        )

    df_map = pd.DataFrame(
        mapper_rows,
        columns=["hotspot", "region", "AREA_NM", "AREA_GU", "AREA_CD", "hotspot_api"],
    )
    if map_search:
        s = map_search.strip()
        if s:
            mask = (
                df_map["hotspot"].astype(str).str.contains(s, case=False, na=False)
                | df_map["region"].astype(str).str.contains(s, case=False, na=False)
                | df_map["AREA_NM"].astype(str).str.contains(s, case=False, na=False)
                | df_map["AREA_GU"].astype(str).str.contains(s, case=False, na=False)
            )
            df_map = df_map[mask]
    st.dataframe(df_map.reset_index(drop=True), use_container_width=True, hide_index=True)

with tab_status:
    st.markdown("### 3) DB 상태")
    with get_db() as db:
        hotspot_cnt = db.query(HotspotAPI).count()
        mapper_cnt = db.query(RegionMapper).count()
        region_cnt = db.query(RegionMaster).count()
        latest = db.query(HotspotAPI.update_time).order_by(HotspotAPI.update_time.desc()).first()
        latest_ts = latest[0] if latest and latest[0] else "-"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("hotspot_api", hotspot_cnt)
    c2.metric("region_mapper", mapper_cnt)
    c3.metric("region_master", region_cnt)
    c4.metric("hotspot 최신 update_time", latest_ts)
