"""Module: telegram_admin_bot.py

Description:
    Telegram bot listener service for statechecker admin actions.

    This service listens for inline keyboard callbacks sent with statechecker
    notifications and applies the requested actions by updating the persisted
    config file (typically logs/config.txt) via configFileManager.

    Supported actions:
        - Unwatch website: remove URL from config.websites.websitesToCheck
        - Watch website: add URL back to config.websites.websitesToCheck
        - Unwatch backup: delete from DB; also remove from config.googleDrive.foldersToCheck if present
        - Unwatch tool: delete from DB (it will auto-reappear if client pings again)

    Security model:
        - Only accepts callbacks from configured admin chat IDs
          (TELEGRAM_RECIPIENTS_ERROR_CHAT_IDS / TELEGRAM_RECIPIENTS_INFO_CHAT_IDS).
"""

from __future__ import annotations

from typing import Any

import os
import re
import sys

import telebot
from telebot import types

sys.path.insert(1, os.path.join(os.path.dirname(__file__), "utils"))
sys.path.insert(1, os.path.join(os.path.dirname(__file__), "models"))
sys.path.insert(1, os.path.join(os.path.dirname(__file__), "definitions"))

import configUtils as ConfigUtils
import emailUtils as EmailUtils
import telegramAdminActions


configUtils = ConfigUtils.ConfigUtils()
emailUtils = EmailUtils.EmailUtils()


