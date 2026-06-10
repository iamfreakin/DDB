from __future__ import annotations

import html
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

CAMPAIGN_GOALS: dict[str, str] = {
    "new_product": "신메뉴/신상품 홍보",
    "new_customer": "신규 고객 방문 유도",
    "repeat_visit": "재방문 유도",
    "seasonal_event": "시즌/행사 홍보",
    "brand_awareness": "브랜드 인지도 향상",
}

CONTENT_STATUS_LABELS: dict[str, str] = {
    "idea": "아이디어",
    "draft": "초안",
    "approved": "승인됨",
    "published": "게시 완료",
    "on_hold": "보류",
}

APP_CSS = """
<style>
    :root {
        --ink: #111111;
        --muted: #6f6f6f;
        --line: #e7e7e7;
        --soft: #f7f7f5;
        --paper: #ffffff;
    }

    .stApp { background: var(--paper); color: var(--ink); }

    [data-testid="stAppViewContainer"] > .main .block-container {
        max-width: 1180px;
        padding: 3.4rem 3rem 6rem;
    }

    [data-testid="stSidebar"] {
        background: var(--soft);
        border-right: 1px solid var(--line);
    }

    [data-testid="stSidebar"] .block-container { padding: 2rem 1.4rem; }

    h1, h2, h3 { color: var(--ink); letter-spacing: -0.035em; }
    h1 {
        font-size: clamp(2rem, 4vw, 3.6rem) !important;
        font-weight: 650 !important;
        line-height: 1.04 !important;
    }
    h2 { margin-top: 2.5rem !important; font-weight: 620 !important; }
    p, label, .stCaption { letter-spacing: -0.012em; }

    .app-kicker {
        margin-bottom: 0.65rem;
        color: var(--muted);
        font-size: 0.74rem;
        font-weight: 700;
        letter-spacing: 0.16em;
        text-transform: uppercase;
    }

    .app-lead, .section-intro {
        max-width: 680px;
        color: var(--muted);
        line-height: 1.7;
    }
    .app-lead { margin: 0.8rem 0 2.4rem; font-size: 1.05rem; }
    .section-intro { margin: 0.35rem 0 1.5rem; }

    .brand-hero {
        margin-bottom: 2rem;
        padding: 0.4rem 0 2rem;
        border-bottom: 1px solid var(--line);
    }
    .brand-hero h1 { margin: 0.2rem 0 0.65rem; }
    .brand-meta { color: var(--muted); font-size: 0.94rem; }

    .metric-row {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.8rem;
        margin: 1.2rem 0 2rem;
    }
    .metric-card {
        min-height: 92px;
        padding: 1.15rem 1.2rem;
        background: var(--soft);
        border: 1px solid #efefed;
        border-radius: 4px;
    }
    .metric-label {
        color: var(--muted);
        font-size: 0.76rem;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }
    .metric-value { margin-top: 0.5rem; font-size: 1.03rem; font-weight: 620; }

    .content-card {
        margin: 0.5rem 0 1.1rem;
        padding: 1.35rem 1.45rem;
        border: 1px solid var(--line);
        border-radius: 4px;
        background: var(--paper);
    }
    .content-card.selected {
        border-color: var(--ink);
        box-shadow: inset 3px 0 0 var(--ink);
    }
    .content-card .eyebrow {
        color: var(--muted);
        font-size: 0.74rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }
    .content-card .opening {
        margin: 0.7rem 0 0.75rem;
        font-size: 1.12rem;
        font-weight: 620;
        line-height: 1.45;
    }

    div[data-testid="stButton"] > button,
    div[data-testid="stFormSubmitButton"] > button,
    div[data-testid="stLinkButton"] > a {
        min-height: 2.65rem;
        border-radius: 2px;
        font-weight: 600;
        transition: none;
    }
    button[kind="primary"] {
        background: var(--ink);
        border-color: var(--ink);
        color: white;
    }
    button[kind="secondary"] {
        background: white;
        border-color: #cfcfcf;
        color: var(--ink);
    }
    div[role="radiogroup"] {
        gap: 1rem;
    }
    div[role="radiogroup"] label {
        padding: 0.28rem 0;
        color: var(--muted);
        font-weight: 600;
    }
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div,
    textarea { border-radius: 2px !important; }
    [data-testid="stExpander"] {
        border: 1px solid var(--line);
        border-radius: 3px;
        box-shadow: none;
    }
    [data-testid="stDataFrame"], [data-testid="stTable"] {
        border: 1px solid var(--line);
    }
    hr { border-color: var(--line) !important; }

    @media (max-width: 760px) {
        [data-testid="stAppViewContainer"] > .main .block-container {
            padding: 2rem 1.1rem 4rem;
        }
        .metric-row { grid-template-columns: 1fr; }
    }
</style>
"""


