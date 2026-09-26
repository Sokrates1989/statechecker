## Execute this file to test if tools are up and running.

# Api for listening to bot commands.
import time

# Import own classes.
# Insert path to utils to allow importing them.
import os
import sys
sys.path.insert(1, os.path.join(os.path.dirname(__file__), "utils"))
sys.path.insert(1, os.path.join(os.path.dirname(__file__), "models"))
sys.path.insert(1, os.path.join(os.path.dirname(__file__), "definitions"))

# Own Utils, classes and other imports.
import stateCheckUtils
import stringUtils
import logger as Logger
import databaseWrapper as DatabaseWrapper
import configUtils as ConfigUtils
import emailUtils as EmailUtils
import telegramNotificationUtils
import checkWorkerMessageHandlers
import checkWorkerAlertDelivery

## Initialize vars.

# Get config.
configUtils = ConfigUtils.ConfigUtils()

# Instantiate classes.
# Database connection.
dbWrapper = DatabaseWrapper.DatabaseWrapper()
# Logger.
logger = Logger.Logger("check_tools")

# Initialize bots.
botToken = configUtils.getTelegramBotToken()
errorChatIDs = configUtils.getTelegramErrorChatsIDs()
infoChatIDs = configUtils.getTelegramInfoChatsIDs()

bot = telegramNotificationUtils.create_telegram_bot(configUtils)

# Initialize email messaging.
emailUtils = EmailUtils.EmailUtils()


## Check whether a scheduled countdown has to be sent.

# Only print every xth time, that we are still checking.
printEvery = 100

# When to send messages?
telegramMessageEveryXMinutes = configUtils.getTelegramStatusMessagesEveryXMinutes()
emailMessageEveryXMinutes = configUtils.getEmailStatusMessagesEveryXMinutes()

# How often to check websiteStates.
checkWebsitesEveryXMinutes = configUtils.getWebsiteChecksEveryXMinutes()
# How often to check google drive backups.
checkGoogleDriveEveryXMinutes = configUtils.getGoogleDriveChecksEveryXMinutes()