def main() -> None:
    """Run the telegram admin bot listener."""

    pending_frequency_requests: dict[tuple[int, int], dict[str, str]] = {}

    def _parse_duration_to_minutes(text: str) -> int:
        """Parse a user-provided duration string into minutes.

        Supported examples:
            - "5" (minutes)
            - "30m"
            - "2h"
            - "1d"

        Args:
            text (str): User input.

        Returns:
            int: Duration in minutes.

        Raises:
            ValueError: If input cannot be parsed.
        """

        if not text or not str(text).strip():
            raise ValueError("missing duration")

        raw = str(text).strip().lower()
        match = re.match(r"^([0-9]+(?:\.[0-9]+)?)\s*(m|min|mins|minute|minutes)?$", raw)
        if match:
            return max(1, int(round(float(match.group(1)))))

        match = re.match(r"^([0-9]+(?:\.[0-9]+)?)\s*(h|hr|hrs|hour|hours)$", raw)
        if match:
            return max(1, int(round(float(match.group(1)) * 60)))

        match = re.match(r"^([0-9]+(?:\.[0-9]+)?)\s*(d|day|days)$", raw)
        if match:
            return max(1, int(round(float(match.group(1)) * 60 * 24)))

        raise ValueError("invalid duration")

    def _send_to_chat(chat_id: Any, message: str, reply_markup: Any = None) -> None:
        """Send a message to a single Telegram chat.

        Args:
            chat_id (Any): Telegram chat id.
            message (str): Message text.
            reply_markup (Any): Optional reply markup.
        """

        try:
            bot.send_message(chat_id, message, reply_markup=reply_markup)
        except Exception:
            pass

    if not configUtils.areTelegramStatusMessagesEnabled():
        raise RuntimeError("Telegram is disabled (TELEGRAM_ENABLED=false)")

    token = configUtils.getTelegramBotToken()
    if not token or str(token).strip() == "" or str(token).lower() == "none":
        raise RuntimeError("Missing TELEGRAM_SENDER_BOT_TOKEN")

    bot = telebot.TeleBot(token, parse_mode="HTML")

    def _send_admin_notification(message: str, reply_markup: Any = None) -> None:
        """Send an admin notification to Telegram + email (best-effort).

        Args:
            message (str): Message to send.
            reply_markup (Any): Optional Telegram markup.
        """

        try:
            # Send to all configured admin channels.
            for chat_id in (configUtils.getTelegramErrorChatsIDs() or []):
                bot.send_message(chat_id, message, reply_markup=reply_markup)
            for chat_id in (configUtils.getTelegramInfoChatsIDs() or []):
                bot.send_message(chat_id, message, reply_markup=reply_markup)
        except Exception:
            pass

        try:
            emailUtils.send_info_mails(message)
        except Exception:
            pass

    @bot.callback_query_handler(func=lambda call: call.data is not None and str(call.data).startswith("admin:"))
    def on_admin_callback(call):
        """Handle inline admin callbacks from statechecker messages."""

        try:
            if call.message is None:
                bot.answer_callback_query(call.id, "No message context", show_alert=True)
                return

            if not telegramAdminActions.is_allowed_chat(configUtils, call.message.chat.id):
                bot.answer_callback_query(call.id, "Not allowed", show_alert=True)
                return

            target_name = telegramAdminActions.extract_target_name_from_message_text(call.message.text or "")
            if not target_name:
                bot.answer_callback_query(call.id, "Could not parse target", show_alert=True)
                return

            parts = str(call.data).split(":")
            if len(parts) == 3:
                _, action, target_type = parts

                if action == "freqmenu":
                    bot.answer_callback_query(call.id, "OK", show_alert=False)

                    markup = types.InlineKeyboardMarkup(row_width=3)
                    markup.row(
                        types.InlineKeyboardButton("5m", callback_data=f"admin:setfreq:{target_type}:5"),
                        types.InlineKeyboardButton("15m", callback_data=f"admin:setfreq:{target_type}:15"),
                        types.InlineKeyboardButton("1h", callback_data=f"admin:setfreq:{target_type}:60"),
                    )
                    markup.row(
                        types.InlineKeyboardButton("6h", callback_data=f"admin:setfreq:{target_type}:360"),
                        types.InlineKeyboardButton("1d", callback_data=f"admin:setfreq:{target_type}:1440"),
                        types.InlineKeyboardButton("Custom…", callback_data=f"admin:freqcustom:{target_type}"),
                    )

                    menu_msg = (
                        "<b>Change Frequency</b>\n\n"
                        f"<b>{target_name}</b>\n\n"
                        "Choose a preset or tap <b>Custom…</b> to enter a duration like: 30m, 2h, 1d\n\n"
                        "<i>Note: If the bot does not respond to your text, make sure it is an administrator in this group/chat.</i>"
                    )
                    _send_to_chat(call.message.chat.id, menu_msg, reply_markup=markup)
                    return

                if action == "freqcustom":
                    bot.answer_callback_query(call.id, "OK", show_alert=False)

                    chat_id = int(call.message.chat.id)
                    user_id = int(getattr(call.from_user, "id", 0) or 0)
                    pending_frequency_requests[(chat_id, user_id)] = {
                        "target_type": str(target_type),
                        "target_name": str(target_name),
                    }

                    _send_to_chat(
                        call.message.chat.id,
                        "<b>Custom frequency</b>\n\n"
                        f"<b>{target_name}</b>\n\n"
                        "Send the desired duration now (examples: 5, 30m, 2h, 1d).\n"
                        "Send <b>cancel</b> to abort.\n\n"
                        "<i>Note: If the bot does not respond to your text, make sure it is an administrator in this group/chat.</i>",
                    )
                    return

                result = telegramAdminActions.apply_admin_action(action, target_type, target_name)
            elif len(parts) == 4:
                _, action, target_type, value = parts
                if action != "setfreq":
                    bot.answer_callback_query(call.id, "Invalid action", show_alert=True)
                    return
                result = telegramAdminActions.apply_frequency_change(target_type, target_name, value)
            else:
                bot.answer_callback_query(call.id, "Invalid action", show_alert=True)
                return

            if len(parts) == 3 and parts[1] == "unwatch" and parts[2] in ("tool", "backup"):
                try:
                    bot.edit_message_reply_markup(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        reply_markup=None,
                    )
                except Exception:
                    pass

            bot.answer_callback_query(call.id, "OK", show_alert=False)

            # Format notification with better structure
            notification = f"<b>Admin action applied</b>\n\n<b>{target_name}</b>\n\n{result}"

            # For websites: provide a re-watch button.
            if len(parts) == 3 and parts[1] == "unwatch" and parts[2] == "website":
                rewatch_markup = types.InlineKeyboardMarkup(row_width=1)
                rewatch_markup.add(
                    types.InlineKeyboardButton("Re-watch website", callback_data="admin:watch:website")
                )
                _send_admin_notification(notification, reply_markup=rewatch_markup)
            else:
                _send_admin_notification(notification)
        except Exception as exc:
            bot.answer_callback_query(call.id, f"Error: {exc}", show_alert=True)

    @bot.message_handler(func=lambda message: message is not None)
    def on_text_message(message):
        """Handle text replies for custom frequency input."""

        try:
            if not telegramAdminActions.is_allowed_chat(configUtils, message.chat.id):
                return

            chat_id = int(message.chat.id)
            user_id = int(getattr(message.from_user, "id", 0) or 0)
            pending = pending_frequency_requests.get((chat_id, user_id))
            if not pending:
                return

            text = str(message.text or "").strip()
            if text.lower() == "cancel":
                pending_frequency_requests.pop((chat_id, user_id), None)
                _send_to_chat(chat_id, "Cancelled.")
                return

            minutes = _parse_duration_to_minutes(text)
            result = telegramAdminActions.apply_frequency_change(
                pending["target_type"],
                pending["target_name"],
                minutes,
            )
            pending_frequency_requests.pop((chat_id, user_id), None)
            _send_to_chat(chat_id, f"<b>Frequency updated</b>\n\n<b>{pending['target_name']}</b>\n\n{result}")
        except Exception as exc:
            try:
                _send_to_chat(message.chat.id, f"Error: {exc}")
            except Exception:
                pass

    bot.infinity_polling()


if __name__ == "__main__":
    main()
