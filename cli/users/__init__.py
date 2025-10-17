"""
User management module for the Okta CLI.

Handles all user-related commands including sync, get, update, and delete.
"""

import json
import logging
from typing import Dict, Any
from argparse import Namespace

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.json import JSON

from ..okta import get_okta_client
from ..database.UsersRepository import UsersRepository
from ..exceptions import UserNotFoundError, OktaApiError, ValidationError

logger = logging.getLogger(__name__)
console = Console()


def handle_sync_users(args: Namespace) -> None:
    """
    Syncs users from Okta to the local database using multi-threading.

    Args:
        args: Command line arguments from argparse
    """
    try:
        console.print("[bold blue]Starting user sync from Okta...[/bold blue]")

        # Get Okta client and users
        okta_client = get_okta_client()
        users_client = okta_client.get_users_client()

        # Fetch users from Okta with progress indicator
        users = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Fetching users from Okta API...", total=None)

            def collect_users(accumulated_users):
                progress.update(
                    task, description=f"Fetched {len(accumulated_users)} users..."
                )

            users = users_client.get_users(cb=collect_users)
            progress.update(task, description=f"Fetched {len(users)} users total")

        if not users:
            console.print("[yellow]No users found in Okta[/yellow]")
            return

        console.print(f"[green]✓[/green] Retrieved {len(users)} users from Okta")

        # Sync users to database using ThreadPoolExecutor
        repository = UsersRepository()
        synced_count = 0
        failed_count = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        ) as progress:
            task = progress.add_task("Syncing users to database...", total=len(users))

            for user in users:
                try:
                    _sync_user(repository=repository, user=user)
                    synced_count += 1
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Failed to sync user {user.get('id')}: {e}")

                progress.update(task, advance=1)

        console.print(f"\n[bold green]✓ Sync completed![/bold green]")
        console.print(f"  • Synced: {synced_count} users")
        if failed_count > 0:
            console.print(f"  • Failed: {failed_count} users (check logs)")

    except Exception as e:
        console.print(f"[bold red]✗ Sync failed:[/bold red] {e}")
        logger.error(f"User sync failed: {e}", exc_info=True)
        raise


def _sync_user(repository: UsersRepository, user: Dict[str, Any]) -> None:
    """
    Helper function to sync a single user to the database.

    Args:
        repository: UsersRepository instance
        user: User data dictionary from Okta API
    """
    repository.create_or_update_user(user)


def handle_get_user(args: Namespace) -> None:
    """
    Retrieves and displays user information.

    Args:
        args: Command line arguments with id, email, and source flags from argparse
    """
    try:
        source = args.source if hasattr(args, "source") else "db"
        user = None

        if source == "api":
            # Fetch from Okta API
            okta_client = get_okta_client()
            users_client = okta_client.get_users_client()

            if args.id:
                console.print(f"[blue]Fetching user {args.id} from Okta API...[/blue]")
                user = users_client.get_user_by_id(args.id)

                # Sync to database
                if user:
                    repository = UsersRepository()
                    repository.create_or_update_user(user)
                    console.print("[dim]✓ User synced to local database[/dim]\n")

            elif args.email:
                console.print(
                    f"[blue]Fetching user {args.email} from Okta API...[/blue]"
                )
                user = users_client.get_user_by_email(args.email)

                # Sync to database
                if user:
                    repository = UsersRepository()
                    repository.create_or_update_user(user)
                    console.print("[dim]✓ User synced to local database[/dim]\n")
            else:
                raise ValidationError("Either --id or --email must be provided")

        else:
            # Fetch from local database
            repository = UsersRepository()

            if args.id:
                console.print(
                    f"[blue]Fetching user {args.id} from local database...[/blue]"
                )
                user = repository.get_user_by_id(args.id)
            elif args.email:
                console.print(
                    f"[blue]Fetching user {args.email} from local database...[/blue]"
                )
                user = repository.get_user_by_email(args.email)
            else:
                raise ValidationError("Either --id or --email must be provided")

        if not user:
            console.print("[yellow]User not found[/yellow]")
            raise UserNotFoundError("User not found")

        # Display user in pretty format
        _display_user(user)

    except Exception as e:
        console.print(f"[bold red]✗ Error:[/bold red] {e}")
        logger.error(f"Failed to get user: {e}", exc_info=True)
        raise


