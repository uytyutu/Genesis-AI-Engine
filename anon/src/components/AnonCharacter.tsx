"use client";

import { useId } from "react";

export type VeilMood =
  | "normal"
  | "secret"
  | "curious"
  | "waiting"
  | "surprised"
  | "happy"
  | "plus"
  | "drop";

export type VeilAccent = "secret" | "moment" | "drop" | "later" | "voice" | "plus" | "games";

const ACCENT: Record<
  VeilAccent,
  { glow: string; sealA: string; sealB: string; line: string }
> = {
  secret: { glow: "#b8a0e0", sealA: "#e0b8d4", sealB: "#b8a0e0", line: "#c9b4f0" },
  moment: { glow: "#e0b8d4", sealA: "#e8c4e0", sealB: "#c9a8d8", line: "#f0d4e8" },
  drop: { glow: "#d4a8c8", sealA: "#e8b4c8", sealB: "#c9a0d0", line: "#e8c8d8" },
  later: { glow: "#a8b4e8", sealA: "#b8c0e8", sealB: "#b0a0d8", line: "#c8d0f0" },
  voice: { glow: "#b0b8e8", sealA: "#c4b8e8", sealB: "#b8a0e0", line: "#d0d4f0" },
  plus: { glow: "#d4cce8", sealA: "#e8e0f4", sealB: "#c9b4f0", line: "#f0ecf8" },
  games: { glow: "#c9b4f0", sealA: "#e0b8d4", sealB: "#b8a0e0", line: "#d8c8f0" },
};

