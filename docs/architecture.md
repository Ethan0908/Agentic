# Agentic Runtime Architecture

## Goal

Agentic generates high-quality local-business websites, stores client and queue state, and prepares outreach. Code should stay in GitHub. The Raspberry Pi should host the app and keep only local runtime state.

## Components

### GitHub

GitHub owns:

- frontend source code
- backend generator source code
- prompts
- Claude agents and skills
- site template
- docs
- validation scripts

Do not make permanent code edits directly on the Pi unless they are committed back to GitHub.

### Frontend

Path: `frontend/`

Purpose:

- client management
- lead inputs
- queue/status management
- supplied photo URLs
- generated-site status

Port:

- development: `3000`
- production: `3000`

Runtime data:

- default: `.runtime/clients.json`
- override: `CLIENT_DATA_FILE=/path/to/clients.json`

### Raspberry Pi

The Pi owns only runtime concerns:

- running the frontend
- saving local client state
- acting as the local intermediary for CLI tools
- temporary generated-site folders

It should not own unique prompts, generator files, templates, or frontend code.

### Website builder

Core files:

- `backend/app/services/site_generator.py`
- `backend/app/services/agentic_site_builder.py`
- `backend/app/prompts/website_generation_prompt.md`
- `backend/app/config/design_systems.json`
- `backend/app/config/section_registry.json`
- `site-template/`

Generated data files:

- `data/business.json`
- `data/design.json`
- `data/sections.json`
- `data/site-plan.json`

## Image-aware generation

The generator accepts public business images through these fields:

- `photos`
- `images`
- `photo_urls`
- `photoUrls`
- `image_urls`
- `imageUrls`
- `gallery`
- `business_photos`
- `businessPhotos`
- `website_images`
- `websiteImages`
- `scraped_images`
- `scrapedImages`
- `hero_image`
- `heroImage`
- `cover_image`
- `coverImage`

The normalised schema writes:

- `business.heroImage`
- `business.photos`

The template uses these fields for the hero image and photo ribbon. If no images are supplied, the page should stay premium through layout, typography, cards, colour, and copy. It should not add unrelated stock photos.

## Operating rule

When something breaks on the Pi, fix it in GitHub first. Then pull the repo on the Pi and restart the service.
