"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { Brand, Mood } from "@/lib/types";

const moods: { value: Mood; label: string }[] = [
  { value: "warm", label: "따뜻한" },
  { value: "friendly", label: "친근한" },
  { value: "emotional", label: "감성적인" },
  { value: "premium", label: "프리미엄" },
  { value: "playful", label: "발랄한" },
  { value: "clean", label: "깔끔한" },
  { value: "trustworthy", label: "신뢰감 있는" },
];

const lines = (value: string) =>
  value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);

export function NewBrandForm() {
  const router = useRouter();
  const [selectedMoods, setSelectedMoods] = useState<Mood[]>([]);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function toggleMood(mood: Mood) {
    setSelectedMoods((current) => {
      if (current.includes(mood)) {
        return current.filter((item) => item !== mood);
      }
      if (current.length >= 3) return current;
      return [...current, mood];
    });
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    const data = new FormData(event.currentTarget);

    try {
      const brand = await api<Brand>("/brands", {
        method: "POST",
        body: JSON.stringify({
          name: data.get("name"),
          industry: data.get("industry"),
          profile: {
            products: lines(String(data.get("products") || "")),
            target_customers: data.get("target_customers"),
            strengths: data.get("strengths"),
            desired_moods: selectedMoods,
            region: data.get("region") || null,
            price_range: data.get("price_range") || null,
            existing_copy: data.get("existing_copy") || null,
            avoid_expressions: lines(
              String(data.get("avoid_expressions") || ""),
            ),
            campaign_facts: {},
          },
        }),
      });
      router.push(`/studio/${brand.id}`);
    } catch (caught) {
      setError(
        caught instanceof ApiError ? caught.message : "가게를 만들지 못했습니다.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={submit}>
      {error && <div className="error-box">{error}</div>}
      <div className="form-grid">
        <div className="field">
          <label htmlFor="name">가게 이름</label>
          <input className="input" id="name" name="name" required maxLength={50} />
        </div>
        <div className="field">
          <label htmlFor="industry">업종</label>
          <input
            className="input"
            id="industry"
            name="industry"
            required
            maxLength={50}
            placeholder="예: 카페, 공방, 미용실"
          />
        </div>
        <div className="field full">
          <label htmlFor="products">대표 상품·서비스</label>
          <textarea
            className="textarea"
            id="products"
            name="products"
            required
            placeholder={"아메리카노\n수제 크림라떼"}
          />
          <small>한 줄에 하나씩, 최대 5개</small>
        </div>
        <div className="field">
          <label htmlFor="target_customers">주요 고객</label>
          <textarea
            className="textarea"
            id="target_customers"
            name="target_customers"
            required
            minLength={10}
            maxLength={300}
          />
        </div>
        <div className="field">
          <label htmlFor="strengths">가게의 강점</label>
          <textarea
            className="textarea"
            id="strengths"
            name="strengths"
            required
            minLength={10}
            maxLength={500}
          />
        </div>
        <div className="field full">
          <label>원하는 분위기</label>
          <div className="checkbox-grid">
            {moods.map((mood) => (
              <label className="check-pill" key={mood.value}>
                <input
                  type="checkbox"
                  checked={selectedMoods.includes(mood.value)}
                  onChange={() => toggleMood(mood.value)}
                />
                <span>{mood.label}</span>
              </label>
            ))}
          </div>
          <small>최대 3개 선택</small>
        </div>
        <div className="field">
          <label htmlFor="region">지역 · 선택</label>
          <input className="input" id="region" name="region" />
        </div>
        <div className="field">
          <label htmlFor="price_range">가격대 · 선택</label>
          <input className="input" id="price_range" name="price_range" />
        </div>
        <div className="field">
          <label htmlFor="existing_copy">기존 홍보 문구 · 선택</label>
          <textarea
            className="textarea"
            id="existing_copy"
            name="existing_copy"
          />
        </div>
        <div className="field">
          <label htmlFor="avoid_expressions">피하고 싶은 표현 · 선택</label>
          <textarea
            className="textarea"
            id="avoid_expressions"
            name="avoid_expressions"
            placeholder="한 줄에 하나"
          />
        </div>
      </div>
      <div className="form-actions">
        <button
          className="button primary"
          type="submit"
          disabled={submitting || selectedMoods.length === 0}
        >
          {submitting ? "브랜드를 만드는 중..." : "브랜드 만들기 →"}
        </button>
      </div>
    </form>
  );
}
