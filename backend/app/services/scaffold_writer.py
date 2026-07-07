from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Mapping

PLACEHOLDER_MARKER = "AGENTIC_REPLACE_ME"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def reset_dir(path: Path, overwrite: bool = True) -> None:
    if path.exists():
        if not overwrite:
            raise FileExistsError(str(path))
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, value: Any) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def generated_site_agents_md() -> str:
    return """# Generated Site Instructions

This folder is a temporary generated Next.js website. It exists so Codex can build a premium custom site from the business data.

## Non-negotiable quality bar

- Treat the starting files as a blank scaffold, not a finished template.
- Rewrite `app/page.tsx` and `app/globals.css` into a complete, polished site.
- Use the factual data in `data/business.json`, `data/design.json`, `data/sections.json`, and `data/site-plan.json`.
- Build a specific art direction for this business; do not create the same rounded-card landing page every time.
- Use supplied business photos only when present. Do not add stock photos or unrelated image URLs.
- Do not invent awards, licences, review counts, years in business, guarantees, emergency availability, prices, staff names, or menu items.
- Make the mobile experience excellent: no horizontal overflow, readable type, clear CTA, and a layout that is not just a squeezed desktop page.
- Keep the project static, dependency-light, and Vercel-friendly.

## Implementation expectations

Use TypeScript-safe React and CSS that should pass `npm run build`. Prefer native CSS, CSS variables, responsive grids, `clamp()`, layered backgrounds, careful spacing, and content-specific components over generic sections.

Before finishing, scan the site for placeholder text, dead CTAs, fake claims, generic AI copy, stretched images, repeated equal-height cards, and weak mobile spacing.
"""


def design_studio_brief(business: Mapping[str, Any]) -> str:
    name = str(business.get("name") or "this business")
    business_type = str(business.get("businessType") or business.get("business_type") or "local business")
    city = str(business.get("city") or business.get("serviceArea") or "the local area")
    photos = business.get("photos") or []
    has_photos = "yes" if photos else "no"
    return f"""# Design Studio Brief

Business: {name}
Type: {business_type}
Market: {city}
Supplied business photos: {has_photos}

The goal is not to fill a template. The goal is to make a credible custom website that looks intentionally designed for this exact business.

Use the JSON files in `data/` as factual inputs. If information is missing, design around the absence instead of inventing claims. For example, if there are no reviews, write an expectations/proof section based on the actual services and contact path rather than making up testimonials.

A strong output should have:

1. a distinct first viewport with a clear conversion path;
2. an industry-appropriate visual system;
3. page sections that answer the visitor's likely questions;
4. polished mobile layout;
5. no generic AI marketing language;
6. no visible scaffold residue.
"""


def write_minimal_project(target: Path, business: Mapping[str, Any]) -> None:
    slug = str(business.get("slug") or "generated-site")
    name = str(business.get("name") or "Generated Site")
    description = str(business.get("description") or business.get("businessType") or "Generated business website")

    write_json(target / "package.json", {
        "name": slug,
        "version": "1.0.0",
        "private": True,
        "scripts": {"dev": "next dev", "build": "next build", "start": "next start"},
        "dependencies": {"next": "^15.3.0", "react": "^19.0.0", "react-dom": "^19.0.0"},
        "devDependencies": {"@types/node": "^22.15.0", "@types/react": "^19.0.0", "@types/react-dom": "^19.0.0", "typescript": "^5.8.0"},
    })
    write_json(target / "tsconfig.json", {
        "compilerOptions": {
            "target": "es5",
            "lib": ["dom", "dom.iterable", "esnext"],
            "allowJs": False,
            "skipLibCheck": True,
            "strict": True,
            "noEmit": True,
            "esModuleInterop": True,
            "module": "esnext",
            "moduleResolution": "bundler",
            "resolveJsonModule": True,
            "isolatedModules": True,
            "jsx": "preserve",
            "incremental": True,
            "plugins": [{"name": "next"}],
        },
        "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
        "exclude": ["node_modules"],
    })
    write_text(target / "next.config.ts", "import type { NextConfig } from 'next';\n\nconst nextConfig: NextConfig = {};\n\nexport default nextConfig;\n")
    write_text(target / "next-env.d.ts", "/// <reference types=\"next\" />\n/// <reference types=\"next/image-types/global\" />\n")
    write_text(target / "app" / "layout.tsx", f"import type {{ Metadata }} from 'next';\nimport type {{ ReactNode }} from 'react';\nimport './globals.css';\n\nexport const metadata: Metadata = {{ title: {name!r}, description: {description!r} }};\n\nexport default function RootLayout({{ children }}: {{ children: ReactNode }}) {{\n  return <html lang=\"en\"><body>{{children}}</body></html>;\n}}\n")
    write_text(target / "app" / "page.tsx", f"import business from '../data/business.json';\n\nexport default function Home() {{\n  return <main className=\"generation-placeholder\" data-generation-marker=\"{PLACEHOLDER_MARKER}\"><p>{{business.name}}</p><h1>{PLACEHOLDER_MARKER}</h1></main>;\n}}\n")
    write_text(target / "app" / "globals.css", f":root {{ background: #0f1115; color: #f6f3ed; font-family: Arial, Helvetica, sans-serif; }}\n* {{ box-sizing: border-box; }}\nbody {{ margin: 0; min-height: 100vh; }}\n.generation-placeholder {{ min-height: 100vh; display: grid; place-items: center; padding: 48px; text-align: center; }}\n/* {PLACEHOLDER_MARKER} */\n")
    write_json(target / "data" / "business.json", business)
    write_json(target / "data" / "generation-mode.json", {"mode": "blank-scaffold", "scaffoldIsFinal": False, "placeholderMarker": PLACEHOLDER_MARKER})
    write_text(target / "AGENTS.md", generated_site_agents_md())
    write_text(target / "DESIGN_STUDIO_BRIEF.md", design_studio_brief(business))
    write_text(target / "GENERATION_BRIEF.md", f"# Generation brief\n\nThis folder is a blank scaffold. Remove `{PLACEHOLDER_MARKER}` and build from `data/business.json`, `data/site-plan.json`, `AGENTS.md`, and `DESIGN_STUDIO_BRIEF.md`.\n")


def assert_replaced(target: Path) -> None:
    paths = [target / "app" / "page.tsx", target / "app" / "globals.css"]
    remaining = [str(path.relative_to(target)) for path in paths if path.exists() and PLACEHOLDER_MARKER in path.read_text(encoding="utf-8")]
    if remaining:
        raise RuntimeError("Placeholder remains in: " + ", ".join(remaining))
