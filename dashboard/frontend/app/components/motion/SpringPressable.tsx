"use client";

import { motion, useReducedMotion, type HTMLMotionProps } from "framer-motion";
import type { ReactNode } from "react";
import { springs } from "../../lib/motion";

type Props = HTMLMotionProps<"button"> & {
  children: ReactNode;
};

/** Spring hover / tap — icon buttons and compact controls. */
export function SpringPressable({ children, className, disabled, ...rest }: Props) {
  const reduce = useReducedMotion();
  return (
    <motion.button
      type="button"
      disabled={disabled}
      className={className}
      whileHover={
        reduce || disabled
          ? undefined
          : {
              scale: 1.06,
              boxShadow: "0 0 28px -6px rgba(91, 141, 239, 0.45)",
            }
      }
      whileTap={reduce || disabled ? undefined : { scale: 0.94 }}
      transition={springs.snappy}
      {...rest}
    >
      {children}
    </motion.button>
  );
}
