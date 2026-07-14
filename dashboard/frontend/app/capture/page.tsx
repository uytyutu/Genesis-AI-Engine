import { Suspense } from "react";
import { CapturePage } from "./CapturePage";

export default function Page() {
  return (
    <Suspense fallback={<p className="p-6 text-sm text-genesis-muted">Открываем приём заявок…</p>}>
      <CapturePage />
    </Suspense>
  );
}
