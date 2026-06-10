"use client";
/* eslint-disable react-hooks/set-state-in-effect -- sections load FastAPI state when their identifiers change. */

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { AiSettings } from "@/components/ai-settings";
import { PosterStudio } from "@/components/poster-studio";
import { api, ApiError, downloadUrl } from "@/lib/api";
import type {
  Analysis,
  Brand,
  CalendarItem,
  Campaign,
  Content,
  Strategy,
} from "@/lib/types";

type Section = "analysis" | "campaign" | "content" | "calendar" | "profile";

const goalLabels: Record<string, string> = {
  new_product: "신메뉴·신상품 홍보",
  new_customer: "신규 고객 방문",
  repeat_visit: "재방문 유도",
  seasonal_event: "시즌·행사 홍보",
  brand_awareness: "브랜드 인지도",
};

const sectionLabels: { id: Section; label: string }[] = [
  { id: "analysis", label: "브랜드 분석" },
  { id: "campaign", label: "캠페인 전략" },
  { id: "content", label: "콘텐츠" },
  { id: "calendar", label: "캘린더" },
  { id: "profile", label: "가게 프로필" },
];

function errorMessage(error: unknown) {
  return error instanceof ApiError
    ? error.message
    : "요청을 처리하지 못했습니다.";
}

export function Workspace({ brandId }: { brandId: string }) {
  const [brand, setBrand] = useState<Brand | null>(null);
  const [section, setSection] = useState<Section>("analysis");
  const [error, setError] = useState("");

  const loadBrand = useCallback(async () => {
    try {
      setBrand(await api<Brand>(`/brands/${brandId}`));
    } catch (caught) {
      setError(errorMessage(caught));
    }
  }, [brandId]);

  useEffect(() => {
    loadBrand();
  }, [loadBrand]);

  if (!brand) {
    return (
      <main className="shell loading">
        {error || "브랜드 작업실을 불러오는 중입니다."}
      </main>
    );
  }

  return (
    <>
      <header className="site-header">
        <div className="shell header-inner">
          <Link href="/" className="wordmark">
            BRAND STUDIO
          </Link>
          <nav className="header-nav">
            <Link href="/">홈</Link>
            <Link href="/studio/new" className="button small">
              새 브랜드
            </Link>
          </nav>
        </div>
      </header>

      <div className="studio-layout">
        <aside className="studio-sidebar">
          <p className="eyebrow">Current brand</p>
          <div className="brand-name">{brand.name}</div>
          <div className="brand-industry">
            {brand.industry} · Profile v{brand.active_profile.version}
          </div>
          <nav className="studio-nav">
            {sectionLabels.map((item) => (
              <button
                type="button"
                className={section === item.id ? "active" : ""}
                onClick={() => {
                  setError("");
                  setSection(item.id);
                }}
                key={item.id}
              >
                {item.label}
              </button>
            ))}
          </nav>
          <AiSettings />
        </aside>

        <main className="studio-main">
          {error && <div className="error-box">{error}</div>}
          {section === "analysis" && (
            <AnalysisSection brand={brand} onError={setError} />
          )}
          {section === "campaign" && (
            <CampaignSection
              brand={brand}
              onError={setError}
              onOpenContents={() => setSection("content")}
            />
          )}
          {section === "content" && (
            <ContentSection brand={brand} onError={setError} />
          )}
          {section === "calendar" && (
            <CalendarSection brand={brand} onError={setError} />
          )}
          {section === "profile" && (
            <ProfileSection brand={brand} onReload={loadBrand} onError={setError} />
          )}
        </main>
      </div>
    </>
  );
}

function SectionTitle({
  eyebrow,
  title,
  action,
}: {
  eyebrow: string;
  title: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="studio-title-row">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
      </div>
      {action}
    </div>
  );
}

