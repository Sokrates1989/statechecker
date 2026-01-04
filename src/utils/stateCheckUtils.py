## Utilities to get states of tools, that are being checked.

# For accessing google drive.
from __future__ import print_function
from googleapiclient.discovery import build

# For getting current timestamp.
import time
# For making POST / GET requests.
import requests
# For parsing and rewriting URLs.
from urllib.parse import urlparse, urlunparse
# For file operations with operating system.
import os
# For creating files.
import fileUtils

## Own classes.
# Database connection.
import databaseWrapper as DatabaseWrapper
# Convert dateString to unixTimestamp.
import dateStringUtils
# ToolStateItem from own models to use location independent.
# Used to wrap state information about the tools to check.
import toolStateItem as ToolStateItem
# BackupCheckItem from own models to use location independent.
import backupCheckItem as BackupCheckItem
# Website State and Message sent state.
import websiteStateAndMessageSentItem as WebsiteStateAndMessageSentItem
# Logger.
import logger as Logger
# Get configuration settings.
import configUtils as ConfigUtils
configUtils = ConfigUtils.ConfigUtils()

# Path to messageSentStates of custom checks.
messageSentStatesDirectory = os.path.join(os.path.dirname(__file__), "..", "..", "messageSentStates/")


# Get states of tools that are being checked by sending their own alive message to api.
# Returns Array of ToolStateItems. See models for further information.
def getToolStates_api():
    # Array of ToolStateItems.
    toolStateItems = []

    # Database connection.
    dbWrapper = DatabaseWrapper.DatabaseWrapper()

    # Did all tools send a state info within desired timespan?
    now = int(time.time())
    allToolsToCheck = dbWrapper.getAllToolsToCheck()
    if allToolsToCheck:
        for toolToCheck in allToolsToCheck:

            # Has the state info been sent within the desired amount of time?
            if int(toolToCheck.lastTimeToolWasUp) + int(toolToCheck.stateCheckFrequency_inMinutes) * 60 + configUtils.getTolerencePeriodInSeconds() < now:

                # No valid state check withing desired timespan.

                # Add state of tool to return array.
                toolStateItem = ToolStateItem.ToolStateItem(
                    toolToCheck.name,
                    False,  # Tool is up boolean value.
                    toolToCheck.toolIsDownMessageHasBeenSent,
                    toolToCheck.description
                )
                toolStateItem.setCheckFrequency(toolToCheck.stateCheckFrequency_inMinutes)
                toolStateItems.append(toolStateItem)


            else:

                # There is a valid state check withing desired timespan.

                # Add state of tool to return array.
                toolStateItem = ToolStateItem.ToolStateItem(
                    toolToCheck.name,
                    True,  # Tool is up boolean value.
                    toolToCheck.toolIsDownMessageHasBeenSent,
                    toolToCheck.description
                )
                toolStateItem.setCheckFrequency(toolToCheck.stateCheckFrequency_inMinutes)
                toolStateItems.append(toolStateItem)

    # Return states of tools checked by the API.
    return toolStateItems


# Get message for tool states to write in state message.
def getToolStatesMessage():
    # The message to return.
    toolStatesMessage = ""

    # Array of ToolStateItems.
    toolStateItems_api = getToolStates_api()
    toolStateItems_custom = getToolStates_custom()
    toolStateItems = toolStateItems_api + toolStateItems_custom
    for toolStateItem in toolStateItems:

        # Is the tool up?
        if toolStateItem.toolIsUp == False:
            # Tool is down.
            toolStatesMessage += "🔸Tool " + str(toolStateItem.name) + " is <b><u>DOWN!</u></b>"
        else:
            # Tool is up.
            toolStatesMessage += "🔸Tool " + str(toolStateItem.name) + " is <b><u>UP!</u></b>"

        # Add description and statusMessage if not empty and spaces to end of message.
        toolStatesMessage += "" if toolStateItem.description == "" else "\n" + str(toolStateItem.description)
        toolStatesMessage += "" if toolStateItem.statusMessage == "" or toolStateItem.statusMessage == "OK" else "\n" + str(
            toolStateItem.statusMessage)
        toolStatesMessage += "" if toolStateItem.checkingEveryXMinutes == None else "\nChecking state every <b>" + str(
            toolStateItem.checkingEveryXMinutes) + "</b> minutes"
        toolStatesMessage += "\n\n"

    return toolStatesMessage