/** Veil — ANON brand character: sealed face, curiosity, secrets. */
export function AnonCharacter({
  size = 120,
  className = "",
  pulse = false,
  mood = "normal",
  accent = "secret",
  showGlow = true,
}: {
  size?: number;
  className?: string;
  pulse?: boolean;
  mood?: VeilMood;
  accent?: VeilAccent;
  showGlow?: boolean;
}) {
  const uid = useId().replace(/:/g, "");
  const a = ACCENT[accent];
  const eyeY = mood === "curious" || mood === "waiting" ? 70 : 72;
  const eyeScale = mood === "surprised" ? 1.35 : mood === "happy" ? 0.85 : 1;
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 160 160"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={`${pulse ? "anon-veil-pulse" : ""} ${className}`}
      aria-hidden
      role="img"
    >
      <title>Veil</title>
      <defs>
        <radialGradient id={`vg-${uid}`} cx="50%" cy="40%" r="55%">
          <stop offset="0%" stopColor={a.glow} stopOpacity="0.55" />
          <stop offset="70%" stopColor={a.glow} stopOpacity="0.12" />
          <stop offset="100%" stopColor="#0e0a16" stopOpacity="0" />
        </radialGradient>
        <linearGradient id={`vm-${uid}`} x1="30" y1="40" x2="130" y2="130">
          <stop stopColor="#2a1f45" />
          <stop offset="0.5" stopColor="#3d2a5c" />
          <stop offset="1" stopColor="#18122a" />
        </linearGradient>
        <linearGradient id={`vs-${uid}`} x1="70" y1="78" x2="90" y2="98">
          <stop stopColor={a.sealA} />
          <stop offset="1" stopColor={a.sealB} />
        </linearGradient>
      </defs>

      {showGlow && <circle cx="80" cy="80" r="72" fill={`url(#vg-${uid})`} />}

      <path
        d="M40 118c8-28 18-52 40-52s32 24 40 52c-12 14-26 22-40 22s-28-8-40-22z"
        fill="#14101c"
        opacity="0.92"
      />
      <ellipse cx="80" cy="62" rx="38" ry="42" fill={`url(#vm-${uid})`} />

      {/* Envelope face */}
      <path
        d="M48 58h64v36c0 8-6 14-14 14H62c-8 0-14-6-14-14V58z"
        stroke="rgba(255,255,255,0.35)"
        strokeWidth="2"
        fill="rgba(15,23,42,0.45)"
      />
      <path
        d="M48 58l32 22 32-22"
        stroke={a.line}
        strokeWidth="2.2"
        strokeLinejoin="round"
      />

      {mood === "curious" && (
        <>
          <path d="M58 62 Q66 58 74 62" stroke="rgba(255,255,255,0.45)" strokeWidth="1.6" fill="none" />
          <path d="M86 62 Q94 58 102 62" stroke="rgba(255,255,255,0.45)" strokeWidth="1.6" fill="none" />
        </>
      )}
      {mood === "waiting" && (
        <>
          <path d="M58 64 Q66 66 74 64" stroke="rgba(255,255,255,0.35)" strokeWidth="1.4" fill="none" />
          <path d="M86 64 Q94 66 102 64" stroke="rgba(255,255,255,0.35)" strokeWidth="1.4" fill="none" />
        </>
      )}

      <g transform={`translate(0 ${(eyeY - 72) * 0.2})`}>
        <ellipse
          cx="66"
          cy={eyeY}
          rx={3.5 * eyeScale}
          ry={(mood === "happy" ? 1.6 : 3.5) * eyeScale}
          fill="#e0e7ff"
          className="anon-veil-eye"
        />
        <ellipse
          cx="94"
          cy={eyeY}
          rx={3.5 * eyeScale}
          ry={(mood === "happy" ? 1.6 : 3.5) * eyeScale}
          fill="#e0e7ff"
          className="anon-veil-eye"
        />
      </g>

      {/* Seal / props by mood */}
      {mood === "waiting" ? (
        <g transform="translate(80 92)">
          <circle r="11" fill={`url(#vs-${uid})`} />
          <circle r="7" stroke="white" strokeWidth="1.2" fill="none" opacity="0.85" />
          <path d="M0 -4v4l3 2" stroke="white" strokeWidth="1.4" strokeLinecap="round" />
        </g>
      ) : mood === "drop" ? (
        <g transform="translate(80 90)">
          <rect x="-10" y="-6" width="20" height="16" rx="3" fill={`url(#vs-${uid})`} />
          <path d="M-10 -6l10 7 10-7" stroke="white" strokeWidth="1.3" fill="none" opacity="0.9" />
        </g>
      ) : mood === "plus" ? (
        <g transform="translate(80 92)">
          <circle r="10" fill={`url(#vs-${uid})`} />
          <path d="M-4 0h8M0 -4v8" stroke="#0f172a" strokeWidth="2" strokeLinecap="round" />
        </g>
      ) : (
        <g transform="translate(80 92)">
          <circle r="9" fill={`url(#vs-${uid})`} />
          <path
            d="M-3 0h6M0 -3v6"
            stroke="white"
            strokeWidth="1.4"
            strokeLinecap="round"
            opacity="0.85"
          />
        </g>
      )}

      {mood === "secret" && (
        <text x="118" y="48" fontSize="18" opacity="0.9">
          👀
        </text>
      )}
    </svg>
  );
}

/** Compact mark for 24px nav / favicon-like UI chips */
export function AnonMark({
  size = 28,
  className = "",
  accent = "secret",
}: {
  size?: number;
  className?: string;
  accent?: VeilAccent;
}) {
  const uid = useId().replace(/:/g, "");
  const a = ACCENT[accent];
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      className={className}
      aria-hidden
    >
      <rect width="32" height="32" rx="8" fill="#070a14" />
      <ellipse cx="16" cy="13" rx="8.5" ry="9" fill="#1e1b4b" />
      <path
        d="M9 12h14v7c0 2-1.5 3.5-3.5 3.5h-7C10.5 22.5 9 21 9 19v-7z"
        fill="#0f172a"
        stroke="rgba(255,255,255,0.4)"
        strokeWidth="0.8"
      />
      <path
        d="M9 12l7 4.5L23 12"
        stroke={a.line}
        strokeWidth="1.1"
        strokeLinejoin="round"
      />
      <circle cx="13" cy="15" r="1.1" fill="#e0e7ff" />
      <circle cx="19" cy="15" r="1.1" fill="#e0e7ff" />
      <circle cx="16" cy="19.2" r="2.2" fill={`url(#mk-${uid})`} />
      <defs>
        <linearGradient id={`mk-${uid}`} x1="14" y1="17" x2="18" y2="21">
          <stop stopColor={a.sealA} />
          <stop offset="1" stopColor={a.sealB} />
        </linearGradient>
      </defs>
    </svg>
  );
}
