"use client";
/* eslint-disable react-hooks/set-state-in-effect -- form mirrors the selected server record. */

import Image from "next/image";
import { useCallback, useEffect, useState } from "react";
import { api, downloadUrl } from "@/lib/api";
import type { GeneratedImage, PosterBrief } from "@/lib/types";

type BriefForm = {
  headline: string;
  supporting_text: string;
  visual_mood: string;
  colors: string;
  layout_description: string;
  image_prompt: string;
  negative_prompt: string;
  aspect_ratio: string;
};

export function PosterStudio({
  brief,
  onRefresh,
  onError,
}: {
  brief: PosterBrief;
  onRefresh: () => Promise<void>;
  onError: (message: string) => void;
}) {
  const [form, setForm] = useState<BriefForm>(() => toForm(brief));
  const [images, setImages] = useState<GeneratedImage[]>([]);
  const [activeImageId, setActiveImageId] = useState("");
  const [busy, setBusy] = useState<"save" | "generate" | "approve" | "">("");
  const [notice, setNotice] = useState("");

  const loadImages = useCallback(async () => {
    try {
      const items = await api<GeneratedImage[]>(
        `/poster-briefs/${brief.id}/images`,
      );
      setImages(items);
      setActiveImageId((current) =>
        items.some((item) => item.id === current)
          ? current
          : items[0]?.id || "",
      );
    } catch (error) {
      onError(message(error));
    }
  }, [brief.id, onError]);

  useEffect(() => {
    setForm(toForm(brief));
    setNotice("");
  }, [brief]);

  useEffect(() => {
    loadImages();
  }, [loadImages]);

  const activeImage =
    images.find((item) => item.id === activeImageId) || images[0];

  function change<K extends keyof BriefForm>(key: K, value: BriefForm[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function payload() {
    return {
      ...form,
      supporting_text: form.supporting_text || null,
      negative_prompt: form.negative_prompt || null,
      colors: form.colors
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean),
    };
  }

  async function saveBrief() {
    setBusy("save");
    setNotice("");
    try {
      await api(`/contents/${brief.content_id}/poster-brief`, {
        method: "PATCH",
        body: JSON.stringify(payload()),
      });
      await onRefresh();
      setNotice("브리프를 저장했습니다.");
    } catch (error) {
      onError(message(error));
    } finally {
      setBusy("");
    }
  }

  async function generateImage() {
    const confirmed = window.confirm(
      "이미지 API를 사용하면 계정에 비용이 발생할 수 있습니다. 현재 브리프로 이미지를 생성할까요?",
    );
    if (!confirmed) return;
    setBusy("generate");
    setNotice("");
    try {
      await api(`/contents/${brief.content_id}/poster-brief`, {
        method: "PATCH",
        body: JSON.stringify(payload()),
      });
      await onRefresh();
      const generated = await api<GeneratedImage>(
        `/poster-briefs/${brief.id}/images`,
        {
          method: "POST",
          body: JSON.stringify({ confirm_cost: true }),
        },
        true,
      );
      await loadImages();
      setActiveImageId(generated.id);
      setNotice(
        generated.provider === "mock"
          ? "Mock 포스터를 생성했습니다. API 키를 적용하면 실제 AI 이미지로 전환됩니다."
          : "AI 포스터를 생성했습니다.",
      );
    } catch (error) {
      onError(message(error));
    } finally {
      setBusy("");
    }
  }

  async function approveImage(imageId: string) {
    setBusy("approve");
    setNotice("");
    try {
      await api(`/generated-images/${imageId}/approve`, { method: "POST" });
      await loadImages();
      setNotice("이 포스터를 최종 승인했습니다.");
    } catch (error) {
      onError(message(error));
    } finally {
      setBusy("");
    }
  }

  return (
    <section className="poster-studio">
      <div className="poster-studio-head">
        <div>
          <p className="eyebrow">Poster studio</p>
          <h2>광고 포스터</h2>
          <p>
            AI는 배경을 만들고, 정확한 한글 제목과 보조 문구는 앱이 합성합니다.
          </p>
        </div>
        <div className="toolbar-group">
          <button
            className="button small subtle"
            type="button"
            onClick={saveBrief}
            disabled={Boolean(busy)}
          >
            {busy === "save" ? "저장 중" : "브리프 저장"}
          </button>
          <button
            className="button small primary"
            type="button"
            onClick={generateImage}
            disabled={Boolean(busy)}
          >
            {busy === "generate"
              ? "이미지 생성 중"
              : images.length
                ? "다시 생성"
                : "이미지 생성"}
          </button>
        </div>
      </div>

      {notice && <div className="success-box">{notice}</div>}

      <div className="poster-workbench">
        <div className="poster-form">
          <label className="field">
            <span>제목</span>
            <input
              className="input"
              value={form.headline}
              onChange={(event) => change("headline", event.target.value)}
            />
          </label>
          <label className="field">
            <span>보조 문구</span>
            <input
              className="input"
              value={form.supporting_text}
              onChange={(event) =>
                change("supporting_text", event.target.value)
              }
            />
          </label>
          <div className="poster-form-row">
            <label className="field">
              <span>비율</span>
              <select
                className="select"
                value={form.aspect_ratio}
                onChange={(event) => change("aspect_ratio", event.target.value)}
              >
                <option value="1:1">1:1 정사각형</option>
                <option value="4:5">4:5 피드</option>
                <option value="9:16">9:16 스토리</option>
              </select>
            </label>
            <label className="field">
              <span>색상</span>
              <input
                className="input"
                value={form.colors}
                onChange={(event) => change("colors", event.target.value)}
                placeholder="#111111, cream"
              />
            </label>
          </div>
          <label className="field">
            <span>분위기</span>
            <input
              className="input"
              value={form.visual_mood}
              onChange={(event) => change("visual_mood", event.target.value)}
            />
          </label>
          <label className="field">
            <span>이미지 프롬프트</span>
            <textarea
              className="textarea"
              value={form.image_prompt}
              onChange={(event) => change("image_prompt", event.target.value)}
            />
          </label>
          <label className="field">
            <span>레이아웃 지시</span>
            <textarea
              className="textarea compact"
              value={form.layout_description}
              onChange={(event) =>
                change("layout_description", event.target.value)
              }
            />
          </label>
          <label className="field">
            <span>제외 요소</span>
            <textarea
              className="textarea compact"
              value={form.negative_prompt}
              onChange={(event) =>
                change("negative_prompt", event.target.value)
              }
            />
          </label>
        </div>

        <div className="poster-preview">
          {activeImage ? (
            <>
              <div className="poster-image-wrap">
                <Image
                  src={downloadUrl(`/generated-images/${activeImage.id}/file`)}
                  alt={`${form.headline} 포스터`}
                  width={activeImage.width}
                  height={activeImage.height}
                  sizes="(max-width: 900px) 100vw, 45vw"
                  unoptimized
                />
              </div>
              <div className="poster-result-meta">
                <div>
                  <strong>VERSION {activeImage.version}</strong>
                  <span>
                    {activeImage.provider} · {activeImage.model}
                  </span>
                </div>
                <span
                  className={`status ${
                    activeImage.status === "approved" ? "dark" : ""
                  }`}
                >
                  {activeImage.status}
                </span>
              </div>
              <div className="toolbar-group poster-actions">
                <a
                  className="button small subtle"
                  href={downloadUrl(
                    `/generated-images/${activeImage.id}/file?download=true`,
                  )}
                >
                  PNG 다운로드
                </a>
                <button
                  className="button small primary"
                  type="button"
                  onClick={() => approveImage(activeImage.id)}
                  disabled={
                    Boolean(busy) || activeImage.status === "approved"
                  }
                >
                  {activeImage.status === "approved" ? "승인됨" : "최종 승인"}
                </button>
              </div>
            </>
          ) : (
            <div className="poster-empty">
              <span>NO IMAGE YET</span>
              <strong>브리프를 다듬고 첫 포스터를 생성해 보세요.</strong>
              <p>API 키가 없으면 비용 없이 Mock 이미지로 흐름을 확인합니다.</p>
            </div>
          )}
        </div>
      </div>

      {images.length > 1 && (
        <div className="poster-history">
          <p className="detail-label">Generation history</p>
          <div className="poster-history-row">
            {images.map((image) => (
              <button
                type="button"
                className={image.id === activeImage?.id ? "active" : ""}
                onClick={() => setActiveImageId(image.id)}
                key={image.id}
              >
                <Image
                  src={downloadUrl(`/generated-images/${image.id}/file`)}
                  alt={`포스터 버전 ${image.version}`}
                  width={108}
                  height={135}
                  unoptimized
                />
                <span>
                  V{image.version} · {image.status}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}

function toForm(brief: PosterBrief): BriefForm {
  return {
    headline: brief.headline,
    supporting_text: brief.supporting_text || "",
    visual_mood: brief.visual_mood,
    colors: brief.colors.join(", "),
    layout_description: brief.layout_description,
    image_prompt: brief.image_prompt,
    negative_prompt: brief.negative_prompt || "",
    aspect_ratio: brief.aspect_ratio,
  };
}

function message(error: unknown) {
  return error instanceof Error ? error.message : "요청을 처리하지 못했습니다.";
}
