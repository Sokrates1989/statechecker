"""Deliver checker transitions before acknowledging their persisted alert state.

The worker has one persisted acknowledgement per monitored item, so a partial
Telegram delivery is acknowledged after one chat succeeds to avoid repeated
messages to chats that already received it. Failed recipients are logged.
"""

from __future__ import annotations

from typing import Any, Callable


def record_website_check_state(tool_state_item: Any, db_wrapper: Any) -> None:
    """Persist the latest website result independently of alert delivery."""
    if tool_state_item.isCustomCheck:
        db_wrapper.updateWebsiteState(
            tool_state_item.name, "Up" if tool_state_item.toolIsUp else "Down"
        )


def deliver_alert(
    *,
    tool_state_item: Any,
    is_down: bool,
    message: str,
    db_wrapper: Any,
    config_utils: Any,
    bot: Any,
    error_chat_ids: list[Any],
    logger: Any,
    email_utils: Any,
    telegram_sender: Callable[..., bool],
    reply_markup: Any = None,
) -> bool:
    """Send a transition and persist its acknowledgement after delivery.

    When Telegram is enabled, at least one error chat must accept the message.
    The worker retries on its next check if none do. Email is sent only after
    Telegram acknowledgement in that mode, preventing repeated email during
    Telegram outages. With Telegram disabled, the prior email-only
    acknowledgement behavior remains. A partial Telegram send is acknowledged
    because the existing single database flag cannot track individual chats.

    Args:
        tool_state_item: Monitored item whose flag is persisted.
        is_down: Whether this alert is for a DOWN transition.
        message: Formatted alert text shared by Telegram and email.
        db_wrapper: Database writer for the monitored item.
        config_utils: Supplies the Telegram enablement flag.
        bot: Sender bot passed to the Telegram transport.
        error_chat_ids: Configured Telegram error destinations.
        logger: Records partial or failed delivery.
        email_utils: Sends email after acknowledgement.
        telegram_sender: Transport returning True on accepted delivery.
        reply_markup: Optional Telegram controls for a DOWN alert.

    Returns:
        True if the transition was acknowledged, False if Telegram delivery
        needs another attempt.
    """
    if config_utils.areTelegramStatusMessagesEnabled():
        delivered = 0
        recipients = error_chat_ids or []
        for chat_id in recipients:
            if telegram_sender(
                bot=bot,
                logger=logger,
                chat_id=chat_id,
                message=message,
                reply_markup=reply_markup,
            ):
                delivered += 1

        if delivered < len(recipients):
            logger.logWarning(
                f"Telegram alert delivered to {delivered}/{len(recipients)} error chats."
            )
        if delivered == 0:
            return False

    sent_flag = 1 if is_down else 0
    if tool_state_item.isCustomCheck:
        db_wrapper.updateWebsiteIsDownMessageHasBeenSentState(
            tool_state_item.name, sent_flag
        )
    elif tool_state_item.isBackupCheck:
        db_wrapper.updateBackupIsDownMessageHasBeenSentState(
            tool_state_item.name, sent_flag
        )
    else:
        db_wrapper.updateToolIsDownMessageHasBeenSentState(
            tool_state_item.name, sent_flag
        )

    email_utils.send_error_mails(message)
    return True
