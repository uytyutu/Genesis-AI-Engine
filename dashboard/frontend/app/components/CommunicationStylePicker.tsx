"use client";

import {
  COMMUNICATION_STYLE_OPTIONS,
  saveCommunicationStyle,
  type CommunicationStyle,
} from "../lib/communicationStyle";

type Props = {
  value: CommunicationStyle;
  onChange: (style: CommunicationStyle) => void;
};

export function CommunicationStylePicker({ value, onChange }: Props) {
  return (
    <div
      className="mb-2 flex flex-wrap items-center gap-1.5"
      role="group"
      aria-label="Communication style"
    >
      {COMMUNICATION_STYLE_OPTIONS.map((opt) => {
        const active = value === opt.id;
        return (
          <button
            key={opt.id}
            type="button"
            title={opt.label}
            onClick={() => {
              saveCommunicationStyle(opt.id);
              onChange(opt.id);
            }}
            className={`rounded-full border px-2.5 py-1 text-xs transition ${
              active
                ? "border-genesis-accent/50 bg-genesis-accent/15 text-white"
                : "border-white/10 bg-genesis-panel/60 text-genesis-muted hover:border-genesis-accent/30 hover:text-white"
            }`}
          >
            <span aria-hidden>{opt.emoji}</span>{" "}
            <span className="hidden sm:inline">{opt.label}</span>
          </button>
        );
      })}
    </div>
  );
}
