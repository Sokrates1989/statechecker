"""Module: adminApiRoutes.py

Description:
    Admin API endpoints for managing watched tools, websites, and backups.

    These endpoints are secured by the server authentication token
    (SERVER_AUTHENTICATION_TOKEN) and persist changes by updating the
    file-based config (typically logs/config.txt).

    The admin API is intentionally focused on *configuration-level* state:
    - websites.websitesToCheck
    - googleDrive.foldersToCheck
    - toolsUsingApi_frequencyOverrides
    - backupFrequencyOverrides

    For runtime/DB artifacts, endpoints also offer cleanup of the database tables
    (checked_tools, checked_websites, checked_backups) to avoid stale entries.
"""

from fastapi import APIRouter

import adminApiBackupsRoutes as AdminApiBackupsRoutes
import adminApiConfigRoutes as AdminApiConfigRoutes
import adminApiGoogleDriveRoutes as AdminApiGoogleDriveRoutes
import adminApiToolsRoutes as AdminApiToolsRoutes
import adminApiWebsitesRoutes as AdminApiWebsitesRoutes


router = APIRouter()
router.include_router(AdminApiConfigRoutes.router)
router.include_router(AdminApiToolsRoutes.router)
router.include_router(AdminApiWebsitesRoutes.router)
router.include_router(AdminApiGoogleDriveRoutes.router)
router.include_router(AdminApiBackupsRoutes.router)
