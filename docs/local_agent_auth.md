# Local Agent Auth

The website pipeline can run without Claude or Codex. Use the deterministic generator first.

Optional agent refinement uses local CLI tools:

```bash
python3 scripts/run_website_pipeline.py leads/example-plumber.json --claude
python3 scripts/run_website_pipeline.py leads/example-plumber.json --codex
```

## Environment files

The repo loads local environment files from:

```text
.env
.env.local
```

These files are for your Pi only and should not be committed.

Example:

```bash
AGENT_PROVIDER_TOKEN=replace-with-your-local-token
```

The pipeline forwards those variables to the Claude/Codex subprocesses. It does not hardcode or print secret values.

## Preview port

Generated-site preview defaults to port `3010` so it does not collide with the main app frontend on port `3000`.

```bash
python3 scripts/run_website_pipeline.py leads/example-plumber.json --preview
```

The script prints both:

```text
Local URL
Network URL
```

Open the Network URL from another computer on the same Wi-Fi.
