# SMTP and Codex Setup

This replaces the earlier Gmail OAuth plan.

## Email direction

Use SMTP from the Raspberry Pi instead of Gmail OAuth.

The safer workflow is:

```text
Business lead
  -> GPT/template generates email copy
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

- For testing: Gmail SMTP with an app password, if your Google account supports app passwords.
- For production: a real transactional or outbound SMTP provider such as Postmark, Mailgun, Amazon SES, Resend, or SendGrid.

## Optional GPT email copy

If `OPENAI_API_KEY` is set, the backend can ask the OpenAI API to generate the email copy. If it is empty, the backend uses the deterministic built-in template.

```env
OPENAI_API_KEY=
OPENAI_EMAIL_MODEL=gpt-5.5
```

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

1. Codex as your coding assistant.
2. The Pi backend that runs your lead/site/email workflow.

Codex can sign in with ChatGPT and work on code. That is useful for improving templates, generating site variants, and opening PRs.

The Pi backend should not depend on ChatGPT OAuth as if it were a normal backend API key. For unattended backend automation, prefer one of these:

- Codex CLI logged in on the Pi, used for trusted local coding tasks.
- OpenAI API key for normal programmatic generation.
- Manual Codex Cloud tasks through ChatGPT/GitHub for larger code changes.

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
Wire the generated local site folder into a GitHub repo and Vercel deployment.
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
Template creates the website
Codex improves templates and special cases
GitHub stores generated sites
Vercel hosts generated sites
Pi app generates reviewed email copy
Pi sends reviewed messages through SMTP one at a time
PostgreSQL tracks everything
```
