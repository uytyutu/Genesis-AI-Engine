"""R3.7.1 — Portal Read API Contract (declared only; not mounted)."""

from __future__ import annotations

from app.portal.read_api_contract import (
    ENGINE_ID,
    PORTAL_READ_ROUTES,
    ClientPath,
    WebsiteAssetsQuery,
    WebsitePath,
    contract_as_dict,
    list_read_paths,
    route_by_name,
)
from app.portal.views import (
    AssetView,
    ClientView,
    DeploymentView,
    EditSessionView,
    WebsiteView,
)


def test_engine_id():
    assert ENGINE_ID == "portal_read_api_contract_v1"


def test_five_get_routes_declared():
    assert len(PORTAL_READ_ROUTES) == 5
    assert all(r.method == "GET" for r in PORTAL_READ_ROUTES)
    paths = list_read_paths()
    assert "/portal/clients/{client_id}" in paths
    assert "/portal/websites/{website_id}" in paths
    assert "/portal/websites/{website_id}/deployment" in paths
    assert "/portal/websites/{website_id}/assets" in paths
    assert "/portal/websites/{website_id}/edit-session" in paths


def test_response_models_are_views():
    by_name = {r.name: r for r in PORTAL_READ_ROUTES}
    assert by_name["get_client"].response_model is ClientView
    assert by_name["get_website"].response_model is WebsiteView
    assert by_name["get_current_deployment"].response_model is DeploymentView
    assert by_name["get_assets"].response_model is AssetView
    assert by_name["get_assets"].response_is_list is True
    assert by_name["get_open_edit_session"].response_model is EditSessionView


def test_input_models_exist():
    assert ClientPath(client_id="c1").client_id == "c1"
    assert WebsitePath(website_id="w1").website_id == "w1"
    q = WebsiteAssetsQuery(website_id="w1", asset_type="logo")
    assert q.asset_type == "logo"


def test_contract_not_mounted():
    snap = contract_as_dict()
    assert snap["mounted"] is False
    assert snap["auth"] is False
    assert route_by_name("get_client") is not None
    assert route_by_name("missing") is None


def test_no_fastapi_in_contract_module():
    import app.portal.read_api_contract as mod

    src = open(mod.__file__, encoding="utf-8").read()
    assert "from fastapi" not in src
    assert "import fastapi" not in src
    assert "APIRouter" not in src
    assert "@app." not in src
    assert "include_router" not in src
