from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.db import get_db
from app.models import Business, Contact, EmailValidationStatus, Event, LeadStatus, OutreachEmail, Website
from app.schemas import (
    BusinessCreate,
    BusinessOut,
    CleanupRequest,
    ContactOut,
    DiscoverRequest,
    DraftRequest,
    MessageOut,
    OutreachEmailOut,
    StatusUpdate,
    WebsiteOut,
)
from app.services.email_finder import find_public_emails
from app.services.email_validator import validate_public_email
from app.services.gmail_drafts import GmailDraftClient, build_pitch_email
from app.services.places import GooglePlacesClient, PlacesNotConfiguredError, normalise_place
from app.services.site_generator import generate_local_site

settings = get_settings()

app = FastAPI(title="Agentic Business Website Maker", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_business_or_404(db: Session, business_id: int) -> Business:
    business = db.scalar(
        select(Business)
        .where(Business.id == business_id)
        .options(selectinload(Business.contacts), selectinload(Business.websites), selectinload(Business.emails))
    )
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    return business


def log_event(db: Session, business_id: int | None, event_type: str, details: dict | None = None) -> None:
    db.add(Event(business_id=business_id, event_type=event_type, details=details or {}))


@app.get("/health")
def health() -> dict:
    return {"ok": True, "environment": settings.app_env}


@app.get("/businesses", response_model=list[BusinessOut])
def list_businesses(status: LeadStatus | None = None, db: Session = Depends(get_db)) -> list[Business]:
    stmt = select(Business).order_by(Business.created_at.desc()).limit(200)
    if status:
        stmt = select(Business).where(Business.status == status).order_by(Business.created_at.desc()).limit(200)
    return list(db.scalars(stmt).all())


@app.post("/businesses", response_model=BusinessOut)
def create_business(payload: BusinessCreate, db: Session = Depends(get_db)) -> Business:
    business = Business(**payload.model_dump(), source="manual", status=LeadStatus.DISCOVERED)
    db.add(business)
    db.flush()
    log_event(db, business.id, "business.created", payload.model_dump())
    db.commit()
    db.refresh(business)
    return business


@app.patch("/businesses/{business_id}/status", response_model=BusinessOut)
def update_business_status(business_id: int, payload: StatusUpdate, db: Session = Depends(get_db)) -> Business:
    business = get_business_or_404(db, business_id)
    business.status = payload.status
    if payload.notes:
        business.notes = payload.notes
    log_event(db, business.id, "business.status_updated", payload.model_dump(mode="json"))
    db.commit()
    db.refresh(business)
    return business


@app.post("/discover", response_model=list[BusinessOut])
async def discover_businesses(payload: DiscoverRequest, db: Session = Depends(get_db)) -> list[Business]:
    try:
        client = GooglePlacesClient()
        places = await client.text_search(payload.keyword, payload.location, payload.max_results)
    except PlacesNotConfiguredError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Google Places request failed: {exc}") from exc

    created: list[Business] = []
    for place in places:
        normalised = normalise_place(place, city=payload.location)
        if normalised["place_id"]:
            existing = db.scalar(select(Business).where(Business.place_id == normalised["place_id"]))
            if existing:
                continue
        business = Business(**normalised, status=LeadStatus.WEBSITE_FOUND if normalised.get("website_url") else LeadStatus.DISCOVERED)
        db.add(business)
        db.flush()
        log_event(db, business.id, "business.discovered", {"keyword": payload.keyword, "location": payload.location})
        created.append(business)

    db.commit()
    for business in created:
        db.refresh(business)
    return created


@app.post("/businesses/{business_id}/enrich-email", response_model=list[ContactOut])
async def enrich_email(business_id: int, db: Session = Depends(get_db)) -> list[Contact]:
    business = get_business_or_404(db, business_id)
    if not business.website_url:
        raise HTTPException(status_code=400, detail="Business has no website_url to crawl")

    findings = await find_public_emails(business.website_url)
    contacts: list[Contact] = []
    for finding in findings:
        existing = db.scalar(select(Contact).where(Contact.business_id == business.id, Contact.email == finding.email))
        if existing:
            contacts.append(existing)
            continue
        contact = Contact(
            business_id=business.id,
            email=finding.email,
            phone=business.phone,
            source_url=finding.source_url,
            confidence=finding.confidence,
        )
        db.add(contact)
        contacts.append(contact)

    business.status = LeadStatus.EMAIL_FOUND if contacts else LeadStatus.WEBSITE_FOUND
    log_event(db, business.id, "email.enriched", {"count": len(contacts)})
    db.commit()
    for contact in contacts:
        db.refresh(contact)
    return contacts


@app.post("/businesses/{business_id}/validate-emails", response_model=list[ContactOut])
def validate_emails(business_id: int, db: Session = Depends(get_db)) -> list[Contact]:
    business = get_business_or_404(db, business_id)
    if not business.contacts:
        raise HTTPException(status_code=400, detail="No contacts to validate")

    for contact in business.contacts:
        if not contact.email:
            continue
        result = validate_public_email(contact.email)
        contact.email = result["email"]
        contact.validation_status = result["status"]
        contact.validation_notes = result["notes"]

    if any(contact.validation_status == EmailValidationStatus.VALID for contact in business.contacts):
        business.status = LeadStatus.EMAIL_VALIDATED

    log_event(db, business.id, "email.validated", {"count": len(business.contacts)})
    db.commit()
    for contact in business.contacts:
        db.refresh(contact)
    return business.contacts


@app.post("/businesses/{business_id}/build-site", response_model=WebsiteOut)
def build_site(business_id: int, db: Session = Depends(get_db)) -> Website:
    business = get_business_or_404(db, business_id)
    generated = generate_local_site(business)
    website = Website(
        business_id=business.id,
        github_repo_name=generated["slug"],
        local_path=generated["local_path"],
        deployment_status="LOCAL_GENERATED",
    )
    business.status = LeadStatus.SITE_BUILT
    db.add(website)
    log_event(db, business.id, "site.generated", generated)
    db.commit()
    db.refresh(website)
    return website


@app.get("/businesses/{business_id}/contacts", response_model=list[ContactOut])
def list_contacts(business_id: int, db: Session = Depends(get_db)) -> list[Contact]:
    get_business_or_404(db, business_id)
    return list(db.scalars(select(Contact).where(Contact.business_id == business_id).order_by(Contact.confidence.desc())).all())


@app.get("/businesses/{business_id}/websites", response_model=list[WebsiteOut])
def list_websites(business_id: int, db: Session = Depends(get_db)) -> list[Website]:
    get_business_or_404(db, business_id)
    return list(db.scalars(select(Website).where(Website.business_id == business_id).order_by(Website.created_at.desc())).all())


@app.post("/businesses/{business_id}/draft-email", response_model=OutreachEmailOut)
def draft_email(business_id: int, payload: DraftRequest, db: Session = Depends(get_db)) -> OutreachEmail:
    business = get_business_or_404(db, business_id)
    recipient = payload.recipient_email or next((contact.email for contact in business.contacts if contact.email), None)
    website_url = str(payload.website_url) if payload.website_url else None
    if not website_url and business.websites:
        latest_site = sorted(business.websites, key=lambda site: site.created_at, reverse=True)[0]
        website_url = latest_site.vercel_url or latest_site.local_path

    subject, body = build_pitch_email(business.name, website_url, business.city)
    outreach = OutreachEmail(
        business_id=business.id,
        recipient_email=recipient,
        subject=subject,
        body=body,
        status="DRAFT_LOCAL",
    )

    if payload.create_gmail_draft:
        if not recipient:
            raise HTTPException(status_code=400, detail="No recipient email available")
        try:
            draft = GmailDraftClient().create_draft(recipient, subject, body)
            outreach.gmail_draft_id = draft.get("id")
            outreach.gmail_thread_id = draft.get("message", {}).get("threadId")
            outreach.status = "GMAIL_DRAFT_CREATED"
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Gmail draft creation failed: {exc}") from exc

    business.status = LeadStatus.DRAFT_CREATED
    db.add(outreach)
    log_event(db, business.id, "email.draft_created", {"recipient": recipient, "gmail": payload.create_gmail_draft})
    db.commit()
    db.refresh(outreach)
    return outreach


@app.post("/cleanup/candidates", response_model=list[WebsiteOut])
def mark_cleanup_candidates(payload: CleanupRequest, db: Session = Depends(get_db)) -> list[Website]:
    cutoff = datetime.now(UTC) - timedelta(days=payload.older_than_days)
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

    if payload.mark_only:
        for website in websites:
            website.delete_pending = True
            if website.business:
                website.business.status = LeadStatus.DELETE_PENDING
            log_event(db, website.business_id, "cleanup.marked_delete_pending", {"website_id": website.id})
        db.commit()

    return websites


@app.post("/websites/{website_id}/keep", response_model=WebsiteOut)
def keep_website(website_id: int, db: Session = Depends(get_db)) -> Website:
    website = db.get(Website, website_id)
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    website.keep = True
    website.delete_pending = False
    log_event(db, website.business_id, "site.keep", {"website_id": website.id})
    db.commit()
    db.refresh(website)
    return website


@app.post("/websites/{website_id}/mark-delete", response_model=WebsiteOut)
def mark_delete_website(website_id: int, db: Session = Depends(get_db)) -> Website:
    website = db.get(Website, website_id)
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    website.delete_pending = True
    log_event(db, website.business_id, "site.mark_delete", {"website_id": website.id})
    db.commit()
    db.refresh(website)
    return website


@app.get("/stats")
def stats(db: Session = Depends(get_db)) -> dict:
    businesses = db.scalars(select(Business)).all()
    return {
        "total": len(businesses),
        "by_status": {status.value: sum(1 for business in businesses if business.status == status) for status in LeadStatus},
    }
