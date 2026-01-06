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

from fastapi import APIRouter, Body, Header, Query
from pydantic import BaseModel, Field

import configUtils as ConfigUtils
import database_config_manager as DbConfig
import databaseWrapper as DatabaseWrapper
import logger as Logger
import telegramNotificationUtils
from adminApiCommon import NameRequest, require_admin_auth_readonly


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
def admin_list_backups(
    server_auth_token: Optional[str] = Query(default=None),
    x_server_authentication_token: Optional[str] = Header(
        default=None,
        alias="X-Server-Authentication-Token",
    ),
) -> Dict[str, Any]:
    """List backups from the database.

    Args:
        server_auth_token (Optional[str]): Token provided as query parameter.
        x_server_authentication_token (Optional[str]): Token provided as header.

    Returns:
        Dict[str, Any]: Backups list.
    """

    require_admin_auth_readonly(server_auth_token, x_server_authentication_token)

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
def admin_delete_backup(
    request: NameRequest = Body(...),
    server_auth_token: Optional[str] = Query(default=None),
    x_server_authentication_token: Optional[str] = Header(
        default=None,
        alias="X-Server-Authentication-Token",
    ),
) -> Dict[str, Any]:
    """Unwatch a backup by deleting it from the DB.

    If a Google Drive folder with the same name exists in config.googleDrive.foldersToCheck,
    it is removed to prevent the server from re-adding the backup entry.

    Args:
        request (NameRequest): Backup name.
        server_auth_token (Optional[str]): Token provided as query parameter.
        x_server_authentication_token (Optional[str]): Token provided as header.

    Returns:
        Dict[str, Any]: Updated ignore list.
    """

    require_admin_auth_readonly(server_auth_token, x_server_authentication_token)

    name = request.name

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
def admin_set_backup_frequency(
    request: BackupFrequencyRequest,
    server_auth_token: Optional[str] = Query(default=None),
    x_server_authentication_token: Optional[str] = Header(
        default=None,
        alias="X-Server-Authentication-Token",
    ),
) -> Dict[str, Any]:
    """Set a persisted frequency override for a backup.

    Args:
        request (BackupFrequencyRequest): Backup name and new frequency.
        server_auth_token (Optional[str]): Token provided as query parameter.
        x_server_authentication_token (Optional[str]): Token provided as header.

    Returns:
        Dict[str, Any]: The updated overrides mapping.
    """

    require_admin_auth_readonly(server_auth_token, x_server_authentication_token)

    # Store override in database
    DbConfig.set_backup_frequency_override(request.name, int(request.stateCheckFrequency_inMinutes))

    # Also update the checked_backups table if the backup exists
    try:
        DatabaseWrapper.DatabaseWrapper().updateBackupCheckFrequencyByName(request.name, int(request.stateCheckFrequency_inMinutes))
    except Exception:
        pass

    return {"backupFrequencyOverrides": configUtils.getBackupFrequencyOverrides()}
