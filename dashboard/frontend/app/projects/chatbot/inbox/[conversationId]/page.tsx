"use client";

import { use } from "react";
import { ConversationWorkspacePanel } from "../../../../components/ConversationWorkspacePanel";

export default function ConversationWorkspacePage({
  params,
}: {
  params: Promise<{ conversationId: string }>;
}) {
  const { conversationId } = use(params);
  return (
    <div className="flex min-h-[calc(100dvh-10rem)] flex-col">
      <ConversationWorkspacePanel conversationId={conversationId} />
    </div>
  );
}
