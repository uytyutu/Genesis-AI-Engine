"use client";

import { motion, useReducedMotion } from "framer-motion";

/** Virtus Core mark — softened Confluence symbol (hidden V in negative space). */
export function VirtusMark({ className = "h-10 w-10" }: { className?: string }) {
  const reduce = useReducedMotion();

  return (
    <motion.div
      className={`relative shrink-0 ${className}`}
      animate={
        reduce
          ? undefined
          : {
              scale: [1, 1.025, 1],
            }
      }
      transition={
        reduce
          ? undefined
          : {
              duration: 4.5,
              repeat: Infinity,
              ease: "easeInOut",
            }
      }
    >
      <motion.span
        className="pointer-events-none absolute inset-0 rounded-[22%]"
        aria-hidden
        animate={
          reduce
            ? undefined
            : {
                opacity: [0.35, 0.65, 0.35],
                boxShadow: [
                  "0 0 20px -4px rgba(124, 143, 212, 0.2)",
                  "0 0 32px -2px rgba(124, 143, 212, 0.45)",
                  "0 0 20px -4px rgba(124, 143, 212, 0.2)",
                ],
              }
        }
        transition={
          reduce
            ? undefined
            : {
                duration: 4.5,
                repeat: Infinity,
                ease: "easeInOut",
              }
        }
      />
      <svg
        className="relative h-full w-full overflow-hidden rounded-[22%] shadow-glow"
        viewBox="0 0 512 512"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden
      >
        <defs>
          <linearGradient id="vc-surface" x1="72" y1="48" x2="440" y2="472" gradientUnits="userSpaceOnUse">
            <stop stopColor="#0C0C14" />
            <stop offset="1" stopColor="#06060A" />
          </linearGradient>
          <radialGradient id="vc-glow" cx="256" cy="300" r="220" gradientUnits="userSpaceOnUse">
            <stop stopColor="#7c8fd4" stopOpacity="0.14" />
            <stop offset="1" stopColor="#7c8fd4" stopOpacity="0" />
          </radialGradient>
          <motion.linearGradient
            id="vc-breathe"
            x1="72"
            y1="48"
            x2="440"
            y2="472"
            gradientUnits="userSpaceOnUse"
            animate={
              reduce
                ? undefined
                : {
                    x1: [72, 88, 72],
                    y1: [48, 56, 48],
                  }
            }
            transition={
              reduce
                ? undefined
                : {
                    duration: 6,
                    repeat: Infinity,
                    ease: "easeInOut",
                  }
            }
          >
            <stop stopColor="#101018" />
            <stop offset="1" stopColor="#06060A" />
          </motion.linearGradient>
        </defs>
        <rect width="512" height="512" rx="118" fill="url(#vc-surface)" />
        <rect width="512" height="512" rx="118" fill="url(#vc-glow)" />
        <rect width="512" height="512" rx="118" fill="url(#vc-breathe)" opacity="0.35" />
        <path
          fill="#E8E8EE"
          d="M 104 104 C 68 192, 76 308, 234 396 C 252 384, 244 332, 238 292 C 228 224, 188 168, 146 132 C 132 122, 116 108, 104 104 Z"
        />
        <path
          fill="#E8E8EE"
          d="M 408 104 C 444 192, 436 308, 278 396 C 260 384, 268 332, 274 292 C 284 224, 324 168, 366 132 C 380 122, 396 108, 408 104 Z"
        />
        <path
          fill="#7C8FD4"
          opacity="0.22"
          d="M 152 132 C 136 192, 148 268, 212 348 C 204 336, 190 280, 186 224 C 182 176, 166 142, 152 132 Z"
        />
        <path
          fill="#7C8FD4"
          opacity="0.22"
          d="M 360 132 C 376 192, 364 268, 300 348 C 308 336, 322 280, 326 224 C 330 176, 346 142, 360 132 Z"
        />
        <circle cx="256" cy="396" r="28" fill="#E8E8EE" />
        <circle cx="256" cy="396" r="16" fill="#7C8FD4" />
        <circle cx="256" cy="396" r="6" fill="#F4F4F8" />
      </svg>
    </motion.div>
  );
}

/** @deprecated use VirtusMark — kept for import compatibility */
export const GenesisMark = VirtusMark;
