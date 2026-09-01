/**
 * Gas / fee window hints for ETH (extension provider or public RPC).
 */
import { ethers } from "ethers";

export type GasWindowHint = "low" | "normal" | "elevated" | "high";

export interface GasAdvice {
  maxFeeGwei: number;
  priorityGwei: number;
  legacyGasGwei: number | null;
  window: GasWindowHint;
  suggestion: string;
  sampledAt: string;
}

function classify(gwei: number): GasWindowHint {
  if (gwei < 8) return "low";
  if (gwei < 25) return "normal";
  if (gwei < 60) return "elevated";
  return "high";
}

function tip(window: GasWindowHint): string {
  switch (window) {
    case "low":
      return "Низкий газ — удобное окно для свода своего ETH.";
    case "normal":
      return "Средний газ — сводите при операционной необходимости.";
    case "elevated":
      return "Газ повышен — отложите несурочные переводы.";
    case "high":
      return "Высокий газ — ждите спокойного окна, если не срочно.";
  }
}

export async function fetchGasAdvice(provider: ethers.Provider): Promise<GasAdvice> {
  const feeData = await provider.getFeeData();
  const maxFee = feeData.maxFeePerGas ?? feeData.gasPrice ?? ethers.parseUnits("20", "gwei");
  const tipFee = feeData.maxPriorityFeePerGas ?? ethers.parseUnits("1", "gwei");
  const maxFeeGwei = Number(ethers.formatUnits(maxFee, "gwei"));
  const priorityGwei = Number(ethers.formatUnits(tipFee, "gwei"));
  const legacyGasGwei = feeData.gasPrice ? Number(ethers.formatUnits(feeData.gasPrice, "gwei")) : null;
  const window = classify(maxFeeGwei);
  return {
    maxFeeGwei: Math.round(maxFeeGwei * 100) / 100,
    priorityGwei: Math.round(priorityGwei * 100) / 100,
    legacyGasGwei: legacyGasGwei != null ? Math.round(legacyGasGwei * 100) / 100 : null,
    window,
    suggestion: tip(window),
    sampledAt: new Date().toISOString(),
  };
}
