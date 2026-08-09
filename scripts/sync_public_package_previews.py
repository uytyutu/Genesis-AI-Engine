"""Sync public Demo Gallery from current Factory / Store engines.

Writes into:
  dashboard/frontend/public/package-previews/sites/<basic|business|premium>/<niche>/
  dashboard/frontend/public/package-previews/stores/<store>/

Replaces thin hand stubs with Design Engine + Visual Intelligence output.
Does NOT invent a new generator — calls existing FactoryService / write_storefront.

Run from repo root:
  py -3.12 scripts/sync_public_package_previews.py
  py -3.12 scripts/sync_public_package_previews.py --tiers basic,business,premium --websites-only
  py -3.12 scripts/sync_public_package_previews.py --websites-only
  py -3.12 scripts/sync_public_package_previews.py --stores-only
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "dashboard" / "backend"
PUBLIC = ROOT / "dashboard" / "frontend" / "public" / "package-previews"
sys.path.insert(0, str(BACKEND))

from app.factory.factory_service import FactoryService  # noqa: E402

WEBSITE_CASES: list[dict] = [
    {
        "folder": "dental",
        "niche": "dental",
        "business_name": "SmileCare Praxis",
        "city": "München",
        "description": (
            "SmileCare Praxis München — Zahnarztpraxis, Prophylaxe, Implantate, "
            "Ästhetik, schmerzarme Behandlung"
        ),
        "services_list": ["Prophylaxe", "Implantate", "Bleaching", "Füllungen"],
        "phone": "+49 89 1234567",
        "email": "kontakt@smilecare-demo.example.de",
        "advantages": ["Schmerzarme Behandlung", "Klare Kostenpläne", "Moderne Praxis"],
        "dream_brief": {
            "who_is_company": "Moderne Praxis: Aufklärung vor Bohrer, klare Kosten, ruhige Behandlung.",
            "commercial_idea": "Präzision, die Ruhe gibt.",
            "problem_before": "Zahnarztangst und unklare Kosten — Sie wollen wissen, was passiert.",
            "client_story": "Zähne ohne Angst — und Kosten, die Sie vorher kennen.",
            "clients_who": "Familien und Berufstätige in München",
            "why_choose_us": "Schmerzarm, transparente Pläne, moderne Technik",
            "brand_feeling": "Hell, ruhig, präzise",
            "style": "clinic",
            "client_fear": "Überraschungskosten und Schmerzen",
            "main_promise": "Zähne ohne Angst — und Kosten, die Sie vorher kennen.",
        },
    },
    {
        "folder": "psychology",
        "niche": "psychology",
        "business_name": "Praxis Klarheit",
        "city": "Hamburg",
        "description": (
            "Praxis Klarheit Hamburg — Psychologische Beratung, Psychotherapie, "
            "Erstgespräch, Online und vor Ort, Burnout-Prävention"
        ),
        "services_list": [
            "Einzeltherapie",
            "Erstgespräch",
            "Online-Beratung",
            "Paartherapie",
            "Burnout-Prävention",
        ],
        "phone": "+49 40 99887766",
        "email": "kontakt@praxis-klarheit-demo.example.de",
        "advantages": [
            "Vertraulich & ruhig",
            "Online und vor Ort",
            "Transparente Honorare",
        ],
        "dream_brief": {
            "who_is_company": (
                "Ruhige Praxis: Schutzraum, Tempo des Menschen, "
                "klare Honorare, keine Wellness-Floskeln."
            ),
            "commercial_idea": "Ein Ort, an dem es ruhiger wird.",
            "problem_before": (
                "Sie tragen etwas mit sich, das schwer bleibt — "
                "und wissen nicht, ob ein Gespräch überhaupt hilft."
            ),
            "client_story": (
                "Manchmal reicht ein Gespräch, "
                "um wieder Boden unter den Füßen zu spüren."
            ),
            "clients_who": "Erwachsene und Paare in Hamburg, die Ruhe und Klarheit suchen",
            "why_choose_us": "Vertraulicher Raum, klare Honorare, Online und vor Ort",
            "brand_feeling": "Warm, ruhig, professionell — wie ein sicherer Ort",
            "admired_companies": "Ruhige Praxen mit editorialem Auftritt",
            "style": "warm_family",
            "client_fear": "Nicht ernst genommen zu werden / Wartelisten ohne Klarheit",
            "main_promise": "Ein Ort, an dem es ruhiger wird.",
        },
    },
    {
        "folder": "law",
        "niche": "law",
        "business_name": "Kanzlei Bergmann",
        "city": "Frankfurt",
        "description": (
            "Kanzlei Bergmann Frankfurt — Rechtsanwalt, Wirtschaftsrecht, "
            "Vertragsprüfung, Erstberatung"
        ),
        "services_list": ["Erstberatung", "Vertragsprüfung", "Vertretung", "Verhandlungen"],
        "phone": "+49 69 7778899",
        "email": "kontakt@kanzlei-bergmann-demo.example.de",
        "advantages": ["Vertraulich", "Klare Honorare", "Feste Ansprechpartner"],
        "dream_brief": {
            "who_is_company": (
                "Boutique-Kanzlei: präzise, vertraulich, ruhig-autoritär, "
                "klare Honorare, Orientierung vor Eskalation."
            ),
            "commercial_idea": "Stille. Ordnung. Kontrolle.",
            "problem_before": (
                "Die Lage wird unübersichtlich. "
                "Sie brauchen keinen Theatersaal — Sie brauchen einen Weg."
            ),
            "client_story": (
                "Wenn die Lage schwierig wird, zählt, "
                "dass jemand den Weg zur Lösung schon kennt."
            ),
            "clients_who": "KMU und Geschäftsführer in Frankfurt",
            "why_choose_us": "Klare Honorare, feste Ansprechpartner, Wirtschaftsrecht",
            "brand_feeling": "Präzise, vertrauenswürdig, ruhig-autoritär",
            "admired_companies": "Boutique-Kanzleien mit klarer Fassade",
            "style": "legal",
            "client_fear": "Undurchsichtige Kosten und lange Antworten",
            "main_promise": "Stille. Ordnung. Kontrolle.",
        },
    },
    {
        "folder": "restaurant",
        "niche": "restaurant",
        "business_name": "Trattoria Luna",
        "city": "Köln",
        "description": (
            "Trattoria Luna Köln — Restaurant, Mittagstisch, Abendkarte, "
            "Reservierung, Events"
        ),
        "services_list": ["Mittagstisch", "Abendkarte", "Reservierung", "Events"],
        "phone": "+49 221 4445566",
        "email": "kontakt@trattorialuna-demo.example.de",
        "advantages": ["Frische Zutaten", "Reservierung mit Bestätigung", "Allergene klar"],
        "dream_brief": {
            "who_is_company": (
                "Familiäre Trattoria: Wärme, Abendlicht, ehrliche Küche, "
                "Tisch wie bei Freunden — kein Touristen-Menü."
            ),
            "commercial_idea": "Ein Abend im italienischen Hof.",
            "problem_before": (
                "Sie wollen nicht nur essen — "
                "Sie wollen den Abend schon spüren, bevor die Karte kommt."
            ),
            "client_story": (
                "Hier beginnt der Abend nicht mit der Speisekarte, "
                "sondern mit dem Gefühl, schon in Italien zu sein."
            ),
            "clients_who": "Gäste, die in Köln ehrlich italienisch essen wollen",
            "why_choose_us": "Frische Zutaten, klare Allergene, Reservierung mit Bestätigung",
            "brand_feeling": "Warm, abendlicht, einladend — wie ein langer Tisch",
            "admired_companies": "Familiäre Trattorien mit starker Atmosphäre",
            "style": "immersive",
            "client_fear": "Touristenfalle / unklare Allergene / keine Tische",
            "main_promise": "Ein Abend im italienischen Hof.",
        },
    },
    {
        "folder": "beauty",
        "niche": "beauty",
        "business_name": "Salon Mira",
        "city": "Berlin",
        "description": (
            "Salon Mira Berlin — Friseursalon, Haarschnitt, Coloration, Balayage, Pflege"
        ),
        "services_list": ["Balayage", "Damenhaarschnitt", "Pflege", "Styling"],
        "phone": "+49 30 9876543",
        "email": "kontakt@salonmira-demo.example.de",
        "advantages": ["Online-Termine", "Premium-Produkte", "Erfahrene Stylisten"],
        "dream_brief": {
            "who_is_company": (
                "Boutique-Atelier: Beratung vor dem Schnitt, ehrliche Produkte, "
                "Alltagstauglichkeit, kein Wartesaal-Gefühl."
            ),
            "commercial_idea": "Ein Ritual der Schönheit — kein Salon.",
            "problem_before": (
                "Sie wollen keinen Wartesaal und keinen Trend-Druck — "
                "nur Zeit, die wirklich Ihnen gehört."
            ),
            "client_story": "Zeit, die nur Ihnen gehört.",
            "clients_who": "Berlinerinnen, die Farbe und Schnitt mit Ruhe wollen",
            "why_choose_us": "Online-Termine, Premium-Produkte, erfahrene Stylisten",
            "brand_feeling": "Hell, gepflegt, modern — Studio, kein Wartesaal",
            "admired_companies": "Boutique-Salons mit starkem Lookbook",
            "style": "clinic",
            "client_fear": "Überraschung nach dem Schnitt / undurchsichtige Preise",
            "main_promise": "Ein Ritual der Schönheit — kein Salon.",
        },
    },
    {
        "folder": "auto",
        "niche": "auto",
        "business_name": "Autowerkstatt Nord",
        "city": "Hamburg",
        "description": (
            "Autowerkstatt Nord Hamburg — Autowerkstatt, Diagnose, Inspektion, "
            "Reifen, Ölwechsel"
        ),
        "services_list": ["Diagnose", "Inspektion", "Reifen", "Ölwechsel"],
        "phone": "+49 40 5551212",
        "email": "kontakt@autownord-demo.example.de",
        "advantages": ["Schriftliche Diagnose", "Keine versteckten Posten", "Garantie"],
        "dream_brief": {
            "who_is_company": "Ehrliche Werkstatt: Diagnose zuerst, Preis danach, kein Theater.",
            "commercial_idea": "Technik ohne Theater.",
            "problem_before": "Das Auto streikt — und Sie fürchten die Rechnung ohne Diagnose.",
            "client_story": "Erst Diagnose, dann Preis — ohne Verkaufsdruck.",
            "clients_who": "Autobesitzer in Hamburg",
            "why_choose_us": "Schriftliche Diagnose, Garantie, keine versteckten Posten",
            "brand_feeling": "Klar, technisch, ehrlich",
            "style": "industrial",
            "client_fear": "Überraschungsrechnung",
            "main_promise": "Erst Diagnose, dann Preis — ohne Verkaufsdruck.",
        },
    },
    {
        "folder": "fitness",
        "niche": "fitness",
        "business_name": "FitBase Studio",
        "city": "Stuttgart",
        "description": (
            "FitBase Studio Stuttgart — Fitnessstudio, Personal Training, "
            "Gruppenkurse, Ernährungsberatung"
        ),
        "services_list": ["Personal Training", "Gruppenkurse", "Probetraining", "Ernährung"],
        "phone": "+49 711 3332211",
        "email": "kontakt@fitbase-demo.example.de",
        "advantages": ["Flexible Zeiten", "Moderne Geräte", "Coaches vor Ort"],
        "dream_brief": {
            "who_is_company": "Studio mit Coaches — Alltagstauglich, ohne Abo-Falle.",
            "commercial_idea": "Form mit Haltung.",
            "problem_before": "Sie wollen starten — ohne monatelanges Abo und Show.",
            "client_story": "Training, das zu Ihrem Alltag passt — nicht umgekehrt.",
            "clients_who": "Berufstätige in Stuttgart",
            "why_choose_us": "Flexible Zeiten, Coaches, Probetraining ohne Falle",
            "brand_feeling": "Energisch, klar, einladend",
            "style": "minimal",
            "client_fear": "Vertragsfalle und peinliches Probetraining",
            "main_promise": "Training, das zu Ihrem Alltag passt — nicht umgekehrt.",
        },
    },
    {
        "folder": "handwerk",
        "niche": "handwerk",
        "business_name": "Meisterbau Hoffmann",
        "city": "Leipzig",
        "description": (
            "Meisterbau Hoffmann Leipzig — Handwerksbetrieb, Renovierung, "
            "Trockenbau, Malerarbeiten, Badumbau"
        ),
        "services_list": ["Renovierung", "Trockenbau", "Malerarbeiten", "Badumbau"],
        "phone": "+49 341 8887766",
        "email": "kontakt@meisterbau-demo.example.de",
        "advantages": ["Festpreisangebot", "Pünktliche Termine", "Saubere Baustelle"],
        "dream_brief": {
            "who_is_company": "Meisterbetrieb: Festpreis, pünktlich, saubere Baustelle.",
            "commercial_idea": "Handwerk mit Haltung.",
            "problem_before": "Renovierung soll nicht im Chaos enden.",
            "client_story": "Renovierung mit Festpreis — ohne Baustellen-Chaos.",
            "clients_who": "Hausbesitzer und Bauherren in Leipzig",
            "why_choose_us": "Festpreis, pünktlich, sauber",
            "brand_feeling": "Solide, klar, zuverlässig",
            "style": "craft",
            "client_fear": "Kostenexplosion und Schmutz",
            "main_promise": "Renovierung mit Festpreis — ohne Baustellen-Chaos.",
        },
    },
    {
        "folder": "dachreinigung",
        "niche": "dachreinigung",
        "business_name": "DachKlar Service",
        "city": "Nürnberg",
        "description": (
            "DachKlar Service Nürnberg — Dachreinigung, Moosentfernung, "
            "Fassadenwäsche, Dachrinne, Imprägnierung für Einfamilienhäuser"
        ),
        "services_list": [
            "Dachreinigung",
            "Moosentfernung",
            "Fassadenwäsche",
            "Dachrinne reinigen",
            "Imprägnierung",
        ],
        "phone": "+49 911 4455667",
        "email": "kontakt@dachklar-demo.example.de",
        "advantages": ["Festpreis vor Ort", "Versichert & zertifiziert", "Vorher/Nachher Fotos"],
        "dream_brief": {
            "who_is_company": (
                "Deutsches Handwerk: Qualität, Sicherheit, Ordnung, "
                "Arbeit nach dem Regen, professionelle Technik, spürbare Zuverlässigkeit."
            ),
            "commercial_idea": "Nach dem Regen sieht das Dach wieder neu aus.",
            "problem_before": (
                "Nach dem Winter liegt Moos auf dem Dach. "
                "Sie öffnen den Browser und fürchten schon die Sanierungskosten."
            ),
            "client_story": (
                "Nach dem Winter ist das Dach voller Moos — "
                "und Sie fürchten, die Sanierung kostet Tausende."
            ),
            "clients_who": "Hausbesitzer in Nürnberg mit Moos und dunklen Ziegeln",
            "why_choose_us": "Festpreis vor Ort, versichert, Vorher/Nachher Fotos",
            "brand_feeling": "Zuverlässig, handwerklich, klar — wie ein Meisterbetrieb",
            "admired_companies": "Deutsche Handwerksbetriebe mit echten Referenzen",
            "style": "craft",
            "client_fear": "Billige Anbieter ohne Versicherung / Schäden am Dach",
            "main_promise": "Nach dem Regen sieht das Dach wieder neu aus.",
        },
    },
    {
        "folder": "zaunbau",
        "niche": "zaunbau",
        "business_name": "ZaunWerk Süd",
        "city": "Augsburg",
        "description": (
            "ZaunWerk Süd Augsburg — Zaunbau, Sichtschutz, Gartentore, "
            "Doppelstabmatten, Montage und Reparatur"
        ),
        "services_list": ["Zaunbau", "Sichtschutz", "Gartentore", "Reparatur", "Beratung vor Ort"],
        "phone": "+49 821 3344556",
        "email": "kontakt@zaunwerk-demo.example.de",
        "advantages": ["Aufmaß kostenlos", "Deutsche Qualität", "Saubere Montage"],
    },
    {
        "folder": "gartenpflege",
        "niche": "gartenpflege",
        "business_name": "Grünzeit Pflege",
        "city": "Münster",
        "description": (
            "Grünzeit Pflege Münster — Gartenpflege, Rasenschnitt, Heckenschnitt, "
            "Laubentsorgung, saisonale Betreuung für Privathäuser"
        ),
        "services_list": ["Rasenschnitt", "Heckenschnitt", "Beetpflege", "Laubentsorgung", "Jahresvertrag"],
        "phone": "+49 251 7788990",
        "email": "kontakt@gruenzeit-demo.example.de",
        "advantages": ["Zuverlässige Termine", "Ökologische Pflege", "Klarer Jahresplan"],
    },
    {
        "folder": "it",
        "niche": "computer",
        "business_name": "ByteForge IT",
        "city": "Düsseldorf",
        "description": (
            "ByteForge IT Düsseldorf — IT-Dienstleister, Managed Services, "
            "Cybersecurity, Cloud, Support für KMU"
        ),
        "services_list": ["Managed Services", "Cybersecurity", "Cloud", "Helpdesk"],
        "phone": "+49 211 6665544",
        "email": "kontakt@byteforge-demo.example.de",
        "advantages": ["SLA klar", "Schnelle Reaktion", "Deutscher Support"],
    },
    {
        "folder": "realestate",
        "niche": "realestate",
        "business_name": "WohnRaum Partner",
        "city": "München",
        "description": (
            "WohnRaum Partner München — Immobilienmakler, Verkauf, Vermietung, "
            "Bewertung, Begleitung bis Notar"
        ),
        "services_list": ["Verkauf", "Vermietung", "Bewertung", "Besichtigungen"],
        "phone": "+49 89 4443322",
        "email": "kontakt@wohnraum-demo.example.de",
        "advantages": ["Lokale Marktkenntnis", "Klare Provision", "Digitale Exposés"],
        "dream_brief": {
            "who_is_company": "Makler mit lokaler Marktkenntnis und klarer Provision.",
            "commercial_idea": "Wohnraum mit Klarheit.",
            "problem_before": "Verkauf oder Miete — ohne Exposé-Nebel.",
            "client_story": "Immobilie verkaufen — mit klarer Strategie, nicht mit Hoffnung.",
            "clients_who": "Eigentümer und Suchende in München",
            "why_choose_us": "Lokale Kenntnis, transparente Provision, digitale Exposés",
            "brand_feeling": "Ruhig, premium, klar",
            "style": "luxury",
            "client_fear": "Undurchsichtige Provision und leere Versprechen",
            "main_promise": "Immobilie verkaufen — mit klarer Strategie, nicht mit Hoffnung.",
        },
    },
    {
        "folder": "energy",
        "niche": "energy",
        "business_name": "SolarNord Energie",
        "city": "Hannover",
        "description": (
            "SolarNord Energie Hannover — Photovoltaik, Speicher, Wallbox, "
            "Planung und Montage für Haushalte und Gewerbe"
        ),
        "services_list": ["PV-Planung", "Montage", "Speicher", "Wartung"],
        "phone": "+49 511 2223344",
        "email": "kontakt@solarnord-demo.example.de",
        "advantages": ["Ertragsfokus", "Saubere Montage", "Nachbetreuung"],
        "dream_brief": {
            "who_is_company": (
                "Photovoltaik-Team aus Hannover: saubere Planung, ehrliche Erträge, "
                "Montage ohne Chaos."
            ),
            "commercial_idea": "Strom vom eigenen Dach — messbar und ruhig geplant.",
            "problem_before": "Unklare Angebote und Angst vor Fehlmontage.",
            "client_story": "Das Dach arbeitet — und die Rechnung wird kleiner.",
            "clients_who": "Haushalte und Gewerbe in der Region Hannover",
            "why_choose_us": "Ertragsfokus, saubere Montage, Nachbetreuung",
            "brand_feeling": "Klar, technisch, vertrauenswürdig",
            "style": "tech",
            "client_fear": "Überverkaufte kWp und schlechte Installation",
            "main_promise": "Das Dach arbeitet — und die Rechnung wird kleiner.",
        },
    },
    # —— NEW unique brands (not regenerating old gallery niches) ——
    {
        "folder": "cleaning",
        "niche": "cleaning",
        "business_name": "KlarRaum Facility",
        "city": "Köln",
        "description": (
            "KlarRaum Facility Köln — Gebäudereinigung, Büroreinigung, "
            "Fensterreinigung, Unterhaltsreinigung für Unternehmen"
        ),
        "services_list": [
            "Büroreinigung",
            "Fensterreinigung",
            "Unterhalt",
            "Sonderreinigung",
        ],
        "phone": "+49 221 5556677",
        "email": "kontakt@klarraum-demo.example.de",
        "advantages": ["Geschulte Teams", "Klare Checklisten", "Festpreise"],
        "dream_brief": {
            "who_is_company": (
                "Facility-Team mit Checklisten statt Chaos — Büros und Glas, "
                "die morgens fertig sind."
            ),
            "commercial_idea": "Sauberkeit, die man merkt — ohne Drama.",
            "problem_before": "Reinigung, die unsichtbar bleibt oder Stress macht.",
            "client_story": "Büro öffnen — und es fühlt sich neu an.",
            "clients_who": "KMU und Praxen in Köln",
            "why_choose_us": "Feste Ansprechpartner, transparente Touren, Qualitätskontrolle",
            "brand_feeling": "Frisch, präzise, zuverlässig",
            "style": "modern",
            "client_fear": "No-shows und schlechte Übergabe",
            "main_promise": "Büro öffnen — und es fühlt sich neu an.",
        },
    },
    {
        "folder": "orthodontics",
        "niche": "orthodontics",
        "business_name": "Alignum Kieferorthopädie",
        "city": "Stuttgart",
        "description": (
            "Alignum Kieferorthopädie Stuttgart — Aligner, festsitzende Apparaturen, "
            "digitale Scans, Behandlung für Jugendliche und Erwachsene"
        ),
        "services_list": ["Aligner", "3D-Scan", "Kontrollen", "Retention"],
        "phone": "+49 711 3344556",
        "email": "kontakt@alignum-demo.example.de",
        "advantages": ["Digitale Planung", "Klare Dauer", "Ruhige Praxis"],
        "dream_brief": {
            "who_is_company": (
                "Kieferorthopädie mit Scan-first Workflow — Lächeln planen, "
                "nicht raten."
            ),
            "commercial_idea": "Ein Lächeln mit Plan.",
            "problem_before": "Unklare Behandlungsdauer und unschöne Spangen-Angst.",
            "client_story": "Zähne, die zu Ihrem Gesicht passen — Schritt für Schritt.",
            "clients_who": "Jugendliche und Erwachsene in Stuttgart",
            "why_choose_us": "3D-Scan, transparente Meilensteine, moderne Praxis",
            "brand_feeling": "Hell, präzise, ermutigend",
            "style": "clinic",
            "client_fear": "Jahre ohne Ergebnis und peinliche Apparatur",
            "main_promise": "Zähne, die zu Ihrem Gesicht passen — Schritt für Schritt.",
        },
    },
    {
        "folder": "auto_detailing",
        "niche": "auto_detailing",
        "business_name": "GlanzWerk Detailing",
        "city": "Düsseldorf",
        "description": (
            "GlanzWerk Detailing Düsseldorf — Lackkorrektur, Keramikversiegelung, "
            "Innenraumaufbereitung, Felgenpflege für Premium-Fahrzeuge"
        ),
        "services_list": [
            "Lackkorrektur",
            "Keramikversiegelung",
            "Innenraum",
            "Felgenpflege",
        ],
        "phone": "+49 211 7788990",
        "email": "kontakt@glanzwerk-demo.example.de",
        "advantages": ["Showroom-Finish", "Messbare Lacktiefe", "Termin klar"],
        "dream_brief": {
            "who_is_company": (
                "Detailing-Studio für Lack und Innenraum — Spiegelglanz ohne "
                "Schnellwäsche-Kompromiss."
            ),
            "commercial_idea": "Lack, der Licht fängt.",
            "problem_before": "Waschanlage-Kratzer und matte Farbe trotz Pflege.",
            "client_story": "Ihr Auto verlässt das Studio wie aus dem Prospekt.",
            "clients_who": "Premium-Fahrer und Sammler in Düsseldorf",
            "why_choose_us": "Mehrstufige Politur, Keramik, dokumentiertes Ergebnis",
            "brand_feeling": "Dunkel, glänzend, präzise",
            "style": "luxury",
            "client_fear": "Beschädigter Lack und leere Versprechen",
            "main_promise": "Ihr Auto verlässt das Studio wie aus dem Prospekt.",
        },
    },
    {
        "folder": "photography",
        "niche": "photography",
        "business_name": "Lichtspur Studio",
        "city": "Leipzig",
        "description": (
            "Lichtspur Studio Leipzig — Business-Porträts, Produktfotografie, "
            "Brand Stories und Editorial für Unternehmen"
        ),
        "services_list": [
            "Business-Porträt",
            "Produktfotos",
            "Brand Story",
            "Retusche",
        ],
        "phone": "+49 341 1122334",
        "email": "kontakt@lichtspur-demo.example.de",
        "advantages": ["Studio + Location", "Schnelle Lieferung", "Brand-Fit"],
        "dream_brief": {
            "who_is_company": (
                "Fotostudio für Marken, die ernst genommen werden wollen — "
                "Licht mit Absicht."
            ),
            "commercial_idea": "Bilder, die Ihre Marke tragen.",
            "problem_before": "Handyfotos und Stock, die niemand glaubt.",
            "client_story": "Ein Bildsatz, der wie Ihre Firma klingt.",
            "clients_who": "Gründer und Mittelstand in Leipzig",
            "why_choose_us": "Konzept vor Auslösen, klare Nutzungsrechte, schnelle Retusche",
            "brand_feeling": "Kontrastreich, editorial, ruhig",
            "style": "editorial",
            "client_fear": "Bilder, die austauschbar wirken",
            "main_promise": "Ein Bildsatz, der wie Ihre Firma klingt.",
        },
    },
    {
        "folder": "it_support",
        "niche": "it_support",
        "business_name": "NetzKlar IT",
        "city": "Nürnberg",
        "description": (
            "NetzKlar IT Nürnberg — IT-Support für KMU, Laptop-Reparatur, "
            "Netzwerk, Backup und Remote-Hilfe"
        ),
        "services_list": [
            "Remote-Support",
            "Laptop-Reparatur",
            "Netzwerk",
            "Backup",
        ],
        "phone": "+49 911 4455667",
        "email": "kontakt@netzklar-demo.example.de",
        "advantages": ["Reaktionszeit SLA", "Klare Tickets", "Vor Ort + Remote"],
        "dream_brief": {
            "who_is_company": (
                "IT-Partner für KMU — Störungen lösen, bevor der Tag kippt."
            ),
            "commercial_idea": "Technik, die wieder unsichtbar wird.",
            "problem_before": "Warteschleifen und Technikchinesisch.",
            "client_story": "Ein Anruf — und das Büro läuft wieder.",
            "clients_who": "Büros und Praxen in Nürnberg",
            "why_choose_us": "SLA, verständliche Sprache, dokumentierte Fixes",
            "brand_feeling": "Klar, technisch, ruhig",
            "style": "modern",
            "client_fear": "Ausfall ohne Ansprechpartner",
            "main_promise": "Ein Anruf — und das Büro läuft wieder.",
        },
    },
    {
        "folder": "elektro",
        "niche": "elektro",
        "business_name": "StromWerk Meisterbetrieb",
        "city": "Köln",
        "description": (
            "StromWerk Meisterbetrieb Köln — Elektroinstallation, Smart Home, "
            "Photovoltaik-Anschluss und Störungsdienst für Haus und Gewerbe"
        ),
        "services_list": [
            "Neuinstallation",
            "Smart Home",
            "PV-Anschluss",
            "Störungsdienst",
        ],
        "phone": "+49 221 7788990",
        "email": "kontakt@stromwerk-demo.example.de",
        "advantages": ["Meisterbetrieb", "Saubere Dokumentation", "Schnelle Hilfe"],
        "dream_brief": {
            "who_is_company": (
                "Elektriker-Meisterteam in Köln — sichere Installationen ohne Chaos."
            ),
            "commercial_idea": "Strom, der einfach funktioniert.",
            "problem_before": "Unklare Angebote und wochenlange Wartezeiten.",
            "client_story": "Licht an — und alles ist fachgerecht erledigt.",
            "clients_who": "Haushalte und KMU in Köln",
            "why_choose_us": "Meisterqualität, Festpreis-Klarheit, Notdienst",
            "brand_feeling": "Präzise, zuverlässig, modern",
            "style": "industrial",
            "client_fear": "Pfusch und teure Nacharbeiten",
            "main_promise": "Licht an — und alles ist fachgerecht erledigt.",
        },
    },
    {
        "folder": "sanitaer",
        "niche": "sanitaer",
        "business_name": "WasserKlar Sanitär",
        "city": "Stuttgart",
        "description": (
            "WasserKlar Sanitär Stuttgart — Sanitär, Heizung, Badsanierung "
            "und Wartung für Privathaushalte und Immobilien"
        ),
        "services_list": [
            "Badsanierung",
            "Heizung",
            "Wartung",
            "Notdienst",
        ],
        "phone": "+49 711 3344556",
        "email": "kontakt@wasserklar-demo.example.de",
        "advantages": ["Saubere Baustelle", "Termintreue", "Ersatzteilservice"],
        "dream_brief": {
            "who_is_company": (
                "Sanitär- und Heizungsteam in Stuttgart — Wasser und Wärme ohne Stress."
            ),
            "commercial_idea": "Bad und Heizung, die zum Alltag passen.",
            "problem_before": "Undichte Stellen und monatelange Sanierungen.",
            "client_story": "Wasser läuft — und das Bad fühlt sich neu an.",
            "clients_who": "Familien und Eigentümer in Stuttgart",
            "why_choose_us": "Klare Abläufe, Meisterhandwerk, ehrliche Preise",
            "brand_feeling": "Frisch, präzise, vertrauenswürdig",
            "style": "modern",
            "client_fear": "Schimmel und endlose Baustelle",
            "main_promise": "Wasser läuft — und das Bad fühlt sich neu an.",
        },
    },
    {
        "folder": "maler",
        "niche": "maler",
        "business_name": "FarbRaum Malermeister",
        "city": "Düsseldorf",
        "description": (
            "FarbRaum Malermeister Düsseldorf — Innenanstrich, Fassade, "
            "Tapezierarbeiten und Beratung für Wohnraum und Gewerbe"
        ),
        "services_list": [
            "Innenanstrich",
            "Fassade",
            "Tapezieren",
            "Beratung",
        ],
        "phone": "+49 211 5566778",
        "email": "kontakt@farbraum-demo.example.de",
        "advantages": ["Saubere Kanten", "Farbberatung", "Staubarme Arbeit"],
        "dream_brief": {
            "who_is_company": (
                "Malermeister-Team in Düsseldorf — Flächen, die ruhig und edel wirken."
            ),
            "commercial_idea": "Farbe als Raumgefühl, nicht nur Anstrich.",
            "problem_before": "Flecken, unruhige Wände, falsche Farbwahl.",
            "client_story": "Raum öffnen — und die Wände atmen Qualität.",
            "clients_who": "Eigentümer und Büros in Düsseldorf",
            "why_choose_us": "Meisterfinish, Farbkonzept, termingerechte Übergabe",
            "brand_feeling": "Warm, handwerklich, ästhetisch",
            "style": "atelier",
            "client_fear": "Schlechte Deckung und Flecken",
            "main_promise": "Raum öffnen — und die Wände atmen Qualität.",
        },
    },
    {
        "folder": "family_psychology",
        "niche": "family_psychology",
        "business_name": "NestKlar Familienpraxis",
        "city": "Berlin",
        "description": (
            "NestKlar Familienpraxis Berlin — Familientherapie, Paarberatung, "
            "Elterncoaching und sichere Räume für Gespräche"
        ),
        "services_list": [
            "Familientherapie",
            "Paarberatung",
            "Elterncoaching",
            "Erstgespräch",
        ],
        "phone": "+49 30 9988776",
        "email": "kontakt@nestklar-demo.example.de",
        "advantages": ["Warmherzige Atmosphäre", "Klare Methoden", "Flexible Termine"],
        "dream_brief": {
            "who_is_company": (
                "Familienpraxis in Berlin — Gespräche, die wieder Verbindung schaffen."
            ),
            "commercial_idea": "Ein sicherer Raum für Familie und Beziehung.",
            "problem_before": "Streit ohne Sprache und Überforderung zu Hause.",
            "client_story": "Nach dem Gespräch fühlt sich Zuhause wieder möglich an.",
            "clients_who": "Familien und Paare in Berlin",
            "why_choose_us": "Empathie, Struktur, alltagsnahe Schritte",
            "brand_feeling": "Warm, ruhig, einladend",
            "style": "editorial",
            "client_fear": "Verurteilt zu werden",
            "main_promise": "Nach dem Gespräch fühlt sich Zuhause wieder möglich an.",
        },
    },
    {
        "folder": "car_dealership",
        "niche": "car_dealership",
        "business_name": "NordLicht Autohaus",
        "city": "München",
        "description": (
            "NordLicht Autohaus München — Neuwagen, Gebrauchtwagen, "
            "Probefahrt und Service mit Showroom-Erlebnis"
        ),
        "services_list": [
            "Neuwagen",
            "Gebrauchtwagen",
            "Probefahrt",
            "Service",
        ],
        "phone": "+49 89 1122334",
        "email": "kontakt@nordlicht-auto-demo.example.de",
        "advantages": ["Transparente Preise", "Probefahrt-Service", "Werkstatt vor Ort"],
        "dream_brief": {
            "who_is_company": (
                "Autohaus in München — Auswahl mit Klarheit statt Druckverkauf."
            ),
            "commercial_idea": "Das nächste Auto ohne Überraschungen.",
            "problem_before": "Intransparente Angebote und Showroom-Stress.",
            "client_story": "Schlüsselübergabe — und alles ist klar dokumentiert.",
            "clients_who": "Pendler und Familien in München",
            "why_choose_us": "Ehrliche Beratung, saubere Historie, Servicenetz",
            "brand_feeling": "Premium, dunkel, präzise",
            "style": "luxury",
            "client_fear": "Versteckte Mängel und Nachverhandlungen",
            "main_promise": "Schlüsselübergabe — und alles ist klar dokumentiert.",
        },
    },
]

STORE_CASES: list[dict] = [
    {
        "folder": "fashion",
        "category": "clothing",
        "company_name": "Nordlicht GmbH",
        "store_name": "Nordlicht Fashion",
        "what_is_sold": "Mode, Schuhe und Accessoires für den deutschen Alltag",
        "style": "warm",
    },
    {
        "folder": "beauty",
        "category": "beauty",
        "company_name": "Glow Lab GmbH",
        "store_name": "Glow Lab Beauty",
        "what_is_sold": "Hautpflege und Kosmetik Made for DE",
        "style": "elegant",
    },
    {
        "folder": "electronics",
        "category": "electronics",
        "company_name": "VoltHaus GmbH",
        "store_name": "VoltHaus Electronics",
        "what_is_sold": "Elektronik und Gadgets für Zuhause und Büro",
        "style": "modern",
    },
    {
        "folder": "furniture",
        "category": "furniture",
        "company_name": "Wohnraum Nord GmbH",
        "store_name": "Wohnraum Furniture",
        "what_is_sold": "Möbel und Einrichtung für moderne Wohnungen",
        "style": "minimal",
    },
    {
        "folder": "accessories",
        "category": "accessories",
        "company_name": "Zeitstück GmbH",
        "store_name": "Zeitstück Accessoires",
        "what_is_sold": "Uhren, Taschen und Accessoires",
        "style": "elegant",
    },
    {
        "folder": "food",
        "category": "food",
        "company_name": "FeinKost Berlin GmbH",
        "store_name": "FeinKost Food",
        "what_is_sold": "Feinkost und regionale Spezialitäten",
        "style": "warm",
    },
    {
        "folder": "handwerk",
        "category": "handwerk",
        "company_name": "Werkstatt Direkt GmbH",
        "store_name": "Werkstatt Direkt",
        "what_is_sold": "Werkzeuge und Material für Handwerker",
        "style": "corporate",
    },
    {
        "folder": "dachreinigung",
        "category": "dachreinigung",
        "company_name": "DachKlar Shop GmbH",
        "store_name": "DachKlar Shop",
        "what_is_sold": (
            "Zubehör und Pflegeprodukte für Dachreinigung, Moosentfernung "
            "und Fassadenschutz in Deutschland"
        ),
        "style": "corporate",
    },
    {
        "folder": "zaunbau",
        "category": "zaunbau",
        "company_name": "ZaunWerk Handel GmbH",
        "store_name": "ZaunWerk Material",
        "what_is_sold": "Zaunsysteme, Tore, Pfosten und Montagezubehör für den deutschen Garten",
        "style": "corporate",
    },
    {
        "folder": "gartenpflege",
        "category": "gartenpflege",
        "company_name": "Grünzeit Shop GmbH",
        "store_name": "Grünzeit Garten",
        "what_is_sold": "Gartenpflege-Produkte, Geräte und saisonale Pflege für Privathäuser",
        "style": "warm",
    },
    {
        "folder": "psychology",
        "category": "psychology",
        "company_name": "Praxis Klarheit GmbH",
        "store_name": "Klarheit Digital",
        "what_is_sold": (
            "Online-Beratung, Gutscheine, Kurse, Meditationen, "
            "Arbeitshefte und digitale Materialien für psychische Gesundheit"
        ),
        "style": "elegant",
    },

    {
        "folder": "sports",
        "category": "other",
        "company_name": "FitTrail Sport GmbH",
        "store_name": "FitTrail Sports",
        "what_is_sold": "Sportbekleidung, Fitnessgeräte und Outdoor-Equipment für den Alltag",
        "style": "modern",
    },
    {
        "folder": "pets",
        "category": "other",
        "company_name": "PfotenGlück GmbH",
        "store_name": "PfotenGlück Pets",
        "what_is_sold": "Futter, Pflege und Zubehör für Hunde und Katzen",
        "style": "warm",
    },
    {
        "folder": "coffee",
        "category": "restaurant",
        "company_name": "Röstwerk Kaffee GmbH",
        "store_name": "Röstwerk Coffee",
        "what_is_sold": "Specialty Coffee, Bohne, Zubehör und Café-Produkte für Zuhause",
        "style": "warm",
    },
    {
        "folder": "jewelry",
        "category": "jewelry",
        "company_name": "Atelier Silberlinie GmbH",
        "store_name": "Silberlinie Jewelry",
        "what_is_sold": "Schmuck, Ringe und zeitlose Accessoires Made for DE",
        "style": "elegant",
    },
    # —— NEW unique stores (not regenerating existing premium folders) ——
    {
        "folder": "cleaning_shop",
        "category": "cleaning",
        "company_name": "FrischMittel GmbH",
        "store_name": "FrischMittel Profi",
        "what_is_sold": (
            "Professionelle Reinigungsmittel, Tücher und Pflegeprodukte "
            "für Facility und Haushalt"
        ),
        "style": "modern",
    },
    {
        "folder": "detailing_shop",
        "category": "auto_detailing",
        "company_name": "MirrorCoat GmbH",
        "store_name": "MirrorCoat Care",
        "what_is_sold": (
            "Keramikversiegelung, Polituren und Detailing-Kits für Lack und Felgen"
        ),
        "style": "luxury",
    },
    {
        "folder": "ortho_care",
        "category": "orthodontics",
        "company_name": "SmileTray Care GmbH",
        "store_name": "SmileTray Care",
        "what_is_sold": "Aligner-Pflege, Reinigungstabletten und Ortho-Hygieneprodukte",
        "style": "clinic",
    },
    {
        "folder": "bookstore",
        "category": "books",
        "company_name": "Seitenwerk Leipzig GmbH",
        "store_name": "Seitenwerk Books",
        "what_is_sold": "Ausgewählte Bücher, Fotobände und Notizbücher für den Alltag",
        "style": "editorial",
    },
    {
        "folder": "it_parts",
        "category": "it_parts",
        "company_name": "ByteErsatz GmbH",
        "store_name": "ByteErsatz Parts",
        "what_is_sold": "SSD, RAM, Akkus und Notebook-Ersatzteile mit DE-Versand",
        "style": "tech",
    },
    {
        "folder": "solar_shop",
        "category": "solar",
        "company_name": "SunGrid Handel GmbH",
        "store_name": "SunGrid Solar Shop",
        "what_is_sold": "PV-Module, Speicher, Wallboxen und Montagezubehör",
        "style": "tech",
    },
    {
        "folder": "auto_parts",
        "category": "auto_parts",
        "company_name": "TeilWerk Autoteile",
        "store_name": "TeilWerk Parts",
        "what_is_sold": "Filter, Bremsen, Pflege und Kfz-Zubehör mit DE-Versand",
        "style": "industrial",
    },
    {
        "folder": "paint_shop",
        "category": "maler",
        "company_name": "PigmentPro Farben",
        "store_name": "PigmentPro Shop",
        "what_is_sold": "Innenfarben, Lacke, Werkzeuge und Malerzubehör",
        "style": "atelier",
    },
    {
        "folder": "wine_shop",
        "category": "food",
        "company_name": "RebenKlar Weine",
        "store_name": "RebenKlar Vinothek",
        "what_is_sold": "Deutsche und europäische Weine, Sets und Geschenkpakete",
        "style": "editorial",
    },
    {
        "folder": "optics_shop",
        "category": "electronics",
        "company_name": "KlarBlick Optik",
        "store_name": "KlarBlick Optics",
        "what_is_sold": "Fassungen, Gläser, Pflege und Seh-Accessoires",
        "style": "tech",
    },
]

MIN_FULL_BYTES = 5000


def _wipe_and_copy(src: Path, dest: Path) -> None:
    import time

    if dest.exists():
        last_err: Exception | None = None
        for attempt in range(6):
            try:
                shutil.rmtree(dest)
                last_err = None
                break
            except OSError as exc:
                last_err = exc
                time.sleep(0.35 * (attempt + 1))
        if last_err is not None and dest.exists():
            # Windows file lock — copy over in place
            for child in dest.iterdir():
                try:
                    if child.is_dir():
                        shutil.rmtree(child, ignore_errors=True)
                    else:
                        child.unlink(missing_ok=True)
                except OSError:
                    pass
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        # Merge copy into existing dest
        for item in src.iterdir():
            target = dest / item.name
            if item.is_dir():
                if target.exists():
                    shutil.rmtree(target, ignore_errors=True)
                shutil.copytree(
                    item,
                    target,
                    ignore=shutil.ignore_patterns("*.pyc", "__pycache__", ".git"),
                )
            else:
                shutil.copy2(item, target)
    else:
        shutil.copytree(
            src,
            dest,
            ignore=shutil.ignore_patterns("*.pyc", "__pycache__", ".git"),
        )


def _ensure_gallery_jpg(dest: Path, *, niche: str = "") -> None:
    """Ensure gallery.jpg + gallery_1..3 niche plates exist for photo bands.

    Never clone hero into every gallery slot — each plate gets its own niche scene.
    """
    assets = dest / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    niche_id = (niche or dest.name or "generic").strip().lower() or "generic"
    try:
        from app.factory.niche_scene_media import write_niche_scene
    except Exception:
        write_niche_scene = None  # type: ignore

    for i, name in enumerate(("gallery.jpg", "gallery_1.jpg", "gallery_2.jpg", "gallery_3.jpg")):
        target = assets / name
        if target.is_file() and target.stat().st_size > 4_000:
            # Replace exact hero clones (same bytes) with a unique plate
            hero = assets / "hero.jpg"
            if (
                hero.is_file()
                and target.stat().st_size == hero.stat().st_size
                and target.read_bytes() == hero.read_bytes()
                and write_niche_scene is not None
            ):
                write_niche_scene(
                    target,
                    niche_id=niche_id,
                    seed=f"gallery-fix|{name}|{dest.name}",
                    role="gallery",
                    size=(1200, 800),
                )
            continue
        if write_niche_scene is not None:
            write_niche_scene(
                target,
                niche_id=niche_id,
                seed=f"gallery-fill|{name}|{dest.name}|{i}",
                role="gallery",
                size=(1200, 800),
            )
            continue
        # Fallback tiny JPEG only if Pillow path unavailable
        hero = assets / "hero.jpg"
        for cand in (
            hero,
            assets / "hero_pack" / "hero_1.jpg",
            assets / "hero_pack" / "banner.jpg",
            assets / "background.jpg",
        ):
            if cand.is_file() and cand.stat().st_size > 500:
                shutil.copy2(cand, target)
                break
        else:
            # Never ship a 1×1 stub — fail loudly rather than empty vitrine plate
            raise RuntimeError(
                f"Media QA FAIL: cannot create gallery plate {target.name} "
                f"for niche={niche_id} (no Pillow scene / no hero source)"
            )


def _assert_media_floor(dest: Path, *, niche: str) -> None:
    """Hard gate: no empty / tiny heroes before public vitrine publish."""
    from app.factory.niche_scene_media import write_niche_scene

    assets = dest / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    images = assets / "images"
    min_bytes = 4_000
    hero_candidates = [
        assets / "hero.jpg",
        assets / "hero_pack" / "hero_1.jpg",
        images / "hero.jpg",
        images / "banner.jpg",
    ]
    hero_ok = next(
        (p for p in hero_candidates if p.is_file() and p.stat().st_size >= min_bytes),
        None,
    )
    if hero_ok is None:
        target = images / "hero.jpg" if images.is_dir() or (dest / "catalog.html").is_file() else assets / "hero.jpg"
        target.parent.mkdir(parents=True, exist_ok=True)
        write_niche_scene(
            target,
            niche_id=niche or dest.name,
            seed=f"vitrine-hero|{dest.name}",
            role="hero",
            size=(1600, 900),
        )
        hero_ok = target
    if hero_ok.stat().st_size < min_bytes:
        raise RuntimeError(f"Media QA FAIL: hero still tiny at {hero_ok}")

    # Gallery / product plates for websites
    gallery = assets / "gallery.jpg"
    if (dest / "index.html").is_file():
        if not gallery.is_file() or gallery.stat().st_size < min_bytes:
            write_niche_scene(
                gallery,
                niche_id=niche or dest.name,
                seed=f"vitrine-gallery|{dest.name}",
                role="gallery",
                size=(1200, 800),
            )
        if gallery.stat().st_size < min_bytes:
            raise RuntimeError(f"Media QA FAIL: gallery still tiny at {gallery}")

    # Store product plate
    product = images / "product.jpg"
    if (dest / "catalog.html").is_file():
        images.mkdir(parents=True, exist_ok=True)
        if not product.is_file() or product.stat().st_size < min_bytes:
            write_niche_scene(
                product,
                niche_id=niche or dest.name,
                seed=f"vitrine-product|{dest.name}",
                role="product",
                size=(900, 1120),
            )
        if product.stat().st_size < min_bytes:
            raise RuntimeError(f"Media QA FAIL: product still tiny at {product}")


def sync_websites(
    *,
    package_id: str = "business",
    folders: list[str] | None = None,
) -> list[dict]:
    sandbox = BACKEND / ".tmp_package_preview_sandbox" / package_id
    if sandbox.exists():
        shutil.rmtree(sandbox)
    sandbox.mkdir(parents=True)
    factory = FactoryService(memory_dir=sandbox, sandbox_dir=sandbox)
    results: list[dict] = []
    cases = WEBSITE_CASES
    if folders:
        want = {f.lower() for f in folders}
        cases = [c for c in WEBSITE_CASES if c["folder"].lower() in want]

    for case in cases:
        folder = case["folder"]
        niche = case["niche"]
        dest = PUBLIC / "sites" / package_id / folder
        contacts = {
            "business_name": case["business_name"],
            "city": case["city"],
            "phone": case["phone"],
            "email": case["email"],
            "whatsapp": case["phone"],
            "niche": niche,
            "services_list": case["services_list"],
            "advantages": case["advantages"],
            "package_id": package_id,
            "market_code": "DE",
            "ui_lang": "de",
            "language": "de",
            "brand_style": "auto",
            "demo_gallery": True,
            "keep_business_name": True,
            "diversity_salt": f"gallery-{package_id}-{folder}",
        }
        if isinstance(case.get("dream_brief"), dict):
            contacts["dream_brief"] = case["dream_brief"]
            # Flatten for First Impression / Interview (never lose client_story)
            for k in (
                "client_story",
                "problem_before",
                "who_is_company",
                "main_promise",
                "why_choose_us",
                "brand_feeling",
                "clients_who",
            ):
                if case["dream_brief"].get(k) and not contacts.get(k):
                    contacts[k] = case["dream_brief"][k]
            style = str(case["dream_brief"].get("style") or "").strip()
            if style:
                contacts["style"] = style
                contacts["brand_style"] = style
        if not str(contacts.get("client_story") or "").strip():
            contacts["client_story"] = (
                str((case.get("dream_brief") or {}).get("main_promise") or "").strip()
                or str(case.get("description") or "").strip()
                or f"{case.get('business_name') or folder} — echte Arbeit für echte Kunden."
            )
        contacts.setdefault("fabricate_company", True)
        # Motion: Basic/Business = CSS; Premium = WebGL 3D when niche sells with it
        from app.factory.creative_direction import recommends_webgl_3d

        use_3d = package_id in ("premium", "connected") and recommends_webgl_3d(
            niche, package_id
        )
        motion = "3d_premium" if use_3d else "css"
        contacts["motion_level"] = motion
        if use_3d:
            contacts["prefer_webgl"] = True
        try:
            summary = factory.build_landing(
                case["description"],
                package_id=package_id,
                contacts=contacts,
                market_code="DE",
                motion_level=motion,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[FAIL] {package_id}/{folder} build: {exc}")
            results.append(
                {
                    "ok": False,
                    "kind": "website",
                    "package_id": package_id,
                    "folder": folder,
                    "niche": niche,
                    "error": str(exc)[:240],
                }
            )
            continue
        product_id = summary["product_id"]
        product_dir = sandbox / product_id
        try:
            _wipe_and_copy(product_dir, dest)
            _ensure_gallery_jpg(dest, niche=niche)
            _assert_media_floor(dest, niche=niche)
        except Exception as exc:  # noqa: BLE001
            print(f"[FAIL] {package_id}/{folder} media: {exc}")
            results.append(
                {
                    "ok": False,
                    "kind": "website",
                    "package_id": package_id,
                    "folder": folder,
                    "niche": niche,
                    "error": str(exc)[:240],
                }
            )
            continue

        if use_3d:
            try:
                from app.factory.scene_3d_engine import (
                    write_hero_3d_snippet,
                    write_scene_assets,
                )

                write_scene_assets(
                    dest,
                    niche_id=niche,
                    accent="#3b82f6",
                    brand_name=str(case.get("business_name") or folder),
                )
                write_hero_3d_snippet(
                    dest,
                    niche_id=niche,
                    accent="#3b82f6",
                    brand_name=str(case.get("business_name") or folder),
                )
            except Exception as exc:  # noqa: BLE001
                print(f"  3D attach warn {folder}: {exc}")

        index = dest / "index.html"
        size = index.stat().st_size if index.is_file() else 0
        # Hard freshness markers for Demo Freshness Gate
        html = index.read_text(encoding="utf-8", errors="replace") if index.is_file() else ""
        import re as _re

        tier_ok = bool(
            _re.search(
                rf'<body\b[^>]*\bdata-tier=["\']{package_id}["\']',
                html,
                _re.I,
            )
        )
        concept_only = (
            "creative_identity_owner_preview" in html
            or "design_concept_owner_preview" in html
        )
        meta_path = dest / "demo_gallery_meta.json"
        meta_path.write_text(
            json.dumps(
                {
                    "kind": "website",
                    "folder": folder,
                    "niche": niche,
                    "package_id": package_id,
                    "product_id": product_id,
                    "business_name": case["business_name"],
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "engine": (
                        "Design Concept Owner Preview"
                        if concept_only
                        else "FactoryService.build_landing + Design DNA + Design Engine + VIE"
                    ),
                    "index_bytes": size,
                    "data_tier_ok": tier_ok,
                    "concept_only": concept_only,
                    "reality_benchmark": "FAIL" if concept_only else "PENDING",
                    "gallery_schema": "tier_v2",
                    "public_url": f"/package-previews/sites/{package_id}/{folder}/index.html",
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        if concept_only and size >= 2500 and tier_ok:
            status = "CONCEPT"
        elif size >= MIN_FULL_BYTES and tier_ok:
            status = "PASS"
        else:
            status = "THIN"
        if not tier_ok:
            status = "STALE_TIER"
        print(f"[{status}] {package_id}/{folder:12} {size:6}B -> {dest}")
        results.append(
            {
                "kind": "website",
                "id": folder,
                "package_id": package_id,
                "status": status,
                "concept_only": concept_only,
                "bytes": size,
                "url": f"/package-previews/sites/{package_id}/{folder}/index.html",
            }
        )
    return results


def sync_stores(
    *,
    package_ids: list[str] | None = None,
    folders: list[str] | None = None,
) -> list[dict]:
    """Write store demos. With package_ids → stores/<tier>/<folder>/; else legacy stores/<folder>/."""
    from app.factory.store_factory.composer import write_storefront
    from app.factory.store_factory.templates import StoreTemplateRegistry
    from app.integration.shop_brief import validate_shop_brief

    results: list[dict] = []
    cases = STORE_CASES
    if folders:
        want = {f.lower() for f in folders}
        cases = [c for c in STORE_CASES if c["folder"].lower() in want]
    tiers = package_ids or [None]

    for package_id in tiers:
        pid = (package_id or "").strip().lower() or None
        for case in cases:
            folder = case["folder"]
            if pid:
                dest = PUBLIC / "stores" / pid / folder
            else:
                dest = PUBLIC / "stores" / folder
            if dest.exists():
                shutil.rmtree(dest)
            dest.mkdir(parents=True)

            brief = validate_shop_brief(
                {
                    "company_name": case["company_name"],
                    "store_name": case["store_name"],
                    "what_is_sold": case["what_is_sold"],
                    "category": case["category"],
                    "catalog_size": "24",
                    "languages": ["de"],
                    "currency": "EUR",
                    "payments": ["stripe"],
                    "shipping": ["dhl"],
                    "pages": [
                        "home",
                        "catalog",
                        "pdp",
                        "about",
                        "contact",
                        "legal",
                        "returns",
                        "cart",
                        "checkout",
                        "account",
                    ],
                    "style": case.get("style") or "modern",
                }
            )
            brief["market_code"] = "DE"
            brief["demo_gallery"] = True
            brief["diversity_salt"] = f"gallery-store-{pid or 'business'}-{folder}"
            if pid:
                brief["package_id"] = pid
            resolved = StoreTemplateRegistry().resolve(brief)
            write_storefront(dest, brief=brief, resolved=resolved)
            from app.factory.store_factory.design_bridge import STORE_CATEGORY_TO_NICHE as _STORE_NICHE_MAP

            niche_for_media = _STORE_NICHE_MAP.get(
                str(case.get("category") or "").lower(),
                str(case.get("category") or folder),
            )
            _assert_media_floor(dest, niche=niche_for_media)

            # Creative Direction + offline premium media note (parity with website Factory)
            try:
                from app.factory.creative_direction import (
                    invent_creative_brief,
                    persist_creative_brief,
                    recommends_webgl_3d,
                )
                from app.factory.store_factory.design_bridge import STORE_CATEGORY_TO_NICHE
                from app.factory.visual_brand_system import image_provider_configured

                niche_id = STORE_CATEGORY_TO_NICHE.get(
                    str(case.get("category") or "").lower(),
                    str(case.get("category") or "generic"),
                )
                creative = invent_creative_brief(
                    brand_name=str(case.get("store_name") or case.get("company_name") or folder),
                    niche_id=niche_id,
                    package_id=pid or "business",
                    diversity_salt=str(brief.get("diversity_salt") or folder),
                )
                persist_creative_brief(dest, creative)
                if (pid or "") in ("premium", "connected") and not image_provider_configured():
                    note = {
                        "status": "studio_offline_media",
                        "message": (
                            "AI Image Provider not connected — Studio Offline Media "
                            "(3D/experience still on)"
                        ),
                        "provider_connected": False,
                        "studio_offline_media": True,
                        "webgl_3d": bool(
                            creative.recommends_webgl
                            or recommends_webgl_3d(niche_id, pid)
                        ),
                        "experience_on": True,
                    }
                    (dest / "PREMIUM_MEDIA_NOTE.json").write_text(
                        json.dumps(note, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8",
                    )
                    assets = dest / "assets"
                    assets.mkdir(parents=True, exist_ok=True)
                    (assets / "premium_media_note.txt").write_text(
                        "AI Image Provider not connected — Studio Offline Media "
                        "(3D/experience still on)\n",
                        encoding="utf-8",
                    )
                if creative.recommends_webgl or recommends_webgl_3d(niche_id, pid):
                    from app.factory.scene_3d_engine import (
                        write_hero_3d_snippet,
                        write_scene_assets,
                    )

                    write_scene_assets(
                        dest,
                        niche_id=niche_id,
                        accent="#3b82f6",
                        brand_name=str(case.get("store_name") or ""),
                    )
                    write_hero_3d_snippet(
                        dest,
                        niche_id=niche_id,
                        accent="#3b82f6",
                        brand_name=str(case.get("store_name") or ""),
                    )
            except Exception:
                pass

            # Legacy carousel still points at stores/<folder> — mirror business tier there
            if pid == "business":
                legacy = PUBLIC / "stores" / folder
                if legacy.exists():
                    shutil.rmtree(legacy)
                shutil.copytree(dest, legacy)

            index = dest / "index.html"
            size = index.stat().st_size if index.is_file() else 0
            html = index.read_text(encoding="utf-8", errors="replace") if index.is_file() else ""
            concept_only = (
            "creative_identity_owner_preview" in html
            or "design_concept_owner_preview" in html
        )
            rel = (
                f"/package-previews/stores/{pid}/{folder}/catalog.html"
                if pid
                else f"/package-previews/stores/{folder}/catalog.html"
            )
            (dest / "demo_gallery_meta.json").write_text(
                json.dumps(
                    {
                        "kind": "store",
                        "folder": folder,
                        "package_id": pid or "business",
                        "category": case["category"],
                        "store_name": case["store_name"],
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                        "engine": (
                            "Design Concept Owner Preview"
                            if concept_only
                            else "write_storefront + Digital Creative Studio"
                        ),
                        "index_bytes": size,
                        "concept_only": concept_only,
                        "reality_benchmark": "FAIL" if concept_only else "PENDING",
                        "public_url": rel,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            if concept_only and size >= 2500:
                status = "CONCEPT"
            elif size >= MIN_FULL_BYTES:
                status = "PASS"
            else:
                status = "THIN"
            tag = f"store/{pid + '/' if pid else ''}{folder}"
            print(f"[{status}] {tag:28} {size:6}B -> {dest}")
            results.append(
                {
                    "kind": "store",
                    "id": f"{pid}/{folder}" if pid else folder,
                    "package_id": pid or "business",
                    "status": status,
                    "concept_only": concept_only,
                    "bytes": size,
                    "url": rel,
                }
            )
    return results


def write_catalog(rows: list[dict]) -> None:
    """Merge new sync rows with existing index so partial --tiers runs keep Business+Stores."""
    PUBLIC.mkdir(parents=True, exist_ok=True)
    catalog_path = PUBLIC / "GALLERY_INDEX.json"
    prev_items: list[dict] = []
    if catalog_path.is_file():
        try:
            prev = json.loads(catalog_path.read_text(encoding="utf-8"))
            if isinstance(prev.get("items"), list):
                prev_items = [x for x in prev["items"] if isinstance(x, dict)]
        except (OSError, json.JSONDecodeError):
            prev_items = []

    def _key(r: dict) -> tuple:
        return (r.get("kind"), r.get("package_id") or "", r.get("id"))

    merged: dict[tuple, dict] = {_key(r): r for r in prev_items if r.get("kind") and r.get("id")}
    for r in rows:
        merged[_key(r)] = r
    all_rows = list(merged.values())

    business_rows = [
        r for r in all_rows if r.get("kind") == "website" and r.get("package_id") == "business"
    ]
    # Legacy business rows may omit package_id — treat bare /sites/business/ URLs as business.
    if not business_rows:
        business_rows = [
            r
            for r in all_rows
            if r.get("kind") == "website"
            and "/sites/business/" in str(r.get("url") or "")
        ]
    website_pass_src = business_rows
    # Prefer tiered business stores; fall back to legacy flat stores/<folder>
    store_rows = [
        r
        for r in all_rows
        if r.get("kind") == "store"
        and (r.get("package_id") in (None, "", "business") or "/stores/business/" in str(r.get("url") or ""))
    ]
    if not store_rows:
        store_rows = [r for r in all_rows if r.get("kind") == "store" and not r.get("package_id")]
    # Deduplicate by folder id for goal counting
    store_by_id: dict[str, dict] = {}
    for r in store_rows:
        sid = str(r.get("id") or "")
        if sid and sid not in store_by_id:
            store_by_id[sid] = r
    store_count_src = list(store_by_id.values()) or store_rows
    catalog = {
        "name": "Virtus Core Commercial Gallery",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "gallery_schema": "tier_v2",
        "tier_policy": {
            "basic": "Starter €199 — clean modern, light motion, no heavy 3D/Lottie",
            "business": "Business €399 — Hero assets, trust+KPI, richer motion",
            "premium": "Premium €699 — premium_design, stats/showcase, cinematic heroes",
        },
        "websites_goal": 8,
        "stores_goal": 6,
        "websites_pass": sum(1 for r in website_pass_src if r.get("status") == "PASS"),
        "stores_pass": sum(1 for r in store_count_src if r.get("status") == "PASS"),
        "tiers_synced": sorted(
            {
                r.get("package_id")
                for r in all_rows
                if r.get("kind") == "website" and r.get("package_id")
            }
        ),
        "items": all_rows,
    }
    catalog_path.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(
        f"Catalog -> {catalog_path} "
        f"websites {catalog['websites_pass']}/8 stores {catalog['stores_pass']}/6 "
        f"tiers={catalog['tiers_synced']}"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--websites-only", action="store_true")
    parser.add_argument("--stores-only", action="store_true")
    parser.add_argument(
        "--tiers",
        default="business",
        help="Comma list: basic,business,premium (default: business)",
    )
    parser.add_argument(
        "--folders",
        default="",
        help="Optional comma list of website folders (default: all / tier defaults)",
    )
    parser.add_argument(
        "--store-tiers",
        default="",
        help="Optional: basic,business,premium → write stores/<tier>/<folder>/",
    )
    parser.add_argument(
        "--store-folders",
        default="",
        help="Optional comma list of store folders",
    )
    args = parser.parse_args()
    tiers = [t.strip().lower() for t in args.tiers.split(",") if t.strip()]
    folders = [f.strip() for f in args.folders.split(",") if f.strip()] or None
    store_tiers = [t.strip().lower() for t in args.store_tiers.split(",") if t.strip()] or None
    store_folders = [f.strip() for f in args.store_folders.split(",") if f.strip()] or None

    rows: list[dict] = []
    if not args.stores_only:
        for tier in tiers:
            if tier not in ("basic", "business", "premium"):
                print(f"skip unknown tier: {tier}")
                continue
            tier_folders = folders
            if tier == "basic" and not folders:
                tier_folders = [
                    "dental",
                    "psychology",
                    "auto",
                    "beauty",
                    "dachreinigung",
                    "zaunbau",
                    "gartenpflege",
                    "handwerk",
                ]
            if tier == "business" and not folders:
                tier_folders = None  # all WEBSITE_CASES
            if tier == "premium" and not folders:
                tier_folders = [
                    "dental",
                    "psychology",
                    "auto",
                    "beauty",
                    "law",
                    "restaurant",
                    "realestate",
                    "energy",
                    "dachreinigung",
                    "zaunbau",
                    "gartenpflege",
                    "handwerk",
                ]
            rows.extend(sync_websites(package_id=tier, folders=tier_folders))
    if not args.websites_only:
        rows.extend(sync_stores(package_ids=store_tiers, folders=store_folders))
    write_catalog(rows)

    # Studio Acceptance — never claim visual PASS from sync logs
    from app.factory.design_dna.studio_acceptance import (
        print_demo_links,
        write_studio_acceptance,
    )

    psych_touched = bool(
        folders and any(f.lower() == "psychology" for f in folders)
    ) or bool(
        store_folders and any(f.lower() == "psychology" for f in store_folders)
    )
    if psych_touched or not (folders or store_folders):
        write_studio_acceptance(
            PUBLIC / "STUDIO_ACCEPTANCE.json",
            base_url="http://127.0.0.1:3001",
            agent_notes={
                "hero": (
                    "PARTIAL",
                    "Cinematic dark Hero D shipped; owner still has not said wow — not sellable yet",
                ),
                "composition": (
                    "PARTIAL",
                    "chamber vs editorial ladder exists; eye-proof of art-director diversity still weak",
                ),
                "atmosphere": (
                    "PARTIAL",
                    "depth layers present; Premium must still clear studio bar by eye",
                ),
                "white_space": ("PARTIAL", "Rhythm improved; owner eye decides"),
                "store": (
                    "PARTIAL",
                    "Premium brand fold (story + collections) added; still not €699–1200 proof",
                ),
                "premium_studio_test": (
                    "FAIL",
                    "Owner: would not sell Premium at €699–1200 yet; prior screenshots not at bar",
                ),
            },
        )
        print("\n=== Studio Acceptance demos (open these — logs are not proof) ===")
        print_demo_links("http://127.0.0.1:3001")
        print(
            "Status: PENDING_OWNER — task incomplete until owner says: "
            "Да, я бы без стыда продал этот сайт клиенту\n"
        )

    failed = [r for r in rows if r["status"] not in ("PASS", "CONCEPT")]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
