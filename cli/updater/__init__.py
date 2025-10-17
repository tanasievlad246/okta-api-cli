"""
Update management module for the Okta CLI.

Handles checking for updates from GitHub and self-updating the CLI tool.
"""

from .version_checker import check_for_updates, get_current_version, get_latest_version
from .installer import install_update
from .commands import handle_update_command, check_for_updates_on_startup

__all__ = [
    "check_for_updates",
    "get_current_version",
    "get_latest_version",
    "install_update",
    "handle_update_command",
    "check_for_updates_on_startup",
]
