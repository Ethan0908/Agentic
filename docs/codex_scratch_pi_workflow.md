# Codex Scratch Website Workflow on Raspberry Pi

Use this workflow when you want Codex to build the generated website from scratch instead of copying or modifying `site-template`.

## Pull the branch

```bash
cd ~/Agentic
git fetch origin
git checkout industry-specific-sites
git pull origin industry-specific-sites
```

## Confirm Codex works

```bash
codex --version
```

If Codex needs local auth or API variables, put them in `.env` or `.env.local` in the repo root. These files are ignored by Git.

## Generate one sector-specific site from scratch

```bash
cd ~/Agentic
python3 -m backend.app.services.codex_scratch_generator leads/example-plumber.json
```

This command:

1. reads the lead JSON,
2. creates `data/business.json`, `data/site-plan.json`, and `data/creative-brief.json`,
3. tells Codex to create the Next.js app files from scratch,
4. runs npm install,
5. runs `npm run build`,
6. runs the quality validator.

## Preview the generated site

```bash
python3 -m backend.app.services.codex_scratch_generator leads/example-plumber.json --preview
```

The generated site preview uses port `3010` so it does not collide with the main app frontend on port `3000`.

Open the printed Network URL, for example:

```text
http://192.168.1.45:3010
```

## Batch-generate all leads

```bash
python3 -m backend.app.services.codex_scratch_generator leads
```

Do not use `--preview` with a folder because preview runs one site server.

## Why this is different from the old generator

The old path copied `site-template/`, so every company started from the same page skeleton.

The new Codex scratch path only prepares a company brief, then Codex writes the actual website files in the generated site folder.

## Sector rules

Industry packs live here:

```text
backend/app/config/industry_site_packs.json
```

For plumbing, the pack uses:

- square/industrial geometry,
- small radius values,
- practical trade copy framing,
- worksite/plumbing image URLs,
- dense service blocks,
- strong CTA contrast.

The validator now checks that generated pages use images and flags trade sites if they use overly rounded/pill styling.
