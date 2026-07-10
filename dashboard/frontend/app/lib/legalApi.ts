import { publicApiBase } from "./publicApiBase";

const API = publicApiBase();

export type LegalSection = { heading: string; body: string };

export type LegalDocument = {
  id: string;
  title: string;
  locale: string;
  subtitle: string;
  publishable: boolean;
  missing_fields: string[];
  sections: LegalSection[];
  disclaimer?: string;
};

export type TrustChecklistItem = {
  id: string;
  icon: string;
  emoji: string;
  title: string;
  body: string;
};

export type DataStorageGuideItem = {
  id: string;
  question: string;
  answer: string;
};

export type TrustCatalog = {
  version: string;
  brand: string;
  trust_checklist: TrustChecklistItem[];
  data_storage_guide: DataStorageGuideItem[];
  principles: string[];
  data_collected: { id: string; label: string; purpose: string }[];
  retention: {
    project_days: number;
    logs_days: number;
    order_days: number;
    deletion_request_days: number;
  };
  storage_location: string;
  access: {
    owner_team: string;
    processors: Record<string, string[]>;
    never_sold: boolean;
  };
  security_center_horizon: {
    status: string;
    planned_modules: string[];
    internal_security: string[];
  };
  interview_completed: boolean;
  publishable_impressum: boolean;
  publishable_datenschutz: boolean;
  localization?: {
    status: string;
    default_market: string;
    markets: unknown[];
  };
};

const fetchOpts = { next: { revalidate: 60 } as const };

export async function fetchLegalDocument(
  docId: string,
  locale = "de"
): Promise<LegalDocument | null> {
  try {
    const res = await fetch(
      `${API}/api/public/legal/documents/${docId}?locale=${encodeURIComponent(locale)}`,
      fetchOpts
    );
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function fetchTrustCatalog(): Promise<TrustCatalog | null> {
  try {
    const res = await fetch(`${API}/api/public/trust`, fetchOpts);
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}
