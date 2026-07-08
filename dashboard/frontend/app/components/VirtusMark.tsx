/** Virtus Core mark — Confluence symbol (hidden V in negative space). */
export function VirtusMark({ className = "h-10 w-10" }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 512 512"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden
    >
      <defs>
        <linearGradient id="vc-surface" x1="72" y1="48" x2="440" y2="472" gradientUnits="userSpaceOnUse">
          <stop stopColor="#0C0C14" />
          <stop offset="1" stopColor="#06060A" />
        </linearGradient>
        <radialGradient id="vc-glow" cx="256" cy="310" r="210" gradientUnits="userSpaceOnUse">
          <stop stopColor="#7c8fd4" stopOpacity="0.11" />
          <stop offset="1" stopColor="#7c8fd4" stopOpacity="0" />
        </radialGradient>
      </defs>
      <rect width="512" height="512" fill="url(#vc-surface)" />
      <rect width="512" height="512" fill="url(#vc-glow)" />
      <path
        fill="#E4E4EA"
        d="M 92 96 C 44 188, 54 324, 238 416 C 256 400, 246 336, 238 284 C 224 200, 172 136, 120 100 C 108 94, 98 92, 92 96 Z"
      />
      <path
        fill="#E4E4EA"
        d="M 420 96 C 468 188, 458 324, 274 416 C 256 400, 266 336, 274 284 C 288 200, 340 136, 392 100 C 404 94, 414 92, 420 96 Z"
      />
      <path
        fill="#7C8FD4"
        opacity="0.26"
        d="M 144 124 C 128 184, 142 264, 208 348 C 200 336, 184 276, 180 216 C 176 168, 160 132, 144 124 Z"
      />
      <path
        fill="#7C8FD4"
        opacity="0.26"
        d="M 368 124 C 384 184, 370 264, 304 348 C 312 336, 328 276, 332 216 C 336 168, 352 132, 368 124 Z"
      />
      <circle cx="256" cy="408" r="26" fill="#E4E4EA" />
      <circle cx="256" cy="408" r="14" fill="#7C8FD4" />
      <circle cx="256" cy="408" r="5" fill="#F0F0F4" />
    </svg>
  );
}

/** @deprecated use VirtusMark — kept for import compatibility */
export const GenesisMark = VirtusMark;
