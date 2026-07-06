# Professional Website Generation Prompt

You are refining a generated premium local-business landing page. The project already contains a compact `data/site-plan.json`, `data/business.json`, `data/design.json`, and `data/sections.json`. Use those files as the source of truth instead of inventing a new site from scratch.

## Goal

Improve the generated website so it feels like a polished agency-built site: visually refined, fast, responsive, credible, specific, and built to convert visitors into phone calls, quote requests, bookings, reservation inquiries, consultation requests, or form submissions.

## Architecture rules

1. Do not turn this into one template. Preserve variant-driven rendering through `data/design.json` and `data/sections.json`.
2. Do not paste or rewrite whole files unless a focused patch is not enough.
3. Keep the generated site static and deployable on Vercel.
4. Do not add dependencies unless the quality gain is obvious and build-safe.
5. Prefer small high-leverage changes over large speculative rewrites.
6. Keep business data in JSON and presentation in React/CSS. Do not hardcode one company's copy into reusable template code.
7. Preserve `data/business.json`, `data/design.json`, `data/sections.json`, and `data/site-plan.json` unless you are correcting a real generated-site problem.

## Non-negotiable standards

1. **No generic AI copy.** Avoid phrases like "we are passionate", "top-notch", "best in class", "your trusted partner", "exceed expectations", and other vague filler.
2. **Keep text concise.** Web users scan. Use short paragraphs, meaningful headings, strong bullets, and one idea per section.
3. **Start with the outcome.** The hero must immediately answer: what service this is, where it operates, why the visitor should trust it, and what action to take.
4. **Conversion first.** Every major section should support the primary CTA. Do not add decorative sections that do not increase trust, clarity, urgency, or intent.
5. **Use proof responsibly.** Do not invent licences, awards, years in business, review counts, brand partnerships, emergency availability, menu items, pricing, client outcomes, or guarantees unless provided in the input.
6. **Use vertical-specific details.** Infer realistic service/dining/booking/intake details from the business type, but do not make unverifiable claims.
7. **Make it feel expensive.** Use intentional spacing, editorial layout, layered cards, restrained motion, confident typography, strong contrast, and real business imagery when supplied.
8. **Mobile must be excellent.** The mobile page should have a visible sticky CTA, readable type, strong spacing, and no horizontal overflow.
9. **Performance matters.** Keep generated pages lean. Avoid unnecessary dependencies, heavy animation, large remote images, and layout shift.
10. **Accessibility matters.** Use semantic HTML, readable contrast, keyboard-focusable CTAs, descriptive labels, and logical heading order.

## Vertical-specific rules

- Omakase, sushi, restaurant, dining, bar, cafe, and catering sites must sound like hospitality/reservation pages, not home-service pages.
- Clinics, spas, salons, and wellness sites must sound calm and appointment-led, not repair-led.
- Law, accounting, finance, consulting, and advisory sites must sound restrained and consultation-led, not emergency-service pages.
- Emergency trade pages should be phone-first and direct, but still cannot invent response times, licences, or availability.
- Never replace vertical-specific `pageCopy` with generic copy.

## Image and uniqueness rules

- If `data/business.json` contains `photos` or `heroImage`, use those images intentionally in the hero, gallery ribbon, or supporting cards.
- Never add unrelated stock images just to make the site look better.
- If images are missing, improve the site with layout, typography, cards, colour, and copy instead of fake photos.
- Each business should feel different through design-system choice, section variants, image strategy, CTA wording, industry-specific copy, and service ordering.
- Do not over-crop logos or tiny UI screenshots as hero photography. Use them smaller or remove them if they weaken the page.

## Agent workflow

When Claude Code project agents are available, use them this way:

1. `business-profiler` verifies vertical, customer intent, image availability, trust gaps, and unsafe claims.
2. `conversion-strategist` checks section order, CTA hierarchy, and objection handling.
3. `brand-director` improves design-system fit and premium visual direction.
4. `copy-polisher` removes generic text and tightens CTAs.
5. `frontend-refiner` applies focused React/CSS improvements.
6. `visual-qa` checks mobile, hierarchy, spacing, CTA visibility, image handling, and fake proof.

## Copywriting rules

- Headlines should be specific, useful, and local when possible.
- CTA labels must be action-oriented: "Request a quote", "Call now", "Request a reservation", "Request an appointment", "Request a consultation".
- Replace vague benefits with concrete ones:
  - weak: "High quality service"
  - strong: "Clear diagnosis before work starts"
- Use direct, objective language.
- Keep paragraphs mostly under 28 words.
- Use local SEO naturally, not through keyword stuffing.

## Visual direction

Design should resemble a premium modern agency site:

- clear typographic scale
- strong above-the-fold composition
- generous whitespace
- soft shadows and borders
- editorial cards
- polished CTA buttons
- restrained colour palette derived from the business type
- real business photos when supplied
- no cheap clipart
- no crowded hero
- no fake stock testimonials

## Output quality checklist

Before finishing, verify:

- Hero communicates service, location, value, and CTA within 5 seconds.
- Page does not rely on fake awards, fake reviews, or exaggerated claims.
- Copy is concise, scannable, and objective.
- Vertical is correct; for example, an omakase page must not mention repair, installation, maintenance, or quote paths unless those words are truly in the input.
- Mobile CTA is obvious.
- Supplied business photos are used correctly, with useful alt text and no broken layout.
- Sections flow from problem → trust → service/experience → process → proof → CTA.
- `python3 -m backend.app.services.site_quality <site>` is not required, but the generated-site quality report should pass when the repo-side generator runs.
- `npm run build` should pass.
