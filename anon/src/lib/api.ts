import { NextResponse } from "next/server";

export function json(data: unknown, status = 200) {
  return NextResponse.json(data, { status });
}

export function err(message: string, status = 400, code?: string) {
  return NextResponse.json({ error: message, code }, { status });
}
