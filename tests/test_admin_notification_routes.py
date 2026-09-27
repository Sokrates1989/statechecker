"""Verify Telegram test notifications without provider network calls."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests
import telebot
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

        self.assertEqual((result["attempted"], result["delivered"], result["failed"]), (2, 2, 0))
        self.assertEqual([item["status"] for item in result["results"]], ["sent", "sent"])
        self.assertEqual(len(result["diagnostic_id"]), 12)
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
        self.assertEqual(caught.exception.detail, "telegram_token_quoted")
        bot_factory.assert_not_called()

    def test_missing_and_placeholder_tokens_have_distinct_diagnostics(self) -> None:
        """An empty secret and a placeholder identify different setup faults."""
        for token, expected in [("", "telegram_token_missing"), ("null", "telegram_token_invalid")]:
            self.config.getTelegramBotToken.return_value = token
            with self.subTest(token=token), patch.object(notifications.telebot, "TeleBot") as bot_factory:
                with self.assertRaises(HTTPException) as caught:
                    notifications.send_test_notification(
                        notifications.TelegramTestRequest(level="info", message="Test"), _=None,
                    )
                self.assertEqual(caught.exception.detail, expected)
                bot_factory.assert_not_called()

    def test_partial_delivery_identifies_recipient_without_provider_details(self) -> None:
        """A failed recipient reports a safe reason and retains other successes."""
        bot = Mock()
        bot.send_message.side_effect = [None, requests.exceptions.Timeout("secret URL")]
        with patch.object(notifications.telebot, "TeleBot", return_value=bot):
            result = notifications.send_test_notification(
                notifications.TelegramTestRequest(level="error", message="Test"),
                _=None,
            )

        self.assertEqual((result["delivered"], result["failed"]), (1, 1))
        self.assertEqual(result["results"][1]["chat_id"], "456")
        self.assertEqual(result["results"][1]["reason"], "network_timeout")
        self.assertNotIn("secret URL", str(result))

    def test_total_provider_failure_returns_safe_details_and_correlation_id(self) -> None:
        """Telegram rejection includes actionable metadata without raw API text."""
        self.config.getTelegramErrorChatsIDs.return_value = ["-123"]
        bot = Mock()
        bot.send_message.side_effect = telebot.apihelper.ApiTelegramException(
            "sendMessage", {"error_code": 400, "description": "Bad Request: chat not found"},
            {"ok": False, "error_code": 400, "description": "Bad Request: chat not found"},
        )
        with patch.object(notifications.telebot, "TeleBot", return_value=bot):
            with self.assertRaises(HTTPException) as caught:
                notifications.send_test_notification(
                    notifications.TelegramTestRequest(level="error", message="Test"), _=None,
                )

        detail = caught.exception.detail
        self.assertEqual(caught.exception.status_code, 502)
        self.assertEqual(detail["code"], "telegram_delivery_failed")
        self.assertEqual(detail["results"][0]["reason"], "chat_not_found")
        self.assertEqual(detail["results"][0]["provider_status"], 400)
        self.assertEqual(len(detail["diagnostic_id"]), 12)
        self.assertNotIn("Bad Request", str(detail))
