"""
Installation module for the Okta CLI updater.

Handles downloading and installing updates.
"""

import logging
import subprocess
import shutil
from typing import Optional

from ..exceptions import InstallationError

logger = logging.getLogger(__name__)

# Package and repository constants
PACKAGE_NAME = "okta-api-cli"
GITHUB_REPO = "tanasievlad246/okta-api-cli"
SUBPROCESS_TIMEOUT = 300  # 5 minutes for install operations


def detect_installer() -> Optional[str]:
    """
    Detects which package manager was used to install the CLI.

    Returns:
        Optional[str]: Name of installer ("uv", "pipx", "pip") or None if not found
    """
    # Check if installed via uv
    if shutil.which("uv"):
        try:
            result = subprocess.run(
                ["uv", "tool", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0 and PACKAGE_NAME in result.stdout:
                logger.debug("CLI installed via uv")
                return "uv"
        except (subprocess.TimeoutExpired, Exception) as e:
            logger.debug(f"Failed to check uv: {e}")

    # Check if installed via pipx
    if shutil.which("pipx"):
        try:
            result = subprocess.run(
                ["pipx", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0 and PACKAGE_NAME in result.stdout:
                logger.debug("CLI installed via pipx")
                return "pipx"
        except (subprocess.TimeoutExpired, Exception) as e:
            logger.debug(f"Failed to check pipx: {e}")

    # Check if installed via pip
    if shutil.which("pip"):
        try:
            result = subprocess.run(
                ["pip", "show", PACKAGE_NAME],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                logger.debug("CLI installed via pip")
                return "pip"
        except (subprocess.TimeoutExpired, Exception) as e:
            logger.debug(f"Failed to check pip: {e}")

    logger.warning("Could not detect package installer")
    return None


def install_update() -> None:
    """
    Downloads and installs the latest version of the CLI.

    Raises:
        InstallationError: If installation fails
    """
    installer = detect_installer()

    if not installer:
        raise InstallationError(
            "Could not detect package manager. Please install manually using:\n"
            f"  pip install --upgrade git+https://github.com/{GITHUB_REPO}.git"
        )

    try:
        logger.info(f"Installing update using {installer}...")

        if installer == "uv":
            _install_with_uv()
        elif installer == "pipx":
            _install_with_pipx()
        elif installer == "pip":
            _install_with_pip()

        logger.info("Update installed successfully")

    except subprocess.CalledProcessError as e:
        logger.error(f"Installation failed: {e}")
        raise InstallationError(f"Failed to install update: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during installation: {e}")
        raise InstallationError(f"Unexpected error: {e}")


def _install_with_uv() -> None:
    """
    Installs the update using uv.

    Raises:
        subprocess.CalledProcessError: If installation fails
    """
    github_url = f"git+https://github.com/{GITHUB_REPO}.git"

    # First, uninstall the current version
    try:
        subprocess.run(
            ["uv", "tool", "uninstall", PACKAGE_NAME],
            check=True,
            capture_output=True,
            text=True,
            timeout=60
        )
    except subprocess.CalledProcessError:
        # If uninstall fails, it might not be installed as a tool, continue anyway
        logger.debug("Could not uninstall with uv tool, may not be installed as tool")
    except subprocess.TimeoutExpired:
        logger.warning("Uninstall timed out, continuing with install")

    # Install the new version
    subprocess.run(
        ["uv", "tool", "install", github_url],
        check=True,
        capture_output=True,
        text=True,
        timeout=SUBPROCESS_TIMEOUT
    )


def _install_with_pipx() -> None:
    """
    Installs the update using pipx.

    Raises:
        subprocess.CalledProcessError: If installation fails
    """
    github_url = f"git+https://github.com/{GITHUB_REPO}.git"

    # pipx supports upgrade command
    result = subprocess.run(
        ["pipx", "upgrade", PACKAGE_NAME],
        capture_output=True,
        text=True,
        timeout=SUBPROCESS_TIMEOUT
    )

    # If upgrade fails (package not installed with pipx), try install
    if result.returncode != 0:
        subprocess.run(
            ["pipx", "install", github_url, "--force"],
            check=True,
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT
        )


def _install_with_pip() -> None:
    """
    Installs the update using pip.

    Raises:
        subprocess.CalledProcessError: If installation fails
    """
    github_url = f"git+https://github.com/{GITHUB_REPO}.git"

    subprocess.run(
        ["pip", "install", "--upgrade", github_url],
        check=True,
        capture_output=True,
        text=True,
        timeout=SUBPROCESS_TIMEOUT
    )


def get_rollback_instructions() -> str:
    """
    Provides instructions for rolling back to a previous version.

    Returns:
        str: Rollback instructions
    """
    return (
        "To rollback to a previous version:\n"
        "  1. Uninstall the current version:\n"
        "     uv tool uninstall okta-api-cli\n"
        "     # or: pipx uninstall okta-api-cli\n"
        "     # or: pip uninstall okta-api-cli\n\n"
        "  2. Install the desired version:\n"
        f"     git clone https://github.com/{GITHUB_REPO}.git\n"
        "     cd okta-api-cli\n"
        "     git checkout <version-tag>\n"
        "     uv tool install .\n"
        "     # or: pipx install .\n"
        "     # or: pip install ."
    )
