from __future__ import annotations

from typing import Any


MOOD_LABELS = {
    "warm": "따뜻한",
    "friendly": "친근한",
    "emotional": "감성적인",
    "premium": "고급스러운",
    "playful": "재치 있는",
    "clean": "깔끔한",
    "trustworthy": "신뢰감 있는",
}


class MockTextGenerationProvider:
    name = "mock"
    model = "deterministic-v1"

    def generate_brand_analysis(
        self, brand: dict[str, Any], profile: dict[str, Any]
    ) -> dict[str, Any]:
        products = profile["products"]
        moods = [MOOD_LABELS[mood] for mood in profile["desired_moods"]]
        first_product = products[0]
        region = profile.get("region")
        location_phrase = f"{region}에서 " if region else ""
        missing_information = []
        if not profile.get("campaign_facts"):
            missing_information.append("가격, 판매 기간 등 캠페인 사실 정보")
        if not profile.get("existing_copy"):
            missing_information.append("기존 홍보 문구")
        return {
            "brand_summary": (
                f"{location_phrase}{first_product}와 {moods[0]} 경험을 전하는 "
                f"{brand['industry']} 브랜드"
            ),
            "target_segments": [profile["target_customers"]],
            "customer_needs": ["믿을 수 있는 상품 정보", "방문할 이유가 되는 경험"],
            "value_proposition": (
                f"{profile['strengths']}을 바탕으로 {first_product}의 매력을 "
                "일관된 메시지로 전달합니다."
            ),
            "differentiators": [profile["strengths"], f"대표 상품: {first_product}"],
            "brand_voice": (moods + ["솔직한", "명확한"])[:3],
            "recommended_keywords": [
                brand["name"].replace(" ", ""),
                first_product.replace(" ", ""),
                *[mood.replace(" ", "") for mood in moods[:2]],
            ],
            "avoid_expressions": profile["avoid_expressions"],
            "missing_information": missing_information,
        }

    def generate_campaign_strategy(
        self,
        brand: dict[str, Any],
        analysis: dict[str, Any],
        campaign: dict[str, Any],
    ) -> dict[str, Any]:
        product = campaign["highlighted_products"][0]
        goal_label = {
            "new_product": "신상품 인지도 확보",
            "new_customer": "신규 고객 방문 유도",
            "repeat_visit": "재방문 이유 강화",
            "seasonal_event": "시즌 행사 참여 유도",
            "brand_awareness": "브랜드 기억 강화",
        }[campaign["goal"]]
        content_types = ["product", "informational", "relationship", "promotion"]
        topics = [
            f"{product} 첫 소개",
            f"{product}의 매력 포인트",
            "가게 분위기와 이용 장면",
            "대표 고객 상황 공감",
            "제작 과정 또는 준비 이야기",
            "방문 전 알아두면 좋은 정보",
            "기간 한정 방문 유도",
            "캠페인 마무리 리마인드",
        ]
        return {
            "core_message": f"{analysis['brand_summary']} - {goal_label}",
            "weekly_goals": [
                {"week": 1, "goal": f"{product}을 자연스럽게 알린다."},
                {"week": 2, "goal": "차별점과 신뢰 요소를 설명한다."},
                {"week": 3, "goal": "방문 상황을 상상하게 만든다."},
                {"week": 4, "goal": "지금 방문해야 할 이유를 분명히 한다."},
            ],
            "content_pillars": ["상품", "신뢰", "공간", "방문 유도"],
            "post_topics": [
                {
                    "sequence": index + 1,
                    "week": (index // 2) + 1,
                    "topic": topic,
                    "content_type": content_types[index % len(content_types)],
                }
                for index, topic in enumerate(topics)
            ],
            "risk_notes": [
                "가격, 할인, 기간은 입력된 사실 정보만 사용하세요.",
                "과장 표현과 비교 비방을 피하세요.",
            ],
        }

    def generate_content_batch(
        self,
        brand: dict[str, Any],
        analysis: dict[str, Any],
        campaign: dict[str, Any],
        strategy: dict[str, Any],
        options: dict[str, Any],
    ) -> list[dict[str, Any]]:
        return [
            {
                "sequence": topic["sequence"],
                "week_number": topic["week"],
                "content_type": topic["content_type"],
                "topic": topic["topic"],
                "core_message": strategy["core_message"],
                "variants": [
                    self._variant(
                        brand,
                        campaign,
                        topic,
                        variant_index,
                        options.get("hashtag_count", 7),
                    )
                    for variant_index in range(1, options.get("variants_per_content", 1) + 1)
                ],
            }
            for topic in strategy["post_topics"]
        ]

    def generate_content_variant(
        self,
        brand: dict[str, Any],
        analysis: dict[str, Any],
        campaign: dict[str, Any],
        content: dict[str, Any],
        existing_variants: list[dict[str, Any]],
        options: dict[str, Any],
    ) -> dict[str, Any]:
        topic = {
            "sequence": content["sequence"],
            "week": content["week_number"],
            "topic": content["topic"],
            "content_type": content["content_type"],
        }
        return self._variant(
            brand,
            campaign,
            topic,
            len([item for item in existing_variants if item["origin"] == "ai"]) + 1,
            options.get("hashtag_count", 7),
            tone=options.get("tone"),
        )

    def generate_poster_brief(
        self,
        brand: dict[str, Any],
        analysis: dict[str, Any],
        campaign: dict[str, Any],
        content: dict[str, Any],
        selected_variant: dict[str, Any] | None,
    ) -> dict[str, Any]:
        product = campaign["highlighted_products"][0]
        headline = selected_variant["opening_line"] if selected_variant else content["topic"]
        return {
            "headline": headline[:100],
            "supporting_text": selected_variant["cta"] if selected_variant else "매장에서 만나보세요.",
            "visual_mood": ", ".join(analysis["brand_voice"]),
            "colors": ["cream", "warm brown", "soft white"],
            "layout_description": (
                "중앙에는 대표 상품을 크게 배치하고, 하단에는 짧은 CTA를 둔다. "
                "배경은 브랜드 분위기에 맞게 단정하고 따뜻하게 유지한다."
            ),
            "image_prompt": (
                f"{brand['name']}의 {product} 광고 포스터. "
                f"{content['topic']}을 표현하는 따뜻한 상업 사진 스타일, "
                "clean layout, realistic product photography, no text in image"
            ),
            "negative_prompt": "blurry, distorted text, fake logo, competitor brand",
            "aspect_ratio": "4:5",
        }

    def _variant(
        self,
        brand: dict[str, Any],
        campaign: dict[str, Any],
        topic: dict[str, Any],
        variant_number: int,
        hashtag_count: int,
        tone: str | None = None,
    ) -> dict[str, Any]:
        product = campaign["highlighted_products"][0]
        tone_names = ["따뜻한 소개형", "짧은 초대형", "정보 강조형"]
        selected_tone = tone or tone_names[(variant_number - 1) % len(tone_names)]
        fact_suffix = ""
        if campaign.get("required_facts"):
            fact_suffix = " " + " ".join(
                f"{key}: {value}" for key, value in campaign["required_facts"].items()
            )
        hashtags = [
            f"#{brand['name'].replace(' ', '')}",
            f"#{product.replace(' ', '')}",
            "#동네가게",
            "#소상공인",
            "#오늘의추천",
            "#방문환영",
            "#인스타그램",
            "#신메뉴",
            "#프로모션",
            "#브랜드스토리",
        ][:hashtag_count]
        return {
            "tone": selected_tone,
            "opening_line": f"{topic['topic']}, 오늘 {brand['name']}에서 만나보세요.",
            "body": (
                f"{product}을 중심으로 {topic['topic']} 이야기를 전합니다. "
                "가게의 강점과 분위기를 살려 고객이 방문 장면을 쉽게 떠올리도록 구성했어요."
                f"{fact_suffix}"
            ),
            "cta": "저장해 두고 편한 시간에 들러보세요.",
            "hashtags": hashtags,
            "image_concept": f"{product}이 잘 보이는 따뜻한 매장 장면",
            "quality_warnings": [],
        }
