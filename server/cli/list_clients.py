"""Command-line interface for listing registry clients."""

import asyncio

from server.registry import repository
from server.registry.models import Client


def _format_client_table(clients: list[Client]) -> str:
    """Format client summaries as a readable fixed-width table."""
    columns = ("SLUG", "BUSINESS", "TIER", "STATUS", "APP_VERSION", "LAST_SYNC", "PAYMENT")
    rows = [
        (
            client.slug,
            client.business_name,
            client.tier.value,
            client.status.value,
            client.app_version or "-",
            client.last_sync_at.isoformat() if client.last_sync_at is not None else "-",
            client.payment_status.value,
        )
        for client in clients
    ]
    widths = [
        max([len(column), *(len(row[index]) for row in rows)])
        for index, column in enumerate(columns)
    ]
    output = ["  ".join(column.ljust(widths[index]) for index, column in enumerate(columns))]
    output.append("  ".join("-" * width for width in widths))
    output.extend(
        "  ".join(value.ljust(widths[index]) for index, value in enumerate(row))
        for row in rows
    )
    return "\n".join(output)


def main() -> None:
    """Fetch and print every registered client."""
    clients = asyncio.run(repository.list_clients())
    if not clients:
        print("No clients found.")
        return
    print(_format_client_table(clients))


if __name__ == "__main__":
    main()
