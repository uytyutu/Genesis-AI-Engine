"use client";

import { useCallback, useEffect, useState } from "react";
import {
  DEFAULT_VOICE_SETTINGS,
  loadVoiceSettings,
  saveVoiceSettings,
  type VoiceSettings,
} from "../lib/voiceSettings";
import { listBrowserVoices } from "../lib/ttsRuntime";

type Props = {
  open: boolean;
  onClose: () => void;
  settings: VoiceSettings;
  onChange: (next: VoiceSettings) => void;
  cloudAvailable?: boolean;
  preferredProvider?: string;
};

export function VoiceSettingsPanel({
  open,
  onClose,
  settings,
  onChange,
  cloudAvailable,
  preferredProvider,
}: Props) {
  const [browserVoices, setBrowserVoices] = useState<
    { name: string; lang: string; voiceURI: string }[]
  >([]);

  useEffect(() => {
    if (!open) return;
    void listBrowserVoices().then(setBrowserVoices);
  }, [open]);

  const patch = useCallback(
    (partial: Partial<VoiceSettings>) => {
      const next = { ...settings, ...partial };
      saveVoiceSettings(next);
      onChange(next);
    },
    [settings, onChange],
  );

  if (!open) return null;

  return (
    <div
      className="mb-2 rounded-2xl border border-white/10 bg-genesis-panel/95 p-4 shadow-lg backdrop-blur-xl"
      role="dialog"
      aria-label="Настройки голоса"
    >
      <div className="mb-3 flex items-center justify-between">
        <p className="text-sm font-semibold text-white">Voice Settings</p>
        <button
          type="button"
          onClick={onClose}
          className="rounded-lg px-2 py-1 text-xs text-genesis-muted hover:bg-white/5 hover:text-white"
        >
          Закрыть
        </button>
      </div>

      {cloudAvailable ? (
        <p className="mb-3 text-xs text-genesis-accent">
          Cloud TTS: {preferredProvider ?? "active"} — основной голос Genesis
        </p>
      ) : (
        <p className="mb-3 text-xs text-genesis-muted">
          Cloud TTS недоступен — используется лучший локальный голос браузера.
        </p>
      )}

      <label className="mb-3 block text-xs text-genesis-muted">
        Voice
        <select
          value={settings.voice}
          onChange={(e) => patch({ voice: e.target.value })}
          className="mt-1 w-full rounded-xl border border-white/10 bg-genesis-bg/80 px-3 py-2 text-sm text-white"
        >
          <option value="auto">Genesis Auto (cloud → browser)</option>
          <option value="cloud">Cloud only</option>
          {browserVoices.map((v) => (
            <option key={v.voiceURI} value={v.voiceURI}>
              {v.name} ({v.lang})
            </option>
          ))}
        </select>
      </label>

      <label className="mb-3 block text-xs text-genesis-muted">
        Speed — {settings.speed.toFixed(2)}×
        <input
          type="range"
          min={0.85}
          max={1.25}
          step={0.05}
          value={settings.speed}
          onChange={(e) => patch({ speed: parseFloat(e.target.value) })}
          className="mt-2 w-full accent-genesis-accent"
        />
      </label>

      <label className="mb-3 block text-xs text-genesis-muted">
        Pitch — {settings.pitch.toFixed(2)}
        <input
          type="range"
          min={0.8}
          max={1.2}
          step={0.05}
          value={settings.pitch}
          onChange={(e) => patch({ pitch: parseFloat(e.target.value) })}
          className="mt-2 w-full accent-genesis-accent"
        />
      </label>

      <label className="mb-3 block text-xs text-genesis-muted">
        Volume — {Math.round(settings.volume * 100)}%
        <input
          type="range"
          min={0.2}
          max={1}
          step={0.05}
          value={settings.volume}
          onChange={(e) => patch({ volume: parseFloat(e.target.value) })}
          className="mt-2 w-full accent-genesis-accent"
        />
      </label>

      <div className="space-y-2 border-t border-white/5 pt-3">
        {(
          [
            ["autoListen", "Auto Listen", "После ответа снова слушать микрофон"],
            ["pushToTalk", "Push To Talk", "Не включать непрерывный режим — только по нажатию"],
            [
              "interruptSpeaking",
              "Interrupt Speaking",
              "Прервать речь Genesis при новом нажатии на микрофон",
            ],
          ] as const
        ).map(([key, label, hint]) => (
          <label
            key={key}
            className="flex cursor-pointer items-start gap-3 rounded-xl px-2 py-1.5 hover:bg-white/5"
          >
            <input
              type="checkbox"
              checked={settings[key]}
              onChange={(e) => patch({ [key]: e.target.checked } as Partial<VoiceSettings>)}
              className="mt-0.5 accent-genesis-accent"
            />
            <span>
              <span className="block text-sm text-white">{label}</span>
              <span className="block text-[11px] text-genesis-muted">{hint}</span>
            </span>
          </label>
        ))}
      </div>

      <button
        type="button"
        onClick={() => {
          saveVoiceSettings(DEFAULT_VOICE_SETTINGS);
          onChange({ ...DEFAULT_VOICE_SETTINGS });
        }}
        className="mt-3 text-xs text-genesis-muted underline hover:text-white"
      >
        Сбросить по умолчанию
      </button>
    </div>
  );
}

export { loadVoiceSettings, saveVoiceSettings, DEFAULT_VOICE_SETTINGS };
