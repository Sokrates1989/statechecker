"""Module: adminApiGoogleDriveRoutes.py

Description:
    Admin API endpoints for managing Google Drive folder backup checks.

    Google Drive folders are configuration-driven via config's
    `googleDrive.foldersToCheck`.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, Header, Query, Request
from fastapi.security import HTTPAuthorizationCredentials

import database_config_manager as DbConfig
import databaseWrapper as DatabaseWrapper
from adminApiCommon import GoogleDriveFolderRequest, NameRequest, require_read_access, require_write_access
from adminApiCommon import bearer_scheme

router = APIRouter(prefix="/v1/admin", tags=["admin"])


@router.get("/google-drive/folders")
async def admin_list_google_drive_folders(
    request: Request,
    server_auth_token: Optional[str] = Query(default=None),
    x_server_authentication_token: Optional[str] = Header(
        default=None,
        alias="X-Server-Authentication-Token",
    ),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
):
    """List configured Google Drive folder checks.

    Args:
        request: FastAPI request object.
        server_auth_token (Optional[str]): Token provided as query parameter.
        x_server_authentication_token (Optional[str]): Token provided as header.
        credentials: Bearer token credentials.

    Returns:
        Dict[str, Any]: Folder checks.
    """

    await require_read_access(request, server_auth_token, x_server_authentication_token, credentials)

    folders = DbConfig.get_google_drive_folders()
    return {"foldersToCheck": folders}


@router.post("/google-drive/folders")
async def admin_add_google_drive_folder(
    request: Request,
    body: GoogleDriveFolderRequest,
    server_auth_token: Optional[str] = Query(default=None),
    x_server_authentication_token: Optional[str] = Header(
        default=None,
        alias="X-Server-Authentication-Token",
    ),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
):
    """Add a Google Drive folder to the foldersToCheck list.

    Args:
        request: FastAPI request object.
        body (GoogleDriveFolderRequest): Folder details.
        server_auth_token (Optional[str]): Token provided as query parameter.
        x_server_authentication_token (Optional[str]): Token provided as header.
        credentials: Bearer token credentials.

    Returns:
        Dict[str, Any]: Updated foldersToCheck list.
    """

    await require_write_access(request, server_auth_token, x_server_authentication_token, credentials)

    DbConfig.add_google_drive_folder(
        name=body.name,
        folder_id=body.folderID,
        description=body.description or "",
        frequency_minutes=body.stateCheckFrequency_inMinutes or 1440
    )

    return {"foldersToCheck": DbConfig.get_google_drive_folders()}


@router.delete("/google-drive/folders")
async def admin_remove_google_drive_folder(
    request: Request,
    body: NameRequest = Body(...),
    server_auth_token: Optional[str] = Query(default=None),
    x_server_authentication_token: Optional[str] = Header(
        default=None,
        alias="X-Server-Authentication-Token",
    ),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
):
    """Remove a Google Drive folder from the foldersToCheck list.

    Args:
        request: FastAPI request object.
        body (NameRequest): Folder name.
        server_auth_token (Optional[str]): Token provided as query parameter.
        x_server_authentication_token (Optional[str]): Token provided as header.
        credentials: Bearer token credentials.

    Returns:
        Dict[str, Any]: Updated foldersToCheck list.
    """

    await require_write_access(request, server_auth_token, x_server_authentication_token, credentials)

    name = body.name

    # Remove from config database
    DbConfig.remove_google_drive_folder(name)

    # Remove check results from database
    try:
        db = DatabaseWrapper.DatabaseWrapper()
        db.deleteBackupCheckByName(name)
    except Exception:
        pass

    return {"foldersToCheck": DbConfig.get_google_drive_folders()}
