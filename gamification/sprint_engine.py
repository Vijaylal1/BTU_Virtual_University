"""
Sprint Engine – manages the 15-hour weekly learning sprint.
Wraps SprintTracker with game-layer logic (badges, wheel unlock).
"""

from __future__ import annotations

from memory.sprint_tracker import SprintTracker
from memory.store import MemoryStore


class SprintEngine:
    def __init__(self, memory: MemoryStore) -> None:
        self.memory  = memory
        self.tracker = SprintTracker(memory)

    async def get_status(self, student_id: str) -> dict:
        return await self.tracker.get_status(student_id)

    async def log_hours(self, student_id: str, hours: float) -> dict:
        status = await self.tracker.log_hours(student_id, hours)
        # Unlock wheel if sprint target hit
        if status["status"] == "completed":
            status["wheel_unlocked"] = True
        return status

    async def check_wheel_eligibility(self, student_id: str) -> bool:
        """Student can spin the wheel when weekly sprint target is met."""
        status = await self.tracker.get_status(student_id)
        return status.get("pct", 0) >= 100
