"""
Badge System – award badges for learning milestones.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from memory.store import MemoryStore


class BadgeTrigger(str, Enum):
    ONBOARDING       = "onboarding"
    CHAPTER_COMPLETE = "chapter_complete"
    SPRINT_COMPLETE  = "sprint_complete"
    WHEEL_SPIN       = "wheel_spin"
    GRADUATION       = "graduation"


@dataclass
class Badge:
    id: str
    label: str
    emoji: str
    description: str


_BADGE_MAP: dict[BadgeTrigger, list[Badge]] = {
    BadgeTrigger.ONBOARDING: [
        Badge("pioneer", "BTU Pioneer",     "🎒", "Joined the BTU Virtual University journey"),
    ],
    BadgeTrigger.CHAPTER_COMPLETE: [
        Badge("chapter_1",  "Place Explorer",   "🗺️",  "Completed Chapter 1: Introduction to Place"),
        Badge("chapter_3",  "Place Master",     "📍",  "Completed all Place chapters (1-3)"),
        Badge("chapter_10", "Halfway Hero",     "🏁",  "Reached the midpoint of the programme"),
        Badge("chapter_30", "BTU Graduate",     "🎓",  "Completed all 30 chapters"),
    ],
    BadgeTrigger.SPRINT_COMPLETE: [
        Badge("sprint_1", "First Sprint",   "🏃",  "Completed Week 1 sprint (15 hrs)"),
        Badge("sprint_5", "Iron Sprinter",  "🔩",  "Completed 5 consecutive sprints"),
    ],
    BadgeTrigger.WHEEL_SPIN: [
        Badge("spin_master", "Spin Master", "🎡", "Spun the Wheel of Fortune"),
    ],
    BadgeTrigger.GRADUATION: [
        Badge("graduate", "BTU Graduate", "🎓", "Completed the full BTU programme"),
    ],
}


class BadgeSystem:
    def __init__(self, memory: MemoryStore) -> None:
        self.memory = memory

    async def award(self, student_id: str, trigger: BadgeTrigger, context: dict | None = None) -> list[Badge]:
        """Award relevant badges based on trigger and context."""
        awarded: list[Badge] = []
        candidates = _BADGE_MAP.get(trigger, [])

        for badge in candidates:
            if trigger == BadgeTrigger.CHAPTER_COMPLETE:
                chapter = (context or {}).get("chapter", 0)
                if badge.id == f"chapter_{chapter}":
                    awarded.append(badge)
                    await self.memory.save_wheel_spin(student_id, badge.label, "badge")
            else:
                awarded.append(badge)
                await self.memory.save_wheel_spin(student_id, badge.label, "badge")

        return awarded

    @staticmethod
    def all_badges() -> list[Badge]:
        return [b for badges in _BADGE_MAP.values() for b in badges]
