import enum
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class LeadStatus(str, enum.Enum):
    DISCOVERED = "DISCOVERED"
    WEBSITE_FOUND = "WEBSITE_FOUND"
    EMAIL_FOUND = "EMAIL_FOUND"
    EMAIL_VALIDATED = "EMAIL_VALIDATED"
    SITE_QUEUED = "SITE_QUEUED"
    SITE_BUILT = "SITE_BUILT"
    SITE_DEPLOYED = "SITE_DEPLOYED"
    DRAFT_CREATED = "DRAFT_CREATED"
    SENT = "SENT"
    WAITING_FOR_REPLY = "WAITING_FOR_REPLY"
    REPLIED_INTERESTED = "REPLIED_INTERESTED"
    REPLIED_NOT_INTERESTED = "REPLIED_NOT_INTERESTED"
    NO_RESPONSE = "NO_RESPONSE"
    UNSUBSCRIBED = "UNSUBSCRIBED"
    DELETE_PENDING = "DELETE_PENDING"
    DELETED = "DELETED"
    CLIENT = "CLIENT"
    ARCHIVED = "ARCHIVED"


class EmailValidationStatus(str, enum.Enum):
    UNKNOWN = "UNKNOWN"
    VALID = "VALID"
    RISKY = "RISKY"
    CATCH_ALL = "CATCH_ALL"
    INVALID = "INVALID"


def utc_now() -> datetime:
    return datetime.now(UTC)


class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    place_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(80), nullable=True)
    website_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    source: Mapped[str] = mapped_column(String(80), default="manual", nullable=False)
    status: Mapped[LeadStatus] = mapped_column(Enum(LeadStatus), default=LeadStatus.DISCOVERED, nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    contacts: Mapped[list["Contact"]] = relationship(back_populates="business", cascade="all, delete-orphan")
    websites: Mapped[list["Website"]] = relationship(back_populates="business", cascade="all, delete-orphan")
    emails: Mapped[list["OutreachEmail"]] = relationship(back_populates="business", cascade="all, delete-orphan")
    events: Mapped[list["Event"]] = relationship(back_populates="business", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("place_id", name="uq_businesses_place_id"),)


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(80), nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    validation_status: Mapped[EmailValidationStatus] = mapped_column(
        Enum(EmailValidationStatus), default=EmailValidationStatus.UNKNOWN, nullable=False, index=True
    )
    validation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    unsubscribed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    business: Mapped[Business] = relationship(back_populates="contacts")


class Website(Base):
    __tablename__ = "websites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    github_repo_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    github_repo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    vercel_project_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vercel_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    local_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    deployment_status: Mapped[str] = mapped_column(String(80), default="LOCAL_GENERATED", nullable=False)
    delete_pending: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    keep: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    business: Mapped[Business] = relationship(back_populates="websites")


class OutreachEmail(Base):
    __tablename__ = "outreach_emails"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    recipient_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    provider_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    thread_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(80), default="DRAFT_LOCAL", nullable=False, index=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    replied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    business: Mapped[Business] = relationship(back_populates="emails")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_id: Mapped[int | None] = mapped_column(ForeignKey("businesses.id", ondelete="SET NULL"), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    business: Mapped[Business | None] = relationship(back_populates="events")
