from __future__ import annotations

import json
import smtplib
from email.message import EmailMessage
from email.utils import formataddr

import httpx

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
    """Generate a concise outreach email with the OpenAI API when configured.

    Falls back to the deterministic template if OPENAI_API_KEY is missing or the
    API response cannot be parsed. This keeps the Pi usable without API access.
    """
    settings = get_settings()
    if not settings.openai_api_key:
        return build_pitch_email(business.name, website_url, business.city)

    prompt = {
        "business": {
            "name": business.name,
            "city": business.city,
            "category": business.category,
            "phone": business.phone,
            "website_url": business.website_url,
            "address": business.address,
        },
        "preview_website_url": website_url,
        "requirements": [
            "Write a short cold outreach email.",
            "Mention the preview website link if provided.",
            "Do not overpromise results.",
            "Keep it under 140 words.",
            "Include an unsubscribe sentence.",
            "Return JSON only with keys subject and body.",
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(
                "https://api.openai.com/v1/responses",
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.openai_email_model,
                    "input": [
                        {
                            "role": "system",
                            "content": "You write compliant, concise B2B outreach emails for website preview offers.",
                        },
                        {"role": "user", "content": json.dumps(prompt)},
                    ],
                    "text": {"format": {"type": "json_object"}},
                },
            )
            response.raise_for_status()
            data = response.json()
    except Exception:
        return build_pitch_email(business.name, website_url, business.city)

    output_text = data.get("output_text")
    if not output_text:
        # Robust fallback for SDK-style response payloads.
        output_parts = data.get("output") or []
        chunks: list[str] = []
        for item in output_parts:
            for content in item.get("content", []) if isinstance(item, dict) else []:
                text = content.get("text") if isinstance(content, dict) else None
                if text:
                    chunks.append(text)
        output_text = "".join(chunks)

    try:
        parsed = json.loads(output_text or "{}")
        subject = str(parsed.get("subject") or f"Quick website mockup for {business.name}").strip()
        body = str(parsed.get("body") or "").strip()
        if subject and body:
            return subject[:255], body
    except Exception:
        pass

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
