"""Write a fresh one-page Next.js project for each company.

This module replaces the old copy-template approach. Each generated site is a
new project folder written from the normalized business profile and a compact
creative brief. Optional Claude/Codex passes can then redesign or rewrite the
site from that brief.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping


def _text(value: Any, fallback: str = "") -> str:
    value = "" if value is None else str(value).strip()
    return value or fallback


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return re.sub(r"-{2,}", "-", cleaned) or "site"


def _services(business: Mapping[str, Any]) -> list[dict[str, str]]:
    services = business.get("services") or []
    normalized: list[dict[str, str]] = []
    for item in services[:8]:
        if isinstance(item, Mapping):
            normalized.append({"title": _text(item.get("title"), "Service"), "description": _text(item.get("description"), "Clear next steps and practical communication.")})
        else:
            normalized.append({"title": _text(item, "Service"), "description": "Clear next steps and practical communication."})
    return normalized or [
        {"title": "Assessment", "description": "Understand the request, location, and timing before setting expectations."},
        {"title": "Service", "description": "Handle the work with direct communication and practical follow-through."},
        {"title": "Next step", "description": "Move from first contact to a clear quote path, visit, or booking option."},
    ]


def choose_archetype(business: Mapping[str, Any]) -> str:
    blob = " ".join([
        _text(business.get("name")),
        _text(business.get("businessType")),
        _text(business.get("city")),
        _text(business.get("serviceArea")),
        " ".join(service["title"] for service in _services(business)),
    ]).lower()

    if any(term in blob for term in ("emergency", "sewer", "leak", "locksmith", "towing", "restoration")):
        return "dark-urgent"
    if any(term in blob for term in ("clinic", "dental", "medical", "therapy", "wellness", "chiropractor")):
        return "calm-clinical"
    if any(term in blob for term in ("law", "legal", "finance", "accounting", "insurance", "mortgage", "consulting")):
        return "editorial-advisory"
    if any(term in blob for term in ("spa", "salon", "interior", "design", "wedding", "hotel", "restaurant", "catering")):
        return "boutique-gallery"
    if any(term in blob for term in ("software", "saas", "marketing", "agency", "technology", "ai", "app")):
        return "modern-bento"
    return "local-authority"


def creative_brief(business: Mapping[str, Any]) -> dict[str, Any]:
    archetype = choose_archetype(business)
    palettes = {
        "dark-urgent": {"bg": "#090b0f", "ink": "#f7f3ea", "muted": "#b9b0a4", "panel": "#121720", "accent": "#f2a93b"},
        "calm-clinical": {"bg": "#eef7f4", "ink": "#10231f", "muted": "#5f746d", "panel": "#ffffff", "accent": "#2f8f83"},
        "editorial-advisory": {"bg": "#f4f1ea", "ink": "#121620", "muted": "#626b79", "panel": "#fffdf8", "accent": "#6f5f45"},
        "boutique-gallery": {"bg": "#f7efe8", "ink": "#241915", "muted": "#806b60", "panel": "#fffaf6", "accent": "#b17b61"},
        "modern-bento": {"bg": "#080b12", "ink": "#f6f8fb", "muted": "#aab3c2", "panel": "#111827", "accent": "#8da2ff"},
        "local-authority": {"bg": "#f5f1eb", "ink": "#15110d", "muted": "#6f655b", "panel": "#fffdf8", "accent": "#9b5f2b"},
    }
    composition = {
        "dark-urgent": "dark split hero with action rail and dense service list",
        "calm-clinical": "calm bright hero with reassurance cards and appointment flow",
        "editorial-advisory": "serious editorial page with numbered decision blocks",
        "boutique-gallery": "spacious gallery-style page with large visual panels",
        "modern-bento": "dark bento page with compact proof and service tiles",
        "local-authority": "warm editorial local service page with bento services",
    }[archetype]

    return {
        "archetype": archetype,
        "composition": composition,
        "palette": palettes[archetype],
        "tone": business.get("brandTone", "direct, premium, specific"),
        "avoid": ["generic hype", "template language", "fake proof", "long paragraphs"],
        "services": _services(business),
    }


def _json_for_ts(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def package_json() -> str:
    return _json_for_ts({
        "scripts": {"dev": "next dev", "build": "next build", "start": "next start", "lint": "next lint"},
        "dependencies": {"@types/node": "latest", "@types/react": "latest", "@types/react-dom": "latest", "eslint": "latest", "eslint-config-next": "latest", "next": "latest", "react": "latest", "react-dom": "latest", "typescript": "latest"},
        "devDependencies": {},
    }) + "\n"


def layout_tsx(business: Mapping[str, Any]) -> str:
    title = f"{business['name']} | {business['businessType']} in {business['serviceArea']}"
    description = business.get("hero", {}).get("subheadline", f"{business['businessType']} serving {business['serviceArea']}.")
    return f"""import type {{ Metadata }} from 'next';
