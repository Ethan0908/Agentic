# Raspberry Pi and Keys Setup

This guide sets up the Raspberry Pi 5, local PostgreSQL app, Google Places key, Gmail OAuth, GitHub token, Vercel token, and Codex OAuth/GitHub connection.

Never commit `.env`, OAuth token JSON files, API keys, or GitHub/Vercel tokens.

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

For generated lead repos, create a fine-grained GitHub personal access token.

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
GENERATED_REPO_PREFIX=lead-
```

Important: if you enable actual repository deletion later, keep `ALLOW_AUTO_DELETE_DEPLOYMENTS=false` until the dashboard has a manual approve button.

## 6. Vercel token

Create a Vercel Access Token from Vercel account settings.

Add to `.env`:

```env
VERCEL_TOKEN=your_vercel_token_here
VERCEL_PROJECT_PREFIX=lead-
```

If deploying under a team, also add:

```env
VERCEL_TEAM_ID=team_xxxxxxxxx
```

## 7. Gmail OAuth for drafts

Use OAuth, not a Gmail password.

In Google Cloud:

1. Enable Gmail API.
2. Configure OAuth consent screen.
3. Create an OAuth Client ID.
4. For easiest testing, choose Desktop app.
5. Download `credentials.json` locally.

You need the `gmail.compose` scope for creating drafts:

```text
https://www.googleapis.com/auth/gmail.compose
```

Generate a refresh token with a small local script on your laptop first, then copy the values into `.env` on the Pi.

Add to `.env`:

```env
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REFRESH_TOKEN=your_refresh_token
GMAIL_SENDER_EMAIL=your_email@gmail.com
```

Keep Gmail draft mode manual at first:

```env
ALLOW_AUTO_SEND_EMAILS=false
```

## 8. Codex OAuth / GitHub connection

Codex does not replace your backend. Use it to improve the repo and create PRs.

Setup:

1. Go to Codex in ChatGPT.
2. Connect your GitHub account.
3. Grant access to `Ethan0908/Agentic` and the generated template repo.
4. Use Codex to work on branches and PRs, not directly on production secrets.

Recommended Codex tasks:

```text
Wire the generated local site folder into GitHub repo creation from template.
```

```text
Add Vercel deployment creation and store vercel_project_id and vercel_url in PostgreSQL.
```

```text
Add Gmail reply tracking by thread ID and update outreach status.
```

Do not give Codex `.env` secrets. Keep secrets on the Pi only.

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
5. Create local draft record.
6. Only after this works, enable Gmail draft creation.
7. Only after this works, wire GitHub repo creation.
8. Only after this works, wire Vercel deployment.
9. Only after this works, add delete approval.

Do not enable auto-send or auto-delete until the approval workflow is fully tested.
