"""OR — Register chatbot ops metrics router."""

from __future__ import annotations

from fastapi import FastAPI

from app.portal.portal_chatbot_ops_router import portal_chatbot_ops_router

ENGINE_ID = "portal_chatbot_ops_registration_v1"


def register_portal_chatbot_ops(app: FastAPI) -> None:
    app.include_router(portal_chatbot_ops_router)
