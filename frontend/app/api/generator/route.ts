async function proxyGenerator(method: "GET" | "POST") {
  const baseUrl = (
    process.env.BACKEND_API_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    "http://127.0.0.1:8000"
  ).replace(/\/$/, "");

  try {
    const response = await fetch(`${baseUrl}/api/v1/generator`, {
      method,
      cache: "no-store",
      signal: AbortSignal.timeout(10000),
    });
    return new Response(await response.text(), {
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
