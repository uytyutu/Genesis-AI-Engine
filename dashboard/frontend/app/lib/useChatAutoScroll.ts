"use client";

import { useCallback, useEffect, useRef, useState, type RefObject } from "react";

const NEAR_BOTTOM_PX = 96;

function distanceFromBottom(el: HTMLElement): number {
  return el.scrollHeight - el.scrollTop - el.clientHeight;
}

function scrollBehavior(): ScrollBehavior {
  if (typeof window === "undefined") return "auto";
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth";
}

/** Smart chat scroll — follow bottom unless user scrolled up to read history. */
export function useChatAutoScroll(
  containerRef: RefObject<HTMLDivElement | null>,
  followDeps: unknown[],
  enabled = true,
) {
  const pinnedRef = useRef(true);
  const [showJumpButton, setShowJumpButton] = useState(false);

  const isNearBottom = useCallback(() => {
    const el = containerRef.current;
    if (!el) return true;
    return distanceFromBottom(el) <= NEAR_BOTTOM_PX;
  }, [containerRef]);

  const scrollToBottom = useCallback(
    (behavior?: ScrollBehavior) => {
      const el = containerRef.current;
      if (!el) return;
      el.scrollTo({
        top: el.scrollHeight,
        behavior: behavior ?? scrollBehavior(),
      });
    },
    [containerRef],
  );

  const handleScroll = useCallback(() => {
    const near = isNearBottom();
    if (near) {
      pinnedRef.current = true;
      setShowJumpButton(false);
    } else {
      pinnedRef.current = false;
      setShowJumpButton(true);
    }
  }, [isNearBottom]);

  const jumpToLatest = useCallback(() => {
    pinnedRef.current = true;
    setShowJumpButton(false);
    scrollToBottom("smooth");
  }, [scrollToBottom]);

  const pinToBottom = useCallback(() => {
    pinnedRef.current = true;
    setShowJumpButton(false);
    scrollToBottom();
  }, [scrollToBottom]);

  useEffect(() => {
    if (!enabled) return;
    const id = requestAnimationFrame(() => {
      if (pinnedRef.current) {
        scrollToBottom();
        setShowJumpButton(false);
      } else if (!isNearBottom()) {
        setShowJumpButton(true);
      }
    });
    return () => cancelAnimationFrame(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- followDeps are explicit triggers
  }, followDeps);

  return { showJumpButton, handleScroll, jumpToLatest, pinToBottom };
}
