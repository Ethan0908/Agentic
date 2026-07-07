# ClassHour-Level Single-Page Website Contract

Use ClassHour-level quality as the benchmark, not as something to copy exactly. The goal is a complete premium editorial single-page website, not a local-business template.

## Reference quality traits

A successful generated site should feel like a finished product page from a small premium studio:

- complete editorial single-page website, not a shell;
- custom font pairing and clear typographic hierarchy;
- art-directed first viewport;
- nav, hero, credibility/authority strip, belief/mission section, proof/metrics, human story, partners/proof grid when factual, commitments/process, and final CTA;
- large whitespace and disciplined section pacing;
- sections that feel written and designed, not generated from a template;
- strong copy blocks with real hierarchy;
- no generic service-card stack as the main design;
- no default SaaS hero, no three-card feature grid, no repeated rounded cards as the page structure.

## Blank-canvas rule

The starting `app/page.tsx` and `app/globals.css` are disposable. Treat them as empty files. Build the page from the business data and design plan.

Do not preserve any starter layout. If the current output looks like a shell, delete the structure and rebuild it.

## Required page architecture

Codex must generate a complete single-page website with at least 9 meaningful sections:

1. premium navigation with anchors and CTA;
2. art-directed hero with headline, deck, CTA, and a distinctive visual system;
3. compact credibility/positioning strip;
4. belief, mission, or brand thesis section;
5. service/program architecture section that is not just cards;
6. proof, experience, metrics, expectations, or decision-support section using only factual data;
7. human/process/story section;
8. commitments, principles, or buyer decision-guide section;
9. contact/conversion section with real contact paths;
10. footer.

If data is thin, the design must still feel complete through editorial composition, interaction, layout, and clear writing. Do not invent fake claims.

## Required visual concept

Before implementation, choose one high-level art direction and commit to it across the whole page. Examples:

- `editorial-founder-letter`: large editorial typography, founder/story note, quiet proof, warm paper palette;
- `luxury-gallery-page`: image-led composition, restrained palette, immersive full-bleed moments;
- `technical-proof-dossier`: precise grids, compact proof modules, confident but restrained typography;
- `neighbourhood-field-guide`: local map/contact panel, practical service decision flow, warm documentary tone;
- `clinical-calm-system`: airy, low-noise, trust-first design with carefully controlled contrast.

The site fails if it looks like a generic website where only the business name changed.

## Typography and fonts

The generated site must use custom fonts through `next/font/google` unless the project cannot access the package. Pair a high-quality display font with a readable body font. Examples:

- `Cormorant_Garamond` + `Inter` for editorial/luxury;
- `DM_Serif_Display` + `Manrope` for premium local brands;
- `Playfair_Display` + `Source_Sans_3` for boutique/editorial;
- `Fraunces` + `Instrument_Sans` for warm modern brands;
- `Space_Grotesk` + `Inter` for technical/proof-led brands.

Do not use browser default fonts for the final site. Do not leave `Arial`, `Helvetica`, or raw `system-ui` as the main visual identity.

## Required implementation depth

The final implementation must feel like a real product page:

- `app/page.tsx` should contain a full page architecture, not a few blocks;
- use multiple React components or clearly separated component functions;
- use data helpers for phone/email/website CTA links;
- use real anchor navigation;
- use a mobile sticky CTA when contact data exists;
- include at least one useful interaction if it fits the data, such as FAQ/details disclosure, service tabs, contact drawer, expandable principles, or comparison toggle;
- include full responsive CSS with desktop/tablet/mobile behaviour;
- include polished hover/focus states and reduced-motion handling;
- include a real final CTA/contact experience and footer;
- no placeholder language;
- no generic cards as the dominant visual language.

## Layout requirements

Use at least four different section rhythms:

- oversized editorial hero;
- strip or ticker-like credibility band;
- two-column belief/story section;
- sticky narrative plus scrolling cards;
- asymmetric bento with no empty holes;
- full-bleed image or CSS-art panel;
- service architecture/tabs, not simple cards only;
- proof/expectations grid;
- high-contrast final CTA.

Use custom CSS variables, `clamp()`, responsive grids, intentional whitespace, and strong desktop/mobile composition.

## Anti-template instructions

Never ship these patterns as the dominant page structure:

- centred hero, three cards, final CTA;
- dark gradient SaaS hero unrelated to the business;
- all sections built from identical rounded cards;
- generic headings like `Our Services`, `Why Choose Us`, `About Us` unless redesigned and contextualized;
- placeholder copy such as `Services presented with clarity`;
- AI marketing phrases such as `top-notch`, `world-class`, `trusted partner`, `cutting-edge`;
- fake stats, fake testimonials, fake awards, fake certifications, fake years in business.

## Visual-director self-review

After the main build, review the page as if rejecting agency work. If it looks like a 5/10 template, rewrite it before finishing.

Ask:

- Does the first viewport look art-directed?
- Are there at least 9 meaningful sections?
- Does the page use custom fonts through `next/font`?
- Is there a real conversion/contact path?
- Does mobile feel intentionally designed?
- Could this page belong to any business if I changed only the name?

If the answer reveals shell/template quality, rebuild the page instead of patching details.

## Rejection criteria

The output fails if:

- it looks like a shell with text;
- it has fewer than 9 meaningful sections;
- it uses default fonts;
- it is mostly repeated service cards;
- it does not include custom `next/font` usage or an intentional font stack;
- it has no real mobile design;
- it has no final CTA/contact experience;
- it has no footer;
- it could be rebranded for any business by changing only the name.
