# Workflow

## 1. Discover businesses

The dashboard calls `POST /discover` with a keyword and location. The backend uses Google Places Text Search and stores only the operational lead record in PostgreSQL.

Recommended stored fields:

- `place_id`
- name
- phone
- website URL
- city/address
- status
- source metadata

## 2. Enrich emails

The backend crawls the business's own public website and checks common contact/about pages. It looks for visible emails and `mailto:` links.

Do not guess emails at scale in the first version. Store guessed patterns separately later if you decide to add that.

## 3. Validate emails

The MVP validates syntax and MX records. It intentionally avoids aggressive SMTP probing by default.

Validation statuses:

- `VALID`
- `RISKY`
- `CATCH_ALL`
- `INVALID`
- `UNKNOWN`

## 4. Generate websites

The backend copies `site-template`, writes a lead-specific `business.json`, and stores the generated local path. The next phase should push that generated site into a GitHub repo created from the template, then create a Vercel project.

## 5. Draft outreach

The backend prepares local email draft records. Gmail draft creation is supported through the service module once OAuth values are configured.

The first production version should keep sending manual.

## 6. Track responses

Use Gmail threads and a lead reference ID to update:

- `SENT`
- `WAITING_FOR_REPLY`
- `REPLIED_INTERESTED`
- `REPLIED_NOT_INTERESTED`
- `UNSUBSCRIBED`
- `NO_RESPONSE`

## 7. Cleanup

Cleanup should be two-step:

1. Worker/dashboard marks old inactive sites as `DELETE_PENDING`.
2. You manually approve GitHub/Vercel deletion.

Keep the database record even after deleting the repo/deployment so you do not pitch the same business repeatedly.
