"""Module: adminApiGoogleDriveRoutes.py

Description:
    Admin API endpoints for managing Google Drive folder backup checks.

    Google Drive folders are configuration-driven via config's
    `googleDrive.foldersToCheck`.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Header, Query

import configFileManager as ConfigFileManager
import databaseWrapper as DatabaseWrapper
from adminApiCommon import GoogleDriveFolderRequest, NameRequest, ensure_list, pydantic_model_to_dict, require_admin_auth


router = APIRouter(prefix="/v1/admin", tags=["admin"])


@router.get("/google-drive/folders")
def admin_list_google_drive_folders(
    server_auth_token: Optional[str] = Query(default=None),
    x_server_authentication_token: Optional[str] = Header(
        default=None,
        alias="X-Server-Authentication-Token",
    ),
) -> Dict[str, Any]:
    """List configured Google Drive folder checks.

    Args:
        server_auth_token (Optional[str]): Token provided as query parameter.
        x_server_authentication_token (Optional[str]): Token provided as header.

    Returns:
        Dict[str, Any]: Folder checks.
    """

    require_admin_auth(server_auth_token, x_server_authentication_token)

    cfg = ConfigFileManager.load_config()
    folders = []
    if "googleDrive" in cfg:
        folders = ensure_list(cfg.get("googleDrive", {}).get("foldersToCheck"))

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
    """Add or update a Google Drive folder check configuration.

    If a folder with the same name already exists, it will be replaced.

    Args:
        request (GoogleDriveFolderRequest): Folder definition.
        server_auth_token (Optional[str]): Token provided as query parameter.
        x_server_authentication_token (Optional[str]): Token provided as header.

    Returns:
        Dict[str, Any]: Updated foldersToCheck list.
    """

    require_admin_auth(server_auth_token, x_server_authentication_token)

    folder_dict = pydantic_model_to_dict(request)

    def _update(cfg: Dict[str, Any]) -> Dict[str, Any]:
        google_drive = cfg.setdefault("googleDrive", {})
        folders = ensure_list(google_drive.get("foldersToCheck"))
        folders = [f for f in folders if isinstance(f, dict) and f.get("name") != folder_dict.get("name")]
        folders.append(folder_dict)
        google_drive["foldersToCheck"] = folders
        return cfg

    updated = ConfigFileManager.update_config(_update)
    return {"foldersToCheck": updated.get("googleDrive", {}).get("foldersToCheck", [])}


@router.delete("/google-drive/folders")
def admin_remove_google_drive_folder(
    request: NameRequest = Body(...),
    server_auth_token: Optional[str] = Query(default=None),
    x_server_authentication_token: Optional[str] = Header(
        default=None,
        alias="X-Server-Authentication-Token",
    ),
) -> Dict[str, Any]:
    """Remove a Google Drive folder check configuration by name.

    Also deletes any matching backup entry from the database to avoid stale alerts.

    Args:
        request (NameRequest): Folder name.
        server_auth_token (Optional[str]): Token provided as query parameter.
        x_server_authentication_token (Optional[str]): Token provided as header.

    Returns:
        Dict[str, Any]: Updated foldersToCheck list.
    """

    require_admin_auth(server_auth_token, x_server_authentication_token)

    name = request.name

    def _update(cfg: Dict[str, Any]) -> Dict[str, Any]:
        google_drive = cfg.setdefault("googleDrive", {})
        folders = ensure_list(google_drive.get("foldersToCheck"))
        google_drive["foldersToCheck"] = [f for f in folders if not (isinstance(f, dict) and f.get("name") == name)]
        return cfg

    updated = ConfigFileManager.update_config(_update)

    try:
        db = DatabaseWrapper.DatabaseWrapper()
        db.deleteBackupCheckByName(name)
    except Exception:
        pass

    return {"foldersToCheck": updated.get("googleDrive", {}).get("foldersToCheck", [])}
