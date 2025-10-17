"""
Configuration management for the updater module.

Handles reading and writing update-related settings.
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Use XDG Base Directory specification
CONFIG_DIR = os.path.join(
    os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")),
    "okta-cli",
)
UPDATE_CONFIG_PATH = os.path.join(CONFIG_DIR, "update_config.json")

# Default configuration
DEFAULT_UPDATE_CONFIG = {
    "auto_check_updates": True,
    "update_check_interval": 86400,  # 24 hours in seconds
    "last_update_check": None,
}


def get_update_config() -> Dict[str, Any]:
    """
    Retrieves the update configuration.

    Returns:
        Dict[str, Any]: Update configuration dictionary
    """
    try:
        if os.path.exists(UPDATE_CONFIG_PATH):
            with open(UPDATE_CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
                # Merge with defaults to ensure all keys exist
                return {**DEFAULT_UPDATE_CONFIG, **config}
        else:
            logger.debug("Update config not found, using defaults")
            return DEFAULT_UPDATE_CONFIG.copy()

    except Exception as e:
        logger.warning(f"Failed to read update config: {e}. Using defaults.")
        return DEFAULT_UPDATE_CONFIG.copy()


def save_update_config(config: Dict[str, Any]) -> None:
    """
    Saves the update configuration.

    Args:
        config: Configuration dictionary to save
    """
    try:
        # Ensure config directory exists
        os.makedirs(CONFIG_DIR, mode=0o700, exist_ok=True)

        # Write config file with UTF-8 encoding
        with open(UPDATE_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        logger.debug(f"Update config saved to {UPDATE_CONFIG_PATH}")

    except Exception as e:
        logger.error(f"Failed to save update config: {e}")


def save_last_check_time() -> None:
    """
    Updates the last update check timestamp to now (UTC).
    """
    try:
        config = get_update_config()
        config["last_update_check"] = datetime.now(timezone.utc).isoformat()
        save_update_config(config)

    except Exception as e:
        logger.warning(f"Failed to save last check time: {e}")


def set_auto_check_updates(enabled: bool) -> None:
    """
    Enables or disables automatic update checking.

    Args:
        enabled: True to enable auto-check, False to disable
    """
    try:
        config = get_update_config()
        config["auto_check_updates"] = enabled
        save_update_config(config)
        logger.info(f"Auto-check updates {'enabled' if enabled else 'disabled'}")

    except Exception as e:
        logger.error(f"Failed to set auto-check updates: {e}")


def set_check_interval(seconds: int) -> None:
    """
    Sets the interval between automatic update checks.

    Args:
        seconds: Number of seconds between checks
    """
    try:
        if seconds < 0:
            raise ValueError("Interval must be non-negative")

        config = get_update_config()
        config["update_check_interval"] = seconds
        save_update_config(config)
        logger.info(f"Update check interval set to {seconds} seconds")

    except Exception as e:
        logger.error(f"Failed to set check interval: {e}")