# Get states of tools that are being checked manually from here.
# Returns Array of ToolStateItems. See models for further information.
def getToolStates_custom():
    # Array of ToolStateItems.
    toolStateItems = []

    # Check website states for felicitas wisdom.
    toolStateItems += getToolStates_websites()
    toolStateItems += getToolStates_backups()

    # Return states of tools checked by the API.
    return toolStateItems


# Get states of websites.
# Returns Array of ToolStateItems. See models for further information.
def getToolStates_websites():
    # Array of ToolStateItems.
    toolStateItems = []

    # Database connection.
    dbWrapper = DatabaseWrapper.DatabaseWrapper()

    # Check all website urls.
    urls = configUtils.getWebsitesToCheck()
    for url in urls:

        # Create website item in db if not exists.
        dbWrapper.createNewWebsiteCheck(WebsiteStateAndMessageSentItem.WebsiteStateAndMessageSentItem(url, "Up", False))

        # Get previous check state.
        websiteStateAndMessageSent = dbWrapper.getWebsiteCheckItemByName(url)

        # Try to call website.
        try:
            urls_to_try = [url]
            parsed = urlparse(url)
            if parsed.hostname in ("localhost", "127.0.0.1") and parsed.scheme in ("http", "https"):
                host = "host.docker.internal"
                port = parsed.port
                if port is None:
                    port = 443 if parsed.scheme == "https" else 80
                urls_to_try.append(
                    urlunparse(
                        parsed._replace(
                            netloc=f"{host}:{port}",
                        )
                    )
                )

            x = None
            last_exc = None
            for try_url in urls_to_try:
                try:
                    x = requests.get(try_url, timeout=10, allow_redirects=True)
                    break
                except Exception as exc:
                    last_exc = exc
                    x = None

            if x is None:
                raise last_exc if last_exc is not None else RuntimeError("request failed")

            # Is website considered up?
            websiteIsUp = True if int(x.status_code) < 400 else False

            # Add state of tool to return array.
            toolStateItem = ToolStateItem.ToolStateItem(
                url,
                websiteIsUp,  # Tool is up boolean value.
                websiteStateAndMessageSent.isMessageIsDownMessageLastSentMessage()
            )
            toolStateItem.setStatusMessage(x.reason)
            toolStateItem.indicateThatToolIsCustom()
            toolStateItems.append(toolStateItem)
        except Exception as e:
            # Add state of tool to return array.
            toolStateItem = ToolStateItem.ToolStateItem(
                url,
                False,  # Tool is up boolean value.
                websiteStateAndMessageSent.isMessageIsDownMessageLastSentMessage()
            )
            toolStateItem.setStatusMessage("An Error was thrown trying to make request")
            toolStateItem.indicateThatToolIsCustom()
            toolStateItems.append(toolStateItem)

    # Return states of tools checked by the API.
    return toolStateItems


# Get states of backups.
# Returns Array of ToolStateItems. See models for further information.
def getToolStates_backups():
    # Array of ToolStateItems.
    backupStateItems = []

    # Database connection.
    dbWrapper = DatabaseWrapper.DatabaseWrapper()

    # Did all tools send a state info within desired timespan?
    now = int(time.time())
    allBackupsToCheck = dbWrapper.getAllBackupsToCheck()
    if allBackupsToCheck:
        for backupToCheck in allBackupsToCheck:

            # Has the state info been sent within the desired amount of time?
            if int(backupToCheck.mostRecentBackupFile_creationDate) + int(
                    backupToCheck.stateCheckFrequency_inMinutes) * 65 < now:

                # No valid state check withing desired timespan.

                # Add state of tool to return array.
                toolStateItem = ToolStateItem.ToolStateItem(
                    backupToCheck.name,
                    False,  # Tool is up boolean value.
                    backupToCheck.backupIsDownMessageHasBeenSent,
                    backupToCheck.description
                )
                toolStateItem.indicateThatToolIsBackup()
                toolStateItem.setCheckFrequency(backupToCheck.stateCheckFrequency_inMinutes)
                backupStateItems.append(toolStateItem)


            else:

                # There is a valid state check withing desired timespan.

                # Add state of tool to return array.
                toolStateItem = ToolStateItem.ToolStateItem(
                    backupToCheck.name,
                    True,  # Tool is up boolean value.
                    backupToCheck.backupIsDownMessageHasBeenSent,
                    backupToCheck.description
                )
                toolStateItem.indicateThatToolIsBackup()
                toolStateItem.setCheckFrequency(backupToCheck.stateCheckFrequency_inMinutes)
                backupStateItems.append(toolStateItem)

    # Return states of tools checked by the API.
    return backupStateItems


