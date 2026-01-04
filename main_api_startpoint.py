"""Module: main_api_startpoint.py

Description:
    FastAPI entrypoint for the statechecker server.

    This module exposes endpoints used by stateChecker-client:
    - /v1/statecheck
    - /v1/backupcheck
    - /v1/*/stop

    It also provides a lightweight /health endpoint for container health checks.
"""

from typing import Union

from fastapi import FastAPI, Response, status
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Import own classes.
# Insert path to own stuff to allow importing them.
import os
import sys
sys.path.insert(1, os.path.join(os.path.dirname(__file__), "src/", "utils"))
sys.path.insert(1, os.path.join(os.path.dirname(__file__), "src/", "models"))
sys.path.insert(1, os.path.join(os.path.dirname(__file__), "src/", "definitions"))

# Database Connection.
import databaseWrapper as DatabaseWrapper

# StateCheckItem from own models to use location independent.
import stateCheckItem as StateCheckItem

# BackupCheckItem from own models to use location independent.
import backupCheckItem as BackupCheckItem

# Get environment variables.
import configUtils as ConfigUtils
configUtils = ConfigUtils.ConfigUtils()

import adminApiBackupsRoutes as AdminApiBackupsRoutes
import adminApiConfigRoutes as AdminApiConfigRoutes
import adminApiGoogleDriveRoutes as AdminApiGoogleDriveRoutes
import adminApiToolsRoutes as AdminApiToolsRoutes
import adminApiWebsitesRoutes as AdminApiWebsitesRoutes

# StateCheckItem as pydantic model to use with fastAPI.
# To unify usage, this model should be converted to StateCheckItem asap.
# @see convertPydanticModelToStateCheckItem().
class StateCheckItem_pydantic(BaseModel):
    """Pydantic API model for a state check request."""

    server_auth_token: str
    name: str
    description: Union[str, "None"] = "None"
    token: str
    hashedString: Union[str, "None"] = "None"
    autoHealCommand: Union[str, "None"] = "None"
    stateCheckFrequency_inMinutes: int



# BackupCheckItem as pydantic model to use with fastAPI.
# To unify usage, this model should be converted to BackupCheckItem asap.
# @see convertPydanticModelToBackupCheckItem().
class BackupCheckItem_pydantic(BaseModel):
    """Pydantic API model for a backup check request."""

    server_auth_token: str
    name: str
    description: Union[str, "None"] = "None"
    token: str
    stateCheckFrequency_inMinutes: int
    mostRecentBackupFile_creationDate: str
    mostRecentBackupFile_hash: str


# Instantiate Fast API.
app = FastAPI()

app.mount("/admin", StaticFiles(directory="website", html=True), name="admin")

app.include_router(AdminApiConfigRoutes.router)
app.include_router(AdminApiToolsRoutes.router)
app.include_router(AdminApiWebsitesRoutes.router)
app.include_router(AdminApiGoogleDriveRoutes.router)
app.include_router(AdminApiBackupsRoutes.router)

@app.get("/")
async def root_get():
    """Root endpoint.

    Returns:
        dict: A hint to the client repository.
    """

    return {"message": "https://github.com/Sokrates1989/stateChecker-client"}


@app.get("/health")
async def health_get():
    """Health endpoint for container health checks.

    Returns:
        dict: Health status.
    """

    return {"status": "ok"}


# Start checking the availability of a new tool or update the last time the tool has been available.
@app.post("/v1/statecheck")
async def statecheck(stateCheckItem_pydantic: StateCheckItem_pydantic, response: Response):
    """Create or update a state check record.

    Args:
        stateCheckItem_pydantic (StateCheckItem_pydantic): Incoming state check payload.
        response (Response): FastAPI response for setting status codes.

    Returns:
        dict|None: Error response on auth failure, otherwise `None`.
    """

    if is_server_authentication_token_valid(stateCheckItem_pydantic.server_auth_token):
        overrides = configUtils.getToolsUsingApiFrequencyOverrides()
        if isinstance(overrides, dict) and stateCheckItem_pydantic.name in overrides:
            try:
                stateCheckItem_pydantic.stateCheckFrequency_inMinutes = int(overrides[stateCheckItem_pydantic.name])
            except Exception:
                pass
        stateCheckItem = convertPydanticModelToStateCheckItem(stateCheckItem_pydantic)
        dbWrapper = DatabaseWrapper.DatabaseWrapper()
        stateCheckItem = dbWrapper.createOrUpdateStateCheck(stateCheckItem)
        if stateCheckItem == None:
            response.status_code = 401
            return {"message": "invalid tool token"}
        else:
            return 
    else:
        response.status_code = 401
        return {"message": "invalid server authentication token"}


# Stop checking the availablity of a watched tool.
@app.post("/v1/statecheck/stop")
async def stop_statecheck(stateCheckItem_pydantic: StateCheckItem_pydantic, response: Response):
    """Stop checking the availability of a watched tool.

    Args:
        stateCheckItem_pydantic (StateCheckItem_pydantic): Incoming state check payload.
        response (Response): FastAPI response for setting status codes.

    Returns:
        dict|StateCheckItem.StateCheckItem: Error response on auth failure, otherwise the stopped item.
    """

    if is_server_authentication_token_valid(stateCheckItem_pydantic.server_auth_token):
        stateCheckItem = convertPydanticModelToStateCheckItem(stateCheckItem_pydantic)
        dbWrapper = DatabaseWrapper.DatabaseWrapper()
        stateCheckItem = dbWrapper.stopStateCheck(stateCheckItem)
        if stateCheckItem == None:
            response.status_code = 401
            return {"message": "invalid token"}
        else:
            return stateCheckItem
    else:
        response.status_code = 401
        return {"message": "invalid server authentication token"}



