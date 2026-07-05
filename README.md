# Agentic Website Builder

This repository is the source of truth for the website builder. The Raspberry Pi should run a direct copy of this repo instead of keeping separate local-only logic.

## What this branch adds

- `backend/app/prompts/website_generation_prompt.md` — the single prompt used to guide Codex or any website-refinement agent.
- `backend/app/services/site_generator.py` — clean Python service for normalizing lead data and generating a site from the canonical template.
- `site-template/` — the canonical premium Next.js template used for every generated business site.

## Design direction

The builder is designed to create professional local-business sites that feel closer to a paid agency build than a generic AI landing page. The template emphasizes:

- concise, scannable copy
- strong above-the-fold CTA hierarchy
- trust points without fake claims
- premium spacing and typography
- mobile-first conversion flow
- fast static deployment on Vercel

## Basic generation flow

1. Collect or infer a business profile from lead data.
2. Normalize it with `normalize_business_profile()`.
3. Copy `site-template/` into `generated_sites/<business-slug>/`.
4. Write `generated_sites/<business-slug>/data/business.json`.
5. Optionally run Codex refinement using `website_generation_prompt.md`.
6. Push the generated site repo and deploy it to Vercel.

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
        "services": [
            {"title": "Drain clearing", "description": "Clear blocked drains with a practical diagnosis before work starts."},
            {"title": "Leak repair", "description": "Find the source of the leak and explain the next step clearly."}
        ]
    },
    refine_with_codex=False,
)

print(site.path)
```

## Template development

```bash
cd site-template
npm install
npm run dev
npm run build
```

The generated site reads from `site-template/data/business.json`. Keep that schema stable so older generated sites do not break.
