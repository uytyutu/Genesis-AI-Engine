"""Platform surface registry — M3.1 classification (Public / Client / CEO)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

SurfaceTarget = Literal["public", "client", "ceo"]
ShellKind = Literal["public", "mission_control", "transitional"]

_REPO_ROOT = Path(__file__).resolve().parents[3]
_REGISTRY_PATH = _REPO_ROOT / "platform" / "surface_registry.json"


@dataclass(frozen=True)
class SurfaceRoute:
    path: str
    label: str
    target: SurfaceTarget
    current_shell: ShellKind
    capabilities: tuple[str, ...]
    overlap: tuple[SurfaceTarget, ...]
    migration_note: str

    def matches(self, pathname: str) -> bool:
        if self.path == pathname:
            return True
        pattern = re.sub(r":(\w+)", r"[^/]+", self.path)
        regex = "^" + pattern.replace("/", r"\/") + "$"
        return bool(re.match(regex, pathname))


def load_registry() -> dict[str, Any]:
    data = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("surface_registry.json must be an object")
    return data


def parse_routes(data: dict[str, Any] | None = None) -> list[SurfaceRoute]:
    raw = data or load_registry()
    routes: list[SurfaceRoute] = []
    for item in raw.get("routes") or []:
        if not isinstance(item, dict):
            continue
        routes.append(
            SurfaceRoute(
                path=str(item.get("path") or ""),
                label=str(item.get("label") or ""),
                target=item.get("target") or "public",
                current_shell=item.get("current_shell") or "public",
                capabilities=tuple(item.get("capabilities") or []),
                overlap=tuple(item.get("overlap") or []),
                migration_note=str(item.get("migration_note") or ""),
            )
        )
    return routes


def routes_for_target(target: SurfaceTarget) -> list[SurfaceRoute]:
    return [r for r in parse_routes() if r.target == target or target in r.overlap]


def classify_path(pathname: str) -> SurfaceRoute | None:
    best: SurfaceRoute | None = None
    best_len = -1
    for route in parse_routes():
        if route.matches(pathname) and len(route.path) > best_len:
            best = route
            best_len = len(route.path)
    return best


def client_nav_paths() -> list[str]:
    nav = load_registry().get("navigation") or {}
    paths = nav.get("client_nav_paths") or ["/projects"]
    return [str(p) for p in paths]


def resolve_navigation_surface(pathname: str) -> SurfaceTarget:
    for prefix in client_nav_paths():
        if pathname == prefix or pathname.startswith(f"{prefix}/"):
            return "client"
    if pathname == "/":
        return "ceo"
    if pathname == "/products":
        return "public"
    for prefix in ceo_mc_prefixes():
        if pathname == prefix or (prefix != "/" and pathname.startswith(f"{prefix}/")):
            return "ceo"
    return "public"


def ceo_mc_prefixes() -> list[str]:
    """Paths that use Mission Control chrome today (AppShell MC_PREFIXES alignment)."""
    prefixes: set[str] = set()
    for route in parse_routes():
        if route.current_shell == "mission_control":
            base = route.path.split("/:")[0].rstrip("/") or "/"
            prefixes.add(base if base != "" else "/")
    return sorted(prefixes, key=lambda p: (p != "/", p))
