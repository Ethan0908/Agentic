from __future__ import annotations

"""Deprecated placeholder.

The project now uses SMTP for reviewed outbound messages. This file remains only
so old imports fail with a clear message if they are accidentally reintroduced.
"""


class GmailDraftClient:
    def __init__(self) -> None:
        raise RuntimeError("Gmail OAuth draft support has been removed. Use SMTP outreach mailer instead.")
