/** Shared spring presets — R3 UI Polish (framer-motion). */
export const springs = {
  gentle: { type: "spring" as const, stiffness: 320, damping: 28, mass: 0.85 },
  snappy: { type: "spring" as const, stiffness: 420, damping: 30, mass: 0.65 },
  soft: { type: "spring" as const, stiffness: 260, damping: 24, mass: 0.9 },
  pop: { type: "spring" as const, stiffness: 480, damping: 22, mass: 0.55 },
} as const;

export const enterFadeUp = {
  initial: { opacity: 0, y: 16, filter: "blur(4px)" },
  animate: { opacity: 1, y: 0, filter: "blur(0px)" },
};

export const enterFadeSlide = {
  initial: { opacity: 0, y: 12, x: -6 },
  animate: { opacity: 1, y: 0, x: 0 },
};
