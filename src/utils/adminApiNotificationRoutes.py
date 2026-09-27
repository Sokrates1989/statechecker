"""Authenticated Telegram test notifications for the admin UI."""

from __future__ import annotations

import html
import logging
import re
from typing import Literal
from uuid import uuid4

import requests
import telebot
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from adminApiCommon import configUtils, require_read_access, require_write_access


router = APIRouter(prefix="/v1/admin/notifications", tags=["admin"])
logger = logging.getLogger(__name__)


class TelegramTestRequest(BaseModel):
    """A localized test message for one configured recipient group."""

    level: Literal["error", "info"]
    message: str = Field(..., min_length=1, max_length=200)


def _recipient_ids(level: str) -> list[str]:
    """Read the same error or info chat IDs used by the check worker."""
    try:
        configured = (
            configUtils.getTelegramErrorChatsIDs()
            if level == "error"
            else configUtils.getTelegramInfoChatsIDs()
        )
    except (KeyError, TypeError, UnboundLocalError, ValueError):
        return []
    return list(dict.fromkeys(str(chat_id) for chat_id in (configured or [])))


def _delivery_failure(exc: Exception) -> tuple[str, int | None]:
    """Classify a failed send without returning provider text or credentials."""
    if isinstance(exc, telebot.apihelper.ApiTelegramException):
        status = getattr(exc, "error_code", None)
        status = status if isinstance(status, int) else None
        description = str(getattr(exc, "description", "")).lower()
        if "chat not found" in description:
            return "chat_not_found", status
        if "bot was blocked" in description or "user is deactivated" in description:
            return "bot_blocked", status
        if status == 403 or "bot was kicked" in description or "not enough rights" in description:
            return "chat_forbidden", status
        if status in (401, 404):
            return "token_rejected", status
        if status == 429:
            return "rate_limited", status
        if status is not None and status >= 500:
            return "provider_unavailable", status
        return "provider_rejected", status
    if isinstance(exc, requests.exceptions.Timeout):
        return "network_timeout", None
    if isinstance(exc, requests.exceptions.RequestException):
        return "network_error", None
    return "unexpected_error", None


@router.get("")
def get_notification_settings(_=Depends(require_read_access)) -> dict:
    """Show Telegram delivery settings without exposing the bot token."""
    return {
        "telegram_enabled": configUtils.areTelegramStatusMessagesEnabled(),
        "error_chat_ids": _recipient_ids("error"),
        "info_chat_ids": _recipient_ids("info"),
    }


@router.post("/test")
def send_test_notification(
    payload: TelegramTestRequest, _=Depends(require_write_access)
) -> dict:
    """Send one test message to each configured chat of the selected level."""
    if not configUtils.areTelegramStatusMessagesEnabled():
        raise HTTPException(status_code=503, detail="telegram_disabled")

    chat_ids = _recipient_ids(payload.level)
    if not chat_ids:
        raise HTTPException(status_code=422, detail="telegram_recipients_missing")

    try:
        token = configUtils.getTelegramBotToken()
    except (AttributeError, OSError, TypeError):
        token = None
    if not isinstance(token, str) or not token.strip():
        raise HTTPException(status_code=503, detail="telegram_token_missing")
    if len(token) >= 3 and token[0] in "\"'" and token[-1] == token[0] and re.fullmatch(
        r"[0-9]+:[A-Za-z0-9_-]+", token[1:-1]
    ):
        raise HTTPException(status_code=503, detail="telegram_token_quoted")
    if not re.fullmatch(r"[0-9]+:[A-Za-z0-9_-]+", token):
        raise HTTPException(status_code=503, detail="telegram_token_invalid")

    try:
        bot = telebot.TeleBot(token, parse_mode="HTML")
    except (TypeError, ValueError):
        raise HTTPException(status_code=503, detail="telegram_token_invalid") from None
    diagnostic_id = uuid4().hex[:12]
    results = []
    for chat_id in chat_ids:
        try:
            bot.send_message(chat_id, html.escape(payload.message))
            results.append({"chat_id": chat_id, "status": "sent"})
        except Exception as exc:
            reason, provider_status = _delivery_failure(exc)
            results.append({
                "chat_id": chat_id,
                "status": "failed",
                "reason": reason,
                "provider_status": provider_status,
            })
            logger.warning(
                "Telegram test delivery failed diagnostic_id=%s chat_id=%s reason=%s provider_status=%s",
                diagnostic_id, chat_id, reason, provider_status,
            )

    delivered = sum(result["status"] == "sent" for result in results)
    outcome = {
        "diagnostic_id": diagnostic_id,
        "attempted": len(chat_ids),
        "delivered": delivered,
        "failed": len(chat_ids) - delivered,
        "results": results,
    }
    logger.info(
        "Telegram test completed diagnostic_id=%s attempted=%s delivered=%s failed=%s",
        diagnostic_id, len(chat_ids), delivered, outcome["failed"],
    )
    if delivered == 0:
        raise HTTPException(status_code=502, detail={"code": "telegram_delivery_failed", **outcome})
    return outcome