def handle_update_user(args: Namespace) -> None:
    """
    Updates a user's profile in both Okta and the local database.

    Args:
        args: Command line arguments with id and profile JSON string from argparse
    """
    try:
        if not args.id:
            raise ValidationError("--id is required for update")

        if not args.profile:
            raise ValidationError("--profile is required for update")

        # Parse profile JSON
        try:
            profile = json.loads(args.profile)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON in --profile: {e}")

        console.print(f"[blue]Updating user {args.id}...[/blue]")

        # Update in Okta
        okta_client = get_okta_client()
        users_client = okta_client.get_users_client()
        updated_user = users_client.update_user(args.id, profile)

        # Update in local database
        repository = UsersRepository()
        repository.update_user_profile(args.id, profile)

        console.print(
            f"[bold green]✓ User {args.id} updated successfully![/bold green]"
        )
        _display_user(updated_user)

    except Exception as e:
        console.print(f"[bold red]✗ Update failed:[/bold red] {e}")
        logger.error(f"Failed to update user: {e}", exc_info=True)
        raise


def handle_delete_user(args: Namespace) -> None:
    """
    Deletes a user from both Okta and the local database.

    Args:
        args: Command line arguments with id or email from argparse
    """
    try:
        user_id = None

        # Get user ID
        if args.id:
            user_id = args.id
        elif args.email:
            # Look up user by email first
            repository = UsersRepository()
            user = repository.get_user_by_email(args.email)
            if user:
                user_id = user["id"]
            else:
                raise UserNotFoundError(f"User with email {args.email} not found")
        else:
            raise ValidationError("Either --id or --email must be provided")

        # Confirm deletion
        console.print(
            f"[yellow]⚠ Are you sure you want to delete user {user_id}? (y/N):[/yellow] ",
            end="",
        )
        confirmation = input().strip().lower()

        if confirmation != "y":
            console.print("[dim]Deletion cancelled[/dim]")
            return

        console.print(f"[blue]Deleting user {user_id}...[/blue]")

        # Delete from Okta
        okta_client = get_okta_client()
        users_client = okta_client.get_users_client()
        users_client.delete_user(user_id)

        # Delete from local database
        repository = UsersRepository()
        repository.delete_user(user_id)

        console.print(
            f"[bold green]✓ User {user_id} deleted successfully![/bold green]"
        )

    except Exception as e:
        console.print(f"[bold red]✗ Delete failed:[/bold red] {e}")
        logger.error(f"Failed to delete user: {e}", exc_info=True)
        raise


def _display_user(user: Dict[str, Any]) -> None:
    """
    Displays user information in a formatted table.

    Args:
        user: User data dictionary in Okta API response format
    """
    table = Table(
        title="User Information", show_header=True, header_style="bold magenta"
    )
    table.add_column("Field", style="cyan", width=20)
    table.add_column("Value", style="green")

    # Basic info
    table.add_row("ID", user.get("id", "N/A"))
    table.add_row("Status", user.get("status", "N/A"))

    # Profile info
    profile = user.get("profile", {})
    table.add_row("First Name", profile.get("firstName", "N/A"))
    table.add_row("Last Name", profile.get("lastName", "N/A"))
    table.add_row("Email", profile.get("email", "N/A"))
    table.add_row("Login", profile.get("login", "N/A"))
    table.add_row("Mobile Phone", profile.get("mobilePhone", "N/A"))

    # Timestamps
    table.add_row("Created", user.get("created", "N/A"))
    table.add_row("Last Updated", user.get("lastUpdated", "N/A"))
    table.add_row("Last Login", user.get("lastLogin", "N/A"))
    table.add_row("Placement Org", profile.get("placementOrg", "N/A"))
    table.add_row("Portal Access Groups", profile.get("portalAccessGroup", "N/A"))

    console.print(table)
