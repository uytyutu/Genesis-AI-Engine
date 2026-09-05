"use client";

import type { ReactNode } from "react";
import { VirtusCommercialShowcase } from "./VirtusCommercialShowcase";

type Props = {
  marketSelect?: ReactNode;
};

/** Commercial /site hero — interactive showcase only (galleries live in Selected Work). */
export function VirtusCoreDirectionsHero({ marketSelect }: Props) {
  return <VirtusCommercialShowcase marketSelect={marketSelect} />;
}
