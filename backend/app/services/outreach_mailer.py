from __future__ import annotations

import json
import smtplib
from email.message import EmailMessage
from email.utils import formataddr

from app.core.config import get_settings
from app.models import Business


class SMTPNotConfiguredError(RuntimeError):
    pass


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


async def build_pitch_email_with_gpt(business: Business, website_url: str | None = None) -> tuple[str, str]:
    """Compatibility wrapper.

    The project intentionally avoids OpenAI API keys. Account-authenticated Codex
    work should happen through the Codex CLI/session on the Pi for website and
    template generation. Email copy stays deterministic unless a reviewed Codex
    workflow writes copy into the database later.
    """
    return build_pitch_email(business.name, website_url, business.city)


class SMTPMailer:
    def __init__(self) -> None:
        self.settings = get_settings()
        required = [
            self.settings.smtp_host,
            self.settings.smtp_port,
            self.settings.smtp_username,
            self.settings.smtp_password,
            self.settings.smtp_from_email,
        ]
        if not all(required):
            raise SMTPNotConfiguredError("SMTP settings are not fully configured")

    def send(self, to: str, subject: str, body: str) -> str | None:
        message = EmailMessage()
        message["From"] = formataddr((self.settings.smtp_from_name, self.settings.smtp_from_email or ""))
        message["To"] = to
        message["Subject"] = subject
        if self.settings.smtp_reply_to:
            message["Reply-To"] = self.settings.smtp_reply_to
        message.set_content(body)

        if self.settings.smtp_use_tls:
            with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=30) as server:
                server.starttls()
                server.login(self.settings.smtp_username or "", self.settings.smtp_password or "")
                response = server.send_message(message)
        else:
            with smtplib.SMTP_SSL(self.settings.smtp_host, self.settings.smtp_port, timeout=30) as server:
                server.login(self.settings.smtp_username or "", self.settings.smtp_password or "")
                response = server.send_message(message)

        # smtplib returns an empty dict on full success.
        return None if response == {} else json.dumps(response)
