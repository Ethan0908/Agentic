from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping

REPO_ROOT = Path(__file__).resolve().parents[3]
PACKS_FILE = REPO_ROOT / "backend" / "app" / "config" / "industry_site_packs.json"


def text(value: Any, fallback: str = "") -> str:
    value = "" if value is None else str(value).strip()
    return value or fallback


def items(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def services(business: Mapping[str, Any]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for item in items(business.get("services"))[:8]:
        if isinstance(item, Mapping):
            out.append({"title": text(item.get("title"), "Service"), "description": text(item.get("description"), "Clear next steps and practical communication.")})
        else:
            out.append({"title": text(item, "Service"), "description": "Clear next steps and practical communication."})
    return out or [
        {"title": "Assessment", "description": "Understand the request, location, and timing before setting expectations."},
        {"title": "Service", "description": "Handle the work with direct communication and practical follow-through."},
        {"title": "Next step", "description": "Move from first contact to a clear quote path, visit, or booking option."}
    ]


def load_packs() -> dict[str, Any]:
    return json.loads(PACKS_FILE.read_text(encoding="utf-8"))


def choose_pack(business: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
    blob = " ".join([
        text(business.get("name")), text(business.get("businessType")), text(business.get("business_type")),
        text(business.get("category")), text(business.get("serviceArea")), text(business.get("service_area")),
        " ".join(s["title"] + " " + s["description"] for s in services(business))
    ]).lower()
    packs = load_packs()
    best_key = "professional"
    best_score = -1
    for key, pack in packs.items():
        score = sum(1 for word in pack.get("keywords", []) if word.lower() in blob)
        if score > best_score:
            best_key = key
            best_score = score
    return best_key, packs[best_key]


def brief_for(business: Mapping[str, Any]) -> dict[str, Any]:
    key, pack = choose_pack(business)
    supplied = business.get("images") if isinstance(business.get("images"), Mapping) else {}
    image_defaults = pack.get("images", {})
    hero_image = text(business.get("heroImage") or business.get("hero_image") or supplied.get("hero"), image_defaults.get("hero", ""))
    secondary_image = text(business.get("secondaryImage") or business.get("secondary_image") or supplied.get("secondary"), image_defaults.get("secondary", hero_image))
    return {
        "industry": key,
        "label": pack["label"],
        "layout": pack["layout"],
        "radius": pack["radius"],
        "cardRadius": pack["cardRadius"],
        "density": pack["density"],
        "palette": pack["palette"],
        "copyFrame": pack["copyFrame"],
        "images": {"hero": hero_image, "secondary": secondary_image},
        "services": services(business)
    }


def js(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def package_json() -> str:
    return js({"scripts": {"dev": "next dev", "build": "next build", "start": "next start"}, "dependencies": {"next": "latest", "react": "latest", "react-dom": "latest", "typescript": "latest", "@types/node": "latest", "@types/react": "latest", "@types/react-dom": "latest"}, "devDependencies": {}}) + "\n"


def layout_tsx(business: Mapping[str, Any]) -> str:
    title = f"{business['name']} | {business['businessType']} in {business['serviceArea']}"
    desc = business.get("hero", {}).get("subheadline", f"{business['businessType']} serving {business['serviceArea']}.")
    return f"""import type {{ Metadata }} from 'next';
import type {{ ReactNode }} from 'react';
import './globals.css';
export const metadata: Metadata = {{ title: {js(title)}, description: {js(desc)} }};
export default function RootLayout({{ children }}: {{ children: ReactNode }}) {{ return <html lang=\"en\"><body>{{children}}</body></html>; }}
"""


def page_tsx(business: Mapping[str, Any], brief: Mapping[str, Any]) -> str:
    data = {"business": business, "brief": brief, "services": brief["services"], "proof": business.get("proofPoints", [])[:4], "process": business.get("processSteps", [])[:4], "faqs": business.get("faqs", [])[:4]}
    return f"""const data = {js(data)} as const;
function phoneHref(phone: string) {{ return `tel:${{phone.replace(/[^+\\d]/g, '')}}`; }}
function contactHref() {{ if (data.business.phone) return phoneHref(data.business.phone); if (data.business.email) return `mailto:${{data.business.email}}`; return '#contact'; }}
export default function Home() {{
  const href = contactHref();
  return <main className=\"site\" data-industry={{data.brief.industry}} data-layout={{data.brief.layout}}>
    <header className=\"nav\"><a className=\"brand\" href=\"#top\"><span>{{data.business.name.slice(0,1)}}</span><strong>{{data.business.name}}</strong></a><nav><a href=\"#services\">Services</a><a href=\"#process\">Process</a><a href=\"#faq\">FAQ</a></nav><a className=\"navCta\" href={{href}}>{{data.business.primaryCta}}</a></header>
    <section id=\"top\" className=\"hero\"><div><p className=\"eyebrow\">{{data.business.hero.eyebrow}}</p><h1>{{data.business.hero.headline}}</h1><p className=\"lead\">{{data.business.hero.subheadline}}</p><div className=\"actions\"><a className=\"button primary\" href={{href}}>{{data.business.primaryCta}}</a><a className=\"button secondary\" href=\"#services\">{{data.business.secondaryCta}}</a></div></div><aside className=\"mediaPanel\"><img src={{data.brief.images.hero}} alt=\"Service work\"/><div className=\"intakeCard\"><p>{{data.brief.copyFrame.heroPanelLabel}}</p><h2>{{data.business.offer}}</h2></div></aside></section>
    <section className=\"proofBar\">{{data.proof.map((item) => <p key={{item}}>{{item}}</p>)}}</section>
    <section id=\"services\" className=\"section\"><div className=\"sectionIntro\"><p className=\"eyebrow\">Services</p><h2>{{data.brief.copyFrame.proofHeading}}</h2><p>{{data.brief.copyFrame.serviceIntro}}</p></div><div className=\"serviceGrid\">{{data.services.map((service,index)=><article className=\"serviceCard\" key={{service.title}}><span>{{String(index+1).padStart(2,'0')}}</span><h3>{{service.title}}</h3><p>{{service.description}}</p></article>)}}</div></section>
    <section id=\"process\" className=\"section process\"><div className=\"photoStrip\"><img src={{data.brief.images.secondary}} alt=\"Service detail\"/></div><div><p className=\"eyebrow\">Process</p><h2>Clear next steps from first contact.</h2><div className=\"processGrid\">{{data.process.map((step,index)=><article key={{step.title}}><span>{{String(index+1).padStart(2,'0')}}</span><h3>{{step.title}}</h3><p>{{step.description}}</p></article>)}}</div></div></section>
    <section id=\"faq\" className=\"section\"><div className=\"sectionIntro\"><p className=\"eyebrow\">FAQ</p><h2>Before getting started.</h2></div><div className=\"faqList\">{{data.faqs.map((item)=><details key={{item.question}}><summary>{{item.question}}</summary><p>{{item.answer}}</p></details>)}}</div></section>
    <section id=\"contact\" className=\"final\"><p className=\"eyebrow\">Next step</p><h2>{{data.brief.copyFrame.finalHeading}}</h2><a className=\"button primary\" href={{href}}>{{data.business.primaryCta}}</a></section>
  </main>;
}}
"""


def globals_css(brief: Mapping[str, Any]) -> str:
    p = brief["palette"]
    return f""":root{{--bg:{p['bg']};--ink:{p['ink']};--muted:{p['muted']};--panel:{p['panel']};--panel-dark:{p['panelDark']};--accent:{p['accent']};--accent-dark:{p['accentDark']};--line:{p['line']};--radius:{brief['radius']};--card-radius:{brief['cardRadius']};--max:1180px}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif}}a{{color:inherit;text-decoration:none}}.site{{min-height:100vh;overflow:hidden}}.nav{{position:sticky;top:0;z-index:20;max-width:calc(var(--max) + 40px);margin:0 auto;padding:16px 20px;display:flex;align-items:center;justify-content:space-between;gap:18px;background:color-mix(in srgb,var(--bg) 88%,transparent);backdrop-filter:blur(18px);border-bottom:1px solid var(--line)}}.brand{{display:inline-flex;align-items:center;gap:12px}}.brand span{{display:grid;place-items:center;width:40px;height:40px;border-radius:var(--radius);background:var(--ink);color:var(--bg);font-weight:900}}.brand strong{{letter-spacing:-.03em}}.nav nav{{display:flex;gap:22px;color:var(--muted);font-size:.92rem;font-weight:750}}.navCta,.button{{display:inline-flex;align-items:center;justify-content:center;min-height:46px;padding:0 22px;border-radius:var(--radius);font-weight:880}}.navCta,.button.primary{{background:var(--accent);color:#111827}}.button.secondary{{border:1px solid var(--line);background:var(--panel);color:var(--ink)}}.hero{{max-width:var(--max);min-height:calc(100vh - 78px);margin:0 auto;padding:72px 20px 84px;display:grid;grid-template-columns:minmax(0,1.02fr) minmax(360px,.9fr);gap:52px;align-items:center}}.eyebrow{{margin:0 0 14px;color:var(--accent-dark);font-size:.74rem;font-weight:950;letter-spacing:.18em;text-transform:uppercase}}h1,h2,h3,p{{margin-top:0}}h1{{max-width:900px;margin-bottom:22px;font-size:clamp(3.1rem,7.2vw,6.6rem);line-height:.91;letter-spacing:-.075em}}h2{{margin-bottom:16px;font-size:clamp(2rem,4vw,4rem);line-height:.98;letter-spacing:-.055em}}p{{color:var(--muted);line-height:1.62}}.lead{{max-width:650px;font-size:clamp(1.05rem,2vw,1.28rem)}}.actions{{display:flex;flex-wrap:wrap;gap:12px;margin:28px 0 12px}}.mediaPanel{{position:relative;min-height:620px;border-radius:var(--radius);overflow:hidden;background:var(--panel-dark)}}.mediaPanel img,.photoStrip img{{width:100%;height:100%;object-fit:cover;display:block}}.mediaPanel img{{min-height:620px}}.intakeCard{{position:absolute;left:18px;right:18px;bottom:18px;padding:22px;border-radius:var(--card-radius);background:color-mix(in srgb,var(--panel-dark) 88%,transparent);color:white;border:1px solid rgba(255,255,255,.16)}}.intakeCard p{{margin-bottom:8px;color:var(--accent);font-size:.76rem;font-weight:950;letter-spacing:.15em;text-transform:uppercase}}.intakeCard h2{{margin:0;color:white;font-size:clamp(1.7rem,3vw,2.8rem)}}.proofBar{{max-width:var(--max);margin:0 auto;padding:0 20px;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border-top:1px solid var(--line);border-bottom:1px solid var(--line)}}.proofBar p{{margin:0;padding:20px 18px;color:var(--ink);font-weight:800;border-right:1px solid var(--line)}}.section{{max-width:var(--max);margin:0 auto;padding:88px 20px}}.sectionIntro{{display:grid;grid-template-columns:minmax(0,.9fr) minmax(280px,.48fr);gap:44px;align-items:end;margin-bottom:36px}}.serviceGrid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}}.serviceCard,.processGrid article,details{{border:1px solid var(--line);border-radius:var(--card-radius);background:var(--panel)}}.serviceCard{{min-height:230px;padding:24px;display:flex;flex-direction:column;justify-content:space-between}}.serviceCard:first-child{{grid-column:span 2;background:var(--panel-dark);color:white}}.serviceCard span,.processGrid span{{color:var(--accent-dark);font-size:.78rem;font-weight:950;letter-spacing:.12em}}.process{{display:grid;grid-template-columns:.78fr 1.22fr;gap:34px;align-items:stretch}}.photoStrip{{min-height:520px;overflow:hidden;border-radius:var(--radius);background:var(--panel-dark)}}.photoStrip img{{min-height:520px}}.processGrid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}}.processGrid article{{min-height:220px;padding:24px}}summary{{cursor:pointer;padding:22px 24px;font-weight:850;list-style:none}}details p{{padding:0 24px 24px}}.final{{max-width:var(--max);margin:0 auto 60px;padding:64px 20px;border-radius:var(--radius);background:var(--panel-dark);color:white;text-align:center}}.final h2,.final p{{color:white}}[data-industry=plumbing] h1,[data-industry=electrical] h1{{font-family:Impact,Haettenschweiler,Arial Narrow Bold,sans-serif;font-weight:900;text-transform:uppercase;letter-spacing:-.055em}}[data-industry=clinic] h1,[data-industry=boutique] h1,[data-industry=professional] h1{{font-family:ui-serif,Georgia,Cambria,Times New Roman,serif;font-weight:520;text-transform:none}}[data-industry=plumbing] .mediaPanel,[data-industry=plumbing] .photoStrip,[data-industry=plumbing] .serviceCard,[data-industry=plumbing] details{{box-shadow:none}}@media(max-width:980px){{.hero,.sectionIntro,.process,.proofBar,.serviceGrid,.processGrid{{grid-template-columns:1fr}}.serviceCard:first-child{{grid-column:auto}}.mediaPanel,.mediaPanel img{{min-height:460px}}}}@media(max-width:680px){{.nav nav,.navCta{{display:none}}.hero,.section{{padding-left:16px;padding-right:16px}}h1{{font-size:clamp(2.7rem,15vw,4.4rem)}}.actions,.button{{width:100%}}}}
"""


def write_project_files(target: Path, business: Mapping[str, Any], site_plan: Mapping[str, Any] | None = None) -> dict[str, Any]:
    brief = brief_for(business)
    (target / "app").mkdir(parents=True, exist_ok=True)
    (target / "data").mkdir(parents=True, exist_ok=True)
    (target / "package.json").write_text(package_json(), encoding="utf-8")
    (target / "next.config.mjs").write_text("const nextConfig = {};\nexport default nextConfig;\n", encoding="utf-8")
    (target / "tsconfig.json").write_text(js({"compilerOptions":{"target":"es5","lib":["dom","dom.iterable","esnext"],"allowJs":True,"skipLibCheck":True,"strict":True,"noEmit":True,"esModuleInterop":True,"module":"esnext","moduleResolution":"bundler","resolveJsonModule":True,"isolatedModules":True,"jsx":"preserve","incremental":True,"plugins":[{"name":"next"}]},"include":["next-env.d.ts","**/*.ts","**/*.tsx",".next/types/**/*.ts"],"exclude":["node_modules"]}) + "\n", encoding="utf-8")
    (target / "next-env.d.ts").write_text("/// <reference types=\"next\" />\n/// <reference types=\"next/image-types/global\" />\n", encoding="utf-8")
    (target / "app" / "layout.tsx").write_text(layout_tsx(business), encoding="utf-8")
    (target / "app" / "page.tsx").write_text(page_tsx(business, brief), encoding="utf-8")
    (target / "app" / "globals.css").write_text(globals_css(brief), encoding="utf-8")
    (target / "data" / "business.json").write_text(json.dumps(business, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (target / "data" / "creative-brief.json").write_text(json.dumps(brief, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if site_plan is not None:
        (target / "data" / "site-plan.json").write_text(json.dumps(site_plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return brief
