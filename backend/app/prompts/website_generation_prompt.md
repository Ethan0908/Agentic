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

## Main objective

Build a custom site that feels made for this specific business, not copied from a vertical template.

The default visual north star is a minimal, editorial, image-led single-page website: calm, refined, premium, and spacious. For restaurants, cafes, bars, private dining, bakeries, boutiques, salons, spas, studios, and other atmosphere-led businesses, strongly prefer an upscale editorial restaurant style over a generic local-business landing page.

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
3. Choose one named design concept. Example: `quiet clinical editorial`, `neighbourhood field guide`, `gallery-led luxury reservation page`, `technical proof dossier`, `minimal editorial restaurant`, or another concept that fits the business.
4. Select a visual rhythm that is not just a hero plus equal-width cards. Use asymmetry, editorial blocks, sticky CTA, split panels, bento panels, timeline, location panel, service matrix, proof rail, photo-led menu, reservation panel, or another pattern when appropriate.
5. Implement the site in `app/page.tsx` and `app/globals.css`.
6. Self-review the result against the quality checklist below and revise weak parts before finishing.

Do not print the plan. Implement the site.

## What you are allowed to change

You may change, rewrite, or replace:

- `app/page.tsx`
- `app/globals.css`
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

## Editorial restaurant / atmosphere-led mode

Use this mode whenever the business is a restaurant, cafe, bakery, bar, omakase, private dining room, hospitality venue, salon, spa, boutique, gallery, studio, or another business where mood, photography, and place matter.

Design traits:

- Minimal editorial restaurant feel: refined, intimate, spacious, and quiet.
- Large visual imagery with careful cropping, not busy decoration.
- Generous negative space and disciplined margins.
- Thin or regular-weight serif display headings paired with a clean sans-serif for navigation, buttons, details, menu items, and body text.
- Large, sometimes uppercase headings with controlled letter spacing.
- Neutral palette: black, white, warm off-white, charcoal, soft beige, and restrained brass/gold accents.
- Avoid bright colours, loud gradients, glassmorphism, neon, and generic SaaS styling.
- Fixed or top-positioned minimal navigation with a few anchor links.
- Simple rectangular or softly rounded buttons with thin borders or solid dark fills.
- Clear vertical single-page flow: hero, atmosphere/brand thesis, menu or services, experience/process, location/contact, reservation/final CTA, footer.
- Menu/service areas should use clean rows or columns with aligned details and prices only when prices are factual.
- Footer should be quiet and functional: address, hours/contact if factual, website/social links if supplied.

Composition ideas:

- Full-width or split hero image with text layered carefully or placed beside the image.
- Editorial intro block with one strong sentence and short supporting copy.
- Photo ribbon or gallery strip using real photos.
- Menu preview with refined dividers and aligned metadata.
- Reservation/contact panel that feels like a restaurant booking card, not a generic CTA block.
- Location block with address, service area, directions CTA, and concise visit details.

The goal is luxury through restraint. Make food, interiors, service, or brand atmosphere feel premium without adding fake claims.

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
- hospitality/restaurant pages that look like SaaS templates instead of editorial, image-led experiences

Fix any issue you find.

## Build requirement

Before finishing, make sure the project is internally consistent and should pass:

```bash
npm run build
```

If dependencies are already installed, run the build. If they are not installed, keep changes conservative and build-safe.

## Final mindset

You are not refining a template. You are using a scaffold and a prompt to create a custom website. The backend provides facts and constraints; you provide the design, UX, and final implementation.