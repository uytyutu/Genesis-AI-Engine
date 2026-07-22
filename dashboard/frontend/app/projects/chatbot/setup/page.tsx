"use client";

import { ChatbotFirstRunWizard } from "../../../components/ChatbotFirstRunWizard";

export default function VectorFirstRunSetupPage() {
  return (
    <div className="flex min-h-[calc(100dvh-10rem)] flex-col">
      <ChatbotFirstRunWizard />
    </div>
  );
}
