"""Virtus AI — digital project director + model orchestrator (stub).

Canon: docs/canon/VIRTUS_AI_WORKSPACE.md
Not a universal chatbot. Not hard-wired to one vendor model.
"""

from __future__ import annotations

from app.integration.virtus_ai.character import welcome_message, redirect_to_project
from app.integration.virtus_ai.orchestrator import handle_turn
from app.integration.virtus_ai.ownership import check_ownership
from app.integration.virtus_ai.session_memory import load_session, save_session

__all__ = [
    "check_ownership",
    "handle_turn",
    "load_session",
    "redirect_to_project",
    "save_session",
    "welcome_message",
]
