# Agentic Business Website Maker

A Raspberry Pi 5-friendly workflow for finding businesses, enriching public contact data, validating email addresses, generating small website previews, deploying them, preparing Gmail drafts, and tracking response/cleanup status.

This repo is intentionally built around **PostgreSQL** as the source of truth. Google Sheets can be added later as a reporting mirror, but the app should not rely on Sheets as the main database.

## What this starter includes

- FastAPI backend
- PostgreSQL database
- Alembic migrations
- Next.js controller dashboard
- Docker Compose for local/Raspberry Pi deployment
- Lead discovery service using Google Places
- Public website email finder
- Email validation service
- Website generation service using a reusable template
- GitHub repository client placeholder
- Vercel deployment client placeholder
- Gmail draft client placeholder
- Cleanup/status workflow tables

## System layout

```text
Laptop/iPad browser
        ↓
Next.js dashboard
        ↓
FastAPI API on Raspberry Pi 5
        ↓
PostgreSQL
        ↓
Google Places / website crawl / GitHub / Vercel / Gmail
```

## Quick start

1. Copy the environment template:

```bash
cp .env.example .env
```

2. Fill in the required keys in `.env`.

3. Start the stack:

```bash
docker compose up --build
```

4. Open:

```text
Dashboard: http://localhost:3000
API docs:  http://localhost:8000/docs
```

5. Run migrations:

```bash
docker compose exec backend alembic upgrade head
```

## Raspberry Pi notes

This is designed to run on a Raspberry Pi 5 using Docker. For easier access from your laptop or iPad, install Tailscale on the Pi and visit the Pi's Tailscale IP with port `3000`.

## Main statuses

```text
DISCOVERED
WEBSITE_FOUND
EMAIL_FOUND
EMAIL_VALIDATED
SITE_QUEUED
SITE_BUILT
SITE_DEPLOYED
DRAFT_CREATED
SENT
WAITING_FOR_REPLY
REPLIED_INTERESTED
REPLIED_NOT_INTERESTED
NO_RESPONSE
UNSUBSCRIBED
DELETE_PENDING
DELETED
CLIENT
ARCHIVED
```

## Safe workflow recommendation

Start with manual approval before sending any email or deleting any repository/deployment. The included system creates drafts and tracks cleanup candidates; it does not mass-send by default.

## Codex OAuth role

Use Codex through GitHub-connected OAuth for improving the master website template and making special one-off edits. The batch system should generate sites from a controlled template and structured `business.json`, not rely on Codex to fully improvise every lead.
