import { clientAuthHeaders } from "./clientAuth";
import { publicApiBase } from "./publicApiBase";

const API = publicApiBase();

export type OfficeLanguage = {
  code: string;
  label_de: string;
  label_en: string;
  native: string;
};

export type OfficeChoice = {
  id: string;
  label_de: string;
  needs_target_language?: boolean;
  default_output?: string;
  price_eur?: number;
};

export type OfficeProposal = {
  filled?: boolean;
  title_de?: string;
  filename?: string;
  detected?: {
    document_type?: string;
    document_type_label_de?: string;
    language?: string;
    language_label_de?: string;
    pages?: number | null;
    tables?: number | null;
    images?: number | null;
    text_detected?: boolean;
    ocr_status?: string;
  };
  explanation?: {
    kind?: string;
    about_id?: string;
    type_label_de?: string;
    type_confidence?: number;
    language_code?: string | null;
    language_confidence?: number | null;
    pages?: number | null;
    content_kind?: string;
    text_chars?: number;
    findings?: Array<{
      id: string;
      value?: string;
      count?: number;
      code?: string;
    }>;
    sections?: Array<{ id: string }>;
    key_facts?: Array<{
      id: string;
      value?: string;
      confidence?: string;
    }>;
    about_signals?: string[];
    uncertain?: Array<{ id: string }>;
    suggested_ui_actions?: string[];
    honesty?: string;
  };
  task?: string | null;
  task_label_de?: string | null;
  result_format?: string | null;
  target_language?: string | null;
  price_eur?: number;
  includes?: string[];
  low_confidence?: boolean;
  show_choice_cards?: boolean;
  choice_options?: OfficeChoice[];
  confidence?: number;
  next_step?: string;
  payment_enabled?: boolean;
  continue_label_de?: string;
  continue_hint_de?: string;
  missing_fields?: Array<{ id?: string; label_de: string }>;
  profile_ready?: boolean;
  disclaimer_de?: string;
  preview?: {
    kind?: string;
    product?: string;
    style?: string;
    language?: string;
    estimated_pages?: number | null;
    structure?: string[];
    excerpt?: string;
    full_document_after_payment?: boolean;
    download_allowed?: boolean;
    change_preview?: Array<{ before?: string; after?: string; note?: string }>;
  };
  document_settings?: {
    filled?: boolean;
    confirmed?: boolean;
    catalog?: Array<Record<string, unknown>>;
    values?: Record<string, unknown>;
    ops?: Array<Record<string, unknown>>;
    preview?: Array<{ before?: string; after?: string; note?: string }>;
    available_sections?: string[];
    special_wishes?: string | null;
    executable_now_count?: number;
    instruction_count?: number;
  };
};

export type OfficePayment = {
  paid?: boolean;
  status?: string;
  requires_payment?: boolean;
  price_locked?: boolean;
  price_locked_at?: string | null;
  order_id?: string | null;
  checkout_url?: string | null;
  price_eur?: number | null;
  stripe_live?: boolean;
  pipeline_live?: boolean;
  execute_unlocked?: boolean;
};

export type OfficeProgressStep = {
  id: string;
  label_de: string;
  state: "done" | "active" | "pending" | "failed";
};

export type OfficeDownloadFormat = {
  format: string;
  label: string;
  available: boolean;
  url?: string | null;
};

export type OfficeJobView = {
  ok?: boolean;
  job_id: string;
  owner_token?: string;
  status: string;
  service_preset?: string | null;
  filename?: string | null;
  file_kind?: string | null;
  understanding?: Record<string, unknown> | null;
  proposal?: OfficeProposal | null;
  quality?: {
    passed?: boolean;
    failed?: string[];
    check_count?: number;
    provider?: string | null;
  } | null;
  quality_report?: {
    status?: "READY" | "NOT_READY" | string;
    problem_count?: number;
    problems?: Array<{
      code?: string;
      severity?: string;
      title?: string;
      detail?: string;
      fix_hint?: string;
    }>;
    meta?: Record<string, unknown>;
  } | null;
  artifact?: {
    filename?: string;
    ext?: string;
    mime?: string;
    size?: number;
    held_for_qa_fail?: boolean;
  } | null;
  languages?: OfficeLanguage[];
  stage2_complete?: boolean;
  stage3_complete?: boolean;
  pipeline_live?: boolean;
  failure_reason?: string | null;
  failure_detail?: string | null;
  artifact_download?: string | null;
  download_formats?: OfficeDownloadFormat[];
  progress?: OfficeProgressStep[];
  has_artifact?: boolean;
  bewerbung_profile?: Record<string, unknown> | null;
  photo_material_id?: string | null;
  payment?: OfficePayment;
  delivery?: {
    delivery_id?: string;
    email_status?: string;
    cabinet_ready?: boolean;
    receipt_path?: string | null;
    order_page_path?: string;
    product_label?: string;
  };
  checkout?: {
    ok?: boolean;
    order_id?: string;
    checkout_url?: string | null;
    already_paid?: boolean;
    price_eur?: number;
  };
};

