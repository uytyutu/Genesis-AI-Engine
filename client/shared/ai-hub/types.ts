/**
 * Genesis AI Hub — provider & routing types (architecture scaffold).
 * No live API keys. No brand names in UI — capabilities only.
 */

export type AiCapability =
  | "chat"
  | "code"
  | "vision"
  | "document"
  | "image"
  | "audio"
  | "embed"
  | "tool";

export type AiProviderKind = "llm" | "tool" | "local";

export type AiProviderStatus = "available" | "degraded" | "offline" | "disabled";

/** Registered backend — OpenAI today, anything tomorrow. */
export type AiProviderDefinition = {
  id: string;
  kind: AiProviderKind;
  capabilities: AiCapability[];
  /** Internal label for logs — never shown to end users as marketing. */
  label: string;
  status: AiProviderStatus;
  /** Minimum tier to use this provider (limits TBD at launch). */
  minTier: "free" | "pro" | "business" | "ceo";
};

export type AiHubInput =
  | { type: "text"; text: string }
  | { type: "voice"; transcript: string; audioRef?: string };

export type AiHubTaskPhase =
  | "intake"
  | "analyze"
  | "plan_ready"
  | "awaiting_approve"
  | "dispatch"
  | "executing"
  | "verify"
  | "report"
  | "failed"
  | "cancelled";

export type AiHubPlanStep = {
  id: string;
  title: string;
  capability: AiCapability;
  providerId?: string;
  toolId?: string;
  requiresApprove: boolean;
};

export type AiHubTask = {
  id: string;
  projectId?: string;
  input: AiHubInput;
  locale: string;
  phase: AiHubTaskPhase;
  plan: AiHubPlanStep[];
  createdAt: string;
  approvedAt?: string;
};

/** Tier limits — values filled after cost analysis, not now. */
export type TierLimits = {
  tier: "free" | "pro" | "business";
  messagesPerDay?: number;
  maxUploadBytes?: number;
  maxContextTokens?: number;
  imageGenerationsPerDay?: number;
};

export type AppSurface = "consumer" | "ceo";

export type AiHubRouteRequest = {
  surface: AppSurface;
  tier: TierLimits["tier"] | "ceo";
  input: AiHubInput;
  locale: string;
  projectId?: string;
};

export type AiHubRouteResult = {
  taskId: string;
  plan: AiHubPlanStep[];
  phase: AiHubTaskPhase;
};
