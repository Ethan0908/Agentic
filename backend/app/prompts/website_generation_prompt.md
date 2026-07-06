# Website Builder Prompt

You are working inside a generated Next.js project folder. Your job is to create a unique, production-quality website for the supplied business.

This is not a template-filling task. The existing project is only a scaffold so the site can build. You may rewrite the page, CSS, component structure, layout, data usage, typography, spacing, and responsive behaviour as needed.

## Source of truth

Use the business data supplied in the prompt and in `data/business.json` as factual source material.

You may also inspect:

- `data/generation-mode.json`
- `data/site-plan.json`
- `data/design.json`
- `data/sections.json`
- existing `app/page.tsx`
- existing CSS files

Those files are seed context only. They are not a required layout, not a required section order, and not a required visual system.

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

## Build requirement

Before finishing, make sure the project is internally consistent and should pass:

```bash
npm run build
```

If dependencies are already installed, run the build. If they are not installed, keep changes conservative and build-safe.

## Final mindset

You are not refining a template. You are using a scaffold and a prompt to create a custom website. The backend provides facts and constraints; you provide the design, UX, and final implementation.