# Start checking a backup or update a backup check.
@app.post("/v1/backupcheck")
async def backupcheck(backupCheckItem_pydantic: BackupCheckItem_pydantic, response: Response):
    """Create or update a backup check record.

    Args:
        backupCheckItem_pydantic (BackupCheckItem_pydantic): Incoming backup check payload.
        response (Response): FastAPI response for setting status codes.

    Returns:
        dict|None: Error response on auth failure, otherwise `None`.
    """

    if is_server_authentication_token_valid(backupCheckItem_pydantic.server_auth_token):
        overrides = configUtils.getBackupFrequencyOverrides()
        if isinstance(overrides, dict) and backupCheckItem_pydantic.name in overrides:
            try:
                backupCheckItem_pydantic.stateCheckFrequency_inMinutes = int(overrides[backupCheckItem_pydantic.name])
            except Exception:
                pass
        backupCheckItem = convertPydanticModelToBackupCheckItem(backupCheckItem_pydantic)
        dbWrapper = DatabaseWrapper.DatabaseWrapper()
        backupCheckItem = dbWrapper.createOrUpdateBackupCheck(backupCheckItem)
        if backupCheckItem == None:
            response.status_code = 401
            return {"message": "invalid token"}
        else:
            return 
    else:
        response.status_code = 401
        return {"message": "invalid server authentication token"}

# Stop checking the availablity of a watched tool.
@app.post("/v1/backupcheck/stop")
async def stop_backupcheck(backupCheckItem_pydantic: BackupCheckItem_pydantic, response: Response):
    """Stop checking the availability of a watched backup.

    Args:
        backupCheckItem_pydantic (BackupCheckItem_pydantic): Incoming backup check payload.
        response (Response): FastAPI response for setting status codes.

    Returns:
        dict|BackupCheckItem.BackupCheckItem: Error response on auth failure, otherwise the stopped item.
    """

    if is_server_authentication_token_valid(backupCheckItem_pydantic.server_auth_token):
        backupCheckItem = convertPydanticModelToBackupCheckItem(backupCheckItem_pydantic)
        dbWrapper = DatabaseWrapper.DatabaseWrapper()
        backupCheckItem = dbWrapper.stopBackupCheck(backupCheckItem)
        if backupCheckItem == None:
            response.status_code = 401
            return {"message": "invalid token"}
        else:
            return backupCheckItem
    else:
        response.status_code = 401
        return {"message": "invalid server authentication token"}



# Converts pydantic StateCheckItem_pydantic to StateCheckItem.
def convertPydanticModelToStateCheckItem(stateCheckItem_pydantic: StateCheckItem_pydantic):
    """Convert a Pydantic model to the internal StateCheckItem model.

    Args:
        stateCheckItem_pydantic (StateCheckItem_pydantic): Incoming Pydantic payload.

    Returns:
        StateCheckItem.StateCheckItem: Converted internal model.
    """

    # Ensure description is set.
    if stateCheckItem_pydantic.description == None:
        stateCheckItem_pydantic.description = ""

    stateCheckItem = StateCheckItem.StateCheckItem(
        stateCheckItem_pydantic.name, 
        stateCheckItem_pydantic.token, 
        stateCheckItem_pydantic.stateCheckFrequency_inMinutes, 
        stateCheckItem_pydantic.description
        )

    # Set hashedString if set.
    if stateCheckItem_pydantic.hashedString != None and stateCheckItem_pydantic.hashedString != "None":
        stateCheckItem.setHashedString(stateCheckItem_pydantic.hashedString)

    # Set autoHealCommand if set.
    if stateCheckItem_pydantic.autoHealCommand != None and stateCheckItem_pydantic.autoHealCommand != "None":
        stateCheckItem.setAutoHealCommand(stateCheckItem_pydantic.autoHealCommand)

    return stateCheckItem



# Converts pydantic BackupCheckItem_pydantic to BackupCheckItem.
def convertPydanticModelToBackupCheckItem(backupCheckItem_pydantic: BackupCheckItem_pydantic):
    """Convert a Pydantic model to the internal BackupCheckItem model.

    Args:
        backupCheckItem_pydantic (BackupCheckItem_pydantic): Incoming Pydantic payload.

    Returns:
        BackupCheckItem.BackupCheckItem: Converted internal model.
    """

    # Ensure description is set.
    if backupCheckItem_pydantic.description == None:
        backupCheckItem_pydantic.description = ""

    backupCheckItem = BackupCheckItem.BackupCheckItem(
        backupCheckItem_pydantic.name,
        backupCheckItem_pydantic.token, 
        backupCheckItem_pydantic.stateCheckFrequency_inMinutes, 
        backupCheckItem_pydantic.mostRecentBackupFile_creationDate, 
        backupCheckItem_pydantic.mostRecentBackupFile_hash, 
        backupCheckItem_pydantic.description
        )
    return backupCheckItem



# Is server authentication token valid?
def is_server_authentication_token_valid(server_auth_token: str):
    """Validate server authentication token.

    Args:
        server_auth_token (str): Provided server auth token.

    Returns:
        bool: True if the token matches the configured one.
    """

    return configUtils.getServerAuthenticationToken() == server_auth_token
