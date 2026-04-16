import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function getBackendBaseUrl() {
  return (
    process.env.HEALTHCARE_AI_API_BASE_URL ||
    process.env.NEXT_PUBLIC_HEALTHCARE_AI_API_BASE_URL ||
    "http://127.0.0.1:8000"
  );
}

export async function POST(request) {
  let payload;
  try {
    payload = await request.json();
  } catch {
    return NextResponse.json({ detail: "Invalid JSON body." }, { status: 400 });
  }

  const backendUrl = new URL("/predict", getBackendBaseUrl());

  let response;
  try {
    response = await fetch(backendUrl, {
      method: "POST",
      headers: {
        "content-type": "application/json"
      },
      body: JSON.stringify(payload),
      cache: "no-store"
    });
  } catch {
    return NextResponse.json(
      {
        detail: `Could not reach the backend at ${backendUrl.origin}. Set HEALTHCARE_AI_API_BASE_URL on Vercel or run the Python API locally.`
      },
      { status: 502 }
    );
  }

  const contentType = response.headers.get("content-type") || "application/json";
  const body = await response.text();

  return new NextResponse(body, {
    status: response.status,
    headers: {
      "content-type": contentType
    }
  });
}