# Browser Website Generator Frontend

This is the preferred testing path. Do not run the generator manually from the CLI unless debugging.

## Start the browser frontend on the Raspberry Pi

```bash
cd ~/Agentic
git fetch origin
git checkout industry-specific-sites
git pull origin industry-specific-sites
bash scripts/start_generator_frontend.sh
```

The server prints two URLs:

```text
Generator frontend local:   http://localhost:8090
Generator frontend network: http://<pi-ip>:8090
```

Open the Network URL from your laptop or another device on the same Wi-Fi.

## How it works

The frontend page lets you:

1. edit or paste lead JSON,
2. choose the Codex command, default `/usr/bin/codex`,
3. click **Generate with Codex**,
4. watch live logs,
5. open the generated site preview when the job completes.

Behind the scenes the browser calls:

```text
POST /api/generate
GET /api/jobs/<jobId>
```

The backend starts the real Codex scratch generator in the background. It does not copy `site-template`.

## Generated site preview

The control panel runs on port `8090`.

Generated website previews run on ports starting at `3100`, so they do not collide with the main app frontend or the control panel.

## Codex permissions

Use `/usr/bin/codex`, not the broken standalone symlink under `~/.local/bin/codex`.

If Codex cannot read `/home/ethan/.codex/config.toml`, run:

```bash
bash scripts/fix_codex_config_permissions.sh
```

Do not run Codex with `sudo`.
