# SMTP and Codex Setup

This replaces the earlier Gmail OAuth and OpenAI API-key plan.

## Email direction

Use SMTP from the Raspberry Pi for sending. Use Codex/ChatGPT account auth for coding and website generation, not API keys in `.env`.

The safer workflow is:

```text
Business lead
  -> template or reviewed Codex task creates email/site copy
  -> copy is saved in PostgreSQL as a local draft
  -> you review it
  -> a one-at-a-time SMTP action sends the reviewed message
  -> PostgreSQL tracks the status
```

Do not make the discovery pipeline automatically send to every lead. Keep sending explicit and review-based.

## SMTP environment variables

Add these to `.env`:

```env
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your_username
SMTP_PASSWORD=your_password_or_app_password
SMTP_FROM_EMAIL=you@example.com
SMTP_FROM_NAME=Denny
SMTP_USE_TLS=true
SMTP_REPLY_TO=
ALLOW_AUTO_SEND_EMAILS=false
```

Recommended providers:

- Testing only: Gmail SMTP with an app password, if your Google account supports app passwords.
- Better production setup: a dedicated domain email plus a real outbound SMTP provider such as Postmark, Amazon SES, Mailgun, Resend, or SendGrid.
- If you use Google Workspace for your domain, use Google Workspace SMTP relay instead of a personal Gmail inbox.

## No OpenAI API keys

Do not set `OPENAI_API_KEY`. The repo should not use OpenAI Platform billing for generation.

Use this instead:

```text
ChatGPT account login -> Codex CLI / Codex Cloud -> generated website/code changes
```

The app can still create deterministic local email drafts. Later, if you want account-authenticated Codex to improve an individual generated site, run Codex on that generated site folder and review the diff.

## GitHub and Vercel prefix decision

You removed the GitHub/Vercel prefix values. That is fine. The repo no longer needs `GENERATED_REPO_PREFIX` or `VERCEL_PROJECT_PREFIX` in `.env`.

Use names like:

```text
arbutus-dental-vancouver
kits-plumbing-vancouver
main-street-cafe-vancouver
```

instead of:

```text
lead-arbutus-dental-vancouver
```

## Codex / ChatGPT OAuth direction

There are two different things:

1. Codex as your account-authenticated coding/site agent.
2. The Pi backend that runs lead tracking, PostgreSQL, GitHub, Vercel, and SMTP.

Codex can sign in with ChatGPT and work on code. That is useful for improving templates, generating site variants, and opening PRs.

The Pi backend should not treat ChatGPT OAuth like a normal backend API key. Instead, install Codex CLI on the Pi, sign in with ChatGPT once, and use reviewed Codex tasks for website/template work.

## Codex CLI on the Pi

Install Codex CLI on the Pi:

```bash
curl -fsSL https://chatgpt.com/codex/install.sh | sh
```

For unattended install:

```bash
curl -fsSL https://chatgpt.com/codex/install.sh | CODEX_NON_INTERACTIVE=1 sh
```

Then sign in:

```bash
codex
```

On a headless Pi, use device login if browser login does not work:

```bash
codex login --device-auth
```

Treat `~/.codex/auth.json` like a password. Do not commit it or paste it into chat.

## Recommended Codex task shape

Use Codex for code and template work, not for every tiny lead.

Good Codex tasks:

```text
Improve the site-template design for dental clinics and make it read business.json cleanly.
```

```text
Create a second website template for restaurants and add template selection by business category.
```

```text
Open this generated site folder and customize copy/layout for the current business. Keep the business facts from business.json. Do not invent claims. Leave a clean diff for review.
```

Bad Codex task:

```text
For every scraped lead, open Codex and make a full custom website with no review.
```

That would be slow, hard to control, and more likely to break.

## Best workflow now

```text
Pi app discovers businesses
Pi app finds/validates public emails
Pi app generates structured business.json
Template creates the first website
Codex improves templates and selected special-case sites through ChatGPT login
GitHub stores generated sites
Vercel hosts generated sites
Pi app creates reviewed email copy
Pi sends reviewed messages through SMTP one at a time
PostgreSQL tracks everything
```
