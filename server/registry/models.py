from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class Tier(StrEnum):
    CORE = "core"
    GROWTH = "growth"
    ADVANCED = "advanced"


class Status(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    OFFBOARDED = "offboarded"


class PaymentStatus(StrEnum):
    PAID = "paid"
    PENDING = "pending"
    OVERDUE = "overdue"


class Client(BaseModel):
    id: UUID
    slug: str
    business_name: str
    contact_name: str | None = None
    contact_phone: str | None = None
    token_hash: str
    tier: Tier
    status: Status
    app_version: str | None = None
    last_sync_at: datetime | None = None
    last_update_at: datetime | None = None
    payment_status: PaymentStatus
    contract_start: datetime | None = None
    offboarded_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class AuditEntry(BaseModel):
    id: UUID
    actor: str
    action: str
    target_slug: str
    old_value: str | None = None
    new_value: str | None = None
    reason: str | None = None
    ip_address: str | None = None
    timestamp: datetime
