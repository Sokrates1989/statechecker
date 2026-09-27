"""Authenticated Telegram test notifications for the admin UI."""

from __future__ import annotations

import html
import logging
import re
from typing import Literal

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
    if not isinstance(token, str) or not re.fullmatch(r"[0-9]+:[A-Za-z0-9_-]+", token):
        raise HTTPException(status_code=503, detail="telegram_token_invalid")

    try:
        bot = telebot.TeleBot(token, parse_mode="HTML")
    except (TypeError, ValueError):
        raise HTTPException(status_code=503, detail="telegram_token_invalid") from None
    delivered = 0
    for chat_id in chat_ids:
        try:
            bot.send_message(chat_id, html.escape(payload.message))
            delivered += 1
        except Exception:
            logger.warning("Telegram test delivery failed for a configured chat")

    if delivered == 0:
        raise HTTPException(status_code=502, detail="telegram_delivery_failed")
    return {"delivered": delivered, "failed": len(chat_ids) - delivered}
