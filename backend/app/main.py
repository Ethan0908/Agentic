from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

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
    OutreachEmailOut,
    StatusUpdate,
    WebsiteOut,
)
from app.services.codex_site import improve_site_with_codex
from app.services.email_finder import find_public_emails
from app.services.email_validator import validate_public_email
from app.services.github_client import GitHubClient
from app.services.outreach_mailer import SMTPMailer, build_pitch_email, build_pitch_email_with_gpt
from app.services.places import GooglePlacesClient, PlacesNotConfiguredError, normalise_place
from app.services.site_generator import generate_local_site
from app.services.vercel_client import VercelClient

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


def get_latest_website_or_404(db: Session, business_id: int) -> Website:
    website = db.scalar(
        select(Website)
        .where(Website.business_id == business_id)
        .order_by(Website.created_at.desc())
    )
    if not website:
        raise HTTPException(status_code=400, detail="No generated website found. Build site first.")
    return website


def log_event(db: Session, business_id: int | None, event_type: str, details: dict | None = None) -> None:
    db.add(Event(business_id=business_id, event_type=event_type, details=details or {}))


def short_repo_name(repo_name_or_full_name: str | None, fallback: str | None = None) -> str:
    value = repo_name_or_full_name or fallback or "generated-business-site"
    return value.split("/", 1)[1] if "/" in value else value


async def create_codex_generated_site(db: Session, business: Business) -> Website:
    generated = generate_local_site(business)
    site_path = Path(generated["local_path"])

    try:
        codex_result = await improve_site_with_codex(site_path, business, generated["business_json"], fallback_repo_name=generated["slug"])
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Codex site generation failed: {exc}") from exc

    # Codex chooses the repo/project name by writing codex-output.json. Fall back
    # to the deterministic slug only if Codex did not produce metadata.
    repo_name = short_repo_name(codex_result.get("repo_name"), generated["slug"])

    website = Website(
        business_id=business.id,
        github_repo_name=repo_name,
        local_path=generated["local_path"],
        deployment_status="CODEX_GENERATED" if codex_result.get("codex_ran") else "LOCAL_GENERATED",
    )
    business.status = LeadStatus.SITE_BUILT
    db.add(website)
    log_event(db, business.id, "site.generated", {"generated": generated, "codex": codex_result, "repo_name": repo_name})
    db.commit()
    db.refresh(website)
    return website


async def publish_website_to_github(db: Session, business: Business, website: Website) -> Website:
    if not website.local_path:
        raise HTTPException(status_code=400, detail="Website has no local_path")

    requested_repo_name = short_repo_name(website.github_repo_name, Path(website.local_path).name)
    source_dir = Path(website.local_path)

    try:
        github = GitHubClient()
        repo = await github.create_repo_from_template(requested_repo_name, private=settings.github_generated_repo_private)
        repo_full_name = repo.get("full_name") or f"{settings.github_owner}/{requested_repo_name}"
        repo_short_name = repo.get("name") or requested_repo_name
        branch = repo.get("default_branch", "main")
        upload = await github.upload_directory(repo_full_name, source_dir, branch=branch)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"GitHub publish failed: {exc}") from exc

    # Store the precise full_name so later Vercel deploys never have to guess the owner.
    website.github_repo_name = repo_full_name
    website.github_repo_url = repo.get("html_url")
    website.deployment_status = "GITHUB_PUBLISHED"
    log_event(db, business.id, "site.github_published", {"repo": repo_full_name, **upload})

    # Best-effort central archive folder inside the configured GitHub repo.
    archive_prefix = f"{settings.github_archive_path.strip('/')}/{repo_short_name}".strip("/")
    if settings.github_archive_repo and archive_prefix:
        try:
            archive_upload = await github.upload_directory_to_path(
                settings.github_archive_repo,
                source_dir,
                target_prefix=archive_prefix,
                branch=settings.github_archive_branch,
            )
            log_event(
                db,
                business.id,
                "site.github_archived",
                {"repo": f"{settings.github_owner}/{settings.github_archive_repo}", "path": archive_prefix, **archive_upload},
            )
        except Exception as exc:
            # Do not block the customer's site if the central archive copy fails.
            log_event(
                db,
                business.id,
                "site.github_archive_failed",
                {"repo": settings.github_archive_repo, "path": archive_prefix, "error": str(exc)},
            )

    db.commit()
    db.refresh(website)
    return website


