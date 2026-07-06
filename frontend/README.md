# Agentic Control Panel

This is the local client-management frontend for the Raspberry Pi.

## Commands

```bash
npm install
npm run dev
npm run build
npm run start
```

Both `dev` and `start` bind to `0.0.0.0:3000`.

## Data storage

The app stores runtime client data in JSON.

Default path from this folder:

```text
../.runtime/clients.json
```

Override with:

```bash
CLIENT_DATA_FILE=/path/to/clients.json npm run start
```

This data file is not committed to GitHub.

## Current features

- Add clients.
- Save business type, city, service area, phone, email, website, notes, and public photo URLs.
- Track statuses: lead, queued, generating, generated, emailed, error.
- Delete clients.

## Next integration step

Wire the queue buttons to the backend generation worker so `queued` clients become generated sites automatically.
