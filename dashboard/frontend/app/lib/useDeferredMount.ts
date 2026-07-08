"use client";

import { useEffect, useState } from "react";

/** Mount children after a short delay — keeps Mission Control first paint responsive. */
export function useDeferredMount(delayMs = 1800): boolean {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const timer = window.setTimeout(() => setReady(true), delayMs);
    return () => window.clearTimeout(timer);
  }, [delayMs]);

  return ready;
}
