import { NextResponse } from "next/server";

/**
 * External pipeline webhook: POST /api/process
 * Body: any JSON (typically { category, prompt }).
 * Optional gate: set PROCESS_API_KEY in .env.local to require X-API-Key.
 */
export async function POST(req: Request) {
  const expectedKey = (process.env.PROCESS_API_KEY || "").trim();
  if (expectedKey) {
    const providedKey = (req.headers.get("x-api-key") || "").trim();
    if (providedKey !== expectedKey) {
      return NextResponse.json({ error: "unauthorized" }, { status: 401 });
    }
  }

  try {
    const body = await req.json();
    console.log("Request received:", body);
    return NextResponse.json({ output: "success" }, { status: 200 });
  } catch (error) {
    console.log("Invalid request:", error);
    return NextResponse.json({ error: "Invalid request" }, { status: 400 });
  }
}
