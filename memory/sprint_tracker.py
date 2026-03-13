"""
Sprint tracker – week-based learning sprint management.
Thin wrapper around MemoryStore for sprint-specific operations.
"""

from __future__ import annotations

from memory.store import MemoryStore


class SprintTracker:
    def __init__(self, memory: MemoryStore) -> None:
        self.memory = memory

    async def get_status(self, student_id: str) -> dict:
        sprint = await self.memory.get_active_sprint(student_id)
        if not sprint:
            return {"week": 1, "logged": 0.0, "target": 15.0, "status": "not_started", "pct": 0}
        pct = min(100, int((sprint.hours_logged / sprint.target_hours) * 100))
        return {
            "week":    sprint.week_number,
            "logged":  sprint.hours_logged,
            "target":  sprint.target_hours,
            "status":  sprint.status,
            "pct":     pct,
        }

    async def log_hours(self, student_id: str, hours: float) -> dict:
        sprint = await self.memory.log_sprint_hours(student_id, hours)
        pct = min(100, int((sprint.hours_logged / sprint.target_hours) * 100))
        return {
            "week":     sprint.week_number,
            "logged":   sprint.hours_logged,
            "target":   sprint.target_hours,
            "status":   sprint.status,
            "pct":      pct,
            "message":  "Sprint target achieved! 🎉" if sprint.status == "completed" else f"{pct}% of weekly goal reached.",
        }
