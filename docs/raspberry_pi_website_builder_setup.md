# Raspberry Pi Website Builder Setup

This guide explains where to run Python and npm for the Agentic website builder.

## Mental model

There are two different places commands run:

1. **Repo root** — run Python generator and validator commands here.
2. **Generated site folder** — run npm commands here to preview/build one generated website.

Do not run npm in the repo root unless the root later gets its own `package.json`.

## 1. Get the latest repo on the Pi

```bash
cd ~

# First time only:
git clone https://github.com/Ethan0908/Agentic.git

cd ~/Agentic
git pull origin main
```

If the repo already exists somewhere else, use that folder instead of `~/Agentic`.

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

## 3. Create a Python virtual environment

Run this from the repo root:

```bash
cd ~/Agentic
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

At the moment, the generator uses the Python standard library only. If a `requirements.txt` file is added later, run:

```bash
pip install -r requirements.txt
```

## 4. Create a lead JSON file

Run from the repo root:

```bash
cd ~/Agentic
mkdir -p leads
nano leads/example-plumber.json
```

Paste something like:

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

Save and exit.

## 5. Generate a website

Run Python from the repo root:

```bash
cd ~/Agentic
source .venv/bin/activate
python scripts/generate_site.py leads/example-plumber.json
```

This creates a folder like:

```bash
generated_sites/nyc-emergency-plumbing
```

The generated folder contains its own Next.js project.

## 6. Preview or build the generated website

Run npm inside the generated site folder:

```bash
cd ~/Agentic/generated_sites/nyc-emergency-plumbing
npm install
npm run dev
```

Then open the shown local URL from the Pi browser, or expose it on the network:

```bash
npm run dev -- --hostname 0.0.0.0
```

From another computer on the same network, open:

```text
http://<raspberry-pi-ip>:3000
```

To build the generated site:

```bash
cd ~/Agentic/generated_sites/nyc-emergency-plumbing
npm run build
```

## 7. Run the quality validator

Run this from the repo root:

```bash
cd ~/Agentic
source .venv/bin/activate
python scripts/validate_site_quality.py generated_sites/nyc-emergency-plumbing
```

## 8. Where Claude and Codex run

Claude and Codex are optional refinement steps.

Run the normal deterministic generator first:

```bash
python scripts/generate_site.py leads/example-plumber.json
```

If Claude Code is installed and authenticated on the Pi, run:

```bash
python scripts/generate_site.py leads/example-plumber.json --claude
```

If Codex is installed and authenticated on the Pi, run:

```bash
python scripts/generate_site.py leads/example-plumber.json --codex
```

Both options should be used only after the basic generator works.

## Command summary

Repo root:

```bash
cd ~/Agentic
source .venv/bin/activate
python scripts/generate_site.py leads/example-plumber.json
python scripts/validate_site_quality.py generated_sites/nyc-emergency-plumbing
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

Use `site-template` only when editing the master template. Use `generated_sites/<slug>` when previewing or deploying a specific generated website.
