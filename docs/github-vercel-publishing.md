# GitHub and Vercel Publishing

Codex is not the deployment engine. Codex helps improve code and templates. The app does the mechanical publishing work through the GitHub and Vercel APIs.

The intended flow is:

```text
Build site
  -> creates local generated site folder
GitHub
  -> creates/reuses a repo
  -> uploads generated site files
Vercel
  -> creates/reuses a project
  -> deploys the GitHub repo
Draft
  -> email uses the public Vercel URL
Send
  -> SMTP/Postfix sends the reviewed email
```

## Required `.env`

```env
GITHUB_TOKEN=github_pat_or_classic_token_here
GITHUB_OWNER=Ethan0908
GITHUB_TEMPLATE_REPO=business-site-template

VERCEL_TOKEN=vercel_token_here
VERCEL_TEAM_ID=
```

The GitHub template repo must exist and be marked as a template repository.

## Dashboard buttons

Use the dashboard buttons in this order:

1. Build site
2. GitHub
3. Vercel
4. Draft
5. Send

## API endpoints

Build local website:

```bash
curl -X POST http://localhost:8000/businesses/1/build-site
```

Publish latest generated website to GitHub:

```bash
curl -X POST http://localhost:8000/businesses/1/publish-latest-site-github
```

Deploy latest GitHub website to Vercel:

```bash
curl -X POST http://localhost:8000/businesses/1/deploy-latest-site-vercel
```

## What the GitHub step does

- Reads the latest generated local site folder.
- Creates or reuses a GitHub repo using the configured template repo.
- Uploads the generated text files into the repo using Git trees/commits.
- Stores `github_repo_name`, `github_repo_url`, and `deployment_status` in PostgreSQL.

## What the Vercel step does

- Reads the latest GitHub repo name from PostgreSQL.
- Looks up the GitHub repo ID.
- Creates or reuses a Vercel project.
- Starts a production deployment from the GitHub repo.
- Stores `vercel_project_id`, `vercel_url`, and `deployment_status` in PostgreSQL.

## Common Vercel issue

If Vercel returns an error about GitHub access, connect the GitHub account/repo owner to Vercel once in the Vercel dashboard. The Vercel API token alone may not be enough if the Vercel GitHub integration cannot see the repository.

## Codex role

Use Codex for:

- Improving `site-template`
- Adding category-specific templates
- Fixing code
- Creating PRs

Do not use Codex as the thing that creates every repo or clicks through Vercel. The app should do that through repeatable APIs.
