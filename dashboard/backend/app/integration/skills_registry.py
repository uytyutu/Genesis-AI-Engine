"""Foundation F7 — skill registration (Factory landing = first skill)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

SkillFamily = Literal["websites", "bots", "commerce", "apps", "automations"]
SkillStatus = Literal["active", "stub", "disabled"]

REGISTRY_VERSION = "foundation-skills-1"


@dataclass(frozen=True)
class SkillDefinition:
    id: str
    family: SkillFamily
    version: str
    label: str
    factory_product_type: str | None
    status: SkillStatus
    enabled: bool
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_SKILLS: dict[str, SkillDefinition] = {
    "landing-page-v1": SkillDefinition(
        id="landing-page-v1",
        family="websites",
        version="0.1",
        label="Landing Page",
        factory_product_type="landing-page",
        status="active",
        enabled=True,
        notes="Factory v0.1 — sandbox HTML landing builder",
    ),
    "telegram-bot-v1": SkillDefinition(
        id="telegram-bot-v1",
        family="bots",
        version="0.0",
        label="Telegram Bot",
        factory_product_type="telegram-bot",
        status="stub",
        enabled=False,
        notes="Horizon — register only, no factory pipeline",
    ),
}


class SkillsRegistry:
    """Read-only skill catalog — links Factory product types to Kernel skill packs."""

    def list_skills(self) -> list[SkillDefinition]:
        return list(_SKILLS.values())

    def get(self, skill_id: str) -> SkillDefinition | None:
        return _SKILLS.get(skill_id)

    def by_factory_type(self, product_type: str) -> SkillDefinition | None:
        for skill in _SKILLS.values():
            if skill.factory_product_type == product_type:
                return skill
        return None

    def snapshot(self) -> dict[str, Any]:
        skills = self.list_skills()
        return {
            "version": REGISTRY_VERSION,
            "skills": [s.to_dict() for s in skills],
            "enabled_count": sum(1 for s in skills if s.enabled),
        }
