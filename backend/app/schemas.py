from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models import EmailValidationStatus, LeadStatus


class BusinessCreate(BaseModel):
    name: str
    city: str | None = None
    category: str | None = None
    phone: str | None = None
    website_url: str | None = None
    address: str | None = None
    notes: str | None = None
    contact_email: str | None = None


class DiscoverRequest(BaseModel):
    keyword: str = Field(..., min_length=2)
    location: str = Field(..., min_length=2)
    radius_m: int = Field(5000, ge=100, le=50000)
    max_results: int = Field(20, ge=1, le=100)


class BusinessOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    place_id: str | None
    name: str
    category: str | None
    phone: str | None
    website_url: str | None
    address: str | None
    city: str | None
    source: str
    status: LeadStatus
    notes: str | None
    latest_github_repo_name: str | None = None
    latest_github_repo_url: str | None = None
    latest_vercel_url: str | None = None
    latest_deployment_status: str | None = None
    created_at: datetime
    updated_at: datetime


class ContactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    business_id: int
    email: str | None
    phone: str | None
    source_url: str | None
    confidence: int
    validation_status: EmailValidationStatus
    validation_notes: str | None
    unsubscribed: bool
    created_at: datetime
    updated_at: datetime


class WebsiteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    business_id: int
    github_repo_name: str | None
    github_repo_url: str | None
    vercel_project_id: str | None
    vercel_url: str | None
    local_path: str | None
    deployment_status: str
    delete_pending: bool
    keep: bool
    created_at: datetime
    deleted_at: datetime | None


class OutreachEmailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    business_id: int
    recipient_email: str | None
    subject: str
    body: str
    gmail_draft_id: str | None
    gmail_thread_id: str | None
    status: str
    sent_at: datetime | None
    replied_at: datetime | None
    created_at: datetime
    updated_at: datetime


class StatusUpdate(BaseModel):
    status: LeadStatus
    notes: str | None = None


class DraftRequest(BaseModel):
    recipient_email: str | None = None
    website_url: HttpUrl | None = None
    use_gpt: bool = True


class CleanupRequest(BaseModel):
    older_than_days: int = Field(30, ge=1, le=365)
    mark_only: bool = True


class MessageOut(BaseModel):
    message: str
