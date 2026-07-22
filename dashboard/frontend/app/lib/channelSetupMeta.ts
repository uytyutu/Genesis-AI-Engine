/**
 * UI metadata for Channel Connections — mirrors portal ALLOWED lists.
 * Presentation only; no domain model.
 */

export const CHANNEL_TYPES = [
  "website",
  "telegram",
  "instagram",
  "facebook",
  "whatsapp",
  "email",
  "other",
] as const;

export type ChannelTypeId = (typeof CHANNEL_TYPES)[number];

export const CHANNEL_STATUSES = [
  "not_configured",
  "configured",
  "enabled",
  "disabled",
] as const;

export type ChannelStatusId = (typeof CHANNEL_STATUSES)[number];

export const CHANNEL_STATUS_LABEL: Record<ChannelStatusId, string> = {
  not_configured: "Not configured",
  configured: "Configured",
  enabled: "Enabled",
  disabled: "Disabled",
};

export const CHANNEL_CONFIG_FIELDS: Record<
  ChannelTypeId,
  Array<{ key: string; label: string; placeholder: string }>
> = {
  website: [
    { key: "widget_name", label: "Widget name", placeholder: "Vector on site" },
    { key: "theme", label: "Theme", placeholder: "light" },
    { key: "language", label: "Language", placeholder: "ru" },
  ],
  telegram: [
    { key: "bot_username", label: "Bot username", placeholder: "@my_business_bot" },
    {
      key: "webhook_placeholder",
      label: "Webhook placeholder",
      placeholder: "https://… (stub)",
    },
  ],
  instagram: [
    {
      key: "business_account_placeholder",
      label: "Business account",
      placeholder: "@studio",
    },
  ],
  facebook: [
    { key: "page_placeholder", label: "Page", placeholder: "My Business Page" },
  ],
  whatsapp: [
    {
      key: "business_number_placeholder",
      label: "Business number",
      placeholder: "+49…",
    },
  ],
  email: [
    {
      key: "inbox_address_placeholder",
      label: "Inbox address",
      placeholder: "hello@company.com",
    },
  ],
  other: [
    { key: "label", label: "Label", placeholder: "Custom channel" },
    { key: "notes", label: "Notes", placeholder: "Internal note" },
  ],
};

export const CHANNEL_META: Record<
  ChannelTypeId,
  { label: string; hint: string }
> = {
  website: {
    label: "Website",
    hint: "Chat widget on your site — stub config only",
  },
  telegram: {
    label: "Telegram",
    hint: "Bot registry entry — no Telegram API calls",
  },
  instagram: {
    label: "Instagram",
    hint: "Business account placeholder — no Meta SDK",
  },
  facebook: {
    label: "Facebook",
    hint: "Page placeholder — no Meta SDK",
  },
  whatsapp: {
    label: "WhatsApp",
    hint: "Number placeholder — no WhatsApp Cloud API",
  },
  email: {
    label: "Email",
    hint: "Inbox address placeholder — no SMTP",
  },
  other: {
    label: "Other",
    hint: "Custom endpoint label for future channels",
  },
};
