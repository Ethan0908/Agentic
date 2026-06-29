from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

lead_status = sa.Enum(
    "DISCOVERED",
    "WEBSITE_FOUND",
    "EMAIL_FOUND",
    "EMAIL_VALIDATED",
    "SITE_QUEUED",
    "SITE_BUILT",
    "SITE_DEPLOYED",
    "DRAFT_CREATED",
    "SENT",
    "WAITING_FOR_REPLY",
    "REPLIED_INTERESTED",
    "REPLIED_NOT_INTERESTED",
    "NO_RESPONSE",
    "UNSUBSCRIBED",
    "DELETE_PENDING",
    "DELETED",
    "CLIENT",
    "ARCHIVED",
    name="leadstatus",
)

email_validation_status = sa.Enum(
    "UNKNOWN",
    "VALID",
    "RISKY",
    "CATCH_ALL",
    "INVALID",
    name="emailvalidationstatus",
)


def upgrade() -> None:
    bind = op.get_bind()
    lead_status.create(bind, checkfirst=True)
    email_validation_status.create(bind, checkfirst=True)

    op.create_table(
        "businesses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("place_id", sa.String(length=255), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=80), nullable=True),
        sa.Column("website_url", sa.Text(), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("source", sa.String(length=80), nullable=False, server_default="manual"),
        sa.Column("status", lead_status, nullable=False, server_default="DISCOVERED"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("place_id", name="uq_businesses_place_id"),
    )
    op.create_index("ix_businesses_place_id", "businesses", ["place_id"])
    op.create_index("ix_businesses_city", "businesses", ["city"])
    op.create_index("ix_businesses_status", "businesses", ["status"])

    op.create_table(
        "contacts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("phone", sa.String(length=80), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("validation_status", email_validation_status, nullable=False, server_default="UNKNOWN"),
        sa.Column("validation_notes", sa.Text(), nullable=True),
        sa.Column("unsubscribed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_contacts_business_id", "contacts", ["business_id"])
    op.create_index("ix_contacts_email", "contacts", ["email"])
    op.create_index("ix_contacts_validation_status", "contacts", ["validation_status"])

    op.create_table(
        "websites",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("github_repo_name", sa.String(length=255), nullable=True),
        sa.Column("github_repo_url", sa.Text(), nullable=True),
        sa.Column("vercel_project_id", sa.String(length=255), nullable=True),
        sa.Column("vercel_url", sa.Text(), nullable=True),
        sa.Column("local_path", sa.Text(), nullable=True),
        sa.Column("deployment_status", sa.String(length=80), nullable=False, server_default="LOCAL_GENERATED"),
        sa.Column("delete_pending", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("keep", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_websites_business_id", "websites", ["business_id"])

    op.create_table(
        "outreach_emails",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recipient_email", sa.String(length=320), nullable=True),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("gmail_draft_id", sa.String(length=255), nullable=True),
        sa.Column("gmail_thread_id", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=80), nullable=False, server_default="DRAFT_LOCAL"),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_outreach_emails_business_id", "outreach_emails", ["business_id"])
    op.create_index("ix_outreach_emails_status", "outreach_emails", ["status"])

    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("businesses.id", ondelete="SET NULL"), nullable=True),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_events_business_id", "events", ["business_id"])
    op.create_index("ix_events_event_type", "events", ["event_type"])


def downgrade() -> None:
    op.drop_index("ix_events_event_type", table_name="events")
    op.drop_index("ix_events_business_id", table_name="events")
    op.drop_table("events")
    op.drop_index("ix_outreach_emails_status", table_name="outreach_emails")
    op.drop_index("ix_outreach_emails_business_id", table_name="outreach_emails")
    op.drop_table("outreach_emails")
    op.drop_index("ix_websites_business_id", table_name="websites")
    op.drop_table("websites")
    op.drop_index("ix_contacts_validation_status", table_name="contacts")
    op.drop_index("ix_contacts_email", table_name="contacts")
    op.drop_index("ix_contacts_business_id", table_name="contacts")
    op.drop_table("contacts")
    op.drop_index("ix_businesses_status", table_name="businesses")
    op.drop_index("ix_businesses_city", table_name="businesses")
    op.drop_index("ix_businesses_place_id", table_name="businesses")
    op.drop_table("businesses")

    bind = op.get_bind()
    email_validation_status.drop(bind, checkfirst=True)
    lead_status.drop(bind, checkfirst=True)