# Check Google Drive folders and add them to backup checks.
# Similar behaviour as sending request to "/v1/backupcheck", but done directly from the server.
# MAKE SURE THAT FOLDER IS GIVEN READ RIGHTS TO ACCOUNT THAT HOLDS CREDENTIALS.
# (See previously working folder's rights in Google Drive for more info)
def updateGoogleDriveFolderBackupChecks():
    """Update backup checks by reading newest files from configured Google Drive folders.

    If Google Drive folders are configured but credentials are missing, this function
    logs an error and exits.
    """

    try:

        # Are there any googleDriveFolders to check?
        googleDriveFoldersToCheck = configUtils.getGoogleDriveFoldersToCheck()
        if googleDriveFoldersToCheck:
        
            # Database connection.
            dbWrapper = DatabaseWrapper.DatabaseWrapper()

            # Connect to google drive.
            credentials = configUtils.getGoogleDriveServiceAccountCredentials()
            if not credentials:
                logger = Logger.Logger("check_tools")
                logger.logError(
                    "Google Drive folders are configured, but no Google Drive credentials are available. "
                    "Set GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON_FILE (path to JSON secret file) or provide "
                    "service_account_key.json in the repository root for local testing."
                )
                return
            service = build('drive', 'v3', credentials=credentials)

            # Check all Google Drive folders of config.
            for googleDriveFolder in googleDriveFoldersToCheck:

                items = []
                pageToken = ""
                while pageToken is not None:
                    response = service.files().list(q="'" + googleDriveFolder["folderID"] + "' in parents", pageSize=1000,
                                                    pageToken=pageToken,
                                                    fields="nextPageToken, files(kind, id, name, createdTime, md5Checksum)").execute()
                    items.extend(response.get('files', []))
                    pageToken = response.get('nextPageToken')

                # Sort files by their creation date (newest files first).
                items.sort(key=getCreationDate, reverse=True)

                if items:
                    backupCheckItem = BackupCheckItem.BackupCheckItem(
                        googleDriveFolder["name"],
                        googleDriveFolder["token"],
                        googleDriveFolder["stateCheckFrequency_inMinutes"],
                        dateStringUtils.convertGoogleDriveDateStringToUnixTimeStamp(items[0]["createdTime"]),
                        items[0]["md5Checksum"],
                        googleDriveFolder["description"]
                    )
                    dbWrapper.createOrUpdateBackupCheck(backupCheckItem)
                else:
                    backupCheckItem = BackupCheckItem.BackupCheckItem(
                        googleDriveFolder["name"],
                        googleDriveFolder["token"],
                        googleDriveFolder["stateCheckFrequency_inMinutes"],
                        "0",
                        "no items",
                        googleDriveFolder["description"]
                    )
                    dbWrapper.createOrUpdateBackupCheck(backupCheckItem)
    
    # In case of any Error: Log and print errror.
    except Exception as e:
        logger = Logger.Logger("check_tools")
        errormsg = f"stateCheckUtils.updateGoogleDriveFolderBackupChecks(). Error trying to update google drive backup state: {e}"
        logger.logError(errormsg)



# Sort files by their creation date -> get creation date of item.
def getCreationDate(elem):
    return elem["createdTime"]


# Write state of sent message to file.
def writeMessageHasBeenSentStateToFile(toolStateItem, websiteState):
    fileNameForMessageSentState = fileUtils.getValidFileNameForString(toolStateItem.name, "txt")
    messageSentStateFile = os.path.join(messageSentStatesDirectory, fileNameForMessageSentState)
    fileUtils.createFileIfNotExists(messageSentStateFile)
    websiteMessageState = WebsiteStateAndMessageSentItem.WebsiteStateAndMessageSentItem(websiteState=websiteState,
                                                                                        messageHasBeenSent=True)
    fileUtils.overwriteContentOfFile(messageSentStateFile, websiteMessageState.toJson())
