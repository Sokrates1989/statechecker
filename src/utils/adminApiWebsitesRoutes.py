"""Module: adminApiWebsitesRoutes.py

Description:
    Admin API endpoints for managing watched websites.

    Websites are configuration-driven via config's `websites.websitesToCheck`.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Header, Query

import configFileManager as ConfigFileManager
import configUtils as ConfigUtils
import databaseWrapper as DatabaseWrapper
import logger as Logger
import telegramNotificationUtils
from adminApiCommon import WebsiteRequest, dedupe_preserve_order, ensure_list, require_admin_auth


configUtils = ConfigUtils.ConfigUtils()

router = APIRouter(prefix="/v1/admin", tags=["admin"])


def _notify_website_unwatched(url: str) -> None:
    """Send a best-effort Telegram notification that a website was removed.

    Args:
        url (str): Website URL.
    """

    try:
        if not configUtils.areTelegramStatusMessagesEnabled():
            return
        bot = telegramNotificationUtils.create_telegram_bot(configUtils)
        logger = Logger.Logger("admin_api")
        msg = (
            "<b>Website removed</b>\n\n"
            f"<b>{url}</b>\n\n"
            "This website was removed from the watchlist via the Admin UI/API."
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


@router.get("/websites")
def admin_list_websites(
    server_auth_token: Optional[str] = Query(default=None),
    x_server_authentication_token: Optional[str] = Header(
        default=None,
        alias="X-Server-Authentication-Token",
    ),
) -> Dict[str, Any]:
    """List configured websites and include last known DB state if available.

    Args:
        server_auth_token (Optional[str]): Token provided as query parameter.
        x_server_authentication_token (Optional[str]): Token provided as header.

    Returns:
        Dict[str, Any]: Websites list.
    """

    require_admin_auth(server_auth_token, x_server_authentication_token)

    urls = configUtils.getWebsitesToCheck() or []
    db = DatabaseWrapper.DatabaseWrapper()

    websites: List[Dict[str, Any]] = []
    for url in urls:
        item = None
        try:
            item = db.getWebsiteCheckItemByName(url)
        except Exception:
            item = None

        websites.append(
            {
                "url": url,
                "state": getattr(item, "state", None),
                "isDownMessageHasBeenSent": getattr(item, "isDownMessageHasBeenSent", None),
            }
        )

    return {"websites": websites}


@router.post("/websites")
def admin_add_website(
    request: WebsiteRequest,
    server_auth_token: Optional[str] = Query(default=None),
    x_server_authentication_token: Optional[str] = Header(
        default=None,
        alias="X-Server-Authentication-Token",
    ),
) -> Dict[str, Any]:
    """Add a website URL to the persisted config.

    Args:
        request (WebsiteRequest): Website url.
        server_auth_token (Optional[str]): Token provided as query parameter.
        x_server_authentication_token (Optional[str]): Token provided as header.

    Returns:
        Dict[str, Any]: Updated websitesToCheck list.
    """

    require_admin_auth(server_auth_token, x_server_authentication_token)

    url = request.url

    def _update(cfg: Dict[str, Any]) -> Dict[str, Any]:
        websites = cfg.setdefault("websites", {})
        websites["websitesToCheck"] = dedupe_preserve_order(ensure_list(websites.get("websitesToCheck")) + [url])
        return cfg

    ConfigFileManager.update_config(_update)
    return {"websitesToCheck": configUtils.getWebsitesToCheck()}


@router.delete("/websites")
def admin_remove_website(
    request: WebsiteRequest = Body(...),
    server_auth_token: Optional[str] = Query(default=None),
    x_server_authentication_token: Optional[str] = Header(
        default=None,
        alias="X-Server-Authentication-Token",
    ),
) -> Dict[str, Any]:
    """Remove a website URL from persisted config and delete DB entry.

    Args:
        request (WebsiteRequest): Website url.
        server_auth_token (Optional[str]): Token provided as query parameter.
        x_server_authentication_token (Optional[str]): Token provided as header.

    Returns:
        Dict[str, Any]: Updated websitesToCheck list.
    """

    require_admin_auth(server_auth_token, x_server_authentication_token)

    url = request.url

    def _update(cfg: Dict[str, Any]) -> Dict[str, Any]:
        websites = cfg.setdefault("websites", {})
        websites["websitesToCheck"] = [item for item in ensure_list(websites.get("websitesToCheck")) if item != url]
        return cfg

    ConfigFileManager.update_config(_update)

    try:
        db = DatabaseWrapper.DatabaseWrapper()
        db.deleteWebsiteCheckByName(url)
    except Exception:
        pass

    _notify_website_unwatched(url)

    return {"websitesToCheck": configUtils.getWebsitesToCheck()}
