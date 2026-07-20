"""Catalog Engine Layer A — JSON product catalog for shop niches (Factory ZIP)."""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SHOP_NICHES = frozenset({"energy", "appliance", "beauty", "computer", "green"})

_BACKEND = Path(__file__).resolve().parents[2]
_SHOWCASES = _BACKEND / "_research_3d" / "showcases"

_SKU_RE = re.compile(r"^[a-z0-9][a-z0-9_\-]{0,63}$")


@dataclass
class CatalogProduct:
    sku: str
    name: str
    content_type: str = "product"  # product|service|portfolio|project|menu|real_estate|vehicle
    category_id: str = ""
    price: float = 0.0
    currency: str = "EUR"
    images: list[str] = field(default_factory=list)
    summary: str = ""
    cta: str = "request"
    three_d_model_enabled: bool = False
    vxp_product_id: str = ""
    vxp_hotspots_ref: str = ""
    attrs: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> CatalogProduct:
        sku = str(raw.get("sku") or "").strip().lower()
        cta = str(raw.get("cta") or "request").strip().lower()
        if cta == "buy":
            cta = "request"  # Layer A: no shop checkout
        images = raw.get("images") if isinstance(raw.get("images"), list) else []
        attrs = raw.get("attrs") if isinstance(raw.get("attrs"), dict) else {}
        ctype = str(raw.get("type") or raw.get("content_type") or "product").strip().lower()
        if ctype not in (
            "product",
            "service",
            "portfolio",
            "project",
            "menu",
            "real_estate",
            "vehicle",
            "case_study",
            "team_member",
            "object",
        ):
            ctype = "product"
        return cls(
            sku=sku,
            name=str(raw.get("name") or sku).strip() or sku,
            content_type=ctype,
            category_id=str(raw.get("category_id") or "").strip(),
            price=float(raw.get("price") or 0),
            currency=str(raw.get("currency") or "EUR").strip().upper() or "EUR",
            images=[str(i) for i in images if str(i).strip()],
            summary=str(raw.get("summary") or "").strip(),
            cta=cta if cta in ("contact", "request") else "request",
            three_d_model_enabled=bool(
                raw.get("3d_model_enabled") or raw.get("three_d_model_enabled")
            ),
            vxp_product_id=str(raw.get("vxp_product_id") or "").strip(),
            vxp_hotspots_ref=str(raw.get("vxp_hotspots_ref") or "").strip(),
            attrs=dict(attrs),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "sku": self.sku,
            "type": self.content_type,
            "name": self.name,
            "category_id": self.category_id,
            "price": self.price,
            "currency": self.currency,
            "images": list(self.images),
            "summary": self.summary,
            "cta": self.cta,
            "3d_model_enabled": self.three_d_model_enabled,
            "vxp_product_id": self.vxp_product_id,
            "vxp_hotspots_ref": self.vxp_hotspots_ref,
            "attrs": dict(self.attrs),
        }


@dataclass
class Catalog:
    version: int = 1
    mode: str = "catalog"
    niche_id: str = "generic"
    currency: str = "EUR"
    categories: list[dict[str, str]] = field(default_factory=list)
    product_skus: list[str] = field(default_factory=list)
    products: list[CatalogProduct] = field(default_factory=list)

    def to_index_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "mode": self.mode,
            "niche_id": self.niche_id,
            "currency": self.currency,
            "categories": list(self.categories),
            "product_skus": list(self.product_skus),
        }


@dataclass
class CatalogView:
    """Resolved catalog ready for landing_builder / ZIP assets."""

    mode: str
    niche_id: str
    currency: str
    categories: list[dict[str, str]]
    products: list[CatalogProduct]
    search: bool = False
    filters: bool = False
    request_cart: bool = False
    rich_cards: bool = False

    def to_public_json(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "niche_id": self.niche_id,
            "currency": self.currency,
            "categories": list(self.categories),
            "products": [p.to_dict() for p in self.products],
            "ui": {
                "search": self.search,
                "filters": self.filters,
                "request_cart": self.request_cart,
                "rich_cards": self.rich_cards,
            },
        }


def is_shop_niche(niche_id: str | None) -> bool:
    return (niche_id or "").strip().lower() in SHOP_NICHES


def _normalize_sku(sku: str) -> str:
    key = (sku or "").strip().lower().replace(" ", "_")
    if not _SKU_RE.match(key):
        raise ValueError(f"invalid_sku:{sku}")
    return key


