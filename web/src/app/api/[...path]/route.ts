const BACKEND_URL = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";
const PROXY_TIMEOUT_MS = 200_000;

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 210;

type RouteContext = {
  params: Promise<{ path: string[] }>;
};

const HOP_BY_HOP_HEADERS = new Set([
  "connection",
  "content-length",
  "host",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade",
]);

async function proxy(request: Request, context: RouteContext) {
  const { path } = await context.params;
  const incomingUrl = new URL(request.url);
  const backendUrl = new URL(
    `/api/${path.map(encodeURIComponent).join("/")}${incomingUrl.search}`,
    BACKEND_URL,
  );
  const headers = new Headers();

  request.headers.forEach((value, key) => {
    if (!HOP_BY_HOP_HEADERS.has(key.toLowerCase())) {
      headers.set(key, value);
    }
  });

  const hasBody = !["GET", "HEAD"].includes(request.method);
  const body = hasBody ? await request.arrayBuffer() : undefined;

  try {
    const response = await fetch(backendUrl, {
      method: request.method,
      headers,
      body,
      cache: "no-store",
      signal: AbortSignal.timeout(PROXY_TIMEOUT_MS),
    });
    const responseHeaders = new Headers();

    response.headers.forEach((value, key) => {
      if (
        !HOP_BY_HOP_HEADERS.has(key.toLowerCase()) &&
        key.toLowerCase() !== "content-encoding"
      ) {
        responseHeaders.set(key, value);
      }
    });

    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    });
  } catch (error) {
    const timedOut =
      error instanceof DOMException && error.name === "TimeoutError";
    return Response.json(
      {
        error: {
          code: timedOut ? "BACKEND_TIMEOUT" : "BACKEND_CONNECTION_RESET",
          message: timedOut
            ? "AI 생성 시간이 길어 요청 제한 시간을 초과했습니다. 잠시 후 다시 시도해 주세요."
            : "백엔드 연결이 생성 도중 끊어졌습니다. 백엔드 서버 상태를 확인하고 다시 시도해 주세요.",
          field_errors: [],
          request_id: crypto.randomUUID(),
          retryable: true,
        },
      },
      { status: timedOut ? 504 : 502 },
    );
  }
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
export const HEAD = proxy;
