"""Module: adminApiBackupsRoutes.py

Description:
    Admin API endpoints for managing watched backups.

    "Unwatch" for backups is intentionally non-sticky for client-reported backups:
    the backup is deleted from the database and will re-appear if the client
    sends a new /v1/backupcheck ping.

    For Google Drive folder-based backups, the folder entry is removed from
    config.googleDrive.foldersToCheck to stop the server from re-creating the
    backup check.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, Header, Query, Request
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

import configUtils as ConfigUtils
import database_config_manager as DbConfig
import databaseWrapper as DatabaseWrapper
import logger as Logger
import telegramNotificationUtils
from adminApiCommon import NameRequest, require_admin_auth_hybrid, bearer_scheme


configUtils = ConfigUtils.ConfigUtils()

router = APIRouter(prefix="/v1/admin", tags=["admin"])


def _notify_backup_unwatched(backup_name: str) -> None:
    """Send a best-effort Telegram notification that a backup was unwatched.

    Args:
        backup_name (str): Backup name.
    """

    try:
        if not configUtils.areTelegramStatusMessagesEnabled():
            return
        bot = telegramNotificationUtils.create_telegram_bot(configUtils)
        logger = Logger.Logger("admin_api")
        msg = (
            "<b>Backup unwatched</b>\n\n"
            f"<b>{backup_name}</b>\n\n"
            "This backup was removed via the Admin UI/API."
        )
        for chat_id in (configUtils.getTelegramInfoChatsIDs() or []):
            telegramNotificationUtils.safe_send_telegram_message(
                bot=bot,
                logger=logger,
                chat_id=chat_id,
                message=msg,
            )
    except Exception:
        return


class BackupFrequencyRequest(BaseModel):
    """Request body for setting a backup frequency override."""

    name: str = Field(..., min_length=1)
    stateCheckFrequency_inMinutes: int = Field(..., gt=0)


@router.get("/backups")
async def admin_list_backups(
    request: Request,
    server_auth_token: Optional[str] = Query(default=None),
    x_server_authentication_token: Optional[str] = Header(
        default=None,
        alias="X-Server-Authentication-Token",
    ),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Dict[str, Any]:
    """List current backup checks from the database.

    Args:
        request: FastAPI request object.
        server_auth_token (Optional[str]): Token provided as query parameter.
        x_server_authentication_token (Optional[str]): Token provided as header.
        credentials: Bearer token credentials.

    Returns:
        Dict[str, Any]: Backups list.
    """

    await require_admin_auth_hybrid(request, server_auth_token, x_server_authentication_token, credentials)

    overrides = configUtils.getBackupFrequencyOverrides()
    db = DatabaseWrapper.DatabaseWrapper()
    backups = db.getAllBackupsToCheck() or []

    return {
        "backups": [
            {
                "name": b.name,
                "description": b.description,
                "stateCheckFrequency_inMinutes": b.stateCheckFrequency_inMinutes,
                "frequencyOverride_inMinutes": overrides.get(b.name),
                "mostRecentBackupFile_creationDate": b.mostRecentBackupFile_creationDate,
                "mostRecentBackupFile_hash": b.mostRecentBackupFile_hash,
            }
            for b in backups
        ]
    }


@router.delete("/backups")
async def admin_delete_backup(
    request: Request,
    body: NameRequest = Body(...),
    server_auth_token: Optional[str] = Query(default=None),
    x_server_authentication_token: Optional[str] = Header(
        default=None,
        alias="X-Server-Authentication-Token",
    ),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Dict[str, Any]:
    """Unwatch a backup by deleting it from the DB.

    If a Google Drive folder with the same name exists in config.googleDrive.foldersToCheck,
    it is removed to prevent the server from re-adding the backup entry.

    Args:
        request: FastAPI request object.
        body (NameRequest): Backup name.
        server_auth_token (Optional[str]): Token provided as query parameter.
        x_server_authentication_token (Optional[str]): Token provided as header.
        credentials: Bearer token credentials.

    Returns:
        Dict[str, Any]: Updated ignore list.
    """

    await require_admin_auth_hybrid(request, server_auth_token, x_server_authentication_token, credentials)

    name = body.name

    # Remove Google Drive folder config from database if exists
    try:
        DbConfig.remove_google_drive_folder(name)
    except Exception:
        pass

    # Remove backup check from database
    try:
        db = DatabaseWrapper.DatabaseWrapper()
        db.deleteBackupCheckByName(name)
    except Exception:
        pass

    _notify_backup_unwatched(name)

    return {"deleted": name}


@router.post("/backups/frequency")
async def admin_set_backup_frequency(
    request: Request,
    body: BackupFrequencyRequest,
    server_auth_token: Optional[str] = Query(default=None),
    x_server_authentication_token: Optional[str] = Header(
        default=None,
        alias="X-Server-Authentication-Token",
    ),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Dict[str, Any]:
    """Set a frequency override for a specific backup.

    Args:
        request: FastAPI request object.
        body (BackupFrequencyRequest): Backup name and new frequency.
        server_auth_token (Optional[str]): Token provided as query parameter.
        x_server_authentication_token (Optional[str]): Token provided as header.
        credentials: Bearer token credentials.

    Returns:
        Dict[str, Any]: The updated overrides mapping.
    """

    await require_admin_auth_hybrid(request, server_auth_token, x_server_authentication_token, credentials)

    # Store override in database
    DbConfig.set_backup_frequency_override(body.name, int(body.stateCheckFrequency_inMinutes))

    # Also update the checked_backups table if the backup exists
    try:
        DatabaseWrapper.DatabaseWrapper().updateBackupCheckFrequencyByName(body.name, int(body.stateCheckFrequency_inMinutes))
    except Exception:
        pass

    return {"backupFrequencyOverrides": configUtils.getBackupFrequencyOverrides()}
