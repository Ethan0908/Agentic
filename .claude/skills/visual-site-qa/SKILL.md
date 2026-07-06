---
name: visual-site-qa
description: Use after generating or editing an Agentic business website to review design quality, mobile layout, CTA clarity, image handling, fake proof, and build risk.
---

# Visual Site QA

Review the generated site like a strict design QA lead.

## Inputs to inspect

- `data/business.json`
- `data/design.json`
- `data/sections.json`
- `data/site-plan.json`
- `app/page.tsx`
- `app/globals.css`
- `app/variants.css`
- `app/photos.css`

## Output format

Return compact findings grouped by severity:

- blocker: build failure, broken CTA, unreadable mobile, horizontal overflow, invalid JSON, broken required data.
- major: weak hero, generic copy, bad image crop, poor contrast, cramped spacing, fake proof, one-template feel.
- minor: polish issues, rhythm inconsistencies, weak microcopy, naming cleanup.

For each finding include:

- file/path
- problem
- recommended fix

## Review checklist

Hero:

- Does the first screen clearly say what the business does?
- Does it state the service area?
- Is there one obvious primary action?
- Is the headline specific rather than generic?

Images:

- Are supplied business photos used when present?
- Are unrelated stock images absent?
- Are images cropped cleanly?
- Is alt text useful?
- Does mobile still work when no images are present?

Conversion:

- Does every major section support trust, clarity, intent, or action?
- Are CTAs repeated at sensible moments?
- Does the FAQ reduce hesitation?

Trust:

- No fake review counts.
- No fake awards.
- No fake licences or certifications.
- No fake emergency or same-day availability.

Mobile:

- No horizontal overflow.
- Sticky CTA is visible.
- Tap targets are large enough.
- Hero text is readable.
- Cards are not cramped.

Build:

- JSON remains valid.
- TypeScript remains buildable.
- No unnecessary packages.
