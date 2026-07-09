"use client";

import { motion, useReducedMotion } from "framer-motion";
import type { ReactNode } from "react";
import { springs } from "../../lib/motion";

type Props = {
  role: "user" | "assistant";
  children: ReactNode;
  contentKey: string;
};

export function ChatMessageSpring({ role, children, contentKey }: Props) {
  const reduce = useReducedMotion();
  const fromX = role === "user" ? 10 : -10;

  return (
    <motion.li
      className={`flex ${role === "user" ? "justify-end" : "justify-start"}`}
      initial={reduce ? false : { opacity: 0, y: 14, x: fromX }}
      animate={{ opacity: 1, y: 0, x: 0 }}
      transition={springs.gentle}
    >
      <motion.div
        key={contentKey}
        className="max-w-[min(92%,36rem)]"
        initial={reduce ? false : { opacity: 0, y: 10, filter: "blur(6px)" }}
        animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
        transition={{ ...springs.soft, delay: role === "assistant" ? 0.04 : 0 }}
      >
        {children}
      </motion.div>
    </motion.li>
  );
}
