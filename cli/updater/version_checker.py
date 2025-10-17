"""
Version checking module for the Okta CLI.

Handles checking for new versions from GitHub releases.
"""

import logging
import requests
from typing import Optional, Tuple
from datetime import datetime, timedelta, timezone
import cli

from ..exceptions import UpdateCheckError
from .config import get_update_config, save_last_check_time

logger = logging.getLogger(__name__)

# GitHub API configuration
GITHUB_REPO = "tanasievlad246/okta-api-cli"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
REQUEST_TIMEOUT = 10  # seconds


def get_current_version() -> str:
    """
    Gets the current version of the CLI.

    Returns:
        str: Current version string (e.g., "0.1.0")
    """
    return cli.__version__


def get_latest_version() -> Tuple[str, str]:
    """
    Fetches the latest version from GitHub releases.

    Returns:
        Tuple[str, str]: Latest version tag and download URL

    Raises:
        UpdateCheckError: If unable to fetch version from GitHub
    """
    try:
        logger.debug(f"Fetching latest version from {GITHUB_API_URL}")

        response = requests.get(
            GITHUB_API_URL,
            timeout=REQUEST_TIMEOUT,
            headers={"Accept": "application/vnd.github+json"}
        )
        response.raise_for_status()

        data = response.json()
        tag_name = data.get("tag_name", "").lstrip("v")  # Remove 'v' prefix if present
        html_url = data.get("html_url", "")

        if not tag_name:
            raise UpdateCheckError("Could not parse version from GitHub response")

        logger.debug(f"Latest version found: {tag_name}")
        return tag_name, html_url

    except requests.Timeout:
        logger.warning("GitHub API request timed out")
        raise UpdateCheckError("Request to GitHub timed out. Please check your internet connection.")
    except requests.RequestException as e:
        logger.warning(f"Failed to fetch latest version: {e}")
        raise UpdateCheckError(f"Failed to check for updates: {e}")
    except (KeyError, ValueError) as e:
        logger.error(f"Failed to parse GitHub response: {e}")
        raise UpdateCheckError("Failed to parse version information from GitHub")


def compare_versions(current: str, latest: str) -> int:
    """
    Compares two semantic version strings.

    Args:
        current: Current version string (e.g., "0.1.0")
        latest: Latest version string (e.g., "0.2.0")

    Returns:
        int: -1 if current < latest, 0 if equal, 1 if current > latest
    """
    try:
        current_parts = [int(x) for x in current.split(".")]
        latest_parts = [int(x) for x in latest.split(".")]

        # Pad with zeros if needed to compare same length
        max_len = max(len(current_parts), len(latest_parts))
        current_parts.extend([0] * (max_len - len(current_parts)))
        latest_parts.extend([0] * (max_len - len(latest_parts)))

        if current_parts < latest_parts:
            return -1
        elif current_parts > latest_parts:
            return 1
        else:
            return 0

    except (ValueError, AttributeError) as e:
        logger.error(f"Failed to compare versions: {e}")
        return 0  # Assume equal if we can't parse


def should_check_for_updates(force: bool = False) -> bool:
    """
    Determines if we should check for updates based on cooldown period.

    Args:
        force: If True, ignore cooldown period

    Returns:
        bool: True if should check, False otherwise
    """
    if force:
        return True

    try:
        config = get_update_config()

        # Check if auto-check is disabled
        if not config.get("auto_check_updates", True):
            logger.debug("Auto-check for updates is disabled")
            return False

        last_check = config.get("last_update_check")
        if not last_check:
            # Never checked before
            return True

        # Parse last check time
        last_check_time = datetime.fromisoformat(last_check)
        # Ensure timezone-aware comparison
        if last_check_time.tzinfo is None:
            last_check_time = last_check_time.replace(tzinfo=timezone.utc)

        check_interval = config.get("update_check_interval", 86400)  # Default 24 hours
        next_check_time = last_check_time + timedelta(seconds=check_interval)

        # Use timezone-aware current time
        now = datetime.now(timezone.utc)
        should_check = now >= next_check_time

        if not should_check:
            logger.debug(f"Skipping update check. Next check at: {next_check_time}")

        return should_check

    except Exception as e:
        logger.debug(f"Error checking update cooldown: {e}. Allowing check.")
        return True  # If we can't determine, allow the check


def check_for_updates(force: bool = False) -> Optional[Tuple[str, str]]:
    """
    Checks if a new version is available.

    Args:
        force: If True, force check even within cooldown period

    Returns:
        Optional[Tuple[str, str]]: (latest_version, download_url) if update available, None otherwise

    Raises:
        UpdateCheckError: If unable to check for updates
    """
    try:
        if not should_check_for_updates(force):
            return None

        current_version = get_current_version()
        latest_version, download_url = get_latest_version()

        # Save check timestamp
        save_last_check_time()

        comparison = compare_versions(current_version, latest_version)

        if comparison < 0:
            logger.info(f"Update available: {current_version} -> {latest_version}")
            return (latest_version, download_url)
        elif comparison > 0:
            logger.debug(f"Current version ({current_version}) is newer than latest release ({latest_version})")
        else:
            logger.debug(f"Already on latest version: {current_version}")

        return None

    except UpdateCheckError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error checking for updates: {e}")
        raise UpdateCheckError(f"Unexpected error: {e}")
