from .OktaApi import OktaApi
from ..config import get_local_config


def get_okta_client() -> OktaApi:
    """
    Returns an initialized Okta API client using local configuration.

    Returns:
        OktaApi: Configured Okta API client

    Raises:
        Exception: If configuration is not found
    """
    local_config = get_local_config()
    return OktaApi(api_key=local_config.api_key, api_url=str(local_config.app_url))


__all__ = ["OktaApi", "get_okta_client"]
