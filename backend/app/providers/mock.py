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

