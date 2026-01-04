### Class for any interaction with the DB.
### All write and read operations of DB should be done in this file/ class.

## Imports.
# database connection.
import mysql.connector
# file sytem operations.
import os
# For getting config.
import json
# To retrieve current timestamp.
import time

# Import own classes.
# Insert path to own stuff to allow importing them.
import os
import sys
sys.path.insert(1, os.path.join(os.path.dirname(__file__), "..", "utils"))
sys.path.insert(1, os.path.join(os.path.dirname(__file__), "..", "models"))
sys.path.insert(1, os.path.join(os.path.dirname(__file__), "..", "definitions"))

# StateCheckItem from own models to use location independent.
import stateCheckItem as StateCheckItem

# BackupCheckItem from own models to use location independent.
import backupCheckItem as BackupCheckItem

# WebsiteState item from own models to use location independent.
import websiteStateAndMessageSentItem as WebsiteStateAndMessageSentItem

# Get configuration settings.
import configUtils as ConfigUtils


class DatabaseWrapper:

	# Constructor.
	def __init__(self):

		# Get connection to database.
		configUtils = ConfigUtils.ConfigUtils()

		# Database connection
		self.mydb = mysql.connector.connect(
			host=configUtils.getDatabaseHost(),
			user=configUtils.getDatabaseUser(),
			password=configUtils.getDatabasePassword(),
			database=configUtils.getDatabaseName(),
			port=3306
		)
		self.mycursor = self.mydb.cursor(buffered=True) # need to buffer to fix mysql.connector.errors.InternalError: Unread result found (https://stackoverflow.com/questions/29772337/python-mysql-connector-unread-result-found-when-using-fetchone)



	# Create or update state check of a tool.
	# Pass stateCheckItem as parameter.
	def createOrUpdateStateCheck(self, stateCheckItemToCreateOrUpdate):

		# Current time.
		now = int(time.time())

		# Does item already exist?
		stateCheckItem = self.getStateCheckItemByName(stateCheckItemToCreateOrUpdate.name)
		if stateCheckItem == None:
			# Create new tool to check for.
			stateCheckItem = self.createNewStateCheck(stateCheckItemToCreateOrUpdate)
		else:
			# Check if the token is the same.
			if stateCheckItem.token == stateCheckItemToCreateOrUpdate.token:
				# Update last time tool was up.
				stateCheckItem = self.indicateThatToolIsUp(stateCheckItem, stateCheckItemToCreateOrUpdate.description, stateCheckItemToCreateOrUpdate.stateCheckFrequency_inMinutes)
			else:
				# token is invalid.
				return None
		return stateCheckItem


	def deleteBackupCheckByName(self, name):
		"""Delete a backup check entry by name.

		Args:
			name (str): Backup name.
		"""

		query = "DELETE FROM checked_backups WHERE name=%s"
		val = (name, )
		self.mycursor.execute(query, val)
		self.mydb.commit()


	def updateBackupCheckFrequencyByName(self, name, stateCheckFrequency_inMinutes):
		"""Update the check frequency for a backup by name.

		Args:
			name (str): Backup name.
			stateCheckFrequency_inMinutes (int): New frequency in minutes.
		"""

		sql = "UPDATE checked_backups SET stateCheckFrequency_inMinutes = %s WHERE name = %s"
		val = (stateCheckFrequency_inMinutes, name)
		self.mycursor.execute(sql, val)
		self.mydb.commit()


	def updateToolCheckFrequencyByName(self, name, stateCheckFrequency_inMinutes):
		"""Update the check frequency for a tool by name.

		Args:
			name (str): Tool name.
			stateCheckFrequency_inMinutes (int): New frequency in minutes.
		"""

		sql = "UPDATE checked_tools SET stateCheckFrequency_inMinutes = %s WHERE name = %s"
		val = (stateCheckFrequency_inMinutes, name)
		self.mycursor.execute(sql, val)
		self.mydb.commit()
		return


	def deleteToolCheckByName(self, name):
		"""Delete a tool check entry by name.

		Args:
			name (str): Tool name.
		"""

		query = "DELETE FROM checked_tools WHERE name=%s"
		val = (name, )
		self.mycursor.execute(query, val)
		self.mydb.commit()

	# Get StateCheckItem by its name.
	# Pass name as parameter.
	# Return is stateCheckItem with DB ID or None.
	def getStateCheckItemByName(self, name):
		query = "SELECT ID, name, description, token, stateCheckFrequency_inMinutes, lastTimeToolWasUp, toolIsDownMessageHasBeenSent FROM checked_tools WHERE name=%s "
		val = (name, )
		self.mycursor.execute(query, val)
		myresult = self.mycursor.fetchone()

		# Did query retrieve valid stateCheckItem?
		stateCheckItem = None
		if (myresult != None):

			stateCheckItemHelper = {
				'ID': myresult[0],
				'name': myresult[1],
				'description': myresult[2],
				'token': myresult[3],
				'stateCheckFrequency_inMinutes': myresult[4],
				'lastTimeToolWasUp': myresult[5],
				'toolIsDownMessageHasBeenSent': myresult[6]
			}

			stateCheckItem = StateCheckItem.StateCheckItem(
				stateCheckItemHelper["name"],
				stateCheckItemHelper["token"], 
				stateCheckItemHelper["stateCheckFrequency_inMinutes"], 
				stateCheckItemHelper["description"],
				stateCheckItemHelper["ID"],
				stateCheckItemHelper["lastTimeToolWasUp"],
				stateCheckItemHelper["toolIsDownMessageHasBeenSent"]
			)
		return stateCheckItem


	# Create a new stateCheck.
	# Pass stateCheckItem as parameter.
	def createNewStateCheck(self, stateCheckItemToCreate):

		# Current time.
		now = int(time.time())

		# Does item already exist?
		stateCheckItem = self.getStateCheckItemByName(stateCheckItemToCreate.name)
		if stateCheckItem == None:

			# Create new tool to check state of.
			# Execute insert query to create a new state check item.
			insertSql = "INSERT INTO checked_tools (name, description, token, stateCheckFrequency_inMinutes, lastTimeToolWasUp) VALUES (%s, %s, %s, %s, %s)"
			val = (stateCheckItemToCreate.name, stateCheckItemToCreate.description, stateCheckItemToCreate.token, stateCheckItemToCreate.stateCheckFrequency_inMinutes, now)
			self.mycursor.execute(insertSql, val)
			self.mydb.commit()

			# Return newly created user.
			return self.getStateCheckItemByName(stateCheckItemToCreate.name)
		else:
			# Item already exists -> do nothing and return None.
			return None



	# Update lastTimeToolWasUp.
	# Returns updated stateItem.
	def indicateThatToolIsUp(self, stateCheckItemToUpdate, description, stateCheckFrequency_inMinutes):

		# Check if the token is the same.
		stateCheckItem = self.getStateCheckItemByName(stateCheckItemToUpdate.name)
		if stateCheckItem.token == stateCheckItemToUpdate.token:

			# Current time.
			now = int(time.time())

			sql = "UPDATE checked_tools SET lastTimeToolWasUp = %s, description = %s, stateCheckFrequency_inMinutes = %s WHERE ID = %s"
			val = (now, description, stateCheckFrequency_inMinutes, stateCheckItemToUpdate.ID)

			# Execute query.
			self.mycursor.execute(sql, val)
			self.mydb.commit()

			# Return updated item.
			return self.getStateCheckItemByName(stateCheckItemToUpdate.name)

		else:
			# Token is invalid.
			return None



	# Update state of ToolIsDownMessageHasBeenSent.
	# Pass stateCheckItemName and new state as parameter.
	def updateToolIsDownMessageHasBeenSentState(self, stateCheckItemName, newToolIsDownMessageHasBeenSentState):

		# Get the stateCheckItem.
		stateCheckItem = self.getStateCheckItemByName(stateCheckItemName)

		# Current time.
		now = int(time.time())

		sql = "UPDATE checked_tools SET toolIsDownMessageHasBeenSent = %s WHERE ID = %s"
		val = (newToolIsDownMessageHasBeenSentState, stateCheckItem.ID)

		# Execute query.
		self.mycursor.execute(sql, val)
		self.mydb.commit()

		# Return updated item.
		return self.getStateCheckItemByName(stateCheckItem.name)

			
	# Stop checking state.
	# Pass stateCheckItem as parameter.
	def stopStateCheck(self, stateCheckItemToDelete):

		# Verify correct token.
		stateCheckItem = self.getStateCheckItemByName(stateCheckItemToDelete.name)
		if stateCheckItem != None and stateCheckItemToDelete.token == stateCheckItem.token:

			# Delete state check.
			query = "DELETE FROM checked_tools WHERE ID=%s "
			val = (stateCheckItem.ID, )
			self.mycursor.execute(query, val)
			self.mydb.commit()

			return "Successfully stopped checking state"
		else:
			return None




	# Get all tools to check.
	# Return is an associative array or an empty array.
	def getAllToolsToCheck(self):
		query = "SELECT name FROM checked_tools ORDER BY ID"
		self.mycursor.execute(query)
		myresults = self.mycursor.fetchall()

		toolsToCheck = []
		for result in myresults:
			toolToCheck = self.getStateCheckItemByName(result[0])
			toolsToCheck.append(toolToCheck)
		return toolsToCheck





	# Create or update backup check of a tool.
	# Pass backupCheckItem as parameter.
	def createOrUpdateBackupCheck(self, backupCheckItemToCreateOrUpdate):

		# Current time.
		now = int(time.time())

		# Does item already exist?
		backupCheckItem = self.getBackupCheckItemByName(backupCheckItemToCreateOrUpdate.name)
		if backupCheckItem == None:
			# Create new tool to check for.
			backupCheckItem = self.createNewBackupCheck(backupCheckItemToCreateOrUpdate)
		else:
			# Check if the token is the same.
			if backupCheckItem.token == backupCheckItemToCreateOrUpdate.token:
				# Update last time tool was up.
				backupCheckItem = self.updateBackupCheck(backupCheckItemToCreateOrUpdate)
			else:
				# token is invalid.
				return None
		return backupCheckItem

	# Get BackupCheckItem by its name.
	# Pass name as parameter.
	# Return is backupCheckItem with DB ID or None.
	def getBackupCheckItemByName(self, name):
		query = "SELECT ID, name, description, token, stateCheckFrequency_inMinutes, mostRecentBackupFile_creationDate, mostRecentBackupFile_hash, backupIsDownMessageHasBeenSent FROM checked_backups WHERE name=%s "
		val = (name, )
		self.mycursor.execute(query, val)
		myresult = self.mycursor.fetchone()

		# Did query retrieve valid backupCheckItem?
		backupCheckItem = None
		if (myresult != None):

			backupCheckItemHelper = {
				'ID': myresult[0],
				'name': myresult[1],
				'description': myresult[2],
				'token': myresult[3],
				'stateCheckFrequency_inMinutes': myresult[4],
				'mostRecentBackupFile_creationDate': myresult[5],
				'mostRecentBackupFile_hash': myresult[6],
				'backupIsDownMessageHasBeenSent': myresult[7]
			}

			backupCheckItem = BackupCheckItem.BackupCheckItem(
				backupCheckItemHelper["name"],
				backupCheckItemHelper["token"], 
				backupCheckItemHelper["stateCheckFrequency_inMinutes"], 
				backupCheckItemHelper["mostRecentBackupFile_creationDate"],
				backupCheckItemHelper["mostRecentBackupFile_hash"],
				backupCheckItemHelper["description"],
				backupCheckItemHelper["ID"],
				backupCheckItemHelper["backupIsDownMessageHasBeenSent"]
			)
		return backupCheckItem


	# Create a new stateCheck.
	# Pass backupCheckItem as parameter.
	def createNewBackupCheck(self, backupCheckItemToCreate):

		# Current time.
		now = int(time.time())

		# Does item already exist?
		backupCheckItem = self.getBackupCheckItemByName(backupCheckItemToCreate.name)
		if backupCheckItem == None:

			# Create new tool to check state of.
			# Execute insert query to create a new backup check item.
			insertSql = "INSERT INTO checked_backups (name, description, token, stateCheckFrequency_inMinutes, mostRecentBackupFile_creationDate, mostRecentBackupFile_hash) VALUES (%s, %s, %s, %s, %s, %s)"
			val = (backupCheckItemToCreate.name, backupCheckItemToCreate.description, backupCheckItemToCreate.token, backupCheckItemToCreate.stateCheckFrequency_inMinutes, backupCheckItemToCreate.mostRecentBackupFile_creationDate, backupCheckItemToCreate.mostRecentBackupFile_hash)
			self.mycursor.execute(insertSql, val)
			self.mydb.commit()

			# Return newly created user.
			return self.getBackupCheckItemByName(backupCheckItemToCreate.name)
		else:
			# Item already exists -> do nothing and return None.
			return None



	# Update backup state.
	# Returns updated stateItem.
	def updateBackupCheck(self, backupCheckItemToUpdate):

		# Check if the token is the same.
		backupCheckItem = self.getBackupCheckItemByName(backupCheckItemToUpdate.name)
		if backupCheckItem.token == backupCheckItemToUpdate.token:

			# Only update the item, if the hash changed.
			if backupCheckItem.mostRecentBackupFile_hash == backupCheckItemToUpdate.mostRecentBackupFile_hash:
				print ("hash did not change")
				return backupCheckItem
			else:
				sql = "UPDATE checked_backups SET description = %s, stateCheckFrequency_inMinutes = %s, mostRecentBackupFile_creationDate = %s, mostRecentBackupFile_hash = %s WHERE ID = %s"
				val = (
					backupCheckItemToUpdate.description, 
					backupCheckItemToUpdate.stateCheckFrequency_inMinutes, 
					backupCheckItemToUpdate.mostRecentBackupFile_creationDate, 
					backupCheckItemToUpdate.mostRecentBackupFile_hash, 
					backupCheckItem.ID
				)

				# Execute query.
				self.mycursor.execute(sql, val)
				self.mydb.commit()

				# Return updated item.
				return self.getBackupCheckItemByName(backupCheckItemToUpdate.name)

		else:
			# Token is invalid.
			return None



	# Update state of backupIsDownMessageHasBeenSent.
	# Pass backupCheckItemName and new state as parameter.
	def updateBackupIsDownMessageHasBeenSentState(self, backupCheckItemName, newBackupIsDownMessageHasBeenSentState):

		# Get the backupCheckItem.
		backupCheckItem = self.getBackupCheckItemByName(backupCheckItemName)

		# Current time.
		now = int(time.time())

		sql = "UPDATE checked_backups SET backupIsDownMessageHasBeenSent = %s WHERE ID = %s"
		val = (newBackupIsDownMessageHasBeenSentState, backupCheckItem.ID)

		# Execute query.
		self.mycursor.execute(sql, val)
		self.mydb.commit()

		# Return updated item.
		return self.getBackupCheckItemByName(backupCheckItem.name)

			
	# Stop checking backup state.
	# Pass backupCheckItem as parameter.
	def stopBackupCheck(self, backupCheckItemToDelete):

		# Verify correct token.
		backupCheckItem = self.getBackupCheckItemByName(backupCheckItemToDelete.name)
		if backupCheckItem != None and backupCheckItemToDelete.token == backupCheckItem.token:

			# Delete backup check.
			query = "DELETE FROM checked_backups WHERE ID=%s "
			val = (backupCheckItem.ID, )
			self.mycursor.execute(query, val)
			self.mydb.commit()

			return "Successfully stopped checking backup"
		else:
			return None




	# Get all backups to check.
	# Return is an associative array or an empty array.
	def getAllBackupsToCheck(self):
		query = "SELECT name FROM checked_backups ORDER BY ID"
		self.mycursor.execute(query)
		myresults = self.mycursor.fetchall()

		toolsToCheck = []
		for result in myresults:
			toolToCheck = self.getBackupCheckItemByName(result[0])
			toolsToCheck.append(toolToCheck)
		return toolsToCheck





	# Get WebsiteCheckItem by its name.
	# Pass name as parameter.
	# Return is WebsiteStateAndMessageSentItem.
	def getWebsiteCheckItemByName(self, name):
		query = "SELECT ID, name, state, isDownMessageHasBeenSent FROM checked_websites WHERE name=%s "
		val = (name, )
		self.mycursor.execute(query, val)
		myresult = self.mycursor.fetchone()

		# Did query retrieve valid websiteCheckItem?
		websiteCheckItem = None
		if (myresult != None):

			websiteCheckItemHelper = {
				'ID': myresult[0],
				'name': myresult[1],
				'state': myresult[2],
				'isDownMessageHasBeenSent': myresult[3]
			}

			websiteCheckItem = WebsiteStateAndMessageSentItem.WebsiteStateAndMessageSentItem(
				websiteCheckItemHelper["name"],
				websiteCheckItemHelper["state"],
				websiteCheckItemHelper["isDownMessageHasBeenSent"]
			)
		return websiteCheckItem


	# Create a new stateCheck.
	# Pass websiteCheckItem as parameter.
	def createNewWebsiteCheck(self, websiteCheckItemToCreate):

		# Does item already exist?
		websiteCheckItem = self.getWebsiteCheckItemByName(websiteCheckItemToCreate.name)
		if websiteCheckItem == None:

			# Create new website to check state of.
			# Execute insert query to create a new website check item.
			insertSql = "INSERT INTO checked_websites (name, state, isDownMessageHasBeenSent) VALUES (%s, %s, %s)"
			val = (websiteCheckItemToCreate.name, websiteCheckItemToCreate.state, websiteCheckItemToCreate.isDownMessageHasBeenSent)
			self.mycursor.execute(insertSql, val)
			self.mydb.commit()

			# Return newly created user.
			return self.getWebsiteCheckItemByName(websiteCheckItemToCreate.name)
		else:
			# Item already exists -> do nothing and return None.
			return None



	# Update website state.
	def updateWebsiteState(self, websiteName, newState):

		# Check if the token is the same.
		sql = "UPDATE checked_websites SET state = %s WHERE name = %s"
		val = (
			newState, 
			websiteName
		)

		# Execute query.
		self.mycursor.execute(sql, val)
		self.mydb.commit()



	# Update state of websiteIsDownMessageHasBeenSent.
	# Pass websiteCheckItemName and new state as parameter.
	def updateWebsiteIsDownMessageHasBeenSentState(self, websiteCheckItemName, newWebsiteIsDownMessageHasBeenSentState):

		# Get the websiteCheckItem.
		websiteCheckItem = self.getWebsiteCheckItemByName(websiteCheckItemName)

		sql = "UPDATE checked_websites SET isDownMessageHasBeenSent = %s WHERE name = %s"
		val = (newWebsiteIsDownMessageHasBeenSentState, websiteCheckItem.name)

		# Execute query.
		self.mycursor.execute(sql, val)
		self.mydb.commit()

		# Return updated item.
		return self.getWebsiteCheckItemByName(websiteCheckItem.name)


	def deleteWebsiteCheckByName(self, name):
		"""Delete a website check entry by name.

		Args:
			name (str): Website URL/name.
		"""

		query = "DELETE FROM checked_websites WHERE name=%s"
		val = (name, )
		self.mycursor.execute(query, val)
		self.mydb.commit()

