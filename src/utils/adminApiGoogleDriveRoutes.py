"""Module: adminApiGoogleDriveRoutes.py

Description:
    Admin API endpoints for managing Google Drive folder backup checks.

    Google Drive folders are configuration-driven via config's
    `googleDrive.foldersToCheck`.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Header, Query

import database_config_manager as DbConfig
import databaseWrapper as DatabaseWrapper
from adminApiCommon import GoogleDriveFolderRequest, NameRequest, require_admin_auth_readonly


router = APIRouter(prefix="/v1/admin", tags=["admin"])


@router.get("/google-drive/folders")
def admin_list_google_drive_folders(
    server_auth_token: Optional[str] = Query(default=None),
    x_server_authentication_token: Optional[str] = Header(
        default=None,
        alias="X-Server-Authentication-Token",
    ),
) -> Dict[str, Any]:
    """List configured Google Drive folder checks from database.

    Args:
        server_auth_token (Optional[str]): Token provided as query parameter.
        x_server_authentication_token (Optional[str]): Token provided as header.

    Returns:
        Dict[str, Any]: Folder checks.
    """

    require_admin_auth_readonly(server_auth_token, x_server_authentication_token)

    folders = DbConfig.get_google_drive_folders()
    return {"foldersToCheck": folders}


@router.post("/google-drive/folders")
def admin_add_google_drive_folder(
    request: GoogleDriveFolderRequest,
    server_auth_token: Optional[str] = Query(default=None),
    x_server_authentication_token: Optional[str] = Header(
        default=None,
        alias="X-Server-Authentication-Token",
    ),
) -> Dict[str, Any]:
    """Add or update a Google Drive folder check configuration in database.

    If a folder with the same name already exists, it will be replaced.

    Args:
        request (GoogleDriveFolderRequest): Folder definition.
        server_auth_token (Optional[str]): Token provided as query parameter.
        x_server_authentication_token (Optional[str]): Token provided as header.

    Returns:
        Dict[str, Any]: Updated foldersToCheck list.
    """

    require_admin_auth_readonly(server_auth_token, x_server_authentication_token)

    DbConfig.add_google_drive_folder(
        name=request.name,
        folder_id=request.folderID,
        description=request.description or "",
        frequency_minutes=request.stateCheckFrequency_inMinutes or 1440
    )

    return {"foldersToCheck": DbConfig.get_google_drive_folders()}


@router.delete("/google-drive/folders")
def admin_remove_google_drive_folder(
    request: NameRequest = Body(...),
    server_auth_token: Optional[str] = Query(default=None),
    x_server_authentication_token: Optional[str] = Header(
        default=None,
        alias="X-Server-Authentication-Token",
    ),
) -> Dict[str, Any]:
    """Remove a Google Drive folder check configuration from database.

    Also deletes any matching backup entry from the database to avoid stale alerts.

    Args:
        request (NameRequest): Folder name.
        server_auth_token (Optional[str]): Token provided as query parameter.
        x_server_authentication_token (Optional[str]): Token provided as header.

    Returns:
        Dict[str, Any]: Updated foldersToCheck list.
    """

    require_admin_auth_readonly(server_auth_token, x_server_authentication_token)

    name = request.name

    # Remove from config database
    DbConfig.remove_google_drive_folder(name)

    # Remove check results from database
    try:
        db = DatabaseWrapper.DatabaseWrapper()
        db.deleteBackupCheckByName(name)
    except Exception:
        pass

    return {"foldersToCheck": DbConfig.get_google_drive_folders()}
