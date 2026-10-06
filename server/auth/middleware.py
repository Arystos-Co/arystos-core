"""Authentication dependencies for client and administrator endpoints."""

from fastapi import Depends, Header, HTTPException

from server.auth.token import extract_bearer, hash_token, tokens_equal
from server.config import ADMIN_TOKEN
from server.registry import repository
from server.registry.models import Client, Status


async def require_client(
    authorization: str | None = Header(default=None),
) -> Client:
    """Authenticate a client bearer token and return its registry record.

    Args:
        authorization: Optional HTTP Authorization header.

    Returns:
        The client associated with the valid bearer token.

    Raises:
        HTTPException: If the header is missing or the token is invalid.
    """
    raw_token = extract_bearer(authorization)
    if raw_token is None:
        error_code = "authentication_required" if authorization is None else "invalid_credentials"
        raise HTTPException(status_code=401, detail=error_code)

    client = await repository.get_client_by_token_hash(hash_token(raw_token))
    if client is None:
        raise HTTPException(status_code=401, detail="invalid_credentials")
    return client


async def require_active_client(
    client: Client = Depends(require_client),  # noqa: B008
) -> Client:
    """Authenticate a client and reject suspended or offboarded accounts.

    Args:
        client: Client returned by the `require_client` dependency.

    Returns:
        The authenticated active client.

    Raises:
        HTTPException: If the client account is not active.
    """
    if client.status is not Status.ACTIVE:
        raise HTTPException(status_code=403, detail="account_locked")
    return client


async def require_admin(
    authorization: str | None = Header(default=None),
) -> None:
    """Validate the configured administrator bearer token.

    Args:
        authorization: Optional HTTP Authorization header.

    Returns:
        None.

    Raises:
        HTTPException: If the header is missing or its token is invalid.
    """
    raw_token = extract_bearer(authorization)
    if raw_token is None:
        error_code = "authentication_required" if authorization is None else "invalid_credentials"
        raise HTTPException(status_code=401, detail=error_code)
    if not tokens_equal(raw_token, ADMIN_TOKEN):
        raise HTTPException(status_code=401, detail="invalid_credentials")
