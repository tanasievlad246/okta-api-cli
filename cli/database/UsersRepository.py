from cli.database import database
import logging
import sqlite3
from typing import Optional, Union
from ..validation import OktaUserResponse

logger = logging.getLogger(__name__)


class UsersRepository:
    """
    Repository for managing user data in the local SQLite database.

    Handles all CRUD operations for users and user profiles.
    """

    def __init__(self) -> None:
        self.connection = database.get_db_connection()

    def create_or_update_user(self, user: Union[dict, OktaUserResponse]) -> None:
        """
        Creates a new user or updates an existing one.

        Args:
            user: User data dictionary or OktaUserResponse from Okta API

        Raises:
            sqlite3.Error: If database operation fails
        """
        # Convert Pydantic model to dict if necessary
        if isinstance(user, OktaUserResponse):
            user = user.model_dump()
        try:
            cursor = self.connection.cursor()

            # Extract user type
            user_type = user.get("type", {})
            if user_type and "id" in user_type:
                cursor.execute(
                    "INSERT OR REPLACE INTO user_types (id) VALUES (?)",
                    (user_type["id"],),
                )

            # Insert or replace user
            # Extract profile for placementOrg (it's in profile, not _embedded)
            profile = user.get("profile", {})

            cursor.execute(
                """
                INSERT OR REPLACE INTO users (
                    id, status, created, activated, statusChanged,
                    lastLogin, lastUpdated, passwordChanged, placementOrg, type_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user.get("id"),
                    user.get("status"),
                    user.get("created"),
                    user.get("activated"),
                    user.get("statusChanged"),
                    user.get("lastLogin"),
                    user.get("lastUpdated"),
                    user.get("passwordChanged"),
                    profile.get("placementOrg"),
                    user_type.get("id") if user_type else None,
                ),
            )

            # Insert or replace user profile (profile already extracted above)
            cursor.execute(
                """
                INSERT OR REPLACE INTO user_profiles (
                    user_id, reportGroupList, firstName, lastName,
                    mobilePhone, portalAccessGroup, secondEmail,
                    ackNewBusiness, login, email, placementOrg
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user.get("id"),
                    profile.get("reportGroupList"),
                    profile.get("firstName"),
                    profile.get("lastName"),
                    profile.get("mobilePhone"),
                    profile.get("portalAccessGroup"),
                    profile.get("secondEmail"),
                    profile.get("ackNewBusiness"),
                    profile.get("login"),
                    profile.get("email"),
                    profile.get("placementOrg"),
                ),
            )

            self.connection.commit()
            logger.debug(f"Upserted user: {user.get('id')}")

        except sqlite3.Error as e:
            self.connection.rollback()
            logger.error(f"Error creating/updating user: {e}")
            raise

    def get_user_by_id(self, user_id: str) -> Optional[dict]:
        """
        Retrieves a user by ID from the database.

        Args:
            user_id: The user's ID

        Returns:
            dict | None: User data with profile formatted like Okta API response, or None if not found
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT
                    u.id, u.status, u.created, u.activated, u.statusChanged,
                    u.lastLogin, u.lastUpdated, u.passwordChanged, u.type_id,
                    p.reportGroupList, p.firstName, p.lastName, p.mobilePhone,
                    p.portalAccessGroup, p.secondEmail, p.ackNewBusiness, p.login, p.email, p.placementOrg
                FROM users u
                LEFT JOIN user_profiles p ON u.id = p.user_id
                WHERE u.id = ?
                """,
                (user_id,),
            )

            row = cursor.fetchone()
            if row:
                return self._row_to_dict(row)
            return None

        except sqlite3.Error as e:
            logger.error(f"Error retrieving user by ID: {e}")
            raise

    def get_user_by_email(self, email: str) -> Optional[dict]:
        """
        Retrieves a user by email from the database.

        Args:
            email: The user's email address

        Returns:
            dict | None: User data with profile formatted like Okta API response, or None if not found
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT
                    u.id, u.status, u.created, u.activated, u.statusChanged,
                    u.lastLogin, u.lastUpdated, u.passwordChanged, u.type_id,
                    p.reportGroupList, p.firstName, p.lastName, p.mobilePhone,
                    p.portalAccessGroup, p.secondEmail, p.ackNewBusiness, p.login, p.email, p.placementOrg
                FROM users u
                LEFT JOIN user_profiles p ON u.id = p.user_id
                WHERE p.email = ?
                """,
                (email,),
            )

            row = cursor.fetchone()
            if row:
                return self._row_to_dict(row)
            return None

        except sqlite3.Error as e:
            logger.error(f"Error retrieving user by email: {e}")
            raise

    def get_all_users(self) -> list[dict]:
        """
        Retrieves all users from the database.

        Returns:
            list[dict]: List of user dictionaries formatted like Okta API responses
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT
                    u.id, u.status, u.created, u.activated, u.statusChanged,
                    u.lastLogin, u.lastUpdated, u.passwordChanged, u.type_id,
                    p.reportGroupList, p.firstName, p.lastName, p.mobilePhone,
                    p.portalAccessGroup, p.secondEmail, p.ackNewBusiness, p.login, p.email, p.placementOrg
                FROM users u
                LEFT JOIN user_profiles p ON u.id = p.user_id
                """
            )

            rows = cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]

        except sqlite3.Error as e:
            logger.error(f"Error retrieving all users: {e}")
            raise

    def update_user_profile(self, user_id: str, profile: dict) -> None:
        """
        Updates a user's profile fields.

        Args:
            user_id: The user's ID
            profile: Dictionary of profile fields to update

        Raises:
            sqlite3.Error: If update fails
        """
        try:
            cursor = self.connection.cursor()

            # Build dynamic UPDATE query based on provided fields
            fields = []
            values = []

            allowed_fields = [
                "reportGroupList",
                "firstName",
                "lastName",
                "mobilePhone",
                "portalAccessGroup",
                "secondEmail",
                "ackNewBusiness",
                "login",
                "email",
                "placementOrg",
            ]

            for field in allowed_fields:
                if field in profile:
                    fields.append(f"{field} = ?")
                    values.append(profile[field])

            if not fields:
                logger.warning(f"No valid fields to update for user {user_id}")
                return

            values.append(user_id)
            query = f"UPDATE user_profiles SET {', '.join(fields)} WHERE user_id = ?"

            cursor.execute(query, values)
            self.connection.commit()

            logger.info(f"Updated profile for user: {user_id}")

        except sqlite3.Error as e:
            self.connection.rollback()
            logger.error(f"Error updating user profile: {e}")
            raise

    def delete_user(self, user_id: str) -> None:
        """
        Deletes a user from the database.

        Args:
            user_id: The user's ID

        Raises:
            sqlite3.Error: If deletion fails
        """
        try:
            cursor = self.connection.cursor()

            # Delete from user_profiles first (foreign key constraint)
            cursor.execute("DELETE FROM user_profiles WHERE user_id = ?", (user_id,))

            # Delete from users
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))

            self.connection.commit()
            logger.info(f"Deleted user: {user_id}")

        except sqlite3.Error as e:
            self.connection.rollback()
            logger.error(f"Error deleting user: {e}")
            raise

    def _row_to_dict(self, row: sqlite3.Row) -> dict:
        """
        Converts a database row to a user dictionary.

        Args:
            row: SQLite Row object

        Returns:
            dict: User data formatted like Okta API response
        """
        return {
            "id": row["id"],
            "status": row["status"],
            "created": row["created"],
            "activated": row["activated"],
            "statusChanged": row["statusChanged"],
            "lastLogin": row["lastLogin"],
            "lastUpdated": row["lastUpdated"],
            "passwordChanged": row["passwordChanged"],
            "type": {"id": row["type_id"]} if row["type_id"] else None,
            "profile": {
                "reportGroupList": row["reportGroupList"],
                "firstName": row["firstName"],
                "lastName": row["lastName"],
                "mobilePhone": row["mobilePhone"],
                "portalAccessGroup": row["portalAccessGroup"],
                "secondEmail": row["secondEmail"],
                "ackNewBusiness": row["ackNewBusiness"],
                "login": row["login"],
                "email": row["email"],
                "placementOrg": row["placementOrg"],
            },
        }
