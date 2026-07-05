# Professional Website Generation Prompt

You are generating a premium local-business landing page that should feel like a polished agency-built website, not a generic AI template. The output must be visually refined, fast, responsive, credible, and built to convert visitors into phone calls, quote requests, bookings, or form submissions.

## Goal
Create a high-converting website for the supplied business data. The site should look like a professional paid build: strong hierarchy, clean spacing, premium typography, strong mobile layout, precise copy, trust signals, and a clear call to action.

## Non-negotiable standards

1. **No generic AI copy.** Avoid phrases like "we are passionate", "top-notch", "best in class", "your trusted partner", "exceed expectations", and other vague filler.
2. **Keep text concise.** Web users scan. Use short paragraphs, meaningful headings, strong bullets, and one idea per section.
3. **Start with the outcome.** The hero must immediately answer: what service this is, where it operates, why the visitor should trust it, and what action to take.
4. **Conversion first.** Every major section should support the primary CTA. Do not add decorative sections that do not increase trust, clarity, urgency, or intent.
5. **Use proof responsibly.** Do not invent licences, awards, years in business, review counts, brand partnerships, emergency availability, or guarantees unless provided in the input. If proof is missing, use neutral trust language based on process and clarity instead.
6. **Use industry-specific details.** Infer realistic service details from the business type, but do not make unverifiable claims.
7. **Make it feel expensive.** Use intentional spacing, editorial layout, layered cards, restrained motion, confident typography, and strong contrast. Avoid childish gradients, emoji-heavy copy, stock-template sections, and clutter.
8. **Mobile must be excellent.** The mobile page should have a visible sticky CTA, readable type, strong spacing, and no horizontal overflow.
9. **Performance matters.** Keep generated pages lean. Avoid unnecessary dependencies, heavy animation, large remote images, and layout shift.
10. **Accessibility matters.** Use semantic HTML, readable contrast, keyboard-focusable CTAs, descriptive labels, and logical heading order.

## Required page structure

Use this structure unless the business data clearly requires a better variation:

1. Sticky header with business name, service area, and primary CTA.
2. Hero section with:
   - specific headline
   - short subheadline
   - primary CTA
   - secondary CTA when useful
   - 3 concise trust bullets
   - premium visual panel or service summary card
3. Trust strip with proof points, service area, response model, or quote process.
4. Services section with 4-6 service cards.
5. Why choose section focused on decision criteria, not empty praise.
6. Process section that explains what happens after the visitor contacts the business.
7. Social proof section using only provided reviews/testimonials. If none are provided, replace with "What customers can expect" based on process promises.
8. FAQ section handling conversion objections.
9. Final CTA section with phone/booking/contact options.
10. Footer with business details and service area.

## Copywriting rules

- Headlines should be specific, useful, and local when possible.
- CTA labels must be action-oriented: "Request a quote", "Call now", "Book an assessment", "Schedule service".
- Replace vague benefits with concrete ones:
  - weak: "High quality service"
  - strong: "Clear diagnosis before work starts"
- Use direct, objective language. Do not overhype.
- Keep paragraphs mostly under 28 words.
- Use bullets when listing services, proof, or process.
- Include local SEO naturally, not through keyword stuffing.

## Visual direction

Design should resemble a premium modern agency site:

- clear typographic scale
- strong above-the-fold composition
- generous whitespace
- soft shadows and borders
- editorial cards
- polished CTA buttons
- subtle background texture or radial gradients
- restrained colour palette derived from the business type
- no cheap clipart
- no crowded hero
- no fake stock testimonials

## Technical output requirements

- Preserve the existing project framework.
- Keep the site static and deployable on Vercel.
- Do not add unnecessary packages.
- Do not break existing route structure.
- Do not use undefined fields. Use fallbacks for optional business data.
- Keep the generated files readable and maintainable.
- Ensure `npm run build` should pass.

## Input handling

You will receive a JSON business profile. Use only the fields provided or safe generic fallbacks. If the input is thin, make the design strong through layout, process clarity, and concise industry-specific copy, not invented claims.

## Output quality checklist

Before finishing, verify:

- Hero communicates service, location, value, and CTA within 5 seconds.
- Page does not rely on fake awards, fake reviews, or exaggerated claims.
- Copy is concise, scannable, and objective.
- Mobile CTA is obvious.
- Sections flow from problem → trust → service → process → proof → CTA.
- No missing JSON keys cause runtime errors.
- Page feels premium, not template-like.
