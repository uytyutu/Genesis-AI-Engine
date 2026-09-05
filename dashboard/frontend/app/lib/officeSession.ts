/** Persist Office job owner tokens so Stripe return / refresh keeps access. */

const KEY = "virtus_office_job_tokens";

export type OfficeJobTokenRow = {
  job_id: string;
  owner_token: string;
  updated_at: string;
  filename?: string | null;
  status?: string;
};

function readAll(): Record<string, OfficeJobTokenRow> {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw) as Record<string, OfficeJobTokenRow>;
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
}

function writeAll(map: Record<string, OfficeJobTokenRow>): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(map));
  } catch {
    /* ignore */
  }
}

export function saveOfficeJobToken(
  jobId: string,
  ownerToken: string,
  meta?: { filename?: string | null; status?: string },
): void {
  const map = readAll();
  map[jobId] = {
    job_id: jobId,
    owner_token: ownerToken,
    updated_at: new Date().toISOString(),
    filename: meta?.filename,
    status: meta?.status,
  };
  writeAll(map);
}

export function getOfficeJobToken(jobId: string): string | null {
  const row = readAll()[jobId];
  return row?.owner_token || null;
}

export function listOfficeJobTokens(): OfficeJobTokenRow[] {
  return Object.values(readAll()).sort((a, b) =>
    (b.updated_at || "").localeCompare(a.updated_at || ""),
  );
}

export function updateOfficeJobTokenMeta(
  jobId: string,
  meta: { filename?: string | null; status?: string },
): void {
  const map = readAll();
  const row = map[jobId];
  if (!row) return;
  map[jobId] = {
    ...row,
    ...meta,
    updated_at: new Date().toISOString(),
  };
  writeAll(map);
}
