"use client";

import { FarmDashboard } from "./components/FarmDashboard";
import { MissionControlRecoverBoundary } from "./components/MissionControlRecoverBoundary";

/** Virtus Core — цифровая ферма микро-комбайнов. */
export default function HomePage() {
  return (
    <MissionControlRecoverBoundary>
      <FarmDashboard />
    </MissionControlRecoverBoundary>
  );
}
