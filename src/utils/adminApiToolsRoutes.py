"""Module: adminApiToolsRoutes.py

Description:
    Admin API endpoints for managing watched tools checked via /v1/statecheck.

    Note:
        "Unwatch" for API tools is intentionally non-sticky: the tool is deleted
        from the database. If the client sends a new /v1/statecheck ping again,
        the tool will appear again automatically.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Header, Query

import configFileManager as ConfigFileManager
import databaseWrapper as DatabaseWrapper
import logger as Logger
import telegramNotificationUtils
from adminApiCommon import NameRequest, require_admin_auth
from pydantic import BaseModel, Field
import configUtils as ConfigUtils


configUtils = ConfigUtils.ConfigUtils()

router = APIRouter(prefix="/v1/admin", tags=["admin"])


def _notify_tool_unwatched(tool_name: str) -> None:
    """Send a best-effort Telegram notification that a tool was unwatched.

    Args:
        tool_name (str): Tool name.
    """

    try:
        if not configUtils.areTelegramStatusMessagesEnabled():
            return
        bot = telegramNotificationUtils.create_telegram_bot(configUtils)
        logger = Logger.Logger("admin_api")
        msg = (
            "<b>Tool unwatched</b>\n\n"
            f"<b>{tool_name}</b>\n\n"
            "This tool was removed via the Admin UI/API. "
            "It will appear again automatically when a client sends a new ping."
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


class ToolFrequencyRequest(BaseModel):
    """Request body for setting a tool frequency override."""

    name: str = Field(..., min_length=1)
    stateCheckFrequency_inMinutes: int = Field(..., gt=0)


@router.get("/tools")
def admin_list_tools(
    server_auth_token: Optional[str] = Query(default=None),
    x_server_authentication_token: Optional[str] = Header(
        default=None,
        alias="X-Server-Authentication-Token",
    ),
) -> Dict[str, Any]:
    """List current tool checks from the database.

    Args:
        server_auth_token (Optional[str]): Token provided as query parameter.
        x_server_authentication_token (Optional[str]): Token provided as header.

    Returns:
        Dict[str, Any]: Tools list.
    """

    require_admin_auth(server_auth_token, x_server_authentication_token)

    overrides = configUtils.getToolsUsingApiFrequencyOverrides()
    db = DatabaseWrapper.DatabaseWrapper()
    tools = db.getAllToolsToCheck() or []

    return {
        "tools": [
            {
                "name": t.name,
                "description": t.description,
                "stateCheckFrequency_inMinutes": t.stateCheckFrequency_inMinutes,
                "frequencyOverride_inMinutes": overrides.get(t.name),
                "lastTimeToolWasUp": t.lastTimeToolWasUp,
            }
            for t in tools
        ]
    }


@router.delete("/tools")
def admin_delete_tool(
    request: NameRequest = Body(...),
    server_auth_token: Optional[str] = Query(default=None),
    x_server_authentication_token: Optional[str] = Header(
        default=None,
        alias="X-Server-Authentication-Token",
    ),
) -> Dict[str, Any]:
    """Unwatch a tool by deleting it from the DB.

    This does NOT persist an ignore list; tools will be watched again if clients
    send pings.

    Args:
        request (NameRequest): Tool name.
        server_auth_token (Optional[str]): Token provided as query parameter.
        x_server_authentication_token (Optional[str]): Token provided as header.

    Returns:
        Dict[str, Any]: Updated ignore list.
    """

    require_admin_auth(server_auth_token, x_server_authentication_token)

    try:
        db = DatabaseWrapper.DatabaseWrapper()
        db.deleteToolCheckByName(request.name)
    except Exception:
        pass

    _notify_tool_unwatched(request.name)

    return {"deleted": request.name}


@router.post("/tools/frequency")
def admin_set_tool_frequency(
    request: ToolFrequencyRequest,
    server_auth_token: Optional[str] = Query(default=None),
    x_server_authentication_token: Optional[str] = Header(
        default=None,
        alias="X-Server-Authentication-Token",
    ),
) -> Dict[str, Any]:
    """Set a persisted frequency override for an API tool.

    Args:
        request (ToolFrequencyRequest): Tool name and new frequency.
        server_auth_token (Optional[str]): Token provided as query parameter.
        x_server_authentication_token (Optional[str]): Token provided as header.

    Returns:
        Dict[str, Any]: The updated overrides mapping.
    """

    require_admin_auth(server_auth_token, x_server_authentication_token)

    def _update(cfg: Dict[str, Any]) -> Dict[str, Any]:
        overrides = cfg.get("toolsUsingApi_frequencyOverrides")
        if not isinstance(overrides, dict):
            overrides = {}
        overrides[request.name] = int(request.stateCheckFrequency_inMinutes)
        cfg["toolsUsingApi_frequencyOverrides"] = overrides
        return cfg

    ConfigFileManager.update_config(_update)

    try:
        DatabaseWrapper.DatabaseWrapper().updateToolCheckFrequencyByName(request.name, int(request.stateCheckFrequency_inMinutes))
    except Exception:
        pass

    return {"toolsUsingApi_frequencyOverrides": configUtils.getToolsUsingApiFrequencyOverrides()}
