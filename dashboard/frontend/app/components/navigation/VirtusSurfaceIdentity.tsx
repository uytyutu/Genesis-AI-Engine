"use client";

import Link from "next/link";
import { useTranslation } from "react-i18next";
import { VirtusMark } from "../VirtusMark";
import { ASSISTANT_NAME, BRAND_NAME } from "../../lib/publicBrand";
import type { SurfaceTarget } from "../../lib/surfaceRegistry";

type Props = {
  surface: SurfaceTarget;
  homeHref?: string;
};

export function VirtusSurfaceIdentity({ surface, homeHref = "/" }: Props) {
  const { t } = useTranslation("common");
  const roleKey =
    surface === "public" ? "surface.public" : surface === "client" ? "surface.client" : "surface.ceo";

  return (
    <div className="virtus-surface-identity">
      <Link href={homeHref} className="virtus-surface-identity__brand">
        <VirtusMark className="h-10 w-10 shrink-0 shadow-glow" />
        <div className="min-w-0">
          <p className="virtus-surface-identity__name">{BRAND_NAME}</p>
          <p className="virtus-surface-identity__tag">
            {ASSISTANT_NAME} · {t(roleKey)}
          </p>
        </div>
      </Link>
      <p className="virtus-surface-identity__vector">
        <span className="virtus-surface-identity__dot" aria-hidden />
        {t("surface.workingWith", { name: ASSISTANT_NAME })}
      </p>
    </div>
  );
}
