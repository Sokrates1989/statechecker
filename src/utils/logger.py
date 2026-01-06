"""Module: logger.py

Description:
    Logging utilities for the statechecker server.

    Logs information and errors to both day-based files and global log files.
    Supports different service scopes: api, check, bot, web.
"""

## Imports.
# For file operations with operating system.
import os
import sys

## Own Modules.
# For creating files.
import fileUtils
# For getting datestrings.
import dateStringUtils


# Service scope configuration for log prefixes
SERVICE_SCOPES = {
    "api": {
        "info": "API_INFO",
        "warning": "API_WARNING",
        "error": "API_ERROR",
    },
    "check": {
        "info": "CHECK_INFO",
        "warning": "CHECK_WARNING",
        "error": "CHECK_ERROR",
    },
    "check_tools": {  # Legacy alias for check
        "info": "TOOLCHECKER_INFO",
        "warning": "TOOLCHECKER_WARNING",
        "error": "TOOLCHECKER_ERROR",
    },
    "bot": {
        "info": "BOT_INFO",
        "warning": "BOT_WARNING",
        "error": "BOT_ERROR",
    },
    "web": {
        "info": "WEB_INFO",
        "warning": "WEB_WARNING",
        "error": "WEB_ERROR",
    },
    "admin_api": {
        "info": "ADMIN_API_INFO",
        "warning": "ADMIN_API_WARNING",
        "error": "ADMIN_API_ERROR",
    },
    "migration": {
        "info": "MIGRATION_INFO",
        "warning": "MIGRATION_WARNING",
        "error": "MIGRATION_ERROR",
    },
}


class Logger:
	"""Logger class for writing to file and console.

	Attributes:
		logScope (str): The service scope for log prefixes.
		logPath (str): Path to the logs directory.
	"""

	def __init__(self, logScope="check_tools"):
		"""Initialize the logger with a specific scope.

		Args:
			logScope (str): Service scope (api, check, bot, web, admin_api, migration).
		"""
		# Get scope configuration or use default
		scope_config = SERVICE_SCOPES.get(logScope, {
			"info": f"{logScope.upper()}_INFO",
			"warning": f"{logScope.upper()}_WARNING",
			"error": f"{logScope.upper()}_ERROR",
		})

		self.logtext_info = scope_config["info"]
		self.logtext_warning = scope_config["warning"]
		self.logtext_error = scope_config["error"]
		self.logScope = logScope

		# Global logs.
		self.logPath = os.path.join("/code" , "logs")
		self.globalErrorLogFile = os.path.join(self.logPath , "errorlog.txt")
		self.globalLogFile = os.path.join(self.logPath , "log.txt")
		fileUtils.createFileIfNotExists(self.globalErrorLogFile)
		fileUtils.createFileIfNotExists(self.globalLogFile)

		# Daybased logs.
		self.dayLogPath = os.path.join(self.logPath, "dayBased")
		self.updateDayBasedLogFilePaths()


	# Create dayBased logfile paths.
	def updateDayBasedLogFilePaths(self):
		dateStringForLogFileName = dateStringUtils.getDateStringForLogFileName()
		dayBasedErrorLogFileName = dateStringForLogFileName + "_errorlog.txt"
		dayBasedLogFileName = dateStringForLogFileName + "_log.txt"
		self.dayBasedErrorLogFile = os.path.join(self.dayLogPath , dayBasedErrorLogFileName)
		self.dayBasedLogFile = os.path.join(self.dayLogPath , dayBasedLogFileName)
		fileUtils.createFileIfNotExists(self.dayBasedErrorLogFile)
		fileUtils.createFileIfNotExists(self.dayBasedLogFile)


	## Logs an Error to 4 logfiles.
	# Logs to globalErrorLogFile, globalLogFile, dayErrorLogFile and dayLogFile.
	# Log entry will look like this: [2022-03-31 22:02:04] - [PYTHON_ERROR] - [errorToLog]
	def logError(self, errorToLog):

		# Always update day based log files first.
		self.updateDayBasedLogFilePaths()

		# Prepare full log text.
		fullLogText = "\n" + dateStringUtils.getDateStringForLogTag() + " - " + "[" + self.logtext_error + "]" + " - [" + errorToLog + "]"

		# write fullLogText to both info and error logs (day and global log files)
		self._log(self.globalErrorLogFile, fullLogText)
		self._log(self.globalLogFile, fullLogText)
		self._log(self.dayBasedErrorLogFile, fullLogText)
		self._log(self.dayBasedLogFile, fullLogText)

		# Print message to CLI.
		self._print_log_message(fullLogText)


	## Logs a Warning to 4 logfiles.
	# Logs to globalErrorLogFile, globalLogFile, dayErrorLogFile and dayLogFile.
	# Log entry will look like this: [2022-03-31 22:02:04] - [PYTHON_WARNING] - [warningToLog]
	def logWarning(self, warningToLog):

		# Always update day based log files first.
		self.updateDayBasedLogFilePaths()

		# Prepare full log text.
		fullLogText = "\n" + dateStringUtils.getDateStringForLogTag() + " - " + "[" + self.logtext_warning + "]" + " - [" + warningToLog + "]"

		# write fullLogText to both info and error logs (day and global log files)
		self._log(self.globalErrorLogFile, fullLogText)
		self._log(self.globalLogFile, fullLogText)
		self._log(self.dayBasedErrorLogFile, fullLogText)
		self._log(self.dayBasedLogFile, fullLogText)

		# Print message to CLI.
		self._print_log_message(fullLogText)


	## Logs an Information to 2 logfiles.
	# Logs to globalLogFile and dayLogFile.
	# Log entry will look like this: [2022-03-31 22:02:04] - [PYTHON_INFO] - [informationToLog]
	def logInformation(self, informationToLog):

		# Always update day based log files first.
		self.updateDayBasedLogFilePaths()

		# Prepare full log text.
		fullLogText = "\n" + dateStringUtils.getDateStringForLogTag() + " - " + "[" + self.logtext_info + "]" + " - [" + informationToLog + "]"

		# write fullLogText info logs (day and global log files)
		self._log(self.globalLogFile, fullLogText)
		self._log(self.dayBasedLogFile, fullLogText)

		# Print message to CLI.
		self._print_log_message(fullLogText)


	# PRIVATE function write a string to a file
	def _log(self, file, fullLogText):
		with open(file, 'a+') as f:
			f.write("\n" + fullLogText)
	
	

	def _print_log_message(self, message_to_print:str):
		"""
		Print message to cli.

		Replaces Special tags to improve output.

		Args:
			message_to_print (str): The message to pring.
		"""
		# String replacements.
		message_to_print=message_to_print.replace("<EMPHASIZE_STRING_START_TAG>", "\"")
		message_to_print=message_to_print.replace("</EMPHASIZE_STRING_END_TAG>", "\"")

		# Print message.
		print(message_to_print)
