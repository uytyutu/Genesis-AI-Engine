"use client";

import { ConversationInboxPanel } from "../../../components/ConversationInboxPanel";

export default function ConversationInboxPage() {
  return (
    <div className="flex min-h-[calc(100dvh-10rem)] flex-col">
      <ConversationInboxPanel />
    </div>
  );
}
