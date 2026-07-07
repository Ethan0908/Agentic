# ClassHour-Level Single-Page Website Contract

Use ClassHour-level quality as the benchmark, not as something to copy exactly.

Reference quality traits:

- complete editorial single-page website, not a shell;
- custom font pairing and clear typographic hierarchy;
- art-directed first viewport;
- nav, hero, credibility/authority strip, belief/mission section, proof/metrics, human story, partners/proof grid when factual, commitments/process, and final CTA;
- large whitespace and disciplined section pacing;
- sections that feel written and designed, not generated from a template;
- strong copy blocks with real hierarchy;
- no generic service-card stack as the main design.

## Required output

Codex must generate a complete single-page website with at least these sections when the business data supports them:

1. premium navigation with anchors and CTA;
2. art-directed hero with headline, deck, CTA, and visual system;
3. compact credibility/positioning strip;
4. belief, mission, or brand thesis section;
5. service/program architecture section;
6. proof, experience, metrics, or expectations section using only factual data;
7. human/process/story section;
8. commitments, principles, or decision-guide section;
9. final CTA/contact section;
10. footer.

If data is thin, the design must still feel complete through editorial composition, not fake claims.

## Typography and fonts

The generated site must use custom fonts, preferably through `next/font/google` unless the project cannot access the package. Pair a high-quality display font with a readable body font. Examples:

- `Cormorant_Garamond` + `Inter` for editorial/luxury;
- `DM_Serif_Display` + `Manrope` for premium local brands;
- `Playfair_Display` + `Source_Sans_3` for boutique/editorial;
- `Fraunces` + `Instrument_Sans` for warm modern brands;
- `Space_Grotesk` + `Inter` for technical/proof-led brands.

Do not use browser default fonts for the final site. Do not leave `Arial, Helvetica, sans-serif` as the main font stack.

## Blank-canvas rule

The starting `app/page.tsx` and `app/globals.css` are disposable. Treat them as empty files. Build the page from the business data and design plan.

## Required implementation depth

The final implementation must feel like a real product page:

- multiple React components or clearly separated component functions;
- data helpers for phone/email/website CTA links;
- real anchor navigation;
- mobile sticky CTA when contact data exists;
- at least one useful interaction if it fits the data, such as FAQ/details disclosure, service tabs, contact drawer, or expandable principles;
- full responsive CSS with desktop/tablet/mobile behaviour;
- polished focus states and reduced-motion handling;
- no placeholder language;
- no generic cards as the dominant visual language.

## Visual standard

The page should feel closer to a small premium design studio build than a generated local-business scaffold. Prefer:

- asymmetric editorial grids;
- full-width or full-bleed sections;
- measured dark/light contrast;
- custom CSS variables;
- textured/linework backgrounds using CSS only;
- meaningful image use;
- large headline scale;
- strong final CTA.

## Rejection criteria

The output fails if:

- it looks like a shell with text;
- it has fewer than 8 meaningful sections;
- it uses default fonts;
- it is mostly repeated service cards;
- it does not include custom `next/font` usage or an intentional font stack;
- it has no real mobile design;
- it has no final CTA/contact experience;
- it could be rebranded for any business by changing only the name.
