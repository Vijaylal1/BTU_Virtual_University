"""
Vercel serverless entry point.
Vercel's @vercel/python builder looks for an `app` ASGI object in this file.
"""

import os
import sys

# Ensure project root is on sys.path so all imports resolve
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from api.app import app  # noqa: E402 – re-export the FastAPI app for Vercel
