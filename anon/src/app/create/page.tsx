import { Suspense } from "react";
import CreateClientInner from "./CreateClientInner";

export default function CreatePage() {
  return (
    <Suspense
      fallback={
        <main className="anim-pulse p-8 text-center text-violet-200">
          ✨ Packing your moment…
        </main>
      }
    >
      <CreateClientInner />
    </Suspense>
  );
}
