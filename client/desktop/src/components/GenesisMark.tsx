/** Genesis Brand v1.0 FROZEN — Orbit Stack */
export function GenesisMark({ className = "sidebar__logo-svg" }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 512 512"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden
    >
      <defs>
        <linearGradient id="genesis-bg-d" x1="96" y1="48" x2="416" y2="464" gradientUnits="userSpaceOnUse">
          <stop stopColor="#5b8def" />
          <stop offset="1" stopColor="#4f46e5" />
        </linearGradient>
        <linearGradient id="genesis-shine-d" x1="128" y1="72" x2="360" y2="288" gradientUnits="userSpaceOnUse">
          <stop stopColor="#ffffff" stopOpacity="0.32" />
          <stop offset="1" stopColor="#ffffff" stopOpacity="0" />
        </linearGradient>
      </defs>
      <rect width="512" height="512" rx="112" fill="url(#genesis-bg-d)" />
      <ellipse cx="204" cy="148" rx="172" ry="124" fill="url(#genesis-shine-d)" />
      <rect x="108" y="296" width="296" height="60" rx="18" fill="#fff" fillOpacity="0.45" />
      <rect x="132" y="224" width="248" height="60" rx="18" fill="#fff" fillOpacity="0.72" />
      <rect x="156" y="152" width="200" height="60" rx="18" fill="#fff" />
      <circle cx="148" cy="372" r="42" fill="#fff" />
      <path
        d="M 380 188 A 92 92 0 1 0 380 332"
        fill="none"
        stroke="#fff"
        strokeWidth="32"
        strokeLinecap="round"
        strokeOpacity="0.4"
      />
    </svg>
  );
}
