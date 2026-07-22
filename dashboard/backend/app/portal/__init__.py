"""Client Portal domain package (R3.5+).

Architecture: Client → Website → Deployment.
Factory builds artifacts; Portal manages Website — not Factory logic.
"""

from app.portal.client import Client, new_client, website_for_client
from app.portal.deployment import Deployment, attach_deployment, new_deployment
from app.portal.website import OrderWebsiteRef, Website, new_website

__all__ = [
    "Client",
    "Deployment",
    "OrderWebsiteRef",
    "Website",
    "attach_deployment",
    "new_client",
    "new_deployment",
    "new_website",
    "website_for_client",
]
