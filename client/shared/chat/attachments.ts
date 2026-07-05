/** Chat attachment types — Consumer + CEO (upload API Stage 2). */

export const ATTACHMENT_KINDS = [
  "image",
  "pdf",
  "word",
  "excel",
  "archive",
  "code",
  "audio",
  "video",
  "other",
] as const;

export type AttachmentKind = (typeof ATTACHMENT_KINDS)[number];

export type ChatAttachmentMeta = {
  id: string;
  name: string;
  mime: string;
  size: number;
  kind: AttachmentKind;
  /** pending = selected locally; uploaded = on server */
  status: "pending" | "uploaded" | "rejected";
};

const MIME_MAP: Record<string, AttachmentKind> = {
  "image/": "image",
  "application/pdf": "pdf",
  "application/msword": "word",
  "application/vnd.openxmlformats-officedocument.wordprocessingml": "word",
  "application/vnd.ms-excel": "excel",
  "application/vnd.openxmlformats-officedocument.spreadsheetml": "excel",
  "application/zip": "archive",
  "application/x-zip-compressed": "archive",
  "application/x-rar-compressed": "archive",
  "audio/": "audio",
  "video/": "video",
};

export function classifyAttachment(mime: string, name: string): AttachmentKind {
  for (const [prefix, kind] of Object.entries(MIME_MAP)) {
    if (mime.startsWith(prefix) || mime === prefix) return kind;
  }
  const ext = name.split(".").pop()?.toLowerCase() ?? "";
  if (["ts", "tsx", "js", "py", "cs", "md", "json", "yaml"].includes(ext)) {
    return "code";
  }
  return "other";
}

export function validateAttachmentSize(
  size: number,
  maxBytes = 25 * 1024 * 1024,
): string | null {
  if (size > maxBytes) {
    return `File too large (max ${Math.round(maxBytes / 1024 / 1024)} MB)`;
  }
  return null;
}

export function attachmentLabel(kind: AttachmentKind): string {
  const labels: Record<AttachmentKind, string> = {
    image: "Image",
    pdf: "PDF",
    word: "Word",
    excel: "Excel",
    archive: "Archive",
    code: "Code",
    audio: "Audio",
    video: "Video",
    other: "File",
  };
  return labels[kind];
}
