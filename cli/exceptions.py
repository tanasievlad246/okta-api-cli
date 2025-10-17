"""
Custom exceptions for the Okta CLI application.
"""


class OktaCliException(Exception):
    """Base exception for Okta CLI errors."""

    pass


class ConfigurationError(OktaCliException):
    """Raised when configuration is invalid or missing."""

    pass


class UserNotFoundError(OktaCliException):
    """Raised when a user cannot be found."""

    pass


class DatabaseError(OktaCliException):
    """Raised when a database operation fails."""

    pass


class OktaApiError(OktaCliException):
    """Raised when an Okta API request fails."""

    pass


class ValidationError(OktaCliException):
    """Raised when input validation fails."""

    pass