export type OfficeCabinet = {
  ok?: boolean;
  jobs: Array<{
    job_id: string;
    status: string;
    filename?: string | null;
    task?: string | null;
    task_label_de?: string | null;
    price_eur?: number | null;
    paid?: boolean;
    order_id?: string | null;
    artifact_ext?: string | null;
    artifact_filename?: string | null;
    download_ready?: boolean;
    failure_reason?: string | null;
    failure_detail?: string | null;
    created_at?: string;
    progress?: OfficeProgressStep[];
  }>;
  files: Array<Record<string, unknown>>;
  invoices: Array<{
    order_id?: string;
    status?: string;
    price_eur?: number;
    price_label?: string;
    package_name?: string;
    receipt_path?: string;
    office_job_id?: string;
  }>;
  downloads: Array<Record<string, unknown>>;
};

async function parseJson(res: Response): Promise<OfficeJobView> {
  const data = (await res.json().catch(() => ({}))) as OfficeJobView & {
    detail?: { message?: string; code?: string } | string;
  };
  if (!res.ok) {
    const detail = data.detail;
    const msg =
      typeof detail === "string"
        ? detail
        : detail?.message || `Office API ${res.status}`;
    throw new Error(msg);
  }
  return data;
}

export async function createOfficeJob(opts?: {
  service_preset?: string;
  email?: string;
}): Promise<OfficeJobView> {
  const res = await fetch(`${API}/api/office/jobs`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...clientAuthHeaders(),
    },
    body: JSON.stringify({
      service_preset: opts?.service_preset || null,
      email: opts?.email || null,
    }),
  });
  return parseJson(res);
}

export async function getOfficeJob(
  jobId: string,
  ownerToken?: string | null,
): Promise<OfficeJobView> {
  const headers: Record<string, string> = {
    ...(clientAuthHeaders() as Record<string, string>),
  };
  if (ownerToken) headers["X-Office-Owner-Token"] = ownerToken;
  const res = await fetch(`${API}/api/office/jobs/${encodeURIComponent(jobId)}`, {
    headers,
  });
  return parseJson(res);
}

export async function uploadOfficeFile(
  jobId: string,
  ownerToken: string,
  file: File,
): Promise<OfficeJobView> {
  const body = new FormData();
  body.append("file", file);
  const res = await fetch(`${API}/api/office/jobs/${encodeURIComponent(jobId)}/upload`, {
    method: "POST",
    headers: { "X-Office-Owner-Token": ownerToken },
    body,
  });
  return parseJson(res);
}

export async function uploadOfficePages(
  jobId: string,
  ownerToken: string,
  files: File[],
): Promise<OfficeJobView> {
  const body = new FormData();
  for (const file of files) {
    body.append("files", file);
  }
  const res = await fetch(
    `${API}/api/office/jobs/${encodeURIComponent(jobId)}/upload-pages`,
    {
      method: "POST",
      headers: { "X-Office-Owner-Token": ownerToken },
      body,
    },
  );
  return parseJson(res);
}

export async function selectOfficeAction(
  jobId: string,
  ownerToken: string,
  payload: {
    action_id: string;
    target_language?: string;
    source_language?: string;
    output_format?: string;
    document_settings?: Record<string, unknown>;
    special_wishes?: string;
    confirm_settings?: boolean;
  },
): Promise<OfficeJobView> {
  const res = await fetch(
    `${API}/api/office/jobs/${encodeURIComponent(jobId)}/select-action`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Office-Owner-Token": ownerToken,
      },
      body: JSON.stringify(payload),
    },
  );
  return parseJson(res);
}