def get_client() -> BackendClient:
    base_url = st.session_state.get("base_url", os.getenv("BACKEND_URL", DEFAULT_BASE_URL))
    openai_api_key = st.session_state.get("openai_api_key") or None
    openai_model = st.session_state.get("openai_model") or "gpt-5-mini"
    return BackendClient(base_url, openai_api_key=openai_api_key, openai_model=openai_model)


@st.cache_data(ttl=60, show_spinner=False)
def get_health(base_url: str) -> dict:
    return BackendClient(base_url).health()


@st.cache_data(ttl=10, show_spinner=False)
def get_brands(base_url: str) -> list[dict]:
    return BackendClient(base_url).list_brands().get("items", [])


def clear_navigation_cache() -> None:
    get_health.clear()
    get_brands.clear()


def lines_to_list(text: str) -> list[str]:
    """줄 단위 입력을 공백 제거 후 빈 줄을 뺀 리스트로 변환한다."""
    return [line.strip() for line in text.splitlines() if line.strip()]


def list_to_lines(values: list[str] | None) -> str:
    return "\n".join(values or [])


def key_value_lines_to_dict(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in lines_to_list(text):
        if ":" in line:
            key, value = line.split(":", 1)
        elif "=" in line:
            key, value = line.split("=", 1)
        else:
            continue
        result[key.strip()] = value.strip()
    return result


def show_api_error(error: ApiError) -> None:
    st.error(f"{error.message}")
    for item in error.field_errors:
        st.caption(f"- {item.get('field', '')}: {item.get('message', '')}")


# --- 사이드바: 연결 상태와 가게 선택 ---
def render_sidebar() -> None:
    st.session_state.setdefault(
        "base_url", os.getenv("BACKEND_URL", DEFAULT_BASE_URL)
    )
    st.session_state.setdefault("openai_api_key", "")
    st.session_state.setdefault("openai_model", "gpt-5-mini")

    st.sidebar.markdown("### BRAND STUDIO")
    st.sidebar.caption("브랜드 전략부터 콘텐츠 캘린더까지")

    try:
        health = get_health(st.session_state["base_url"])
        st.sidebar.caption(f"● 연결됨 · API v{health.get('version', '?')}")
    except ApiError as error:
        st.sidebar.error(error.message)
        st.stop()

    st.sidebar.divider()
    st.sidebar.caption("WORKSPACE")

    try:
        brands = get_brands(st.session_state["base_url"])
    except ApiError as error:
        st.sidebar.error(error.message)
        brands = []

    options = {"+ 새 가게": None}
    for brand in brands:
        options[f"{brand['name']} · {brand['industry']}"] = brand["id"]

    selected_brand_id = st.session_state.get("selected_brand_id")
    selected_index = 0
    option_values = list(options.values())
    if selected_brand_id in option_values:
        selected_index = option_values.index(selected_brand_id)

    selection = st.sidebar.radio(
        "가게 선택",
        list(options.keys()),
        index=selected_index,
        label_visibility="collapsed",
    )
    st.session_state["selected_brand_id"] = options[selection]

    st.sidebar.divider()
    with st.sidebar.expander("연결 및 AI 설정"):
        with st.form("connection_settings"):
            base_url = st.text_input(
                "백엔드 주소", value=st.session_state["base_url"]
            )
            openai_api_key = st.text_input(
                "OpenAI API 키 (선택)",
                value=st.session_state["openai_api_key"],
                type="password",
                help="브라우저 세션에만 보관되며 생성 요청에만 전달됩니다.",
            )
            openai_model = st.text_input(
                "OpenAI 모델", value=st.session_state["openai_model"]
            )
            apply_settings = st.form_submit_button("설정 적용")

        if apply_settings:
            st.session_state["base_url"] = base_url.strip() or DEFAULT_BASE_URL
            st.session_state["openai_api_key"] = openai_api_key.strip()
            st.session_state["openai_model"] = openai_model.strip() or "gpt-5-mini"
            clear_navigation_cache()
            st.rerun()

        mode = "OpenAI" if st.session_state["openai_api_key"] else "Mock"
        st.caption(f"현재 생성 모드: {mode}")


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
    st.markdown('<div class="app-kicker">New workspace</div>', unsafe_allow_html=True)
    st.title("브랜드의 기준부터 시작합니다.")
    st.markdown(
        '<p class="app-lead">가게의 상품, 고객, 강점을 입력하면 이후의 분석과 콘텐츠가 같은 목소리를 유지합니다.</p>',
        unsafe_allow_html=True,
    )
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
            clear_navigation_cache()
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


def get_approved_analysis(analyses: list[dict]) -> dict | None:
    for analysis in analyses:
        if analysis["status"] == "approved":
            return analysis
    return None


def render_campaign_form(
    client: BackendClient, brand: dict, approved_analysis: dict
) -> None:
    st.subheader("새 캠페인")
    st.markdown(
        '<p class="section-intro">목표와 강조 상품을 정하면 4주 캠페인의 기준이 만들어집니다.</p>',
        unsafe_allow_html=True,
    )
    profile = brand["active_profile"]
    with st.form("create_campaign"):
        col1, col2 = st.columns(2)
        name = col1.text_input("캠페인명", value=f"{brand['name']} 4주 캠페인")
        goal = col2.selectbox(
            "목표",
            options=list(CAMPAIGN_GOALS.keys()),
            format_func=lambda value: CAMPAIGN_GOALS[value],
        )
        start_date = col1.date_input("시작일")
        highlighted = col2.multiselect(
            "강조 상품",
            options=profile["products"],
            default=profile["products"][:1],
        )
        facts_text = st.text_area(
            "필수 사실 정보 (key: value, 한 줄에 하나)",
            value="price: \nsales_period: ",
        )
        submitted = st.form_submit_button("캠페인 생성", type="primary")

    if submitted:
        try:
            client.create_campaign(
                {
                    "brand_id": brand["id"],
                    "brand_analysis_id": approved_analysis["id"],
                    "name": name.strip(),
                    "goal": goal,
                    "start_date": start_date.isoformat(),
                    "highlighted_products": highlighted,
                    "required_facts": {
                        key: value
                        for key, value in key_value_lines_to_dict(facts_text).items()
                        if value
                    },
                }
            )
            st.success("캠페인을 생성했습니다.")
            st.rerun()
        except ApiError as error:
            show_api_error(error)


@st.fragment
def render_content_detail(client: BackendClient, content_id: str) -> None:
    try:
        content = client.get_content(content_id)
    except ApiError as error:
        show_api_error(error)
        return

    st.markdown(
        f"""
        <div class="content-card selected">
            <div class="eyebrow">WEEK {content['week_number']} · {html.escape(content['content_type'])}</div>
            <div class="opening">{html.escape(content['topic'])}</div>
            <div>{html.escape(content['core_message'])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    variants = content["variants"]
    columns = st.columns(min(len(variants), 3)) if variants else []
    for index, variant in enumerate(variants):
        is_selected = content.get("selected_variant_id") == variant["id"]
        with columns[index % len(columns)].container(border=True):
            selected_label = " · SELECTED" if is_selected else ""
            st.caption(
                f"VERSION {variant['variant_number']} · {variant['tone']}{selected_label}"
            )
            st.markdown(f"**{variant['opening_line']}**")
            st.write(variant["body"])
            st.caption(variant["cta"])
            st.caption(" ".join(variant["hashtags"]))
            st.caption(f"이미지 콘셉트 · {variant['image_concept']}")
            if st.button(
                "선택됨" if is_selected else "이 버전 선택",
                key=f"select_{content['id']}_{variant['id']}",
                type="primary" if is_selected else "secondary",
                disabled=is_selected,
                use_container_width=True,
            ):
                try:
                    client.select_variant(content["id"], variant["id"])
                    st.toast("사용할 버전을 선택했습니다.")
                    st.rerun(scope="fragment")
                except ApiError as error:
                    show_api_error(error)

    action_cols = st.columns(3)
    if action_cols[0].button(
        "변형 추가",
        key=f"variant_{content['id']}",
        disabled=len([item for item in variants if item["origin"] == "ai"]) >= 3,
        use_container_width=True,
    ):
        try:
            client.generate_variant(content["id"])
            st.toast("새 변형을 생성했습니다.")
            st.rerun(scope="fragment")
        except ApiError as error:
            show_api_error(error)

    if action_cols[1].button(
        "포스터 브리프",
        key=f"brief_{content['id']}",
        use_container_width=True,
    ):
        try:
            client.generate_poster_brief(content["id"])
            st.toast("포스터 브리프를 생성했습니다.")
            st.rerun(scope="fragment")
        except ApiError as error:
            show_api_error(error)

    if action_cols[2].button(
        "앞 2개 비교",
        key=f"compare_{content['id']}",
        disabled=len(variants) < 2,
        use_container_width=True,
    ):
        try:
            client.create_comparison(
                f"{content['topic']} 비교",
                [variants[0]["id"], variants[1]["id"]],
            )
            st.toast("비교 세트를 저장했습니다.")
        except ApiError as error:
            show_api_error(error)

    if content.get("poster_brief"):
        brief = content["poster_brief"]
        st.markdown("### 포스터 브리프")
        brief_col, prompt_col = st.columns([0.8, 1.2])
        with brief_col:
            st.caption("HEADLINE")
            st.markdown(f"**{brief['headline']}**")
            st.caption(f"분위기 · {brief['visual_mood']}")
            st.caption(f"비율 · {brief['aspect_ratio']}")
        with prompt_col:
            st.caption("IMAGE PROMPT")
            st.code(brief["image_prompt"], language=None)


def render_campaign_workspace(client: BackendClient, brand: dict) -> None:
    try:
        analyses = client.list_analyses(brand["id"])
    except ApiError as error:
        show_api_error(error)
        return

    approved_analysis = get_approved_analysis(analyses)
    if not approved_analysis:
        st.info("캠페인을 만들려면 먼저 브랜드 분석을 승인해 주세요.")
        return

    try:
        campaigns = client.list_campaigns(brand["id"]).get("items", [])
    except ApiError as error:
        show_api_error(error)
        campaigns = []

    if not campaigns:
        render_campaign_form(client, brand, approved_analysis)
        return

    view = st.radio(
        "캠페인 메뉴",
        ["콘텐츠", "전략", "캘린더", "새 캠페인"],
        horizontal=True,
        index=0,
        key=f"campaign_view_{brand['id']}",
        label_visibility="collapsed",
    )
    if view == "새 캠페인":
        render_campaign_form(client, brand, approved_analysis)
        return

    labels = {f"{item['name']} · {item['status']}": item for item in campaigns}
    selected_label = st.selectbox(
        "캠페인 선택",
        list(labels.keys()),
        key=f"campaign_select_{brand['id']}",
    )
    campaign = labels[selected_label]
    st.markdown(
        f"""
        <div class="metric-row">
            <div class="metric-card">
                <div class="metric-label">Period</div>
                <div class="metric-value">{html.escape(campaign['start_date'])} — {html.escape(campaign['end_date'])}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Goal</div>
                <div class="metric-value">{html.escape(CAMPAIGN_GOALS.get(campaign['goal'], campaign['goal']))}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Status</div>
                <div class="metric-value">{html.escape(campaign['status'].replace('_', ' ').upper())}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if view == "전략":
        st.subheader("캠페인 전략")
        try:
            strategies = client.list_strategies(campaign["id"])
        except ApiError as error:
            show_api_error(error)
            strategies = []

        if not strategies:
            st.markdown(
                '<p class="section-intro">승인된 브랜드 분석을 바탕으로 4주 전략과 8개 주제를 설계합니다.</p>',
                unsafe_allow_html=True,
            )
            if st.button("전략 생성", type="primary"):
                try:
                    client.generate_strategy(campaign["id"])
                    st.rerun()
                except ApiError as error:
                    show_api_error(error)
            return

        strategy = strategies[0]
        with st.container(border=True):
            st.write("**핵심 메시지**", strategy["core_message"])
            st.write("**콘텐츠 기둥**", ", ".join(strategy["content_pillars"]))
        st.dataframe(
            strategy["post_topics"],
            use_container_width=True,
            hide_index=True,
        )
        return

    if view == "캘린더":
        st.subheader("콘텐츠 캘린더")
        try:
            calendar = client.list_calendar(campaign["id"])
        except ApiError as error:
            show_api_error(error)
            calendar = []

        if not calendar:
            st.markdown(
                '<p class="section-intro">완성된 게시물을 4주 일정에 주 2회씩 배치합니다.</p>',
                unsafe_allow_html=True,
            )
            if st.button("캘린더 생성", type="primary"):
                try:
                    client.create_calendar(campaign["id"])
                    st.rerun()
                except ApiError as error:
                    show_api_error(error)
            return

        st.dataframe(
            [
                {
                    "날짜": item["scheduled_date"],
                    "상태": CONTENT_STATUS_LABELS.get(item["status"], item["status"]),
                    "주제": item["content"]["topic"] if item.get("content") else "",
                }
                for item in calendar
            ],
            use_container_width=True,
            hide_index=True,
        )
        download_col1, download_col2 = st.columns(2)
        download_col1.link_button(
            "캘린더 CSV 다운로드",
            client.export_calendar_csv_url(campaign["id"]),
            use_container_width=True,
        )
        download_col2.link_button(
            "브랜드 보고서 다운로드",
            client.export_analysis_markdown_url(approved_analysis["id"]),
            use_container_width=True,
        )
        return

    st.subheader("콘텐츠")
    try:
        strategies = client.list_strategies(campaign["id"])
    except ApiError as error:
        show_api_error(error)
        strategies = []

    if not strategies:
        st.info("먼저 전략 메뉴에서 캠페인 전략을 생성해 주세요.")
        return

    try:
        contents = client.list_contents(campaign["id"])
    except ApiError as error:
        show_api_error(error)
        contents = []

    if not contents:
        st.markdown(
            '<p class="section-intro">전략의 8개 주제를 실제 Instagram 게시물 초안으로 바꿉니다.</p>',
            unsafe_allow_html=True,
        )
        if st.button("게시물 8개 생성", type="primary"):
            try:
                client.generate_contents(
                    campaign["id"], strategies[0]["id"], variants_per_content=2
                )
                st.rerun()
            except ApiError as error:
                show_api_error(error)
        return

    content_labels = {
        (
            f"{item['sequence']:02d}  {item['topic']}  ·  "
            f"{CONTENT_STATUS_LABELS.get(item['status'], item['status'])}"
        ): item["id"]
        for item in contents
    }
    selected_content_label = st.selectbox(
        "게시물 선택",
        list(content_labels.keys()),
        key=f"content_select_{campaign['id']}",
    )
    render_content_detail(client, content_labels[selected_content_label])


# --- 선택된 가게 화면 ---
def render_brand_workspace(client: BackendClient, brand_id: str) -> None:
    try:
        brand = client.get_brand(brand_id)
    except ApiError as error:
        show_api_error(error)
        return

    profile = brand["active_profile"]
    moods = ", ".join(MOOD_LABELS.get(m, m) for m in profile["desired_moods"])
    st.markdown(
        f"""
        <div class="brand-hero">
            <div class="app-kicker">Current brand</div>
            <h1>{html.escape(brand['name'])}</h1>
            <div class="brand-meta">{html.escape(brand['industry'])} · 프로필 v{profile['version']} · {html.escape(moods)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    page = st.radio(
        "작업 단계",
        ["브랜드 분석", "캠페인 · 콘텐츠", "가게 프로필"],
        horizontal=True,
        index=0,
        key=f"workspace_page_{brand_id}",
        label_visibility="collapsed",
    )

    if page == "브랜드 분석":
        st.subheader("브랜드 분석")
        st.markdown(
            '<p class="section-intro">가게가 누구에게 어떤 이유로 선택되어야 하는지 정리하고, 콘텐츠의 언어를 승인합니다.</p>',
            unsafe_allow_html=True,
        )
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
        return

    if page == "캠페인 · 콘텐츠":
        render_campaign_workspace(client, brand)
        return

    st.subheader("가게 프로필")
    st.markdown(
        '<p class="section-intro">정보를 바꾸면 새 버전으로 저장됩니다. 기존 분석과 결과물은 이력으로 보존됩니다.</p>',
        unsafe_allow_html=True,
    )
    with st.expander(f"현재 프로필 · v{profile['version']}", expanded=False):
        st.write("**주요 상품**:", ", ".join(profile["products"]))
        st.write("**타깃 고객**:", profile["target_customers"])
        st.write("**강점**:", profile["strengths"])
        st.write("**분위기**:", moods)

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
    st.set_page_config(
        page_title="Brand Studio",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(APP_CSS, unsafe_allow_html=True)

    render_sidebar()
    client = get_client()

    brand_id = st.session_state.get("selected_brand_id")
    if brand_id is None:
        render_create_brand(client)
    else:
        render_brand_workspace(client, brand_id)


if __name__ == "__main__":
    main()
