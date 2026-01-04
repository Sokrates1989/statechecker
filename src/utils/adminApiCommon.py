"""Module: adminApiCommon.py

Description:
    Shared helpers for the statechecker admin API.

    This module contains authentication helpers (SERVER_AUTHENTICATION_TOKEN),
    config persistence preconditions, and small utility helpers used by the
    admin route modules.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import Header, HTTPException, Query, status
from pydantic import BaseModel, Field

import configFileManager as ConfigFileManager
import configUtils as ConfigUtils


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


def require_admin_auth(
    server_auth_token: Optional[str] = Query(default=None),
    x_server_authentication_token: Optional[str] = Header(
        default=None,
        alias="X-Server-Authentication-Token",
    ),
) -> None:
    """Validate admin access for the request.

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
