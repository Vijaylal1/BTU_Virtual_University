"""
SME evaluation harness for Prof. Priya Place (chapters 1-3).
Runs a set of curated questions through the full pipeline and scores responses.

Usage:
    python tests/sme/eval_place.py

Requires: running API (make dev) and valid ANTHROPIC_API_KEY.
"""

from __future__ import annotations

import asyncio
import json

import httpx

BASE_URL = "http://localhost:8080"

_TEST_CASES = [
    {
        "question": "What factors should I consider when choosing a retail location?",
        "expected_keywords": ["footfall", "demographics", "competition", "lease", "accessibility"],
        "chapter": 1,
    },
    {
        "question": "How do I evaluate whether a site is suitable for my business?",
        "expected_keywords": ["site", "analysis", "zoning", "cost", "visibility"],
        "chapter": 2,
    },
    {
        "question": "What is a footprint strategy and why does it matter?",
        "expected_keywords": ["footprint", "expansion", "multi-site", "hub"],
        "chapter": 3,
    },
]


async def run_eval(token: str) -> None:
    headers = {"Authorization": f"Bearer {token}"}
    results = []

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60) as client:
        for case in _TEST_CASES:
            resp = await client.post("/chat", headers=headers, json={"message": case["question"]})
            resp.raise_for_status()
            data = resp.json()
            text = data["text"].lower()
            score = sum(1 for kw in case["expected_keywords"] if kw in text)
            pct = score / len(case["expected_keywords"]) * 100
            results.append({
                "chapter": case["chapter"],
                "question": case["question"][:60],
                "score": f"{score}/{len(case['expected_keywords'])}",
                "pct": f"{pct:.0f}%",
                "agent": data["source_agent"],
            })

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    import os
    token = os.environ.get("BTU_TEST_TOKEN", "")
    if not token:
        print("Set BTU_TEST_TOKEN env var with a valid JWT to run SME eval.")
    else:
        asyncio.run(run_eval(token))
