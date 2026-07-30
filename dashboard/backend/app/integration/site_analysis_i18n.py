"""Localized site-analysis issue/strength strings.

Analysis used to emit German-only copy; that leaked into EN/SG/etc. KP drafts.
Issue *codes* stay language-agnostic; messages resolve by generation language.
"""

from __future__ import annotations

import re
from typing import Any

# code → {lang → template}. Templates may use {status} / {ms}.
_ISSUE_MSGS: dict[str, dict[str, str]] = {
    "no_https": {
        "de": "Kein HTTPS — unsicher für Besucher",
        "en": "No HTTPS — insecure for visitors",
        "ru": "Нет HTTPS — небезопасно для посетителей",
        "uk": "Немає HTTPS — небезпечно для відвідувачів",
        "fr": "Pas de HTTPS — risqué pour les visiteurs",
        "es": "Sin HTTPS — inseguro para visitantes",
        "nl": "Geen HTTPS — onveilig voor bezoekers",
        "pl": "Brak HTTPS — niebezpieczne dla odwiedzających",
        "cs": "Bez HTTPS — nebezpečné pro návštěvníky",
        "pt": "Sem HTTPS — inseguro para visitantes",
        "it": "Niente HTTPS — non sicuro per i visitatori",
    },
    "http_error": {
        "de": "Seite antwortet mit HTTP {status}",
        "en": "Site responds with HTTP {status}",
        "ru": "Сайт отвечает HTTP {status}",
        "uk": "Сайт відповідає HTTP {status}",
        "fr": "Le site répond HTTP {status}",
        "es": "El sitio responde HTTP {status}",
        "nl": "Site antwoordt met HTTP {status}",
        "pl": "Strona odpowiada HTTP {status}",
        "cs": "Stránka odpovídá HTTP {status}",
        "pt": "O site responde HTTP {status}",
        "it": "Il sito risponde HTTP {status}",
    },
    "no_viewport": {
        "de": "Kein viewport — oft schlecht auf dem Handy",
        "en": "No viewport — often weak on mobile",
        "ru": "Нет viewport — часто плохо на телефоне",
        "uk": "Немає viewport — часто погано на телефоні",
        "fr": "Pas de viewport — souvent mauvais sur mobile",
        "es": "Sin viewport — a menudo mal en móvil",
        "nl": "Geen viewport — vaak slecht op mobiel",
        "pl": "Brak viewport — często słabo na telefonie",
        "cs": "Chybí viewport — často špatně na mobilu",
        "pt": "Sem viewport — muitas vezes fraco no telemóvel",
        "it": "Niente viewport — spesso debole su mobile",
    },
    "thin_content": {
        "de": "Sehr wenig Inhalt — möglicherweise veraltet oder Platzhalter",
        "en": "Very little content — possibly outdated or placeholder",
        "ru": "Очень мало контента — возможно устарело или заглушка",
        "uk": "Дуже мало контенту — можливо застаріло або заглушка",
        "fr": "Très peu de contenu — peut-être obsolète ou placeholder",
        "es": "Muy poco contenido — posiblemente desactualizado o placeholder",
        "nl": "Zeer weinig inhoud — mogelijk verouderd of placeholder",
        "pl": "Bardzo mało treści — możliwe, że nieaktualne lub placeholder",
        "cs": "Velmi málo obsahu — možná zastaralé nebo placeholder",
        "pt": "Muito pouco conteúdo — possivelmente desatualizado ou placeholder",
        "it": "Pochissimo contenuto — forse obsoleto o placeholder",
    },
    "outdated_tech": {
        "de": "Anzeichen veralteter Technik oder Baustelle",
        "en": "Signs of outdated tech or under construction",
        "ru": "Признаки устаревшей техники или стройки",
        "uk": "Ознаки застарілої техніки або будівництва",
        "fr": "Signes de techno obsolète ou chantier",
        "es": "Señales de tecnología antigua o en obras",
        "nl": "Tekenen van verouderde techniek of bouwplaats",
        "pl": "Oznaki przestarzałej technologii lub budowy",
        "cs": "Známky zastaralé techniky nebo stavby",
        "pt": "Sinais de tecnologia antiga ou em construção",
        "it": "Segnali di tech obsoleta o cantiere",
    },
    "no_contact_form": {
        "de": "Kein sichtbares Kontaktformular / E-Mail-Feld",
        "en": "No visible contact form / email field",
        "ru": "Нет видимой формы / поля email",
        "uk": "Немає видимої форми / поля email",
        "fr": "Pas de formulaire / champ e-mail visible",
        "es": "Sin formulario / campo de email visible",
        "nl": "Geen zichtbaar contactformulier / e-mailveld",
        "pl": "Brak widocznego formularza / pola e-mail",
        "cs": "Žádný viditelný formulář / e-mailové pole",
        "pt": "Sem formulário / campo de e-mail visível",
        "it": "Nessun form / campo email visibile",
    },
    "no_call_whatsapp": {
        "de": "Kein direkter Anruf / WhatsApp-Link",
        "en": "No direct call / WhatsApp link",
        "ru": "Нет прямой ссылки на звонок / WhatsApp",
        "uk": "Немає прямого дзвінка / посилання WhatsApp",
        "fr": "Pas de lien appel / WhatsApp direct",
        "es": "Sin enlace de llamada / WhatsApp",
        "nl": "Geen directe bel- / WhatsApp-link",
        "pl": "Brak bezpośredniego telefonu / WhatsApp",
        "cs": "Žádný přímý hovor / WhatsApp odkaz",
        "pt": "Sem ligação direta / link WhatsApp",
        "it": "Nessun link chiamata / WhatsApp",
    },
    "no_cta": {
        "de": "Kein klares CTA auf der Startseite",
        "en": "No clear call-to-action on the homepage",
        "ru": "Нет явного CTA на главной",
        "uk": "Немає чіткого CTA на головній",
        "fr": "Pas de CTA clair sur la page d'accueil",
        "es": "Sin CTA claro en la portada",
        "nl": "Geen duidelijke CTA op de homepage",
        "pl": "Brak wyraźnego CTA na stronie głównej",
        "cs": "Žádné jasné CTA na úvodní stránce",
        "pt": "Sem CTA claro na página inicial",
        "it": "Nessun CTA chiaro in homepage",
    },
    "no_maps": {
        "de": "Keine Google Maps Einbindung erkannt",
        "en": "No Google Maps embed detected",
        "ru": "Встраивание Google Maps не найдено",
        "uk": "Вбудовування Google Maps не знайдено",
        "fr": "Pas d'intégration Google Maps détectée",
        "es": "No se detectó Google Maps",
        "nl": "Geen Google Maps-inbedding gevonden",
        "pl": "Nie wykryto Google Maps",
        "cs": "Nebylo nalezeno vložení Google Maps",
        "pt": "Nenhuma incorporação Google Maps detetada",
        "it": "Nessuna mappa Google Maps rilevata",
    },
    "no_title": {
        "de": "Kein Seitentitel — schlecht für SEO",
        "en": "No page title — weak for SEO",
        "ru": "Нет заголовка страницы — плохо для SEO",
        "uk": "Немає заголовка сторінки — погано для SEO",
        "fr": "Pas de titre de page — mauvais pour le SEO",
        "es": "Sin título de página — malo para SEO",
        "nl": "Geen paginatitel — slecht voor SEO",
        "pl": "Brak tytułu strony — słabo pod SEO",
        "cs": "Chybí titulek stránky — špatné pro SEO",
        "pt": "Sem título de página — fraco para SEO",
        "it": "Nessun titolo pagina — debole per SEO",
    },
    "no_social_meta": {
        "de": "Keine Social-Meta-Tags — schwache Vorschau in Messengern",
        "en": "No social meta tags — weak preview in messengers",
        "ru": "Нет social meta — слабый превью в мессенджерах",
        "uk": "Немає social meta — слабкий прев'ю в месенджерах",
        "fr": "Pas de meta sociales — aperçu faible dans les messageries",
        "es": "Sin meta sociales — vista previa débil en mensajería",
        "nl": "Geen social meta-tags — zwakke preview in messengers",
        "pl": "Brak social meta — słaby podgląd w communicatorach",
        "cs": "Chybí social meta — slabý náhled v messengerech",
        "pt": "Sem meta sociais — pré-visualização fraca em messengers",
        "it": "Niente meta social — anteprima debole nei messenger",
    },
    "slow_response": {
        "de": "Langsame Antwort (~{ms} ms)",
        "en": "Slow response (~{ms} ms)",
        "ru": "Медленный ответ (~{ms} мс)",
        "uk": "Повільна відповідь (~{ms} мс)",
        "fr": "Réponse lente (~{ms} ms)",
        "es": "Respuesta lenta (~{ms} ms)",
        "nl": "Trage reactie (~{ms} ms)",
        "pl": "Wolna odpowiedź (~{ms} ms)",
        "cs": "Pomalá odpověď (~{ms} ms)",
        "pt": "Resposta lenta (~{ms} ms)",
        "it": "Risposta lenta (~{ms} ms)",
    },
    "unreachable": {
        "de": "Website nicht erreichbar oder ungültige URL",
        "en": "Website unreachable or invalid URL",
        "ru": "Сайт недоступен или неверный URL",
        "uk": "Сайт недоступний або невірний URL",
        "fr": "Site inaccessible ou URL invalide",
        "es": "Sitio inaccesible o URL inválida",
        "nl": "Website niet bereikbaar of ongeldige URL",
        "pl": "Strona niedostępna lub nieprawidłowy URL",
        "cs": "Web nedostupný nebo neplatná URL",
        "pt": "Site inacessível ou URL inválido",
        "it": "Sito non raggiungibile o URL non valido",
    },
}

