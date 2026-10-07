export type OrderStatus =
  | "pending"
  | "paid"
  | "failed"
  | "cancelled"
  | "refunded";

export type GiftStatus =
  | "draft"
  | "awaiting_payment"
  | "paid"
  | "sent"
  | "opened"
  | "replied"
  | "expired"
  | "blocked";

export type RevealStatus = "hidden" | "available" | "purchased" | "revealed";

export interface UserRow {
  id: string;
  email: string;
  password_hash: string;
  display_name: string;
  username: string | null;
  avatar: string | null;
  language: string;
  timezone: string;
  role: "user" | "owner" | "admin" | "moderator" | "support" | "analyst";
  created_at: string;
  banned_at: string | null;
  last_seen_at?: string | null;
}

export interface GiftRow {
  id: string;
  token: string;
  sender_id: string | null;
  recipient_id: string | null;
  recipient_label: string | null;
  type: string;
  status: GiftStatus;
  price_cents: number;
  currency: string;
  message: string;
  media_json: string;
  theme: string;
  music: string | null;
  anonymous: number;
  anonymous_id: string | null;
  reveal_enabled: number;
  reveal_status: RevealStatus;
  open_when_label: string | null;
  unlock_at: string | null;
  opened_at: string | null;
  expires_at: string | null;
  created_at: string;
  easter_clicks: number;
}

export interface OrderRow {
  id: string;
  user_id: string | null;
  gift_id: string | null;
  gift_type: string;
  amount_cents: number;
  currency: string;
  stripe_session_id: string | null;
  stripe_payment_id: string | null;
  status: OrderStatus;
  anonymous: number;
  reveal_status: RevealStatus;
  metadata_json: string;
  created_at: string;
  paid_at: string | null;
}

export interface AnonIdentityRow {
  id: string;
  public_anon_id: string;
  owner_user_id: string;
  is_revealed: number;
  created_at: string;
}

export interface ChatThreadRow {
  id: string;
  gift_id: string;
  anon_identity_id: string | null;
  sender_label: string;
  recipient_label: string;
  created_at: string;
}

export interface ChatMessageRow {
  id: string;
  thread_id: string;
  sender_side: "anon" | "recipient" | "system";
  body: string;
  created_at: string;
  read_at: string | null;
}

export interface NotificationRow {
  id: string;
  user_id: string;
  type: string;
  title: string;
  body: string;
  href: string | null;
  read_at: string | null;
  created_at: string;
}

export interface ReportRow {
  id: string;
  reporter_id: string | null;
  target_type: string;
  target_id: string;
  reason: string;
  status: string;
  created_at: string;
}

export interface BlockRow {
  id: string;
  blocker_id: string;
  blocked_key: string;
  created_at: string;
}
