from __future__ import annotations

import base64
from email.message import EmailMessage

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.core.config import get_settings


class GmailDraftClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        required = [
            self.settings.google_client_id,
            self.settings.google_client_secret,
            self.settings.google_refresh_token,
            self.settings.gmail_sender_email,
        ]
        if not all(required):
            raise RuntimeError("Gmail OAuth settings are not fully configured")

        credentials = Credentials(
            token=None,
            refresh_token=self.settings.google_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.settings.google_client_id,
            client_secret=self.settings.google_client_secret,
            scopes=["https://www.googleapis.com/auth/gmail.compose"],
        )
        self.service = build("gmail", "v1", credentials=credentials)

    def create_draft(self, to: str, subject: str, body: str) -> dict:
        message = EmailMessage()
        message.set_content(body)
        message["To"] = to
        message["From"] = self.settings.gmail_sender_email or ""
        message["Subject"] = subject

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {"message": {"raw": encoded_message}}
        return self.service.users().drafts().create(userId="me", body=create_message).execute()


def build_pitch_email(business_name: str, website_url: str | None, city: str | None = None) -> tuple[str, str]:
    subject = f"Quick website mockup for {business_name}"
    city_line = f" in {city}" if city else ""
    link_line = f"\n\nI made a quick website concept here:\n{website_url}" if website_url else ""
    body = (
        f"Hi,\n\n"
        f"I was looking at local businesses{city_line} and put together a cleaner website concept for {business_name}."
        f"{link_line}\n\n"
        "The idea is to make calls, directions, and basic service information easier to find on mobile. "
        "If this is useful, I can customise it further.\n\n"
        "Best,\n"
        "Denny\n\n"
        "To stop future emails from me, reply \"unsubscribe\"."
    )
    return subject, body
