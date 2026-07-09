"use client";

import { motion, useReducedMotion, type HTMLMotionProps } from "framer-motion";
import type { ReactNode } from "react";
import { enterFadeUp, springs } from "../../lib/motion";

type Props = HTMLMotionProps<"div"> & {
  children: ReactNode;
  delay?: number;
};

/** Spring enter — cards, panels, welcome blocks. */
export function SpringIn({ children, delay = 0, className, ...rest }: Props) {
  const reduce = useReducedMotion();
  if (reduce) {
    return (
      <div className={className} {...(rest as object)}>
        {children}
      </div>
    );
  }
  return (
    <motion.div
      className={className}
      initial={enterFadeUp.initial}
      animate={enterFadeUp.animate}
      transition={{ ...springs.gentle, delay }}
      {...rest}
    >
      {children}
    </motion.div>
  );
}
