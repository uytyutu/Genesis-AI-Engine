"use client";

import { useCallback, useEffect, useRef, useState, type RefObject } from "react";

const NEAR_BOTTOM_PX = 120;

function distanceFromBottom(el: HTMLElement): number {
  return el.scrollHeight - el.scrollTop - el.clientHeight;
}

function scrollBehavior(instant = false): ScrollBehavior {
  if (instant) return "auto";
  if (typeof window === "undefined") return "auto";
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth";
}

/** Smart chat scroll — follow bottom unless user scrolled up to read history. */
export function useChatAutoScroll(
  containerRef: RefObject<HTMLDivElement | null>,
  followDeps: unknown[],
  enabled = true,
  options?: { forceFollow?: boolean },
) {
  const pinnedRef = useRef(true);
  const scrollRafRef = useRef<number | null>(null);
  const [showJumpButton, setShowJumpButton] = useState(false);
  const forceFollow = Boolean(options?.forceFollow);

  const isNearBottom = useCallback(() => {
    const el = containerRef.current;
    if (!el) return true;
    return distanceFromBottom(el) <= NEAR_BOTTOM_PX;
  }, [containerRef]);

  const scrollToBottom = useCallback(
    (behavior?: ScrollBehavior) => {
      const el = containerRef.current;
      if (!el) return;
      const instant = forceFollow || behavior === "auto";
      el.scrollTo({
        top: el.scrollHeight,
        behavior: behavior ?? scrollBehavior(instant),
      });
    },
    [containerRef, forceFollow],
  );

  const handleScroll = useCallback(() => {
    if (scrollRafRef.current !== null) return;
    scrollRafRef.current = requestAnimationFrame(() => {
      scrollRafRef.current = null;
      const near = isNearBottom();
      if (near) {
        pinnedRef.current = true;
        setShowJumpButton(false);
      } else {
        pinnedRef.current = false;
        setShowJumpButton(true);
      }
    });
  }, [isNearBottom]);

  const jumpToLatest = useCallback(() => {
    pinnedRef.current = true;
    setShowJumpButton(false);
    scrollToBottom("auto");
  }, [scrollToBottom]);

  const pinToBottom = useCallback(() => {
    pinnedRef.current = true;
    setShowJumpButton(false);
    scrollToBottom("auto");
  }, [scrollToBottom]);

  useEffect(() => {
    if (!enabled) return;
    const id = requestAnimationFrame(() => {
      if (pinnedRef.current || forceFollow) {
        scrollToBottom("auto");
        setShowJumpButton(false);
      } else if (!isNearBottom()) {
        setShowJumpButton(true);
      }
    });
    return () => cancelAnimationFrame(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- followDeps are explicit triggers
  }, [...followDeps, forceFollow]);

  return { showJumpButton, handleScroll, jumpToLatest, pinToBottom };
}
