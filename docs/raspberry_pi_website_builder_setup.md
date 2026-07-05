# Raspberry Pi Website Builder Setup

This guide explains how to run the Agentic website builder on a Raspberry Pi.

## The important rule

Use the one-command pipeline for normal work:

```bash
cd ~/Agentic
python3 scripts/run_website_pipeline.py leads/example-plumber.json
```

That command automatically:

1. generates the website,
2. installs npm dependencies inside the generated site,
3. runs `npm run build`,
4. runs the Python quality validator.

You should not manually `cd` into every generated site unless you want to inspect or debug it.

## 1. Fix an old/stale local repo

If files such as `scripts/generate_site.py` or `scripts/run_website_pipeline.py` are missing, your Pi has not pulled the latest GitHub version.

Run:

```bash
cd ~/Agentic
git status
git fetch origin
git pull origin main
```

If the folder is disposable and you want the Pi to exactly match GitHub `main`, run this stronger reset:

```bash
cd ~/Agentic
git fetch origin
git reset --hard origin/main
git clean -fd
```

Warning: `git reset --hard` and `git clean -fd` remove uncommitted local changes and untracked files.

## 2. Install system tools

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip curl build-essential
```

Install Node.js 20 or newer. One common option is NodeSource:

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

node -v
npm -v
python3 --version
```

## 3. Python environment

The current generator uses the Python standard library. You can run it directly with `python3`.

Optional virtual environment:

```bash
cd ~/Agentic
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

If `.venv/bin/activate` is missing, it simply means the virtual environment was never created. Run the `python3 -m venv .venv` command first, or just use `python3` directly.

## 4. Create a lead JSON file

```bash
cd ~/Agentic
mkdir -p leads
nano leads/example-plumber.json
```

Paste:

```json
{
  "name": "NYC Emergency Plumbing",
  "business_type": "emergency plumbing",
  "city": "New York",
  "service_area": "Manhattan, Brooklyn, and Queens",
  "phone": "",
  "primary_cta": "Request emergency service",
  "services": [
    {"title": "Drain clearing", "description": "Clear blocked drains with a practical diagnosis before work starts."},
    {"title": "Leak repair", "description": "Find the source of the leak and explain the next step clearly."},
    {"title": "Sewer service", "description": "Understand the source of the blockage and the practical next step."}
  ]
}
```

## 5. Run the automatic pipeline

```bash
cd ~/Agentic
python3 scripts/run_website_pipeline.py leads/example-plumber.json
```

This creates a folder like:

```bash
generated_sites/nyc-emergency-plumbing
```

and automatically runs npm install/build and the quality validator.

## 6. Preview only when needed

To automatically generate, build, validate, and start a preview server:

```bash
cd ~/Agentic
python3 scripts/run_website_pipeline.py leads/example-plumber.json --preview
```

From another computer on the same network, open:

```text
http://<raspberry-pi-ip>:3000
```

The preview command keeps running until you stop it with `Ctrl+C`.

## 7. Optional Claude or Codex refinement

Only use these after the normal deterministic pipeline works.

```bash
python3 scripts/run_website_pipeline.py leads/example-plumber.json --claude
python3 scripts/run_website_pipeline.py leads/example-plumber.json --codex
```

## Old manual commands, for debugging only

Repo root:

```bash
cd ~/Agentic
python3 scripts/generate_site.py leads/example-plumber.json
python3 scripts/validate_site_quality.py generated_sites/nyc-emergency-plumbing
```

Generated site folder:

```bash
cd ~/Agentic/generated_sites/nyc-emergency-plumbing
npm install
npm run dev
npm run build
```

Template development folder:

```bash
cd ~/Agentic/site-template
npm install
npm run dev
npm run build
```

Use `site-template` only when editing the master template. Use `generated_sites/<slug>` only when debugging or deploying a specific generated website.
