"""Module: adminApiCommon.py

Description:
    Shared helpers for the statechecker admin API.

    This module contains authentication helpers supporting both:
    - SERVER_AUTHENTICATION_TOKEN (for stateChecker-client and legacy access)
    - Keycloak JWT (for web UI when KEYCLOAK_ENABLED=true)

    Config persistence preconditions and small utility helpers used by the
    admin route modules are also included.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import Depends, Header, HTTPException, Query, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from pydantic import BaseModel, Field

import configFileManager as ConfigFileManager
import configUtils as ConfigUtils

try:
    from keycloak_auth import (
        KeycloakUser,
        get_keycloak_auth,
        get_keycloak_enabled,
        bearer_scheme,
    )
    KEYCLOAK_AVAILABLE = True
except ImportError:
    KEYCLOAK_AVAILABLE = False
    KeycloakUser = None
    get_keycloak_auth = None
    get_keycloak_enabled = lambda: False
    bearer_scheme = HTTPBearer(auto_error=False)


configUtils = ConfigUtils.ConfigUtils()


class NameRequest(BaseModel):
    """Request body containing a name field."""

    name: str = Field(..., min_length=1)


class WebsiteRequest(BaseModel):
    """Request body containing a website URL."""

    url: str = Field(..., min_length=1)


class GoogleDriveFolderRequest(BaseModel):
    """Request body for creating or updating a Google Drive folder check."""

    name: str = Field(..., min_length=1)
    description: str = ""
    folderID: str = Field(..., min_length=1)
    token: str = Field(..., min_length=1)
    stateCheckFrequency_inMinutes: int = Field(..., gt=0)


def pydantic_model_to_dict(model: BaseModel) -> Dict[str, Any]:
    """Convert a Pydantic model into a plain dict.

    This supports both Pydantic v1 (`dict`) and v2 (`model_dump`).

    Args:
        model (BaseModel): Pydantic model instance.

    Returns:
        Dict[str, Any]: Dictionary representation.
    """

    if hasattr(model, "model_dump"):
        return model.model_dump()  # type: ignore[attr-defined]
    return model.dict()


def get_request_server_auth_token(
    server_auth_token: Optional[str],
    x_server_authentication_token: Optional[str],
) -> str:
    """Resolve the server authentication token from request inputs.

    Args:
        server_auth_token (Optional[str]): Token provided as query parameter.
        x_server_authentication_token (Optional[str]): Token provided as header.

    Returns:
        str: The resolved token.

    Raises:
        HTTPException: If no token was provided.
    """

    if x_server_authentication_token and x_server_authentication_token.strip():
        return x_server_authentication_token.strip().strip('"')

    if server_auth_token and server_auth_token.strip():
        return server_auth_token.strip().strip('"')

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="missing server authentication token",
    )


def _validate_token_auth(
    server_auth_token: Optional[str],
    x_server_authentication_token: Optional[str],
) -> bool:
    """Validate using SERVER_AUTHENTICATION_TOKEN.

    Args:
        server_auth_token: Token from query param.
        x_server_authentication_token: Token from header.

    Returns:
        True if valid, raises HTTPException if provided but invalid.
    """
    try:
        token = get_request_server_auth_token(server_auth_token, x_server_authentication_token)
        if configUtils.getServerAuthenticationToken() == token:
            return True
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid server authentication token",
        )
    except HTTPException as e:
        if "missing" in str(e.detail).lower():
            return False
        raise


def _validate_keycloak_auth(
    credentials: Optional[HTTPAuthorizationCredentials],
) -> Optional[KeycloakUser]:
    """Validate using Keycloak JWT.

    Args:
        credentials: Bearer token credentials.

    Returns:
        KeycloakUser if valid, None if no credentials, raises HTTPException if invalid.
    """
    if not KEYCLOAK_AVAILABLE:
        return None
        
    if credentials is None:
        return None

    keycloak = get_keycloak_auth()
    if keycloak is None:
        return None

    return keycloak.validate_token(credentials.credentials)


async def require_admin_auth_hybrid(
    request: Request,
    server_auth_token: Optional[str] = Query(default=None),
    x_server_authentication_token: Optional[str] = Header(
        default=None,
        alias="X-Server-Authentication-Token",
    ),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[KeycloakUser]:
    """Validate admin access using either token or Keycloak JWT.

    This hybrid auth allows:
    - stateChecker-client to use X-Server-Authentication-Token
    - Web UI to use Keycloak Bearer token when KEYCLOAK_ENABLED=true

    Args:
        request: FastAPI request object.
        server_auth_token: Token from query param.
        x_server_authentication_token: Token from header.
        credentials: Bearer token credentials.

    Returns:
        KeycloakUser if authenticated via Keycloak, None if via token.

    Raises:
        HTTPException: If no valid auth provided.
    """
    # Try Keycloak first if enabled and credentials provided
    if KEYCLOAK_AVAILABLE and get_keycloak_enabled() and credentials is not None:
        user = _validate_keycloak_auth(credentials)
        if user is not None:
            return user

    # Fallback to token auth
    if _validate_token_auth(server_auth_token, x_server_authentication_token):
        return None

    # Neither auth method succeeded
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide X-Server-Authentication-Token or Bearer token.",
    )


def require_admin_auth_readonly(
    server_auth_token: Optional[str] = Query(default=None),
    x_server_authentication_token: Optional[str] = Header(
        default=None,
        alias="X-Server-Authentication-Token",
    ),
) -> None:
    """Validate admin access for read-only operations (token-only, legacy).

    This only checks the authentication token without requiring file-based config.
    Use this for GET endpoints that don't modify state.
    NOTE: For new endpoints, prefer require_admin_auth_hybrid for Keycloak support.

    Args:
        server_auth_token (Optional[str]): Token provided as query parameter.
        x_server_authentication_token (Optional[str]): Token provided as header.

    Raises:
        HTTPException: If token is missing or invalid.
    """

    token = get_request_server_auth_token(server_auth_token, x_server_authentication_token)

    if configUtils.getServerAuthenticationToken() != token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid server authentication token",
        )


def require_admin_auth(
    server_auth_token: Optional[str] = Query(default=None),
    x_server_authentication_token: Optional[str] = Header(
        default=None,
        alias="X-Server-Authentication-Token",
    ),
) -> None:
    """Validate admin access for write operations.

    This checks both the authentication token AND requires file-based config
    to be available for persisting changes.

    Args:
        server_auth_token (Optional[str]): Token provided as query parameter.
        x_server_authentication_token (Optional[str]): Token provided as header.

    Raises:
        HTTPException: If token is missing/invalid or file-based config is not available.
    """

    token = get_request_server_auth_token(server_auth_token, x_server_authentication_token)

    if configUtils.getServerAuthenticationToken() != token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid server authentication token",
        )

    if not ConfigFileManager.is_file_based_config_available():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="file-based config is not available; cannot persist admin changes",
        )


def ensure_list(value: Any) -> List[Any]:
    """Normalize a value into a list.

    Args:
        value (Any): Value to normalize.

    Returns:
        List[Any]: A list (empty if not already a list).
    """

    return value if isinstance(value, list) else []


def dedupe_preserve_order(items: List[Any]) -> List[Any]:
    """Deduplicate a list while preserving order.

    Args:
        items (List[Any]): Input list.

    Returns:
        List[Any]: Deduplicated list.
    """

    seen = set()
    out: List[Any] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out
