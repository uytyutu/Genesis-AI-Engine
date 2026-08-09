"""Niche composition DNA — silhouette recognition without reading text.

Rule (Owner):
  If you remove all text, is the site still recognizable?
  If you replace the logo, can you still name the niche from composition alone?
  If no → REBUILD.

This is NOT a template skin. Each niche owns rhythm, type scale, media crop,
and motion bias — so Premium Auto ≠ Premium Psychology with swapped photos.
"""

from __future__ import annotations

# Niche → CSS variables + layout bias injected on body[data-niche]
NICHE_COMPOSITION_CSS: dict[str, str] = {
    "auto": """
body[data-niche="auto"] {
  --nc-hero-min: 88vh;
  --nc-split: 1.25fr 0.85fr;
  --nc-type-display: clamp(2.4rem, 5.5vw, 4.2rem);
  --nc-type-lead: 1.35;
  --nc-type-track: -0.035em;
  --nc-pad-y: clamp(2rem, 5vw, 3.5rem);
  --nc-density: compact;
  --nc-accent-line: 3px;
}
body[data-niche="auto"] [data-split-hero="1"] {
  grid-template-columns: var(--nc-split);
  min-height: var(--nc-hero-min);
  clip-path: polygon(0 0, 100% 0, 100% 94%, 0 100%);
}
body[data-niche="auto"] [data-split-hero="1"] h1 {
  font-size: var(--nc-type-display);
  letter-spacing: var(--nc-type-track);
  line-height: 1.05;
  max-width: 14ch;
  text-wrap: balance;
}
body[data-niche="auto"] .rx-band-grid {
  grid-template-columns: 1.4fr 1fr 1fr;
  gap: .5rem;
}
body[data-niche="auto"] .rx-band-cell:first-child .rx-band-img { min-height: 260px; }
body[data-niche="auto"] .rx-svc-media { min-height: 170px; transform: skewY(-1.2deg); transform-origin: left; }
""",
    "psychology": """
body[data-niche="psychology"] {
  --nc-hero-min: 82vh;
  --nc-split: 0.85fr 1.15fr;
  --nc-type-display: clamp(2.1rem, 4.2vw, 3.4rem);
  --nc-type-lead: 1.65;
  --nc-type-track: -0.02em;
  --nc-pad-y: clamp(3.5rem, 9vw, 6.5rem);
  --nc-density: airy;
}
body[data-niche="psychology"] [data-split-hero="1"] {
  grid-template-columns: var(--nc-split);
  min-height: var(--nc-hero-min);
  gap: 0;
}
body[data-niche="psychology"] [data-split-hero="1"] h1 {
  font-size: var(--nc-type-display);
  letter-spacing: var(--nc-type-track);
  line-height: 1.12;
  max-width: 11ch;
  font-weight: 450;
}
body[data-niche="psychology"] .fi-arc { gap: 1.15rem; }
body[data-niche="psychology"] .fi-emotion,
body[data-niche="psychology"] .fi-offer {
  line-height: var(--nc-type-lead);
  max-width: 28ch;
}
body[data-niche="psychology"] .rx-services,
body[data-niche="psychology"] .rx-about,
body[data-niche="psychology"] .rx-photo-band {
  padding-top: var(--nc-pad-y);
  padding-bottom: var(--nc-pad-y);
  max-width: 780px;
}
body[data-niche="psychology"] .rx-svc-grid { grid-template-columns: 1fr; gap: 0; }
body[data-niche="psychology"] .rx-svc-card {
  border: 0; border-bottom: 1px solid rgba(28,25,22,.12);
  background: transparent; display: grid; grid-template-columns: 120px 1fr;
}
body[data-niche="psychology"] .rx-band-grid { grid-template-columns: 1fr 1fr; gap: 1.25rem; }
body[data-niche="psychology"] .rx-band-cell:nth-child(n+5) { display: none; }
/* Soft ink on light panels — contrast for morning scenes */
body[data-niche="psychology"] .ed-hero-copy,
body[data-niche="psychology"] .ed-hero-copy h1,
body[data-niche="psychology"] .ed-hero-copy .fi-arc {
  color: #1a1714 !important;
}
body[data-niche="psychology"] .ed-link,
body[data-niche="psychology"] .fi-actions a {
  color: #1a1714 !important;
  border-color: rgba(26,23,20,.45);
}
body[data-niche="psychology"] .ed-hero-media {
  filter: saturate(0.88) contrast(1.06) brightness(1.02);
}
body[data-niche="psychology"] .ed-hero-media::after {
  background: linear-gradient(90deg, rgba(247,244,239,.15), rgba(247,244,239,.92) 88%);
}
""",
    "family_psychology": """
body[data-niche="family_psychology"] {
  --nc-hero-min: 84vh;
  --nc-split: 0.8fr 1.2fr;
  --nc-type-display: clamp(2rem, 4vw, 3.25rem);
  --nc-type-lead: 1.7;
  --nc-type-track: -0.018em;
  --nc-pad-y: clamp(3.75rem, 10vw, 7rem);
  --nc-density: airy;
}
body[data-niche="family_psychology"] [data-split-hero="1"] {
  grid-template-columns: var(--nc-split);
  min-height: var(--nc-hero-min);
  gap: 0;
}
body[data-niche="family_psychology"] [data-split-hero="1"] h1 {
  font-size: var(--nc-type-display);
  letter-spacing: var(--nc-type-track);
  line-height: 1.14;
  max-width: 10ch;
  font-weight: 420;
}
body[data-niche="family_psychology"] .fi-arc { gap: 1.35rem; }
body[data-niche="family_psychology"] .fi-emotion,
body[data-niche="family_psychology"] .fi-offer {
  line-height: var(--nc-type-lead);
  max-width: 26ch;
}
body[data-niche="family_psychology"] .rx-services,
body[data-niche="family_psychology"] .rx-about,
body[data-niche="family_psychology"] .rx-photo-band {
  padding-top: var(--nc-pad-y);
  padding-bottom: var(--nc-pad-y);
  max-width: 720px;
}
body[data-niche="family_psychology"] .rx-svc-grid { grid-template-columns: 1fr; gap: 0; }
body[data-niche="family_psychology"] .rx-svc-card {
  border: 0; border-bottom: 1px solid rgba(28,25,22,.1);
  background: transparent; display: grid; grid-template-columns: 100px 1fr;
  padding: 1.5rem 0;
}
body[data-niche="family_psychology"] .rx-band-grid { grid-template-columns: 1fr 1fr; gap: 1.5rem; }
body[data-niche="family_psychology"] .rx-band-cell:nth-child(n+5) { display: none; }
body[data-niche="family_psychology"] .ed-hero-copy,
body[data-niche="family_psychology"] .ed-hero-copy h1,
body[data-niche="family_psychology"] .ed-hero-copy .fi-arc {
  color: #1a1714 !important;
}
body[data-niche="family_psychology"] .ed-link,
body[data-niche="family_psychology"] .fi-actions a {
  color: #1a1714 !important;
}
body[data-niche="family_psychology"] .ed-hero-media::after {
  background: linear-gradient(90deg, rgba(246,240,232,.1), rgba(246,240,232,.95) 90%);
}
""",
    "car_dealership": """
body[data-niche="car_dealership"] {
  --nc-hero-min: 94vh;
  --nc-split: 1.45fr 0.7fr;
  --nc-type-display: clamp(2.8rem, 6.5vw, 5.2rem);
  --nc-type-track: -0.045em;
  --nc-pad-y: clamp(2rem, 5vw, 3.25rem);
  --nc-density: cinematic;
}
body[data-niche="car_dealership"] [data-split-hero="1"] {
  grid-template-columns: var(--nc-split);
  min-height: var(--nc-hero-min);
}
body[data-niche="car_dealership"] [data-split-hero="1"] h1 {
  font-size: var(--nc-type-display);
  letter-spacing: var(--nc-type-track);
  line-height: 0.98;
  max-width: 9ch;
  font-weight: 380;
  color: #f5f0e8 !important;
}
body[data-niche="car_dealership"] .lx-band,
body[data-niche="car_dealership"] .lx-band .fi-arc {
  color: #f5f0e8 !important;
  /* Transparent scrim so Studio WebGL / hero media remain visible */
  background: linear-gradient(105deg, rgba(7,9,12,.48), rgba(7,9,12,.06)) !important;
  background-color: transparent !important;
}
body[data-niche="car_dealership"] .lx-enter,
body[data-niche="car_dealership"] .fi-actions a {
  color: #f5f0e8 !important;
  border-bottom-color: rgba(245,240,232,.55);
}
body[data-niche="car_dealership"] .lx-hero-media {
  filter: contrast(1.12) saturate(0.92) brightness(0.92);
}
body[data-niche="car_dealership"] .lx-hero-media::after {
  background: linear-gradient(105deg, transparent 35%, rgba(7,9,12,.75));
}
body[data-niche="car_dealership"] .rx-band-grid {
  grid-template-columns: 1.6fr 1fr 1fr;
  gap: .35rem;
}
body[data-niche="car_dealership"] .rx-band-img { min-height: 280px; }
body[data-niche="car_dealership"] .rx-svc-grid { grid-template-columns: repeat(3, 1fr); }
body[data-niche="car_dealership"] .rx-svc-media { min-height: 160px; }
""",
    "restaurant": """
body[data-niche="restaurant"] {
  --nc-hero-min: 92vh;
  --nc-split: 1.35fr 0.75fr;
  --nc-type-display: clamp(2.6rem, 6vw, 4.8rem);
  --nc-type-track: -0.04em;
}
body[data-niche="restaurant"] [data-split-hero="1"] {
  grid-template-columns: var(--nc-split);
  min-height: var(--nc-hero-min);
}
body[data-niche="restaurant"] [data-split-hero="1"] h1 {
  font-size: var(--nc-type-display);
  letter-spacing: var(--nc-type-track);
  line-height: 1; max-width: 10ch; font-weight: 400;
}
body[data-niche="restaurant"] .rx-about {
  grid-template-columns: 1.2fr 0.8fr;
}
body[data-niche="restaurant"] .rx-about-media { min-height: 420px; }
body[data-niche="restaurant"] .rx-band-grid {
  grid-template-columns: 1fr 1fr;
  gap: .4rem;
}
body[data-niche="restaurant"] .rx-band-img { min-height: 240px; opacity: .95; }
body[data-niche="restaurant"] .rx-band-cell:nth-child(3) {
  grid-column: 1 / -1;
}
body[data-niche="restaurant"] .rx-band-cell:nth-child(3) .rx-band-img { min-height: 320px; }
body[data-niche="restaurant"] .rx-svc-media { min-height: 200px; }
body[data-niche="restaurant"] .rt-plate,
body[data-niche="restaurant"] .rt-plate .fi-arc {
  color: #faf6f1 !important;
  background: #140e0a !important;
}
body[data-niche="restaurant"] .rt-btn,
body[data-niche="restaurant"] .fi-actions a {
  color: #faf6f1 !important;
  border-color: rgba(250,246,241,.65) !important;
}
body[data-niche="restaurant"] .rt-hero-media {
  filter: saturate(1.08) contrast(1.08) brightness(0.9);
}
body[data-niche="restaurant"] .rt-hero-media::after {
  background: linear-gradient(100deg, transparent 30%, rgba(20,14,10,.7));
}
""",
    "law": """
body[data-niche="law"] {
  --nc-hero-min: 72vh;
  --nc-split: 0.7fr 1.3fr;
  --nc-type-display: clamp(2rem, 3.8vw, 3.1rem);
  --nc-type-lead: 1.55;
  --nc-type-track: -0.015em;
}
body[data-niche="law"] [data-split-hero="1"] {
  grid-template-columns: var(--nc-split);
  min-height: var(--nc-hero-min);
}
body[data-niche="law"] [data-split-hero="1"] h1 {
  font-size: var(--nc-type-display);
  letter-spacing: var(--nc-type-track);
  line-height: 1.15; max-width: 16ch; font-weight: 500;
}
body[data-niche="law"] .rx-svc-grid {
  grid-template-columns: 1fr 1fr;
  gap: 0;
}
body[data-niche="law"] .rx-svc-card {
  border-radius: 0; border: 0;
  border-top: 1px solid rgba(20,22,28,.14);
  background: transparent;
  display: grid; grid-template-columns: 0 1fr;
}
body[data-niche="law"] .rx-svc-media { display: none; }
body[data-niche="law"] .rx-band-grid { grid-template-columns: repeat(4, 1fr); }
body[data-niche="law"] .rx-band-cell:nth-child(n+5) { display: none; }
body[data-niche="law"] .rx-band-img { min-height: 120px; opacity: .75; }
body[data-niche="law"] .rx-photo-band h2 { font-size: 1.15rem; font-weight: 500; }
""",
    "dachreinigung": """
body[data-niche="dachreinigung"] {
  --nc-hero-min: 90vh;
  --nc-split: 1.2fr 0.9fr;
  --nc-type-display: clamp(2.2rem, 4.8vw, 3.6rem);
}
body[data-niche="dachreinigung"] [data-split-hero="1"] {
  grid-template-columns: var(--nc-split);
  min-height: var(--nc-hero-min);
}
body[data-niche="dachreinigung"] [data-split-hero="1"] h1 {
  font-size: var(--nc-type-display);
  line-height: 1.08; max-width: 15ch; font-weight: 650;
}
body[data-niche="dachreinigung"] .rx-about {
  grid-template-columns: 1fr 1fr;
}
body[data-niche="dachreinigung"] .rx-svc-grid {
  grid-template-columns: repeat(2, 1fr);
}
body[data-niche="dachreinigung"] .rx-band-grid {
  grid-template-columns: 1.1fr 0.9fr 1fr;
}
body[data-niche="dachreinigung"] .cr-case-wall,
body[data-niche="dachreinigung"] .rx-band-img {
  filter: contrast(1.06) saturate(1.05);
}
""",
    "handwerk": """
body[data-niche="handwerk"] {
  --nc-hero-min: 88vh;
  --nc-split: 1.2fr 0.9fr;
  --nc-type-display: clamp(2.2rem, 4.6vw, 3.6rem);
}
body[data-niche="handwerk"] [data-split-hero="1"] {
  grid-template-columns: var(--nc-split);
  min-height: var(--nc-hero-min);
}
body[data-niche="handwerk"] [data-split-hero="1"] h1 {
  font-size: var(--nc-type-display); max-width: 13ch; font-weight: 680;
}
body[data-niche="handwerk"] .cr-hero-board,
body[data-niche="handwerk"] .cr-hero-board .fi-arc {
  color: #f8f4ec !important;
  background: linear-gradient(180deg, rgba(18,12,6,.92), rgba(18,12,6,.97)) !important;
}
body[data-niche="handwerk"] .cr-btn {
  background: #f59e0b !important;
  color: #1a1008 !important;
  font-weight: 700;
}
body[data-niche="handwerk"] .rx-svc-grid { grid-template-columns: repeat(2, 1fr); }
body[data-niche="handwerk"] .rx-band-grid { grid-template-columns: repeat(3, 1fr); }
body[data-niche="handwerk"] .cr-case-wall { filter: contrast(1.05) saturate(1.08); }
""",
    "beauty": """
body[data-niche="beauty"] {
  --nc-hero-min: 84vh;
  --nc-split: 0.95fr 1.05fr;
  --nc-type-display: clamp(2.3rem, 5vw, 3.8rem);
  --nc-type-track: -0.03em;
}
body[data-niche="beauty"] [data-split-hero="1"] {
  grid-template-columns: var(--nc-split);
  min-height: var(--nc-hero-min);
}
body[data-niche="beauty"] [data-split-hero="1"] h1 {
  font-size: var(--nc-type-display);
  letter-spacing: var(--nc-type-track);
  line-height: 1.06; max-width: 12ch; font-weight: 400;
}
body[data-niche="beauty"] .rx-svc-grid { grid-template-columns: repeat(3, 1fr); }
body[data-niche="beauty"] .rx-band-img { min-height: 200px; border-radius: 1px; }
""",
    "dental": """
body[data-niche="dental"] {
  --nc-hero-min: 82vh;
  --nc-split: 1fr 1fr;
  --nc-type-display: clamp(2.05rem, 3.9vw, 3.15rem);
}
body[data-niche="dental"] [data-split-hero="1"] {
  grid-template-columns: var(--nc-split);
  min-height: var(--nc-hero-min);
}
body[data-niche="dental"] [data-split-hero="1"] h1 {
  font-size: var(--nc-type-display); max-width: 13ch; font-weight: 560;
  color: #0f172a !important;
}
body[data-niche="dental"] .cl-panel,
body[data-niche="dental"] .cl-panel .fi-arc {
  color: #0f172a !important;
  background: #f8fafc !important;
}
body[data-niche="dental"] .cl-btn {
  background: #0f766e !important;
  color: #fff !important;
}
body[data-niche="dental"] .cl-hero-media {
  filter: saturate(0.85) brightness(1.06) contrast(1.04);
}
body[data-niche="dental"] .cl-hero-media::after {
  background: linear-gradient(90deg, rgba(248,250,252,.05), rgba(248,250,252,.88) 85%);
}
body[data-niche="dental"] .rx-svc-grid { grid-template-columns: repeat(2, 1fr); gap: 1rem; }
body[data-niche="dental"] .rx-band-grid { grid-template-columns: 1fr 1fr 1fr; gap: .75rem; }
""",
    "fitness": """
body[data-niche="fitness"] {
  --nc-hero-min: 90vh;
  --nc-split: 1.3fr 0.8fr;
  --nc-type-display: clamp(2.5rem, 5.5vw, 4.4rem);
  --nc-type-track: -0.045em;
}
body[data-niche="fitness"] [data-split-hero="1"] {
  grid-template-columns: var(--nc-split);
  min-height: var(--nc-hero-min);
}
body[data-niche="fitness"] [data-split-hero="1"] h1 {
  font-size: var(--nc-type-display);
  letter-spacing: var(--nc-type-track);
  text-transform: uppercase; max-width: 12ch; line-height: .95;
}
body[data-niche="fitness"] .rx-band-grid { grid-template-columns: 1.5fr 1fr 1fr; }
""",
    "realestate": """
body[data-niche="realestate"] {
  --nc-hero-min: 85vh;
  --nc-split: 1.1fr 0.9fr;
  --nc-type-display: clamp(2.2rem, 4.5vw, 3.6rem);
}
body[data-niche="realestate"] [data-split-hero="1"] {
  grid-template-columns: var(--nc-split);
  min-height: var(--nc-hero-min);
}
body[data-niche="realestate"] [data-split-hero="1"] h1 {
  font-size: var(--nc-type-display); max-width: 13ch; font-weight: 450;
}
body[data-niche="realestate"] .rx-about-media { min-height: 380px; }
body[data-niche="realestate"] .rx-band-grid { grid-template-columns: 1.4fr 1fr 1fr; }
""",
}

