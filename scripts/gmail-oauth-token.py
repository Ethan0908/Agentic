#!/usr/bin/env python3
"""Generate Gmail OAuth refresh-token values for .env.

Usage:
  1. In Google Cloud, enable Gmail API.
  2. Create an OAuth Client ID as a Desktop app.
  3. Download the JSON file as credentials.json.
  4. Run:
       python3 -m pip install google-auth-oauthlib
       python3 scripts/gmail-oauth-token.py /path/to/credentials.json
  5. Copy the printed GOOGLE_* values into .env on the Raspberry Pi.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/gmail-oauth-token.py /path/to/credentials.json", file=sys.stderr)
        raise SystemExit(2)

    credentials_path = Path(sys.argv[1])
    if not credentials_path.exists():
        print(f"File not found: {credentials_path}", file=sys.stderr)
        raise SystemExit(2)

    data = json.loads(credentials_path.read_text(encoding="utf-8"))
    client_config = data.get("installed") or data.get("web")
    if not client_config:
        print("credentials.json must contain an installed or web OAuth client", file=sys.stderr)
        raise SystemExit(2)

    flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent")

    print("Copy these into .env:")
    print(f"GOOGLE_CLIENT_ID={client_config.get('client_id', '')}")
    print(f"GOOGLE_CLIENT_SECRET={client_config.get('client_secret', '')}")
    print(f"GOOGLE_REFRESH_TOKEN={creds.refresh_token or ''}")
    print("GMAIL_SENDER_EMAIL=your_email@gmail.com")


if __name__ == "__main__":
    main()