def _package_ui_flags(package_id: str | None) -> dict[str, bool]:
    pid = (package_id or "basic").strip().lower()
    if pid == "premium":
        return {
            "search": True,
            "filters": True,
            "request_cart": True,
            "rich_cards": True,
        }
    if pid == "business":
        return {
            "search": True,
            "filters": True,
            "request_cart": True,
            "rich_cards": False,
        }
    return {
        "search": False,
        "filters": False,
        "request_cart": False,
        "rich_cards": False,
    }


def _mode_for_package(package_id: str | None) -> str:
    pid = (package_id or "basic").strip().lower()
    return "storefront" if pid in ("business", "premium") else "catalog"


class CatalogManager:
    """Disk CRUD for catalog.json + products/<sku>.json under a product folder."""

    def __init__(self, catalog_dir: Path) -> None:
        self.catalog_dir = Path(catalog_dir)
        self.products_dir = self.catalog_dir / "products"

    def ensure_dirs(self) -> None:
        self.products_dir.mkdir(parents=True, exist_ok=True)

    def load(self) -> Catalog:
        index_path = self.catalog_dir / "catalog.json"
        if not index_path.is_file():
            return Catalog()
        try:
            raw = json.loads(index_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return Catalog()
        if not isinstance(raw, dict):
            return Catalog()
        skus = [str(s).strip().lower() for s in (raw.get("product_skus") or []) if str(s).strip()]
        products: list[CatalogProduct] = []
        for sku in skus:
            path = self.products_dir / f"{sku}.json"
            if not path.is_file():
                continue
            try:
                pdata = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            if isinstance(pdata, dict):
                pdata.setdefault("sku", sku)
                products.append(CatalogProduct.from_dict(pdata))
        cats = raw.get("categories") if isinstance(raw.get("categories"), list) else []
        categories = [
            {"id": str(c.get("id") or "").strip(), "label": str(c.get("label") or "").strip()}
            for c in cats
            if isinstance(c, dict) and str(c.get("id") or "").strip()
        ]
        return Catalog(
            version=int(raw.get("version") or 1),
            mode=str(raw.get("mode") or "catalog"),
            niche_id=str(raw.get("niche_id") or "generic"),
            currency=str(raw.get("currency") or "EUR").upper(),
            categories=categories,
            product_skus=[p.sku for p in products],
            products=products,
        )

    def _write_index(self, catalog: Catalog) -> None:
        self.ensure_dirs()
        catalog.product_skus = [p.sku for p in catalog.products]
        (self.catalog_dir / "catalog.json").write_text(
            json.dumps(catalog.to_index_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def upsert_product(self, sku: str, data: dict[str, Any]) -> CatalogProduct:
        key = _normalize_sku(sku)
        payload = dict(data)
        payload["sku"] = key
        product = CatalogProduct.from_dict(payload)
        self.ensure_dirs()
        (self.products_dir / f"{key}.json").write_text(
            json.dumps(product.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        catalog = self.load()
        by_sku = {p.sku: p for p in catalog.products}
        by_sku[key] = product
        catalog.products = list(by_sku.values())
        if not catalog.niche_id or catalog.niche_id == "generic":
            catalog.niche_id = str(payload.get("niche_id") or catalog.niche_id or "generic")
        self._write_index(catalog)
        return product

    def delete_product(self, sku: str) -> bool:
        key = _normalize_sku(sku)
        path = self.products_dir / f"{key}.json"
        existed = path.is_file()
        if existed:
            path.unlink()
        catalog = self.load()
        catalog.products = [p for p in catalog.products if p.sku != key]
        self._write_index(catalog)
        return existed

    def import_catalog(self, payload: dict[str, Any] | Path) -> Catalog:
        if isinstance(payload, Path):
            raw = json.loads(payload.read_text(encoding="utf-8"))
        else:
            raw = payload
        if not isinstance(raw, dict):
            raise ValueError("invalid_catalog_payload")
        self.ensure_dirs()
        products_raw = raw.get("products")
        if isinstance(products_raw, list):
            items = products_raw
        else:
            items = []
            for sku in raw.get("product_skus") or []:
                items.append({"sku": sku})
        catalog = Catalog(
            version=int(raw.get("version") or 1),
            mode=str(raw.get("mode") or "catalog"),
            niche_id=str(raw.get("niche_id") or "generic"),
            currency=str(raw.get("currency") or "EUR").upper(),
            categories=[
                {"id": str(c.get("id") or ""), "label": str(c.get("label") or "")}
                for c in (raw.get("categories") or [])
                if isinstance(c, dict)
            ],
            products=[],
        )
        for item in items:
            if not isinstance(item, dict):
                continue
            sku = str(item.get("sku") or "").strip()
            if not sku:
                continue
            product = CatalogProduct.from_dict(item)
            (self.products_dir / f"{product.sku}.json").write_text(
                json.dumps(product.to_dict(), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            catalog.products.append(product)
        self._write_index(catalog)
        return self.load()

    def seed_from_vxp_energy(self) -> Catalog:
        """Seed SolarPanel + Inverter with Layer B 3D contract fields."""
        self.ensure_dirs()
        hotspots_solar = {
            "version": 1,
            "product_id": "solar_panel",
            "hotspots": [
                {
                    "id": "hs_watt",
                    "label": "400W",
                    "position": [0.12, 0.4, 0.05],
                    "binds": {"field": "attrs.watt", "sku": "solar_panel"},
                },
                {
                    "id": "hs_price",
                    "label": "Preis",
                    "position": [0.2, 0.15, 0.0],
                    "binds": {"field": "price", "sku": "solar_panel"},
                },
            ],
        }
        research_hs = _SHOWCASES / "energy" / "products" / "solar_panel" / "hotspots.json"
        if research_hs.parent.is_dir():
            try:
                research_hs.write_text(
                    json.dumps(hotspots_solar, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
            except OSError:
                pass

        payload = {
            "version": 1,
            "mode": "catalog",
            "niche_id": "energy",
            "currency": "EUR",
            "categories": [
                {"id": "pv", "label": "Solar"},
                {"id": "power", "label": "Systemtechnik"},
            ],
            "products": [
                {
                    "sku": "solar_panel",
                    "type": "product",
                    "name": "SolarPanel 400W",
                    "category_id": "pv",
                    "price": 189,
                    "currency": "EUR",
                    "images": ["assets/catalog/solar_panel.jpg"],
                    "summary": "Hochleistungs-Modul für Eigenverbrauch",
                    "cta": "request",
                    "3d_model_enabled": True,
                    "vxp_product_id": "solar_panel",
                    "vxp_hotspots_ref": "showcases/energy/products/solar_panel/hotspots.json",
                    "attrs": {"watt": 400, "warranty_years": 25},
                },
                {
                    "sku": "inverter",
                    "type": "product",
                    "name": "Inverter Hybrid 5kW",
                    "category_id": "power",
                    "price": 890,
                    "currency": "EUR",
                    "images": ["assets/catalog/inverter.jpg"],
                    "summary": "Wechselrichter für PV-Anlagen und Speicherung",
                    "cta": "request",
                    "3d_model_enabled": True,
                    "vxp_product_id": "inverter",
                    "vxp_hotspots_ref": "showcases/energy/products/inverter/hotspots.json",
                    "attrs": {"power_kw": 5},
                },
            ],
        }
        return self.import_catalog(payload)

    def seed_shop_defaults(self, niche_id: str) -> Catalog:
        niche = (niche_id or "").strip().lower()
        if niche == "energy":
            return self.seed_from_vxp_energy()
        labels = {
            "appliance": ("Geräte", "Service"),
            "beauty": ("Produkte", "Behandlungen"),
            "computer": ("Hardware", "Zubehör"),
            "green": ("Systeme", "Zubehör"),
        }
        cat_a, cat_b = labels.get(niche, ("Produkte", "Sonstiges"))
        return self.import_catalog(
            {
                "version": 1,
                "mode": "catalog",
                "niche_id": niche,
                "currency": "EUR",
                "categories": [
                    {"id": "main", "label": cat_a},
                    {"id": "extra", "label": cat_b},
                ],
                "products": [
                    {
                        "sku": f"{niche}_item_a",
                        "type": "product",
                        "name": f"{niche.title()} Angebot A",
                        "category_id": "main",
                        "price": 99,
                        "currency": "EUR",
                        "images": [],
                        "summary": "Produkt aus dem Katalog — Anfrage möglich.",
                        "cta": "request",
                        "3d_model_enabled": False,
                    },
                    {
                        "sku": f"{niche}_item_b",
                        "type": "product",
                        "name": f"{niche.title()} Angebot B",
                        "category_id": "extra",
                        "price": 149,
                        "currency": "EUR",
                        "images": [],
                        "summary": "Weiteres Angebot — Details auf Anfrage.",
                        "cta": "request",
                        "3d_model_enabled": False,
                    },
                ],
            }
        )

    def resolve_for_build(
        self,
        niche_id: str | None,
        package_id: str | None,
        *,
        seed_if_missing: bool = True,
    ) -> CatalogView | None:
        niche = (niche_id or "").strip().lower()
        if not is_shop_niche(niche):
            return None
        catalog = self.load()
        if not catalog.products and seed_if_missing:
            catalog = self.seed_shop_defaults(niche)
        if not catalog.products:
            return None
        flags = _package_ui_flags(package_id)
        mode = _mode_for_package(package_id)
        catalog.mode = mode
        catalog.niche_id = niche
        self._write_index(catalog)
        return CatalogView(
            mode=mode,
            niche_id=niche,
            currency=catalog.currency,
            categories=list(catalog.categories),
            products=list(catalog.products),
            search=flags["search"],
            filters=flags["filters"],
            request_cart=flags["request_cart"],
            rich_cards=flags["rich_cards"],
        )


def write_catalog_assets(product_dir: Path, view: CatalogView) -> None:
    """Write catalog/ tree, assets/catalog.json, catalog.js, and niche image copies."""
    catalog_dir = product_dir / "catalog"
    mgr = CatalogManager(catalog_dir)
    mgr.ensure_dirs()
    for product in view.products:
        (mgr.products_dir / f"{product.sku}.json").write_text(
            json.dumps(product.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    index = Catalog(
        version=1,
        mode=view.mode,
        niche_id=view.niche_id,
        currency=view.currency,
        categories=list(view.categories),
        products=list(view.products),
    )
    mgr._write_index(index)

    assets = product_dir / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    cat_img = assets / "catalog"
    cat_img.mkdir(parents=True, exist_ok=True)
    (assets / "catalog.json").write_text(
        json.dumps(view.to_public_json(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (assets / "catalog.js").write_text(CATALOG_JS, encoding="utf-8")

    if view.niche_id == "energy":
        for sku, fname in (
            ("solar_panel", "solar_panel.jpg"),
            ("inverter", "inverter.jpg"),
        ):
            src = _SHOWCASES / "energy" / "products" / sku / "preview.jpg"
            dest = cat_img / fname
            if src.is_file():
                try:
                    shutil.copy2(src, dest)
                except OSError:
                    pass


CATALOG_JS = r"""(function () {
  var root = document.getElementById("catalog");
  if (!root) return;
  var search = document.getElementById("catalog-search");
  var filter = document.getElementById("catalog-filter");
  var cards = Array.prototype.slice.call(root.querySelectorAll(".product-card"));
  var cart = [];
  var cartEl = document.getElementById("catalog-cart");
  var cartList = document.getElementById("catalog-cart-items");

  function apply() {
    var q = (search && search.value ? search.value : "").toLowerCase().trim();
    var cat = filter && filter.value ? filter.value : "";
    cards.forEach(function (card) {
      var name = (card.getAttribute("data-name") || "").toLowerCase();
      var summary = (card.getAttribute("data-summary") || "").toLowerCase();
      var c = card.getAttribute("data-category") || "";
      var okCat = !cat || c === cat;
      var okQ = !q || name.indexOf(q) >= 0 || summary.indexOf(q) >= 0;
      card.style.display = okCat && okQ ? "" : "none";
    });
  }
  if (search) search.addEventListener("input", apply);
  if (filter) filter.addEventListener("change", apply);

  function renderCart() {
    if (!cartList || !cartEl) return;
    cartEl.hidden = cart.length === 0;
    cartList.innerHTML = cart
      .map(function (sku) {
        return "<li>" + sku + "</li>";
      })
      .join("");
    var field = document.getElementById("catalog-inquiry-skus");
    if (field) field.value = cart.join(", ");
  }

  root.addEventListener("click", function (ev) {
    var btn = ev.target.closest("[data-cta]");
    if (!btn) return;
    var card = btn.closest(".product-card");
    if (!card) return;
    var sku = card.getAttribute("data-sku") || "";
    var cta = btn.getAttribute("data-cta") || "request";
    if (cta === "request" && cartEl) {
      if (cart.indexOf(sku) < 0) cart.push(sku);
      renderCart();
      var contact = document.getElementById("contact");
      if (contact) contact.scrollIntoView({ behavior: "smooth" });
      return;
    }
    var contact = document.getElementById("contact");
    if (contact) contact.scrollIntoView({ behavior: "smooth" });
  });
})();
"""
