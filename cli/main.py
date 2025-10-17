#!/usr/bin/env python3
"""
Okta CLI - Command line interface for Okta API.

Main entry point for the application.
"""

import argparse
import sys
from cli.config import config_machine
from cli.users import (
    handle_sync_users,
    handle_get_user,
    handle_update_user,
    handle_delete_user,
    handle_password_reset,
)
from cli.utils import setup_logging
# from typer import Typer

# app = Typer()


# @app.command()
def main():
    """Main entry point for the Okta CLI."""
    parser = argparse.ArgumentParser(
        prog="okta",
        description="Okta API CLI - Manage Okta users from the command line",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging (DEBUG level)",
    )

    subparser = parser.add_subparsers(dest="command", required=True)

    # CONFIG COMMAND
    config_parser = subparser.add_parser(
        "config",
        help="Configure Okta API credentials",
        description="Sets up the required API key and organization URL for the Okta API",
    )
    config_parser.add_argument(
        "--okta-api-key",
        type=str,
        required=True,
        help="Your Okta API key (SSWS token)",
    )
    config_parser.add_argument(
        "--okta-org-url",
        type=str,
        required=True,
        help="Your Okta organization URL (e.g., https://dev-123456.okta.com)",
    )
    config_parser.set_defaults(func=config_machine)

    # USERS COMMAND
    users_parser = subparser.add_parser(
        "users",
        help="Manage Okta users",
        description="User management commands",
    )
    users_subparser = users_parser.add_subparsers(dest="subcommand", required=True)

    # USERS SYNC SUBCOMMAND
    sync_parser = users_subparser.add_parser(
        "sync",
        help="Sync all users from Okta to local database",
        description="Fetches all users from Okta and syncs them to the local SQLite database using multi-threading",
    )
    sync_parser.set_defaults(func=handle_sync_users)

    # USERS GET SUBCOMMAND
    get_parser = users_subparser.add_parser(
        "get",
        help="Get user information",
        description="Retrieve user information by ID or email from local database or Okta API",
    )
    get_group = get_parser.add_mutually_exclusive_group(required=True)
    get_group.add_argument(
        "--id",
        type=str,
        help="User ID to retrieve",
    )
    get_group.add_argument(
        "--email",
        type=str,
        help="User email to retrieve",
    )
    get_parser.add_argument(
        "--source",
        type=str,
        choices=["db", "api"],
        default="db",
        help="Source to fetch user from: 'db' for local database (default), 'api' for Okta API",
    )
    get_parser.set_defaults(func=handle_get_user)

    # USERS UPDATE SUBCOMMAND
    update_parser = users_subparser.add_parser(
        "update",
        help="Update user profile",
        description="Update a user's profile in both Okta and the local database",
    )
    update_parser.add_argument(
        "--id",
        type=str,
        required=True,
        help="User ID to update",
    )
    update_parser.add_argument(
        "--profile",
        type=str,
        required=True,
        help='Profile data as JSON string (e.g., \'{"firstName": "John", "lastName": "Doe"}\')',
    )
    update_parser.set_defaults(func=handle_update_user)

    # USERS DELETE SUBCOMMAND
    delete_parser = users_subparser.add_parser(
        "delete",
        help="Delete a user",
        description="Delete a user from both Okta and the local database",
    )
    delete_group = delete_parser.add_mutually_exclusive_group(required=True)
    delete_group.add_argument(
        "--id",
        type=str,
        help="User ID to delete",
    )
    delete_group.add_argument(
        "--email",
        type=str,
        help="User email to delete",
    )
    delete_parser.set_defaults(func=handle_delete_user)

    # USERS RESET PASSWORD SUBCOMMAND
    reset_password_group = users_subparser.add_parser(
        "reset-password", help="User to reset password for"
    )
    reset_password_group.add_argument(
        "--id", type=str, help="The okta id for the user to reset password for"
    )
    reset_password_group.set_defaults(func=handle_password_reset)

    # Parse arguments
    args = parser.parse_args()

    # Setup logging
    setup_logging(verbose=args.verbose)

    # Execute command
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            raise
        sys.exit(1)


if __name__ == "__main__":
    main()
