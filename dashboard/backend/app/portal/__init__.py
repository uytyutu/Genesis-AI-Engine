"""Client Portal domain package (R3.5+).

Architecture: Client → Website → Deployment.
Factory builds artifacts; Portal manages Website — not Factory logic.
"""

from app.portal.client import Client, new_client, website_for_client
from app.portal.website import Deployment, OrderWebsiteRef, Website, new_website

__all__ = [
    "Client",
    "Deployment",
    "OrderWebsiteRef",
    "Website",
    "new_client",
    "new_website",
    "website_for_client",
]
