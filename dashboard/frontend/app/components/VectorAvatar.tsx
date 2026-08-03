"use client";

import { useEffect, useRef } from "react";

/** Storefront Vector presence — muted looping MP4 (first commercial version). */
export const VECTOR_AVATAR_SRC = "/brand/vector-avatar.mp4";
export const VECTOR_MARK_SRC = "/brand/vector-mark-192.png";

type Size = "xs" | "sm" | "md" | "lg" | "hero";

const SIZE_CLASS: Record<Size, string> = {
  xs: "h-7 w-7",
  sm: "h-9 w-9",
  md: "h-14 w-14",
  lg: "h-40 w-40",
  hero: "h-[min(52vh,22rem)] w-full max-w-[16rem]",
};

type AvatarProps = {
  size?: Size;
  className?: string;
  /** Decorative presence next to chat — no controls, autoplay loop. */
  decorative?: boolean;
};

export function VectorAvatar({
  size = "md",
  className = "",
  decorative = true,
}: AvatarProps) {
  const ref = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.muted = true;
    el.defaultMuted = true;
    const play = () => {
      void el.play().catch(() => {
        /* autoplay policy — muted should allow; ignore if blocked */
      });
    };
    play();
    el.addEventListener("loadeddata", play);
    return () => el.removeEventListener("loadeddata", play);
  }, []);

  return (
    <div
      className={`vector-avatar relative overflow-hidden rounded-full bg-sky-500/10 ring-1 ring-sky-300/30 ${SIZE_CLASS[size]} ${className}`}
    >
      <video
        ref={ref}
        src={VECTOR_AVATAR_SRC}
        autoPlay
        muted
        loop
        playsInline
        preload="metadata"
        controls={false}
        disablePictureInPicture
        aria-hidden={decorative}
        aria-label={decorative ? undefined : "Vector"}
        className="h-full w-full object-cover object-center"
      />
      <span
        className="pointer-events-none absolute inset-0 rounded-full ring-1 ring-inset ring-white/10"
        aria-hidden
      />
    </div>
  );
}

/** Lightweight chat bubble / FAB mark (static — avoids N video streams). */
export function VectorChatIcon({
  className = "",
  size = "sm",
}: {
  className?: string;
  size?: "xs" | "sm" | "md";
}) {
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={VECTOR_MARK_SRC}
      alt=""
      width={size === "md" ? 40 : size === "sm" ? 36 : 28}
      height={size === "md" ? 40 : size === "sm" ? 36 : 28}
      className={`rounded-full object-cover ring-1 ring-sky-300/35 ${SIZE_CLASS[size]} ${className}`}
      aria-hidden
    />
  );
}

/** Stage beside ChatGPT-style panel — storefront glass frame. */
export function VectorAvatarStage({ className = "" }: { className?: string }) {
  return (
    <aside
      className={`vector-avatar-stage flex shrink-0 flex-col items-center justify-end gap-3 border-l border-white/8 bg-gradient-to-b from-sky-500/10 via-transparent to-violet-500/10 px-4 pb-6 pt-8 ${className}`}
      aria-label="Vector"
    >
      <div className="relative flex w-full flex-1 items-end justify-center">
        <div
          className="pointer-events-none absolute bottom-[18%] h-24 w-24 rounded-full bg-sky-400/25 blur-3xl"
          aria-hidden
        />
        <VectorAvatar size="hero" className="!rounded-[1.75rem] shadow-[0_20px_60px_-20px_rgba(56,189,248,0.55)] ring-sky-300/25" />
      </div>
      <p className="text-center text-[11px] font-medium tracking-wide text-sky-100/70">
        Vector
      </p>
    </aside>
  );
}
