# Website Generator Pipeline

The dashboard's **Build + deploy** button is now meant to run the full website pipeline:

```text
lead in PostgreSQL
  -> copy site-template to a generated website folder
  -> run Codex CLI against that folder using ChatGPT account auth
  -> create/reuse one GitHub repo for that business website
  -> upload the generated site into that repo
  -> also archive the same files under business-websites/<slug>/ in this repo
  -> create/reuse a Vercel project
  -> create a production deployment
  -> save GitHub/Vercel URLs back to PostgreSQL
```

## Why Codex is in the backend container

The backend runs inside Docker. The dashboard button talks to the backend, not directly to the Pi host shell. Therefore the backend container needs:

1. Codex CLI installed inside the container.
2. Your Pi user's `~/.codex` mounted into `/root/.codex` in the backend container.

The Compose file does this:

```yaml
volumes:
  - ${HOME}/.codex:/root/.codex
```

Do not run Docker Compose with `sudo`, or `${HOME}` may point to `/root` instead of `/home/ethan`.

## Required `.env`

```env
CODEX_ENABLED=true
CODEX_WORKDIR=/app/.generated-sites
CODEX_DEFAULT_MODEL=
CODEX_TIMEOUT_SECONDS=900

GITHUB_TOKEN=your_github_token
GITHUB_OWNER=Ethan0908
GITHUB_TEMPLATE_REPO=
GITHUB_GENERATED_REPO_PRIVATE=true
GITHUB_ARCHIVE_REPO=Agentic
GITHUB_ARCHIVE_BRANCH=starter-postgres-website-maker
GITHUB_ARCHIVE_PATH=business-websites

VERCEL_TOKEN=your_vercel_token
VERCEL_TEAM_ID=
```

Leave `GITHUB_TEMPLATE_REPO` empty unless you specifically want to create from a GitHub template repo. The backend now creates a generated repo directly and uploads the generated site files.

## Codex setup on the Pi

Run on the Pi host, not inside Docker:

```bash
codex login --device-auth
```

Check:

```bash
ls -l ~/.codex/auth.json
```

Then rebuild the backend so the container has Codex installed:

```bash
docker compose up --build -d backend frontend
```

Check Codex inside the backend container:

```bash
docker compose exec backend codex --version
docker compose exec backend ls -l /root/.codex/auth.json
```

Run a simple non-editing test:

```bash
docker compose exec backend codex exec "say OK and nothing else"
```

## GitHub token permissions

Use a fine-grained token for `Ethan0908` with:

- Contents: write
- Metadata: read
- Administration: write, only if you want the backend to create repos

The generated business website will get its own repo, such as:

```text
Ethan0908/arbutus-dental-vancouver
```

The same files are also archived in:

```text
Ethan0908/Agentic/business-websites/arbutus-dental-vancouver/
```

## Vercel setup

The Vercel token must belong to the account/team that has the GitHub integration installed and can see the generated GitHub repo.

If Vercel cannot access the GitHub repo, the API call will fail even if `VERCEL_TOKEN` is correct. Fix that in Vercel by installing or updating the GitHub integration for the generated repo owner.

## Run the full pipeline manually

Replace `BUSINESS_ID`:

```bash
curl -X POST http://localhost:8000/businesses/BUSINESS_ID/build-publish-deploy-site
```

Or from another machine over Tailscale:

```bash
curl -X POST http://TAILSCALE_IP:8000/businesses/BUSINESS_ID/build-publish-deploy-site
```

## Debug order

1. `docker compose logs -f backend`
2. Confirm Codex auth is visible inside the container.
3. Confirm GitHub token can create repos.
4. Confirm Vercel token and GitHub integration can deploy that repo.
5. Confirm `business-websites/<slug>/` appears in the configured archive repo/branch.

## Expected dashboard result

Click **Build + deploy**. It may take several minutes because Codex runs first. On success, the dashboard message should show the Vercel URL and the lead status should become `SITE_DEPLOYED`.
