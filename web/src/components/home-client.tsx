"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Brand } from "@/lib/types";

export function HomeClient() {
  const [brands, setBrands] = useState<Brand[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api<{ items: Brand[] }>("/brands?limit=6&offset=0")
      .then((result) => setBrands(result.items))
      .catch(() => setBrands([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main>
      <section className="shell hero">
        <div>
          <p className="eyebrow">AI brand & content workspace</p>
          <h1>
            가게의 이야기를,
            <br />
            브랜드로 만듭니다.
          </h1>
          <p className="hero-copy">
            전문 마케터 없이도 브랜드의 기준을 세우고, 4주 캠페인과
            Instagram 콘텐츠를 한곳에서 완성하세요.
          </p>
          <div className="button-row">
            <Link href="/studio/new" className="button primary">
              새 브랜드 시작하기 <span>→</span>
            </Link>
            {brands[0] && (
              <Link href={`/studio/${brands[0].id}`} className="button">
                최근 작업 계속하기
              </Link>
            )}
          </div>
        </div>
        <div className="poster-frame" aria-hidden="true">
          <div className="poster-index">
            <span>BRAND / 01</span>
            <span>2026</span>
          </div>
          <div className="poster-title">
            YOUR STORY,
            <br />
            MADE CLEAR.
          </div>
        </div>
      </section>

      <section id="process" className="section">
        <div className="shell">
          <div className="section-heading">
            <p className="eyebrow">How it works</p>
            <h2>흩어진 가게의 강점을 하나의 목소리로 정리합니다.</h2>
          </div>
          <div className="process-grid">
            {[
              ["01", "Brand", "상품, 고객, 강점을 분석해 브랜드의 기준을 세웁니다."],
              ["02", "Campaign", "목표에 맞는 4주 홍보 전략과 주제를 설계합니다."],
              ["03", "Content", "게시물 문구, 이미지 콘셉트, 캘린더를 완성합니다."],
            ].map(([number, title, copy]) => (
              <article className="process-card" key={number}>
                <span className="process-number">{number}</span>
                <h3>{title}</h3>
                <p>{copy}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section id="recent" className="section">
        <div className="shell">
          <div className="section-heading">
            <p className="eyebrow">Recent work</p>
            <h2>멈춘 곳에서 바로 이어서 작업하세요.</h2>
          </div>
          {loading ? (
            <div className="empty-card">최근 작업을 불러오는 중입니다.</div>
          ) : brands.length ? (
            <div className="recent-grid">
              {brands.slice(0, 3).map((brand) => (
                <Link
                  href={`/studio/${brand.id}`}
                  className="recent-card"
                  key={brand.id}
                >
                  <div className="card-meta">
                    <span>{brand.industry}</span>
                    <span>PROFILE V{brand.active_profile.version}</span>
                  </div>
                  <h3>{brand.name}</h3>
                  <p>{brand.active_profile.strengths}</p>
                </Link>
              ))}
            </div>
          ) : (
            <div className="empty-card">
              아직 저장된 브랜드가 없습니다.
              <br />
              첫 브랜드의 기준을 만들어 보세요.
            </div>
          )}
        </div>
      </section>

      <footer className="site-footer">
        <div className="shell footer-inner">
          <strong>BRAND STUDIO</strong>
          <span>Brand analysis · Campaign · Content calendar</span>
        </div>
      </footer>
    </main>
  );
}
