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
async def admin_list_tools(
    request: Request,
    server_auth_token: Optional[str] = Query(default=None),
    x_server_authentication_token: Optional[str] = Header(
        default=None,
        alias="X-Server-Authentication-Token",
    ),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
):
    """List current tool checks from the database.

    Args:
        request: FastAPI request object.
        server_auth_token (Optional[str]): Token provided as query parameter.
        x_server_authentication_token (Optional[str]): Token provided as header.
        credentials: Bearer token credentials.

    Returns:
        Dict[str, Any]: Tools list.
    """

    await require_admin_auth_hybrid(request, server_auth_token, x_server_authentication_token, credentials)

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
async def admin_delete_tool(
    request: Request,
    body: NameRequest = Body(...),
    server_auth_token: Optional[str] = Query(default=None),
    x_server_authentication_token: Optional[str] = Header(
        default=None,
        alias="X-Server-Authentication-Token",
    ),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
):
    """Unwatch a tool by deleting it from the DB.

    This does NOT persist an ignore list; tools will be watched again if clients
    send pings.

    Args:
        request: FastAPI request object.
        body (NameRequest): Tool name.
        server_auth_token (Optional[str]): Token provided as query parameter.
        x_server_authentication_token (Optional[str]): Token provided as header.
        credentials: Bearer token credentials.

    Returns:
        Dict[str, Any]: Updated ignore list.
    """

    await require_admin_auth_hybrid(request, server_auth_token, x_server_authentication_token, credentials)

    try:
        db = DatabaseWrapper.DatabaseWrapper()
        db.deleteToolCheckByName(body.name)
    except Exception:
        pass

    _notify_tool_unwatched(body.name)

    return {"deleted": body.name}


@router.post("/tools/frequency")
async def admin_set_tool_frequency(
    request: Request,
    body: ToolFrequencyRequest,
    server_auth_token: Optional[str] = Query(default=None),
    x_server_authentication_token: Optional[str] = Header(
        default=None,
        alias="X-Server-Authentication-Token",
    ),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
):
    """Set a persisted frequency override for an API tool in database.

    Args:
        request: FastAPI request object.
        body (ToolFrequencyRequest): Tool name and new frequency.
        server_auth_token (Optional[str]): Token provided as query parameter.
        x_server_authentication_token (Optional[str]): Token provided as header.
        credentials: Bearer token credentials.

    Returns:
        Dict[str, Any]: The updated overrides mapping.
    """

    await require_admin_auth_hybrid(request, server_auth_token, x_server_authentication_token, credentials)

    # Store override in database
    DbConfig.set_tool_frequency_override(body.name, int(body.stateCheckFrequency_inMinutes))

    # Also update the checked_tools table if the tool exists
    try:
        DatabaseWrapper.DatabaseWrapper().updateToolCheckFrequencyByName(body.name, int(body.stateCheckFrequency_inMinutes))
    except Exception:
        pass

    return {"toolsUsingApi_frequencyOverrides": configUtils.getToolsUsingApiFrequencyOverrides()}
