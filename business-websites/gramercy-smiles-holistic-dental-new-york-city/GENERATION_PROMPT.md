# Custom Website Generation Prompt

This project is a blank starter, not a website template.

Use business.json as the source of truth.

Codex must decide:
- what kind of company this is
- what tone fits the company
- what sections belong on the page
- whether products, services, programs, inventory, menu items, or other offerings are relevant
- what design style fits the company
- what calls to action should appear

Minimum loose structure:
1. Intro section
2. Body or supporting sections
3. Products, services, or offerings only if relevant
4. Trust, process, details, benefits, or FAQs only if relevant
5. Contact or conversion section

Rules:
- Do not use a fixed template.
- Do not reuse any previous generated concept.
- Do not force any single industry.
- Do not hardcode industry-specific copy unless the company data supports it.
- Do not invent exact hours, prices, reviews, awards, certifications, staff names, or guarantees.
- Use safe wording when facts are missing.
- Build a polished, responsive, production-ready landing page.
- The site must feel custom to the exact company in business.json.

Required output:
- Replace the starter page with a complete custom website.
- Edit app/page.tsx.
- Edit app/globals.css.
- Edit app/layout.tsx metadata if useful.
- Create codex-output.json.
