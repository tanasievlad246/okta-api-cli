from .RequestClient import HttpRequestClient
from typing import Callable, Any
from ..validation import OktaUserResponse
import logging

logger = logging.getLogger(__name__)


class OktaApi:
    """
    Main Okta API client.

    Provides access to various Okta API resources.
    """

    def __init__(self, api_key: str, api_url: str):
        self.api_key = api_key
        self.api_url = api_url
        self.request_client = HttpRequestClient(
            base_url=api_url,
            base_headers={"Authorization": f"SSWS {api_key}"},
        )

    def get_users_client(self) -> "OktaUsers":
        """Returns the users API client."""
        return OktaUsers(self.request_client)


class OktaUsers:
    """
    Okta Users API client.

    Handles all user-related operations in Okta.
    """

    def __init__(self, request_client: HttpRequestClient) -> None:
        self.request_client = request_client
        self.base_path = "api/v1/users"

    def get_users(self, cb: Callable | None = None) -> list[dict]:
        """
        Retrieves all users from Okta with automatic pagination.

        Args:
            cb: Optional callback function called with accumulated results

        Returns:
            list[dict]: All users from Okta (dict format for compatibility)
        """
        logger.info("Fetching all users from Okta")
        users = self.request_client.get(self.base_path, cb=cb)
        logger.info(f"Retrieved {len(users)} users from Okta")
        return users

    def get_user_by_id(self, user_id: str) -> dict | None:
        """
        Retrieves a single user by ID.

        Args:
            user_id: The Okta user ID

        Returns:
            dict | None: User data or None if not found

        Raises:
            requests.HTTPError: If user not found or request fails
        """
        logger.info(f"Fetching user by ID: {user_id}")
        path = f"{self.base_path}/{user_id}"
        users = self.request_client.get(path)
        return users[0] if users else None

    def get_user_by_email(self, email: str) -> dict | None:
        """
        Retrieves a single user by email address.

        Args:
            email: The user's email address

        Returns:
            dict | None: User data or None if not found
        """
        logger.info(f"Fetching user by email: {email}")
        users = self.request_client.get(
            self.base_path, params={"filter": f'profile.email eq "{email}"'}
        )
        return users[0] if users else None

    def update_user(self, user_id: str, profile: dict) -> dict:
        """
        Updates a user's profile.

        Args:
            user_id: The Okta user ID
            profile: Dictionary containing profile fields to update

        Returns:
            dict: Updated user data

        Raises:
            requests.HTTPError: If update fails
        """
        logger.info(f"Updating user profile for user ID: {user_id}")
        path = f"{self.base_path}/{user_id}"
        print(profile)
        data = {"profile": profile}
        return self.request_client.post(path, data=data)

    def delete_user(self, user_id: str) -> None:
        """
        Deletes a user from Okta.

        Args:
            user_id: The Okta user ID

        Raises:
            requests.HTTPError: If deletion fails
        """
        logger.info(f"Deleting user with ID: {user_id}")
        path = f"{self.base_path}/{user_id}"
        self.request_client.delete(path)

    def reset_user_password(self, user_id: str) -> dict:
        """
        Resets a given users password and sends an email to that user for the password reset_user_password

        Args:
            user_id: The Okta user ID

        Returns:
            dict: Password reset information with a summary and password reset url
            {
                "summary": "Reset password without sending email",
                "resetPasswordUrl": "https://{yourOktaDomain}/reset_password/XE6wE17zmphl3KqAPFxO"
            }
        Raises:
            requests.HTTPError: If the reset fails
        """
        logger.info(f"Reseting password for user with id {user_id}")
        path = f"{self.base_path}/{user_id}/lifecycle/reset_password?sendEmail=true"
        r = self.request_client.post(path=path)
        logger.info(r)
        return r.json()

    @staticmethod
    def validate_user_response(user_data: dict) -> OktaUserResponse:
        """
        Validates and parses a user response from Okta API using Pydantic.

        Args:
            user_data: Raw user data dictionary from API

        Returns:
            OktaUserResponse: Validated user response

        Raises:
            ValidationError: If the response doesn't match the expected schema
        """
        return OktaUserResponse(**user_data)
