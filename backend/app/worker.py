from __future__ import annotations

"""Simple worker entrypoint for Pi cron/systemd.

Run manually:
    python -m app.worker cleanup

For the first MVP, keep destructive cleanup manual in the dashboard. This worker only
marks stale generated sites as DELETE_PENDING unless ALLOW_AUTO_DELETE_DEPLOYMENTS
is explicitly enabled and deletion code is added.
"""

import argparse
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.config import get_settings
from app.db import SessionLocal
from app.models import Business, Event, LeadStatus, Website


def mark_cleanup_candidates() -> int:
    settings = get_settings()
    cutoff = datetime.now(UTC) - timedelta(days=settings.default_no_response_days)
    count = 0
    with SessionLocal() as db:
        websites = list(
            db.scalars(
                select(Website)
                .join(Business)
                .where(
                    Website.created_at < cutoff,
                    Website.keep.is_(False),
                    Website.delete_pending.is_(False),
                    Business.status.notin_([LeadStatus.CLIENT, LeadStatus.REPLIED_INTERESTED, LeadStatus.DELETED]),
                )
            ).all()
        )
        for website in websites:
            website.delete_pending = True
            if website.business:
                website.business.status = LeadStatus.DELETE_PENDING
            db.add(Event(business_id=website.business_id, event_type="worker.cleanup_candidate", details={"website_id": website.id}))
            count += 1
        db.commit()
    return count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["cleanup"])
    args = parser.parse_args()

    if args.command == "cleanup":
        count = mark_cleanup_candidates()
        print(f"Marked {count} cleanup candidates")


if __name__ == "__main__":
    main()
