from __future__ import annotations

import dns.resolver
from email_validator import EmailNotValidError, validate_email

from app.models import EmailValidationStatus


class ValidationResult(dict):
    status: EmailValidationStatus
    notes: str


def validate_public_email(email: str) -> dict:
    """Validate email without sending mail.

    This intentionally avoids aggressive SMTP probing by default. SMTP checks are
    noisy, unreliable with catch-all domains, and can make the sender look bad.
    """
    try:
        result = validate_email(email, check_deliverability=False)
        normalised = result.normalized
    except EmailNotValidError as exc:
        return {"email": email, "status": EmailValidationStatus.INVALID, "notes": str(exc)}

    domain = normalised.split("@", 1)[1]
    try:
        answers = dns.resolver.resolve(domain, "MX", lifetime=5)
        mx_records = [str(answer.exchange).rstrip(".") for answer in answers]
    except Exception as exc:  # DNS exceptions vary by resolver/platform.
        return {
            "email": normalised,
            "status": EmailValidationStatus.RISKY,
            "notes": f"Syntax valid, but MX lookup failed: {exc}",
        }

    if not mx_records:
        return {"email": normalised, "status": EmailValidationStatus.INVALID, "notes": "No MX records found"}

    return {
        "email": normalised,
        "status": EmailValidationStatus.VALID,
        "notes": f"Syntax valid; MX records found: {', '.join(mx_records[:3])}",
    }
