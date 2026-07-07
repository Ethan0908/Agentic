from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping


def _text(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    return text or fallback


def _items(value: Any) -> list[Any]:
    return value if isinstance(value, list) else ([] if value in (None, "") else [value])


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return cleaned or "premium-site"


def infer_signature(business: Mapping[str, Any]) -> dict[str, Any]:
    blob = " ".join(
        str(part or "")
        for part in [business.get("businessType"), business.get("brandTone"), business.get("description"), business.get("name")]
    ).lower()
    photos = _items(business.get("photos"))
    has_photos = bool(photos)

    if any(term in blob for term in ("dental", "clinic", "medical", "therapy", "health", "doctor")):
        archetype = "quiet-clinical-editorial"
        palette = {"ink": "#17201d", "paper": "#f7f5ef", "muted": "#dfe7df", "accent": "#4f7d68", "deep": "#0d1412"}
    elif any(term in blob for term in ("omakase", "restaurant", "bakery", "cafe", "spa", "salon", "studio", "boutique", "gallery")):
        archetype = "gallery-led-luxury"
        palette = {"ink": "#1b1611", "paper": "#f8f0e4", "muted": "#ead7bf", "accent": "#9b6845", "deep": "#120d09"}
    elif any(term in blob for term in ("law", "finance", "consult", "accounting", "insurance", "real estate")):
        archetype = "technical-proof-dossier"
        palette = {"ink": "#10151f", "paper": "#f4f6f8", "muted": "#d8deea", "accent": "#365c8d", "deep": "#090d14"}
    elif any(term in blob for term in ("plumb", "repair", "construction", "contractor", "electric", "hvac", "roof", "clean")):
        archetype = "local-field-guide"
        palette = {"ink": "#181713", "paper": "#f4efe3", "muted": "#ded4bf", "accent": "#9f5f2b", "deep": "#12100c"}
    else:
        archetype = "editorial-local-brand"
        palette = {"ink": "#141414", "paper": "#f6f2ea", "muted": "#dfd8cc", "accent": "#7b5f3f", "deep": "#0f0f0e"}

    return {
        "archetype": archetype,
        "hasPhotos": has_photos,
        "palette": palette,
        "layoutPrinciple": "premium editorial composition with varied section rhythm, not a repeated card stack",
        "qualityTarget": "expensive local-business site with strong hierarchy, restrained copy, cinematic spacing, and real CTA paths",
    }


def _page_tsx() -> str:
    return """import businessData from '../data/business.json';
import styleSignature from '../data/style-signature.json';

type Photo = { url?: string; alt?: string; caption?: string };
type Service = string | { title?: string; name?: string; description?: string };
type Business = {
  name?: string;
  businessType?: string;
  city?: string;
  serviceArea?: string;
  phone?: string;
  email?: string;
  website?: string;
  address?: string;
  primaryCta?: string;
  secondaryCta?: string;
  headline?: string;
  subheadline?: string;
  description?: string;
  services?: Service[];
  processSteps?: Service[];
  proofPoints?: Service[];
  reviews?: Service[];
  faqs?: Array<{ question?: string; answer?: string }>;
  photos?: Photo[];
  heroImage?: Photo | null;
  logo?: string;
};

const business = businessData as Business;
const signature = styleSignature as { archetype?: string; palette?: Record<string, string> };

function text(value: unknown, fallback = '') {
  return typeof value === 'string' && value.trim() ? value.trim() : fallback;
}

function itemTitle(item: Service, fallback: string) {
  if (typeof item === 'string') return item;
  return text(item.title || item.name, fallback);
}

function itemDescription(item: Service, fallback = '') {
  if (typeof item === 'string') return fallback;
  return text(item.description, fallback);
}

const name = text(business.name, 'Local Business');
const type = text(business.businessType, 'local business');
const area = text(business.serviceArea || business.city, 'the local area');
const description = text(business.description || business.subheadline, `${name} is a ${type} serving ${area}.`);
const headline = text(business.headline, `${name} brings ${type} service to ${area}.`);
const services = (business.services || []).slice(0, 6);
const process = (business.processSteps || []).slice(0, 4);
const proof = (business.proofPoints || business.reviews || []).slice(0, 4);
const photos = business.photos || [];
const hero = business.heroImage || photos[0];

const ctaHref = business.phone
  ? `tel:${business.phone.replace(/[^+0-9]/g, '')}`
  : business.email
    ? `mailto:${business.email}`
    : business.website || '#contact';
const ctaLabel = text(business.primaryCta, business.phone ? 'Call now' : business.website ? 'Visit website' : 'Contact');

function Header() {
  return (
    <header className="site-header">
      <a className="brand-mark" href="#top" aria-label={`${name} home`}>
        {business.logo ? <img src={business.logo} alt={`${name} logo`} /> : <span>{name.slice(0, 2)}</span>}
      </a>
      <nav aria-label="Site navigation">
        <a href="#services">Services</a>
        <a href="#process">Process</a>
        <a href="#contact">Contact</a>
      </nav>
      <a className="header-cta" href={ctaHref}>{ctaLabel}</a>
    </header>
  );
}

function HeroVisual() {
  if (hero?.url) {
    return (
      <figure className="hero-visual image-visual">
        <img src={hero.url} alt={hero.alt || `${name} photo`} />
        <figcaption>{text(hero.caption, `${type} in ${area}`)}</figcaption>
      </figure>
    );
  }
  return (
    <div className="hero-visual abstract-visual" aria-hidden="true">
      <div className="orb orb-one" />
      <div className="orb orb-two" />
      <div className="signature-card">
        <span>{signature.archetype || 'premium local brand'}</span>
        <strong>{area}</strong>
      </div>
    </div>
  );
}

function Hero() {
  return (
    <section id="top" className="hero-section">
      <div className="hero-copy">
        <p className="eyebrow">{type} · {area}</p>
        <h1>{headline}</h1>
        <p className="hero-deck">{description}</p>
        <div className="hero-actions">
          <a className="button button-primary" href={ctaHref}>{ctaLabel}</a>
          <a className="button button-secondary" href="#services">Review services</a>
        </div>
      </div>
      <HeroVisual />
    </section>
  );
}

function ProofRail() {
  const fallback = [
    `${type} support for ${area}`,
    business.address ? `Located at ${business.address}` : 'Clear next step before you commit',
    business.website ? 'Existing website available for more details' : 'Direct contact path available',
  ];
  const items = proof.length ? proof.map((item, index) => itemTitle(item, fallback[index] || 'Relevant service detail')) : fallback;
  return (
    <section className="proof-rail" aria-label="Business highlights">
      {items.slice(0, 4).map((item, index) => (
        <article key={item + index}>
          <span>{String(index + 1).padStart(2, '0')}</span>
          <p>{item}</p>
        </article>
      ))}
    </section>
  );
}

function Services() {
  const fallback = ['Consultation', 'Service review', 'Follow-up support'];
  const items = services.length ? services : fallback;
  return (
    <section id="services" className="chapter services-chapter">
      <div className="chapter-heading">
        <p className="eyebrow">What visitors need to know</p>
        <h2>Services presented with clarity, not filler.</h2>
      </div>
      <div className="service-matrix">
        {items.map((item, index) => (
          <article className={index === 0 ? 'service-card service-card-featured' : 'service-card'} key={itemTitle(item, `Service ${index + 1}`)}>
            <span className="service-index">{String(index + 1).padStart(2, '0')}</span>
            <h3>{itemTitle(item, fallback[index] || 'Service')}</h3>
            <p>{itemDescription(item, `Ask ${name} about this ${type} service in ${area}.`)}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

function Gallery() {
  if (!photos.length) return null;
  return (
    <section className="photo-ribbon" aria-label={`${name} photos`}>
      {photos.slice(0, 5).map((photo, index) => (
        <figure key={(photo.url || '') + index}>
          <img src={photo.url} alt={photo.alt || `${name} photo ${index + 1}`} />
        </figure>
      ))}
    </section>
  );
}

function Process() {
  const fallback = ['Share what you need', 'Confirm the right next step', 'Move forward with clear expectations'];
  const items = process.length ? process : fallback;
  return (
    <section id="process" className="chapter process-chapter">
      <div className="sticky-note">
        <p className="eyebrow">How it works</p>
        <h2>A simple path from interest to action.</h2>
      </div>
      <div className="process-list">
        {items.map((item, index) => (
          <article key={itemTitle(item, `Step ${index + 1}`)}>
            <span>{String(index + 1).padStart(2, '0')}</span>
            <div>
              <h3>{itemTitle(item, fallback[index] || 'Next step')}</h3>
              <p>{itemDescription(item, 'Use the contact path below to confirm details directly with the business.')}</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function Contact() {
  return (
    <section id="contact" className="contact-panel">
      <div>
        <p className="eyebrow">Contact</p>
        <h2>Ready to check availability or ask a direct question?</h2>
        <p>{business.address ? `Visit or contact ${name} at ${business.address}.` : `Contact ${name} for details about ${type} services in ${area}.`}</p>
      </div>
      <div className="contact-actions">
        <a className="button button-primary" href={ctaHref}>{ctaLabel}</a>
        {business.phone ? <a href={`tel:${business.phone.replace(/[^+0-9]/g, '')}`}>{business.phone}</a> : null}
        {business.email ? <a href={`mailto:${business.email}`}>{business.email}</a> : null}
        {business.website ? <a href={business.website}>Official website</a> : null}
      </div>
    </section>
  );
}

export default function Home() {
  return (
    <main className="luxury-page">
      <Header />
      <Hero />
      <ProofRail />
      <Services />
      <Gallery />
      <Process />
      <Contact />
      <a className="mobile-sticky-cta" href={ctaHref}>{ctaLabel}</a>
    </main>
  );
}
"""


def _globals_css() -> str:
    return """:root {
  --ink: #17140f;
  --paper: #f6f0e6;
  --paper-soft: #fffaf2;
  --muted: #dbcebb;
  --accent: #8b5d33;
  --accent-deep: #2e2015;
  --deep: #100d09;
  --line: rgba(23, 20, 15, 0.16);
  --line-light: rgba(255, 250, 242, 0.18);
  --shadow: 0 28px 90px rgba(27, 20, 12, 0.18);
  --radius-lg: 34px;
  --radius-md: 22px;
  --max: 1440px;
  color: var(--ink);
  background: var(--paper);
  font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  min-height: 100vh;
  background:
    radial-gradient(circle at 12% 10%, rgba(139, 93, 51, 0.18), transparent 34rem),
    radial-gradient(circle at 86% 4%, rgba(255, 250, 242, 0.78), transparent 26rem),
    linear-gradient(135deg, var(--paper-soft), var(--paper));
  color: var(--ink);
}
a { color: inherit; text-decoration: none; }
img { max-width: 100%; display: block; }

.luxury-page {
  width: 100%;
  overflow-x: hidden;
  position: relative;
}

.site-header {
  position: sticky;
  top: 18px;
  z-index: 20;
  width: min(calc(100% - 32px), var(--max));
  margin: 18px auto 0;
  padding: 10px 10px 10px 16px;
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 18px;
  border: 1px solid rgba(255,255,255,0.58);
  border-radius: 999px;
  background: rgba(255, 250, 242, 0.76);
  backdrop-filter: blur(22px);
  box-shadow: 0 18px 60px rgba(27, 20, 12, 0.12);
}

.brand-mark {
  display: inline-grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  overflow: hidden;
  background: var(--deep);
  color: var(--paper-soft);
  font-size: 0.8rem;
  font-weight: 800;
  letter-spacing: -0.04em;
}
.brand-mark img { width: 100%; height: 100%; object-fit: cover; }
.site-header nav { display: flex; justify-content: center; gap: clamp(16px, 3vw, 38px); font-size: 0.78rem; letter-spacing: 0.12em; text-transform: uppercase; }
.site-header nav a { opacity: 0.72; transition: opacity .25s ease; }
.site-header nav a:hover { opacity: 1; }
.header-cta { padding: 13px 20px; border-radius: 999px; background: var(--deep); color: var(--paper-soft); font-size: 0.82rem; font-weight: 750; }

.hero-section {
  width: min(calc(100% - 40px), var(--max));
  min-height: calc(100dvh - 96px);
  margin: 0 auto;
  padding: clamp(56px, 7vw, 104px) 0 clamp(48px, 6vw, 84px);
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(340px, 0.9fr);
  gap: clamp(28px, 5vw, 74px);
  align-items: center;
}

.eyebrow {
  margin: 0 0 18px;
  font-size: 0.76rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: rgba(23, 20, 15, 0.62);
  font-weight: 760;
}

.hero-copy h1 {
  max-width: 1040px;
  margin: 0;
  font-size: clamp(3.8rem, 8.2vw, 8.75rem);
  line-height: 0.88;
  letter-spacing: -0.085em;
  text-wrap: balance;
}
.hero-deck {
  max-width: 660px;
  margin: clamp(24px, 3vw, 42px) 0 0;
  font-size: clamp(1.08rem, 1.5vw, 1.42rem);
  line-height: 1.58;
  color: rgba(23, 20, 15, 0.72);
}
.hero-actions { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 34px; }
.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 52px;
  padding: 0 22px;
  border-radius: 999px;
  font-weight: 760;
  transition: transform .25s ease, background .25s ease, color .25s ease, border-color .25s ease;
}
.button:hover { transform: translateY(-2px); }
.button-primary { background: var(--deep); color: var(--paper-soft); }
.button-secondary { border: 1px solid var(--line); color: var(--ink); background: rgba(255,255,255,.28); }

.hero-visual {
  position: relative;
  min-height: clamp(470px, 56vw, 720px);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow);
  isolation: isolate;
}
.image-visual img { width: 100%; height: 100%; min-height: inherit; object-fit: cover; filter: contrast(1.03) saturate(.92); }
.image-visual::after { content: ''; position: absolute; inset: 0; background: linear-gradient(to top, rgba(16,13,9,.62), transparent 54%); }
.image-visual figcaption {
  position: absolute;
  left: 22px;
  right: 22px;
  bottom: 22px;
  z-index: 2;
  padding: 18px 20px;
  border: 1px solid var(--line-light);
  border-radius: 22px;
  background: rgba(16,13,9,.38);
  backdrop-filter: blur(16px);
  color: var(--paper-soft);
}
.abstract-visual {
  background: linear-gradient(145deg, var(--deep), var(--accent-deep));
}
.orb { position: absolute; border-radius: 999px; filter: blur(2px); }
.orb-one { width: 52%; aspect-ratio: 1; right: -10%; top: 8%; background: radial-gradient(circle, rgba(255,250,242,.54), transparent 68%); }
.orb-two { width: 68%; aspect-ratio: 1; left: -20%; bottom: -16%; background: radial-gradient(circle, rgba(139,93,51,.72), transparent 64%); }
.signature-card {
  position: absolute;
  left: 26px;
  right: 26px;
  bottom: 26px;
  padding: 26px;
  border: 1px solid var(--line-light);
  border-radius: 26px;
  background: rgba(255,255,255,.1);
  color: var(--paper-soft);
  backdrop-filter: blur(16px);
}
.signature-card span { display: block; opacity: .68; text-transform: uppercase; letter-spacing: .16em; font-size: .72rem; }
.signature-card strong { display: block; margin-top: 12px; font-size: clamp(1.6rem, 3vw, 2.8rem); letter-spacing: -.05em; }

.proof-rail {
  width: min(calc(100% - 40px), var(--max));
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  border-block: 1px solid var(--line);
}
.proof-rail article { min-height: 150px; padding: 28px; border-right: 1px solid var(--line); display: flex; flex-direction: column; justify-content: space-between; }
.proof-rail article:last-child { border-right: 0; }
.proof-rail span { font-size: .72rem; opacity: .44; font-weight: 800; }
.proof-rail p { margin: 0; font-size: clamp(1rem, 1.4vw, 1.35rem); line-height: 1.28; letter-spacing: -.035em; }

.chapter {
  width: min(calc(100% - 40px), var(--max));
  margin: 0 auto;
  padding: clamp(92px, 12vw, 180px) 0;
}
.chapter-heading { display: grid; grid-template-columns: .42fr 1fr; gap: clamp(24px, 6vw, 90px); align-items: start; margin-bottom: clamp(36px, 5vw, 70px); }
.chapter-heading h2, .sticky-note h2, .contact-panel h2 { margin: 0; font-size: clamp(2.25rem, 5.4vw, 6.4rem); line-height: .94; letter-spacing: -.07em; text-wrap: balance; }

.service-matrix { display: grid; grid-template-columns: repeat(12, 1fr); gap: 16px; }
.service-card {
  grid-column: span 4;
  min-height: 300px;
  padding: clamp(24px, 3vw, 38px);
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  background: rgba(255,250,242,.42);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  transition: transform .35s ease, background .35s ease;
}
.service-card:hover { transform: translateY(-4px); background: rgba(255,250,242,.78); }
.service-card-featured { grid-column: span 8; background: var(--deep); color: var(--paper-soft); }
.service-index { opacity: .52; font-weight: 800; font-size: .78rem; }
.service-card h3 { margin: 36px 0 12px; font-size: clamp(1.55rem, 2.4vw, 3rem); line-height: .98; letter-spacing: -.055em; }
.service-card p { margin: 0; max-width: 52ch; line-height: 1.55; opacity: .74; }

.photo-ribbon { width: 100%; display: grid; grid-template-columns: 1.2fr .8fr 1fr .7fr; gap: 12px; padding: 0 20px clamp(64px, 9vw, 130px); }
.photo-ribbon figure { margin: 0; height: clamp(280px, 34vw, 560px); overflow: hidden; border-radius: 28px; }
.photo-ribbon figure:nth-child(even) { transform: translateY(44px); }
.photo-ribbon img { width: 100%; height: 100%; object-fit: cover; transition: transform .7s ease; }
.photo-ribbon figure:hover img { transform: scale(1.055); }

.process-chapter { display: grid; grid-template-columns: .42fr 1fr; gap: clamp(24px, 6vw, 90px); align-items: start; }
.sticky-note { position: sticky; top: 120px; }
.process-list { display: grid; gap: 14px; }
.process-list article {
  display: grid;
  grid-template-columns: 90px 1fr;
  gap: 24px;
  padding: clamp(24px, 3vw, 38px);
  border-radius: 28px;
  background: rgba(255,250,242,.56);
  border: 1px solid var(--line);
}
.process-list span { font-size: .8rem; font-weight: 850; opacity: .46; }
.process-list h3 { margin: 0 0 10px; font-size: clamp(1.35rem, 2vw, 2.25rem); letter-spacing: -.04em; }
.process-list p { margin: 0; line-height: 1.55; color: rgba(23,20,15,.68); }

.contact-panel {
  width: min(calc(100% - 40px), var(--max));
  margin: 0 auto clamp(56px, 7vw, 94px);
  padding: clamp(34px, 6vw, 78px);
  border-radius: var(--radius-lg);
  background: var(--deep);
  color: var(--paper-soft);
  display: grid;
  grid-template-columns: 1fr minmax(280px, .42fr);
  gap: clamp(28px, 5vw, 72px);
  align-items: end;
  box-shadow: var(--shadow);
}
.contact-panel .eyebrow { color: rgba(255,250,242,.58); }
.contact-panel p { max-width: 68ch; color: rgba(255,250,242,.72); line-height: 1.58; }
.contact-actions { display: grid; gap: 12px; }
.contact-actions .button-primary { background: var(--paper-soft); color: var(--deep); }
.contact-actions > a:not(.button) { padding: 16px 0; border-bottom: 1px solid var(--line-light); color: rgba(255,250,242,.86); overflow-wrap: anywhere; }

.mobile-sticky-cta { display: none; }

@media (max-width: 980px) {
  .site-header { grid-template-columns: auto 1fr; top: 10px; }
  .site-header nav { display: none; }
  .header-cta { justify-self: end; }
  .hero-section, .chapter-heading, .process-chapter, .contact-panel { grid-template-columns: 1fr; }
  .hero-section { min-height: auto; padding-top: 66px; }
  .hero-copy h1 { font-size: clamp(3.1rem, 16vw, 6.8rem); }
  .hero-visual { min-height: 420px; }
  .proof-rail { grid-template-columns: repeat(2, 1fr); }
  .proof-rail article:nth-child(2) { border-right: 0; }
  .service-card, .service-card-featured { grid-column: span 6; }
  .photo-ribbon { grid-template-columns: repeat(2, 1fr); }
  .sticky-note { position: static; }
}

@media (max-width: 640px) {
  .site-header { width: calc(100% - 20px); }
  .header-cta { display: none; }
  .hero-section, .chapter, .proof-rail, .contact-panel { width: calc(100% - 24px); }
  .hero-actions { flex-direction: column; }
  .button { width: 100%; }
  .hero-visual { min-height: 360px; border-radius: 26px; }
  .proof-rail { grid-template-columns: 1fr; }
  .proof-rail article { border-right: 0; border-bottom: 1px solid var(--line); }
  .service-matrix { grid-template-columns: 1fr; }
  .service-card, .service-card-featured { grid-column: auto; min-height: 250px; }
  .photo-ribbon { grid-template-columns: 1fr; padding-inline: 12px; }
  .photo-ribbon figure:nth-child(even) { transform: none; }
  .process-list article { grid-template-columns: 1fr; gap: 14px; }
  .contact-panel { margin-bottom: 92px; }
  .mobile-sticky-cta {
    position: fixed;
    z-index: 30;
    left: 12px;
    right: 12px;
    bottom: 12px;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 54px;
    border-radius: 999px;
    background: var(--deep);
    color: var(--paper-soft);
    font-weight: 820;
    box-shadow: 0 18px 48px rgba(16,13,9,.26);
  }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { scroll-behavior: auto !important; transition: none !important; animation: none !important; }
}
"""


def write_premium_seed_site(target: Path, business: Mapping[str, Any], site_plan: Mapping[str, Any]) -> None:
    signature = infer_signature(business)
    signature["sourceDesignSystem"] = site_plan.get("design", {}).get("id") if isinstance(site_plan.get("design"), Mapping) else None
    data_dir = target / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "style-signature.json").write_text(json.dumps(signature, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (target / "app" / "page.tsx").write_text(_page_tsx(), encoding="utf-8")
    (target / "app" / "globals.css").write_text(_globals_css(), encoding="utf-8")
    (target / "LUXURY_BASELINE.md").write_text(
        "# Luxury Baseline\n\nThis generated site starts from a premium editorial baseline before Codex refinement. Codex should improve this baseline, not replace it with a generic card-stack landing page.\n",
        encoding="utf-8",
    )
