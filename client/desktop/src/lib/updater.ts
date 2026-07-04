/**
 * Stage 1 updater scaffold.
 * Wire tauri-plugin-updater in Stage 2 when release endpoint exists.
 */
export type UpdateCheckResult = {
  supported: boolean;
  message: string;
};

export async function checkForUpdates(
  enabled: boolean,
): Promise<UpdateCheckResult> {
  if (!enabled) {
    return { supported: false, message: "Automatic update checks are off." };
  }

  const isTauri = Boolean(
    typeof window !== "undefined" &&
      ("__TAURI_INTERNALS__" in window || "__TAURI__" in window),
  );

  if (!isTauri) {
    return {
      supported: false,
      message: "Updates run in the packaged Genesis Client (Tauri build).",
    };
  }

  return {
    supported: false,
    message: "Updater endpoint not configured yet (Stage 2).",
  };
}