_STRENGTH_MSGS: dict[str, dict[str, str]] = {
    "https_ok": {
        "de": "HTTPS aktiv",
        "en": "HTTPS active",
        "ru": "HTTPS активен",
        "uk": "HTTPS активний",
        "fr": "HTTPS actif",
        "es": "HTTPS activo",
        "nl": "HTTPS actief",
        "pl": "HTTPS aktywny",
        "cs": "HTTPS aktivní",
        "pt": "HTTPS ativo",
        "it": "HTTPS attivo",
    },
    "reachable": {
        "de": "Seite erreichbar",
        "en": "Site reachable",
        "ru": "Сайт доступен",
        "uk": "Сайт доступний",
        "fr": "Site accessible",
        "es": "Sitio accesible",
        "nl": "Site bereikbaar",
        "pl": "Strona dostępna",
        "cs": "Stránka dostupná",
        "pt": "Site acessível",
        "it": "Sito raggiungibile",
    },
    "viewport_ok": {
        "de": "Viewport für Mobilgeräte",
        "en": "Mobile viewport present",
        "ru": "Viewport для мобильных",
        "uk": "Viewport для мобільних",
        "fr": "Viewport mobile présent",
        "es": "Viewport móvil presente",
        "nl": "Mobiele viewport aanwezig",
        "pl": "Viewport mobilny obecny",
        "cs": "Mobilní viewport přítomen",
        "pt": "Viewport móvel presente",
        "it": "Viewport mobile presente",
    },
    "contact_ok": {
        "de": "Kontaktweg sichtbar",
        "en": "Contact path visible",
        "ru": "Контакт виден",
        "uk": "Контакт видно",
        "fr": "Chemin de contact visible",
        "es": "Ruta de contacto visible",
        "nl": "Contactpad zichtbaar",
        "pl": "Ścieżka kontaktu widoczna",
        "cs": "Kontaktní cesta viditelná",
        "pt": "Caminho de contacto visível",
        "it": "Percorso contatto visibile",
    },
    "cta_ok": {
        "de": "CTA erkennbar",
        "en": "CTA recognizable",
        "ru": "CTA заметен",
        "uk": "CTA помітний",
        "fr": "CTA identifiable",
        "es": "CTA reconocible",
        "nl": "CTA herkenbaar",
        "pl": "CTA rozpoznawalny",
        "cs": "CTA rozpoznatelné",
        "pt": "CTA reconhecível",
        "it": "CTA riconoscibile",
    },
    "maps_ok": {
        "de": "Karte / Maps gefunden",
        "en": "Map / Maps found",
        "ru": "Карта найдена",
        "uk": "Карту знайдено",
        "fr": "Carte / Maps trouvée",
        "es": "Mapa encontrado",
        "nl": "Kaart / Maps gevonden",
        "pl": "Mapa znaleziona",
        "cs": "Mapa nalezena",
        "pt": "Mapa encontrado",
        "it": "Mappa trovata",
    },
    "load_ok": {
        "de": "Ladezeit ~{ms} ms",
        "en": "Load time ~{ms} ms",
        "ru": "Загрузка ~{ms} мс",
        "uk": "Завантаження ~{ms} мс",
        "fr": "Chargement ~{ms} ms",
        "es": "Carga ~{ms} ms",
        "nl": "Laadtijd ~{ms} ms",
        "pl": "Czas ładowania ~{ms} ms",
        "cs": "Načítání ~{ms} ms",
        "pt": "Carregamento ~{ms} ms",
        "it": "Caricamento ~{ms} ms",
    },
}