export async function configureOfficeDocument(
  jobId: string,
  ownerToken: string,
  payload: {
    values?: Record<string, unknown>;
    special_wishes?: string;
    confirm?: boolean;
    action_id?: string;
    target_language?: string;
    source_language?: string;
    output_format?: string;
  },
): Promise<OfficeJobView> {
  const res = await fetch(
    `${API}/api/office/jobs/${encodeURIComponent(jobId)}/document-settings`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Office-Owner-Token": ownerToken,
      },
      body: JSON.stringify(payload),
    },
  );
  return parseJson(res);
}

export async function submitBewerbungProfile(
  jobId: string,
  ownerToken: string,
  payload: {
    profile: Record<string, unknown>;
    action_id?: string;
    output_format?: string;
  },
): Promise<OfficeJobView> {
  const res = await fetch(
    `${API}/api/office/jobs/${encodeURIComponent(jobId)}/bewerbung-profile`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Office-Owner-Token": ownerToken,
      },
      body: JSON.stringify(payload),
    },
  );
  return parseJson(res);
}

export async function attachBewerbungPhoto(
  jobId: string,
  ownerToken: string,
  file: File,
): Promise<OfficeJobView> {
  const body = new FormData();
  body.append("file", file);
  const res = await fetch(
    `${API}/api/office/jobs/${encodeURIComponent(jobId)}/bewerbung-photo`,
    {
      method: "POST",
      headers: { "X-Office-Owner-Token": ownerToken },
      body,
    },
  );
  return parseJson(res);
}

export async function continueOfficeJob(
  jobId: string,
  ownerToken?: string | null,
): Promise<OfficeJobView> {
  const headers: Record<string, string> = {
    ...(clientAuthHeaders() as Record<string, string>),
  };
  if (ownerToken) headers["X-Office-Owner-Token"] = ownerToken;
  const res = await fetch(
    `${API}/api/office/jobs/${encodeURIComponent(jobId)}/execute`,
    { method: "POST", headers },
  );
  return parseJson(res);
}

export async function checkoutOfficeJob(
  jobId: string,
  ownerToken: string,
  payload: {
    success_url: string;
    cancel_url: string;
    email?: string;
    price_eur?: number;
  },
): Promise<OfficeJobView> {
  const res = await fetch(
    `${API}/api/office/jobs/${encodeURIComponent(jobId)}/checkout`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Office-Owner-Token": ownerToken,
        ...clientAuthHeaders(),
      },
      body: JSON.stringify(payload),
    },
  );
  return parseJson(res);
}

export async function fetchOfficeCabinet(): Promise<OfficeCabinet> {
  const res = await fetch(`${API}/api/office/cabinet`, {
    headers: { ...clientAuthHeaders() },
  });
  const data = (await res.json().catch(() => ({}))) as OfficeCabinet & {
    detail?: string | { message?: string };
  };
  if (!res.ok) {
    const detail = data.detail;
    const msg =
      typeof detail === "string"
        ? detail
        : detail?.message || `Office cabinet ${res.status}`;
    throw new Error(msg);
  }
  return data;
}

export function officeArtifactUrl(jobId: string, format?: string): string {
  const q = format ? `?format=${encodeURIComponent(format)}` : "";
  return `${API}/api/office/jobs/${encodeURIComponent(jobId)}/artifact${q}`;
}

export async function downloadOfficeArtifact(
  jobId: string,
  ownerToken: string | null | undefined,
  format?: string,
  deliveryToken?: string | null,
): Promise<void> {
  const headers: Record<string, string> = {
    ...(clientAuthHeaders() as Record<string, string>),
  };
  if (ownerToken) headers["X-Office-Owner-Token"] = ownerToken;
  if (deliveryToken) headers["X-Office-Delivery-Token"] = deliveryToken;
  const res = await fetch(officeArtifactUrl(jobId, format), { headers });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const detail = (data as { detail?: { message?: string } }).detail;
    throw new Error(detail?.message || `Download failed (${res.status})`);
  }
  const blob = await res.blob();
  const cd = res.headers.get("Content-Disposition") || "";
  const match = /filename=\"([^\"]+)\"/i.exec(cd);
  const filename = match?.[1] || `virtus-office-${jobId}.${format || "bin"}`;
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
