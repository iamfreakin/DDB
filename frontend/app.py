from __future__ import annotations

import os

import streamlit as st

from api_client import ApiError, BackendClient, DEFAULT_BASE_URL


# API의 desired_moods enum과 동일한 값. 표시용 한국어 라벨을 매핑한다.
MOOD_LABELS: dict[str, str] = {
    "warm": "따뜻한",
    "friendly": "친근한",
    "emotional": "감성적인",
    "premium": "프리미엄",
    "playful": "발랄한",
    "clean": "깔끔한",
    "trustworthy": "신뢰감 있는",
}

STATUS_LABELS: dict[str, str] = {
    "draft": "초안",
    "approved": "승인됨",
    "stale": "프로필 변경됨",
    "superseded": "대체됨",
}


def get_client() -> BackendClient:
    base_url = st.session_state.get("base_url", os.getenv("BACKEND_URL", DEFAULT_BASE_URL))
    return BackendClient(base_url)


def lines_to_list(text: str) -> list[str]:
    """줄 단위 입력을 공백 제거 후 빈 줄을 뺀 리스트로 변환한다."""
    return [line.strip() for line in text.splitlines() if line.strip()]


def list_to_lines(values: list[str] | None) -> str:
    return "\n".join(values or [])


def show_api_error(error: ApiError) -> None:
    st.error(f"{error.message}")
    for item in error.field_errors:
        st.caption(f"- {item.get('field', '')}: {item.get('message', '')}")


# --- 사이드바: 연결 상태와 가게 선택 ---
def render_sidebar() -> None:
    st.sidebar.header("설정")
    st.session_state.setdefault(
        "base_url", os.getenv("BACKEND_URL", DEFAULT_BASE_URL)
    )
    st.session_state["base_url"] = st.sidebar.text_input(
        "백엔드 주소", value=st.session_state["base_url"]
    )

    client = get_client()
    try:
        health = client.health()
        st.sidebar.success(f"백엔드 연결됨 (v{health.get('version', '?')})")
    except ApiError as error:
        st.sidebar.error(error.message)
        st.stop()

    st.sidebar.divider()
    st.sidebar.subheader("가게")

    try:
        brands = client.list_brands().get("items", [])
    except ApiError as error:
        st.sidebar.error(error.message)
        brands = []

    options = {"➕ 새 가게 만들기": None}
    for brand in brands:
        options[f"{brand['name']} ({brand['industry']})"] = brand["id"]

    selected_brand_id = st.session_state.get("selected_brand_id")
    selected_index = 0
    option_values = list(options.values())
    if selected_brand_id in option_values:
        selected_index = option_values.index(selected_brand_id)

    selection = st.sidebar.radio("선택", list(options.keys()), index=selected_index)
    st.session_state["selected_brand_id"] = options[selection]


# --- 프로필 입력 폼 ---
def render_profile_fields(prefix: str, defaults: dict | None = None) -> dict | None:
    """프로필 입력 위젯을 그리고 유효하면 payload, 아니면 None을 반환한다."""
    defaults = defaults or {}
    products = st.text_area(
        "주요 상품 (한 줄에 하나, 1~5개)",
        value=list_to_lines(defaults.get("products")),
        key=f"{prefix}_products",
    )
    target_customers = st.text_area(
        "타깃 고객 (10~300자)",
        value=defaults.get("target_customers", ""),
        key=f"{prefix}_target",
    )
    strengths = st.text_area(
        "가게의 강점 (10~500자)",
        value=defaults.get("strengths", ""),
        key=f"{prefix}_strengths",
    )
    moods = st.multiselect(
        "원하는 분위기 (1~3개)",
        options=list(MOOD_LABELS.keys()),
        default=defaults.get("desired_moods", []),
        format_func=lambda value: MOOD_LABELS[value],
        key=f"{prefix}_moods",
    )
    col1, col2 = st.columns(2)
    region = col1.text_input(
        "지역 (선택)", value=defaults.get("region") or "", key=f"{prefix}_region"
    )
    price_range = col2.text_input(
        "가격대 (선택)",
        value=defaults.get("price_range") or "",
        key=f"{prefix}_price",
    )
    existing_copy = st.text_area(
        "기존 홍보 문구 (선택)",
        value=defaults.get("existing_copy") or "",
        key=f"{prefix}_copy",
    )
    avoid_expressions = st.text_area(
        "피하고 싶은 표현 (선택, 한 줄에 하나)",
        value=list_to_lines(defaults.get("avoid_expressions")),
        key=f"{prefix}_avoid",
    )

    payload: dict = {
        "products": lines_to_list(products),
        "target_customers": target_customers.strip(),
        "strengths": strengths.strip(),
        "desired_moods": moods,
        "avoid_expressions": lines_to_list(avoid_expressions),
        "campaign_facts": {},
    }
    if region.strip():
        payload["region"] = region.strip()
    if price_range.strip():
        payload["price_range"] = price_range.strip()
    if existing_copy.strip():
        payload["existing_copy"] = existing_copy.strip()
    return payload


# --- 새 가게 생성 화면 ---
def render_create_brand(client: BackendClient) -> None:
    st.header("새 가게 등록")
    with st.form("create_brand"):
        col1, col2 = st.columns(2)
        name = col1.text_input("가게 이름 (1~50자)")
        industry = col2.text_input("업종 (1~50자)")
        st.divider()
        profile = render_profile_fields("create")
        submitted = st.form_submit_button("가게 만들기", type="primary")

    if submitted:
        payload = {
            "name": name.strip(),
            "industry": industry.strip(),
            "profile": profile,
        }
        try:
            brand = client.create_brand(payload)
            st.session_state["selected_brand_id"] = brand["id"]
            st.success(f"'{brand['name']}' 가게를 만들었습니다.")
            st.rerun()
        except ApiError as error:
            show_api_error(error)


