"""Business rules for provisioning registry clients."""

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

import aiosqlite

from server.auth.token import generate_token, hash_token
from server.registry import repository
from server.registry.models import Tier

SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]$")
MAX_BUSINESS_NAME_LENGTH = 255
MAX_CONTACT_NAME_LENGTH = 100
MAX_CONTACT_PHONE_LENGTH = 25


class ValidationError(Exception):
    """Raised when client provisioning input fails validation."""


class DuplicateSlugError(Exception):
    """Raised when a client slug is already registered."""


@dataclass(frozen=True)
class ProvisionResult:
    """Client identifiers and the raw token returned at provisioning time."""

    client_id: str
    slug: str
    raw_token: str


def validate_slug(slug: str) -> None:
    """Validate a client slug against the registry format.

    Args:
        slug: Slug to validate.

    Returns:
        None.

    Raises:
        ValidationError: If the slug does not match the required pattern.
    """
    if not isinstance(slug, str) or SLUG_PATTERN.fullmatch(slug) is None:
        raise ValidationError("slug must be 3 to 63 lowercase letters, digits, or hyphens")


def validate_lengths(
    business_name: str,
    contact_name: str | None,
    contact_phone: str | None,
) -> None:
    """Validate the maximum lengths of client name and contact fields.

    Args:
        business_name: Client business name.
        contact_name: Optional contact name.
        contact_phone: Optional contact phone number.

    Returns:
        None.

    Raises:
        ValidationError: If a field exceeds its maximum length.
    """
    if len(business_name) > MAX_BUSINESS_NAME_LENGTH:
        raise ValidationError("business_name must be at most 255 characters")
    if contact_name is not None and len(contact_name) > MAX_CONTACT_NAME_LENGTH:
        raise ValidationError("contact_name must be at most 100 characters")
    if contact_phone is not None and len(contact_phone) > MAX_CONTACT_PHONE_LENGTH:
        raise ValidationError("contact_phone must be at most 25 characters")


async def provision_client(
    slug: str,
    business_name: str,
    contact_name: str | None,
    contact_phone: str | None,
    tier: Tier,
) -> ProvisionResult:
    """Validate, register, and audit a client, returning its raw token once.

    Args:
        slug: Unique registry slug for the client.
        business_name: Client business name.
        contact_name: Optional contact name.
        contact_phone: Optional contact phone number.
        tier: Service tier to assign.

    Returns:
        The new client's id, slug, and unpersisted raw token.

    Raises:
        ValidationError: If the slug, field lengths, or tier is invalid.
        DuplicateSlugError: If a client with the slug already exists.
        aiosqlite.Error: If database persistence fails for another reason.
    """
    validate_slug(slug)
    validate_lengths(business_name, contact_name, contact_phone)
    try:
        validated_tier = Tier(tier)
    except (TypeError, ValueError) as error:
        raise ValidationError("tier must be one of: core, growth, advanced") from error

    client_id = str(uuid4())
    raw_token = generate_token()
    token_hash = hash_token(raw_token)
    timestamp = datetime.now(UTC).isoformat()

    async with repository.transaction() as connection:
        try:
            await repository.insert_client(
                client_id,
                slug,
                business_name,
                contact_name,
                contact_phone,
                token_hash,
                validated_tier.value,
                connection=connection,
            )
        except aiosqlite.IntegrityError as error:
            raise DuplicateSlugError(f"client slug already exists: {slug}") from error

        await repository.insert_audit_entry(
            str(uuid4()),
            "system",
            "client.provisioned",
            slug,
            None,
            validated_tier.value,
            None,
            None,
            timestamp,
            connection=connection,
        )

    return ProvisionResult(client_id, slug, raw_token)
