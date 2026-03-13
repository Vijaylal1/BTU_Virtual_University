"""
Wheel of Fortune – random prize draw unlocked when sprint target is met.
"""

from __future__ import annotations

import random

from agents.handoff import WheelPrize
from memory.store import MemoryStore

_PRIZES = [
    WheelPrize(prize_label="🕐 Bonus 2 Hours",       prize_type="bonus_hours", value=2),
    WheelPrize(prize_label="⚡ Double XP Weekend",    prize_type="double_xp",   value=2),
    WheelPrize(prize_label="💡 Professor Hint",        prize_type="hint",        value=1),
    WheelPrize(prize_label="⏭️ Chapter Fast-Track",   prize_type="skip",        value=1),
    WheelPrize(prize_label="🎁 Mystery Bonus",         prize_type="mystery",     value=None),
    WheelPrize(prize_label="📚 Curriculum PDF Unlock", prize_type="pdf_unlock",  value=1),
    WheelPrize(prize_label="🏅 Bonus Badge",           prize_type="badge",       value="Spin Master"),
    WheelPrize(prize_label="🔁 Free Respin",           prize_type="respin",      value=1),
]


class WheelOfFortune:
    def __init__(self, memory: MemoryStore) -> None:
        self.memory = memory

    async def spin(self, student_id: str) -> WheelPrize:
        prize = random.choice(_PRIZES)
        await self.memory.save_wheel_spin(
            student_id=student_id,
            prize=prize.prize_label,
            prize_type=prize.prize_type,
        )
        return prize

    def get_prizes(self) -> list[WheelPrize]:
        """Return all possible prizes (for UI rendering)."""
        return list(_PRIZES)
