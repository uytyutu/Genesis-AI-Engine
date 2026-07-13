import Link from "next/link";
import { Card } from "./ui";
import type { OrderLaunchContext } from "../lib/orderProjectLaunch";

type Props = {
  launch: OrderLaunchContext;
};

export function OrderProjectSummary({ launch }: Props) {
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
      {launch.previewHref ? (
        <Link
          href={launch.previewHref}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-4 inline-flex text-sm text-genesis-accent hover:underline"
        >
          Посмотреть согласованную версию →
        </Link>
      ) : null}
    </Card>
  );
}
