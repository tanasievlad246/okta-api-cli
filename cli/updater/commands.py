"""
Command handlers for update-related operations.
"""

import logging
import sys
from argparse import Namespace

from rich.console import Console
from rich.table import Table

from ..exceptions import UpdateCheckError, InstallationError
from .version_checker import check_for_updates, get_current_version
from .installer import install_update, get_rollback_instructions

logger = logging.getLogger(__name__)
console = Console()


def handle_update_command(args: Namespace) -> None:
    """
    Handles the update command.

    Args:
        args: Command line arguments with check and force flags
    """
    try:
        check_only = getattr(args, "check", False)
        force = getattr(args, "force", False)

        current_version = get_current_version()
        console.print(f"[blue]Current version:[/blue] {current_version}")
        console.print("\n[blue]Checking for updates...[/blue]")

        # Check for updates
        update_info = check_for_updates(force=force)

        if not update_info:
            console.print("[green]✓ You are running the latest version![/green]")
            return

        latest_version, download_url = update_info

        # Display update information
        table = Table(title="Update Available", show_header=True, header_style="bold magenta")
        table.add_column("Field", style="cyan", width=20)
        table.add_column("Value", style="green")

        table.add_row("Current Version", current_version)
        table.add_row("Latest Version", f"[bold]{latest_version}[/bold]")
        table.add_row("Release Page", download_url)

        console.print("\n")
        console.print(table)

        # If check-only mode, exit
        if check_only:
            console.print("\n[dim]Run 'okta update' to install the update[/dim]")
            return

        # Handle automatic confirmation
        auto_yes = getattr(args, "yes", False)

        if not auto_yes:
            # Check if running in non-interactive environment
            if not sys.stdin.isatty():
                console.print("\n[yellow]Non-interactive environment detected. Use --yes flag to auto-confirm updates.[/yellow]")
                return

            # Confirm installation interactively
            console.print("\n[yellow]Do you want to install the update? (y/N):[/yellow] ", end="")
            confirmation = input().strip().lower()

            if confirmation != "y":
                console.print("[dim]Update cancelled[/dim]")
                return

        # Install update
        console.print("\n[blue]Installing update...[/blue]")
        install_update()

        console.print(f"\n[bold green]✓ Successfully updated to version {latest_version}![/bold green]")
        console.print("\n[dim]Please restart the CLI for changes to take effect[/dim]")

    except UpdateCheckError as e:
        console.print(f"\n[bold red]✗ Failed to check for updates:[/bold red] {e}")
        logger.error(f"Update check failed: {e}", exc_info=True)

    except InstallationError as e:
        console.print(f"\n[bold red]✗ Installation failed:[/bold red] {e}")
        console.print("\n[yellow]Rollback instructions:[/yellow]")
        console.print(get_rollback_instructions())
        logger.error(f"Installation failed: {e}", exc_info=True)

    except Exception as e:
        console.print(f"\n[bold red]✗ Unexpected error:[/bold red] {e}")
        logger.error(f"Unexpected error during update: {e}", exc_info=True)


def check_for_updates_on_startup() -> None:
    """
    Performs a non-intrusive update check on CLI startup.

    Only shows a message if an update is available.
    Does not interrupt user workflow.
    """
    try:
        # Check for updates (respects cooldown period)
        update_info = check_for_updates(force=False)

        if update_info:
            latest_version, _ = update_info
            console.print(
                f"\n[dim]💡 Update available: [bold]{latest_version}[/bold]. "
                f"Run 'okta update' to upgrade.[/dim]\n"
            )

    except Exception as e:
        # Silently fail - don't interrupt user workflow
        logger.debug(f"Background update check failed: {e}")
