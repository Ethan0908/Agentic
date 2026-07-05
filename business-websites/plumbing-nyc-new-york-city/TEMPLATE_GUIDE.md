# Generated Website Template

This folder is the canonical base template for every generated website.

`backend/app/services/site_generator.py` copies this entire folder into:

```text
/app/.generated-sites/<business-slug>
```

Then `backend/app/services/codex_site.py` runs Codex inside that copied folder using the prompt at:

```text
backend/app/prompts/website_generation_prompt.md
```

Edit this folder when you want to improve the starting website design.
Edit the prompt file when you want to improve Codex's instructions.
Do not edit files inside `/app/.generated-sites` directly because those are temporary generated outputs.
