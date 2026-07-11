"use client";

import Link from "next/link";
import { VirtusMark } from "./VirtusMark";
import { ASSISTANT_NAME, BRAND_NAME } from "../lib/publicBrand";
import { surfaceNavMeta } from "../lib/surfaceNavConfig";
import type { SurfaceTarget } from "../lib/surfaceRegistry";

type Props = {
  surface: SurfaceTarget;
  homeHref?: string;
};

export function VirtusSurfaceIdentity({ surface, homeHref = "/" }: Props) {
  const meta = surfaceNavMeta(surface);
  const roleLabel =
    surface === "public"
      ? "Витрина"
      : surface === "client"
        ? "Моя компания"
        : "Кабинет владельца";

  return (
    <div className="virtus-surface-identity">
      <Link href={homeHref} className="virtus-surface-identity__brand">
        <VirtusMark className="h-10 w-10 shrink-0 shadow-glow" />
        <div className="min-w-0">
          <p className="virtus-surface-identity__name">{BRAND_NAME}</p>
          <p className="virtus-surface-identity__tag">
            {ASSISTANT_NAME} · {roleLabel}
          </p>
        </div>
      </Link>
      <p className="virtus-surface-identity__vector">
        <span className="virtus-surface-identity__dot" aria-hidden />
        Работаю с <strong>{ASSISTANT_NAME}</strong>
      </p>
      {meta.scenario ? (
        <p className="virtus-surface-identity__scenario">{meta.scenario}</p>
      ) : null}
    </div>
  );
}
