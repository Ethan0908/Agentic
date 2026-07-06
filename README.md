# Agentic Website Builder

This repository is the source of truth for the website builder. The Raspberry Pi should run a direct copy of this repo instead of keeping separate local-only logic.

## Architecture

- `frontend/` — local client-management control panel on port `3000`.
- Raspberry Pi — thin host/intermediary that runs the frontend, keeps runtime client data, and runs local CLI tools.
- GitHub — source of truth for frontend code, backend code, prompts, templates, Claude agents, Claude skills, docs, and validation scripts.
- Vercel — deployment target for generated static sites.

The Pi should only store runtime state such as `.runtime/clients.json` or the path configured by `CLIENT_DATA_FILE`. App code, prompts, and templates belong in GitHub.

## Current system

- `frontend/` — Next.js control panel for clients and queue status, bound to port `3000`.
- `backend/app/services/site_generator.py` — main Python entrypoint.
- `backend/app/services/agentic_site_builder.py` — token-efficient site planner, design-system selector, section planner, image strategy, and Claude prompt builder.
- `backend/app/services/site_quality.py` — deterministic generated-site QA gate that writes `data/quality-report.json` and can fail bad sites before deployment.
- `backend/app/services/generate_site_cli.py` — local CLI for generating one site from a lead JSON file.
- `backend/app/config/design_systems.json` — multiple visual systems, not one template.
- `backend/app/config/section_registry.json` — reusable hero/proof/services/process/CTA variants.
- `backend/app/config/token_budget.json` — compact handoff rules for agent prompts.
- `.claude/agents/` — project-level Claude Code subagents for profiling, conversion strategy, brand direction, copy polish, frontend refinement, and visual QA.
- `.claude/skills/` — project skills for premium site generation and visual QA.
- `site-template/` — canonical Next.js codebase that renders different visual systems from `data/business.json`, `data/design.json`, and `data/sections.json`.
- `scripts/validate_site_quality.py` — CLI wrapper around the generated-site quality gate.
- `examples/` — smoke-test input files for generation testing.
- `docs/` — Pi and architecture notes.

## Design direction

The builder is designed to create professional local-business sites that feel closer to a paid agency build than a generic AI landing page. It emphasizes:

- concise, scannable copy
- strong above-the-fold CTA hierarchy
- trust points without fake claims
- vertical-specific copy and CTAs
- multiple industry-specific visual systems
- supplied business photos when available
- premium spacing and typography
- mobile-first conversion flow
- fast static deployment on Vercel

## Image-aware generation

The generator accepts public business image fields such as `photos`, `images`, `photo_urls`, `photoUrls`, `website_images`, `websiteImages`, `scraped_images`, `scrapedImages`, `heroImage`, and `coverImage`.

Those inputs are normalized to:

- `data/business.json` → `heroImage`
- `data/business.json` → `photos`
- `data/sections.json` → `imageStrategy`

The template uses supplied photos in the hero and photo ribbon. If no photos are supplied, it should stay premium through typography, layout, cards, and copy. It should not add unrelated stock photos.

## Vertical-aware generation

The generator now detects verticals before the site is rendered. That means an omakase restaurant, emergency plumber, clinic, salon, advisory firm, software agency, and home-service company do not receive the same default page.

Vertical profiles affect:

- `business.vertical`
- hero headline/subheadline
- primary and secondary CTA labels
- services/experience cards
- proof points
- process steps
- FAQ answers
- `pageCopy` used by the React template
- design-system choice
- section variant choice
- quality-gate checks

Important example: an omakase lead should generate a restaurant/reservation page. It should not mention repair, installation, maintenance, quote paths, fake awards, fake ratings, prices, or invented menu details.

## Generation flow

1. Collect or infer a business profile from lead data.
2. Normalize it with `normalize_business_profile()`.
3. Detect vertical and generate vertical-specific defaults.
4. Select a design system with `select_design_system()`.
5. Plan section variants with `build_section_plan()`.
6. Copy `site-template/` into `generated_sites/<business-slug>/`.
7. Write:
   - `data/business.json`
   - `data/design.json`
   - `data/sections.json`
   - `data/site-plan.json`
8. Optionally run Claude Code project subagents with `refine_with_claude=True`.
9. Optionally run Codex refinement with `refine_with_codex=True`.
10. Run the deterministic quality gate and write `data/quality-report.json`.
11. Build the generated Next.js site.
12. Push the generated site repo and deploy it to Vercel.

## Frontend usage

```bash
cd frontend
npm install
npm run dev
```

Production:

```bash
cd frontend
npm install
npm run build
npm run start
```

The frontend runs on `0.0.0.0:3000` and stores runtime client data at `../.runtime/clients.json` unless `CLIENT_DATA_FILE` is set.

## Example Python usage

```python
from backend.app.services.site_generator import generate_site

site = generate_site(
    {
        "name": "NYC Emergency Plumbing",
        "business_type": "emergency plumbing",
        "city": "New York",
        "service_area": "Manhattan, Brooklyn, and Queens",
        "phone": "",
        "primary_cta": "Request emergency service",
        "photos": [
            "https://example.com/public-business-photo.jpg"
        ],
        "services": [
            {"title": "Drain clearing", "description": "Clear blocked drains with a practical diagnosis before work starts."},
            {"title": "Leak repair", "description": "Find the source of the leak and explain the next step clearly."},
            {"title": "Sewer service", "description": "Understand the source of the blockage and the practical next step."}
        ]
    },
    refine_with_claude=False,
    refine_with_codex=False,
)

print(site.path)
print(site.design_system)
print(site.quality_score)
print(site.quality_report_path)
```

## Pi smoke test

Generate the restaurant smoke-test site:

```bash
cd /home/ethan/Agentic
python3 -m backend.app.services.generate_site_cli \
  --input examples/omakase-restaurant-smoke-test.json \
  --output generated_sites
```

Then build it:

```bash
cd generated_sites/sample-omakase-restaurant
npm install
npm run build
```

With Codex refinement enabled:

```bash
cd /home/ethan/Agentic
python3 -m backend.app.services.generate_site_cli \
  --input examples/omakase-restaurant-smoke-test.json \
  --output generated_sites \
  --codex
```

## Quality checks

```bash
python3 -m py_compile \
  backend/app/services/site_generator.py \
  backend/app/services/agentic_site_builder.py \
  backend/app/services/site_quality.py \
  backend/app/services/generate_site_cli.py

python3 scripts/validate_site_quality.py generated_sites/<business-slug>

cd site-template
npm install
npm run build

cd ../frontend
npm install
npm run build
```

## Template development

```bash
cd site-template
npm install
npm run dev
npm run build
```

Generated sites read from `data/business.json`, `data/design.json`, and `data/sections.json`. Keep those schemas stable so older generated sites do not break.
