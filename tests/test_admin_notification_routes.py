"""Verify Telegram test notifications without provider network calls."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "utils"))

import adminApiNotificationRoutes as notifications


class AdminNotificationTests(unittest.TestCase):
    """Test configured routing, partial delivery, and secret validation."""

    def setUp(self) -> None:
        """Use one configured error chat and a valid fake bot token."""
        self.config = Mock()
        self.config.areTelegramStatusMessagesEnabled.return_value = True
        self.config.getTelegramErrorChatsIDs.return_value = ["-123", "-123", "456"]
        self.config.getTelegramInfoChatsIDs.return_value = ["789"]
        self.config.getTelegramBotToken.return_value = "123:valid_token"
        self.config_patch = patch.object(notifications, "configUtils", self.config)
        self.config_patch.start()
        self.addCleanup(self.config_patch.stop)

    def test_settings_show_configured_chats_without_token(self) -> None:
        """The read endpoint does not return bot credentials."""
        settings = notifications.get_notification_settings(_=None)

        self.assertEqual(settings["error_chat_ids"], ["-123", "456"])
        self.assertEqual(settings["info_chat_ids"], ["789"])
        self.assertNotIn("token", str(settings).lower())

    def test_test_send_requires_authentication(self) -> None:
        """An anonymous request never reaches Telegram delivery."""
        app = FastAPI()
        app.include_router(notifications.router)
        with patch.object(notifications.telebot, "TeleBot") as bot_factory:
            response = TestClient(app).post(
                "/v1/admin/notifications/test",
                json={"level": "error", "message": "Test"},
            )

        self.assertEqual(response.status_code, 401)
        bot_factory.assert_not_called()

    def test_sends_one_escaped_message_per_configured_chat(self) -> None:
        """Duplicate configured IDs cannot produce duplicate test sends."""
        bot = Mock()
        with patch.object(notifications.telebot, "TeleBot", return_value=bot):
            result = notifications.send_test_notification(
                notifications.TelegramTestRequest(level="error", message="Test <b>alert</b>"),
                _=None,
            )

        self.assertEqual(result, {"delivered": 2, "failed": 0})
        self.assertEqual(bot.send_message.call_count, 2)
        bot.send_message.assert_any_call("-123", "Test &lt;b&gt;alert&lt;/b&gt;")

    def test_malformed_token_is_rejected_without_sending(self) -> None:
        """A mounted secret with enclosing quotes remains invalid."""
        self.config.getTelegramBotToken.return_value = '"123:quoted"'
        with patch.object(notifications.telebot, "TeleBot") as bot_factory:
            with self.assertRaises(HTTPException) as caught:
                notifications.send_test_notification(
                    notifications.TelegramTestRequest(level="info", message="Test"),
                    _=None,
                )

        self.assertEqual(caught.exception.status_code, 503)
        self.assertEqual(caught.exception.detail, "telegram_token_invalid")
        bot_factory.assert_not_called()

    def test_partial_delivery_reports_counts_without_provider_details(self) -> None:
        """A failed recipient yields a safe summary and retries remain possible."""
        bot = Mock()
        bot.send_message.side_effect = [None, RuntimeError("provider details")]
        with patch.object(notifications.telebot, "TeleBot", return_value=bot):
            result = notifications.send_test_notification(
                notifications.TelegramTestRequest(level="error", message="Test"),
                _=None,
            )

        self.assertEqual(result, {"delivered": 1, "failed": 1})
