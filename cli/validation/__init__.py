from pydantic import BaseModel, Field, HttpUrl, EmailStr, ValidationError
from typing import Optional
from datetime import datetime


class ConfigModel(BaseModel):
    """Configuration model for Okta API credentials."""

    api_key: str
    app_url: HttpUrl


class UserQueryModel(BaseModel):
    """Model for user query parameters."""

    id: str | None = None
    email: EmailStr | None = None


class OktaUserType(BaseModel):
    """Okta user type reference."""

    id: str


class OktaCredentialsProvider(BaseModel):
    """Okta credentials provider information."""

    type: str
    name: str


class OktaCredentials(BaseModel):
    """Okta user credentials."""

    provider: OktaCredentialsProvider


class OktaUserProfile(BaseModel):
    """
    Okta user profile data.

    Contains all profile fields from the Okta User API.
    """

    reportGroupList: Optional[str] = None
    firstName: str
    lastName: str
    mobilePhone: Optional[str] = None
    placementOrg: Optional[str] = None
    portalAccessGroup: Optional[str] = None
    secondEmail: Optional[str] = None
    login: EmailStr
    email: EmailStr
    ackNewBusiness: Optional[int] = None

    class Config:
        """Pydantic config."""

        # Allow extra fields that might come from Okta
        extra = "allow"


class OktaUserResponse(BaseModel):
    """
    Complete Okta user API response.

    Based on the Okta Users API v1 schema.
    """

    id: str
    status: str
    created: Optional[str] = None
    activated: Optional[str] = None
    statusChanged: Optional[str] = None
    lastLogin: Optional[str] = None
    lastUpdated: str
    passwordChanged: Optional[str] = None
    type: OktaUserType
    profile: OktaUserProfile
    credentials: Optional[OktaCredentials] = None

    class Config:
        """Pydantic config."""

        # Allow extra fields like _links that we don't use
        extra = "allow"


__all__ = [
    "ConfigModel",
    "UserQueryModel",
    "OktaUserType",
    "OktaCredentialsProvider",
    "OktaCredentials",
    "OktaUserProfile",
    "OktaUserResponse",
    "ValidationError",
]