async def deploy_website_to_vercel(db: Session, business: Business, website: Website) -> Website:
    if not website.github_repo_name:
        raise HTTPException(status_code=400, detail="Publish the latest site to GitHub first")

    try:
        github = GitHubClient()
        repo = await github.get_repo(website.github_repo_name)
        repo_short_name = repo.get("name") or short_repo_name(website.github_repo_name)
        repo_full_name = repo.get("full_name") or website.github_repo_name
        repo_id = repo.get("id")
        if not repo_id:
            raise RuntimeError(f"GitHub repo has no id: {repo_full_name}")

        vercel = VercelClient()
        project = await vercel.create_project_for_github_repo(repo_short_name, repo_full_name)
        deployment = await vercel.create_deployment_from_github(
            repo_short_name,
            repo_id,
            ref=repo.get("default_branch", "main"),
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Vercel deployment failed: {exc}") from exc

    deployment_url = deployment.get("url")
    if deployment_url and not deployment_url.startswith("http"):
        deployment_url = f"https://{deployment_url}"

    website.vercel_project_id = project.get("id") or project.get("name") or short_repo_name(website.github_repo_name)
    website.vercel_url = deployment_url
    website.deployment_status = "VERCEL_DEPLOYED"
    business.status = LeadStatus.SITE_DEPLOYED
    log_event(
        db,
        business.id,
        "site.vercel_deployed",
        {"project": project.get("name"), "deployment_id": deployment.get("id"), "url": deployment_url},
    )
    db.commit()
    db.refresh(website)
    return website


async def build_publish_deploy_pipeline(db: Session, business: Business) -> Website:
    website = await create_codex_generated_site(db, business)
    website = await publish_website_to_github(db, business, website)
    website = await deploy_website_to_vercel(db, business, website)
    return website


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
    data = payload.model_dump()
    contact_email = data.pop("contact_email", None)
    business = Business(**data, source="manual", status=LeadStatus.EMAIL_FOUND if contact_email else LeadStatus.DISCOVERED)
    db.add(business)
    db.flush()
    if contact_email:
        db.add(
            Contact(
                business_id=business.id,
                email=contact_email.strip(),
                phone=business.phone,
                source_url="manual",
                confidence=100,
            )
        )
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
async def build_site(business_id: int, db: Session = Depends(get_db)) -> Website:
    """One-click website path: Codex build + GitHub publish + Vercel deploy."""
    business = get_business_or_404(db, business_id)
    return await build_publish_deploy_pipeline(db, business)


@app.post("/businesses/{business_id}/generate-site-only", response_model=WebsiteOut)
async def generate_site_only(business_id: int, db: Session = Depends(get_db)) -> Website:
    """Developer/debug path only. The dashboard should not use this."""
    business = get_business_or_404(db, business_id)
    return await create_codex_generated_site(db, business)


@app.post("/businesses/{business_id}/publish-latest-site-github", response_model=WebsiteOut)
async def publish_latest_site_github(business_id: int, db: Session = Depends(get_db)) -> Website:
    business = get_business_or_404(db, business_id)
    website = get_latest_website_or_404(db, business_id)
    return await publish_website_to_github(db, business, website)


@app.post("/businesses/{business_id}/deploy-latest-site-vercel", response_model=WebsiteOut)
async def deploy_latest_site_vercel(business_id: int, db: Session = Depends(get_db)) -> Website:
    business = get_business_or_404(db, business_id)
    website = get_latest_website_or_404(db, business_id)
    return await deploy_website_to_vercel(db, business, website)


@app.post("/businesses/{business_id}/build-publish-deploy-site", response_model=WebsiteOut)
async def build_publish_deploy_site(business_id: int, db: Session = Depends(get_db)) -> Website:
    business = get_business_or_404(db, business_id)
    return await build_publish_deploy_pipeline(db, business)


@app.get("/businesses/{business_id}/contacts", response_model=list[ContactOut])
def list_contacts(business_id: int, db: Session = Depends(get_db)) -> list[Contact]:
    get_business_or_404(db, business_id)
    return list(db.scalars(select(Contact).where(Contact.business_id == business_id).order_by(Contact.confidence.desc())).all())


@app.get("/businesses/{business_id}/websites", response_model=list[WebsiteOut])
def list_websites(business_id: int, db: Session = Depends(get_db)) -> list[Website]:
    get_business_or_404(db, business_id)
    return list(db.scalars(select(Website).where(Website.business_id == business_id).order_by(Website.created_at.desc())).all())


@app.get("/businesses/{business_id}/outreach-emails", response_model=list[OutreachEmailOut])
def list_outreach_emails(business_id: int, db: Session = Depends(get_db)) -> list[OutreachEmail]:
    get_business_or_404(db, business_id)
    return list(db.scalars(select(OutreachEmail).where(OutreachEmail.business_id == business_id).order_by(OutreachEmail.created_at.desc())).all())


@app.post("/businesses/{business_id}/draft-email", response_model=OutreachEmailOut)
async def draft_email(business_id: int, payload: DraftRequest, db: Session = Depends(get_db)) -> OutreachEmail:
    business = get_business_or_404(db, business_id)
    recipient = payload.recipient_email or next((contact.email for contact in business.contacts if contact.email), None)
    website_url = str(payload.website_url) if payload.website_url else None
    if not website_url and business.websites:
        latest_site = sorted(business.websites, key=lambda site: site.created_at, reverse=True)[0]
        website_url = latest_site.vercel_url or latest_site.local_path

    if payload.use_gpt:
        subject, body = await build_pitch_email_with_gpt(business, website_url)
    else:
        subject, body = build_pitch_email(business.name, website_url, business.city)

    outreach = OutreachEmail(
        business_id=business.id,
        recipient_email=recipient,
        subject=subject,
        body=body,
        status="DRAFT_LOCAL",
    )

    business.status = LeadStatus.DRAFT_CREATED
    db.add(outreach)
    log_event(db, business.id, "email.draft_created", {"recipient": recipient, "use_gpt": payload.use_gpt})
    db.commit()
    db.refresh(outreach)
    return outreach


@app.post("/businesses/{business_id}/send-latest-email", response_model=OutreachEmailOut)
def send_latest_email(business_id: int, db: Session = Depends(get_db)) -> OutreachEmail:
    business = get_business_or_404(db, business_id)
    outreach = db.scalar(
        select(OutreachEmail)
        .where(OutreachEmail.business_id == business.id, OutreachEmail.status != "SENT")
        .order_by(OutreachEmail.created_at.desc())
    )
    if not outreach:
        raise HTTPException(status_code=400, detail="No unsent local draft found. Create a draft first.")
    if not outreach.recipient_email:
        raise HTTPException(status_code=400, detail="Draft has no recipient email. Add a contact email first.")

    try:
        send_result = SMTPMailer().send(outreach.recipient_email, outreach.subject, outreach.body)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"SMTP send failed: {exc}") from exc

    outreach.status = "SENT"
    outreach.sent_at = datetime.now(UTC)
    business.status = LeadStatus.SENT
    log_event(db, business.id, "email.sent", {"outreach_email_id": outreach.id, "smtp_result": send_result})
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
