export type LegalSection = { heading: string; body: string };

export type LegalDocument = {
  id: string;
  title: string;
  subtitle: string;
  publishable: boolean;
  missingFields: string[];
  sections: LegalSection[];
  source: "virtus_api" | "env_entity" | "file_entity" | "pending";
};