# Exact German (legacy cache) → code
_LEGACY_DE_EXACT: dict[str, str] = {
    v["de"]: code for code, v in _ISSUE_MSGS.items() if "de" in v and "{" not in v["de"]
}
_LEGACY_DE_EXACT.update(
    {v["de"]: code for code, v in _STRENGTH_MSGS.items() if "de" in v and "{" not in v["de"]}
)


def analysis_lang_base(language: str | None = None, market: str | None = None) -> str:
    try:
        from app.integration.locale_service import resolve_generation_language

        resolved = resolve_generation_language(language, market_code=market)
    except Exception:
        resolved = language or "en"
    base = str(resolved or "en").lower().strip().replace("_", "-").split("-")[0]
    if base in _ISSUE_MSGS["no_https"]:
        return base
    return "en"


def issue_message(code: str, lang: str, **fmt: Any) -> str:
    pack = _ISSUE_MSGS.get(code) or {}
    text = pack.get(lang) or pack.get("en") or pack.get("de") or code
    try:
        return text.format(**fmt) if fmt else text
    except (KeyError, ValueError):
        return text


def strength_message(code: str, lang: str, **fmt: Any) -> str:
    pack = _STRENGTH_MSGS.get(code) or {}
    text = pack.get(lang) or pack.get("en") or pack.get("de") or code
    try:
        return text.format(**fmt) if fmt else text
    except (KeyError, ValueError):
        return text


