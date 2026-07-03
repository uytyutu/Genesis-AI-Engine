"""Project roadmap timeline for owner UI."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Milestone:
    id: str
    label: str
    status: str  # done | active | pending


_MILESTONES: tuple[Milestone, ...] = (
    Milestone("kernel", "Kernel", "done"),
    Milestone("brain", "Brain", "done"),
    Milestone("storage", "Storage", "done"),
    Milestone("command_center", "Command Center", "done"),
    Milestone("launcher", "Launcher", "done"),
    Milestone("owner_ux", "Интерфейс владельца", "active"),
    Milestone("factory", "Factory", "pending"),
    Milestone("templates", "Templates", "pending"),
    Milestone("marketplace", "Marketplace", "pending"),
    Milestone("revenue", "Revenue", "pending"),
    Milestone("evolution", "Evolution", "pending"),
)


class TimelineService:
    """Factual build progress — not business revenue projections."""

    def snapshot(self) -> dict:
        total = len(_MILESTONES)
        done = sum(1 for m in _MILESTONES if m.status == "done")
        active = sum(1 for m in _MILESTONES if m.status == "active")
        # Active milestone counts as half a step toward the bar.
        progress_percent = round(((done + active * 0.5) / total) * 100)

        items = []
        for m in _MILESTONES:
            symbol = "✔" if m.status == "done" else "◐" if m.status == "active" else "◯"
            items.append(
                {
                    "id": m.id,
                    "label": m.label,
                    "status": m.status,
                    "symbol": symbol,
                }
            )

        return {
            "progress_percent": progress_percent,
            "label": "Инженерный фундамент",
            "milestones": items,
            "done_count": done,
            "active_count": active,
            "pending_count": sum(1 for m in _MILESTONES if m.status == "pending"),
        }
