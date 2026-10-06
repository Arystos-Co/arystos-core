"""Pydantic response models for API endpoints."""

from datetime import datetime

from pydantic import BaseModel

from server.registry.models import PaymentStatus, Status, Tier


class StatusResponse(BaseModel):
    """Status and minimum-version requirements for an authenticated client."""

    status: Status
    business_name: str
    tier: Tier
    app_version_required: str
    message: str | None = None


class ManifestResponse(BaseModel):
    """Published application release metadata."""

    manifest_version: int
    latest_version: str
    min_supported_version: str
    released_at: datetime
    release_notes: str
    download_url: str
    checksum: str
    signature: str


class ErrorResponse(BaseModel):
    """Canonical API error payload."""

    error: str
    detail: str | None = None


class ClientSummary(BaseModel):
    """Public summary of a registered client."""

    slug: str
    business_name: str
    tier: Tier
    status: Status
    app_version: str | None = None
    last_sync_at: datetime | None = None
    payment_status: PaymentStatus


class ClientDetail(ClientSummary):
    """Detailed client response for administrative endpoints."""

    contact_name: str | None = None
    contact_phone: str | None = None
    contract_start: datetime | None = None
    offboarded_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
