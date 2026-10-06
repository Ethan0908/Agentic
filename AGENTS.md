# Agentic Operating Instructions

## Source of truth

GitHub is the source of truth for this project. The Raspberry Pi must run a direct checkout of this repository. Do not create Pi-only copies of generator logic, prompts, templates, frontend files, or deployment scripts.

## Runtime architecture

- `frontend/` is the local control panel. It runs on port `3000` and manages clients, statuses, queue state, and website inputs.
- The Raspberry Pi is a thin host and intermediary. It may store runtime state and local environment values, but it should not contain unique application code.
- Runtime client data belongs in `.runtime/` or the path set by `CLIENT_DATA_FILE`. This folder is ignored by git.
- Generated site folders may be created temporarily under `generated_sites/`, but durable output should be pushed to GitHub and deployed through Vercel.
- Keep private values out of the repository. Use `.env.local`, shell environment variables, or the Pi service manager environment.

## Website generation standards

Generated sites must feel specific to each business, not like one reused template.

Use these inputs when available:

- business name
- business type / vertical
- city and service area
- phone and email
- website URL
- supplied public business photos
- services
- reviews or testimonials
- offer / CTA / notes

Rules:

- Use supplied business photos when present.
- Do not add unrelated stock images.
- Do not invent licences, awards, review counts, years in business, warranties, guarantees, 24/7 availability, same-day service, or emergency availability.
- Keep copy concise and scannable.
- Make the hero communicate service, area, value, and CTA within five seconds.
- Keep the page static and Vercel-friendly.
- Preserve variant-driven rendering through `data/business.json`, `data/design.json`, and `data/sections.json`.

## Claude and Codex workflow

Before changing generated-site quality, inspect:

- `backend/app/services/site_generator.py`
- `backend/app/services/agentic_site_builder.py`
- `backend/app/prompts/website_generation_prompt.md`
- `backend/app/config/design_systems.json`
- `backend/app/config/section_registry.json`
- `site-template/app/page.tsx`
- `site-template/app/globals.css`
- `site-template/app/variants.css`
- `site-template/app/photos.css`

Use the checked-in Claude agents and skills instead of making one giant prompt. Keep agent outputs compact and implementation-focused.

## Validation commands

Run these after generator/template changes when dependencies are available:

```bash
python -m py_compile backend/app/services/site_generator.py backend/app/services/agentic_site_builder.py
python scripts/validate_site_quality.py generated_sites/<business-slug>

cd site-template
npm install
npm run build

cd ../frontend
npm install
npm run build
```

## Pi update rule

When the Pi is messy, fix the repository first, then update the Pi by pulling the repository and restarting services. Do not manually patch files on the Pi and leave GitHub behind.

# Autonomous Maintenance Agent
## Objective
Improve this repository through small, high-confidence changes.
Do not modify code merely because you are expected to make a
change. If no clearly beneficial improvement exists, leave the
repository unchanged.
## Scope
You may modify files only inside this repository. Never use sudo.
Never modify operating-system configuration. Never access or
modify files outside this repository unless explicitly required
by a project-owned test command.
## One task per run
Perform exactly one coherent improvement during each run. Good
tasks include: - fixing a real bug - improving error handling -
adding an important missing test - fixing a failing test -
removing clearly duplicated logic - correcting a type or lint
error - fixing a measurable performance issue - improving
deficient documentation Do not: - perform broad rewrites -
redesign the architecture - introduce speculative features - make
mass formatting changes - add unnecessary dependencies
## Priority
Prefer work in this order: 1. Correctness bugs 2. Security
problems 3. Failing tests 4. Reliability 5. Missing important
tests 6. Type or lint problems 7. Performance 8. Maintainability
9. Documentation
## Git
The external supervisor owns Git operations. Do not: - commit -
push - pull - fetch - merge - rebase - reset - switch branches -
force push - modify Git configuration You may inspect: - git
status - git diff - git log
## Protected files
Do not modify: - AGENTS.md - scripts/agent-validate.sh -
.github/workflows/ - .gitmodules - .env files - OAuth files -
credentials - private keys - certificates
## Dependencies
Do not add a dependency unless there is a strong technical
justification. Do not perform large dependency upgrades
autonomously.
## Validation
Run relevant existing tests after making a change. Never weaken
or remove a test merely to make broken code pass.
## Completion
Before finishing: 1. Review the complete diff. 2. Verify that
only one logical improvement was made. 3. Run relevant tests. 4.
Leave only the intended changes in the working tree. 5. Explain
what changed and what validation was performed.
If uncertain whether a change is beneficial or safe, do not make it.