i = 0
print("checking ...")
checkWorkerMessageHandlers.infoCheckingToolsIsWorking(
    logger=logger,
    configUtils=configUtils,
    bot=bot,
    infoChatIDs=infoChatIDs,
    emailUtils=emailUtils,
    stringUtils=stringUtils,
    stateCheckUtils=stateCheckUtils,
    checkWebsitesEveryXMinutes=checkWebsitesEveryXMinutes,
    telegramMessageEveryXMinutes=telegramMessageEveryXMinutes,
    emailMessageEveryXMinutes=emailMessageEveryXMinutes,
    justStartedChecking=True,
)
while True:
    try:
        # Always recreate database to avoid disconnection error.
        dbWrapper = DatabaseWrapper.DatabaseWrapper()

        ## Info that checking of schedule is still taking place.

        # Increment counter.
        i = i + 1

        # Output to console.
        if (i % printEvery == 0):
            print("checking (" + str(i) + ") ...")

        # Update google drive backup states.
        if (i % checkGoogleDriveEveryXMinutes == 1):
            stateCheckUtils.updateGoogleDriveFolderBackupChecks()

        # Get states of tools.
        toolStateItems_api = stateCheckUtils.getToolStates_api()
        toolStateItems = toolStateItems_api
        toolStateItems += stateCheckUtils.getToolStates_backups()

        # Check websites.
        if (i % checkWebsitesEveryXMinutes == 1):
            toolStateItems += stateCheckUtils.getToolStates_websites()

        # Check the states of the tools.
        for toolStateItem in toolStateItems:

            # Website state describes the last check, regardless of whether an
            # outage or recovery alert has reached Telegram yet.
            checkWorkerAlertDelivery.record_website_check_state(
                toolStateItem, dbWrapper
            )

            # Is the tool up?
            if toolStateItem.toolIsUp == False:

                # Tool is down.

                # Has the error message already been sent?
                if toolStateItem.toolIsDownMessageHasBeenSent == False:

                    # The error message has not been sent yet.
                    # Output info.
                    print("Found tool, that is is down and message has not been sent yet..")
                    print(toolStateItem.name)
                    print("sending mesage now..")

                    # Send the message to the error message channel.
                    toolStateItemIsDownMsg = "Your tool is <b>DOWN!</b> \n\n<b>" + str(toolStateItem.name) + "</b>"
                    toolStateItemIsDownMsg += "" if toolStateItem.description == "" else "\n" + str(
                        toolStateItem.description)
                    toolStateItemIsDownMsg += "" if toolStateItem.statusMessage == "" or toolStateItem.statusMessage == "OK" else "\n" + str(
                        toolStateItem.statusMessage)
                    
                    reply_markup = telegramNotificationUtils.build_admin_inline_keyboard(toolStateItem)
                    checkWorkerAlertDelivery.deliver_alert(
                        tool_state_item=toolStateItem,
                        is_down=True,
                        message=toolStateItemIsDownMsg,
                        db_wrapper=dbWrapper,
                        config_utils=configUtils,
                        bot=bot,
                        error_chat_ids=errorChatIDs,
                        logger=logger,
                        email_utils=emailUtils,
                        telegram_sender=telegramNotificationUtils.safe_send_telegram_message,
                        reply_markup=reply_markup,
                    )
                    


            else:

                # Tool is up.

                # Has there been an error cleared message already ?
                if toolStateItem.toolIsDownMessageHasBeenSent == True:

                    # There has been an error message recently.
                    # Output info.
                    print("Found tool, that is up again..")
                    print(toolStateItem.name)
                    print("sending message now..")

                    # Send the message to the error message channel.
                    toolStateItemIsUpAgainMsg = "Your tool is <b>UP AGAIN!</b> \n\n<b>" + str(
                        toolStateItem.name) + "</b>"
                    toolStateItemIsUpAgainMsg += "" if toolStateItem.description == "" else "\n" + str(
                        toolStateItem.description)
                    toolStateItemIsUpAgainMsg += "" if toolStateItem.statusMessage == "" or toolStateItem.statusMessage == "OK" else "\n" + str(
                        toolStateItem.statusMessage)
                    
                    checkWorkerAlertDelivery.deliver_alert(
                        tool_state_item=toolStateItem,
                        is_down=False,
                        message=toolStateItemIsUpAgainMsg,
                        db_wrapper=dbWrapper,
                        config_utils=configUtils,
                        bot=bot,
                        error_chat_ids=errorChatIDs,
                        logger=logger,
                        email_utils=emailUtils,
                        telegram_sender=telegramNotificationUtils.safe_send_telegram_message,
                    )

        # Send info messages that tool is still checking.
        if (i % telegramMessageEveryXMinutes == 0):
            checkWorkerMessageHandlers.infoCheckingToolsIsWorking(
                logger=logger,
                configUtils=configUtils,
                bot=bot,
                infoChatIDs=infoChatIDs,
                emailUtils=emailUtils,
                stringUtils=stringUtils,
                stateCheckUtils=stateCheckUtils,
                checkWebsitesEveryXMinutes=checkWebsitesEveryXMinutes,
                telegramMessageEveryXMinutes=telegramMessageEveryXMinutes,
                emailMessageEveryXMinutes=emailMessageEveryXMinutes,
                telegramTimeReached=True,
            )
        if (i % emailMessageEveryXMinutes == 0):
            checkWorkerMessageHandlers.infoCheckingToolsIsWorking(
                logger=logger,
                configUtils=configUtils,
                bot=bot,
                infoChatIDs=infoChatIDs,
                emailUtils=emailUtils,
                stringUtils=stringUtils,
                stateCheckUtils=stateCheckUtils,
                checkWebsitesEveryXMinutes=checkWebsitesEveryXMinutes,
                telegramMessageEveryXMinutes=telegramMessageEveryXMinutes,
                emailMessageEveryXMinutes=emailMessageEveryXMinutes,
                emailTimeReached=True,
            )

        # Sleep 60 seconds with calculated offset.
        time.sleep(configUtils.calculateOffset(60))

    except Exception as e:
        checkWorkerMessageHandlers.handleCommandException(
            logger=logger,
            configUtils=configUtils,
            bot=bot,
            errorChatIDs=errorChatIDs,
            emailUtils=emailUtils,
            exceptionLocationAndAdditionalInformation="An Error occured while checking tools: ",
            exception=str(e),
        )

        # Sleep 60 seconds with calculated offset.
        time.sleep(configUtils.calculateOffset(60))
