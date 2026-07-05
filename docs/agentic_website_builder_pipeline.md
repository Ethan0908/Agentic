# Agentic Website Builder Pipeline

The builder should behave like a small design-and-code studio, not a single prompt.

## Pipeline

1. **Normalize business data**
   - Entry: `normalize_business_profile()`
   - Output: `data/business.json`

2. **Select design system**
   - Entry: `select_design_system()`
   - Registry: `backend/app/config/design_systems.json`
   - Output: `data/design.json`

3. **Plan section variants**
   - Entry: `build_section_plan()`
   - Registry: `backend/app/config/section_registry.json`
   - Output: `data/sections.json`

4. **Persist compact shared context**
   - Entry: `write_site_plan()`
   - Output: `data/site-plan.json`

5. **Render deterministic baseline**
   - Source: `site-template/`
   - The template uses `business.json`, `design.json`, and `sections.json` so different industries produce different layouts and visual systems.

6. **Optional Claude Code refinement**
   - Project agents live in `.claude/agents/`.
   - The orchestrator builds a compact prompt instead of pasting whole files.
   - Haiku-level agents handle classification and copy triage.
   - Sonnet-level agents handle brand, frontend, and visual QA.

7. **Quality gate**
   - Run `python scripts/validate_site_quality.py generated_sites/<slug>`.
   - Run `npm run build` inside the generated site when dependencies are installed.

## Why this is token efficient

- Agents receive compact JSON and paths, not the full repo.
- Reusable registries keep design knowledge out of long prompts.
- Repeated decisions are deterministic where possible.
- Claude is used for the parts humans actually pay designers/engineers for: judgement, polish, and QA.

## Why this is not one template

There is one canonical codebase for maintainability, but multiple runtime design systems:

- `premium-local-service`
- `emergency-response`
- `clinical-trust`
- `professional-advisory`
- `boutique-luxury`
- `modern-growth`

Each design system can select different hero, proof, services, process, and CTA variants.