import type {{ ReactNode }} from 'react';
import './globals.css';

export const metadata: Metadata = {{
  title: {_json_for_ts(title)},
  description: {_json_for_ts(description)},
}};

export default function RootLayout({{ children }}: {{ children: ReactNode }}) {{
  return (
    <html lang=\"en\">
      <body>{{children}}</body>
    </html>
  );
}}
"""


def page_tsx(business: Mapping[str, Any], brief: Mapping[str, Any]) -> str:
    data = {
        "business": business,
        "brief": brief,
        "services": brief["services"],
        "proof": business.get("proofPoints", [])[:4],
        "process": business.get("processSteps", [])[:4],
        "faqs": business.get("faqs", [])[:4],
    }
    return f"""const data = {_json_for_ts(data)} as const;

function phoneHref(phone: string) {{
  return `tel:${{phone.replace(/[^+\\d]/g, '')}}`;
}}

function contactHref() {{
  if (data.business.phone) return phoneHref(data.business.phone);
  if (data.business.email) return `mailto:${{data.business.email}}`;
  return '#contact';
}}

export default function Home() {{
  const href = contactHref();
  const phone = data.business.phone;

  return (
    <main data-archetype={{data.brief.archetype}}>
      <header className=\"nav\">
        <a className=\"brand\" href=\"#top\">
          <span>{{data.business.name.slice(0, 1)}}</span>
          <strong>{{data.business.name}}</strong>
        </a>
        <nav>
          <a href=\"#services\">Services</a>
          <a href=\"#process\">Process</a>
          <a href=\"#faq\">FAQ</a>
        </nav>
        <a className=\"navCta\" href={{href}}>{{data.business.primaryCta}}</a>
      </header>

      <section id=\"top\" className=\"hero\">
        <div className=\"heroCopy\">
          <p className=\"eyebrow\">{{data.business.hero.eyebrow}}</p>
          <h1>{{data.business.hero.headline}}</h1>
          <p className=\"lead\">{{data.business.hero.subheadline}}</p>
          <div className=\"actions\">
            <a className=\"button primary\" href={{href}}>{{data.business.primaryCta}}</a>
            <a className=\"button ghost\" href=\"#services\">{{data.business.secondaryCta}}</a>
          </div>
          <p className=\"smallNote\">{{phone ? `Call ${{phone}} or send the request details.` : `Serving ${{data.business.serviceArea}}.`}}</p>
        </div>

        <aside className=\"signaturePanel\">
          <p>{{data.brief.composition}}</p>
          <h2>{{data.business.offer}}</h2>
          <div className=\"panelList\">
            {{data.proof.map((item) => <span key={{item}}>{{item}}</span>)}}
          </div>
        </aside>
      </section>

      <section id=\"services\" className=\"section services\">
        <div className=\"sectionIntro\">
          <p className=\"eyebrow\">Services</p>
          <h2>{{data.business.businessType}} help shaped around the actual request.</h2>
          <p>Start with the issue, location, timing, and any details that make the work easier to understand.</p>
        </div>
        <div className=\"serviceGrid\">
          {{data.services.map((service, index) => (
            <article className=\"serviceCard\" key={{service.title}}>
              <span>{{String(index + 1).padStart(2, '0')}}</span>
              <h3>{{service.title}}</h3>
              <p>{{service.description}}</p>
            </article>
          ))}}
        </div>
      </section>

      <section id=\"process\" className=\"section process\">
        <div className=\"sectionIntro\">
          <p className=\"eyebrow\">Process</p>
          <h2>Clear next steps from first contact.</h2>
        </div>
        <div className=\"processGrid\">
          {{data.process.map((step, index) => (
            <article key={{step.title}}>
              <span>{{String(index + 1).padStart(2, '0')}}</span>
              <h3>{{step.title}}</h3>
              <p>{{step.description}}</p>
            </article>
          ))}}
        </div>
      </section>

      <section className=\"statement\">
        <p>{{data.business.guarantee}}</p>
        <h2>{{data.business.name}} keeps the path simple: explain the need, get the next step, move forward with fewer unknowns.</h2>
      </section>

      <section id=\"faq\" className=\"section faq\">
        <div className=\"sectionIntro\">
          <p className=\"eyebrow\">FAQ</p>
          <h2>Before getting started.</h2>
        </div>
        <div className=\"faqList\">
          {{data.faqs.map((item) => (
            <details key={{item.question}}>
              <summary>{{item.question}}</summary>
              <p>{{item.answer}}</p>
            </details>
          ))}}
        </div>
      </section>

      <section id=\"contact\" className=\"final\">
        <p className=\"eyebrow\">Next step</p>
        <h2>{{data.business.offer}}</h2>
        <a className=\"button primary\" href={{href}}>{{data.business.primaryCta}}</a>
      </section>
    </main>
  );
}}
"""


def globals_css(brief: Mapping[str, Any]) -> str:
    p = brief["palette"]
    archetype = brief["archetype"]
    return f""":root {{
  --bg: {p['bg']};
  --ink: {p['ink']};
  --muted: {p['muted']};
  --panel: {p['panel']};
  --accent: {p['accent']};
  --line: color-mix(in srgb, var(--ink) 14%, transparent);
  --max: 1180px;
}}

