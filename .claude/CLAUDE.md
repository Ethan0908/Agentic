# Agentic Website Builder Instructions

Keep this file concise so it does not waste context.

## Project goal
Generate premium, high-converting local-business websites from lead data.

## Architecture
- `backend/app/services/site_generator.py` is the main entrypoint.
- `backend/app/services/agentic_site_builder.py` creates compact `site-plan.json`, `design.json`, and `sections.json`.
- `backend/app/config/design_systems.json` controls visual systems.
- `backend/app/config/section_registry.json` controls section variants.
- `site-template/` is the canonical Next.js template.
- Generated websites read from `data/business.json`, `data/design.json`, and `data/sections.json`.

## Rules
- Do not turn this back into one huge prompt or one visual template.
- Do not invent licences, awards, review counts, years in business, warranties, emergency availability, or guarantees.
- Use short, specific, scannable copy.
- Prefer deterministic registries plus compact agent refinement.
- Use Haiku-level agents for classification/copy triage and Sonnet-level agents for frontend/design/QA work.
- Do not add dependencies unless the quality gain is obvious.
- Keep generated sites Vercel-friendly.

## Build checks
For template changes, run from `site-template/`:

```bash
npm install
npm run build
```

For Python syntax checks:

```bash
python -m py_compile backend/app/services/site_generator.py backend/app/services/agentic_site_builder.py
```
