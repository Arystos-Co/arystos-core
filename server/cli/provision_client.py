"""Command-line interface for provisioning registry clients."""

import argparse
import asyncio
import sys

from server.registry.models import Tier
from server.registry.service import (
    DuplicateSlugError,
    ValidationError,
    provision_client,
)


async def _provision_client(arguments: argparse.Namespace) -> None:
    """Create a client from parsed command-line arguments and print its credentials."""
    result = await provision_client(
        slug=arguments.slug,
        business_name=arguments.business,
        contact_name=arguments.contact_name,
        contact_phone=arguments.contact_phone,
        tier=Tier(arguments.tier),
    )
    print(f"slug: {result.slug}")
    print(f"client_id: {result.client_id}")
    print(f"raw_token: {result.raw_token}")


def main() -> None:
    """Parse provisioning arguments, create a client, and report domain errors."""
    parser = argparse.ArgumentParser(description="Provision a new ARYSTOS client.")
    parser.add_argument("--slug", required=True)
    parser.add_argument("--business", required=True)
    parser.add_argument("--contact-name")
    parser.add_argument("--contact-phone")
    parser.add_argument("--tier", required=True, choices=[tier.value for tier in Tier])
    arguments = parser.parse_args()

    try:
        asyncio.run(_provision_client(arguments))
    except (ValidationError, DuplicateSlugError) as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