def _guess_issue_code(text: str) -> tuple[str | None, dict[str, Any]]:
    low = (text or "").lower()
    m = re.search(r"http\s*(\d{3})", low)
    if m and ("antwort" in low or "respond" in low or "répond" in low or "отвечает" in low):
        return "http_error", {"status": m.group(1)}
    m = re.search(r"~?\s*(\d+)\s*ms", low)
    if m and ("langsam" in low or "slow" in low or "медлен" in low or "trage" in low):
        return "slow_response", {"ms": m.group(1)}
    markers = (
        ("https", "no_https"),
        ("viewport", "no_viewport"),
        ("platzhalter", "thin_content"),
        ("placeholder", "thin_content"),
        ("wenig inhalt", "thin_content"),
        ("little content", "thin_content"),
        ("veraltet", "outdated_tech"),
        ("outdated", "outdated_tech"),
        ("baustelle", "outdated_tech"),
        ("kontaktformular", "no_contact_form"),
        ("contact form", "no_contact_form"),
        ("whatsapp", "no_call_whatsapp"),
        ("cta", "no_cta"),
        ("maps", "no_maps"),
        ("seitentitel", "no_title"),
        ("page title", "no_title"),
        ("social-meta", "no_social_meta"),
        ("social meta", "no_social_meta"),
        ("nicht erreichbar", "unreachable"),
        ("unreachable", "unreachable"),
    )
    for needle, code in markers:
        if needle in low:
            return code, {}
    return None, {}


def localize_analysis_issues(
    issues: list[str] | None,
    *,
    language: str | None = None,
    market: str | None = None,
    codes: list[str] | None = None,
) -> list[str]:
    """Re-emit issue lines in target language (legacy DE cache → EN/etc.)."""
    lang = analysis_lang_base(language, market)
    out: list[str] = []
    if codes:
        for raw in codes:
            code = str(raw or "").strip()
            if not code:
                continue
            # codes may be "http_error:403" or "slow_response:3200"
            if ":" in code:
                base, arg = code.split(":", 1)
                if base == "http_error":
                    out.append(issue_message(base, lang, status=arg))
                elif base == "slow_response":
                    out.append(issue_message(base, lang, ms=arg))
                else:
                    out.append(issue_message(base, lang))
            else:
                out.append(issue_message(code, lang))
        return out

    for raw in issues or ():
        text = str(raw or "").strip()
        if not text:
            continue
        code = _LEGACY_DE_EXACT.get(text)
        fmt: dict[str, Any] = {}
        if not code:
            # Parametric legacy DE
            m = re.match(r"Seite antwortet mit HTTP (\d+)", text)
            if m:
                code, fmt = "http_error", {"status": m.group(1)}
            else:
                m = re.match(r"Langsame Antwort \(~(\d+) ms\)", text)
                if m:
                    code, fmt = "slow_response", {"ms": m.group(1)}
        if not code:
            code, fmt = _guess_issue_code(text)
        if code:
            out.append(issue_message(code, lang, **fmt))
        else:
            # Drop leftover German fingerprints outside DE; keep other unknowns.
            if lang != "de" and re.search(
                r"\b(kein|keine|antwortet|seitentitel|öffnungs|langsam)\b",
                text,
                re.I,
            ):
                continue
            out.append(text)
    return out
