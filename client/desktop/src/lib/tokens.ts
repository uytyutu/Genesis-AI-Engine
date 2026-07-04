import shared from "../../../shared/design-tokens.json";

export const tokens = {
  ...shared,
  typography: {
    fontSans:
      'ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
  },
} as const;

export type ThemeMode = "dark" | "light" | "system";
