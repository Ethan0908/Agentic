# Premium Website Generation Playbook

Use this playbook before writing code.

## 1. Pick a concept, not a template

Write the site as if it has an art direction sentence. Do not render the same section stack for every business.

Good concepts:

- Quiet clinical editorial for a dentist, therapist, or health office.
- Warm neighbourhood atelier for a cafe, studio, bakery, or boutique.
- Sparse luxury reservation page for an omakase, spa, or private service.
- Minimal editorial restaurant for hospitality, food, boutique, and atmosphere-led businesses.
- Technical proof-led layout for professional, legal, or financial services.
- Local field-guide layout for home service, repair, or construction businesses.
- Location-first storefront guide for businesses where address, hours, and area matter most.

Weak concepts:

- generic local service landing page
- modern premium website
- clean professional design
- hero, services, testimonials, CTA

## 2. Use a multi-pass build process

High-quality AI site builders do not rely on one generic template. They combine planning, generated code, preview, editing, integrations, and review. In this repo, Codex must simulate that process inside the local folder:

1. profile the business;
2. choose a conversion goal;
3. choose an art direction;
4. implement the custom React/CSS;
5. self-QA desktop and mobile;
6. revise anything that still feels generic.

Do not stop after the first plausible page. Improve it until the first screen, CTA hierarchy, copy, spacing, and mobile layout all feel intentional.

## 3. Choose one conversion path

Decide the one action the visitor should take. The CTA should match available contact facts:

- phone-first when a phone number exists and the service is urgent or appointment-driven;
- website-first when the business already has a working website and no phone/email is provided;
- email-first when email is the only contact method;
- location-first when the visitor likely wants address/directions;
- reservation-first for restaurants, bars, cafes, and hospitality when a booking or website path exists;
- quote-first when services are consultative and no direct booking path exists.

Avoid CTAs that go nowhere. If there is no valid link, render the CTA as explanatory copy rather than a fake button.

## 4. Make the design specific

Use the business name, category, city, service area, address, rating/review notes, phone, and website to shape copy and layout. Avoid stock copy. Avoid generic feature cards.

Design specificity can come from:

- an industry-specific hero structure;
- service-area mapping language;
- a realistic process section;
- a decision guide or expectation panel;
- a photo ribbon only when real photos exist;
- a local/address panel for storefronts;
- a booking/contact panel for clinics and appointment businesses;
- a reservation/location panel for restaurants and hospitality;
- a menu/service preview with aligned details when factual data supports it;
- an emergency call panel for urgent services only when supported by the data.

## 5. Editorial restaurant mode

For restaurants, cafes, bars, private dining, bakeries, food businesses, salons, spas, boutiques, galleries, studios, and other atmosphere-led sites, the default should be a minimal editorial restaurant style:

- large imagery, careful crops, and quiet overlays;
- generous empty space and wide margins;
- thin or regular serif display headings with a clean sans-serif for UI and body text;
- neutral palette: black, white, warm off-white, charcoal, beige, and restrained brass/gold accents;
- no bright gradients, no SaaS mesh backgrounds, no glassmorphism, no random icon packs;
- minimal anchor navigation with only the useful links;
- simple buttons with thin borders or solid dark fills;
- vertical single-page rhythm with hero, atmosphere, menu/services, experience, location/contact, final CTA, and footer;
- clean menu rows/columns, with prices only when supplied as facts;
- a quiet footer with contact, address, website, and socials only when supplied.

The page should feel calm, premium, and intimate. Luxury comes from restraint, photography, typography, spacing, and editorial composition rather than heavy decoration.

## 6. Visual quality checklist

The final page should include:

- A first viewport with strong type hierarchy and intentional negative space.
- A distinct layout rhythm, not equal-width boxes everywhere.
- CSS custom properties that fit the concept.
- Responsive behaviour that changes layout structure on mobile.
- At least one custom component or visual pattern that would not work unchanged for every industry.
- Clear visual grouping between services, proof, process, and CTA.
- Consistent spacing and border language.
- Accessible colour contrast.

## 7. Anti-AI-design checklist

Fix these before finishing:

- everything is in centred text;
- every section is a rounded card grid;
- the hero says generic marketing words without saying what the business does;
- the page uses fake review/testimonial/proof language;
- the site could be rebranded by changing only the logo/name;
- buttons have no real `href` or action;
- photos are stretched, tiny, irrelevant, or leaking API keys in query strings;
- mobile is only a squished desktop layout;
- paragraphs are too long for a landing page;
- restaurants, cafes, bars, salons, spas, boutiques, and studios look like generic SaaS or contractor pages instead of atmosphere-led editorial pages.

## 8. Do not invent facts

Never invent awards, credentials, staff names, prices, menu items, guarantees, years in business, emergency availability, same-day service, or promises.

When proof is missing, use careful expectation-setting instead:

- what the visitor can ask about;
- how to prepare before calling;
- what service areas are mentioned;
- what services are listed;
- what information is available from the existing website.

## 9. Finish criteria

Remove every placeholder. The site must be coherent if screenshots are viewed without context. The site must pass `npm run build` or be written conservatively enough to pass in this scaffold.