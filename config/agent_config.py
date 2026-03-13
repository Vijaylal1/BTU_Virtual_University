"""
Agent-level configuration: chapter→professor mapping, POC scope,
agent display names, and per-professor chapter ranges.

The BTU programme is structured around 10 P's of Business:
  Place · People · Process · Positioning · Performance
  Platform · Pricing · Purpose · Policy · Profit
"""

from __future__ import annotations

# ── Chapter → Professor ID mapping (30 chapters, 10 professors, 3 each) ──────
CHAPTER_TO_PROFESSOR: dict[int, str] = {
    # P1 – Prof. Priya Place        (Ch. 1-3)   ← POC ACTIVE
    1: "place",  2: "place",  3: "place",
    # P2 – Prof. Maya People        (Ch. 4-6)
    4: "people", 5: "people", 6: "people",
    # P3 – Prof. Sam Process        (Ch. 7-9)
    7: "process", 8: "process", 9: "process",
    # P4 – Prof. Pablo Positioning  (Ch. 10-12)
    10: "positioning", 11: "positioning", 12: "positioning",
    # P5 – Prof. Leila Performance  (Ch. 13-15)
    13: "performance", 14: "performance", 15: "performance",
    # P6 – Prof. Dana Platform      (Ch. 16-18)
    16: "platform", 17: "platform", 18: "platform",
    # P7 – Prof. Marcus Pricing     (Ch. 19-21)
    19: "pricing", 20: "pricing", 21: "pricing",
    # P8 – Prof. Iris Purpose       (Ch. 22-24)
    22: "purpose", 23: "purpose", 24: "purpose",
    # P9 – Prof. Lucas Policy       (Ch. 25-27)
    25: "policy", 26: "policy", 27: "policy",
    # P10 – Prof. Petra Profit      (Ch. 28-30)
    28: "profit", 29: "profit", 30: "profit",
}

# ── Professor → Chapter list ──────────────────────────────────────────────────
PROFESSOR_CHAPTERS: dict[str, list[int]] = {}
for _ch, _prof in CHAPTER_TO_PROFESSOR.items():
    PROFESSOR_CHAPTERS.setdefault(_prof, []).append(_ch)

# ── Professor display info ────────────────────────────────────────────────────
PROFESSOR_META: dict[str, dict] = {
    "place":       {"name": "Prof. Priya Place",       "domain": "Location & Footprint Strategy",      "active": True},
    "people":      {"name": "Prof. Maya People",       "domain": "Team & Talent Strategy",             "active": False},
    "process":     {"name": "Prof. Sam Process",       "domain": "Operations & Workflow Design",       "active": False},
    "positioning": {"name": "Prof. Pablo Positioning", "domain": "Growth & Customer Positioning",      "active": False},
    "performance": {"name": "Prof. Leila Performance", "domain": "Leadership & Performance Culture",   "active": False},
    "platform":    {"name": "Prof. Dana Platform",     "domain": "Digital Platform & Transformation",  "active": False},
    "pricing":     {"name": "Prof. Marcus Pricing",    "domain": "Financial Planning & Pricing",       "active": False},
    "purpose":     {"name": "Prof. Iris Purpose",      "domain": "ESG, Purpose & Social Impact",       "active": False},
    "policy":      {"name": "Prof. Lucas Policy",      "domain": "Legal, Policy & Compliance",         "active": False},
    "profit":      {"name": "Prof. Petra Profit",      "domain": "Revenue Optimisation & Exit",        "active": False},
}

# ── Agents active in POC ──────────────────────────────────────────────────────
POC_ACTIVE_PROFESSORS: list[str] = [pid for pid, meta in PROFESSOR_META.items() if meta["active"]]

# ── Agent IDs ─────────────────────────────────────────────────────────────────
DEAN_ID  = "dean_morgan"
COACH_ID = "elias_vance"


def get_professor_for_chapter(chapter: int) -> str | None:
    return CHAPTER_TO_PROFESSOR.get(chapter)


def get_chapters_for_professor(professor_id: str) -> list[int]:
    return PROFESSOR_CHAPTERS.get(professor_id, [])


def is_professor_active(professor_id: str) -> bool:
    return PROFESSOR_META.get(professor_id, {}).get("active", False)
