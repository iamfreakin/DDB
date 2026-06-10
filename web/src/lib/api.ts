const API_PREFIX = "/api/v1";

export class ApiError extends Error {
  constructor(
    message: string,
    public code = "UNKNOWN_ERROR",
    public status = 500,
  ) {
    super(message);
  }
}

function aiHeaders(): HeadersInit {
  if (typeof window === "undefined") return {};
  const apiKey = sessionStorage.getItem("openai_api_key");
  if (!apiKey) return {};
  return {
    "X-OpenAI-API-Key": apiKey,
    "X-OpenAI-Model":
      sessionStorage.getItem("openai_model") || "gpt-5-mini",
    "X-OpenAI-Image-Model":
      sessionStorage.getItem("openai_image_model") || "gpt-image-2",
  };
}

export async function api<T>(
  path: string,
  options: RequestInit = {},
  useAi = false,
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_PREFIX}${path}`, {
      ...options,
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
        ...(useAi ? aiHeaders() : {}),
        ...options.headers,
      },
    });
  } catch {
    throw new ApiError(
      "서버 연결이 생성 도중 끊어졌습니다. 백엔드 상태를 확인하고 다시 시도해 주세요.",
      "NETWORK_CONNECTION_RESET",
      0,
    );
  }

  if (!response.ok) {
    let body: {
      error?: { message?: string; code?: string };
    } = {};
    try {
      body = await response.json();
    } catch {
      // Keep the generic response below.
    }
    throw new ApiError(
      body.error?.message || "요청을 처리하지 못했습니다.",
      body.error?.code,
      response.status,
    );
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export function downloadUrl(path: string) {
  return `${API_PREFIX}${path}`;
}
