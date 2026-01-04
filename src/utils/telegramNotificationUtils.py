"""Module: telegramNotificationUtils.py

Description:
    Telegram notification helpers for the statechecker check worker.

    This module centralizes:
    - Creating a TeleBot instance (when enabled)
    - Safely sending messages with robust error handling
    - Building admin inline keyboards for DOWN notifications
"""

from __future__ import annotations

from typing import Any, Optional

import telebot
from telebot import types


def create_telegram_bot(config_utils) -> Optional[telebot.TeleBot]:
    """Create a Telegram bot instance if Telegram is enabled and configured.

    Args:
        config_utils: ConfigUtils instance.

    Returns:
        Optional[telebot.TeleBot]: TeleBot instance or None.
    """

    try:
        if not config_utils.areTelegramStatusMessagesEnabled():
            return None

        token = config_utils.getTelegramBotToken()
        if not token or str(token).strip() == "" or str(token).lower() == "none":
            return None

        return telebot.TeleBot(token, parse_mode="HTML")
    except Exception:
        return None


def safe_send_telegram_message(
    *,
    bot: Optional[telebot.TeleBot],
    logger,
    chat_id: Any,
    message: str,
    reply_markup: Optional[Any] = None,
) -> bool:
    """Safely send a Telegram message with proper error handling.

    Handles common Telegram API errors gracefully.

    Args:
        bot (Optional[telebot.TeleBot]): TeleBot instance.
        logger: Logger instance.
        chat_id (Any): Telegram chat id.
        message (str): Message to send.
        reply_markup (Optional[Any]): Optional Telegram reply markup.

    Returns:
        bool: True if message was sent successfully, False otherwise.
    """

    if bot is None:
        return False

    try:
        bot.send_message(chat_id, message, reply_markup=reply_markup)
        return True
    except telebot.apihelper.ApiTelegramException as e:
        error_desc = str(e).lower()

        if "chat not found" in error_desc:
            logger.logWarning(
                f"Telegram chat not found (chat_id={chat_id}). "
                f"The chat ID may be invalid or the user may have blocked the bot. "
                f"Consider removing this chat ID from the configuration."
            )
        elif "bot was blocked" in error_desc:
            logger.logWarning(
                f"Telegram bot was blocked by user (chat_id={chat_id}). "
                f"The user has blocked the bot. Remove this chat ID from config."
            )
        elif "user is deactivated" in error_desc:
            logger.logWarning(
                f"Telegram user is deactivated (chat_id={chat_id}). "
                f"The user account no longer exists. Remove this chat ID from config."
            )
        elif "forbidden" in error_desc:
            logger.logWarning(
                f"Telegram API forbidden error (chat_id={chat_id}): {e}. "
                f"Bot may not have permission to send messages to this chat."
            )
        else:
            logger.logError(
                f"Telegram API error sending to chat_id={chat_id}: "
                f"{type(e).__name__}: {e}"
            )
        return False
    except Exception as e:
        logger.logError(
            f"Unexpected error sending Telegram message to chat_id={chat_id}: "
            f"{type(e).__name__}: {e}"
        )
        return False


def build_admin_inline_keyboard(tool_state_item) -> types.InlineKeyboardMarkup:
    """Build an admin inline keyboard for a ToolStateItem notification.

    Args:
        tool_state_item: ToolStateItem instance.

    Returns:
        types.InlineKeyboardMarkup: Inline keyboard for admin actions.
    """

    markup = types.InlineKeyboardMarkup(row_width=3)

    if tool_state_item.isCustomCheck == True:
        markup.add(types.InlineKeyboardButton("Unwatch website", callback_data="admin:unwatch:website"))
        return markup

    if tool_state_item.isBackupCheck == True:
        markup.add(types.InlineKeyboardButton("Unwatch backup", callback_data="admin:unwatch:backup"))
        markup.add(types.InlineKeyboardButton("Change Frequency", callback_data="admin:freqmenu:backup"))
        return markup

    markup.add(types.InlineKeyboardButton("Unwatch tool", callback_data="admin:unwatch:tool"))
    markup.add(types.InlineKeyboardButton("Change Frequency", callback_data="admin:freqmenu:tool"))
    return markup
