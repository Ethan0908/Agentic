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

That means the running backend is checking for an old expected auth file path inside the container:

```text
/root/.codex/auth.json
```

The current repo-side generator does not check for that filename directly; it runs `codex exec` and lets the Codex CLI use its own local state.

### Check that the Pi user can run Codex

Run this on the Pi host, not inside the container:

```bash
cd /home/ethan/Agentic
whoami
codex --version
codex --help | sed -n '1,120p'
```

If the help output shows a login command, run it as the `ethan` user, not with `sudo`. For example:

```bash
codex login
```

Then test a tiny non-project command from the Pi host:

```bash
codex exec "Return only the word OK."
```

Do not copy Codex state files into GitHub, do not paste them into ChatGPT, and do not bake them into a Docker image.

### Repair Codex folder ownership if needed

If the Pi says `Permission denied` when the `ethan` user checks `/home/ethan/.codex`, the folder is probably owned by `root` or has bad mode bits. That often happens after running Codex with `sudo`.

Run this on the Pi host:

```bash
sudo ls -ld /home/ethan/.codex
sudo chown -R ethan:ethan /home/ethan/.codex
chmod 700 /home/ethan/.codex
find /home/ethan/.codex -type d -exec chmod 700 {} +
find /home/ethan/.codex -type f -exec chmod 600 {} +
ls -la /home/ethan/.codex
```

After this, run Codex as `ethan`, not with `sudo`.

### Mount Codex state into a backend container

`-v /home/ethan/.codex:/root/.codex` is not a standalone shell command. It is an argument to `docker run`.

If you use `docker run`, add this mount to the backend container command:

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
