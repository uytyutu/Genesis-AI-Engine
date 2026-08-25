"use client";

import Link from "next/link";
import { VirtusMark } from "../VirtusMark";
import { ASSISTANT_NAME, BRAND_NAME } from "../../lib/publicBrand";
import type { SurfaceTarget } from "../../lib/surfaceRegistry";

type Props = {
  surface: SurfaceTarget;
  homeHref?: string;
};

export function VirtusSurfaceIdentity({ surface, homeHref = "/" }: Props) {
  // Mission Control = fixed RU chrome (не смешивать с Client i18n DE/EN).
  const roleLabel =
    surface === "client"
      ? "Mein Unternehmen"
      : surface === "public"
        ? "Virtus Core"
        : "Mission Control";
  const workingWith =
    surface === "client"
      ? `${ASSISTANT_NAME} hilft Ihnen gerne`
      : surface === "ceo"
        ? "Управление компанией"
        : `${ASSISTANT_NAME}`;

  return (
    <div className="virtus-surface-identity">
      <Link href={homeHref} className="virtus-surface-identity__brand">
        <VirtusMark
          className="h-10 w-10 shrink-0 shadow-glow"
          animate={surface !== "public"}
        />
        <div className="min-w-0">
          <p className="virtus-surface-identity__name">{BRAND_NAME}</p>
          <p className="virtus-surface-identity__tag" suppressHydrationWarning>
            {surface === "public" ? roleLabel : `${ASSISTANT_NAME} · ${roleLabel}`}
          </p>
        </div>
      </Link>
      {surface !== "public" ? (
        <p className="virtus-surface-identity__vector" suppressHydrationWarning>
          <span className="virtus-surface-identity__dot" aria-hidden />
          {workingWith}
        </p>
      ) : null}
    </div>
  );
}
