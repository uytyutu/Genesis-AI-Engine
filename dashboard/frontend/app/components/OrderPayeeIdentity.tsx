"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card } from "./ui";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type OperatorPreview = {
  trade_name: string;
  full_name: string;
  legal_form: string;
  email: string;
  phone: string;
  website: string;
  address_lines: string[];
  vat_id: string;
  impressum_publishable: boolean;
  datenschutz_publishable: boolean;
};

export function OrderPayeeIdentity() {
  const [operator, setOperator] = useState<OperatorPreview | null>(null);

  useEffect(() => {
    fetch(`${API}/api/public/legal/operator`)
      .then((r) => (r.ok ? r.json() : null))
      .then((body) => setOperator(body))
      .catch(() => setOperator(null));
  }, []);

  if (!operator) return null;

  const sellerName = operator.full_name || operator.trade_name;

  return (
    <Card
      hover={false}
      padding="md"
      className="border-white/10 bg-black/20 text-left"
    >
      <p className="genesis-label text-genesis-muted">Получатель платежа</p>
      <p className="mt-2 text-sm font-semibold text-white">{sellerName}</p>
      {operator.full_name && operator.trade_name !== operator.full_name ? (
        <p className="text-xs text-genesis-muted">{operator.trade_name}</p>
      ) : null}
      {operator.legal_form ? (
        <p className="mt-1 text-xs text-genesis-muted">{operator.legal_form}</p>
      ) : null}
      {operator.address_lines.length > 0 ? (
        <p className="mt-2 whitespace-pre-line text-xs leading-relaxed text-genesis-muted">
          {operator.address_lines.join("\n")}
        </p>
      ) : null}
      <p className="mt-2 text-xs text-genesis-muted">
        E-Mail:{" "}
        <a href={`mailto:${operator.email}`} className="text-genesis-accent hover:underline">
          {operator.email}
        </a>
      </p>
      {operator.phone ? (
        <p className="mt-1 text-xs text-genesis-muted">Telefon: {operator.phone}</p>
      ) : null}
      {operator.vat_id ? (
        <p className="mt-1 text-xs text-genesis-muted">USt-IdNr.: {operator.vat_id}</p>
      ) : null}
      {operator.impressum_publishable ? (
        <p className="mt-3 text-[10px] text-genesis-muted/90">
          <Link href="/impressum" className="text-genesis-accent hover:underline">
            Impressum
          </Link>
          {" · "}
          <Link href="/datenschutz" className="text-genesis-accent hover:underline">
            Datenschutz
          </Link>
          {" · "}
          <Link href="/agb" className="text-genesis-accent hover:underline">
            AGB
          </Link>
        </p>
      ) : (
        <p className="mt-3 text-[10px] text-amber-100/80" role="status">
          Полный Impressum с адресом будет опубликован после завершения регистрации. Вопросы —{" "}
          <a href={`mailto:${operator.email}`} className="text-genesis-accent hover:underline">
            {operator.email}
          </a>
          .
        </p>
      )}
    </Card>
  );
}
