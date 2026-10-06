"""Command-line interface for changing client and payment status."""

import argparse
import asyncio
import sys

from server.access import service as access_service
from server.admin import service as admin_service
from server.registry.models import PaymentStatus, Status


async def _set_status(slug: str, value: str) -> str:
    """Set a client's status and return the service result for display."""
    result = await access_service.set_client_status(
        slug=slug,
        new_status=Status(value),
        actor="cli",
        ip_address=None,
    )
    return f"Client {result.slug} status set to {result.status.value}."


async def _set_payment_status(slug: str, value: str) -> str:
    """Set a client's payment status and return the service result for display."""
    result = await admin_service.set_payment_status(
        slug=slug,
        new_status=PaymentStatus(value),
        actor="cli",
        ip_address=None,
    )
    return f"Client {result.slug} payment status set to {result.payment_status.value}."


def main() -> None:
    """Parse and execute a client status or payment-status change."""
    parser = argparse.ArgumentParser(description="Manage an ARYSTOS client.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    status_parser = subparsers.add_parser("status", help="Change client status.")
    status_parser.add_argument("--slug", required=True)
    status_parser.add_argument(
        "--value",
        required=True,
        choices=[status.value for status in Status],
    )

    payment_parser = subparsers.add_parser("payment", help="Change payment status.")
    payment_parser.add_argument("--slug", required=True)
    payment_parser.add_argument(
        "--value",
        required=True,
        choices=[status.value for status in PaymentStatus],
    )

    arguments = parser.parse_args()
    try:
        if arguments.command == "status":
            message = asyncio.run(_set_status(arguments.slug, arguments.value))
        else:
            message = asyncio.run(_set_payment_status(arguments.slug, arguments.value))
    except (
        access_service.ClientNotFoundError,
        access_service.AlreadyOffboardedError,
        access_service.InvalidTransitionError,
    ) as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1) from error

    print(message)


if __name__ == "__main__":
    main()
