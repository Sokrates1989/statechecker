## Basic file operations.

# Interaction with operating system (read write files).
import os

# For string sanitization.
import re

def createFileIfNotExists(fileToCreateIfNotExists):
	"""
	Creates a file and its parent directories if they do not exist.

	Args:
		fileToCreateIfNotExists (str): Absolute or relative path to the file.
	"""
	# Seperate directory from filename.
	if "/" in fileToCreateIfNotExists:
		lastSlashPosition = fileToCreateIfNotExists.rfind("/")

		directoryName = fileToCreateIfNotExists[0:(lastSlashPosition)]
		if not os.path.exists(directoryName):
			os.makedirs(directoryName)
			os.chmod(directoryName, 0o775)

		if not os.path.exists(fileToCreateIfNotExists):
			os.mknod(fileToCreateIfNotExists)
			os.chmod(fileToCreateIfNotExists, 0o775)
	else:
		print("Cannot create a file without directory (pass filename containing filepath like \"path/to/file.txt\")")


# Get a valid filename for a string.
def getValidFileNameForString(stringToConvertToFileName, fileType):
	"""
	Converts a string into a valid filename by removing non-alphanumeric characters.

	Args:
		stringToConvertToFileName (str): The string to convert.
		fileType (str): The file extension to append.

	Returns:
		str: A sanitized filename.
	"""
	whiteListedCharactersRegEx = r"[^a-zA-Z0-9.\-_]"
	validFilename = re.sub(whiteListedCharactersRegEx, '', str(stringToConvertToFileName) )
	validFilename = validFilename[:100]
	validFilename += "." + str(fileType)
	return validFilename


# Read string from file.
def readStringFromFile(fileToReadStringFrom):
	"""
	Reads the entire content of a file as a string.

	Args:
		fileToReadStringFrom (str): Path to the file.

	Returns:
		str: The file content.
	"""
	string = ""
	with open(fileToReadStringFrom, 'r') as file:
		string = file.read().rstrip()
	return string


# Overwrite string of file.
# !!! Completely removes previous content !!!
def overwriteContentOfFile(fileToEdit, newString):
	"""
	Overwrites the content of a file with a new string.

	Args:
		fileToEdit (str): Path to the file.
		newString (str): The new content.
	"""
	with open(fileToEdit,'w') as f:
		f.write(str(newString))