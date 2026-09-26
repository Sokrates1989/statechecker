"""Check alert acknowledgement without database or network connections."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "utils"))

from checkWorkerAlertDelivery import deliver_alert, record_website_check_state


class AlertDeliveryTests(unittest.TestCase):
    """Verify delivery, retries, and persisted transition acknowledgement."""

    def setUp(self) -> None:
        """Create isolated collaborators for a monitored website."""
        self.item = SimpleNamespace(
            name="https://peer.example/health",
            toolIsUp=False,
            isCustomCheck=True,
            isBackupCheck=False,
        )
        self.database = Mock()
        self.config = Mock()
        self.config.areTelegramStatusMessagesEnabled.return_value = True
        self.logger = Mock()
        self.email = Mock()
        self.sender = Mock(return_value=True)

    def deliver(self, *, is_down: bool, recipients: list[int]) -> bool:
        """Invoke the alert boundary with the current test collaborators."""
        return deliver_alert(
            tool_state_item=self.item,
            is_down=is_down,
            message="peer transition",
            db_wrapper=self.database,
            config_utils=self.config,
            bot=object(),
            error_chat_ids=recipients,
            logger=self.logger,
            email_utils=self.email,
            telegram_sender=self.sender,
        )

    def test_successful_down_alert_acknowledges_after_send(self) -> None:
        """A successful Telegram send persists the down acknowledgement."""
        def send_after_checking_database(**_kwargs: object) -> bool:
            self.database.updateWebsiteIsDownMessageHasBeenSentState.assert_not_called()
            return True

        self.sender.side_effect = send_after_checking_database
        self.assertTrue(self.deliver(is_down=True, recipients=[1]))

        self.sender.assert_called_once()
        self.database.updateWebsiteIsDownMessageHasBeenSentState.assert_called_once_with(
            self.item.name, 1
        )
        self.email.send_error_mails.assert_called_once_with("peer transition")

    def test_failed_send_leaves_down_pending_and_records_website_down(self) -> None:
        """A Telegram outage leaves the flag clear for the next check."""
        self.sender.return_value = False
        record_website_check_state(self.item, self.database)

        self.assertFalse(self.deliver(is_down=True, recipients=[1]))
        self.database.updateWebsiteState.assert_called_once_with(self.item.name, "Down")
        self.database.updateWebsiteIsDownMessageHasBeenSentState.assert_not_called()
        self.email.send_error_mails.assert_not_called()

    def test_recovery_retries_until_telegram_accepts_it(self) -> None:
        """Do not clear the down flag before the UP AGAIN alert is delivered."""
        self.item.toolIsUp = True
        record_website_check_state(self.item, self.database)
        self.sender.side_effect = [False, True]

        self.assertFalse(self.deliver(is_down=False, recipients=[1]))
        self.database.updateWebsiteIsDownMessageHasBeenSentState.assert_not_called()
        self.assertTrue(self.deliver(is_down=False, recipients=[1]))
        self.database.updateWebsiteState.assert_called_once_with(self.item.name, "Up")
        self.database.updateWebsiteIsDownMessageHasBeenSentState.assert_called_once_with(
            self.item.name, 0
        )

    def test_partial_delivery_acknowledges_once_and_logs_failure(self) -> None:
        """One success prevents repeated alerts to a chat that received it."""
        self.sender.side_effect = [True, False]

        self.assertTrue(self.deliver(is_down=True, recipients=[1, 2]))
        self.assertEqual(self.sender.call_count, 2)
        self.database.updateWebsiteIsDownMessageHasBeenSentState.assert_called_once_with(
            self.item.name, 1
        )
        self.logger.logWarning.assert_called_once()

    def test_empty_recipient_list_remains_pending(self) -> None:
        """An enabled but unconfigured Telegram channel cannot be acknowledged."""
        self.assertFalse(self.deliver(is_down=True, recipients=[]))
        self.database.updateWebsiteIsDownMessageHasBeenSentState.assert_not_called()
        self.email.send_error_mails.assert_not_called()

    def test_email_only_configuration_keeps_existing_acknowledgement(self) -> None:
        """With Telegram disabled, send email and persist the transition."""
        self.config.areTelegramStatusMessagesEnabled.return_value = False

        self.assertTrue(self.deliver(is_down=True, recipients=[]))
        self.sender.assert_not_called()
        self.email.send_error_mails.assert_called_once_with("peer transition")
        self.database.updateWebsiteIsDownMessageHasBeenSentState.assert_called_once_with(
            self.item.name, 1
        )

    def test_backup_and_tool_flags_keep_their_existing_storage_paths(self) -> None:
        """The shared delivery boundary updates the correct persisted flag."""
        self.item.isCustomCheck = False
        self.item.isBackupCheck = True
        self.assertTrue(self.deliver(is_down=True, recipients=[1]))
        self.database.updateBackupIsDownMessageHasBeenSentState.assert_called_once_with(
            self.item.name, 1
        )

        self.item.isBackupCheck = False
        self.assertTrue(self.deliver(is_down=False, recipients=[1]))
        self.database.updateToolIsDownMessageHasBeenSentState.assert_called_once_with(
            self.item.name, 0
        )


if __name__ == "__main__":
    unittest.main()
