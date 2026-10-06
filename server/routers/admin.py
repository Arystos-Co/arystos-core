"""Administrator API routes for registry and audit data."""

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from server.access.service import (
    AlreadyOffboardedError,
    ClientNotFoundError,
    InvalidTransitionError,
    set_client_status,
)
from server.admin.service import set_payment_status
from server.auth.require_role import require_role
from server.auth.token import generate_token, hash_token
from server.database.connection import get_async_connection
from server.registry import repository
from server.registry.models import AuditEntry, PaymentStatus, Status, Tier
from server.registry.service import DuplicateSlugError, ValidationError, provision_client
from server.registry.user_models import UserPublic, UserRole
from server.routers.schemas import ClientDetail, ClientSummary

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


class StatusChangeRequest(BaseModel):
    """Validated request body for changing a client's status."""

    status: Literal["active", "suspended", "offboarded"]


class PaymentChangeRequest(BaseModel):
    """Validated request body for changing a client's payment status."""

    payment_status: Literal["paid", "pending", "overdue"]


class ProvisionClientRequest(BaseModel):
    """Request body used to provision a registration client."""

    slug: str
    business_name: str
    contact_name: str | None = None
    contact_phone: str | None = None
    tier: Literal["core", "growth", "advanced"]


@router.get("/clients", response_model=list[ClientSummary])
async def list_admin_clients(
    _: UserPublic = Depends(require_role(UserRole.OWNER, UserRole.OPERATOR, UserRole.READ_ONLY)),  # noqa: B008
) -> list[ClientSummary]:
    """Return safe summary models for every registered client."""
    clients = await repository.list_clients()
    return [ClientSummary.model_validate(client.model_dump()) for client in clients]


@router.post("/clients", status_code=201, response_model=None)
async def provision_admin_client(
    body: ProvisionClientRequest,
    _: UserPublic = Depends(require_role(UserRole.OWNER, UserRole.OPERATOR)),  # noqa: B008
) -> JSONResponse:
    """Provision a client after role validation and return the raw token once."""
    try:
        result = await provision_client(
            body.slug,
            body.business_name,
            body.contact_name,
            body.contact_phone,
            Tier(body.tier),
        )
    except ValidationError as exc:
        return JSONResponse(
            status_code=422,
            content={"error": "invalid_input", "detail": str(exc)},
        )
    except DuplicateSlugError as exc:
        return JSONResponse(
            status_code=409,
            content={"error": "duplicate_slug", "detail": str(exc)},
        )

    return JSONResponse(
        status_code=201,
        content={
            "client_id": result.client_id,
            "slug": result.slug,
            "raw_token": result.raw_token,
            "download_url": "/api/v1/delivery/installer",
        },
    )


@router.get("/clients/{slug}", response_model=None)
async def get_admin_client(
    slug: str,
    _: UserPublic = Depends(require_role(UserRole.OWNER, UserRole.OPERATOR, UserRole.READ_ONLY)),  # noqa: B008
) -> ClientDetail | JSONResponse:
    """Return details for a registered client without its token hash."""
    client = await repository.get_client_by_slug(slug)
    if client is None:
        return JSONResponse(status_code=404, content={"error": "client_not_found"})
    return ClientDetail.model_validate(client.model_dump())


@router.post("/clients/{slug}/status", response_model=None)
async def change_admin_client_status(
    slug: str,
    body: StatusChangeRequest,
    request: Request,
    _: UserPublic = Depends(require_role(UserRole.OWNER, UserRole.OPERATOR)),  # noqa: B008
) -> JSONResponse:
    """Change a client's status and return the service result."""
    ip_address = request.client.host if request.client is not None else None
    try:
        result = await set_client_status(
            slug,
            Status(body.status),
            actor="admin",
            ip_address=ip_address,
        )
    except ClientNotFoundError:
        return JSONResponse(status_code=404, content={"error": "client_not_found"})
    except AlreadyOffboardedError:
        return JSONResponse(status_code=409, content={"error": "already_offboarded"})
    except InvalidTransitionError as error:
        return JSONResponse(
            status_code=409,
            content={"error": "invalid_transition", "detail": str(error)},
        )
    return JSONResponse(
        status_code=200,
        content={"slug": result.slug, "status": result.status.value},
    )


@router.post("/clients/{slug}/payment", response_model=None)
async def change_admin_payment_status(
    slug: str,
    body: PaymentChangeRequest,
    request: Request,
    _: UserPublic = Depends(require_role(UserRole.OWNER, UserRole.OPERATOR)),  # noqa: B008
) -> JSONResponse:
    """Change a client's payment status and return the service result."""
    ip_address = request.client.host if request.client is not None else None
    try:
        result = await set_payment_status(
            slug,
            PaymentStatus(body.payment_status),
            actor="admin",
            ip_address=ip_address,
        )
    except ClientNotFoundError:
        return JSONResponse(status_code=404, content={"error": "client_not_found"})
    return JSONResponse(
        status_code=200,
        content={"slug": result.slug, "payment_status": result.payment_status.value},
    )


@router.post("/clients/{slug}/regenerate-token", response_model=None)
async def regenerate_client_token(
    slug: str,
    _: UserPublic = Depends(require_role(UserRole.OWNER)),  # noqa: B008
) -> JSONResponse:
    """Rotate a client's token and return the new raw value once."""
    client = await repository.get_client_by_slug(slug)
    if client is None:
        return JSONResponse(status_code=404, content={"error": "client_not_found"})

    raw_token = generate_token()
    token_hash = hash_token(raw_token)
    timestamp = datetime.now(UTC).isoformat()
    async with get_async_connection() as connection:
        await connection.execute(
            "UPDATE clients SET token_hash = ?, updated_at = ? WHERE slug = ?",
            (token_hash, timestamp, slug),
        )
        await connection.commit()
    await repository.insert_audit_entry(
        str(uuid4()),
        "admin",
        "client.token_regenerated",
        slug,
        None,
        None,
        None,
        None,
        timestamp,
    )
    return JSONResponse(
        status_code=200,
        content={
            "slug": slug,
            "raw_token": raw_token,
            "download_url": "/api/v1/delivery/installer",
        },
    )


@router.get("/clients/{slug}/audit", response_model=list[AuditEntry])
async def get_client_audit(
    slug: str,
    _: UserPublic = Depends(require_role(UserRole.OWNER, UserRole.OPERATOR, UserRole.READ_ONLY)),  # noqa: B008
) -> list[AuditEntry]:
    """Return the audit entries associated with a single client."""
    entries = await repository.list_recent_audit_entries()
    return [entry for entry in entries if entry.target_slug == slug]


@router.get("/audit", response_model=list[AuditEntry])
async def list_admin_audit(
    _: UserPublic = Depends(require_role(UserRole.OWNER, UserRole.OPERATOR, UserRole.READ_ONLY)),  # noqa: B008
) -> list[AuditEntry]:
    """Return the most recent audit records."""
    return await repository.list_recent_audit_entries()
