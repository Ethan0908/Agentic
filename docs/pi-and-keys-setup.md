# Raspberry Pi and Keys Setup

This guide sets up the Raspberry Pi 5, local PostgreSQL app, Google Places key, SMTP email sending, GitHub token, Vercel token, and Codex/ChatGPT setup.

Important update: Gmail OAuth has been replaced by SMTP. For the current email and Codex plan, read `docs/smtp-and-codex-setup.md` first.

Never commit `.env`, OAuth token files, API keys, GitHub tokens, Vercel tokens, SMTP passwords, or Codex auth files.

## 1. Prepare the Raspberry Pi

Recommended OS:

- Raspberry Pi OS Lite 64-bit
- SSH enabled
- Ethernet if possible
- Hostname: `crm-pi` or `agentic-pi`

After first SSH login:

```bash
sudo apt-get update
sudo apt-get upgrade -y
sudo reboot
```

Then run the setup script:

```bash
git clone https://github.com/Ethan0908/Agentic.git
cd Agentic
git checkout starter-postgres-website-maker
bash scripts/pi-install.sh
```

Log out and back in so Docker group permissions apply.

## 2. Enable private access with Tailscale

Run:

```bash
sudo tailscale up
tailscale ip -4
```

Use the returned Tailscale IP from your laptop or iPad:

```text
http://TAILSCALE_IP:3000
```

Do not use public port forwarding for this project at the start.

## 3. Configure `.env`

```bash
cp .env.example .env
nano .env
```

Minimum local test values:

```env
POSTGRES_USER=agentic
POSTGRES_PASSWORD=change_this_password
POSTGRES_DB=agentic
DATABASE_URL=postgresql+psycopg://agentic:change_this_password@postgres:5432/agentic
API_BASE_URL=http://localhost:8000
PUBLIC_APP_URL=http://localhost:3000
ALLOW_AUTO_SEND_EMAILS=false
ALLOW_AUTO_DELETE_DEPLOYMENTS=false
```

Start the app:

```bash
docker compose up --build -d
docker compose exec backend alembic upgrade head
```

Check:

```bash
docker compose ps
docker compose logs -f backend
```

## 4. Google Places API key

Create a Google Cloud project, enable Places API (New), then create an API key.

Recommended restriction:

- API restriction: Places API only
- Application restriction: IP addresses if your Pi has a stable public outbound IP; otherwise leave unrestricted during testing and rotate/restrict later

Add to `.env`:

```env
GOOGLE_PLACES_API_KEY=your_key_here
```

Restart backend:

```bash
docker compose restart backend
```

Test in dashboard with keyword + city.

## 5. GitHub token

For generated business repos, create a fine-grained GitHub personal access token.

Recommended permissions:

- Resource owner: `Ethan0908`
- Repository access: all repositories under the account, or selected repos if you later move generated repos under a dedicated owner/org
- Repository permissions:
  - Administration: write
  - Contents: write
  - Metadata: read

Add to `.env`:

```env
GITHUB_TOKEN=github_pat_or_classic_token_here
GITHUB_OWNER=Ethan0908
GITHUB_TEMPLATE_REPO=business-site-template
```

Important: if you enable actual repository deletion later, keep `ALLOW_AUTO_DELETE_DEPLOYMENTS=false` until the dashboard has a manual approve button.

## 6. Vercel token

Create a Vercel Access Token from Vercel account settings.

Add to `.env`:

```env
VERCEL_TOKEN=your_vercel_token_here
```

If deploying under a team, also add:

```env
VERCEL_TEAM_ID=team_xxxxxxxxx
```

## 7. SMTP email sending

Use SMTP instead of Gmail OAuth.

Add to `.env`:

```env
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your_username
SMTP_PASSWORD=your_password_or_app_password
SMTP_FROM_EMAIL=you@example.com
SMTP_FROM_NAME=Denny
SMTP_USE_TLS=true
SMTP_REPLY_TO=
```

Keep sending review-based:

```env
ALLOW_AUTO_SEND_EMAILS=false
```

## 8. Codex / ChatGPT setup

Codex can sign in with ChatGPT and work on the repo, but the Pi app should not treat ChatGPT OAuth like a generic backend API key.

Install Codex CLI on the Pi:

```bash
curl -fsSL https://chatgpt.com/codex/install.sh | sh
```

On a headless Pi, use device login if needed:

```bash
codex login --device-auth
```

Treat `~/.codex/auth.json` like a password.

## 9. Run the app on the Pi

```bash
cd ~/Agentic
git pull
git checkout starter-postgres-website-maker
cp .env.example .env
nano .env
bash scripts/bootstrap.sh
```

Dashboard:

```text
http://TAILSCALE_IP:3000
```

API docs:

```text
http://TAILSCALE_IP:8000/docs
```

## 10. Backup PostgreSQL

Create a backup folder:

```bash
mkdir -p ~/agentic-backups
```

Manual backup:

```bash
docker compose exec -T postgres pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > ~/agentic-backups/agentic-$(date +%F).sql
```

Add cron later after the app is stable.

## 11. Safe first test order

1. Add one manual business in the dashboard.
2. Run email enrichment on that one business.
3. Validate that email.
4. Build local site.
5. Create local email copy.
6. Review the copy.
7. Test SMTP with your own address first.
8. Wire GitHub repo creation.
9. Wire Vercel deployment.
10. Add manual delete approval.

Do not enable auto-send or auto-delete until the approval workflow is fully tested.
