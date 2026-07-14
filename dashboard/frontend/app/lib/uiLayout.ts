import layoutJson from "../../ui_layout.json";

export type UiLayoutMode = "ceo" | "master";

export type UiLayoutConfig = {
  mode: UiLayoutMode;
  label: string;
  compact_sidebar: boolean;
  sidebar_width_px: number;
  hide_link_hints: boolean;
  home_label: string;
};

export const UI_LAYOUT: UiLayoutConfig = layoutJson as UiLayoutConfig;

export function isMasterWorkshop(): boolean {
  return UI_LAYOUT.mode === "master";
}
