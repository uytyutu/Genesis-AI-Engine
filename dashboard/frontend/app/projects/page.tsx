"use client";

import { ProjectPlatformShell } from "../components/ProjectPlatformShell";

function focusVector() {
  window.location.href = "/site?view=vector";
}

export default function ProjectsPage() {
  return (
    <div className="flex min-h-[calc(100dvh-10rem)] flex-col">
      <p className="mb-4 text-sm text-genesis-muted">
        Ваши проекты и результаты — здесь, в вашей цифровой компании. Vector ведёт процесс.
      </p>
      <div className="min-h-[min(72dvh,44rem)] flex-1">
        <ProjectPlatformShell onStartProject={focusVector} />
      </div>
    </div>
  );
}
