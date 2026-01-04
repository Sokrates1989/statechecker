"""Module: checkWorkerMessageHandlers.py

Description:
    Message/log handling helpers for the statechecker check worker.

    This module exists primarily to keep src/check_tools.py small enough to comply
    with the project file-size rules.

    It centralizes:
    - exception handling (log + notify)
    - periodic "still running" status messages
"""

from __future__ import annotations

import traceback

import telegramNotificationUtils


def handleCommandException(
    logger,
    configUtils,
    bot,
    errorChatIDs,
    emailUtils,
    exceptionLocationAndAdditionalInformation,
    exception,
):
    """Handle an exception in the check worker.

    Logs the traceback and sends admin notifications.

    Args:
        logger: Logger instance.
        configUtils: ConfigUtils instance.
        bot: TeleBot instance or None.
        errorChatIDs: List of admin chat ids.
        emailUtils: EmailUtils instance.
        exceptionLocationAndAdditionalInformation (str): Context for error.
        exception: Exception instance or string.
    """

    # Log error.
    errorLogText = exceptionLocationAndAdditionalInformation + " " + str(exception)

    # Add traceback to logfile.
    traceOfError = traceback.format_exc()
    logger.logError(str(traceOfError) + "\n" + errorLogText)

    # Send error message to admin telegram chat, if intended.
    if configUtils.areTelegramStatusMessagesEnabled():
        for errorChatID in errorChatIDs:
            telegramNotificationUtils.safe_send_telegram_message(
                bot=bot,
                logger=logger,
                chat_id=errorChatID,
                message=errorLogText,
            )

    # Send mails.
    emailUtils.send_error_mails(errorLogText)


def infoCheckingToolsIsWorking(
    logger,
    configUtils,
    bot,
    infoChatIDs,
    emailUtils,
    stringUtils,
    stateCheckUtils,
    checkWebsitesEveryXMinutes,
    telegramMessageEveryXMinutes,
    emailMessageEveryXMinutes,
    justStartedChecking=False,
    telegramTimeReached=False,
    emailTimeReached=False,
):
    """Send a periodic "still running" status message.

    Args:
        logger: Logger instance.
        configUtils: ConfigUtils instance.
        bot: TeleBot instance or None.
        infoChatIDs: List of admin chat ids.
        emailUtils: EmailUtils instance.
        stringUtils: stringUtils module.
        stateCheckUtils: stateCheckUtils module.
        checkWebsitesEveryXMinutes (int): Website check frequency.
        telegramMessageEveryXMinutes (int): Telegram status message frequency.
        emailMessageEveryXMinutes (int): Email status message frequency.
        justStartedChecking (bool): Whether this is the startup message.
        telegramTimeReached (bool): Whether it's time to send telegram status.
        emailTimeReached (bool): Whether it's time to send email status.
    """

    # Create info text.
    infoLogText = "<b><u>Tools are being checked.</u></b>\nWebsites are being checked every <b>" + str(
        checkWebsitesEveryXMinutes) + "</b> minutes"
    if justStartedChecking:
        infoLogText += "\nJust (re-)started checking tools.\n"

        # Telegram message enabled? -> Add frequency info.
        if configUtils.areTelegramStatusMessagesEnabled():
            infoLogText += "\nAbout every <b>" + str(telegramMessageEveryXMinutes) + "</b> minutes a telegram message should be send, to verify that this program is still working correctly."

        # Email message enabled? -> Add frequency info.
        if configUtils.areEmailStatusMessagesEnabled():
            infoLogText += "\nAbout every <b>" + str(emailMessageEveryXMinutes) + "</b> minutes a status email should be send, to verify that this program is still working correctly."
    else:
        infoLogText += "\n\nThis is an information to ensure, that the program is working correctly.\n"

        # Telegram message enabled and telegramtimeReached? -> Add frequency info.
        if configUtils.areTelegramStatusMessagesEnabled() and telegramTimeReached:
            infoLogText += "\nThis message should show up again in " + str(
            telegramMessageEveryXMinutes) + " minutes, verifying that this program is still working correctly."

        # Email message enabled and emailtimeReached? -> Add frequency info.
        if configUtils.areEmailStatusMessagesEnabled() and emailTimeReached:
            infoLogText += "\nThis message should show up again in " + str(
            emailMessageEveryXMinutes) + " minutes, verifying that this program is still working correctly."

    infoLogText += "\nIf not -> Try to restart this program and take a look at the logs."

    # Add status message of checked tools.
    infoLogText += "\n\n" + stateCheckUtils.getToolStatesMessage()

    # Log information.
    logger.logInformation(infoLogText)

    # Send message to admin telegram chat, if enabled and time reached.
    if configUtils.areTelegramStatusMessagesEnabled() and (justStartedChecking or telegramTimeReached):

        # Does message have to be split?
        if len(infoLogText) > 4096:

            # Split message.
            individualMessages = stringUtils.splitLongTextIntoWorkingMessages(infoLogText)

            # Send messages.
            for individualMessage in individualMessages:
                for infoChatID in infoChatIDs:
                    telegramNotificationUtils.safe_send_telegram_message(
                        bot=bot,
                        logger=logger,
                        chat_id=infoChatID,
                        message=individualMessage,
                    )

        else:
            # Message does not have to be split.
            for infoChatID in infoChatIDs:
                telegramNotificationUtils.safe_send_telegram_message(
                    bot=bot,
                    logger=logger,
                    chat_id=infoChatID,
                    message=infoLogText,
                )

    # Send mails.
    if justStartedChecking or emailTimeReached:
        emailUtils.send_info_mails(infoLogText)
