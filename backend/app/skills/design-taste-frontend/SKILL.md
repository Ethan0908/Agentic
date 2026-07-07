---
name: design-taste-frontend
source: https://github.com/Leonxlnx/taste-skill
source_skill: design-taste-frontend
description: Persistent anti-slop frontend design skill for generated local-business websites. Adapted for this generator's Next.js static-site scaffold.
---

# Design Taste Frontend Skill

Use this skill on every generated business website before writing React or CSS.

## 0. Full-site authority

Codex is not a template filler. Codex may rewrite the entire generated frontend when the current page looks scaffold-like or not premium enough.

Allowed edits include:

- `app/page.tsx`;
- `app/globals.css`;
- `app/layout.tsx`;
- new files under `app/` or `components/`;
- `package.json`, when a dependency is genuinely useful and the project remains buildable.

The baseline is a fallback/reference, not a restriction. Preserve factual business data, not weak layout choices.

## 1. Read the room first

Before code, infer:

- page kind: local service, storefront, clinic, restaurant, professional practice, boutique, portfolio, or other;
- audience: urgent caller, appointment booker, comparison shopper, local visitor, trust-first buyer, or visual consumer;
- available brand assets: logo, public photos, colours, typography clues, address, website, phone, reviews, service list;
- quiet constraints: medical/legal/financial trust, accessibility, family services, public safety, regulated claims.

Do not default to AI-purple gradients, centred hero over dark mesh, three equal feature cards, generic glassmorphism, Inter plus slate, or vague trust copy.

## 2. Set the three dials

Use these as design variables in the plan:

- DESIGN_VARIANCE: 1 = perfectly conventional, 10 = experimental. Default 8 for generated premium sites.
- MOTION_INTENSITY: 1 = static, 10 = cinematic. Default 4, but use 2 for trust-critical sites.
- VISUAL_DENSITY: 1 = airy gallery, 10 = dense cockpit. Default 4.

For trust-critical industries, reduce variance and motion. For restaurants, boutiques, studios, and luxury services, increase visual rhythm and photo use.

## 3. Structure before code

Write or follow `DESIGN_SPEC.md` before implementation. It must include:

- design read;
- single art direction for the whole site;
- site sections in order;
- component list;
- CTA map;
- colour and typography system;
- image/asset strategy;
- optional interaction plan;
- mobile behaviour;
- baseline elements to delete or replace;
- anti-generic checks.

## 4. Typography rules

- Avoid defaulting to Inter unless the brief clearly calls for a neutral product look.
- Use wide headline containers so hero text does not become a narrow six-line wall.
- Prefer `clamp()` for display type and responsive spacing.
- Body copy should be short, readable, and under control. Avoid large paragraphs.
- Use one clear hierarchy: eyebrow or location line, H1, supporting line, CTA row, trust/contact note.
- If the page feels like scaffold text, rewrite the section structure and typography, not just the copy.

## 5. Layout rules

- Use CSS Grid for major layout, not fragile flex percentage math.
- Make the first viewport distinctive: split panel, editorial composition, bento field guide, photo-led hero, technical dossier, or calm clinical panel.
- Do not use identical rounded cards for every section.
- Mix at least two section rhythms: e.g. service matrix plus process timeline, proof rail plus location panel, photo ribbon plus CTA drawer.
- The mobile layout must be redesigned, not just squeezed.
- Use `overflow-x: hidden` on the page shell to prevent accidental horizontal scrolling.
- If the current page feels like a starter template, delete the structure and rebuild it around a stronger concept.

## 6. Full-site build discipline

Build in passes, but the main implementation pass may edit the whole site:

1. foundation: data helpers, CTA helpers, shell, design tokens;
2. full-site composition: header, hero, sections, contact, mobile CTA;
3. useful interactions that fit the business;
4. visual-director review;
5. polish and QA.

Each pass should improve the previous one instead of preserving weak scaffold choices.

## 7. Interactions

Only add interactions when they help. Examples:

- pricing or service-scope toggle when price tiers or categories exist;
- FAQ accordion when FAQs exist or can be safely derived from factual service data;
- modal/contact drawer when there are multiple contact paths;
- sticky mobile CTA for phone-first or appointment-first sites;
- hover states and image reveals using CSS transitions;
- subtle scroll/entrance motion if the package is installed or safely added.

Do not add fake dashboards, arbitrary counters, fake testimonials, or meaningless animation.

## 8. Assets and branding

Use supplied business photos, logo, website screenshots, or brand colours when present. If no real images are available, create visual quality through typography, layout, gradient fields, CSS shapes, borders, and cards. Do not hotlink unrelated stock photography unless the business profile explicitly allows stock imagery.

Sanitize asset URLs. Never expose API keys or private tokens in image URLs or rendered markup.

## 9. Final anti-slop check

Before finishing, verify:

- no placeholder markers;
- no fake proof;
- no generic hero language;
- H1 is readable and not too narrow;
- buttons have strong contrast;
- mobile has a real layout;
- sections do not all look identical;
- photos are used intentionally;
- the page could not be rebranded by changing only the business name;
- the output looks like a finished custom site, not a scaffold with text.
