# Raspberry Pi Deployment Notes

These notes keep the Pi simple: pull code from GitHub, run the frontend, and store only runtime state locally.

## First setup

```bash
cd /home/pi
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
export CLIENT_DATA_FILE=/home/pi/agentic-state/clients.json
```

That file is intentionally not committed to GitHub.

## Update flow

```bash
cd /home/pi/Agentic
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
User=pi
WorkingDirectory=/home/pi/Agentic/frontend
Environment=NODE_ENV=production
Environment=CLIENT_DATA_FILE=/home/pi/agentic-state/clients.json
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
