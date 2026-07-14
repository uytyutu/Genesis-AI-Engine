/**
 * PE-1.1 — client-side product path timing (dev console only, never shown to user).
 */

export type PathMark = {
  step: string;
  atMs: number;
  deltaMs: number;
};

let marks: PathMark[] = [];
let startedAt = 0;

export function resetProductPath(): void {
  marks = [];
  startedAt = typeof performance !== "undefined" ? performance.now() : 0;
}

export function markProductPath(step: string): void {
  if (typeof performance === "undefined") return;
  const atMs = performance.now();
  const deltaMs = marks.length ? atMs - marks[marks.length - 1].atMs : atMs - startedAt;
  marks.push({ step, atMs: Math.round(atMs - startedAt), deltaMs: Math.round(deltaMs) });
}

export function flushProductPath(label: string): void {
  if (!marks.length) return;
  console.info(`[Vector path] ${label}`, marks);
  marks = [];
}