* {{ box-sizing: border-box; }}
html {{ scroll-behavior: smooth; }}
body {{ margin: 0; background: var(--bg); color: var(--ink); font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif; }}
a {{ color: inherit; text-decoration: none; }}
main {{ min-height: 100vh; overflow: hidden; background: radial-gradient(circle at 10% 6%, color-mix(in srgb, var(--accent) 22%, transparent), transparent 30rem), linear-gradient(180deg, color-mix(in srgb, var(--bg) 94%, white), var(--bg)); }}
.nav {{ position: sticky; top: 0; z-index: 20; max-width: calc(var(--max) + 48px); margin: 0 auto; padding: 18px 24px; display: flex; align-items: center; justify-content: space-between; gap: 18px; backdrop-filter: blur(22px); }}
.brand {{ display: inline-flex; align-items: center; gap: 12px; min-width: 0; }}
.brand span {{ display: grid; place-items: center; width: 42px; height: 42px; border-radius: 50%; background: var(--ink); color: var(--bg); font-weight: 900; }}
.brand strong {{ max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; letter-spacing: -0.03em; }}
.nav nav {{ display: flex; gap: 22px; color: var(--muted); font-size: .92rem; font-weight: 700; }}
.navCta, .button {{ display: inline-flex; align-items: center; justify-content: center; min-height: 46px; padding: 0 22px; border-radius: 999px; font-weight: 850; }}
.navCta, .button.primary {{ background: var(--accent); color: color-mix(in srgb, var(--bg) 92%, white); box-shadow: 0 18px 50px color-mix(in srgb, var(--accent) 28%, transparent); }}
.button.ghost {{ border: 1px solid var(--line); background: color-mix(in srgb, var(--panel) 70%, transparent); }}
.hero {{ max-width: var(--max); min-height: calc(100vh - 90px); margin: 0 auto; padding: 76px 24px 92px; display: grid; grid-template-columns: minmax(0, 1.05fr) minmax(340px, .82fr); gap: 58px; align-items: center; }}
.eyebrow {{ margin: 0 0 16px; color: var(--accent); font-size: .74rem; font-weight: 950; letter-spacing: .18em; text-transform: uppercase; }}
h1, h2, h3, p {{ margin-top: 0; }}
h1 {{ max-width: 900px; margin-bottom: 24px; font-family: ui-serif, Georgia, Cambria, \"Times New Roman\", serif; font-size: clamp(3.4rem, 8vw, 7.1rem); font-weight: 520; line-height: .9; letter-spacing: -.075em; }}
h2 {{ margin-bottom: 18px; font-family: ui-serif, Georgia, Cambria, \"Times New Roman\", serif; font-size: clamp(2.15rem, 4.5vw, 4.5rem); font-weight: 520; line-height: .96; letter-spacing: -.055em; }}
h3 {{ margin-bottom: 10px; letter-spacing: -.03em; }}
p {{ color: var(--muted); line-height: 1.65; }}
.lead {{ max-width: 670px; font-size: clamp(1.08rem, 2vw, 1.32rem); }}
.actions {{ display: flex; flex-wrap: wrap; gap: 12px; margin: 30px 0 14px; }}
.smallNote {{ margin: 0; font-size: .96rem; }}
.signaturePanel {{ position: relative; overflow: hidden; padding: 34px; border: 1px solid var(--line); border-radius: 34px; background: color-mix(in srgb, var(--panel) 88%, transparent); box-shadow: 0 28px 88px color-mix(in srgb, var(--ink) 10%, transparent); }}
.signaturePanel::after {{ content: \"\"; position: absolute; inset: auto -18% -30% 35%; height: 240px; border-radius: 999px; background: color-mix(in srgb, var(--accent) 18%, transparent); filter: blur(24px); }}
.signaturePanel > * {{ position: relative; z-index: 1; }}
.signaturePanel > p:first-child {{ color: var(--accent); font-size: .78rem; font-weight: 900; letter-spacing: .12em; text-transform: uppercase; }}
.panelList {{ display: grid; gap: 10px; margin-top: 34px; }}
.panelList span {{ padding: 14px 0; border-top: 1px solid var(--line); color: var(--ink); font-weight: 760; }}
.section {{ max-width: var(--max); margin: 0 auto; padding: 92px 24px; }}
.sectionIntro {{ display: grid; grid-template-columns: minmax(0, .95fr) minmax(260px, .45fr); gap: 46px; align-items: end; margin-bottom: 40px; }}
.serviceGrid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; }}
.serviceCard, .processGrid article, details {{ border: 1px solid var(--line); border-radius: 26px; background: color-mix(in srgb, var(--panel) 78%, transparent); box-shadow: 0 16px 48px color-mix(in srgb, var(--ink) 7%, transparent); }}
.serviceCard {{ min-height: 260px; padding: 28px; display: flex; flex-direction: column; justify-content: space-between; }}
.serviceCard:first-child {{ grid-column: span 2; background: var(--ink); color: var(--bg); }}
.serviceCard:first-child p, .serviceCard:first-child span {{ color: color-mix(in srgb, var(--bg) 75%, transparent); }}
.serviceCard span, .processGrid span {{ color: var(--accent); font-size: .78rem; font-weight: 930; letter-spacing: .12em; }}
.processGrid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; }}
.processGrid article {{ min-height: 230px; padding: 28px; }}
.processGrid span {{ display: inline-flex; margin-bottom: 48px; }}
.statement {{ max-width: var(--max); margin: 0 auto; padding: 80px 24px; }}
.statement p {{ color: var(--accent); font-weight: 850; }}
.statement h2 {{ max-width: 960px; }}
.faqList {{ display: grid; gap: 12px; }}
details {{ overflow: hidden; }}
summary {{ cursor: pointer; padding: 24px 26px; font-weight: 850; list-style: none; }}
summary::-webkit-details-marker {{ display: none; }}
summary::after {{ content: \"+\"; float: right; color: var(--accent); }}
details[open] summary::after {{ content: \"-\"; }}
details p {{ max-width: 760px; margin: 0; padding: 0 26px 26px; }}
.final {{ max-width: var(--max); margin: 0 auto 64px; padding: clamp(42px, 7vw, 76px) 24px; border-radius: 36px; text-align: center; background: var(--ink); color: var(--bg); }}
.final h2, .final p {{ color: var(--bg); }}
.final .button {{ margin-top: 16px; }}
[data-archetype=\"dark-urgent\"] .serviceCard:first-child, [data-archetype=\"modern-bento\"] .serviceCard:first-child {{ background: linear-gradient(145deg, var(--panel), color-mix(in srgb, var(--accent) 22%, var(--panel))); }}
[data-archetype=\"boutique-gallery\"] .serviceGrid {{ grid-template-columns: 1.2fr .8fr .8fr; }}
[data-archetype=\"editorial-advisory\"] .hero {{ grid-template-columns: minmax(0, 1.18fr) minmax(320px, .72fr); }}
@media (max-width: 980px) {{ .hero, .sectionIntro {{ grid-template-columns: 1fr; }} .serviceGrid, .processGrid, [data-archetype=\"boutique-gallery\"] .serviceGrid {{ grid-template-columns: 1fr; }} .serviceCard:first-child {{ grid-column: auto; }} }}
@media (max-width: 680px) {{ .nav nav, .navCta {{ display: none; }} .hero, .section {{ padding-left: 18px; padding-right: 18px; }} h1 {{ font-size: clamp(3rem, 16vw, 4.8rem); }} .signaturePanel, .serviceCard, .processGrid article, details, .final {{ border-radius: 24px; }} .actions, .button {{ width: 100%; }} }}
"""


def write_project_files(target: Path, business: Mapping[str, Any], site_plan: Mapping[str, Any] | None = None) -> dict[str, Any]:
    brief = creative_brief(business)
    (target / "app").mkdir(parents=True, exist_ok=True)
    (target / "data").mkdir(parents=True, exist_ok=True)

    (target / "package.json").write_text(package_json(), encoding="utf-8")
    (target / "next.config.mjs").write_text("const nextConfig = {};\nexport default nextConfig;\n", encoding="utf-8")
    (target / "tsconfig.json").write_text(_json_for_ts({"compilerOptions": {"target": "es5", "lib": ["dom", "dom.iterable", "esnext"], "allowJs": True, "skipLibCheck": True, "strict": True, "noEmit": True, "esModuleInterop": True, "module": "esnext", "moduleResolution": "bundler", "resolveJsonModule": True, "isolatedModules": True, "jsx": "preserve", "incremental": True, "plugins": [{"name": "next"}]}, "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"], "exclude": ["node_modules"]}) + "\n", encoding="utf-8")
    (target / "next-env.d.ts").write_text("/// <reference types=\"next\" />\n/// <reference types=\"next/image-types/global\" />\n\n// This file is generated by Next.js.\n", encoding="utf-8")
    (target / "app" / "layout.tsx").write_text(layout_tsx(business), encoding="utf-8")
    (target / "app" / "page.tsx").write_text(page_tsx(business, brief), encoding="utf-8")
    (target / "app" / "globals.css").write_text(globals_css(brief), encoding="utf-8")
    (target / "data" / "business.json").write_text(json.dumps(business, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (target / "data" / "creative-brief.json").write_text(json.dumps(brief, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if site_plan is not None:
        (target / "data" / "site-plan.json").write_text(json.dumps(site_plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return brief
