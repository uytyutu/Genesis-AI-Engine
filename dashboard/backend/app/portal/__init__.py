"""Client Portal domain package (R3.5+ / R3.6+).

Architecture: Client → Website → Deployment | Asset | EditSession.
Read layer: PortalReadService (R3.6.1).
Factory builds artifacts; Portal manages Website — not Factory logic.
"""

from app.portal.asset import Asset, new_asset
from app.portal.client import Client, new_client, website_for_client
from app.portal.deployment import Deployment, attach_deployment, new_deployment
from app.portal.edit_session import EditSession, close_edit_session, new_edit_session
from app.portal.read_service import PortalCatalog, PortalReadService
from app.portal.website import OrderWebsiteRef, Website, new_website

__all__ = [
    "Asset",
    "Client",
    "Deployment",
    "EditSession",
    "OrderWebsiteRef",
    "PortalCatalog",
    "PortalReadService",
    "Website",
    "attach_deployment",
    "close_edit_session",
    "new_asset",
    "new_client",
    "new_deployment",
    "new_edit_session",
    "new_website",
    "website_for_client",
]
