from ..validation import ConfigModel
import json
import os
import logging

# Use XDG Base Directory specification or fall back to home directory
CONFIG_DIR = os.path.join(
    os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")),
    "okta-cli",
)
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

logger = logging.getLogger(__name__)


def config_machine(args):
    """
    Configures the Okta API credentials for the current machine.

    Args:
        args: Command line arguments containing okta_api_key and okta_org_url
    """
    try:
        config = ConfigModel(
            api_key=args.okta_api_key,
            app_url=args.okta_org_url,
        )

        # Save the configuration to file
        create_local_config(str(config.app_url), config.api_key)

        print(f"✓ Configuration saved successfully to {CONFIG_PATH}")

    except Exception as e:
        print(f"✗ Invalid configuration: {e}")
        return


def get_local_config() -> ConfigModel:
    """
    Retrieves the local configuration from the config file.

    Returns:
        ConfigModel: The validated configuration

    Raises:
        Exception: If config file is not found
    """
    try:
        with open(CONFIG_PATH, "r") as f:
            local_config = json.load(f)
            return ConfigModel(**local_config)
    except FileNotFoundError:
        logger.error("Config file not found")
        raise Exception(
            "API url and API key are not configured, please run: okta config --okta-api-key <key> --okta-org-url <url>"
        )
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        raise Exception(f"Failed to load configuration: {e}")


def create_local_config(api_url: str, api_key: str) -> dict:
    """
    Creates and saves the local configuration file with secure permissions.

    Args:
        api_url: The Okta organization URL
        api_key: The Okta API key

    Returns:
        dict: The configuration dictionary

    Raises:
        Exception: If unable to write config file
    """
    try:
        config = {"api_key": api_key, "app_url": api_url}

        # Ensure config directory exists
        os.makedirs(CONFIG_DIR, mode=0o700, exist_ok=True)

        # Create config file with secure permissions (owner read/write only)
        fd = os.open(CONFIG_PATH, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump(config, f, indent=2)

        return config

    except Exception as e:
        logger.error(f"Could not write config file: {e}")
        raise Exception(f"Failed to save configuration: {e}")
