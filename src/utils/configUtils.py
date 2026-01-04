## Config operations like getting config array or other config Values.

# For accessing google drive.
from __future__ import print_function
from oauth2client.service_account import ServiceAccountCredentials

# Interaction with operating system (read write files).
import os

# For getting config.
import json

# String verification.
import re

# For making time timezone aware.
import pytz

# For safely parsing json string to dict (https://stackoverflow.com/questions/988228/convert-a-string-representation-of-a-dictionary-to-a-dictionary).
import ast

import configFileManager as ConfigFileManager


class ConfigUtils:
    """
    Get any configuration settings.
    """
    # Constructor creating logfiles and paths.
    def __init__(self):
          
        try:
            config_file_pathAndName = str(ConfigFileManager.resolve_config_file_path())
            config_file = open(config_file_pathAndName)
            self._config_array = json.load(config_file)
            try:
                ConfigFileManager.ensure_original_backup_exists()
            except Exception:
                pass
        except:
            # Get config array from Environment Variable.
            statechecker_server_config = os.getenv("STATECHECKER_SERVER_CONFIG")
            if statechecker_server_config:
                self._config_array = json.loads(statechecker_server_config)
            else:
                # If neither the file nor the environment variable is found, raise an error or handle it appropriately
                raise ValueError("configUtils: Could not get config array from config.txt nor environment variable STATECHECKER_SERVER_CONFIG")


    def getConfigArray(self):
        """
        Get the configuration array.

        Just for debugging. Please use direct methods for individual configuration items.

        Returns:
            (array): Confiuration array.
        """
        return self._config_array
    

    def getTolerencePeriodInSeconds(self):
        """
        Get tools using api tolerence period in seconds.

        Returns:
            (int): Tolerence period in seconds.
        """
        tools_using_api_tolerance_period_in_seconds=os.getenv("TOOLS_USING_API_TOLERANCE_PERIOD_IN_SECONDS")
        if tools_using_api_tolerance_period_in_seconds:
            tools_using_api_tolerance_period_in_seconds = tools_using_api_tolerance_period_in_seconds.strip().strip("\"")
        else:
            if "toolsUsingApi_tolerancePeriod_inSeconds" in self._config_array:
                tools_using_api_tolerance_period_in_seconds = self._config_array["toolsUsingApi_tolerancePeriod_inSeconds"]
        return int(tools_using_api_tolerance_period_in_seconds)
    

    def getWebsitesToCheck(self):
        """
        Get websites to check.

        Returns:
            (array): Websites to check.
        """
        websites_to_check=os.getenv("WEBSITES_TO_CHECK")
        if websites_to_check:
            websites_to_check = [item.strip() for item in websites_to_check.strip().strip("\"").split(',')]
        else:
            config_source = self._config_array
            if ConfigFileManager.is_file_based_config_available():
                try:
                    config_source = ConfigFileManager.load_config()
                except Exception:
                    config_source = self._config_array
            if "websites" in config_source:
                if "websitesToCheck" in config_source["websites"]:
                    websites_to_check = config_source["websites"]["websitesToCheck"]
        return websites_to_check


    def getIgnoredToolsUsingApi(self):
        """Get a list of API tools that should be ignored (admin-disabled).

        Note:
            Deprecated: statechecker no longer uses a persisted ignore list for
            "unwatch" semantics. Unwatching now deletes the tool from the DB and
            the tool will re-appear automatically when the client sends a new ping.

        Returns:
            list: A list of tool names to ignore.
        """

        config_source = self._config_array
        if ConfigFileManager.is_file_based_config_available():
            try:
                config_source = ConfigFileManager.load_config()
            except Exception:
                config_source = self._config_array

        ignored = []
        if "ignoredToolsUsingApi" in config_source:
            ignored = config_source.get("ignoredToolsUsingApi")
        return ignored if isinstance(ignored, list) else []


    def getToolsUsingApiFrequencyOverrides(self):
        """Get frequency overrides for API tools.

        The override map is stored in config.txt under `toolsUsingApi_frequencyOverrides`.
        If present, the server will enforce the configured frequency even if
        clients send a different one.

        Returns:
            dict: Mapping {tool_name: frequency_in_minutes}.
        """

        config_source = self._config_array
        if ConfigFileManager.is_file_based_config_available():
            try:
                config_source = ConfigFileManager.load_config()
            except Exception:
                config_source = self._config_array

        overrides = config_source.get("toolsUsingApi_frequencyOverrides") if isinstance(config_source, dict) else None
        return overrides if isinstance(overrides, dict) else {}


    def getBackupFrequencyOverrides(self):
        """Get frequency overrides for backups.

        The override map is stored in config.txt under `backupFrequencyOverrides`.

        Returns:
            dict: Mapping {backup_name: frequency_in_minutes}.
        """

        config_source = self._config_array
        if ConfigFileManager.is_file_based_config_available():
            try:
                config_source = ConfigFileManager.load_config()
            except Exception:
                config_source = self._config_array

        overrides = config_source.get("backupFrequencyOverrides") if isinstance(config_source, dict) else None
        return overrides if isinstance(overrides, dict) else {}


    def getIgnoredBackups(self):
        """Get a list of backups that should be ignored (admin-disabled).

        Note:
            Deprecated: statechecker no longer uses a persisted ignore list for
            "unwatch" semantics. Unwatching now deletes the backup from the DB and
            the backup will re-appear automatically when the client sends a new ping.

        Returns:
            list: A list of backup names to ignore.
        """

        config_source = self._config_array
        if ConfigFileManager.is_file_based_config_available():
            try:
                config_source = ConfigFileManager.load_config()
            except Exception:
                config_source = self._config_array

        ignored = []
        if "ignoredBackups" in config_source:
            ignored = config_source.get("ignoredBackups")
        return ignored if isinstance(ignored, list) else []


    
    ## DB Con ##
    def getDatabaseHost(self):
        """
        Get database host.

        Returns:
            (str): Host where db is.
        """
        db_host=os.getenv("DB_HOST")
        if db_host:
            db_host = db_host.strip().strip("\"")
        else:
            if "database" in self._config_array:
                if "host" in self._config_array["database"]:
                    db_host = self._config_array["database"]["host"]
        return db_host
    
    def getDatabaseUser(self):
        """
        Get database user.

        Returns:
            (str): Database user.
        """
        db_user=os.getenv("DB_USER")
        if db_user:
            db_user = db_user.strip().strip("\"")
        else:
            if "database" in self._config_array:
                if "user" in self._config_array["database"]:
                    db_user = self._config_array["database"]["user"]
        return db_user
    
    def getDatabasePassword(self):
        """
        Get database password.

        Returns:
            (str): Database password of database user.
        """
        db_pw=""
        try:
            DB_PW_FILE = os.getenv("DB_PW_FILE")
            with open(f"{DB_PW_FILE}", "r") as db_pw_file:
                db_pw = db_pw_file.read().strip()
        except:
            pass
        finally:
            # In case of an error or the secret is not set.
            if not db_pw or db_pw.lower() == "none":
                db_pw = os.getenv('DB_PW').strip().strip("\"")
        if not db_pw or db_pw == "":
            # Get PW from config.
            if "database" in self._config_array:
                if "password" in self._config_array["database"]:
                    db_pw = self._config_array["database"]["password"]

        return db_pw
    
    def getDatabaseName(self):
        """
        Get database name.

        Returns:
            (str): Name of database.
        """
        db_name=os.getenv("DB_NAME")
        if db_name:
            db_name = db_name.strip().strip("\"")
        else:
            if "database" in self._config_array:
                if "database" in self._config_array["database"]:
                    db_name = self._config_array["database"]["database"]
        return db_name
    
    # Telegram settings.
    def areTelegramStatusMessagesEnabled(self):
        """
        Are telgram status messages enabled?

        Returns:
            (bool): Whether telegram status messages are enabled.
        """
        areTelegramStatusMessagesEnabled=os.getenv("TELEGRAM_ENABLED")
        if areTelegramStatusMessagesEnabled:
            areTelegramStatusMessagesEnabled = areTelegramStatusMessagesEnabled.strip().strip("\"").lower() == "true"
        else:
            areTelegramStatusMessagesEnabled = True
            if "telegram" in self._config_array:
                if "enabled" in self._config_array["telegram"]:
                        areTelegramStatusMessagesEnabled = self._config_array["telegram"]["enabled"].strip().strip("\"").lower() == "true"
        return bool(areTelegramStatusMessagesEnabled)
    

    def getTelegramStatusMessagesEveryXMinutes(self):
        """
        Get amount of minutes when to send telegram status messages.

        Send telegram status messages every x minutes based on this value.

        Returns:
            (int): Amount of minutes between each telegram status message.
        """
        telegramStatusMessageEveryXMinutes=os.getenv("TELEGRAM_STATUS_MESSAGES_EVERY_X_MINUTES")
        if telegramStatusMessageEveryXMinutes:
            telegramStatusMessageEveryXMinutes = telegramStatusMessageEveryXMinutes.strip().strip("\"")
        else:
            if "telegram" in self._config_array:
                if "adminStatusMessage_everyXMinutes" in self._config_array["telegram"]:
                    telegramStatusMessageEveryXMinutes = self._config_array["telegram"]["adminStatusMessage_everyXMinutes"]

        return int(telegramStatusMessageEveryXMinutes)
    

    def getTelegramBotToken(self):
        """
        Get telegram bot token.

        Returns:
            (str): Token for the bot.
        """
        bot_token=""
        try:
            TELEGRAM_SENDER_BOT_TOKEN_FILE = os.getenv("TELEGRAM_SENDER_BOT_TOKEN_FILE")
            with open(f"{TELEGRAM_SENDER_BOT_TOKEN_FILE}", "r") as bot_token_file:
                bot_token = bot_token_file.read().strip()
        except:
            pass
        finally:
            # In case of an error or the secret is not set.
            if not bot_token or bot_token.lower() == "none":
                bot_token = os.getenv('TELEGRAM_SENDER_BOT_TOKEN').strip().strip("\"")
        if not bot_token or bot_token == "":
            # Get PW from config.
            if "telegram" in self._config_array:
                if "botToken" in self._config_array["telegram"]:
                    bot_token = self._config_array["telegram"]["botToken"]

        return bot_token



    def getTelegramErrorChatsIDs(self):
        """
        Get chat ids to send error messages to.

        Returns:
            (array): Chat ids for errors.
        """
        errorChatIDs=os.getenv("TELEGRAM_RECIPIENTS_ERROR_CHAT_IDS")
        if errorChatIDs:
            errorChatIDs, warnings = self._get_telegram_array_from_telegram_chats_list_string(errorChatIDs)
        else:
            if "telegram" in self._config_array:
                if "errorChatIDs" in self._config_array["telegram"]:
                    errorChatIDs, warnings = self._get_telegram_array_from_telegram_chats_list_string(self._config_array["telegram"]["errorChatIDs"].strip().strip("\""))
                elif "errorChatID" in self._config_array["telegram"]:
                    errorChatIDs=[]
                    errorChatIDs.append(self._config_array["telegram"]["errorChatID"])
        return errorChatIDs


    def getTelegramInfoChatsIDs(self):
        """
        Get chat ids to send info messages to.

        Returns:
            (array): Chat ids for info messages.
        """
        infoChatIDs=os.getenv("TELEGRAM_RECIPIENTS_INFO_CHAT_IDS")
        if infoChatIDs:
            infoChatIDs, warnings = self._get_telegram_array_from_telegram_chats_list_string(infoChatIDs)
        else:
            if "telegram" in self._config_array:
                if "infoChatIDs" in self._config_array["telegram"]:
                    infoChatIDs, warnings = self._get_telegram_array_from_telegram_chats_list_string(self._config_array["telegram"]["infoChatIDs"].strip().strip("\""))
                elif "infoChatID" in self._config_array["telegram"]:
                    infoChatIDs=[]
                    infoChatIDs.append(self._config_array["telegram"]["infoChatID"])
        return infoChatIDs



    def _get_telegram_array_from_telegram_chats_list_string(self, telegram_chats_list_string):
        """
        Extracts an array of telegram chat ids from a comma-separated string of telegram chat ids.

        Args:
        - telegram_chats_list_string (str): A comma-separated string containing telegram chat ids.

        Returns:
        A tuple consisting of:
        - valid_telegram_chats (list): A list of valid telegram chat ids extracted from the input string.
        - warnings (list): A list of warnings generated during the process, such as invalid telegram chat ids.
        """
        warnings = []  # A list to store any warnings encountered during processing.
        valid_telegram_chats = []  # A list to store valid telegram chat ids.

        try:
            # If the input string is empty or 'None', return empty lists.
            if not telegram_chats_list_string or telegram_chats_list_string.lower() == "none":
                return valid_telegram_chats, warnings

            # Split the string by commas and strip any whitespace from each chat id.
            telegram_array = [telegram.strip() for telegram in telegram_chats_list_string.split(',')]

            # Validate each telegram in the array
            for telegram_chat_id in telegram_array:
                if self._is_telegram_chat_id_valid(telegram_chat_id):
                    valid_telegram_chats.append(telegram_chat_id)
                else:
                    # If an telegram is invalid, add a warning to the list.
                    warnings.append(f"Invalid Telegram Chat ID: <EMPHASIZE_STRING_START_TAG>{telegram_chat_id}</EMPHASIZE_STRING_END_TAG> was not added to the recipients.")

            return valid_telegram_chats, warnings
            
        except Exception as e:
            # If any unexpected error occurs, add a warning with details.
            warnings.append(f"Error extracting telegram chat ids from string <EMPHASIZE_STRING_START_TAG>{telegram_chats_list_string}</EMPHASIZE_STRING_END_TAG>: {str(e)}")
            return valid_telegram_chats, warnings
        

    def _is_telegram_chat_id_valid(self, chat_id):
        """
        Check if the given telegram chat id is valid.
        """
        chat_id_regex = r'^-?\d+$'  # An optional negative sign followed by one or more digits
        return re.match(chat_id_regex, str(chat_id)) is not None

    

    # Status Messages.
    def _getStatusMessagesTimeOffsetPercentage(self):
        """
        Get time offset besed on the amount of time the calculation handling takes, to make every x minutes more accurate.

        Returns:
            (float): percentage value to adjust time every x minutes.
        """
        telegramStatusMessageEveryXMinutes=os.getenv("STATUS_MESSAGES_TIME_OFFSET_PERCENTAGE")
        if telegramStatusMessageEveryXMinutes:
            telegramStatusMessageEveryXMinutes = telegramStatusMessageEveryXMinutes.strip().strip("\"")
        else:
            if "adminStatusMessage_operationTime_offsetPercentage" in self._config_array:
                    telegramStatusMessageEveryXMinutes = self._config_array["adminStatusMessage_operationTime_offsetPercentage"]
            elif "telegram" in self._config_array:
                if "adminStatusMessage_operationTime_offsetPercentage" in self._config_array["telegram"]:
                    telegramStatusMessageEveryXMinutes = self._config_array["telegram"]["adminStatusMessage_operationTime_offsetPercentage"]
        return float(telegramStatusMessageEveryXMinutes)
    
    

    # Email.
    def areEmailStatusMessagesEnabled(self):
        """
        Are email status messages enabled?

        Returns:
            (bool): Whether email status messages are enabled.
        """
        areEmailStatusMessagesEnabled=os.getenv("EMAIL_ENABLED")
        if areEmailStatusMessagesEnabled:
            areEmailStatusMessagesEnabled = areEmailStatusMessagesEnabled.strip().strip("\"").lower() == "true"
        else:
            areEmailStatusMessagesEnabled = False
            if "email" in self._config_array:
                if "enabled" in self._config_array["email"]:
                        areEmailStatusMessagesEnabled = self._config_array["email"]["enabled"].strip().strip("\"").lower() == "true"
        return bool(areEmailStatusMessagesEnabled)
    
    
    def getEmailSenderUser(self):
        """
        Get email sender user.

        Returns:
            (str): User for smtp email sender.
        """
        email_sender_user=os.getenv("EMAIL_SENDER_USER")
        if email_sender_user:
            email_sender_user = email_sender_user.strip().strip("\"")
        else:
            email_sender_user = ""
            if "email" in self._config_array:
                if "sender" in self._config_array["email"]:
                    if "user" in self._config_array["email"]["sender"]:
                        email_sender_user = self._config_array["email"]["sender"]["user"]
        return email_sender_user
    
    
    def getEmailSenderPassword(self):
        """
        Get email sender password.

        Returns:
            (str): User for smtp email sender.
        """
        email_sender_password=""
        try:
            EMAIL_SENDER_PASSWORD_FILE = os.getenv("EMAIL_SENDER_PASSWORD_FILE")
            with open(f"{EMAIL_SENDER_PASSWORD_FILE}", "r") as email_sender_password_file:
                email_sender_password = email_sender_password_file.read().strip()
        except:
            pass
        finally:
            # In case of an error or the secret is not set.
            if not email_sender_password or email_sender_password.lower() == "none":
                email_sender_password = os.getenv('EMAIL_SENDER_PASSWORD').strip().strip("\"")
        if not email_sender_password or email_sender_password == "":
            # Get PW from config.
            email_sender_password = ""
            if "email" in self._config_array:
                if "sender" in self._config_array["email"]:
                    if "password" in self._config_array["email"]["sender"]:
                        email_sender_password = self._config_array["email"]["sender"]["password"]
                    
        return email_sender_password
    
    
    def getEmailSenderHost(self):
        """
        Get email sender host.

        Returns:
            (str): Host for smtp email sender.
        """
        email_sender_host=os.getenv("EMAIL_SENDER_HOST")
        if email_sender_host:
            email_sender_host = email_sender_host.strip().strip("\"")
        else:
            email_sender_host = ""
            if "email" in self._config_array:
                if "sender" in self._config_array["email"]:
                    if "host" in self._config_array["email"]["sender"]:
                        email_sender_host = self._config_array["email"]["sender"]["host"]
        return email_sender_host
    
    
    def getEmailSenderPort(self):
        """
        Get email sender port.

        Returns:
            (str): Port for smtp email sender.
        """
        email_sender_port=os.getenv("EMAIL_SENDER_PORT")
        if email_sender_port:
            email_sender_port = email_sender_port.strip().strip("\"")
        else:
            email_sender_port = ""
            if "email" in self._config_array:
                if "sender" in self._config_array["email"]:
                    if "port" in self._config_array["email"]["sender"]:
                        email_sender_port = self._config_array["email"]["sender"]["port"]
        return int(email_sender_port)
    
    

    def getEmailErrorAdresses(self):
        """
        Get email adresses to send error messages to.

        Returns:
            (array): Email adresses for errors.
        """
        errorMailAddresses=os.getenv("EMAIL_RECIPIENTS_ERROR")
        if errorMailAddresses:
            errorMailAddresses, warnings = self._get_email_array_from_emails_list_string(errorMailAddresses)
        else:
            if "email" in self._config_array:
                if "recipients" in self._config_array["email"]:
                    if "error" in self._config_array["email"]["recipients"]:
                        errorMailAddresses, warnings = self._get_email_array_from_emails_list_string(self._config_array["email"]["recipients"]["error"].strip().strip("\""))
        return errorMailAddresses


    def getEmailInfoAdresses(self):
        """
        Get email adresses to send info messages to.

        Returns:
            (array): Email adresses for info messages.
        """
        infoMailAddresses=os.getenv("EMAIL_RECIPIENTS_INFORMATION")
        if infoMailAddresses:
            infoMailAddresses, warnings = self._get_email_array_from_emails_list_string(infoMailAddresses)
        else:
            if "email" in self._config_array:
                if "recipients" in self._config_array["email"]:
                    if "info" in self._config_array["email"]["recipients"]:
                        infoMailAddresses, warnings = self._get_email_array_from_emails_list_string(self._config_array["email"]["recipients"]["info"].strip().strip("\""))
        return infoMailAddresses

    
    def getEmailStatusMessagesEveryXMinutes(self):
        """
        Get amount of minutes when to send email status messages.

        Send email status messages every x minutes based on this value.

        Returns:
            (int): Amount of minutes between each email status message.
        """
        emailStatusMessageEveryXMinutes=os.getenv("EMAIL_STATUS_MESSAGES_EVERY_X_MINUTES")
        if emailStatusMessageEveryXMinutes:
            emailStatusMessageEveryXMinutes = emailStatusMessageEveryXMinutes.strip().strip("\"")
        else:
            emailStatusMessageEveryXMinutes = 60
            if "email" in self._config_array:
                if "adminStatusMessage_everyXMinutes" in self._config_array["email"]:
                    emailStatusMessageEveryXMinutes = self._config_array["email"]["adminStatusMessage_everyXMinutes"]
        return int(emailStatusMessageEveryXMinutes)
    
    

    def _get_email_array_from_emails_list_string(self, emails_list_string):
        """
        Extracts an array of emails from a comma-separated string of emails.

        Args:
        - emails_list_string (str): A comma-separated string containing email addresses.

        Returns:
        A tuple consisting of:
        - valid_emails (list): A list of valid email addresses extracted from the input string.
        - warnings (list): A list of warnings generated during the process, such as invalid emails.
        """
        warnings = []  # A list to store any warnings encountered during processing.
        valid_emails = []  # A list to store valid email addresses.

        try:
            # If the input string is empty or 'None', return empty lists.
            if not emails_list_string or emails_list_string.lower() == "none":
                return valid_emails, warnings

            # Split the string by commas and strip any whitespace from each .
            email_array = [email.strip() for email in emails_list_string.split(',')]

            # Validate each email in the array
            for email in email_array:
                if self._is_email_valid(email):
                    valid_emails.append(email)
                else:
                    # If an email is invalid, add a warning to the list.
                    warnings.append(f"Invalid Email: <EMPHASIZE_STRING_START_TAG>{email}</EMPHASIZE_STRING_END_TAG> was not added to the recipients.")

            return valid_emails, warnings
            
        except Exception as e:
            # If any unexpected error occurs, add a warning with details.
            warnings.append(f"Error extracting emails from string <EMPHASIZE_STRING_START_TAG>{emails_list_string}</EMPHASIZE_STRING_END_TAG>: {str(e)}")
            return valid_emails, warnings

    def _is_email_valid(self, email):
        """Check if the given email address is valid."""
        email_regex = r'^[\w\.-]+@[a-zA-Z\d\.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_regex, email) is not None


    # Check Frequency.
    def getWebsiteChecksEveryXMinutes(self):
        """How often to check websiteStates?

        Returns:
            (int): Amount of minutes between each website checks.
        """
        websiteChecksEveryXMinutes=os.getenv("CHECK_WEBSITES_EVERY_X_MINUTES")
        if websiteChecksEveryXMinutes:
            websiteChecksEveryXMinutes = websiteChecksEveryXMinutes.strip().strip("\"")
        else:
            websiteChecksEveryXMinutes = 30
            config_source = self._config_array
            if ConfigFileManager.is_file_based_config_available():
                try:
                    config_source = ConfigFileManager.load_config()
                except Exception:
                    config_source = self._config_array
            if "websites" in config_source:
                if "checkWebSitesEveryXMinutes" in config_source["websites"]:
                    websiteChecksEveryXMinutes = config_source["websites"]["checkWebSitesEveryXMinutes"]
        return int(websiteChecksEveryXMinutes)


    # Google Drive.
    def getGoogleDriveFoldersToCheck(self):
        """Get google drive folders to check.

        Returns:
            (array): Google drive folders to check.
        """
        config_source = self._config_array
        if ConfigFileManager.is_file_based_config_available():
            try:
                config_source = ConfigFileManager.load_config()
            except Exception:
                config_source = self._config_array

        foldersToCheck = []
        if "googleDrive" in config_source:
            if "foldersToCheck" in config_source["googleDrive"]:
                foldersToCheck = config_source["googleDrive"]["foldersToCheck"]
        return foldersToCheck


    def getGoogleDriveServiceAccountCredentials(self):
        """Get google drive service account credentials.

        Returns:
            (credentials|None): Google drive service account credentials, or None if
            Google Drive is not configured.
        """
        scope = ['https://www.googleapis.com/auth/drive.metadata.readonly']
        swarm_credentials_secret_json = os.getenv("GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON_FILE")
        if not swarm_credentials_secret_json:
            return None

        swarm_credentials_secret_json = swarm_credentials_secret_json.strip().strip("\"")
        if swarm_credentials_secret_json.lower() == "none":
            return None

        # If deployed via swarm -> use secret file, if not use service_account_key.json nin main directory.
        if swarm_credentials_secret_json == "/run/secrets/SET THIS ENVIRONMENT VAR IN SWARM DEPLOY ENVIRONMENTS":
            if not os.path.exists("service_account_key.json"):
                return None
            try:
                return ServiceAccountCredentials.from_json_keyfile_name('service_account_key.json', scope)
            except Exception:
                return None

        if not os.path.exists(swarm_credentials_secret_json):
            return None

        try:
            with open(f"{swarm_credentials_secret_json}", "r") as googleDriveServiceAccountJson_file:
                raw = googleDriveServiceAccountJson_file.read().strip()
                if not raw or raw.lower() == "none":
                    return None
                googleDriveServiceAccountJson_dict = ast.literal_eval(raw)
                return ServiceAccountCredentials.from_json_keyfile_dict(googleDriveServiceAccountJson_dict, scope)
        except Exception:
            return None


    def getGoogleDriveChecksEveryXMinutes(self):
        """How often to check google drive folders?

        Returns:
            (int): Amount of minutes between each goolge drive folder checks.
        """
        googleDriveChecksEveryXMinutes=os.getenv("CHECK_GOOGLEDRIVE_EVERY_X_MINUTES")
        if googleDriveChecksEveryXMinutes:
            googleDriveChecksEveryXMinutes = googleDriveChecksEveryXMinutes.strip().strip("\"")
        else:
            googleDriveChecksEveryXMinutes = 60
            config_source = self._config_array
            if ConfigFileManager.is_file_based_config_available():
                try:
                    config_source = ConfigFileManager.load_config()
                except Exception:
                    config_source = self._config_array
            if "googleDrive" in config_source:
                if "checkFilesEveryXMinutes" in config_source["googleDrive"]:
                    googleDriveChecksEveryXMinutes = config_source["googleDrive"]["checkFilesEveryXMinutes"]
        return int(googleDriveChecksEveryXMinutes)


    # Other methods.
    def calculateOffset(self, base_to_calulate_offset_from):
        """Calculate reduced time based on provided offset.

        Offset is caused from the time consumed by operation time of checking tools.

        Args:
        - base_to_calulate_offset_from (int): The base value to calculate offset of.

        Returns:
            (float): Minutes with calculated offset.
        """
        calculated_value_with_offset = float(base_to_calulate_offset_from - (
                    base_to_calulate_offset_from * self._getStatusMessagesTimeOffsetPercentage() / 100))
        # Avoid zero devision error.
        if calculated_value_with_offset <= 0:
            calculated_value_with_offset = 1

        return float(calculated_value_with_offset)


    def getTimezone(self):
        """Get the timezone based on the environment variable TIMEZONE.

        View all valid timezones: https://mljar.com/blog/list-pytz-timezones/

        Returns:
            pytz.timezone: A pytz timezone object representing the timezone.
        """
        # Default timezone to UTC.
        timezone = 'Etc/UTC'
        try:
            # Try to get the timezone from the environment variable.
            timezone = os.getenv("TIMEZONE")
        except Exception as e:
            # Log a warning if timezone could not be retrieved from environment.
            pass
        finally:
            # Check if the provided timezone is valid.
            if timezone not in pytz.all_timezones:
                # Log a warning if the timezone is invalid and default to UTC.
                timezone = "Etc/UTC"

        # Return the timezone object.
        return pytz.timezone(timezone)


    def getServerAuthenticationToken(self):
        """Get token required to talk to api.

        Returns:
            (str): Server authentication token.
        """
        server_auth_token=""
        try:
            SERVER_AUTHENTICATION_TOKEN_FILE = os.getenv("SERVER_AUTHENTICATION_TOKEN_FILE")
            with open(f"{SERVER_AUTHENTICATION_TOKEN_FILE}", "r") as server_auth_token_file:
                server_auth_token = server_auth_token_file.read().strip()
        except:
            pass
        finally:
            # In case of an error or the secret is not set.
            if not server_auth_token or server_auth_token == "" or server_auth_token.lower() == "none":
                server_auth_token = os.getenv('SERVER_AUTHENTICATION_TOKEN').strip().strip("\"")
        if not server_auth_token or server_auth_token == "":
            # Get PW from config.
            server_auth_token = ""
            if "serverAuthenticationToken" in self._config_array:
                server_auth_token = self._config_array["serverAuthenticationToken"]
                
        return server_auth_token
