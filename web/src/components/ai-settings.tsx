"use client";
/* eslint-disable react-hooks/set-state-in-effect -- sessionStorage is an external browser store. */

import { useEffect, useState } from "react";

export function AiSettings() {
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState("gpt-5-mini");
  const [imageModel, setImageModel] = useState("gpt-image-2");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setApiKey(sessionStorage.getItem("openai_api_key") || "");
    setModel(sessionStorage.getItem("openai_model") || "gpt-5-mini");
    setImageModel(
      sessionStorage.getItem("openai_image_model") || "gpt-image-2",
    );
  }, []);

  function save() {
    if (apiKey.trim()) {
      sessionStorage.setItem("openai_api_key", apiKey.trim());
    } else {
      sessionStorage.removeItem("openai_api_key");
    }
    sessionStorage.setItem("openai_model", model.trim() || "gpt-5-mini");
    sessionStorage.setItem(
      "openai_image_model",
      imageModel.trim() || "gpt-image-2",
    );
    setSaved(true);
    window.setTimeout(() => setSaved(false), 1800);
  }

  return (
    <details className="settings">
      <summary>AI 설정 · {apiKey ? "OpenAI" : "Mock"}</summary>
      <div className="settings-body">
        <input
          className="input"
          type="password"
          value={apiKey}
          onChange={(event) => setApiKey(event.target.value)}
          placeholder="OpenAI API 키"
          autoComplete="off"
        />
        <input
          className="input"
          value={model}
          onChange={(event) => setModel(event.target.value)}
          placeholder="모델"
        />
        <input
          className="input"
          value={imageModel}
          onChange={(event) => setImageModel(event.target.value)}
          placeholder="이미지 모델"
        />
        <button type="button" className="button small full" onClick={save}>
          {saved ? "저장됨" : "세션에 적용"}
        </button>
        <small>키는 현재 브라우저 탭에만 보관되며 서버에 저장되지 않습니다.</small>
      </div>
    </details>
  );
}
