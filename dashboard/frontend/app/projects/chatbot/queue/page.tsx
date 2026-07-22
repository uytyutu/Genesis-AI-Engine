"use client";

import { DailyQueuePanel } from "../../../components/DailyQueuePanel";

export default function DailyQueuePage() {
  return (
    <div className="flex min-h-[calc(100dvh-10rem)] flex-col">
      <DailyQueuePanel />
    </div>
  );
}