# Shared: readable type + contrast floor + micro-life (not decoration)
COMPOSITION_BASE_CSS = """
/* Virtus Core floor — never weaker than marketing /site readability */
[data-split-hero="1"] > *:last-child {
  position: relative;
  z-index: 2;
  background: inherit;
}
/* Text on media / dark panels must stay readable — no washout */
.fi-arc h1,
[data-split-hero="1"] h1 {
  color: inherit;
  text-shadow: none;
  -webkit-font-smoothing: antialiased;
}
.fi-problem, .fi-emotion, .fi-trust, .fi-offer, .fi-idea, .rx-hero-eyebrow {
  opacity: 1 !important;
  color: inherit;
}
.fi-problem { opacity: .72 !important; }
.fi-idea { opacity: .65 !important; font-style: italic; }
/* Dark shells → explicit ink */
.co-band, .lx-band, .rt-plate, .cr-hero-board, .mn-band {
  color: #f4f1ea;
}
.co-band .fi-problem, .lx-band .fi-problem, .rt-plate .fi-problem,
.cr-hero-board .fi-problem, .mn-band .fi-problem { color: rgba(244,241,234,.72); }
.co-band .fi-emotion, .lx-band .fi-emotion, .rt-plate .fi-emotion,
.cr-hero-board .fi-emotion, .mn-band .fi-emotion,
.co-band .fi-trust, .lx-band .fi-trust, .rt-plate .fi-trust,
.cr-hero-board .fi-trust, .mn-band .fi-trust,
.co-band .fi-offer, .lx-band .fi-offer, .rt-plate .fi-offer,
.cr-hero-board .fi-offer, .mn-band .fi-offer { color: rgba(244,241,234,.92); }
/* Light shells → dark ink */
.ed-hero-copy, .cl-panel, .lg-band {
  color: #14161c;
  background: #f7f4ef;
}
.ed-hero-copy .fi-problem, .cl-panel .fi-problem, .lg-band .fi-problem {
  color: rgba(20,22,28,.62);
}
.ed-hero-copy .fi-emotion, .cl-panel .fi-emotion, .lg-band .fi-emotion,
.ed-hero-copy .fi-trust, .cl-panel .fi-trust, .lg-band .fi-trust,
.ed-hero-copy .fi-offer, .cl-panel .fi-offer, .lg-band .fi-offer {
  color: rgba(20,22,28,.88);
}
/* Micro-life — site breathes */
@keyframes nc-rise {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes nc-fade {
  from { opacity: 0; }
  to { opacity: 1; }
}
[data-split-hero="1"] .fi-arc > * {
  animation: nc-rise .7s ease both;
}
[data-split-hero="1"] .fi-arc > *:nth-child(1) { animation-delay: .05s; }
[data-split-hero="1"] .fi-arc > *:nth-child(2) { animation-delay: .12s; }
[data-split-hero="1"] .fi-arc > *:nth-child(3) { animation-delay: .2s; }
[data-split-hero="1"] .fi-arc > *:nth-child(4) { animation-delay: .28s; }
[data-split-hero="1"] .fi-arc > *:nth-child(5) { animation-delay: .36s; }
.rx-svc-card, .rx-band-cell {
  transition: transform .35s ease, box-shadow .35s ease, opacity .35s ease;
}
.rx-svc-card:hover, .rx-band-cell:hover {
  transform: translateY(-3px);
}
.rx-band-img { transition: opacity .4s ease, filter .4s ease; }
.rx-band-cell:hover .rx-band-img { opacity: 1; filter: saturate(1.08); }
.topbar-cta, .fi-actions a, .co-btn, .cl-btn, .rt-btn, .cr-btn, .lx-enter, .mn-cta {
  transition: transform .2s ease, background .2s ease, opacity .2s ease;
}
.topbar-cta:hover, .fi-actions a:hover, .co-btn:hover, .cl-btn:hover,
.rt-btn:hover, .cr-btn:hover { transform: translateY(-1px); }
@media (prefers-reduced-motion: reduce) {
  [data-split-hero="1"] .fi-arc > *,
  .rx-svc-card, .rx-band-cell, .rx-band-img,
  .topbar-cta, .fi-actions a { animation: none !important; transition: none !important; }
}
"""


def niche_composition_css(niche_id: str) -> str:
    key = (niche_id or "").strip().lower()
    parts = [COMPOSITION_BASE_CSS]
    specific = NICHE_COMPOSITION_CSS.get(key)
    if specific:
        parts.append(specific)
    else:
        # Generic but still not flat — slight air + readable floor
        parts.append(
            """
body[data-niche]:not([data-niche=""]) [data-split-hero="1"] h1 {
  font-size: clamp(2rem, 4.2vw, 3.3rem);
  line-height: 1.1; max-width: 15ch;
}
"""
        )
    return "\n".join(parts)


__all__ = ["niche_composition_css", "NICHE_COMPOSITION_CSS", "COMPOSITION_BASE_CSS"]
