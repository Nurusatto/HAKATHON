async function proxyGenerator(method: "GET" | "POST") {
  const baseUrl = (
    process.env.BACKEND_API_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    "http://127.0.0.1:8000"
  ).replace(/\/$/, "");

  try {
    const path = method === "GET" ? "/api/v1/generator/status" : "/api/v1/generator";
    const response = await fetch(`${baseUrl}${path}`, {
      method,
      cache: "no-store",
      signal: AbortSignal.timeout(10000),
    });
    const body = await response.text();
    if (!response.headers.get("content-type")?.includes("application/json")) {
      return Response.json(
        { detail: `Бэкенд вернул HTTP ${response.status}. Подробности в логах FastAPI.` },
        { status: response.ok ? 502 : response.status },
      );
    }
    return new Response(body, {
      status: response.status,
      headers: { "Content-Type": "application/json" },
    });
  } catch {
    return Response.json(
      { detail: "Не удалось связаться с бэкендом" },
      { status: 502 },
    );
  }
}

export async function GET() {
  return proxyGenerator("GET");
}

export async function POST() {
  return proxyGenerator("POST");
}
