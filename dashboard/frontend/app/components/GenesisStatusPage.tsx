"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import { VirtusMark } from "./VirtusMark";
import { BRAND_NAME, ASSISTANT_NAME, BRAND_SIGNATURE, PUBLIC_WELCOME } from "../lib/publicBrand";
import { Button, ButtonLink } from "./ui";

type Props = {
  code: string;
  title: string;
  description: string;
  actions?: ReactNode;
  onRetry?: () => void;
};

/** Branded 404/500 — Virtus Core shell */
export function GenesisStatusPage({ code, title, description, actions, onRetry }: Props) {
  return (
    <div className="genesis-app-shell min-h-screen">
      <aside className="genesis-sidebar hidden lg:flex" aria-hidden>
        <div className="genesis-sidebar__brand pointer-events-none">
          <VirtusMark className="h-10 w-10 shrink-0 shadow-glow" />
          <div>
            <p className="genesis-sidebar__name">{BRAND_NAME}</p>
            <p className="genesis-sidebar__tag">
              {ASSISTANT_NAME} · {BRAND_SIGNATURE}
            </p>
          </div>
        </div>
      </aside>
      <div className="genesis-app-main flex min-h-screen items-center justify-center">
        <main className="mx-auto max-w-md px-6 py-16 text-center animate-fade-up">
          <VirtusMark className="mx-auto h-16 w-16 shadow-glow" />
          <p className="mt-6 text-5xl font-bold tabular-nums text-genesis-accent/90">{code}</p>
          <h1 className="mt-3 text-xl font-bold tracking-tight">{title}</h1>
          <p className="mt-3 text-sm leading-relaxed text-genesis-muted">{description}</p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            {actions ?? (
              <>
                {onRetry && (
                  <Button variant="primary" size="md" onClick={onRetry}>
                    Повторить
                  </Button>
                )}
                <ButtonLink href="/" variant="secondary" size="md">
                  На пульт
                </ButtonLink>
              </>
            )}
          </div>
          <p className="mt-10 text-[10px] uppercase tracking-[0.14em] text-genesis-muted/60">
            Brand v1.0 · Orbit Stack
          </p>
        </main>
      </div>
    </div>
  );
}

export function GenesisBackLink({ href = "/" }: { href?: string }) {
  return (
    <Link
      href={href}
      className="text-sm text-genesis-muted transition-colors hover:text-genesis-accent"
    >
      ← {BRAND_NAME}
    </Link>
  );
}
