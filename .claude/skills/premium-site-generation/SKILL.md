---
name: premium-site-generation
description: Use when generating or refining a local-business website from Agentic lead data. Applies the project architecture, image rules, conversion rules, and validation checklist.
---

# Premium Site Generation

## When to use this skill

Use this skill whenever you generate, refine, or QA a business website in this repository.

## Source files

Read only the files needed for the current change. Start with:

- `data/business.json`
- `data/design.json`
- `data/sections.json`
- `data/site-plan.json`
- `app/page.tsx`
- `app/globals.css`
- `app/variants.css`
- `app/photos.css`

For generator/template changes, inspect:

- `backend/app/services/site_generator.py`
- `backend/app/services/agentic_site_builder.py`
- `backend/app/prompts/website_generation_prompt.md`
- `site-template/`

## Quality standard

The site should feel like a polished agency-built landing page, not a generic AI page.

Prioritize:

1. Clear hero: service, location, value, CTA.
2. Real business imagery when supplied.
3. Strong CTA hierarchy.
4. Concise industry-specific copy.
5. Responsive mobile layout.
6. Good contrast, spacing, rhythm, and accessibility.
7. Vercel-safe static output.

## Image rules

- Use `business.photos` and `business.heroImage` when present.
- Never add unrelated stock images.
- Never invent images, projects, awards, badges, reviews, or proof.
- If images are missing, use editorial composition, cards, typography, and section rhythm instead.
- Use descriptive alt text.
- Keep remote images lean and avoid layout shift.

## Copy rules

Avoid generic claims such as:

- top-notch
- best in class
- trusted partner
- world-class
- award-winning
- licensed / insured / certified unless supplied
- five-star / #1 / trusted by thousands unless supplied
- guaranteed / 24/7 / same-day unless supplied

Use direct, concrete wording:

- Clear diagnosis before work starts.
- Send photos and timing to get the next step.
- Book an assessment.
- Request a quote.
- Call now.

## Implementation rules

- Keep business data in JSON.
- Keep reusable layout logic in React/CSS.
- Preserve `data/design.json` and `data/sections.json` as the variant controls.
- Avoid new dependencies unless the gain is obvious and build-safe.
- Do not rewrite whole files unless a focused patch cannot solve the issue.

## Validation

Run what is available:

```bash
python -m py_compile backend/app/services/site_generator.py backend/app/services/agentic_site_builder.py
python scripts/validate_site_quality.py generated_sites/<business-slug>
cd site-template && npm run build
```

If dependencies are not installed, state that build validation was not run.
