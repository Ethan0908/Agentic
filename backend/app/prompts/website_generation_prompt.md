# Premium Website Builder Prompt

You are working inside a generated Next.js project folder. Your job is to create a unique, production-quality website for the supplied business.

This is not a template-filling task. The existing project is only a scaffold so the site can build. You may rewrite the page, CSS, component structure, layout, data usage, typography, spacing, and responsive behaviour as needed.

## Source of truth

Use the business data supplied in the prompt and in `data/business.json` as factual source material.

Also inspect:

- `AGENTS.md`
- `DESIGN_STUDIO_BRIEF.md`
- `data/generation-mode.json`
- `data/site-plan.json`
- `data/design.json`
- `data/sections.json`
- existing `app/page.tsx`
- existing CSS files

Those files are seed context only. They are not a required layout, not a required section order, and not a required visual system.

## Enriched business fields

When present, use these fields to make the page more specific without inventing claims:

- `address`
- `rating`
- `reviewCount`
- `contentAngles`
- `visitorQuestions`
- `proofPoints`

Treat `contentAngles` and `visitorQuestions` as design and copy prompts, not as factual claims. For example, they can shape a patient decision guide, a service-area checklist, a visit-planning panel, or a buyer-prep section.

## Main objective

Build a custom site that feels made for this specific business, not copied from a vertical template.

The final site should:

- look premium and intentional
- clearly explain the business and next step
- use the business's actual photos when supplied
- avoid fake proof and exaggerated claims
- be excellent on mobile
- build successfully with `npm run build`
- remain deployable as a static Next.js/Vercel site

## Mandatory generation process

Before editing files, silently complete this process:

1. Read the business JSON and site plan.
2. Decide the visitor's likely intent: call, book, request a quote, visit location, or review services.
3. Choose one named design concept. Example: `quiet clinical editorial`, `neighbourhood field guide`, `gallery-led luxury reservation page`, `technical proof dossier`, or another concept that fits the business.
4. Select a visual rhythm that is not just a hero plus equal-width cards. Use asymmetry, editorial blocks, sticky CTA, split panels, bento panels, timeline, location panel, service matrix, proof rail, or another pattern when appropriate.
5. Implement the site in `app/page.tsx` and `app/globals.css`.
6. Self-review the result against the quality checklist below and revise weak parts before finishing.

Do not print the plan. Implement the site.

## What you are allowed to change

You may change, rewrite, or replace:

- `app/page.tsx`
- `app/globals.css`
- `app/layout.tsx`
- any local CSS imported by the app
- local components you create
- how JSON data is read and rendered
- section order
- CTA hierarchy
- page structure
- visual direction
- responsive layout
- image treatment
- microcopy

You may remove unused scaffold imports, unused sections, or generic layout code.

Do not preserve code just because it already exists. Keep only what improves the final site.

## What you should not do

Do not:

- create hardcoded reusable vertical templates
- force every restaurant, plumber, clinic, or law firm into the same structure
- add unrelated stock photos
- invent awards, licences, certifications, review counts, ratings, prices, guarantees, emergency availability, menu items, case results, client names, or years in business
- add fake testimonials
- overstuff local SEO keywords
- add heavy dependencies unless absolutely necessary
- break Vercel/static deployment assumptions

## How to design the site

Start from the business itself. Infer the best structure from the business data, not from a predetermined backend template.

For each site, decide:

- what the visitor most likely wants
- what action the page should drive
- what proof is actually available
- whether the site should be urgent, calm, editorial, luxurious, technical, clinical, local, visual, or minimal
- how photos should be used if supplied
- what should be removed because it feels generic

The site can be one page, but it should not feel like a generic landing-page checklist. Use only sections that make sense for the business.

## Required page depth

The page must feel complete when viewed as screenshots without context. It should normally include at least 9 meaningful sections plus a footer:

1. navigation with anchors and CTA
2. art-directed hero
3. credibility or positioning strip
4. business thesis or belief section
5. service/program architecture
6. visitor decision guide
7. process, visit flow, or expectation section
8. proof or factual listing section
9. location/service-area or conversion section
10. FAQ/visitor-questions section when useful
11. final CTA
12. footer

Do not make these sections all look the same. At least four section rhythms should be visibly different.

## Design quality bar

The page should look like a careful agency landing page, not like an AI default.

Use:

- CSS custom properties for the concept's colour, border, radius, shadow, and spacing system
- `clamp()` for responsive type and spacing
- one strong first viewport with obvious CTA hierarchy
- varied section composition instead of repeating identical cards
- purposeful negative space
- custom service/proof modules that fit the business type
- a mobile layout that changes structure, not merely shrinks
- real contact paths from available data
- content-specific icons or text marks only if they are simple CSS/HTML, not external assets
- custom `next/font` typography from `app/layout.tsx` or the page implementation

Avoid:

- generic beige SaaS gradients unless the business truly calls for that tone
- identical rounded cards for every section
- huge vague paragraphs
- fake dashboard/mockup blocks that have nothing to do with the business
- CTAs that point nowhere when phone, email, or website data exists
- visual clutter above the fold

## Copy standards

Use concise, specific copy. Prefer direct sentences over marketing filler.

Avoid phrases like:

- top-notch
- world-class
- best in class
- your trusted partner
- exceed expectations
- passionate about serving
- cutting-edge solutions
- award-winning unless provided

Every headline should earn its place. Every paragraph should help the visitor understand, trust, or act.

## Image standards

If `photos` or `heroImage` are provided:

- use them intentionally
- write descriptive alt text
- crop with care
- avoid stretching or using tiny logos as full hero photos
- use weaker images smaller if needed
- do not expose private API keys in image URLs or query strings

If no real photos are provided:

- do not add fake stock photos
- create quality through typography, spacing, cards, layout, gradients, and copy

## UI/UX standards

The final site should have:

- a strong above-the-fold composition
- clear primary CTA
- scannable sections
- polished spacing
- premium typography hierarchy
- accessible contrast
- mobile sticky or repeated CTA when appropriate
- no horizontal overflow
- no crowded hero
- no tiny unreadable text
- no dead links unless no contact method exists

## Final self-review before stopping

Before finishing, check the generated files for:

- `AGENTIC_REPLACE_ME`
- placeholder copy
- invented claims
- generic AI phrases
- broken or empty CTA links
- image URLs with leaked API keys or irrelevant stock domains
- TypeScript errors from unsafe JSON assumptions
- CSS that works only on desktop
- sections that could be copied unchanged into any other business
- fewer than 9 meaningful sections
- no real `<footer>` element
- weak or default typography

Fix any issue you find.

## Build requirement

Before finishing, make sure the project is internally consistent and should pass:

```bash
npm run build
```

If dependencies are already installed, run the build. If they are not installed, keep changes conservative and build-safe.

## Final mindset

You are not refining a template. You are using a scaffold and a prompt to create a custom website. The backend provides facts and constraints; you provide the design, UX, and final implementation.
