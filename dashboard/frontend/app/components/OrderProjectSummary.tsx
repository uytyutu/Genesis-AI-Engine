"use client";

import { useMemo } from "react";
import Link from "next/link";
import { Card } from "./ui";
import type { OrderLaunchContext } from "../lib/orderProjectLaunch";
import { resolvePackagePreviewSlides } from "../lib/packagePreviewGallery";

type Props = {
  launch: OrderLaunchContext;
  packageId?: string;
  niche?: string | null;
};

/** Always a polished public demo — never the broken execution preview shell. */
function nicheDemoHref(packageId?: string, niche?: string | null): string {
  const slide = resolvePackagePreviewSlides(packageId || "basic", niche, 1)[0];
  const path = (slide?.siteSrc || "sites/basic/auto/index.html").replace(/^\/+/, "");
  return `/package-previews/${path}`;
}

export function OrderProjectSummary({ launch, packageId, niche }: Props) {
  const demoHref = useMemo(
    () => nicheDemoHref(packageId, niche),
    [packageId, niche],
  );

  const rows: { label: string; value: string }[] = [
    { label: "Компания", value: launch.company },
    { label: "Бизнес", value: launch.businessLine },
  ];
  if (launch.market) rows.push({ label: "Рынок", value: launch.market });
  if (launch.style) rows.push({ label: "Стиль", value: launch.style });
  if (launch.palette) rows.push({ label: "Палитра", value: launch.palette });
  rows.push({ label: "Версия", value: launch.versionLabel });
  if (launch.approvedAt) {
    rows.push({ label: "Согласовано", value: launch.approvedAt });
  }

  return (
    <Card glow className="border-emerald-500/20 bg-emerald-950/10" padding="md">
      <p className="genesis-label text-emerald-200/90">Ваш проект</p>
      <h2 className="mt-2 text-2xl font-bold tracking-tight">
        {launch.projectLabel} {launch.company}
      </h2>
      <p className="mt-2 text-sm text-genesis-muted leading-relaxed">
        Мы уже собрали проект вместе. Сейчас вы оплачиваете{" "}
        <span className="text-white">запуск и публикацию</span> этой версии — не
        обещание «сделаем когда-нибудь».
      </p>
      <dl className="mt-4 grid gap-2 sm:grid-cols-2">
        {rows.map((row) => (
          <div
            key={row.label}
            className="rounded-lg border border-white/5 bg-black/20 px-3 py-2"
          >
            <dt className="text-[10px] uppercase tracking-wide text-genesis-muted">
              {row.label}
            </dt>
            <dd className="mt-0.5 text-sm font-medium text-white">{row.value}</dd>
          </div>
        ))}
      </dl>

      <div className="mt-4 overflow-hidden rounded-xl border border-white/10 bg-white">
        <div className="border-b border-black/5 bg-emerald-950/90 px-3 py-1.5 text-center text-[10px] font-medium text-emerald-100">
          Пример готового сайта этой ниши (полный демо-сайт)
        </div>
        <iframe
          title={`Пример сайта: ${launch.company}`}
          src={demoHref}
          className="h-[min(70vh,560px)] w-full border-0 bg-white"
          sandbox="allow-same-origin allow-scripts allow-popups allow-forms"
        />
      </div>

      <a
        href={demoHref}
        target="_blank"
        rel="noopener noreferrer"
        className="mt-3 inline-flex text-sm text-genesis-accent hover:underline"
      >
        Открыть полный пример сайта →
      </a>

      <p className="mt-3 text-xs text-genesis-muted">
        Нужна обычная форма заказа без привязки к чату?{" "}
        <Link href="/order?form=1" className="text-emerald-300 hover:underline">
          Заполнить бриф →
        </Link>
      </p>
    </Card>
  );
}
