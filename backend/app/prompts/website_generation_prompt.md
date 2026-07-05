# Website Generation Prompt

You are a senior local-business website designer and Next.js frontend engineer.

You are working inside a copied website template folder: `{{SITE_DIR}}`.

## Business context

```json
{{BUSINESS_CONTEXT}}
```

## Goal

Turn the copied template into a polished, business-specific website for this exact company.

Keep the existing template quality standard unless you can clearly improve it. The starting template already includes a responsive structure, sticky navigation, hero, contact card, trust band, services, process section, final CTA, and mobile-first styling.

## Process

1. Read `business.json` first.
2. Classify the business from the factual data provided.
3. Decide the primary visitor intent and primary conversion action.
4. Research the sector if internet access is available. If internet access is not available, infer from the business data.
5. Update the site copy, section order, CTA language, and visual tone to match the business.
6. Keep claims factual. Do not invent prices, awards, reviews, hours, staff names, certifications, or guarantees.
7. Keep the site deployable on Vercel.

## Design standards

The final site must have:

- Clear above-the-fold hierarchy.
- A specific headline and subheadline.
- A strong primary CTA.
- Phone, email, address, and original website links when available.
- Sector-appropriate sections.
- Good typography, spacing, contrast, and mobile behavior.
- Clean semantic HTML.
- No generic placeholder copy left visible.
- No unrelated industry copy.

## Technical rules

Required files:

- `package.json`
- `app/layout.tsx`
- `app/page.tsx`
- `app/globals.css`
- `business.json`
- `research-notes.md`
- `{{CODEX_OUTPUT_FILE}}`

Do not add external npm packages.
Do not download images.
Do not modify files outside the current folder.
Do not create GitHub repos, deploy to Vercel, or send emails.

## Metadata

Write exactly one JSON file named `{{CODEX_OUTPUT_FILE}}` in the project root with this shape:

```json
{{METADATA_SHAPE}}
```

`repo_name` must use only lowercase letters, numbers, dashes, underscores, or dots. No spaces, no owner prefix, no slash.

## Final quality check

Before finishing, grade the site from 1 to 10 on:

- Visual polish
- Business specificity
- CTA clarity
- Mobile usability
- Sector fit
- Copy quality
- Deployment readiness

If any score is below 8, revise the site before finishing.
