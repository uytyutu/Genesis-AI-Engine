export function GenesisMark({ className = "h-10 w-10" }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 40 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden
    >
      <rect width="40" height="40" rx="10" fill="url(#g-mark)" />
      <path
        d="M12 28V12h4.2l5.8 9.4V12H26v16h-4.2l-5.8-9.6V28H12z"
        fill="white"
        fillOpacity="0.95"
      />
      <defs>
        <linearGradient id="g-mark" x1="4" y1="4" x2="36" y2="36" gradientUnits="userSpaceOnUse">
          <stop stopColor="#5b8def" />
          <stop offset="1" stopColor="#4f46e5" />
        </linearGradient>
      </defs>
    </svg>
  );
}
