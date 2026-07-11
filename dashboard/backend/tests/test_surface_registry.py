"""M3.1 — Surface registry completeness and AppShell alignment."""

from __future__ import annotations

from app.platform.surface_registry import (
    classify_path,
    load_registry,
    parse_routes,
    routes_for_target,
)

# AppShell MC_PREFIXES as of M3.1 (must stay in sync until M3.2 wires registry)
APP_SHELL_MC_PREFIXES = [
    "/finance",
    "/company",
    "/ai",
    "/cursor",
    "/revenue",
    "/marketplace",
    "/monitor",
    "/dev",
    "/check",
    "/create",
    "/settings",
    "/setup",
    "/launch",
    "/opportunities",
    "/acquisition",
    "/projects",
    "/products",
    "/growth",
    "/tasks",
]


def test_registry_loads():
    data = load_registry()
    assert data["version"] == "m3.3"
    assert len(data.get("routes") or []) >= 30


def test_three_surfaces_represented():
    public = routes_for_target("public")
    client = routes_for_target("client")
    ceo = routes_for_target("ceo")
    assert any(r.path == "/site" for r in public)
    assert any(r.path == "/projects" for r in client)
    assert any(r.path == "/" for r in ceo)


def test_kernel_layers_documented():
    layers = load_registry().get("kernel_layers") or []
    assert "planner" in layers
    assert "memory" in layers


def test_slice_gate_questions():
    gate = load_registry().get("slice_gate") or []
    assert len(gate) == 3


def test_site_classified_with_overlap():
    site = classify_path("/site")
    assert site is not None
    assert site.target == "public"
    assert "client" in site.overlap


def test_mission_control_root():
    mc = classify_path("/")
    assert mc is not None
    assert mc.target == "ceo"


def test_app_shell_prefixes_covered_by_registry():
    routes = parse_routes()
    mc_paths = {r.path.split("/:")[0] for r in routes if r.current_shell == "mission_control"}
    mc_paths.add("/")
    for prefix in APP_SHELL_MC_PREFIXES:
        if prefix == "/products":
            # Public catalog exception — documented in AppShell
            continue
        assert prefix in mc_paths or any(
            p == prefix or p.startswith(prefix + "/") for p in mc_paths
        ), f"MC prefix {prefix} missing from registry mission_control routes"


def test_no_route_without_capabilities():
    for route in parse_routes():
        assert route.capabilities, f"{route.path} must list capabilities"


def test_navigation_surfaces_defined():
    nav = load_registry().get("navigation") or {}
    surfaces = nav.get("surfaces") or {}
    assert "public" in surfaces
    assert "client" in surfaces
    assert "ceo" in surfaces
    assert surfaces["public"].get("user_flow")


def test_m3_3_gate_questions():
    gate = load_registry().get("m3_3_gate") or []
    assert len(gate) == 4


def test_m3_4_principles_and_gate():
    data = load_registry()
    assert len(data.get("m3_4_principles") or []) >= 5
    assert len(data.get("m3_4_gate") or []) == 5


def test_resolve_navigation_surface_m3_2():
    from app.platform.surface_registry import resolve_navigation_surface

    assert resolve_navigation_surface("/site") == "public"
    assert resolve_navigation_surface("/projects") == "client"
    assert resolve_navigation_surface("/") == "ceo"
    assert resolve_navigation_surface("/finance") == "ceo"
    assert resolve_navigation_surface("/create") == "ceo"