# --- 분석 결과 표시 ---
def render_analysis_detail(client: BackendClient, analysis: dict) -> None:
    status = analysis["status"]
    st.caption(
        f"상태: {STATUS_LABELS.get(status, status)} · 생성일 {analysis['created_at']}"
    )

    if status == "stale":
        st.warning("가게 프로필이 변경되어 오래된 분석입니다. 새 분석을 생성해 주세요.")
    elif status == "superseded":
        st.info("더 최신 승인 분석이 있어 보관된 분석입니다.")

    editable = status == "draft"
    with st.form(f"edit_{analysis['id']}"):
        brand_summary = st.text_area(
            "브랜드 요약 (1~300자)",
            value=analysis["brand_summary"],
            disabled=not editable,
        )
        value_proposition = st.text_area(
            "핵심 가치 제안 (1~500자)",
            value=analysis["value_proposition"],
            disabled=not editable,
        )
        col1, col2 = st.columns(2)
        target_segments = col1.text_area(
            "타깃 세그먼트 (한 줄에 하나)",
            value=list_to_lines(analysis["target_segments"]),
            disabled=not editable,
        )
        customer_needs = col2.text_area(
            "고객 니즈 (한 줄에 하나)",
            value=list_to_lines(analysis["customer_needs"]),
            disabled=not editable,
        )
        differentiators = col1.text_area(
            "차별점 (한 줄에 하나)",
            value=list_to_lines(analysis["differentiators"]),
            disabled=not editable,
        )
        brand_voice = col2.text_area(
            "브랜드 보이스 (정확히 3개)",
            value=list_to_lines(analysis["brand_voice"]),
            disabled=not editable,
        )
        recommended_keywords = col1.text_area(
            "추천 키워드 (한 줄에 하나)",
            value=list_to_lines(analysis["recommended_keywords"]),
            disabled=not editable,
        )
        avoid_expressions = col2.text_area(
            "피할 표현 (한 줄에 하나)",
            value=list_to_lines(analysis["avoid_expressions"]),
            disabled=not editable,
        )
        save = st.form_submit_button("수정 저장", disabled=not editable)

    if save and editable:
        payload = {
            "brand_summary": brand_summary.strip(),
            "value_proposition": value_proposition.strip(),
            "target_segments": lines_to_list(target_segments),
            "customer_needs": lines_to_list(customer_needs),
            "differentiators": lines_to_list(differentiators),
            "brand_voice": lines_to_list(brand_voice),
            "recommended_keywords": lines_to_list(recommended_keywords),
            "avoid_expressions": lines_to_list(avoid_expressions),
        }
        try:
            client.update_analysis(analysis["id"], payload)
            st.success("수정 내용을 저장했습니다.")
            st.rerun()
        except ApiError as error:
            show_api_error(error)

    if status == "draft":
        if st.button("이 분석 승인하기", key=f"approve_{analysis['id']}", type="primary"):
            try:
                client.approve_analysis(analysis["id"])
                st.success("분석을 승인했습니다.")
                st.rerun()
            except ApiError as error:
                show_api_error(error)


# --- 선택된 가게 화면 ---
def render_brand_workspace(client: BackendClient, brand_id: str) -> None:
    try:
        brand = client.get_brand(brand_id)
    except ApiError as error:
        show_api_error(error)
        return

    st.header(f"{brand['name']}")
    st.caption(f"업종: {brand['industry']}")

    profile = brand["active_profile"]
    with st.expander(f"현재 프로필 (버전 {profile['version']})", expanded=False):
        st.write("**주요 상품**:", ", ".join(profile["products"]))
        st.write("**타깃 고객**:", profile["target_customers"])
        st.write("**강점**:", profile["strengths"])
        st.write(
            "**분위기**:",
            ", ".join(MOOD_LABELS.get(m, m) for m in profile["desired_moods"]),
        )

    tab_analysis, tab_profile = st.tabs(["브랜드 분석", "프로필 새 버전"])

    with tab_analysis:
        if st.button("AI 브랜드 분석 생성", type="primary"):
            try:
                client.generate_analysis(brand_id)
                st.rerun()
            except ApiError as error:
                show_api_error(error)

        try:
            analyses = client.list_analyses(brand_id)
        except ApiError as error:
            show_api_error(error)
            analyses = []

        if not analyses:
            st.info("아직 생성된 분석이 없습니다. 위 버튼으로 분석을 생성하세요.")
        for analysis in analyses:
            label = STATUS_LABELS.get(analysis["status"], analysis["status"])
            with st.expander(
                f"분석 {analysis['created_at']} · {label}",
                expanded=(analysis["status"] in ("draft", "approved")),
            ):
                render_analysis_detail(client, analysis)

    with tab_profile:
        st.write("가게 정보가 바뀌면 새 프로필 버전을 만듭니다. 기존 분석은 보존됩니다.")
        with st.form("new_profile"):
            profile_payload = render_profile_fields("newver", defaults=profile)
            submitted = st.form_submit_button("새 프로필 버전 저장")
        if submitted:
            try:
                client.create_profile_version(brand_id, profile_payload)
                st.success("새 프로필 버전을 저장했습니다.")
                st.rerun()
            except ApiError as error:
                show_api_error(error)


def main() -> None:
    st.set_page_config(page_title="AI 소상공인 콘텐츠 스튜디오", layout="wide")
    st.title("AI 소상공인 콘텐츠 스튜디오")

    render_sidebar()
    client = get_client()

    brand_id = st.session_state.get("selected_brand_id")
    if brand_id is None:
        render_create_brand(client)
    else:
        render_brand_workspace(client, brand_id)


if __name__ == "__main__":
    main()
