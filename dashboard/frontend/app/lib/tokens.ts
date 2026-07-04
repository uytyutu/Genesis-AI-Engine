/**
 * Genesis Brand System — design tokens (RC2).
 * Source of truth for UI Kit; mirrored in tailwind.config.
 */
export const tokens = {
  colors: {
    bg: "#050508",
    surface: "#0c0c12",
    panel: "#111118",
    elevated: "#18181f",
    border: "#27272f",
    borderSubtle: "#1c1c24",
    accent: "#5b8def",
    accentSoft: "#3d6fd4",
    purple: "#a78bfa",
    green: "#34d399",
    amber: "#fbbf24",
    rose: "#fb7185",
    muted: "#8b8b9a",
    text: "#ececf1",
  },
  radius: {
    sm: "0.5rem",
    md: "0.75rem",
    lg: "1rem",
    xl: "1.25rem",
    full: "9999px",
  },
  motion: {
    fast: "150ms",
    normal: "250ms",
    slow: "400ms",
    easing: "cubic-bezier(0.16, 1, 0.3, 1)",
  },
  typography: {
    fontSans:
      'ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    label: "0.75rem / 500 / 0.05em uppercase",
  },
} as const;

export type ButtonVariant = "primary" | "secondary" | "ghost" | "success" | "danger";
export type ButtonSize = "sm" | "md" | "lg";
