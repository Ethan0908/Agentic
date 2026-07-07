---
description: Build a custom premium website from business facts. Use when generating or improving a local business website, landing page, or Vercel-ready Next.js site.
---

# Premium Website Builder Skill

You are not filling a landing-page template. Create a site with a specific editorial/design concept derived from the business.

## Required process

1. Read the supplied business facts and identify the visitor's real job-to-be-done.
2. Choose one distinct design concept before coding. Examples: quiet clinical editorial, dramatic luxury hospitality, technical field-service dashboard, neighborhood craft studio, high-trust professional office.
3. Rewrite `app/page.tsx` and `app/globals.css` around that concept.
4. Use only facts provided. Do not invent awards, credentials, testimonials, team size, years in business, guarantees, prices, or emergency availability.
5. Build a finished page, not a wireframe.

## Anti-template rules

Do not use a predictable hero/features/services/testimonials/contact stack unless the business truly demands it.
Do not use generic cards with identical icons.
Do not make every local business look like the same SaaS landing page.
Do not use generic marketing phrases such as world-class, top-notch, trusted partner, best-in-class, or exceed expectations.
Do not create fake reviews or fake proof.

## Layout standards

The first viewport must have a deliberate composition: asymmetric grid, editorial split, strong type lockup, visual rhythm, or a high-quality minimal layout.
Every section must have a reason to exist.
Use white space, scale, contrast, and alignment instead of decoration.
Create at least one memorable visual device: custom stat band, location panel, appointment rail, service matrix, process timeline, typographic masthead, map-inspired block, or layered content system.

## Code standards

Keep dependencies minimal.
Use semantic HTML.
Use CSS that is specific to this site, not a reusable template system.
Ensure mobile has no horizontal overflow.
Use real links only when supplied.
Run or reason through `npm run build` before finishing.
