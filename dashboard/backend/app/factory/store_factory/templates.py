"""Niche → theme tokens + section set for AI Store storefronts.

Premium Generation: colors/typography resolve through Design Engine;
category themes keep shop copy, demo products and warm backgrounds.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.factory.store_factory.design_bridge import (
    StoreVisualPreset,
    resolve_store_design,
    store_category_to_niche_id,
    store_colors_from_tokens,
    visual_preset_for_niche,
)


@dataclass(frozen=True)
class StoreTheme:
    template_id: str
    primary: str
    secondary: str
    accent: str
    background: str
    surface: str
    text: str
    muted: str
    hero_eyebrow: str
    hero_cta: str
    sections: tuple[str, ...] = (
        "hero",
        "featured",
        "catalog_teaser",
        "trust",
        "footer",
    )
    demo_product_names: tuple[str, ...] = ()
    category_labels: tuple[str, ...] = ()


_CATEGORY_THEMES: dict[str, StoreTheme] = {
    "clothing": StoreTheme(
        template_id="niche_clothing",
        primary="#f5e6d8",
        secondary="#2a211c",
        accent="#e07a3d",
        background="#14110f",
        surface="#1c1815",
        text="#faf7f2",
        muted="#d2c4b4",
        hero_eyebrow="New season",
        hero_cta="Shop collection",
        demo_product_names=(
            "Classic Tee",
            "Linen Shirt",
            "City Jacket",
            "Everyday Trousers",
            "Canvas Tote",
            "Wool Overshirt",
            "Relaxed Chinos",
            "Merino Crew",
            "Denim Jacket Soft",
            "Wide Leg Pants",
            "Silk Camisole",
            "Tailored Blazer",
            "Cashmere Scarf",
            "Leather Belt",
            "Sneaker Clean",
            "Ankle Boot",
            "Hoodie Soft",
            "Pleated Skirt",
            "Oxford Shirt",
            "Gift Card Soft",
        ),
        category_labels=("Jackets", "Shirts", "Trousers", "Accessories"),
    ),
    "electronics": StoreTheme(
        template_id="niche_electronics",
        primary="#93c5fd",
        secondary="#152033",
        accent="#3b82f6",
        background="#0c1219",
        surface="#141c28",
        text="#f1f5f9",
        muted="#a8bdd4",
        hero_eyebrow="Tech essentials",
        hero_cta="Browse devices",
        demo_product_names=(
            "Wireless Earbuds",
            "USB-C Hub",
            "Smart Watch",
            "Portable Charger",
            "Desk Lamp LED",
            "Noise Cancelling Headphones",
            "Mechanical Keyboard",
            "4K Webcam",
            "SSD Portable 1TB",
            "Laptop Stand Aluminum",
            "USB Microphone",
            "Wireless Mouse",
            "Monitor Arm",
            "Cable Kit Pro",
            "Smart Plug Duo",
            "Bluetooth Speaker",
            "Power Bank 20k",
            "Tablet Sleeve",
            "Hub Dock Station",
            "Ring Light Mini",
        ),
        category_labels=("Audio", "Wearables", "Accessories", "Power"),
    ),
    "auto": StoreTheme(
        template_id="niche_auto",
        primary="#fca5a5",
        secondary="#1c1518",
        accent="#ef4444",
        background="#101218",
        surface="#181c24",
        text="#f8fafc",
        muted="#b8c0cc",
        hero_eyebrow="Parts & care",
        hero_cta="Find parts",
        demo_product_names=(
            "Oil Filter Kit",
            "Car Cover",
            "LED Headlight Set",
            "Floor Mats",
            "Jump Starter",
            "Tire Inflator",
            "Cabin Filter",
            "Wiper Blades Pro",
            "Trunk Organizer",
            "Phone Mount Mag",
            "Detailing Spray",
            "Wheel Brush Set",
            "OBD Scanner",
            "Seat Organizer",
            "Emergency Kit",
            "Ceramic Coat",
            "Air Freshener Soft",
            "Tool Bag Soft",
            "Battery Tender",
            "Cargo Net",
        ),
        category_labels=("Filters", "Lighting", "Interior", "Tools"),
    ),
    "beauty": StoreTheme(
        template_id="niche_beauty",
        primary="#f9a8d4",
        secondary="#2a1824",
        accent="#ec4899",
        # Premium-grade atmosphere — never flat white shop canvas
        background="#141016",
        surface="#1c141c",
        text="#faf5f7",
        muted="#d4b8c6",
        hero_eyebrow="Care routine",
        hero_cta="Discover products",
        demo_product_names=(
            "Cuticle Oil Rose",
            "Gel Polish Nude",
            "Brow Lamination Kit",
            "Lash Serum Soft",
            "Massageöl Lavendel",
            "Handcreme Samt",
            "Nail Strengthener",
            "Augenbrauen-Stift Soft",
            "Wimpernserum Pro",
            "Pediküre-Öl Set",
            "Spa Handmaske",
            "Lippenöl Gloss",
            "Gesichtsöl Glow",
            "Körperbutter Rose",
            "Maniküre-Feile Keramik",
            "Nagelöl Tropfen",
            "Brow Mapping Gel",
            "Lash Cleanser",
            "Massagekerze Soft",
            "Professional Base Coat",
            "Top Coat Gloss",
            "Augenpads Kühl",
            "Ritual Box Atelier",
            "Zertifikat Gutschein",
        ),
        category_labels=("Nägel", "Brauen", "Wimpern", "Massage", "Pflege"),
    ),
    "psychology": StoreTheme(
        template_id="niche_psychology",
        primary="#5b7c6e",
        secondary="#24302b",
        accent="#c9b8a6",
        # Virtus-grade atmosphere — never flat white shop canvas
        background="#141a17",
        surface="#1c2420",
        text="#f5f5f4",
        muted="#a8b5ae",
        hero_eyebrow="Digitale Begleitung",
        hero_cta="Programme entdecken",
        demo_product_names=(
            "Online-Erstgespräch (60 Min)",
            "Geschenk-Gutschein Beratung",
            "Selbstfürsorge-Kurs (4 Wochen)",
            "Abend-Meditation Audio",
            "Arbeitsheft Emotionen",
            "Checkliste Erstgespräch",
            "Live-Webinar Burnout",
            "Monats-Abo Praxisimpulse",
            "Paar-Session Online",
            "Schlaf-Ritual Audio",
            "Journaling Starter Kit",
            "Atemübungen Pack",
            "Stress-Reset Kurs",
            "Familien-Gutschein",
            "Wochenimpuls PDF",
            "Abendgruppe Live",
        ),
        category_labels=("Beratung", "Kurse", "Audio", "Materialien", "Gutscheine"),
    ),
    "jewelry": StoreTheme(
        template_id="niche_jewelry",
        primary="#e7e5e4",
        secondary="#292524",
        accent="#d4a574",
        background="#12100e",
        surface="#1c1917",
        text="#fafaf9",
        muted="#c4b5a0",
        hero_eyebrow="Fine details",
        hero_cta="View pieces",
        demo_product_names=(
            "Gold Hoop Earrings",
            "Silver Chain",
            "Pearl Studs",
            "Signet Ring",
            "Bracelet Set",
            "Layered Necklace",
            "Cuff Bracelet",
            "Drop Earrings",
            "Minimal Ring Duo",
            "Charm Pendant",
            "Twisted Band",
            "Anklet Soft",
            "Brooch Vintage",
            "Ear Cuff Set",
            "Locket Heart",
            "Stacking Rings",
            "Bar Necklace",
            "Gem Studs",
            "Chain Bracelet",
            "Gift Pouch Set",
        ),
        category_labels=("Earrings", "Necklaces", "Rings", "Bracelets"),
    ),
    "accessories": StoreTheme(
        template_id="niche_accessories",
        primary="#e7e5e4",
        secondary="#1f1c18",
        accent="#c9a227",
        background="#12100e",
        surface="#1a1714",
        text="#fafaf9",
        muted="#c4b5a0",
        hero_eyebrow="Curated details",
        hero_cta="Shop accessories",
        demo_product_names=(
            "Leather Card Holder",
            "Silk Scarf Soft",
            "Minimal Watch Band",
            "Canvas Belt",
            "Sunglasses Case",
            "Key Fob Brass",
            "Travel Pouch",
            "Hair Clip Set",
            "Phone Strap Cord",
            "Compact Mirror",
            "Wallet Slim",
            "Tote Mini",
            "Cap Soft Wool",
            "Gloves Touch",
            "Umbrella Compact",
            "Passport Sleeve",
            "Ear Cuff Duo",
            "Pin Badge Set",
            "Gift Wrap Kit",
            "Desk Tray Brass",
            "Notebook Softcover",
            "Candle Travel Tin",
            "Sock Bundle",
            "Lanyard Everyday",
        ),
        category_labels=("Bags", "Wear", "Travel", "Gifts", "Desk"),
    ),
    "furniture": StoreTheme(
        template_id="niche_furniture",
        primary="#e7d5c0",
        secondary="#2a221c",
        accent="#c2783a",
        background="#16120e",
        surface="#1f1a15",
        text="#faf6f1",
        muted="#d2c0ae",
        hero_eyebrow="Home & living",
        hero_cta="Explore furniture",
        demo_product_names=(
            "Oak Side Table",
            "Linen Cushion",
            "Floor Lamp",
            "Storage Shelf",
            "Ceramic Vase",
            "Walnut Desk",
            "Boucle Armchair",
            "Wool Throw",
            "Mirror Round",
            "Bookcase Slim",
            "Candle Stand",
            "Rug Soft Weave",
            "Dining Chair Pair",
            "Nightstand Mini",
            "Plant Stand",
            "Wall Hook Set",
            "Tray Oak",
            "Sofa Throw Pillow",
            "Pendant Light",
            "Entry Bench",
        ),
        category_labels=("Tables", "Lighting", "Textiles", "Decor"),
    ),
    "food": StoreTheme(
        template_id="niche_food",
        primary="#86efac",
        secondary="#1a2e22",
        accent="#4ade80",
        background="#0f1612",
        surface="#162019",
        text="#f0fdf4",
        muted="#b7d4c0",
        hero_eyebrow="Fresh selection",
        hero_cta="Order now",
        demo_product_names=(
            "Organic Honey",
            "Artisan Bread",
            "Olive Oil",
            "Spice Mix",
            "Tea Sampler",
            "Wildflower Jam",
            "Dark Chocolate Bar",
            "Herb Salt Blend",
            "Cold Press Juice",
            "Granola Crunch",
            "Pasta Bronze Cut",
            "Balsamic Glaze",
            "Coffee Beans Roast",
            "Herbal Infusion",
            "Nut Butter Jar",
            "Pickle Trio",
            "Cheese Cracker Box",
            "Seasonal Fruit Box",
            "Soup Broth Pack",
            "Baking Flour Mix",
            "Maple Syrup",
            "Chili Oil Drop",
            "Gift Basket Small",
            "Weekly Pantry Box",
        ),
        category_labels=("Pantry", "Bakery", "Oils", "Tea", "Gifts"),
    ),
    "handwerk": StoreTheme(
        template_id="niche_handwerk",
        primary="#fbbf24",
        secondary="#2a2114",
        accent="#f59e0b",
        background="#16120a",
        surface="#1f1a10",
        text="#fffbeb",
        muted="#e8d4a8",
        hero_eyebrow="Handwerk & Qualität",
        hero_cta="Produkte ansehen",
        demo_product_names=(
            "Werkzeug-Set Pro",
            "Holzschutz Öl",
            "Präzisionsmaß",
            "Arbeitshandschuhe",
            "Montage-Kit",
            "Schraubendreher Set",
            "Wasserwaage Digital",
            "Dübel-Sortiment",
            "Sägeblatt Fine",
            "Schutzbrille Clear",
            "Knieschoner Soft",
            "Werkzeugtasche",
            "Bit-Set Magnet",
            "Abdeckfolie Rolle",
            "Fugenmesser",
            "Steckschlüssel Set",
            "Lackrolle Pro",
            "Cutter Soft Grip",
            "Messlatte Alu",
            "Schraubzwingen Duo",
        ),
        category_labels=("Werkzeug", "Material", "Schutz", "Kits"),
    ),
    "dachreinigung": StoreTheme(
        template_id="niche_dachreinigung",
        primary="#93c5e8",
        secondary="#1a2430",
        accent="#3b82c4",
        background="#0f1720",
        surface="#162029",
        text="#f0f7fc",
        muted="#a8c0d4",
        hero_eyebrow="Dach & Fassade",
        hero_cta="Zubehör ansehen",
        demo_product_names=(
            "Hochdrucklanze Pro",
            "Dachziegel-Reiniger",
            "Moosentferner Konzentrat",
            "Sicherheitsgurt Set",
            "Teleskopstange 6m",
            "Imprägnierung Dach",
            "Rinnenreiniger Set",
            "Schutzanzug Wetter",
            "Schaumlanze Soft",
            "Fassadenbürste Soft",
            "Algenblocker Liter",
            "Steiger-Gurt Comfort",
            "Wasserfilter Kartusche",
            "Dichtmasse Rinne",
            "Antirutsch-Schuhe",
            "Kamera-Inspektion Kit",
            "Dachlatte Ersatz",
            "Laubschutz Gitter",
            "Wartungsvertrag Digital",
            "Geschenkgutschein Service",
        ),
        category_labels=("Reinigung", "Schutz", "Sicherheit", "Wartung"),
    ),
    "zaunbau": StoreTheme(
        template_id="niche_zaunbau",
        primary="#d97706",
        secondary="#2a2118",
        accent="#b45309",
        background="#16120e",
        surface="#1f1a14",
        text="#fffbeb",
        muted="#e8d4a8",
        hero_eyebrow="Zäune & Tore",
        hero_cta="Material wählen",
        demo_product_names=(
            "Zaunpfosten Holz",
            "Doppelstabmatte 8/6/8",
            "Gartentor 100cm",
            "Betonfundament Set",
            "Sichtschutzstreifen",
            "Pfostenträger feuerverzinkt",
            "Maschendraht Rolle",
            "Torantrieb Starter",
            "Latte Lärche 2m",
            "Schrauben-Sortiment Outdoor",
            "Beschlag Set Tor",
            "Farblasur Zaun",
            "Gabionen-Korb 100cm",
            "Einfahrtstor 3m",
            "Abstandhalter Set",
            "Erdanker Pro",
            "Zaunlatte Composite",
            "Schloss Zylinder Outdoor",
            "Montage-Clip Pack",
            "Planungs-Gutschein",
        ),
        category_labels=("Zäune", "Tore", "Pfosten", "Zubehör"),
    ),
    "gartenpflege": StoreTheme(
        template_id="niche_gartenpflege",
        primary="#86efac",
        secondary="#1a2e22",
        accent="#22c55e",
        background="#0f1612",
        surface="#162019",
        text="#f0fdf4",
        muted="#b7d4c0",
        hero_eyebrow="Garten & Pflege",
        hero_cta="Pflegeprodukte",
        demo_product_names=(
            "Rasensamen Premium",
            "Heckenschere Akku",
            "Mulch Rindenstück",
            "Gartenschlauch 20m",
            "Dünger Langzeit",
            "Laubsauger Kombi",
            "Hochbeet Bausatz",
            "Gartenschere Bypass",
            "Bewässerungs-Timer",
            "Unkrautvlies Rolle",
            "Komposter 300L",
            "Pflanzenstütze Set",
            "Rasenkante Metall",
            "Erde Bio 40L",
            "Gartengeräte-Set",
            "Vogelhaus Design",
            "Teichnetz Fein",
            "Winterschutz Vlies",
            "Samen-Mix Wildblumen",
            "Garten-Gutschein",
        ),
        category_labels=("Rasen", "Hecke", "Geräte", "Pflege"),
    ),
    "cleaning": StoreTheme(
        template_id="niche_cleaning",
        primary="#ecfeff",
        secondary="#083344",
        accent="#06b6d4",
        background="#0c1920",
        surface="#132430",
        text="#ecfeff",
        muted="#a5f3fc",
        hero_eyebrow="Profi-Pflege",
        hero_cta="Reinigungsmittel kaufen",
        demo_product_names=(
            "Glasreiniger Pro",
            "Bodenpflege Set",
            "Desinfektion Spray",
            "Mikrofasertücher 12er",
            "Poliermaschine Pad",
            "Fensterwischer Deluxe",
            "Büro-Küchenkit",
            "Anti-Kalk Bad",
            "Staubsaugerbeutel",
            "Handschuhe Nitril",
            "Duftneutral Konzentrat",
            "Schwamm Premium",
        ),
        category_labels=("Glas", "Boden", "Hygiene", "Zubehör"),
    ),
    "auto_detailing": StoreTheme(
        template_id="niche_detailing",
        primary="#fafafa",
        secondary="#0a0a0a",
        accent="#d4af37",
        background="#050505",
        surface="#141414",
        text="#fafafa",
        muted="#a1a1aa",
        hero_eyebrow="Showroom Finish",
        hero_cta="Detailing Shop",
        demo_product_names=(
            "Keramikversiegelung",
            "Lackpolitur Set",
            "Felgenreiniger",
            "Innenraum Foam",
            "Mikrofasertuch Gold",
            "Clay Bar Kit",
            "Quick Detailer",
            "Lederpflege",
            "Scheibenversiegelung",
            "Pad Set Cutting",
            "Wax Soft",
            "Spray Sealant",
        ),
        category_labels=("Lack", "Innenraum", "Felgen", "Kits"),
    ),
    "orthodontics": StoreTheme(
        template_id="niche_ortho",
        primary="#f0fdfa",
        secondary="#134e4a",
        accent="#14b8a6",
        background="#042f2e",
        surface="#0f3d3a",
        text="#f0fdfa",
        muted="#99f6e4",
        hero_eyebrow="Aligner Care",
        hero_cta="Pflegeprodukte",
        demo_product_names=(
            "Aligner Reinigungstabletten",
            "Reise-Case",
            "Interdentalbürsten",
            "Mundspülung Soft",
            "Wachssticks",
            "Putztasche Clinic",
            "Zahnseide Ortho",
            "Spiegel Pocket",
            "Chewies Soft",
            "Hygiene Spray",
            "Aufbewahrungsbox",
            "Starter Care Kit",
        ),
        category_labels=("Reinigung", "Reise", "Hygiene", "Kits"),
    ),
    "books": StoreTheme(
        template_id="niche_books",
        primary="#f5f0e8",
        secondary="#1c1917",
        accent="#b45309",
        background="#1c1917",
        surface="#292524",
        text="#fafaf9",
        muted="#d6d3d1",
        hero_eyebrow="Neue Titel",
        hero_cta="Bücher entdecken",
        demo_product_names=(
            "Essay Softbound",
            "Roman Hardcover",
            "Fotoband City",
            "Notizbuch Leinen",
            "Kinderbuch",
            "Kochbuch Seasonal",
            "Business Brief",
            "Poesie Slim",
            "Reiseführer DE",
            "Kunstkatalog",
            "Lesezeichen Set",
            "Geschenkbox Buch",
        ),
        category_labels=("Fiction", "Sachbuch", "Kunst", "Geschenk"),
    ),
    "it_parts": StoreTheme(
        template_id="niche_it_parts",
        primary="#e0f2fe",
        secondary="#0f172a",
        accent="#38bdf8",
        background="#020617",
        surface="#0f172a",
        text="#f8fafc",
        muted="#94a3b8",
        hero_eyebrow="Tech Parts",
        hero_cta="Ersatzteile",
        demo_product_names=(
            "SSD 1TB NVMe",
            "RAM 16GB Kit",
            "Laptop Akku Pro",
            "USB-C Hub",
            "Wärmeleitpaste",
            "Tastaturmodul",
            "Netzteil 90W",
            "Displaykabel",
            "Lüfter Quiet",
            "Werkzeug ESD",
            "Dock Station",
            "Backup Drive",
        ),
        category_labels=("Speicher", "Strom", "Notebook", "Werkzeug"),
    ),

    "solar": StoreTheme(
        template_id="niche_solar",
        primary="#fbbf24",
        secondary="#0c1a12",
        accent="#f59e0b",
        background="#07140f",
        surface="#0f1f18",
        text="#fefce8",
        muted="#c5d9b8",
        hero_eyebrow="Solar & Energie",
        hero_cta="Produkte entdecken",
        demo_product_names=(
            "PV Modul 400W",
            "Wechselrichter Hybrid",
            "Speicher 10kWh",
            "Wallbox 11kW",
            "Optimierer Set",
            "Montageschiene",
            "DC Kabel Kit",
            "Monitoring Stick",
            "Unterkonstruktion",
            "Überspannungsschutz",
            "Backup Box",
            "Smart Meter",
            "Mikro-WR Duo",
            "Halterung Flachdach",
            "Erdungskit",
            "Reinigungsset PV",
            "Notstrom Umschalter",
            "Energie-Monitor",
            "Kabelkanal Solar",
            "Wartungs-Check",
        ),
        category_labels=("Module", "Speicher", "Wallbox", "Zubehör"),
    ),
    "auto_parts": StoreTheme(
        template_id="niche_auto_parts",
        primary="#fca5a5",
        secondary="#1c1518",
        accent="#ef4444",
        background="#101218",
        surface="#181c24",
        text="#f8fafc",
        muted="#b8c0cc",
        hero_eyebrow="Ersatzteile & Pflege",
        hero_cta="Teile finden",
        demo_product_names=(
            "Ölfilter Kit",
            "Bremsbeläge Set",
            "LED Scheinwerfer",
            "Zündkerzen Pack",
            "Luftfilter Sport",
            "Wischerblätter Pro",
            "Batterie AGM",
            "Keilriemen",
            "Stoßdämpfer",
            "Radmuttern Set",
            "Motoröl 5W30",
            "Kühlmittel",
            "Kabinenfilter",
            "Starthilfekabel",
            "Wagenheber",
            "Diagnose OBD",
            "Felgenreiniger",
            "Reifendruck Set",
            "Anhängerkupplung",
            "Warndreieck Premium",
        ),
        category_labels=("Filter", "Bremsen", "Elektrik", "Pflege"),
    ),
    "maler": StoreTheme(
        template_id="niche_maler",
        primary="#fdba74",
        secondary="#2a1810",
        accent="#ea580c",
        background="#140e0a",
        surface="#1f1610",
        text="#fff7ed",
        muted="#e8c4a0",
        hero_eyebrow="Farbe & Oberfläche",
        hero_cta="Sortiment ansehen",
        demo_product_names=(
            "Innenfarbe Matt",
            "Fassadenfarbe",
            "Lack Seidenmatt",
            "Grundierung Tief",
            "Rollerset Pro",
            "Pinsel Fein",
            "Abdeckfolie",
            "Malerkrepp",
            "Spachtelmasse",
            "Lasur Holz",
            "Anti-Schimmel",
            "Deckenweiß",
            "Akzentfarbe Terra",
            "Sprühfarbe",
            "Schleifpapier Pack",
            "Farbwanne",
            "Teleskopstange",
            "Fugenweiß",
            "Schutzanzug",
            "Farbfächer Guide",
        ),
        category_labels=("Farben", "Lacke", "Werkzeug", "Zubehör"),
    ),
    "optics": StoreTheme(
        template_id="niche_optics",
        primary="#93c5fd",
        secondary="#152033",
        accent="#3b82f6",
        background="#0c1219",
        surface="#141c28",
        text="#f1f5f9",
        muted="#a8bdd4",
        hero_eyebrow="Optik & Sehen",
        hero_cta="Brillen entdecken",
        demo_product_names=(
            "Fassungs-Klassik",
            "Sportbrille UV",
            "Gleitsicht Premium",
            "Kontaktlinsen Monat",
            "Reinigungsspray",
            "Mikrofasertuch",
            "Etui Leder",
            "Blaulicht-Filter",
            "Sonnenclip",
            "Kinderfassung",
            "Titanrahmen Leicht",
            "Lesbrille +2.0",
            "Pflegelösung",
            "Anti-Beschlag",
            "Ersatzbügel",
            "Nasepad Set",
            "Sehstärken-Check",
            "Screen Brille",
            "Polarisiert Pro",
            "Geschenk-Voucher",
        ),
        category_labels=("Fassungen", "Gläser", "Linsen", "Pflege"),
    ),
    "other": StoreTheme(
        template_id="niche_general",
        primary="#e7e5e4",
        secondary="#1c1917",
        accent="#34d399",
        background="#121416",
        surface="#1a1d20",
        text="#fafaf9",
        muted="#c4c0bb",
        hero_eyebrow="Featured",
        hero_cta="Shop now",
        demo_product_names=(
            "Starter Pack",
            "Best Seller",
            "Gift Set",
            "Everyday Essential",
            "Limited Edition",
            "Bundle Deal",
            "Seasonal Pick",
            "Member Favorite",
            "Travel Size",
            "Premium Edition",
            "Value Multipack",
            "Weekend Kit",
            "Desk Essential",
            "Soft Launch",
            "Archive Drop",
            "Curated Trio",
            "Signature Item",
            "Restock Classic",
            "Gift Card Soft",
            "Discovery Box",
        ),
        category_labels=("New", "Bestsellers", "Gifts", "Essentials"),
    ),
}

# Style overrides must keep warm non-white page backgrounds (Visual Design Rule).
_STYLE_OVERRIDES: dict[str, dict[str, str]] = {
    "minimal": {"accent": "#525252", "background": "#f5f2ed", "secondary": "#ebe7e1", "surface": "#faf8f5"},
    "luxury": {"accent": "#a16207", "primary": "#0c0a09", "background": "#f5f0e8", "surface": "#faf6f0"},
    "tech": {"accent": "#2563eb", "primary": "#0f172a", "background": "#eef2f6", "surface": "#f5f8fb"},
    "bold": {"accent": "#e11d48", "primary": "#18181b", "background": "#f5f0ec"},
    "warm": {"accent": "#c2410c", "background": "#fff4e8", "secondary": "#ffe8d4", "surface": "#fffaf5"},
    "graphite": {"accent": "#64748b", "primary": "#0f172a", "background": "#eef1f4", "surface": "#f5f7f9"},
    "storefront_light": {"background": "#f7f3ee", "accent": "#059669", "surface": "#faf7f2"},
}

_PURE_WHITE = frozenset({"#fff", "#ffffff", "white"})
_DARK_CANVAS_BG = frozenset(
    {
        "#141a17",
        "#0c0a09",
        "#09090b",
        "#121816",
        "#141016",
        "#12100e",
        "#0f1612",
        "#121416",
        "#1a1d20",
    }
)


def _warm_bg(value: str, fallback: str = "#f5f1eb") -> str:
    v = (value or "").strip().lower()
    if v in _PURE_WHITE or not v:
        return fallback
    return value


def _is_dark_canvas(bg: str) -> bool:
    v = (bg or "").strip().lower()
    if v in _DARK_CANVAS_BG:
        return True
    if not v.startswith("#") or len(v) not in (4, 7):
        return False
    h = v[1:]
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    try:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except ValueError:
        return False
    # Relative luminance — dark shop atmosphere
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) < 70


def _expand_product_names(names: list[str], target: int) -> list[str]:
    if target <= len(names):
        return names[:target]
    out = list(names)
    i = 0
    while len(out) < target:
        base = names[i % len(names)]
        variant = (i // len(names)) + 2
        out.append(f"{base} · {variant}")
        i += 1
    return out


@dataclass
class ResolvedTemplate:
    template_id: str
    theme: StoreTheme
    colors: dict[str, str] = field(default_factory=dict)
    sections: tuple[str, ...] = ()
    demo_products: list[dict[str, Any]] = field(default_factory=list)
    category_labels: tuple[str, ...] = ()
    niche_id: str = "generic"
    visual_preset: StoreVisualPreset | None = None


class StoreTemplateRegistry:
    """Map shop_brief.category / style → Design Engine + storefront adaptation."""

    def resolve(self, brief: dict[str, Any]) -> ResolvedTemplate:
        category = str(brief.get("category") or "other").strip().lower()
        base = _CATEGORY_THEMES.get(category) or _CATEGORY_THEMES["other"]
        style = str(brief.get("style") or "modern").strip().lower()
        if style == "minimalism":
            style = "minimal"

        package_id = str(brief.get("package_id") or "business").strip().lower() or "business"
        niche_id = store_category_to_niche_id(category)
        tokens, preset, _pack = resolve_store_design(category, package_id=package_id)

        # Design Engine hues + store backgrounds (dark niches keep Premium atmosphere).
        colors = store_colors_from_tokens(
            tokens,
            warm_background=base.background,
            warm_surface=base.surface,
            warm_secondary=base.secondary,
        )
        dark_canvas = _is_dark_canvas(base.background) or niche_id == "psychology"
        if dark_canvas:
            # Lock invented dark brand palette — never let light Design Engine ink win.
            colors["text"] = base.text
            colors["muted"] = base.muted
            colors["primary"] = base.primary
            colors["accent"] = base.accent
            colors["secondary"] = base.secondary
            colors["surface"] = base.surface
            colors["background"] = base.background
        # Keep category-tuned text when Design Engine ink is too dark for fashion.
        if category == "clothing" and not dark_canvas:
            colors["primary"] = "#1a1a1a"
            colors["text"] = "#1a1a1a"
            colors["accent"] = tokens.primary if tokens.primary.startswith("#") else base.accent

        if not dark_canvas:
            for key, val in (_STYLE_OVERRIDES.get(style) or {}).items():
                colors[key] = val
            colors["background"] = _warm_bg(colors["background"], base.background)
            colors["surface"] = _warm_bg(colors.get("surface", base.surface), base.surface)
        colors["hero_gradient"] = tokens.hero_gradient

        custom = str(brief.get("color_scheme") or brief.get("color") or "").strip()
        if custom.startswith("#") and len(custom) in (4, 7):
            colors["accent"] = custom

        currency = str(brief.get("currency") or "EUR").upper()
        symbol = "€" if currency == "EUR" else ("$" if currency == "USD" else currency + " ")
        prices = [
            12.90,
            19.90,
            24.90,
            29.90,
            34.90,
            39.90,
            49.00,
            59.00,
            69.00,
            79.00,
            89.00,
            99.00,
            119.00,
            129.00,
            149.00,
            159.00,
            179.00,
            199.00,
        ]
        old_prices = [p + 10 for p in prices]
        names = list(base.demo_product_names) or list(_CATEGORY_THEMES["other"].demo_product_names)
        catalog_raw = brief.get("catalog_size") or brief.get("product_count")
        try:
            catalog_n = int(catalog_raw) if catalog_raw is not None else None
        except (TypeError, ValueError):
            catalog_n = None
        tier_default = {"basic": 12, "business": 18, "premium": 24, "starter": 12}.get(
            package_id, 18
        )
        target = max(8, min(36, catalog_n or tier_default))
        names = _expand_product_names(names, target)
        count = len(names)
        demo: list[dict[str, Any]] = []
        for i, name in enumerate(names[:count]):
            price = prices[i % len(prices)]
            old = old_prices[i % len(old_prices)]
            badge = ""
            if i == 0:
                badge = "NEW"
            elif i == 2:
                badge = "HIT"
            elif i % 5 == 1:
                badge = "SALE"
            meta = ""
            if preset.show_specs:
                meta = f"SKU-{1000 + i}"
            demo.append(
                {
                    "id": f"demo-{i + 1}",
                    "name": name,
                    "price": price,
                    "price_label": f"{symbol}{price:.2f}",
                    "old_price": old if badge == "SALE" else None,
                    "old_price_label": f"{symbol}{old:.2f}" if badge == "SALE" else "",
                    "badge": badge,
                    "rating": 4.2 + (i % 4) * 0.2,
                    "reviews": 12 + i * 7,
                    "stock": "In stock" if i % 7 != 3 else "Few left",
                    "category": category,
                    "card_meta": meta,
                    "image_slot": preset.image_slots.product,
                }
            )

        return ResolvedTemplate(
            template_id=base.template_id,
            theme=base,
            colors=colors,
            sections=base.sections,
            demo_products=demo,
            category_labels=base.category_labels
            or _CATEGORY_THEMES["other"].category_labels,
            niche_id=niche_id,
            visual_preset=preset or visual_preset_for_niche(niche_id),
        )
