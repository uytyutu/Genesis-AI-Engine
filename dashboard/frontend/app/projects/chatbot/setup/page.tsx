"use client";

import { ChatbotSetupQuestionnaire } from "../../../components/ChatbotSetupQuestionnaire";

export default function VectorFirstRunSetupPage() {
  return (
    <div className="flex min-h-[calc(100dvh-10rem)] flex-col">
      <ChatbotSetupQuestionnaire />
    </div>
  );
}
