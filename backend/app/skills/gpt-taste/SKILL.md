---
name: gpt-taste
source: https://github.com/Leonxlnx/taste-skill
source_skill: gpt-taste
description: Codex-focused anti-slop skill for full-site premium redesigns, higher-variance hero layouts, stronger spacing, careful grids, and mandatory pre-flight design planning.
---

# GPT Taste Skill for Codex

Use this when Codex is generating or refining a visual website.

## Core directive

Codex is allowed to redesign the entire frontend. Do not behave like a cautious patch editor. If the current page looks like scaffolding with text, replace it.

Break the common LLM frontend defaults:

- narrow 6-line hero headings;
- centred dark-gradient hero plus three cards;
- cheap labels like `SECTION 01`, `QUESTION 05`, or `ABOUT US`;
- invisible button text;
- repeated left/right sections;
- empty bento grid holes;
- generic stock-looking sections;
- layout that only looks acceptable at one desktop width;
- local-business pages that look like generic SaaS templates;
- baseline sections that are technically complete but visually boring.

## Mandatory design plan before code

Before writing React or CSS, create or follow a `<design_plan>` / `DESIGN_SPEC.md` with:

1. deterministic design selection: hero architecture, typography stack, component architectures, interaction pattern;
2. page structure: navigation, attention, interest, desire, action;
3. hero math: max width and type scale so H1 lands in about 2-3 lines on desktop;
4. grid math: service/proof/bento layout with no dead empty cells;
5. label and contrast sweep: no meta-labels, buttons remain readable;
6. mobile behaviour: how sections collapse or reorder;
7. asset policy: real assets first, no unrelated stock unless explicitly allowed;
8. deletion plan: what scaffold/baseline elements will be removed because they look cheap.

## Full-site rewrite permission

Allowed edits:

- rewrite `app/page.tsx` from scratch;
- rewrite `app/globals.css` from scratch;
- update `app/layout.tsx` metadata/fonts/body structure;
- create `components/*` files if it improves structure;
- update `package.json` for a justified dependency, then keep the project buildable.

The only things that must be preserved are factual business data, real contact paths, real photos/logo/brand assets, and safety against invented claims.

## Hero rules

- Make the hero breathe.
- Use a wide container and `clamp()` type.
- The H1 should normally be 2-3 desktop lines, not a vertical text wall.
- Do not place raw stats or spammy badges in the hero unless factual data supports them.
- Hero CTA must use real phone/email/website/address data when available.
- The first viewport should look art-directed, not assembled from starter components.

Approved hero families:

- cinematic centre with strong CTA and background treatment;
- artistic asymmetry with image or visual object;
- editorial split with negative space;
- technical proof dossier for professional services;
- local field-guide for home/service businesses;
- quiet clinical panel for healthcare or trust-first work;
- gallery-led luxury for restaurants, salons, boutiques, and studios.

## Component arsenal

Choose only what fits the business:

- gapless bento grid;
- horizontal service selector;
- FAQ accordion;
- contact drawer/modal;
- sticky mobile CTA;
- location/contact panel;
- process timeline;
- proof rail;
- photo ribbon;
- comparison/decision guide;
- service matrix;
- editorial quote/proof spread;
- split sticky narrative section.

Use 3-5 highly intentional modules rather than 8 weak cards.

## Motion and interaction

Prefer native CSS transitions unless a package is already installed or intentionally added. Use:

- hover scale inside overflow-hidden image containers;
- focus-visible rings;
- accordion transitions;
- sticky CTA;
- subtle ambient backgrounds;
- reduced-motion-safe CSS;
- scroll/entrance motion only if implemented build-safely.

Do not add animation that distracts from conversion or makes the site feel like a demo.

## Asset rules

- Use `business.photos`, `business.heroImage`, `business.logo`, and brand fields first.
- Crop photos carefully with `object-fit: cover`.
- Weak photos should become smaller accents, not full-screen heroes.
- If no photos exist, create premium composition through layout, type, CSS gradients, linework, and cards.
- Never render API keys, private query tokens, or scraper implementation details in asset URLs.

## Final pre-flight

The final files should pass these checks:

- `app/page.tsx` is not thin or placeholder-like;
- `app/globals.css` contains a real design system;
- at least one media query exists;
- `clamp()` is used for type or spacing;
- CTA links are real where data exists;
- no fake claims;
- no generic AI phrases;
- no horizontal overflow;
- mobile and desktop both look intentional;
- the finished site no longer looks like the baseline scaffold.