function AnalysisSection({
  brand,
  onError,
}: {
  brand: Brand;
  onError: (message: string) => void;
}) {
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      setAnalyses(await api<Analysis[]>(`/brands/${brand.id}/analyses`));
    } catch (caught) {
      onError(errorMessage(caught));
    }
  }, [brand.id, onError]);

  useEffect(() => {
    load();
  }, [load]);

  async function generate() {
    setBusy(true);
    onError("");
    try {
      await api(
        `/brands/${brand.id}/analyses`,
        { method: "POST", body: JSON.stringify({ regenerate: analyses.length > 0 }) },
        true,
      );
      await load();
    } catch (caught) {
      onError(errorMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <SectionTitle
        eyebrow="01 · Brand definition"
        title="브랜드 분석"
        action={
          <button className="button primary" onClick={generate} disabled={busy}>
            {busy ? "분석 중..." : analyses.length ? "새 분석 생성" : "AI 분석 생성"}
          </button>
        }
      />
      {!analyses.length ? (
        <div className="info-box">
          아직 분석이 없습니다. 가게 정보를 바탕으로 브랜드의 고객, 가치와
          목소리를 정의하세요.
        </div>
      ) : (
        analyses.map((analysis) => (
          <AnalysisCard
            analysis={analysis}
            onChanged={load}
            onError={onError}
            key={analysis.id}
          />
        ))
      )}
    </>
  );
}

function AnalysisCard({
  analysis,
  onChanged,
  onError,
}: {
  analysis: Analysis;
  onChanged: () => Promise<void>;
  onError: (message: string) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [summary, setSummary] = useState(analysis.brand_summary);
  const [value, setValue] = useState(analysis.value_proposition);
  const [busy, setBusy] = useState(false);
  const editable = analysis.status === "draft";

  async function save() {
    setBusy(true);
    try {
      await api(`/analyses/${analysis.id}`, {
        method: "PATCH",
        body: JSON.stringify({
          brand_summary: summary,
          value_proposition: value,
        }),
      });
      setEditing(false);
      await onChanged();
    } catch (caught) {
      onError(errorMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  async function approve() {
    setBusy(true);
    try {
      await api(`/analyses/${analysis.id}/approve`, { method: "POST" });
      await onChanged();
    } catch (caught) {
      onError(errorMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  return (
    <article className="panel">
      <div className="panel-head">
        <div>
          <span className={`status ${analysis.status === "approved" ? "dark" : ""}`}>
            {analysis.status}
          </span>
          <h2 style={{ marginTop: 16 }}>
            {editing ? "분석 내용 수정" : analysis.brand_summary}
          </h2>
        </div>
        {editable && (
          <div className="toolbar-group">
            <button className="button small" onClick={() => setEditing(!editing)}>
              {editing ? "취소" : "수정"}
            </button>
            {!editing && (
              <button className="button small primary" onClick={approve} disabled={busy}>
                분석 승인
              </button>
            )}
          </div>
        )}
      </div>

      {editing ? (
        <div className="form-grid">
          <div className="field full">
            <label>브랜드 요약</label>
            <textarea
              className="textarea"
              value={summary}
              onChange={(event) => setSummary(event.target.value)}
            />
          </div>
          <div className="field full">
            <label>핵심 가치 제안</label>
            <textarea
              className="textarea"
              value={value}
              onChange={(event) => setValue(event.target.value)}
            />
          </div>
          <button className="button primary" onClick={save} disabled={busy}>
            수정 저장
          </button>
        </div>
      ) : (
        <div className="detail-grid">
          <Detail label="Value proposition" text={analysis.value_proposition} />
          <Detail label="Target" items={analysis.target_segments} />
          <Detail label="Customer needs" items={analysis.customer_needs} />
          <Detail label="Differentiators" items={analysis.differentiators} />
          <Detail label="Brand voice" items={analysis.brand_voice} />
          <Detail label="Keywords" items={analysis.recommended_keywords} />
        </div>
      )}
    </article>
  );
}

function Detail({
  label,
  text,
  items,
}: {
  label: string;
  text?: string;
  items?: string[];
}) {
  return (
    <div className="detail-cell">
      <div className="detail-label">{label}</div>
      {text && <p>{text}</p>}
      {items && (
        <div className="tag-row">
          {items.map((item) => (
            <span className="tag" key={item}>
              {item}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function useCampaignData(brandId: string, onError: (message: string) => void) {
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);

  const load = useCallback(async () => {
    try {
      const [analysisData, campaignData] = await Promise.all([
        api<Analysis[]>(`/brands/${brandId}/analyses`),
        api<{ items: Campaign[] }>(`/campaigns?brand_id=${brandId}&limit=100`),
      ]);
      setAnalyses(analysisData);
      setCampaigns(campaignData.items);
    } catch (caught) {
      onError(errorMessage(caught));
    }
  }, [brandId, onError]);

  useEffect(() => {
    load();
  }, [load]);

  return { analyses, campaigns, load };
}

function CampaignSection({
  brand,
  onError,
  onOpenContents,
}: {
  brand: Brand;
  onError: (message: string) => void;
  onOpenContents: () => void;
}) {
  const { analyses, campaigns, load } = useCampaignData(brand.id, onError);
  const [selectedId, setSelectedId] = useState("");
  const [strategy, setStrategy] = useState<Strategy | null>(null);
  const [busy, setBusy] = useState(false);
  const approved = analyses.find((item) => item.status === "approved");
  const selected = campaigns.find(
    (item) => item.id === (selectedId || campaigns[0]?.id),
  );

  useEffect(() => {
    if (!selected) {
      setStrategy(null);
      return;
    }
    api<Strategy[]>(`/campaigns/${selected.id}/strategies`)
      .then((items) => setStrategy(items[0] || null))
      .catch((caught) => onError(errorMessage(caught)));
  }, [selected, onError]);

  async function createCampaign(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!approved) return;
    setBusy(true);
    const data = new FormData(event.currentTarget);
    try {
      await api("/campaigns", {
        method: "POST",
        body: JSON.stringify({
          brand_id: brand.id,
          brand_analysis_id: approved.id,
          name: data.get("name"),
          goal: data.get("goal"),
          start_date: data.get("start_date"),
          highlighted_products: [data.get("product")],
          required_facts: {},
        }),
      });
      await load();
      event.currentTarget.reset();
    } catch (caught) {
      onError(errorMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  async function generateStrategy() {
    if (!selected) return;
    setBusy(true);
    try {
      const result = await api<Strategy>(
        `/campaigns/${selected.id}/strategies`,
        { method: "POST", body: JSON.stringify({ regenerate: Boolean(strategy) }) },
        true,
      );
      setStrategy(result);
    } catch (caught) {
      onError(errorMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  async function generateContents() {
    if (!selected || !strategy) return;
    setBusy(true);
    try {
      await api(
        `/campaigns/${selected.id}/contents:generate`,
        {
          method: "POST",
          body: JSON.stringify({
            strategy_id: strategy.id,
            variants_per_content: 2,
            hashtag_count: 7,
          }),
        },
        true,
      );
      onOpenContents();
    } catch (caught) {
      onError(errorMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <SectionTitle eyebrow="02 · Campaign plan" title="캠페인 전략" />
      {!approved && (
        <div className="info-box">
          브랜드 분석을 승인한 뒤 캠페인을 만들 수 있습니다.
        </div>
      )}
      {approved && (
        <details className="panel" open={!campaigns.length}>
          <summary>새 캠페인 만들기</summary>
          <form onSubmit={createCampaign} style={{ marginTop: 28 }}>
            <div className="form-grid">
              <div className="field">
                <label>캠페인명</label>
                <input
                  className="input"
                  name="name"
                  defaultValue={`${brand.name} 4주 캠페인`}
                  required
                />
              </div>
              <div className="field">
                <label>목표</label>
                <select className="select" name="goal">
                  {Object.entries(goalLabels).map(([value, label]) => (
                    <option value={value} key={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label>시작일</label>
                <input
                  className="input"
                  type="date"
                  name="start_date"
                  defaultValue={new Date().toISOString().slice(0, 10)}
                  required
                />
              </div>
              <div className="field">
                <label>강조 상품</label>
                <select className="select" name="product">
                  {brand.active_profile.products.map((product) => (
                    <option value={product} key={product}>
                      {product}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="form-actions">
              <button className="button primary" disabled={busy}>
                캠페인 생성
              </button>
            </div>
          </form>
        </details>
      )}

      {campaigns.length > 0 && (
        <>
          <div className="toolbar">
            <select
              className="select campaign-select"
              value={selected?.id || ""}
              onChange={(event) => setSelectedId(event.target.value)}
            >
              {campaigns.map((campaign) => (
                <option value={campaign.id} key={campaign.id}>
                  {campaign.name}
                </option>
              ))}
            </select>
            <div className="toolbar-group">
              <button className="button small" onClick={generateStrategy} disabled={busy}>
                {strategy ? "전략 다시 생성" : "전략 생성"}
              </button>
              <button
                className="button small primary"
                onClick={generateContents}
                disabled={busy || !strategy}
              >
                게시물 8개 생성
              </button>
            </div>
          </div>
          {selected && (
            <div className="metrics">
              <Metric label="Period" value={`${selected.start_date} — ${selected.end_date}`} />
              <Metric label="Goal" value={goalLabels[selected.goal] || selected.goal} />
              <Metric label="Status" value={selected.status.replace("_", " ")} />
            </div>
          )}
          {strategy ? (
            <div className="panel">
              <div className="panel-head">
                <div>
                  <p className="eyebrow">Core message</p>
                  <h2>{strategy.core_message}</h2>
                </div>
                <span className="status">VERSION {strategy.version}</span>
              </div>
              <div className="tag-row" style={{ marginBottom: 26 }}>
                {strategy.content_pillars.map((item) => (
                  <span className="tag" key={item}>
                    {item}
                  </span>
                ))}
              </div>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>No.</th>
                      <th>Week</th>
                      <th>Topic</th>
                      <th>Type</th>
                    </tr>
                  </thead>
                  <tbody>
                    {strategy.post_topics.map((topic) => (
                      <tr key={topic.sequence}>
                        <td>{topic.sequence}</td>
                        <td>{topic.week}</td>
                        <td>{topic.topic}</td>
                        <td>{topic.content_type}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="info-box">
              캠페인 전략을 생성하면 핵심 메시지와 게시물 주제 8개가 표시됩니다.
            </div>
          )}
        </>
      )}
    </>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <div className="detail-label">{label}</div>
      <strong>{value}</strong>
    </div>
  );
}

function ContentSection({
  brand,
  onError,
}: {
  brand: Brand;
  onError: (message: string) => void;
}) {
  const { campaigns } = useCampaignData(brand.id, onError);
  const [campaignId, setCampaignId] = useState("");
  const [contents, setContents] = useState<Content[]>([]);
  const [selectedContentId, setSelectedContentId] = useState("");
  const [busy, setBusy] = useState(false);
  const activeCampaignId = campaignId || campaigns[0]?.id || "";
  const selected =
    contents.find((item) => item.id === selectedContentId) || contents[0];

  const loadContents = useCallback(async () => {
    if (!activeCampaignId) {
      setContents([]);
      return;
    }
    try {
      const items = await api<Content[]>(
        `/campaigns/${activeCampaignId}/contents`,
      );
      setContents(items);
      setSelectedContentId((current) =>
        items.some((item) => item.id === current) ? current : items[0]?.id || "",
      );
    } catch (caught) {
      onError(errorMessage(caught));
    }
  }, [activeCampaignId, onError]);

  useEffect(() => {
    loadContents();
  }, [loadContents]);

  async function refreshContent(contentId: string) {
    const refreshed = await api<Content>(`/contents/${contentId}`);
    setContents((current) =>
      current.map((item) => (item.id === contentId ? refreshed : item)),
    );
  }

  async function selectVariant(contentId: string, variantId: string) {
    setBusy(true);
    try {
      const refreshed = await api<Content>(
        `/contents/${contentId}/selected-variant`,
        { method: "POST", body: JSON.stringify({ variant_id: variantId }) },
      );
      setContents((current) =>
        current.map((item) => (item.id === contentId ? refreshed : item)),
      );
    } catch (caught) {
      onError(errorMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  async function generateVariant(contentId: string) {
    setBusy(true);
    try {
      await api(
        `/contents/${contentId}/variants`,
        { method: "POST", body: JSON.stringify({ hashtag_count: 7 }) },
        true,
      );
      await refreshContent(contentId);
    } catch (caught) {
      onError(errorMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  async function generateBrief(contentId: string) {
    setBusy(true);
    try {
      await api(
        `/contents/${contentId}/poster-brief`,
        { method: "POST", body: JSON.stringify({}) },
        true,
      );
      await refreshContent(contentId);
    } catch (caught) {
      onError(errorMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <SectionTitle eyebrow="03 · Content lab" title="콘텐츠" />
      {!campaigns.length ? (
        <div className="info-box">먼저 캠페인과 게시물 8개를 생성해 주세요.</div>
      ) : (
        <>
          <div className="toolbar">
            <select
              className="select campaign-select"
              value={activeCampaignId}
              onChange={(event) => {
                setCampaignId(event.target.value);
                setSelectedContentId("");
              }}
            >
              {campaigns.map((campaign) => (
                <option value={campaign.id} key={campaign.id}>
                  {campaign.name}
                </option>
              ))}
            </select>
            <span className="status">
              {contents.length ? `${contents.length} POSTS` : "NO CONTENT"}
            </span>
          </div>

          {!contents.length ? (
            <div className="info-box">
              이 캠페인에는 아직 게시물이 없습니다. 캠페인 전략 화면에서 생성해
              주세요.
            </div>
          ) : (
            <div className="content-layout">
              <aside className="content-list">
                {contents.map((content) => (
                  <button
                    type="button"
                    className={selected?.id === content.id ? "active" : ""}
                    onClick={() => setSelectedContentId(content.id)}
                    key={content.id}
                  >
                    {String(content.sequence).padStart(2, "0")} · {content.topic}
                  </button>
                ))}
              </aside>

              {selected && (
                <div>
                  <div className="panel">
                    <div className="panel-head">
                      <div>
                        <p className="eyebrow">
                          WEEK {selected.week_number} · {selected.content_type}
                        </p>
                        <h2>{selected.topic}</h2>
                      </div>
                      <span className="status">{selected.status}</span>
                    </div>
                    <p>{selected.core_message}</p>
                  </div>

                  <div className="toolbar" style={{ marginTop: 28 }}>
                    <h2>문구 변형</h2>
                    <div className="toolbar-group">
                      <button
                        className="button small"
                        onClick={() => generateVariant(selected.id)}
                        disabled={
                          busy ||
                          selected.variants.filter((item) => item.origin === "ai")
                            .length >= 3
                        }
                      >
                        변형 추가
                      </button>
                      <button
                        className="button small primary"
                        onClick={() => generateBrief(selected.id)}
                        disabled={busy}
                      >
                        포스터 브리프
                      </button>
                    </div>
                  </div>

                  <div className="variant-grid">
                    {selected.variants.map((variant) => {
                      const isSelected =
                        selected.selected_variant_id === variant.id;
                      return (
                        <article
                          className={`variant-card ${isSelected ? "selected" : ""}`}
                          key={variant.id}
                        >
                          <div className="card-meta">
                            <span>
                              VERSION {variant.variant_number} · {variant.tone}
                            </span>
                            {isSelected && <span>SELECTED</span>}
                          </div>
                          <h3>{variant.opening_line}</h3>
                          <p>{variant.body}</p>
                          <p>
                            <strong>CTA</strong> · {variant.cta}
                          </p>
                          <p className="hashtags">
                            {variant.hashtags.join(" ")}
                          </p>
                          <p className="hashtags">
                            IMAGE · {variant.image_concept}
                          </p>
                          <button
                            className={`button small full ${
                              isSelected ? "primary" : ""
                            }`}
                            onClick={() =>
                              selectVariant(selected.id, variant.id)
                            }
                            disabled={busy || isSelected}
                          >
                            {isSelected ? "선택됨" : "이 버전 선택"}
                          </button>
                        </article>
                      );
                    })}
                  </div>

                  {selected.poster_brief && (
                    <PosterStudio
                      brief={selected.poster_brief}
                      onRefresh={() => refreshContent(selected.id)}
                      onError={onError}
                    />
                  )}
                </div>
              )}
            </div>
          )}
        </>
      )}
    </>
  );
}

function CalendarSection({
  brand,
  onError,
}: {
  brand: Brand;
  onError: (message: string) => void;
}) {
  const { analyses, campaigns } = useCampaignData(brand.id, onError);
  const [campaignId, setCampaignId] = useState("");
  const [items, setItems] = useState<CalendarItem[]>([]);
  const [busy, setBusy] = useState(false);
  const activeCampaignId = campaignId || campaigns[0]?.id || "";
  const approved = analyses.find((item) => item.status === "approved");

  const load = useCallback(async () => {
    if (!activeCampaignId) {
      setItems([]);
      return;
    }
    try {
      setItems(
        await api<CalendarItem[]>(
          `/campaigns/${activeCampaignId}/calendar`,
        ),
      );
    } catch (caught) {
      onError(errorMessage(caught));
    }
  }, [activeCampaignId, onError]);

  useEffect(() => {
    load();
  }, [load]);

  async function createCalendar() {
    if (!activeCampaignId) return;
    setBusy(true);
    try {
      await api(`/campaigns/${activeCampaignId}/calendar`, {
        method: "POST",
        body: JSON.stringify({ preferred_weekdays: [2, 5] }),
      });
      await load();
    } catch (caught) {
      onError(errorMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  async function refreshCalendar() {
    if (!activeCampaignId) return;
    setBusy(true);
    try {
      setItems(
        await api<CalendarItem[]>(
          `/campaigns/${activeCampaignId}/calendar:refresh`,
          { method: "POST" },
        ),
      );
    } catch (caught) {
      onError(errorMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <SectionTitle
        eyebrow="04 · Publishing plan"
        title="콘텐츠 캘린더"
        action={
          activeCampaignId && !items.length ? (
            <button
              className="button primary"
              onClick={createCalendar}
              disabled={busy}
            >
              캘린더 생성
            </button>
          ) : null
        }
      />
      {!campaigns.length ? (
        <div className="info-box">먼저 캠페인을 만들어 주세요.</div>
      ) : (
        <>
          <div className="toolbar">
            <select
              className="select campaign-select"
              value={activeCampaignId}
              onChange={(event) => setCampaignId(event.target.value)}
            >
              {campaigns.map((campaign) => (
                <option value={campaign.id} key={campaign.id}>
                  {campaign.name}
                </option>
              ))}
            </select>
            {items.length > 0 && (
              <div className="toolbar-group">
                <button
                  className="button small subtle"
                  type="button"
                  onClick={refreshCalendar}
                  disabled={busy}
                >
                  {busy ? "최신화 중" : "최신화"}
                </button>
                <a
                  className="button small"
                  href={downloadUrl(
                    `/campaigns/${activeCampaignId}/calendar/export.csv`,
                  )}
                >
                  CSV 다운로드
                </a>
                {approved && (
                  <a
                    className="button small"
                    href={downloadUrl(`/analyses/${approved.id}/export.md`)}
                  >
                    브랜드 보고서
                  </a>
                )}
              </div>
            )}
          </div>
          {!items.length ? (
            <div className="info-box">
              게시물을 생성한 뒤 캘린더를 만들면 4주 일정에 자동 배치됩니다.
            </div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Week</th>
                    <th>Topic</th>
                    <th>Selected Copy</th>
                    <th>Poster</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => {
                    const selectedVariant = selectedVariantFor(item);
                    return (
                      <tr key={item.id}>
                        <td>{item.scheduled_date}</td>
                        <td>{item.content?.week_number || "-"}</td>
                        <td>
                          <strong>{item.content?.topic || "-"}</strong>
                          <p className="table-subtext">
                            {item.content?.content_type || ""}
                          </p>
                        </td>
                        <td>
                          {selectedVariant ? (
                            <>
                              <strong>{selectedVariant.opening_line}</strong>
                              <p className="table-subtext">
                                {selectedVariant.cta}
                              </p>
                            </>
                          ) : (
                            "-"
                          )}
                        </td>
                        <td>
                          {item.approved_image ? (
                            <a
                              className="status dark"
                              href={downloadUrl(
                                `/generated-images/${item.approved_image.id}/file`,
                              )}
                              target="_blank"
                            >
                              POSTER V{item.approved_image.version}
                            </a>
                          ) : (
                            <span className="status">NO POSTER</span>
                          )}
                        </td>
                        <td>
                          <span
                            className={`status ${
                              item.status === item.content?.status ? "dark" : ""
                            }`}
                          >
                            {item.status}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </>
  );
}

function selectedVariantFor(item: CalendarItem) {
  const content = item.content;
  if (!content) return null;
  return (
    content.variants.find(
      (variant) => variant.id === content.selected_variant_id,
    ) ||
    content.variants[0] ||
    null
  );
}

function ProfileSection({
  brand,
  onReload,
  onError,
}: {
  brand: Brand;
  onReload: () => Promise<void>;
  onError: (message: string) => void;
}) {
  const profile = brand.active_profile;
  const [busy, setBusy] = useState(false);

  async function save(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    const data = new FormData(event.currentTarget);
    const split = (name: string) =>
      String(data.get(name) || "")
        .split("\n")
        .map((item) => item.trim())
        .filter(Boolean);

    try {
      await api(`/brands/${brand.id}/profile`, {
        method: "PUT",
        body: JSON.stringify({
          products: split("products"),
          target_customers: data.get("target_customers"),
          strengths: data.get("strengths"),
          desired_moods: profile.desired_moods,
          region: data.get("region") || null,
          price_range: data.get("price_range") || null,
          existing_copy: data.get("existing_copy") || null,
          avoid_expressions: split("avoid_expressions"),
          campaign_facts: profile.campaign_facts,
        }),
      });
      await onReload();
    } catch (caught) {
      onError(errorMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <SectionTitle eyebrow="Brand source" title="가게 프로필" />
      <div className="info-box">
        수정 내용은 새 프로필 버전으로 저장됩니다. 기존 결과물은 이력으로
        보존되고 분석에는 오래됨 상태가 표시됩니다.
      </div>
      <form className="panel" onSubmit={save}>
        <div className="panel-head">
          <h2>Profile v{profile.version}</h2>
          <span className="status">{brand.industry}</span>
        </div>
        <div className="form-grid">
          <div className="field full">
            <label>대표 상품</label>
            <textarea
              className="textarea"
              name="products"
              defaultValue={profile.products.join("\n")}
              required
            />
          </div>
          <div className="field">
            <label>주요 고객</label>
            <textarea
              className="textarea"
              name="target_customers"
              defaultValue={profile.target_customers}
              required
            />
          </div>
          <div className="field">
            <label>가게 강점</label>
            <textarea
              className="textarea"
              name="strengths"
              defaultValue={profile.strengths}
              required
            />
          </div>
          <div className="field">
            <label>지역</label>
            <input
              className="input"
              name="region"
              defaultValue={profile.region || ""}
            />
          </div>
          <div className="field">
            <label>가격대</label>
            <input
              className="input"
              name="price_range"
              defaultValue={profile.price_range || ""}
            />
          </div>
          <div className="field">
            <label>기존 홍보 문구</label>
            <textarea
              className="textarea"
              name="existing_copy"
              defaultValue={profile.existing_copy || ""}
            />
          </div>
          <div className="field">
            <label>피하고 싶은 표현</label>
            <textarea
              className="textarea"
              name="avoid_expressions"
              defaultValue={profile.avoid_expressions.join("\n")}
            />
          </div>
        </div>
        <div className="form-actions">
          <button className="button primary" disabled={busy}>
            {busy ? "저장 중..." : "새 프로필 버전 저장"}
          </button>
        </div>
      </form>
    </>
  );
}
