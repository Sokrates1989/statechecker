"""Module: adminApiWebsitesRoutes.py

Description:
    Admin API endpoints for managing watched websites.

    Websites are configuration-driven via config's `websites.websitesToCheck`.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, urlunparse

import requests
from fastapi import APIRouter, Body, Depends, Header, Query, Request
from fastapi.security import HTTPAuthorizationCredentials

import configUtils as ConfigUtils
import database_config_manager as DbConfig
import databaseWrapper as DatabaseWrapper
import logger as Logger
import telegramNotificationUtils
import websiteStateAndMessageSentItem as WebsiteStateAndMessageSentItem
from adminApiCommon import WebsiteRequest, require_read_access, require_write_access, bearer_scheme


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
async def admin_list_websites(
    request: Request,
    server_auth_token: Optional[str] = Query(default=None),
    x_server_authentication_token: Optional[str] = Header(
        default=None,
        alias="X-Server-Authentication-Token",
    ),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
):
    """List configured websites and include last known DB state if available.

    Args:
        request: FastAPI request object.
        server_auth_token (Optional[str]): Token provided as query parameter.
        x_server_authentication_token (Optional[str]): Token provided as header.
        credentials: Bearer token credentials.

    Returns:
        Dict[str, Any]: Websites list.
    """

    await require_read_access(request, server_auth_token, x_server_authentication_token, credentials)

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
async def admin_add_website(
    request: Request,
    body: WebsiteRequest,
    server_auth_token: Optional[str] = Query(default=None),
    x_server_authentication_token: Optional[str] = Header(
        default=None,
        alias="X-Server-Authentication-Token",
    ),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
):
    """Add a website to the websitesToCheck list.

    Args:
        request: FastAPI request object.
        body (WebsiteRequest): Website url.
        server_auth_token (Optional[str]): Token provided as query parameter.
        x_server_authentication_token (Optional[str]): Token provided as header.
        credentials: Bearer token credentials.

    Returns:
        Dict[str, Any]: Updated websitesToCheck list.
    """

    await require_write_access(request, server_auth_token, x_server_authentication_token, credentials)

    url = body.url
    DbConfig.add_website(url)

    # Immediately check the website state
    _check_website_state(url)

    return {"websitesToCheck": configUtils.getWebsitesToCheck()}


def _check_website_state(url: str) -> Dict[str, Any]:
    """Check a website's state and update the database.

    Args:
        url (str): Website URL to check.

    Returns:
        Dict[str, Any]: Check result with state and status code.
    """
    db = DatabaseWrapper.DatabaseWrapper()

    # Create entry if not exists
    db.createNewWebsiteCheck(
        WebsiteStateAndMessageSentItem.WebsiteStateAndMessageSentItem(url, "Up", False)
    )

    try:
        urls_to_try = [url]
        parsed = urlparse(url)
        if parsed.hostname in ("localhost", "127.0.0.1") and parsed.scheme in ("http", "https"):
            host = "host.docker.internal"
            port = parsed.port
            if port is None:
                port = 443 if parsed.scheme == "https" else 80
            urls_to_try.append(
                urlunparse(parsed._replace(netloc=f"{host}:{port}"))
            )

        response = None
        last_exc = None
        for try_url in urls_to_try:
            try:
                response = requests.get(try_url, timeout=10, allow_redirects=True)
                break
            except Exception as exc:
                last_exc = exc
                response = None

        if response is None:
            raise last_exc if last_exc is not None else RuntimeError("request failed")

        # Website is up if status code < 400
        is_up = int(response.status_code) < 400
        state = "Up" if is_up else "Down"

        # Update database
        db.updateWebsiteState(url, state)

        return {"url": url, "state": state, "status_code": response.status_code}

    except Exception as e:
        # Website is down
        db.updateWebsiteState(url, "Down")
        return {"url": url, "state": "Down", "error": str(e)}


@router.post("/websites/check")
async def admin_check_website(
    request: Request,
    body: WebsiteRequest,
    server_auth_token: Optional[str] = Query(default=None),
    x_server_authentication_token: Optional[str] = Header(
        default=None,
        alias="X-Server-Authentication-Token",
    ),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
):
    """Check a website's current state.

    Args:
        request: FastAPI request object.
        body (WebsiteRequest): Website url.
        server_auth_token (Optional[str]): Token provided as query parameter.
        x_server_authentication_token (Optional[str]): Token provided as header.
        credentials: Bearer token credentials.

    Returns:
        Dict[str, Any]: Check result with state.
    """
    await require_read_access(request, server_auth_token, x_server_authentication_token, credentials)
    return _check_website_state(body.url)


@router.delete("/websites")
async def admin_remove_website(
    request: Request,
    body: WebsiteRequest = Body(...),
    server_auth_token: Optional[str] = Query(default=None),
    x_server_authentication_token: Optional[str] = Header(
        default=None,
        alias="X-Server-Authentication-Token",
    ),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
):
    """Remove a website from the websitesToCheck list.

    Args:
        request: FastAPI request object.
        body (WebsiteRequest): Website url.
        server_auth_token (Optional[str]): Token provided as query parameter.
        x_server_authentication_token (Optional[str]): Token provided as header.
        credentials: Bearer token credentials.

    Returns:
        Dict[str, Any]: Updated websitesToCheck list.
    """

    await require_write_access(request, server_auth_token, x_server_authentication_token, credentials)

    url = body.url

    # Remove from config database
    DbConfig.remove_website(url)

    # Remove check results from database
    try:
        db = DatabaseWrapper.DatabaseWrapper()
        db.deleteWebsiteCheckByName(url)
    except Exception:
        pass

    _notify_website_unwatched(url)

    return {"websitesToCheck": configUtils.getWebsitesToCheck()}
