"""
User management module for the Okta CLI.

Handles all user-related commands including sync, get, update, and delete.
"""

import json
import logging
import os
from typing import Dict, Any, List
from argparse import Namespace
from datetime import date
import csv

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table

from ..okta import get_okta_client
from ..database.UsersRepository import UsersRepository
from ..exceptions import UserNotFoundError, ValidationError


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


def handle_password_reset(args: Namespace):
    try:
        if not args.id:
            raise ValidationError("--id is required for password reset")

        okta_client = get_okta_client()
        users_client = okta_client.get_users_client()
        password_reset_reponse = users_client.reset_user_password(args.id)
        console.log(password_reset_reponse)
        console.print(
            f"[bold green]✓ User {args.id} password reset successfully![/bold green]"
        )
        _display_dict_as_table("Password reset response", password_reset_reponse)
    except Exception:
        pass


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


def _display_dict_as_table(title: str, input: Dict[str, Any]) -> None:
    """
    Displays a given dict as a table, the dict must not have any nested dicts or lists

    Args:
        title: Title for the table
        input: A dict with data
    """
    table = Table(title=title, show_header=True, header_style="bold magenta")

    table.add_column("Field", style="cyan", width=20)
    table.add_column("Value", style="green")

    for k, v in input.items():
        if isinstance(v, (dict, list, set, tuple)):
            table.add_row(k, str(v))
        else:
            table.add_row(k, str(v))

    console.print(table)


def list_users(args: Namespace) -> None:
    """
    Retrieves and displays user information.

    Args:
        args: Command line arguments with page, limit, or export to export users to a csv file
    """
    try:
        repository = UsersRepository()

        if args.export:
            console.print("[blue]Exporting all users to CSV...[/blue]")
            users = repository.get_all_users()

            if not users:
                console.print("[yellow]No users found to export[/yellow]")
                return

            # Define CSV columns
            fieldnames = [
                "id",
                "status",
                "firstName",
                "lastName",
                "email",
                "login",
                "mobilePhone",
                "created",
                "lastUpdated",
                "lastLogin",
                "placementOrg",
                "portalAccessGroup",
            ]

            filename = f"okta_users_export_{date.today()}.csv"
            filepath = os.path.join(os.getcwd(), filename)

            with open(filepath, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for user in users:
                    profile = user.get("profile", {})
                    row = {
                        "id": user.get("id", ""),
                        "status": user.get("status", ""),
                        "firstName": profile.get("firstName", ""),
                        "lastName": profile.get("lastName", ""),
                        "email": profile.get("email", ""),
                        "login": profile.get("login", ""),
                        "mobilePhone": profile.get("mobilePhone", ""),
                        "created": user.get("created", ""),
                        "lastUpdated": user.get("lastUpdated", ""),
                        "lastLogin": user.get("lastLogin", ""),
                        "placementOrg": profile.get("placementOrg", ""),
                        "portalAccessGroup": profile.get("portalAccessGroup", ""),
                    }
                    writer.writerow(row)

            console.print(f"[bold green]✓ Exported {len(users)} users to {filename}[/bold green]")
            return

        # Paginated display
        limit = args.limit if hasattr(args, 'limit') and args.limit is not None else 25
        page = args.page if hasattr(args, 'page') and args.page is not None else 1

        result = repository.get_all_users_paginated(limit, page)
        _print_users_profile_table(result)

    except Exception as e:
        console.print(f"[bold red]✗ Error:[/bold red] {e}")
        logger.error(f"Failed to list users: {e}", exc_info=True)
        raise


def _print_users_profile_table(result: dict) -> None:
    """
    Displays a paginated table of users with their profile information.

    Args:
        result: Dictionary from get_all_users_paginated containing users and pagination info
    """
    users = result.get("users", [])
    total_users = result.get("total_users", 0)
    total_pages = result.get("total_pages", 0)
    current_page = result.get("current_page", 1)

    if not users:
        console.print("[yellow]No users found[/yellow]")
        return

    # Create table with pagination info in title
    title = f"Users (Page {current_page} of {total_pages} | Total: {total_users})"
    table = Table(title=title, show_header=True, header_style="bold magenta")

    # Add columns
    table.add_column("ID", style="cyan", overflow="fold", max_width=15)
    table.add_column("Status", style="green")
    table.add_column("First Name", style="white")
    table.add_column("Last Name", style="white")
    table.add_column("Email", style="blue", overflow="fold")
    table.add_column("Mobile Phone", style="white")
    table.add_column("Placement Org", style="yellow", overflow="fold")
    table.add_column("Last Login", style="dim", overflow="fold", max_width=20)

    # Add rows
    for user in users:
        profile = user.get("profile", {})
        table.add_row(
            user.get("id", "N/A")[:15],  # Truncate long IDs
            user.get("status", "N/A"),
            profile.get("firstName", "N/A"),
            profile.get("lastName", "N/A"),
            profile.get("email", "N/A"),
            profile.get("mobilePhone", "N/A"),
            profile.get("placementOrg", "N/A"),
            user.get("lastLogin", "N/A")[:19] if user.get("lastLogin") else "N/A",  # Show date only
        )

    console.print(table)

def handler_set_temp_password(args: Namespace) -> None:
    """
    Sets a temporary password for a user and displays it.

    Args:
        args: Command line arguments with id flag from argparse
    """
    try:
        if not args.id:
            raise ValidationError("--id is required for setting temporary password")

        console.print(f"[blue]Generating temporary password for user {args.id}...[/blue]")

        # Get Okta client and generate temp password
        okta_client = get_okta_client()
        users_client = okta_client.get_users_client()
        temp_password = users_client.expire_user_password_with_new_password(args.id)

        # Get user info to display email
        repository = UsersRepository()
        user = repository.get_user_by_id(args.id)

        console.print(f"[bold green]✓ Temporary password generated successfully![/bold green]\n")

        # Display result in a table
        table = Table(
            title="Temporary Password Information",
            show_header=True,
            header_style="bold magenta"
        )
        table.add_column("Field", style="cyan", width=20)
        table.add_column("Value", style="yellow")

        table.add_row("User ID", args.id)
        if user:
            profile = user.get("profile", {})
            table.add_row("Email", profile.get("email", "N/A"))
            table.add_row("Name", f"{profile.get('firstName', '')} {profile.get('lastName', '')}".strip() or "N/A")

        table.add_row("Temporary Password", f"[bold]{temp_password}[/bold]")

        console.print(table)
        console.print("\n[dim]⚠ Note: This password must be changed on first login[/dim]")

    except UserNotFoundError as e:
        console.print(f"[bold red]✗ Error:[/bold red] {e}")
        logger.error(f"User not found: {e}", exc_info=True)
        raise
    except Exception as e:
        console.print(f"[bold red]✗ Failed to set temporary password:[/bold red] {e}")
        logger.error(f"Failed to set temporary password: {e}", exc_info=True)
        raise
