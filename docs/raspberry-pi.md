# Raspberry Pi Deployment Notes

These notes keep the Pi simple: pull code from GitHub, run the frontend, and store only runtime state locally.

The examples below use `/home/ethan` because the current Pi prompt shows `ethan@rpi5`. If your Linux user is different, replace `ethan` with that username.

## First setup

```bash
cd /home/ethan
git clone https://github.com/Ethan0908/Agentic.git
cd Agentic/frontend
npm install
npm run build
npm run start
```

The frontend listens on port `3000`.

## Runtime client data

By default, the frontend stores clients at:

```text
Agentic/.runtime/clients.json
```

For a more durable state folder, set:

```bash
mkdir -p /home/ethan/agentic-state
export CLIENT_DATA_FILE=/home/ethan/agentic-state/clients.json
```

That file is intentionally not committed to GitHub.

## Codex auth on the Pi

If site generation runs Codex inside a backend container, the container must be able to read the same Codex auth folder used by the Pi user.

The common failure looks like this:

```text
Codex auth not found at /root/.codex/auth.json. Mount the Pi user's ~/.codex into the backend container.
```

That means Codex is authenticated for the host user, usually:

```text
/home/ethan/.codex/auth.json
```

but the backend process is running inside a container as `root`, so it looks for:

```text
/root/.codex/auth.json
```

### Check that the Pi user is logged in to Codex

Run this on the Pi host, not inside the container:

```bash
ls -la /home/ethan/.codex
codex --version
```

If there is no `/home/ethan/.codex/auth.json`, log in to Codex from the Pi user account first.

Do not copy `auth.json` into GitHub, do not paste it into ChatGPT, and do not bake it into a Docker image.

### Mount Codex auth into a backend container

If you use `docker run`, add this mount to the backend container:

```bash
-v /home/ethan/.codex:/root/.codex
```

A full example looks like:

```bash
docker run --rm \
  -v /home/ethan/Agentic:/app \
  -v /home/ethan/.codex:/root/.codex \
  -w /app \
  agentic-backend-image \
  python3 -m backend.app.services.site_generator
```

If you use Compose, add this to the backend service:

```yaml
services:
  backend:
    volumes:
      - /home/ethan/Agentic:/app
      - /home/ethan/.codex:/root/.codex
```

Then restart the backend container.

## Update flow

```bash
cd /home/ethan/Agentic
git pull
cd frontend
npm install
npm run build
# restart your service or terminal process
```

## Example service file

Create a system service only after the app builds normally in the terminal.

```ini
[Unit]
Description=Agentic Frontend
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=ethan
WorkingDirectory=/home/ethan/Agentic/frontend
Environment=NODE_ENV=production
Environment=CLIENT_DATA_FILE=/home/ethan/agentic-state/clients.json
ExecStart=/usr/bin/npm run start
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable agentic-frontend
sudo systemctl restart agentic-frontend
sudo systemctl status agentic-frontend
```

## Rule

Do not fix app code directly on the Pi and leave it there. Make the change in GitHub, pull it on the Pi, then restart the service.
